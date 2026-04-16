import pytest
from graph.neo4j_client import Neo4jClient

def test_neo4j_connection():
    client = Neo4jClient()
    assert client.verify_connection() == True
    client.close()