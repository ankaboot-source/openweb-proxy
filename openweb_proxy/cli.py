#!/bin/env python3
# Copyright 2022 Badreddine LEJMI.
# SPDX-License-Identifier: AGPL-3.0-or-later
import argparse
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger as log

PROXIES_FILE = "proxies.txt"
PROXY_FILE = "proxy.txt"
ISPROXY_URL = "http://ip-api.com/json/{ip}?fields=status,proxy"
ISPROXY_URL_BATCH = "http://ip-api.com/batch?fields=status,proxy,query"
MAX_ISPROXY_BATCH = 100
CHECK_URL = {
    "url": "https://google.com",
    #    'url': "https://vpnapi.io/proxy-detection",
    #    'not_proxy': "this IP address is not a proxy server",
}
CHECK_MAX = 100
MAX_CHECK_WORKERS = 20
PROXY_PROTOCOL = "socks5"
DEFAULT_PROXY = "https://localhost:3128"
TIMEOUT = 5
MAX_WORKERS = 10

PROXY_SOURCES = {
    "https": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    ],
    "socks5": [
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://www.proxyscan.io/download?type=socks5",
        "https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/User-R3X/proxy-list/main/online/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/socks5.txt",
    ],
}


def random_ua_headers():
    """
    generate a random user-agent
    most basic technique against bot blockers
    """
    ua = UserAgent()
    return {"user-agent": ua.random}


