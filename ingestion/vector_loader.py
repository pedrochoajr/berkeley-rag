import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()


class VectorLoader:
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma.get_or_create_collection(
            name="courses", metadata={"hnsw:space": "cosine"}
        )

    def load_courses(self, courses: list[dict]) -> None:
        for course in courses:
            text = self._build_text(course)
            if not text.strip():
                continue
            embedding = self._embed(text)
            self._store(course, text, embedding)

    def _build_text(self, course: dict) -> str:
        return f"""Course: {course['code']} - {course['name']}
                Department: {course['department']}
                Level: {course['level']}
                Units: {course['units']}
                Description: {course['description']}
                Prerequisites: {course['prerequisite_text']}""".strip()

    def _embed(self, text: str) -> list[float]:
        response = self.openai.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return response.data[0].embedding

    def _store(self, course: dict, text: str, embedding: list[float]) -> None:
        self.collection.upsert(
            ids=[course["course_id"]],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "course_id": course["course_id"],
                    "code": course["code"],
                    "name": course["name"],
                    "department": course["department"],
                    "units": float(course["units"]),
                    "level": course["level"],
                }
            ],
        )

    def clear_collection(self) -> None:
        self.chroma.delete_collection("courses")
        self.collection = self.chroma.get_or_create_collection(
            name="courses", metadata={"hnsw:space": "cosine"}
        )

    def query(self, query_text: str, n_results: int = 5, filters: dict = None) -> list[dict]:
        query_embedding = self._embed(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=n_results, where=filters
        )
        return results
