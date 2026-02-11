"""GitHub-specific configuration types."""

from dataclasses import dataclass
from typing import Literal, TypedDict


class GitHubRepoConfigType(TypedDict, total=False):
    """Typed dict mirroring :class:`GitHubRepoConfig` fields.

    Used as the ``**kwargs`` type for :func:`create_github_repository`.
    """

    name: str
    project_directory: str
    username: str
    branch: Literal["main", "master"] | str
    description: str
    visibility: Literal["public", "private", "local"]


@dataclass
class GitHubRepoConfig(dict):
    """Canonical GitHub repository configuration.

    Field names here are the *single source of truth* for config keys
    across the dialog, the hook, and the repo-creation script.
    """

    name: str = "{{ cookiecutter.__gh_slug }}"
    project_directory: str = "{{ cookiecutter.__project_dir }}"
    username: str = ("{{ cookiecutter.__gh_slug }}").split("/")[0]
    branch: Literal["main", "master"] | str = "master"
    description: str = "{{ cookiecutter.project_short_description }}"
    visibility: Literal["public", "private", "local"] = "local"

    def asdict(self) -> GitHubRepoConfigType:
        """Convert to a :class:`GitHubRepoConfigType` dict."""
        return GitHubRepoConfigType(**self)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)

    def keys(self):
        return self.__dataclass_fields__.keys()
