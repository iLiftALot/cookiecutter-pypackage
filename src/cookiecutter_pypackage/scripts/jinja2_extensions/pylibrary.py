"""Jinja2 extensions for the cookiecutter-pypackage project.

Provides custom filters and globals that are registered via a single
``PyLibraryExtension`` entry-point.  Add new capabilities by decorating
plain functions/classes with ``@jinja_filter`` or ``@jinja_global``.

Usage in cookiecutter.json::

    "_extensions": [
        "src.cookiecutter_pypackage.scripts.jinja2_extensions.pylibrary.PyLibraryExtension"
    ]

Available in templates::

    {{ some_string | jsonquote }}
    {{ Env("HOME").value }}
    {{ (Env("HOME").value | path) / "Documents" }}
    {% set os = import("os") %}
"""

from __future__ import annotations

import os
from json import dumps
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from jinja2 import Environment
from jinja2.ext import Extension

load_dotenv()

# ---------------------------------------------------------------------------
# Decorator-based registry
# ---------------------------------------------------------------------------

_FILTERS: dict[str, Callable[..., Any]] = {}
_GLOBALS: dict[str, Callable[..., Any]] = {}


def jinja_filter(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a function as a Jinja2 filter.

    Example::

        @jinja_filter("jsonquote")
        def jsonquote(value: str) -> str: ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        _FILTERS[name] = func
        return func

    return decorator


def jinja_global(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a class or function as a Jinja2 global.

    Example::

        @jinja_global("Env")
        class Env: ...
    """

    def decorator(cls_or_func: Callable[..., Any]) -> Callable[..., Any]:
        _GLOBALS[name] = cls_or_func
        return cls_or_func

    return decorator


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


@jinja_filter("jsonquote")
def jsonquote(value: Any) -> str:
    """JSON-encode a value for safe embedding.

    Template usage::

        {{ some_string | jsonquote }}
    """
    return dumps(value, ensure_ascii=False)


@jinja_filter("path")
def path(value: str) -> Path:
    """Convert a string to a pathlib.Path object.

    Template usage::

        {{ some_path_string | path }}
    """
    return Path(value)


# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------


@jinja_global("Env")
class Env:
    """Read an environment variable, with ``.value`` and ``.path`` accessors.

    Template usage::

        {{ Env("HOME").value }}
    """

    def __init__(self, var_name: str) -> None:
        self.name: str = var_name
        self._value: str = os.getenv(var_name, "")

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Env({self.name!r})"


@jinja_global("import")
def import_lib(lib_name: str) -> Any:
    """Dynamically import a Python module inside a template.

    Template usage::

        {% set os = import("os") %}
        {{ os.path.sep }}
    """
    try:
        module = __import__(lib_name)
        for comp in lib_name.split(".")[1:]:
            module = getattr(module, comp)
        return module
    except ImportError as e:
        raise ImportError(f"Could not import library '{lib_name}': {e}") from e


@jinja_global("pycode")
def pycode(code: str) -> Any:
    """Execute Python code and return the result.

    Template usage::

        {{ pycode("2 + 2") }}                        → 4
        {{ pycode("__import__('os').getenv('HOME')") }} → /Users/...
    """
    shared_ns: dict[str, Any] = {"__builtins__": __builtins__}
    try:
        # Try as an expression first (returns a value)
        return eval(code, shared_ns)
    except SyntaxError:
        # Fall back to statement execution (e.g., assignments, imports)
        exec(code, shared_ns)
        return shared_ns.get("_result")


# ---------------------------------------------------------------------------
# Single Extension entry-point
# ---------------------------------------------------------------------------


class PyLibraryExtension(Extension):
    """One Jinja2 extension that registers all project filters and globals.

    Cookiecutter loads this via the ``_extensions`` list in
    ``cookiecutter.json``.  Every function/class decorated with
    ``@jinja_filter`` or ``@jinja_global`` above is installed
    automatically.
    """

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.filters.update(_FILTERS)
        environment.globals.update(_GLOBALS)
        environment.globals["pylibrary"] = self

    @property
    def extensions(self) -> dict[str, dict[str, Callable[..., Any]]]:
        """Return the registered filters and globals as a dictionary."""
        return {
            "globals": _GLOBALS,
            "filters": _FILTERS,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{k}={getattr(self, k)!r}' for k in dir(self) if not k.startswith('_'))})"
