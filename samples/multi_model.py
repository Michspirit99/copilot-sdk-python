#!/usr/bin/env python3
"""
Multi-model comparison - compare responses from different models.
Demonstrates how to query multiple models with the same prompt.
"""
import asyncio
from copilot import CopilotClient


async def query_model(client: CopilotClient, model: str, prompt: str) -> str:
    """Query a single model and return the complete response."""
    session = await client.create_session({"model": model})
    response = await session.send_and_wait({"prompt": prompt})
    result = response.data.content
    await session.destroy()
    return result


async def main():
    """Compare responses from different models."""
    models = ["gpt-4.1", "gpt-5-mini"]
    prompt = "Explain the single responsibility principle in software design in 2-3 sentences."
    
    print("🔄 Multi-Model Comparison\n")
    print(f"📝 Prompt: {prompt}\n")
    print("=" * 80 + "\n")
    
    client = CopilotClient()
    await client.start()

    try:
        # Query each model
        for model in models:
            print(f"🤖 Model: {model}")
            print("-" * 80)

            response = await query_model(client, model, prompt)
            print(response)
            print("\n" + "=" * 80 + "\n")
    finally:
        await client.stop()
    
    print("✅ Comparison complete!")


if __name__ == "__main__":
    asyncio.run(main())
