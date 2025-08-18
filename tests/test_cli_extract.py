"""Tests for the ``forge extract`` CLI command."""

from __future__ import annotations

from pathlib import Path
import shutil

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from forge.cli.main import app
from forge.core.schema import FileRecord, FileStatus, ProjectFSMStatus, ProjectState


def test_extract_parses_files_and_updates_db() -> None:
    runner = CliRunner()
    example_src = (
        Path(__file__).resolve().parents[1] / "examples" / "basic" / "src"
    )

    with runner.isolated_filesystem():
        shutil.copytree(example_src, Path("src"))

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["extract", "--max-workers", "1"])
        assert result.exit_code == 0

        # AST file should be created
        ast_path = Path(".forge/asts/src/vector_mod.f90.ast")
        assert ast_path.is_file()

        # Database should contain a record for the file and project state updated
        engine = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(engine) as session:
            fr = session.query(FileRecord).filter_by(
                source_path="src/vector_mod.f90"
            ).one()
            assert fr.status == FileStatus.EXTRACTED
            assert fr.ast_path == str(ast_path)

            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.EXTRACTED


def test_extract_accepts_max_workers_option() -> None:
    runner = CliRunner()

    example_src = (
        Path(__file__).resolve().parents[1] / "examples" / "basic" / "src"
    )

    with runner.isolated_filesystem():
        shutil.copytree(example_src, Path("src"))

        runner.invoke(app, ["init"])

        # Simply ensure the option is accepted
        result = runner.invoke(app, ["extract", "--max-workers", "2"])
        assert result.exit_code == 0

