"""
Cookiecutter PyPackage Development Watcher

This script watches for changes in the {{cookiecutter.pypi_package_name}}/ template directory
and automatically regenerates the python_boilerplate/ output directory when changes are detected.

Usage:
    1. Run this script from the cookiecutter-pypackage repo root directory
    2. Make changes to files in {{cookiecutter.pypi_package_name}}/
    3. The script will automatically regenerate python_boilerplate/ with your changes
    4. Press Ctrl+C to stop watching

The generated python-boilerplate/ directory will be created in the repo root.
"""

import shutil
import sys
import time
from pathlib import Path

from cookiecutter.main import cookiecutter
from rich.console import Console
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

console = Console(emoji=True)
ROOT = Path(__file__).parents[2]


class ChangeHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.last_run = 0
        self.debounce_period = 2  # seconds

    def on_any_event(self, event: FileSystemEvent) -> None:
        # Ignore changes to run.py itself and directories
        if Path(event.src_path).name == "run.py" or event.is_directory:
            return

        current_time = time.time()
        if (current_time - self.last_run) > self.debounce_period:
            self.last_run = current_time
            console.print(
                f":warning: [yellow]Detected change in[/yellow]"
                f"[green]{str(Path(event.src_path).relative_to(Path.cwd()))}[/green].\n"
                "[yellow]Running cookiecutter...[/yellow]"
            )
            try:
                # The output directory is in the repo root (matches cookiecutter.json pypi_package_name)
                output_dir = ROOT / Path("python-boilerplate")
                if output_dir.exists() and output_dir.is_dir():
                    console.print(
                        "[b]:warning:[/b] [yellow]Removing existing directory:[/yellow]\n"
                        f"    [red]{output_dir}[/red]"
                    )
                    shutil.rmtree(output_dir)

                # The template is the root directory, output to repo root
                cookiecutter(
                    str(ROOT),
                    no_input=True,
                    output_dir=str(ROOT),
                )
                console.print(
                    ":white_check_mark: [green]Cookiecutter finished successfully.[/green]"
                )
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    raise e from None
                console.print(f":x: [red]Error running cookiecutter[/red]:\n{e}")

            console.print(":hourglass: [yellow]Waiting for next change...[/yellow]")


def main():
    # Watch the template directory where actual changes matter
    path = str(ROOT / Path("{{ cookiecutter.pypi_package_name }}").resolve())
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    console.print(
        ":eyes: [yellow]Watching for file changes in[/yellow]"
        f"[green][u][b]{ROOT.name / Path(path).relative_to(ROOT)}[/b][/u][/green]..."
    )
    console.print(
        ":information_source: [yellow]Output directory is[/yellow]"
        f"[green][u][b]{ROOT.name / Path('python-boilerplate').resolve().relative_to(ROOT)}[/b][/u][/green]"
    )
    console.print(
        ":green_circle: [yellow]Press[/yellow] [bold][u]Ctrl+C[/u][/bold] [yellow]to stop.[/yellow]"
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stderr.write("\r  ")  # Clear the ^C from console
        console.print("\n:stop_sign: [red]Stopping watcher...[/red]")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
