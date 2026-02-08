#!/usr/bin/env python3
"""
Playwright AI Agent - browser automation guided by Copilot.
Requires: pip install playwright && python -m playwright install chromium
"""
import asyncio
import sys
from copilot import CopilotClient


async def main():
    """Run the Playwright AI agent."""
    if len(sys.argv) < 2:
        print("Usage: python playwright_agent.py <url> [task]")
        print("\nExamples:")
        print("  python playwright_agent.py https://example.com")
        print('  python playwright_agent.py https://github.com "Find trending repositories"')
        sys.exit(1)
    
    url = sys.argv[1]
    task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Describe what you see on the page"
    
    print("🌐 Playwright AI Agent")
    print(f"📍 Target: {url}")
    print(f"🎯 Task: {task}\n")

    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError:
        print("❌ This sample requires Playwright.")
        print("   Install it with:")
        print("     pip install playwright")
        print("     python -m playwright install chromium")
        sys.exit(1)
    
    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the URL
            await page.goto(url)
            page_title = await page.title()
            page_content = await page.content()
            print(f"✅ Loaded: {page_title}\n")
            
            # Set up Copilot
            client = CopilotClient()
            await client.start()

            try:
                session = await client.create_session({"model": "gpt-5-mini"})

                prompt = f"""You are a browser automation agent. Current page: {url}
Page title: {page_title}

Page HTML (excerpt):
```html
{page_content[:3000]}
```

Task: {task}

Analyze the page content and complete the task."""

                print("🤖 Agent:\n")
                response = await session.send_and_wait({"prompt": prompt})
                print(response.data.content)
                print("\n✅ Task complete!")

                await session.destroy()
            finally:
                await client.stop()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
