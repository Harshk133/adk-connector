from typing import List
from adk_connectors.models.outgoing import OutgoingMessage

class ResponseFormatter:
    def __init__(self, max_message_length: int = 4096):
        self.max_message_length = max_message_length

    def chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.max_message_length:
            return [text]
        
        chunks = []
        while text:
            if len(text) <= self.max_message_length:
                chunks.append(text)
                break
            
            # Split at the last newline within the limit, if possible
            split_idx = text.rfind('\n', 0, self.max_message_length)
            if split_idx == -1:
                # If no newline, split at space
                split_idx = text.rfind(' ', 0, self.max_message_length)
            
            if split_idx == -1:
                # Force split at maximum length
                split_idx = self.max_message_length
                
            chunks.append(text[:split_idx])
            text = text[split_idx:].lstrip()
            
        return chunks

    def format_response(self, chat_id: str, text: str) -> List[OutgoingMessage]:
        chunks = self.chunk_text(text)
        return [OutgoingMessage(chat_id=chat_id, text=chunk) for chunk in chunks]
