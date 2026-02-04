import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import asdict
from subprocess import run
from tkinter import filedialog
import asyncio
from cookiecutter_pypackage.scripts import (
    ButtonField,
    ComboBoxField,
    FormInputs,
    FormResult,
    GitHubRepoConfig,
    LabelField,
    OrderedFormField,
    # CheckBoxField,
    TextField,
    create_github_repository,
    show_form_dialog,
)
from iterm2_api_wrapper import create_iterm_client


load_dotenv()
SUCCESS = "\x1b[1;32m"  # Green
INFO = "\x1b[1;33m"     # Yellow
ERROR = "\x1b[1;31m"    # Red
TERMINATOR = "\x1b[0m"  # Reset color


def run_command(command: str, cwd: str | Path | None = None) -> None:
    """Run a shell command and print its output.

    Args:
        command: The shell command to run.
        cwd: Working directory for the command.
    """
    # Use shell=True for shell built-ins and complex commands
    process = run(command, capture_output=True, text=True, shell=True, cwd=cwd)
    stdout, stderr = process.stdout, process.stderr

    if process.returncode != 0:
        print(f"Error running command: {command}")
        print(stderr)
    else:
        if stdout.strip():
            print(f"\n{stdout}")


def create_gh_modal() -> FormResult:
    title = "GitHub Settings"
    subtitle = "Git Repository Configuration"
    initial_dir = os.getenv("PWD", os.getcwd())
    ordered_fields: list[OrderedFormField] = [
        OrderedFormField(
            field_tuple=ButtonField(
                field_label="Submit",
                help_text="Submit the GitHub repository settings.",
                callback_function=None,
            ),
            xy=(7, 0),
        ),
        OrderedFormField(
            field_tuple=ButtonField(
                field_label="Cancel",
                help_text="Cancel and do not create a GitHub repository.",
                callback_function=None,
            ),
            xy=(7, 1),
        ),
        OrderedFormField(
            field_tuple=ComboBoxField(
                field_label="GitHub Repo Visibility",
                default_value="private",
                help_text="Public/Private for remote repo visibility, or local for non-remote.",
                options=["public", "private", "local"],
            ),
            xy=(6, 0),
        ),
        OrderedFormField(
            field_tuple=LabelField(field_label="GitHub Repository Settings"),
            xy=(0, 0),
        ),
        OrderedFormField(
            field_tuple=TextField(
                field_label="",
                default_value="{{ cookiecutter.__project_dir }}",
                help_text="",
            ),
            xy=(0, 1),
            key="project_directory",
        ),
        OrderedFormField(
            field_tuple=ButtonField(
                field_label="Project Directory",
                help_text="Path to the project directory.",
                callback_function=(
                    lambda: filedialog.askdirectory(
                        initialdir=initial_dir,
                        mustexist=True,
                        title="Select Project Directory",
                    )
                ),
                bind_to="project_directory",
            ),
            xy=(0, 1),
        ),
        OrderedFormField(
            field_tuple=TextField(
                field_label="GitHub Username",
                default_value="iLiftALot",
                help_text="GitHub username for the repository.",
            ),
            xy=(2, 0),
        ),
        OrderedFormField(
            field_tuple=TextField(
                field_label="GitHub Repo Branch",
                default_value="master",
                help_text="Branch name for the repository.",
            ),
            xy=(3, 0),
        ),
        OrderedFormField(
            field_tuple=TextField(
                field_label="GitHub Repo Name",
                default_value="{{ cookiecutter.__gh_slug }}",
                help_text="Name of the GitHub repository.",
            ),
            xy=(4, 0),
        ),
        OrderedFormField(
            field_tuple=TextField(
                field_label="GitHub Repo Description",
                default_value="{{ cookiecutter.project_short_description }}",
                help_text="Description of the GitHub repository.",
            ),
            xy=(5, 0),
        ),
    ]

    form_settings: FormInputs = FormInputs(ordered_fields=ordered_fields)

    gh_modal_response: FormResult = show_form_dialog(
        title=title,
        subtitle=subtitle,
        **form_settings,
    )

    return gh_modal_response


def run_hook() -> None:
    should_create_repo: bool = "{{cookiecutter.create_github_repo}}" == "yes"
    project_dir = Path("{{ cookiecutter.__project_dir }}")
    cd_command = f"cd {project_dir}"
    gh_commands: list[str] = []

    if (
        should_create_repo
        and (gh_modal_response := create_gh_modal()).cancelled is False
    ):
        gh_config: GitHubRepoConfig = gh_modal_response.config
        project_dir = Path(gh_config.project_directory or project_dir)
        cd_command = f"cd {project_dir}"
        gh_commands.extend(create_github_repository(**asdict(gh_config)))

    # Commands that need to run in the project directory
    init_commands = [
        cd_command,
        "uv sync --dev",
        "source .venv/bin/activate",
        *gh_commands,
    ]
    with create_iterm_client(new_tab=True) as client:
        state = client.get_state()
        for cmd in init_commands:
            print(f">>> {INFO}{cmd}{TERMINATOR}")
            # Use run_coroutine_threadsafe since state.run_command is async
            # and must run on the client's internal event loop
            future = asyncio.run_coroutine_threadsafe(
                state.run_command(cmd), client.loop
            )
            try:
                output = future.result(timeout=120)
                if output.strip():
                    print(output)
            except TimeoutError:
                print(ERROR + f"Command timed out: {cmd}" + TERMINATOR)
            except Exception as e:
                print(ERROR + f"Command failed: {cmd}\nError: {e}" + TERMINATOR)


def main() -> None:
    run_hook()


if __name__ == "__main__":
    print(INFO + "Starting post-generation script..." + TERMINATOR)
    main()
    print(SUCCESS + "Post-generation script completed." + TERMINATOR)
