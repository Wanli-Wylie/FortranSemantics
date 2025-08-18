from __future__ import annotations

from .base import BaseOfflineTask
from fpyevolve_core.keys.fortran import ModuleKey, SubprogramKey
from fpyevolve_core.models.fortran import FortranDeclaredEntity

class AddResultVarTask(BaseOfflineTask):
    """Add implicit function result variables named after the function."""

    def execute(self) -> None:
        for sp_id, decl in self.query_handle.iter_result_symbols():
            if decl.name.lower() == sp_id.subprogram_name.lower():
                continue
            if self.query_handle.find_symbol_decl(
                ModuleKey(sp_id.module_name), sp_id, sp_id.subprogram_name
            ):
                continue
            new_decl = FortranDeclaredEntity(
                name=sp_id.subprogram_name,
                line_declared=decl.line_declared,
                type_declared=decl.type_declared,
                attributes=decl.attributes,
                initial_value=decl.initial_value,
            )
            self.command_handle.add_symbol(sp_id, new_decl)

