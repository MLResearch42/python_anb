#!/usr/bin/env python
"""Tests for the features added on top of the original pyanx API.

This work is made available under the Apache License, Version 2.0.
"""
import csv
import os
import tempfile
import unittest

import pyanx


class LayoutTest(unittest.TestCase):
    def _positions(self, **kwargs):
        chart = pyanx.Pyanx(**kwargs)
        chart.add_nodes([
            dict(entity_type='Person', label='Alice'),
            dict(entity_type='Person', label='Bob'),
            dict(entity_type='Person', label='Carol'),
            dict(entity_type='Person', label='Dave'),
        ])
        return chart._compute_positions()

    def test_random_layout_is_seeded(self):
        a = self._positions(layout='random', seed=42)
        b = self._positions(layout='random', seed=42)
        self.assertEqual(a, b)

    def test_grid_layout_is_deterministic(self):
        positions = self._positions(layout='grid')
        # 4 nodes -> 2x2 grid at spacing 150
        self.assertEqual(positions['Alice'], (0, 0))
        self.assertEqual(positions['Bob'], (150, 0))
        self.assertEqual(positions['Carol'], (0, 150))
        self.assertEqual(positions['Dave'], (150, 150))

    def test_unknown_layout_rejected(self):
        with self.assertRaises(ValueError):
            pyanx.Pyanx(layout='spiral')


class NodeIdTest(unittest.TestCase):
    def test_duplicate_labels_with_distinct_ids(self):
        chart = pyanx.Pyanx()
        chart.add_node(entity_type='Person', label='Alice')
        chart.add_node(entity_type='Person', label='Alice', node_id='alice2')
        self.assertEqual(2, len(chart.nodes))

    def test_node_requires_identity(self):
        chart = pyanx.Pyanx()
        with self.assertRaises(ValueError):
            chart.add_node(entity_type='Person')


class StrictValidationTest(unittest.TestCase):
    def test_dangling_edge_raises_in_strict_mode(self):
        chart = pyanx.Pyanx(strict=True)
        chart.add_node(label='A')
        chart.add_edge('A', 'B')  # B was never added
        with self.assertRaises(ValueError):
            chart.create(tempfile.mktemp(suffix='.anx'))

    def test_non_strict_allows_dangling_edge(self):
        chart = pyanx.Pyanx(strict=False)
        chart.add_node(label='A')
        chart.add_edge('A', 'B')
        path = chart.create(tempfile.mktemp(suffix='.anx'))
        self.assertTrue(os.path.exists(path))
        os.remove(path)


class CsvImportTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.nodes = os.path.join(self.dir, 'nodes.csv')
        self.edges = os.path.join(self.dir, 'edges.csv')
        with open(self.nodes, 'w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['id', 'label', 'entity_type'])
            writer.writerow(['1', 'Tyrion', 'Person'])
            writer.writerow(['2', 'Tywin', 'Person'])
        with open(self.edges, 'w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['source', 'sink', 'label'])
            writer.writerow(['2', '1', 'Father of'])

    def test_from_csv_builds_chart(self):
        chart = pyanx.Pyanx.from_csv(self.nodes, self.edges, layout='grid')
        self.assertEqual(2, len(chart.nodes))
        self.assertEqual(1, len(chart.edges))
        path = chart.create(os.path.join(self.dir, 'out.anx'))
        parsed = pyanx.anx.parse(path, silence=True)
        labels = [item.get_Label()
                  for item in parsed.get_ChartItemCollection()[0].get_ChartItem()]
        self.assertIn('Tyrion', labels)
        self.assertIn('Tywin', labels)


class CliTest(unittest.TestCase):
    def test_cli_round_trip(self):
        from pyanx.__main__ import main

        directory = tempfile.mkdtemp()
        nodes = os.path.join(directory, 'n.csv')
        out = os.path.join(directory, 'o.anx')
        with open(nodes, 'w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['id', 'label', 'entity_type'])
            writer.writerow(['1', 'Solo', 'Person'])

        exit_code = main(['--nodes', nodes, '-o', out, '--layout', 'circle'])
        self.assertEqual(0, exit_code)
        self.assertTrue(os.path.exists(out))


class NetworkxInteropTest(unittest.TestCase):
    def test_round_trip(self):
        try:
            import networkx as nx
        except ImportError:
            self.skipTest('networkx is not installed')

        graph = nx.DiGraph()
        graph.add_node('a', label='Alice', entity_type='Person')
        graph.add_node('b', label='Bob', entity_type='Person')
        graph.add_edge('a', 'b', label='knows')

        chart = pyanx.Pyanx.from_networkx(graph, seed=1)
        self.assertEqual(2, len(chart.nodes))
        self.assertEqual(1, len(chart.edges))

        restored = chart.to_networkx()
        self.assertEqual(2, restored.number_of_nodes())
        self.assertEqual(1, restored.number_of_edges())


if __name__ == '__main__':
    unittest.main()
