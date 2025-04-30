import pandas as pd
from typing import List
from models.schemas import TaskRow, OKR, InputPayload


def run_analysis_cli(task_xlsx="assets/excel/team tasks spreadsheet.xlsx", okr_xlsx="assets/excel/okr.xlsx"):
    # load from Excel
    task_rows = load_task_table(task_xlsx)
    okr_list = load_okrs(okr_xlsx)
    print("files loaded")
    print(task_rows)
    print(okr_list)
    payload = InputPayload(task_table=task_rows, okrs=okr_list)
    print("payload returned")
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

    # Handle missing values
    df["Key Results"] = df["Key Results"].fillna("")

    # Vectorized operation (faster than iterrows)
    okrs = [
        OKR(id=str(row["KR_code"]).strip(), description=str(row["Key Results"]).strip())
        for _, row in df.iterrows()
    ]
    return okrs
