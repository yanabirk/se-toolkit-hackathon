from pathlib import Path

import httpx

from bot.config import settings


class BackendClientError(RuntimeError):
    pass


class BackendClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.backend_api_key}"}

    async def upsert_telegram_user(self, tg_user: object) -> dict:
        payload = {
            "telegram_user_id": tg_user.id,
            "username": getattr(tg_user, "username", None),
            "first_name": getattr(tg_user, "first_name", None),
            "last_name": getattr(tg_user, "last_name", None),
        }
        return await self._post("/api/v1/telegram-users/upsert", json=payload)

    async def create_study_plan(self, payload: dict) -> dict:
        return await self._post("/api/v1/study-plans", json=payload)

    async def generate_study_plan(self, plan_id: int) -> dict:
        return await self._post(f"/api/v1/study-plans/{plan_id}/generate")

    async def get_user_plans(self, user_id: int) -> list[dict]:
        return await self._get(f"/api/v1/users/{user_id}/study-plans")

    async def get_plan(self, plan_id: int) -> dict:
        return await self._get(f"/api/v1/study-plans/{plan_id}")

    async def get_plan_progress(self, plan_id: int) -> dict:
        return await self._get(f"/api/v1/study-plans/{plan_id}/progress")

    async def get_plan_sessions(self, plan_id: int) -> list[dict]:
        return await self._get(f"/api/v1/study-plans/{plan_id}/sessions")

    async def get_plan_materials(self, plan_id: int) -> list[dict]:
        return await self._get(f"/api/v1/materials/plan/{plan_id}")

    async def upload_text_material(self, payload: dict) -> dict:
        return await self._post("/api/v1/materials/paste-text", json=payload)

    async def upload_file_material(self, user_id: int, study_plan_id: int, file_path: Path, filename: str) -> dict:
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                with file_path.open("rb") as file_obj:
                    response = await client.post(
                        f"{self.base_url}/api/v1/materials/upload",
                        headers=self.headers,
                        data={"user_id": str(user_id), "study_plan_id": str(study_plan_id)},
                        files={"file": (filename, file_obj)},
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                raise BackendClientError(self._extract_error_message(exc.response)) from exc
            except httpx.HTTPError as exc:
                raise BackendClientError(f"Backend request failed: {exc}") from exc

    async def regenerate_study_plan(self, plan_id: int) -> dict:
        return await self._post(f"/api/v1/study-plans/{plan_id}/regenerate")

    async def delete_study_plan(self, plan_id: int) -> dict:
        return await self._delete(f"/api/v1/study-plans/{plan_id}")

    async def complete_session(self, session_id: int) -> dict:
        return await self._patch(f"/api/v1/study-sessions/{session_id}/complete")

    async def skip_session(self, session_id: int) -> dict:
        return await self._patch(f"/api/v1/study-sessions/{session_id}/skip")

    async def _get(self, path: str) -> dict | list[dict]:
        return await self._request("GET", path, timeout=60.0)

    async def _post(self, path: str, json: dict | None = None) -> dict:
        return await self._request("POST", path, json=json, timeout=120.0)

    async def _patch(self, path: str) -> dict:
        return await self._request("PATCH", path, timeout=60.0)

    async def _delete(self, path: str) -> dict:
        return await self._request("DELETE", path, timeout=60.0)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        timeout: float,
    ) -> dict | list[dict]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=self.headers,
                    json=json,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise BackendClientError(self._extract_error_message(exc.response)) from exc
            except httpx.HTTPError as exc:
                raise BackendClientError(f"Backend request failed: {exc}") from exc
            return response.json()

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"Backend returned status {response.status_code}"
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict):
            nested = detail.get("error", {}).get("message")
            if isinstance(nested, str) and nested:
                return nested
        return f"Backend returned status {response.status_code}"
