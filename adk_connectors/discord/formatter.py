import discord
from typing import Dict, Any, List
from adk_connectors.models.outgoing import OutgoingMessage, InlineButton

class DiscordFormatter:
    @staticmethod
    def format_inline_keyboard(keyboard: List[List[InlineButton]]) -> discord.ui.View:
        view = discord.ui.View()
        for row_idx, row in enumerate(keyboard):
            for btn in row:
                if btn.url:
                    discord_btn = discord.ui.Button(
                        label=btn.text,
                        url=btn.url,
                        row=row_idx
                    )
                else:
                    custom_id = btn.callback_data or btn.text
                    discord_btn = discord.ui.Button(
                        label=btn.text,
                        custom_id=custom_id,
                        row=row_idx
                    )
                view.add_item(discord_btn)
        return view

    @classmethod
    def to_api_payload(cls, message: OutgoingMessage) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "content": message.text
        }
        
        if message.inline_keyboard:
            payload["view"] = cls.format_inline_keyboard(message.inline_keyboard)
            
        return payload
