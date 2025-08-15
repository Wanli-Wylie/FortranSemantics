from pydantic import BaseModel, Field, ConfigDict

class FormalParameter(BaseModel):
    """
    Represents a formal parameter in a Fortran function or subroutine signature.
    
    Attributes:
        name (str): The name of the parameter.
        type (str): The type of the parameter.
    """
    model_config = ConfigDict(frozen=True)
    
    name: str = Field(description="The name of the parameter")
    type: str = Field(description="The type of the parameter")
    
    @property
    def is_derived_type(self) -> bool:
        return self.type.startswith("TYPE-")