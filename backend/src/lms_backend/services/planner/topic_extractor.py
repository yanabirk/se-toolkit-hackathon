from collections import Counter

from lms_backend.utils.text_utils import clean_text


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "you",
    "exam", "topic", "topics", "chapter", "lecture", "notes", "material", "materials",
    "focus", "prefer", "preferred", "practice", "theory", "balanced", "weak", "student",
    "context", "study", "plan", "priority", "priorities", "review",
}


def extract_priority_topics(materials_text: str) -> list[str]:
    prefixes = (
        "weak topics:",
        "priority topics:",
        "topics to review:",
        "focus areas:",
    )
    topics: list[str] = []
    seen: set[str] = set()
    for raw_line in clean_text(materials_text).split("\n"):
        line = raw_line.strip()
        lowered = line.lower()
        prefix = next((item for item in prefixes if lowered.startswith(item)), None)
        if prefix is None:
            continue
        _, _, value = line.partition(":")
        for part in value.replace(";", ",").split(","):
            topic = part.strip(" -")
            key = topic.lower()
            if topic and key not in seen:
                topics.append(topic[:120])
                seen.add(key)
    return topics


def detect_study_preference(materials_text: str) -> str:
    text = clean_text(materials_text).lower()
    if any(
        token in text
        for token in (
            "preferred mode: practice",
            "more practice",
            "practice-first",
            "practice heavy",
        )
    ):
        return "practice"
    if any(
        token in text
        for token in (
            "preferred mode: theory",
            "more theory",
            "concept-first",
            "theory heavy",
        )
    ):
        return "theory"
    return "balanced"


def extract_topics_fallback(exam_name: str, materials_text: str) -> list[str]:
    prioritized = extract_priority_topics(materials_text)
    if prioritized:
        return prioritized[:8]
    words = []
    for token in clean_text(f"{exam_name} {materials_text}").replace("\n", " ").split(" "):
        token = token.strip(" ,.;:!?()[]{}\"'").lower()
        if len(token) < 4 or token in STOPWORDS:
            continue
        words.append(token)
    common = [word.title() for word, _ in Counter(words).most_common(8)]
    if common:
        return common
    return [part.strip() for part in exam_name.split() if part.strip()]
