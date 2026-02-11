# GUI Dialogs

The `cookiecutter_pypackage.scripts.gui` package provides a reusable Tk/ttk
form-dialog framework.  You can build dialogs using either the **declarative
spec** API or the **fluent builder** API.

---

## Declarative API (`FormSpec` / `FieldSpec`)

Define the dialog as data — a `FormSpec` containing a list of `FieldSpec`
objects — then hand it to `FormDialog` to render.

```python
from cookiecutter_pypackage.scripts.gui import (
    FieldKind,
    FieldSpec,
    FormDialog,
    FormSpec,
    required,
)

spec = FormSpec(
    title="New Widget",
    min_width=500,
    min_height=300,
    fields=[
        FieldSpec(kind=FieldKind.LABEL, label="Widget Settings", row=0, col=0,
                  font=("Arial", 12, "bold")),
        FieldSpec(kind=FieldKind.TEXT, key="widget_name", label="Name",
                  default="my-widget", help_text="Name of the widget.",
                  row=1, col=0, validators=[required]),
        FieldSpec(kind=FieldKind.SELECT, key="colour", label="Colour",
                  default="blue", options=["red", "green", "blue"],
                  readonly=True, row=2, col=0),
        FieldSpec(kind=FieldKind.CHECKBOX, key="publish", label="Publish",
                  default=False, row=3, col=0),
        FieldSpec(kind=FieldKind.BUTTON, label="Submit", row=4, col=0),
        FieldSpec(kind=FieldKind.BUTTON, label="Cancel", row=4, col=1),
    ],
)

result = FormDialog(spec).show()

if not result.cancelled:
    print(result.values)
    # e.g. {"widget_name": "my-widget", "colour": "blue", "publish": False}
```

---

## Builder API (`DialogBuilder`)

Construct the same dialog with chainable method calls — useful when you
prefer an imperative style or need conditional fields.

```python
from cookiecutter_pypackage.scripts.gui import DialogBuilder, required

result = (
    DialogBuilder("New Widget")
    .min_size(500, 300)
    .add_label("Widget Settings", row=0, col=0)
    .add_text("widget_name", label="Name", default="my-widget",
              help_text="Name of the widget.", row=1, col=0,
              validators=[required])
    .add_select("colour", label="Colour", default="blue",
                options=["red", "green", "blue"], readonly=True,
                row=2, col=0)
    .add_checkbox("publish", label="Publish", default=False, row=3, col=0)
    .add_button("Submit", row=4, col=0)
    .add_button("Cancel", row=4, col=1)
    .show()
)

if not result.cancelled:
    print(result.values)
```

> **Tip:** `DialogBuilder.show()` is a shortcut for `.build()` → `FormDialog(spec).show()`.

---

## GitHub Repository Dialog

A ready-made dialog for configuring a GitHub repository is available as
`GitHubRepoDialog`:

```python
from cookiecutter_pypackage.scripts import GitHubRepoDialog

result = GitHubRepoDialog(
    project_dir="/tmp/my-project",
    username="octocat",
    repo_name="my-project",
    description="A great project",
).show()

if not result.cancelled:
    config = result.to_config()  # -> GitHubRepoConfig dataclass
```

---

## Notes

- The framework uses the native macOS ttk **aqua** theme by default.
- Dialogs are modal (`grab_set` + `wait_window`) with `Escape` / window-close
  mapped to cancel.
- A **brief `-topmost`** strategy is used to bring the dialog to the front on
  macOS without permanently forcing always-on-top.
- Tooltips use the `CreateToolTip` class.
