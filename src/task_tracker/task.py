"""The task record."""

from dataclasses import KW_ONLY, dataclass, field
from datetime import date, datetime, time

from task_tracker.priority import Priority
from task_tracker.status import Status

# Stands in for "not given" so a timestamp can default to the clock reading the
# task already holds while the field stays typed `datetime`. Always compared with
# `is`, never `==`, so a caller who passes an equal date still has it kept. D6
# chose naive local time on purpose, so DTZ001 does not apply here.
_UNSET = datetime(1, 1, 1)  # noqa: DTZ001
_GIVEN_DATETIMES = ("due", "date_completed", "start", "stop")


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
        self._validate(now)

    def _normalize(self) -> None:
        if not isinstance(self.name, str):
            # ValueError, not TypeError: the loader catches one type for any bad field.
            raise ValueError("name must be a string")  # noqa: TRY004
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("name must not be blank")
        self.status = Status(self.status)
        self.priority = Priority(self.priority)
        for name in _GIVEN_DATETIMES:
            value = getattr(self, name)
            if value is not _UNSET:
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

    def _validate(self, now: datetime) -> None:
        done = self.date_completed
        if done is not None:
            if self.status is not Status.DONE:
                raise ValueError("only a DONE task can have a date completed")
            if done > now:
                raise ValueError("date completed must not be in the future")
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
