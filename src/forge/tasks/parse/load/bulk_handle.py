from __future__ import annotations

"""Thin wrappers around bulk inserts for semantics DB entities."""

from typing import Iterable, Mapping, Sequence

from sqlalchemy.orm.session import Session

from fpyevolve_core.db.schema.fortrans import (
    FortranCall,
    FortranDerivedType,
    FortranIOCall,
    FortranModule,
    FortranSubprogram,
    FortranSubprogramSignature,
    FortranSymbol,
    FortranSymbolReference,
    FortranUse,
    SubprogramSignatureDir,
    SubprogramType,
    SymbolReferenceType,
)
from fpyevolve_core.keys.fortran import ModuleKey, SubprogramKey

from fpyevolve_core.models.fortran import (
    FortranDeclaredEntity,
    FortranDerivedTypeDefinition,
    FunctionCall,
    IOCall,
    Signature,
    SubroutineCall,
    SymbolReferenceRead,
    SymbolReferenceWrite,
)


class BulkHandle:
    """Encapsulates bulk insert operations for semantics DB entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _add(self, rows: Iterable[object]) -> None:
        rows_list: list[object] = list(rows)
        if not rows_list:
            return
        self._session.add_all(rows_list)
    
    def commit(self) -> None:
        self._session.commit()

    # ------------------------------------------------------------------
    # entity-specific helpers
    def add_modules(self, modules: Iterable[ModuleKey]) -> None:
        rows = [FortranModule(name=m.module_name) for m in modules]
        self._add(rows)

    def add_subprograms(self, rows: Iterable[tuple[int, SubprogramKey]]) -> None:
        sp_rows = [
            FortranSubprogram(
                module_id=module_id,
                name=sp.subprogram_name,
                type=SubprogramType(sp.subprogram_type),
            )
            for module_id, sp in rows
        ]
        self._add(sp_rows)

    def add_calls(
        self, caller_id: int, sequence: Sequence[FunctionCall | SubroutineCall]
    ) -> None:
        rows = []
        for call in sequence:
            call_type = (
                SubprogramType.SUBROUTINE
                if isinstance(call, SubroutineCall)
                else SubprogramType.FUNCTION
            )
            rows.append(
                FortranCall(
                    caller_id=caller_id,
                    callee_name=call.name,
                    line=call.line,
                    call_type=call_type,
                )
            )
        self._add(rows)

    def add_ios(self, subprogram_id: int, sequence: Sequence[IOCall]) -> None:
        rows = [
            FortranIOCall(subprogram_id=subprogram_id, operation=io.operation, line=io.line)
            for io in sequence
        ]
        self._add(rows)

    def add_signatures(self, subprogram_id: int, signature: Signature) -> None:
        rows: list[FortranSubprogramSignature] = []
        for param in signature.inputs.values():
            rows.append(
                FortranSubprogramSignature(
                    subprogram_id=subprogram_id,
                    arg_name=param.name,
                    arg_type=param.type,
                    arg_direction=SubprogramSignatureDir.IN,
                    result=None,
                )
            )
        if signature.output is not None:
            rows.append(
                FortranSubprogramSignature(
                    subprogram_id=subprogram_id,
                    arg_name=signature.output.name,
                    arg_type=signature.output.type,
                    arg_direction=SubprogramSignatureDir.OUT,
                    result=True,
                )
            )
        self._add(rows)

    def add_symbol_references(
        self,
        subprogram_id: int | None,
        sequence: Sequence[SymbolReferenceRead | SymbolReferenceWrite],
    ) -> None:
        rows = [
            FortranSymbolReference(
                subprogram_id=subprogram_id,
                symbol_id=None,
                is_part_ref=ref.is_part_ref,
                component_name=ref.component_name,
                name=ref.name,
                line=ref.line,
                reference_type=SymbolReferenceType(ref.reference_type),
            )
            for ref in sequence
        ]
        self._add(rows)

    def add_symbols(
        self,
        module_id: int,
        subprogram_id: int | None,
        mapping: Mapping[str, FortranDeclaredEntity],
    ) -> None:
        rows = []
        for name, decl in mapping.items():
            rows.append(
                FortranSymbol(
                    module_id=module_id,
                    subprogram_id=subprogram_id,
                    name=name,
                    line_declared=decl.line_declared,
                    type_declared=decl.type_declared,
                    array_spec=decl.attributes.array_spec.model_dump_json()
                    if decl.attributes.array_spec
                    else None,
                    intent=decl.attributes.intent,
                    additional_keywords=(
                        decl.attributes.additional_keywords
                        if decl.attributes.additional_keywords
                        and len(decl.attributes.additional_keywords) > 0
                        else None
                    ),
                    initial_value=decl.initial_value,
                )
            )
        self._add(rows)

    def add_derived_types(
        self,
        module_id: int,
        mapping: Mapping[str, FortranDerivedTypeDefinition],
    ) -> None:
        rows = []
        for name, dtype in mapping.items():
            for comp_name, comp in dtype.declared_components.items():
                rows.append(
                    FortranDerivedType(
                        module_id=module_id,
                        name=name,
                        component_name=comp_name,
                        component_type=comp.type_declared,
                        component_array_spec=comp.attributes.array_spec.model_dump_json()
                        if comp.attributes.array_spec
                        else None,
                        component_intent=comp.attributes.intent,
                        component_keywords=comp.attributes.additional_keywords,
                        component_initial_value=comp.initial_value,
                    )
                )
        self._add(rows)

    def add_uses(
        self,
        source_module_id: int,
        source_subprogram_id: int | None,
        targets: Iterable[tuple[str, int | None]],
    ) -> None:
        rows = []
        for name, target_id in targets:
            rows.append(
                FortranUse(
                    source_module_id=source_module_id,
                    source_subprogram_id=source_subprogram_id,
                    target_module_id=target_id,
                    target_module_name=None if target_id else name,
                )
            )
        self._add(rows)

