"""Tests for the ``forge extract`` CLI command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from forge.cli.main import app
from forge.core.schema import FileRecord, FileStatus, ProjectFSMStatus, ProjectState


def _write_sample_fortran(path: Path) -> None:
    path.write_text(
        """program hello\nprint *, 'hello'\nend program hello\n""",
        encoding="utf-8",
    )


def test_extract_parses_files_and_updates_db() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        src_dir = Path("src")
        src_dir.mkdir()
        _write_sample_fortran(src_dir / "hello.f90")

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["extract", "--max-workers", "1"])
        assert result.exit_code == 0

        # AST file should be created
        ast_path = Path(".forge/asts/src/hello.f90.ast")
        assert ast_path.is_file()

        # Database should contain a record for the file and project state updated
        engine = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(engine) as session:
            fr = session.query(FileRecord).filter_by(source_path="src/hello.f90").one()
            assert fr.status == FileStatus.EXTRACTED
            assert fr.ast_path == str(ast_path)

            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.EXTRACTED


def test_extract_accepts_max_workers_option() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("src").mkdir()
        _write_sample_fortran(Path("src/hello.f90"))

        runner.invoke(app, ["init"])

        # Simply ensure the option is accepted
        result = runner.invoke(app, ["extract", "--max-workers", "2"])
        assert result.exit_code == 0

