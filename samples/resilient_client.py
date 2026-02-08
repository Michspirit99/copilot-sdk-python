#!/usr/bin/env python3
"""
Resilient client - production-grade error handling patterns for the Copilot SDK.

SDK features shown:
  - Connection validation with ping()
  - Authentication checks before work
  - Graceful retry with exponential backoff
  - Timeout enforcement
  - Structured error reporting
  - Clean shutdown on failure
"""
import asyncio
import sys
import time
from copilot import CopilotClient


# ── Retry helper ────────────────────────────────────────────────────────

async def retry_async(
    coro_factory,
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    label: str = "operation",
):
    """Retry an async operation with exponential backoff.

    Args:
        coro_factory: A zero-arg callable that returns a new awaitable each call.
        max_attempts: Maximum number of attempts.
        base_delay: Initial delay in seconds (doubles each retry).
        label: Human-readable label for log messages.

    Returns:
        The result of the awaitable on success.

    Raises:
        The last exception encountered after all attempts are exhausted.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_factory()
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"  ⚠️  {label} failed (attempt {attempt}/{max_attempts}): {exc}")
                print(f"     Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                print(f"  ❌ {label} failed after {max_attempts} attempts: {exc}")
    raise last_error


# ── Timeout wrapper ─────────────────────────────────────────────────────

async def with_timeout(coro, *, seconds: float, label: str = "operation"):
    """Wrap an awaitable with a timeout, raising a clear error."""
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"{label} timed out after {seconds:.0f}s")


# ── Pre-flight checks ──────────────────────────────────────────────────

async def preflight(client: CopilotClient) -> bool:
    """Run connectivity and auth checks. Returns True if everything is OK."""
    print("🔍 Pre-flight checks\n")

    # 1. Ping
    try:
        pong = await with_timeout(
            client.ping("preflight"), seconds=10, label="Ping"
        )
        print(f"  ✅ Server reachable  (protocol v{pong.protocolVersion})")
    except Exception as exc:
        print(f"  ❌ Server unreachable: {exc}")
        return False

    # 2. Authentication
    try:
        auth = await with_timeout(
            client.get_auth_status(), seconds=10, label="Auth check"
        )
        if auth.isAuthenticated:
            print(f"  ✅ Authenticated as {auth.login or 'unknown'}")
        else:
            print(f"  ❌ Not authenticated: {auth.statusMessage}")
            print("     Run 'copilot auth login' first.")
            return False
    except Exception as exc:
        print(f"  ❌ Auth check failed: {exc}")
        return False

    # 3. Model availability
    try:
        models = await with_timeout(
            client.list_models(), seconds=15, label="List models"
        )
        print(f"  ✅ {len(models)} model(s) available")
    except Exception as exc:
        print(f"  ⚠️  Could not list models: {exc}")
        # Non-fatal — we can still try to create a session

    print()
    return True


# ── Main workflow ───────────────────────────────────────────────────────

async def main():
    """Demonstrate resilient patterns for production use."""
    prompts = [
        "What is the Liskov Substitution Principle? Answer in 2 sentences.",
        "Give a Python code example that violates it.",
        "Now fix the example so it follows the principle.",
    ]

    print("🛡️  Resilient Copilot Client\n")

    # ── Start client with retry ─────────────────────────────────────────
    client = CopilotClient()
    try:
        await retry_async(
            lambda: client.start(),
            max_attempts=3,
            label="Client start",
        )
    except Exception:
        print("\n❌ Could not start Copilot client. Is `copilot` CLI installed?")
        sys.exit(1)

    try:
        # ── Pre-flight ──────────────────────────────────────────────────
        if not await preflight(client):
            print("❌ Pre-flight checks failed. Exiting.")
            return

        # ── Create session with retry ───────────────────────────────────
        session = await retry_async(
            lambda: client.create_session({"model": "gpt-5-mini"}),
            max_attempts=3,
            label="Session creation",
        )

        print("💬 Sending prompts with timeout + retry\n")

        for i, prompt in enumerate(prompts, 1):
            print(f"{'─' * 60}")
            print(f"📝 Prompt {i}: {prompt}\n")

            start = time.perf_counter()

            try:
                response = await retry_async(
                    lambda p=prompt: with_timeout(
                        session.send_and_wait({"prompt": p}),
                        seconds=30,
                        label=f"Prompt {i}",
                    ),
                    max_attempts=2,
                    label=f"Prompt {i}",
                )
                elapsed = time.perf_counter() - start
                print(f"🤖 Response ({elapsed:.1f}s):\n")
                print(response.data.content)
            except Exception as exc:
                elapsed = time.perf_counter() - start
                print(f"❌ Failed after {elapsed:.1f}s: {exc}")
                print("   Skipping to next prompt...\n")

            print()

        await session.destroy()
        print("✅ All prompts processed!")

    finally:
        errors = await client.stop()
        if errors:
            print(f"\n⚠️  Shutdown warnings: {errors}")


if __name__ == "__main__":
    asyncio.run(main())
