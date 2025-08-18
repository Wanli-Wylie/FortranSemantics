from fpyevolve_core.keys.fortran import SubprogramKey, ModuleKey, SubprogramDeclKey, ModuleDeclKey
from fpyevolve_core.models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite,
    SubroutineCall,
    FunctionCall,
)
from .base import BaseOfflineTask

class SymbolReferenceUpdateTask(BaseOfflineTask):
    """Update resolved symbol references in the database."""

    def resolve(
        self,
        host: SubprogramKey | ModuleKey,
        ref: SymbolReferenceRead | SymbolReferenceWrite,
    ) -> SubprogramDeclKey | ModuleDeclKey | None:
        
        if isinstance(host, SubprogramKey):
            decl = self.query_handle.find_symbol_decl(ModuleKey(host.module_name), host, ref.name)
            if decl:
                return decl

        decl = self.query_handle.find_symbol_decl(ModuleKey(host.module_name), None, ref.name)
        if decl:
            return decl

        for mod in self.query_handle.visible_modules(host):
            decl = self.query_handle.find_symbol_decl(mod, None, ref.name)
            if decl:
                return decl

        return None

    def execute(self) -> None:
        for host, ref in self.query_handle.iter_symbol_references():
            
            resolved = self.resolve(host, ref)
            self.command_handle.update_symbol_reference(host, ref, resolved)

class CallReferenceUpdateTask(BaseOfflineTask):
    """Update resolved subroutine call targets."""

    def resolve(
        self,
        host: SubprogramKey,
        call: SubroutineCall,
    ) -> SubprogramKey | None:
        sp = self.query_handle.find_subroutine_in_module(ModuleKey(host.module_name), call.name)
        if sp:
            return sp

        for mod in self.query_handle.visible_modules(host):
            sp = self.query_handle.find_subroutine_in_module(mod, call.name)
            if sp:
                return sp
        return None

    def execute(self) -> None:
        for host_sp, call in self.query_handle.iter_call_references():
            resolved = self.resolve(host_sp, call)
            self.command_handle.update_resolved_call_reference(host_sp, call, resolved)


class PartRefUpdateTask(BaseOfflineTask):
    """Update references for part-ref expressions."""

    def resolve(
        self,
        host: SubprogramKey | ModuleKey,
        part_ref: SymbolReferenceRead | SymbolReferenceWrite,
    ) -> SymbolReferenceRead | FunctionCall:
        for arr_id in self.query_handle.visible_arrays(host):
            if arr_id.declaration_name == part_ref.name:
                return SymbolReferenceRead(
                    name=part_ref.name,
                    line=part_ref.line,
                    resolved_symbol=str(arr_id),
                )

        for func_id in self.query_handle.visible_functions(host):
            if func_id.subprogram_name == part_ref.name:
                return FunctionCall(
                    name=part_ref.name,
                    line=part_ref.line,
                    resolved_function=str(func_id),
                    actual_args=[],
                )

        return SymbolReferenceRead(name=part_ref.name, line=part_ref.line, resolved_symbol="")

    def execute(self) -> None:
        for host, part_ref in self.query_handle.iter_part_refs():
            resolved = self.resolve(host, part_ref)
            if isinstance(resolved, FunctionCall):
                if isinstance(host, SubprogramKey):
                    self.command_handle.add_function_call(host, resolved)
                self.command_handle.remove_part_ref(host, part_ref)
            else:
                self.command_handle.update_resolved_part_ref(host, part_ref, resolved)

