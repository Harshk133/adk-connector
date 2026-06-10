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

Depending on your use case, install `adk-connector` using one of the following setups:

### 1. Standard Setup
For basic bot deployment without database session persistence or web UI synchronization:
```bash
pip install adk-connector
```

### 2. Advanced Setup (Session Synchronization)
For database-backed cross-device session synchronization (e.g. syncing with the `adk web` UI), you will also need the Google ADK database components:
```bash
pip install adk-connector
pip install "google-adk[db]"
```

### 3. Local Developer Setup (From Source)
If you are developing or testing `adk-connector` locally, clone this repository and install it in editable mode:
```bash
git clone https://github.com/Harshk133/adk-connector.git
cd adk-connector

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode with dependencies
pip install -e .
```

---

## ⚙️ Environment Configuration

Create a `.env` file in your project root (or copy `.env.example`) and configure the required environment variables:

```env
# Required for agent reasoning
GEMINI_API_KEY=your_gemini_api_key_here

# Required for Telegram bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Required ONLY for Advanced Setup (to map your Telegram ID to the local Web UI user)
TELEGRAM_USER_ID=your_telegram_user_id_here
```

---

## ⚡ Standard Setup: Quick Start

The standard setup launches a standalone chatbot that handles messages but does not sync with the `adk web` UI.

### 1. Create your Run Script
Write the following code to `agent_standard.py`:

```python
import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from adk_connectors.telegram import TelegramConnector

# Load environment variables from .env
load_dotenv()

# 1. Define your standard Google ADK Agent
assistant = Agent(
    model='gemini-2.5-flash',
    name='my_assistant',
    instruction='You are a helpful assistant.'
)

if __name__ == "__main__":
    # 2. Retrieve your Telegram Bot Token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # 3. Bind the connector
    connector = TelegramConnector(
        token=token,
        agent=assistant
    )
    
    # 4. Start polling!
    connector.start()
```

### 2. Run the Script
Execute the script from your terminal:
```bash
python agent_standard.py
```
*Alternatively, you can test this mode using the pre-configured basic example in the repository:*
```bash
python examples/telegram-basic/main.py
```

---

## 🔄 Advanced Setup: Session Synchronization (with `adk web`)

The advanced setup enables the unified cross-device sync engine so you can chat with your bot on Telegram, and view, inspect, or continue the exact same conversation inside the local **ADK Web UI** (`adk web`).

### 1. Configure the Connector
Set `session_management_across_device=True` and pass your personal Telegram user ID to `dev_user_id`. This automatically maps your chats to the `"user"` namespace in `adk web`:

```python
connector = TelegramConnector(
    token=token,
    agent=assistant,
    session_management_across_device=True,  # Spin up DB & mapping persistence
    dev_user_id=os.getenv("TELEGRAM_USER_ID") # Syncs this ID to the "user" Web UI namespace
)
```

### 2. Run the Bot & Web Server
You can run this using the pre-configured `my_agent` workspace in the repository:

1. **Launch the Telegram Bot**:
   Run the agent code which has `session_management_across_device=True`:
   ```bash
   python my_agent/agent.py
   ```
2. **Launch the ADK Web Server** in a separate terminal:
   ```bash
   adk web my_agent
   ```
3. Open your browser and navigate to `http://127.0.0.1:8000`. Your Telegram conversation history and tool executions will appear in the sidebar session list. You can seamlessly chat from either Telegram or the Web UI!

---

## 🗺️ Roadmap

- [x] **Telegram Connector** (v0.1.0)
- [ ] **WhatsApp Connector** (Planned for v0.2.0)
- [ ] **Discord Connector** (Planned for v0.3.0)
- [ ] **Slack Connector** (Planned for v0.4.0)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
