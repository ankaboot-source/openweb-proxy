import argparse

from openweb_proxy import config


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Proxy Miner - Mine and verify proxies from the web.")
    parser.add_argument(
        "proxies_file",
        nargs="?",
        default=config.PROXIES_FILE,
        help="The file to load/save the proxies. Default is 'proxies.txt'.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Load proxies from the web if the specified file is empty or not provided.",
    )
    parser.add_argument(
        "--bench",
        action="store_true",
        help="Benchmark web sources for proxies, this option doesn't write to file",
    )
    parser.add_argument(
        "--verbose",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the verbosity level. Choose from INFO, DEBUG, WARNING, or ERROR. Default is INFO.",
    )
    return parser.parse_args()
