from sqlalchemy import create_engine, Table, MetaData
from datetime import datetime


# Convert Persian date string (e.g., '14040206') to Python date
def parse_persian_date(date_str):
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    return datetime(year=year, month=month, day=day).date()


# Example input
day_str = "14040206"  # Persian date
day = parse_persian_date(day_str)

tasks_json = {
    "rezazadeh": ["پیگیری تیکت‌های مربوط به سرورهای جدید", "پیگیری تیکت مربوط به تایید امنیت..."],
    "mamdoohi": ["ایجاد Stored Procedure برای گزارش اقدامات", "وارد کردن داده‌های Roaming..."],
    # ... other people and tasks
}

# Connect to PostgreSQL
engine = create_engine("postgresql://user:password@localhost/dbname")
metadata = MetaData(bind=engine)
connection = engine.connect()

# Reflect the table
tasks_table = Table('tasks', metadata, autoload_with=engine)

# Insert tasks
for person, tasks in tasks_json.items():
    for task in tasks:
        stmt = tasks_table.insert().values(
            day=str(day),
            person=person,
            task=task
        )
        connection.execute(stmt)

connection.commit()
connection.close()