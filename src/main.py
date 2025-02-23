import tui
import db
from db import TaskInstance


class Controller:

    def __init__(self, session):
        self.session = session

    def add_task(self, *, task_dict:dict) -> TaskInstance:
        return db.add_task(session=self.session, task_dict=task_dict)

    def get_all_tasks(self) -> TaskInstance:
        return db.get_task_instances(self.session)

    def get_task(self, *, row_id:int) -> TaskInstance:
        return db.get_task_instance(self.session, row_id=row_id)

    def delete_task(self, *, row_id:int) -> bool:
        return db.delete_task(session=self.session, row_id=row_id)

    def edit_task(self, *, row_id:int, task_dict:dict) -> TaskInstance:
        return db.edit_task(session=self.session, row_id=row_id, task_dict=task_dict)

def main():
    db.create_tables()
    with db.DatabaseSession() as session:
        controller = Controller(session)
        app = tui.TasksApp(controller=controller)
        app.run()

if __name__ == '__main__':
    main()
