#!/usr/bin/env python3
"""
AI-powered code reviewer with streaming output and structured findings.

SDK features shown:
  - Streaming via session.on() event handlers
  - @define_tool for structured review output
  - system_message for persona control
  - Multiple event types (delta, tool calls, idle)
"""
import asyncio
import json
import sys
from pathlib import Path
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool


# ── Structured findings accumulator ────────────────────────────────────
_findings: list[dict] = []


class FindingParams(BaseModel):
    severity: str = Field(description="critical | warning | suggestion | praise")
    category: str = Field(description="bug | security | performance | style | best-practice")
    line: int = Field(default=0, description="Approximate line number (0 if general)")
    message: str = Field(description="One-line summary of the finding")


@define_tool(description=(
    "Record a single review finding. Call this once for each code issue or "
    "positive observation. The findings are collected into a structured report."
))
def record_finding(params: FindingParams) -> str:
    entry = params.model_dump()
    _findings.append(entry)
    return f"Recorded {params.severity} finding: {params.message}"


async def main():
    """Stream a code review and collect structured findings."""
    _findings.clear()
    if len(sys.argv) < 2:
        print("Usage: python code_reviewer.py <file-path>")
        print("Example:  python code_reviewer.py hello_copilot.py")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    code = file_path.read_text(encoding="utf-8")
    print(f"Reviewing: {file_path.name}  ({len(code.splitlines())} lines)\n")

    client = CopilotClient()
    await client.start()

    try:
        # Pass 1: tool-only extraction (most reliable way to ensure tool calls)
        extraction_session = await client.create_session({
            "model": "gpt-5-mini",
            "tools": [record_finding],
            "system_message": (
                "You are a senior code reviewer. "
                "You MUST use the tool record_finding to record ALL findings. "
                "Do NOT write findings as plain text. "
                "After recording findings, respond with only the word DONE."
            ),
        })

        extraction_prompt = (
            f"Review the following code from {file_path.name}.\n"
            "Record each finding using record_finding(severity, category, line, message).\n"
            "Severity must be one of: critical, warning, suggestion, praise.\n"
            "Category must be one of: bug, security, performance, style, best-practice.\n\n"
            f"```\n{code}\n```"
        )
        _ = await extraction_session.send_and_wait({"prompt": extraction_prompt})
        await extraction_session.destroy()

        # Print structured report
        if _findings:
            print("\n\n--- Structured Findings ---")
            for i, f in enumerate(_findings, 1):
                sev = f["severity"].upper()
                loc = f"L{f['line']}" if f["line"] else "general"
                print(f"  {i}. [{sev}] ({f['category']}, {loc}) {f['message']}")
            print(f"\nTotal: {len(_findings)} findings")
        else:
            print("\n\nNo structured findings recorded.")

        # Pass 2: streaming narrative summary
        summary_session = await client.create_session({
            "model": "gpt-4o",
            "streaming": True,
            "system_message": (
                "Write a concise code review summary based on the provided structured findings. "
                "Do not mention tool calls."
            ),
        })
        done = asyncio.Event()

        def on_event(event):
            if event.type.value == "assistant.message_delta":
                print(event.data.delta_content, end="", flush=True)
            elif event.type.value == "session.idle":
                done.set()

        summary_session.on(on_event)
        print("\n\n--- Summary ---\n")
        await summary_session.send({
            "prompt": (
                "Summarize the review in 5-10 lines. Include: overall assessment, top 2 risks, top 2 improvements.\n\n"
                f"Structured findings (JSON):\n{json.dumps(_findings, indent=2)}"
            )
        })
        await done.wait()
        print("\n\nReview complete.")
        await summary_session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
