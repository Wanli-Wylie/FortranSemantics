from __future__ import annotations

from .base import BaseOfflineTask
from fpyevolve_core.keys.fortran import SubprogramKey, ModuleKey
from fpyevolve_core.models.fortran import SubroutineCall

class CalleeNameParseTask(BaseOfflineTask):
    """Resolve call records that only store the callee name."""

    def resolve(self, host: SubprogramKey, call: SubroutineCall) -> SubprogramKey | None:
        sp = self.query_handle.find_subroutine_in_module(ModuleKey(host.module_name), call.name)
        if sp:
            return sp

        for mod in self.query_handle.visible_modules(host):
            sp = self.query_handle.find_subroutine_in_module(mod, call.name)
            if sp:
                return sp
        return None

    def execute(self) -> None:
        for host, call in self.query_handle.iter_unresolved_call_names():
            resolved = self.resolve(host, call)
            self.command_handle.update_resolved_call_reference(host, call, resolved)
