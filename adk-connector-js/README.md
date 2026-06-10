# 🚀 ADK Connectors (JavaScript / TypeScript)

**adk-connector-js** is a plug-and-play TypeScript/JavaScript wrapper that exposes any [Google Agent Development Kit (ADK)](https://github.com/google/adk-js) agent as a chatbot on Telegram.

By adding just a few lines of code, you can bridge the gap between local development, testing, and production messaging platforms.

---

## 📦 Installation

Install `adk-connector-js` along with its peer dependencies using `npm` or `yarn`:

```bash
npm install adk-connector-js @google/adk telegraf dotenv
```

Make sure you have Node.js version 18 or higher.

---

## ⚡ Quick Start: How to Use It

Integrating the Telegram connector is simple. You can import and initialize it directly inside your main agent file (e.g. `agent.ts`).

### 1. Define and Start the Bot in Your Agent File

Here is how to wrap a TypeScript ADK Agent:

```typescript
import { LlmAgent } from '@google/adk';
import { TelegramConnector } from 'adk-connector-js';
import dotenv from 'dotenv';

// Load environment variables (.env)
dotenv.config();

// 1. Define your standard Google ADK Agent
export const rootAgent = new LlmAgent({
  name: 'my_assistant',
  model: 'gemini-2.5-flash',
  description: 'A helpful coding assistant.',
  instruction: 'You are a helpful assistant.'
});

// 2. Launch the Telegram Connector under entrypoint
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('agent.ts')) {
  const token = process.env.TELEGRAM_BOT_TOKEN;

  if (!token) {
    console.error('❌ Error: TELEGRAM_BOT_TOKEN is not defined in your environment.');
    process.exit(1);
  }

  const connector = new TelegramConnector({
    token: token,
    agent: rootAgent
  });

  connector.start();
}
```

### 2. Configure Environment Variables
Create a `.env` file in your project root with your API keys and bot tokens:

```env
# Gemini API credentials
GEMINI_API_KEY=your_gemini_api_key_here

# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### 3. Run the Bot
Execute the script using your favorite TypeScript runner (like `tsx` or `ts-node`):
```bash
npx tsx agent.ts
```

---

## 🤖 Multi-Agent & Sub-Agent Support

`adk-connector-js` supports complex agent configurations that include sub-agents and tool calls out of the box:

- **Auto-Resolution of State Placeholders**: If a sub-agent's prompt uses variable templates (like `{seminal_paper}` or `{blog_outline}`) that are not populated in the initial state of a session, the connector automatically detects and seeds them with empty strings or user input fallbacks. This **prevents `KeyError` compiler crashes** when running single-turn or text-only scenarios.
- **Intelligent Stream Routing**: The connector filters out internal sub-agent event cycles (tokens with a `branch` property) and only delivers the final synthesized response to the Telegram chat, keeping your bot conversation clean.

---

## 📄 License

This project is licensed under the MIT License.
