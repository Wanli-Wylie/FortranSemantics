from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import json

from forge.cli.main import app
from forge.core.schema import FileRecord, FileStatus, ProjectFSMStatus, ProjectState


def _write_sample_fortran(path: Path) -> None:
    path.write_text(
        (
            "MODULE m\n"
            "  INTEGER :: a\n"
            "CONTAINS\n"
            "  SUBROUTINE hello()\n"
            "    PRINT *, a\n"
            "  END SUBROUTINE hello\n"
            "END MODULE m\n"
        ),
        encoding="utf-8",
    )


def test_transform_generates_json_and_updates_db() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        src_dir = Path("src")
        src_dir.mkdir()
        _write_sample_fortran(src_dir / "hello.f90")

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["extract", "--max-workers", "1"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["transform", "--max-workers", "1"])
        assert result.exit_code == 0

        json_path = Path(".forge/json/src/hello.f90.json")
        assert json_path.is_file()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["modules"]["m"]["symbol_table"]["a"]["type_declared"] == "INTEGER"
        assert "m::hello" in data["subprograms"]

        engine = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(engine) as session:
            fr = session.query(FileRecord).filter_by(source_path="src/hello.f90").one()
            assert fr.status == FileStatus.TRANSFORMED
            assert fr.json_path == str(json_path)

            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.TRANSFORMED


def test_transform_accepts_max_workers_option() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("src").mkdir()
        _write_sample_fortran(Path("src/hello.f90"))

        runner.invoke(app, ["init"])
        runner.invoke(app, ["extract", "--max-workers", "1"])

        result = runner.invoke(app, ["transform", "--max-workers", "2"])
        assert result.exit_code == 0

