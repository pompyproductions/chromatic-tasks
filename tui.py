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
from datetime import datetime

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
    def validate(self, value: str) -> ValidationResult:
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
        self.month_input = None
        self.year_input = None

    def set_inputs(self, month_input, year_input):
        self.month_input = month_input
        self.year_input = year_input

    def validate(self, value: str) -> ValidationResult:
        try:
            day = int(value)
            month = int(self.month_input.value)
            year = int(self.year_input.value)
            if day < 1:
                return self.failure("Day can't be lower than 1.")
            elif day > 31:
                return self.failure("Day can't be higher than 31.")
            else:
                try:
                    datetime(year, month, day)
                    return self.success()
                except ValueError:
                    return self.failure("The specific date does not exist.")
        except ValueError:
            return self.failure("Couldn't convert to a number.")

class HourValidator(Validator):
    def validate(self, value) -> ValidationResult:
        try:
            hour = int(value)
            if hour < 0:
                return self.failure("Hour can't be negative")
            elif hour > 23:
                return self.failure("Hour can't be higher than 23")
            return self.success()
        except ValueError:
            return self.failure("Couldn't convert to number.")


class MinuteValidator(Validator):
    def validate(self, value) -> ValidationResult:
        try:
            mins = int(value)
            if mins < 0:
                return self.failure("Minutes can't be negative")
            elif mins > 59:
                return self.failure("Minutes can't be higher than 59")
            return self.success()
        except ValueError:
            return self.failure("Couldn't convert to number.")


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

    @staticmethod
    def month_to_word(month):
        try:
            return [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ][int(month) - 1]
        except ValueError:
            return "Invalid_Month"

    def update_date(self):
        self.date["year"] = None
        self.date["month"] = None
        self.date["day"] = None
        self.time["hour"] = None
        self.time["mins"] = None
        text = "No date"
        year = self.query_one("#date-year")
        if year.is_valid:
            text = year.value
            self.date["year"] = int(year.value)
            month = self.query_one("#date-month")
            if month.is_valid:
                text = f"{self.month_to_word(month.value)} {year.value}"
                self.date["month"] = int(month.value)
                day = self.query_one("#date-day")
                if day.is_valid:
                    text = f"{self.month_to_word(month.value)} {day.value}, {year.value}"
                    self.date["day"] = int(day.value)
                    hour = self.query_one("#time-hour")
                    if hour.is_valid:
                        text = f"{self.month_to_word(month.value)} {day.value}, {year.value} | {hour.value}h00"
                        self.time["hour"] = int(hour.value)
                        self.time["mins"] = 0
                        minutes = self.query_one("#time-mins")
                        if minutes.is_valid:
                            text = f"{self.month_to_word(month.value)} {day.value}, {year.value} | {hour.value}h{minutes.value}"
                            self.time["mins"] = int(minutes.value)
        self.query_one("Label").update(text)



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date = {
            "year": None,
            "month": None,
            "day": None
        }
        self.time = {
            "hour": None,
            "mins": None
        }
        self.date_validator = DateValidator()

    def compose(self) -> ComposeResult:
        yield Input(max_length=4, placeholder="YYYY", type="integer", classes="double", id="date-year", validators=[YearValidator()], validate_on=["changed"])
        yield Input(max_length=2, placeholder="MM", type="integer", id="date-month", validators=[MonthValidator()])
        yield Input(max_length=2, placeholder="DD", type="integer", id="date-day", validators=[self.date_validator])
        yield Input(max_length=2, placeholder="hh", type="integer", id="time-hour", validators=[HourValidator()])
        yield Input(max_length=2, placeholder="mm", type="integer", id="time-mins", validators=[MinuteValidator()])
        yield Label("No date")

    def on_mount(self):
        self.date_validator.set_inputs(
            month_input=self.query_one("#date-month"),
            year_input=self.query_one("#date-year")
        )
        for id in ["#date-year", "#date-month", "#date-day", "#time-hour", "#time-mins"]:
            elem = self.query_one(id)
            elem.validate(elem.value)

    @on(Input.Changed)
    def validate_inputs(self, event):
        month = self.query_one("#date-month")
        day = self.query_one("#date-day")
        hour = self.query_one("#time-hour")
        mins = self.query_one("#time-mins")

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
        self.update_date()

# ---
# Main views

class TasksTable(DataTable):

    BINDINGS = [
        ("backspace", "delete_entry()", "Delete Entry")
    ]
    class DeleteEntry(Message):
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

    def action_delete_entry(self):
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            self.post_message(self.DeleteEntry(row_key))
        except Exception:
            print("Failed.")
        # self.remove_row(row_key)
        # print(self.remove_row(self.cursor_row))

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
        yield FormCouple("Scheduled:", DateInput(id="new-task-scheduled"), optional=True)
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
        date_elem = self.query_one("#new-task-scheduled")
        if not date_elem.is_disabled:
            if date_elem.date["year"]:
                print("Year: ", date_elem.date["year"])
            if date_elem.date["month"]:
                print("Month: ", date_elem.date["month"])
            if date_elem.date["day"]:
                print("Day: ", date_elem.date["day"])
            if date_elem.time["hour"]:
                print("Hour: ", date_elem.time["hour"])
            if date_elem.time["mins"]:
                print("Mins: ", date_elem.time["mins"])
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

    @on(TasksTable.DeleteEntry)
    def delete_entry(self, message):
        if self.controller.delete_task(id=message.key.value):
            self.query_one(TasksTable).remove_row(message.key)
        # print(message.key.value)