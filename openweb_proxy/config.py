import re
from bs4 import BeautifulSoup
from loguru import logger as log
import requests
from .random_ua_headers import random_ua_headers

PROXIES_FILE = "proxies.txt"
ISPROXY_URL = "http://ip-api.com/json/{ip}?fields=status,proxy"
ISPROXY_URL_BATCH = "http://ip-api.com/batch?fields=status,proxy,query"
MAX_ISPROXY_BATCH = 100
CHECK_URLS = {
    "url": "https://google.com",
    "generic": "smtp.freesmtpservers.com:25",
    "banned": "https://raw.githubusercontent.com/ankaboot-source/\
email-open-data/main/mailserver-banned-ips.txt",
}
CHECK_MAX = 100
MAX_CHECK_WORKERS = 20
PROXY_PROTOCOL = "socks5"
DEFAULT_PROXY = "https://localhost:3128"
TIMEOUT = 5
SOURCE_TIMEOUT = 20
MAX_WORKERS = 10

RE_URL = re.compile(r"^https?://", re.IGNORECASE)
RE_IP_V4 = re.compile(
    r"(?:^|\D)(({0}\.{1}\.{1}\.{1}):{2})(?!.)".format(
        r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])",  # 1-255
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])",  # 0-255
        r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
        + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])",  # 0-65535
    )
)


def _get_sslproxies(timeout: int = 0) -> set[str]:
    """Get HTTPS proxies from sslproxies.org"""
    r = requests.get(
        "https://www.sslproxies.org/", random_ua_headers(), timeout=timeout
    )
    soup = BeautifulSoup(r.text, "html.parser")
    proxies_table = soup.find("table", class_="table-striped").tbody

    proxies = set()
    for row in proxies_table.find_all("tr"):
        proxy = row.find_all("td")
        ip = proxy[0].string
        port = proxy[1].string
        proxies.add(f"https://{ip}:{port}")
    log.debug(f"🪲 Proxies sslproxies number: {len(proxies)}")
    return proxies


def _get_clarketm(timeout: int = 0) -> set[str]:
    """Get HTTPS proxies from clarketm on github"""
    r = requests.get(
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt",
        timeout=timeout,
    )
    proxies = set()
    for proxy_l in r.text.splitlines()[6:-2]:
        if "S" in proxy_l:
            proxies.add(f"https://{proxy_l.split()[0]}")
    log.debug(f"🪲 Proxies clarketm number: {len(proxies)}")
    return proxies


def get_geonde_proxies(timeout: int) -> set[str]:
    """Downloads proxies from https://geonode.com/free-proxy-list"""
    proxies, i = set(), 1
    while True:
        try:
            r = requests.get(
                f"https://proxylist.geonode.com/api/proxy-list?limit=500\
&page={i}&sort_by=lastChecked&sort_type=desc",
                timeout=timeout,
            )
            data = r.json()["data"]
        except requests.exceptions.RequestException as e:
            log.info(f"Genode Proxies stopped at page {i} with exception: {e}")
            data = ""
        if not data:
            break
        for element in data:
            ip, port = element["ip"], element["port"]
            proxies.add(f"socks5://{ip}:{port}")
        i += 1
    return proxies


PROXY_SOURCES: dict[str, list] = {
    "https": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://spys.me/proxy.txt",
        _get_sslproxies,
        _get_clarketm,
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
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/\
online-proxies/txt/proxies-socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
        "https://openproxy.space/list/socks5",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/\
socks5.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&\
protocol=socks5&timeout=10000&country=all&simplified=true",
        "https://spys.me/socks.txt",
        get_geonde_proxies,
    ],
}
