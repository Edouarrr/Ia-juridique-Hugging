"""Module de gestion des templates"""

import streamlit as st
from typing import Dict, List

MODULE_FUNCTIONS = {
    "show_templates": "Afficher les templates",
    "create_template": "Créer un template",
    "load_template": "Charger un template",
    "save_template": "Sauvegarder un template",
}

TEMPLATES = {
    "plainte": "PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE",
    "conclusions": "CONCLUSIONS",
}


def show_templates() -> None:
    """Affiche l'interface des templates."""
    st.header("📑 Templates de documents")
    template_type = st.selectbox("Type de template", list(TEMPLATES.keys()))
    if template_type:
        st.text_area("Contenu du template", value=TEMPLATES[template_type], height=400)


def create_template(name: str, content: str) -> bool:
    """Crée un nouveau template."""
    if name not in TEMPLATES:
        TEMPLATES[name] = content
        return True
    return False


def load_template(name: str) -> str:
    """Charge un template."""
    return TEMPLATES.get(name, "")


def save_template(name: str, content: str) -> bool:
    """Sauvegarde un template."""
    TEMPLATES[name] = content
    return True
