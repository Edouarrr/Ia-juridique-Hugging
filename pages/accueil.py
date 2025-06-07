# pages/accueil.py
"""Page d'accueil de l'application"""

import streamlit as st
from datetime import datetime

from config.app_config import APP_TITLE, APP_VERSION, APP_ICON, TYPES_INFRACTIONS, MESSAGES
from utils.styles import load_custom_css, format_metric_card, create_alert_box


def show():
    """Affiche la page d'accueil"""
    # Note: Le titre principal est déjà affiché dans app.py, donc on ne le répète pas ici
    
    # Message de bienvenue
    st.markdown("## 👋 " + MESSAGES.get("welcome", "Bienvenue dans l'Assistant Pénal des Affaires IA"))
    
    # Section des fonctionnalités principales
    st.markdown("## 🚀 Fonctionnalités principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(format_metric_card(
            "🔍 Recherche intelligente",
            "Documents & Jurisprudence",
            color="primary"
        ), unsafe_allow_html=True)
        
        if st.button("Accéder à la recherche", key="btn_recherche", use_container_width=True):
            st.info("👉 Utilisez le menu de navigation à gauche pour accéder à la recherche")
    
    with col2:
        st.markdown(format_metric_card(
            "📋 Analyse juridique",
            "IA & Insights",
            color="success"
        ), unsafe_allow_html=True)
        
        if st.button("Lancer une analyse", key="btn_analyse", use_container_width=True):
            st.info("👉 Utilisez le menu de navigation à gauche pour accéder à l'analyse")
    
    with col3:
        st.markdown(format_metric_card(
            "💬 Assistant interactif",
            "Questions & Réponses",
            color="info"
        ), unsafe_allow_html=True)
        
        if st.button("Démarrer l'assistant", key="btn_assistant", use_container_width=True):
            st.info("👉 Utilisez le menu de navigation à gauche pour accéder à l'assistant")
    
    # Statistiques et métriques
    st.markdown("---")
    st.markdown("## 📊 Tableau de bord")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nb_docs = len(st.session_state.get('azure_documents', {}))
        st.metric(
            "Documents chargés",
            nb_docs,
            delta=f"+{nb_docs}" if nb_docs > 0 else None
        )
    
    with col2:
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        st.metric(
            "Pièces sélectionnées",
            nb_pieces,
            delta=f"+{nb_pieces}" if nb_pieces > 0 else None
        )
    
    with col3:
        nb_analyses = st.session_state.get('analyses_count', 0)
        st.metric(
            "Analyses effectuées",
            nb_analyses
        )
    
    with col4:
        nb_styles = len(st.session_state.get('learned_styles', {}))
        st.metric(
            "Styles appris",
            nb_styles
        )
    
    # Section d'aide rapide
    st.markdown("---")
    st.markdown("## 💡 Aide rapide")
    
    with st.expander("🎯 Comment démarrer ?"):
        st.markdown("""
        1. **Recherchez vos documents** : Utilisez la fonction de recherche pour explorer vos documents SharePoint
        2. **Sélectionnez les pièces pertinentes** : Organisez vos documents par catégorie
        3. **Lancez une analyse** : Utilisez l'IA pour analyser vos documents
        4. **Générez des documents** : Créez des plaintes, conclusions ou courriers
        5. **Consultez l'assistant** : Posez vos questions juridiques spécifiques
        """)
    
    with st.expander("📚 Types d'infractions supportées"):
        # Afficher les infractions en colonnes
        infractions_cols = st.columns(3)
        for i, infraction in enumerate(TYPES_INFRACTIONS):
            with infractions_cols[i % 3]:
                st.write(f"• {infraction}")
    
    with st.expander("🔧 Configuration requise"):
        st.markdown("""
        **Services Azure nécessaires :**
        - ✅ Azure Blob Storage (pour accéder à SharePoint)
        - ✅ Azure Search (pour la recherche vectorielle)
        - ✅ Azure OpenAI (pour les embeddings)
        
        **IA supportées :**
        - Claude (Anthropic)
        - GPT-4 (OpenAI/Azure)
        - Gemini (Google)
        - Perplexity
        - Mistral
        """)
    
    # Section actualités/mises à jour
    st.markdown("---")
    st.markdown("## 📰 Actualités juridiques")
    
    # Simuler des actualités
    actualites = [
        {
            "titre": "Nouvelle jurisprudence sur l'abus de biens sociaux",
            "date": "15 juin 2025",
            "description": "La Cour de cassation précise les conditions de caractérisation..."
        },
        {
            "titre": "Réforme du droit pénal des affaires",
            "date": "10 juin 2025",
            "description": "Le projet de loi renforçant la lutte contre la corruption..."
        }
    ]
    
    for actu in actualites:
        with st.container():
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <h4 style='margin: 0; color: #1a237e;'>{actu['titre']}</h4>
                <p style='margin: 0.5rem 0; color: #666; font-size: 0.9rem;'>{actu['date']}</p>
                <p style='margin: 0;'>{actu['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Note: Le footer est déjà dans app.py, donc on ne le répète pas ici