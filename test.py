from core.analyzer import OKRAnalyzer
from models.ps_sql_schema import get_task_db

db_dic = get_task_db()
OKRAnalyzer.invoke_for_single_kr_with_description_for_split_tasks_3step(db_dic)