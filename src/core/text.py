"""Utilities for normalizing Italian commands and user input."""

import unicodedata


def normalize_text(text: str) -> str:
    """Return lowercase text without accents and surrounding whitespace."""
    normalized = unicodedata.normalize("NFD", text.casefold().strip())
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )
