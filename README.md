# OpenWeb Proxy 🌐

[![Release](https://img.shields.io/github/v/release/ankaboot-source/openweb-proxy)](https://img.shields.io/github/v/release/ankaboot-source/openweb-proxy)
[![Commit activity](https://img.shields.io/github/commit-activity/m/ankaboot-source/openweb-proxy)](https://img.shields.io/github/commit-activity/m/ankaboot-source/openweb-proxy)
[![License](https://img.shields.io/github/license/ankaboot-source/openweb-proxy)](https://img.shields.io/github/license/ankaboot-source/openweb-proxy)

Making the Web Open Again

- **Github repository**: <https://github.com/ankaboot-source/openweb-proxy/>
- **Documentation** <https://ankaboot-source.github.io/openweb-proxy/>

OpenWeb Proxy 🌐 is a powerful tool to generate clean and stealth socks5 proxies. It efficiently picks only fast (timeout), working with other protocols than HTTPs and not banned from tons of proxies public sources.


## Usage

For usage instructions and available options, run the following command:

```
python -m openweb-proxy --help
```

## Examples

Here are some examples of how to use OpenWeb proxy:

1. Download and check proxies from the web:
```sh
python -m openweb-proxy --web
```

2. Benchmark sources for proxies:

```sh
python -m openweb-proxy --bench
```

3. Load proxies from a file and verify them:

```sh
python -m openweb-proxy /path/to/proxies.txt
```

## License

OpenWeb Proxy is released under the AGPL-3.0 license. See the [LICENSE](/LICENSE) file for more details.

## Acknowledgements

OpenWeb Proxy uses proxies from various sources. You can find the list of sources in the [config.py](/openweb_proxy/config.py) file.

**Disclaimer:** OpenWeb Proxy comes with no warranty. The user is responsible for the usage and legitimacy of the proxies obtained using this software.

## ToDo:
[ ] Set-up publish to PyPi
[ ] Unit tests
[ ] Amplify current list of IP proxies to generate more proxies IPs
[ ] Replace SaaS Proxy detection tool with home-made
