from typing import Dict, Any, Optional
from adk_connectors.models.incoming import IncomingMessage, MediaType

class TelegramParser:
    @staticmethod
    def parse_update(update: Dict[str, Any]) -> Optional[IncomingMessage]:
        message_data = update.get("message") or update.get("edited_message")
        
        if not message_data:
            return None
            
        chat = message_data.get("chat", {})
        from_user = message_data.get("from", {})
        
        chat_id = str(chat.get("id"))
        user_id = str(from_user.get("id"))
        message_id = str(message_data.get("message_id"))
        
        if not chat_id or not user_id or not message_id:
            return None
            
        text = message_data.get("text")
        media_type = MediaType.TEXT
        file_name = None
        
        if "photo" in message_data:
            media_type = MediaType.PHOTO
            photo_sizes = message_data["photo"]
            if photo_sizes:
                file_name = photo_sizes[-1].get("file_id")
        elif "document" in message_data:
            media_type = MediaType.DOCUMENT
            doc = message_data["document"]
            file_name = doc.get("file_name")
        elif "voice" in message_data:
            media_type = MediaType.VOICE
            voice = message_data["voice"]
            file_name = voice.get("file_id")
            
        return IncomingMessage(
            platform="telegram",
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            media_type=media_type,
            file_name=file_name,
            raw_update=update
        )
