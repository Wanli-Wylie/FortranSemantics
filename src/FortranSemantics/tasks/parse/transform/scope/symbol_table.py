from fparser.two.Fortran2003 import Subroutine_Subprogram, Function_Subprogram, Module, Specification_Part, Type_Declaration_Stmt, Implicit_Part
from .....data_models.fortran import FortranDeclaredEntity
from ..unit.declared_entity import from_type_declaration_stmt
from ..utils import get_specification_part, is_iterable
from collections import deque
from .base import BaseTableTransformer

class SymbolTableTransformer(BaseTableTransformer):
    @staticmethod
    def from_module(module: Module) -> dict[str, FortranDeclaredEntity]:
        """
        Create a SymbolTable instance from a Fortran module.
        
        Args:
            module (Module): The Fortran module AST node.
            
        Returns:
            dict[str, DeclaredEntity]: A dictionary mapping symbol names to their corresponding DeclaredEntity instances.
        """
        specification_part = get_specification_part(module)
        data = create_from_specification_part(specification_part)
        return data
    
    @staticmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> dict[str, FortranDeclaredEntity]:
        """
        Create a SymbolTable instance from a Fortran subprogram.
        
        Args:
            subprogram (Subroutine_Subprogram | Function_Subprogram): The Fortran subprogram AST node.
            
        Returns:
            dict[str, DeclaredEntity]: A dictionary mapping symbol names to their corresponding DeclaredEntity instances.
        """
        specification_part = get_specification_part(subprogram)
        data = create_from_specification_part(specification_part)
        return data

def create_from_specification_part(specification_part: Specification_Part) -> dict[str, FortranDeclaredEntity]:
    """
    Create a dictionary of DeclaredEntity instances from a Fortran specification part.
    
    Args:
        specification_part (Specification_Part): The Fortran specification part AST node.
        
    Returns:
        dict[str, DeclaredEntity]: A dictionary mapping symbol names to their corresponding DeclaredEntity instances.
    """
    data = {}
    if specification_part is None:
        return {}
    
    stmts = deque([specification_part])
    
    while stmts:
        stmt = stmts.popleft()

        if isinstance(stmt, Type_Declaration_Stmt):
            data.update(from_type_declaration_stmt(stmt))
        
        if is_iterable(stmt):
            for child in stmt.children:
                if isinstance(child, Implicit_Part):
                    continue
                stmts.append(child)
    
    return data