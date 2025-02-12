import datetime, os

from enums import TaskCompletionStatus, TaskCategory

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy import String, Integer, Enum, ForeignKey, Date, Time
from sqlalchemy import Column, Table

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.exc import SQLAlchemyError

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
    # OPTIONAL
    description: Mapped[str | None] = mapped_column(String(), nullable=True)
    category: Mapped[TaskCategory | None] = mapped_column(Enum(TaskCategory), nullable=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("task_template.id"), nullable=True)
    year_scheduled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month_scheduled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_scheduled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_scheduled: Mapped[datetime.time | None] = mapped_column(Time, nullable=True)


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
def add_task(*, session, title,
             status=TaskCompletionStatus.PENDING,
             schedule_date=None,
             schedule_time=None,

             ):
    session.add(TaskInstance(
        title=title,
        status=status
    ))

def delete_task(*, session, id):
    task = session.get(TaskInstance, id)
    if not task:
        return False  # Task not found
    try:
        session.delete(task)
        session.commit()  # Ensure the delete is saved
        return True
    except SQLAlchemyError:
        session.rollback()  # Undo changes on failure
        return False

def get_task_instances(session):
    return session.execute(select(TaskInstance))
