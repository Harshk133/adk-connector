# Discord Basic Example

This example demonstrates how to deploy a Google ADK (Agent Development Kit) agent to Discord using ADK Connectors.

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in your `DISCORD_BOT_TOKEN` (get it from the Discord Developer Portal) and your `GEMINI_API_KEY` (get it from Google AI Studio).

3. Make sure to enable **Message Content Intent** in your Bot settings on the Discord Developer Portal.

4. Run the script:
   ```bash
   python main.py
   ```

5. Invite the bot to your server and start chatting with it!
