# pyanx

[![CI](https://github.com/MLResearch42/python_anb/actions/workflows/ci.yml/badge.svg)](https://github.com/MLResearch42/python_anb/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

**Generate IBM i2 Analyst's Notebook charts from Python.**

`pyanx` is a small, dependency-free library for building entity/link charts and
exporting them to the **ANX** (Analyst's Notebook XML) format. You describe a
graph of entities and the relationships between them in a few lines of Python,
and `pyanx` writes a `.anx` file that opens directly in Analyst's Notebook.

The output is tested against **i2 Chart Reader 8** — the free, read-only viewer
for Analyst's Notebook charts.

<div align="center"><img src="test/anb_integration.png" width="600" alt="Example chart rendered in Analyst's Notebook"/></div>

---

## Contents

- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Command-line interface](#command-line-interface)
- [Building charts from CSV](#building-charts-from-csv)
- [NetworkX interoperability](#networkx-interoperability)
- [Layouts](#layouts)
- [Dates, timezones and styling](#dates-timezones-and-styling)
- [API reference](#api-reference)
- [Development](#development)
- [License & credits](#license--credits)

---

## Features

- **Simple API** — add nodes and edges, then call `create()`.
- **Reproducible layouts** — `random` (seedable), `grid`, or `circle`.
- **Custom node IDs** — let several nodes share a display label.
- **Validation** — optional `strict` mode catches links to undefined nodes.
- **CSV import** — turn node/edge spreadsheets into a chart in one call.
- **NetworkX bridge** — convert to/from `networkx` graphs.
- **CLI** — `python -m pyanx` converts CSV files to `.anx` with no code.
- **Zero required dependencies**, runs on **Python 3.7+**.

## Installation

```bash
pip install .
```

Or, with the optional NetworkX integration and developer tooling:

```bash
pip install ".[networkx]"   # adds networkx
pip install ".[dev]"        # adds networkx + pytest
```

## Quickstart

```python
import pyanx

chart = pyanx.Pyanx()

tyrion = chart.add_node(entity_type='Person', label='Tyrion')
tywin  = chart.add_node(entity_type='Person', label='Tywin')
jaime  = chart.add_node(entity_type='Person', label='Jaime')
cersei = chart.add_node(entity_type='Woman',  label='Cersei')

chart.add_edge(tywin,  tyrion, 'Father of')
chart.add_edge(jaime,  tyrion, 'Brother of')
chart.add_edge(cersei, tyrion, 'Sister of')

chart.create('demo.anx')
```

Open `demo.anx` in Analyst's Notebook or i2 Chart Reader.

`add_node` returns the node's id, which you pass to `add_edge`. By default the
id is the node's `label`.

## Command-line interface

Convert CSV files to a chart without writing any Python:

```bash
python -m pyanx --nodes people.csv --edges relations.csv -o chart.anx
# or, after `pip install`, simply:
pyanx --nodes people.csv --edges relations.csv -o chart.anx
```

| Option | Description |
| --- | --- |
| `--nodes CSV` | Nodes file (required). |
| `--edges CSV` | Edges file (optional). |
| `-o, --output ANX` | Output path (required). |
| `--layout {random,grid,circle}` | Node positioning (default: `random`). |
| `--seed N` | Seed the random layout for reproducible output. |
| `--strict` | Fail if a link references an undefined node. |
| `--no-pretty` | Emit compact XML. |

## Building charts from CSV

```python
chart = pyanx.Pyanx.from_csv('people.csv', 'relations.csv', layout='grid')
chart.create('chart.anx')
```

**`people.csv`** — at least one of `id`/`label` is required:

```csv
id,label,entity_type,description
1,Tyrion,Person,Hand of the King
2,Tywin,Person,Head of House Lannister
3,Cersei,Woman,Queen
```

Also recognised: `ring_color`, `datestr`, `datestr_description`, `timezone`.

**`relations.csv`**:

```csv
source,sink,label
2,1,Father of
3,1,Sister of
```

Column aliases are accepted: `from`/`to`/`target` for edge endpoints, and
`type` for `entity_type`.

## NetworkX interoperability

```python
import networkx as nx
import pyanx

g = nx.DiGraph()
g.add_node('tyrion', label='Tyrion', entity_type='Person')
g.add_node('tywin',  label='Tywin',  entity_type='Person')
g.add_edge('tywin', 'tyrion', label='Father of')

chart = pyanx.Pyanx.from_networkx(g, layout='circle', seed=1)
chart.create('chart.anx')

# ...and back again
graph = chart.to_networkx()
```

NetworkX is an optional dependency (`pip install ".[networkx]"`).

## Layouts

Node positions are computed when you call `create()`:

- `random` *(default)* — random positions; pass `seed=` for reproducibility.
- `grid` — nodes arranged on a square grid (deterministic).
- `circle` — nodes evenly spaced around a circle (deterministic).

```python
chart = pyanx.Pyanx(layout='grid', seed=42)
```

## Dates, timezones and styling

```python
chart = pyanx.Pyanx()

meeting = chart.add_node(
    entity_type='Event',
    label='Meeting',
    ring_color=255,                       # red ring around the icon
    datestr='2014-05-14T10:46:00',
    datestr_description='First contact',
    timezone='UTC',
)

chart.add_edge(
    'Alice', meeting,
    label='Attended',
    style='Dashed',                       # 'Solid' (default) or 'Dashed'
    color=16711680,
    datestr='2014-05-14T10:46:00',
)
```

## API reference

### `Pyanx(ring_margin=5, layout='random', seed=None, strict=False)`
Create a chart builder. `layout` is one of `'random'`, `'grid'`, `'circle'`;
`seed` makes the random layout reproducible; `strict=True` makes `create()`
raise if any link references an undefined node.

### `add_node(entity_type='Anon', label=None, ring_color=None, description='', datestr=None, datestr_description=None, dateformat='%Y-%m-%dT%H:%M:%S', timezone=None, node_id=None) -> id`
Add an entity and return its id (defaults to `label`). Provide `node_id` to give
nodes distinct identities even when they share a label.

### `add_edge(source, sink, label='', color=0, style='Solid', description='', datestr=None, datestr_description=None, dateformat='%Y-%m-%dT%H:%M:%S', timezone=None)`
Add a directed link between two node ids.

### `add_nodes(nodes)` / `add_edges(edges)`
Bulk variants taking iterables of keyword-argument dicts.

### `create(path, pretty=True, encoding='utf8') -> path`
Serialize the chart to `path` and return it.

### `Pyanx.from_csv(nodes_path, edges_path=None, **kwargs)` *(classmethod)*
Build a chart from CSV files. Extra keyword arguments are forwarded to the
constructor.

### `Pyanx.from_networkx(graph, ...)` *(classmethod)* / `to_networkx()`
Convert between `pyanx` charts and `networkx` graphs.

## Development

Run the test suite:

```bash
python -m pytest            # if pytest is installed
# or, with no extra dependencies:
PYTHONPATH=. python test/pyanx_test.py
PYTHONPATH=. python test/features_test.py
```

The bindings in `pyanx/anx.py` are generated from the ANX XML schema with
[`generateDS`](https://pypi.org/project/generateDS/); the hand-written API
lives in `pyanx/pyanx.py`.

## License & credits

Licensed under the [Apache License 2.0](LICENSE).

Originally created by **Petter Chr. Bjelland** (petter.bjelland@gmail.com).
*Analyst's Notebook* and *i2* are trademarks of their respective owners; this
project is not affiliated with or endorsed by IBM.
