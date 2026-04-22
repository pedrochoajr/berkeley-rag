from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

class GraphLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    def close(self):
        self.driver.close()

    def load_courses(self, courses: list[dict]) -> None:
        with self.driver.session() as session:
            for course in courses:
                session.execute_write(self._merge_course_node, course)

        with self.driver.session() as session:
            for course in courses:
                session.execute_write(self._merge_prerequisite_edges, course)

    @staticmethod
    def _merge_course_node(tx, course: dict) -> None:
        tx.run("""
            MERGE (c:Course {course_id: $course_id})
            SET c.code = $code,
                c.name = $name,
                c.description = $description,
                c.units = $units,
                c.department = $department,
                c.level = $level,
                c.prerequisite_text = $prerequisite_text
        """,
            course_id=course["course_id"],
            code=course["code"],
            name=course["name"],
            description=course["description"],
            units=course["units"],
            department=course["department"],
            level=course["level"],
            prerequisite_text=course["prerequisite_text"]
        )

    @staticmethod
    def _merge_prerequisite_edges(tx, course: dict) -> None:
        for group_id, prereq_group in enumerate(course["prerequisites"]):
            for prereq_id in prereq_group["course_ids"]:
                tx.run("""
                    MERGE (prereq:Course {course_id: $prereq_id})
                    MERGE (course:Course {course_id: $course_id})
                    MERGE (prereq)-[:REQUIRES {group_id: $group_id}]->(course)
                """,
                    prereq_id=prereq_id,
                    course_id=course["course_id"],
                    group_id=group_id
                )

    def clear_graph(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")