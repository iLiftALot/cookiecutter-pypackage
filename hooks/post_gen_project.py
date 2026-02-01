import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(
            "/Users/nicholascorbin/CodeProjects/custom/confs/.cookiecutters/cookiecutter-pypackage/hooks"
        )
    ),
)

import asyncio
from ast import literal_eval
from dataclasses import asdict
from shlex import split
from subprocess import run
from tkinter import filedialog

from scripts import (  # ty:ignore[unresolved-import]
    ButtonField,
    ComboBoxField,
    FormInputs,
    FormResult,
    GitHubRepoConfig,
    OrderedFormField,
    # CheckBoxField,
    TextField,
    LabelField,
    create_github_repository,
    show_form_dialog,
)


def run_command(command: str) -> None:
    """Run a shell command and print its output."""

    process = run(split(command), capture_output=True, text=True)
    stdout, stderr = process.stdout, process.stderr

    if process.returncode != 0:
        print(f"\nError running command: {command}")
        print(stderr)
    else:
        print(f"\n{stdout}")


async def create_gh_modal() -> FormResult:
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


async def run_hook() -> None:
    should_create_repo: bool = literal_eval("{{cookiecutter.create_github_repo}}")
    cd_command = "cd {{ cookiecutter.__project_dir }}"
    gh_commands: list[str] = []
    if (
        should_create_repo
        and (gh_modal_response := await create_gh_modal()).cancelled is False
    ):
        gh_config: GitHubRepoConfig = gh_modal_response.config
        cd_command = f"cd {gh_config.project_directory}"
        gh_commands.extend(create_github_repository(**asdict(gh_config)))

    init_commands = [
        cd_command,
        "uv sync --dev",
        *gh_commands
    ]
    for cmd in init_commands:
        run_command(cmd)


def main() -> None:
    asyncio.run(run_hook())


if __name__ == "__main__":
    print("Starting post-generation script...")
    main()
    print("\nPost-generation script completed.")
