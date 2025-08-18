from sqlalchemy.orm.session import Session
from sqlalchemy.orm import aliased
from fpyevolve_core.keys.fortran import (
    SubprogramKey,
    ModuleKey,
    SubprogramDeclKey,
    ModuleDeclKey,
)
from fpyevolve_core.db.schema.fortrans import (
    FortranSubprogram,
    FortranUse,
    FortranSymbol,
    FortranSubprogramSignature,
    FortranDerivedType,
    FortranSymbolReference,
    SymbolReferenceType,
    SubprogramType,
    FortranCall,
    FortranModule,
)
from fpyevolve_core.models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite,
    SubroutineCall,
    FortranDeclaredEntity,
)
from fpyevolve_core.models.fortran.attr_spec import AttrSpec, ArraySpec
import json
from typing import Iterable, Tuple, Optional

def _parse_array_spec(raw: str | None) -> ArraySpec | None:
    if not raw:
        return None
    return ArraySpec.model_validate_json(raw)

def _parse_additional_keywords(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    return json.loads(raw)

class QueryHandle:
    """SQLite/SQLAlchemy backend implementing the symbol query interfaces."""

    def __init__(self, session: Session) -> None:
        if session is None:
            raise ValueError("Session cannot be None")
        self.session = session

    # basic lookup helpers -------------------------------------------------
    def module_id(self, mod: ModuleKey) -> int:
        row = self.session.query(FortranModule).filter_by(name=mod.module_name).one()
        return row.id

    def subprogram_id(self, sp: SubprogramKey) -> int:
        row = (
            self.session.query(FortranSubprogram)
            .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
            .filter(
                FortranModule.name == sp.module_name,
                FortranSubprogram.name == sp.subprogram_name,
                FortranSubprogram.type == SubprogramType(sp.subprogram_type),
            )
            .one()
        )
        return row.id

    def module_ids(self, names: Iterable[str]) -> dict[str, int]:
        name_set = set(names)
        if not name_set:
            return {}
        rows = (
            self.session.query(FortranModule)
            .filter(FortranModule.name.in_(name_set))
            .all()
        )
        return {row.name: row.id for row in rows}

    # ---------- Uses ---------------------------------------------------------
    def target_modules_used_by_module(self, mod: ModuleKey) -> set[ModuleKey]:
        src_mod = aliased(FortranModule)
        tgt_mod = aliased(FortranModule)

        q = (
            self.session.query(tgt_mod.name)
            .select_from(FortranUse)
            .join(tgt_mod, FortranUse.target_module_id == tgt_mod.id)
            .join(src_mod, FortranUse.source_module_id == src_mod.id)
            .filter(
                src_mod.name == mod.module_name,
                FortranUse.source_subprogram_id.is_(None),
            )
        )

        return {ModuleKey(module_name=row.name) for row in q.all()}

    def target_modules_used_by_subprogram(self, sp: SubprogramKey) -> set[ModuleKey]:
        src_mod = aliased(FortranModule)
        tgt_mod = aliased(FortranModule)

        q = (
            self.session.query(tgt_mod.name)
            .select_from(FortranUse)
            .join(FortranSubprogram, FortranUse.source_subprogram_id == FortranSubprogram.id)
            .join(src_mod, FortranSubprogram.module_id == src_mod.id)
            .join(tgt_mod, FortranUse.target_module_id == tgt_mod.id)
            .filter(
                src_mod.name == sp.module_name,
                FortranSubprogram.name == sp.subprogram_name,
                FortranSubprogram.type == sp.subprogram_type,
            )
        )
        return {ModuleKey(module_name=row.name) for row in q.all()}

    def modules_used_in_subprogram(self, sp: SubprogramKey) -> set[ModuleKey]:
        """Alias for target_modules_used_by_subprogram for interface compatibility."""
        return self.target_modules_used_by_subprogram(sp)

    def visible_modules(self, host: ModuleKey | SubprogramKey) -> set[ModuleKey]:
        """Get all visible modules for a given host."""
        mods = self.target_modules_used_by_module(ModuleKey(host.module_name))
        if isinstance(host, SubprogramKey):
            mods |= self.modules_used_in_subprogram(host)
        return mods

    def visible_arrays(
        self, host: ModuleKey | SubprogramKey
    ) -> list[ModuleDeclKey | SubprogramDeclKey]:
        """Get all visible arrays for a given host."""
        arrays: list[ModuleDeclKey | SubprogramDeclKey] = []
        if isinstance(host, SubprogramKey):
            # Get arrays declared in subprogram
            q = self.session.query(FortranSymbol.name).join(
                FortranSubprogram, FortranSymbol.subprogram_id == FortranSubprogram.id
            ).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == host.module_name,
                FortranSubprogram.name == host.subprogram_name,
                FortranSubprogram.type == host.subprogram_type,
                FortranSymbol.array_spec.isnot(None)
            )
            arrays.extend([
                SubprogramDeclKey(
                    module_name=host.module_name,
                    subprogram_type=host.subprogram_type,
                    subprogram_name=host.subprogram_name,
                    declaration_name=name,
                )
                for (name,) in q.all()
            ])
        
        # Get arrays declared in module
        q = self.session.query(FortranSymbol.name).join(
            FortranModule, FortranSymbol.module_id == FortranModule.id
        ).filter(
            FortranModule.name == host.module_name,
            FortranSymbol.subprogram_id.is_(None),
            FortranSymbol.array_spec.isnot(None)
        )
        arrays.extend([
            ModuleDeclKey(module_name=host.module_name, declaration_name=name)
            for (name,) in q.all()
        ])
        
        # Get arrays from visible modules
        for mod in self.visible_modules(host):
            q = self.session.query(FortranSymbol.name).join(
                FortranModule, FortranSymbol.module_id == FortranModule.id
            ).filter(
                FortranModule.name == mod.module_name,
                FortranSymbol.subprogram_id.is_(None),
                FortranSymbol.array_spec.isnot(None)
            )
            arrays.extend([
                ModuleDeclKey(module_name=mod.module_name, declaration_name=name)
                for (name,) in q.all()
            ])
        
        return arrays

    def visible_functions(self, host: ModuleKey | SubprogramKey) -> set[SubprogramKey]:
        """Get all visible functions for a given host."""
        funcs = set()
        
        # Get functions defined in the host module
        q = self.session.query(FortranSubprogram).join(
            FortranModule, FortranSubprogram.module_id == FortranModule.id
        ).filter(
            FortranModule.name == host.module_name,
            FortranSubprogram.type == SubprogramType.FUNCTION
        )
        funcs.update({
            SubprogramKey(
                module_name=host.module_name,
                subprogram_type=row.type.value,
                subprogram_name=row.name,
            )
            for row in q.all()
        })
        
        # Get functions from visible modules
        for mod in self.visible_modules(host):
            q = self.session.query(FortranSubprogram).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == mod.module_name,
                FortranSubprogram.type == SubprogramType.FUNCTION
            )
            if not q.all():
                pass
            funcs.update({
                SubprogramKey(
                    module_name=mod.module_name,
                    subprogram_type=row.type.value,
                    subprogram_name=row.name,
                )
                for row in q.all()
            })
        
        return funcs

    # ---------- Subprograms / 函数 & 子程序 -----------------------------------
    def find_subroutine_in_module(
        self, mod: ModuleKey, name: str
    ) -> SubprogramKey | None:
        row = (
            self.session.query(FortranSubprogram).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == mod.module_name,
                FortranSubprogram.name == name,
                FortranSubprogram.type == SubprogramType.SUBROUTINE,
            )
            .first()
        )
        if row:
            return SubprogramKey(
                module_name=mod.module_name, subprogram_type=row.type.value, subprogram_name=row.name
            )
        return None

    # ---------- SymbolTable：数组 & 普通符号 ----------------------------------
    def find_symbol_decl(
        self,
        host_module: ModuleKey,
        host_subprogram: SubprogramKey | None,
        name: str,
    ) -> Optional[ModuleDeclKey | SubprogramDeclKey]:
        
        if host_subprogram:
            row = (
                self.session.query(FortranSymbol).join(
                    FortranSubprogram, FortranSymbol.subprogram_id == FortranSubprogram.id
                ).join(
                    FortranModule, FortranSubprogram.module_id == FortranModule.id
                ).filter(
                    FortranModule.name == host_subprogram.module_name,
                    FortranSubprogram.name == host_subprogram.subprogram_name,
                    FortranSubprogram.type == host_subprogram.subprogram_type,
                    FortranSymbol.name == name,
                )
                .first()
            )
            if row:
                return SubprogramDeclKey(
                    module_name=host_subprogram.module_name,
                    subprogram_type=host_subprogram.subprogram_type,
                    subprogram_name=host_subprogram.subprogram_name,
                    declaration_name=row.name,
                )
                
        row = (
            self.session.query(FortranSymbol).join(
                FortranModule, FortranSymbol.module_id == FortranModule.id
            ).filter(
                FortranModule.name == host_module.module_name,
                FortranSymbol.subprogram_id.is_(None),
                FortranSymbol.name == name,
            )
            .first()
        )
        if row:
            return ModuleDeclKey(module_name=host_module.module_name, declaration_name=row.name)
        
        for mod in self.visible_modules(host_subprogram if host_subprogram else host_module):
            row = (
                self.session.query(FortranSymbol).join(
                    FortranModule, FortranSymbol.module_id == FortranModule.id
                ).filter(
                    FortranModule.name == mod.module_name,
                    FortranSymbol.subprogram_id.is_(None),
                    FortranSymbol.name == name,
                )
                .first()
            )
            if row:
                return ModuleDeclKey(module_name=mod.module_name, declaration_name=row.name)
        
        return None

    # ---------- 实现 3 个迭代器 --------------------------------------------
    def iter_symbol_references(
        self,
    ) -> Iterable[Tuple[SubprogramKey | ModuleKey, SymbolReferenceRead | SymbolReferenceWrite]]:
        q = (
            self.session.query(FortranSymbolReference).join(
                FortranSubprogram, FortranSymbolReference.subprogram_id == FortranSubprogram.id
            ).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(FortranSymbolReference.reference_type.in_((SymbolReferenceType.READ, SymbolReferenceType.WRITE)))
            .yield_per(2000)
        )
        for row in q:
            
            if row.name == "Cpools":
                pass
            
            host = (
                SubprogramKey(
                    module_name=row.subprogram.module.name,
                    subprogram_type=row.subprogram.type.value,
                    subprogram_name=row.subprogram.name,
                )
                if row.subprogram
                else ModuleKey(module_name=row.subprogram.module.name if row.subprogram else "")
            )
            ref_cls = (
                SymbolReferenceRead
                if row.reference_type == SymbolReferenceType.READ
                else SymbolReferenceWrite
            )
            yield host, ref_cls(name=row.name, line=row.line, resolved_symbol=row.symbol.name if row.symbol else "")

    def iter_call_references(
        self,
    ) -> Iterable[Tuple[SubprogramKey, SubroutineCall]]:
        q = (
            self.session.query(FortranCall).join(
                FortranSubprogram, FortranCall.caller_id == FortranSubprogram.id
            ).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(FortranCall.call_type == SubprogramType.SUBROUTINE)
            .yield_per(2000)
        )
        for row in q:
            host = SubprogramKey(
                module_name=row.caller.module.name,
                subprogram_type=row.caller.type.value,
                subprogram_name=row.caller.name,
            )
            call = SubroutineCall(name=row.callee.name if row.callee else "", line=row.line, actual_args=[], resolved_subroutine=row.callee.fullname if row.callee else "")
            yield host, call

    def iter_unresolved_call_names(
        self,
    ) -> Iterable[Tuple[SubprogramKey, SubroutineCall]]:
        q = (
            self.session.query(FortranCall)
            .join(FortranSubprogram, FortranCall.caller_id == FortranSubprogram.id)
            .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
            .filter(
                FortranCall.call_type == SubprogramType.SUBROUTINE,
                FortranCall.callee_id.is_(None),
            )
            .yield_per(2000)
        )
        for row in q:
            host = SubprogramKey(
                module_name=row.caller.module.name,
                subprogram_type=row.caller.type.value,
                subprogram_name=row.caller.name,
            )
            call = SubroutineCall(
                name=row.callee_name or "",
                line=row.line,
                actual_args=[],
                resolved_subroutine="",
            )
            yield host, call

    def iter_part_refs(
        self,
    ) -> Iterable[Tuple[SubprogramKey | ModuleKey, SymbolReferenceRead | SymbolReferenceWrite]]:
        q = (
            self.session.query(FortranSymbolReference).join(
                FortranSubprogram, FortranSymbolReference.subprogram_id == FortranSubprogram.id
            ).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(FortranSymbolReference.is_part_ref == True)
            .yield_per(2000)
        )
        for row in q:
            host = (
                SubprogramKey(
                    module_name=row.subprogram.module.name,
                    subprogram_type=row.subprogram.type.value,
                    subprogram_name=row.subprogram.name,
                )
                if row.subprogram
                else ModuleKey(module_name=row.subprogram.module.name if row.subprogram else "")
            )
            ref_cls = (
                SymbolReferenceRead
                if row.reference_type == SymbolReferenceType.READ
                else SymbolReferenceWrite
            )
            yield host, ref_cls(name=row.name, line=row.line, resolved_symbol=row.symbol.name if row.symbol else "", is_part_ref=True)

    def iter_result_symbols(
        self,
    ) -> Iterable[Tuple[SubprogramKey, FortranDeclaredEntity]]:
        q = (
            self.session.query(
                FortranSubprogramSignature,
                FortranSubprogram,
                FortranModule,
                FortranSymbol,
            )
            .join(FortranSubprogram, FortranSubprogramSignature.subprogram_id == FortranSubprogram.id)
            .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
            .join(
                FortranSymbol,
                (FortranSymbol.subprogram_id == FortranSubprogram.id)
                & (FortranSymbol.name == FortranSubprogramSignature.arg_name),
            )
            .filter(FortranSubprogramSignature.result.is_(True))
            .yield_per(2000)
        )
        for sig_row, sp_row, mod_row, sym_row in q:
            decl = FortranDeclaredEntity(
                name=sym_row.name,
                line_declared=sym_row.line_declared,
                type_declared=sym_row.type_declared,
                attributes=AttrSpec(
                    array_spec=_parse_array_spec(sym_row.array_spec),
                    intent=sym_row.intent,
                    additional_keywords=_parse_additional_keywords(sym_row.additional_keywords),
                ),
                initial_value=sym_row.initial_value,
            )
            sp_key = SubprogramKey(
                module_name=mod_row.name,
                subprogram_type=sp_row.type.value,
                subprogram_name=sp_row.name,
            )
            yield sp_key, decl