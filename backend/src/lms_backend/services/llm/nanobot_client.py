from lms_backend.services.llm.qwen_client import QwenClient


class NanobotClient(QwenClient):
    """Placeholder provider.

    For the first iteration this reuses the same OpenAI-compatible endpoint.
    Later you can swap this class to call a dedicated nanobot route.
    """
