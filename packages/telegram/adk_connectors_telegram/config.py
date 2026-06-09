from pydantic import BaseModel
from typing import Optional

class TelegramConfig(BaseModel):
    token: str
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    poll_interval: float = 1.REMOVED_VALUE  # seconds between poll requests in long polling
