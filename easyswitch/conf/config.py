"""
EasySwitch - Configs Management
"""
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from dotenv import load_dotenv

from easyswitch.types import ApiCredentials, Provider


@dataclass
class Config:
    """EasySwitch SDK configurations class."""

    # General configurations
    environment: str = "sandbox"  # 'sandbox' or 'production'
    timeout: int = 30  # timeout in secondes for http requests
    debug: bool = False

    # Logging configurations
    log_level: str = "INFO"  # Options are (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_file: Optional[str] = None  # Path to log file
    log_format: Optional[str] = None  # Log format string
    console_logging: bool = True  # Enabled console logging

    # Enabled providers
    enabled_providers: List[str] = []
    # Default provider
    default_provider: Optional[str] = None

    # Autres configs
    extra_headers: Dict[str, str] = field(default_factory=dict)
    proxy_settings: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization method to load environment variables and validate credentials."""

        if len(self.enabled_providers) == 0:
            # reload from env if no providers are set
            self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment variables."""

        load_dotenv()

        # Load general parameters
        self.environment = os.getenv("EASYSWITCH_ENVIRONMENT", self.environment)
        self.timeout = int(os.getenv("EASYSWITCH_TIMEOUT", self.timeout))
        self.debug = os.getenv("EASYSWITCH_DEBUG", "").lower() in ("true", "1", "yes")
        self.log_file = os.getenv("EASYSWITCH_LOG_FILE", self.log_file)
        self.log_level = os.getenv("EASYSWITCH_LOG_LEVEL", self.log_level).upper()
        self.log_format = os.getenv("EASYSWITCH_LOG_FORMAT", self.log_format)
        self.console_logging = os.getenv("EASYSWITCH_CONSOLE_LOGGING", "").lower() in (
            "true",
            "1",
            "yes",
        )

        # Load enabled providers from env only if not already set
        if len(self.enabled_providers) == 0:
            self.enabled_providers = os.getenv(
                "EASYSWITCH_ENABLED_PROVIDERS", ""
            ).split(",")

        # We don't need to check the vality of the providers here
        # we just pass them to the Client class for validation.

    def _check_api_key(self, provider: str) -> bool:
        """Check if the API key is set for a given provider in the environment variables."""

        env_key = f"EASYSWITCH_{provider.upper()}_API_KEY"
        return os.getenv(env_key) is not None
