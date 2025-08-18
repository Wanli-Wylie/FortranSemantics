"""Implementation of the ``forge transform`` command.

This command reads previously extracted Abstract Syntax Trees (ASTs) and
produces a JSON based semantic representation for each source file.  The
resulting JSON files are stored under ``.forge/json`` and the project's state
database is updated accordingly.

The transformation step populates ``ModuleSemantics`` and
``SubprogramSemantics`` instances by leveraging the table transformer
utilities under ``forge.tasks.parse.transform``.  These helpers walk the AST and
construct symbol tables, reference lists and other semantic data which is then
serialised to JSON.  The command mirrors the real project and provides the
``--max-workers`` parameter to control the level of concurrency.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import datetime as _dt
import pickle
import json

import typer
from pydantic import BaseModel, Field
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fparser.two.Fortran2003 import Module, Subroutine_Subprogram, Function_Subprogram

from ...core.models.semantics import ModuleSemantics, SubprogramSemantics
from ...core.schema import (
    FileRecord,
    FileStatus,
    ProjectFSMStatus,
    ProjectState,
)
from ...tasks.parse.transform.scope import (
    SymbolTableTransformer,
    DerivedTypeDefinitionTableTransformer,
    ReferenceTableTransformer,
    CallTableTransformer,
    IOTableTransformer,
    SignatureTransformer,
    UsedModulesTransformer,
)
from ...tasks.parse.transform.utils import get_subprogram_part


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


app = typer.Typer(help="Transform ASTs into JSON semantics")
console = Console()


@app.callback(invoke_without_command=True)
def transform(
    max_workers: int = typer.Option(
        default=4,
        min=1,
        help="Maximum number of worker threads used for transformation",
        show_default=True,
    )
) -> None:
    """Convert extracted ASTs to a JSON based semantic representation."""

    project_root = Path.cwd()
    forge_dir = project_root / ".forge"
    db_path = forge_dir / "forge.sqlite3"
    json_root = forge_dir / "json"
    json_root.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{db_path}")

    # Gather all file records that have an extracted AST ready for processing
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()
        records = (
            session.query(FileRecord)
            .filter_by(project_id=project_state.id, status=FileStatus.EXTRACTED)
            .all()
        )

    to_process: list[tuple[Path, Path, Path]] = []
    for rec in records:
        if not rec.ast_path:
            continue
        ast_path = project_root / rec.ast_path
        json_path = json_root / rec.source_path
        json_path = json_path.with_suffix(Path(rec.source_path).suffix + ".json")
        to_process.append((Path(rec.source_path), ast_path, json_path))

    def _transform_file(args: tuple[Path, Path, Path]):
        rel, ast_path, json_path = args
        try:
            with open(ast_path, "rb") as f:
                ast = pickle.load(f)

            semantics = FileSemantics()

            def handle_module(mod: Module) -> None:
                name = str(mod.content[0].items[1])
                print(f"Processing module: {name}")
                modulesem = ModuleSemantics(
                    symbol_table=SymbolTableTransformer.from_module(mod),
                    derived_types=DerivedTypeDefinitionTableTransformer.from_module(mod),
                    references=ReferenceTableTransformer.from_module(mod),
                    calls=CallTableTransformer.from_module(mod),
                    used_modules=sorted(UsedModulesTransformer.from_module(mod)),
                )
                semantics.modules[name] = modulesem
                
                for sp in get_subprogram_part(mod):
                    handle_subprogram(sp, name)

            def handle_subprogram(
                sp: Subroutine_Subprogram | Function_Subprogram, module_name: str | None = None
            ) -> None:
                name = str(sp.content[0].items[1])
                key = f"{module_name}::{name}" if module_name else name
                subsem = SubprogramSemantics(
                    symbol_table=SymbolTableTransformer.from_subprogram(sp),
                    derived_types=DerivedTypeDefinitionTableTransformer.from_subprogram(sp),
                    references=ReferenceTableTransformer.from_subprogram(sp),
                    calls=CallTableTransformer.from_subprogram(sp),
                    ios=IOTableTransformer.from_subprogram(sp),
                    signature=SignatureTransformer.from_subprogram(sp),
                    used_modules=sorted(UsedModulesTransformer.from_subprogram(sp)),
                )
                semantics.subprograms[key] = subsem

            for node in getattr(ast, "content", []):
                if isinstance(node, Module):
                    handle_module(node)
                elif isinstance(node, (Subroutine_Subprogram, Function_Subprogram)):
                    handle_subprogram(node)

            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(semantics.model_dump(), f, indent=4)
            return (rel, json_path, None)
        except Exception as exc:  # pragma: no cover - best effort
            return (rel, None, str(exc))

    results: list[tuple[Path, Path | None, str | None]] = []
    if to_process:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for res in executor.map(_transform_file, to_process):
                results.append(res)

    # Persist results to the database
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()

        for rel, json_path, error in results:
            record = (
                session.query(FileRecord)
                .filter_by(project_id=project_state.id, source_path=str(rel))
                .one()
            )

            if error is None and json_path is not None:
                record.status = FileStatus.TRANSFORMED
                record.json_path = str(json_path.relative_to(project_root))
                record.last_processed = _dt.datetime.utcnow()
                record.error_message = None
            else:
                record.status = FileStatus.FAILED_TRANSFORM
                record.error_message = error

        if results and all(err is None for *_rest, err in results):
            project_state.fsm_status = ProjectFSMStatus.TRANSFORMED

        session.commit()

    console.print(f"[green]Processed {len(results)} files.[/green]")


__all__ = ["app"]

