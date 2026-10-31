"""The task record."""

from dataclasses import KW_ONLY, dataclass
from datetime import date, datetime, time

from task_tracker.priority import Priority
from task_tracker.status import Status

# Stands in for "not given" so the four timestamps can share one clock reading
# while the fields stay typed `datetime`. Always compared with `is`, never `==`,
# so a caller who passes an equal date still has it kept. D6 chose naive local
# time on purpose, so DTZ001 does not apply here.
_UNSET = datetime(1, 1, 1)  # noqa: DTZ001
_TIMESTAMPS = ("created", "updated", "start", "stop")
_DATETIME_FIELDS = ("created", "updated", "due", "date_completed", "start", "stop")


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
    created: datetime = _UNSET
    updated: datetime = _UNSET
    due: datetime | None = None
    date_completed: datetime | None = None
    status: Status = Status.TO_DO
    priority: Priority = Priority.LOW
    start: datetime = _UNSET
    stop: datetime = _UNSET

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            # ValueError, not TypeError: the loader catches one type for any bad field.
            raise ValueError("name must be a string")  # noqa: TRY004
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("name must not be blank")
        self.status = Status(self.status)
        self.priority = Priority(self.priority)
        now = datetime.now().replace(microsecond=0)  # noqa: DTZ005
        self._fill_unset_timestamps(now)
        for name in _DATETIME_FIELDS:
            setattr(self, name, _as_naive_datetime(name, getattr(self, name)))
        self._settle_date_completed(now)

    def _fill_unset_timestamps(self, now: datetime) -> None:
        for name in _TIMESTAMPS:
            if getattr(self, name) is _UNSET:
                setattr(self, name, now)

    def _settle_date_completed(self, now: datetime) -> None:
        if self.status is not Status.DONE:
            if self.date_completed is not None:
                raise ValueError("only a DONE task can have a date completed")
        elif self.date_completed is None:
            self.date_completed = now
        elif self.date_completed > now:
            raise ValueError("date completed must not be in the future")
