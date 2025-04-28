import json
import re


def extract_json_from_response(response_text: str) -> dict:
    """
    Extracts the JSON block from LLM response text (with ```json ... ```).
    Cleans and loads it into a Python dictionary.
    """
    # Use regex to find the first ```json ... ``` block
    match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON block found in response.")

    # Extract inside the code block
    json_text = match.group(1).strip()

    # Load as dict
    try:
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")
