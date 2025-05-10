# services/okr_analyzer.py
import json
from fastapi import HTTPException
from models.schemas import InputPayload, AnalysisResult
from services.db_tasks import get_unique_persons, get_person_tasks, save_scores_in_db, is_task_kr_person_exist
from services.openai_client import client as openai_client
from services.openai_client import OpenAIClient
from utils.excel_reader import load_okrs, load_okrs_with_objective, run_analysis_cli_with_description
from utils.extract_json_prompt import extract_json_from_response
from langchain_core.runnables import Runnable
import logging

logger = logging.getLogger(__name__)


def create_person_task_text(tasks_for_person, person):
    text = f" for *{person}* we have these tasks: ["
    for task in tasks_for_person:
        text = text + f"## task_id={task.id}, task={task.task} ##,"
    text = text + "]"
    text.replace(",]", "]")
    return text


def get_initial_tasks(task_text, okr_id, okr_description):
    # Build structured prompt focused on the single KR
    initial_prompt = [
        {"role": "system", "content": (
            "You are a task filtering assistant. Your job is to identify tasks with *any* potential connection to the specified Key Result using their database IDs.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Use ONLY task IDs in your response\n"
            "2. Include tasks showing even indirect connection to the KR\n"
            "3. Exclude tasks with no obvious relation\n"
            "4. For each ID, provide explicit reasoning\n"
            "5. Return tasks by ID in the exact JSON format\n\n"

            "ANALYSIS FRAMEWORK:\n"
            "For each task ID:\n"
            "1. Does the task relate to any KR component?\n"
            "2. Is there implicit/explicit connection to KR objectives?\n"
            "3. Could it contribute to KR success (directly or indirectly)?\n\n"

            "RESPONSE FORMAT (STRICTLY FOLLOW):\n"
            "{\n"
            "  \"kr_deconstruction\": [\"KR component 1\", \"KR component 2\", ...],\n"
            "  \"task_analysis\": {\n"
            "    \"147\": {\n"
            "      \"reason\": \"Explicitly relates to infrastructure setup (KR component 1)\",\n"
            "      \"relevance_score\": 90,\n"
            "      \"include\": true\n"
            "    },\n"
            "    \"152\": {\n"
            "      \"reason\": \"Meeting context unclear - could relate to KR planning\",\n"
            "      \"relevance_score\": 60,\n"
            "      \"include\": true\n"
            "    }\n"
            "  },\n"
            "  \"candidate_task_ids\": [147, 152]\n"
            "}\n\n"

            "DATABASE TASK CONTEXT:\n"
            "All tasks are stored with IDs in Persian format. Use only IDs in responses."
        )},
        {"role": "user", "content": (
            f"ID-to-Task Mapping:\n{task_text}\n\n"
            f"Target KR: {okr_id}\n"
            f"KR Description: {okr_description}\n\n"
            "INSTRUCTION:\n"
            "1. Deconstruct the KR into 3-5 components\n"
            "2. Analyze each task ID with reasoning\n"
            "3. Return candidate task IDs with:\n"
            "   - Chain-of-thought analysis\n"
            "   - Relevance score (0-100)\n"
            "   - Inclusion decision\n"
            "4. Final list must contain only IDs"
        )}
    ]

    unified_prompt = [
        {"role": "system", "content": (
            "You are an advanced task-KR mapping specialist. For each task ID, perform a complete analysis from deconstruction to scoring.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Use ONLY task IDs in your response\n"
            "2. Provide explicit reasoning for every score\n"
            "3. Return scores for ALL input tasks (even those with zero relevance)\n"
            "4. Score range: 0-100 (0 = completely unrelated, 100 = direct implementation)\n"
            "5. Include full task analysis with reasoning\n"
            "6. Never include text outside JSON structure\n\n"

            "ANALYSIS FRAMEWORK:\n"
            "1. **Deconstruct KR**: Identify 3-5 core components from the KR\n"
            "2. **Map Tasks**: For each task ID:\n"
            "   - Does it relate to any KR component?\n"
            "   - What's the nature of the connection (direct/indirect)?\n"
            "   - Is there explicit evidence of relevance?\n"
            "3. **Score Tasks**: Apply these criteria:\n"
            "   - 90-100: Direct implementation of KR requirements\n"
            "   - 70-89: Clear indirect contribution\n"
            "   - 50-69: Potential tangential relevance\n"
            "   - 0-49: No meaningful connection to KR\n\n"

            "RESPONSE FORMAT:\n"
            "{\n"
            "  \"kr_deconstruction\": [\"KR component 1\", \"KR component 2\"],\n"
            "  \"task_analysis\": {\n"
            "    \"147\": {\n"
            "      \"reason\": \"Explicitly relates to infrastructure setup (KR component 1)\",\n"
            "      \"relevance_score\": 95,\n"
            "      \"confidence\": 90,\n"
            "      \"include\": true\n"
            "    },\n"
            "    \"152\": {\n"
            "      \"reason\": \"Meeting context unclear - requires additional information\",\n"
            "      \"relevance_score\": 30,\n"
            "      \"confidence\": 40,\n"
            "      \"include\": false\n"
            "    }\n"
            "  },\n"
            "  \"all_task_scores\": [\n"
            "    {\"id\": 147, \"score\": 95, \"reason\": \"Direct implementation of infrastructure requirements\"},\n"
            "    {\"id\": 152, \"score\": 30, \"reason\": \"No clear connection to KR objectives\"}\n"
            "  ]\n"
            "}\n\n"
            "DATABASE TASK CONTEXT:\n"
            "All tasks are stored with IDs in Persian format. Use only IDs in responses."
        )},
        {"role": "user", "content": (
            f"ID-to-Task Mapping:\n{task_text}\n\n"
            f"Target KR: {okr_id}\n"
            f"KR Description: {okr_description}\n\n"
            "INSTRUCTION:\n"
            "1. Deconstruct KR into 3-5 components\n"
            "2. Analyze each task ID with reasoning for:\n"
            "   - Connection to KR components\n"
            "   - Evidence of relevance\n"
            "   - Implementation path\n"
            "3. Provide scores for ALL tasks (0-100) with:\n"
            "   - Detailed reasoning\n"
            "   - Confidence level (0-100)\n"
            "   - Inclusion decision\n"
            "4. Final list must contain scores for every task ID"
        )}
    ]
    tasks = {}
    i = 0
    while i < 4:
        try:
            content = OpenAIClient.chat(
                unified_prompt,
                temperature=0,  # Deterministic output
                seed=42  # Reproducibility
            )

            # Extract JSON from response using triple backticks
            data = extract_json_from_response(content)
            for task in data["all_task_scores"]:
                try:
                    tasks[task["id"]] += task["score"]
                except:
                    tasks[task["id"]] = task["score"]
            i += 1


        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    print(str(tasks))
    return tasks


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

    @staticmethod
    def invoke_for_single_kr_with_description(payload: InputPayload, kr_code: str) -> AnalysisResult:
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
                f"KR RELATION with GM OKR: {payload.okrs_text}"
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

    @staticmethod
    def invoke_for_single_kr_with_description_for_split_tasks_3step(db_dic):
        okr_xlsx = "assets/excel/SPM BI OKR 1404.xlsx"
        okr_list, _ = load_okrs_with_objective(okr_xlsx, "")
        persons = get_unique_persons(db_dic["session"], db_dic["Tasks"])
        for okr in okr_list:
            _, okr_str = load_okrs_with_objective(okr_xlsx, okr.id)
            for person in persons:
                print(okr.description, person)
                if is_task_kr_person_exist(db_dic["session"], db_dic["TaskScore"], okr.id, person):
                    continue
                print("checkpoint 1")
                tasks_for_person = get_person_tasks(db_dic["session"], db_dic["Tasks"], person)
                task_text = create_person_task_text(tasks_for_person, person)
                scored_tasks = get_initial_tasks(task_text, okr.id, okr.description)
                save_scores_in_db(scored_tasks, db_dic["session"], db_dic["TaskScore"], okr.id, person)


