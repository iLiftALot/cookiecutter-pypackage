from __future__ import annotations
import ast
import csv
import copy
import importlib
import inspect
import sys
from functools import lru_cache
from types import ModuleType
from typing import Callable, TypedDict, get_origin
import typer
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = PACKAGE_DIR.parents[3]
COMPLETION_LOG = PROJECT_ROOT / "logs" / "completion_debug.log"


class ObjectArgInfo(TypedDict):
    # args: list[str]
    args: dict[str, str]
    func: Callable


type ModuleFuncArgMap = dict[str, dict[str, ObjectArgInfo]]


def debug_completions(message: str) -> None:
    """Helper function to log debug messages for completions."""
    try:
        COMPLETION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with COMPLETION_LOG.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        # Never break shell completion or CLI execution due to logging.
        return


def _import_path(module_name: str) -> str:
    return f"jupiter.{module_name}"


def _safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "Unknown"


def _coerce_arg_value(text: str) -> object:
    """Best-effort conversion of a CLI token to a Python value.

    - Uses `ast.literal_eval` when possible (numbers, lists, dicts, quoted strings).
    - Falls back to the original string for everything else.
    """

    text = text.strip()
    if text == "":
        return ""
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def _split_obj_args(parts: list[str]) -> list[str]:
    """Split raw CLI parts into individual arg tokens.

    Supports:
    - multiple tokens:  juptest run-module ... a b mode=show
    - a single comma string (CSV): juptest run-module ... "a,b,mode=show"
      (including quoted values containing commas).
    """

    tokens: list[str] = []
    for part in parts:
        if not part:
            continue
        try:
            row = next(csv.reader([part], skipinitialspace=True))
            tokens.extend([t for t in row if t != ""])
        except Exception:
            tokens.append(part)
    return tokens


def _parse_call_args(raw_parts: list[str]) -> tuple[list[object], dict[str, object]]:
    """Parse OBJ_ARGS parts into positional args and kwargs.

    Keyword args are provided as `name=value` tokens.
    """

    tokens = _split_obj_args(raw_parts)

    positional: list[object] = []
    kwargs: dict[str, object] = {}

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        key, sep, value = token.partition("=")
        if sep and key.strip():
            kwargs[key.strip()] = _coerce_arg_value(value)
        else:
            positional.append(_coerce_arg_value(token))

    return positional, kwargs


def _looks_like_type_expr(expr: ast.AST) -> bool:
    """Best-effort heuristic: detect expressions that are likely type aliases.

    This allows completions to work even when a module can't be imported.
    """

    # Most type aliases are built from Names/Attributes/Subscripts and unions.
    if isinstance(expr, (ast.Name, ast.Attribute, ast.Subscript, ast.Call, ast.Tuple)):
        return True
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr):
        return _looks_like_type_expr(expr.left) and _looks_like_type_expr(expr.right)
    if isinstance(expr, ast.Constant):
        return expr.value is None or expr.value is Ellipsis
    return False


def _collect_type_aliases(tree: ast.Module) -> dict[str, ast.AST]:
    """Collect simple module-level type aliases.

    Supports both:
    - PEP 695: `type Alias = ...`
    - Assignments: `Alias = ...` (best-effort)
    - Annotated assignments: `Alias: TypeAlias = ...` (best-effort)
    """

    aliases: dict[str, ast.AST] = {}

    for node in tree.body:
        # PEP 695
        if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
            aliases[node.name.id] = node.value
            continue

        # Classic assignment: Alias = ...
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and _looks_like_type_expr(node.value):
                aliases[target.id] = node.value
            continue

        # Annotated assignment: Alias: TypeAlias = ...
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            annotation_text = _safe_unparse(node.annotation)
            if annotation_text.endswith("TypeAlias") and _looks_like_type_expr(node.value):
                aliases[node.target.id] = node.value

    return aliases


