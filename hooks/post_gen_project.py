# ---------------------------------------------------------------------------
# Bootstrap: re-exec under the project venv if we're running under a
# different interpreter (e.g. Homebrew's system Python).
# ---------------------------------------------------------------------------
# ruff: noqa: E402
import os
import sys
from pathlib import Path as _Path

_VENV_PYTHON = _Path("{{ cookiecutter.__template_dir }}") / ".venv" / "bin" / "python"

if _VENV_PYTHON.is_file() and _Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), *sys.argv])

# ---------------------------------------------------------------------------

import asyncio
from ast import literal_eval
from pathlib import Path
from subprocess import run

from dotenv import load_dotenv
from iterm2_api_wrapper import get_shared_client

from cookiecutter_pypackage.scripts import (
    GitHubRepoConfig,
    GitHubRepoDialog,
    create_github_repository,
)

load_dotenv()
SUCCESS = "\x1b[1;32m"  # Green
INFO = "\x1b[1;33m"  # Yellow
ERROR = "\x1b[1;31m"  # Red
TERMINATOR = "\x1b[0m"  # Reset color


def run_command(command: str, cwd: str | Path | None = None) -> None:
    """Run a shell command and print its output.

    Args:
        command: The shell command to run.
        cwd: Working directory for the command.
    """
    process = run(command, capture_output=True, text=True, shell=True, cwd=cwd)
    stdout, stderr = process.stdout, process.stderr

    if process.returncode != 0:
        print(f"Error running command: {command}")
        print(stderr)
    else:
        if stdout.strip():
            print(f"\n{stdout}")


async def run_hook() -> None:
    debug: bool = literal_eval("{{cookiecutter.__debug}}")
    project_dir = Path.cwd().parent.name / Path.cwd().relative_to(
        "{{ cookiecutter.__project_dir }}"
    )
    print(f"{INFO}Project directory: {project_dir}{TERMINATOR}")
    # project_name = "{{ cookiecutter.pypi_package_name }}"
    cd_command = f"cd '{project_dir}'"
    gh_commands: list[str] = []
    gh_username, gh_repo_name = ("{{ cookiecutter.__gh_slug }}").split("/")
    gh_description = "{{ cookiecutter.project_short_description }}"
    gh_dialog = GitHubRepoDialog(
        project_dir=str(project_dir),
        username=gh_username,
        repo_name=gh_repo_name,
        description=gh_description,
        debug=debug,
    )
    should_create_repo: bool = "{{cookiecutter.create_github_repo}}" == "yes"

    if should_create_repo:
        result = gh_dialog.show()

        if result.cancelled:
            print(INFO + "GitHub repository creation cancelled by user." + TERMINATOR)
            return

        gh_config: GitHubRepoConfig = result.to_config()
        project_dir = gh_config.directory
        cd_command = f"cd '{project_dir}'"
        gh_commands.extend(create_github_repository(**gh_config.asdict()))

    # Commands that need to run in the project directory
    init_commands = [
        cd_command,
        "uv sync --dev",
        "source .venv/bin/activate",
        *gh_commands,
    ]
    # exit(0)
    client = await get_shared_client(new_tab=True)
    state = await client.get_state_async()
    for cmd in init_commands:
        print(f">>> {INFO}{cmd}{TERMINATOR}")
        try:
            output = await state.run_command(cmd, timeout=15)
            if output.strip():
                print(output)
        except TimeoutError:
            print(ERROR + f"Command timed out: {cmd}" + TERMINATOR)
        except Exception as e:
            print(ERROR + f"Command failed: {cmd}\nError: {e}" + TERMINATOR)


def main() -> None:
    asyncio.run(run_hook())


if __name__ == "__main__":
    print(INFO + "Starting post-generation script..." + TERMINATOR)
    main()
    print(SUCCESS + "Post-generation script completed." + TERMINATOR)
