import datetime
from typing import Optional, Any, Sequence, Mapping

from kubragen.configfile import ConfigFileOutput, ConfigFileOutput_Dict, ConfigFile_Extend, \
    ConfigFileExtension, ConfigFileExtensionData
from kubragen.merger import Merger
from kubragen.option import OptionDef
from kubragen.options import Options, option_root_get, OptionGetter


class LokiConfigFileOptions(Options):
    def define_options(self) -> Optional[Any]:
        return {
            'config': {
                'merge_config': OptionDef(allowed_types=[Mapping]),
            },
        }


class LokiConfigFile(ConfigFile_Extend):
    options: LokiConfigFileOptions

    def __init__(self, options: Optional[LokiConfigFileOptions] = None,
                 extensions: Optional[Sequence[ConfigFileExtension]] = None):
        super().__init__(extensions)
        if options is None:
            options = LokiConfigFileOptions()
        self.options = options

    def option_get(self, name: str):
        return option_root_get(self.options, name)

    def init_value(self, options: OptionGetter) -> ConfigFileExtensionData:
        ret = ConfigFileExtensionData({
            'auth_enabled': False,
            'ingester': {
                'chunk_idle_period': '3m',
                'chunk_block_size': 262144,
                'chunk_retain_period': '1m',
                'max_transfer_retries': 0,
                'lifecycler': {
                    'ring': {
                        'kvstore': {
                            'store': 'inmemory'
                        },
                        'replication_factor': 1
                    }
                }
            },
            'limits_config': {
                'enforce_metric_name': False,
                'reject_old_samples': True,
                'reject_old_samples_max_age': '168h'
            },
            'schema_config': {
                'configs': [{
                    'from': datetime.date(2020, 10, 24),
                    'store': 'boltdb-shipper',
                    'object_store': 'filesystem',
                    'schema': 'v11',
                    'index': {
                        'prefix': 'index_',
                        'period': '24h'
                    }
                }]
            },
            'server': {
                'http_listen_port': 3100
            },
            'storage_config': {
                'boltdb_shipper': {
                    'active_index_directory': '/data/loki/boltdb-shipper-active',
                    'cache_location': '/data/loki/boltdb-shipper-cache',
                    'cache_ttl': '24h',
                    'shared_store': 'filesystem'
                },
                'filesystem': {
                    'directory': '/data/loki/chunks'
                }
            },
            'chunk_store_config': {
                'max_look_back_period': '0s'
            },
            'table_manager': {
                'retention_deletes_enabled': False,
                'retention_period': '0s'
            },
            'compactor': {
                'working_directory': '/data/loki/boltdb-shipper-compactor',
                'shared_store': 'filesystem'
            }
        })

        return ret

    def finish_value(self, options: OptionGetter, data: ConfigFileExtensionData) -> ConfigFileOutput:
        if self.option_get('config.merge_config') is not None:
            Merger.merge(data.data, self.option_get('config.merge_config'))
        return ConfigFileOutput_Dict(data.data)
