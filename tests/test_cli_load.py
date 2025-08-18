from __future__ import annotations

from pathlib import Path
import shutil

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from forge.cli.main import app
from forge.core.schema import FileRecord, FileStatus, ProjectFSMStatus, ProjectState

from fpyevolve_core.db.schema.fortrans import (
    FortranModule,
    FortranSubprogram,
    FortranDerivedType,
)


def test_load_populates_semantic_db_and_updates_state() -> None:
    runner = CliRunner()

    example_src = (
        Path(__file__).resolve().parents[1] / "examples" / "basic" / "src"
    )

    with runner.isolated_filesystem():
        shutil.copytree(example_src, Path("src"))

        runner.invoke(app, ["init"])
        runner.invoke(app, ["extract", "--max-workers", "1"])
        runner.invoke(app, ["transform", "--max-workers", "1"])

        db_url = "sqlite:///semantics.sqlite3"
        result = runner.invoke(app, ["load", "--db-url", db_url])
        assert result.exit_code == 0

        # verify target semantics database
        engine_sem = create_engine(db_url)
        with Session(engine_sem) as session:
            mod = session.query(FortranModule).filter_by(name="vector_mod").one()
            assert mod.name == "vector_mod"
            sp = session.query(FortranSubprogram).filter_by(name="plus").one()
            assert sp.type.value == "function"
            dt = (
                session.query(FortranDerivedType)
                .filter_by(name="vector3_t", component_name="x")
                .one()
            )
            assert dt.component_type == "REAL"

        # verify local state database
        engine = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(engine) as session:
            fr = session.query(FileRecord).filter_by(
                source_path="src/vector_mod.f90"
            ).one()
            assert fr.status == FileStatus.LOADED
            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.LOADED

