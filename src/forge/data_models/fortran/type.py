from pydantic import BaseModel, Field

class FortranType(BaseModel):
    intrinsic: bool = Field(default=False, description="Whether the type is intrinsic")
    name: str = Field(default="", description="The name of the type")
    
    def __str__(self) -> str:
        if self.intrinsic:
            return f"{self.name}"
        else:
            return f"TYPE-{self.name}"