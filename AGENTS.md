# AGENTS.md - openweb-proxy

## What this repo is

A smart and tiny tool to generate clean, stealth socks5 proxies. It loads proxies from public sources, checks speed and reachability, filters out banned ones, and writes surviving proxies to a file. Built with Python 3.10+ (hatch).

## How to run it

Canonical invocation:

```sh
hatch run python -m openweb_proxy --timeout 15 --web ../proxylist.txt
```

The README documents `python -m openweb-proxy --help`, `--web`, `--bench`, and a positional proxies file. **Stale README note:** those examples use a hyphen (`openweb-proxy`), but the actual module directory is `openweb_proxy` (underscore). The correct module name is `openweb_proxy`. Real invocations:

```sh
python -m openweb_proxy --help
python -m openweb_proxy --web
python -m openweb_proxy --bench
python -m openweb_proxy /path/to/proxies.txt
```

`pyproject.toml` has no `[project.scripts]` entry point, so the module invocation is the only way to run the tool.

## Output contract

The tool writes a plain-text file with one proxy per line in `<protocol>://<host>:<port>` form (default protocol `socks5`, e.g. `socks5://127.0.0.1:1080`). The filename comes from the positional `proxies_file` argument. Default in `openweb_proxy/config.py` is `proxies.txt`. Pass an explicit output path; callers commonly write outside the repo.

## Hard rules

- Do not commit generated proxy lists (`proxylist.txt`, `proxylist.json`, or anything containing generated proxies). They are runtime artifacts.
- Do not change CLI flags or the output format without a major bump and a README usage note.
