from pydantic import BaseModel
from typing import Optional, List

class InlineButton(BaseModel):
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None

class OutgoingMessage(BaseModel):
    chat_id: str
    text: str
    reply_to_message_id: Optional[str] = None
    inline_keyboard: Optional[List[List[InlineButton]]] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # photo, document, etc.
