from ingestion.catalog_client import fetch_courses_by_department

def test_fetch_compsci_courses():
    courses = fetch_courses_by_department("COMPSCI")
    
    assert len(courses) > 0
    
    first = courses[0]

    assert "courseGroupId" in first
    assert "code" in first
    assert "description" in first
    assert "credits" in first
    assert "requisites" in first

def test_fetch_returns_only_active_approved():
    courses = fetch_courses_by_department("MATH")
    
    for course in courses:
        print(course["code"])
        assert course["status"] == "Active"
        assert course["courseApproved"] == "Approved"