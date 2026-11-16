"""Tests for which list file a command works on."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest

from task_tracker.infrastructure.location import list_path


@pytest.fixture(name="home")
def _home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # `Path.home()` reads HOME first on POSIX, so this is the home directory.
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    return home


def test_neither_choice_gives_the_list_in_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)

    assert list_path(use_global=False, directory=None) == tmp_path / "tasks.json"


def test_global_gives_the_list_in_the_hidden_directory_of_the_home(home: Path):
    expected = home / ".task-tracker" / "tasks.json"

    assert list_path(use_global=True, directory=None) == expected


def test_a_directory_gives_the_list_inside_it(tmp_path: Path):
    chosen = tmp_path / "groceries"

    assert list_path(use_global=False, directory=chosen) == chosen / "tasks.json"


def test_a_relative_directory_is_joined_to_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)

    found = list_path(use_global=False, directory=Path("groceries"))

    assert found == tmp_path / "groceries" / "tasks.json"


def test_a_directory_that_starts_with_a_tilde_is_expanded(home: Path):
    found = list_path(use_global=False, directory=Path("~/groceries"))

    assert found == home / "groceries" / "tasks.json"


def test_the_global_list_together_with_a_directory_is_refused():
    # Both would name a list, and one of them would silently lose (the global list
    # won), so the caller finds out. The command line refuses it first, with exit 2.
    with pytest.raises(ValueError, match="together"):
        list_path(use_global=True, directory=Path("/groceries"))
