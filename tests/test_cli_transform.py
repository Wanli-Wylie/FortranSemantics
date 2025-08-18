from __future__ import annotations

from pathlib import Path
import shutil

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import json

from forge.cli.main import app
from forge.core.schema import FileRecord, FileStatus, ProjectFSMStatus, ProjectState


def test_transform_generates_json_and_updates_db() -> None:
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

        result = runner.invoke(app, ["transform", "--max-workers", "1"])
        assert result.exit_code == 0

        json_path = Path(".forge/json/src/vector_mod.f90.json")
        assert json_path.is_file()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert (
            data["modules"]["vector_mod"]["derived_types"]["vector3_t"]["declared_components"]["x"]["type_declared"]
            == "REAL"
        )
        assert "vector_mod::plus" in data["subprograms"]

        engine = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(engine) as session:
            fr = session.query(FileRecord).filter_by(
                source_path="src/vector_mod.f90"
            ).one()
            assert fr.status == FileStatus.TRANSFORMED
            assert fr.json_path == str(json_path)

            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.TRANSFORMED


def test_transform_accepts_max_workers_option() -> None:
    runner = CliRunner()

    example_src = (
        Path(__file__).resolve().parents[1] / "examples" / "basic" / "src"
    )

    with runner.isolated_filesystem():
        shutil.copytree(example_src, Path("src"))

        runner.invoke(app, ["init"])
        runner.invoke(app, ["extract", "--max-workers", "1"])

        result = runner.invoke(app, ["transform", "--max-workers", "2"])
        assert result.exit_code == 0

