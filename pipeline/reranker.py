import cohere
from dotenv import load_dotenv
import os

load_dotenv()

class Reranker:
    def __init__(self):
        self.client = cohere.Client(os.getenv("COHERE_API_KEY"))
        self.model = "rerank-english-v3.0"

    def rerank(self, query: str, results: list[dict], top_k: int = 7) -> list[dict]:
        if not results:
            return []

        documents = [r["text"] for r in results]

        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_k
        )

        reranked = []
        for item in response.results:
            result = results[item.index]
            result["relevance_score"] = item.relevance_score
            reranked.append(result)

        return reranked