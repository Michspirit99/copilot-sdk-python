# Contributing to Copilot SDK Python Scripts

Thank you for your interest in contributing! This repository showcases single-file Python scripts using the GitHub Copilot SDK.

## How to Contribute

### Adding New Samples

1. **Keep it simple** — Each sample should be a single `.py` file
2. **Follow conventions** — Use snake_case for filenames, type hints, async/await patterns
3. **Make it runnable** — Ensure `python samples/your_script.py` works immediately after `pip install -r requirements.txt`
4. **Document it** — Add clear docstrings and usage examples
5. **Update README** — Add your sample to the table in README.md

### Sample Structure

```python
#!/usr/bin/env python3
"""
Brief description of what this sample does.
"""
import asyncio
from copilot import CopilotClient, SessionConfig

async def main():
    """Main entry point."""
    #  Your code here
    pass

if __name__ == "__main__":
    asyncio.run(main())
```

### Code Guidelines

- **Type hints** — Use them for function signatures
- **Error handling** — Include try/except where appropriate
- **CLI args** — Use `argparse` for command-line arguments
- **Async** — Use `async`/`await` patterns consistently
- **Comments** — Explain complex logic, not obvious code

### Testing Your Sample

1. Install dependencies: `pip install -r requirements.txt`
2. Run your script: `python samples/your_script.py`
3. Verify it works end-to-end with real Copilot calls

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-sample-name`
3. Add your sample in `samples/`
4. Update README.md to list your sample
5. Test it locally
6. Submit a PR with a clear description

### Questions?

Open an issue for discussion before starting work on major changes.

## Code of Conduct

Be respectful, constructive, and helpful. This is a learning and demonstration project — all skill levels are welcome.
