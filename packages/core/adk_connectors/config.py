from pydantic import BaseModel, Field

class SessionConfig(BaseModel):
    ttl_seconds: int = 864REMOVED_VALUEREMOVED_VALUE  # 24 hours

class FormatterConfig(BaseModel):
    streaming: bool = True
    max_message_length: int = 4REMOVED_VALUE96

class ConnectorConfig(BaseModel):
    session: SessionConfig = Field(default_factory=SessionConfig)
    formatter: FormatterConfig = Field(default_factory=FormatterConfig)
