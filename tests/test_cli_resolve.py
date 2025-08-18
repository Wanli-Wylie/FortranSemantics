from __future__ import annotations

from pathlib import Path
import shutil

from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from forge.cli.main import app
from forge.core.schema import ProjectState, ProjectFSMStatus
from fpyevolve_core.db.schema.fortrans import (
    FortranCall,
    FortranModule,
    FortranSubprogram,
    FortranSymbolReference,
)


def test_resolve_updates_references_and_state() -> None:
    runner = CliRunner()
    example_src = Path(__file__).resolve().parents[1] / "examples" / "basic" / "src"

    with runner.isolated_filesystem():
        shutil.copytree(example_src, Path("src"))

        runner.invoke(app, ["init"])
        runner.invoke(app, ["extract", "--max-workers", "1"])
        runner.invoke(app, ["transform", "--max-workers", "1"])

        db_url = "sqlite:///semantics.sqlite3"
        runner.invoke(app, ["load", "--db-url", db_url])
        result = runner.invoke(app, ["resolve", "--db-url", db_url])
        assert result.exit_code == 0

        # Check semantic database updates
        eng_sem = create_engine(db_url)
        with Session(eng_sem) as session:
            call = (
                session.query(FortranCall)
                .join(FortranSubprogram, FortranCall.caller_id == FortranSubprogram.id)
                .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
                .filter(
                    FortranModule.name == "physics_mod",
                    FortranSubprogram.name == "force_pressure",
                )
                .one()
            )
            assert call.callee is not None
            assert call.callee.name == "area_circle"

            ref = (
                session.query(FortranSymbolReference)
                .join(FortranSubprogram, FortranSymbolReference.subprogram_id == FortranSubprogram.id)
                .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
                .filter(
                    FortranModule.name == "physics_mod",
                    FortranSubprogram.name == "potential_energy",
                    FortranSymbolReference.name == "constants",
                )
                .one()
            )
            assert ref.symbol is not None
            assert ref.symbol.name == "constants"

        # Check project state
        eng_state = create_engine("sqlite:///.forge/forge.sqlite3")
        with Session(eng_state) as session:
            ps = session.query(ProjectState).one()
            assert ps.fsm_status == ProjectFSMStatus.RESOLVED
