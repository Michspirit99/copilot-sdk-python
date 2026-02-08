#!/usr/bin/env python3
"""
Log analyzer - AI-powered log file analysis with custom tools.

SDK features shown:
  - @define_tool with Pydantic parameters for structured tool calling
  - Tools that operate on captured external state (log content)
  - Streaming output with event handlers
"""
import asyncio
import re
import sys
import secrets
from collections import Counter
from pathlib import Path
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool


# ── Log content is captured here after file read ────────────────────────
_log_lines: list[str] = []
RUN_ID = secrets.token_hex(4)


# ── Tool parameter models ──────────────────────────────────────────────

class GrepParams(BaseModel):
    pattern: str = Field(description="Regex pattern to search for in the log")
    max_results: int = Field(default=10, description="Maximum lines to return")


class TimeRangeParams(BaseModel):
    start: str = Field(description="Start time prefix to filter from, e.g. '2024-01-15 14:'")
    end: str = Field(description="End time prefix to filter to, e.g. '2024-01-15 15:'")


# ── Tool definitions ───────────────────────────────────────────────────

@define_tool(description="Get log file statistics: total lines, error count, warning count, and top repeated messages")
def get_log_stats() -> str:
    total = len(_log_lines)
    errors = sum(1 for line in _log_lines if re.search(r"\b(ERROR|FATAL|CRITICAL)\b", line, re.I))
    warnings = sum(1 for line in _log_lines if re.search(r"\bWARN(ING)?\b", line, re.I))
    infos = sum(1 for line in _log_lines if re.search(r"\bINFO\b", line, re.I))

    # Find most common messages (strip timestamps for grouping)
    stripped = [re.sub(r"^[\d\-T:.,\s\[\]]+", "", line).strip() for line in _log_lines]
    top = Counter(stripped).most_common(5)
    top_str = "\n".join(f"  {count}x  {msg[:100]}" for msg, count in top)

    return (
        f"RunId: {RUN_ID}\n"
        f"Total lines: {total}\n"
        f"ERROR/FATAL/CRITICAL: {errors}\n"
        f"WARN: {warnings}\n"
        f"INFO: {infos}\n"
        f"Top repeated messages:\n{top_str}"
    )


@define_tool(description="Search the log with a regex pattern and return matching lines")
def grep_log(params: GrepParams) -> str:
    try:
        compiled = re.compile(params.pattern, re.IGNORECASE)
    except re.error as e:
        return f"Invalid regex: {e}"
    matches = [line for line in _log_lines if compiled.search(line)]
    if not matches:
        return f"No lines matching '{params.pattern}'."
    shown = matches[:params.max_results]
    footer = f"\n... and {len(matches) - len(shown)} more" if len(matches) > len(shown) else ""
    return f"RunId: {RUN_ID}\nFound {len(matches)} matches:\n" + "\n".join(shown) + footer


@define_tool(description="Extract log lines within a time range (by string prefix comparison)")
def get_time_range(params: TimeRangeParams) -> str:
    matches = [line for line in _log_lines if params.start <= line[: len(params.start)] <= params.end]
    if not matches:
        return f"No lines between '{params.start}' and '{params.end}'."
    if len(matches) > 20:
        return f"RunId: {RUN_ID}\nFound {len(matches)} lines. First 20:\n" + "\n".join(matches[:20])
    return f"RunId: {RUN_ID}\nFound {len(matches)} lines:\n" + "\n".join(matches)


@define_tool(description="Get the first N and last N lines of the log file for context")
def get_log_boundaries() -> str:
    head = _log_lines[:10]
    tail = _log_lines[-10:] if len(_log_lines) > 10 else []
    result = f"RunId: {RUN_ID}\nFirst 10 lines:\n" + "\n".join(head)
    if tail:
        result += f"\n\n... ({len(_log_lines) - 20} lines omitted) ...\n\nLast 10 lines:\n" + "\n".join(tail)
    return result


async def main():
    """Analyze a log file with AI + tool-assisted investigation."""
    global _log_lines

    if len(sys.argv) < 2:
        print("Usage: python log_analyzer.py <log-file-path> [analysis-type]")
        print("\nAnalysis types: errors | security | performance | summary (default)")
        print("Example:  python log_analyzer.py /var/log/app.log errors")
        sys.exit(1)

    log_path = Path(sys.argv[1])
    analysis_type = sys.argv[2].lower() if len(sys.argv) > 2 else "summary"

    if not log_path.exists():
        print(f"Error: File not found: {log_path}")
        sys.exit(1)

    # Load log content into the module-level list so tools can access it
    _log_lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    print(f"Analyzing: {log_path.name}  ({len(_log_lines)} lines)")
    print(f"Analysis type: {analysis_type}\n")

    analysis_prompts = {
        "errors":      "Find and categorise all errors. Group by type, show counts, and recommend fixes.",
        "security":    "Identify security issues: failed logins, suspicious IPs, privilege escalations.",
        "performance": "Find performance bottlenecks, slow queries, timeouts, and resource exhaustion.",
        "summary":     "Give a comprehensive overview: key events, error patterns, and recommendations.",
    }
    focus = analysis_prompts.get(analysis_type, analysis_prompts["summary"])

    client = CopilotClient()
    await client.start()

    try:
        # Create session with analysis tools
        session = await client.create_session({
            "model": "gpt-5-mini",
            "tools": [get_log_stats, grep_log, get_time_range, get_log_boundaries],
            "streaming": True,
            "system_message": (
                "You are a senior SRE analyzing a log file. "
                "You MUST use the provided tools to investigate before giving your final answer. "
                "Always start by calling get_log_stats and get_log_boundaries to orient yourself, "
                "then use grep_log to drill into specifics. "
                "Do not claim counts or patterns you didn't verify with tools. "
                "The tools return a RunId value; you must include that RunId in your final answer."
            ),
        })

        # Stream the assistant's response
        done = asyncio.Event()
        tool_calls_seen: list[str] = []

        def on_event(event):
            t = event.type.value
            if t == "assistant.message_delta":
                print(event.data.delta_content, end="", flush=True)
            elif ("tool" in t) and ("start" in t):
                raw_name = (
                    getattr(event.data, "tool_name", None)
                    or getattr(event.data, "name", None)
                    or getattr(event.data, "mcp_tool_name", None)
                )
                name = str(raw_name) if raw_name else "tool"
                tool_calls_seen.append(name)
                print(f"\n  [calling {name}...]", flush=True)
            elif t == "session.idle":
                done.set()

        session.on(on_event)
        await session.send({
            "prompt": (
                "Analyze this log file.\n\n"
                f"Focus: {focus}\n\n"
                "Process (required):\n"
                "1) Call get_log_stats()\n"
                "2) Call get_log_boundaries()\n"
                "3) Use grep_log() at least once for ERROR/WARN patterns\n"
                "Then write your final analysis with concrete evidence and include the exact RunId value from the tool output."
            )
        })
        await done.wait()

        # Some runtimes may not emit explicit tool execution events for local tools.
        # The assistant is required to echo the tool RunId; matching it proves tool usage.
        tools_str = ", ".join(map(str, tool_calls_seen)) if tool_calls_seen else "(see RunId match)"
        print(f"\n\nTools invoked: {tools_str}")
        print(f"RunId (local): {RUN_ID}")
        print("Analysis complete.")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
