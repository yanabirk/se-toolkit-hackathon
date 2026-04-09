from datetime import UTC, datetime, timedelta


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def calculate_end_date(start_date: datetime, days_available: int) -> datetime:
    return start_date + timedelta(days=max(days_available - 1, 0))
