"""The task record."""

from dataclasses import dataclass, field
from datetime import datetime

from task_tracker.priority import Priority
from task_tracker.status import Status


@dataclass
class Task:
    """A unit of work to track."""

    id: int
    name: str
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
        if not self.name.strip():
            raise ValueError("name must not be blank")
