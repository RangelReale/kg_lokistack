from typing import Optional, Any, Sequence, Mapping

from kubragen.configfile import ConfigFileOutput, ConfigFileOutput_Dict, ConfigFile_Extend, \
    ConfigFileExtension, ConfigFileExtensionData, ConfigFile
from kubragen.merger import Merger
from kubragen.option import OptionDef
from kubragen.options import Options, option_root_get, OptionGetter


class PromtailConfigFileOptions(Options):
    def define_options(self) -> Optional[Any]:
        return {
            'config': {
                'merge_config': OptionDef(allowed_types=[Mapping]),
            },
        }


class PromtailConfigFile(ConfigFile_Extend):
    options: PromtailConfigFileOptions

    def __init__(self, options: Optional[PromtailConfigFileOptions] = None,
                 extensions: Optional[Sequence[ConfigFileExtension]] = None):
        super().__init__(extensions)
        if options is None:
            options = PromtailConfigFileOptions()
        self.options = options

    def option_get(self, name: str):
        return option_root_get(self.options, name)

    def init_value(self, options: OptionGetter) -> ConfigFileExtensionData:
        ret = ConfigFileExtensionData({
            'client': {
                'backoff_config': {
                    'max_period': '5m',
                    'max_retries': 10,
                    'min_period': '500ms'
                },
                'batchsize': 1048576,
                'batchwait': '1s',
                'external_labels': {},
                'timeout': '10s'
            },
            'positions': {
                'filename': '/run/promtail/positions.yaml'
            },
            'server': {
                'http_listen_port': 3101
            },
            'target_config': {
                'sync_period': '10s'
            },
            'scrape_configs': []
        })

        return ret

    def finish_value(self, options: OptionGetter, data: ConfigFileExtensionData) -> ConfigFileOutput:
        if self.option_get('config.merge_config') is not None:
            Merger.merge(data.data, self.option_get('config.merge_config'))
        return ConfigFileOutput_Dict(data.data)


