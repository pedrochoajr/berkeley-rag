import pytest
from ingestion.parser import parse_course
from ingestion.catalog_client import fetch_courses_by_department


# ── Fixtures ──────────────────────────────────────────────────────────────────

FULL_COURSE = {
    "courseGroupId": "1145002",
    "code": "MATH52",
    "longName": "Calculus II",
    "description": "Continuation of 51. Techniques of integration.",
    "subjectCode": "MATH",
    "credits": {"numberOfCredits": 4},
    "customFields": {"catalogAttributes": ["CCLV - UGLD (UG Lower Division)"]},
    "requisites": {
        "requisitesSimple": [
            {
                "type": "Prerequisite",
                "rules": [
                    {
                        "name": "MATH 51.",
                        "condition": "completedAnyOf",
                        "value": {
                            "values": [{"logic": "or", "value": ["1144962", "1145001"]}]
                        },
                    }
                ],
            }
        ]
    },
}

FREEFORM_COURSE = {
    "courseGroupId": "1042961",
    "code": "COMPSCI2",
    "longName": "Topics in Computer Science",
    "description": "A seminar course.",
    "subjectCode": "COMPSCI",
    "credits": {"numberOfCredits": 1},
    "customFields": {"catalogAttributes": ["CCLV - UGLD (UG Lower Division)"]},
    "requisites": {
        "requisitesSimple": [
            {
                "type": "Prerequisite",
                "rules": [
                    {"condition": "freeformText", "value": "Consent of instructor."}
                ],
            }
        ]
    },
}

EMPTY_COURSE = {
    "courseGroupId": "9999999",
    "code": "TEST99",
    "longName": "Test Course",
    "description": "",
    "subjectCode": "TEST",
    "credits": {},
    "customFields": {},
    "requisites": {},
}

MULTI_RULE_COURSE = {
    "courseGroupId": "1042881",
    "code": "COMPSCI189",
    "longName": "Introduction to Machine Learning",
    "description": "Theoretical foundations of ML.",
    "subjectCode": "COMPSCI",
    "credits": {"numberOfCredits": 4},
    "customFields": {"catalogAttributes": ["CCUP - UGUD (UG Upper Division)"]},
    "requisites": {
        "requisitesSimple": [
            {
                "type": "Prerequisite",
                "rules": [
                    {
                        "name": "MATH 54 or EECS 16A.",
                        "condition": "completedAnyOf",
                        "value": {
                            "values": [{"logic": "or", "value": ["1147051", "1063251"]}]
                        },
                    },
                    {
                        "name": "STAT 134 or STAT 140.",
                        "condition": "completedAnyOf",
                        "value": {
                            "values": [{"logic": "or", "value": ["1234567", "1234568"]}]
                        },
                    },
                ],
            }
        ]
    },
}

# ── Happy path ─────────────────────────────────────────────────────────────────


def test_parse_basic_fields():
    result = parse_course(FULL_COURSE)
    assert result["course_id"] == "1145002"
    assert result["code"] == "MATH52"
    assert result["name"] == "Calculus II"
    assert result["description"] == "Continuation of 51. Techniques of integration."
    assert result["department"] == "MATH"
    assert result["units"] == 4


def test_parse_level_lower_division():
    result = parse_course(FULL_COURSE)
    assert result["level"] == "Lower Division"


def test_parse_level_upper_division():
    result = parse_course(MULTI_RULE_COURSE)
    assert result["level"] == "Upper Division"


# ── Prerequisite parsing ───────────────────────────────────────────────────────


def test_parse_structured_prerequisites():
    result = parse_course(FULL_COURSE)
    assert len(result["prerequisites"]) == 1
    prereq = result["prerequisites"][0]
    assert prereq["type"] == "or"
    assert "1144962" in prereq["course_ids"]
    assert "1145001" in prereq["course_ids"]
    assert prereq["text"] == "MATH 51."


def test_parse_multiple_prerequisite_rules():
    result = parse_course(MULTI_RULE_COURSE)
    assert len(result["prerequisites"]) == 2


def test_freeform_excluded_from_prerequisites():
    result = parse_course(FREEFORM_COURSE)
    assert result["prerequisites"] == []


def test_freeform_captured_in_prerequisite_text():
    result = parse_course(FREEFORM_COURSE)
    assert "Consent of instructor" in result["prerequisite_text"]


def test_course_ids_are_strings():
    result = parse_course(FULL_COURSE)
    for prereq in result["prerequisites"]:
        for cid in prereq["course_ids"]:
            assert isinstance(cid, str)


# ── Edge cases ─────────────────────────────────────────────────────────────────


def test_missing_credits_defaults_to_zero():
    result = parse_course(EMPTY_COURSE)
    assert result["units"] == 0


def test_missing_prerequisites_returns_empty_list():
    result = parse_course(EMPTY_COURSE)
    assert result["prerequisites"] == []


def test_missing_description_returns_empty_string():
    result = parse_course(EMPTY_COURSE)
    assert result["description"] == ""


def test_missing_level_returns_unknown():
    result = parse_course(EMPTY_COURSE)
    assert result["level"] == "Unknown"



##API test###
@pytest.mark.integration
def test_parse_real_api_data():
    raw_courses = fetch_courses_by_department("MATH")
    
    for raw in raw_courses:
        result = parse_course(raw)
        
        assert isinstance(result["course_id"], str)
        assert isinstance(result["code"], str)
        assert isinstance(result["name"], str)
        assert isinstance(result["description"], str)
        assert isinstance(result["units"], (int, float))
        assert isinstance(result["prerequisites"], list)
        assert isinstance(result["prerequisite_text"], str)

        print(result)
