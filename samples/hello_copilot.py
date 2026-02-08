#!/usr/bin/env python3
"""
Minimal "Hello World" Copilot SDK example.
Sends a single prompt and prints the response.
"""
import asyncio
from copilot import CopilotClient


async def main():
    """Send a simple prompt to Copilot and print the response."""
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-5-mini"})

        print("🤖 Copilot Hello World\n")

        response = await session.send_and_wait(
            {"prompt": "Say hello and explain what you are in one sentence"}
        )
        print(response.data.content)
        print("\n✅ Done!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
