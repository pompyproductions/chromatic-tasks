from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.validation import Validator, ValidationResult, Number

class TestApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme = "gruvbox"
    def compose(self) -> ComposeResult:
        yield Input(validators=[YearValidator()], validate_on=["changed"])

def main():
    app = TestApp()
    app.run()

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

if __name__ == '__main__':
    main()