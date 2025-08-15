from fparser.two.Fortran2003 import (
    Module, 
    Subroutine_Subprogram, 
    Function_Subprogram,
    Assignment_Stmt,
    Implicit_Part)
from typing import List
from collections import deque
from .....data_models.fortran.reference_entry import (
    SymbolReferenceRead,
    SymbolReferenceWrite,
)
from ..utils import get_specification_part, get_execution_part, is_iterable
from ..unit.reference_entry import from_assignment_stmt
from .base import BaseTableTransformer

def _recursive_descend_resolution(scopes: deque) -> list[SymbolReferenceRead | SymbolReferenceWrite]:
    """
    Recursively traverse AST nodes to extract reference entries.
    
    Args:
        scopes (deque): A queue of AST nodes to process.
        
    Returns:
        List[ReferenceEntry]: A list of all reference entries found in the AST nodes.
    """
    entries = []
    while scopes:
        current_scope = scopes.popleft()
        if is_iterable(current_scope):
            for child in current_scope.children:
                if isinstance(child, Assignment_Stmt):
                    entries.extend(from_assignment_stmt(child))
                elif isinstance(child, Implicit_Part):
                    pass
                else:
                    scopes.append(child)
    return entries

class ReferenceTableTransformer(BaseTableTransformer):
    @staticmethod
    def from_module(module: Module) -> list[SymbolReferenceRead | SymbolReferenceWrite]:
        """
        Create a ReferenceTable instance from a Fortran module.
        
        Args:
            module (Module): The Fortran module AST node.
            
        Returns:
            ReferenceTable: A reference table containing all symbol references from the module.
        """
        if module is None:
            return {}
        
        specification_part = get_specification_part(module)
        scopes = deque([specification_part])
        entries = _recursive_descend_resolution(scopes)
        return entries
    
    @staticmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> list[SymbolReferenceRead | SymbolReferenceWrite]:
        """
        Create a ReferenceTable instance from a Fortran subprogram.
        
        Args:
            subprogram (Subroutine_Subprogram | Function_Subprogram): The Fortran subprogram AST node.
            
        Returns:
            ReferenceTable: A reference table containing all symbol references from the subprogram.
        """
        if subprogram is None:
            return {}
        
        specification_part = get_specification_part(subprogram)
        execution_part = get_execution_part(subprogram)
        scopes = deque([specification_part, execution_part])
        entries = _recursive_descend_resolution(scopes)
        return entries
