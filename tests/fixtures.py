MATH51 = {
    "course_id": "1144962",
    "code": "MATH51",
    "name": "Calculus I",
    "description": "Introduction to calculus.",
    "units": 4,
    "department": "MATH",
    "level": "Lower Division",
    "prerequisite_text": "",
    "prerequisites": []
}

MATH52 = {
    "course_id": "1145002",
    "code": "MATH52",
    "name": "Calculus II",
    "description": "Continuation of Calculus I.",
    "units": 4,
    "department": "MATH",
    "level": "Lower Division",
    "prerequisite_text": "",
    "prerequisites": [
        {
            "type": "or",
            "course_ids": ["1144962", "1145001"],
            "text": "MATH 51."
        }
    ]
}

CS189 = {
    "course_id": "1042881",
    "code": "COMPSCI189",
    "name": "Introduction to Machine Learning",
    "description": "Theoretical foundations of ML.",
    "units": 4,
    "department": "COMPSCI",
    "level": "Upper Division",
    "prerequisite_text": "",
    "prerequisites": [
        {
            "type": "or",
            "course_ids": ["1147051", "1063251"],
            "text": "MATH 54 or EECS 16A."
        },
        {
            "type": "or",
            "course_ids": ["1234567", "1234568"],
            "text": "STAT 134 or STAT 140."
        }
    ]
}