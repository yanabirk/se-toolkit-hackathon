from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.db.llm_requests import create_llm_request
from lms_backend.db.materials import list_materials_for_plan
from lms_backend.db.plan_topics import list_plan_topics, replace_plan_topics
from lms_backend.db.study_plans import activate_study_plan
from lms_backend.db.study_sessions import replace_sessions
from lms_backend.models.llm_request import LlmRequest
from lms_backend.models.study_plan import StudyPlan
from lms_backend.services.llm.nanobot_client import NanobotClient
from lms_backend.services.llm.qwen_client import QwenClient
from lms_backend.services.planner.schedule_builder import build_skeleton
from lms_backend.services.planner.session_refiner import apply_topics_to_skeleton
from lms_backend.services.planner.topic_extractor import (
    detect_study_preference,
    extract_topics_fallback,
)
from lms_backend.settings import settings
from lms_backend.utils.enums import LlmRequestStatus


GENERIC_TITLES = {"study session", "session", "session title"}
GENERIC_DESCRIPTIONS = {
    "review material",
    "study theory",
    "practice problems",
    "core study block",
}


def _get_llm_client() -> QwenClient | NanobotClient:
    if settings.llm_provider == "nanobot":
        return NanobotClient()
    return QwenClient()


def _normalize_text(value: object) -> str:
    return " ".join(str(value).split()).strip()


def _title_is_useful(title: object) -> bool:
    normalized = _normalize_text(title).lower()
    if not normalized:
        return False
    if normalized in GENERIC_TITLES:
        return False
    if normalized.startswith("session ") and normalized[8:].isdigit():
        return False
    return len(normalized) >= 6


def _description_is_useful(description: object) -> bool:
    normalized = _normalize_text(description).lower()
    if not normalized:
        return False
    if normalized in GENERIC_DESCRIPTIONS:
        return False
    return len(normalized.split()) >= 6


def _merge_refined_sessions(
    base_sessions: list[dict[str, object]],
    refined_sessions: list[dict[str, object]],
) -> list[dict[str, object]]:
    refined_by_slot = {
        (int(session["day_number"]), int(session["session_order"])): session
        for session in refined_sessions
    }
    base_slots = {
        (int(session["day_number"]), int(session["session_order"])) for session in base_sessions
    }
    if set(refined_by_slot) != base_slots:
        raise ValueError("LLM returned session slots that do not match the deterministic plan")

    merged: list[dict[str, object]] = []
    for session in base_sessions:
        slot = (int(session["day_number"]), int(session["session_order"]))
        refined = refined_by_slot[slot]
        merged.append(
            {
                **session,
                "title": (
                    _normalize_text(refined.get("title"))
                    if _title_is_useful(refined.get("title"))
                    else str(session["title"])
                ),
                "description": (
                    _normalize_text(refined.get("description"))
                    if _description_is_useful(refined.get("description"))
                    else str(session["description"])
                ),
                "source": refined.get("source", session["source"]),
            }
        )
    return merged


async def analyze_materials_and_topics(
    session: AsyncSession, plan: StudyPlan
) -> list[str]:
    materials = await list_materials_for_plan(session, plan.id or 0)
    materials_text = "\n\n".join(material.extracted_text or "" for material in materials).strip()
    topics = extract_topics_fallback(plan.exam_name, materials_text)
    if materials_text:
        llm_client = _get_llm_client()
        try:
            topics = await llm_client.extract_topics(plan.exam_name, materials_text)
            await create_llm_request(
                session,
                LlmRequest(
                    study_plan_id=plan.id,
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    request_payload={"action": "extract_topics"},
                    response_payload={"topics": topics},
                    status=LlmRequestStatus.SUCCESS.value,
                ),
            )
        except Exception as exc:
            await create_llm_request(
                session,
                LlmRequest(
                    study_plan_id=plan.id,
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    request_payload={"action": "extract_topics"},
                    response_payload={"error": str(exc)},
                    status=LlmRequestStatus.FAILED.value,
                ),
            )
    await replace_plan_topics(session, plan.id or 0, topics, source="llm" if materials_text else "fallback")
    return topics


async def generate_plan(session: AsyncSession, plan: StudyPlan) -> list[dict[str, object]]:
    skeleton = build_skeleton(plan.days_available, plan.hours_per_day)
    materials = await list_materials_for_plan(session, plan.id or 0)
    materials_text = "\n\n".join(material.extracted_text or "" for material in materials).strip()
    preferred_mode = detect_study_preference(materials_text)
    plan_topics = await list_plan_topics(session, plan.id or 0)
    topics = [topic.topic_name for topic in plan_topics]
    if not topics:
        topics = await analyze_materials_and_topics(session, plan)
    sessions = apply_topics_to_skeleton(
        skeleton,
        topics,
        preferred_mode=preferred_mode,
        exam_name=plan.exam_name,
    )

    llm_client = _get_llm_client()
    try:
        refined = await llm_client.refine_sessions(
            exam_name=plan.exam_name,
            days_available=plan.days_available,
            hours_per_day=plan.hours_per_day,
            topics=topics,
            sessions=sessions,
            materials_text=materials_text,
            preferred_mode=preferred_mode,
        )
        sessions = _merge_refined_sessions(sessions, refined)
        await create_llm_request(
            session,
            LlmRequest(
                study_plan_id=plan.id,
                provider=settings.llm_provider,
                model=settings.llm_model,
                request_payload={"action": "refine_sessions"},
                response_payload={"sessions_count": len(sessions)},
                status=LlmRequestStatus.SUCCESS.value,
            ),
        )
    except Exception as exc:
        await create_llm_request(
            session,
            LlmRequest(
                study_plan_id=plan.id,
                provider=settings.llm_provider,
                model=settings.llm_model,
                request_payload={"action": "refine_sessions"},
                response_payload={"error": str(exc)},
                status=LlmRequestStatus.FAILED.value,
            ),
        )

    await replace_sessions(session, plan.id or 0, sessions)
    await activate_study_plan(session, plan)
    return sessions
