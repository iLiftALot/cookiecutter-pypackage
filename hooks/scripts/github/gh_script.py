from typing import Unpack
from scripts.github.shared_types import GitHubRepoConfigType  # ty:ignore[unresolved-import]


def create_github_repository(**github_config: Unpack[GitHubRepoConfigType]) -> list[str]:
    """Create a GitHub repository using gh CLI."""

    branch = github_config.get("github_repo_branch")
    commands = ["uv sync", f"git init --initial-branch={branch}"]
    visibility = github_config.get('github_repo_visibility')
    should_create_remote = visibility != "local"

    if should_create_remote:
        repo_name = github_config.get("github_repo_name")
        description = github_config.get("github_repo_description")
        project_dir = github_config.get("project_directory")
        commands.append(
            f'gh repo create "{repo_name}" --{visibility} --source="{project_dir}" --remote=origin --description="{description}"'
        )

    return commands
