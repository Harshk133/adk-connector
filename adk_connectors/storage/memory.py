from typing import Dict, Optional
from adk_connectors.storage.base import SessionStorage
from adk_connectors.models.session import SessionModel

class MemorySessionStorage(SessionStorage):
    def __init__(self):
        self._storage: Dict[str, SessionModel] = {}

    async def get(self, platform_key: str) -> Optional[SessionModel]:
        return self._storage.get(platform_key)

    async def set(self, platform_key: str, session: SessionModel) -> None:
        self._storage[platform_key] = session

    async def delete(self, platform_key: str) -> None:
        if platform_key in self._storage:
            del self._storage[platform_key]
