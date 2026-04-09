from lms_backend.utils.enums import SessionSource


def _topic_variants(topic: str) -> tuple[str, str]:
    topic_clean = topic.strip() or "Core material"
    return topic_clean, topic_clean.lower()


def _study_title(topic: str, index: int) -> str:
    patterns = [
        "{topic}: foundations and anchor examples",
        "{topic}: key ideas and worked examples",
        "{topic}: build understanding and quick recall",
    ]
    return patterns[index % len(patterns)].format(topic=topic)


def _practice_title(topic: str, index: int) -> str:
    patterns = [
        "{topic}: targeted practice set",
        "{topic}: applied problems and error check",
        "{topic}: practice sprint",
    ]
    return patterns[index % len(patterns)].format(topic=topic)


def _revision_title(topic: str, index: int) -> str:
    patterns = [
        "{topic}: revision and memory check",
        "{topic}: recap and weak-point cleanup",
        "{topic}: quick revision block",
    ]
    return patterns[index % len(patterns)].format(topic=topic)


def _study_description(topic: str, preferred_mode: str, index: int) -> str:
    _, topic_lower = _topic_variants(topic)
    if preferred_mode == "practice":
        variants = [
            f"Start with a 10-minute recap of {topic_lower}, then solve 3-5 representative tasks and note the rule behind each mistake.",
            f"Refresh the core ideas in {topic_lower}, then spend most of the block applying them to short targeted exercises.",
        ]
    elif preferred_mode == "theory":
        variants = [
            f"Rebuild the main ideas in {topic_lower} from memory, then summarize the key rules and one worked example in your own words.",
            f"Clarify the logic behind {topic_lower}, write a compact explanation for yourself, and test it on 1-2 examples.",
        ]
    else:
        variants = [
            f"Identify the core rules in {topic_lower}, work through 2 representative examples, and leave yourself a short recap for revision day.",
            f"Map the main ideas in {topic_lower}, then test them on a couple of examples and record one confusion to revisit later.",
        ]
    return variants[index % len(variants)]


def _practice_description(topic: str, index: int) -> str:
    _, topic_lower = _topic_variants(topic)
    variants = [
        f"Solve 4-6 focused tasks on {topic_lower}; after each set, write down the mistake pattern or shortcut you want to remember.",
        f"Work through a targeted problem set on {topic_lower}, then group your misses by type and fix the weakest step.",
        f"Do a short drill on {topic_lower} with timed questions, then review why each difficult item was tricky.",
    ]
    return variants[index % len(variants)]


def _revision_description(topic: str, index: int) -> str:
    _, topic_lower = _topic_variants(topic)
    variants = [
        f"Recall {topic_lower} without notes, check the gaps, and compress the essentials into a one-page recap or flash list.",
        f"Review the rules, formulas, or patterns behind {topic_lower}, then do a quick self-check from memory.",
        f"Use this block to tighten weak spots in {topic_lower} and turn them into a short revision sheet.",
    ]
    return variants[index % len(variants)]


def _mock_description(topics: list[str], index: int) -> str:
    if topics:
        focus = ", ".join(topic.lower() for topic in topics[:3])
        return (
            f"Run a timed mixed set covering {focus}, then review the misses and queue the weakest pattern for your next revision block."
        )
    return "Run a timed mixed set, then review the misses and turn them into a short weak-points checklist."


def apply_topics_to_skeleton(
    skeleton: list[dict[str, object]],
    topics: list[str],
    preferred_mode: str = "balanced",
    exam_name: str | None = None,
) -> list[dict[str, object]]:
    if not topics:
        topics = ["Overview", "Practice", "Revision"]
    rows: list[dict[str, object]] = []
    for index, session in enumerate(skeleton):
        topic = topics[index % len(topics)]
        session_type = str(session["session_type"])
        title = _study_title(topic, index)
        description = _study_description(topic, preferred_mode, index)
        if session_type == "practice":
            title = _practice_title(topic, index)
            description = _practice_description(topic, index)
        elif session_type == "revision":
            title = _revision_title(topic, index)
            description = _revision_description(topic, index)
        elif session_type == "mock":
            exam_label = exam_name.strip() if exam_name else "exam"
            title = f"Mock exam: {exam_label}"
            description = _mock_description(topics[index % len(topics) :] + topics[: index % len(topics)], index)
        rows.append(
            {
                **session,
                "title": title,
                "description": description,
                "source": SessionSource.SYSTEM.value,
            }
        )
    return rows
