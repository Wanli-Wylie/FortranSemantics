from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class DimKind(str, Enum):
    """Enumeration of 3 array dimension forms, corresponding to Fortran semantics."""
    explicit = "explicit"   # EXPLICIT_SHAPE_SPEC (1:10)
    deferred = "deferred"   # DEFERRED_SHAPE_SPEC (:)
    assumed  = "assumed"    # ASSUMED_SHAPE_SPEC (*)

class DimensionSpec(BaseModel):
    """Upper and lower bound information for a single dimension."""
    kind: DimKind = Field(..., description="explicit / deferred / assumed")
    lower: Optional[str] = Field(
        None, description="Explicit lower bound expression; None for deferred/assumed"
    )
    upper: Optional[str] = Field(
        None, description="Explicit upper bound expression; None for deferred/assumed"
    )

    model_config = ConfigDict(extra="forbid")

class ArraySpec(BaseModel):
    """Overall array specification: a group of dimensions."""

    # Use ``conlist`` to ensure at least one dimension is provided across
    # supported Pydantic versions.
    dimensions: list[DimensionSpec] = Field(...)


class AttrSpec(BaseModel):
    """
    Comprehensive Fortran attribute list parsing result.
    Conventions:
    - If `is_array` is True, then `array_spec` must not be empty.
    - `extra='allow'` enables **any `is_*` boolean flags** to be automatically received and preserved.
    """
    array_spec: Optional[ArraySpec] = None
    intent: Optional[Literal["in", "out", "inout"]] = None
    additional_keywords: Optional[list[str]] = None

    model_config = ConfigDict(extra="allow")  # Allow dynamic fields like is_pointer
