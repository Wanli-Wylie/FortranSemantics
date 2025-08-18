from __future__ import annotations

"""Pydantic models describing semantic information extracted from Fortran ASTs.

These models capture symbol tables, call graphs and other semantic data for
subprograms and modules. They can be serialised directly to JSON via
:meth:`model_dump_json`.
"""

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .declared_entity import FortranDeclaredEntity
from .derived_type_definition import FortranDerivedTypeDefinition
from .reference_entry import SymbolReferenceRead, SymbolReferenceWrite
from .calls import FunctionCall, SubroutineCall
from .io_calls import IOCall
from .signature import Signature


class SubprogramUnit(BaseModel):
    """Semantic information extracted for a single subprogram."""

    symbol_table: Dict[str, FortranDeclaredEntity] = Field(
        default_factory=dict,
        description="Mapping of local symbol names to their declarations.",
    )
    derived_types: Dict[str, FortranDerivedTypeDefinition] = Field(
        default_factory=dict,
        description="Derived type definitions local to the subprogram.",
    )
    references: List[Union[SymbolReferenceRead, SymbolReferenceWrite]] = Field(
        default_factory=list,
        description="Symbol reference entries found within the subprogram.",
    )
    calls: List[Union[FunctionCall, SubroutineCall]] = Field(
        default_factory=list,
        description="Function or subroutine calls made by the subprogram.",
    )
    ios: List[IOCall] = Field(
        default_factory=list,
        description="I/O related operations within the subprogram.",
    )
    signature: Optional[Signature] = Field(
        default=None,
        description="Signature of the subprogram, if applicable.",
    )
    used_modules: List[str] = Field(
        default_factory=list,
        description="Names of modules used within the subprogram.",
    )


class ModuleUnit(BaseModel):
    """Semantic information extracted for a Fortran module."""

    symbol_table: Dict[str, FortranDeclaredEntity] = Field(
        default_factory=dict,
        description="Symbols declared at module scope.",
    )
    derived_types: Dict[str, FortranDerivedTypeDefinition] = Field(
        default_factory=dict,
        description="Derived types defined in the module.",
    )
    references: List[Union[SymbolReferenceRead, SymbolReferenceWrite]] = Field(
        default_factory=list,
        description="Symbol references appearing at module scope.",
    )
    calls: List[Union[FunctionCall, SubroutineCall]] = Field(
        default_factory=list,
        description="Function or subroutine calls occurring at module scope.",
    )
    ios: List[IOCall] = Field(
        default_factory=list,
        description="I/O related operations at module scope.",
    )
    used_modules: List[str] = Field(
        default_factory=list,
        description="Names of modules imported via USE statements.",
    )
    subprograms: Dict[str, SubprogramUnit] = Field(
        default_factory=dict,
        description="Contained subprograms and their semantics.",
    )


__all__ = ["SubprogramUnit", "ModuleUnit"]
