from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from .formal_parameter import FormalParameter

class Signature(BaseModel):
    """
    Represents a function or subroutine signature in Fortran.
    
    This class defines the input parameters and output parameter for a Fortran
    function or subroutine.
    
    Attributes:
        inputs (Dict[str, FormalParameter]): Dictionary mapping parameter names to their
                                            corresponding FormalParameter instances.
        output (Optional[FormalParameter]): The output parameter, if any (None for subroutines).
    """
    model_config = ConfigDict(frozen=True)
    
    inputs: Dict[str, FormalParameter] = Field(
        default_factory=dict,
        description="Dictionary mapping parameter names to their corresponding FormalParameter instances",
    )
    output: Optional[FormalParameter] = Field(
        default=None,
        description="The output parameter, if any (None for subroutines)",
    )
    result_var_same_as_name: Optional[bool] = Field(
        default=None,
        description=(
            "For functions, True if the RESULT variable is implicitly the function"
            " name; False if an explicit RESULT clause is present. None for"
            " subroutines."
        ),
    )