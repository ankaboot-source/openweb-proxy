#!/bin/env python3
# Copyright 2022 Badreddine LEJMI.
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys

from loguru import logger as log

from openweb_proxy import config
from .cli import parse_arguments
from .proxy_miner import ProxyMiner


def main() -> None:
    """
    Entry point for the proxy miner application.

    This function is the main entry point for the proxy miner application. It
    reads command-line arguments, initializes the ProxyMiner instance with
    appropriate configurations, performs benchmarking, loading, verification,
    and cleaning of proxies, and provides information about the mined proxies.

    :return: None
    """
    args = parse_arguments()

    log.remove(0)
    log.add(sys.stderr, level=args.verbose)

    proxies_file = args.proxies_file

    pm_kwargs = {}

    if args.protocol:
        pm_kwargs["protocol"] = args.protocol
    if args.timeout:
        pm_kwargs["timeout"] = args.timeout

    checker = config.CHECK_URLS
    if args.http:
        checker["http"] = args.http
    if args.generic:
        checker["generic"] = args.generic
    if args.banned:
        checker["banned"] = args.banned

    pm_kwargs["checker"] = checker

    pm = ProxyMiner(**pm_kwargs)
    if args.bench:
        pm.benchmark_sources()
        sys.exit()
    pm.load(proxies_file, args.web)
    pm.verify()
    pm.clean()
    log.debug(f"🪲 Proxies: {pm.proxies}")

    if not pm.proxies:
        sys.exit(1)

    pm.save(proxies_file)
    log.info(f"Random proxy: {pm.random()}")


if __name__ == "__main__":
    main()
