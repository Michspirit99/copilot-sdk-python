#!/usr/bin/env python3
"""
Robot Framework BDD Testing with Copilot SDK — AI-powered keyword library.

SDK features shown:
  - Robot Framework keyword library wrapping Copilot SDK
  - BDD/Gherkin-style AI agent testing (Given/When/Then)
  - Custom keywords that invoke AI, then assert on results
  - Bridging enterprise test automation with LLM-powered agents
  - Both Robot and standalone execution modes

Run with Robot Framework:
    robot samples/copilot_bdd.robot

Run standalone (no Robot required):
    python samples/robot_copilot_library.py

This file is the Python keyword library used by copilot_bdd.robot.
It also works as a standalone sample that demonstrates the same scenarios.
"""
import asyncio
import ast
import json
import re

from copilot import CopilotClient


# ── Copilot Keyword Library for Robot Framework ────────────────────────


class CopilotLibrary:
    """Robot Framework keyword library that wraps Copilot SDK actions.

    Robot Framework discovers this class and makes each method available
    as a keyword.  Example: 'Start Copilot Session' maps to
    ``start_copilot_session()``.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self._client = None
        self._session = None
        self._last_response = ""
        self._last_code = ""

    # ── Lifecycle keywords ──

    def start_copilot_session(self, model: str = "gpt-5-mini"):
        """Start a new Copilot client and session.

        Example (Robot):
            Start Copilot Session    gpt-5-mini
        """
        loop = _get_event_loop()
        self._client = CopilotClient()
        loop.run_until_complete(self._client.start())
        self._session = loop.run_until_complete(
            self._client.create_session({"model": model})
        )

    def stop_copilot_session(self):
        """Tear down session and client."""
        loop = _get_event_loop()
        if self._session:
            loop.run_until_complete(self._session.destroy())
        if self._client:
            loop.run_until_complete(self._client.stop())
        self._session = None
        self._client = None

    # ── Action keywords ──

    def ask_copilot(self, prompt: str) -> str:
        """Send a prompt and store the response.

        Example (Robot):
            ${response}=    Ask Copilot    Explain recursion in one sentence
        """
        if not self._session:
            raise RuntimeError("Call 'Start Copilot Session' first")
        loop = _get_event_loop()
        response = loop.run_until_complete(
            self._session.send_and_wait({"prompt": prompt})
        )
        self._last_response = response.data.content
        return self._last_response

    def ask_copilot_to_generate_code(self, description: str) -> str:
        """Ask Copilot to generate Python code and extract the code block.

        Example (Robot):
            ${code}=    Ask Copilot To Generate Code    a Fibonacci function
        """
        prompt = (
            f"Write Python code: {description}\n"
            "Return ONLY the code inside a ```python code block."
        )
        raw = self.ask_copilot(prompt)
        self._last_code = _extract_code_block(raw)
        return self._last_code

    def ask_copilot_to_review_code(self, code: str) -> str:
        """Ask Copilot to review the given code.

        Example (Robot):
            ${review}=    Ask Copilot To Review Code    ${code}
        """
        prompt = f"Review this Python code for bugs. Be specific:\n\n```python\n{code}\n```"
        return self.ask_copilot(prompt)

    def ask_copilot_to_generate_json(self, description: str) -> str:
        """Ask Copilot to generate a JSON object.

        Example (Robot):
            ${json}=    Ask Copilot To Generate JSON    a user profile with name, age, email
        """
        prompt = (
            f"Generate a JSON object: {description}. "
            "Return ONLY the raw JSON object, no markdown."
        )
        raw = self.ask_copilot(prompt)
        # Strip markdown fences if present
        clean = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
        clean = re.sub(r"\n?```\s*$", "", clean)
        self._last_response = clean
        return clean

    # ── Assertion keywords ──

    def response_should_contain(self, text: str):
        """Assert that the last response contains the given text (case-insensitive).

        Example (Robot):
            Response Should Contain    fibonacci
        """
        if text.lower() not in self._last_response.lower():
            raise AssertionError(
                f"Expected response to contain '{text}'.\n"
                f"Got: {self._last_response[:300]}"
            )

    def code_should_be_valid_python(self):
        """Assert that the last generated code parses as valid Python.

        Example (Robot):
            Code Should Be Valid Python
        """
        try:
            ast.parse(self._last_code)
        except SyntaxError as e:
            raise AssertionError(
                f"Invalid Python syntax: {e}\n\nCode:\n{self._last_code}"
            )

    def code_should_define_function(self, function_name: str):
        """Assert that the generated code defines a function with the given name.

        Example (Robot):
            Code Should Define Function    fibonacci
        """
        try:
            tree = ast.parse(self._last_code)
        except SyntaxError as e:
            raise AssertionError(f"Code is not valid Python: {e}")

        func_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        matches = [n for n in func_names if function_name.lower() in n.lower()]
        if not matches:
            raise AssertionError(
                f"Expected function '{function_name}' but found: {func_names}\n\n"
                f"Code:\n{self._last_code}"
            )

    def response_should_mention_bug(self, *keywords):
        """Assert that a code review mentions at least one of the given keywords.

        Example (Robot):
            Response Should Mention Bug    zero    empty    division
        """
        lower = self._last_response.lower()
        found = [kw for kw in keywords if kw.lower() in lower]
        if not found:
            raise AssertionError(
                f"Expected review to mention one of {list(keywords)}.\n"
                f"Got: {self._last_response[:300]}"
            )

    def json_should_be_valid(self) -> dict:
        """Assert that the last response is valid JSON and return the parsed dict."""
        try:
            data = json.loads(self._last_response)
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"Invalid JSON: {e}\n\nRaw:\n{self._last_response[:300]}"
            )

        if not isinstance(data, dict):
            raise AssertionError(
                f"Expected JSON object (dict), but got {type(data).__name__}.\n"
                f"Value: {str(data)[:300]}"
            )
        return data

    def json_should_have_keys(self, *keys):
        """Assert that the parsed JSON contains all specified keys.

        Example (Robot):
            JSON Should Have Keys    name    age    email
        """
        data = self.json_should_be_valid()
        # json_should_be_valid() already asserts isinstance(data, dict)
        missing = set(keys) - set(data.keys())
        if missing:
            raise AssertionError(
                f"Missing JSON keys: {missing}.\nGot: {list(data.keys())}"
            )


# ── Helpers ─────────────────────────────────────────────────────────────


def _get_event_loop():
    """Get or create an event loop (works across Robot / standalone)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _extract_code_block(text: str, language: str = "python") -> str:
    pattern = rf"```{language}\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


