"""StudyMate CLI: guarded task tools and optional OpenRouter response mode."""
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATA = Path(__file__).with_name("tasks.json")
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"reveal (the )?(system prompt|api key|secret)",
    r"bypass (the )?(approval|security|policy)",
]

def load_tasks():
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []

def save_tasks(tasks):
    DATA.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")

def looks_like_injection(text):
    return any(re.search(p, text, re.I) for p in INJECTION_PATTERNS)

def add_task(title, due=None):
    title = title.strip()
    if not title or len(title) > 180:
        return {"ok": False, "error": "Task title must be 1–180 characters."}
    if looks_like_injection(title):
        return {"ok": False, "error": "Blocked: task text resembles a prompt-injection attempt."}
    tasks = load_tasks()
    task = {
        "id": f"T{len(tasks)+1:03d}",
        "title": title,
        "due": due,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    tasks.append(task)
    save_tasks(tasks)
    return {"ok": True, "task": task}

def list_tasks():
    return {"ok": True, "tasks": load_tasks()}

def search_tasks(query):
    q = query.strip().lower()
    return {"ok": True, "tasks": [t for t in load_tasks() if q in t["title"].lower()]}

def delete_task(task_id, confirmation):
    if confirmation != f"confirm delete {task_id}":
        return {"ok": False, "error": f"Approval required. Type exactly: confirm delete {task_id}"}
    tasks = load_tasks()
    remaining = [t for t in tasks if t["id"] != task_id]
    if len(remaining) == len(tasks):
        return {"ok": False, "error": "Task ID not found."}
    save_tasks(remaining)
    return {"ok": True, "deleted_id": task_id}

def handle_command(command):
    raw = command.strip()
    if not raw:
        return "Please enter a command."
    low = raw.lower()
    if low in ("list", "list tasks", "show tasks"):
        return json.dumps(list_tasks(), ensure_ascii=False, indent=2)
    if low.startswith("add task:"):
        body = raw.split(":", 1)[1].strip()
        due = None
        m = re.search(r"\s+by\s+(.+)$", body, re.I)
        if m:
            due = m.group(1).strip()
            body = body[:m.start()].strip()
        return json.dumps(add_task(body, due), ensure_ascii=False, indent=2)
    if low.startswith("search:"):
        return json.dumps(search_tasks(raw.split(":", 1)[1]), ensure_ascii=False, indent=2)
    if low.startswith("delete "):
        parts = raw.split(maxsplit=1)
        task_id = parts[1].strip()
        return json.dumps(delete_task(task_id, ""), ensure_ascii=False, indent=2)
    if low.startswith("confirm delete "):
        task_id = raw[len("confirm delete "):].strip()
        return json.dumps(delete_task(task_id, raw), ensure_ascii=False, indent=2)
    if looks_like_injection(raw):
        return "Blocked: I treat instruction-like content as untrusted input."
    return ("I can help with study tasks. Commands: `add task: <title>`, "
            "`list tasks`, `search: <keyword>`, `delete <task_id>`, "
            "`confirm delete <task_id>`.")

def live_response(user_text):
    """Optional model call; task mutations remain in guarded local functions."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "replace_me":
        return "Live mode requested, but OPENROUTER_API_KEY is missing. Use offline mode or configure .env."
    try:
        import requests
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "google/gemma-3-12b-it:free",
                "messages": [
                    {"role": "system", "content": Path(__file__).with_name("AGENTS.md").read_text(encoding="utf-8")},
                    {"role": "user", "content": user_text}
                ],
                "max_tokens": 250,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"Live model request failed ({type(exc).__name__}). Try offline commands."

def main():
    print("StudyMate — Academic Task Agent")
    print("Offline mode. Commands: add task: ..., list tasks, search: ..., delete T001")
    print("Type quit to exit. Deletion requires a separate confirmation.")
    live = os.getenv("STUDYMATE_LIVE", "0") == "1"
    while True:
        try:
            command = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if command.lower() in {"quit", "exit"}:
            break
        if live and not re.match(r"^(add task:|list tasks|show tasks|search:|delete |confirm delete )", command, re.I):
            print("Agent> " + live_response(command))
        else:
            print("Agent> " + handle_command(command))

if __name__ == "__main__":
    main()
