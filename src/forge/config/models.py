# src/forge/config/models.py

"""
Pydantic models for the `forge.toml` configuration file.

These models define the schema, default values, and validation rules for all
project settings.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Define literal types for fields with a fixed set of allowed values.
ParserType = Literal["fparser", "lfortran"]
DatabaseDialect = Literal["sqlite", "postgresql", "mysql"]
LoadInitMode = Literal["recreate", "append"]


class ProjectConfig(BaseModel):
    """Schema for the `[project]` section of forge.toml."""
    name: str = Field(
        ...,
        description="The name of the project."
    )
    fortran_version: Optional[str] = Field(
        None,
        description="The Fortran standard version (e.g., '2008'). Informational only."
    )
    source_directories: List[str] = Field(
        default=["src"],
        description="A list of directories containing Fortran source files."
    )
    exclude_patterns: List[str] = Field(
        default=[],
        description="A list of glob patterns to exclude from source file discovery."
    )


class ExtractStageConfig(BaseModel):
    """Schema for the `[stage.extract]` section."""
    parser: ParserType = Field(
        default="fparser",
        description="The Fortran parser to use for analysis."
    )
    num_workers: int = Field(
        default=0,
        ge=0,
        description="Number of parallel processes for parsing. 0 means use all available CPU cores."
    )


class TransformStageConfig(BaseModel):
    """Schema for the `[stage.transform]` section."""
    resolve_macros: bool = Field(
        default=True,
        description="Whether to attempt resolving preprocessor macros during transformation."
    )


class LoadStageConfig(BaseModel):
    """Schema for the `[stage.load]` section."""
    dialect: DatabaseDialect = Field(
        default="sqlite",
        description="The dialect of the target SQL database."
    )
    url: str = Field(
        ...,
        description=(
            "The database connection URL. "
            "Supports environment variable substitution, e.g., '${DB_PASSWORD}'."
        )
    )
    init_mode: LoadInitMode = Field(
        default="recreate",
        description=(
            "Action to take before loading data: "
            "'recreate' drops and recreates tables, 'append' adds to existing tables."
        )
    )


class StageConfig(BaseModel):
    """Container for all stage-specific configurations."""
    extract: ExtractStageConfig = Field(default_factory=ExtractStageConfig)
    transform: TransformStageConfig = Field(default_factory=TransformStageConfig)
    load: LoadStageConfig


class ForgeConfig(BaseModel):
    """The root model for the entire `forge.toml` configuration."""
    project: ProjectConfig
    stage: StageConfig