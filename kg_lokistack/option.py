from typing import Optional, Any, Mapping, Sequence

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
          - ```loki-stack```
        * - namespace
          - namespace
          - str
          - ```loki-stack```
        * - config |rarr| prometheus_annotation
          - add prometheus annotations
          - bool
          - ```False```
        * - config |rarr| grafana_install_plugins
          - Grafana install plugins
          - Sequence
          - ```[]```
        * - config |rarr| grafana_service_port
          - Grafana service port
          - int
          - 80
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
        * - enable |rarr| grafana
          - whether grafana will be deployed
          - bool
          - ```False```
        * - container |rarr| promtail
          - promtail container image
          - str
          - ```grafana/promtail:<version>```
        * - container |rarr| loki
          - loki container image
          - str
          - ```grafana/loki:<version>```
        * - container |rarr| grafana
          - Grafana container image
          - str
          - ```grafana/grafana:<version>```
        * - kubernetes |rarr| volumes |rarr| loki-data
          - Loki Kubernetes data volume
          - dict, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          -
        * - kubernetes |rarr| volumes |rarr| grafana-data
          - Grafana Kubernetes data volume
          - Mapping, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          - ```{'emptyDir': {}}```
        * - kubernetes |rarr| resources |rarr| promtail-daemonset
          - Promtail Kubernetes StatefulSet resources
          - dict
          -
        * - kubernetes |rarr| resources |rarr| loki-statefulset
          - Loki Kubernetes StatefulSet resources
          - dict
          -
        * - kubernetes |rarr| resources |rarr| grafana-deployment
          - Grafana Kubernetes Deployment resources
          - Mapping
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
                'grafana_service_port': OptionDef(required=True, default_value=80, allowed_types=[int]),
                'grafana_install_plugins': OptionDef(default_value=[], allowed_types=[Sequence]),
                'authorization': {
                    'serviceaccount_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                    'roles_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'roles_bind': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                },
            },
            'enable': {
                'grafana': OptionDef(required=True, default_value=False, allowed_types=[bool]),
            },
            'container': {
                'promtail': OptionDef(required=True, default_value='grafana/promtail:2.0.0', allowed_types=[str]),
                'loki': OptionDef(required=True, default_value='grafana/loki:2.0.0', allowed_types=[str]),
                'grafana': OptionDef(required=True, default_value='grafana/grafana:7.2.0', allowed_types=[str]),
            },
            'kubernetes': {
                'volumes': {
                    'loki-data': OptionDef(required=True, format=OptionDefFormat.KDATA_VOLUME,
                                      allowed_types=[Mapping, *KDataHelper_Volume.allowed_kdata()]),
                    'grafana-data': OptionDef(required=True, format=OptionDefFormat.KDATA_VOLUME,
                                              default_value={'emptyDir': {}},
                                              allowed_types=[Mapping, *KDataHelper_Volume.allowed_kdata()]),
                },
                'resources': {
                    'promtail-daemonset': OptionDef(allowed_types=[Mapping]),
                    'loki-statefulset': OptionDef(allowed_types=[Mapping]),
                    'grafana-deployment': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
