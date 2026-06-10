# Monkeypatch ADK BaseAgent to allow duplicate parent assignment under double-import cycles (e.g. runpy python -m)
try:
    from google.adk.agents.base_agent import BaseAgent
    def _patched_set_parent(self) -> BaseAgent:
        for sub_agent in self.sub_agents:
            sub_agent.parent_agent = self
        return self
    BaseAgent._BaseAgent__set_parent_agent_for_sub_agents = _patched_set_parent
except Exception:
    pass

from adk_connectors.config import ConnectorConfig, SessionConfig, FormatterConfig
from adk_connectors.base_adapter import BaseAdapter
from adk_connectors.connector_manager import ConnectorManager
from adk_connectors.models.incoming import IncomingMessage, MediaType
from adk_connectors.models.outgoing import OutgoingMessage, InlineButton
from adk_connectors.models.session import SessionModel
from adk_connectors.storage.base import SessionStorage
from adk_connectors.storage.memory import MemorySessionStorage
from adk_connectors.storage.json_file import JSONFileSessionStorage
from adk_connectors.event_router import EventRouter
from adk_connectors.response_formatter import ResponseFormatter
from adk_connectors.session_manager import SessionManager

__all__ = [
    "ConnectorConfig",
    "SessionConfig",
    "FormatterConfig",
    "BaseAdapter",
    "ConnectorManager",
    "IncomingMessage",
    "MediaType",
    "OutgoingMessage",
    "InlineButton",
    "SessionModel",
    "SessionStorage",
    "MemorySessionStorage",
    "JSONFileSessionStorage",
    "EventRouter",
    "ResponseFormatter",
    "SessionManager",
]
