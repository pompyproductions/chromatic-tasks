import enum


class TaskCompletionStatus(enum.Enum):
    PENDING = 0
    SCHEDULED = 1
    COMPLETE = 2
    CANCELLED = 3
    ARCHIVED = 4


class TaskCategory(enum.Enum):
    WORK = 0
    SOCIAL = 1
    HOME = 2