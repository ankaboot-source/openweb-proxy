import argparse
import os

from __about__ import (
    __title__,
    __description__
)

from openweb_proxy import config


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the OpenWeb Proxy application.

    This function sets up and configures the argument parser for the OpenWeb Proxy
    application. It defines command-line options related to proxy mining, loading,
    and benchmarking. The parsed arguments are returned as a namespace object.

    :return: argparse.Namespace - A namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=f"{__title__} - {__description__}",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "proxies_file",
        nargs="?",
        default=config.PROXIES_FILE,
        help=f"The file to load/save the proxies. Default is '{config.PROXIES_FILE }'.",
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
        help=f"Timeout for requests in seconds. Default is {config.TIMEOUT} seconds.",
    )
    HTTP_HOST = config.CHECK_URLS["url"]
    parser.add_argument(
        "--http",
        help=f"URL to check if a proxy is working. Default is '{HTTP_HOST}'.",
    )
    GENERIC_HOST = config.CHECK_URLS["generic"]
    parser.add_argument(
        "--generic",
        help=f"""host:port format server to check if reachable via proxy.
        Defaults to {GENERIC_HOST}.""",
    )
    parser.add_argument(
        "--verbose",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="""Set the verbosity level.
        Choose from INFO, DEBUG, WARNING, or ERROR. Default is INFO.
        This can also be set using the LOG_LEVEL env var.""",
    )
    parser.add_argument(
        "--banned",
        help="""URL or FILE of exluded addresses""",
    )
    return parser.parse_args()
