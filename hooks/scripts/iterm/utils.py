from functools import partial
from typing import Literal

from iterm2 import alert, connection, session


async def send_command_to_iterm(session: session.Session, command: str) -> None:
    """Send a command to the iTerm2 session."""
    await session.async_send_text(command + "\n", suppress_broadcast=True)


async def poly_modal_alert_handler(
    title: str,
    subtitle: str,
    connection: connection.Connection,
    window_id: str | None = None,
    button_names: list[str] | None = None,
    checkboxes: list[tuple[str, Literal[0, 1]]] | None = None,
    comboboxes: tuple[list[str], str | None] | None = None,
    text_fields: tuple[list[str], list[str]] | None = None,
):
    """Shows the poly modal alert.

    :param title: The title of the alert.
    :type title: ``str``
    :param subtitle: The subtitle of the alert.
    :type subtitle: ``str```
    :param connection: The iTerm2 connection.
    :type connection: ``iterm2.connection.Connection``
    :param window_id: The window ID to attach the alert to.
    :type window_id: ``str | None``
    :param button_names: A list of button names to add to the alert.
    :type button_names: ``list[str] | None``
    :param checkboxes: A list of tuples containing checkbox label
    and default value (0 or 1).
    :type checkboxes: ``list[tuple[str, Literal[0, 1]]] | None``
    :param comboboxes: A tuple containing a list of combobox items
    and the default selected item.
    :type comboboxes: ``tuple[list[str], str | None] | None``
    :param text_fields: A tuple containing a list of text field placeholders
    and a list of default values for the text fields.
    :type text_fields: ``tuple[list[str], list[str]] | None``
    :returns: A PolyModalResult object containing values corresponding to
    :rtype: ``iterm2.alert.PolyModalResult``
    the UI elements that were added
        - the label of clicked button
        - text entered into the field input
        - selected combobox text (``''`` if combobox was present but nothing
        selected)
        - array of checked checkbox labels.
    If no buttons were defined
        then a single button, "OK", is automatically added
            and "button" will be absent from PolyModalResult.

    :raises iterm2.rpc.RPCException: if something goes wrong.
    """

    alert_instance = alert.PolyModalAlert(
        title=title, subtitle=subtitle # , window_id=window_id
    )

    for btn in button_names or []:
        alert_instance.add_button(btn)

    for cb_label, cb_default in checkboxes or []:
        alert_instance.add_checkbox_item(cb_label, cb_default)

    if comboboxes is not None:
        combobox_caller = partial(alert_instance.add_combobox, items=comboboxes[0])
        if comboboxes[1] is not None:
            combobox_caller.keywords["default"] = comboboxes[1]
        combobox_caller()

    if text_fields is not None:
        placeholders, default_values = text_fields
        for placeholder, default_value in zip(
            placeholders, default_values, strict=True
        ):
            alert_instance.add_text_field(placeholder, default_value)

    response = await alert_instance.async_run(connection=connection)
    return response