class PromtailConfigFileExt_Kubernetes(ConfigFileExtension):
    def process(self, configfile: ConfigFile, data: ConfigFileExtensionData, options: OptionGetter) -> None:
        data.data['scrape_configs'].extend([{
            'job_name': 'kubernetes-pods-name',
            'pipeline_stages': [{'docker': {}}],
            'kubernetes_sd_configs': [{'role': 'pod'}],
            'relabel_configs': [{
                'source_labels': ['__meta_kubernetes_pod_label_name'],
                'target_label': '__service__'
            },
            {
                'source_labels': ['__meta_kubernetes_pod_node_name'],
                'target_label': '__host__'
            },
            {
                'action': 'drop',
                'regex': '',
                'source_labels': ['__service__']
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_pod_label_(.+)'
            },
            {
                'action': 'replace',
                'replacement': '$1',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_namespace', '__service__'],
                'target_label': 'job'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_namespace'],
                'target_label': 'namespace'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_name'],
                'target_label': 'pod'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_container_name'],
                'target_label': 'container'
            },
            {
                'replacement': '/var/log/pods/*$1/*.log',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_pod_uid', '__meta_kubernetes_pod_container_name'],
                'target_label': '__path__'
            }]
        },
        {
            'job_name': 'kubernetes-pods-app',
            'pipeline_stages': [{'docker': {}}],
            'kubernetes_sd_configs': [{'role': 'pod'}],
            'relabel_configs': [{
                'action': 'drop',
                'regex': '.+',
                'source_labels': ['__meta_kubernetes_pod_label_name']
            },
            {
                'source_labels': ['__meta_kubernetes_pod_label_app'],
                'target_label': '__service__'
            },
            {
                'source_labels': ['__meta_kubernetes_pod_node_name'],
                'target_label': '__host__'
            },
            {
                'action': 'drop',
                'regex': '',
                'source_labels': ['__service__']
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_pod_label_(.+)'
            },
            {
                'action': 'replace',
                'replacement': '$1',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_namespace',
                    '__service__'],
                'target_label': 'job'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_namespace'],
                'target_label': 'namespace'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_name'],
                'target_label': 'pod'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_container_name'],
                'target_label': 'container'
            },
            {
                'replacement': '/var/log/pods/*$1/*.log',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_pod_uid',
                    '__meta_kubernetes_pod_container_name'],
                'target_label': '__path__'
            }]
        },
        {
            'job_name': 'kubernetes-pods-direct-controllers',
            'pipeline_stages': [{'docker': {}}],
            'kubernetes_sd_configs': [{'role': 'pod'}],
            'relabel_configs': [{
                'action': 'drop',
                'regex': '.+',
                'separator': '',
                'source_labels': ['__meta_kubernetes_pod_label_name', '__meta_kubernetes_pod_label_app']
            },
            {
                'action': 'drop',
                'regex': '[0-9a-z-.]+-[0-9a-f]{8,10}',
                'source_labels': ['__meta_kubernetes_pod_controller_name']
            },
            {
                'source_labels': ['__meta_kubernetes_pod_controller_name'],
                'target_label': '__service__'
            },
            {
                'source_labels': ['__meta_kubernetes_pod_node_name'],
                'target_label': '__host__'
            },
            {
                'action': 'drop',
                'regex': '',
                'source_labels': ['__service__']
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_pod_label_(.+)'
            },
            {
                'action': 'replace',
                'replacement': '$1',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_namespace',
                    '__service__'],
                'target_label': 'job'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_namespace'],
                'target_label': 'namespace'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_name'],
                'target_label': 'pod'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_container_name'],
                'target_label': 'container'
            },
            {
                'replacement': '/var/log/pods/*$1/*.log',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_pod_uid',
                    '__meta_kubernetes_pod_container_name'],
                'target_label': '__path__'
            }]
        },
        {
            'job_name': 'kubernetes-pods-indirect-controller',
            'pipeline_stages': [{'docker': {}}],
            'kubernetes_sd_configs': [{'role': 'pod'}],
            'relabel_configs': [{
                'action': 'drop',
                'regex': '.+',
                'separator': '',
                'source_labels': ['__meta_kubernetes_pod_label_name',
                    '__meta_kubernetes_pod_label_app']
            },
            {
                'action': 'keep',
                'regex': '[0-9a-z-.]+-[0-9a-f]{8,10}',
                'source_labels': ['__meta_kubernetes_pod_controller_name']
            },
            {
                'action': 'replace',
                'regex': '([0-9a-z-.]+)-[0-9a-f]{8,10}',
                'source_labels': ['__meta_kubernetes_pod_controller_name'],
                'target_label': '__service__'
            },
            {
                'source_labels': ['__meta_kubernetes_pod_node_name'],
                'target_label': '__host__'
            },
            {
                'action': 'drop',
                'regex': '',
                'source_labels': ['__service__']
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_pod_label_(.+)'
            },
            {
                'action': 'replace',
                'replacement': '$1',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_namespace',
                    '__service__'],
                'target_label': 'job'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_namespace'],
                'target_label': 'namespace'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_name'],
                'target_label': 'pod'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_container_name'],
                'target_label': 'container'
            },
            {
                'replacement': '/var/log/pods/*$1/*.log',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_pod_uid',
                    '__meta_kubernetes_pod_container_name'],
                'target_label': '__path__'
            }]
        },
        {
            'job_name': 'kubernetes-pods-static',
            'pipeline_stages': [{'docker': {}}],
            'kubernetes_sd_configs': [{'role': 'pod'}],
            'relabel_configs': [{
                'action': 'drop',
                'regex': '',
                'source_labels': ['__meta_kubernetes_pod_annotation_kubernetes_io_config_mirror']
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_label_component'],
                'target_label': '__service__'
            },
            {
                'source_labels': ['__meta_kubernetes_pod_node_name'],
                'target_label': '__host__'
            },
            {
                'action': 'drop',
                'regex': '',
                'source_labels': ['__service__']
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_pod_label_(.+)'
            },
            {
                'action': 'replace',
                'replacement': '$1',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_namespace',
                    '__service__'],
                'target_label': 'job'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_namespace'],
                'target_label': 'namespace'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_name'],
                'target_label': 'pod'
            },
            {
                'action': 'replace',
                'source_labels': ['__meta_kubernetes_pod_container_name'],
                'target_label': 'container'
            },
            {
                'replacement': '/var/log/pods/*$1/*.log',
                'separator': '/',
                'source_labels': ['__meta_kubernetes_pod_annotation_kubernetes_io_config_mirror',
                    '__meta_kubernetes_pod_container_name'],
                'target_label': '__path__'
            }],
        }])
