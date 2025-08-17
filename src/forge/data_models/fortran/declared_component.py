from typing import Optional
from pydantic import BaseModel, Field
from .attr_spec import AttrSpec

class FortranDeclaredComponent(BaseModel):
    """
    Represents a component (field) in a Fortran derived type definition.
    
    This class captures all the essential information about a component in a Fortran
    derived type, including its name, type, attributes, and any initial value. It's
    used to maintain the compiler's understanding of derived type components.
    
    Attributes:
        name (str): The name of the component.
        line_declared (int): The line number in the source file where the component is declared.
        type_declared (str): The Fortran type of the component (e.g., INTEGER, REAL, etc.).
        attributes (AttrSpec): Additional attributes associated with the component
                         (e.g., DIMENSION, POINTER, etc.).
        initial_value (Optional[str]): The initial value assigned to the component, if any.
    """
    name: str = Field(default="", description="The name of the component")
    line_declared: int = Field(default=0, description="The line number in the source file where the component is declared")
    type_declared: str = Field(default="", description="The Fortran type of the component (e.g., INTEGER, REAL, etc.)")
    attributes: AttrSpec = Field(default_factory=AttrSpec, description="Additional attributes associated with the component (e.g., DIMENSION, POINTER, etc.)")
    initial_value: Optional[str] = Field(default=None, description="The initial value assigned to the component, if any")
    
    @property
    def is_derived_type(self) -> bool:
        return self.type_declared.startswith("TYPE-")