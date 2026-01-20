from collections.abc import Callable
from dataclasses import dataclass, field
from typing import NamedTuple, TypedDict


class GitHubRepoConfigType(TypedDict, total=True):
    project_directory: str | None
    github_username: str | None
    github_repo_branch: str | None
    github_repo_name: str | None
    github_repo_description: str | None
    github_repo_visibility: str | None


@dataclass
class GitHubRepoConfig:
    project_directory: str | None = None
    github_username: str | None = None
    github_repo_branch: str | None = None
    github_repo_name: str | None = None
    github_repo_description: str | None = None
    github_repo_visibility: str | None = None

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)


@dataclass
class FormResult:
    cancelled: bool = True
    config: GitHubRepoConfig = field(default_factory=GitHubRepoConfig)


class ButtonField(NamedTuple):
    """(field_label, help_text, callback_function, bind_to)"""

    field_label: str
    help_text: str
    callback_function: Callable[[], str | None] | None = None
    bind_to: str | None = None


TextField = NamedTuple(
    "TextField", [("field_label", str), ("default_value", str), ("help_text", str)]
)
"""(field_label, default_value, help_text)"""


ComboBoxField = NamedTuple(
    "ComboBoxField",
    [
        ("field_label", str),
        ("default_value", str),
        ("help_text", str),
        ("options", list[str]),
    ],
)
"""(field_label, default_value, help_text, options)"""


CheckBoxField = NamedTuple(
    "CheckBoxField",
    [("field_label", str), ("default_value", bool | int), ("help_text", str)],
)
"""(field_label, default_value, help_text)"""

LabelField = NamedTuple("LabelField", [("field_label", str)])
"""(field_label)"""

type AnyField = ButtonField | TextField | ComboBoxField | CheckBoxField | LabelField
"""Union of all field types."""


class OrderedFormField(NamedTuple):
    """(field_tuple, xy, key)"""

    field_tuple: AnyField
    xy: tuple[int, int]
    key: str | None = None


def place(
    field_tuple: AnyField, row: int, col: int, key: str | None = None
) -> OrderedFormField:
    """Helper to place a field at (row, col) with an optional key."""
    return OrderedFormField(field_tuple=field_tuple, xy=(row, col), key=key)


class FormInputs(TypedDict, total=False):
    """
    TypedDict for form dialog inputs.

    ---

    :param ordered_fields: A dictionary containing form fields in a specific structure.
    :type ordered_fields: ``list[OrderedFormField]``

    :param button_fields: A list of button fields.
    :type button_fields: ``list[ButtonField]``
    :param text_fields: A list of text fields.
    :type text_fields: ``list[TextField]``
    :param combo_boxes: A list of combo box fields.
    :type combo_boxes: ``list[ComboBoxField]``
    :param check_boxes: A list of check box fields.
    :type check_boxes: ``list[CheckBoxField]``
    ---

    .. Example::

        ```python
        # Example usage without 'ordered_fields' key:

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

        # Example usage with 'ordered_fields' key:

        # These will be rendered in the order defined in the 'ordered_fields' list
        form_settings: FormInputs = FormInputs(
            ordered_fields=[
                (TextField("Name", "John Doe", "Enter your full name."), (0, 0)),
                (ButtonField("Submit", "Submit the form.", lambda: None), (0, 1)),
                (ComboBoxField("Country", "USA", "Select your country.", ["USA", "Canada", "UK"]), (1, 0)),
                (CheckBoxField("Subscribe to newsletter", True, "Receive monthly updates."), (1, 1)),
            ],
        )
    """

    ordered_fields: list[OrderedFormField]
    """
    A list of tuples each containing:
    - field_type: ``type[AnyField]``
    - field_tuple: ``AnyField``
    - xy: ``tuple[int, int]``
    """

    button_fields: list[ButtonField]
    """
    A list of tuples each containing:
    - button_label: ``str``
    - help_text: ``str``
    - callback_function: ``Callable[[], str | None] | None``
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
