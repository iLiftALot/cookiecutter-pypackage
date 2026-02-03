from __future__ import annotations

import logging
import os
from enum import StrEnum
from typing import Any, Literal, NamedTuple, Required, TypedDict, Unpack

from github import (
    Auth,
    AuthenticatedUser,
    Consts,
    Github,
    GithubObject,
    Repository,
    Requester,
)
from urllib3 import Retry

from .shared_types import GitHubRepoConfigType

GITHUB_AUTH = Auth.Token(os.getenv("GITHUB_TOKEN", ""))
type GitHubRequestValue = Literal["GET", "POST", "PATCH", "PUT", "DELETE"]


class GitHubEndpoint(NamedTuple):
    method: GitHubRequestValue
    endpoint: str


class RepositoryKwargs(TypedDict, total=False):
    name: Required[str]
    description: str
    private: bool
    auto_init: bool
    has_issues: bool
    has_wiki: bool
    has_downloads: bool
    has_projects: bool
    has_discussions: bool
    license_template: str
    gitignore_template: str
    allow_squash_merge: bool
    allow_merge_commit: bool
    allow_rebase_merge: bool
    delete_branch_on_merge: bool


class RepositoryWrapper(Repository.Repository):
    def __init__(
        self,
        github_config: GitHubRepoConfigType,
        requester: Requester.Requester,
        headers: dict[str, str | int] | None = None,
        attributes: dict[str, Any] | None = None,
        completed: bool | None = None,
        *,
        url: str | None = None,
        accept: str | None = None,
    ):
        super().__init__(
            requester, headers, attributes, completed, url=url, accept=accept
        )
        self.github_config = github_config
        self._set_attributes()

    def _set_attributes(self) -> None:
        class RepoAttributes(StrEnum):
            DEFAULT_BRANCH = self.github_config.get("github_repo_branch", "master")

        self._default_branch = RepoAttributes.DEFAULT_BRANCH


class GithubWrapper(Github):
    def __init__(
        self,
        github_config: GitHubRepoConfigType | None = None,
        login_or_token: str | None = None,
        password: str | None = None,
        jwt: str | None = None,
        app_auth: Auth.AppInstallationAuth | None = None,
        base_url: str = Consts.DEFAULT_BASE_URL,
        timeout: int = Consts.DEFAULT_TIMEOUT,
        user_agent: str = Consts.DEFAULT_USER_AGENT,
        per_page: int = Consts.DEFAULT_PER_PAGE,
        verify: bool | str = True,
        retry: int | Retry | None = Github.default_retry,
        pool_size: int | None = None,
        seconds_between_requests: float
        | None = Consts.DEFAULT_SECONDS_BETWEEN_REQUESTS,
        seconds_between_writes: float | None = Consts.DEFAULT_SECONDS_BETWEEN_WRITES,
        auth: Auth.Auth | None = None,
        lazy: bool = False,
    ) -> None:
        super().__init__(
            login_or_token,
            password,
            jwt,
            app_auth,  # ty:ignore[invalid-argument-type]
            base_url,
            timeout,
            user_agent,
            per_page,
            verify,
            retry,
            pool_size,
            seconds_between_requests,
            seconds_between_writes,
            auth,
            lazy,
        )
        self.github_config = github_config or {}
        self.__repo: RepositoryWrapper | None = None
        self.__user: AuthenticatedUser.AuthenticatedUser = self.get_user()
        logging.getLogger("github.Requester").disabled = True

    @property
    def repo(self) -> RepositoryWrapper:
        if self.__repo is None:
            raise AttributeError("Repository not set. Try calling `set_repo` first.")
        return self.__repo

    @property
    def user(self) -> AuthenticatedUser.AuthenticatedUser:
        return self.__user

    def set_repo(self, full_name_or_id: str, lazy: bool = False) -> GithubWrapper:
        url_base = "/repositories/" if isinstance(full_name_or_id, int) else "/repos/"
        url = f"{url_base}{full_name_or_id}"
        if lazy:
            return RepositoryWrapper(
                self.github_config, self.requester, {}, {"url": url}, completed=False
            )
        headers, data = self.requester.requestJsonAndCheck("GET", url)
        self.__repo = RepositoryWrapper(
            github_config=self.github_config,
            requester=self.requester,
            headers=headers,
            attributes=data,
            completed=True,
            url=None,
            accept=None,
        )
        return self

    def create_repo(self, **kwargs: Unpack[RepositoryKwargs]) -> RepositoryWrapper:
        """Create a new repository locally and remotely on GitHub."""
        post_parameters: dict[str, Any] = GithubObject.NotSet.remove_unset_items(kwargs)
        headers, data = self.requester.requestJsonAndCheck(
            "POST", "/user/repos", input=post_parameters
        )
        self.__repo = RepositoryWrapper(
            github_config=self.github_config,
            requester=self.requester,
            headers=headers,
            attributes=data,
            completed=True,
            url=None,
            accept=None,
        )
        return self.__repo


def create_github_repository(
    **github_config: Unpack[GitHubRepoConfigType],
) -> list[str]:
    """Create a GitHub repository using gh CLI."""

    github = GithubWrapper(github_config=github_config, auth=GITHUB_AUTH)
    branch = github_config.get("github_repo_branch", "master")
    commands = [
        f"git init --initial-branch={branch}",
        "git add . && git commit -m 'Initial commit'",
    ]
    visibility = github_config.get("github_repo_visibility", "local")
    should_create_remote = visibility != "local"

    if should_create_remote:
        repo_name = github_config.get(
            "github_repo_name", "{{ cookiecutter.__gh_slug }}"
        ).split("/")[-1]
        description = github_config.get(
            "github_repo_description", "{{ cookiecutter.project_short_description }}"
        )
        repo = github.create_repo(
            name=repo_name,
            description=description,
            private=(visibility == "private"),
            auto_init=False,
        )
        commands.extend(
            [
                f'git remote add origin "{repo.clone_url}"',
                f"git push -u origin {branch}",
            ]
        )

    return commands
