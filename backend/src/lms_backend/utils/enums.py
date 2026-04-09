from enum import StrEnum


class StudyPlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class GenerationMode(StrEnum):
    DETERMINISTIC = "deterministic"
    HYBRID = "hybrid"
    LLM = "llm"


class SessionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class SessionType(StrEnum):
    STUDY = "study"
    REVISION = "revision"
    PRACTICE = "practice"
    MOCK = "mock"


class SessionSource(StrEnum):
    SYSTEM = "system"
    LLM = "llm"


class MaterialType(StrEnum):
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"


class LlmRequestStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
