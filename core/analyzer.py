# services/okr_analyzer.py
import json
from fastapi import HTTPException
from models.schemas import InputPayload, AnalysisResult
from services.openai_client import OpenAIClient
from utils.extract_json_prompt import extract_json_from_response


class OKRAnalyzer:
    @staticmethod
    def invoke(payload: InputPayload) -> AnalysisResult:
        # Build structured prompt with Chain-of-Thought
        prompt = [
            {"role": "system", "content": (
                "You are an analytics assistant tasked with mapping daily tasks to OKRs.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. First, perform a detailed Chain-of-Thought analysis internally\n"
                "2. Use the exact JSON schema provided below\n"
                "3. Never include any text outside the JSON structure\n"
                "4. Always use the same KR-to-task mapping logic\n\n"

                "ANALYSIS STEPS:\n"
                "1. For each task, identify its purpose and technical intent\n"
                "2. Match tasks to KRs based on verbs and objectives\n"
                "3. Group risks by common themes\n"
                "4. Derive deliverables from task outcomes\n\n"

                "EXAMPLE COMPLETION (partial):\n"
                "{\n"
                "  \"tasks_by_kr\": {\n"
                "    \"KR1\": {\n"
                "      \"rezazadeh\": [\"1- پیگیری تیکت های...\", \"2- جلسه با تیم امنیت\"]\n"
                "    }\n"
                "  },\n"
                "  \"risks\": {\n"
                "    \"KR1\": [\"عدم دسترسی به سرورها\", \"تاخیر در راه اندازی سیستم جدید\"],\n"
                "    \"KR2\": [\"عدم هماهنگی بین تیم‌ها\", \"مشکلات فنی در ETL\"],\n"
                "    ...\n"
                "  },\n"
                "  \"deliverables\": {\n"
                "    \"KR1\": [\"گزارش وضعیت سرورهای جدید\", \"روند کاری استاندارد امنیتی\"],\n"
                "    ...\n"
                "  }\n"
                "}\n\n"
        
                

                "ADDITIONAL RULES:\n"
                "- Maintain consistent person names as given\n"
                "- Use Persian tasks as-is without translation\n"
                "- Preserve exact KR identifiers from input\n"
                "- Prioritize precision over completeness\n"
                "- Never invent new KRs or tasks"
            )},
            {"role": "user", "content": (
                f"Task table (list of days): {json.dumps([row.tasks for row in payload.task_table], indent=2)}\n"
                f"OKRs list: {json.dumps([okr.dict() for okr in payload.okrs], indent=2)}"
            )}
        ]

        try:
            content = OpenAIClient.chat(
                prompt,
                temperature=0,  # Deterministic output
                seed=42  # Reproducibility
            )

            print(40 * "#" + "\n" + content + "\n" + 40 * "#")

            # Extract JSON from response using triple backticks
            data = extract_json_from_response(content)

            # Validate required keys exist
            for key in ["tasks_by_kr", "risks", "deliverables"]:
                if key not in data:
                    raise ValueError(f"Missing required key '{key}' in response")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

        return AnalysisResult(
            tasks_by_kr=data.get("tasks_by_kr", {}),
            risks=data.get("risks", {}),
            deliverables=data.get("deliverables", {})
        )

    @staticmethod
    def invoke_for_single_kr(payload: InputPayload, kr_code: str) -> AnalysisResult:
        # Build structured prompt focused on the single KR
        prompt = [
            {"role": "system", "content": (
                f"You are an analytics assistant tasked with mapping daily tasks to a specific Key Result ({kr_code}).\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. Focus ONLY on tasks related to the provided KR\n"
                "2. Use the exact JSON schema with the same keys\n"
                "3. Never include any text outside the JSON structure\n"
                "4. Prioritize precision over completeness\n"
                "5. Only return data for the specified KR\n\n"

                "ANALYSIS STEPS:\n"
                "1. For each task, determine its relevance to the KR's objectives\n"
                "2. Identify risks directly impacting KR achievement\n"
                "3. Derive deliverables from completed/documented tasks\n\n"

                "EXAMPLE COMPLETION (partial):\n"
                "{\n"
                f"  \"tasks_by_kr\": {{\n"
                f"    \"{kr_code}\": {{\n"
                "      \"rezazadeh\": [\"1- پیگیری تیکت های...\", \"2- جلسه با تیم امنیت\"],\n"
                "      \"kakoolvand\": [\"1- پیگیری تیکت های...\", \"2- جلسه با تیم امنیت\"],\n"
                "       ..."
                "    }\n"
                "  },\n"
                f"  \"risks\": {{\n"
                f"    \"{kr_code}\": [\"عدم دسترسی به سرورها\", \"تاخیر در راه اندازی سیستم جدید\"]\n"
                "  },\n"
                f"  \"deliverables\": {{\n"
                f"    \"{kr_code}\": [\"گزارش وضعیت سرورهای جدید\", \"روند کاری استاندارد امنیتی\"]\n"
                "  }\n"
                "}\n\n"

                "ADDITIONAL RULES:\n"
                "- Maintain consistent person names as given\n"
                "- Use Persian tasks as-is without translation\n"
                "- Preserve exact KR identifiers from input\n"
                "- Return empty arrays if no matches found\n"
            )},
            {"role": "user", "content": (
                f"Task table (list of days): {json.dumps([row.tasks for row in payload.task_table], indent=2)}\n"
                f"Target KR: {json.dumps([okr.dict() for okr in payload.okrs], indent=2)}"
            )}
        ]

        try:
            content = OpenAIClient.chat(
                prompt,
                temperature=0,  # Deterministic output
                seed=42  # Reproducibility
            )

            print(40 * "#" + "\n" + content + "\n" + 40 * "#")

            # Extract JSON from response using triple backticks
            data = extract_json_from_response(content)

            # Validate required keys exist
            for key in ["tasks_by_kr", "risks", "deliverables"]:
                if key not in data:
                    raise ValueError(f"Missing required key '{key}' in response")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

        # Ensure only the requested KR appears in the output
        return AnalysisResult(
            tasks_by_kr={kr_code: data.get("tasks_by_kr", {}).get(kr_code, {})},
            risks={kr_code: data.get("risks", {}).get(kr_code, [])},
            deliverables={kr_code: data.get("deliverables", {}).get(kr_code, [])}
        )