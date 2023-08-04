# OpenWeb Proxy 🌐

[![Release](https://img.shields.io/github/v/release/ankaboot-source/openweb-proxy)](https://img.shields.io/github/v/release/ankaboot-source/openweb-proxy)
[![Build status](https://img.shields.io/github/actions/workflow/status/ankaboot-source/openweb-proxy/main.yml?branch=main)](https://github.com/ankaboot-source/openweb-proxy/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/ankaboot-source/openweb-proxy/branch/main/graph/badge.svg)](https://codecov.io/gh/ankaboot-source/openweb-proxy)
[![Commit activity](https://img.shields.io/github/commit-activity/m/ankaboot-source/openweb-proxy)](https://img.shields.io/github/commit-activity/m/ankaboot-source/openweb-proxy)
[![License](https://img.shields.io/github/license/ankaboot-source/openweb-proxy)](https://img.shields.io/github/license/ankaboot-source/openweb-proxy)

Making the Web Open Again

- **Github repository**: <https://github.com/ankaboot-source/openweb-proxy/>
- **Documentation** <https://ankaboot-source.github.io/openweb-proxy/>

OpenWeb Proxy 🌐 is a powerful tool for downloading and checking proxies from various sources. It efficiently produces a small list of working and efficient proxies from a larger list.

## Installation

To install OpenWeb Proxy, simply use pip:

```sh
pip install https://github.com/ankaboot-source/openweb-proxy
```

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


## Contributing

Contributions to OpenWeb Proxy are welcome! If you'd like to contribute, please follow these guidelines:

1. Fork the repository and create a new branch and clone it locally.
2. Make sure you have `poetry` and `cookiecutter` installed.
3. Run `make install` to setup the environment and the pre-commit hooks.
4. Make your changes and test them thoroughly.
5. Submit a pull request with a clear description of your changes.

## License

OpenWeb Proxy is released under the AGPL-3.0 license. See the [LICENSE](/LICENSE) file for more details.

## Acknowledgements

OpenWeb Proxy uses proxies from various sources. You can find the list of sources in the [config.py](/openweb_proxy/config.py) file.

**Disclaimer:** OpenWeb Proxy comes with no warranty. The user is responsible for the usage and legitimacy of the proxies obtained using this software.

## ToDo:
Finalizing the set-up for publishing to PyPi or Artifactory, see
[here](https://fpgmaas.github.io/cookiecutter-poetry/features/publishing/#set-up-for-pypi).
Enabling the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/codecov/).

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
