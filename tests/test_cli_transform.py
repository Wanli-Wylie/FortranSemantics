from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from forge.cli.main import app
from forge.core.schema import FileRecord, FileStatus, ProjectFSMStatus, ProjectState


def _write_sample_fortran(path: Path) -> None:
    path.write_text(
        """module m
  integer :: a
contains
  subroutine s()
    a = 1
  end subroutine s
end module m
""",
        encoding="utf-8",
    )


def test_transform_generates_json_and_updates_db() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        src_dir = Path("src")
        src_dir.mkdir()
        _write_sample_fortran(src_dir / "mod.f90")

        assert runner.invoke(app, ["init"]).exit_code == 0
        assert runner.invoke(app, ["extract", "--max-workers", "1"]).exit_code == 0

        result = runner.invoke(app, ["transform", "--max-workers", "1"])
        assert result.exit_code == 0

        json_path = Path(".forge/jsons/src/mod.f90.json")
        assert json_path.is_file()

        data = json.loads(json_path.read_text())
        # symbol table should contain variable 'a'
        assert (
            data["modules"]["m"]["symbol_table"]["a"]["type_declared"]
            == "INTEGER"
        )

        engine = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(engine) as session:
            fr = session.query(FileRecord).filter_by(source_path="src/mod.f90").one()
            assert fr.status == FileStatus.TRANSFORMED
            assert fr.json_path == str(json_path)

            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.TRANSFORMED
