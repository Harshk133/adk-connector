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


def test_discord_formatter():
    from adk_connectors.discord import DiscordFormatter
    from adk_connectors.models.outgoing import OutgoingMessage, InlineButton
    
    # Text only
    msg = OutgoingMessage(chat_id="123", text="Hello world")
    payload = DiscordFormatter.to_api_payload(msg)
    assert payload["content"] == "Hello world"
    assert "view" not in payload
    
    # Text with inline keyboard
    msg_keyboard = OutgoingMessage(
        chat_id="123",
        text="Choose:",
        inline_keyboard=[[InlineButton(text="Click me", callback_data="btn_click")]]
    )
    payload_keyboard = DiscordFormatter.to_api_payload(msg_keyboard)
    assert payload_keyboard["content"] == "Choose:"
    assert "view" in payload_keyboard
    view = payload_keyboard["view"]
    assert len(view.children) == 1
    assert view.children[0].label == "Click me"
    assert view.children[0].custom_id == "btn_click"


def test_discord_parser():
    from adk_connectors.discord import DiscordParser
    from unittest.mock import MagicMock
    
    # Mock discord.Message
    mock_author = MagicMock()
    mock_author.id = 456
    mock_author.bot = False
    
    mock_channel = MagicMock()
    mock_channel.id = 789
    
    mock_message = MagicMock()
    mock_message.id = 123
    mock_message.author = mock_author
    mock_message.channel = mock_channel
    mock_message.content = "Test message"
    mock_message.attachments = []
    
    parsed = DiscordParser.parse_message(mock_message)
    assert parsed is not None
    assert parsed.platform == "discord"
    assert parsed.user_id == "456"
    assert parsed.chat_id == "789"
    assert parsed.message_id == "123"
    assert parsed.text == "Test message"


def test_whatsapp_config():
    from adk_connectors.whatsapp.config import WhatsAppConfig
    cfg = WhatsAppConfig()
    assert cfg.port == 3001
    assert cfg.host == "127.0.0.1"
    assert cfg.bridge_token is None

def test_whatsapp_connector_alias():
    from adk_connectors.whatsapp.connector import WhatsAppConnector, WhatsAppWebConnector
    assert WhatsAppConnector is WhatsAppWebConnector

@pytest.mark.asyncio
async def test_whatsapp_adapter_mock():
    from adk_connectors.whatsapp.config import WhatsAppConfig
    from adk_connectors.whatsapp.adapter import WhatsAppAdapter
    from unittest.mock import MagicMock, AsyncMock
    import asyncio
    
    cfg = WhatsAppConfig(port=9999, host="127.0.0.1", bridge_token="test_token")
    adapter = WhatsAppAdapter(cfg)
    
    from unittest.mock import patch
    
    with patch("subprocess.Popen") as mock_popen, \
         patch("websockets.connect", new_callable=AsyncMock) as mock_connect, \
         patch("shutil.which", return_value="/usr/bin/node") as mock_which, \
         patch("os.path.exists", return_value=True):
         
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        
        await adapter.start()
        
        assert adapter._is_running is True
        assert adapter.config.bridge_token == "test_token"
        
        await adapter.stop()


