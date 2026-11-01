"""Tests for the Task record."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import time
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from itertools import count
from typing import Any

import pytest

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.task import Task

TIMESTAMP_FIELDS = ["created", "updated", "start", "stop"]
# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
NAIVE_DAY = datetime(2026, 11, 2)  # noqa: DTZ001
PAST_DAY = datetime(2000, 1, 1)  # noqa: DTZ001
FUTURE_DAY = datetime(2999, 1, 1)  # noqa: DTZ001
MIDDLE_DAY = datetime(2500, 1, 1)  # noqa: DTZ001
AWARE_DAY = datetime(2026, 11, 2, tzinfo=UTC)
FIRST_READING = datetime(2026, 10, 31, 9, 30, 0)  # noqa: DTZ001


@pytest.fixture(name="readings")
def _readings(monkeypatch: pytest.MonkeyPatch) -> Iterator[datetime]:
    # Each call to the task's clock hands out the next second, so a task that
    # reads the clock twice ends up holding two different times.
    ticks = (FIRST_READING + timedelta(seconds=n) for n in count())
    monkeypatch.setattr("task_tracker.task._now", lambda: next(ticks))
    return ticks


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


def test_new_task_takes_a_single_clock_reading_for_all_its_timestamps(
    readings: Iterator[datetime],
):
    task = Task(id=1, name="Buy milk")

    assert task.created == task.updated == task.start == task.stop == FIRST_READING
    # The next reading is still unused, so the task took exactly one.
    assert next(readings) == FIRST_READING + timedelta(seconds=1)


@pytest.mark.usefixtures("readings")
def test_a_timestamp_given_is_kept_and_the_others_share_one_reading():
    task = Task(id=1, name="Buy milk", stop=FUTURE_DAY)

    assert task.stop == FUTURE_DAY
    assert task.created == task.updated == task.start == FIRST_READING


@pytest.mark.parametrize("field_name", ["created", "updated"])
def test_created_and_updated_cannot_be_given(field_name: str):
    # The model stamps them, so a caller cannot pass a false history.
    with pytest.raises(TypeError, match=field_name):
        Task(**{"id": 1, "name": "x", field_name: NAIVE_DAY})  # type: ignore[arg-type]


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
        Task(id=1, name="x", status=status, date_completed=PAST_DAY)


@pytest.mark.parametrize("status", [Status.TO_DO, Status.IN_PROGRESS])
def test_a_task_that_is_not_done_has_no_date_completed_by_default(status: Status):
    assert Task(id=1, name="x", status=status).date_completed is None


def test_a_new_task_cannot_be_done_before_it_was_created():
    # A task that already existed can be done in the past; that is for restore (M2).
    with pytest.raises(ValueError, match="date completed must not be before created"):
        Task(id=1, name="x", status=Status.DONE, date_completed=PAST_DAY)


def test_done_task_without_a_date_completed_gets_the_moment_it_was_created():
    task = Task(id=1, name="x", status=Status.DONE)

    assert task.date_completed is not None
    assert task.date_completed == task.created == task.start == task.stop


def test_a_start_before_created_is_rejected():
    with pytest.raises(ValueError, match="start must not be before created"):
        Task(id=1, name="x", start=PAST_DAY)


def test_a_start_after_created_is_kept():
    # Only "not before created" is ruled out, so a planned future start is fine.
    assert Task(id=1, name="x", start=FUTURE_DAY).start == FUTURE_DAY


def test_the_default_stop_follows_a_future_start():
    # A default of "now" would be before the start and be rejected.
    assert Task(id=1, name="x", start=FUTURE_DAY).stop == FUTURE_DAY


def test_a_stop_before_start_is_rejected():
    with pytest.raises(ValueError, match="stop must not be before start"):
        Task(id=1, name="x", start=FUTURE_DAY, stop=MIDDLE_DAY)


def test_a_stop_before_created_is_rejected():
    with pytest.raises(ValueError, match="stop must not be before"):
        Task(id=1, name="x", stop=PAST_DAY)


def test_a_stop_equal_to_start_is_accepted():
    task = Task(id=1, name="x", start=FUTURE_DAY, stop=FUTURE_DAY)

    assert task.stop == task.start == FUTURE_DAY


def test_a_start_after_the_date_completed_is_rejected():
    with pytest.raises(ValueError, match="start must not be after the date completed"):
        Task(id=1, name="x", status=Status.DONE, start=FUTURE_DAY)


def test_a_stop_after_the_date_completed_is_rejected():
    with pytest.raises(ValueError, match="stop must not be after the date completed"):
        Task(id=1, name="x", status=Status.DONE, stop=FUTURE_DAY)


@pytest.mark.usefixtures("readings")
def test_a_stop_equal_to_the_date_completed_is_accepted():
    task = Task(id=1, name="x", status=Status.DONE, stop=FIRST_READING)

    assert task.stop == task.date_completed == FIRST_READING


def test_stop_has_no_limit_while_the_task_is_not_done():
    assert Task(id=1, name="x", stop=FUTURE_DAY).stop == FUTURE_DAY


@pytest.mark.parametrize("future", [FUTURE_DAY, "2999-01-01", "2999-01-01 09:30:00"])
def test_a_date_completed_in_the_future_is_rejected(future: object):
    with pytest.raises(ValueError, match="future"):
        Task(id=1, name="x", status=Status.DONE, date_completed=future)  # type: ignore[arg-type]


@pytest.mark.usefixtures("readings")
def test_a_date_completed_of_this_very_moment_is_accepted():
    # A real clock reading carries microseconds. They are dropped before the
    # comparison, or a date completed of "now" would count as in the future.
    moment = FIRST_READING.replace(microsecond=500_000)

    task = Task(id=1, name="x", status=Status.DONE, date_completed=moment)

    assert task.date_completed == FIRST_READING


# --- Task.restore: rebuilding a task from a stored record (M2) ---

STORED_CREATED = datetime(2026, 10, 10, 9, 0, 0)  # noqa: DTZ001
STORED_DONE = datetime(2026, 10, 15, 17, 30, 0)  # noqa: DTZ001
# The restore checks that compare with "now" use the controlled clock, so they
# hold whatever day the tests run on.
with_fixed_clock = pytest.mark.usefixtures("readings")


def stored(**overrides: Any) -> dict[str, Any]:
    """A valid stored record; each test changes only the field it is about."""
    record = {
        "id": 1,
        "name": "Buy milk",
        "description": "",
        "created": STORED_CREATED,
        "updated": STORED_CREATED,
        "due": None,
        "date_completed": None,
        "status": Status.TO_DO,
        "priority": Priority.LOW,
        "start": STORED_CREATED,
        "stop": STORED_CREATED,
    }
    return record | overrides


@with_fixed_clock
def test_restore_keeps_the_stored_created_and_updated():
    updated = STORED_CREATED + timedelta(days=1)

    task = Task.restore(**stored(updated=updated))

    assert task.created == STORED_CREATED
    assert task.updated == updated


@with_fixed_clock
def test_restore_accepts_a_task_that_was_done_in_the_past():
    # The constructor cannot build this: its created is always now.
    task = Task.restore(
        **stored(
            status=Status.DONE,
            updated=STORED_DONE,
            stop=STORED_DONE,
            date_completed=STORED_DONE,
        )
    )

    assert task.created == STORED_CREATED
    assert task.date_completed == STORED_DONE


def test_restore_needs_every_field_and_fills_none_in():
    with pytest.raises(TypeError):
        # The missing arguments are the point of the test.
        Task.restore(1, "Buy milk")  # type: ignore[call-arg]  # pylint: disable=missing-kwoa


@with_fixed_clock
def test_restore_turns_iso_text_into_the_one_datetime_form():
    task = Task.restore(
        **stored(
            created="2026-10-10T09:00:00",
            updated="2026-10-10 09:00:00",
            start="2026-10-10T09:00:00",
            stop="2026-10-10T09:00:00",
            due="2026-11-02",
        )
    )

    assert task.created == task.updated == task.start == task.stop == STORED_CREATED
    assert task.due == NAIVE_DAY


@with_fixed_clock
def test_restore_turns_labels_into_enum_members():
    task = Task.restore(
        **stored(
            status="DONE",
            priority="HIGH",
            updated=STORED_DONE,
            stop=STORED_DONE,
            date_completed=STORED_DONE,
        )
    )

    assert task.status is Status.DONE
    assert task.priority is Priority.HIGH


@with_fixed_clock
@pytest.mark.parametrize("field_name", ["created", "updated"])
def test_restore_rejects_bad_stamp_text_naming_the_field(field_name: str):
    with pytest.raises(ValueError, match=field_name):
        Task.restore(**stored(**{field_name: "not a date"}))


@with_fixed_clock
@pytest.mark.parametrize("field_name", ["created", "updated"])
def test_restore_rejects_a_timezone_aware_stamp(field_name: str):
    with pytest.raises(ValueError, match=field_name):
        Task.restore(**stored(**{field_name: AWARE_DAY}))


@with_fixed_clock
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "status": Status.DONE,
                "date_completed": STORED_CREATED - timedelta(days=1),
            },
            "date completed must not be before created",
        ),
        (
            {"start": STORED_CREATED - timedelta(days=1)},
            "start must not be before created",
        ),
        (
            {
                "start": STORED_CREATED + timedelta(days=2),
                "stop": STORED_CREATED + timedelta(days=1),
            },
            "stop must not be before start",
        ),
        (
            {
                "status": Status.DONE,
                "date_completed": STORED_DONE,
                "updated": STORED_DONE,
                "start": STORED_DONE + timedelta(hours=1),
                "stop": STORED_DONE + timedelta(hours=1),
            },
            "start must not be after the date completed",
        ),
        (
            {
                "status": Status.DONE,
                "date_completed": STORED_DONE,
                "updated": STORED_DONE,
                "stop": STORED_DONE + timedelta(hours=1),
            },
            "stop must not be after the date completed",
        ),
        (
            {"updated": STORED_CREATED - timedelta(days=1)},
            "updated must not be before created",
        ),
    ],
    ids=[
        "date-completed-before-created",
        "start-before-created",
        "stop-before-start",
        "start-after-date-completed",
        "stop-after-date-completed",
        "updated-before-created",
    ],
)
def test_restore_rejects_each_broken_timeline_link(
    overrides: dict[str, Any], message: str
):
    with pytest.raises(ValueError, match=message):
        Task.restore(**stored(**overrides))


@with_fixed_clock
def test_restore_rejects_a_created_in_the_future():
    record = stored(
        created=FUTURE_DAY, updated=FUTURE_DAY, start=FUTURE_DAY, stop=FUTURE_DAY
    )

    with pytest.raises(ValueError, match="created must not be in the future"):
        Task.restore(**record)


@with_fixed_clock
def test_restore_rejects_an_updated_in_the_future():
    with pytest.raises(ValueError, match="updated must not be in the future"):
        Task.restore(**stored(updated=FUTURE_DAY))


@with_fixed_clock
def test_restore_rejects_a_date_completed_in_the_future():
    with pytest.raises(ValueError, match="future"):
        Task.restore(**stored(status=Status.DONE, date_completed=FUTURE_DAY))


def test_restore_rejects_a_done_task_without_a_date_completed():
    # The constructor would fill in "now". A stored DONE task always has its date.
    with pytest.raises(ValueError, match="DONE task must have a date completed"):
        Task.restore(**stored(status=Status.DONE))


@pytest.mark.parametrize("status", [Status.TO_DO, Status.IN_PROGRESS])
def test_restore_rejects_a_date_completed_on_a_task_that_is_not_done(status: Status):
    with pytest.raises(ValueError, match="only a DONE task"):
        Task.restore(**stored(status=status, date_completed=STORED_DONE))


@pytest.mark.parametrize("bad_id", ["1", 1.5, True, None])
def test_an_id_that_is_not_an_int_is_rejected(bad_id: object):
    # A hand-edited tasks.json can hold any JSON value. True is an int in Python.
    with pytest.raises(ValueError, match="id must be an int"):
        Task(id=bad_id, name="x")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_id", ["1", 1.5, True, None])
def test_restore_rejects_an_id_that_is_not_an_int(bad_id: object):
    with pytest.raises(ValueError, match="id must be an int"):
        Task.restore(**stored(id=bad_id))


@pytest.mark.parametrize("bad_description", [5, None, ["a"]])
def test_a_description_that_is_not_text_is_rejected(bad_description: object):
    with pytest.raises(ValueError, match="description must be a string"):
        Task(id=1, name="x", description=bad_description)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_description", [5, None, ["a"]])
def test_restore_rejects_a_description_that_is_not_text(bad_description: object):
    with pytest.raises(ValueError, match="description must be a string"):
        Task.restore(**stored(description=bad_description))
