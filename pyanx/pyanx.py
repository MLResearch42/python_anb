#!/usr/bin/env python
"""High-level builder for IBM i2 Analyst's Notebook ANX chart files.

This work is made available under the Apache License, Version 2.0.

You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
"""
from __future__ import annotations

import csv
import datetime
import math
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import anx

__author__ = 'Petter Chr. Bjelland (petter.bjelland@gmail.com)'

#: Default ``strptime``/``strftime`` pattern used to parse ``datestr`` values.
DEFAULT_DATEFORMAT = '%Y-%m-%dT%H:%M:%S'

#: Supported automatic layout strategies for positioning nodes.
LAYOUTS = ('random', 'grid', 'circle')


class Pyanx(object):
    """Build an Analyst's Notebook chart and export it to the ANX format.

    Nodes and links are accumulated in memory and serialized to an ``.anx``
    file by :meth:`create`. Nodes are identified by an ``id`` (which defaults
    to the node's ``label``); links reference nodes by that id.

    Args:
        ring_margin: Margin used when drawing a coloured ring around a node.
        layout: Strategy used to position nodes on the chart. One of
            ``"random"`` (default), ``"grid"`` or ``"circle"``.
        seed: Optional seed for the random layout, making output reproducible.
        strict: When ``True``, :meth:`create` raises ``ValueError`` if any link
            references a node that was never added.
    """

    def __init__(self, ring_margin: int = 5, layout: str = 'random',
                 seed: Optional[int] = None, strict: bool = False):
        if layout not in LAYOUTS:
            raise ValueError(
                'unknown layout %r; choose one of %s' % (layout, ', '.join(LAYOUTS)))

        self.entity_types: Dict[str, bool] = {}
        self.edges: List[Tuple[Any, Any, Dict[str, Any]]] = []
        self.nodes: Dict[Any, Dict[str, Any]] = {}
        self.timezones: Dict[str, int] = {}
        self.ring_margin = ring_margin
        self.layout = layout
        self.strict = strict
        self._rng = random.Random(seed)

    def add_node(self, entity_type: str = 'Anon', label: Optional[str] = None,
                 ring_color: Optional[int] = None, description: str = '',
                 datestr: Optional[str] = None,
                 datestr_description: Optional[str] = None,
                 dateformat: str = DEFAULT_DATEFORMAT,
                 timezone: Optional[str] = None,
                 node_id: Optional[Any] = None) -> Any:
        """Add an entity (node) to the chart and return its id.

        Args:
            entity_type: Entity/icon type, e.g. ``"Person"``.
            label: Text shown beside the icon. Also the default node id.
            ring_color: Optional integer colour for a ring drawn around the icon.
            description: Free-text description attached to the entity.
            datestr: Optional date/time string parsed using ``dateformat``.
            datestr_description: Optional label for the date/time.
            dateformat: ``strptime`` pattern used to parse ``datestr``.
            timezone: Optional timezone name associated with the date/time.
            node_id: Explicit id for the node. Defaults to ``label``. Use this
                when several nodes share the same label.

        Returns:
            The node id, suitable for passing to :meth:`add_edge`.
        """
        current_id = node_id if node_id is not None else label

        if current_id is None:
            raise ValueError("add_node requires a 'label' or an explicit 'node_id'")

        if timezone and timezone not in self.timezones:
            self.timezones[timezone] = len(self.timezones)

        if entity_type not in self.entity_types:
            self.entity_types[entity_type] = True

        if datestr:
            _datetime = datetime.datetime.strptime(datestr, dateformat)
        else:
            _datetime = None

        self.nodes[current_id] = {
            'id': current_id,
            'entity_type': entity_type,
            'label': label if label is not None else str(current_id),
            'ring_color': ring_color,
            'description': description,
            'datetime': _datetime,
            'datetime_description': datestr_description,
            'timezone': timezone
        }

        return current_id

    def add_nodes(self, nodes: Iterable[Dict[str, Any]]) -> List[Any]:
        """Add several nodes at once.

        Args:
            nodes: An iterable of keyword-argument dicts for :meth:`add_node`.

        Returns:
            The list of created node ids.
        """
        return [self.add_node(**node) for node in nodes]

    def add_edge(self, source: Any, sink: Any, label: str = '', color: int = 0,
                 style: str = 'Solid', description: str = '',
                 datestr: Optional[str] = None,
                 datestr_description: Optional[str] = None,
                 dateformat: str = DEFAULT_DATEFORMAT,
                 timezone: Optional[str] = None) -> None:
        """Add a directed link between two nodes.

        Args:
            source: Id of the originating node (as returned by :meth:`add_node`).
            sink: Id of the destination node.
            label: Text shown on the link.
            color: Integer line colour.
            style: Link strength/style, e.g. ``"Solid"`` or ``"Dashed"``.
            description: Free-text description attached to the link.
            datestr: Optional date/time string parsed using ``dateformat``.
            datestr_description: Optional label for the date/time.
            dateformat: ``strptime`` pattern used to parse ``datestr``.
            timezone: Optional timezone name associated with the date/time.
        """
        if datestr:
            _datetime = datetime.datetime.strptime(datestr, dateformat)
        else:
            _datetime = None

        if timezone and timezone not in self.timezones:
            self.timezones[timezone] = len(self.timezones)

        self.edges.append((source, sink, {
            'label': label,
            'color': color,
            'style': style,
            'description': description,
            'datetime': _datetime,
            'datetime_description': datestr_description,
            'timezone': timezone
        }))

    def add_edges(self, edges: Iterable[Dict[str, Any]]) -> None:
        """Add several links at once.

        Args:
            edges: An iterable of keyword-argument dicts for :meth:`add_edge`.
                Each dict must contain ``source`` and ``sink`` keys.
        """
        for edge in edges:
            self.add_edge(**edge)

    def _validate(self) -> None:
        """Ensure every link references a known node; raise otherwise."""
        missing = set()
        for source, sink, _ in self.edges:
            if source not in self.nodes:
                missing.add(source)
            if sink not in self.nodes:
                missing.add(sink)

        if missing:
            raise ValueError(
                'the following link endpoints are not defined as nodes: %s'
                % ', '.join(repr(m) for m in sorted(missing, key=str)))

    def _compute_positions(self) -> Dict[Any, Tuple[int, int]]:
        """Return an ``id -> (x, y)`` mapping based on :attr:`layout`."""
        ids = list(self.nodes.keys())
        count = len(ids)
        positions: Dict[Any, Tuple[int, int]] = {}

        if self.layout == 'grid':
            cols = max(1, int(math.ceil(math.sqrt(count))))
            spacing = 150
            for index, node_id in enumerate(ids):
                positions[node_id] = (
                    (index % cols) * spacing, (index // cols) * spacing)
        elif self.layout == 'circle':
            radius = max(150, count * 30)
            for index, node_id in enumerate(ids):
                angle = 2 * math.pi * index / max(1, count)
                positions[node_id] = (
                    int(radius + radius * math.cos(angle)),
                    int(radius + radius * math.sin(angle)))
        else:  # random
            for node_id in ids:
                positions[node_id] = (
                    self._rng.randint(0, 1000), self._rng.randint(0, 1000))

        return positions

    def __add_entity_types(self, chart):
        entity_type_collection = anx.EntityTypeCollection()

        for entity_type in self.entity_types:
            entity_type_collection.add_EntityType(anx.EntityType(Name=entity_type, IconFile=entity_type))

        chart.add_EntityTypeCollection(entity_type_collection)

    def __add_link_types(self, chart):
        link_type_collection = anx.LinkTypeCollection()
        link_type_collection.add_LinkType(anx.LinkType(Name="Link"))
        chart.add_LinkTypeCollection(link_type_collection)

    def __set_date(self, chart_item, data):
        if not data['datetime']:
            return

        chart_item.set_DateTime(data['datetime'])

        if data['timezone']:
            chart_item.set_TimeZone(anx.TimeZone(data['timezone'], UniqueID=self.timezones[data['timezone']]))

        chart_item.set_DateTimeDescription(data['datetime_description'])
        chart_item.set_DateSet(True)
        chart_item.set_TimeSet(True)

    def __add_entities(self, chart, positions):
        chart_item_collection = anx.ChartItemCollection()

        for data in self.nodes.values():
            circle = None

            if data['ring_color']:
                circle = anx.FrameStyle(Colour=data['ring_color'], Visible=1, Margin=self.ring_margin)

            x, y = positions[data['id']]

            icon = anx.Icon(IconStyle=anx.IconStyle(Type=data['entity_type'], FrameStyle=circle))
            entity = anx.Entity(Icon=icon, EntityId=data['id'], Identity=data['id'])
            chart_item = anx.ChartItem(XPosition=x, Label=data['label'], End=anx.End(X=x, Y=y, Entity=entity), Description=data['description'])

            self.__set_date(chart_item, data)

            chart_item_collection.add_ChartItem(chart_item)

        chart.add_ChartItemCollection(chart_item_collection)

    def __add_links(self, chart):
        chart_item_collection = anx.ChartItemCollection()

        for source, sink, data in self.edges:
            link_style = anx.LinkStyle(StrengthReference=data['style'], Type='Link', ArrowStyle='ArrowOnHead', LineColour=data['color'], MlStyle="MultiplicityMultiple")
            link = anx.Link(End1Id=source, End2Id=sink, LinkStyle=link_style)

            chart_item = anx.ChartItem(Label=data['label'], Link=link, Description=data['description'])

            self.__set_date(chart_item, data)

            chart_item_collection.add_ChartItem(chart_item)

        chart.add_ChartItemCollection(chart_item_collection)

    def create(self, path: str, pretty: bool = True, encoding: str = 'utf8') -> str:
        """Serialize the chart and write it to ``path``.

        Args:
            path: Destination file path for the ``.anx`` chart.
            pretty: Whether to pretty-print (indent) the XML.
            encoding: Text encoding used to write the file.

        Returns:
            The ``path`` that was written, for convenience.
        """
        if self.strict:
            self._validate()

        positions = self._compute_positions()

        chart = anx.Chart(IdReferenceLinking=False)
        chart.add_StrengthCollection(anx.StrengthCollection([
            anx.Strength(DotStyle="DotStyleDashed", Name="Dashed", Id="Dashed"),
            anx.Strength(DotStyle="DotStyleSolid", Name="Solid", Id="Solid")
        ]))

        self.__add_entity_types(chart)
        self.__add_link_types(chart)
        self.__add_entities(chart, positions)
        self.__add_links(chart)

        with open(path, 'w', encoding=encoding) as output_file:
            chart.export(output_file, 0, pretty_print=pretty, namespacedef_=None)

        return path

    # ------------------------------------------------------------------
    # Interoperability helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_csv(cls, nodes_path: str, edges_path: Optional[str] = None,
                 **kwargs) -> 'Pyanx':
        """Build a chart from one or two CSV files.

        The *nodes* file must have a header row. Recognised columns are
        ``id``/``label`` (at least one is required), ``entity_type``/``type``,
        ``description``, ``ring_color``, ``datestr``, ``datestr_description``
        and ``timezone``. The optional *edges* file recognises
        ``source``/``from``, ``sink``/``to``/``target``, ``label``, ``style``,
        ``color`` and ``description``.

        Args:
            nodes_path: Path to the nodes CSV file.
            edges_path: Optional path to the edges CSV file.
            **kwargs: Forwarded to the :class:`Pyanx` constructor.

        Returns:
            A populated :class:`Pyanx` instance.
        """
        chart = cls(**kwargs)

        with open(nodes_path, newline='') as handle:
            for row in csv.DictReader(handle):
                label = (row.get('label') or row.get('id') or '').strip()
                node_id = (row.get('id') or row.get('label') or '').strip()
                ring = row.get('ring_color')
                chart.add_node(
                    entity_type=(row.get('entity_type') or row.get('type') or 'Anon').strip(),
                    label=label,
                    node_id=node_id,
                    description=(row.get('description') or '').strip(),
                    ring_color=int(ring) if ring not in (None, '') else None,
                    datestr=(row.get('datestr') or None),
                    datestr_description=(row.get('datestr_description') or None),
                    timezone=(row.get('timezone') or None),
                )

        if edges_path:
            with open(edges_path, newline='') as handle:
                for row in csv.DictReader(handle):
                    color = row.get('color')
                    chart.add_edge(
                        (row.get('source') or row.get('from') or '').strip(),
                        (row.get('sink') or row.get('to') or row.get('target') or '').strip(),
                        label=(row.get('label') or '').strip(),
                        style=(row.get('style') or 'Solid').strip(),
                        color=int(color) if color not in (None, '') else 0,
                        description=(row.get('description') or '').strip(),
                    )

        return chart

    @classmethod
    def from_networkx(cls, graph, entity_type_attr: str = 'entity_type',
                      label_attr: str = 'label', edge_label_attr: str = 'label',
                      default_entity_type: str = 'Anon', **kwargs) -> 'Pyanx':
        """Build a chart from a `networkx` graph.

        Each graph node becomes an entity (its node key is used as the node id)
        and each edge becomes a link. Node/edge attributes are read using the
        configurable attribute names.

        Args:
            graph: A ``networkx`` graph (any flavour).
            entity_type_attr: Node attribute used for the entity type.
            label_attr: Node attribute used for the entity label.
            edge_label_attr: Edge attribute used for the link label.
            default_entity_type: Entity type used when none is set on a node.
            **kwargs: Forwarded to the :class:`Pyanx` constructor.

        Returns:
            A populated :class:`Pyanx` instance.
        """
        chart = cls(**kwargs)

        for node, data in graph.nodes(data=True):
            chart.add_node(
                entity_type=str(data.get(entity_type_attr, default_entity_type)),
                label=str(data.get(label_attr, node)),
                node_id=str(node),
                description=str(data.get('description', '')),
            )

        for source, sink, data in graph.edges(data=True):
            chart.add_edge(
                str(source), str(sink),
                label=str(data.get(edge_label_attr, '')),
                description=str(data.get('description', '')),
            )

        return chart

    def to_networkx(self):
        """Return a ``networkx.DiGraph`` view of the chart.

        Requires the optional ``networkx`` dependency.
        """
        import networkx as nx

        graph = nx.DiGraph()
        for node_id, data in self.nodes.items():
            graph.add_node(
                node_id, label=data['label'],
                entity_type=data['entity_type'],
                description=data['description'])
        for source, sink, data in self.edges:
            graph.add_edge(
                source, sink, label=data['label'],
                description=data['description'])
        return graph
