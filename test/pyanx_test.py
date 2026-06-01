#!/usr/bin/env python
"""
This work is made available under the Apache License, Version 2.0.

You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
"""

import os
import unittest

import pyanx

__author__ = 'Petter Chr. Bjelland (petter.bjelland@gmail.com)'


class PyanxUnitTest(unittest.TestCase):
  def setUp(self):
    chart = pyanx.Pyanx()

    tyrion = chart.add_node(entity_type='Person', label='Tyrion') # n0
    tywin = chart.add_node(entity_type='Person', label='Tywin') # n1
    jaime = chart.add_node(entity_type='Person', label='Jaime') # n2
    cersei = chart.add_node(entity_type='Woman', label='Cersei') # n3

    chart.add_edge(tywin, tyrion, 'Father of')
    chart.add_edge(jaime, tyrion, 'Brother of')
    chart.add_edge(cersei, tyrion, 'Sister of')

    probe = 'test_probe.anx'

    chart.create(probe)

    self.parsed_chart = pyanx.anx.parse(probe, silence=True)

    os.remove(probe)

  def test_EntityTypes(self):
    entity_types = self.parsed_chart.get_EntityTypeCollection()[0].get_EntityType()

    self.assertEqual(2, len(entity_types))
    self.assertEqual("Person", entity_types[0].get_Name())
    self.assertEqual("Woman", entity_types[1].get_Name())

  def test_LinkTypes(self):
    link_types = self.parsed_chart.get_LinkTypeCollection()[0].get_LinkType()

    self.assertEqual(1, len(link_types))
    self.assertEqual("Link", link_types[0].get_Name())

  def test_ChartItemCount(self):
    chart_items = self.parsed_chart.get_ChartItemCollection()[0].get_ChartItem()

    self.assertEqual(4, len(chart_items))

  def test_ChartItemNodes(self):
    chart_items = self.parsed_chart.get_ChartItemCollection()[0].get_ChartItem()

    # Nodes are emitted in insertion order (dicts preserve order on Python 3.7+).
    self.assertEqual('Tyrion', chart_items[0].get_Label())
    self.assertEqual('Person', chart_items[0].get_End().get_Entity().get_Icon().get_IconStyle().get_Type())

    self.assertEqual('Tywin', chart_items[1].get_Label())
    self.assertEqual('Person', chart_items[1].get_End().get_Entity().get_Icon().get_IconStyle().get_Type())

    self.assertEqual('Jaime', chart_items[2].get_Label())
    self.assertEqual('Person', chart_items[2].get_End().get_Entity().get_Icon().get_IconStyle().get_Type())

    self.assertEqual('Cersei', chart_items[3].get_Label())
    self.assertEqual('Woman', chart_items[3].get_End().get_Entity().get_Icon().get_IconStyle().get_Type())

  def test_ChartItemEdges(self):
    chart_items = self.parsed_chart.get_ChartItemCollection()[1].get_ChartItem()

    self.assertEqual('Father of', chart_items[0].get_Label())
    self.assertEqual('Tywin', chart_items[0].get_Link().get_End1Id())
    self.assertEqual('Tyrion', chart_items[0].get_Link().get_End2Id())

    self.assertEqual('Brother of', chart_items[1].get_Label())
    self.assertEqual('Jaime', chart_items[1].get_Link().get_End1Id())
    self.assertEqual('Tyrion', chart_items[1].get_Link().get_End2Id())

    self.assertEqual('Sister of', chart_items[2].get_Label())
    self.assertEqual('Cersei', chart_items[2].get_Link().get_End1Id())
    self.assertEqual('Tyrion', chart_items[2].get_Link().get_End2Id())

if __name__ == '__main__':
  unittest.main()
