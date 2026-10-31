"""The task record."""

from dataclasses import KW_ONLY, dataclass, field, fields
from datetime import datetime

from task_tracker.priority import Priority
from task_tracker.status import Status


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
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    due: datetime | None = None
    date_completed: datetime | None = None
    status: Status = Status.TO_DO
    priority: Priority = Priority.LOW
    start: datetime = field(default_factory=datetime.now)
    stop: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            # ValueError, not TypeError: the loader catches one type for any bad field.
            raise ValueError("name must be a string")  # noqa: TRY004
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("name must not be blank")
        self.status = Status(self.status)
        self.priority = Priority(self.priority)
        self._reject_aware_datetimes()
        if self.status is not Status.DONE and self.date_completed is not None:
            raise ValueError("only a DONE task can have a date completed")

    def _reject_aware_datetimes(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, datetime) and value.tzinfo is not None:
                raise ValueError(f"{item.name} must be a naive local datetime")
