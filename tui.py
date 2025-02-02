from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, DataTable, \
    ContentSwitcher, ListView, ListItem, Button, Input, Select, \
    Switch, Checkbox
from textual.containers import Horizontal, Vertical
from textual.message import Message
import db
from enums import TaskCompletionStatus, TaskCategory

# ---
# Composite widgets

class FormCouple(Horizontal):
    def __init__(self, label, input_widget, *args, optional=False, **kwargs):
        self.optional = optional
        self.label = label
        self.input_widget = input_widget
        input_widget.add_class("input-widget")
        super().__init__(*args, **kwargs)
        # no need for this, CSS can target base classes:
        # self.add_class("form-couple")

    def compose(self) -> ComposeResult:
        if self.optional:
            self.input_widget.disabled = True
            yield Checkbox(self.label, classes="input-label optional")
        else:
            yield Label(self.label, classes="input-label")
        yield self.input_widget

    def on_checkbox_changed(self, event):
        self.query_one(".input-widget").disabled = not event.value
        # print(event.value)

# ---
# Main views

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
        yield FormCouple("Title:", Input(id="new-task-title"))
        yield FormCouple("Category:", Select(category_options, allow_blank=False, id="new-task-category"))
        yield FormCouple("Status:", Select(status_options, allow_blank=False, id="new-task-status"), optional=True)
        with Horizontal(classes="form-end"):
            yield Button("Create task", id="submit")

    def on_select_changed(self, event):
        print(event.value)

    def on_button_pressed(self, event):
        print(self.query_one("#new-task-title").value)
        print(self.query_one("#new-task-category").value)
        status_elem = self.query_one("#new-task-status")
        if not status_elem.is_disabled:
            print(status_elem.value)


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

    CSS_PATH = "style.tcss"
    # BINDINGS = [
    #     ("a", "prev", "Previous"),
    #     ("d", "next", "Next"),
    # ]

    def create_columns(self, table):
        table.add_columns(
            "Title", "Status", "Date/Time"
        )

    def populate_table(self, table):
        tasks = self.controller.get_all_tasks()
        for task in tasks:
            title = task[0].title
            status = task[0].status
            match status:
                case TaskCompletionStatus.COMPLETE:
                    status = "Complete"
                case TaskCompletionStatus.PENDING:
                    status = "Pending"
                case TaskCompletionStatus.SCHEDULED:
                    status = "Scheduled"
            table.add_row(title, status, key=task[0].id)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar()
            with ContentSwitcher(initial="data-table"):
                yield DataTable(id="data-table")
                yield NewTaskForm(id="create-task", classes="form")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        DataTable.cursor_type = "row"
        self.create_columns(table)
        self.populate_table(table)

    def on_list_view_highlighted(self, event):
        print(event.item.id)
        self.query_one(ContentSwitcher).current = event.item.id