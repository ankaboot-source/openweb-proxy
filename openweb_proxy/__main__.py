#!/bin/env python3
# Copyright 2022 Badreddine LEJMI.
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys

from loguru import logger as log

from .cli import parse_arguments
from .proxy_miner import ProxyMiner
import openweb_proxy.config as config


def main() -> None:
    args = parse_arguments()

    log.remove(0)
    log.add(sys.stderr, level=args.verbose)

    proxies_file = args.proxies_file

    pm_kwargs = {}

    if args.protocol:
        pm_kwargs["protocol"] = args.protocol
    if args.timeout:
        pm_kwargs["timeout"] = args.timeout

    checker = {}
    if args.generic_check:
        checker = config.checker

    if args.http_checker:
        checker["http"] = args.checker
    if args.generic_checker_server:
        checker["g-server"] = args.generic_checker_server
    if args.generic_checker_port:
        checker["g-port"] = args.generic_checker_port

    if checker:
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
