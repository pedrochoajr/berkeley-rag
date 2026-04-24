DEPARTMENTS = [
    "MATH",
    "STAT",
    "PHYSICS",
    "COMPSCI",
    "ELENG",
    "EECS",
    "DATA"
]

CATALOG_ID = "IiU0X4phYTcf0MnvC8yj"

BASE_URL = "https://app.coursedog.com/api/v1/cm/ucberkeley_peoplesoft/courses/search/%24filters"

HEADERS = {
    "X-Requested-With": "catalog",
    "Origin": "https://undergraduate.catalog.berkeley.edu",
    "Referer": "https://undergraduate.catalog.berkeley.edu/",
    "Accept": "application/json, text/plain, */*"
}

LEVEL_MAP = {
    "UGLD": "Lower Division",
    "UGUD": "Upper Division",
    "GRAD": "Graduate"
}