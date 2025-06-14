"""Elements d'interface communs pour l'application Streamlit."""

from __future__ import annotations

import streamlit as st

__all__ = ["apply_theme", "render_header", "render_footer", "page_layout"]


def apply_theme() -> None:
    """Applique le thème STERU BARATTE AARPI."""

    st.markdown(
        """
        <style>
        body {
            background-color: #F5F7FA;
            color: #2C3E50;
        }
        .stButton > button {
            background-color: #1F77B4;
            color: white;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Affiche l'en-tête de l'application."""

    st.markdown(
        """
        <div style='background-color:#2C3E50;padding:15px;border-radius:5px;margin-bottom:15px'>
            <h1 style='color:white;text-align:center'>⚖️ STERU BARATTE AARPI</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Ajoute un pied de page discret."""

    st.markdown(
        """
        <hr>
        <div style='text-align:center;color:gray;font-size:0.8em'>
            © STERU BARATTE AARPI – Assistant IA Juridique – Paris, 2025
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_layout(title: str) -> None:
    """Applique le theme puis affiche l'en-tete et le titre."""

    apply_theme()
    render_header()
    st.title(title)

