#!/usr/bin/env python3
"""
Interactive chat with multi-turn memory and session introspection.

SDK features shown:
  - Multi-turn conversation in a single session (context preserved automatically)
  - Streaming via session.on() event handlers
  - session.get_messages() to retrieve conversation history
  - Slash-commands implemented in Python to show hybrid local/AI workflows
"""
import asyncio
from copilot import CopilotClient


HELP_TEXT = """\
Commands:
  /history  - Show conversation turns so far
  /model    - Show the model used for this session
  /clear    - End session and start a fresh one
  /help     - Show this help message
  exit      - Quit
"""


async def main():
    """Run an interactive multi-turn chat loop."""
    client = CopilotClient()
    await client.start()

    model = "gpt-5-mini"
    turn_count = 0
    done = asyncio.Event()

    def on_event(event):
        if event.type.value == "assistant.message_delta":
            print(event.data.delta_content, end="", flush=True)
        elif event.type.value == "session.idle":
            done.set()

    try:
        session = await client.create_session({"model": model, "streaming": True})
        session.on(on_event)

        print("Copilot Interactive Chat")
        print(f"Model: {model}  |  Type /help for commands\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # ── Local slash-commands ──────────────────────────
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if user_input == "/help":
                print(HELP_TEXT)
                continue

            if user_input == "/model":
                print(f"  Model: {model}\n")
                continue

            if user_input == "/history":
                try:
                    events = await session.get_messages()
                    if not events:
                        print("  (no messages yet)\n")
                    else:
                        shown = 0
                        for ev in events:
                            ev_type = getattr(getattr(ev, "type", None), "value", None)
                            if ev_type not in ("user.message", "assistant.message"):
                                continue
                            data = getattr(ev, "data", None)
                            role = getattr(data, "role", None) or ("user" if ev_type == "user.message" else "assistant")
                            content = getattr(data, "content", "") or ""
                            preview = (content[:120] + "...") if len(content) > 120 else content
                            print(f"  [{role}] {preview}")
                            shown += 1
                        if shown == 0:
                            print("  (no user/assistant messages yet)\n")
                        print()
                except Exception as e:
                    print(f"  Could not retrieve history: {e}\n")
                continue

            if user_input == "/clear":
                await session.destroy()
                session = await client.create_session({"model": model, "streaming": True})
                session.on(on_event)
                turn_count = 0
                print("  Session cleared.\n")
                continue

            # ── Send to Copilot ───────────────────────────────
            turn_count += 1
            print("Copilot: ", end="", flush=True)
            done.clear()
            await session.send({"prompt": user_input})
            await done.wait()
            print(f"\n  (turn {turn_count})\n")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
