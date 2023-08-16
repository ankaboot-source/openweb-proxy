#!/bin/env python3
# Copyright 2022 Badreddine LEJMI.
# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
import socket


import requests
import socks
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

    re_ip_v4 = config.RE_IP_V4

    # pylint: disable=dangerous-default-value
    def __init__(
        self,
        protocol: str = config.PROXY_PROTOCOL,
        timeout: int = config.TIMEOUT,
        sources: dict[str, list] = config.PROXY_SOURCES,
        checker: dict[str, str] = config.CHECK_URLS,
    ):
        self.protocol = protocol
        self.timeout = timeout
        self.sources = sources
        self.checker = checker

        if os.path.exists(self.checker["banned"]):
            with open(self.checker["banned"], "r", encoding="utf-8") as file:
                self.banned_list = file.read().split("\n")
        elif config.RE_URL.match(self.checker["banned"]):
            try:
                self.banned_list = requests.get(
                    self.checker["banned"], timeout=self.timeout
                ).text.split("\n")
            except requests.exceptions.RequestException as e:
                log.warning(f"Unable to get banned list: {e}")
                self.banned_list = []
        elif self.checker["banned"]:
            log.warning(
                f"{self.checker['banned']}: Not a URL or file does not exist"
            )
            self.banned_list = []
        else:
            self.banned_list = []

        self.proxies: set[str] = set()

    def _get_proxies(self, url: str) -> None:
        """Get proxies list from github and al"""
        try:
            r = requests.get(url, timeout=self.timeout)
            self.proxies.update(
                {
                    f"{self.protocol}://{proxy.group(1)}"
                    for proxy in self.re_ip_v4.finditer(r.text)
                }
            )
            log.debug(f"🪲 Proxies number from {url}: {len(self.proxies)}")
        except requests.exceptions.ReadTimeout:
            log.error(f"❌ Source {url} timed out")
        except requests.exceptions.ConnectionError as e:
            log.error(f"❌ Connection to source {url} failed with error {e}")

    def get(self) -> list[str]:
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

    def _check_generic(self, proxy) -> str | bool:
        proxy_host, proxy_port = proxy.removeprefix(
            f"{self.protocol}://"
        ).split(":")
        proxy_port = int(proxy_port)

        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
        socket.socket = socks.socksocket

        generic_server, generic_port = self.checker["generic"].split(":")
        generic_port = int(generic_port)

        try:
            client_socket = socket.create_connection(
                (generic_server, generic_port), timeout=5
            )
            log.debug(f"🪲 Proxy is OK (generic): {proxy}")
        except OSError as e:
            log.debug(f"❌ Proxy connection failed: {proxy} with error {e}")
            return False

        if "client_socket" in locals():
            client_socket.close()

        return proxy

    def _check_http(self, proxy) -> str | bool:
        try:
            r = requests.get(
                self.checker["url"],
                random_ua_headers(),
                proxies={"https": proxy},
                timeout=self.timeout,
            )
        except requests.ConnectTimeout:
            log.debug(f"❌ Proxy timeout: {proxy}")
            return False
        except requests.exceptions.ProxyError as e:
            log.debug(f"❌ Proxy error. Proxy: {proxy}. Error: {e}")
            return False
        except requests.RequestException as e:
            log.debug(f"❌ Request error. Proxy: {proxy}. Error: {e}")
            return False
        except UnicodeError as e:
            log.debug(f"❌ Unicode error. Proxy: {proxy}. Error: {e}")
            return False

        if not r.ok:
            log.debug(f"❌ Proxy rejected by website: {proxy}")
            return False
        # needs a website with a specific string that says "this is/isn't a proxy"
        # #if not CHECK_URL['not_proxy'] in r.text:
        #    log.info(f"👎 Proxy detected {proxy}")
        #    return False

        log.debug(f"🪲 Proxy is OK (http): {proxy}")
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
        """
        Clean the list of proxies by removing non-working proxies.

        This method filters out non-working proxies from the list of proxies stored
        in the instance. Proxies are checked for their functionality using concurrent
        requests to determine if they are operational.

        :param max_workers: The maximum number of concurrent workers.
            Defaults to the value specified in the configuration.
        :type max_workers: int, optional

        :return: None
        """
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
                    and future_proxies[proxy] not in self.banned_list
                ):
                    proxies_clean.add(future_proxies[proxy])
                continue
        self.proxies = proxies_clean

    def is_proxy(self, ip: str, check_url: str = config.ISPROXY_URL) -> bool:
        "Uses a check url to see if a proxy is detectable as a proxy."
        log.info(f"i Testing {ip}")
        try:
            r = requests.get(check_url.format(ip=ip), timeout=self.timeout)
        except requests.RequestException:
            return False

        resp = r.json()

        if resp["status"] != "success":
            log.warning(f"Failed to check: {ip}")
            return False
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
                "🪲 Still {r.headers['X-Rl']} requests in {r.headers['X-Ttl']} seconds"
            )
            if int(r.headers["X-Rl"]) == 0:
                log.info(
                    f"Batch testing. Chunk: {chunk_i}/{len(chunks)}. "
                    + f"Sleep: {r.headers['X-Ttl']}s before next chunk"
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
    ) -> list[str]:
        """Load set of proxies from file or web if file is empty

        Args:
            filename (str, optional): filename. Defaults to PROXIES_FILE.
            web (bool, optional): Loads from Web as fallback.
                                  Defaults to True (forced if file doesn't exist).
        """
        if filename and os.path.exists(filename):
            with open(filename, "r+", encoding="utf-8") as p:
                self.proxies.update(p.read().splitlines())
            if self.proxies:
                log.info(
                    f"✅ {len(self.proxies)} proxies loaded from {filename}"
                )
            else:
                log.debug(f"❌ No proxies loaded from {filename}")

        if web:
            log.warning("Will load from Web")
            log.warning(f"No proxies found in {filename}. Will load from Web")
            return self.get()
        log.warning(f"No proxies found in {filename}")
        log.warning("Nothing to do, please add `--web` to pull from web")
        return []

    def save(self, filename: str = config.PROXIES_FILE) -> int:
        """Save list of proxies into file

        Args:
            filename (str, optional): filename. Defaults to PROXIES_FILE.
        """
        if self.proxies:
            with open(filename, "w", encoding="utf-8") as f:
                return f.write("\n".join(self.proxies) + "\n")
        return -1

    def random(self) -> dict[str, str]:
        "Returns a random proxy from the list"
        return {self.protocol: random.choice(list(self.proxies))}

    def refresh(self) -> None:
        """Refresh proxies from the source list."""
        self.load()
        self.verify()
        self.clean()

    def benchmark_sources(self) -> None:
        """
        Benchmarks the sources to determine their quality.
        """
        source_properties = {"total": 0, "clean": 0, "working": 0}
        sources = {
            source: source_properties.copy()
            for source in self.sources[self.protocol]
        }
        log.warning("Benchmarking sources, nothing will be written to file")
        for source in sources:
            self.sources[self.protocol] = [source]
            self.get()
            sources[source]["total"] = len(self.proxies)
            self.clean()
            sources[source]["clean"] = len(self.proxies)
            self.verify()
            sources[source]["working"] = len(self.proxies)
        for source in sources:
            for stage in source_properties:
                if sources[source][stage]:
                    log.info(
                        f"👍 Source {source} contains \
{sources[source][stage]} {stage} proxies"
                    )
                else:
                    log.info(f"👎 Source {source} has no {stage} proxies")
