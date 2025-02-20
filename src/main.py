import tui
import db

class Controller:

    def __init__(self, session):
        self.session = session

    def add_task(self, *, task):
        return db.add_task(session=self.session, task=task)

    def get_all_tasks(self):
        return db.get_task_instances(self.session)

    def get_task(self, id):
        return db.get_task_instance(self.session, id=id)

    def delete_task(self, *, id):
        return db.delete_task(session=self.session, id=id)

def main():
    db.create_tables()
    with db.DatabaseSession() as session:
        controller = Controller(session)
        app = tui.TasksApp(controller=controller)
        app.run()

if __name__ == '__main__':
    main()
