from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import Length
from textual.widgets import Checkbox, Label, Input, Select, Button
from textual.message import Message

from enums import FormType, TaskCompletionStatus, TaskCategory
from .validators import YearValidator, MonthValidator, DateValidator, HourValidator, MinuteValidator


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

    @staticmethod
    def date_to_str(date):
        if not date["year"]:
            return "No date"
        part_year = str(date["year"])
        part_month = ""
        if date["month"]:
            part_month = DateInput.month_to_word(date["month"]) + " "
        part_day = ""
        if date["day"]:
            part_day = str(date["day"]) + ", "

        text = part_month + part_day + part_year
        if date["hour"]:
            text += f" | {date["hour"]}h{'%02d' % (date["mins"],) if date["mins"] else '00'}"
        return text


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_dict = {
            "year": None,
            "month": None,
            "day": None,
            "hour": None,
            "mins": None
        }
        self.date_validator = DateValidator()

    def compose(self) -> ComposeResult:
        yield Input(
            max_length=4, placeholder="YYYY", type="integer",
            classes="double", id="date-year",
            validators=[YearValidator()], validate_on=["changed"]
        )
        yield Input(
            max_length=2, placeholder="MM", type="integer",
            id="date-month",
            validators=[MonthValidator()], validate_on=["changed"])
        yield Input(
            max_length=2, placeholder="DD", type="integer",
            id="date-day",
            validators=[self.date_validator], validate_on=["changed"])
        yield Input(
            max_length=2, placeholder="hh", type="integer",
            id="time-hour",
            validators=[HourValidator()], validate_on=["changed"])
        yield Input(
            max_length=2, placeholder="mm", type="integer",
            id="time-mins",
            validators=[MinuteValidator()], validate_on=["changed"])
        yield Label("No date")

    def on_mount(self):
        self.date_validator.set_inputs(
            month_input=self.query_one("#date-month"),
            year_input=self.query_one("#date-year")
        )
        for widget_id in ["#date-year", "#date-month", "#date-day", "#time-hour", "#time-mins"]:
            elem = self.query_one(widget_id, expect_type=Input)
            elem.validate(elem.value)

    def parse_date(self) -> dict:
        date : dict[str, None | int] = {
            "year": None,
            "month": None,
            "day": None,
            "hour": None,
            "mins": None
        }
        for date_part in ["year", "month", "day"]:
            input_elem = self.query_one("#date-" + date_part, expect_type=Input)
            if not input_elem.is_valid:
                return date
            date[date_part] = int(input_elem.value)
        for time_part in ["hour", "mins"]:
            input_elem = self.query_one("#time-" + time_part, expect_type=Input)
            if not input_elem.is_valid:
                return date
            date[time_part] = int(input_elem.value)
        return date

    def update_date(self):
        self.date_dict = self.parse_date()
        self.query_one("Label", expect_type=Label).update(
            DateInput.date_to_str(self.date_dict)
        )

    def populate_inputs(self, date: dict):
        if not date["year"]:
            return
        self.disabled = False
        self.query_one("#date-year", expect_type=Input).value = str(date["year"])
        for key in ["year", "month", "day"]:
            if not date[key]:
                return
            self.query_one(f"#date-{key}", expect_type=Input).value = str(date[key])
        for key in ["hour", "mins"]:
            if not date[key]:
                return
            self.query_one(f"#time-{key}", expect_type=Input).value = str(date[key])

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

class TaskForm(Vertical):
    class SubmitForm(Message):
        def __init__(self, task_dict):
            super().__init__()
            self.task_dict = task_dict
    class Close(Message):
        def __init__(self):
            super().__init__()

    def __init__(self, form_type:FormType, *, task_dict:dict|None=None):
        super().__init__()
        self.form_type = form_type
        self.category_options = [
            ("Home", TaskCategory.HOME),
            ("Work", TaskCategory.WORK),
            ("Social", TaskCategory.SOCIAL)
        ]
        self.status_options = [
            ("Completed", TaskCompletionStatus.COMPLETE),
            ("Archived", TaskCompletionStatus.ARCHIVED),
            ("Cancelled", TaskCompletionStatus.CANCELLED)
        ]
        self.task_dict = task_dict
        match form_type:
            case FormType.NEW_TASK:
                self.form_name = "new-task"
            case FormType.EDIT_TASK:
                self.form_name = "edit-task"
                self.status_options.append(("Pending", TaskCompletionStatus.PENDING))

    def reset_form(self):
        for elem in self.query(Input):
            elem.value = ""
        self.query_one(f"#{self.form_name}-scheduled").parent.disabled = True
        self.query_one(f"#{self.form_name}-status").parent.disabled = True

    def populate_form(self, task_dict:dict):
        # Required values
        self.query_one(f"#{self.form_name}-title", expect_type=Input).value = task_dict["title"]
        self.query_one(f"#{self.form_name}-status", expect_type=Select).value = task_dict["status"]
        self.query_one(f"#{self.form_name}-category", expect_type=Select).value = task_dict["category"]
        # Optional values
        if task_dict["date"]:
            self.query_one(DateInput).populate_inputs(task_dict["date"])

    def compose(self):
        is_status_optional = True
        submit_label = "Create task"
        if self.form_type == FormType.EDIT_TASK:
            is_status_optional = False
            submit_label = "Edit task"
        yield FormCouple("Title:", Input(
            id=f"{self.form_name}-title",
            placeholder="Short descriptor for your task.",
            validators=[Length(minimum=1)],
            valid_empty=False,
            validate_on=["changed"]
        ))
        yield FormCouple("Category:", Select(
            self.category_options,
            allow_blank=False,
            id=f"{self.form_name}-category"
        ))
        yield FormCouple("Status:", Select(
            self.status_options,
            allow_blank=False,
            id=f"{self.form_name}-status"
        ), optional=is_status_optional)
        yield FormCouple("Scheduled:", DateInput(
            id=f"{self.form_name}-scheduled"
        ), optional=True)
        with Horizontal(classes="form-end"):
            yield Button("Cancel", id="cancel")
            yield Button(submit_label, id="submit")

    def on_mount(self):
        elem = self.query_one(f"#{self.form_name}-title", expect_type=Input)
        elem.validate(elem.value)
        if self.form_type == FormType.EDIT_TASK:
            self.populate_form(self.task_dict)

    @on(Input.Submitted)
    @on(Button.Pressed, "#submit")
    def submit_form(self):
        title_input = self.query_one(f"#{self.form_name}-title", expect_type=Input)
        if not title_input.is_valid:
            print("Title not valid.")
            return
        task_dict = {
            "title": title_input.value,
            "category": self.query_one(f"#{self.form_name}-category", expect_type=Select).value,
            "status": TaskCompletionStatus.PENDING
        }
        status_input = self.query_one(f"#{self.form_name}-status", expect_type=Select)
        if not status_input.is_disabled:
            task_dict["status"] = status_input.value
        date_input = self.query_one(f"#{self.form_name}-scheduled", expect_type=DateInput)
        if not date_input.is_disabled:
            task_dict["date"] = date_input.parse_date()
            if task_dict["date"]["year"] and task_dict["status"] == TaskCompletionStatus.PENDING:
                task_dict["status"] = TaskCompletionStatus.SCHEDULED
        else:
            task_dict["date"] = {
                "year": None,
                "month": None,
                "day": None,
                "hour": None,
                "mins": None
            }

        self.post_message(self.SubmitForm(task_dict))
