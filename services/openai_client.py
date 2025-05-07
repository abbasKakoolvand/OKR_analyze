# services/openai_client.py
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")


# Initialize AzureOpenAI client
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)



class OpenAIClient:
    @staticmethod
    def chat(
            messages,
            deployment: str = AZURE_OPENAI_DEPLOYMENT,
            temperature: float = 0.0,  # Deterministic mode
            max_tokens: int = 8196,
            top_p: float = 1.0,
            seed: int = 42  # Fixed seed for reproducibility
    ) -> str:
        """
        Send a chat completion request to Azure OpenAI with deterministic settings.

        :param messages: List of {"role": ..., "content": ...} dicts
        :param deployment: Model deployment name
        :param temperature: Sampling temperature (0 for deterministic)
        :param max_tokens: Max response tokens
        :param top_p: Nucleus sampling parameter
        :param seed: Random seed for reproducibility
        :return: The assistant's reply text
        """
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=deployment,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                seed=seed  # Critical for reproducibility
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI Chat API call failed: {e}")