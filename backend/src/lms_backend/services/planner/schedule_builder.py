from math import ceil

from lms_backend.utils.enums import SessionSource, SessionStatus, SessionType


def build_skeleton(days_available: int, hours_per_day: float) -> list[dict[str, object]]:
    total_minutes = max(int(days_available * hours_per_day * 60), 60)
    preferred_session_minutes = 90
    sessions_count = max(1, ceil(total_minutes / preferred_session_minutes))
    daily_capacity = max(1, ceil(hours_per_day * 60 / preferred_session_minutes))

    rows: list[dict[str, object]] = []
    for index in range(sessions_count):
        day_number = min(days_available, index // daily_capacity + 1)
        session_order = index % daily_capacity + 1
        if index == sessions_count - 1:
            session_type = SessionType.MOCK.value
        elif index >= max(1, sessions_count - 2):
            session_type = SessionType.REVISION.value
        elif index % 3 == 2:
            session_type = SessionType.PRACTICE.value
        else:
            session_type = SessionType.STUDY.value
        rows.append(
            {
                "day_number": day_number,
                "session_order": session_order,
                "title": f"Session {index + 1}",
                "description": "Core study block",
                "duration_minutes": preferred_session_minutes,
                "session_type": session_type,
                "status": SessionStatus.PENDING.value,
                "source": SessionSource.SYSTEM.value,
            }
        )
    return rows
