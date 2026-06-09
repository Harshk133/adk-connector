from pydantic import BaseModel, Field
from typing import Dict, Any

class SessionModel(BaseModel):
    platform_key: str  # e.g., "telegram:123456789"
    adk_session_id: str
    adk_user_id: str
    created_at: float
    last_active: float
    platform_metadata: Dict[str, Any] = Field(default_factory=dict)
