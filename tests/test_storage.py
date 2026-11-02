"""Tests for saving tasks to a JSON file and loading them back."""

# Test names state the intent, so per-test docstrings would only repeat them.
# `== []` pins that load returns a list; `not load(...)` would also pass for None.
# pylint: disable=missing-function-docstring,use-implicit-booleaness-not-comparison

import json
import os
import re
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.storage import load, save
from task_tracker.task import Task

# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
DUE = datetime(2026, 11, 1, 9, 0, 0)  # noqa: DTZ001
OPENED = datetime(2026, 10, 10, 9, 0, 0)  # noqa: DTZ001
FILED = datetime(2026, 10, 15, 17, 30, 0)  # noqa: DTZ001
RECORD_FIELDS = {
    "id",
    "name",
    "description",
    "created",
    "updated",
    "due",
    "date_completed",
    "status",
    "priority",
    "start",
    "stop",
}


@pytest.fixture(name="two_tasks")
def _two_tasks() -> list[Task]:
    buy_milk = Task(1, "Buy milk", priority=Priority.HIGH, due=DUE)
    # Done in the past, which only `restore` can build.
    file_taxes = Task.restore(
        id=2,
        name="File taxes",
        description="",
        created=OPENED,
        updated=FILED,
        due=None,
        date_completed=FILED,
        status=Status.DONE,
        priority=Priority.LOW,
        start=OPENED,
        stop=FILED,
    )
    return [buy_milk, file_taxes]


def test_loading_a_missing_file_gives_an_empty_list_and_creates_nothing(
    tmp_path: Path,
):
    assert load(tmp_path / "tasks.json") == []
    assert not any(tmp_path.iterdir())


def test_loading_from_a_missing_directory_does_not_create_it(tmp_path: Path):
    missing = tmp_path / "groceries"

    assert load(missing / "tasks.json") == []
    assert not missing.exists()


def test_saved_tasks_load_back_equal(tmp_path: Path, two_tasks: list[Task]):
    path = tmp_path / "tasks.json"

    save(two_tasks, path)
    loaded = load(path)

    assert loaded == two_tasks
    assert loaded[0].priority is Priority.HIGH
    assert loaded[1].status is Status.DONE
    assert loaded[0].date_completed is None
    assert loaded[1].due is None


def test_an_empty_list_loads_back_empty(tmp_path: Path):
    path = tmp_path / "tasks.json"

    save([], path)

    assert load(path) == []


def test_the_file_holds_a_json_list_of_plain_records(tmp_path: Path):
    # The file is meant to be read by a person (D1), so dates are ISO 8601 text
    # (D6) and the enums are their labels.
    path = tmp_path / "tasks.json"
    task = Task(1, "Buy milk", priority=Priority.HIGH, due=DUE)

    save([task], path)

    [record] = json.loads(path.read_text(encoding="utf-8"))
    assert set(record) == RECORD_FIELDS
    assert record["id"] == 1
    assert record["name"] == "Buy milk"
    assert record["priority"] == "HIGH"
    assert record["status"] == "TO_DO"
    assert record["due"] == "2026-11-01T09:00:00"
    assert record["created"] == task.created.isoformat()
    assert record["date_completed"] is None


def test_the_file_ends_with_a_newline(tmp_path: Path):
    # A text file without one prints badly in a terminal and shows up in diffs.
    path = tmp_path / "tasks.json"

    save([], path)

    assert path.read_text(encoding="utf-8").endswith("\n")


def test_saving_creates_the_missing_directories(tmp_path: Path):
    path = tmp_path / "nested" / "dir" / "tasks.json"

    save([], path)

    assert path.is_file()


def a_record(**overrides: object) -> dict[str, object]:
    """A valid stored record; each test changes only the field it is about."""
    record: dict[str, object] = {
        "id": 1,
        "name": "Buy milk",
        "description": "",
        "created": "2026-10-10T09:00:00",
        "updated": "2026-10-10T09:00:00",
        "due": None,
        "date_completed": None,
        "status": "TO_DO",
        "priority": "LOW",
        "start": "2026-10-10T09:00:00",
        "stop": "2026-10-10T09:00:00",
    }
    return record | overrides


def without(field_name: str) -> dict[str, object]:
    record = a_record()
    del record[field_name]
    return record


def contents(*records: object) -> str:
    return json.dumps(list(records))


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("not json", "not valid JSON"),
        ("", "not valid JSON"),
        ('{"id": 1}', "must hold a list"),
        # json.load gives up on this with a RecursionError, which is not a ValueError.
        ("[" * 200_000, "nested too deeply"),
        (contents("a task"), "record 1: must be an object"),
        (contents(None), "record 1: must be an object"),
        (contents(without("stop")), "record 1: missing field.*stop"),
        (contents(a_record(colour="red")), "record 1: unknown field.*colour"),
        # A field named like a parameter of `Task.restore` must not reach it as one.
        (contents(a_record(cls=1)), "record 1: unknown field.*cls"),
        (contents(a_record(id="1")), "record 1: id must be an int"),
        (contents(a_record(id=True)), "record 1: id must be an int"),
        (contents(a_record(id=0)), "record 1: id must be 1 or more"),
        (contents(a_record(id=-5)), "record 1: id must be 1 or more"),
        (contents(a_record(created=None)), "record 1: created must be a date"),
        (contents(a_record(updated=None)), "record 1: updated must be a date"),
        (contents(a_record(start=None)), "record 1: start must be a date"),
        (contents(a_record(stop=None)), "record 1: stop must be a date"),
        (contents(a_record(name="  ")), "record 1: name must not be blank"),
        (
            contents(a_record(name="bad \ud83d")),
            "record 1: name must be valid UTF-8 text",
        ),
        (
            contents(a_record(description="bad \ud83d")),
            "record 1: description must be valid UTF-8 text",
        ),
        (contents(a_record(priority="URGENT")), "record 1: .*URGENT"),
        (contents(a_record(due="soon")), "record 1: due"),
        (
            contents(a_record(updated="2026-10-09T09:00:00")),
            "record 1: updated must not be before created",
        ),
        (
            contents(a_record(id=1), a_record(id=2), a_record(id=1)),
            "record 3: duplicate id 1",
        ),
    ],
    ids=[
        "not-json",
        "empty-file",
        "object-instead-of-list",
        "nested-too-deeply",
        "record-is-text",
        "record-is-null",
        "missing-field",
        "unknown-field",
        "field-named-cls",
        "id-is-text",
        "id-is-true",
        "id-is-zero",
        "id-is-negative",
        "created-is-null",
        "updated-is-null",
        "start-is-null",
        "stop-is-null",
        "blank-name",
        "name-with-a-lone-surrogate",
        "description-with-a-lone-surrogate",
        "unknown-priority",
        "bad-date",
        "updated-before-created",
        "duplicate-id",
    ],
)
def test_a_corrupt_file_is_rejected_naming_the_file_and_left_unchanged(
    tmp_path: Path, text: str, message: str
):
    path = tmp_path / "tasks.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match=f"{re.escape(str(path))}: {message}"):
        load(path)

    assert path.read_text(encoding="utf-8") == text


def test_a_file_that_is_not_text_is_rejected_naming_the_file(tmp_path: Path):
    path = tmp_path / "tasks.json"
    path.write_bytes(b"\xff\xfe\x00 not utf-8 \x80")

    with pytest.raises(ValueError, match=f"{re.escape(str(path))}: not valid JSON"):
        load(path)


def test_the_second_bad_record_is_reported_by_its_position(tmp_path: Path):
    path = tmp_path / "tasks.json"
    path.write_text(contents(a_record(), a_record(id=2, name="")), encoding="utf-8")

    with pytest.raises(ValueError, match="record 2: name must not be blank"):
        load(path)


