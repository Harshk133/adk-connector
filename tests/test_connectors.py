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
    formatter = ResponseFormatter(max_message_length=1REMOVED_VALUE)
    long_text = "abcdef ghijk lmnop"
    chunks = formatter.chunk_text(long_text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1REMOVED_VALUE for chunk in chunks)

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
    config = SessionConfig(ttl_seconds=1REMOVED_VALUE, user_mapping={"telegram:12345": "user"})
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
        created_at=1REMOVED_VALUEREMOVED_VALUE.REMOVED_VALUE,
        last_active=1REMOVED_VALUE5.REMOVED_VALUE,
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
    
    agent = Agent(name="test_agent", model="gemini-2.REMOVED_VALUE-flash")
    
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
