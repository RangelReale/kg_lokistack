from typing import Optional, Sequence

from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.data import ValueData
from kubragen.exception import InvalidParamError, InvalidNameError
from kubragen.helper import LiteralStr, QuotedStr
from kubragen.kdatahelper import KDataHelper_Volume
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
        * - BUILDITEM_CONFIG
          - ConfigMap
        * - BUILDITEM_CONFIG_SECRET
          - Secret
        * - BUILDITEM_SERVICE_ACCOUNT
          - ServiceAccount
        * - BUILDITEM_PROMTAIL_CLUSTER_ROLE
          - Promtail ClusterRole
        * - BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING
          - Promtail ClusterRoleBinding
        * - BUILDITEM_PROMTAIL_DAEMONSET
          - Promtail Daemonset
        * - BUILDITEM_LOKI_SERVICE_HEADLESS
          - Loki Service Headless
        * - BUILDITEM_LOKI_SERVICE
          - Loki Service
        * - BUILDITEM_LOKI_STATEFULSET
          - Loki StatefulSet

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - config
          - ConfigMap
          - ```<basename>-config```
        * - config-secret
          - Secret
          - ```<basename>-config-secret```
        * - service-account
          - ServiceAccount
          - ```<basename>```
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
    """
    options: LokiStackOptions
    configfile: Optional[str]
    _namespace: str

    SOURCE_NAME = 'kg_lokistack'

    BUILD_ACCESSCONTROL: TBuild = 'accesscontrol'
    BUILD_CONFIG: TBuild = 'config'
    BUILD_SERVICE: TBuild = 'service'

    BUILDITEM_CONFIG: TBuildItem = 'config'
    BUILDITEM_CONFIG_SECRET: TBuildItem = 'config-secret'
    BUILDITEM_SERVICE_ACCOUNT: TBuildItem = 'service-account'
    BUILDITEM_PROMTAIL_CLUSTER_ROLE: TBuildItem = 'promtail-cluster-role'
    BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING: TBuildItem = 'promtail-cluster-role-binding'
    BUILDITEM_PROMTAIL_DAEMONSET: TBuildItem = 'promtail-daemonset'
    BUILDITEM_LOKI_SERVICE_HEADLESS: TBuildItem = 'loki-service-headless'
    BUILDITEM_LOKI_SERVICE: TBuildItem = 'loki-service'
    BUILDITEM_LOKI_STATEFULSET: TBuildItem = 'loki-statefulset'

    def __init__(self, kubragen: KubraGen, options: Optional[LokiStackOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = LokiStackOptions()
        self.options = options
        self.configfile = None

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

        self.object_names_update({
            'config': self.basename('-config'),
            'config-secret': self.basename('-config-secret'),
            'service-account': serviceaccount_name,
            'promtail-cluster-role': self.basename('-promtail'),
            'promtail-cluster-role-binding': self.basename('-promtail'),
            'promtail-daemonset': self.basename('-promtail'),
            'promtail-pod-label-app': self.basename('-promtail'),
            'loki-service-headless': self.basename('-loki-headless'),
            'loki-service': self.basename('-loki'),
            'loki-statefulset': self.basename('-loki'),
            'loki-pod-label-app': self.basename('-loki'),
        })

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
            self.BUILDITEM_CONFIG,
            self.BUILDITEM_CONFIG_SECRET,
            self.BUILDITEM_SERVICE_ACCOUNT,
            self.BUILDITEM_PROMTAIL_CLUSTER_ROLE,
            self.BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING,
            self.BUILDITEM_PROMTAIL_DAEMONSET,
            self.BUILDITEM_LOKI_SERVICE_HEADLESS,
            self.BUILDITEM_LOKI_SERVICE,
            self.BUILDITEM_LOKI_STATEFULSET,
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
        ret = []

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

        if self.option_get('config.authorization.roles_create') is not False:
            ret.extend([
                Object({
                    'kind': 'ClusterRole',
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'metadata': {
                        'name': self.object_name('promtail-cluster-role'),
                    },
                    'rules': [{
                        'apiGroups': [''],
                        'resources': ['nodes',
                                      'nodes/proxy',
                                      'services',
                                      'endpoints',
                                      'pods'],
                        'verbs': ['get', 'watch', 'list']
                    }]
                }, name=self.BUILDITEM_PROMTAIL_CLUSTER_ROLE, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        if self.option_get('config.authorization.roles_bind') is not False:
            ret.extend([
                Object({
                    'kind': 'ClusterRoleBinding',
                    'apiVersion': 'rbac.authorization.k8s.io/v1beta1',
                    'metadata': {
                        'name': self.object_name('promtail-cluster-role-binding'),
                    },
                    'subjects': [{
                        'kind': 'ServiceAccount',
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }],
                    'roleRef': {
                        'apiGroup': 'rbac.authorization.k8s.io',
                        'kind': 'ClusterRole',
                        'name': self.object_name('promtail-cluster-role'),
                    }
                }, name=self.BUILDITEM_PROMTAIL_CLUSTER_ROLE_BINDING, source=self.SOURCE_NAME, instance=self.basename())
            ])

        return ret

    def internal_build_config(self) -> Sequence[ObjectItem]:
        ret = []

        ret.append(Object({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': self.object_name('config'),
                'namespace': self.namespace(),
            },
            'data': {
                'promtail.yaml': LiteralStr(self.promtail_configfile()),
            }
        }, name=self.BUILDITEM_CONFIG, source=self.SOURCE_NAME, instance=self.basename()))

        ret.append(Object({
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': self.object_name('config-secret'),
                'namespace': self.namespace(),
            },
            'type': 'Opaque',
            'data': {
                'loki.yaml': self.kubragen.secret_data_encode(self.loki_configfile()),
            }
        }, name=self.BUILDITEM_CONFIG_SECRET, source=self.SOURCE_NAME, instance=self.basename()))

        return ret

    def internal_build_service(self) -> Sequence[ObjectItem]:
        ret = []

        ret.extend([
            Object({
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': self.object_name('loki-service-headless'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('loki-pod-label-app'),
                    }
                },
                'spec': {
                    'clusterIP': 'None',
                    'ports': [{
                        'port': 3100,
                        'protocol': 'TCP',
                        'name': 'http-metrics',
                        'targetPort': 'http-metrics'
                    }],
                    'selector': {
                        'app': self.object_name('loki-pod-label-app'),
                    }
                }
            }, name=self.BUILDITEM_LOKI_SERVICE_HEADLESS, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': self.object_name('loki-service'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('loki-pod-label-app'),
                    },
                },
                'spec': {
                    'type': 'ClusterIP',
                    'ports': [{
                        'port': 3100,
                        'protocol': 'TCP',
                        'name': 'http-metrics',
                        'targetPort': 'http-metrics'
                    }],
                    'selector': {
                        'app': self.object_name('loki-pod-label-app'),
                    },
                }
            }, name=self.BUILDITEM_LOKI_SERVICE, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'apps/v1',
                'kind': 'DaemonSet',
                'metadata': {
                    'name': self.object_name('promtail-daemonset'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('promtail-pod-label-app'),
                    },
                },
                'spec': {
                    'selector': {
                        'matchLabels': {
                            'app': self.object_name('promtail-pod-label-app'),
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': self.object_name('promtail-pod-label-app'),
                            },
                            'annotations': ValueData({
                                'prometheus.io/scrape': QuotedStr('true'),
                                'prometheus.io/port': QuotedStr('http-metrics'),
                            }, enabled=self.option_get('config.prometheus_annotation') is not False),
                        },
                        'spec': {
                            'serviceAccountName': self.object_name('service-account'),
                            'containers': [{
                                'name': 'promtail',
                                'image': self.option_get('container.promtail'),
                                'args': [
                                    '-config.file=/etc/promtail/promtail.yaml',
                                    '-client.url=http://{}:3100/loki/api/v1/push'.format(
                                        self.object_name('loki-service'))
                                ],
                                'volumeMounts': [{
                                    'name': 'config',
                                    'mountPath': '/etc/promtail'
                                },
                                {
                                    'name': 'run',
                                    'mountPath': '/run/promtail'
                                },
                                {
                                    'mountPath': '/var/lib/docker/containers',
                                    'name': 'docker',
                                    'readOnly': True
                                },
                                {
                                    'mountPath': '/var/log/pods',
                                    'name': 'pods',
                                    'readOnly': True
                                }],
                                'env': [{
                                    'name': 'HOSTNAME',
                                    'valueFrom': {
                                        'fieldRef': {
                                            'fieldPath': 'spec.nodeName'
                                        }
                                    },
                                }],
                                'ports': [{
                                    'containerPort': 3101,
                                    'name': 'http-metrics'
                                }],
                                'securityContext': {
                                    'readOnlyRootFilesystem': True,
                                    'runAsGroup': 0,
                                    'runAsUser': 0
                                },
                                'readinessProbe': {
                                    'failureThreshold': 5,
                                    'httpGet': {
                                        'path': '/ready',
                                        'port': 'http-metrics'
                                    },
                                    'initialDelaySeconds': 10,
                                    'periodSeconds': 10,
                                    'successThreshold': 1,
                                    'timeoutSeconds': 1
                                },
                                'resources': ValueData(
                                    value=self.option_get('kubernetes.resources.promtail-daemonset'),
                                    disabled_if_none=True),
                            }],
                            'tolerations': [{
                                'effect': 'NoSchedule',
                                'key': 'node-role.kubernetes.io/master',
                                'operator': 'Exists'
                            }],
                            'volumes': [{
                                'name': 'config',
                                'configMap': {
                                    'name': self.object_name('config'),
                                    'items': [{
                                        'key': 'promtail.yaml',
                                        'path': 'promtail.yaml',
                                    }]
                                }
                            },
                            {
                                'name': 'run',
                                'hostPath': {
                                    'path': '/run/promtail'
                                }
                            },
                            {
                                'hostPath': {
                                    'path': '/var/lib/docker/containers'
                                },
                                'name': 'docker'
                            },
                            {
                                'hostPath': {
                                    'path': '/var/log/pods'
                                },
                                'name': 'pods'
                            }]
                        }
                    }
                }
            }, name=self.BUILDITEM_PROMTAIL_DAEMONSET, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'apps/v1',
                'kind': 'StatefulSet',
                'metadata': {
                    'name': self.object_name('loki-statefulset'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('loki-pod-label-app'),
                    },
                },
                'spec': {
                    'podManagementPolicy': 'OrderedReady',
                    'replicas': 1,
                    'selector': {
                        'matchLabels': {
                            'app': self.object_name('loki-pod-label-app'),
                        }
                    },
                    'serviceName': self.object_name('loki-service-headless'),
                    'updateStrategy': {
                        'type': 'RollingUpdate'
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': self.object_name('loki-pod-label-app'),
                            },
                            'annotations': ValueData({
                                'prometheus.io/scrape': QuotedStr('true'),
                                'prometheus.io/port': QuotedStr('http-metrics'),
                            }, enabled=self.option_get('config.prometheus_annotation') is not False),
                        },
                        'spec': {
                            'serviceAccountName': self.object_name('service-account'),
                            'securityContext': {
                                'fsGroup': 10001,
                                'runAsGroup': 10001,
                                'runAsNonRoot': True,
                                'runAsUser': 10001
                            },
                            'containers': [{
                                'name': 'loki',
                                'image': self.option_get('container.loki'),
                                'args': [
                                    '-config.file=/etc/loki/loki.yaml'
                                ],
                                'volumeMounts': [{
                                    'name': 'config',
                                    'mountPath': '/etc/loki'
                                },
                                {
                                    'name': 'storage',
                                    'mountPath': '/data',
                                    'subPath': None
                                }],
                                'ports': [{
                                    'name': 'http-metrics',
                                    'containerPort': 3100,
                                    'protocol': 'TCP'
                                }],
                                'livenessProbe': {
                                    'httpGet': {
                                        'path': '/ready',
                                        'port': 'http-metrics'
                                    },
                                    'initialDelaySeconds': 45
                                },
                                'readinessProbe': {
                                    'httpGet': {
                                        'path': '/ready',
                                        'port': 'http-metrics'
                                    },
                                    'initialDelaySeconds': 45
                                },
                                'securityContext': {
                                    'readOnlyRootFilesystem': True
                                },
                                'resources': ValueData(value=self.option_get('kubernetes.resources.loki-statefulset'),
                                                       disabled_if_none=True),
                            }],
                            'terminationGracePeriodSeconds': 4800,
                            'volumes': [{
                                'name': 'config',
                                'secret': {
                                    'secretName': self.object_name('config-secret'),
                                    'items': [{
                                        'key': 'loki.yaml',
                                        'path': 'loki.yaml',
                                    }]
                                }
                            },
                            KDataHelper_Volume.info(base_value={
                                'name': 'storage',
                            }, value=self.option_get('kubernetes.volumes.loki-data'))]
                        }
                    }
                }
            }, name=self.BUILDITEM_LOKI_STATEFULSET, source=self.SOURCE_NAME, instance=self.basename()),
        ])

        return ret

    def loki_configfile(self):
        return '''auth_enabled: false
chunk_store_config:
  max_look_back_period: 0s
compactor:
  shared_store: filesystem
  working_directory: /data/loki/boltdb-shipper-compactor
ingester:
  chunk_block_size: 262144
  chunk_idle_period: 3m
  chunk_retain_period: 1m
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  max_transfer_retries: 0
limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
schema_config:
  configs:
  - from: "2020-10-24"
    index:
      period: 24h
      prefix: index_
    object_store: filesystem
    schema: v11
    store: boltdb-shipper
server:
  http_listen_port: 3100
storage_config:
  boltdb_shipper:
    active_index_directory: /data/loki/boltdb-shipper-active
    cache_location: /data/loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /data/loki/chunks
table_manager:
  retention_deletes_enabled: false
  retention_period: 0s        
'''

    def promtail_configfile(self):
        return '''client:
  backoff_config:
    max_period: 5m
    max_retries: 10
    min_period: 500ms
  batchsize: 1048576
  batchwait: 1s
  external_labels: {}
  timeout: 10s
positions:
  filename: /run/promtail/positions.yaml
server:
  http_listen_port: 3101
target_config:
  sync_period: 10s
scrape_configs:
- job_name: kubernetes-pods-name
  pipeline_stages:
    - docker: {}
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels:
    - __meta_kubernetes_pod_label_name
    target_label: __service__
  - source_labels:
    - __meta_kubernetes_pod_node_name
    target_label: __host__
  - action: drop
    regex: ''
    source_labels:
    - __service__
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
  - action: replace
    replacement: $1
    separator: /
    source_labels:
    - __meta_kubernetes_namespace
    - __service__
    target_label: job
  - action: replace
    source_labels:
    - __meta_kubernetes_namespace
    target_label: namespace
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_name
    target_label: pod
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_container_name
    target_label: container
  - replacement: /var/log/pods/*$1/*.log
    separator: /
    source_labels:
    - __meta_kubernetes_pod_uid
    - __meta_kubernetes_pod_container_name
    target_label: __path__
- job_name: kubernetes-pods-app
  pipeline_stages:
    - docker: {}
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - action: drop
    regex: .+
    source_labels:
    - __meta_kubernetes_pod_label_name
  - source_labels:
    - __meta_kubernetes_pod_label_app
    target_label: __service__
  - source_labels:
    - __meta_kubernetes_pod_node_name
    target_label: __host__
  - action: drop
    regex: ''
    source_labels:
    - __service__
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
  - action: replace
    replacement: $1
    separator: /
    source_labels:
    - __meta_kubernetes_namespace
    - __service__
    target_label: job
  - action: replace
    source_labels:
    - __meta_kubernetes_namespace
    target_label: namespace
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_name
    target_label: pod
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_container_name
    target_label: container
  - replacement: /var/log/pods/*$1/*.log
    separator: /
    source_labels:
    - __meta_kubernetes_pod_uid
    - __meta_kubernetes_pod_container_name
    target_label: __path__
- job_name: kubernetes-pods-direct-controllers
  pipeline_stages:
    - docker: {}
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - action: drop
    regex: .+
    separator: ''
    source_labels:
    - __meta_kubernetes_pod_label_name
    - __meta_kubernetes_pod_label_app
  - action: drop
    regex: '[0-9a-z-.]+-[0-9a-f]{8,10}'
    source_labels:
    - __meta_kubernetes_pod_controller_name
  - source_labels:
    - __meta_kubernetes_pod_controller_name
    target_label: __service__
  - source_labels:
    - __meta_kubernetes_pod_node_name
    target_label: __host__
  - action: drop
    regex: ''
    source_labels:
    - __service__
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
  - action: replace
    replacement: $1
    separator: /
    source_labels:
    - __meta_kubernetes_namespace
    - __service__
    target_label: job
  - action: replace
    source_labels:
    - __meta_kubernetes_namespace
    target_label: namespace
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_name
    target_label: pod
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_container_name
    target_label: container
  - replacement: /var/log/pods/*$1/*.log
    separator: /
    source_labels:
    - __meta_kubernetes_pod_uid
    - __meta_kubernetes_pod_container_name
    target_label: __path__
- job_name: kubernetes-pods-indirect-controller
  pipeline_stages:
    - docker: {}
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - action: drop
    regex: .+
    separator: ''
    source_labels:
    - __meta_kubernetes_pod_label_name
    - __meta_kubernetes_pod_label_app
  - action: keep
    regex: '[0-9a-z-.]+-[0-9a-f]{8,10}'
    source_labels:
    - __meta_kubernetes_pod_controller_name
  - action: replace
    regex: '([0-9a-z-.]+)-[0-9a-f]{8,10}'
    source_labels:
    - __meta_kubernetes_pod_controller_name
    target_label: __service__
  - source_labels:
    - __meta_kubernetes_pod_node_name
    target_label: __host__
  - action: drop
    regex: ''
    source_labels:
    - __service__
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
  - action: replace
    replacement: $1
    separator: /
    source_labels:
    - __meta_kubernetes_namespace
    - __service__
    target_label: job
  - action: replace
    source_labels:
    - __meta_kubernetes_namespace
    target_label: namespace
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_name
    target_label: pod
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_container_name
    target_label: container
  - replacement: /var/log/pods/*$1/*.log
    separator: /
    source_labels:
    - __meta_kubernetes_pod_uid
    - __meta_kubernetes_pod_container_name
    target_label: __path__
- job_name: kubernetes-pods-static
  pipeline_stages:
    - docker: {}
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - action: drop
    regex: ''
    source_labels:
    - __meta_kubernetes_pod_annotation_kubernetes_io_config_mirror
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_label_component
    target_label: __service__
  - source_labels:
    - __meta_kubernetes_pod_node_name
    target_label: __host__
  - action: drop
    regex: ''
    source_labels:
    - __service__
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
  - action: replace
    replacement: $1
    separator: /
    source_labels:
    - __meta_kubernetes_namespace
    - __service__
    target_label: job
  - action: replace
    source_labels:
    - __meta_kubernetes_namespace
    target_label: namespace
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_name
    target_label: pod
  - action: replace
    source_labels:
    - __meta_kubernetes_pod_container_name
    target_label: container
  - replacement: /var/log/pods/*$1/*.log
    separator: /
    source_labels:
    - __meta_kubernetes_pod_annotation_kubernetes_io_config_mirror
    - __meta_kubernetes_pod_container_name
    target_label: __path__        
'''
