"""Implementation of the ``forge transform`` command.

This command reads previously extracted AST artefacts, converts them into
higher level semantic information (symbol tables, call graphs, etc.) and
serialises the results as JSON files.  Metadata about the processed files
is stored in the project's SQLite database and the overall project state
is advanced to ``TRANSFORMED``.
"""

from __future__ import annotations

import datetime as _dt
import pickle
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import typer
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ...config.loader import load_config
from ...core.schema import (
    FileRecord,
    FileStatus,
    ProjectFSMStatus,
    ProjectState,
)
from ...core.models.transform_result import FileTransformResult
from ...data_models.fortran import ModuleUnit, SubprogramUnit
from ...tasks.parse.transform.scope.call_table import CallTableTransformer
from ...tasks.parse.transform.scope.derived_type_definition_table import (
    DerivedTypeDefinitionTableTransformer,
)
from ...tasks.parse.transform.scope.io_table import IOTableTransformer
from ...tasks.parse.transform.scope.reference_table import ReferenceTableTransformer
from ...tasks.parse.transform.scope.signature import SignatureTransformer
from ...tasks.parse.transform.scope.symbol_table import SymbolTableTransformer
from ...tasks.parse.transform.scope.used_modules import UsedModulesTransformer
from ...tasks.parse.transform.utils.get_name_from_node import get_name_from_node
from ...tasks.parse.transform.utils.get_subprograms import get_subprogram_part

app = typer.Typer(help="Transform ASTs into structured JSON")
console = Console()


# ---------------------------------------------------------------------------
# Helper functions


def _transform_subprogram(ast) -> SubprogramUnit:
    """Create :class:`SubprogramUnit` from a subprogram AST node."""

    return SubprogramUnit(
        symbol_table=SymbolTableTransformer.from_subprogram(ast),
        derived_types=DerivedTypeDefinitionTableTransformer.from_subprogram(ast),
        references=ReferenceTableTransformer.from_subprogram(ast),
        calls=CallTableTransformer.from_subprogram(ast),
        ios=IOTableTransformer.from_subprogram(ast),
        signature=SignatureTransformer.from_subprogram(ast),
        used_modules=list(UsedModulesTransformer.from_subprogram(ast)),
    )


def _transform_module(ast) -> ModuleUnit:
    """Create :class:`ModuleUnit` from a module AST node."""

    subprograms: dict[str, SubprogramUnit] = {}
    for sp in get_subprogram_part(ast):
        name = get_name_from_node(sp)
        subprograms[name] = _transform_subprogram(sp)

    return ModuleUnit(
        symbol_table=SymbolTableTransformer.from_module(ast),
        derived_types=DerivedTypeDefinitionTableTransformer.from_module(ast),
        references=ReferenceTableTransformer.from_module(ast),
        calls=CallTableTransformer.from_module(ast),
        ios=IOTableTransformer.from_module(ast),
        used_modules=list(UsedModulesTransformer.from_module(ast)),
        subprograms=subprograms,
    )


def _ast_to_model(ast) -> FileTransformResult:
    """Convert an extracted AST to :class:`FileTransformResult`."""

    from fparser.two.Fortran2003 import Module

    modules: dict[str, ModuleUnit] = {}

    # The extracted AST may be a Program node or a single Module.
    if isinstance(ast, Module):
        modules[get_name_from_node(ast)] = _transform_module(ast)
    else:
        for child in getattr(ast, "children", []):
            if isinstance(child, Module):
                modules[get_name_from_node(child)] = _transform_module(child)

    return FileTransformResult(modules=modules)


# ---------------------------------------------------------------------------
# CLI implementation


@app.callback(invoke_without_command=True)
def transform(
    max_workers: int = typer.Option(
        default=4,
        min=1,
        help="Maximum number of worker threads used for transformation",
        show_default=True,
    ),
) -> None:
    """Transform previously extracted AST files into JSON artefacts."""

    project_root = Path.cwd()
    load_config(project_root)  # Ensure this is a Forge project

    forge_dir = project_root / ".forge"
    db_path = forge_dir / "forge.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")

    ast_root = forge_dir / "asts"
    json_root = forge_dir / "jsons"
    json_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Collect file records to process
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()
        records = (
            session.query(FileRecord)
            .filter_by(project_id=project_state.id)
            .all()
        )

    to_process: list[FileRecord] = [r for r in records if r.status == FileStatus.EXTRACTED]

    results: list[tuple[FileRecord, Path | None, str | None]] = []

    def _process(rec: FileRecord) -> tuple[FileRecord, Path | None, str | None]:
        ast_path = project_root / rec.ast_path if rec.ast_path else None
        if not ast_path or not ast_path.exists():
            return (rec, None, "AST artifact missing")
        try:
            with open(ast_path, "rb") as f:
                ast = pickle.load(f)
            model = _ast_to_model(ast)
            rel = Path(rec.source_path)
            json_path = json_root / rel
            json_path = json_path.with_suffix(rel.suffix + ".json")
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(model.model_dump_json(indent=2))
            return (rec, json_path, None)
        except Exception as exc:  # pragma: no cover - best effort
            return (rec, None, str(exc))

    if to_process:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for res in executor.map(_process, to_process):
                results.append(res)

    # ------------------------------------------------------------------
    # Persist results
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()
        for orig_rec, json_path, error in results:
            record = (
                session.query(FileRecord)
                .filter_by(project_id=project_state.id, source_path=orig_rec.source_path)
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
        if results and all(err is None for *_rec, err in results):
            project_state.fsm_status = ProjectFSMStatus.TRANSFORMED
        session.commit()

    console.print(f"[green]Processed {len(results)} files.[/green]")


__all__ = ["app"]
