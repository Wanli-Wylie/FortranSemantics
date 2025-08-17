from pydantic import BaseModel, Field
from .declared_component import FortranDeclaredComponent

class FortranDerivedTypeDefinition(BaseModel):
    """
    Represents a Fortran derived type definition.
    
    This class captures the structure of a Fortran derived type, including its name
    and all its components. It's used to maintain the compiler's understanding of
    user-defined types in the Fortran source code.
    
    Attributes:
        name (str): The name of the derived type.
        declared_components (Dict[str, DeclaredComponent]): A dictionary mapping component
                                                          names to their corresponding
                                                          DeclaredComponent instances.
    """
    name: str = Field(default="", description="The name of the derived type")
    declared_components: dict[str, FortranDeclaredComponent] = Field(default_factory=dict, description="A dictionary mapping component names to their corresponding DeclaredComponent instances")