from pydantic import BaseModel, Field

from forge.data_models.fortran import FortranDeclaredEntity, FortranDerivedTypeDefinition, SymbolReferenceRead, FunctionCall, IOCall, SymbolReferenceWrite, SubroutineCall, Signature    

class ModuleSemantics(BaseModel):
    symbol_table: dict[str, FortranDeclaredEntity] = Field(
        default_factory=dict,
        description="Mapping of local symbol names to their declarations.",
    )
    
    derived_types: dict[str, FortranDerivedTypeDefinition] = Field(
        default_factory=dict,
        description="Derived type definitions local to the module.",
    )
    
    references: list[SymbolReferenceRead] = Field(
        default_factory=list,
        description="Symbol reference entries found within the module.",
    )
    
    calls: list[FunctionCall] = Field(
        default_factory=list,
        description="Function calls made by the module.",
    )
    
    used_modules: list[str] = Field(
        default_factory=list,
        description="Names of modules imported via USE statements.",
    )
    
class SubprogramSemantics(BaseModel):
    symbol_table: dict[str, FortranDeclaredEntity] = Field(
        default_factory=dict,
        description="Mapping of local symbol names to their declarations.",
    )
    
    derived_types: dict[str, FortranDerivedTypeDefinition] = Field(
        default_factory=dict,
        description="Derived type definitions local to the subprogram.",
    )
    
    references: list[SymbolReferenceRead | SymbolReferenceWrite] = Field(
        default_factory=list,
        description="Symbol reference entries found within the subprogram.",
    )
    
    calls: list[FunctionCall | SubroutineCall] = Field(
        default_factory=list,
        description="Function calls made by the subprogram.",
    )
    
    ios: list[IOCall] = Field(
        default_factory=list,
        description="I/O related operations within the subprogram.",
    )
    
    signature: Signature = Field(
        description="Signature of the subprogram.",
    )
    
    used_modules: list[str] = Field(
        default_factory=list,
        description="Names of modules imported via USE statements.",
    )