# pages/accueil.py
"""Page d'accueil de l'application"""

import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from config import APP_TITLE, APP_VERSION, APP_ICON, TYPES_INFRACTIONS, MESSAGES
from utils import load_custom_css, create_header, format_metric_card, create_alert_box

def show():
    """Affiche la page d'accueil"""
    # Charger les styles personnalisés
    load_custom_css()
    
    # Header personnalisé
    st.markdown(create_header(
        f"{APP_ICON} {APP_TITLE}",
        f"Version {APP_VERSION} - Votre expert en droit pénal des affaires"
    ), unsafe_allow_html=True)
    
    # Message de bienvenue
    st.markdown(create_alert_box(MESSAGES["welcome"], "info"), unsafe_allow_html=True)
    
    # Statistiques en colonnes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        analyses_count = st.session_state.get('analyses_count', 0)
        st.markdown(format_metric_card(
            "Analyses réalisées",
            str(analyses_count),
            "+5 cette semaine" if analyses_count > 0 else None,
            "primary"
        ), unsafe_allow_html=True)
    
    with col2:
        verifications_count = st.session_state.get('verifications_count', 0)
        st.markdown(format_metric_card(
            "Jurisprudences vérifiées",
            str(verifications_count),
            None,
            "success"
        ), unsafe_allow_html=True)
    
    with col3:
        documents_count = st.session_state.get('documents_count', 0)
        st.markdown(format_metric_card(
            "Documents traités",
            str(documents_count),
            None,
            "info"
        ), unsafe_allow_html=True)
    
    with col4:
        risk_score = st.session_state.get('average_risk_score', 0)
        st.markdown(format_metric_card(
            "Score de risque moyen",
            f"{risk_score:.1f}/10",
            None,
            "warning" if risk_score > 5 else "success"
        ), unsafe_allow_html=True)
    
    # Séparateur
    st.markdown("---")
    
    # Section fonctionnalités principales
    st.markdown("## 🎯 Fonctionnalités principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📋 Analyse juridique
        - Analyse complète de cas
        - Identification des infractions
        - Évaluation des risques
        - Recommandations stratégiques
        """)
        if st.button("Commencer une analyse", key="btn_analyse"):
            st.switch_page("pages/analyse.py")
    
    with col2:
        st.markdown("""
        ### 🔍 Recherche jurisprudentielle
        - Recherche multi-sources
        - Vérification automatique
        - Base Judilibre & Légifrance
        - Suggestions IA
        """)
        if st.button("Rechercher", key="btn_recherche"):
            st.switch_page("pages/recherche.py")
    
    with col3:
        st.markdown("""
        ### 💬 Assistant interactif
        - Chatbot juridique expert
        - Réponses personnalisées
        - Multi-modèles IA
        - Historique conservé
        """)
        if st.button("Discuter", key="btn_assistant"):
            st.switch_page("pages/assistant.py")
    
    # Section infractions
    st.markdown("## 📊 Types d'infractions traités")
    
    # Graphique des infractions
    fig_infractions = create_infractions_chart()
    st.plotly_chart(fig_infractions, use_container_width=True)
    
    # Guides rapides
    st.markdown("## 📚 Guides rapides")
    
    with st.expander("🚀 Comment démarrer ?"):
        st.markdown("""
        1. **Configurez vos clés API** dans la page Configuration
        2. **Importez vos documents** ou saisissez directement votre cas
        3. **Lancez l'analyse** et obtenez des recommandations détaillées
        4. **Vérifiez les jurisprudences** citées automatiquement
        5. **Exportez vos résultats** dans le format souhaité
        """)
    
    with st.expander("⚡ Raccourcis utiles"):
        st.markdown("""
        - `Ctrl + K` : Recherche rapide
        - `Ctrl + N` : Nouvelle analyse
        - `Ctrl + E` : Export
        - `Ctrl + H` : Historique
        """)
    
    with st.expander("🔒 Sécurité et confidentialité"):
        st.markdown("""
        - Vos données ne sont pas stockées sur nos serveurs
        - Les clés API sont chiffrées localement
        - Connexion sécurisée HTTPS
        - Conformité RGPD
        """)
    
    # Actualités juridiques (placeholder)
    st.markdown("## 📰 Actualités juridiques")
    
    news_container = st.container()
    with news_container:
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **Nouvelle jurisprudence** 🆕  
            Cass. crim., 15 janvier 2025 : Précisions sur l'élément intentionnel 
            en matière d'abus de biens sociaux...
            """)
        
        with col2:
            st.info("""
            **Réforme législative** 📜  
            Projet de loi renforçant la lutte contre la corruption : 
            nouvelles obligations de compliance...
            """)
    
    # Footer
    st.markdown("---")
    st.caption(f"© 2025 {APP_TITLE} - Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y')}")

def create_infractions_chart():
    """Crée un graphique des types d'infractions"""
    # Données fictives pour la démo
    infractions_data = {
        'Type': TYPES_INFRACTIONS[:8],
        'Nombre de cas': [45, 38, 32, 28, 25, 22, 18, 15]
    }
    
    fig = px.bar(
        infractions_data,
        x='Nombre de cas',
        y='Type',
        orientation='h',
        color='Nombre de cas',
        color_continuous_scale='Blues',
        title="Infractions les plus fréquemment analysées"
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_title="Nombre de cas traités",
        yaxis_title="",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# Point d'entrée pour Streamlit
if __name__ == "__main__":
    show()