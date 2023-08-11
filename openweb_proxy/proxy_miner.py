#!/bin/env python3
# Copyright 2022 Badreddine LEJMI.
# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from typing import Any, Dict, List, Set, Union
import socket


import requests
import socks
from bs4 import BeautifulSoup
from loguru import logger as log

from openweb_proxy import config

from .random_ua_headers import random_ua_headers


class ProxyMiner:
    """
    Mine proxies from the Web:
    - load them from public sources on the Web
    - check and keep proxies undetected as proxy
    - verify and keep only working proxies
    """

    def __init__(
        self,
        protocol: str = config.PROXY_PROTOCOL,
        timeout: int = config.TIMEOUT,
        sources: Dict[str, List[Any]] = config.PROXY_SOURCES,
        checker: Dict[str, str] = config.CHECK_URL,
        regex: str = config.RE_IP_V4,
    ):
        self.protocol = protocol
        self.timeout = timeout
        self.sources = sources
        self.checker = checker
        self.regex = regex

        self.proxies: Set[str] = set()

        self.sources["https"].extend(
            [
                self._get_sslproxies,
                self._get_clarketm,
            ]
        )

    def _get_sslproxies(self, timeout: int = 0) -> Set[str]:
        """Get HTTPS proxies from sslproxies.org"""
        timeout = timeout if timeout else self.timeout
        r = requests.get(
            "https://www.sslproxies.org/", random_ua_headers(), timeout=timeout
        )
        soup = BeautifulSoup(r.text, "html.parser")
        proxies_table = soup.find("table", class_="table-striped").tbody
        for row in proxies_table.find_all("tr"):
            proxy = row.find_all("td")
            ip = proxy[0].string
            port = proxy[1].string
            self.proxies.add(f"https://{ip}:{port}")
        log.debug(f"🪲 Proxies sslproxies number: {len(self.proxies)}")
        # Return empty set since we updated proxies via self
        return set()

    def _get_clarketm(self, timeout: int = 0) -> Set[str]:
        """Get HTTPS proxies from clarketm on github"""
        timeout = timeout if timeout else self.timeout
        r = requests.get(
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt",
            timeout=timeout,
        )
        for proxy_l in r.text.splitlines()[6:-2]:
            if "S" in proxy_l:
                self.proxies.add("https://%s" % proxy_l.split(" ")[0])
        log.debug(f"🪲 Proxies clarketm number: {len(self.proxies)}")
        # Return empty set since we updated proxies via self
        return set()

    def _get_proxies(self, url: str) -> None:
        """Get proxies list from github and al"""
        try:
            r = requests.get(url, timeout=self.timeout)
            self.proxies.update(
                {
                    f"{self.protocol}://{proxy.group(1)}"
                    for proxy in self.regex.finditer(r.text)
                }
            )
            log.debug(f"🪲 Proxies number from {url}: {len(self.proxies)}")
        except requests.exceptions.ReadTimeout:
            log.error(f"❌ Source {url} timed out")
        except requests.exceptions.ConnectionError:
            log.error(f"❌ Connection to source {url} failed")

    def get(self) -> List[str]:
        """Get proxies from public sources

        Args:
            protocol (str, optional): Default proxy protocol (HTTPS or Socks).
                                      Defaults to PROXY_PROTOCOL.
            timeout (int, optional): timeout. Defaults to TIMEOUT.
            sources (dict, optional): Public sources of proxies.
                                      Defaults to PROXY_GETTERS.

        Returns:
            list[str]: list of URL proxies
        """
        for proxy_getter in self.sources[self.protocol]:
            if callable(proxy_getter):
                proxies = proxy_getter(self.timeout)
                if proxies:
                    self.proxies.update(proxies)
            else:
                self._get_proxies(proxy_getter)
        log.info(f"Proxies number (raw): {len(self.proxies)}")
        return list(self.proxies)

    def _check_generic(self, proxy) -> str:
        proxy_host, proxy_port = proxy.removeprefix(
            f"{self.protocol}://"
        ).split(":")
        proxy_port = int(proxy_port)

        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
        socket.socket = socks.socksocket

        generic_server, generic_port = config.checker["generic"].split(":")
        generic_port = int(generic_port)

        try:
            client_socket = socket.create_connection(
                (generic_server, generic_port), timeout=5
            )
            log.debug(f"✅ Proxy is OK (generic): {proxy}")
        except OSError as e:
            log.debug(f"❌ Proxy connection failed: {proxy} with error {e}")
            return ""

        if "client_socket" in locals():
            client_socket.close()

        return proxy

    def _check_http(self, proxy) -> str:
        try:
            r = requests.get(
                self.checker["url"],
                random_ua_headers(),
                proxies={"https": proxy},
                timeout=self.timeout,
            )
        except requests.ConnectTimeout:
            log.debug(f"❌ Proxy timeout: {proxy}")
            return ""
        except requests.exceptions.ProxyError as e:
            log.debug(f"❌ Proxy error. Proxy: {proxy}. Error: {e}")
            return ""
        except requests.RequestException as e:
            log.debug(f"❌ Request error. Proxy: {proxy}. Error: {e}")
            return ""
        except UnicodeError as e:
            log.debug(f"❌ Unicode error. Proxy: {proxy}. Error: {e}")
            return ""

        if not r.ok:
            log.debug(f"❌ Proxy rejected by website: {proxy}")
            return ""
        # needs a website with a specific string that says "this is/isn't a proxy"
        # #if not CHECK_URL['not_proxy'] in r.text:
        #    log.info(f"👎 Proxy detected {proxy}")
        #    return ""

        log.debug(f"✅ Proxy is OK (http): {proxy}")
        log.debug(f"🪲 Answer: {r.text}")
        return proxy

    def _clean_proxy(self, proxy: str) -> str:
        """Check if a proxy URL is working"""
        log.debug(f"🪲 Testing proxy: {proxy}")

        proxy = self._check_generic(proxy)
        if not proxy:
            return False

        proxy = self._check_http(proxy)
        if not proxy:
            return False

        log.info(f"✅ Proxy is OK: {proxy}")
        return proxy

    def clean(self, max_workers: int = config.MAX_CHECK_WORKERS) -> None:
        mail_banned_ips = requests.get(
            config.BANNED_URL, timeout=self.timeout
        ).text
        # We can use a with statement to ensure threads are cleaned up promptly
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            proxies_clean = set()
            log.info(
                f"Checking if {len(self.proxies)} proxies given are working"
            )
            # Start the load operations and mark each future with its URL
            future_proxies = {
                executor.submit(self._clean_proxy, proxy): proxy
                for proxy in self.proxies
            }
            for proxy in as_completed(future_proxies):
                if (
                    proxy.result()
                    and future_proxies[proxy] not in mail_banned_ips
                ):
                    proxies_clean.add(future_proxies[proxy])
                continue
        self.proxies = proxies_clean

    def is_proxy(
        self, ip: str, check_url: str = config.ISPROXY_URL
    ) -> Union[bool, None]:
        log.info(f"i Testing {ip}")
        try:
            r = requests.get(check_url.format(ip=ip), timeout=self.timeout)
        except requests.RequestException:
            return None

        resp = r.json()

        if resp["status"] != "success":
            log.warning(f"Failed to check: {ip}")
            return None
        if resp["proxy"]:
            log.info(f"Proxy detected: {ip}")
            return True
        return False

    def verify(
        self,
        url: str = config.ISPROXY_URL_BATCH,
        max_proxy_batch: int = config.MAX_ISPROXY_BATCH,
    ) -> bool:
        """Keep only proxies undetected as proxy by the webservice URL

        Args:
            url (str, optional): Is Proxy Webservice. Defaults to ISPROXY_URL_BATCH.
            max_proxy_batch (int, optional): max by batch.
                                             Defaults to MAX_ISPROXY_BATCH.

        Returns:
            bool: success
        """
        ips = dict(
            [
                p.removeprefix(f"{self.protocol}://").split(":")
                for p in self.proxies
            ]
        )
        ips_l = list(ips.keys())
        chunks = [
            ips_l[x : x + max_proxy_batch]
            for x in range(0, len(ips_l), max_proxy_batch)
        ]
        chunk_i = 1
        log.debug(f"Start Batch Testing. Chunks: {len(chunks)}.")
        for chunk in chunks:
            log.debug(f"Batch testing. Chunk: {chunk_i}/{len(chunks)}")
            try:
                r = requests.post(
                    url, data=str(chunk).replace("'", '"'), timeout=self.timeout
                )
            except requests.RequestException as e:
                log.error(f"Batch testing. Request Error: {e}")
                return False

            if not r.ok:
                log.error(f"Batch testing. HTTP Error: {r.text}")
                return False

            log.debug(
                "🪲 Still {} requests in {} seconds".format(
                    r.headers["X-Rl"], r.headers["X-Ttl"]
                )
            )
            if int(r.headers["X-Rl"]) == 0:
                log.info(
                    f"Batch testing. Chunk: {chunk_i}/{len(chunks)}. "
                    + "Sleep: {r.headers['X-Ttl']}s before next chunk"
                )
                sleep(int(r.headers["X-Ttl"]) + self.timeout)

            results = r.json()
            self.proxies.update(
                [
                    f"{self.protocol}://{p['query']}:{ips[p['query']]}"
                    for p in results
                    if p["status"] == "success" and not p["proxy"]
                ]
            )
            chunk_i += 1

        return True

    def load(
        self, filename: str = config.PROXIES_FILE, web: bool = True
    ) -> List[str]:
        """Load set of proxies from file or web if file is empty

        Args:
            filename (str, optional): filename. Defaults to PROXIES_FILE.
            web (bool, optional): Loads from Web as fallback.
                                  Defaults to True (forced if file doesn't exist).
        """
        if web:
            log.warning("Will load from Web")
            return self.get()
        elif not os.path.exists(filename):
            log.warning(f"File {filename} not found")
            log.warning("Nothing to do, please add `--web` to pull from web")
            return []
        with open(filename, "r+") as p:
            proxies = p.read().splitlines()
            if proxies:
                log.info(f"✅ {len(proxies)} proxies loaded from {filename}")
                self.proxies.update(proxies)
                return list(self.proxies)
            elif web:
                log.warning(
                    f"No proxies found in {filename}. Will load from Web"
                )
                return self.get()
            else:
                log.warning(f"No proxies found in {filename}")
                return []

    def save(self, filename: str = config.PROXIES_FILE) -> int:
        """Save list of proxies into file

        Args:
            filename (str, optional): filename. Defaults to PROXIES_FILE.
        """
        if self.proxies:
            with open(filename, "w") as f:
                return f.write("\n".join(self.proxies) + "\n")
        return -1

    def random(self) -> Dict[str, str]:
        return {self.protocol: random.choice(list(self.proxies))}

    def refresh(self) -> None:
        self.load()
        self.verify()
        self.clean()

    def benchmark_sources(self) -> None:
        sources = {source: 0 for source in self.sources[self.protocol]}
        log.warning("Benchmarking sources, nothing will be written to file")
        for source in sources:
            self.sources[self.protocol] = [source]
            self.get()
            self.verify()
            self.clean()
            sources[source] = len(self.proxies)
        for source in sources:
            if sources[source]:
                log.info(
                    f"👍 Source {source} contains {sources[source]} valid proxies"
                )
            else:
                log.info(f"👎 Source {source} has no valid proxies")
