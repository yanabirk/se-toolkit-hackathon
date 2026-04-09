import json


def build_topics_prompt(exam_name: str, materials_text: str) -> str:
    return (
        "Extract 5-12 concise study topics for the exam. "
        "Return only valid JSON as an array of strings. "
        f"Exam: {exam_name}\n"
        f"Materials:\n{materials_text[:12000]}"
    )


def build_refine_sessions_prompt(
    exam_name: str,
    days_available: int,
    hours_per_day: float,
    topics: list[str],
    sessions: list[dict[str, object]],
) -> str:
    return (
        "You are refining a study plan. Return only valid JSON as an array. "
        "Each element must keep: day_number, session_order, duration_minutes, session_type. "
        "Add or improve title and description. Be concrete, short, and realistic.\n"
        f"Exam: {exam_name}\n"
        f"Days available: {days_available}\n"
        f"Hours per day: {hours_per_day}\n"
        f"Topics: {json.dumps(topics, ensure_ascii=False)}\n"
        f"Sessions: {json.dumps(sessions, ensure_ascii=False)}"
    )
