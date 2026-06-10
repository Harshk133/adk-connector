import pytest
from adk_connectors import ResponseFormatter, SessionManager, MemorySessionStorage, SessionConfig, JSONFileSessionStorage, SessionModel
from adk_connectors.telegram import TelegramFormatter, TelegramParser, TelegramConnector


def test_telegram_formatter_markdown():
    text = "Hello **world**, this is *italic* and `code`."
    html_text = TelegramFormatter.markdown_to_html(text)
    assert "<b>world</b>" in html_text
    assert "<b>italic</b>" in html_text
    assert "<code>code</code>" in html_text

def test_telegram_formatter_escaping():
    text = "Hello <script>alert(1)</script> & welcome"
    html_text = TelegramFormatter.markdown_to_html(text)
    assert "&lt;script&gt;" in html_text
    assert "&amp;" in html_text

def test_telegram_formatter_code_blocks():
    text = "Here is some code:\n```python\nprint('hello')\n```"
    html_text = TelegramFormatter.markdown_to_html(text)
    assert "<pre>print(&#x27;hello&#x27;)\n</pre>" in html_text or "<pre>print(&#x27;hello&#x27;)</pre>" in html_text


def test_telegram_parser():
    raw_update = {
        "update_id": 12345,
        "message": {
            "message_id": 999,
            "from": {"id": 111, "first_name": "Test"},
            "chat": {"id": 222, "type": "private"},
            "text": "Hello world"
        }
    }
    parsed = TelegramParser.parse_update(raw_update)
    assert parsed is not None
    assert parsed.platform == "telegram"
    assert parsed.user_id == "111"
    assert parsed.chat_id == "222"
    assert parsed.text == "Hello world"

def test_response_formatter_chunking():
    formatter = ResponseFormatter(max_message_length=10)
    long_text = "abcdef ghijk lmnop"
    chunks = formatter.chunk_text(long_text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 10 for chunk in chunks)

@pytest.mark.asyncio
async def test_session_manager():
    storage = MemorySessionStorage()
    config = SessionConfig(ttl_seconds=1)
    manager = SessionManager(storage, config)
    
    session = await manager.get_or_create("user123", "telegram")
    assert session is not None
    assert session.platform_key == "telegram:user123"
    
    session2 = await manager.get_or_create("user123", "telegram")
    assert session.adk_session_id == session2.adk_session_id

@pytest.mark.asyncio
async def test_session_manager_with_user_mapping():
    storage = MemorySessionStorage()
    config = SessionConfig(ttl_seconds=10, user_mapping={"telegram:12345": "user"})
    manager = SessionManager(storage, config)
    
    session = await manager.get_or_create("12345", "telegram")
    assert session is not None
    assert session.platform_key == "telegram:12345"
    assert session.adk_user_id == "user"

@pytest.mark.asyncio
async def test_json_file_session_storage(tmp_path):
    file_path = str(tmp_path / "sessions.json")
    storage = JSONFileSessionStorage(file_path)
    
    session_model = SessionModel(
        platform_key="telegram:123",
        adk_session_id="session-456",
        adk_user_id="user-789",
        created_at=100.0,
        last_active=105.0,
        platform_metadata={"foo": "bar"}
    )
    
    await storage.set("telegram:123", session_model)
    
    # Load from another storage pointing to same file
    storage2 = JSONFileSessionStorage(file_path)
    loaded = await storage2.get("telegram:123")
    assert loaded is not None
    assert loaded.adk_session_id == "session-456"
    assert loaded.adk_user_id == "user-789"
    assert loaded.platform_metadata == {"foo": "bar"}

@pytest.mark.asyncio
async def test_session_management_across_device_auto_init(tmp_path):
    import sys
    from adk_connectors import ConnectorManager
    from google.adk.sessions.sqlite_session_service import SqliteSessionService
    from adk_connectors.storage.json_file import JSONFileSessionStorage
    from google.adk.agents.llm_agent import Agent
    
    agent = Agent(name="test_agent", model="gemini-2.0-flash")
    
    class MockMain:
        __file__ = str(tmp_path / "run_agent.py")
        
    sys.modules['__main__'] = MockMain
    
    manager = ConnectorManager(
        agent=agent,
        session_management_across_device=True,
        dev_user_id="123456"
    )
    
    assert isinstance(manager.adk_session_service, SqliteSessionService)
    assert isinstance(manager.session_manager.storage, JSONFileSessionStorage)
    assert manager.config.session.user_mapping["telegram:123456"] == "user"


@pytest.mark.asyncio
async def test_sub_agent_event_handling():
    from adk_connectors import ConnectorManager, BaseAdapter, IncomingMessage, OutgoingMessage
    from google.adk.agents.llm_agent import Agent
    from google.adk.events.event import Event
    from google.genai import types
    
    agent = Agent(name="test_agent", model="gemini-2.0-flash")
    
    class MockAdapter(BaseAdapter):
        platform = "telegram"
        def __init__(self):
            super().__init__()
            self.sent_messages = []
            self.edited_messages = []
            
        async def start(self) -> None:
            pass
            
        async def stop(self) -> None:
            pass
            
        async def send_message(self, chat_id: str, message: OutgoingMessage):
            self.sent_messages.append(message)
            class MockResponse:
                message_id = len(self.sent_messages)
            return MockResponse()
            
        async def edit_message(self, chat_id: str, message_id: str, new_content: str):
            self.edited_messages.append((message_id, new_content))
            return {}
            
        async def set_typing_indicator(self, chat_id: str) -> None:
            pass
            
    adapter = MockAdapter()
    manager = ConnectorManager(agent=agent)
    manager.register_adapter(adapter)
    
    # Mock runner's run_async
    class MockRunner:
        async def run_async(self, user_id, session_id, new_message):
            # 1. Yield sub-agent partial event
            event1 = Event(
                branch="sub_agent_branch",
                partial=True,
                content=types.Content(parts=[types.Part.from_text(text="sub-agent partial")])
            )
            yield event1
            
            # 2. Yield sub-agent final event
            event2 = Event(
                branch="sub_agent_branch",
                partial=False,
                content=types.Content(parts=[types.Part.from_text(text="sub-agent final response")])
            )
            yield event2
            
            # 3. Yield parent agent partial event
            event3 = Event(
                branch=None,
                partial=True,
                content=types.Content(parts=[types.Part.from_text(text="parent partial")])
            )
            yield event3
            
            # 4. Yield parent agent final event
            event4 = Event(
                branch=None,
                partial=False,
                content=types.Content(parts=[types.Part.from_text(text="parent final response")])
            )
            yield event4
            
    manager._runner = MockRunner()
    
    incoming = IncomingMessage(
        message_id="msg123",
        platform="telegram",
        chat_id="chat123",
        user_id="user456",
        text="hello"
    )
    
    await manager.handle_incoming_message(incoming)
    
    # Since streaming is enabled by default, the parent's partial is streamed,
    # then edited with the parent's final response.
    # The sub-agent's events should be completely ignored in message delivery.
    assert len(adapter.sent_messages) == 1
    assert adapter.sent_messages[0].text == "parent partial"
    
    assert len(adapter.edited_messages) == 1
    assert adapter.edited_messages[0] == ("1", "parent final response")
