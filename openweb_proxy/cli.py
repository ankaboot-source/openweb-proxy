import argparse
import os

from openweb_proxy import config


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenWeb Proxy - generate working, fast and stealth proxy list - "
        + "#MakeTheWebOpenAgain\nCopyright ankaboot.io",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "proxies_file",
        nargs="?",
        default=config.PROXIES_FILE,
        help="The file to load/save the proxies. Default is 'proxies.txt'.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Load proxies from the web",
    )
    parser.add_argument(
        "--bench",
        action="store_true",
        help="Benchmark web sources for proxies, this option doesn't write to file",
    )
    parser.add_argument(
        "--protocol",
        choices=["https", "socks5"],
        help="""Protocol for the proxies.
        Choices: 'https' or 'socks5'. Default is 'socks5'.""",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="Timeout for requests in seconds. Default is 5 seconds.",
    )
    parser.add_argument(
        "--http",
        help="URL to check if a proxy is working. Default is 'https://google.com'.",
    )
    parser.add_argument(
        "--generic",
        help="host:port format server to check if reachable via proxy.",
    )
    parser.add_argument(
        "--verbose",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="""Set the verbosity level.
        Choose from INFO, DEBUG, WARNING, or ERROR. Default is INFO.""",
    )
    return parser.parse_args()
