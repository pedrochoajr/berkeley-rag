from rank_bm25 import BM25Okapi
from ingestion.vector_loader import VectorLoader
import re

class HybridRetriever:
    def __init__(self, vector_loader: VectorLoader):
        self.vector_loader = vector_loader
        self.bm25, self.bm25_docs, self.bm25_ids = self._build_bm25_index()

    def _build_bm25_index(self):
        all_data = self.vector_loader.collection.get(
            include=["documents", "metadatas"]
        )
        documents = all_data["documents"]
        ids = all_data["ids"]
        tokenized = [self._tokenize(doc) for doc in documents]
        bm25 = BM25Okapi(tokenized)
        return bm25, documents, ids

    def _tokenize(self, text: str) -> list[str]:
        return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).split()

    def retrieve(self, queries: list[str], n_results: int = 5, filters: dict = None) -> list[dict]:
        all_rankings = []

        for query in queries:
            semantic_ids = self._semantic_search(query, n_results, filters)
            all_rankings.append(semantic_ids)

            keyword_ids = self._keyword_search(query, n_results)
            all_rankings.append(keyword_ids)

        top_ids = self._reciprocal_rank_fusion(all_rankings, n_results)
        return self._fetch_results(top_ids)

    def _semantic_search(self, query: str, n_results: int, filters: dict = None) -> list[str]:
        results = self.vector_loader.query(
            query_text=query,
            n_results=n_results,
            filters=filters
        )
        return results["ids"][0]

    def _keyword_search(self, query: str, n_results: int) -> list[str]:
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:n_results]
        return [self.bm25_ids[i] for i in top_indices]

    def _reciprocal_rank_fusion(self, rankings: list[list[str]], n_results: int, k: int = 60) -> list[str]:
        scores = {}
        for ranking in rankings:
            for rank, course_id in enumerate(ranking):
                if course_id not in scores:
                    scores[course_id] = 0
                scores[course_id] += 1 / (rank + k)

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_ids[:n_results]

    def _fetch_results(self, course_ids: list[str]) -> list[dict]:
        if not course_ids:
            return []
        results = self.vector_loader.collection.get(
            ids=course_ids,
            include=["documents", "metadatas"]
        )
        return [
            {
                "course_id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            }
            for i in range(len(results["ids"]))
        ]