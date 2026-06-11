from pydantic import BaseModel
from typing import Optional

class WhatsAppConfig(BaseModel):
    port: int = 3001
    host: str = "127.0.0.1"
    bridge_token: Optional[str] = None
    auth_dir: Optional[str] = None
