from .update import (
    SymbolReferenceUpdateTask,
    CallReferenceUpdateTask,
    PartRefUpdateTask,
)
from .parse_callee import CalleeNameParseTask
from .add_result_var import AddResultVarTask

__all__ = [
    "SymbolReferenceUpdateTask",
    "CallReferenceUpdateTask",
    "PartRefUpdateTask",
    "CalleeNameParseTask",
    "AddResultVarTask",
]