"""Task status values."""

from enum import StrEnum


class Status(StrEnum):
    """Current status of a task."""

    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
