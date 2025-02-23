from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, DataTable, \
    ContentSwitcher, ListView, ListItem, Button
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual import on

from enums import TaskCompletionStatus, TaskCategory, FormType

from .widgets import FormCouple, DateInput, TaskForm

# ---
# Main views

class TasksTable(DataTable):

    @staticmethod
    def date_to_string(year=None, month=None, day=None):
        text = "No date"
        if year:
            text = str(year)
            if month:
                text = f"{DateInput.month_to_word(month)} {str(year)}"
                if day:
                    text = f"{DateInput.month_to_word(month)} {str(day)}, {str(year)}"
        return text

    @staticmethod
    def time_to_string(time_dict):
        return f"{time_dict.hour}h{time_dict.minute:02d}"

    BINDINGS = [
        ("backspace", "delete_entry()", "Delete entry"),
        ("enter", "edit_entry()", "Edit entry"),
        ("m", "mark_as_complete()", "Mark as complete")
    ]

    class DeleteEntry(Message):
        def __init__(self, key):
            self.key = key
            super().__init__()
    class EditEntry(Message):
        def __init__(self, key):
            self.key = key
            super().__init__()
    class ChangeEntryStatus(Message):
        def __init__(self, *, key, status):
            self.key = key
            self.status = status
            super().__init__()

    def __init__(self, *args, tasks=None, **kwargs):
        if tasks is None:
            tasks = []
        self.tasks = tasks
        super().__init__(*args, **kwargs)

    def on_mount(self):
        self.cursor_type = "row"
        self.create_columns()
        for task in self.tasks:
            self.create_row(task[0])

    def create_columns(self):
        for key, label, width in [
            ("title", "Title", 0),
            ("status", "Status", 10),
            ("scheduled", "Date/Time", 0)
        ]:
            if width:
                self.add_column(label, key=key, width=width)
            else:
                self.add_column(label, key=key)

    def create_row(self, task):
        title = task.title
        status = task.status
        match status:
            case TaskCompletionStatus.COMPLETE:
                status = "Complete"
            case TaskCompletionStatus.PENDING:
                status = "Pending"
            case TaskCompletionStatus.SCHEDULED:
                status = "Scheduled"
            case TaskCompletionStatus.ARCHIVED:
                status = "Archived"
        date_time = self.date_to_string(
            task.year_scheduled,
            task.month_scheduled,
            task.day_scheduled
        )
        if task.time_scheduled:
            date_time += f" | {self.time_to_string(task.time_scheduled)}"

        self.add_row(title, status, date_time, key=task.id)

    def edit_row(self, *, row, task):
        columns = ["title", "status", "schedule"]
        for key, value in task.items():
            if key in columns:
                label = value
                if isinstance(value, TaskCategory | TaskCompletionStatus):
                    label = label.name.title()
                self.update_cell(row_key=row, column_key=key, value=label)

    def action_delete_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.DeleteEntry(row_key))
        except Exception: # this happens when there are no rows & you try to delete row 0
            print("Failed.")

    def action_edit_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            # print(row_key.value)
            self.post_message(self.EditEntry(row_key))
        except Exception:
            print("Failed.")

    def action_mark_as_complete(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.ChangeEntryStatus(key=row_key, status=TaskCompletionStatus.COMPLETE))
        except Exception:
            print("Failed.")


class NewTaskForm(Vertical):

    class SubmitForm(Message):
        def __init__(self, task):
            self.task = task
            super().__init__()

    def compose(self) -> ComposeResult:
        yield TaskForm(FormType.NEW_TASK)

    @on(TaskForm.SubmitForm)
    def handle_submit(self, message):
        self.post_message(self.SubmitForm(message.task_dict))
        self.query_one(TaskForm).reset_form()

# ---
# Modals

class EditTaskPopup(ModalScreen):

    class SubmitForm(Message):
        def __init__(self, task_dict):
            super().__init__()
            self.task_dict = task_dict

    def __init__(self, *args, task_dict:dict, **kwargs):
        self.task_dict = task_dict
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield TaskForm(FormType.EDIT_TASK, task_dict=self.task_dict)

    @on(Button.Pressed, "#cancel")
    def key_escape(self):
        self.app.pop_screen()

    @on(TaskForm.SubmitForm)
    def handle_submit(self, message):
        self.post_message(self.SubmitForm(message.task_dict))

# ---
# Navigation
class Sidebar(ListView):
    def compose(self):
        yield ListItem(Label("Table view"), id="data-table")
        yield ListItem(Label("Create task"), id="create-task")

# ---
# App
class TasksApp(App):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller
        self.theme = "gruvbox"
        self.title = "CHROMATIC Tasks"

    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar()
            with ContentSwitcher(initial="create-task"):
                yield TasksTable(id="data-table", tasks=self.controller.get_all_tasks())
                yield NewTaskForm(id="create-task", classes="form")
        yield Footer()

    def on_list_view_highlighted(self, event):
        self.query_one(ContentSwitcher).current = event.item.id

    @on(TasksTable.DeleteEntry)
    def delete_entry(self, message):
        if self.controller.delete_task(task_id=message.key.value):
            self.query_one(TasksTable).remove_row(message.key)

    @on(TasksTable.EditEntry)
    def edit_entry(self, message):
        task_entry = self.controller.get_task(task_id=message.key.value)
        if task_entry:
            print(task_entry.to_dict())
            popup = EditTaskPopup(task_dict=task_entry.to_dict())
            self.push_screen(popup)

    @on(TasksTable.ChangeEntryStatus)
    def change_entry_status(self, message):
        modified_task = self.controller.edit_task(id=message.key.value, props={"status": message.status})
        if modified_task:
            self.query_one(TasksTable).edit_row(row=message.key, task=modified_task.to_dict())

    @on(NewTaskForm.SubmitForm)
    def create_task(self, message):
        new_task = self.controller.add_task(task_dict=message.task)
        if new_task:
            self.query_one(TasksTable).create_row(new_task)
