# KubraGen Builder: Loki Stack

[![PyPI version](https://img.shields.io/pypi/v/kg_lokistack.svg)](https://pypi.python.org/pypi/kg_lokistack/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/kg_lokistack.svg)](https://pypi.python.org/pypi/kg_lokistack/)

kg_lokistack is a builder for [KubraGen](https://github.com/RangelReale/kubragen) that deploys 
a [Loki Stack](https://grafana.com/oss/loki/) stack in Kubernetes.

The Loki Stack consists of Loki, Promtail and Grafana (optional).

[KubraGen](https://github.com/RangelReale/kubragen) is a Kubernetes YAML generator library that makes it possible to generate
configurations using the full power of the Python programming language.

* Website: https://github.com/RangelReale/kg_lokistack
* Repository: https://github.com/RangelReale/kg_lokistack.git
* Documentation: https://kg_lokistack.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/kg_lokistack

## Example

```python
from kg_loki import LokiConfigFile, LokiConfigFileOptions
from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_lokistack import LokiStackBuilder, LokiStackOptions

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: lokistack
#
lokiconfigfile = LokiConfigFile(options=LokiConfigFileOptions({
}))

lokistack_config = LokiStackBuilder(kubragen=kg, options=LokiStackOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'mylokistack',
    'config': {
        'loki_config': lokiconfigfile,
    },
    'enable': {
        'grafana': True,
    },
    'kubernetes': {
        'volumes': {
            'loki-data': {
                'persistentVolumeClaim': {
                    'claimName': 'lokistack-storage-claim'
                }
            }
        },
        'resources': {
            'loki-statefulset': {
                'requests': {
                    'cpu': '150m',
                    'memory': '300Mi'
                },
                'limits': {
                    'cpu': '300m',
                    'memory': '450Mi'
                },
            },
        },
    }
}))

lokistack_config.ensure_build_names(lokistack_config.BUILD_ACCESSCONTROL, lokistack_config.BUILD_CONFIG,
                                    lokistack_config.BUILD_SERVICE)

#
# OUTPUTFILE: lokistack-config.yaml
#
file = OutputFile_Kubernetes('lokistack-config.yaml')
out.append(file)

file.append(lokistack_config.build(lokistack_config.BUILD_ACCESSCONTROL, lokistack_config.BUILD_CONFIG))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# OUTPUTFILE: lokistack.yaml
#
file = OutputFile_Kubernetes('lokistack.yaml')
out.append(file)

file.append(lokistack_config.build(lokistack_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-lokistack-config.yaml ********
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mylokistack
  namespace: app-monitoring
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: mylokistack-promtail
rules:
- apiGroups: ['']
  resources: [nodes, nodes/proxy, services, endpoints, pods]
  verbs: [get, watch, list]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: mylokistack-promtail
subjects:
- kind: ServiceAccount
  name: mylokistack
  namespace: app-monitoring
<...more...>
****** END FILE: 002-lokistack-config.yaml ********
****** BEGIN FILE: 003-lokistack.yaml ********
apiVersion: v1
kind: Service
metadata:
  name: mylokistack-loki-headless
  namespace: app-monitoring
  labels:
    app: mylokistack-loki
spec:
  clusterIP: None
  ports:
  - port: 3100
    protocol: TCP
    name: http-metrics
    targetPort: http-metrics
  selector:
    app: mylokistack-loki
---
apiVersion: v1
kind: Service
metadata:
  name: mylokistack-loki
<...more...>
****** END FILE: 003-lokistack.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-lokistack-config.yaml
kubectl apply -f 003-lokistack.yaml

****** END FILE: create_gke.sh ********
```

## Credits

based on

[Install Loki with Helm](https://grafana.com/docs/loki/latest/installation/helm/)

## Author

Rangel Reale (rangelspam@gmail.com)
