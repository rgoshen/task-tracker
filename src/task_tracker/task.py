"""The task record."""

from dataclasses import KW_ONLY, dataclass, field, fields
from datetime import date, datetime, time
from typing import Any, Self

from task_tracker.priority import Priority
from task_tracker.status import Status

# Stands in for "not given" so a timestamp can default to the clock reading the
# task already holds while the field stays typed `datetime`. Always compared with
# `is`, never `==`, so a caller who passes an equal date still has it kept. D6
# chose naive local time on purpose, so DTZ001 does not apply here.
_UNSET = datetime(1, 1, 1)  # noqa: DTZ001
_DATETIME_FIELDS = ("created", "updated", "due", "date_completed", "start", "stop")
# The only datetimes that may be empty. The others take part in the timeline.
_OPTIONAL_DATETIMES = ("due", "date_completed")


def _now() -> datetime:
    """The current local time to whole seconds.

    A task reads this once and shares the result, so its timestamps agree.
    Tests replace it to control the clock.
    """
    return datetime.now().replace(microsecond=0)  # noqa: DTZ005


def _as_naive_datetime(name: str, value: object) -> datetime | None:
    """Turn an ISO 8601 string, a date, or a datetime into one form.

    The result is a naive local datetime with whole seconds, so `isoformat()`
    always reads `YYYY-MM-DDTHH:MM:SS`. A bare date means midnight (Q6).
    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
    elif isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min)
    if not isinstance(value, datetime):
        # ValueError, not TypeError: the loader catches one type for any bad field.
        raise ValueError(f"{name} must be a date or ISO 8601 text")  # noqa: TRY004
    if value.tzinfo is not None:
        raise ValueError(f"{name} must be a naive local datetime")
    return value.replace(microsecond=0)


def _require_utf8_text(name: str, text: str) -> None:
    """Refuse text that UTF-8 cannot hold, because `save` writes UTF-8.

    An undecodable byte in a command-line argument becomes a lone surrogate
    (`surrogateescape`), and JSON accepts an escaped one, so such text can arrive
    from either side. Refusing it here makes it a clear error at the door, and a
    file that holds it a corrupt file that names the record, instead of a codec
    error from partway through a listing or a save.
    """
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"{name} must be valid UTF-8 text") from None


# README.md "Task object" defines 11 fields; pylint's default limit is 7.
@dataclass
class Task:  # pylint: disable=too-many-instance-attributes
    """A unit of work to track."""

    id: int
    name: str
    # Everything below is keyword-only: six fields share a type, so swapped
    # positional arguments would pass type checking.
    _: KW_ONLY
    description: str = ""
    # Stamped by the model, never given by a caller, so a history cannot be
    # faked. Storage restores stored values through `Task.restore()` (M2).
    created: datetime = field(init=False)
    updated: datetime = field(init=False)
    due: datetime | None = None
    date_completed: datetime | None = None
    status: Status = Status.TO_DO
    priority: Priority = Priority.LOW
    start: datetime = _UNSET
    stop: datetime = _UNSET

    def __post_init__(self) -> None:
        now = _now()
        self.created = now
        self.updated = now
        self._normalize()
        self._fill_in_defaults(now)
        self._validate()
        # Only a new task is held to the clock. A stored one was valid when it was
        # saved, and the clock can move back (daylight saving, a changed time zone).
        if self.date_completed is not None and self.date_completed > now:
            raise ValueError("date completed must not be in the future")

    @classmethod
    def restore(cls, /, **record: Any) -> Self:
        """Rebuild a task from a stored record, keeping its stored stamps.

        The constructor stamps `created` and `updated` with the clock, so it cannot
        build a task that already existed. This runs every other rule the
        constructor does and fills nothing in, so a record must hold every field
        and no other. The field list is the dataclass's own.

        `cls` is positional-only so that a stored key named `cls` lands in `record`
        and is reported as an unknown field, not raised as a TypeError.
        """
        names = {field.name for field in fields(cls)}
        if missing := names - record.keys():
            raise ValueError(f"missing field(s): {', '.join(sorted(missing))}")
        if unknown := record.keys() - names:
            raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
        task = cls.__new__(cls)
        for name in names:
            setattr(task, name, record[name])
        # Same class: restore is a classmethod of Task, so these steps are its own.
        task._normalize()  # pylint: disable=protected-access
        task._validate()  # pylint: disable=protected-access
        return task

    def _normalize(self) -> None:
        # ValueError, not TypeError: the loader catches one type for any bad field.
        # bool is an int in Python, and JSON `true` must not pass for an ID.
        if isinstance(self.id, bool) or not isinstance(self.id, int):
            raise ValueError("id must be an int")  # noqa: TRY004
        if self.id < 1:
            raise ValueError("id must be 1 or more")
        if not isinstance(self.name, str):
            raise ValueError("name must be a string")  # noqa: TRY004
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("name must not be blank")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")  # noqa: TRY004
        _require_utf8_text("name", self.name)
        _require_utf8_text("description", self.description)
        self.status = Status(self.status)
        self.priority = Priority(self.priority)
        for name in _DATETIME_FIELDS:
            value = getattr(self, name)
            if value is _UNSET:
                continue
            if value is None and name not in _OPTIONAL_DATETIMES:
                # ValueError, not TypeError: a null in the file must reach the loader.
                raise ValueError(f"{name} must be a date or ISO 8601 text")
            setattr(self, name, _as_naive_datetime(name, value))

    def _fill_in_defaults(self, now: datetime) -> None:
        if self.status is Status.DONE and self.date_completed is None:
            self.date_completed = now
        if self.start is _UNSET:
            self.start = self.created
        if self.stop is _UNSET:
            # Now, unless the task is planned to start later: a stop before the
            # start is impossible.
            self.stop = max(now, self.start)

    def _validate(self) -> None:
        if self.updated < self.created:
            raise ValueError("updated must not be before created")
        done = self.date_completed
        if self.status is Status.DONE and done is None:
            raise ValueError("a DONE task must have a date completed")
        if self.status is not Status.DONE and done is not None:
            raise ValueError("only a DONE task can have a date completed")
        self._check_timeline()

    def _check_timeline(self) -> None:
        """Enforce created <= start <= stop <= date completed (when there is one)."""
        done = self.date_completed
        if done is not None and done < self.created:
            raise ValueError("date completed must not be before created")
        if self.start < self.created:
            raise ValueError("start must not be before created")
        if self.stop < self.start:
            raise ValueError("stop must not be before start")
        if done is not None and self.start > done:
            raise ValueError("start must not be after the date completed")
        if done is not None and self.stop > done:
            raise ValueError("stop must not be after the date completed")
