from lms_backend.utils.enums import SessionSource


def apply_topics_to_skeleton(
    skeleton: list[dict[str, object]],
    topics: list[str],
    preferred_mode: str = "balanced",
) -> list[dict[str, object]]:
    if not topics:
        topics = ["Overview", "Practice", "Revision"]
    rows: list[dict[str, object]] = []
    for index, session in enumerate(skeleton):
        topic = topics[index % len(topics)]
        title = f"{topic}"
        description = f"Focus on {topic.lower()} and write short notes."
        if str(session["session_type"]) == "practice":
            title = f"Practice: {topic}"
            description = f"Solve targeted problems on {topic.lower()} and check mistakes."
        elif str(session["session_type"]) == "revision":
            title = f"Revision: {topic}"
            description = f"Review key formulas for {topic.lower()} and make a short recap."
        elif str(session["session_type"]) == "mock":
            title = "Mock exam and weak points review"
            description = "Run a timed mixed set, then review weak points and error patterns."
        if preferred_mode == "practice" and str(session["session_type"]) == "study":
            description = (
                f"Start with a short theory recap, then spend most of the block solving tasks on {topic.lower()}."
            )
        elif preferred_mode == "theory" and str(session["session_type"]) in {"study", "revision"}:
            description = (
                f"Build conceptual understanding of {topic.lower()}, then summarize rules and examples."
            )
        rows.append(
            {
                **session,
                "title": title,
                "description": description,
                "source": SessionSource.SYSTEM.value,
            }
        )
    return rows
