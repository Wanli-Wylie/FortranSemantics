from __future__ import annotations

"""Pydantic model representing the persisted result of the transform step."""

from typing import Dict

from pydantic import BaseModel, Field

from forge.data_models.fortran import ModuleUnit


class FileTransformResult(BaseModel):
    """Top level container for all semantic information of a source file."""

    modules: Dict[str, ModuleUnit] = Field(
        default_factory=dict, description="Modules discovered in the source file."
    )


__all__ = ["FileTransformResult"]
