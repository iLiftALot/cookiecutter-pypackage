from functools import partial
from typing import Annotated
from python_boilerplate.cli.completions import (
    module_completion,
    module_objs_completion,
    obj_args_completion,
    module_details,
    _parse_call_args
)

import typer
from rich.console import Console
from rich.pretty import pprint


console = Console()
pp = partial(pprint, expand_all=True)

app = typer.Typer(name="{{cookiecutter.project_slug}}", help="{{cookiecutter.project_short_description}}")


@app.command()
def run_module(
    module: Annotated[
        str,
        typer.Argument(..., help="The module to run.", autocompletion=module_completion),
    ],
    module_obj: Annotated[
        str,
        typer.Argument(
            ...,
            help="The object/function within the module to run.",
            autocompletion=module_objs_completion,
        ),
    ],
    obj_args: Annotated[
        list[str] | None,
        typer.Argument(
            ...,
            help="The arguments for the object/function.",
            autocompletion=obj_args_completion,
        ),
    ] = None,
):
    console.print(
        f"Running [b][green]{{ cookiecutter.project_slug }}.{module}[/green].[yellow]{module_obj}[/yellow][/b] {'with args: ' if obj_args else ''} [blue]test{','.join(obj_args) if obj_args else ''}[/blue]"
    )
    module_details_result = module_details(module, lambda: None)
    if isinstance(module_details_result, type(None)):
        console.print(f":x: [red][b]{{ cookiecutter.project_slug }}.{module}[/b] could not be found.[/red]")
        return
    _, import_path, module_obj_instance = module_details_result
    if not module_obj_instance:
        console.print(f":x: [red][b]{{ cookiecutter.project_slug }}.{module}[/b] could not be imported.[/red]")
        return
    func = getattr(module_obj_instance, module_obj, None)
    if not func or not callable(func):
        console.print(
            f":x: [red]Function [b]{module_obj}[/b] not found in module [b]{{ cookiecutter.project_slug }}.{module}[/b].[/red]"
        )
        return
    raw_parts = obj_args or []
    pos_args, kw_args = _parse_call_args(raw_parts)
    try:
        result = func(*pos_args, **kw_args)
    except TypeError as exc:
        console.print(
            f":x: [red]Failed to call[/red] [b]{import_path}.{module_obj}[/b]: [yellow]{exc}[/yellow]"
        )
        console.print(
            "[dim]Tip: pass keyword args as name=value (e.g., mode=show).[/dim]"
        )
        return
    console.print(
        f":white_check_mark: [green]Function[/green] [b][yellow]{module_obj}[/yellow][/b] [green]executed successfully.[/green]"
    )
    console.print("\nResult:")
    console.print(f"[pink]{result}[/pink]" if isinstance (result, str) else result)

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
