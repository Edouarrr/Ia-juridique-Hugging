# pages/accueil.py
"""Page d'accueil de l'application"""

import streamlit as st


def show():
    """Affiche la page d'accueil"""
    # Debug - Vérifier que la fonction est bien appelée
    st.write("DEBUG: La fonction show() est appelée")
    
    # Titre principal très simple
    st.title("⚖️ Assistant Pénal des Affaires IA")
    st.markdown("Intelligence artificielle au service du droit pénal économique")
    
    # Test simple
    st.write("Si vous voyez ce message, la page fonctionne !")
    
    # Message de bienvenue
    st.header("👋 Bienvenue")
    st.info("Cette plateforme utilise l'intelligence artificielle pour vous accompagner dans vos analyses juridiques.")
    
    # Fonctionnalités principales
    st.header("🚀 Fonctionnalités principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔍 Recherche")
        st.write("Explorez vos documents")
        st.button("Rechercher", key="btn1")
    
    with col2:
        st.subheader("📋 Analyse")
        st.write("Analysez avec l'IA")
        st.button("Analyser", key="btn2")
    
    with col3:
        st.subheader("💬 Assistant")
        st.write("Posez vos questions")
        st.button("Discuter", key="btn3")
    
    # Métriques simples
    st.header("📊 Statistiques")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", "0")
    
    with col2:
        st.metric("Analyses", "0")
    
    with col3:
        st.metric("Questions", "0")
    
    with col4:
        st.metric("Réponses", "0")
    
    # Test de session state
    st.header("🧪 Test Session State")
    if st.button("Tester"):
        st.session_state.test = "OK"
    
    if "test" in st.session_state:
        st.success(f"Test session state: {st.session_state.test}")
    
    # Fin
    st.markdown("---")
    st.markdown("© 2025 Assistant Pénal des Affaires IA")