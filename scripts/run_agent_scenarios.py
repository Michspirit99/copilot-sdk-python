#!/usr/bin/env python3
"""Run end-to-end agent scenarios for CI proof.

This script is intended for CI environments where you *want proof* that the
Copilot SDK can run real scenarios (network + auth required).

It runs a small, deterministic set of scenarios and prints a short transcript.

Modes
-----
- Copilot mode (default): uses your Copilot CLI auth.
- OpenAI mode: uses BYOK provider config with OPENAI_API_KEY.

Notes
-----
- These are E2E checks, not unit tests.
- Keep prompts short to reduce cost/latency.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass

from copilot import CopilotClient


@dataclass
class ScenarioResult:
    name: str
    ok: bool
    details: str = ""


def _provider_config(provider: str) -> dict | None:
    if provider == "copilot":
        return None
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for provider=openai")
        return {
            "type": "openai",
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "api_key": api_key,
        }
    raise ValueError(f"Unknown provider: {provider}")


async def scenario_ping(client: CopilotClient) -> ScenarioResult:
    try:
        pong = await client.ping("ci")
        return ScenarioResult("ping", True, f"protocol={pong.protocolVersion}")
    except Exception as e:
        return ScenarioResult("ping", False, str(e))


async def scenario_single_prompt(client: CopilotClient, *, model: str, provider_cfg: dict | None) -> ScenarioResult:
    try:
        cfg: dict = {"model": model}
        if provider_cfg is not None:
            cfg["provider"] = provider_cfg
        session = await client.create_session(cfg)
        try:
            timeout_s = float(os.getenv("COPILOT_E2E_TIMEOUT", "60"))
            resp = await asyncio.wait_for(
                session.send_and_wait({
                    "prompt": "Reply with exactly: OK",
                }),
                timeout=timeout_s,
            )
            text = (resp.data.content or "").strip()
            ok = text.startswith("OK")
            return ScenarioResult("single_prompt", ok, f"response={text[:80]!r}")
        finally:
            await session.destroy()
    except Exception as e:
        return ScenarioResult("single_prompt", False, str(e))


async def run(provider: str, model: str) -> int:
    provider_cfg = _provider_config(provider)

    client_opts: dict = {}
    # For unattended CI runs with the Copilot provider, prefer a token-based auth path.
    # The Copilot SDK client supports `github_token` for non-interactive authentication.
    github_token = os.getenv("COPILOT_GITHUB_TOKEN")
    if provider == "copilot" and github_token:
        client_opts["github_token"] = github_token

    client = CopilotClient(client_opts or None)
    await client.start()
    try:
        results: list[ScenarioResult] = []
        results.append(await scenario_ping(client))
        results.append(await scenario_single_prompt(client, model=model, provider_cfg=provider_cfg))

        print("Agent scenarios")
        print(f"  provider: {provider}")
        print(f"  model   : {model}")
        print()

        failed = 0
        for r in results:
            status = "PASS" if r.ok else "FAIL"
            print(f"- {r.name:14} {status}  {r.details}")
            if not r.ok:
                failed += 1

        return 0 if failed == 0 else 1
    finally:
        await client.stop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default=os.getenv("COPILOT_E2E_PROVIDER", "copilot"), choices=["copilot", "openai"])
    parser.add_argument("--model", default=os.getenv("COPILOT_E2E_MODEL", "gpt-5-mini"))
    args = parser.parse_args()

    try:
        return asyncio.run(run(args.provider, args.model))
    except Exception as e:
        print(f"E2E runner error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
