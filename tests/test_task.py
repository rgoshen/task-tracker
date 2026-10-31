"""Tests for the Task record."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import time
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.task import Task

TIMESTAMP_FIELDS = ["created", "updated", "start", "stop"]
# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
NAIVE_DAY = datetime(2026, 11, 2)  # noqa: DTZ001
PAST_DAY = datetime(2000, 1, 1)  # noqa: DTZ001
AWARE_DAY = datetime(2026, 11, 2, tzinfo=UTC)
# Separate clock reads differ in only about a quarter of constructions, so one
# construction can pass by luck; repeating makes the check reliable.
SKEW_REPEATS = 200


@pytest.fixture
def kolkata_time(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # UTC+5:30 with no daylight saving, so it differs from UTC all year round.
    monkeypatch.setenv("TZ", "Asia/Kolkata")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_new_task_has_the_documented_defaults():
    task = Task(id=1, name="Buy milk")

    assert task.status is Status.TO_DO
    assert task.priority is Priority.LOW
    assert task.description == ""
    assert task.due is None
    assert task.date_completed is None


@pytest.mark.parametrize(
    "given",
    [
        "2026-11-02",
        "2026-11-02T00:00:00",
        "2026-11-02 00:00:00",
        date(2026, 11, 2),
        datetime(2026, 11, 2, 0, 0, 0, 123456),  # noqa: DTZ001
    ],
)
def test_every_way_of_giving_a_date_becomes_the_same_datetime(given: object):
    task = Task(id=1, name="x", due=given)  # type: ignore[arg-type]

    assert task.due is not None
    assert task.due == NAIVE_DAY
    assert task.due.isoformat() == "2026-11-02T00:00:00"


@pytest.mark.parametrize("field_name", TIMESTAMP_FIELDS)
def test_default_timestamps_have_whole_seconds(field_name: str):
    assert getattr(Task(id=1, name="x"), field_name).microsecond == 0


@pytest.mark.parametrize(
    "given", ["2026-13-45", "not a date", 5, "2026-11-02T09:00:00+00:00"]
)
def test_a_date_that_is_not_naive_local_time_is_rejected_naming_the_field(
    given: object,
):
    with pytest.raises(ValueError, match="due"):
        Task(id=1, name="x", due=given)  # type: ignore[arg-type]


def test_new_task_shares_one_clock_reading_across_its_timestamps():
    for _ in range(SKEW_REPEATS):
        task = Task(id=1, name="Buy milk")

        assert task.created == task.updated == task.start == task.stop


def test_timestamps_not_given_share_one_reading_and_given_ones_are_kept():
    for _ in range(SKEW_REPEATS):
        task = Task(id=1, name="Buy milk", updated=PAST_DAY)

        assert task.updated == PAST_DAY
        assert task.created == task.start == task.stop
        assert task.created > PAST_DAY


@pytest.mark.usefixtures("kolkata_time")
@pytest.mark.parametrize("field_name", TIMESTAMP_FIELDS)
def test_timestamp_defaults_to_the_moment_the_task_is_created(field_name: str):
    # Under a non-UTC zone this fails for a default read from UTC, which would
    # otherwise pass on a UTC machine such as the CI runner.
    # D6 chose naive local time on purpose, so DTZ005 does not apply here.
    # The task keeps whole seconds, so the lower bound is truncated the same way.
    before = datetime.now().replace(microsecond=0)  # noqa: DTZ005
    task = Task(id=1, name="Buy milk")
    after = datetime.now()  # noqa: DTZ005

    assert before <= getattr(task, field_name) <= after


@pytest.mark.parametrize("field_name", TIMESTAMP_FIELDS)
def test_default_timestamps_are_naive_local_time(field_name: str):
    task = Task(id=1, name="Buy milk")

    assert getattr(task, field_name).tzinfo is None


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected(name: str):
    with pytest.raises(ValueError, match="name"):
        Task(id=1, name=name)


def test_non_string_name_is_rejected_with_value_error():
    # A hand-edited tasks.json can hold null, and the loader must see ValueError.
    with pytest.raises(ValueError, match="name"):
        Task(id=1, name=None)  # type: ignore[arg-type]


def test_name_is_stored_without_surrounding_whitespace():
    assert Task(id=1, name="  Buy milk  ").name == "Buy milk"


def test_status_and_priority_labels_become_enum_members():
    task = Task(id=1, name="x", status="DONE", priority="HIGH")  # type: ignore[arg-type]

    assert task.status is Status.DONE
    assert task.priority is Priority.HIGH


@pytest.mark.parametrize(
    ("field_name", "label"), [("status", "FINISHED"), ("priority", "URGENT")]
)
def test_unknown_status_or_priority_label_is_rejected(field_name: str, label: str):
    with pytest.raises(ValueError, match=label):
        Task(**{"id": 1, "name": "x", field_name: label})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "extra"),
    [
        ("created", {}),
        ("updated", {}),
        ("start", {}),
        ("stop", {}),
        ("due", {}),
        ("date_completed", {"status": Status.DONE}),
    ],
)
def test_timezone_aware_datetime_is_rejected(field_name: str, extra: dict):
    # An aware value next to naive ones makes a later sort raise TypeError.
    fields = {"id": 1, "name": "x", field_name: AWARE_DAY, **extra}

    with pytest.raises(ValueError, match=field_name):
        Task(**fields)


def test_id_and_name_can_be_given_positionally():
    task = Task(1, "Buy milk")

    assert (task.id, task.name) == (1, "Buy milk")


def test_other_fields_cannot_be_given_positionally():
    # Six fields share the datetime type, so swapped arguments would type-check.
    with pytest.raises(TypeError):
        Task(1, "x", "a description", NAIVE_DAY, NAIVE_DAY)  # type: ignore[misc]


@pytest.mark.parametrize("status", [Status.TO_DO, Status.IN_PROGRESS])
def test_only_a_done_task_can_have_a_date_completed(status: Status):
    with pytest.raises(ValueError, match="date completed"):
        Task(id=1, name="x", status=status, date_completed=NAIVE_DAY)


def test_done_task_keeps_its_date_completed():
    task = Task(id=1, name="x", status=Status.DONE, date_completed=NAIVE_DAY)

    assert task.date_completed == NAIVE_DAY
