from enum import Enum


class TaskCompletionStatus(Enum):
    PENDING = 0
    SCHEDULED = 1
    COMPLETE = 2
    CANCELLED = 3
    ARCHIVED = 4
    def to_str(self):
        return self.name.capitalize()

class TaskCategory(Enum):
    WORK = 0
    SOCIAL = 1
    HOME = 2

class FormType(Enum):
    NEW_TASK = 0
    EDIT_TASK = 1