# import os
# from dotenv import load_dotenv
# import openai
#
# # load environment variables from .env (project root)
# load_dotenv()
#
# # now fetch the key
# openai.api_key = os.getenv("OPENAI_API_KEY")
#
# class OpenAIClient:
#     @staticmethod
#     def chat(messages, model="gpt-3.5-turbo", temperature=0.2, max_tokens=1000) -> str:
#         try:
#             response = openai.ChatCompletion.create(
#                 model=model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#             )
#             return response.choices[0].message.content.strip()
#         except Exception as e:
#             raise RuntimeError(f"OpenAI Chat API call failed: {e}")


import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

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
            temperature: float = 0.2,
            max_tokens: int = 4096,
            top_p: float = 1.0
    ) -> str:
        """
        Send a chat completion request to Azure OpenAI.

        :param messages: List of {"role": ..., "content": ...} dicts
        :param deployment: the name of your deployed chat model
        :param temperature: sampling temperature
        :param max_tokens: max tokens in the response
        :param top_p: nucleus sampling parameter
        :return: the assistant's reply text
        """
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=deployment,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI Chat API call failed: {e}")
