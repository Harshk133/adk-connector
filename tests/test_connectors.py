import pytest
from adk_connectors import ResponseFormatter, SessionManager, MemorySessionStorage, SessionConfig
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
