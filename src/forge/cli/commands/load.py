# src/forge/cli/commands/clean.py

import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def load():
    pass