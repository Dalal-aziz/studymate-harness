
"""Persistent memory and retrieval for StudyMate."""
import json
from pathlib import Path
from datetime import datetime, timezone

MEMORY_FILE = Path(__file__).with_name("memory.json")
MAX_MEMORIES = 500


def load_memories():
    """Load saved memories safely."""
    if not MEMORY_FILE.exists():
        return []
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def remember(text: str, category: str = "general") -> dict:
    """Save a non-empty memory with a timestamp."""
    text = text.strip()
    category = category.strip() or "general"

    if not text or len(text) > 1000:
        return {"ok": False, "error": "Memory must contain 1–1000 characters."}

    memories = load_memories()
    memory = {
        "id": f"M{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "text": text,
        "category": category[:60],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    memories.append(memory)
    memories = memories[-MAX_MEMORIES:]

    MEMORY_FILE.write_text(
        json.dumps(memories, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"ok": True, "memory": memory}


def recall(query: str, limit: int = 5) -> dict:
    """Retrieve memories matching query words."""
    query_words = set(query.lower().split())
    if not query_words:
        return {"ok": True, "memories": []}

    scored = []
    for memory in load_memories():
        text_words = set(memory.get("text", "").lower().split())
        category_words = set(memory.get("category", "").lower().split())
        score = len(query_words & (text_words | category_words))
        if score:
            scored.append((score, memory))

    scored.sort(key=lambda item: item[0], reverse=True)
    return {
        "ok": True,
        "memories": [memory for _, memory in scored[:max(1, min(limit, 20))]],
    }


def clear_memory(memory_id: str, confirmation: str = "") -> dict:
    """Delete a memory only with exact confirmation."""
    if confirmation != f"confirm delete {memory_id}":
        return {
            "ok": False,
            "error": f"Approval required: confirm delete {memory_id}",
        }

    memories = load_memories()
    remaining = [m for m in memories if m.get("id") != memory_id]

    if len(remaining) == len(memories):
        return {"ok": False, "error": "Memory ID not found."}

    MEMORY_FILE.write_text(
        json.dumps(remaining, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"ok": True, "deleted_id": memory_id}
