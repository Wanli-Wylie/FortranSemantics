from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class ReferenceType(Enum):
    READ = "read"
    WRITE = "write"
    PART_REF = "part_ref"

class ReferenceSummary(BaseModel):
    """
    Represents a summary of references to a symbol in the Fortran source code.
    
    This class aggregates multiple references to the same symbol, collecting
    line numbers, reference types, and the resolved symbol name.
    
    Attributes:
        line (List[int]): List of line numbers where the symbol is referenced.
        ref_type (List[str]): List of reference types (read, write, call, part_ref).
        resolved_symbol (Optional[str]): The resolved symbol name after any aliases or references are resolved.
    """
    line: list[int] = Field(default_factory=list, description="List of line numbers where the symbol is referenced")
    ref_type: list[str] = Field(default_factory=list, description="List of reference types (read, write, call, part_ref)")
    resolved_symbol: Optional[str] = Field(default="", description="The resolved symbol name after any aliases or references are resolved")
