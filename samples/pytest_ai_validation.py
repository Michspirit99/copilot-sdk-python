#!/usr/bin/env python3
"""
AI-Enhanced Testing with pytest — use Copilot SDK as an intelligent test oracle.

SDK features shown:
  - pytest fixtures for Copilot client/session lifecycle
  - AI-as-judge pattern (one AI call validates another's output)
  - Combining deterministic assertions (ast.parse, json.loads) with AI validation
  - Reusable async test scenarios for both pytest and standalone execution

Run with pytest:
    pytest samples/pytest_ai_validation.py -v

Run standalone:
    python samples/pytest_ai_validation.py
"""
import asyncio
import ast
import json
import re

from copilot import CopilotClient


# ── Helpers ─────────────────────────────────────────────────────────────


def extract_code_block(text: str, language: str = "python") -> str:
    """Extract a fenced code block from a markdown-formatted AI response."""
    pattern = rf"```{language}\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: any fenced block
    match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


async def ai_judge(session, content: str, criteria: str) -> tuple[bool, str]:
    """AI-as-judge: ask the model to evaluate content against criteria.

    Returns (passed, explanation).
    """
    prompt = (
        "You are a strict test validator. Evaluate the content against the criteria.\n"
        "Respond with EXACTLY 'PASS' or 'FAIL' on the first line, "
        "followed by a one-line explanation.\n\n"
        f"Content:\n{content[:500]}\n\n"
        f"Criteria: {criteria}"
    )
    response = await session.send_and_wait({"prompt": prompt})
    result = response.data.content.strip()
    passed = result.upper().startswith("PASS")
    return passed, result


# ── Test Scenarios (shared by pytest and standalone runner) ─────────────


async def scenario_code_generation(session) -> tuple[bool, str]:
    """AI-generated code must be syntactically valid Python."""
    response = await session.send_and_wait({
        "prompt": (
            "Write a Python function called 'fibonacci' that returns the "
            "nth Fibonacci number using recursion.\n"
            "Return ONLY the code in a ```python code block."
        )
    })
    code = extract_code_block(response.data.content)

    try:
        tree = ast.parse(code)
        func_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        has_target = any("fib" in n.lower() for n in func_names)
        if has_target:
            return True, f"Valid Python with function(s): {func_names}\n\n{code}"
        return False, f"Parsed OK but no fibonacci function found: {func_names}\n\n{code}"
    except SyntaxError as e:
        return False, f"SyntaxError: {e}\n\nGenerated code:\n{code}"


async def scenario_bug_detection(session) -> tuple[bool, str]:
    """AI code review should detect an obvious division-by-zero bug."""
    buggy_code = (
        "def calculate_average(numbers):\n"
        "    total = 0\n"
        "    for num in numbers:\n"
        "        total += num\n"
        "    return total / len(numbers)  # crashes if list is empty\n"
    )
    response = await session.send_and_wait({
        "prompt": (
            "Review this Python code for bugs. Be specific:\n\n"
            f"```python\n{buggy_code}```"
        )
    })
    review = response.data.content.lower()
    keywords = ["zero", "empty", "division", "len"]
    found = [kw for kw in keywords if kw in review]

    if found:
        return True, f"Bug detected (keywords: {found})\n\n{response.data.content[:300]}"
    return False, f"Bug NOT detected.\n\n{response.data.content[:300]}"


async def scenario_structured_output(session) -> tuple[bool, str]:
    """AI should produce valid JSON matching an expected schema."""
    response = await session.send_and_wait({
        "prompt": (
            "Generate a JSON object for a user profile with these exact fields: "
            '"name" (string), "age" (integer), "email" (string). '
            "Return ONLY the raw JSON object, no markdown."
        )
    })
    raw = response.data.content.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)

    try:
        data = json.loads(raw)
        required = {"name", "age", "email"}
        missing = required - set(data.keys())
        if missing:
            return False, f"Missing keys: {missing}\nGot: {data}"

        checks = []
        if isinstance(data.get("name"), str):
            checks.append("name:str")
        if isinstance(data.get("age"), int):
            checks.append("age:int")
        if isinstance(data.get("email"), str) and "@" in data["email"]:
            checks.append("email:valid")

        return True, f"Valid JSON  |  Checks: {', '.join(checks)}\n{json.dumps(data, indent=2)}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}\n\nRaw:\n{raw[:300]}"


