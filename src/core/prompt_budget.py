"""Small dependency-free helpers for keeping prompts within a token budget.

The character estimate is deliberately approximate and is not a provider tokenizer.
"""

from math import ceil


CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate tokens without downloading or installing a model tokenizer."""
    return ceil(len(text) / CHARS_PER_TOKEN)


def compact_history(messages, token_budget: int, chars_per_token: int = CHARS_PER_TOKEN):
    """Keep the newest whole history messages that fit a rough token budget."""
    if token_budget <= 0 or not messages:
        return []
    char_budget = max(0, token_budget * chars_per_token - 24)
    kept = []
    used = 0
    for message in reversed(messages):
        content = message.get("content", "")
        if not isinstance(content, str):
            continue
        cost = len(content) + 12  # reserve room for role/message framing
        if used + cost > char_budget:
            if not kept and char_budget > 12:
                message = {**message, "content": content[-(char_budget - 12):]}
                kept.append(message)
            break
        kept.append(message)
        used += cost
    kept.reverse()
    return kept


def compact_facts(facts, max_chars: int = 1400):
    """Serialize as many key/value pairs as fit, preserving mapping order."""
    import json

    selected = {}
    for key, value in facts.items():
        candidate = {**selected, key: value}
        serialized = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
        if len(serialized) > max_chars:
            continue
        selected = candidate
    return json.dumps(selected, ensure_ascii=False, separators=(",", ":"))
