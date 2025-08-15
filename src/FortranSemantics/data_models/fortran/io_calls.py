from typing import List, Union
from pydantic import BaseModel
from .reference_entry import SymbolReferenceRead, SymbolReferenceWrite

class IOCall(BaseModel):
    """Generic representation of an I/O related operation."""
    operation: str
    line: int
    args: List[Union[SymbolReferenceRead, SymbolReferenceWrite]] = []
