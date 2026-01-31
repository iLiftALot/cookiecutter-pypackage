from pathlib import Path
from typing import Unpack
from scripts.github.shared_types import GitHubRepoConfigType  # ty:ignore[unresolved-import]


def create_github_repository(
    **github_config: Unpack[GitHubRepoConfigType],
) -> list[str]:
    """Create a GitHub repository using gh CLI."""

    branch = github_config.get("github_repo_branch", "master")
    commands = ["uv sync --dev", f"git init --initial-branch={branch}"]
    visibility = github_config.get("github_repo_visibility", "local")
    should_create_remote = visibility != "local"

    if should_create_remote:
        repo_name = github_config.get(
            "github_repo_name", "{{ cookiecutter.__gh_slug }}"
        )
        description = github_config.get(
            "github_repo_description", "{{ cookiecutter.project_short_description }}"
        )
        project_dir = github_config.get(
            "project_directory", "{{ cookiecutter.__project_dir }}"
        )
        commands.append(
            f'''gh repo create "{repo_name}" --{visibility} --source="{
                project_dir if str(Path.cwd()) != Path(project_dir).parent else "."
            }" --remote=origin --description="{description}"'''
        )
    return commands
