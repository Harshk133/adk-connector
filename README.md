# 🚀 ADK Connectors

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org)
[![PyPI version](https://badge.fury.io/py/adk-connector.svg)](https://pypi.org/project/adk-connector/)

**ADK Connectors** is a plug-and-play toolkit that wraps any [Google Agent Development Kit (ADK)](https://github.com/google/adk) agent and exposes it as a chatbot on Telegram, Discord, WhatsApp, and Slack. 

By adding just **three lines of code**, you can bridge the gap between local development, testing, and production messaging platforms.

---

## ✨ Key Features

* 🚀 **3-Line Wrapper**: Deploy any `google-adk` agent to messaging channels with virtually zero code changes.
* 🔄 **Cross-Device Session Sync**: Enable `session_management_across_device` to sync conversations seamlessly. Chat on Telegram, then inspect and continue the exact same conversation inside the ADK Web UI (`adk web`).
* 💾 **Automatic Database Engine Setup**: Transparently spins up an asynchronous SQLite (`aiosqlite`) backend to record session states, events, and tool invocations.
* 🔒 **Local Persistent Mapping**: Uses a secure, local JSON mapping engine so restarting the bot never breaks session IDs or active chats.
* 🧩 **Extensible Architecture**: Structured from day one to support multiple providers (Telegram, and future modules for WhatsApp, Discord, and Slack).

---

## 📦 Installation

Install the package via pip:

```bash
pip install adk-connector
```

*Note: For the full database-backed cross-device session synchronization, ensure you have the Google ADK database components installed (`pip install google-adk[db]`).*

---

## ⚡ Quick Start (Standard Mode)

Wrap your agent and launch a Telegram bot in minutes:

```python
import os
from google.adk.agents.llm_agent import Agent
from adk_connectors.telegram import TelegramConnector

# 1. Define your standard Google ADK Agent
assistant = Agent(
    model='gemini-2.5-flash',
    name='my_assistant',
    instruction='You are a helpful assistant.'
)

if __name__ == "__main__":
    # 2. Bind the connector with your Telegram Bot Token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    connector = TelegramConnector(
        token=token,
        agent=assistant
    )
    
    # 3. Start polling!
    connector.start()
```

---

## 🔄 Advanced: Session Synchronization (with `adk web`)

Want to inspect your Telegram chats and continue them directly inside the local **ADK Web UI** (`adk web`)? Enable the unified cross-device sync engine:

### 1. Configure the Connector
Set `session_management_across_device=True` and pass your personal Telegram user ID to `dev_user_id`. This automatically maps your chats to the `"user"` namespace in `adk web`:

```python
connector = TelegramConnector(
    token=token,
    agent=assistant,
    session_management_across_device=True,  # Spin up DB & mapping persistence
    dev_user_id="YOUR_TELEGRAM_USER_ID"     # Syncs this ID to the "user" Web UI namespace
)
```

### 2. Run the Bot & Web Server
1. **Launch the Telegram Bot**:
   ```bash
   python my_agent/agent.py
   ```
2. **Launch the ADK Web Server** in a separate terminal:
   ```bash
   adk web my_agent
   ```
3. Open the browser at `http://127.0.0.1:8000`. Your Telegram conversation will appear in the sidebar session list. You can view the history, inspect tool execution, and chat from either screen!

---

## 🗺️ Roadmap

- [x] **Telegram Connector** (v0.1.0)
- [ ] **WhatsApp Connector** (Planned for v0.2.0)
- [ ] **Discord Connector** (Planned for v0.3.0)
- [ ] **Slack Connector** (Planned for v0.4.0)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
