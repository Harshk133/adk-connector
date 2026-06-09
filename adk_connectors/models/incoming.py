from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class MediaType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VOICE = "voice"
    DOCUMENT = "document"

class IncomingMessage(BaseModel):
    platform: str
    user_id: str
    chat_id: str
    message_id: str
    text: Optional[str] = None
    media_type: MediaType = MediaType.TEXT
    media_url: Optional[str] = None
    file_name: Optional[str] = None
    raw_update: Dict[str, Any] = Field(default_factory=dict)
