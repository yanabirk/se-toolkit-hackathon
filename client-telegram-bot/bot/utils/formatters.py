def _status_marker(status: str) -> str:
    return {
        "completed": "✅ Done",
        "skipped": "⏭ Skipped",
        "pending": "◻️ To do",
    }.get(status, status.title())


def _status_icon(status: str) -> str:
    return {
        "completed": "✅",
        "skipped": "⏭",
        "pending": "◻️",
    }.get(status, "•")


def _session_type_label(session_type: str) -> str:
    return {
        "study": "study block",
        "practice": "practice block",
        "revision": "revision block",
        "mock": "mock block",
    }.get(session_type, session_type)


def _trim(value: str, limit: int = 58) -> str:
    text = " ".join(value.split()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def format_plan_overview(
    plan: dict,
    *,
    progress: dict | None = None,
    materials: list[dict] | None = None,
) -> str:
    lines = [f"📘 {plan['exam_name']}", ""]
    current_day = plan.get("current_day_number")
    if current_day is not None:
        lines.append(f"Today is day {current_day} of {plan['days_available']}.")
    else:
        lines.append(f"{plan['days_available']} days planned.")
    lines.append(f"⏱ {plan['hours_per_day']} h/day")
    lines.append(f"📍 Status: {str(plan['status']).replace('_', ' ')}")
    if progress is not None:
        lines.append(
            f"✅ {progress['completed']}/{progress['total']} done • ◻️ {progress['pending']} left • ⏭ {progress['skipped']} skipped"
        )
    if materials is not None:
        lines.append(f"📎 Materials: {len(materials)}")
        if materials:
            recent = [
                _trim(
                    str(
                        item.get("original_filename")
                        or item.get("material_type", "material")
                    ),
                    limit=24,
                )
                for item in materials[:3]
            ]
            lines.append("Recent: " + ", ".join(recent))
    lines.append("")
    lines.append("Use the buttons below to browse sessions or update the plan.")
    return "\n".join(lines)


def format_session_browser(plan: dict, sessions: list[dict], *, context: str) -> str:
    if context == "today":
        title = f"📅 Today for {plan['exam_name']}"
        current_day = int(plan.get("current_day_number") or 1)
        lines = [title, "", f"Day {current_day}. Tap a session below to open it."]
    else:
        lines = [f"🗂 Sessions for {plan['exam_name']}", "", "Tap a session below to view details."]

    if not sessions:
        lines.append("")
        lines.append("No sessions to show yet.")
        return "\n".join(lines)

    lines.append("")
    current_day = None
    for session in sessions:
        if context == "plan" and session["day_number"] != current_day:
            current_day = session["day_number"]
            if lines[-1] != "":
                lines.append("")
            lines.append(f"Day {current_day}")
        lines.append(
            f"{_status_icon(session['status'])} {session['session_order']}. {_trim(session['title'])} • {session['duration_minutes']} min"
        )
    return "\n".join(lines)


def format_session_detail(plan: dict, session: dict, *, context: str) -> str:
    lines = [
        f"{_status_icon(session['status'])} {session['title']}",
        "",
        f"📘 {plan['exam_name']}",
        f"🗓 Day {session['day_number']} • Session {session['session_order']}",
        f"⏱ {session['duration_minutes']} min • {_session_type_label(str(session['session_type']))}",
        f"📍 {_status_marker(str(session['status']))}",
    ]
    description = str(session.get("description", "")).strip()
    if description:
        lines.append("")
        lines.append(description)
    if context == "today":
        lines.append("")
        lines.append("This session is part of today's plan.")
    elif str(session["status"]) == "pending":
        lines.append("")
        lines.append("Mark it done when you finish it.")
    return "\n".join(lines)


def format_plan_sessions(plan: dict) -> str:
    return format_session_browser(plan, plan.get("sessions", []), context="plan")


def format_plan(plan: dict) -> str:
    return format_plan_sessions(plan)


def format_plans_list(plans: list[dict]) -> str:
    if not plans:
        return "📚 You don't have any study plans yet."
    lines = ["📚 Your study plans", ""]
    for plan in plans:
        lines.append(f"📘 Plan {plan['id']} · {plan['exam_name']}")
        lines.append(
            f"   {plan['days_available']} days • {plan['hours_per_day']} h/day • {str(plan['status']).replace('_', ' ')}"
        )
    return "\n".join(lines)
