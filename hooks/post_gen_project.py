from ast import literal_eval
from shlex import split
from subprocess import run


def run_command(command: str) -> None:
    """Run a shell command and print its output."""

    process = run(split(command), capture_output=True, text=True)
    stdout, stderr = process.stdout, process.stderr

    if process.returncode != 0:
        print(f"\nError running command: {command}")
        print(stderr)
    else:
        print(f"\n{stdout}")


def create_github_repository(create_cloud_repo: bool) -> None:
    """Create a GitHub repository using gh CLI."""

    branch = "{{cookiecutter.github_branch}}"
    commands = ["uv sync", f"git init --initial-branch={branch}"]

    if create_cloud_repo:
        visibility = (
            "--private"
            if literal_eval("{{cookiecutter.github_private}}") is True
            else "--public"
        )
        repo_name = "{{ cookiecutter.github_repository }}"
        description = "{{ cookiecutter.project_short_description }}"
        commands.append(
            f'gh repo create "{repo_name}" {visibility} --source=. --remote=origin --description="{description}"'
        )

    for command in commands:
        run_command(command)


if __name__ == "__main__":
    create_github_repository(literal_eval("{{cookiecutter.create_github_repo}}"))
    print("\nPost-generation script completed.")
