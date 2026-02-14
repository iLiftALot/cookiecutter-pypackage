"""GitHubRepoDialog — professional GitHub repository configuration dialog.

Usage::

    from cookiecutter_pypackage.scripts.github.repo_dialog import GitHubRepoDialog

    result = GitHubRepoDialog(
        project_dir="/path/to/project",
        username="octocat",
        repo_name="my-project",
        description="A great project",
    ).show()

    if not result.cancelled:
        config = result.to_config()
        # config is a GitHubRepoConfig with canonical field names
"""

from __future__ import annotations

import os
from dataclasses import fields as dc_fields
from pathlib import Path

from ..gui.builder import DialogBuilder
from ..gui.result import FormResult as _GenericFormResult
from ..gui.validation import choices, no_spaces_warning, path_exists
from ..gui.window import ask_directory
from .shared_types import GitHubRepoConfig


class GitHubFormResult(_GenericFormResult):
    """Extends :class:`FormResult` with a helper to produce a typed config."""

    def to_config(self) -> GitHubRepoConfig:
        """Map collected values into a :class:`GitHubRepoConfig`.

        Only keys that correspond to declared ``GitHubRepoConfig`` fields are
        assigned; unknown keys are silently ignored.
        """
        config = GitHubRepoConfig()
        valid_fields = {f.name for f in dc_fields(GitHubRepoConfig)}
        for key, value in self.values.items():
            if key in valid_fields:
                setattr(config, key, value)
        return config


class GitHubRepoDialog:
    """Professional GitHub repository configuration dialog.

    Parameters correspond to default values pre-filled into the form.
    """

    def __init__(
        self,
        *,
        project_dir: str = "",
        username: str = "",
        repo_name: str = "",
        description: str = "",
        branch: str = "master",
        visibility: str = "local",
        debug: bool = False,
    ) -> None:
        self._project_dir = project_dir
        self._username = username
        self._repo_name = repo_name
        self._description = description
        self._branch = branch
        self._visibility = visibility
        self._debug = debug

    def show(self) -> GitHubFormResult:
        """Display the dialog and return a :class:`GitHubFormResult`."""
        from ..gui.dialog import FormDialog
        from ..gui.font import TkFont

        text_field_font = TkFont(
            family="TkDefaultFont",
            size=12,
            weight="normal",
            slant="roman",
            underline=False,
            overstrike=False,
        ).value
        initial_dir = os.getenv("PWD", os.getcwd())

        # We need a reference to the dialog so the Browse callback can
        # parent the file-picker correctly.  We achieve this by patching
        # the callback after construction.
        dialog_ref: FormDialog | None = None

        def _browse() -> str:
            if dialog_ref is None or dialog_ref._dialog is None:
                raise RuntimeError("Dialog reference not set for browse callback.")
            new_dir = ask_directory(
                dialog_ref._dialog,
                initial_dir=initial_dir,
                title="Select Project Directory",
            )
            if new_dir is None:
                print("Directory selection cancelled.")
                return os.path.relpath(str(Path(initial_dir).parent), start=initial_dir)
            full_path = Path(os.path.abspath(new_dir)).resolve()
            relative_path = os.path.relpath(
                full_path, start=str(Path(initial_dir).parent)
            )
            print(f"Selected directory: {new_dir} (relative path: {relative_path})")
            return relative_path

        spec = (
            DialogBuilder("GitHub Repository Configuration", debug=self._debug)
            .min_size(520, 340)
            # -- row 0: project directory label (header) spanning full width
            # .add_label(
            #     "Project Directory",
            #     row=0,
            #     col=0,
            #     font=TkFont(family="Arial", size=12, weight="bold", slant="roman", underline="normal", overstrike="normal").value,
            # )
            # -- row 1: project directory entry + browse button
            .add_text(
                "directory",
                label="Directory",
                default=self._project_dir,
                row=1,
                col=1,
                validators=[path_exists],
                font=text_field_font,
                is_bound=True,  # Assist with layout and callback binding for the browse button
            )
            .add_button(
                "browse",
                help_text="Select the project directory.",
                callback=_browse,
                bind_to="project_directory",
                row=1,
                col=2,
            )
            # -- row 2: username
            .add_text(
                "username",
                label="Username",
                default=self._username,
                help_text=(
                    "GitHub username (informational). "
                    "The repository is created under the GITHUB_TOKEN owner."
                ),
                row=2,
                col=1,
                font=text_field_font,
            )
            # -- row 3: branch
            .add_text(
                "branch",
                label="Branch",
                default=self._branch,
                help_text="Initial branch name for the repository.",
                row=3,
                col=1,
                font=text_field_font,
            )
            # -- row 4: repo name
            .add_text(
                "name",
                label="Name",
                default=self._repo_name,
                help_text="Name of the GitHub repository.",
                row=4,
                col=1,
                validators=[no_spaces_warning],
                font=text_field_font,
            )
            # -- row 5: description
            .add_text(
                "description",
                label="Description",
                default=self._description,
                help_text="Short description of the repository.",
                row=5,
                col=1,
                font=text_field_font,
            )
            # -- row 6: visibility
            .add_select(
                "visibility",
                label="Visibility",
                default=self._visibility,
                help_text="public/private for remote, or local for no remote.",
                options=["public", "private", "local"],
                readonly=True,
                row=6,
                col=1,
                validators=[choices("public", "private", "local")],
                font=text_field_font,
            )
            # -- action buttons (row value doesn't matter — they go in the bar)
            .add_button("submit", help_text="Create the repository.", row=7, col=1)
            .add_button("cancel", help_text="Cancel without creating.", row=7, col=2)
        ).build()

        dialog = FormDialog(spec, debug=self._debug)
        dialog_ref = dialog  # patch the reference for _browse

        generic_result = dialog.show()

        # Resolve the relative display path with the absolute path
        relative_dir: str = generic_result.values.get("project_directory", "")
        if relative_dir:
            generic_result.values["project_directory"] = str(
                (Path(initial_dir).parent / relative_dir).resolve()
            )

        # Wrap into GitHubFormResult
        gh_result = GitHubFormResult(
            cancelled=generic_result.cancelled,
            values=generic_result.values,
        )
        return gh_result
