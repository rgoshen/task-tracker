"""Task priority levels."""

from enum import StrEnum


class Priority(StrEnum):
    """Priority level of a task."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MED = "MED"
    LOW = "LOW"