#defining a runnable class to invoke the analyzer
class OKRClassifier(Runnable):
    def __init__(self, payload: InputPayload):
        self.okrs = payload

    #Function for calling LLM and returning the result
    def __llm_analysis(self) -> AnalysisResult:
        # Define the function schema for OKR classification
        llm_tools = [
            {
                "type": "function",
                "function": {
                    "name": "classify_okrs",
                    "description": "Classify a list of OKRs based on Type, Scope, Automation Level, and Dependency, returning a JSON array.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "classified_okrs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "okr": {"type": "string", "description": "The original OKR text"},
                                        "type": {
                                            "type": "string",
                                            "enum": ["Outcome", "Follow-up", "Setup/Preparation",
                                                     "Exploration/Feasibility"],
                                            "description": "The type of OKR"
                                        },
                                        "scope": {
                                            "type": "string",
                                            "enum": ["Strategic", "Operational", "Technical"],
                                            "description": "The scope of the OKR"
                                        },
                                        "automation_level": {
                                            "type": "string",
                                            "enum": ["Manual", "Semi-Automated", "Fully Automated"],
                                            "description": "The automation level of the OKR"
                                        },
                                        "dependency": {
                                            "type": "string",
                                            "enum": ["Independent", "Dependent"],
                                            "description": "Whether the OKR depends on others"
                                        },
                                        "depends_on": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "List of OKR texts this OKR depends on (if Dependent)"
                                        }
                                    },
                                    "required": ["okr", "type", "scope", "automation_level", "dependency"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["classified_okrs"],
                        "additionalProperties": False
                    }
                }
            }
        ]
        system_prompt = """
            You are a system designed to classify Objectives and Key Results (OKRs) based on specific attributes and output the results in JSON format using the provided function schema. Follow these steps:

            1. **Input**: You will receive a list of OKRs as plain text. The OKRs are in Persian and must not be translated or modified.
            2. **Attributes**:
            - **Type**:
                - Outcome: OKRs delivering a measurable result (e.g., completing a profile).
                - Follow-up: OKRs tracking or monitoring progress (e.g., obtaining approvals).
                - Setup/Preparation: OKRs establishing infrastructure (e.g., acquiring hardware).
                - Exploration/Feasibility: OKRs researching possibilities (e.g., feasibility studies).
            - **Scope**:
                - Strategic: High-level, long-term goals (e.g., strategic indicators).
                - Operational: Day-to-day processes (e.g., updating dashboards).
                - Technical: Infrastructure or systems (e.g., setting up servers).
            - **Automation Level**:
                - Manual: Requires human intervention (e.g., approvals).
                - Semi-Automated: Partial automation (e.g., dashboards).
                - Fully Automated: Full automation (e.g., high-level AI automation).
            - **Dependency**:
                - Independent: Can be executed standalone.
                - Dependent: Requires other OKRs’ completion (list them in depends_on).
            3. **Process**:
            - Analyze each OKR’s text to classify its Type, Scope, Automation Level, and Dependency.
            - For Dependent OKRs, identify which OKRs they depend on based on context (e.g., dashboards depend on automated indicators).
            4. **Output**:
            - Use the classify_okrs function to return a JSON array of classified OKRs.
            - Ensure each OKR has: okr (original text), type, scope, automation_level, dependency, and depends_on (if Dependent).
            5. **Constraints**:
            - Do not translate or modify OKR text.
            - If classification is ambiguous, choose the most likely attribute and proceed.
            - Return all OKRs in the output.
            """

        # Prepare the user message with the OKR list
        user_message = "Classify the following OKRs:\n" + "\n".join(self.okrs)

        logger.info(f"User message: {user_message}")
        logger.info(f"System prompt: {system_prompt}")

        # Call the OpenAI API with function calling
        response = openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            tools=llm_tools,
            model='gpt-4o-mini',

        )
        tool_call = response.choices[0].message.tool_calls[0]
        classified_okrs = json.loads(tool_call.function.arguments)["classified_okrs"]
        return_response = json.dumps(classified_okrs, ensure_ascii=False, indent=3)

        #save the response to a file
        with open("assets/json/classified_okrs.json", "w", encoding="utf-8") as f:
            f.write(return_response)

        return return_response

    def invoke(self):
        classified_okrs = self.__llm_analysis()

        return classified_okrs

    def invoke_for_single_kr(self, kr_code: str) -> AnalysisResult:
        return OKRAnalyzer.invoke_for_single_kr(self.payload, kr_code)
