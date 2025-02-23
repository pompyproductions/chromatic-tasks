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
        def __init__(self, *, row_key):
            super().__init__()
            self.row_key = row_key

    class EditEntry(Message):
        def __init__(self, *, row_key):
            super().__init__()
            self.row_key = row_key

    class ChangeEntryStatus(Message):
        def __init__(self, *, row_key, status:TaskCompletionStatus):
            super().__init__()
            self.row_key = row_key
            self.status = status

    def __init__(self, *args, task_instances=None, **kwargs):
        super().__init__(*args, **kwargs)
        if task_instances is None:
            task_instances = []
        self.task_instances = task_instances

    def on_mount(self):
        self.cursor_type = "row"
        self.create_columns()
        for task in self.task_instances:
            self.create_row(task[0])

    def create_columns(self):
        for column_id, label, width in [
            ("title", "Title", 0),
            ("status", "Status", 10),
            ("scheduled", "Date/Time", 0)
        ]:
            if width:
                self.add_column(label, key=column_id, width=width)
            else:
                self.add_column(label, key=column_id)

    def create_row(self, task_instance):
        title = task_instance.title
        status = task_instance.status
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
            task_instance.year_scheduled,
            task_instance.month_scheduled,
            task_instance.day_scheduled
        )
        if task_instance.time_scheduled:
            date_time += f" | {self.time_to_string(task_instance.time_scheduled)}"

        self.add_row(title, status, date_time, key=task_instance.id)

    def edit_row(self, *, row_key, task_dict:dict):
        self.update_cell(
            row_key=row_key, column_key="title",
            value=task_dict["title"]
        )
        self.update_cell(
            row_key=row_key, column_key="status",
            value=task_dict["status"].to_str()
        )
        if task_dict["date"]:
            self.update_cell(
                row_key=row_key, column_key="scheduled",
                value=DateInput.date_to_str(task_dict["date"])
            )

    def get_row_by_id(self, row_id:int):
        for row_key, row in self.rows.items():
            if row_key.value == row_id:
                return row

    def get_row_key(self, row_id:int):
        for row_key, row in self.rows.items():
            if row_key.value == row_id:
                return row_key

    def action_delete_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.DeleteEntry(row_key=row_key))
        except Exception: # this happens when there are no rows & you try to delete row 0
            print("Failed.")

    def action_edit_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.EditEntry(row_key=row_key))
        except Exception:
            print("Failed.")

    def action_mark_as_complete(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.ChangeEntryStatus(row_key=row_key, status=TaskCompletionStatus.COMPLETE))
        except Exception:
            print("Failed.")


class NewTaskForm(Vertical):

    class SubmitForm(Message):
        def __init__(self, *, task_dict:dict):
            self.task_dict = task_dict
            super().__init__()

    def compose(self) -> ComposeResult:
        yield TaskForm(FormType.NEW_TASK)

    @on(TaskForm.SubmitForm)
    def handle_submit(self, message):
        self.post_message(self.SubmitForm(task_dict=message.task_dict))
        self.query_one(TaskForm).reset_form()

# ---
# Modals

class EditTaskPopup(ModalScreen):

    class SubmitForm(Message):
        def __init__(self, *, task_dict:dict, row_key:int):
            super().__init__()
            self.row_key = row_key
            self.task_dict = task_dict

    def __init__(self, *args, task_dict:dict, row_key, **kwargs):
        self.task_dict = task_dict
        self.row_key = row_key
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield TaskForm(FormType.EDIT_TASK, task_dict=self.task_dict)

    @on(Button.Pressed, "#cancel")
    def key_escape(self):
        self.app.pop_screen()

    @on(TaskForm.SubmitForm)
    def handle_submit(self, message):
        self.post_message(self.SubmitForm(task_dict=message.task_dict, row_key=self.row_key))

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
        self.ref_task_table = None

    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar()
            with ContentSwitcher(initial="create-task"):
                yield TasksTable(id="data-table", task_instances=self.controller.get_all_tasks())
                yield NewTaskForm(id="create-task", classes="form")
        yield Footer()

    def on_mount(self):
        self.ref_task_table = self.query_one(TasksTable)

    def on_list_view_highlighted(self, event):
        self.query_one(ContentSwitcher).current = event.item.id

    @on(TasksTable.DeleteEntry)
    def delete_entry(self, message):
        if self.controller.delete_task(row_id=message.row_key.value):
            self.query_one(TasksTable).remove_row(message.row_key)

    @on(TasksTable.EditEntry)
    def edit_entry(self, message):
        task_instance = self.controller.get_task(row_id=message.row_key.value)
        if task_instance:
            popup = EditTaskPopup(task_dict=task_instance.to_dict(), row_key=message.row_key)
            self.push_screen(popup)

    @on(TasksTable.ChangeEntryStatus)
    def change_entry_status(self, message):
        task_instance = self.controller.edit_task(row_id=message.row_key.value, task_dict={"status": message.status})
        if task_instance:
            self.query_one(TasksTable).edit_row(row_key=message.row_key, task_dict=task_instance.to_dict())

    @on(NewTaskForm.SubmitForm)
    def create_task(self, message):
        task_instance = self.controller.add_task(task_dict=message.task_dict)
        if task_instance:
            self.query_one(TasksTable).create_row(task_instance)

    @on(EditTaskPopup.SubmitForm)
    def edit_task(self, message):
        task = self.controller.edit_task(row_id=message.row_key.value, task_dict=message.task_dict)
        if task:
            self.ref_task_table.edit_row(row_key=message.row_key, task_dict=task.to_dict())
            self.pop_screen()