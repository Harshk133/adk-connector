from pydantic import BaseModel, Field
from typing import Optional

class SessionConfig(BaseModel):
    ttl_seconds: int = 86400  # 24 hours
    user_mapping: dict[str, str] = Field(default_factory=dict)

class FormatterConfig(BaseModel):
    streaming: bool = True
    max_message_length: int = 4096

class TunnelConfig(BaseModel):
    enabled: bool = False
    port: int = 8000
    host: str = "127.0.0.1"
    provider: str = "cloudflare"  # "cloudflare" or "ngrok"
    authtoken: Optional[str] = None

class ConnectorConfig(BaseModel):
    session: SessionConfig = Field(default_factory=SessionConfig)
    formatter: FormatterConfig = Field(default_factory=FormatterConfig)
    tunnel: TunnelConfig = Field(default_factory=TunnelConfig)