@pytest.mark.asyncio
async def test_connector_manager_webhook_flow():
    from adk_connectors import ConnectorManager, ConnectorConfig, BaseAdapter, IncomingMessage
    from unittest.mock import AsyncMock, patch, MagicMock
    from google.adk.agents.llm_agent import Agent
    
    agent = Agent(name="test_agent", model="gemini-2.0-flash")
    config = ConnectorConfig()
    config.tunnel.enabled = True
    config.tunnel.port = 18080
    config.tunnel.host = "127.0.0.1"
    
    manager = ConnectorManager(agent=agent, config=config)
    
    class MockWebhookAdapter(BaseAdapter):
        platform = "mockplatform"
        def __init__(self):
            super().__init__()
            self.config = MagicMock()
            self.config.webhook_url = None
            self.start_called = False
            self.stop_called = False
            
        async def start(self):
            self.start_called = True
            
        async def stop(self):
            self.stop_called = True
            
        async def send_message(self, chat_id, message):
            pass
            
        async def edit_message(self, chat_id, message_id, new_content):
            pass
            
        async def set_typing_indicator(self, chat_id):
            pass
            
        def parse_webhook_payload(self, payload, headers=None):
            return IncomingMessage(
                platform="mockplatform",
                user_id="user123",
                chat_id="chat456",
                message_id="msg789",
                text=payload.get("text")
            )
            
    adapter = MockWebhookAdapter()
    manager.register_adapter(adapter)
    
    mock_tunnel = AsyncMock()
    mock_tunnel.start.return_value = "https://mock.trycloudflare.com"
    
    with patch("adk_connectors.tunnel.CloudflareTunnel", return_value=mock_tunnel):
        await manager.start()
        
        assert adapter.start_called is True
        assert adapter.config.webhook_url == "https://mock.trycloudflare.com/webhooks/mockplatform"
        
        import httpx
        async with httpx.AsyncClient() as client:
            res = await client.post("http://127.0.0.1:18080/webhooks/mockplatform", json={"text": "hello webhook"})
            assert res.status_code == 200
            assert res.text == "OK"
            
        await manager.stop()
        assert adapter.stop_called is True
        mock_tunnel.stop.assert_called_once()


def test_find_free_port():
    import socket
    from adk_connectors import ConnectorManager
    from google.adk.agents.llm_agent import Agent
    
    agent = Agent(name="test_agent", model="gemini-2.0-flash")
    manager = ConnectorManager(agent=agent)
    
    # Bind a port manually
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    bound_port = s.getsockname()[1]
    
    # Find a free port starting from bound_port
    free_port = manager._find_free_port(bound_port)
    assert free_port != bound_port
    assert free_port > bound_port
    
    s.close()


def test_multi_platform_connector_registration():
    import pytest
    from adk_connectors import ConnectorManager, BaseAdapter
    from adk_connectors.telegram import TelegramConnector
    from adk_connectors.discord import DiscordConnector
    from google.adk.agents.llm_agent import Agent

    agent = Agent(name="test_agent", model="gemini-2.0-flash")

    # 1. Verify connector raises error if start is called when agent is None
    telegram_conn_no_agent = TelegramConnector(token="mock_telegram_token")
    assert telegram_conn_no_agent.manager is None
    with pytest.raises(ValueError, match="Cannot start connector directly because no agent was provided"):
        telegram_conn_no_agent.start()

    discord_conn_no_agent = DiscordConnector(token="mock_discord_token")
    assert discord_conn_no_agent.manager is None
    with pytest.raises(ValueError, match="Cannot start connector directly because no agent was provided"):
        discord_conn_no_agent.start()

    # 2. Verify ConnectorManager raises error when _get_runner is called without an agent
    manager_no_agent = ConnectorManager(platforms=[telegram_conn_no_agent])
    with pytest.raises(ValueError, match="Agent must be set on ConnectorManager before running."):
        manager_no_agent._get_runner()

    # 3. Verify ConnectorManager accepts platforms, registers their adapters, and binds connectors
    manager = ConnectorManager(
        agent=agent,
        platforms=[
            telegram_conn_no_agent,
            discord_conn_no_agent
        ]
    )

    # Both adapters should be registered
    assert len(manager.adapters) == 2
    assert any(a.platform == "telegram" for a in manager.adapters)
    assert any(a.platform == "discord" for a in manager.adapters)

    # Connector manager attributes should be updated to point to the central manager
    assert telegram_conn_no_agent.manager is manager
    assert discord_conn_no_agent.manager is manager

    # 4. Verify registering a raw adapter directly works
    class MockRawAdapter(BaseAdapter):
        platform = "mock_raw"
        async def start(self): pass
        async def stop(self): pass
        async def send_message(self, chat_id, message): pass
        async def edit_message(self, chat_id, message_id, new_content): pass
        async def set_typing_indicator(self, chat_id): pass

    raw_adapter = MockRawAdapter()
    manager.register_platform(raw_adapter)
    assert len(manager.adapters) == 3
    assert any(a.platform == "mock_raw" for a in manager.adapters)

    # 5. Verify type error is raised when registering invalid platform
    with pytest.raises(TypeError, match="Expected a platform connector wrapping an adapter or a BaseAdapter subclass"):
        manager.register_platform("invalid_platform_type")





