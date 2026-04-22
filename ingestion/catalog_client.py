import requests
from dotenv import load_dotenv
from ingestion.config import BASE_URL, CATALOG_ID, HEADERS

load_dotenv()

def fetch_courses_by_department(department_code: str) -> list[dict]:
    courses = []
    skip = 0
    limit = 100

    while True:
        params = {
            "catalogId": CATALOG_ID,
            "skip": skip,
            "limit": limit,
            "orderBy": "code",
            "formatDependents": "false"
        }

        body = {
            "condition": "AND",
            "filters": [
                {
                    "condition": "AND",
                    "filters": [
                        {"name": "status", "type": "is", "value": "Active"},
                        {"name": "courseApproved", "type": "is", "value": "Approved"}
                    ]
                },
                {
                    "condition": "AND",
                    "filters": [
                        {"name": "subjectCode", "type": "anyOf", "value": department_code}
                    ]
                }
            ]
        }

        response = requests.post(BASE_URL, params=params, json=body, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        courses.extend(data["data"])

        total = data["listLength"]
        skip += limit

        if skip >= total:
            break

    return courses