import pandas as pd
from typing import List
from models.schemas import TaskRow, OKR, InputPayload


def run_analysis_cli(task_xlsx="assets/excel/team tasks spreadsheet.xlsx", okr_xlsx="assets/excel/okr.xlsx"):
    # load from Excel
    task_rows = load_task_table(task_xlsx)
    okr_list = load_okrs(okr_xlsx)
    payload = InputPayload(task_table=task_rows, okrs=okr_list)
    return payload


# utils/excel_reader.py


def load_task_table(path: str) -> List[TaskRow]:
    """
    Reads an Excel file where each row is one work‐day and columns are:
      date, day, <person1>, <person2>, ...
    Returns a list of TaskRow, each with .tasks mapping person->task_str.
    """
    df = pd.read_excel(path, engine="openpyxl")
    # assume first two cols are metadata
    task_cols = [c for c in df.columns if c not in ("date", "day")]
    rows: List[TaskRow] = []
    for _, r in df.iterrows():
        tasks = {}
        for col in task_cols:
            val = r[col]
            if pd.notna(val):
                # preserve multiline strings
                tasks[col] = str(val).strip()
        rows.append(TaskRow(tasks=tasks))
    return rows


def load_okrs(path: str) -> List[OKR]:
    """
    Reads an Excel file where the first column holds each Key Result.
    Auto‐assigns IDs KR1, KR2, … in order of appearance.
    """
    df = pd.read_excel(path, engine="openpyxl")
    kr_col = df.columns[0]
    okrs: List[OKR] = []
    for idx, val in enumerate(df[kr_col].dropna(), start=1):
        okrs.append(OKR(id=f"KR{idx}", description=str(val).strip()))
    return okrs