def test_a_file_that_cannot_be_read_is_not_reported_as_corrupt(tmp_path: Path):
    # Only the content is "corrupt". A directory where the file should be is a
    # problem with the disk, and the caller sees the operating system's error.
    with pytest.raises(OSError) as raised:
        load(tmp_path)

    # The wording, and even the exception class, differ between operating systems
    # (IsADirectoryError on macOS and Linux, PermissionError on Windows), so the
    # test checks only what must hold everywhere.
    assert not isinstance(raised.value, ValueError)


@pytest.fixture(name="replacements")
def _replacements(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[Path, Path]]:
    # Records every os.replace call as (source, destination) and still performs it.
    moves: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def spy(source: Any, destination: Any) -> None:
        moves.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", spy)
    return moves


def files_in(directory: Path) -> list[str]:
    return sorted(entry.name for entry in directory.iterdir())


def write_part_then_fail(_records: object, file: Any, **_options: object) -> None:
    # The destination (or temp file) already holds a half-written document when
    # the failure comes. A failure that raised before any byte was written would
    # pass against a plain overwrite too, and prove nothing about atomicity.
    file.write("[{")
    raise OSError("no space left on device")


def test_a_save_that_fails_partway_leaves_the_old_file_unchanged(
    tmp_path: Path, two_tasks: list[Task], monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "tasks.json"
    save(two_tasks, path)
    before = path.read_bytes()
    monkeypatch.setattr(json, "dump", write_part_then_fail)

    with pytest.raises(OSError, match="no space"):
        save([Task(3, "Walk the dog")], path)

    assert path.read_bytes() == before
    assert files_in(tmp_path) == ["tasks.json"]


def test_a_first_save_that_fails_partway_leaves_nothing_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "tasks.json"
    monkeypatch.setattr(json, "dump", write_part_then_fail)

    with pytest.raises(OSError, match="no space"):
        save([Task(1, "Buy milk")], path)

    assert files_in(tmp_path) == []


def test_a_save_that_cannot_replace_the_file_leaves_the_old_file_and_no_temp_file(
    tmp_path: Path, two_tasks: list[Task], monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "tasks.json"
    save(two_tasks, path)
    before = path.read_bytes()

    def refuse(_source: object, _destination: object) -> None:
        raise OSError("operation not permitted")

    monkeypatch.setattr(os, "replace", refuse)

    with pytest.raises(OSError, match="not permitted"):
        save([Task(3, "Walk the dog")], path)

    assert path.read_bytes() == before
    assert files_in(tmp_path) == ["tasks.json"]


def test_the_new_file_is_built_next_to_the_target_before_it_replaces_it(
    tmp_path: Path, replacements: list[tuple[Path, Path]]
):
    # os.replace is atomic only within one filesystem, and the system temp
    # directory is often on another.
    path = tmp_path / "tasks.json"
    save([], path)

    assert len(replacements) == 1
    source, destination = replacements[0]
    assert destination == path
    assert source.parent == path.parent
    assert source != destination


def test_a_save_that_succeeds_leaves_no_temp_file(tmp_path: Path):
    save([Task(1, "Buy milk")], tmp_path / "tasks.json")

    assert files_in(tmp_path) == ["tasks.json"]


# --- review of PR #25: save must not write what load would reject ---


def blank_named() -> Task:
    # The dataclass is mutable, so a later assignment skips the checks made at
    # construction (M5's `update` will assign too).
    task = Task(1, "Buy milk")
    task.name = "   "
    return task


def surrogate_named() -> Task:
    # A command-line argument that is not valid UTF-8 reaches Python as a lone
    # surrogate. `Task` refuses it at construction, so assign it afterwards.
    task = Task(1, "Buy milk")
    task.name = "bad \udcff"
    return task


@pytest.mark.parametrize(
    ("tasks", "message"),
    [
        ([Task(1, "a"), Task(2, "b"), Task(1, "c")], "record 3: duplicate id 1"),
        ([blank_named()], "record 1: name must not be blank"),
        ([surrogate_named()], "record 1: name must be valid UTF-8 text"),
    ],
    ids=[
        "duplicate-id",
        "name-blanked-after-construction",
        "name-with-a-lone-surrogate-after-construction",
    ],
)
def test_save_refuses_tasks_that_load_would_reject_and_keeps_the_old_file(
    tmp_path: Path,
    two_tasks: list[Task],
    tasks: list[Task],
    message: str,
):
    path = tmp_path / "tasks.json"
    save(two_tasks, path)
    before = path.read_bytes()

    with pytest.raises(ValueError, match=f"{re.escape(str(path))}: {message}"):
        save(tasks, path)

    assert path.read_bytes() == before
    assert files_in(tmp_path) == ["tasks.json"]


def test_a_refused_save_creates_no_directory(tmp_path: Path):
    path = tmp_path / "nested" / "tasks.json"

    with pytest.raises(ValueError, match="duplicate id 1"):
        save([Task(1, "a"), Task(1, "b")], path)

    assert not path.parent.exists()


# --- review of PR #25: what the file looks like ---


def test_non_ascii_text_is_written_as_text_not_as_escapes(tmp_path: Path):
    # The file is meant to be read and edited by a person (D1).
    path = tmp_path / "tasks.json"

    save([Task(1, "Café ☕")], path)

    text = path.read_text(encoding="utf-8")
    assert "Café ☕" in text
    assert "\\u" not in text
    assert load(path)[0].name == "Café ☕"


def test_a_date_assigned_after_construction_is_written_in_whole_seconds(
    tmp_path: Path,
):
    # The model drops microseconds when it builds or restores a task, not when a
    # field is assigned later (M5's update will assign). The file always holds
    # YYYY-MM-DDTHH:MM:SS, as the README promises.
    path = tmp_path / "tasks.json"
    task = Task(1, "Buy milk")
    task.due = DUE.replace(microsecond=123456)

    save([task], path)

    [record] = json.loads(path.read_text(encoding="utf-8"))
    assert record["due"] == "2026-11-01T09:00:00"
    assert load(path)[0].due == DUE


# --- review of PR #25: the file being replaced may be a link or have a mode ---

only_on_posix = pytest.mark.skipif(
    sys.platform == "win32", reason="Windows has no owner, group, and other bits"
)


def test_saving_through_a_symlink_updates_the_file_it_points_to(
    tmp_path: Path, two_tasks: list[Task]
):
    # A list kept in a synced folder or a dotfiles repository is often linked in.
    real = tmp_path / "synced" / "tasks.json"
    link = tmp_path / "tasks.json"
    save([], real)
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("this system does not allow symbolic links")

    save(two_tasks, link)

    assert link.is_symlink()
    assert load(real) == two_tasks
    assert files_in(real.parent) == ["tasks.json"]
    assert files_in(tmp_path) == ["synced", "tasks.json"]


def test_saving_through_a_symlink_builds_the_new_file_beside_the_real_one(
    tmp_path: Path, replacements: list[tuple[Path, Path]]
):
    # os.replace is atomic only within one filesystem, and a link can point to
    # another one, so the temporary file belongs next to the file it replaces.
    real = tmp_path / "synced" / "tasks.json"
    link = tmp_path / "tasks.json"
    save([], real)
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("this system does not allow symbolic links")
    replacements.clear()  # the setup save above was recorded too
    save([], link)

    assert len(replacements) == 1
    source, destination = replacements[0]
    assert destination == real
    assert source.parent == real.parent


def test_saving_through_a_symlink_creates_the_directory_it_points_into(
    tmp_path: Path, two_tasks: list[Task]
):
    real = tmp_path / "not-yet" / "tasks.json"
    link = tmp_path / "tasks.json"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("this system does not allow symbolic links")

    save(two_tasks, link)

    assert link.is_symlink()
    assert load(real) == two_tasks


@only_on_posix
def test_saving_keeps_the_mode_of_the_file_it_replaces(tmp_path: Path):
    path = tmp_path / "tasks.json"
    save([], path)
    path.chmod(0o644)

    save([Task(1, "Buy milk")], path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o644


@only_on_posix
def test_a_new_file_is_readable_and_writable_by_its_owner_only(tmp_path: Path):
    path = tmp_path / "tasks.json"

    save([], path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