class ProxyMiner:
    """
    Mine proxies from the Web:
    - load them from public sources on the Web
    - check and keep proxies undetected as proxy
    - verify and keep only working proxie
    """

    def __init__(
        self,
        protocol: str = PROXY_PROTOCOL,
        timeout: int = TIMEOUT,
        sources: dict = PROXY_SOURCES,
        checker: str = CHECK_URL,
    ):
        self.protocol = protocol
        self.timeout = timeout
        self.sources = sources
        self.checker = checker
        self.regex = re.compile(
            r"(?:^|\D)(({0}\.{1}\.{1}\.{1}):{2})(?:\D|$)".format(
                r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])",  # 1-255
                r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])",  # 0-255
                r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}" + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])",  # 0-65535
            )
        )
        self.proxies = set()

        self.sources["https"].extend(
            [
                self._get_sslproxies,
                self._get_clarketm,
            ]
        )

    def _get_sslproxies(self):
        """Get HTTPS proxies from sslproxies.org"""
        r = requests.get("https://www.sslproxies.org/", random_ua_headers(), timeout=self.timeout)
        soup = BeautifulSoup(r.text, "html.parser")
        proxies_table = soup.find("table", class_="table-striped").tbody
        for row in proxies_table.find_all("tr"):
            proxy = row.find_all("td")
            ip = proxy[0].string
            port = proxy[1].string
            self.proxies.add(f"https://{ip}:{port}")
        log.debug(f"🪲 Proxies sslproxies number: {len(self.proxies)}")

    def _get_clarketm(self):
        """Get HTTPS proxies from clarketm on github"""
        r = requests.get(
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt", timeout=self.timeout
        )
        for proxy_l in r.text.splitlines()[6:-2]:
            if "S" in proxy_l:
                self.proxies.add("https://%s" % proxy_l.split(" ")[0])
        log.debug(f"🪲 Proxies clarketm number: {len(self.proxies)}")

    def _get_proxies(self, url: str):
        """Get proxies list from github and al"""
        r = requests.get(url, timeout=self.timeout)
        self.proxies.update({f"{self.protocol}://{proxy}" for proxy in self.regex.finditer(r.text)})
        log.debug(f"🪲 Proxies number from {url}: {len(self.proxies)}")

    def get(self) -> list[str]:
        """Get proxies from public sources

        Args:
            protocol (str, optional): default proxy protocol (HTTPS or Socks). Defaults to PROXY_PROTOCOL.
            timeout (int, optional): timeout. Defaults to TIMEOUT.
            sources (dict, optional): public sources of proxies. Defaults to PROXY_GETTERS.

        Returns:
            list[str]: list of URL proxies
        """
        for proxy_getter in self.sources[self.protocol]:
            if type(proxy_getter) == str:
                self._get_proxies(proxy_getter)
            else:
                proxy_getter()
        log.info(f"Proxies number (raw): {len(self.proxies)}")
        return list(self.proxies)

    def _clean_proxy(self, proxy):
        """Check if a proxy URL is working"""
        log.debug(f"🪲 Testing proxy: {proxy}")
        try:
            r = requests.get(self.checker["url"], random_ua_headers(), proxies={"https": proxy}, timeout=self.timeout)
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

        log.debug(f"🪲 Answer: {r.text}")
        log.info(f"✅ Proxy is OK: {proxy}")

        return proxy

    def clean(self, max_workers=MAX_CHECK_WORKERS):
        # We can use a with statement to ensure threads are cleaned up promptly
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            proxies_clean = set()
            log.info(f"Checking if {len(self.proxies)} proxies given are working")
            # Start the load operations and mark each future with its URL
            future_proxies = {executor.submit(self._clean_proxy, proxy): proxy for proxy in self.proxies}
            for proxy in as_completed(future_proxies):
                if proxy.result():
                    proxies_clean.add(future_proxies[proxy])
                continue
        self.proxies = proxies_clean

    def is_proxy(self, ip, check_url=ISPROXY_URL):
        log.info(f"i Testing {ip}")
        try:
            r = requests.get(check_url.format(ip=ip), timeout=self.timeout)
        except requests.RequestException:
            return None

        r = r.json()

        if r["status"] != "success":
            log.warning(f"Failed to check: {ip}")
            return None
        if r["proxy"]:
            log.info(f"Proxy detected: {ip}")
            return True
        return False

    def verify(self, url: str = ISPROXY_URL_BATCH, max_proxy_batch: int = MAX_ISPROXY_BATCH) -> bool:
        """Keep only proxies undetected as proxy by the webservice URL

        Args:
            url (str, optional): Is Proxy Webservice. Defaults to ISPROXY_URL_BATCH.
            max_proxy_batch (int, optional): max by batch. Defaults to MAX_ISPROXY_BATCH.

        Returns:
            bool: success
        """
        ips = dict([p.removeprefix(f"{self.protocol}://").split(":") for p in self.proxies])
        ips_l = list(ips.keys())
        chunks = [ips_l[x : x + max_proxy_batch] for x in range(0, len(ips_l), max_proxy_batch)]
        chunk_i = 1
        log.debug(f"Start Batch Testing. Chunks: {len(chunks)}.")
        for chunk in chunks:
            log.debug(f"Batch testing. Chunk: {chunk_i}/{len(chunks)}")
            try:
                r = requests.post(url, data=str(chunk).replace("'", '"'), timeout=self.timeout)
            except requests.RequestException as e:
                log.error(f"Batch testing. Request Error: {e}")
                return None

            if not r.ok:
                log.error(f"Batch testing. HTTP Error: {r.text}")
                return None

            log.debug("🪲 Still {} requests in {} seconds".format(r.headers["X-Rl"], r.headers["X-Ttl"]))
            if int(r.headers["X-Rl"]) == 0:
                log.info(
                    f"Batch testing. Chunk: {chunk_i}/{len(chunks)}. Sleep: {r.headers['X-Ttl']}s before next chunk"
                )
                sleep(int(r.headers["X-Ttl"]))

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

    def load(self, filename: str = PROXIES_FILE, web: bool = True):
        """Load set of proxies from file or web if file is empty

        Args:
            filename (str, optional): filename. Defaults to PROXIES_FILE.
            web (bool, optional): loads from Web as fallback. Defaults to True (forced if file doesn't exist).
        """
        if not os.path.exists(filename):
            log.warning(f"File {filename} not found")
            if web:
                log.warning("Will load from Web")
                self.get()
            else:
                log.warning("Nothing to do, please add `--web` to pull from web")
            return
        with open(filename, "r+") as p:
            proxies = p.read().splitlines()
            if proxies:
                log.info(f"✅ {len(proxies)} proxies loaded from {filename}")
                self.proxies.update(proxies)
            elif web:
                log.warning(f"No proxies found in {filename}. Will load from Web")
                self.get()
            else:
                log.warning(f"No proxies found in {filename}")

    def save(self, filename: str = PROXIES_FILE):
        """Save list of proxies into file

        Args:
            filename (str, optional): filename. Defaults to PROXIES_FILE.
        """
        if self.proxies:
            with open(filename, "w") as f:
                return f.write("\n".join(self.proxies))

    def random(self):
        return {self.protocol: random.choice(list(self.proxies))}

    def refresh(self):
        self.load()
        self.verify()
        self.clean()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Proxy Miner - Mine and verify proxies from the web.")
    parser.add_argument(
        "proxies_file",
        nargs="?",
        default=PROXIES_FILE,
        help="The file to load/save the proxies. Default is 'proxies.txt'.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Load proxies from the web if the specified file is empty or not provided.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    log.remove(0)
    log.add(sys.stderr, level="INFO")

    args = parse_arguments()
    proxies_file = args.proxies_file

    pm = ProxyMiner()
    pm.load(proxies_file, args.web)
    pm.verify()
    pm.clean()
    log.debug(f"🪲 Proxies: {pm.proxies}")

    if not pm.proxies:
        sys.exit(1)

    pm.save(proxies_file)
    log.info(f"Random proxy: {pm.random()}")
