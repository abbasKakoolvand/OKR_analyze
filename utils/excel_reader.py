import pandas as pd
from typing import List
from models.schemas import TaskRow, OKR, InputPayload, InputPayload_with_description


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


def run_analysis_cli_with_description(kr_code="", task_xlsx="assets/excel/team tasks spreadsheet.xlsx",
                                      okr_xlsx="assets/excel/SPM BI OKR 1404.xlsx"):
    # load from Excel
    task_rows = load_task_table(task_xlsx)
    okr_list, okr_text = load_okrs_with_objective(okr_xlsx, kr_code)

    print("files loaded")
    print(task_rows)
    print(okr_list)
    payload = InputPayload_with_description(task_table=task_rows, okrs=okr_list, okrs_text=okr_text)
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


def load_okrs_with_objective(path: str, okr_code: str):
    """
    Reads an Excel file where the first column holds each Key Result.
    Auto‐assigns IDs KR1, KR2, … in order of appearance.
    """
    import pandas as pd
    # 1. Read & filter
    df = pd.read_excel(
        path,
        sheet_name='SPMBI OKR 1404Q1-python'
    )
    filtered = df[df['SPM BI Key Results (نتایج کلیدی)'].notna() & df['SPM BI Key Results (نتایج کلیدی)'].astype(
        str).str.strip().ne('')]
    filtered = filtered[filtered['SPMBIKR-CODE'] == okr_code]
    print(f"filtered {okr_code}:", )
    flag_description = True  # toggle whether to include the description field
    # 2. Build the text
    lines = []
    for obj, obj_df in filtered.groupby('Objective (هدف)'):
        kr_lines = []
        for gm_kr, kr_df in obj_df.groupby('SPM Key Results (نتایج کلیدی)'):
            # collect all the BI‐level KRs under this GM KR
            items = []
            for _, row in kr_df.iterrows():
                bi_kr = row['SPM BI Key Results (نتایج کلیدی)']
                if flag_description:
                    desc = row['Descriptin (توضیحات)']
                    items.append(f"**KR: {bi_kr}, KR_Description: {desc}**")
                else:
                    items.append(f"**KR: {bi_kr}**")
            kr_list = ", ".join(items)
            kr_lines.append(f"###for GM KR *{gm_kr}* we have these team KRs:[{kr_list}]###")
        # join all the GM KR blocks under this Objective
        joined_kr_blocks = " ".join(kr_lines)
        lines.append(f"for GM Objective *{obj}* we have these GM KRs:[{joined_kr_blocks}]")
    # 3. Final output
    okr_text = "\n\n".join(lines)
    print(okr_text)

    okrs = [
        OKR(id=str(row["SPMBIKR-CODE"]).strip(), description=str(row["SPM BI Key Results (نتایج کلیدی)"]).strip())
        for _, row in filtered.iterrows()
    ]
    return okrs, okr_text
