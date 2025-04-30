from typing import List, Dict
from pydantic import BaseModel


class TaskRow(BaseModel):
    tasks: Dict[str, str]  # person -> task description for a day


class OKR(BaseModel):
    id: str
    description: str


class InputPayload(BaseModel):
    task_table: List[TaskRow]
    okrs: List[OKR]


class AnalysisResult(BaseModel):
    tasks_by_kr: Dict[str, Dict[str, List[str]]]
    risks: Dict[str, List[str]]
    deliverables: Dict[str, List[str]]

