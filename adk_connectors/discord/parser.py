from typing import Dict, Any, Optional
import discord
from adk_connectors.models.incoming import IncomingMessage, MediaType

class DiscordParser:
    @staticmethod
    def parse_message(message: discord.Message) -> Optional[IncomingMessage]:
        if message.author.bot:
            return None
            
        chat_id = str(message.channel.id)
        user_id = str(message.author.id)
        message_id = str(message.id)
        
        text = message.content
        media_type = MediaType.TEXT
        media_url = None
        file_name = None
        
        if message.attachments:
            attachment = message.attachments[0]
            file_name = attachment.filename
            media_url = attachment.url
            content_type = attachment.content_type or ""
            
            if content_type.startswith("image/"):
                media_type = MediaType.PHOTO
            elif content_type.startswith("audio/"):
                media_type = MediaType.VOICE
            else:
                media_type = MediaType.DOCUMENT
                
        raw_update = {
            "id": message.id,
            "channel_id": message.channel.id,
            "author_id": message.author.id,
            "content": message.content,
            "attachments": [
                {
                    "filename": att.filename,
                    "url": att.url,
                    "content_type": att.content_type
                }
                for att in message.attachments
            ]
        }
        
        return IncomingMessage(
            platform="discord",
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            media_type=media_type,
            media_url=media_url,
            file_name=file_name,
            raw_update=raw_update
        )
