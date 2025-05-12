"""
EasySwitch - Conf Module.
"""

from importlib import import_module
from typing import Dict, Type

from easyswitch.conf.base import (
    BaseConfigModel,
    BaseConfigSource,
    LogFormat,
    LoggingConfig,
    LogLevel,
    ProviderConfig,
    RootConfig,
)

# from easyswitch.conf.manager import (
#     ConfigManager
# )

__all__ = [
    "easyswitch.conf.manager.ConfigManager",
    "BaseConfigSource",
    "LogLevel",
    "LogFormat",
    "LoggingConfig",
    "BaseConfigModel",
    "ProviderConfig",
    "RootConfig",
    "register_source",
    "get_source",
]

SOURCES: Dict[str, Type[BaseConfigSource]] = {}


def register_source(name: str):
    """Decorator that registers new configuration source."""

    def decorator(cls: Type[BaseConfigSource]):
        SOURCES[name] = cls
        return cls

    return decorator


def get_source(name: str) -> Type[BaseConfigSource]:
    """Get a config source class byit's name."""

    if name not in SOURCES:
        try:
            import_module(f"easyswitch.config.sources.{name}")
        except ImportError:
            pass
    return SOURCES.get(name)
