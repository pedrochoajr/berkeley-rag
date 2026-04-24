import logging
from ingestion.catalog_client import fetch_courses_by_department
from ingestion.parser import parse_course
from ingestion.graph_loader import GraphLoader
from ingestion.vector_loader import VectorLoader
from ingestion.config import DEPARTMENTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_ingestion(clear_existing: bool = False):
    graph_loader = GraphLoader()
    vector_loader = VectorLoader()
    failed_courses = []

    try:
        if clear_existing:
            logger.info("Clearing existing data...")
            graph_loader.clear_graph()
            vector_loader.clear_collection()

        for department in DEPARTMENTS:
            logger.info(f"Processing department: {department}")

            raw_courses = fetch_courses_by_department(department)
            logger.info(f"Fetched {len(raw_courses)} courses for {department}")

            parsed_courses = []
            for raw in raw_courses:
                try:
                    parsed = parse_course(raw)
                    parsed_courses.append(parsed)
                except Exception as e:
                    failed_courses.append((raw.get("code", "unknown"), str(e)))
                    logger.warning(f"Failed to parse course {raw.get('code')}: {e}")

            graph_loader.load_courses(parsed_courses)
            logger.info(f"Loaded {len(parsed_courses)} courses to Neo4j")

            vector_loader.load_courses(parsed_courses)
            logger.info(f"Loaded {len(parsed_courses)} courses to Chroma")

        if failed_courses:
            logger.warning(f"Failed courses: {len(failed_courses)}")
            for code, error in failed_courses:
                logger.warning(f"  {code}: {error}")

        logger.info("Ingestion complete")

    finally:
        graph_loader.close()

if __name__ == "__main__":
    run_ingestion(clear_existing=True)