import tui
import db
from enums import TaskCompletionStatus, TaskCategory

class Controller:
    def __init__(self, session):
        self.session = session

    def add_task(self, *, title, status=TaskCompletionStatus.PENDING):
        db.add_task(session=self.session, title=title, status=status)

    def get_all_tasks(self):
        return db.get_task_instances(self.session)

def main():
    db.create_tables()
    with db.DatabaseSession() as session:
        controller = Controller(session)
        # controller.add_task(title="Completed task", status=TaskCompletionStatus.COMPLETE)
        app = tui.TasksApp(controller=controller)
        app.run()

if __name__ == '__main__':
    main()
