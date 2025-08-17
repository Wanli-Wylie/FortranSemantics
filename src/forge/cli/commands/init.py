# src/forge/cli/commands/init.py

from pathlib import Path
import typer
from rich.console import Console

# 注意：每个命令模块都创建一个新的 Typer 实例
# 这是一种模块化组织方式，然后在 main.py 中被 `app.add_typer` 注册
app = typer.Typer()
console = Console()

@app.callback(invoke_without_command=True)
def init():
    pass