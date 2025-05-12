"""
EasySwitch - Configs Base
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, field_validator

from easyswitch.exceptions import ConfigurationError
from easyswitch.types import Currency, Provider


####
##     LOG LEVELs
#####
class LogLevel(str, Enum):
    """Log Levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


####
##      LOG FORMAT CHOICES
#####
class LogFormat(str, Enum):
    """Log Format choices."""

    PLAIN = "plain"
    JSON = "json"


####
##      LOGGING CONFIG MODEL CLASS
#####
class LoggingConfig(BaseModel):
    """Logging Configuration Model"""

    enabled: bool = False
    level: LogLevel = LogLevel.INFO
    file: Optional[str] = None
    console: bool = True
    max_size: int = 10  # MB
    backups: int = 5
    compress: bool = True
    format: LogFormat = LogFormat.PLAIN
    rotate: bool = True


####
##      BASE CONFIGURATION CLASS
#####
class BaseConfigModel(BaseModel):
    """Base class of all configuration models."""

    class Config:
        extra = "forbid"  # Undefined fields are not allowed
        validate_all = True
        use_enum_values = True


####
##      PROVIDER CONFIGURATION CLASS
#####
class ProviderConfig(BaseConfigModel):
    """A configuration model for Providers."""

    api_key: str
    api_secret: Optional[str] = None
    token: Optional[str] = None
    base_url: Optional[str] = None
    callback_url: Optional[str] = None
    return_url: Optional[str] = None
    timeout: int = 30
    environment: str = "sandbox"  # sandbox|production
    extra: Dict[str, Any] = {}  # Extra data (specific for each provider)


####
##      ROOT CONFIGURATION CLASS
#####
class RootConfig(BaseConfigModel):
    """Configuration root, represents EasySwitch config."""

    environment: str = "sandbox"
    """ API environment """

    debug: bool = False
    """ If True, enable debug mode. """

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    """ Logging configurations. """

    default_currency: str = Currency.XOF

    providers: Dict[Provider, ProviderConfig] = Field(default_factory=dict)
    """ Enabled providers. """

    default_provider: Optional[Provider] = None

    @field_validator("environment")
    def validate_environment(cls, v):
        """Ensure Config's environment value is valid."""

        if v not in ("sandbox", "production", "development"):
            raise ConfigurationError(
                "Environment must be 'sandbox', 'development' or 'production'"
            )
        return v

    @field_validator("default_provider")
    def validate_default_provider(cls, v, values):
        """Ensure default provider is valid."""

        # Ensure default provider is in enabled providers
        if v is not None and "providers" in values and v not in values["providers"]:
            raise ValueError(f"Default provider {v} must be in enabled providers")

        # and in supported Providers
        if v not in Provider.__members__:
            raise ValueError(f"Default provider {v} is not supported")
        return v

    @field_validator("default_currency")
    def validate_default_currency(cls, v):
        """Ensure Config's default currency value is valid."""

        if v not in Currency.__members__:
            raise ConfigurationError(
                f"Invalid default currency value '{v}'"
                f"available choices are: {Currency.__members__}."
            )
        return v


####
##      BASE CONFIGURATION SOURCE CLASS
#####
class BaseConfigSource(ABC):
    """Base interface for all configuration sources."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Loads configurations from the source."""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the sourse is valid"""
        pass
