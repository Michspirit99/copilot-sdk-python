#!/usr/bin/env python3
"""
Git commit message writer - generate commit messages from staged changes.
"""
import asyncio
import subprocess
from copilot import CopilotClient


def get_git_diff() -> str:
    """Get the current git diff of staged changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        return result.stdout or ""
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e}")
    except FileNotFoundError:
        raise RuntimeError("Git is not installed or not in PATH")


async def main():
    """Generate a commit message from staged git changes."""
    try:
        diff = get_git_diff()
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        return
    
    if not diff.strip():
        print("⚠️  No staged changes found. Use 'git add' to stage changes first.")
        return
    
    print("📝 Analyzing staged changes...\n")
    
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-5-mini"})

        prompt = f"""Based on these git changes, write a clear, conventional commit message.

Format:
<type>(<scope>): <subject>

<body (optional)>

Types: feat, fix, docs, style, refactor, test, chore

Changes:
```diff
{diff}
```

Write only the commit message, no explanations."""

        print("🤖 Suggested commit message:\n")
        print("-" * 60)

        response = await session.send_and_wait({"prompt": prompt})
        print(response.data.content)

        print("-" * 60)
        print("\n💡 To use this message:")
        print("   git commit -m '<message>'")
        print("\n✅ Done!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
