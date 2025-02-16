from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, DataTable, \
    ContentSwitcher, ListView, ListItem, Button, Input, Select, \
    Checkbox
from textual.containers import Horizontal, Vertical
from textual.validation import Length
from textual.message import Message
from textual.screen import ModalScreen
from textual import on

from enums import TaskCompletionStatus, TaskCategory
from datetime import time

from .widgets import FormCouple, DateInput


# ---
# Objects

class Task:
    def __init__(self, *args, title:str, category:TaskCategory):
        self.title = title
        self.category = category
        self.status = TaskCompletionStatus.PENDING
        self.description : str | None = None
        self.year_scheduled : int | None = None
        self.month_scheduled : int | None = None
        self.day_scheduled : int | None = None
        self.time_scheduled : time | None = None

    def setup(self, task_entry): # using a db entry
        self.title = task_entry.title

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
    def time_to_string(time):
        return f"{time.hour}h{time.minute:02d}"

    BINDINGS = [
        ("backspace", "delete_entry()", "Delete Entry"),
        ("enter", "edit_entry()", "Edit Entry")
    ]

    class DeleteEntry(Message):
        def __init__(self, key):
            self.key = key
            super().__init__()
    class EditEntry(Message):
        def __init__(self, key):
            self.key = key
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
        self.add_columns(
            "Title", "Status", "Date/Time"
        )

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

    def action_delete_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.DeleteEntry(row_key))
        except Exception: # this happens when there are no rows & you try to delete row 0
            print("Failed.")

    def action_edit_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            print(row_key.value, self.get_row(row_key))
            self.post_message(self.EditEntry(row_key))
        except Exception:
            print("Failed.")

class NewTaskForm(Vertical):

    class NewTaskSubmit(Message):
        def __init__(self, task):
            self.task = task
            super().__init__()

    def compose(self) -> ComposeResult:
        category_options = [
            ("Home", TaskCategory.HOME),
            ("Work", TaskCategory.WORK),
            ("Social", TaskCategory.SOCIAL)
        ]
        status_options = [
            ("Completed", TaskCompletionStatus.COMPLETE),
            ("Archived", TaskCompletionStatus.ARCHIVED),
            ("Cancelled", TaskCompletionStatus.CANCELLED)
        ]
        yield FormCouple("Title:", Input(id="new-task-title", placeholder="Short descriptor for your task.", validators=[Length(minimum=1)], valid_empty=False, validate_on=["changed"]))
        yield FormCouple("Category:", Select(category_options, allow_blank=False, id="new-task-category"))
        yield FormCouple("Status:", Select(status_options, allow_blank=False, id="new-task-status"), optional=True)
        yield FormCouple("Scheduled:", DateInput(id="new-task-scheduled"), optional=True)
        with Horizontal(classes="form-end"):
            yield Button("Create task", id="submit")

    def on_select_changed(self, event):
        print(event.value)

    def on_mount(self):
        elem = self.query_one("#new-task-title")
        elem.validate(elem.value)

    @on(Input.Submitted)
    @on(Button.Pressed, "#submit")
    def submit_form(self, event):
        title_elem = self.query_one("#new-task-title", expect_type=Input)
        if not title_elem.is_valid:
            print("title not valid")
            return
        task = Task(
            title=title_elem.value,
            category=self.query_one("#new-task-category", expect_type=Select).value
        )

        status_elem = self.query_one("#new-task-status", expect_type=Select)
        if not status_elem.is_disabled:
            task.status = status_elem.value

        date_elem = self.query_one("#new-task-scheduled", expect_type=DateInput)
        if not date_elem.is_disabled:
            if date_elem.date["year"]:
                task.year_scheduled = date_elem.date["year"]
            if date_elem.date["month"]:
                task.month_scheduled = date_elem.date["month"]
            if date_elem.date["day"]:
                task.day_scheduled = date_elem.date["day"]
            if date_elem.time["hour"]:
                if date_elem.time["mins"]:
                    task.time_scheduled = time(hour=date_elem.time["hour"], minute=date_elem.time["mins"])
                else:
                    task.time_scheduled = time(hour=date_elem.time["hour"])
        self.post_message(self.NewTaskSubmit(task))
        self.reset_form()

    def reset_form(self):
        for elem in self.query("Input"):
            elem.value = ""

# ---
# Modals

class EditTaskPopup(ModalScreen):
    category_options = [
        ("Home", TaskCategory.HOME),
        ("Work", TaskCategory.WORK),
        ("Social", TaskCategory.SOCIAL)
    ]
    status_options = [
        ("Pending", TaskCompletionStatus.PENDING),
        ("Completed", TaskCompletionStatus.COMPLETE),
        ("Archived", TaskCompletionStatus.ARCHIVED),
        ("Cancelled", TaskCompletionStatus.CANCELLED)
    ]

    def __init__(self, *args, task_data:dict, **kwargs):
        self.task_data = task_data
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield FormCouple("Title:", Input(
                id="edit-task-title",
                placeholder="Short descriptor for your task.",
                validators=[Length(minimum=1)],
                valid_empty=False,
                validate_on=["changed"]
            ))
            yield FormCouple("Category:", Select(
                EditTaskPopup.category_options,
                allow_blank=False,
                id="edit-task-category"
            ))
            yield FormCouple("Status:", Select(
                EditTaskPopup.status_options,
                allow_blank=False,
                id="edit-task-status"
            ))
            yield FormCouple("Scheduled:", DateInput(
                id="edit-task-scheduled"
            ), optional=True)
            with Horizontal(classes="form-end"):
                yield Button("Cancel", id="cancel")
                yield Button("Edit task", id="submit")

    def on_mount(self):
        # Required values
        self.query_one("#edit-task-title", expect_type=Input).value = self.task_data["title"]
        self.query_one("#edit-task-status", expect_type=Select).value = self.task_data["status"]
        self.query_one("#edit-task-category", expect_type=Select).value = self.task_data["category"]
        # Optional values
        task_date = {
            "year": None,
            "month": None,
            "day": None
        }
        task_time = {
            "hour": None,
            "mins": None
        }
        for task_key, task_value in self.task_data.items():
            if task_key in ["title", "status", "id", "category"]:
                continue
            if task_key in ["year_scheduled", "month_scheduled", "day_scheduled"]:
                task_date[task_key[:-10]] = task_value
            elif task_key == "time_scheduled":
                task_time["hour"] = task_value.hour
                task_time["mins"] = task_value.minute
            else:
                print(f"{task_key}: {task_value}")
        self.query_one("#edit-task-scheduled", expect_type=DateInput).set_date(
            date=task_date, time=task_time
        )

    @on(Button.Pressed, "#cancel")
    def key_escape(self):
        self.app.pop_screen()

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
        if self.controller.delete_task(id=message.key.value):
            self.query_one(TasksTable).remove_row(message.key)
        # print(message.key.value)

    @on(TasksTable.EditEntry)
    def edit_entry(self, message):
        task_entry = self.controller.get_task(id=message.key.value)
        if task_entry:
            print(task_entry.to_dict())
            # popup = EditTaskPopup()
            popup = EditTaskPopup(task_data=task_entry.to_dict())
            self.push_screen(popup)

    @on(NewTaskForm.NewTaskSubmit)
    def create_task(self, message):
        new_task = self.controller.add_task(task=message.task)
        if new_task:
            self.query_one(TasksTable).create_row(new_task)
        # for attr in dir(message.task):
        #     if not attr.startswith("__"):
        #         print(attr, getattr(message.task, attr))