from typing import Optional, Any, Mapping, Sequence

from kubragen.configfile import ConfigFile
from kubragen.kdata import KData_Secret
from kubragen.kdatahelper import KDataHelper_Volume, KDataHelper_Env
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
        * - config |rarr| loki |rarr| loki_config
          - Loki config file
          - str, ConfigFile
          - :class:`kg_loki.LokiConfigFile`
        * - config |rarr| loki |rarr| service_port
          - Loki service port
          - int
          - 80
        * - config |rarr| promtail |rarr| promtail_config
          - Promtail config file
          - str, ConfigFile
          - :class:`kg_promtail.PromtailConfigFile` with Kubernetes extension
        * - config |rarr| grafana |rarr| grafana_config
          - Grafana INI config file
          - str, :class:`kubragen.configfile.ConfigFile`
          - :class:`kg_grafana.GrafanaConfigFile`
        * - config |rarr| grafana |rarr| service_port
          - Grafana service port
          - int
          - 80
        * - config |rarr| grafana |rarr| install_plugins
          - Grafana install plugins
          - Sequence
          - ```[]```
        * - config |rarr| grafana |rarr| provisioning |rarr| datasources
          - Grafana datasource provisioning
          - str, Sequence, ConfigFile
          -
        * - config |rarr| grafana |rarr| provisioning |rarr| plugins
          - Grafana plugins provisioning
          - str, Sequence, ConfigFile
          -
        * - config |rarr| grafana |rarr| provisioning |rarr| dashboards
          - Grafana dashboards provisioning. ```options.path``` will be set automatically if it is not set
          - str, Sequence, ConfigFile
          -
        * - config |rarr| grafana  |rarr| dashboards
          - Grafana dashboards to pre install
          - :class:`Sequence[GrafanaDashboardSource]`
          -
        * - config |rarr| grafana  |rarr| dashboards_path
          - The root path where Grafana dashboards will be installed on the container.
          - str
          - ```/var/lib/grafana/dashboards```
        * - config |rarr| grafana  |rarr| dashboard_config_max_size
          - The maximum size of a Grafana dashboard config ConfigMap size (set None to disable check)
          - int
          - 250000
        * - config |rarr| grafana |rarr| admin |rarr| user
          - Grafana admin user name
          - str, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          -
        * - config |rarr| grafana |rarr| admin |rarr| password
          - Grafana admin password
          - str, :class:`KData_Secret`
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
                'loki': {
                    'loki_config': OptionDef(allowed_types=[str, ConfigFile]),
                    'service_port': OptionDef(required=True, default_value=80, allowed_types=[int]),
                },
                'promtail': {
                    'promtail_config': OptionDef(allowed_types=[str, ConfigFile]),
                },
                'grafana': {
                    'grafana_config': OptionDef(allowed_types=[str, ConfigFile]),
                    'service_port': OptionDef(required=True, default_value=80, allowed_types=[int]),
                    'install_plugins': OptionDef(default_value=[], allowed_types=[Sequence]),
                    'provisioning': {
                        'datasources': OptionDef(allowed_types=[str, Sequence, ConfigFile]),
                        'plugins': OptionDef(allowed_types=[str, Sequence, ConfigFile]),
                        'dashboards': OptionDef(allowed_types=[str, Sequence, ConfigFile]),
                    },
                    'dashboards': OptionDef(allowed_types=[Sequence]),
                    'dashboards_path': OptionDef(required=True, default_value='/var/lib/grafana/dashboards',
                                                 allowed_types=[str]),
                    'dashboard_config_max_size': OptionDef(default_value=250000, allowed_types=[int]),
                    'admin': {
                        'user': OptionDef(format=OptionDefFormat.KDATA_ENV, allowed_types=[str, *KDataHelper_Env.allowed_kdata()]),
                        'password': OptionDef(format=OptionDefFormat.KDATA_ENV, allowed_types=[str, KData_Secret]),
                    },
                },
                'authorization': {
                    'serviceaccount_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                    'roles_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'roles_bind': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                },
            },
            'enable': {
                'grafana': OptionDef(required=True, default_value=True, allowed_types=[bool]),
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
