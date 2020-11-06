import uuid
from typing import Sequence, Optional, Any, Mapping

from kubragen.configfile import ConfigFile
from kubragen.kdata import KData_Secret
from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.option import OptionDef, OptionDefFormat
from kubragen.options import Options


class LokiStackOptions(Options):
    """
    Options for the Loki Stack builder.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - basename
          - object names prefix
          - str
          - ```lokistack```
        * - namespace
          - namespace
          - str
          - ```lokistack```
        * - config |rarr| enabled_plugins
          - enabled plugins
          - Sequence
          - ```['lokistack_peer_discovery_k8s']```
        * - config |rarr| lokistack_conf
          - lokistack.conf file
          - str, :class:`kubragen.configfile.ConfigFile`
          - :class:`kg_lokistack.Loki StackConfigFile`
        * - config |rarr| erlang_cookie
          - erlang cookie
          - str, dict, :class:`KData_Secret`
          - ```uuid.uuid4()```
        * - config |rarr| loglevel
          - server log level
          - str
          - ```info```
        * - config |rarr| enable_prometheus
          - enable prometheus
          - bool
          - ```True```
        * - config |rarr| prometheus_annotation
          - add prometheus annotations
          - bool
          - ```False```
        * - config |rarr| load_definitions
          - load Loki Stack definitions
          - bool, :class:`KData_Secret`
          -
        * - config |rarr| authorization |rarr| serviceaccount_create
          - whether to create a service account
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| serviceaccount_use
          - service account to use if not creating
          - str
          -
        * - config |rarr| authorization |rarr| roles_create
          - whether create roles
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| roles_bind
          - whether to bind roles to service account
          - bool
          - ```True```
        * - container |rarr| busybox
          - busybox container image
          - str
          - ```busybox:<version>```
        * - container |rarr| lokistack
          - lokistack container image
          - str
          - ```lokistack:<version>```
        * - kubernetes |rarr| volumes |rarr| data
          - Kubernetes data volume
          - dict, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          -
        * - kubernetes |rarr| resources |rarr| statefulset
          - Kubernetes StatefulSet resources
          - dict
          -
    """
    def define_options(self) -> Optional[Any]:
        """
        Declare the options for the Loki Stack builder.

        :return: The supported options
        """
        return {
            'basename': OptionDef(required=True, default_value='loki-stack', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='loki-stack', allowed_types=[str]),
            'config': {
                'prometheus_annotation': OptionDef(required=True, default_value=False, allowed_types=[bool]),
                'authorization': {
                    'serviceaccount_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                    'roles_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'roles_bind': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                },
            },
            'container': {
                'promtail': OptionDef(required=True, default_value='grafana/promtail:2.0.0', allowed_types=[str]),
                'loki': OptionDef(required=True, default_value='grafana/loki:2.0.0', allowed_types=[str]),
            },
            'kubernetes': {
                'volumes': {
                    'loki-data': OptionDef(required=True, format=OptionDefFormat.KDATA_VOLUME,
                                      allowed_types=[Mapping, *KDataHelper_Volume.allowed_kdata()]),
                },
                'resources': {
                    'promtail-daemonset': OptionDef(allowed_types=[Mapping]),
                    'loki-statefulset': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
