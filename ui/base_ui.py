"""Composants d'interface réutilisables pour les pages Streamlit."""

import streamlit as st

# Palette de couleurs professionnelle
PRIMARY_COLOR = "#0d47a1"  # Bleu foncé
SECONDARY_COLOR = "#f5f7fa"  # Gris très clair
TEXT_COLOR = "#333333"
BRAND_NAME = "STERU BARATTE AARPI"


def apply_theme() -> None:
    """Applique le thème général de l'application."""
    st.set_page_config(page_title=BRAND_NAME, page_icon="⚖️", layout="wide")
    st.markdown(
        f"""
        <style>
            body {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            .sb-header {{
                background-color: {PRIMARY_COLOR};
                color: white;
                padding: 1rem;
                text-align: center;
                border-radius: 4px;
                margin-bottom: 1.5rem;
            }}
            .sb-footer {{
                color: {TEXT_COLOR};
                text-align: center;
                margin-top: 2rem;
                font-size: 0.9rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Affiche l'en-tête standard de l'application."""
    st.markdown(f"<div class='sb-header'><h1>{BRAND_NAME}</h1></div>", unsafe_allow_html=True)


def render_footer() -> None:
    """Affiche le pied de page standard."""
    st.markdown(
        "<div class='sb-footer'>\u00a9 2024 STERU BARATTE AARPI - Tous droits réservés.</div>",
        unsafe_allow_html=True,
    )


def page_layout(title: str) -> None:
    """Initialise la page avec le thème, le header et le titre."""
    apply_theme()
    render_header()
    st.title(title)

