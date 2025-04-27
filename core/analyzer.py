import json
from fastapi import HTTPException
from models.schemas import InputPayload, AnalysisResult
from services.openai_client import OpenAIClient


class OKRAnalyzer:
    @staticmethod
    def invoke(payload: InputPayload) -> AnalysisResult:
        # Build prompt
        prompt = [
            {"role": "system", "content": (
                "You are an analytics assistant. "
                "Given a table of daily tasks for team members and a list of team OKRs, "
                "produce two outputs:\n"
                "1) For each OKR, list which tasks each person completed that contribute to that OKR.\n"
                "2) For each OKR, identify potential risks and key deliverables.\n"
                "Respond in strictly JSON format with keys: tasks_by_kr, risks, deliverables."
            )},
            {"role": "user", "content": (
                f"Task table (list of days): {json.dumps([row.tasks for row in payload.task_table], indent=2)}\n"
                f"OKRs list: {json.dumps([okr.dict() for okr in payload.okrs], indent=2)}"
            )}
        ]

        try:
            content = OpenAIClient.chat(prompt)
            data = json.loads(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

        return AnalysisResult(
            tasks_by_kr=data.get("tasks_by_kr", {}),
            risks=data.get("risks", {}),
            deliverables=data.get("deliverables", {})
        )
