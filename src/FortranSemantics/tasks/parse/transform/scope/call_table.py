"""Transform Fortran AST nodes into :class:`CallTable` objects."""

from collections import deque
from fparser.two.Fortran2003 import (
    Call_Stmt,
    Module,
    Subroutine_Subprogram,
    Function_Subprogram,
    Implicit_Part,
)

from .....data_models.fortran import FunctionCall, SubroutineCall

from ..unit.calls import from_call_stmt
from ..utils import get_specification_part, get_execution_part, is_iterable
from .base import BaseTableTransformer


def _collect_calls(scopes: deque) -> list[SubroutineCall]:
    """Traverse *scopes* breadth‑first and collect ``Call_Stmt`` nodes."""

    calls: list[SubroutineCall] = []
    while scopes:
        current = scopes.popleft()
        if isinstance(current, Call_Stmt):
            calls.append(from_call_stmt(current))
        elif isinstance(current, Implicit_Part):
            continue
        elif is_iterable(current):
            for child in current.children:
                scopes.append(child)
    return calls

class CallTableTransformer(BaseTableTransformer):

    @staticmethod
    def from_module(module: Module) -> list[FunctionCall | SubroutineCall]:
        """Create a :class:`CallTable` from a Fortran module."""

        if module is None:
            return []

        specification_part = get_specification_part(module)
        scopes = deque([specification_part])
        calls = _collect_calls(scopes)
        return calls
    
    @staticmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> list[FunctionCall | SubroutineCall]:
        """Create a :class:`CallTable` from a Fortran subprogram."""

        if subprogram is None:
            return []

        specification_part = get_specification_part(subprogram)
        execution_part = get_execution_part(subprogram)
        scopes = deque([specification_part, execution_part])
        calls = _collect_calls(scopes)
        return calls