# ── Standalone runner (BDD narrative printed to stdout) ─────────────────

SCENARIOS = [
    {
        "name": "Code Generation",
        "given": "I have a Copilot SDK session",
        "when": 'I ask Copilot to write a "fibonacci" function',
        "then": [
            "the response should contain valid Python",
            "the code should define a function named 'fibonacci'",
        ],
    },
    {
        "name": "Bug Detection in Code Review",
        "given": "I have a Copilot SDK session",
        "when": "I ask Copilot to review code with a division-by-zero bug",
        "then": [
            "the review should mention the bug",
            "the response should reference 'zero' or 'empty'",
        ],
    },
    {
        "name": "Structured JSON Output",
        "given": "I have a Copilot SDK session",
        "when": 'I ask Copilot to generate a user profile in JSON',
        "then": [
            "the output should be valid JSON",
            "the JSON should contain 'name', 'age', and 'email'",
        ],
    },
]


async def main():
    """Run BDD scenarios in standalone mode (no Robot Framework required)."""
    print("🤖 Robot Framework BDD Testing — Copilot SDK\n")
    print("Demonstrates BDD-style AI agent testing:")
    print("  - Given/When/Then scenarios for AI behaviour")
    print("  - Python keyword library wrapping the Copilot SDK")
    print("  - Robot Framework .robot file for enterprise test suites")
    print("  - Standalone runner for CI (this script)\n")

    # In standalone mode, use async SDK directly (not the sync library wrappers)
    client = CopilotClient()
    await client.start()

    passed = 0
    failed = 0

    try:
        session = await client.create_session({
            "model": "gpt-5-mini",
            "system_message": "You are a helpful coding assistant. Be concise.",
        })

        for scenario in SCENARIOS:
            print(f"Scenario: {scenario['name']}")
            print(f"  Given {scenario['given']}")
            print(f"  When  {scenario['when']}")

            try:
                if "fibonacci" in scenario["when"]:
                    prompt = (
                        "Write Python code: a recursive function named 'fibonacci' "
                        "that returns the nth Fibonacci number.\n"
                        "Return ONLY the code inside a ```python code block."
                    )
                    response = await session.send_and_wait({"prompt": prompt})
                    code = _extract_code_block(response.data.content)
                    tree = ast.parse(code)
                    func_names = [
                        n.name for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    matches = [n for n in func_names if "fib" in n.lower()]
                    if not matches:
                        raise AssertionError(f"No fibonacci function found: {func_names}")
                    detail = f"Generated code:\n{code[:200]}"

                elif "division-by-zero" in scenario["when"]:
                    buggy = (
                        "def calculate_average(numbers):\n"
                        "    total = sum(numbers)\n"
                        "    return total / len(numbers)\n"
                    )
                    prompt = f"Review this Python code for bugs. Be specific:\n\n```python\n{buggy}\n```"
                    response = await session.send_and_wait({"prompt": prompt})
                    review = response.data.content.lower()
                    keywords = ["zero", "empty", "division", "len"]
                    found = [kw for kw in keywords if kw in review]
                    if not found:
                        raise AssertionError("Bug not detected in review")
                    detail = f"Review:\n{response.data.content[:200]}"

                elif "JSON" in scenario["when"]:
                    prompt = (
                        "Generate a JSON object: a user profile with name (string), "
                        "age (integer), email (string). Return ONLY the raw JSON object, no markdown."
                    )
                    response = await session.send_and_wait({"prompt": prompt})
                    raw = response.data.content.strip()
                    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
                    raw = re.sub(r"\n?```\s*$", "", raw)
                    data = json.loads(raw)
                    missing = {"name", "age", "email"} - set(data.keys())
                    if missing:
                        raise AssertionError(f"Missing keys: {missing}")
                    detail = f"JSON:\n{json.dumps(data, indent=2)[:200]}"
                else:
                    detail = "Unknown scenario"
                    raise ValueError(detail)

                for then_step in scenario["then"]:
                    print(f"  Then  {then_step}  ✅")
                print("  Result: PASS")
                print(f"  {detail}")
                passed += 1

            except (AssertionError, Exception) as e:
                for then_step in scenario["then"]:
                    print(f"  Then  {then_step}")
                print(f"  Result: FAIL — {e}")
                failed += 1

            print()

        await session.destroy()

    finally:
        await client.stop()

    total = len(SCENARIOS)
    print(f"BDD Results: {passed} passed, {failed} failed out of {total}")
    if failed == 0:
        print("\n✅ All BDD scenarios passed!")
    else:
        print("\n⚠️  Some scenarios failed")


if __name__ == "__main__":
    asyncio.run(main())
