from __future__ import annotations

"""CLI command for the ``forge resolve`` sub-command.

This command performs the final post-processing step of the Forge pipeline.
It operates directly on the semantic target database produced by the ``load``
command and runs a number of resolution tasks.  Once complete the local project
state is advanced to ``RESOLVED``.
"""

from pathlib import Path

import typer
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ...core.schema import ProjectState, ProjectFSMStatus
from ...tasks.resolve import (
    AddResultVarTask,
    CalleeNameParseTask,
    CallReferenceUpdateTask,
    PartRefUpdateTask,
    SymbolReferenceUpdateTask,
)

app = typer.Typer(help="Resolve symbols")
console = Console()


@app.callback(invoke_without_command=True)
def resolve(
    db_url: str = typer.Option(
        ..., "--db-url", help="Target database URL", show_default=False
    ),
) -> None:
    """Run all resolution tasks against the target database."""

    project_root = Path.cwd()
    forge_dir = project_root / ".forge"
    state_db = forge_dir / "forge.sqlite3"

    state_engine = create_engine(f"sqlite:///{state_db}")
    target_engine = create_engine(db_url)

    # Run the individual resolution tasks sequentially on the target DB
    with Session(target_engine) as session:
        tasks = [
            AddResultVarTask(session),
            SymbolReferenceUpdateTask(session),
            PartRefUpdateTask(session),
            CalleeNameParseTask(session),
            CallReferenceUpdateTask(session),
        ]
        for task in tasks:
            task.execute()

    # Update the local project state to reflect completion
    with Session(state_engine) as session:
        project_state = session.query(ProjectState).one()
        project_state.fsm_status = ProjectFSMStatus.RESOLVED
        session.commit()

    console.print("[green]Resolution completed.[/green]")


__all__ = ["app"]
