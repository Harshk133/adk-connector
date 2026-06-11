import asyncio
import logging
import discord
from typing import Optional, Dict, Any
from adk_connectors.base_adapter import BaseAdapter
from adk_connectors.models.incoming import IncomingMessage, MediaType
from adk_connectors.models.outgoing import OutgoingMessage
from adk_connectors.discord.config import DiscordConfig
from adk_connectors.discord.parser import DiscordParser
from adk_connectors.discord.formatter import DiscordFormatter

logger = logging.getLogger("adk_connectors.discord")

class DiscordAdapter(BaseAdapter):
    platform = "discord"

    def __init__(self, config: DiscordConfig):
        super().__init__()
        self.config = config
        
        # Setup discord.py intents
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.dm_messages = True
        intents.guild_messages = True
        
        self.client = discord.Client(intents=intents)
        self._bot_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Register event handlers
        @self.client.event
        async def on_ready():
            logger.info(f"Discord Bot logged in as {self.client.user.name} (ID: {self.client.user.id})")

        @self.client.event
        async def on_message(message: discord.Message):
            if not self._is_running:
                return
            if message.author == self.client.user:
                return
            
            parsed = DiscordParser.parse_message(message)
            if parsed and self.on_message_callback:
                asyncio.create_task(self.on_message_callback(parsed))

        @self.client.event
        async def on_interaction(interaction: discord.Interaction):
            if not self._is_running:
                return
            if interaction.type == discord.InteractionType.component:
                try:
                    await interaction.response.defer()
                except Exception as e:
                    logger.warning(f"Failed to defer interaction: {e}")
                
                custom_id = interaction.data.get("custom_id")
                if not custom_id:
                    return
                
                parsed = IncomingMessage(
                    platform="discord",
                    user_id=str(interaction.user.id),
                    chat_id=str(interaction.channel.id),
                    message_id=str(interaction.message.id) if interaction.message else "0",
                    text=custom_id,
                    media_type=MediaType.TEXT,
                    raw_update={
                        "interaction_id": interaction.id,
                        "custom_id": custom_id,
                        "user_id": interaction.user.id,
                        "channel_id": interaction.channel.id
                    }
                )
                
                if self.on_message_callback:
                    asyncio.create_task(self.on_message_callback(parsed))

    async def start(self) -> None:
        self._is_running = True
        logger.info("Starting Discord Client...")
        self._bot_task = asyncio.create_task(self.client.start(self.config.token))

    async def stop(self) -> None:
        self._is_running = False
        logger.info("Stopping Discord Client...")
        await self.client.close()
        if self._bot_task:
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass

    async def _get_channel(self, chat_id: str):
        try:
            channel_id = int(chat_id)
        except ValueError:
            logger.error(f"Invalid channel ID: {chat_id}")
            return None
        
        channel = self.client.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.client.fetch_channel(channel_id)
            except Exception as e:
                logger.debug(f"Failed to fetch channel {channel_id}: {e}")
                
                # Try to resolve user ID as DM channel
                try:
                    user = self.client.get_user(channel_id)
                    if not user:
                        user = await self.client.fetch_user(channel_id)
                    if user:
                        channel = user.dm_channel or await user.create_dm()
                except Exception as ue:
                    logger.error(f"Failed to fetch user or create DM for {channel_id}: {ue}")
        return channel

    async def send_message(self, chat_id: str, message: OutgoingMessage) -> Dict[str, Any]:
        channel = await self._get_channel(chat_id)
        if not channel:
            raise ValueError(f"Channel or User not found for ID: {chat_id}")
            
        payload = DiscordFormatter.to_api_payload(message)
        
        reference = None
        if message.reply_to_message_id:
            try:
                reference = discord.MessageReference(
                    message_id=int(message.reply_to_message_id),
                    channel_id=channel.id
                )
            except Exception as e:
                logger.warning(f"Could not create message reference: {e}")
                
        sent_msg = await channel.send(
            content=payload.get("content"),
            view=payload.get("view"),
            reference=reference
        )
        return {"message_id": str(sent_msg.id)}

    async def edit_message(self, chat_id: str, message_id: str, new_content: str) -> Dict[str, Any]:
        channel = await self._get_channel(chat_id)
        if not channel:
            raise ValueError(f"Channel not found for ID: {chat_id}")
            
        try:
            msg = await channel.fetch_message(int(message_id))
        except Exception as e:
            logger.error(f"Failed to fetch message {message_id} to edit: {e}")
            raise
            
        edited_msg = await msg.edit(content=new_content)
        return {"message_id": str(edited_msg.id)}

    async def set_typing_indicator(self, chat_id: str) -> None:
        channel = await self._get_channel(chat_id)
        if not channel:
            logger.warning(f"Channel not found for ID {chat_id}, cannot set typing indicator")
            return
            
        try:
            async with channel.typing():
                pass
        except Exception as e:
            logger.warning(f"Failed to set typing: {e}")
