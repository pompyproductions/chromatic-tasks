from enum import Enum


class TaskCompletionStatus(Enum):
    PENDING = 0
    SCHEDULED = 1
    COMPLETE = 2
    CANCELLED = 3
    ARCHIVED = 4

class TaskCategory(Enum):
    WORK = 0
    SOCIAL = 1
    HOME = 2