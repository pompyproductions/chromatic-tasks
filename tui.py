from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, DataTable, \
    ContentSwitcher, ListView, ListItem, Button, Input, Select, \
    Switch, Checkbox
from textual.containers import Horizontal, Vertical
from textual.validation import Validator, ValidationResult
from textual.message import Message
from textual import on
import db
from enums import TaskCompletionStatus, TaskCategory

# ---
# Input validators

class YearValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        try:
            year = int(value)
            if year < 999:
                return self.failure("Year too small.")
            elif year > 2999:
                return self.failure("Year too big.")
            else:
                return self.success()
        except ValueError:
            return self.failure("Couldn't convert to a number.")

class MonthValidator(Validator):
    def validate(self, value: str):
        try:
            month = int(value)
            if month < 1:
                return self.failure("Month should be between 1 and 12 inclusive.")
            elif month > 12:
                return self.failure("Month should be between 1 and 12 inclusive.")
            else:
                return self.success()
        except ValueError:
            return self.failure("Couldn't convert to a number.")

class DateValidator(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.month_input = month_input
        # self.year_input = year_input

    def validate(self, value: str):
        try:
            day = int(value)
            month = self.parent_widget.
        except ValueError:
            return self.failure("Couldn't convert to a number.")

# ---
# Composite widgets

class FormCouple(Horizontal):
    def __init__(self, label, input_widget, *args, optional=False, **kwargs):
        self.optional = optional
        self.label = label
        self.input_widget = input_widget
        input_widget.add_class("input-widget")
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        if self.optional:
            self.input_widget.disabled = True
            yield Checkbox(self.label, classes="input-label optional")
        else:
            yield Label(self.label, classes="input-label")
        yield self.input_widget

    def on_checkbox_changed(self, event):
        self.query_one(".input-widget").disabled = not event.value


class DateInput(Horizontal):
    def compose(self) -> ComposeResult:
        yield Input(max_length=4, placeholder="YYYY", type="integer", classes="double", id="date-year", validators=[YearValidator()], validate_on=["changed"])
        yield Input(max_length=2, placeholder="MM", type="integer", id="date-month", validators=[MonthValidator()], validate_on=["changed"])
        yield Input(max_length=2, placeholder="DD", type="integer", id="date-day", validators=[DateValidator()])
        yield Input(max_length=2, placeholder="hh", type="integer", id="time-hour")
        yield Input(max_length=2, placeholder="mm", type="integer", id="time-mins")
        yield Label("No date")

    @on(Input.Changed)
    def validate_inputs(self, event):
        year = self.query_one("#date-year")
        month = self.query_one("#date-month")
        day = self.query_one("#date-day")
        hour = self.query_one("#time-hour")
        mins = self.query_one("#time-mins")
        if event:
            print(event.input.id)
        match event.input.id:
            case "date-year":
                if event.input.is_valid:
                    self.query_one("#date-month").disabled = False
                else:
                    month.disabled = True
                    day.disabled = True
                    hour.disabled = True
                    mins.disabled = True
            case "date-month":
                if event.input.is_valid:
                    self.query_one("#date-day").disabled = False
                else:
                    day.disabled = True
                    hour.disabled = True
                    mins.disabled = True
            case "date-day":
                if event.input.is_valid:
                    self.query_one("#time-hour").disabled = False
                else:
                    hour.disabled = True
                    mins.disabled = True
            case "time-hour":
                if event.input.is_valid:
                    self.query_one("#time-mins").disabled = False
                else:
                    mins.disabled = True

# ---
# Main views

class TasksTable(DataTable):
    def __init__(self, *args, tasks=None, **kwargs):
        if tasks is None:
            tasks = []
        self.tasks = tasks
        super().__init__(*args, **kwargs)

    def on_mount(self):
        self.cursor_type = "row"
        self.create_columns()
        for task in self.tasks:
            title = task[0].title
            status = task[0].status
            match status:
                case TaskCompletionStatus.COMPLETE:
                    status = "Complete"
                case TaskCompletionStatus.PENDING:
                    status = "Pending"
                case TaskCompletionStatus.SCHEDULED:
                    status = "Scheduled"
            self.add_row(title, status, key=task[0].id)

    def create_columns(self):
        self.add_columns(
            "Title", "Status", "Date/Time"
        )


class NewTaskForm(Vertical):

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
        yield FormCouple("Title:", Input(id="new-task-title", placeholder="Short descriptor for your task."))
        yield FormCouple("Category:", Select(category_options, allow_blank=False, id="new-task-category"))
        yield FormCouple("Status:", Select(status_options, allow_blank=False, id="new-task-status"), optional=True)
        yield FormCouple("Scheduled:", DateInput(), optional=True, id="new-task-scheduled")
        with Horizontal(classes="form-end"):
            yield Button("Create task", id="submit")

    def on_select_changed(self, event):
        print(event.value)

    @on(Input.Submitted)
    @on(Button.Pressed, "#submit")
    def submit_form(self, event):
        print("Title: ", self.query_one("#new-task-title").value)
        print("Category: ", self.query_one("#new-task-category").value)
        status_elem = self.query_one("#new-task-status")
        if not status_elem.is_disabled:
            print("Status: ", status_elem.value)
        self.reset_form()

    def reset_form(self):
        for elem in self.query("Input"):
            elem.value = ""



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