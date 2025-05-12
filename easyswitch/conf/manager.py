"""
EasySwitch - Configs Manager
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from easyswitch.conf import get_source
from easyswitch.conf.base import BaseConfigSource, RootConfig
from easyswitch.exceptions import ConfigurationError


####
##      CONFIGURATION MANAGER CLASS
#####
class ConfigManager:
    """Main Configuration Manager."""

    def __init__(self):
        self._sources: List[BaseConfigSource] = []
        self._config: Optional[RootConfig] = None

    def add_source(self, source_type: str, **kwargs) -> "ConfigManager":
        """Adds a new configuration source."""

        # Get the corresponding config source class
        source_class = get_source(source_type)
        if not source_class:
            raise ConfigurationError(f"Source type '{source_type}' not supported.")

        source = source_class(**kwargs)
        self._sources.append(source)
        return self

    def load(self) -> "ConfigManager":
        """Loads configurations from all available source."""
        merged_config = {}

        for source in self._sources:
            # Ignoring all invalid sources.
            if not source.is_valid():
                continue

            # Then merge configs
            try:
                # Get parsed config dict from source
                source_config = source.load()
                self._merge_configs(merged_config, source_config)
            except Exception as e:
                raise ConfigurationError(f"Failed to load config from source: {str(e)}")

        try:
            self._config = RootConfig(**merged_config)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {str(e)}")

        return self

    def get_config(self) -> RootConfig:
        """Return the validated config."""

        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config

    def _merge_configs(self, base: Dict[str, Any], new: Dict[str, Any]) -> None:
        """Merge recursively two dictionnaries."""

        for key, value in new.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConfigManager":
        """Create a configManager from a dict"""
        return cls().add_source("dict", config_dict=config_dict)

    @classmethod
    def from_env(cls, env_file: str = None) -> "ConfigManager":
        """Create a ConfigManager from .env file"""
        return cls().add_source("env", env_file=env_file)

    @classmethod
    def from_json(cls, file_path: Union[str, Path]) -> "ConfigManager":
        """Create a ConfigManager from JSON file"""
        return cls().add_source("json", file_path=file_path)

    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]) -> "ConfigManager":
        """Crate a ConfigManager from YAML file"""
        return cls().add_source("yaml", file_path=file_path)
