#!/usr/bin/env python3
"""
File summarizer - AI-powered text file summarization.
"""
import asyncio
import sys
from pathlib import Path
from copilot import CopilotClient


async def main():
    """Summarize a text file using Copilot."""
    if len(sys.argv) < 2:
        print("Usage: python file_summarizer.py <file-path>")
        print("\nExample:")
        print("  python file_summarizer.py README.md")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    # Read the file
    content = file_path.read_text(encoding='utf-8')
    
    print(f"📄 Summarizing: {file_path.name}")
    print(f"📊 Size: {len(content)} characters\n")
    
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-5-mini"})

        prompt = f"""Summarize this file in a clear, concise way:

File: {file_path.name}
Content:
```
{content}
```

Provide:
1. Main purpose/topic
2. Key points (3-5 bullets)
3. Target audience (if identifiable)
"""

        print("🤖 Summary:\n")
        response = await session.send_and_wait({"prompt": prompt})
        print(response.data.content)
        print("\n✅ Summary complete!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
