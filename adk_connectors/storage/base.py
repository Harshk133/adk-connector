from abc import ABC, abstractmethod
from typing import Optional
from adk_connectors.models.session import SessionModel

class SessionStorage(ABC):
    @abstractmethod
    async def get(self, platform_key: str) -> Optional[SessionModel]:
        pass

    @abstractmethod
    async def set(self, platform_key: str, session: SessionModel) -> None:
        pass

    @abstractmethod
    async def delete(self, platform_key: str) -> None:
        pass
