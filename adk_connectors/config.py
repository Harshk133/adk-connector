from pydantic import BaseModel, Field

class SessionConfig(BaseModel):
    ttl_seconds: int = 86400  # 24 hours
    user_mapping: dict[str, str] = Field(default_factory=dict)

class FormatterConfig(BaseModel):
    streaming: bool = True
    max_message_length: int = 4096

class ConnectorConfig(BaseModel):
    session: SessionConfig = Field(default_factory=SessionConfig)
    formatter: FormatterConfig = Field(default_factory=FormatterConfig)
