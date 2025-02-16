from textual.validation import Validator, ValidationResult
from datetime import datetime


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