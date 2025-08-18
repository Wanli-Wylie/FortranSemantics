from fparser.two.Fortran2003 import (
    Module, Subroutine_Subprogram, Function_Subprogram, Specification_Part,
    Derived_Type_Def, Implicit_Part)
from fpyevolve_core.models.fortran import FortranDerivedTypeDefinition
from ..unit.derived_type_definition import from_derived_type_definition
from ..utils import get_specification_part, is_iterable
from collections import deque
from .base import BaseTableTransformer


def from_specification_part(specification_part: Specification_Part) -> dict[str, FortranDerivedTypeDefinition]:
    """
    Create a DerivedTypeDefinitionTable instance from a Fortran specification part.
    """
    data = {}
    scopes = deque([specification_part])
    
    # Use breadth-first traversal to process all nodes in the AST
    while scopes:
        current_scope = scopes.popleft()
        if is_iterable(current_scope):
            for child in current_scope.children:
                # Process type declarations (variables, etc.)
                # Process derived type definitions
                if isinstance(child, Derived_Type_Def):
                    derived_type_definition = from_derived_type_definition(child)
                    data.update({derived_type_definition.name: derived_type_definition})
                # Add other nodes to the queue for further processing
                elif isinstance(child, Implicit_Part):
                    pass
                else:
                    scopes.append(child)

    # Create and return the final symbol table
    return data

class DerivedTypeDefinitionTableTransformer(BaseTableTransformer):
    @staticmethod
    def from_module(module: Module) -> dict[str, FortranDerivedTypeDefinition]:
        """
        Create a DerivedTypeDefinitionTable instance from a Fortran module.
        """
        specification_part = get_specification_part(module)
        return from_specification_part(specification_part)
    
    @staticmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> dict[str, FortranDerivedTypeDefinition]:
        """
        Create a DerivedTypeDefinitionTable instance from a Fortran subprogram.
        """
        specification_part = get_specification_part(subprogram)
        return from_specification_part(specification_part)
