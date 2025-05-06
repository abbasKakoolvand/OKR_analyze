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
        start_index = response_text.find('{')
        end_index = response_text.rfind('}')

        # Check if both indices are valid
        if start_index != -1 and end_index != -1 and start_index < end_index:
            # Extract the substring between the first '{' and the last '}'
            json_str = response_text[start_index:end_index + 1].strip()
            print("Extracted JSON String:", json_str)
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to decode JSON: {e}")
        else:
            print("No valid JSON found between the first '{' and the last '}'")

    # Extract inside the code block
    json_text = match.group(1).strip()

    # Load as dict
    try:
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")
