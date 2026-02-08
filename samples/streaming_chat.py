#!/usr/bin/env python3
"""
Streaming chat example - displays responses token-by-token in real time.
"""
import asyncio
import sys
from copilot import CopilotClient


async def main():
    """Stream a response from Copilot token-by-token."""
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-5-mini", "streaming": True})

        prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Explain async/await in Python"

        print(f"📝 Prompt: {prompt}\n")
        print("🤖 Copilot: ", end="", flush=True)

        done = asyncio.Event()

        def on_event(event):
            if event.type.value == "assistant.message_delta":
                print(event.data.delta_content, end="", flush=True)
            elif event.type.value == "session.idle":
                done.set()

        session.on(on_event)
        await session.send({"prompt": prompt})
        await done.wait()

        print("\n\n✅ Done!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
