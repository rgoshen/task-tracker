"""The layers depend only downward: `domain`, then `infrastructure`, then `cli`.

M8. The check reads the source and never imports it, so a module that cannot be
imported yet is still found.

A second check keeps each layer to its job: `domain` imports no module for files or
the terminal and calls no `print`, `open` or `input`, and `infrastructure` imports
no `argparse`. It is a tripwire for the likely slip, not a proof of purity.
"""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import ast
from pathlib import Path

import pytest

import task_tracker

_PACKAGE = Path(task_tracker.__file__).parent
# What each layer may import from this package: itself and the layers below it.
_ALLOWED = {
    "domain": frozenset({"domain"}),
    "infrastructure": frozenset({"domain", "infrastructure"}),
}


# What each layer must not use, because it would undo what the layer is for: `domain`
# does no file or terminal work, and `infrastructure` knows nothing of the command line.
_IO_IMPORTS = {
    "domain": frozenset(
        {"os", "sys", "pathlib", "json", "tempfile", "shutil", "argparse"}
    ),
    "infrastructure": frozenset({"argparse"}),
}
# Builtins that reach the terminal or a file with no import, so the lists above cannot
# see them. Names are a tripwire and not a proof: `p = print` gets past them.
_IO_CALLS = {
    "domain": frozenset({"print", "open", "input"}),
    "infrastructure": frozenset(),
}


def _imports(source: str) -> list[tuple[int, str | None]]:
    """Return the line and module name of every import in `source`.

    A relative import has no module name, because it hides which module it reaches.
    """
    found: list[tuple[int, str | None]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.append((node.lineno, None if node.level else node.module))
    return found


def _violations(source: str, allowed: frozenset[str]) -> list[str]:
    """Return one text for each import in `source` that leaves the `allowed` layers.

    A relative import hides which layer it reaches, and the bare package imports
    `cli` (`__init__.py` re-exports `main`), so both count as leaving.
    """
    found = []
    for lineno, module in _imports(source):
        if module is None:
            found.append(f"line {lineno}: relative import")
            continue
        top, _, rest = module.partition(".")
        # `rest` is empty for the bare package, which no layer is named.
        if top == "task_tracker" and rest.partition(".")[0] not in allowed:
            found.append(f"line {lineno}: imports {module}")
    return found


def _io_uses(source: str, imports: frozenset[str], calls: frozenset[str]) -> list[str]:
    """Return one text for each import of a module in `imports` or call of a name in `calls`.

    The module is compared by its top name, so `os.path` is `os` and `ossified` is not.
    A call counts only as a bare name (`print(...)`), so `console.print(...)` does not.
    """
    found = [
        f"line {lineno}: imports {module}"
        for lineno, module in _imports(source)
        if module and module.partition(".")[0] in imports
    ]
    found.extend(
        f"line {node.lineno}: calls {node.func.id}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in calls
    )
    return found


def _layer_sources(layer: str) -> dict[str, str]:
    """Return the source of every module in `layer`, by path under the package."""
    files = sorted((_PACKAGE / layer).rglob("*.py"))
    # An empty layer must fail: with no files there would be nothing to check.
    assert files, f"{layer} has no modules"
    return {
        str(file.relative_to(_PACKAGE)): file.read_text(encoding="utf-8")
        for file in files
    }


@pytest.mark.parametrize(
    "source",
    [
        "from . import task",
        "from ..domain import task",
        "from task_tracker import main",
        "import task_tracker",
        "from task_tracker.cli import main",
        "import task_tracker.infrastructure.storage",
        "def late():\n    from task_tracker.cli import main",
    ],
)
def test_the_layer_check_flags_an_import_that_leaves_the_layer(source: str):
    assert _violations(source, frozenset({"domain"}))


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "from datetime import datetime",
        "import task_trackerish",
        "from task_tracker.domain.task import Task",
        "import task_tracker.domain.status",
    ],
)
def test_the_layer_check_accepts_other_packages_and_the_layer_itself(source: str):
    assert not _violations(source, frozenset({"domain"}))


@pytest.mark.parametrize("layer", _ALLOWED)
def test_layers_only_import_downward(layer: str):
    found = {
        name: problems
        for name, source in _layer_sources(layer).items()
        if (problems := _violations(source, _ALLOWED[layer]))
    }
    assert not found


@pytest.mark.parametrize(
    "source",
    [
        "import json",
        "import os",
        "import os.path",
        "import sys",
        "import pathlib",
        "from pathlib import Path",
        "from sys import stdout",
        "import tempfile",
        "import shutil",
        "import argparse",
        "def late():\n    import json",
        "print('x')",
        "def show():\n    return open('tasks.json')",
        "answer = input('? ')",
    ],
)
def test_the_domain_check_flags_a_file_or_terminal_use(source: str):
    assert _io_uses(source, _IO_IMPORTS["domain"], _IO_CALLS["domain"])


@pytest.mark.parametrize(
    "source",
    [
        "from collections.abc import Sequence",
        "from datetime import datetime",
        "import dataclasses",
        "from enum import StrEnum",
        "import jsonschema",
        "import ossified",
        "task.open()",
        "console.print('x')",
        "def print_all():\n    return opened",
    ],
)
def test_the_domain_check_accepts_pure_code_and_look_alikes(source: str):
    assert not _io_uses(source, _IO_IMPORTS["domain"], _IO_CALLS["domain"])


def test_the_infrastructure_check_flags_the_command_line_and_accepts_the_files():
    assert _io_uses("import argparse", _IO_IMPORTS["infrastructure"], frozenset())
    for source in ["import json", "import os", "from pathlib import Path"]:
        assert not _io_uses(source, _IO_IMPORTS["infrastructure"], frozenset())


@pytest.mark.parametrize("layer", _ALLOWED)
def test_layers_keep_to_their_own_kind_of_work(layer: str):
    found = {
        name: problems
        for name, source in _layer_sources(layer).items()
        if (problems := _io_uses(source, _IO_IMPORTS[layer], _IO_CALLS[layer]))
    }
    assert not found
