from fparser.two.Fortran2003 import (
    Module, 
    Subroutine_Subprogram, 
    Function_Subprogram, 
    Specification_Part, 
    Use_Stmt, 
    Implicit_Part
)
from collections import deque
from ..utils import get_specification_part, is_iterable
from .base import BaseTableTransformer

class UsedModulesTransformer(BaseTableTransformer):
    @staticmethod
    def from_module(module: Module) -> set[str]:
        specification_part = get_specification_part(module)
        return from_specification_part(specification_part)

    @staticmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> set[str]:
        specification_part = get_specification_part(subprogram)
        return from_specification_part(specification_part)

def _process_use_stmt(use_stmt: Use_Stmt) -> str:
    """
    Process a USE statement and return a set of module names.
    Very simple implementation, just return the module names.
    """
    return str(use_stmt.items[2])

def from_specification_part(specification_part: Specification_Part) -> set[str]:
    """Return a list of module names used in *specification_part*."""

    scopes = deque([specification_part])

    modules: set[str] = set()
    while scopes:
        current = scopes.popleft()
        if isinstance(current, Use_Stmt):
            modules.add(_process_use_stmt(current))
        elif isinstance(current, Implicit_Part):
            continue
        else:
            if is_iterable(current):
                for child in current.children:
                    scopes.append(child)
    return modules