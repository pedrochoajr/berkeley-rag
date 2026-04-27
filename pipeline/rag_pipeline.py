from pipeline.query_rewriter import QueryRewriter
from pipeline.retriever import HybridRetriever
from pipeline.reranker import Reranker
from pipeline.generator import Generator
from ingestion.vector_loader import VectorLoader
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.vector_loader = VectorLoader()
        self.query_rewriter = QueryRewriter()
        self.retriever = HybridRetriever(self.vector_loader)
        self.reranker = Reranker()
        self.generator = Generator()

    def query(self, user_query: str, filters: dict = None) -> dict:
        logger.info(f"Query received: {user_query}")

        # Step 1 — rewrite
        queries = self.query_rewriter.rewrite(user_query)
        logger.info(f"Rewritten into {len(queries)} queries")

        # Step 2 — retrieve
        results = self.retriever.retrieve(queries, n_results=10, filters=filters)
        logger.info(f"Retrieved {len(results)} results")

        # Step 3 — rerank
        reranked = self.reranker.rerank(user_query, results, top_k=7)
        logger.info(f"Reranked to {len(reranked)} results")

        # Step 4 — generate
        response = self.generator.generate(user_query, reranked)
        logger.info(f"Generated answer with {len(response['sources'])} sources")

        return response