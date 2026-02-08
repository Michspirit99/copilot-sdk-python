#!/usr/bin/env python3
"""
Custom tools example - define Python functions that Copilot can call.
Demonstrates tool/function calling with the Copilot SDK.
"""
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool


# Define custom tools using Pydantic models for parameters


class CalculateParams(BaseModel):
    expression: str = Field(description="A mathematical expression to evaluate")


class ReverseStringParams(BaseModel):
    text: str = Field(description="The string to reverse")


@define_tool(description="Get the current time in ISO format")
def get_current_time() -> str:
    return datetime.now().isoformat()


@define_tool(description="Safely evaluate a mathematical expression")
def calculate(params: CalculateParams) -> str:
    try:
        # Only allow safe math operations
        result = eval(params.expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@define_tool(description="Reverse a string")
def reverse_string(params: ReverseStringParams) -> str:
    return params.text[::-1]


async def main():
    """Demonstrate custom tools with Copilot."""
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({
            "model": "gpt-5-mini",
            "tools": [get_current_time, calculate, reverse_string],
        })

        print("🔧 Copilot with Custom Tools\n")
        print("Available tools:")
        print("  - get_current_time()")
        print("  - calculate(expression)")
        print("  - reverse_string(text)\n")

        prompt = """Please:
1. Tell me the current time
2. Calculate 42 * 137
3. Reverse the string 'Hello Copilot'
"""

        print(f"📝 Task: {prompt}\n")
        print("🤖 Response:\n")

        response = await session.send_and_wait({"prompt": prompt})
        print(response.data.content)

        print("\n✅ Done!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
