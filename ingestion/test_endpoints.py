import requests

LISTING_URL = "https://app.coursedog.com/api/v1/cm/ucberkeley_peoplesoft/courses/search/%24filters"

listing_params = {
    "catalogId": "IiU0X4phYTcf0MnvC8yj",
    "skip": 0,
    "limit": 5,
    "orderBy": "code",
    "formatDependents": "false"
}

listing_body = {
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
                {"name": "subjectCode", "type": "anyOf", "value": "COMPSCI"}
            ]
        }
    ]
}

headers = {
    "X-Requested-With": "catalog",
    "Origin": "https://undergraduate.catalog.berkeley.edu",
    "Referer": "https://undergraduate.catalog.berkeley.edu/",
    "Accept": "application/json, text/plain, */*"
}

response = requests.post(
    LISTING_URL,
    params=listing_params,
    json=listing_body,
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"First course: {response.json()}")