
from lms_backend.utils.enums import SessionStatus, SessionType


def validate_topics(payload: object) -> list[str]:
    if not isinstance(payload, list):
        raise ValueError("LLM topics payload must be a list")
    topics: list[str] = []
    for item in payload:
        topic = str(item).strip()
        if topic and topic not in topics:
            topics.append(topic[:120])
    if not topics:
        raise ValueError("No topics returned")
    return topics[:12]


def validate_sessions(payload: object) -> list[dict[str, object]]:
    if not isinstance(payload, list):
        raise ValueError("LLM sessions payload must be a list")
    normalized: list[dict[str, object]] = []
    valid_session_types = {item.value for item in SessionType}
    valid_statuses = {item.value for item in SessionStatus}
    for item in payload:
        if not isinstance(item, dict):
            continue
        required = {"day_number", "session_order", "duration_minutes", "session_type"}
        if not required.issubset(item.keys()):
            continue
        try:
            day_number = int(item["day_number"])
            session_order = int(item["session_order"])
            duration_minutes = int(item["duration_minutes"])
        except (TypeError, ValueError):
            continue
        session_type = str(item["session_type"]).strip().lower()
        if day_number < 1 or session_order < 1 or duration_minutes <= 0:
            continue
        if session_type not in valid_session_types:
            continue
        status = str(item.get("status", SessionStatus.PENDING.value)).strip().lower()
        if status not in valid_statuses:
            status = SessionStatus.PENDING.value
        normalized.append(
            {
                "day_number": day_number,
                "session_order": session_order,
                "duration_minutes": duration_minutes,
                "session_type": session_type,
                "title": str(item.get("title", "Study session")).strip()[:160] or "Study session",
                "description": str(item.get("description", "")).strip()[:1000],
                "source": "llm",
                "status": status,
            }
        )
    if not normalized:
        raise ValueError("No valid sessions returned")
    return normalized
