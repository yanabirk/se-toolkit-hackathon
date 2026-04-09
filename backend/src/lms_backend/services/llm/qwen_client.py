import logging

import httpx

from lms_backend.settings import settings
from lms_backend.services.llm.prompts import build_refine_sessions_prompt, build_topics_prompt
from lms_backend.services.llm.serializers import extract_json
from lms_backend.services.llm.validators import validate_sessions, validate_topics

logger = logging.getLogger(__name__)


class QwenClient:
    async def healthcheck(self) -> dict[str, object]:
        headers: dict[str, str] = {}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        async with httpx.AsyncClient(timeout=min(settings.llm_timeout_seconds, 10.0)) as client:
            response = await client.get(
                f"{settings.llm_base_url}/models",
                headers=headers,
            )
            response.raise_for_status()
        data = response.json()
        models = data.get("data", []) if isinstance(data, dict) else []
        return {
            "status": "ok",
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "models_available": len(models) if isinstance(models, list) else 0,
        }

    async def _chat(self, prompt: str) -> str:
        headers: dict[str, str] = {}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])

    async def extract_topics(self, exam_name: str, materials_text: str) -> list[str]:
        prompt = build_topics_prompt(exam_name, materials_text)
        raw = await self._chat(prompt)
        return validate_topics(extract_json(raw))

    async def refine_sessions(
        self,
        exam_name: str,
        days_available: int,
        hours_per_day: float,
        topics: list[str],
        sessions: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        prompt = build_refine_sessions_prompt(
            exam_name=exam_name,
            days_available=days_available,
            hours_per_day=hours_per_day,
            topics=topics,
            sessions=sessions,
        )
        raw = await self._chat(prompt)
        return validate_sessions(extract_json(raw))
