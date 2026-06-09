import os
import json
import logging
from typing import Optional, Dict
from adk_connectors.storage.base import SessionStorage
from adk_connectors.models.session import SessionModel

logger = logging.getLogger("adk_connectors.storage")

class JSONFileSessionStorage(SessionStorage):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._storage: Dict[str, SessionModel] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.file_path):
            self._storage = {}
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._storage = {
                    k: SessionModel(**v) for k, v in data.items()
                }
        except Exception as e:
            logger.error(f"Failed to load sessions from {self.file_path}: {e}")
            self._storage = {}

    def _save(self) -> None:
        try:
            dir_name = os.path.dirname(self.file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v.model_dump() for k, v in self._storage.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save sessions to {self.file_path}: {e}")

    async def get(self, platform_key: str) -> Optional[SessionModel]:
        return self._storage.get(platform_key)

    async def set(self, platform_key: str, session: SessionModel) -> None:
        self._storage[platform_key] = session
        self._save()

    async def delete(self, platform_key: str) -> None:
        if platform_key in self._storage:
            del self._storage[platform_key]
            self._save()
