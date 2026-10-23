"""Parsing helpers for dates and cities in weather requests."""

import re
from datetime import date, timedelta

from core.text import normalize_text


MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

WEEKDAYS = {
    "lunedi": 0,
    "martedi": 1,
    "mercoledi": 2,
    "giovedi": 3,
    "venerdi": 4,
    "sabato": 5,
    "domenica": 6,
}


def extract_weather_city(text: str) -> str | None:
    match = re.search(r"\ba\s+([a-z]+(?:\s+[a-z]+)?)\s*[?.!,]*$", normalize_text(text))
    if not match:
        return None

    city = match.group(1).strip()
    if city in {"oggi", "domani", "dopodomani", *WEEKDAYS}:
        return None
    return city.title()


def interpret_weather_date(text: str, today: date | None = None) -> date | None:
    normalized = normalize_text(text)
    today = today or date.today()

    if "dopodomani" in normalized:
        return today + timedelta(days=2)
    if "domani" in normalized:
        return today + timedelta(days=1)
    if "oggi" in normalized:
        return today

    numeric = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b", normalized)
    if numeric:
        day, month = int(numeric.group(1)), int(numeric.group(2))
        year = int(numeric.group(3)) if numeric.group(3) else today.year
        try:
            requested = date(year, month, day)
        except ValueError:
            return None
        if numeric.group(3) is None and requested < today:
            requested = date(year + 1, month, day)
        return requested

    for month_name, month_number in MONTHS.items():
        named = re.search(rf"\b(\d{{1,2}})\s+{month_name}(?:\s+(\d{{4}}))?\b", normalized)
        if named:
            day = int(named.group(1))
            year = int(named.group(2)) if named.group(2) else today.year
            try:
                requested = date(year, month_number, day)
            except ValueError:
                return None
            if named.group(2) is None and requested < today:
                requested = date(year + 1, month_number, day)
            return requested

    for name, weekday in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", normalized):
            days_ahead = (weekday - today.weekday()) % 7 or 7
            return today + timedelta(days=days_ahead)
    return None