def _expand_alias(name: str, aliases: dict[str, ast.AST], *, max_depth: int = 10) -> str:
    """Expand chained aliases like `type B = list[A]`.

    Cycles are handled by a max depth cutoff.
    """

    current = aliases.get(name)
    if current is None:
        return name

    seen: set[str] = set()
    depth = 0
    while isinstance(current, ast.Name) and current.id in aliases and depth < max_depth:
        if current.id in seen:
            break
        seen.add(current.id)
        current = aliases[current.id]
        depth += 1

    return _safe_unparse(current)


def _resolve_alias_expr(name: str, aliases: dict[str, ast.AST], *, max_depth: int = 10) -> ast.AST | None:
    """Resolve a type alias name to its AST value (following chained aliases)."""

    current = aliases.get(name)
    if current is None:
        return None

    seen: set[str] = set()
    depth = 0
    while isinstance(current, ast.Name) and current.id in aliases and depth < max_depth:
        if current.id in seen:
            break
        seen.add(current.id)
        current = aliases[current.id]
        depth += 1

    return current


class _AliasExpander(ast.NodeTransformer):
    def __init__(self, aliases: dict[str, ast.AST]):
        self._aliases = aliases

    def visit_Name(self, node: ast.Name) -> ast.AST:
        resolved = _resolve_alias_expr(node.id, self._aliases)
        if resolved is None:
            return node

        # Expand alias references recursively (and avoid mutating shared nodes).
        replacement = copy.deepcopy(resolved)
        return self.visit(replacement)


def _format_type_value(value: object) -> str:
    """Format a runtime type-ish object into a readable string."""

    # PEP 695: typing.TypeAliasType
    if hasattr(value, "__value__"):
        try:
            value = value.__value__
        except Exception:
            pass

    if value is None or value is type(None):
        return "None"

    # Classes and protocols
    if isinstance(value, type):
        return value.__name__

    origin = get_origin(value)
    if origin is not None:
        # Prefer the modern builtins-style repr when possible.
        try:
            return str(value).removeprefix("typing.")
        except Exception:
            pass

    # Fallback
    try:
        return str(value).removeprefix("typing.")
    except Exception:
        return repr(value)


def _format_annotation(
    annotation: ast.AST | None,
    *,
    module_obj: ModuleType | None,
    aliases: dict[str, ast.AST],
) -> str:
    if annotation is None:
        return "Unknown"

    expanded = annotation
    if aliases:
        try:
            expanded = _AliasExpander(aliases).visit(copy.deepcopy(annotation))
            ast.fix_missing_locations(expanded)
        except Exception:
            expanded = annotation

    text = _safe_unparse(expanded)

    # If the module is importable, resolve simple named annotations to the
    # runtime object to improve formatting (e.g., PEP 695 aliases).
    if module_obj and isinstance(annotation, ast.Name):
        value = getattr(module_obj, annotation.id, None)
        if value is not None:
            return _format_type_value(value)

    return text


def module_details[T](
    module_name: str, rtype_fallback: Callable[[], T]
) -> T | tuple[str, str, ModuleType | None]:
    module_path = PACKAGE_DIR.joinpath(*module_name.split(".")).with_suffix(".py")
    if not module_path.is_file():
        debug_completions(f"Module path {module_path} does not exist.")
        return rtype_fallback()

    import_path = _import_path(module_name)
    debug_completions(f"Import path: {import_path}")

    module_obj = sys.modules.get(import_path)
    if module_obj is None:
        try:
            module_obj = importlib.import_module(import_path)
        except Exception as exc:
            debug_completions(f"Failed to import module: {import_path}: {exc!r}")
            return rtype_fallback()

    debug_completions(f"module obj: {module_obj!r}")
    return str(module_path), import_path, module_obj


@lru_cache(maxsize=1)
def package_modules() -> tuple[str, ...]:
    """gathers all modules in the jupiter package"""
    modules: list[str] = []

    for path in PACKAGE_DIR.rglob("*.py"):
        if path.name in ["cmd.py", "completions.py"] or path.name.startswith("_"):
            continue
        if "__pycache__" in path.parts:
            continue
        if any(part.startswith(".") for part in path.parts):
            continue

        rel = path.relative_to(PACKAGE_DIR).with_suffix("")
        modules.append(".".join(rel.parts))

    modules.sort()
    return tuple(modules)


