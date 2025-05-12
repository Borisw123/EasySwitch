"""
EasySwitch - Yaml config source loader.
"""
from pathlib import Path
from typing import Any, Dict

import yaml

from easyswitch.conf import register_source
from easyswitch.conf.base import BaseConfigSource


####
##      YAML CONFIGURATION SOURSE CLASS
#####
@register_source("yaml")
class YamlConfigSource(BaseConfigSource):
    """Loads EasySwitch configurations from a YAML file."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self) -> Dict[str, Any]:
        """Load the yaml file."""
        with open(self.file_path, "r") as f:
            return yaml.safe_load(f)

    def is_valid(self) -> bool:
        """Check that the source path exists and it's content is valid."""

        if not self.file_path.exists():
            return False

        try:
            with open(self.file_path, "r") as f:
                yaml.safe_load(f)
            return True
        except (yaml.YAMLError, UnicodeDecodeError):
            return False
