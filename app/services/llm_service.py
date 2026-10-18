from openai import OpenAI

from app.config import OPENAI_API_KEY


class LLMService:

    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    def ask(
        self,
        input,
        tools=None,
        tool_choice="auto",
    ):
        response = self.client.responses.create(
            model="gpt-6-luna",
            input=input,
            tools=tools or [],
            tool_choice=tool_choice,
        )

        return response

    def ask_structured(
        self,
        input,
        text_format,
    ):
        response = self.client.responses.parse(
            model="gpt-6-luna",
            input=input,
            text_format=text_format,
        )

        return response