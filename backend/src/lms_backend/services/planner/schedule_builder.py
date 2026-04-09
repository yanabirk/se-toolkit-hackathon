from math import ceil

from lms_backend.utils.enums import SessionSource, SessionStatus, SessionType


def build_skeleton(days_available: int, hours_per_day: float) -> list[dict[str, object]]:
    total_minutes = max(int(days_available * hours_per_day * 60), 60)
    preferred_session_minutes = 85
    sessions_count = max(1, ceil(total_minutes / preferred_session_minutes))
    if total_minutes >= days_available * 45:
        sessions_count = max(sessions_count, days_available)

    base_duration = total_minutes // sessions_count
    extra_minutes = total_minutes % sessions_count

    # Spread sessions across days while keeping slot positions stable for status persistence.
    active_days = min(days_available, sessions_count)
    day_loads = [sessions_count // active_days] * active_days
    for index in range(sessions_count % active_days):
        day_loads[index] += 1

    rows: list[dict[str, object]] = []
    slot_index = 0
    for day_offset, sessions_in_day in enumerate(day_loads):
        for session_order in range(1, sessions_in_day + 1):
            duration_minutes = base_duration + (1 if slot_index < extra_minutes else 0)
            index = slot_index
            day_number = day_offset + 1
            slot_index += 1

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
                    "duration_minutes": duration_minutes,
                    "session_type": session_type,
                    "status": SessionStatus.PENDING.value,
                    "source": SessionSource.SYSTEM.value,
                }
            )
    return rows
