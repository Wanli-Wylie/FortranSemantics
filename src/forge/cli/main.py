"""Command line entrypoint for Forge.

This module exposes the top level :data:`app` which wires together all
sub-commands implemented under :mod:`forge.cli.commands`.  The application is
built with `Typer <https://typer.tiangolo.com/>`_ and simply delegates to the
corresponding command modules.

The goal of this file is to provide a small and easy to maintain entry point
that can be invoked either via ``python -m forge`` or the ``forge`` console
script.
"""

from __future__ import annotations

import typer

# Import the individual command modules.  Each module exposes its own ``app``
# object which we register on the main application.  The modules may contain
# additional subcommands; using ``add_typer`` keeps things nicely namespaced and
# lazily imported.
from .commands import clean, extract, init, load, resolve, status, transform


# ``no_args_is_help`` ensures ``forge`` displays the help message when invoked
# without any arguments.
app = typer.Typer(no_args_is_help=True, help="Forge command line interface")


# Register subcommands.  The name provided here becomes the command name used
# on the CLI, e.g. ``forge init``.
app.add_typer(init.app, name="init", help="Initialise a new Forge project")
app.add_typer(status.app, name="status", help="Show project status")
app.add_typer(extract.app, name="extract", help="Parse source files")
app.add_typer(transform.app, name="transform", help="Transform ASTs to JSON")
app.add_typer(load.app, name="load", help="Load data into a database")
app.add_typer(resolve.app, name="resolve", help="Resolve symbols")
app.add_typer(clean.app, name="clean", help="Remove generated artefacts")


def main() -> None:
    """Run the Typer application.

    This function is used as the console script entry point.  Keeping it as a
    thin wrapper makes it straightforward to test.
    """

    app()


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    main()

