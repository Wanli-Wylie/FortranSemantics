# src/forge/config/__init__.py

"""
Configuration management for the Forge toolkit.

This module handles the loading, validation, and representation of the `forge.toml`
project configuration file.
"""

from .loader import load_config, ConfigError
from .models import (
    ForgeConfig,
    ProjectModel,
    SourcesModel,
    ParserModel,
)

# Expose key components for easy access from other parts of the application.
__all__ = [
    "load_config",
    "ConfigError",
    "ForgeConfig",
    "ProjectModel",
    "SourcesModel",
    "ParserModel",
]