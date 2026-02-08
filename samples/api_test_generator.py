#!/usr/bin/env python3
"""
API test generator - generate test cases from OpenAPI/Swagger specifications.
"""
import asyncio
import sys
import json
from pathlib import Path
from copilot import CopilotClient


def parse_openapi(spec_content: str) -> str:
    """Parse OpenAPI spec and extract endpoints."""
    try:
        spec = json.loads(spec_content)
        paths = spec.get('paths', {})
        endpoints = []
        
        for path, methods in paths.items():
            for method in methods.keys():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoints.append(f"{method.upper()} {path}")
        
        return f"Found {len(endpoints)} endpoints:\n" + "\n".join(endpoints[:20])
    except json.JSONDecodeError as e:
        return f"Error parsing OpenAPI spec: {str(e)}"


async def main():
    """Generate API tests from OpenAPI spec."""
    if len(sys.argv) < 2:
        print("Usage: python api_test_generator.py <spec-path> [format]")
        print("\nFormats:")
        print("  pytest   - Generate pytest test cases (default)")
        print("  postman  - Generate Postman collection")
        print("  curl     - Generate curl commands")
        print("\nExamples:")
        print("  python api_test_generator.py swagger.json")
        print("  python api_test_generator.py openapi.yaml pytest")
        sys.exit(1)
    
    spec_path = Path(sys.argv[1])
    format_type = sys.argv[2].lower() if len(sys.argv) > 2 else "pytest"
    
    if not spec_path.exists():
        print(f"❌ Error: File not found: {spec_path}")
        sys.exit(1)
    
    # Read spec
    spec_content = spec_path.read_text(encoding='utf-8')
    
    print(f"📋 OpenAPI Spec: {spec_path.name}")
    print(f"🧪 Format: {format_type}\n")
    
    # Pre-parse endpoints
    endpoint_summary = parse_openapi(spec_content)
    
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-5-mini"})

        format_instructions = {
            'pytest': "Generate pytest test cases with fixtures, assertions, and test data.",
            'postman': "Generate a Postman collection JSON with requests for all endpoints.",
            'curl': "Generate curl commands for testing each endpoint."
        }

        prompt = f"""Generate API tests from this OpenAPI specification.

Format: {format_type}
{format_instructions.get(format_type, format_instructions['pytest'])}

Endpoint summary:
{endpoint_summary}

OpenAPI Spec:
```json
{spec_content[:3000]}
```

Generate comprehensive tests."""

        print("🤖 Generated Tests:\n")
        print("-" * 80)
        response = await session.send_and_wait({"prompt": prompt})
        print(response.data.content)
        print("-" * 80)
        print("\n✅ Test generation complete!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
