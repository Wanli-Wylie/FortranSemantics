"""Implementation of the ``forge transform`` command.

This command reads the previously extracted Abstract Syntax Trees (ASTs)
from the ``.forge/asts`` directory, converts them into a simplified JSON
representation and stores the result under ``.forge/json``.

The command updates the project's SQLite database recording the location
of the generated JSON artefacts and marks the processed files with the
``TRANSFORMED`` status.  Any failures are recorded with
``FAILED_TRANSFORM``.

A ``--max-workers`` option controls the level of parallelism used during
transformation, mirroring the behaviour of the ``forge extract`` command
for consistency.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import datetime as _dt
import json
import pickle

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


app = typer.Typer(help="Transform ASTs to JSON")
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
    """Convert extracted AST files into JSON artefacts."""

    project_root = Path.cwd()
    # Ensure configuration exists; the returned object is not used further but
    # loading it validates that we're inside a Forge project.
    load_config(project_root)

    forge_dir = project_root / ".forge"
    db_path = forge_dir / "forge.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")

    json_root = forge_dir / "json"
    json_root.mkdir(parents=True, exist_ok=True)

    # Gather all file records so we know which ASTs need processing.
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()
        records = (
            session.query(FileRecord)
            .filter_by(project_id=project_state.id)
            .all()
        )

    to_process: list[tuple[str, Path, Path]] = []
    skipped = 0

    for rec in records:
        if not rec.ast_path:
            continue
        ast_path = project_root / rec.ast_path
        if not ast_path.exists():
            continue

        rel_source = Path(rec.source_path)
        json_path = json_root / rel_source
        json_path = json_path.with_suffix(rel_source.suffix + ".json")

        if (
            rec.status == FileStatus.TRANSFORMED
            and rec.json_path
            and (project_root / rec.json_path).exists()
        ):
            skipped += 1
            continue

        to_process.append((rec.source_path, ast_path, json_path))

    def _transform_file(args: tuple[str, Path, Path]):
        source_rel, ast_path, json_path = args
        try:
            with open(ast_path, "rb") as f:
                ast = pickle.load(f)
            data = {"ast_type": type(ast).__name__}
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(data), encoding="utf-8")
            return (source_rel, json_path, None)
        except Exception as exc:  # pragma: no cover - best effort
            return (source_rel, None, str(exc))

    results: list[tuple[str, Path | None, str | None]] = []
    if to_process:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for res in executor.map(_transform_file, to_process):
                results.append(res)

    # Persist transformation results.
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()
        for rel, json_path, error in results:
            record = (
                session.query(FileRecord)
                .filter_by(project_id=project_state.id, source_path=rel)
                .one()
            )

            if error is None:
                record.status = FileStatus.TRANSFORMED
                record.json_path = str(json_path.relative_to(project_root)) if json_path else None
                record.last_processed = _dt.datetime.utcnow()
                record.error_message = None
            else:
                record.status = FileStatus.FAILED_TRANSFORM
                record.json_path = None
                record.error_message = error

        if results and all(err is None for *_rest, err in results):
            project_state.fsm_status = ProjectFSMStatus.TRANSFORMED

        session.commit()

    console.print(f"[green]Processed {len(results)} files (skipped {skipped}).[/green]")


__all__ = ["app"]
