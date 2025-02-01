from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, DataTable, \
    ContentSwitcher, ListView, ListItem, Button, Input, Select
from textual.containers import Horizontal, Vertical
from textual.message import Message
import db

# ---
# Composite widgets

# ---
# Main views

class NewTaskForm(Vertical):
    def compose(self):
        options = [
            ("Hello", 1),
            ("Hola", 2)
        ]
        with Horizontal(classes="form-couple"):
            yield Label("Title:", classes="input-label")
            yield Input()
        with Horizontal():
            yield Label("Category:", classes="input-label")
            yield Select(options)


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
                case db.CompletionStatus.COMPLETE:
                    status = "Complete"
                case db.CompletionStatus.PENDING:
                    status = "Pending"
                case db.CompletionStatus.SCHEDULED:
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
    #
    # def on_sidebar_switch_view(self, message: Sidebar.SwitchView):
    #     print(message.target)
    def on_list_view_highlighted(self, event):
        print(event.item.id)
        self.query_one(ContentSwitcher).current = event.item.id