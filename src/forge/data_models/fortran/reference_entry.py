from typing import Optional, Sequence
from pydantic import BaseModel, Field
from enum import Enum

class SymbolReferenceRead(BaseModel):
    """
    Represents a read reference to a symbol in the Fortran source code.
    
    This class captures information about how a symbol is read from in the code,
    including the type of reference (read) and where it occurs.
    """
    name: str = Field(default="", description="The name of the referenced symbol")
    line: int = Field(default=0, description="The line number where the reference occurs")
    resolved_symbol: Optional[str] = Field(default="", description="The resolved symbol name after any aliases or references are resolved")
    is_part_ref: bool = Field(default=False, description="Whether the reference is a part reference")
    component_name: Optional[list[str]] = Field(default=None, description="The name of the component of the referenced symbol")

    @property
    def reference_type(self) -> str:
        return "read"

class SymbolReferenceWrite(BaseModel):
    """
    Represents a write reference to a symbol in the Fortran source code.
    
    This class captures information about how a symbol is written to in the code,
    including the type of reference (write) and where it occurs.
    """
    name: str = Field(default="", description="The name of the referenced symbol")
    line: int = Field(default=0, description="The line number where the reference occurs")
    resolved_symbol: Optional[str] = Field(default="", description="The resolved symbol name after any aliases or references are resolved")
    is_part_ref: bool = Field(default=False, description="Whether the reference is a part reference")
    component_name: Optional[list[str]] = Field(default=None, description="The name of the component of the referenced symbol")
    
    @property
    def reference_type(self) -> str:
        return "write"
    
class SymbolReferencePartRef(BaseModel):
    """
    Represents a part reference to a symbol in the Fortran source code.
    
    This class captures information about how a symbol is referenced as part of a larger expression,
    including the type of reference (part_ref) and where it occurs.
    """
    name: str = Field(default="", description="The name of the referenced symbol")
    line: int = Field(default=0, description="The line number where the reference occurs")
    resolved_symbol: Optional[str] = Field(default="", description="The resolved symbol name after any aliases or references are resolved")

    @property
    def reference_type(self) -> str:
        return "part_ref"
    