"""Module de gestion des documents longs"""

import streamlit as st
from typing import List, Dict, Any

MODULE_FUNCTIONS = {
    "display_long_documents": "Afficher les documents longs",
    "split_document": "Diviser un document en sections",
    "merge_documents": "Fusionner plusieurs documents",
    "analyze_long_text": "Analyser un texte long",
}


def display_long_documents() -> None:
    """Affiche l'interface de gestion des documents longs."""
    st.header("📄 Documents longs")
    st.info("Module de gestion des documents longs en cours de développement")


def split_document(content: str, max_length: int = 1000) -> List[str]:
    """Divise ``content`` en sections de ``max_length`` caractères."""
    sections: List[str] = []
    words = content.split()
    current_section: List[str] = []
    current_length = 0
    for word in words:
        current_section.append(word)
        current_length += len(word) + 1
        if current_length >= max_length:
            sections.append(" ".join(current_section))
            current_section = []
            current_length = 0
    if current_section:
        sections.append(" ".join(current_section))
    return sections


def merge_documents(documents: List[str]) -> str:
    """Fusionne plusieurs documents."""
    return "\n\n---\n\n".join(documents)


def analyze_long_text(text: str) -> Dict[str, Any]:
    """Analyse un texte long."""
    return {
        "length": len(text),
        "words": len(text.split()),
        "paragraphs": len(text.split("\n\n")),
        "sections": len(split_document(text)),
    }
