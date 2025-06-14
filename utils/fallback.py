"""Fallback implementations for core utility functions."""
from datetime import datetime
import re
import unicodedata
from typing import Union

__all__ = ["truncate_text", "clean_key", "format_legal_date"]

JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Return ``text`` truncated to ``max_length`` characters."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    avail = max_length - len(suffix)
    return text[:avail] + suffix

def clean_key(key: str) -> str:
    """Sanitize ``key`` for use as an identifier."""
    if not key:
        return ""
    key = ''.join(
        c for c in unicodedata.normalize("NFD", str(key))
        if unicodedata.category(c) != "Mn"
    )
    key = key.lower()
    key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return re.sub(r"_+", "_", key)

def format_legal_date(date: Union[str, datetime], include_day_name: bool = False) -> str:
    """Format ``date`` using a simple French legal style."""
    if isinstance(date, str):
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                date = datetime.strptime(date, fmt)
                break
            except Exception:
                continue
        else:
            return date
    if isinstance(date, datetime):
        day = f"{JOURS_FR[date.weekday()]} " if include_day_name else ""
        return f"{day}{date.day} {MOIS_FR[date.month - 1]} {date.year}"
    return str(date)
