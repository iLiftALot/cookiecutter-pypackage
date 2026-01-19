import sys
from pathlib import Path

# Append project directory to sys.path
sys.path.insert(
    0,
    str(Path("~/CodeProjects/cookiecutter-pypackage/hooks").expanduser()),
)

import asyncio
import textwrap
from dataclasses import asdict
from ast import literal_eval
from shlex import split
from subprocess import run
from scripts import (  # ty:ignore[unresolved-import]
    GlobaliTermState,
    GitHubRepoConfig,
    create_github_repository,
    send_command_to_iterm,
    setup_session,
    show_form_dialog,
    FormResult,
    FormInputs,
    ButtonField,
    TextField,
    ComboBoxField,
    # CheckBoxField,
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


def reveal_hotkey_window():
    """Reveal the iTerm2 hotkey window using AppleScript."""
    script = """
    tell application "iTerm2"
        tell current window
            reveal hotkey window
        end tell
    end tell
    """
    run(["osascript", "-e", script], check=True)


def create_gh_modal(iterm: GlobaliTermState) -> FormResult:
    title = "GitHub Settings"
    subtitle = "Git Repository Configuration"
    button_fields: list[ButtonField] = [
        ("Submit", "Submit the GitHub repository settings.", None),
        ("Cancel", "Cancel and do not create a GitHub repository.", None),
    ]
    comboboxes: list[ComboBoxField] = [
        (
            "GitHub Repo Visibility",
            "private",
            "Public/Private for remote repo visibility, or local for non-remote.",
            ["public", "private", "local"],
        )
    ]
    text_fields: list[TextField] = [
        (
            "Project Directory",
            "{{ cookiecutter.__project_dir }}",
            "Path to the project directory.",
        ),
        ("GitHub Username", "iLiftALot", "GitHub username for the repository."),
        ("GitHub Repo Branch", "master", "Branch name for the repository."),
        (
            "GitHub Repo Name",
            "{{ cookiecutter.__gh_slug }}",
            "Name of the GitHub repository.",
        ),
        (
            "GitHub Repo Description",
            "{{ cookiecutter.project_short_description }}",
            "Description of the GitHub repository.",
        ),
    ]

    form_settings: FormInputs = FormInputs(
        button_fields=button_fields,
        combo_boxes=comboboxes,
        text_fields=text_fields,
    )
    gh_modal_response: FormResult = show_form_dialog(
        title=title,
        subtitle=subtitle,
        **form_settings,
    )

    return gh_modal_response


async def run_hook() -> None:
    iterm: GlobaliTermState = await setup_session()
    reveal_hotkey_window_osa = textwrap.dedent("""\
    tell application "iTerm2"
        tell current window
            reveal hotkey window
        end tell
    end tell\
    """)
    osa_command = f"osascript -e '{reveal_hotkey_window_osa}'"
    run_command(osa_command)
    # await iterm.window.async_create_tab(profile=iterm.profile.name)

    should_create_repo: bool = literal_eval("{{cookiecutter.create_github_repo}}")
    cd_command = 'cd "{{cookiecutter.__project_dir}}"'
    gh_commands: list[str] = []
    if (
        should_create_repo
        and (gh_modal_response := create_gh_modal(iterm)).cancelled is False
    ):
        print(asdict(gh_modal_response))
        gh_config: GitHubRepoConfig = gh_modal_response.config
        cd_command = f'cd "{gh_config.project_directory}"'
        gh_commands.extend(create_github_repository(**asdict(gh_config)))

    cd_command = (
        'cd "~/CodeProjects/cookiecutter-pypackage"'  # --- TEMPORARY OVERRIDE ---
    )

    await send_command_to_iterm(iterm.session, cd_command)
    # for cmd in gh_commands:
    #     await send_command_to_iterm(iterm.session, cmd)


def main() -> None:
    asyncio.run(run_hook())


if __name__ == "__main__":
    print("Starting post-generation script...")
    main()
    print("\nPost-generation script completed.")
