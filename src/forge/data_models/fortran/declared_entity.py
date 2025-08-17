from typing import Optional
from pydantic import BaseModel, Field
from .attr_spec import AttrSpec

class FortranDeclaredEntity(BaseModel):
    """
    Represents a Fortran variable declaration in the compiler's symbol table.
    
    This class captures all the essential information about a Fortran variable declaration,
    including its name, type, attributes, and any initial value. It's used to maintain
    the compiler's understanding of variables declared in the Fortran source code.
    
    Attributes:
        name (str): The name of the declared variable.
        line_declared (int): The line number in the source file where the variable is declared.
        type_declared (str): The Fortran type of the variable (e.g., INTEGER, REAL, etc.).
        attributes (dict): A dictionary of additional attributes associated with the variable
                         (e.g., DIMENSION, INTENT, etc.).
        initial_value (Optional[str]): The initial value assigned to the variable, if any.
    """
    name: str = Field(default="", description="The name of the declared variable")
    line_declared: int = Field(default=0, description="The line number in the source file where the variable is declared")
    type_declared: str = Field(default="", description="The Fortran type of the variable (e.g., INTEGER, REAL, etc.)")
    attributes: AttrSpec = Field(default_factory=AttrSpec, description="A dictionary of additional attributes associated with the variable (e.g., DIMENSION, INTENT, etc.)")
    initial_value: Optional[str] = Field(default=None, description="The initial value assigned to the variable, if any")
    
    @property
    def is_derived_type(self) -> bool:
        return self.type_declared.startswith("TYPE-")