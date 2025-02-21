from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Checkbox, Label, Input

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
        self.date = self.parse_date()
        self.query_one("Label", expect_type=Label).update(
            DateInput.date_to_str(self.date)
        )

    def populate_inputs(self, *, date: dict, time: dict):
        if not date["year"]:
            return
        self.disabled = False
        self.query_one("#date-year", expect_type=Input).value = str(date["year"])
        for date_part in ["year", "month", "day"]:
            if not date[date_part]:
                return
            self.query_one(f"#date-{date_part}", expect_type=Input).value = str(date[date_part])
        for time_part in ["hour", "mins"]:
            if not time[time_part]:
                return
            self.query_one(f"#time-{time_part}", expect_type=Input).value = str(time[time_part])

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
