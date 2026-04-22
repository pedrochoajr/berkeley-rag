from ingestion.config import LEVEL_MAP

def parse_course(raw: dict) -> dict:
    return {
        "course_id": raw.get("courseGroupId", ""),
        "code": raw.get("code", ""),
        "name": raw.get("longName", ""),
        "description": raw.get("description", ""),
        "department": raw.get("subjectCode", ""),
        "units": _parse_units(raw),
        "level": _parse_level(raw),
        "prerequisites": _parse_prerequisites(raw),
        "prerequisite_text": _parse_prerequisite_text(raw)
    }

def _parse_units(raw: dict) -> int:
    try:
        return raw["credits"]["numberOfCredits"]
    except (KeyError, TypeError):
        return 0

def _parse_level(raw: dict) -> str:
    try:
        attributes = raw["customFields"]["catalogAttributes"]
        for attribute in attributes:
            for code, level in LEVEL_MAP.items():
                if code in attribute:
                    return level
        return "Unknown"
    except (KeyError, TypeError):
        return "Unknown"

def _parse_prerequisites(raw: dict) -> list[dict]:
    prerequisites = []
    try:
        rules = raw["requisites"]["requisitesSimple"]
        for rule in rules:
            if rule.get("type") != "Prerequisite":
                continue
            for r in rule.get("rules", []):
                condition = r.get("condition")
                if condition == "freeformText":
                    continue
                value = r.get("value", {})
                for group in value.get("values", []):
                    course_ids = group.get("value", [])
                    if course_ids:
                        prerequisites.append({
                            "type": group.get("logic", "or"),
                            "course_ids": [str(cid) for cid in course_ids],
                            "text": r.get("name", "")
                        })
    except (KeyError, TypeError):
        pass
    return prerequisites

def _parse_prerequisite_text(raw: dict) -> str:
    try:
        rules = raw["requisites"]["requisitesSimple"]
        texts = []
        for rule in rules:
            for r in rule.get("rules", []):
                if r.get("condition") == "freeformText":
                    texts.append(r.get("value", ""))
                elif r.get("name"):
                    texts.append(r.get("name", ""))
        return " ".join(texts).strip()
    except (KeyError, TypeError):
        return ""