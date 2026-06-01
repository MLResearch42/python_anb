# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0]

### Added
- Custom node identifiers via `add_node(node_id=...)`, allowing multiple nodes
  to share the same display label.
- Bulk helpers `add_nodes()` and `add_edges()`.
- Pluggable, reproducible node layouts (`layout="random"|"grid"|"circle"`) with
  an optional `seed` for deterministic output.
- Optional `strict` mode that validates every link references a known node.
- `Pyanx.from_csv()` to build charts from node/edge CSV files.
- `Pyanx.from_networkx()` / `to_networkx()` interoperability (optional
  `networkx` dependency).
- A command-line interface: `python -m pyanx` (and a `pyanx` console script).
- Type hints and docstrings across the public API.
- `pyproject.toml` packaging, an Apache-2.0 `LICENSE` file, expanded test
  suite, and GitHub Actions CI.

### Changed
- `create()` now returns the written path.

### Fixed
- **Python 3 support.** The previously Python 2-only generated bindings and API
  now run on Python 3.7+ (exception syntax, `print`, `basestring`,
  `dict.iteritems`, `StringIO`, package-relative imports, and the
  `.encode(ExternalEncoding)` output corruption).

## [0.2.0]
- Circle frames, link styles, multi-links, descriptions and datetimes.
- UTF-8 as the default export encoding.

## [0.1.0]
- Initial release.
