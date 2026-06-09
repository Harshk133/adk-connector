import time
import uuid
import asyncio
from typing import Optional, Dict
from contextlib import asynccontextmanager
from adk_connectors.storage.base import SessionStorage
from adk_connectors.models.session import SessionModel
from adk_connectors.config import SessionConfig

class SessionManager:
    def __init__(self, storage: SessionStorage, config: SessionConfig):
        self.storage = storage
        self.config = config
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get_or_create(self, platform_id: str, platform: str) -> SessionModel:
        platform_key = f"{platform}:{platform_id}"
        session = await self.storage.get(platform_key)
        now = time.time()
        
        if session is not None:
            # Check for expiry
            if now - session.last_active > self.config.ttl_seconds:
                session = self._create_new_session(platform_key, platform_id)
                await self.storage.set(platform_key, session)
            else:
                session.last_active = now
                await self.storage.set(platform_key, session)
        else:
            session = self._create_new_session(platform_key, platform_id)
            await self.storage.set(platform_key, session)
            
        return session


    def _create_new_session(self, platform_key: str, platform_id: str) -> SessionModel:
        now = time.time()
        adk_session_id = str(uuid.uuid4())
        
        adk_user_id = platform_key
        if self.config.user_mapping:
            if platform_key in self.config.user_mapping:
                adk_user_id = self.config.user_mapping[platform_key]
            elif platform_id in self.config.user_mapping:
                adk_user_id = self.config.user_mapping[platform_id]
        
        session = SessionModel(
            platform_key=platform_key,
            adk_session_id=adk_session_id,
            adk_user_id=adk_user_id,
            created_at=now,
            last_active=now,
            platform_metadata={}
        )
        return session

    async def update(self, session: SessionModel) -> None:
        session.last_active = time.time()
        await self.storage.set(session.platform_key, session)

    async def destroy(self, platform_id: str, platform: str) -> None:
        platform_key = f"{platform}:{platform_id}"
        await self.storage.delete(platform_key)

    @asynccontextmanager
    async def lock(self, platform_key: str):
        if platform_key not in self._locks:
            self._locks[platform_key] = asyncio.Lock()
        async with self._locks[platform_key]:
            try:
                yield
            finally:
                # Clean up lock object if no other coroutines are waiting
                if not self._locks[platform_key].locked():
                    self._locks.pop(platform_key, None)
