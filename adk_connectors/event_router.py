from typing import Dict, List, Callable, Awaitable
from adk_connectors.models.incoming import IncomingMessage, MediaType

class EventRouter:
    def __init__(self):
        self._handlers: Dict[MediaType, List[Callable[[IncomingMessage], Awaitable[None]]]] = {
            t: [] for t in MediaType
        }
        self._global_middlewares: List[Callable[[IncomingMessage, Callable[[], Awaitable[None]]], Awaitable[None]]] = []

    def register_handler(self, media_type: MediaType, handler: Callable[[IncomingMessage], Awaitable[None]]) -> None:
        if media_type not in self._handlers:
            self._handlers[media_type] = []
        self._handlers[media_type].append(handler)

    def use_middleware(self, middleware: Callable[[IncomingMessage, Callable[[], Awaitable[None]]], Awaitable[None]]) -> None:
        self._global_middlewares.append(middleware)

    async def dispatch(self, event: IncomingMessage) -> None:
        handlers = self._handlers.get(event.media_type, [])
        
        async def run_handlers():
            for handler in handlers:
                await handler(event)

        async def run_chain(index: int):
            if index < len(self._global_middlewares):
                async def next_step():
                    await run_chain(index + 1)
                await self._global_middlewares[index](event, next_step)
            else:
                await run_handlers()

        await run_chain(0)
