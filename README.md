# Berkeley Course Navigator

A production-level RAG system over UC Berkeley's STEM course catalog that answers complex student questions about courses, prerequisites, and academic planning.

## Architecture

The core architectural insight: prerequisite questions are fundamentally a **graph traversal problem**, not a text retrieval problem. Storing prerequisites as text chunks would require recursive LLM calls that compound errors at each hop. Instead the system separates concerns into two stores:

- **Neo4j knowledge graph** — prerequisite traversal with AND/OR logic encoded as typed edges
- **Chroma vector store** — semantic course search via OpenAI embeddings

```
Student query
    ↓
Query rewriting (GPT-4o-mini) — 4 semantic variations
    ↓
Hybrid retrieval — BM25 + semantic search merged via RRF
    ↓
Reranking (Cohere) — 10 candidates → top 7
    ↓
Grounded generation (GPT-4o) — citations required
    ↓
Guardrails + LangSmith evals (in development)
    ↓
LangGraph multi-hop agent (in development)
```

## Data

Ingested from Berkeley's internal Coursedog API — reverse engineered from network requests, no public documentation available.

| Store | Contents |
|---|---|
| Neo4j | 946 course nodes, 799 prerequisite edges |
| Chroma | 918 course embeddings (1536 dimensions) |

**Departments:** COMPSCI · EECS · MATH · STAT · PHYSICS · ELENG · DATA

## Tech Stack

| Component | Tool |
|---|---|
| Graph database | Neo4j (local) → AuraDB (production) |
| Vector store | Chroma (local) → Pinecone (production) |
| Embedding model | OpenAI text-embedding-3-small |
| Reranker | Cohere rerank-english-v3.0 |
| LLM | GPT-4o (generation) · GPT-4o-mini (rewriting) |
| Agent framework | LangChain · LangGraph |
| Evals | LangSmith |
| Testing | pytest |

## Project Structure

```
berkeley-rag/
├── ingestion/
│   ├── catalog_client.py    # Coursedog API client with pagination
│   ├── parser.py            # Raw JSON → clean structured course dicts
│   ├── graph_loader.py      # Writes nodes and edges to Neo4j
│   ├── vector_loader.py     # Embeds and stores courses in Chroma
│   └── config.py            # Departments, constants, level map
├── pipeline/
│   ├── query_rewriter.py    # Rewrites queries into 4 variations
│   ├── retriever.py         # BM25 + semantic hybrid retrieval + RRF
│   ├── reranker.py          # Cohere reranking
│   ├── generator.py         # Grounded generation with citations
│   └── rag_pipeline.py      # End-to-end pipeline orchestrator
├── graph/
│   └── neo4j_client.py      # Neo4j connection and query utilities
├── agent/                   # LangGraph multi-hop agent (in development)
├── evals/                   # LangSmith evaluation suite (in development)
├── tests/
│   ├── conftest.py          # Shared pytest fixtures
│   ├── fixtures.py          # Shared test data
│   ├── test_ingestion.py    # Catalog client tests
│   ├── test_parser.py       # Parser unit tests
│   ├── test_graph.py        # Neo4j graph loader tests
│   ├── test_vectorstore.py  # Chroma vector loader tests
│   └── test_pipeline.py     # Query rewriter, retriever, reranker, generator tests
├── main.py                  # Ingestion orchestrator
├── requirements.txt
└── .env                     # API keys and DB credentials (not committed)
```

## Setup

### Prerequisites

- Python 3.11+
- Neo4j Desktop
- OpenAI API key
- Cohere API key

### Installation

```bash
git clone https://github.com/pedrochoajr/berkeley-rag
cd berkeley-rag

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=yourpassword
OPENAI_API_KEY=your_openai_key
COHERE_API_KEY=your_cohere_key
```

### Start Neo4j

Open Neo4j Desktop, start your local DBMS, and verify it is running (green status).

### Run Ingestion

```bash
python main.py
```

This fetches all courses from Berkeley's Coursedog API, parses them, loads 946 nodes and 799 prerequisite edges into Neo4j, and stores 918 course embeddings in Chroma. Runtime is approximately 5-10 minutes depending on OpenAI API latency.

### Run Tests

```bash
# All tests
pytest -v

# Unit tests only (no network calls)
pytest -v -m "not integration"

# Specific component
pytest tests/test_graph.py -v
pytest tests/test_pipeline.py -v -k "rerank"
```

### Query the Pipeline

```python
from pipeline.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
response = pipeline.query("I want to learn machine learning, what should I take?")

print(response["answer"])
print(response["sources"])
```

## Key Design Decisions

### Graph over chunks for prerequisites

Prerequisites are relational data masquerading as text. Storing them as chunks would require the LLM to recursively retrieve and parse prerequisite chains — each hop introducing new errors. A Neo4j graph allows deterministic traversal in a single Cypher query:

```cypher
MATCH (prereq:Course)-[:REQUIRES*]->(c:Course {code: "COMPSCI189"})
RETURN prereq.code, prereq.name
```

### AND/OR logic as typed edges

Each prerequisite group gets a `group_id` property on the edge:

- Edges sharing the same `group_id` = OR alternatives (satisfy any one)
- Different `group_id` values = AND groups (must satisfy all)

This encodes Berkeley's full prerequisite logic structurally without any text parsing at query time.

### Hybrid retrieval

BM25 catches exact matches (course codes, professor names). Semantic search catches conceptual queries ("courses about how machines learn"). Results are merged via Reciprocal Rank Fusion with k=60, which rewards courses appearing in multiple result lists over courses ranking highly in just one.

### Stub nodes for cross-department prerequisites

When a course references a prerequisite from an unloaded department, a minimal stub node is created with just the `course_id`. When that department is later ingested, `MERGE` finds the existing stub and fills in all properties. No separate tracking system needed — the graph itself is the promise container.

### Topological department ordering

Departments are ingested in dependency order (MATH → STAT → PHYSICS → ELENG → EECS → COMPSCI → DATA) to minimize stub nodes and ensure most prerequisite nodes exist before the courses that reference them.

## What's Next

- [ ] Guardrails — input and output validation using rule-based and LLM-based checks
- [ ] LangSmith evals — golden dataset, faithfulness scoring, retrieval quality metrics
- [ ] LangGraph multi-hop agent — dynamic routing between Neo4j and Chroma based on query type
- [ ] RateMyProfessor integration — professor review data as additional semantic layer
- [ ] Pinecone migration — swap Chroma for Pinecone for production deployment
- [ ] AuraDB migration — swap local Neo4j for AuraDB for production deployment

## License

MIT
