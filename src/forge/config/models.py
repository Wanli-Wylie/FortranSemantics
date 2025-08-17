# config/models.py
"""
This module defines Pydantic models for validating and representing forge.toml configuration files.
"""
from pydantic import BaseModel, Field
from typing import Optional

class ProjectModel(BaseModel):
    """Configuration corresponding to the [project] table"""
    name: str = Field(
        ...,
        description="The name of the project, must be specified.",
        examples=["CFD_Project_Typhoon"]
    )
    description: Optional[str] = Field(
        None,
        description="A brief description of the project."
    )
    fortran_standard: Optional[str] = Field(
        None,
        description="The Fortran standard that the code follows (e.g., 'F2008')."
    )

class SourcesModel(BaseModel):
    """
    Configuration corresponding to the [sources] table
    """
    source_dirs: list[str] = Field(
        ...,
        description="List of directories containing source code."
    )
    include_patterns: list[str] = Field(
        default=[
            "**/*.f90", 
            "**/*.F90"],
        description="Glob patterns for including source files."
    )
    exclude_patterns: list[str] = Field(
        default=[],
        description="Glob patterns for excluding files or directories."
    )

class ParserModel(BaseModel):
    """
    Configuration corresponding to the [parser] table
    """
    encoding: str = Field(
        "utf-8",
        description="The encoding format of source files."
    )


class ForgeConfig(BaseModel):
    """
    Top-level configuration model representing the structure of the entire forge.toml file.
    """
    project: ProjectModel
    sources: SourcesModel
    parser: ParserModel = Field(default_factory=lambda: ParserModel(encoding="utf-8"))