# ruff: noqa: E402
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .github.gh_script import create_github_repository as create_github_repository
    from .github.repo_dialog import (
        GitHubFormResult as GitHubFormResult,
        GitHubRepoDialog as GitHubRepoDialog,
    )
    from .github.shared_types import (
        GitHubRepoConfig as GitHubRepoConfig,
        GitHubRepoConfigType as GitHubRepoConfigType,
    )
    from .gui import (
        CreateToolTip as CreateToolTip,
        DialogBuilder as DialogBuilder,
        FieldKind as FieldKind,
        FieldSpec as FieldSpec,
        FormDialog as FormDialog,
        FormResult as FormResult,
        FormSpec as FormSpec,
        Severity as Severity,
        ValidationIssue as ValidationIssue,
        ValidationResult as ValidationResult,
        ask_directory as ask_directory,
        bring_to_front_briefly as bring_to_front_briefly,
        center_window as center_window,
        choices as choices,
        make_modal as make_modal,
        no_spaces_warning as no_spaces_warning,
        path_exists as path_exists,
        required as required,
    )

# -- Lazy imports (deps may not be available at extension-load time) --------
_LAZY_IMPORTS = {
    # GitHub (needs PyGithub)
    "create_github_repository": ".github.gh_script",
    "GitHubFormResult": ".github.repo_dialog",
    "GitHubRepoDialog": ".github.repo_dialog",
    "GitHubRepoConfig": ".github.shared_types",
    "GitHubRepoConfigType": ".github.shared_types",
    # GUI core (needs tkinter)
    "CreateToolTip": ".gui",
    "DialogBuilder": ".gui",
    "FieldKind": ".gui",
    "FieldSpec": ".gui",
    "FormDialog": ".gui",
    "FormResult": ".gui",
    "FormSpec": ".gui",
    "Severity": ".gui",
    "ValidationIssue": ".gui",
    "ValidationResult": ".gui",
    "ask_directory": ".gui",
    "bring_to_front_briefly": ".gui",
    "center_window": ".gui",
    "choices": ".gui",
    "make_modal": ".gui",
    "no_spaces_warning": ".gui",
    "path_exists": ".gui",
    "required": ".gui",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name], __package__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # GitHub
    "create_github_repository",
    "GitHubRepoDialog",
    "GitHubFormResult",
    "GitHubRepoConfig",
    "GitHubRepoConfigType",
    # GUI core — spec
    "FormSpec",
    "FieldSpec",
    "FieldKind",
    # GUI core — builder
    "DialogBuilder",
    # GUI core — renderer
    "FormDialog",
    # GUI core — result
    "FormResult",
    # GUI core — validation
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "required",
    "choices",
    "path_exists",
    "no_spaces_warning",
    # GUI core — tooltip
    "CreateToolTip",
    # GUI core — window
    "center_window",
    "bring_to_front_briefly",
    "make_modal",
    "ask_directory",
]
