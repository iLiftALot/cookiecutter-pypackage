from collections.abc import Callable
from typing import TypedDict
from dataclasses import dataclass, field


class GitHubRepoConfigType(TypedDict, total=True):
    project_directory: str
    github_username: str
    github_repo_branch: str
    github_repo_name: str
    github_repo_description: str
    github_repo_visibility: str


@dataclass
class GitHubRepoConfig:
    project_directory: str = field(default="{{ cookiecutter.__project_dir }}")
    github_username: str = field(default="iLiftALot")
    github_repo_branch: str = field(default="master")
    github_repo_name: str = field(default="{{ cookiecutter.__gh_slug }}")
    github_repo_description: str = field(default="{{ cookiecutter.project_short_description }}")
    github_repo_visibility: str = field(default="local")

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

@dataclass
class FormResult:

    cancelled: bool = True
    config: GitHubRepoConfig = field(default_factory=GitHubRepoConfig)


type ButtonField = tuple[str, str, Callable[[], None] | None]
"""(button_label, help_text, callback_function)"""
type TextField = tuple[str, str, str]
"""(field_label, default_value, help_text)"""
type ComboBoxField = tuple[str, str, str, list[str]]
"""(field_label, default_value, help_text, options)"""
type CheckBoxField = tuple[str, bool | int, str]
"""(field_label, default_value, help_text)"""


class FormInputs(TypedDict, total=False):
    """
    TypedDict for form dialog inputs.

    ---

    :param button_fields: A list of button fields.
    :type button_fields: ``list[tuple[str, str, Callable[[], None] | None]]``
    :param text_fields: A list of text fields.
    :type text_fields: ``list[tuple[str, str, str]]``
    :param combo_boxes: A list of combo box fields.
    :type combo_boxes: ``list[tuple[str, str, str, list[str]]]``
    :param check_boxes: A list of check box fields.
    :type check_boxes: ``list[tuple[str, bool | int, str]]``

    ---

    .. Example::

        ```python
        form_settings: FormInputs = FormInputs(
            button_fields=[
                ("Submit", "Submit the form.", None),
                ("Cancel", "Cancel the form.", None),
            ],
            text_fields=[
                ("Name", "John Doe", "Enter your full name."),
                ("Email", "john.doe@example.com", "Enter your email address."),
            ],
            combo_boxes=[
                ("Country", "USA", "Select your country.", ["USA", "Canada", "UK"]),
                ("Language", "English", "Select your preferred language.", ["English", "Spanish", "French"]),
            ],
            check_boxes=[
                ("Subscribe to newsletter", True, "Receive monthly updates."),
                ("Accept terms and conditions", False, "You must accept to proceed."),
                ("Enable notifications", 1, "Get notified about updates."),
            ],
        )
        ```
    """

    button_fields: list[ButtonField]
    """
    A list of tuples each containing:
    - button_label: ``str``
    - help_text: ``str``
    - callback_function: ``Callable[[], None] | None``
    """
    text_fields: list[TextField]
    """
    A list of tuples each containing:
    - field_label: ``str``
    - default_value: ``str``
    - help_text: ``str``
    """
    combo_boxes: list[ComboBoxField]
    """
    A list of tuples each containing:
    - field_label: ``str``
    - default_value: ``str``
    - help_text: ``str``
    - options: ``list[str]``
    """
    check_boxes: list[CheckBoxField]
    """
    A list of tuples each containing:
    - field_label: ``str``
    - default_value: ``bool | int``
    - help_text: ``str``
    """
