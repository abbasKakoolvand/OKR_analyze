import os
from dotenv import load_dotenv
import openai

# load environment variables from .env (project root)
load_dotenv()

# now fetch the key
openai.api_key = os.getenv("OPENAI_API_KEY")

class OpenAIClient:
    @staticmethod
    def chat(messages, model="gpt-3.5-turbo", temperature=0.2, max_tokens=1000) -> str:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI Chat API call failed: {e}")
