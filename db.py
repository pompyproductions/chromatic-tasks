import datetime, os
from enums import TaskCompletionStatus, TaskCategory

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy import String, Integer, Enum, ForeignKey, Date, Time
from sqlalchemy import Column, Table

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    status: Mapped[CompletionStatus] = mapped_column(Enum(CompletionStatus))
    # OPTIONAL
    description: Mapped[str | None] = mapped_column(String(), nullable=True)
    category: Mapped[TaskCategory | None] = mapped_column(Enum(TaskCategory), nullable=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("task_template.id"), nullable=True)
    date_scheduled: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    hour_scheduled: Mapped[datetime.time | None] = mapped_column(Time, nullable=True)


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
             status=CompletionStatus.PENDING,
             schedule_date=None,
             schedule_time=None,

             ):
    session.add(TaskInstance(
        title=title,
        status=status
    ))


def get_task_instances(session):
    return session.execute(select(TaskInstance))
