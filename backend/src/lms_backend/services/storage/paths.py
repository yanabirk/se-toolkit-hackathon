from pathlib import Path

from lms_backend.settings import settings


class StoragePaths:
    @staticmethod
    def root() -> Path:
        path = Path(settings.storage_root)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def materials_dir(user_id: int, study_plan_id: int | None) -> Path:
        suffix = str(study_plan_id) if study_plan_id is not None else "unlinked"
        path = StoragePaths.root() / "materials" / str(user_id) / suffix
        path.mkdir(parents=True, exist_ok=True)
        return path
