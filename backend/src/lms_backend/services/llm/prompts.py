import json
import re


def _normalize_materials_text(materials_text: str) -> str:
    return re.sub(r"\s+", " ", materials_text).strip()


def _build_material_excerpt(materials_text: str, *, limit: int) -> str:
    normalized = _normalize_materials_text(materials_text)
    if len(normalized) <= limit:
        return normalized

    chunk_size = max(limit // 3, 1)
    middle_start = max(len(normalized) // 2 - chunk_size // 2, 0)
    chunks = [
        normalized[:chunk_size],
        normalized[middle_start : middle_start + chunk_size],
        normalized[-chunk_size:],
    ]
    unique_chunks: list[str] = []
    for chunk in chunks:
        cleaned = chunk.strip()
        if cleaned and cleaned not in unique_chunks:
            unique_chunks.append(cleaned)
    excerpt = " ... ".join(unique_chunks)
    return excerpt[:limit]


def build_topics_prompt(exam_name: str, materials_text: str) -> str:
    excerpt = _build_material_excerpt(materials_text, limit=12000)
    return (
        "You are helping a student prepare for an exam. "
        "Extract 5-12 concrete study topics or sub-topics that would be useful for a day-by-day study plan. "
        "Prefer named concepts, methods, formulas, themes, task types, chapters, or problem families that are actually present in the materials. "
        "Avoid vague labels like 'theory', 'practice', 'revision', or 'review' unless paired with a real topic. "
        "Return only valid JSON as an array of short strings. "
        f"Exam: {exam_name}\n"
        f"Materials excerpt:\n{excerpt}"
    )


def build_refine_sessions_prompt(
    exam_name: str,
    days_available: int,
    hours_per_day: float,
    topics: list[str],
    sessions: list[dict[str, object]],
    materials_text: str,
    preferred_mode: str,
) -> str:
    excerpt = _build_material_excerpt(materials_text, limit=6000)
    return (
        "You are refining a study plan for a student. Return only valid JSON as an array. "
        "Keep exactly the same sessions and preserve day_number, session_order, duration_minutes, and session_type for every item. "
        "You may improve title and description only. "
        "Make the plan specific to the exam, topics, and materials. "
        "Descriptions must be concise, actionable, student-friendly, and naturally written, usually 1-2 short sentences. "
        "Each description should tell the student what to do in that block and what useful output or checkpoint to produce. "
        "Use concrete focus points from the provided topics and materials when available. "
        "Avoid empty generic wording like 'review material', 'study theory', or 'practice problems' unless you expand it with specific focus. "
        "Early sessions should build foundations, middle sessions should deepen understanding and targeted practice, and late sessions should consolidate and test weak areas. "
        "Return only the JSON array with the same number of elements.\n"
        f"Exam: {exam_name}\n"
        f"Days available: {days_available}\n"
        f"Hours per day: {hours_per_day}\n"
        f"Preferred mode: {preferred_mode}\n"
        f"Topics: {json.dumps(topics, ensure_ascii=False)}\n"
        f"Materials excerpt: {excerpt or 'No extra materials provided.'}\n"
        f"Draft sessions to improve: {json.dumps(sessions, ensure_ascii=False)}"
    )
