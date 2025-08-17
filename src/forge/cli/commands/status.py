# src/forge/cli/commands/status.py

import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def status():
    pass