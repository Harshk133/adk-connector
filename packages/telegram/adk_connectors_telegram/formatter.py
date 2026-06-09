import html
import re
from typing import Dict, Any, List
from adk_connectors.models.outgoing import OutgoingMessage, InlineButton

class TelegramFormatter:
    @staticmethod
    def markdown_to_html(text: str) -> str:
        # Escape HTML entities first to avoid parsing conflicts
        escaped = html.escape(text)
        
        # Preformatted blocks (```code```)
        escaped = re.sub(
            r'```(?:[a-zA-ZREMOVED_VALUE-9_-]+\n)?(.*?)```',
            r'<pre>\1</pre>',
            escaped,
            flags=re.DOTALL
        )
        
        # Inline code (`code`)
        escaped = re.sub(
            r'`(.*?)`',
            r'<code>\1</code>',
            escaped
        )
        
        # Bold (**bold** or *bold*)
        escaped = re.sub(
            r'\*\*(.*?)\*\*',
            r'<b>\1</b>',
            escaped
        )
        escaped = re.sub(
            r'\*(.*?)\*',
            r'<b>\1</b>',
            escaped
        )
        
        # Italic (__italic__ or _italic_)
        escaped = re.sub(
            r'__(.*?)__',
            r'<i>\1</i>',
            escaped
        )
        escaped = re.sub(
            r'_(.*?)_',
            r'<i>\1</i>',
            escaped
        )
        
        return escaped

    @staticmethod
    def format_inline_keyboard(keyboard: List[List[InlineButton]]) -> Dict[str, Any]:
        buttons_json = []
        for row in keyboard:
            row_json = []
            for btn in row:
                btn_data = {"text": btn.text}
                if btn.url:
                    btn_data["url"] = btn.url
                elif btn.callback_data:
                    btn_data["callback_data"] = btn.callback_data
                else:
                    btn_data["callback_data"] = btn.text
                row_json.append(btn_data)
            buttons_json.append(row_json)
        return {"inline_keyboard": buttons_json}

    @classmethod
    def to_api_payload(cls, message: OutgoingMessage) -> Dict[str, Any]:
        text_html = cls.markdown_to_html(message.text)
        
        payload: Dict[str, Any] = {
            "chat_id": message.chat_id,
            "text": text_html,
            "parse_mode": "HTML"
        }
        
        if message.reply_to_message_id:
            payload["reply_to_message_id"] = int(message.reply_to_message_id)
            
        if message.inline_keyboard:
            payload["reply_markup"] = cls.format_inline_keyboard(message.inline_keyboard)
            
        return payload
