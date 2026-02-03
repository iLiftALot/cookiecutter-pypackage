from functools import partial
from pathlib import Path
import subprocess
from typing import Annotated
from {{ cookiecutter.project_slug }}.cli.completions import (
    module_completion,
    module_objs_completion,
    obj_args_completion,
    module_details,
    _parse_call_args
)

import typer
from rich.console import Console
from rich.pretty import pprint

log_path = Path(__file__).resolve().parents[3] / "logs" / "{{ cookiecutter.project_slug }}.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text("")  # Clear log file on each run
file_console = Console(
    file=open(log_path, "a"), log_time=True, log_time_format="%Y-%m-%d %H:%M:%S"
)
terminal_console = Console(emoji=True)
app = typer.Typer(name="{{ cookiecutter.project_slug }}", help="{{cookiecutter.project_short_description}}")


def log(message: str, *args, mode: Literal["terminal", "file", "all"] = "all", **kwargs) -> None:
    """Log a message to both the log file and the terminal."""
    if mode in ("file", "all"):
        file_console.log(message, *args, **kwargs)
    if mode in ("terminal", "all"):
        terminal_console.log(message, *args, **kwargs)


def run_raw_module(module_name: str) -> None:
    log(f"Running module: {module_name}")
    module_run_name = f"src/{module_name.replace('.', '/')}.py"
    cmd = subprocess.run(["uv", "run", module_run_name], capture_output=True, text=True)
    if cmd.returncode != 0:
        log(f":x: [red]Module [b]{module_run_name}[/b] failed to run.[/red]")
        log(f"[red]{cmd.stderr}[/red]")
    else:
        log(cmd.stdout)
        log(f":white_check_mark: [green]Module [b]{module_run_name}[/b] ran successfully.[/green]")


@app.command()
def run_module(
    module: Annotated[
        str,
        typer.Argument(..., help="The module to run.", autocompletion=module_completion),
    ],
    module_obj: Annotated[
        str | None,
        typer.Argument(
            ...,
            help="The object/function within the module to run.",
            autocompletion=module_objs_completion,
        ),
    ] = None,
    obj_args: Annotated[
        list[str] | None,
        typer.Argument(
            ...,
            help="The arguments for the object/function.",
            autocompletion=obj_args_completion,
        ),
    ] = None,
):
    if not module_obj:
        run_raw_module(module)
        return
    log(
        f"Running [b][green]{{ cookiecutter.project_slug }}.{module}[/green].[yellow]{module_obj}[/yellow][/b] {'with args: ' if obj_args else ''} [blue]{','.join(obj_args) if obj_args else ''}[/blue]"
    )
    module_details_result = module_details(module, lambda: None)
    if isinstance(module_details_result, type(None)):
        log(f":x: [red][b]{{ cookiecutter.project_slug }}.{module}[/b] could not be found.[/red]")
        return
    _, import_path, module_obj_instance = module_details_result
    if not module_obj_instance:
        log(f":x: [red][b]{{ cookiecutter.project_slug }}.{module}[/b] could not be imported.[/red]")
        return
    func = getattr(module_obj_instance, module_obj, None)
    if not func or not callable(func):
        log(
            f":x: [red]Function [b]{module_obj}[/b] not found in module [b]{{ cookiecutter.project_slug }}.{module}[/b].[/red]"
        )
        return
    raw_parts = obj_args or []
    pos_args, kw_args = _parse_call_args(raw_parts)
    try:
        result = func(*pos_args, **kw_args)
    except TypeError as exc:
        log(
            f":x: [red]Failed to call[/red] [b]{import_path}.{module_obj}[/b]: [yellow]{exc}[/yellow]"
        )
        log(
            "[dim]Tip: pass keyword args as name=value (e.g., mode=show).[/dim]"
        )
        return
    log(
        f":white_check_mark: [green]Function[/green] [b][yellow]{module_obj}[/yellow][/b] [green]executed successfully.[/green]"
    )
    log("\nResult:")
    log(f"[pink]{result}[/pink]" if isinstance (result, str) else result)

    debugs = {
        "module": module,
        "module_obj": module_obj,
        "obj_args": obj_args,
        "import_path": import_path,
        "function_called": func.__name__ if func else "None",
    }

    pp(debugs)


if __name__ == "__main__":
    app()
