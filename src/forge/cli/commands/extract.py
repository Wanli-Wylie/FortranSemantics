"""Implementation of the ``forge extract`` command.

This command scans the project's configured source directories, parses any
Fortran source files and stores their Abstract Syntax Trees (ASTs) on disk.
Metadata about processed files is persisted in the project's SQLite database
and the overall project state is updated to ``EXTRACTED``.

The command accepts an optional ``--max-workers`` argument to control the level
of parallelism used when parsing files.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import datetime as _dt
import fnmatch
import glob
import hashlib
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
from ...tasks.parse.extract import extract_from_fortran_string


app = typer.Typer(help="Parse source files")
console = Console()


def _collect_source_files(project_root: Path, config) -> list[Path]:
    """Return a list of source files based on include/exclude patterns."""

    files: list[Path] = []
    for src_dir in config.sources.source_dirs:
        base = project_root / src_dir
        for pattern in config.sources.include_patterns:
            glob_pattern = str(base / pattern)
            for file_name in glob.glob(glob_pattern, recursive=True):
                candidate = Path(file_name)
                rel = candidate.relative_to(project_root)
                # Apply exclusion patterns
                if any(
                    fnmatch.fnmatch(str(rel), pat)
                    for pat in config.sources.exclude_patterns
                ):
                    continue
                files.append(candidate)
    return files


def _hash_text(text: str, encoding: str) -> str:
    return hashlib.sha256(text.encode(encoding)).hexdigest()


@app.callback(invoke_without_command=True)
def extract(
    max_workers: int = typer.Option(
        default=4,
        min=1,
        help="Maximum number of worker threads used for parsing",
        show_default=True,
    )
) -> None:
    """Parse Fortran source files and persist their ASTs."""

    project_root = Path.cwd()
    config = load_config(project_root)

    forge_dir = project_root / ".forge"
    db_path = forge_dir / "forge.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")

    # Load existing file records so we can skip unchanged files
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()
        existing = {
            Path(rec.source_path): rec
            for rec in session.query(FileRecord)
            .filter_by(project_id=project_state.id)
            .all()
        }

    ast_root = forge_dir / "asts"
    ast_root.mkdir(parents=True, exist_ok=True)

    source_files = _collect_source_files(project_root, config)

    # Determine which files need processing
    to_process: list[tuple[Path, Path, str, str]] = []
    skipped = 0
    for file_path in source_files:
        rel = file_path.relative_to(project_root)
        text = file_path.read_text(encoding=config.parser.encoding)
        file_hash = _hash_text(text, config.parser.encoding)

        rec = existing.get(rel)
        ast_file = ast_root / rel
        ast_file = ast_file.with_suffix(file_path.suffix + ".ast")
        if (
            rec
            and rec.file_hash == file_hash
            and rec.status == FileStatus.EXTRACTED
            and ast_file.exists()
        ):
            skipped += 1
            continue

        to_process.append((file_path, rel, text, file_hash))

    def _parse_file(args: tuple[Path, Path, str, str]):
        path, rel, text, file_hash = args
        try:
            ast = extract_from_fortran_string(text)
            ast_path = ast_root / rel
            ast_path = ast_path.with_suffix(path.suffix + ".ast")
            ast_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ast_path, "wb") as f:
                pickle.dump(ast, f)

            return (rel, file_hash, ast_path, None)
        except Exception as exc:  # pragma: no cover - best effort
            return (rel, file_hash, None, str(exc))

    results: list[tuple[Path, str, Path | None, str | None]] = []
    if to_process:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for res in executor.map(_parse_file, to_process):
                results.append(res)

    # Persist results to the database
    with Session(engine) as session:
        project_state = session.query(ProjectState).one()

        for rel, file_hash, ast_path, error in results:
            rel_str = str(rel)
            last_modified = _dt.datetime.utcfromtimestamp(
                (project_root / rel).stat().st_mtime
            )

            record = (
                session.query(FileRecord)
                .filter_by(project_id=project_state.id, source_path=rel_str)
                .one_or_none()
            )

            status = FileStatus.EXTRACTED if error is None else FileStatus.FAILED_EXTRACT

            if record is None:
                record = FileRecord(
                    project_id=project_state.id,
                    source_path=rel_str,
                    file_hash=file_hash,
                    status=status,
                    ast_path=str(ast_path.relative_to(project_root)) if ast_path else None,
                    last_modified=last_modified,
                    last_processed=_dt.datetime.utcnow() if error is None else None,
                    error_message=error,
                )
                session.add(record)
            else:
                record.file_hash = file_hash
                record.status = status
                record.ast_path = (
                    str(ast_path.relative_to(project_root)) if ast_path else None
                )
                record.last_modified = last_modified
                record.last_processed = _dt.datetime.utcnow() if error is None else record.last_processed
                record.error_message = error

        if results and all(err is None for *_rest, err in results):
            project_state.fsm_status = ProjectFSMStatus.EXTRACTED

        session.commit()

    console.print(
        f"[green]Processed {len(results)} files (skipped {skipped}).[/green]"
    )


__all__ = ["app"]

