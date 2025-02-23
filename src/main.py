import tui
import db

class Controller:

    def __init__(self, session):
        self.session = session

    def add_task(self, task_dict):
        return db.add_task(session=self.session, task_dict=task_dict)

    def get_all_tasks(self):
        return db.get_task_instances(self.session)

    def get_task(self, task_id):
        return db.get_task_instance(self.session, task_id=task_id)

    def delete_task(self, task_id):
        return db.delete_task(session=self.session, task_id=task_id)

    def edit_task(self, task_id, task_dict):
        return db.edit_task(session=self.session, task_id=task_id, task_dict=task_dict)

def main():
    db.create_tables()
    with db.DatabaseSession() as session:
        controller = Controller(session)
        app = tui.TasksApp(controller=controller)
        app.run()

if __name__ == '__main__':
    main()
