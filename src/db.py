import datetime, os

from enums import TaskCompletionStatus, TaskCategory

from sqlalchemy import create_engine
from sqlalchemy import select, inspect
from sqlalchemy import String, Integer, Enum, ForeignKey, Time
from sqlalchemy import Column, Table

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.exc import SQLAlchemyError
from datetime import time

DATABASE_URL = os.getenv("CHROMATIC_TASK_DATABASE_URL", "sqlite:///default.db")
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(engine)


# ---
# BASE CLASSES
class Base(DeclarativeBase):
    pass


# ---
# TABLES
class TaskInstance(Base):
    __tablename__ = "task_instance"
    # REQUIRED
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    status: Mapped[TaskCompletionStatus] = mapped_column(Enum(TaskCompletionStatus))
    category: Mapped[TaskCategory] = mapped_column(Enum(TaskCategory))
    # OPTIONAL
    description: Mapped[str | None] = mapped_column(String(), nullable=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("task_template.id"), nullable=True)
    year_scheduled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month_scheduled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_scheduled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_scheduled: Mapped[datetime.time | None] = mapped_column(Time, nullable=True)

    def to_dict(self) -> dict:
        task_dict = {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "category": self.category
        }
        for key in ["description", "template_id"]:
            if getattr(self, key):
                task_dict[key] = getattr(self, key)
        date_dict = {
            "year": self.year_scheduled,
            "month": self.month_scheduled,
            "day": self.day_scheduled,
            "hour": None,
            "mins": None
        }
        if self.time_scheduled:
            date_dict["hour"] = self.time_scheduled.hour
            date_dict["mins"] = self.time_scheduled.minute
        task_dict["date"] = date_dict
        return task_dict

    def set_date(self, date_dict):
        self.year_scheduled = date_dict["year"]
        self.month_scheduled = date_dict["month"]
        self.day_scheduled = date_dict["day"]
        if date_dict["hour"]:
            if date_dict["mins"]:
                self.time_scheduled = datetime.time(date_dict["hour"], date_dict["mins"])
            else:
                self.time_scheduled = datetime.time(date_dict["hour"])


class TaskTemplate(Base):
    __tablename__ = "task_template"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(), nullable=True)
    category: Mapped[TaskCategory | None] = mapped_column(Enum(TaskCategory), nullable=True)


class DatabaseSession:
    def __enter__(self) -> Session:
        self.session = Session()
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


def create_tables():
    Base.metadata.create_all(engine)


def get_session():
    with Session() as session:
        yield session


# ---
# CRUD

def add_task(*, session, task_dict:dict):
    entry = TaskInstance(
        title=task_dict["title"],
        status=task_dict["status"],
        category=task_dict["category"],
        # description=task.description,
    )
    if task_dict["date"]:
        entry.set_date(task_dict["date"])
    try:
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry
    except SQLAlchemyError:
        return None

def edit_task(*, session, row_id:int, task_dict:dict):
    task_instance = session.get(TaskInstance, row_id)
    if not task_instance:
        return False
    try:
        for key, value in task_dict.items():
            if key == "date":
                setattr(task_instance, "year_scheduled", value["year"])
                setattr(task_instance, "month_scheduled", value["month"])
                setattr(task_instance, "day_scheduled", value["day"])
                if value["hour"]:
                    if value["mins"]:
                        setattr(task_instance, "time_scheduled", time(hour=value["hour"], minute=value["mins"]))
                    else:
                        setattr(task_instance, "time_scheduled", time(hour=value["hour"]))
            else:
                setattr(task_instance, key, value)
        session.commit()
        return task_instance

    except SQLAlchemyError:
        session.rollback()
        return False

def delete_task(*, session, row_id:int):
    task_instance = session.get(TaskInstance, row_id)
    if not task_instance:
        return False
    try:
        session.delete(task_instance)
        session.commit()
        return True
    except SQLAlchemyError:
        session.rollback()
        return False

def get_task_instances(session):
    return session.execute(select(TaskInstance))

def get_task_instance(session, row_id:int):
    return session.execute(
        select(TaskInstance).where(TaskInstance.id == row_id)
    ).scalar()