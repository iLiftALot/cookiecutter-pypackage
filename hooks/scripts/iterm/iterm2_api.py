"""Main module."""

import asyncio
from dataclasses import dataclass

from iterm2 import app, connection, profile, session, tab, window


@dataclass
class GlobaliTermState:
    """Global iTerm2 state."""

    connection: connection.Connection
    app: app.App
    window: window.Window
    tab: tab.Tab
    session: session.Session
    profile: profile.Profile

    def __post_init__(self):
        # TODO: validate all fields are not None
        pass


async def get_default_profile(connection: connection.Connection) -> profile.Profile:
    """Get default profile."""
    default_profile = await profile.Profile.async_get_default(connection)
    return default_profile


async def get_connection() -> connection.Connection:
    """Get connection and register tools."""
    iterm2_connection = await connection.Connection().async_create()
    return iterm2_connection


async def get_app(connection: connection.Connection) -> app.App:
    """Get iTerm2 app."""
    app_instance = await app.async_get_app(connection, create_if_needed=True)
    if app_instance is None:
        raise RuntimeError("Could not get iTerm2 app")
    return app_instance


async def get_window(
    app: app.App, connection: connection.Connection, profile: profile.Profile
) -> window.Window:
    """Get current window."""
    iterm2_window: window.Window | None = (
        app.current_window or await window.Window.async_create(connection, profile.name)
    )
    if iterm2_window is None:
        iterm2_window = app.windows[0]
    # await iterm2_window.async_activate()
    return iterm2_window


async def get_tab(window: window.Window) -> tab.Tab:
    """Get current tab."""
    tab_instance = await window.async_create_tab()
    if tab_instance is None:
        tab_instance = window.tabs[-1]
    # await tab_instance.async_activate(order_window_front=True)
    return tab_instance


async def get_session(tab: tab.Tab) -> session.Session:
    """Get current session."""
    session_instance = tab.current_session or tab.all_sessions[-1]
    # await session_instance.async_activate(select_tab=True, order_window_front=True)
    return session_instance


async def setup_session() -> GlobaliTermState:
    """Setup window."""
    connection = await get_connection()
    app = await get_app(connection)
    profile = await get_default_profile(connection)
    window = await get_window(app, connection, profile)
    tab = await get_tab(window)
    session = await get_session(tab)

    return GlobaliTermState(
        connection=connection,
        app=app,
        profile=profile,
        window=window,
        tab=tab,
        session=session,
    )


async def main() -> GlobaliTermState:
    global_iterm_state = await setup_session()
    await global_iterm_state.app.async_activate(
        raise_all_windows=True, ignoring_other_apps=True
    )
    await global_iterm_state.window.async_activate()
    return global_iterm_state


if __name__ == "__main__":
    asyncio.run(main())
