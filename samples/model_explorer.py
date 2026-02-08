#!/usr/bin/env python3
"""
Model explorer - discover available models, check auth, and inspect capabilities.
Demonstrates the Copilot SDK's client-level introspection APIs.

SDK features shown:
  - client.ping()           → verify server connectivity
  - client.get_auth_status() → inspect authentication
  - client.list_models()    → enumerate available models with capabilities
  - client.get_status()     → server status information
"""
import asyncio
from copilot import CopilotClient


def format_token_limit(value: int | None) -> str:
    """Format a token limit into a human-readable string."""
    if value is None:
        return "unlimited"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return str(value)


async def main():
    """Explore connected models and SDK capabilities."""
    client = CopilotClient()
    await client.start()

    try:
        # ── 1. Ping the server ──────────────────────────────────────────
        print("🔌 Connecting to Copilot...\n")
        pong = await client.ping("hello")
        print(f"  Ping response : {pong.message}")
        print(f"  Protocol ver  : {pong.protocolVersion}")
        print(f"  Server time   : {pong.timestamp}")

        # ── 2. Check authentication ─────────────────────────────────────
        print("\n🔐 Authentication\n")
        auth = await client.get_auth_status()
        if auth.isAuthenticated:
            print("  Status  : ✅ Authenticated")
            print(f"  User    : {auth.login or 'unknown'}")
            print(f"  Host    : {auth.host or 'github.com'}")
            print(f"  Method  : {auth.authType or 'unknown'}")
        else:
            print("  Status  : ❌ Not authenticated")
            print(f"  Message : {auth.statusMessage}")
            print("\n  Run 'copilot auth login' to authenticate.")
            return

        # ── 3. List all available models ────────────────────────────────
        print("\n📋 Available Models\n")
        models = await client.list_models()

        # Table header
        header = f"  {'Model ID':<30} {'Vision':>6} {'Reasoning':>9} {'Context':>10} {'Prompt':>10}"
        print(header)
        print("  " + "─" * (len(header) - 2))

        for model in sorted(models, key=lambda m: m.id):
            vision = "✓" if model.capabilities.supports.vision else "–"
            reasoning = "✓" if model.capabilities.supports.reasoning_effort else "–"
            ctx = format_token_limit(model.capabilities.limits.max_context_window_tokens)
            prompt = format_token_limit(model.capabilities.limits.max_prompt_tokens)
            print(f"  {model.id:<30} {vision:>6} {reasoning:>9} {ctx:>10} {prompt:>10}")

        # ── 4. Highlight key models ─────────────────────────────────────
        vision_models = [m for m in models if m.capabilities.supports.vision]
        reasoning_models = [m for m in models if m.capabilities.supports.reasoning_effort]

        print("\n📊 Summary")
        print(f"  Total models       : {len(models)}")
        print(f"  Vision-capable     : {len(vision_models)}")
        print(f"  Reasoning-capable  : {len(reasoning_models)}")

        if reasoning_models:
            print("\n🧠 Reasoning models with effort levels:")
            for m in reasoning_models:
                efforts = m.supported_reasoning_efforts or []
                default = m.default_reasoning_effort or "–"
                print(f"  {m.id}: {', '.join(efforts)} (default: {default})")

        # ── 5. Quick model test ─────────────────────────────────────────
        print("\n🧪 Quick model smoke test\n")
        session = await client.create_session({"model": "gpt-5-mini"})
        response = await session.send_and_wait(
            {"prompt": "Respond with only the word 'OK'."}
        )
        result = response.data.content.strip()
        status = "✅ PASS" if "OK" in result.upper() else f"⚠️  Got: {result}"
        print(f"  gpt-5-mini → {status}")
        await session.destroy()

        print("\n✅ Exploration complete!")

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
