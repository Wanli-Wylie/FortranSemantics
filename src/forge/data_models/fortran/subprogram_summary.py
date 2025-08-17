from pydantic import BaseModel
from enum import Enum

class SubprogramType(str, Enum):
    FUNCTION = "function"
    SUBROUTINE = "subroutine"

class SubprogramSummary(BaseModel):
    host_module: str
    subprogram_type: SubprogramType
    subprogram_name: str
    module_decl_reads: list[str]
    module_decl_writes: list[str]
    calls: list[str]