from openai import OpenAI

from app.config import settings


class ResponseGenerator:
    def __init__(self) -> None:
        if not settings.zyrangg_api_key:
            raise ValueError('Missing ZYRANGG_API_KEY environment variable')
        self.client = OpenAI(api_key=settings.zyrangg_api_key, base_url=settings.zyrangg_base_url)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.chat_model,
            temperature=0,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        content = response.choices[0].message.content
        return content.strip() if content else "I don't know based on the provided Medium articles data."
