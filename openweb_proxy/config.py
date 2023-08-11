from typing import Any, Dict, List, Set

import requests

PROXIES_FILE = "proxies.txt"
PROXY_FILE = "proxy.txt"
ISPROXY_URL = "http://ip-api.com/json/{ip}?fields=status,proxy"
ISPROXY_URL_BATCH = "http://ip-api.com/batch?fields=status,proxy,query"
MAX_ISPROXY_BATCH = 100
CHECK_URL = {
    "url": "https://google.com",
    "g-server": "smtp.freesmtpservers.com",
    "g-port": 25,
}
CHECK_MAX = 100
MAX_CHECK_WORKERS = 20
PROXY_PROTOCOL = "socks5"
DEFAULT_PROXY = "https://localhost:3128"
TIMEOUT = 5
MAX_WORKERS = 10

BANNED_URL = "https://raw.githubusercontent.com/ankaboot-source/email-open-data/main/mailserver-banned-ips.txt"


def get_geonde_proxies(timeout: int) -> Set[str]:
    """Downloads proxies from https://geonode.com/free-proxy-list"""
    proxies, i = set(), 1
    while True:
        r = requests.get(
            f"https://proxylist.geonode.com/api/proxy-list?limit=500&page={i}&sort_by=lastChecked&sort_type=desc",
            timeout=timeout,
        )
        data = r.json()["data"]
        if not data:
            break
        for element in data:
            ip, port = element["ip"], element["port"]
            proxies.add(f"socks5://{ip}:{port}")
        i += 1
    return proxies


PROXY_SOURCES: Dict[str, List[Any]] = {
    "https": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://spys.me/proxy.txt",
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
        "https://openproxy.space/list/socks5",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/socks5.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all&simplified=true",
        "https://spys.me/socks.txt",
        get_geonde_proxies,
    ],
}