def _iter_function_params(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.arg]:
    params: list[ast.arg] = []
    params.extend(fn.args.posonlyargs)
    params.extend(fn.args.args)
    if fn.args.vararg is not None:
        params.append(fn.args.vararg)
    params.extend(fn.args.kwonlyargs)
    if fn.args.kwarg is not None:
        params.append(fn.args.kwarg)
    return params


@lru_cache(maxsize=1)
def module_objects() -> ModuleFuncArgMap:
    """Parse all package modules and build a completion map.

    Parsing is AST-based (so it works even if a module can't be imported).
    If import succeeds, we attach the runtime callable for parity with the
    previous behavior.
    """

    func_arg_map: ModuleFuncArgMap = {}

    for module_name in package_modules():
        module_path = PACKAGE_DIR.joinpath(*module_name.split(".")).with_suffix(".py")
        if not module_path.is_file():
            continue

        import_path = _import_path(module_name)
        func_arg_map.setdefault(import_path, {})

        try:
            source = module_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except SyntaxError as exc:
            debug_completions(f"SyntaxError parsing {module_path}: {exc}")
            continue
        except Exception as exc:
            debug_completions(f"Failed reading/parsing {module_path}: {exc!r}")
            continue

        aliases = _collect_type_aliases(tree)

        # Import is best-effort; completions should still work without it.
        module_obj: ModuleType | None
        try:
            module_obj = importlib.import_module(import_path)
        except Exception as exc:
            debug_completions(f"Failed to import {import_path} for introspection: {exc!r}")
            module_obj = None

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue

            func_arg_map[import_path][node.name] = {
                "args": {
                    arg.arg: _format_annotation(
                        arg.annotation,
                        module_obj=module_obj,
                        aliases=aliases,
                    )
                    for arg in _iter_function_params(node)
                },
                "func": getattr(module_obj, node.name, lambda: None)
                if module_obj is not None
                else (lambda: None),
            }

    return func_arg_map


def module_completion(incomplete: str, ctx: typer.Context) -> list[str]:
    """Recursively find all modules in the jupiter package that start with the incomplete string."""
    module_names = package_modules()
    modules = (
        [m for m in module_names if m.startswith(incomplete)]
        if module_names
        else ["No Modules Found..."]
    )
    return modules


def module_objs_completion(incomplete: str, ctx: typer.Context) -> list[str]:
    """Provide completion for module arguments based on collected function argument names."""

    module_name = ctx.params.get("module")
    if not module_name:
        debug_completions("No module name provided in context.")
        return []

    import_path = _import_path(module_name)
    possible_args = module_objects()

    completions = [
        obj for obj in possible_args.get(import_path, {}) if obj.startswith(incomplete)
    ]
    return sorted(completions)


def obj_args_completion(incomplete: str, ctx: typer.Context) -> list[tuple[str, str]]:
    """Provide completion for object/function arguments based on collected function argument names."""
    module_name = ctx.params.get("module")
    module_obj_name = ctx.params.get("module_obj")
    if not module_name or not module_obj_name:
        debug_completions("Module name or object name not provided in context.")
        return []

    import_path = _import_path(module_name)
    possible_args = module_objects()

    func_info = possible_args.get(import_path, {}).get(module_obj_name)
    if not func_info:
        debug_completions(
            f"No function info found for {module_obj_name} in {import_path}."
        )
        return []
    sig = inspect.signature(func_info["func"]).parameters
    func_params = [
        (f"{name}='", f"{param} ({param.kind.description})")
        for name, param in sig.items()
        if name not in ("return", "state", "client")
    ]
    return [
        (value, help_text)
        for value, help_text in func_params[len(ctx.params.get("args", ()) or ()) :]
        if value.startswith(incomplete)
    ]
