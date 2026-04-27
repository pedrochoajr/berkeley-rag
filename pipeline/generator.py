from openai import OpenAI
from dotenv import load_dotenv
from pipeline.config import SYSTEM_GENERATION_PROMPT
import os

load_dotenv()

class Generator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(self, query: str, results: list[dict]) -> dict:
        if not results:
            return {
                "answer": "I couldn't find any relevant courses for your query.",
                "sources": []
            }

        context = self._build_context(results)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_GENERATION_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
            temperature=0.2
        )

        answer = response.choices[0].message.content.strip()

        return {
            "answer": answer,
            "sources": [r["metadata"]["code"] for r in results]
        }

    def _build_context(self, results: list[dict]) -> str:
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"""
Course {i}:
{result['text']}
Relevance Score: {result.get('relevance_score', 'N/A')}
---""")
        return "\n".join(context_parts)

