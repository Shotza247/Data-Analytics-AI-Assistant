import re


MAX_MEMORY_ENTRIES = 6
MAX_QUESTION_CHARS = 120
MAX_FINDING_CHARS = 160
MAX_CHART_CHARS = 80
MAX_CAVEAT_CHARS = 100
MIN_SENTENCE_WORDS = 5

CAVEAT_RE = re.compile(
    r"\b(however|caveat|limited|limitation|correlation|causation|small sample|"
    r"not enough|cannot|may not|might not|should be treated|interpret with caution)\b",
    re.IGNORECASE,
)
CHART_TITLE_RE = re.compile(r"title=(['\"])(.*?)\1, x_axis=")


def _clean(text):
    text = re.sub(r"[#*`>_]+", "", text or "")
    return re.sub(r"[ \t]+", " ", text).strip()


def _truncate(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _sentences(text):
    sentences = []
    for line in _clean(text).splitlines():
        for sentence in re.split(r"(?<=[.!?])\s+", line.strip()):
            if len(sentence.split()) >= MIN_SENTENCE_WORDS:
                sentences.append(sentence)
    return sentences


def build_memory_note(content, chart_metadata=()):
    """One-line note for an answer: the finding, the chart title, and a caveat if present."""
    sentences = _sentences(content)
    if not sentences:
        return ""
    finding = next((s for s in sentences if re.search(r"\d", s)), sentences[0])
    parts = [f"Found: {_truncate(finding, MAX_FINDING_CHARS)}"]

    for entry in chart_metadata:
        match = CHART_TITLE_RE.search(entry)
        if match and match.group(2).strip():
            parts.append(f"Chart: {_truncate(match.group(2), MAX_CHART_CHARS)}")
            break

    caveat = next((s for s in sentences if s != finding and CAVEAT_RE.search(s)), None)
    if caveat:
        parts.append(f"Caveat: {_truncate(caveat, MAX_CAVEAT_CHARS)}")
    return " | ".join(parts)


def build_session_memory(messages, recent_count):
    """Summarise turns older than the last `recent_count` messages, one line each.

    Messages inside the recent window are sent in full elsewhere, so they are not repeated here.
    An assistant message with an empty `memory_note` (for example a PDF approval prompt) is skipped.
    """
    kept = [m for m in messages if m.get("content")]
    older = kept[:-recent_count] if recent_count else kept
    entries = []
    question = None
    for message in older:
        if message["role"] == "user":
            question = _truncate(_clean(message["content"]), MAX_QUESTION_CHARS)
        elif question is not None:
            if "memory_note" in message:
                note = message["memory_note"]
            else:
                note = build_memory_note(message["content"])
            if note:
                entries.append(f"- Asked: {question} | {note}")
            question = None
    return "\n".join(entries[-MAX_MEMORY_ENTRIES:])
