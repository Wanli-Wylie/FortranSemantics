from .models import ForgeConfig
from pathlib import Path
import tomllib
from pydantic import ValidationError

class ConfigError(Exception):
    """Custom exception raised when configuration loading or validation fails."""
    pass

def load_config(project_root: Path) -> ForgeConfig:
    """
    Load and validate the forge.toml file from the specified project root directory.

    Args:
        project_root: Path to the Forge project root directory.

    Returns:
        A validated ForgeConfig instance.

    Raises:
        FileNotFoundError: If the forge.toml file does not exist.
        ConfigError: If the file format is incorrect or content validation fails.
    """
    config_path = project_root / "forge.toml"

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: '{config_path}'.\n"
            f"Please run 'forge init' command in the project root directory first to create one."
        )

    try:
        # Use 'rb' mode to open in compliance with tomli requirements
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Error parsing TOML file '{config_path}':\n{e}")

    try:
        # Pydantic V2 uses model_validate method
        config = ForgeConfig.model_validate(config_data)
        return config
    except ValidationError as e:
        # Format Pydantic error messages to make them more user-friendly
        error_details = "\n".join(
            [f"  - In '{'.'.join(map(str, err['loc']))}' field: {err['msg']}" for err in e.errors()]
        )
        raise ConfigError(
            f"Configuration file '{config_path}' content is invalid:\n{error_details}"
        )