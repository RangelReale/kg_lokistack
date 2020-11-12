import copy
from typing import Optional, Sequence, Mapping, List

from kg_grafana import GrafanaBuilder, GrafanaOptions
from kg_loki import LokiBuilder, LokiOptions
from kg_promtail import PromtailBuilder, PromtailOptions, PromtailConfigFile, PromtailConfigFileExt_Kubernetes
from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.exception import InvalidParamError, InvalidNameError, OptionError
from kubragen.object import ObjectItem, Object
from kubragen.types import TBuild, TBuildItem

from .option import LokiStackOptions


class LokiStackBuilder(Builder):
    """
    Loki Stack builder.

    Based on `Install Loki with Helm <https://grafana.com/docs/loki/latest/installation/helm/>`_.

    .. list-table::
        :header-rows: 1

        * - build
          - description
        * - BUILD_ACCESSCONTROL
          - creates service account, roles, and roles bindings
        * - BUILD_CONFIG
          - creates ConfigMap and Secret
        * - BUILD_SERVICE
          - creates deployments and services

    .. list-table::
        :header-rows: 1

        * - build item
          - description
        * - BUILDITEM_SERVICE_ACCOUNT
          - ServiceAccount
        * - BUILDITEM_PROMTAIL_CONFIG
          - Promtail ConfigMap
        * - BUILDITEM_PROMTAIL_CLUSTER_ROLE
          - Promtail ClusterRole
        * - BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING
          - Promtail ClusterRoleBinding
        * - BUILDITEM_PROMTAIL_DAEMONSET
          - Promtail Daemonset
        * - BUILDITEM_CONFIG_LOKI_SECRET
          - Loki Secret
        * - BUILDITEM_LOKI_SERVICE_HEADLESS
          - Loki Service Headless
        * - BUILDITEM_LOKI_SERVICE
          - Loki Service
        * - BUILDITEM_LOKI_STATEFULSET
          - Loki StatefulSet
        * - BUILDITEM_GRAFANA_DEPLOYMENT
          - Grafana Deployment
        * - BUILDITEM_GRAFANA_SERVICE
          - Grafana Service

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - service-account
          - ServiceAccount
          - ```<basename>```
        * - promtail-config
          - Promtail ConfigMap
          - ```<basename>-promtail-config```
        * - promtail-cluster-role
          - Promtail cluster role
          - ```<basename>-promtail```
        * - promtail-cluster-role-binding
          - Promtail cluster role binding
          - ```<basename>-promtail```
        * - promtail-daemonset
          - Promtail DaemonSet
          - ```<basename>-promtail```
        * - promtail-pod-label-app
          - Promtail label *app* to be used by selection
          - ```<basename>-promtail```
        * - loki-config-secret
          - Loki Secret
          - ```<basename>-loki-config-secret```
        * - loki-service-headless
          - Loki Service headless
          - ```<basename>-loki-headless```
        * - loki-service
          - Loki Service
          - ```<basename>-loki```
        * - loki-statefulset
          - Loki StatefulSet
          - ```<basename>-loki```
        * - loki-pod-label-app
          - Loki label *app* to be used by selection
          - ```<basename>-loki```
        * - grafana-service
          - Grafana Service
          - ```<basename>-grafana```
        * - grafana-deployment
          - Grafana Deployment
          - ```<basename>-grafana```
    """
    options: LokiStackOptions
    _namespace: str
    _default_object_names: Mapping[str, str]

    SOURCE_NAME = 'kg_lokistack'

    BUILD_ACCESSCONTROL = TBuild('accesscontrol')
    BUILD_CONFIG = TBuild('config')
    BUILD_SERVICE = TBuild('service')

    BUILDITEM_SERVICE_ACCOUNT = TBuildItem('service-account')
    BUILDITEM_PROMTAIL_CONFIG = TBuildItem('promtail-config')
    BUILDITEM_PROMTAIL_CLUSTER_ROLE = TBuildItem('promtail-cluster-role')
    BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING = TBuildItem('promtail-cluster-role-binding')
    BUILDITEM_PROMTAIL_DAEMONSET = TBuildItem('promtail-daemonset')
    BUILDITEM_LOKI_CONFIG_SECRET = TBuildItem('loki-config-secret')
    BUILDITEM_LOKI_SERVICE_HEADLESS = TBuildItem('loki-service-headless')
    BUILDITEM_LOKI_SERVICE = TBuildItem('loki-service')
    BUILDITEM_LOKI_STATEFULSET = TBuildItem('loki-statefulset')
    BUILDITEM_GRAFANA_DEPLOYMENT = TBuildItem('grafana-deployment')
    BUILDITEM_GRAFANA_SERVICE = TBuildItem('grafana-service')

    def __init__(self, kubragen: KubraGen, options: Optional[LokiStackOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = LokiStackOptions()
        self.options = options
        self._default_object_names = {}

        self._namespace = self.option_get('namespace')

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            serviceaccount_name = self.basename()
        else:
            serviceaccount_name = self.option_get('config.authorization.serviceaccount_use')
            if serviceaccount_name == '':
                serviceaccount_name = None

        if self.option_get('config.authorization.roles_bind') is not False:
            if serviceaccount_name is None:
                raise InvalidParamError('To bind roles a service account is required')

        self.object_names_init({
            'service-account': serviceaccount_name,
        })

        loki_config = self._create_loki_config()
        loki_config.ensure_build_names(loki_config.BUILD_CONFIG, loki_config.BUILD_SERVICE)

        self.object_names_init({
            'loki-config-secret': loki_config.object_name('config-secret'),
            'loki-service-headless': loki_config.object_name('service-headless'),
            'loki-service': loki_config.object_name('service'),
            'loki-statefulset': loki_config.object_name('statefulset'),
            'loki-pod-label-app': loki_config.object_name('pod-label-app'),
        })

        promtail_config = self._create_promtail_config()
        promtail_config.ensure_build_names(promtail_config.BUILD_ACCESSCONTROL, promtail_config.BUILD_CONFIG,
                                           promtail_config.BUILD_SERVICE)

        self.object_names_init({
            'promtail-config': promtail_config.object_name('config'),
            'promtail-cluster-role': promtail_config.object_name('cluster-role'),
            'promtail-cluster-role-binding': promtail_config.object_name('cluster-role-binding'),
            'promtail-daemonset': promtail_config.object_name('daemonset'),
            'promtail-pod-label-app': promtail_config.object_name('pod-label-app'),
        })

        if self.option_get('enable.grafana') is not False:
            granana_config = self._create_granana_config()
            granana_config.ensure_build_names(granana_config.BUILD_CONFIG, granana_config.BUILD_SERVICE)

            self.object_names_init({
                'grafana-deployment': granana_config.object_name('deployment'),
                'grafana-service': granana_config.object_name('service'),
            })

        self._default_object_names = copy.deepcopy(self.object_names())

    def option_get(self, name: str):
        return self.kubragen.option_root_get(self.options, name)

    def basename(self, suffix: str = ''):
        return '{}{}'.format(self.option_get('basename'), suffix)

    def namespace(self):
        return self._namespace

    def build_names(self) -> Sequence[TBuild]:
        return [self.BUILD_ACCESSCONTROL, self.BUILD_CONFIG, self.BUILD_SERVICE]

    def build_names_required(self) -> Sequence[TBuild]:
        ret = [self.BUILD_CONFIG, self.BUILD_SERVICE]
        if self.option_get('config.authorization.serviceaccount_create') is not False or \
                self.option_get('config.authorization.roles_create') is not False:
            ret.append(self.BUILD_ACCESSCONTROL)
        return ret

    def builditem_names(self) -> Sequence[TBuildItem]:
        return [
            self.BUILDITEM_SERVICE_ACCOUNT,
            self.BUILDITEM_PROMTAIL_CONFIG,
            self.BUILDITEM_PROMTAIL_CLUSTER_ROLE,
            self.BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING,
            self.BUILDITEM_PROMTAIL_DAEMONSET,
            self.BUILDITEM_LOKI_CONFIG_SECRET,
            self.BUILDITEM_LOKI_SERVICE_HEADLESS,
            self.BUILDITEM_LOKI_SERVICE,
            self.BUILDITEM_LOKI_STATEFULSET,
            self.BUILDITEM_GRAFANA_DEPLOYMENT,
            self.BUILDITEM_GRAFANA_SERVICE,
        ]

    def internal_build(self, buildname: TBuild) -> Sequence[ObjectItem]:
        if buildname == self.BUILD_ACCESSCONTROL:
            return self.internal_build_accesscontrol()
        elif buildname == self.BUILD_CONFIG:
            return self.internal_build_config()
        elif buildname == self.BUILD_SERVICE:
            return self.internal_build_service()
        else:
            raise InvalidNameError('Invalid build name: "{}"'.format(buildname))

    def internal_build_accesscontrol(self) -> Sequence[ObjectItem]:
        ret: List[ObjectItem] = []

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'v1',
                    'kind': 'ServiceAccount',
                    'metadata': {
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }
                }, name=self.BUILDITEM_SERVICE_ACCOUNT, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        ret.extend(self._build_result_change(
            self._create_promtail_config().build(PromtailBuilder.BUILD_ACCESSCONTROL), 'promtail'))

        return ret

    def internal_build_config(self) -> Sequence[ObjectItem]:
        ret: List[ObjectItem] = []

        ret.extend(self._build_result_change(
            self._create_promtail_config().build(PromtailBuilder.BUILD_CONFIG), 'promtail'))

        ret.extend(self._build_result_change(
            self._create_loki_config().build(LokiBuilder.BUILD_CONFIG), 'loki'))

        if self.option_get('enable.grafana') is not False:
            ret.extend(self._build_result_change(
                self._create_granana_config().build(GrafanaBuilder.BUILD_CONFIG), 'grafana'))

        return ret

    def internal_build_service(self) -> Sequence[ObjectItem]:
        ret: List[ObjectItem] = []

        ret.extend(self._build_result_change(
            self._create_loki_config().build(LokiBuilder.BUILD_SERVICE), 'loki'))

        ret.extend(self._build_result_change(
            self._create_promtail_config().build(PromtailBuilder.BUILD_SERVICE), 'promtail'))

        if self.option_get('enable.grafana') is not False:
            ret.extend(self._build_result_change(
                self._create_granana_config().build(GrafanaBuilder.BUILD_SERVICE), 'grafana'))

        return ret

    def _build_result_change(self, items: Sequence[ObjectItem], name_prefix: str) -> Sequence[ObjectItem]:
        for o in items:
            if isinstance(o, Object):
                o.name = '{}-{}'.format(name_prefix, o.name)
                o.source = self.SOURCE_NAME
                o.instance = self.basename()
        return items

    def _object_names_changed(self, prefix: str) -> Mapping[str, str]:
        ret = {}
        for dname, dvalue in self.object_names().items():
            if dname.startswith(prefix) and dname in self._default_object_names:
                if self._default_object_names[dname] != dvalue:
                    ret[dname[len(prefix):]] = dvalue
        return ret

    def _create_loki_config(self) -> LokiBuilder:
        try:
            ret = LokiBuilder(kubragen=self.kubragen, options=LokiOptions({
                'basename': self.basename('-loki'),
                'namespace': self.namespace(),
                'config': {
                    'prometheus_annotation': self.option_get('config.prometheus_annotation'),
                    'loki_config': self.option_get('config.loki_config'),
                    'service_port': self.option_get('config.loki_service_port'),
                    'authorization': {
                        'serviceaccount_use': self.object_name('service-account'),
                    },
                },
                'kubernetes': {
                    'volumes': {
                        'data': self.option_get('kubernetes.volumes.loki-data'),
                    },
                    'resources': {
                        'statefulset': self.option_get('kubernetes.resources.loki-statefulset'),
                    },
                },
            }))
            ret.object_names_change(self._object_names_changed('loki-'))
            return ret
        except OptionError as e:
            raise OptionError('Grafana option error: {}'.format(str(e))) from e
        except TypeError as e:
            raise OptionError('Grafana type error: {}'.format(str(e))) from e

    def _create_promtail_config(self) -> PromtailBuilder:
        try:
            config = self.option_get('config.promtail_config')
            if config is None:
                config = PromtailConfigFile(extensions=[PromtailConfigFileExt_Kubernetes()])

            ret = PromtailBuilder(kubragen=self.kubragen, options=PromtailOptions({
                'basename': self.basename('-promtail'),
                'namespace': self.namespace(),
                'config': {
                    'prometheus_annotation': self.option_get('config.prometheus_annotation'),
                    'promtail_config': config,
                    'loki_url': 'http://{}:{}'.format(self.object_name('loki-service'),
                                                      self.option_get('config.loki_service_port')),
                    'authorization': {
                        'serviceaccount_create': False,
                        'serviceaccount_use': self.object_name('service-account'),
                        'roles_create': self.option_get('config.authorization.roles_create'),
                        'roles_bind': self.option_get('config.authorization.roles_bind'),
                    },
                },
                'container': {
                    'promtail': self.option_get('container.promtail'),
                },
                'kubernetes': {
                    'resources': {
                        'daemonset': self.option_get('kubernetes.resources.promtail-daemonset'),
                    },
                },
            }))
            ret.object_names_change(self._object_names_changed('promtail-'))
            return ret
        except OptionError as e:
            raise OptionError('Prometheus option error: {}'.format(str(e))) from e
        except TypeError as e:
            raise OptionError('Prometheus type error: {}'.format(str(e))) from e

    def _create_granana_config(self) -> GrafanaBuilder:
        if self.option_get('enable.grafana') is not True:
            raise InvalidParamError('Grafana is not enabled')

        try:
            ret = GrafanaBuilder(kubragen=self.kubragen, options=GrafanaOptions({
                'basename': self.basename('-grafana'),
                'namespace': self.namespace(),
                'config': {
                    'install_plugins': self.option_get('config.grafana_install_plugins'),
                    'service_port': self.option_get('config.grafana_service_port'),
                    'provisioning': {
                        'datasources': self.option_get('config.grafana_provisioning.datasources'),
                        'plugins': self.option_get('config.grafana_provisioning.plugins'),
                        'dashboards': self.option_get('config.grafana_provisioning.dashboards'),
                    },
                },
                'kubernetes': {
                    'volumes': {
                        'data': self.option_get('kubernetes.volumes.grafana-data'),
                    },
                    'resources': {
                        'deployment': self.option_get('kubernetes.resources.grafana-deployment'),
                    },
                },
            }))
            ret.object_names_change(self._object_names_changed('grafana-'))
            return ret
        except OptionError as e:
            raise OptionError('Grafana option error: {}'.format(str(e))) from e
        except TypeError as e:
            raise OptionError('Grafana type error: {}'.format(str(e))) from e
