"""Implementation of the ``forge clean`` command."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import shutil

import typer
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ...core.schema import Base, ProjectState


app = typer.Typer(help="Remove generated artefacts and reset project state")
console = Console()


def _get_version() -> str:
    """Return the installed Forge version or a sensible default."""

    try:
        return version("forge")
    except PackageNotFoundError:  # pragma: no cover - best effort fallback
        return "0.0.0"


@app.callback(invoke_without_command=True)
def clean() -> None:
    """Remove the ``.forge`` directory and recreate an empty state database.

    This command keeps the ``forge.toml`` configuration file but discards all
    generated artefacts.  A fresh ``.forge`` directory and SQLite database are
    created so the project can be processed again from the beginning.
    """

    project_root = Path.cwd()
    config_path = project_root / "forge.toml"
    forge_dir = project_root / ".forge"

    if not config_path.exists():
        console.print("[red]No 'forge.toml' configuration file found.[/red]")
        raise typer.Exit(code=1)

    if forge_dir.exists():
        shutil.rmtree(forge_dir)
        console.print(f"[yellow]Removed existing directory {forge_dir}[/yellow]")

    forge_dir.mkdir()
    db_path = forge_dir / "forge.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            ProjectState(
                project_name=project_root.name,
                forge_version=_get_version(),
            )
        )
        session.commit()

    console.print(f"[green]Reinitialised project database at {db_path}[/green]")
    console.print("[bold green]Project cleaned successfully.[/bold green]")


__all__ = ["app"]
