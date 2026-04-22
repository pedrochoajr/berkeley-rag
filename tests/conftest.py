import pytest
from ingestion.graph_loader import GraphLoader

@pytest.fixture
def graph_loader():
    loader = GraphLoader()
    loader.clear_graph()
    yield loader
    loader.clear_graph()
    loader.close()