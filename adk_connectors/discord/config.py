from pydantic import BaseModel
from typing import Optional

class DiscordConfig(BaseModel):
    token: str
