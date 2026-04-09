from lms_backend.models.study_session import StudySession
from lms_backend.utils.enums import SessionStatus


def build_progress_summary(sessions: list[StudySession]) -> dict[str, int]:
    completed = sum(1 for session in sessions if session.status == SessionStatus.COMPLETED.value)
    skipped = sum(1 for session in sessions if session.status == SessionStatus.SKIPPED.value)
    total = len(sessions)
    pending = total - completed - skipped
    completion_percent = int((completed / total) * 100) if total else 0
    return {
        "total": total,
        "completed": completed,
        "skipped": skipped,
        "pending": pending,
        "completion_percent": completion_percent,
    }
