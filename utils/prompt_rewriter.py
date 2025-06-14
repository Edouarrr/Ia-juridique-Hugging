"""Simple prompt rewriting utilities."""
import re

_REPLACEMENTS = {
    "donne-moi": "fournis-moi",
    "dis-moi": "indique-moi",
    "contrat": "convention",
    "société": "entreprise",
    "personne": "individu",
    "montre": "démontre",
}


def rewrite_prompt(text: str) -> str:
    """Rewrite prompt with basic synonym substitutions."""
    if not text:
        return ""
    new_text = str(text)
    for word, repl in _REPLACEMENTS.items():
        pattern = re.compile(rf"\b{re.escape(word)}\b", flags=re.IGNORECASE)
        new_text = pattern.sub(repl, new_text)
    return new_text
