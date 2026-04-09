def _status_marker(status: str) -> str:
    return {
        "completed": "[done]",
        "skipped": "[skip]",
        "pending": "[todo]",
    }.get(status, f"[{status}]")


def format_plan_overview(
    plan: dict,
    *,
    progress: dict | None = None,
    materials: list[dict] | None = None,
) -> str:
    lines = [
        f"Plan: {plan['exam_name']}",
        f"ID: {plan['id']}",
        f"Days: {plan['days_available']} | Hours/day: {plan['hours_per_day']}",
        f"Status: {plan['status']}",
    ]
    current_day = plan.get("current_day_number")
    if current_day is not None:
        lines.append(f"Current day: {current_day}/{plan['days_available']}")
    if progress is not None:
        lines.append(
            f"Progress: {progress['completed']}/{progress['total']} done, {progress['pending']} pending, {progress['skipped']} skipped"
        )
    if materials is not None:
        lines.append(f"Materials: {len(materials)}")
        if materials:
            recent = [item.get("original_filename") or item.get("material_type", "material") for item in materials[:3]]
            lines.append("Recent: " + ", ".join(recent))
    return "\n".join(lines)


def format_plan_sessions(plan: dict) -> str:
    lines = [f"Sessions for {plan['exam_name']}"]
    current_day = None
    for session in plan.get("sessions", []):
        if session["day_number"] != current_day:
            current_day = session["day_number"]
            lines.append(f"Day {current_day}")
        lines.append(
            f"{session['session_order']}. {session['title']} — {session['duration_minutes']} min {_status_marker(session['status'])}"
        )
        description = str(session.get("description", "")).strip()
        if description:
            lines.append(f"   {description}")
    return "\n".join(lines)


def format_plan(plan: dict) -> str:
    return format_plan_sessions(plan)


def format_plans_list(plans: list[dict]) -> str:
    if not plans:
        return "No plans yet."
    lines = ["Your plans:"]
    for plan in plans:
        lines.append(
            f"Plan {plan['id']}: {plan['exam_name']} | {plan['days_available']} days | {plan['hours_per_day']} h/day | {plan['status']}"
        )
    return "\n".join(lines)
