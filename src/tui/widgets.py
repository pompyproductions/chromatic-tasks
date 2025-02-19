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
        year = self.query_one("#date-year", expect_type=Input)
        if not year.is_valid:
            return date
        date["year"] = year.value
        month= self.query_one("#month-year", expect_type=Input)

        if not month.is_valid:
            pass

        # self.date["year"] = None
        # self.date["month"] = None
        # self.date["day"] = None
        # self.time["hour"] = None
        # self.time["mins"] = None
        text = "No date"
        year = self.query_one("#date-year", expect_type=Input)
        if year.is_valid:
            text = year.value
            self.date["year"] = int(year.value)
            month = self.query_one("#date-month", expect_type=Input)
            if month.is_valid:
                text = f"{self.month_to_word(month.value)} {year.value}"
                self.date["month"] = int(month.value)
                day = self.query_one("#date-day", expect_type=Input)
                if day.is_valid:
                    text = f"{self.month_to_word(month.value)} {day.value}, {year.value}"
                    self.date["day"] = int(day.value)
                    hour = self.query_one("#time-hour", expect_type=Input)
                    if hour.is_valid:
                        text = f"{self.month_to_word(month.value)} {day.value}, {year.value} | {hour.value}h00"
                        self.time["hour"] = int(hour.value)
                        self.time["mins"] = 0
                        minutes = self.query_one("#time-mins", expect_type=Input)
                        if minutes.is_valid:
                            text = f"{self.month_to_word(month.value)} {day.value}, {year.value} | {hour.value}h{minutes.value}"
                            self.time["mins"] = int(minutes.value)
        self.query_one("Label", expect_type=Label).update(text)

    def update_date(self):
        self.date["year"] = None
        self.date["month"] = None
        self.date["day"] = None
        self.time["hour"] = None
        self.time["mins"] = None
        text = "No date"
        year = self.query_one("#date-year", expect_type=Input)
        if year.is_valid:
            text = year.value
            self.date["year"] = int(year.value)
            month = self.query_one("#date-month", expect_type=Input)
            if month.is_valid:
                text = f"{self.month_to_word(month.value)} {year.value}"
                self.date["month"] = int(month.value)
                day = self.query_one("#date-day", expect_type=Input)
                if day.is_valid:
                    text = f"{self.month_to_word(month.value)} {day.value}, {year.value}"
                    self.date["day"] = int(day.value)
                    hour = self.query_one("#time-hour", expect_type=Input)
                    if hour.is_valid:
                        text = f"{self.month_to_word(month.value)} {day.value}, {year.value} | {hour.value}h00"
                        self.time["hour"] = int(hour.value)
                        self.time["mins"] = 0
                        minutes = self.query_one("#time-mins", expect_type=Input)
                        if minutes.is_valid:
                            text = f"{self.month_to_word(month.value)} {day.value}, {year.value} | {hour.value}h{minutes.value}"
                            self.time["mins"] = int(minutes.value)
        self.query_one("Label", expect_type=Label).update(text)

    def set_date(self, *, date: dict, time: dict):
        if date["year"]:
            self.query_one("#date-year", expect_type=Input).value = str(date["year"])

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
