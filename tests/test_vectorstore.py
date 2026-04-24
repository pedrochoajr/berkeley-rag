import pytest
import chromadb
from unittest.mock import patch, MagicMock
from ingestion.vector_loader import VectorLoader
from tests.fixtures import MATH51, MATH52, CS189

FAKE_EMBEDDING = [0.1] * 1536

# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def vector_loader():
    loader = VectorLoader()
    loader.clear_collection()
    yield loader
    loader.clear_collection()

@pytest.fixture
def mock_embed(vector_loader):
    with patch.object(
        vector_loader.openai.embeddings,
        'create'
    ) as mock_create:
        mock_create.return_value.data = [
            MagicMock(embedding=FAKE_EMBEDDING)
        ]
        yield vector_loader

# ── Text building ──────────────────────────────────────────────────────────────

def test_build_text_includes_all_fields(mock_embed):
    text = mock_embed._build_text(CS189)
    assert "COMPSCI189" in text
    assert "Introduction to Machine Learning" in text
    assert "COMPSCI" in text
    assert "Upper Division" in text
    assert "4" in text
    assert "Theoretical foundations" in text

def test_build_text_handles_empty_description(mock_embed):
    course = {**MATH51, "description": ""}
    text = mock_embed._build_text(course)
    assert "MATH51" in text
    assert text.strip() != ""

# ── Storage ────────────────────────────────────────────────────────────────────

def test_course_stored_in_chroma(mock_embed):
    mock_embed.load_courses([MATH51])

    result = mock_embed.collection.get(ids=[MATH51["course_id"]])
    assert len(result["ids"]) == 1
    assert result["ids"][0] == MATH51["course_id"]

def test_metadata_attached_to_vector(mock_embed):
    mock_embed.load_courses([MATH51])

    result = mock_embed.collection.get(
        ids=[MATH51["course_id"]],
        include=["metadatas"]
    )
    metadata = result["metadatas"][0]
    assert metadata["code"] == "MATH51"
    assert metadata["department"] == "MATH"
    assert metadata["level"] == "Lower Division"
    assert metadata["units"] == 4.0

def test_document_text_stored(mock_embed):
    mock_embed.load_courses([MATH51])

    result = mock_embed.collection.get(
        ids=[MATH51["course_id"]],
        include=["documents"]
    )
    assert "MATH51" in result["documents"][0]

def test_multiple_courses_stored(mock_embed):
    mock_embed.load_courses([MATH51, MATH52, CS189])

    result = mock_embed.collection.get()
    assert len(result["ids"]) == 3

# ── Idempotency ────────────────────────────────────────────────────────────────

def test_loading_same_course_twice_no_duplicates(mock_embed):
    mock_embed.load_courses([MATH51])
    mock_embed.load_courses([MATH51])

    result = mock_embed.collection.get()
    assert len(result["ids"]) == 1

# ── Query ──────────────────────────────────────────────────────────────────────

def test_query_returns_results(mock_embed):
    mock_embed.load_courses([MATH51, MATH52, CS189])

    results = mock_embed.query("calculus course", n_results=2)
    assert len(results["ids"][0]) == 2

def test_query_with_department_filter(mock_embed):
    mock_embed.load_courses([MATH51, MATH52, CS189])

    results = mock_embed.query(
        "calculus",
        n_results=3,
        filters={"department": "MATH"}
    )
    for metadata in results["metadatas"][0]:
        assert metadata["department"] == "MATH"

def test_query_with_units_filter(mock_embed):
    mock_embed.load_courses([MATH51, MATH52, CS189])

    results = mock_embed.query(
        "math course",
        n_results=3,
        filters={"units": 4.0}
    )
    for metadata in results["metadatas"][0]:
        assert metadata["units"] == 4.0

# ── Clear collection ───────────────────────────────────────────────────────────

def test_clear_collection_removes_all_vectors(mock_embed):
    mock_embed.load_courses([MATH51, MATH52])
    mock_embed.clear_collection()

    result = mock_embed.collection.get()
    assert len(result["ids"]) == 0