async def scenario_ai_judge_relevance(session) -> tuple[bool, str]:
    """AI-as-judge validates that a response is topically relevant."""
    response = await session.send_and_wait({
        "prompt": "Explain what a Python decorator is in 2-3 sentences."
    })
    explanation = response.data.content

    passed, verdict = await ai_judge(
        session,
        explanation,
        "The content should explain Python decorators accurately. "
        "It should mention wrapping functions or modifying behavior.",
    )
    return passed, f"AI Judge: {verdict}\n\nOriginal:\n{explanation[:200]}"


# ── pytest integration (only when pytest is installed) ──────────────────

try:
    import pytest
    import pytest_asyncio

    @pytest_asyncio.fixture
    async def copilot_session():
        """Fixture: create a Copilot session for each test."""
        client = CopilotClient()
        await client.start()
        session = await client.create_session({"model": "gpt-5-mini"})
        yield session
        await session.destroy()
        await client.stop()

    @pytest.mark.asyncio
    async def test_code_generation_produces_valid_python(copilot_session):
        """AI-generated code must be syntactically valid."""
        passed, detail = await scenario_code_generation(copilot_session)
        assert passed, detail

    @pytest.mark.asyncio
    async def test_code_review_detects_bugs(copilot_session):
        """AI code review should catch the division-by-zero bug."""
        passed, detail = await scenario_bug_detection(copilot_session)
        assert passed, detail

    @pytest.mark.asyncio
    async def test_structured_json_output(copilot_session):
        """AI should produce valid JSON with expected schema."""
        passed, detail = await scenario_structured_output(copilot_session)
        assert passed, detail

    @pytest.mark.asyncio
    async def test_ai_judge_validates_relevance(copilot_session):
        """AI-as-judge should confirm response relevance."""
        passed, detail = await scenario_ai_judge_relevance(copilot_session)
        assert passed, detail

except ImportError:
    # pytest / pytest-asyncio not installed — standalone mode only
    pass


# ── Standalone runner (E2E compatible) ──────────────────────────────────

SCENARIOS = [
    ("Code Generation -> Valid Python", scenario_code_generation),
    ("Bug Detection -> Finds Division-by-Zero", scenario_bug_detection),
    ("Structured Output -> Valid JSON Schema", scenario_structured_output),
    ("AI-as-Judge -> Response Relevance", scenario_ai_judge_relevance),
]


async def main():
    """Run AI validation tests in standalone mode."""
    print("🧪 pytest AI Validation — Copilot SDK\n")
    print("Demonstrates AI-enhanced testing patterns:")
    print("  - Deterministic assertions on AI output (ast.parse, json.loads)")
    print("  - AI-as-judge pattern (one AI call validates another)")
    print("  - Reusable scenarios for pytest + standalone execution\n")

    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({
            "model": "gpt-5-mini",
            "system_message": "You are a helpful coding assistant. Be concise.",
        })

        passed = 0
        failed = 0

        for name, scenario_fn in SCENARIOS:
            print(f"--- {name} ---")
            try:
                ok, detail = await scenario_fn(session)
                status = "PASS" if ok else "FAIL"
                marker = "✅" if ok else "❌"
                print(f"  {marker} {status}")
                for line in detail.split("\n"):
                    if line.strip():
                        print(f"  {line}")
                if ok:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                failed += 1
            print()

        await session.destroy()

        total = len(SCENARIOS)
        print(f"Results: {passed} passed, {failed} failed out of {total}")
        if failed == 0:
            print("\n✅ All AI validation tests passed!")
        else:
            print("\n⚠️  Some tests failed (AI responses are non-deterministic)")

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
