#!/usr/bin/env python
"""Command-line interface for pyanx.

Convert CSV node/edge files into an Analyst's Notebook ``.anx`` chart::

    python -m pyanx --nodes people.csv --edges relations.csv -o chart.anx

See ``Pyanx.from_csv`` for the recognised CSV columns.
"""
from __future__ import annotations

import argparse
import sys

from . import LAYOUTS, Pyanx, __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='pyanx',
        description='Generate an Analyst\'s Notebook (.anx) chart from CSV files.')
    parser.add_argument('--nodes', required=True, metavar='CSV',
                        help='CSV file describing the entities (nodes).')
    parser.add_argument('--edges', metavar='CSV',
                        help='Optional CSV file describing the links (edges).')
    parser.add_argument('-o', '--output', required=True, metavar='ANX',
                        help='Path to write the generated .anx chart.')
    parser.add_argument('--layout', choices=LAYOUTS, default='random',
                        help='Node positioning strategy (default: random).')
    parser.add_argument('--seed', type=int, default=None,
                        help='Seed for the random layout (reproducible output).')
    parser.add_argument('--strict', action='store_true',
                        help='Fail if a link references an undefined node.')
    parser.add_argument('--no-pretty', dest='pretty', action='store_false',
                        help='Write compact XML instead of indented output.')
    parser.add_argument('--version', action='version',
                        version='pyanx %s' % __version__)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        chart = Pyanx.from_csv(
            args.nodes, args.edges,
            layout=args.layout, seed=args.seed, strict=args.strict)
        chart.create(args.output, pretty=args.pretty)
    except (OSError, ValueError) as error:
        print('pyanx: error: %s' % error, file=sys.stderr)
        return 1

    print('Wrote %s (%d entities, %d links)'
          % (args.output, len(chart.nodes), len(chart.edges)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
