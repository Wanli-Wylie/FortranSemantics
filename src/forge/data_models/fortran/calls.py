from typing import List
from pydantic import BaseModel
from .formal_parameter import FormalParameter
from .reference_entry import SymbolReferenceRead

class FunctionCall(BaseModel):
    """
    Represents a function call in Fortran source code.
    
    This class captures the essential information about a function call,
    including the name of the function, the line number where the call occurs,
    and the resolved symbol name after any aliases or references are resolved.
    """
    
    name: str
    line: int
    resolved_function: str
    actual_args: list[SymbolReferenceRead]

class SubroutineCall(BaseModel):
    """
    Represents a subroutine call in Fortran source code.
    
    This class captures the essential information about a subroutine call,
    including the name of the subroutine, the line number where the call occurs,
    and the resolved symbol name after any aliases or references are resolved.
    """
    name: str
    line: int
    resolved_subroutine: str
    actual_args: list[SymbolReferenceRead]