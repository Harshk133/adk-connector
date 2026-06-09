from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable
from adk_connectors.models.incoming import IncomingMessage
from adk_connectors.models.outgoing import OutgoingMessage

class BaseAdapter(ABC):
    platform: str

    def __init__(self):
        self.on_message_callback: Optional[Callable[[IncomingMessage], Awaitable[None]]] = None

    def register_message_handler(self, callback: Callable[[IncomingMessage], Awaitable[None]]) -> None:
        self.on_message_callback = callback

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def send_message(self, chat_id: str, message: OutgoingMessage) -> None:
        pass

    @abstractmethod
    async def edit_message(self, chat_id: str, message_id: str, new_content: str) -> None:
        pass

    @abstractmethod
    async def set_typing_indicator(self, chat_id: str) -> None:
        pass
