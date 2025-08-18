# src/forge/cli/commands/clean.py

from pydantic import BaseModel, Field

from ...keys import ModuleKey, SubprogramKey
from ...core.models.semantics import ModuleSemantics, SubprogramSemantics


class FileSemantics(BaseModel):
    modules: dict[ModuleKey, ModuleSemantics] = Field(
        default_factory=dict,
        description="Mapping of module keys to their semantics.",
    )
    
    subprograms: dict[SubprogramKey, SubprogramSemantics] = Field(
        default_factory=dict,
        description="Mapping of subprogram keys to their semantics.",
    )


import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def transform():
    pass