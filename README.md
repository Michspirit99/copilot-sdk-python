# Copilot SDK Python Scripts 🐍

> **Zero-ceremony AI scripts in Python** — Single-file Python scripts using the [GitHub Copilot SDK](https://github.com/github/copilot-sdk). Just `pip install` and run. No setup.py, no boilerplate—pure Python simplicity meets AI-powered automation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Copilot SDK](https://img.shields.io/badge/Copilot_SDK-Technical_Preview-green.svg)](https://github.com/github/copilot-sdk)

## What Is This?

This repository demonstrates the [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk/tree/main/python) through practical,single-file scripts. Each script is:

- **Self-contained** — One `.py` file, ready to run
- **Practical** — Real-world automation use cases
- **Modern Python** — Type hints, async/await, argparse
- **Zero boilerplate** — No setup.py, no project scaffolding

The GitHub Copilot SDK gives you programmatic access to the same AI agent runtime powering Copilot CLI and Copilot Chat.

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/) installed
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line) installed and in PATH
- A [GitHub Copilot subscription](https://github.com/features/copilot#pricing) (free tier available)
- Authenticated with Copilot CLI (`copilot auth login`)

## Quick Start

```bash
# Clone this repo
git clone https://github.com/Michspirit99/copilot-sdk-python-scripts.git
cd copilot-sdk-python-scripts

# Install dependencies
pip install -r requirements.txt

# Run any script — instant AI!
python samples/hello_copilot.py
```

That's it. No virtual environment required (but recommended). No project setup. Just Python and AI.

## Samples

### Core Examples

| Script | Description |
|--------|-------------|
| [`hello_copilot.py`](samples/hello_copilot.py) | Minimal "Hello World" — send a prompt, get a response |
| [`streaming_chat.py`](samples/streaming_chat.py) | Stream responses token-by-token in real time |
| [`interactive_chat.py`](samples/interactive_chat.py) | Full interactive chat loop in the terminal |
| [`code_reviewer.py`](samples/code_reviewer.py) | AI-powered code review — pass any file for analysis |
| [`custom_tools.py`](samples/custom_tools.py) | Define custom Python functions callable by AI |
| [`multi_model.py`](samples/multi_model.py) | Compare responses from gpt-4.1 vs gpt-5-mini |
| [`file_summarizer.py`](samples/file_summarizer.py) | Summarize any text file using AI |
| [`git_commit_writer.py`](samples/git_commit_writer.py) | Generate conventional commit messages from staged changes |

### Automation & Testing

| Script | Description |
|--------|-------------|
| [`playwright_agent.py`](samples/playwright_agent.py) | 🌐 AI-driven browser automation with Playwright |
| [`log_analyzer.py`](samples/log_analyzer.py) | 📊 Analyze logs for errors, security issues, performance |
| [`api_test_generator.py`](samples/api_test_generator.py) | 🧪 Generate API tests from OpenAPI/Swagger specs |
| [`test_data_generator.py`](samples/test_data_generator.py) | 🎲 Generate realistic test data in JSON/SQL/CSV |

### Usage Examples

```bash
# Basic usage
python samples/hello_copilot.py

# Core samples with arguments
python samples/code_reviewer.py path/to/file.py
python samples/file_summarizer.py README.md
python samples/streaming_chat.py "Explain decorators in Python"

# Automation samples
python samples/playwright_agent.py https://example.com "Describe the page"
python samples/log_analyzer.py app.log errors
python samples/api_test_generator.py swagger.json pytest
python samples/test_data_generator.py user 50 json
```

## Automation Use Cases

The automation scripts demonstrate practical AI-powered workflows:

**🌐 Browser Automation ([playwright_agent.py](samples/playwright_agent.py))**
- Navigate websites and extract data
- AI-guided form filling and interaction
- Automated testing scenarios
- Web scraping with natural language commands

**📊 Log Analysis ([log_analyzer.py](samples/log_analyzer.py))**
- Find and categorize errors automatically
- Security threat detection
- Performance bottleneck identification
- Automated incident reports

**🧪 API Testing ([api_test_generator.py](samples/api_test_generator.py))**
- Generate pytest/unittest test cases
- Create Postman collections
- Generate curl command references
- Test coverage analysis from OpenAPI specs

**🎲 Test Data ([test_data_generator.py](samples/test_data_generator.py))**
- Realistic user profiles and datasets
- Product catalogs and inventories
- Order histories and transactions
- Custom schemas in JSON/SQL/CSV formats

## How It Works

### The Copilot SDK

```python
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({"model": "gpt-5-mini"})
    response = await session.send_and_wait(
        {"prompt": "Explain async/await"}
    )
    print(response.data.content)

    await session.destroy()
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

Key concepts:
- **CopilotClient** — Manages the connection to Copilot
- **Session config** — Pass a dict with model, tools, and options
- **Streaming** — Use `session.on()` with event handlers for token-by-token output
- **Tools** — Define tools with `@define_tool` decorator and Pydantic models

### Custom Tools (Function Calling)

```python
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field

class GetWeatherParams(BaseModel):
    city: str = Field(description="The city name")

@define_tool(description="Get the weather for a city")
def get_weather(params: GetWeatherParams) -> str:
    return f"Sunny in {params.city}"

# Pass tools in session config
session = await client.create_session({
    "model": "gpt-5-mini",
    "tools": [get_weather],
})
response = await session.send_and_wait(
    {"prompt": "What's the weather in Seattle?"}
)
print(response.data.content)
```

## Virtual Environments (Recommended)

While not required, using a virtual environment is best practice:

```bash
# Create and activate venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run samples
python samples/hello_copilot.py
```

## BYOK (Bring Your Own Key)

Don't have a Copilot subscription? Use your own OpenAI API key:

```python
import os

session = await client.create_session({
    "model": "gpt-5-mini",
    "provider": {
        "type": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
})
```

Set your API key:
```bash
export OPENAI_API_KEY="sk-..."  # On Windows: set OPENAI_API_KEY=sk-...
```

## Project Structure

```
copilot-sdk-python-scripts/
├── samples/                    # All runnable scripts
│   ├── hello_copilot.py        # Minimal example
│   ├── streaming_chat.py       # Streaming responses
│   ├── interactive_chat.py     # Interactive terminal chat
│   ├── code_reviewer.py        # AI code review
│   ├── custom_tools.py         # Custom tool definitions
│   ├── multi_model.py          # Multi-model comparison
│   ├── file_summarizer.py      # File summarization
│   ├── git_commit_writer.py    # Git commit message generation
│   ├── playwright_agent.py     # Browser automation
│   ├── log_analyzer.py         # Log file analysis
│   ├── api_test_generator.py   # API test generation
│   └── test_data_generator.py  # Test data generation
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # CI validation (no live AI calls)
│   │   └── agent-scenarios.yml  # Optional E2E proof runs
├── requirements.txt             # Python dependencies
├── README.md
├── LICENSE
├── .gitignore
└── CONTRIBUTING.md
```

## Why Python + Copilot SDK?

| Traditional Approach | This Repository |
|---|---|
| Create project directory | Just create a `.py` file |
| Write `setup.py` or `pyproject.toml` | `requirements.txt` only |
| Manage dependencies manually | One `pip install` command |
| Multiple files for simple tasks | Single file, pure Python |
| Project scaffolding overhead | Zero ceremony |

Python is already the language of choice for quick scripts—this repository shows how to make them AI-powered with minimal effort.

## CI/CD

This repository includes GitHub Actions CI that:

- ✅ Lints (ruff)
- ✅ Checks syntax (`compileall`)
- ✅ Runs import smoke tests (so samples keep working for contributors)

Because end-to-end runs require network + authentication (and can consume quota), live AI calls are **opt-in**.

- Default CI: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- Optional E2E proof (manual): [.github/workflows/agent-scenarios.yml](.github/workflows/agent-scenarios.yml)

See [CI-SETUP.md](CI-SETUP.md) for details.

## Contributing

Contributions welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines. Whether you're:

- Adding new sample scripts
- Improving existing samples
- Fixing bugs or typos
- Enhancing documentation

All contributions are appreciated!

## License

[MIT](LICENSE) — Use these samples however you like.

## Resources

- [GitHub Copilot SDK (Python)](https://github.com/github/copilot-sdk/tree/main/python)
- [GitHub Copilot SDK (Main Repo)](https://github.com/github/copilot-sdk)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [GitHub Copilot](https://github.com/features/copilot)

## Related Projects

- [copilot-sdk-file-apps](https://github.com/Michspirit99/copilot-sdk-file-apps) — C# version using .NET 10 file-based apps

---

**Made with 🤖 and Python | Star ⭐ if you find this useful!**
