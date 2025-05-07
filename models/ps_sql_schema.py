from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


def get_task_db():
    DATABASE_URI = 'postgresql+psycopg2://postgres:ario.1377@localhost:5432/okr_tasks'
    engine = create_engine(DATABASE_URI)

    Base = declarative_base()

    class Tasks(Base):
        __tablename__ = 'tasks'
        id = Column(Integer, primary_key=True)
        day = Column(String(10), nullable=False)  # ✅ Save as string (e.g., "14040206")
        person = Column(String(50), nullable=False)
        task = Column(Text, nullable=False)

    class TaskScore(Base):
        __tablename__ = 'task_scores'

        id = Column(Integer, primary_key=True)  # Auto-increment ID
        task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)  # Foreign key to tasks table
        kr_code = Column(String(50), nullable=False)  # KR identifier (e.g., K-B2B-048)
        score = Column(Integer, nullable=False)  # 0-100 relevance score
        person = Column(String(50), nullable=False)

    # Create table if not exists
    inspector = inspect(engine)
    if not inspector.has_table('tasks'):
        Base.metadata.create_all(engine)
        print("Table 'tasks' created.")
    else:
        print("Table 'tasks' already exists.")
    if not inspector.has_table('task_scores'):
        Base.metadata.create_all(engine)
        print("Table 'task_scores' created.")
    else:
        print("Table 'task_scores' already exists.")

    Session = sessionmaker(bind=engine)
    session = Session()
    return {"session": session,
            "Tasks": Tasks,
            "Base": Base,
            "TaskScore": TaskScore}
