# base_ui.py
"""Composants d'interface réutilisables pour les pages Streamlit.

Ce module centralise l'en-tête, le pied de page et le thème de base
aux couleurs du cabinet STERU BARATTE AARPI.
"""

import streamlit as st


def render_header() -> None:
    """Affiche la bannière du cabinet."""
    st.markdown(
        """
        <div style='background-color:#2C3E50;padding:15px;border-radius:5px'>
            <h1 style='color:white;text-align:center'>⚖️ STERU BARATTE AARPI</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Affiche un pied de page discret."""
    st.markdown(
        """
        <hr>
        <div style='text-align:center;color:gray;font-size:0.8em'>
            © STERU BARATTE AARPI – Assistant IA Juridique – Paris, 2025
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme() -> None:
    """Applique un thème visuel basique."""
    st.markdown(
        """
        <style>
        body { background-color: #F5F7FA; color: #2C3E50; }
        .stButton>button { background-color: #1F77B4; color: white; border-radius: 5px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

