import re


MAX_MEMORY_ENTRIES = 6
MAX_QUESTION_CHARS = 120
MAX_FINDING_CHARS = 160


def _clean(text):
    text = re.sub(r"[#*`>_]+", "", text or "")
    return re.sub(r"[ \t]+", " ", text).strip()


def _truncate(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _headline(text):
    """First substantive sentence of a reply, skipping label-only lines."""
    lines = [line.strip() for line in _clean(text).splitlines() if line.strip()]
    chosen = next((line for line in lines if len(line.split()) >= 5), lines[0] if lines else "")
    return re.split(r"(?<=[.!?])\s", chosen, maxsplit=1)[0]


def build_session_memory(messages, recent_count):
    """Summarise turns older than the last `recent_count` messages, one line each.

    Messages inside the recent window are sent in full elsewhere, so they are not repeated here.
    """
    kept = [m for m in messages if m.get("content")]
    older = kept[:-recent_count] if recent_count else kept
    entries = []
    question = None
    for message in older:
        if message["role"] == "user":
            question = _truncate(_clean(message["content"]), MAX_QUESTION_CHARS)
        elif question is not None:
            finding = _truncate(_headline(message["content"]), MAX_FINDING_CHARS)
            entries.append(f"- Asked: {question} | Found: {finding}")
            question = None
    return "\n".join(entries[-MAX_MEMORY_ENTRIES:])
