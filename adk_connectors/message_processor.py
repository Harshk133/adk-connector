from typing import Any
from adk_connectors.models.incoming import IncomingMessage, MediaType

try:
    from google.genai import types as genai_types
except ImportError:
    genai_types = None

class MessageProcessor:
    def __init__(self):
        pass

    async def process(self, message: IncomingMessage) -> Any:
        text = message.text or ""
        
        if message.media_type == MediaType.PHOTO:
            text = f"[Photo] {text}" if text else "[Photo]"
        elif message.media_type == MediaType.DOCUMENT:
            name = message.file_name or "unnamed"
            text = f"[Document: {name}] {text}" if text else f"[Document: {name}]"
        elif message.media_type == MediaType.VOICE:
            text = f"[Voice Message] {text}" if text else "[Voice Message]"

        if genai_types is not None:
            return genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=text)]
            )
        else:
            return text
