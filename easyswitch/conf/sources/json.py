"""
EasySwitch - Json config source loader.
"""

import json
from pathlib import Path
from typing import Any, Dict

from easyswitch.conf import register_source
from easyswitch.conf.base import BaseConfigSource


####
##      JSON CONFIGURATION SOURSE CLASS
#####
@register_source("json")
class JsonConfigSource(BaseConfigSource):
    """Loads EasySwitch configurations from a JSON file."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self) -> Dict[str, Any]:
        """Load the JSON file"""

        with open(self.file_path, "r") as f:
            return json.load(f)

    def is_valid(self) -> bool:
        """Check if the config file exists and it's content is valid."""
        if not self.file_path.exists():
            return False

        try:
            with open(self.file_path, "r") as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
