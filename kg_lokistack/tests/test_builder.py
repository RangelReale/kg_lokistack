import unittest

from kubragen import KubraGen
from kubragen.jsonpatch import FilterJSONPatches_Apply, ObjectFilter, FilterJSONPatch
from kubragen.provider import Provider_Generic

from kg_lokistack import LokiStackBuilder, LokiStackOptions


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.kg = KubraGen(provider=Provider_Generic())

    def test_empty(self):
        lokistack_config = LokiStackBuilder(kubragen=self.kg)
        self.assertEqual(lokistack_config.object_name('config'), 'loki-stack-config')
        self.assertEqual(lokistack_config.object_name('loki-statefulset'), 'loki-stack-loki')

    def test_basedata(self):
        lokistack_config = LokiStackBuilder(kubragen=self.kg, options=LokiStackOptions({
            'namespace': 'myns',
            'basename': 'mylokistack',
            'kubernetes': {
                'volumes': {
                    'loki-data': {
                        'emptyDir': {},
                    }
                }
            }
        }))
        self.assertEqual(lokistack_config.object_name('config'), 'mylokistack-config')
        self.assertEqual(lokistack_config.object_name('loki-statefulset'), 'mylokistack-loki')

        FilterJSONPatches_Apply(items=lokistack_config.build(lokistack_config.BUILD_SERVICE), jsonpatches=[
            FilterJSONPatch(filters=ObjectFilter(names=[lokistack_config.BUILDITEM_LOKI_SERVICE]), patches=[
                {'op': 'check', 'path': '/metadata/name', 'cmp': 'equals', 'value': 'mylokistack-loki'},
                {'op': 'check', 'path': '/metadata/namespace', 'cmp': 'equals', 'value': 'myns'},
            ]),
        ])
