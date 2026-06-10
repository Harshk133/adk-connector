# Contributing to ADK Connectors

First off, thank you for considering contributing to ADK Connectors! It's people like you who make this toolkit a great utility for the developer community.

When contributing to this repository, please first discuss the change you wish to make via an issue, email, or any other method with the owners of this repository before making a change.

---

## 🚀 Getting Started

Follow these steps to set up your local development environment:

### 1. Fork and Clone
Fork the repository on GitHub, then clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/adk-connector.git
cd adk-connector
```

### 2. Set Up a Virtual Environment
We recommend using a virtual environment (`venv`) to keep your dependencies isolated:
```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
Install the package in editable mode along with testing requirements:
```bash
pip install -e .
pip install pytest pytest-asyncio
```

---

## 🛠️ Development Workflow

We follow a typical Git branching and Pull Request (PR) workflow:

1. **Sync your fork** with the upstream repository to ensure you are working off the latest changes.
2. **Create a branch** for your work. Keep the branch name descriptive:
   ```bash
   git checkout -b feat/add-slack-connector
   ```
3. **Write your code** and adhere to the project's architecture guidelines:
   * **Core changes** should go into the [adk_connectors/](file:///D:/Project/adk-connector/adk_connectors) package.
   * **Adapter/Platform implementations** (e.g., WhatsApp, Discord) should go into their respective sub-directories under `adk_connectors/`.
4. **Preserve comments and docstrings** for code sections you aren't modifying.
5. **Add tests** for your changes in the [tests/](file:///D:/Project/adk-connector/tests) directory.

---

## 🧪 Testing

We use `pytest` for running our test suite. Before submitting any changes, make sure all tests pass:

```bash
# Run all tests
pytest
```

If you are adding new features, please ensure that you write corresponding unit tests inside the `tests/` folder.

---

## 📝 Coding Standards

* **PEP 8**: Follow PEP 8 guidelines for Python code style.
* **Type Hints**: Use type hints (`typing` module / standard types) where possible.
* **Docstrings**: Document new classes, methods, and functions using descriptive docstrings.
* **Security**: **NEVER** commit API keys, credentials, or bot tokens to the repository. Use environment variables (loaded via `python-dotenv`) for local tests.

---

## 📬 Submitting a Pull Request

Once your code is ready and all tests pass:

1. **Commit your changes** with a clear, descriptive commit message:
   ```bash
   git commit -am "feat: Add basic Slack adapter and configuration model"
   ```
2. **Push your branch** to your fork:
   ```bash
   git push origin feat/add-slack-connector
   ```
3. Open a **Pull Request** against the `main` branch of the upstream repository.
4. Provide a clear description of the changes in the PR template, referencing any related issues.

Thank you for your contribution!
