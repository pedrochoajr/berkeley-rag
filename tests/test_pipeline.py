import pytest
from unittest.mock import patch, MagicMock
from pipeline.query_rewriter import QueryRewriter
from pipeline.retriever import HybridRetriever
from ingestion.vector_loader import VectorLoader
from unittest.mock import patch, MagicMock

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def rewriter():
    return QueryRewriter()

def make_mock_response(content: str):
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock

# ── Happy path ─────────────────────────────────────────────────────────────────

def test_rewrite_returns_list(rewriter):
    mock_response = make_mock_response(
        '["upper division math courses", "calculus prerequisites", "STEM sequences"]'
    )
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("what should i take after calc")

    assert isinstance(result, list)

def test_rewrite_includes_original_query(rewriter):
    mock_response = make_mock_response(
        '["upper division math courses", "calculus prerequisites", "STEM sequences"]'
    )
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("what should i take after calc")

    assert "what should i take after calc" in result

def test_rewrite_returns_four_queries(rewriter):
    mock_response = make_mock_response(
        '["upper division math courses", "calculus prerequisites", "STEM sequences"]'
    )
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("what should i take after calc")

    assert len(result) == 4

def test_original_query_is_first(rewriter):
    mock_response = make_mock_response(
        '["upper division math courses", "calculus prerequisites", "STEM sequences"]'
    )
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("what should i take after calc")

    assert result[0] == "what should i take after calc"

# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_invalid_json_falls_back_to_original(rewriter):
    mock_response = make_mock_response(
        "Here are three alternative queries for your search..."
    )
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("what should i take after calc")

    assert result == ["what should i take after calc"]

def test_non_list_json_falls_back_to_original(rewriter):
    mock_response = make_mock_response('{"query": "upper division math"}')
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("what should i take after calc")

    assert result == ["what should i take after calc"]

def test_empty_query_handled(rewriter):
    mock_response = make_mock_response(
        '["STEM courses", "Berkeley courses", "undergraduate courses"]'
    )
    with patch.object(rewriter.client.chat.completions, 'create', return_value=mock_response):
        result = rewriter.rewrite("")

    assert isinstance(result, list)
    assert "" in result


from pipeline.retriever import HybridRetriever
from ingestion.vector_loader import VectorLoader
from unittest.mock import patch, MagicMock

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def retriever():
    vector_loader = VectorLoader()
    return HybridRetriever(vector_loader)

# ── Return structure ───────────────────────────────────────────────────────────

def test_retrieve_returns_list(retriever):
    results = retriever.retrieve(["machine learning"], n_results=3)
    assert isinstance(results, list)

def test_retrieve_returns_correct_structure(retriever):
    results = retriever.retrieve(["calculus"], n_results=3)
    assert len(results) > 0
    for result in results:
        assert "course_id" in result
        assert "text" in result
        assert "metadata" in result

def test_retrieve_respects_n_results(retriever):
    results = retriever.retrieve(["mathematics"], n_results=3)
    assert len(results) <= 3

# ── Semantic search ────────────────────────────────────────────────────────────

def test_semantic_search_returns_relevant_results(retriever):
    results = retriever._semantic_search("machine learning theory", 5, None)
    assert len(results) > 0
    assert isinstance(results[0], str)

def test_semantic_search_with_department_filter(retriever):
    ids = retriever._semantic_search(
        "programming",
        5,
        {"department": "COMPSCI"}
    )
    if ids:
        fetched = retriever.vector_loader.collection.get(
            ids=ids,
            include=["metadatas"]
        )
        for metadata in fetched["metadatas"]:
            assert metadata["department"] == "COMPSCI"

# ── BM25 search ────────────────────────────────────────────────────────────────

def test_keyword_search_returns_results(retriever):
    results = retriever._keyword_search("calculus", 5)
    assert len(results) > 0

def test_keyword_search_gibberish_returns_results(retriever):
    results = retriever._keyword_search("xkqzwpvmjf", 5)
    assert isinstance(results, list)

def test_keyword_search_returns_course_ids(retriever):
    results = retriever._keyword_search("linear algebra", 5)
    for course_id in results:
        assert isinstance(course_id, str)

# ── RRF ────────────────────────────────────────────────────────────────────────

def test_rrf_consensus_beats_single_high_rank(retriever):
    course_a = "course_appearing_once_at_rank_1"
    course_b = "course_appearing_three_times_at_rank_2"

    rankings = [
        [course_a, "other1", "other2"],
        [course_b, "other3", "other4"],
        [course_b, "other5", "other6"],
        [course_b, "other7", "other8"]
    ]

    result = retriever._reciprocal_rank_fusion(rankings, n_results=2)
    assert result[0] == course_b

def test_rrf_deduplicates_results(retriever):
    rankings = [
        ["course1", "course2", "course3"],
        ["course1", "course2", "course3"],
        ["course1", "course2", "course3"]
    ]

    result = retriever._reciprocal_rank_fusion(rankings, n_results=5)
    assert len(result) == len(set(result))

def test_rrf_score_compression(retriever):
    k = 60
    score_rank_1 = 1 / (1 + k)
    score_rank_2 = 1 / (2 + k)
    difference = score_rank_1 - score_rank_2
    assert difference < 0.001

def test_rrf_returns_correct_count(retriever):
    rankings = [
        ["a", "b", "c", "d", "e"],
        ["b", "c", "d", "e", "f"]
    ]
    result = retriever._reciprocal_rank_fusion(rankings, n_results=3)
    assert len(result) == 3

# ── Full pipeline ──────────────────────────────────────────────────────────────

def test_retrieve_with_multiple_queries(retriever):
    queries = [
        "machine learning",
        "statistical learning theory",
        "neural networks optimization"
    ]
    results = retriever.retrieve(queries, n_results=5)
    assert len(results) > 0

def test_retrieve_with_metadata_filter(retriever):
    results = retriever.retrieve(
        ["programming languages"],
        n_results=3,
        filters={"department": "COMPSCI"}
    )
    for result in results:
        assert result["metadata"]["department"] == "COMPSCI"