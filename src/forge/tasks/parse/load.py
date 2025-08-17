from typing import Iterable, Mapping, Sequence
from sqlalchemy.orm.session import Session

from ...keys import ModuleKey, SubprogramKey
from ...data_models.fortran import (
    FortranDeclaredEntity,
    FortranDerivedTypeDefinition,
    FunctionCall,
    IOCall,
    Signature,
    SubroutineCall,
    SymbolReferenceRead,
    SymbolReferenceWrite,
)
from ...database.repository.bulk_handle import BulkHandle
from ...database.repository.query_handle import QueryHandle


def load_modules(session: Session, modules: Iterable[ModuleKey]) -> None:
    BulkHandle(session).add_modules(modules)


def load_subprograms(session: Session, subprograms: Iterable[SubprogramKey]) -> None:
    rows = [(QueryHandle(session).module_id(ModuleKey(sp.module_name)), sp) for sp in subprograms]
    handle = BulkHandle(session)
    handle.add_subprograms(rows)
    handle.commit()


def load_uses(session: Session, hosts: Iterable[ModuleKey | SubprogramKey], uses: Iterable[Iterable[str]]) -> None:
    handle = BulkHandle(session)
    
    for host, use in zip(hosts, uses):
        source_module_id = QueryHandle(session).module_id(ModuleKey(host.module_name))
        source_subprogram_id = (
            QueryHandle(session).subprogram_id(host) if isinstance(host, SubprogramKey) else None
        )
        target_map = QueryHandle(session).module_ids(use)
        targets = [(u, target_map.get(u)) for u in use]
        handle.add_uses(source_module_id, source_subprogram_id, targets)
    handle.commit()


def load_signatures_from_subprogram(
    session: Session,
    subprogram_ids: Iterable[SubprogramKey],
    signatures: Iterable[Signature],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for sp_id, signature in zip(subprogram_ids, signatures):
        sp_id = query_handle.subprogram_id(sp_id)
    handle = BulkHandle(session)
    handle.add_signatures(sp_id, signature)
    handle.commit()


def load_symbol_table_from_module(
    session: Session,
    module_ids: Iterable[ModuleKey],
    mappings: Iterable[Mapping[str, FortranDeclaredEntity]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for mod_id, mapping in zip(module_ids, mappings):
        mod_id = query_handle.module_id(mod_id)
        bulk_handle.add_symbols(mod_id, None, mapping)
    bulk_handle.commit()


def load_symbol_table_from_subprogram(
    session: Session,
    subprogram_ids: Iterable[SubprogramKey],
    mappings: Iterable[Mapping[str, FortranDeclaredEntity]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for sp_id, mapping in zip(subprogram_ids, mappings):
        module_id = query_handle.module_id(ModuleKey(sp_id.module_name))
        sp_id = query_handle.subprogram_id(sp_id)
        bulk_handle.add_symbols(module_id, sp_id, mapping)
    bulk_handle.commit()


def load_symbol_references_from_module(
    session: Session,
    module_ids: Iterable[ModuleKey],
    sequences: Iterable[Sequence[SymbolReferenceRead | SymbolReferenceWrite]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for mod_id, sequence in zip(module_ids, sequences):
        mod_id = query_handle.module_id(mod_id)
        bulk_handle.add_symbol_references(None, sequence)
    bulk_handle.commit()


def load_symbol_references_from_subprogram(
    session: Session,
    subprogram_ids: Iterable[SubprogramKey],
    sequences: Iterable[Sequence[SymbolReferenceRead | SymbolReferenceWrite]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for sp_id, sequence in zip(subprogram_ids, sequences):
        sp_id = query_handle.subprogram_id(sp_id)
        bulk_handle.add_symbol_references(sp_id, sequence)
    bulk_handle.commit()


def load_calls_from_subprogram(
    session: Session,
    subprogram_ids: Iterable[SubprogramKey],
    sequences: Iterable[Sequence[FunctionCall | SubroutineCall]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for sp_id, sequence in zip(subprogram_ids, sequences):
        sp_id = query_handle.subprogram_id(sp_id)
        bulk_handle.add_calls(sp_id, sequence)
    bulk_handle.commit()


def load_ios_from_subprogram(
    session: Session,
    subprogram_ids: Iterable[SubprogramKey],
    sequences: Iterable[Sequence[IOCall]],
) -> None:
    """Load IOCall records for a given subprogram."""
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for sp_id, sequence in zip(subprogram_ids, sequences):
        sp_id = query_handle.subprogram_id(sp_id)
        bulk_handle.add_ios(sp_id, sequence)
    bulk_handle.commit()


def load_derived_types_from_module(
    session: Session,
    module_ids: Iterable[ModuleKey],
    mappings: Iterable[Mapping[str, FortranDerivedTypeDefinition]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for mod_id, mapping in zip(module_ids, mappings):
        mod_id = query_handle.module_id(mod_id)
        bulk_handle.add_derived_types(mod_id, mapping)
    bulk_handle.commit()


def load_derived_types_from_subprogram(
    session: Session,
    subprogram_ids: Iterable[SubprogramKey],
    mappings: Iterable[Mapping[str, FortranDerivedTypeDefinition]],
) -> None:
    bulk_handle = BulkHandle(session)
    query_handle = QueryHandle(session)
    for sp_id, mapping in zip(subprogram_ids, mappings):
        module_id = query_handle.module_id(ModuleKey(sp_id.module_name))
        sp_id = query_handle.subprogram_id(sp_id)
        bulk_handle.add_derived_types(module_id, mapping)
    bulk_handle.commit()