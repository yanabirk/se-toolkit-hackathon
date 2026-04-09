from typing import Protocol


class BaseLlmClient(Protocol):
    async def healthcheck(self) -> dict[str, object]: ...

    async def extract_topics(self, exam_name: str, materials_text: str) -> list[str]: ...

    async def refine_sessions(
        self,
        exam_name: str,
        days_available: int,
        hours_per_day: float,
        topics: list[str],
        sessions: list[dict[str, object]],
    ) -> list[dict[str, object]]: ...
