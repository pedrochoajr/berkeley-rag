import json
from openai import OpenAI
from dotenv import load_dotenv
import os
from pipeline.config import SYSTEM_PROMPT

load_dotenv()

class QueryRewriter:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def rewrite(self, query: str) -> list[str]:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.3
        )

        raw = response.choices[0].message.content.strip()

        try:
            queries = json.loads(raw)
            if not isinstance(queries, list):
                return [query]
            return [query] + queries
        except json.JSONDecodeError:
            return [query]