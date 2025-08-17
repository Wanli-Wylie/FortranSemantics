# src/forge/config/loader.py

"""
Loads and validates the `forge.toml` configuration file.
"""

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

from .models import ForgeConfig

# Use the standard library tomllib if available (Python 3.11+),
# otherwise fall back to the tomli package.
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        # This should not happen if dependencies are installed correctly.
        print("Error: 'tomli' package is required for Python < 3.11.", file=sys.stderr)
        sys.exit(1)

# Define custom exceptions for clearer error reporting.
class ConfigNotFoundError(FileNotFoundError):
    """Raised when `forge.toml` cannot be found in the directory hierarchy."""
    pass

class EnvironmentVariableError(KeyError):
    """Raised when a required environment variable is not set."""
    pass


# Regex to find environment variable placeholders like ${VAR_NAME}
_ENV_VAR_PATTERN = re.compile(r"\$\{(?P<name>[A-Z_][A-Z0-9_]*)\}")


def _substitute_env_vars(content: str) -> str:
    """
    Replaces all `${VAR_NAME}` placeholders in a string with their
    corresponding environment variable values.
    """
    def replace(match: re.Match) -> str:
        var_name = match.group("name")
        var_value = os.getenv(var_name)
        if var_value is None:
            raise EnvironmentVariableError(
                f"Configuration requires environment variable '{var_name}', which is not set."
            )
        return var_value
    return _ENV_VAR_PATTERN.sub(replace, content)


def find_config_file(search_path: Path) -> Path:
    """
    Searches upward from `search_path` for a `forge.toml` file.

    Args:
        search_path: The directory to start the search from.

    Returns:
        The path to the found `forge.toml` file.

    Raises:
        ConfigNotFoundError: If the file is not found before reaching the root.
    """
    current_dir = search_path.resolve()
    while True:
        config_file = current_dir / "forge.toml"
        if config_file.is_file():
            return config_file
        
        # Stop if we've reached the filesystem root
        if current_dir.parent == current_dir:
            break
        current_dir = current_dir.parent

    raise ConfigNotFoundError(
        f"Could not find a 'forge.toml' file in '{search_path}' or any parent directory."
    )


def load_config(search_path: Path = Path.cwd()) -> ForgeConfig:
    """
    Finds, loads, and validates the `forge.toml` file.

    This is the main entrypoint for the configuration module. It orchestrates
    finding the file, substituting environment variables, parsing TOML, and
    validating the structure with Pydantic.

    Args:
        search_path: The directory to start searching for the config file.
                     Defaults to the current working directory.

    Returns:
        A validated ForgeConfig object.
    
    Raises:
        ConfigNotFoundError: If no `forge.toml` is found.
        EnvironmentVariableError: If a required env variable is missing.
        pydantic.ValidationError: If the config content is invalid.
    """
    config_file_path = find_config_file(search_path)
    
    try:
        raw_content = config_file_path.read_text(encoding="utf-8")
        
        # Step 1: Substitute environment variables
        content_with_env = _substitute_env_vars(raw_content)

        # Step 2: Parse the TOML content
        config_dict: Dict[str, Any] = tomllib.loads(content_with_env)

        # Step 3: Validate with Pydantic
        config = ForgeConfig.model_validate(config_dict)
        
        return config

    except Exception as e:
        # Add context to the error message
        print(f"Error processing configuration file at '{config_file_path}':", file=sys.stderr)
        raise e