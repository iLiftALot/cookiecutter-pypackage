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
import threading
import time
import traceback
from pathlib import Path

from cookiecutter.hooks import logger as cookiecutter_logger
from cookiecutter.main import cookiecutter
from rich.console import Console
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

console = Console(emoji=True)
ROOT = Path(__file__).parents[2]
WATCH_PATH = ROOT / "{{cookiecutter.pypi_package_name}}"
OUTPUT_PATH = ROOT / "python-boilerplate"
REL_WATCH_PATH = ROOT.name / WATCH_PATH.relative_to(ROOT)
REL_OUTPUT_PATH = ROOT.name / OUTPUT_PATH.relative_to(ROOT)
STOP_EVENT = threading.Event()


class ChangeHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.stop_event: threading.Event = STOP_EVENT
        self.last_run = 0.0
        self.debounce_period = 2  # seconds
        # Disable hook logging to avoid exit messages
        cookiecutter_logger.disabled = True

    def on_any_event(self, event: FileSystemEvent) -> None:
        # Ignore changes to run.py itself and directories
        if Path(event.src_path).name == "run.py" or event.is_directory:
            return

        if self.stop_event.is_set():
            return

        current_time = time.time()
        if (current_time - self.last_run) > self.debounce_period:
            self.last_run = current_time
            console.print(
                f":warning: [yellow]Detected change in[/yellow] "
                f"[green]{str(Path(event.src_path).relative_to(Path.cwd()))}[/green].\n"
                "[yellow]Running cookiecutter...[/yellow]"
            )
            try:
                # The output directory is in the repo root (matches cookiecutter.json pypi_package_name)
                if OUTPUT_PATH.exists() and OUTPUT_PATH.is_dir():
                    console.print(
                        "[b]:warning:[/b] [yellow]Removing existing directory:[/yellow]\n"
                        f"    [red]{OUTPUT_PATH}[/red]"
                    )
                    shutil.rmtree(OUTPUT_PATH)

                # The template is the root directory, output to repo root
                cookiecutter(
                    str(ROOT),
                    no_input=True,
                    output_dir=str(ROOT),
                )
                if self.stop_event.is_set():
                    return
                console.print(
                    ":white_check_mark: [green]Cookiecutter finished successfully.[/green]"
                )
            except Exception as e:
                if isinstance(e, KeyboardInterrupt) or self.stop_event.is_set():
                    return
                console.print(f":x: [red]Error running cookiecutter[/red]:\n{e}")
                traceback.print_exception(type(e), e, e.__traceback__, colorize=True)  # type: ignore

            if not self.stop_event.is_set():
                console.print(":hourglass: [yellow]Waiting for next change...[/yellow]")


def main():
    # Watch the template directory where actual changes matter
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler=event_handler, path=str(WATCH_PATH), recursive=True)
    observer.start()
    console.print(
        ":eyes: [yellow]Watching for file changes in[/yellow] "
        f"[green][u][b]{REL_WATCH_PATH}[/b][/u][/green]..."
    )
    console.print(
        ":information_source: [yellow]Output directory is[/yellow] "
        f"[green][u][b]{REL_OUTPUT_PATH}[/b][/u][/green]"
    )
    console.print(
        ":green_circle: [yellow]Press[/yellow] [bold][u]Ctrl+C[/u][/bold] [yellow]to stop.[/yellow]"
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        STOP_EVENT.set()
        sys.stderr.write("\r  \r")  # Clear the ^C from console
        console.print(":stop_sign: [red]Stopping watcher...[/red]")
        observer.stop()

    observer.join(timeout=5)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
