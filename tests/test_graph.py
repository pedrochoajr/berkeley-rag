import pytest
from ingestion.graph_loader import GraphLoader
from graph.neo4j_client import Neo4jClient
from tests.fixtures import MATH51, MATH52, CS189


# Connection to Neo4js
def test_neo4j_connection():
    client = Neo4jClient()
    assert client.verify_connection() == True
    client.close()

# Node creation

def test_course_node_created_with_correct_properties(graph_loader):
    graph_loader.load_courses([MATH51])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (c:Course {course_id: $course_id})
            RETURN c
        """, course_id="1144962").single()

    assert result is not None
    node = result["c"]
    assert node["code"] == "MATH51"
    assert node["name"] == "Calculus I"
    assert node["units"] == 4
    assert node["department"] == "MATH"
    assert node["level"] == "Lower Division"

def test_correct_number_of_nodes_created(graph_loader):
    graph_loader.load_courses([MATH51, MATH52])

    with graph_loader.driver.session() as session:
        result = session.run("MATCH (c:Course) RETURN count(c) as count").single()

    # MATH51, MATH52, plus 2 stub nodes for MATH52's prereqs
    # but MATH51 is already a real node so only 1 stub
    assert result["count"] == 3

def test_stub_node_created_for_unknown_prereq(graph_loader):
    graph_loader.load_courses([MATH52])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (c:Course {course_id: $course_id})
            RETURN c
        """, course_id="1144962").single()

    assert result is not None
    node = result["c"]
    assert node["code"] is None

def test_stub_node_filled_in_when_department_loaded(graph_loader):
    graph_loader.load_courses([MATH52])
    graph_loader.load_courses([MATH51])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (c:Course {course_id: $course_id})
            RETURN c
        """, course_id="1144962").single()

    node = result["c"]
    assert node["code"] == "MATH51"
    assert node["name"] == "Calculus I"

# Edge creation

def test_prerequisite_edge_created(graph_loader):
    graph_loader.load_courses([MATH51, MATH52])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (prereq:Course {course_id: $prereq_id})
                  -[r:REQUIRES]->
                  (course:Course {course_id: $course_id})
            RETURN r
        """, prereq_id="1144962", course_id="1145002").single()

    assert result is not None

def test_edges_share_group_id_within_or_group(graph_loader):
    graph_loader.load_courses([CS189])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (prereq:Course)-[r:REQUIRES]->(course:Course {course_id: $course_id})
            RETURN prereq.course_id as prereq_id, r.group_id as group_id
            ORDER BY group_id
        """, course_id="1042881").data()

    group_0 = [r["prereq_id"] for r in result if r["group_id"] == 0]
    group_1 = [r["prereq_id"] for r in result if r["group_id"] == 1]

    assert "1147051" in group_0
    assert "1063251" in group_0
    assert "1234567" in group_1
    assert "1234568" in group_1

def test_and_groups_have_different_group_ids(graph_loader):
    graph_loader.load_courses([CS189])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (prereq:Course)-[r:REQUIRES]->(course:Course {course_id: $course_id})
            RETURN DISTINCT r.group_id as group_id
        """, course_id="1042881").data()

    group_ids = [r["group_id"] for r in result]
    assert len(set(group_ids)) == 2

# Idempotency

def test_loading_same_courses_twice_no_duplicates(graph_loader):
    graph_loader.load_courses([MATH51, MATH52])
    graph_loader.load_courses([MATH51, MATH52])

    with graph_loader.driver.session() as session:
        node_count = session.run(
            "MATCH (c:Course) RETURN count(c) as count"
        ).single()["count"]

        edge_count = session.run(
            "MATCH ()-[r:REQUIRES]->() RETURN count(r) as count"
        ).single()["count"]

    assert node_count == 3
    assert edge_count == 2

# Traversal

def test_graph_traversal_finds_prerequisites(graph_loader):
    graph_loader.load_courses([MATH51, MATH52])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (prereq:Course)-[:REQUIRES*]->(course:Course {code: $code})
            RETURN prereq.code as prereq_code
        """, code="MATH52").data()

    prereq_codes = [r["prereq_code"] for r in result]
    assert "MATH51" in prereq_codes

def test_graph_traversal_finds_unlocked_courses(graph_loader):
    graph_loader.load_courses([MATH51, MATH52])

    with graph_loader.driver.session() as session:
        result = session.run("""
            MATCH (course:Course {code: $code})-[:REQUIRES*]->(unlocked:Course)
            RETURN unlocked.code as unlocked_code
        """, code="MATH51").data()

    unlocked_codes = [r["unlocked_code"] for r in result]
    assert "MATH52" in unlocked_codes

# Clear graph

def test_clear_graph_removes_all_nodes(graph_loader):
    graph_loader.load_courses([MATH51, MATH52])
    graph_loader.clear_graph()

    with graph_loader.driver.session() as session:
        count = session.run(
            "MATCH (n) RETURN count(n) as count"
        ).single()["count"]

    assert count == 0

