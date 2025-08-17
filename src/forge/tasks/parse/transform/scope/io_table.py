"""Transform Fortran AST nodes into lists of IOCall objects."""

from collections import deque
from fparser.two.Fortran2003 import (
    Module,
    Subroutine_Subprogram,
    Function_Subprogram,
    Implicit_Part,
    Open_Stmt,
    Close_Stmt,
    Read_Stmt,
    Write_Stmt,
    Print_Stmt,
    Call_Stmt,
)

from .....data_models.fortran import IOCall
from ..unit.io_calls import (
    from_open_stmt,
    from_close_stmt,
    from_read_stmt,
    from_write_stmt,
    from_print_stmt,
    from_mpi_call_stmt,
)
from ..utils import get_specification_part, get_execution_part, is_iterable
from .base import BaseTableTransformer


def _collect_ios(scopes: deque) -> list[IOCall]:
    calls: list[IOCall] = []
    while scopes:
        current = scopes.popleft()
        if isinstance(current, Open_Stmt):
            calls.append(from_open_stmt(current))
        elif isinstance(current, Close_Stmt):
            calls.append(from_close_stmt(current))
        elif isinstance(current, Read_Stmt):
            calls.append(from_read_stmt(current))
        elif isinstance(current, Write_Stmt):
            calls.append(from_write_stmt(current))
        elif isinstance(current, Print_Stmt):
            calls.append(from_print_stmt(current))
        elif isinstance(current, Call_Stmt):
            io = from_mpi_call_stmt(current)
            if io:
                calls.append(io)
        elif isinstance(current, Implicit_Part):
            continue
        elif is_iterable(current):
            for child in current.children:
                scopes.append(child)
    return calls


class IOTableTransformer(BaseTableTransformer):
    @staticmethod
    def from_module(module: Module) -> list[IOCall]:
        if module is None:
            return []
        specification_part = get_specification_part(module)
        scopes = deque([specification_part])
        return _collect_ios(scopes)

    @staticmethod
    def from_subprogram(
        subprogram: Subroutine_Subprogram | Function_Subprogram,
    ) -> list[IOCall]:
        if subprogram is None:
            return []
        specification_part = get_specification_part(subprogram)
        execution_part = get_execution_part(subprogram)
        scopes = deque([specification_part, execution_part])
        return _collect_ios(scopes)
