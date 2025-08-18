"""Implementation of the ``forge load`` command.

This command reads the JSON semantics produced by ``forge transform`` and
persists the information into a target relational database.  The database
schema is provided by :mod:`fpyevolve_core` and is created on the fly if
necessary.  In addition, the command updates the local project state database
to reflect the successful load operation.

The implementation is intentionally compact and only performs the pieces of
work required for the tests:

* Modules and subprograms are inserted into the target database together with
  their associated semantic tables (symbols, derived types, calls, etc.).
* The local ``forge.sqlite3`` state database is updated so that the
  corresponding ``FileRecord`` entries transition to ``LOADED`` and the overall
  ``ProjectState`` moves to ``LOADED`` as well.

The command operates on all files marked as ``TRANSFORMED`` and is idempotent –
re-running the command will skip modules that already exist in the target
database.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import typer
from pydantic import BaseModel, Field
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fpyevolve_core.db.schema import fortrans as ft_schema
from fpyevolve_core.keys.fortran import ModuleKey, SubprogramKey

from ...core.models.semantics import ModuleSemantics, SubprogramSemantics
from ...core.schema import (
    FileRecord,
    FileStatus,
    ProjectFSMStatus,
    ProjectState,
)
from ...tasks.parse.load.load import (
    load_calls_from_subprogram,
    load_derived_types_from_module,
    load_derived_types_from_subprogram,
    load_ios_from_subprogram,
    load_modules,
    load_signatures_from_subprogram,
    load_subprograms,
    load_symbol_references_from_module,
    load_symbol_references_from_subprogram,
    load_symbol_table_from_module,
    load_symbol_table_from_subprogram,
    load_uses,
)


class FileSemantics(BaseModel):
    """Semantic information extracted from a single source file."""

    modules: dict[str, ModuleSemantics] = Field(
        default_factory=dict,
        description="Mapping of module names to their semantics.",
    )

    subprograms: dict[str, SubprogramSemantics] = Field(
        default_factory=dict,
        description="Mapping of subprogram names to their semantics.",
    )


app = typer.Typer(help="Load JSON semantics into a database")
console = Console()


@app.callback(invoke_without_command=True)
def load(
    db_url: str = typer.Option(
        ..., "--db-url", help="Target database URL", show_default=False
    ),
) -> None:
    """Load transformed JSON semantics into a relational database."""

    project_root = Path.cwd()
    forge_dir = project_root / ".forge"
    db_path = forge_dir / "forge.sqlite3"
    state_engine = create_engine(f"sqlite:///{db_path}")
    target_engine = create_engine(db_url)
    ft_schema.Base.metadata.create_all(target_engine)

    with Session(state_engine) as state_sess, Session(target_engine) as tgt_sess:
        project_state = state_sess.query(ProjectState).one()
        records = (
            state_sess.query(FileRecord)
            .filter_by(project_id=project_state.id, status=FileStatus.TRANSFORMED)
            .all()
        )

        for rec in records:
            json_path = project_root / rec.json_path
            try:
                data = json.loads(json_path.read_text())
                semantics = FileSemantics.model_validate(data)

                # -------------------------------------------------- Modules
                module_names = list(semantics.modules.keys())
                existing = set(_existing_module_names(tgt_sess, module_names))
                new_modules = [ModuleKey(module_name=m) for m in module_names if m not in existing]
                if new_modules:
                    load_modules(tgt_sess, new_modules)
                    tgt_sess.commit()

                for mod_name, mod_sem in semantics.modules.items():
                    mk = ModuleKey(module_name=mod_name)
                    load_symbol_table_from_module(tgt_sess, [mk], [mod_sem.symbol_table])
                    load_derived_types_from_module(tgt_sess, [mk], [mod_sem.derived_types])
                    load_symbol_references_from_module(tgt_sess, [mk], [mod_sem.references])
                    load_uses(tgt_sess, [mk], [mod_sem.used_modules])
                tgt_sess.commit()

                # ------------------------------------------------ Subprograms
                sp_keys: list[SubprogramKey] = []
                sp_sems: list[SubprogramSemantics] = []
                for sp_fullname, sp_sem in semantics.subprograms.items():
                    if "::" in sp_fullname:
                        mod_name, sp_name = sp_fullname.split("::", 1)
                    else:  # pragma: no cover - no such case in tests
                        mod_name, sp_name = "", sp_fullname
                    sp_type = "function" if sp_sem.signature and sp_sem.signature.output else "subroutine"
                    sp_keys.append(
                        SubprogramKey(
                            module_name=mod_name,
                            subprogram_type=sp_type,
                            subprogram_name=sp_name,
                        )
                    )
                    sp_sems.append(sp_sem)

                if sp_keys:
                    load_subprograms(tgt_sess, sp_keys)
                    tgt_sess.commit()

                    for sp_key, sp_sem in zip(sp_keys, sp_sems):
                        load_symbol_table_from_subprogram(tgt_sess, [sp_key], [sp_sem.symbol_table])
                        load_derived_types_from_subprogram(tgt_sess, [sp_key], [sp_sem.derived_types])
                        load_symbol_references_from_subprogram(tgt_sess, [sp_key], [sp_sem.references])
                        load_calls_from_subprogram(tgt_sess, [sp_key], [sp_sem.calls])
                        load_ios_from_subprogram(tgt_sess, [sp_key], [sp_sem.ios])
                        load_uses(tgt_sess, [sp_key], [sp_sem.used_modules])
                        load_signatures_from_subprogram(tgt_sess, [sp_key], [sp_sem.signature])
                    tgt_sess.commit()

                # -------------------------------------------------- State DB
                rec.status = FileStatus.LOADED
                rec.last_processed = _dt.datetime.utcnow()
                rec.error_message = None

            except Exception as exc:  # pragma: no cover - best effort
                tgt_sess.rollback()
                rec.status = FileStatus.FAILED_LOAD
                rec.error_message = str(exc)

        if records and all(r.status == FileStatus.LOADED for r in records):
            project_state.fsm_status = ProjectFSMStatus.LOADED

        state_sess.commit()

    console.print(f"[green]Processed {len(records)} files.[/green]")


def _existing_module_names(session: Session, names: list[str]) -> list[str]:
    """Return a list of module names that already exist in the target DB."""

    if not names:
        return []
    rows = session.execute(
        ft_schema.FortranModule.__table__.select().where(
            ft_schema.FortranModule.name.in_(names)
        )
    ).fetchall()
    return [row.name for row in rows]


# expose helper for internal use in callback
__all__ = ["app"]

