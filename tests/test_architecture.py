"""The layers depend only downward: `domain`, then `infrastructure`, then `cli`.

M8. The check reads the source and never imports it, so a module that cannot be
imported yet is still found.
"""

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


def _violations(source: str, allowed: frozenset[str]) -> list[str]:
    """Return one text for each import in `source` that leaves the `allowed` layers.

    A relative import hides which layer it reaches, and the bare package imports
    `cli` (`__init__.py` re-exports `main`), so both count as leaving.
    """
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                found.append(f"line {node.lineno}: relative import")
                continue
            modules = [node.module or ""]
        else:
            continue
        for module in modules:
            top, _, rest = module.partition(".")
            # `rest` is empty for the bare package, which no layer is named.
            if top == "task_tracker" and rest.partition(".")[0] not in allowed:
                found.append(f"line {node.lineno}: imports {module}")
    return found


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
    files = sorted((_PACKAGE / layer).rglob("*.py"))
    # An empty layer must fail: with no files there would be nothing to check.
    assert files, f"{layer} has no modules"
    found = {
        str(file.relative_to(_PACKAGE)): problems
        for file in files
        if (problems := _violations(file.read_text(encoding="utf-8"), _ALLOWED[layer]))
    }
    assert not found
