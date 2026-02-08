#!/usr/bin/env python3
"""
Multi-turn agentic workflow - a task-tracking assistant that maintains
state across conversation turns using custom tools.

SDK features shown:
  - @define_tool with Pydantic models
  - Multi-turn conversations (multiple send calls in one session)
  - Tool state persisted across turns
  - Streaming output with event handlers
"""
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool


# ── In-memory task store (persists across conversation turns) ────────────

tasks: dict[int, dict] = {}
next_id: int = 1


# ── Tool parameter models ───────────────────────────────────────────────

class AddTaskParams(BaseModel):
    title: str = Field(description="Short title for the task")
    priority: str = Field(
        description="Priority level: high, medium, or low",
        default="medium",
    )


class UpdateTaskParams(BaseModel):
    task_id: int = Field(description="ID of the task to update")
    status: str = Field(description="New status: todo, in-progress, or done")


class DeleteTaskParams(BaseModel):
    task_id: int = Field(description="ID of the task to delete")


# ── Tool definitions ────────────────────────────────────────────────────

@define_tool(description="Add a new task to the tracker")
def add_task(params: AddTaskParams) -> str:
    global next_id
    task = {
        "id": next_id,
        "title": params.title,
        "priority": params.priority,
        "status": "todo",
        "created": datetime.now().strftime("%H:%M:%S"),
    }
    tasks[next_id] = task
    next_id += 1
    return f"Created task #{task['id']}: {task['title']} [{task['priority']}]"


@define_tool(description="List all tasks with their status and priority")
def list_tasks() -> str:
    if not tasks:
        return "No tasks yet."
    lines = []
    icons = {"todo": "⬜", "in-progress": "🔄", "done": "✅"}
    for t in tasks.values():
        icon = icons.get(t["status"], "❓")
        lines.append(f"  {icon} #{t['id']} [{t['priority']}] {t['title']} ({t['status']})")
    return "\n".join(lines)


@define_tool(description="Update the status of an existing task")
def update_task(params: UpdateTaskParams) -> str:
    if params.task_id not in tasks:
        return f"Task #{params.task_id} not found."
    tasks[params.task_id]["status"] = params.status
    return f"Task #{params.task_id} updated to '{params.status}'."


@define_tool(description="Delete a task by ID")
def delete_task(params: DeleteTaskParams) -> str:
    if params.task_id not in tasks:
        return f"Task #{params.task_id} not found."
    removed = tasks.pop(params.task_id)
    return f"Deleted task #{removed['id']}: {removed['title']}"


# ── Agent loop ───────────────────────────────────────────────────────────

async def main():
    """Run a multi-turn task management agent."""
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({
            "model": "gpt-5-mini",
            "streaming": True,
            "tools": [add_task, list_tasks, update_task, delete_task],
            "system_message": {
                "content": (
                    "You are a task management assistant. Use the provided tools "
                    "to manage tasks. Always use list_tasks after modifications "
                    "so the user can see the current state. Be concise."
                ),
            },
        })

        # Register the event handler ONCE for the entire session
        done = asyncio.Event()

        def on_event(event):
            if event.type.value == "assistant.message_delta":
                print(event.data.delta_content, end="", flush=True)
            elif event.type.value == "session.idle":
                done.set()

        session.on(on_event)

        print("Task Agent — manages tasks across conversation turns.")
        print("Type 'exit' to quit.\n")

        # ── Scripted turns ──────────────────────────────────────────────
        turns = [
            "Add three tasks: 'Design database schema' (high), 'Write unit tests' (medium), 'Update README' (low)",
            "Mark 'Design database schema' as in-progress and show all tasks",
            "Add a new high-priority task 'Fix authentication bug', then mark 'Write unit tests' as done",
            "Show me a summary of what's left to do",
        ]

        for i, prompt in enumerate(turns, 1):
            print(f"{'─' * 60}")
            print(f"Turn {i}: {prompt}\n")
            print("Agent: ", end="")
            done.clear()
            await session.send({"prompt": prompt})
            await done.wait()
            print("\n")

        # ── Interactive mode ────────────────────────────────────────────
        print(f"{'─' * 60}")
        print("Now in interactive mode — continue managing tasks.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            print("Agent: ", end="")
            done.clear()
            await session.send({"prompt": user_input})
            await done.wait()
            print("\n")

        await session.destroy()

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
