from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, DataTable, \
    ContentSwitcher, ListView, ListItem, Button, Input, Select
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
    def __init__(self, *, title:str, category:TaskCategory):
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

    def on_mount(self):
        elem = self.query_one("#new-task-title", expect_type=Input)
        elem.validate(elem.value)


    def reset_form(self):
        for elem in self.query("Input"):
            elem.value = ""
        self.query_one("#new-task-scheduled").parent.disabled = True
        self.query_one("#new-task-status").parent.disabled = True

    @on(Input.Submitted)
    @on(Button.Pressed, "#submit")
    def submit_form(self):

        title_input = self.query_one("#new-task-title", expect_type=Input)
        if not title_input.is_valid:
            print("Title not valid.")
            return
        task_dict = {
            "title": title_input.value,
            "category": self.query_one("#new-task-category", expect_type=Select).value,
            "status": TaskCompletionStatus.PENDING
        }
        status_input = self.query_one("#new-task-status", expect_type=Select)
        if not status_input.is_disabled:
            task_dict["status"] = status_input.value
        date_input = self.query_one("#new-task-scheduled", expect_type=DateInput)

        if not date_input.is_disabled:
            task_dict["date"] = date_input.parse_date()
            if task_dict["date"]["year"] and task_dict["status"] == TaskCompletionStatus.PENDING:
                task_dict["status"] = TaskCompletionStatus.SCHEDULED

        self.post_message(self.NewTaskSubmit(task_dict))
        self.reset_form()



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
            "day": None,
            "hour": None,
            "mins": None
        }
        for task_key, task_value in self.task_data.items():
            if task_value is None:
                continue
            if task_key in ["title", "status", "id", "category"]:
                continue
            if task_key in ["year_scheduled", "month_scheduled", "day_scheduled"]:
                task_date[task_key[:-10]] = task_value
            elif task_key == "time_scheduled":
                task_date["hour"] = task_value.hour
                task_date["mins"] = task_value.minute
            else:
                print(f"(DID NOT DISPLAY) {task_key}: {task_value}")
        self.query_one("#edit-task-scheduled", expect_type=DateInput).populate_inputs(
            date=task_date
        )

    @on(Button.Pressed, "#cancel")
    def key_escape(self):
        self.app.pop_screen()

    @on(Input.Submitted)
    @on(Button.Pressed, "#submit")
    def handle_submit(self):
        print(self.query_one(DateInput).parse_date())

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

    @on(TasksTable.EditEntry)
    def edit_entry(self, message):
        # print(message.key.value)
        task_entry = self.controller.get_task(id=message.key.value)
        if task_entry:
            print(task_entry.to_dict())
            popup = EditTaskPopup(task_data=task_entry.to_dict())
            self.push_screen(popup)

    @on(TasksTable.ChangeEntryStatus)
    def change_entry_status(self, message):
        modified_task = self.controller.edit_task(id=message.key.value, props={"status": message.status})
        if modified_task:
            self.query_one(TasksTable).edit_row(row=message.key, task=modified_task.to_dict())

    @on(NewTaskForm.NewTaskSubmit)
    def create_task(self, message):
        new_task = self.controller.add_task(task=message.task)
        if new_task:
            self.query_one(TasksTable).create_row(new_task)
