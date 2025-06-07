# app.py
"""
Assistant Pénal des Affaires IA
Point d'entrée principal de l'application
"""

import streamlit as st
import sys
from pathlib import Path
import logging
from datetime import datetime

# Configuration de base de Streamlit - DOIT ÊTRE EN PREMIER
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/votre-repo',
        'Report a bug': "https://github.com/votre-repo/issues",
        'About': "Assistant IA spécialisé en droit pénal des affaires français"
    }
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports des modules de l'application
try:
    # Configuration
    from config import APP_TITLE, APP_ICON, PAGES, MESSAGES
    from config import LLM_CONFIGS, get_llm_client
    
    # Modèles
    from models import (
        AnalyseJuridique, CasJuridique, Personne,
        JurisprudenceReference, VerificationResult
    )
    
    # Gestionnaires
    from managers import (
        LLMManager,
        DocumentManager,
        JurisprudenceVerifier,
        LegalSearchManager
    )
    
    # Pages
    from pages import accueil, analyse, recherche, visualisation, assistant, configuration
    
    # Utilitaires
    from utils import load_custom_css, initialize_session_state
    
except ImportError as e:
    st.error(f"Erreur d'import des modules: {e}")
    st.stop()

# Initialisation de session_state
def init_session_state():
    """Initialise toutes les variables de session"""
    defaults = {
        # Gestionnaires
        'llm_manager': LLMManager(),
        'doc_manager': DocumentManager(),
        'jurisprudence_verifier': JurisprudenceVerifier(),
        'legal_search_manager': None,  # Initialisé après LLM
        
        # État de l'application
        'current_page': 'Accueil',
        'analysis_history': [],
        'current_analysis': None,
        'imported_content': "",
        
        # Configuration des modèles
        'selected_provider': 'OpenAI',
        'selected_model': 'gpt-4o-mini',
        
        # Clés API (à charger depuis les secrets ou l'environnement)
        'openai_api_key': st.secrets.get('OPENAI_API_KEY', ''),
        'anthropic_api_key': st.secrets.get('ANTHROPIC_API_KEY', ''),
        'google_api_key': st.secrets.get('GOOGLE_API_KEY', ''),
        'mistral_api_key': st.secrets.get('MISTRAL_API_KEY', ''),
        'groq_api_key': st.secrets.get('GROQ_API_KEY', ''),
        
        # Statut des APIs juridiques
        'judilibre_enabled': False,
        'legifrance_enabled': False,
        
        # Historique et cache
        'search_history': [],
        'verification_cache': {},
        
        # Paramètres utilisateur
        'user_preferences': {
            'theme': 'light',
            'auto_verify_jurisprudence': True,
            'include_ai_suggestions': True,
            'export_format': 'docx'
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialiser le gestionnaire de recherche juridique avec le LLM manager
    if st.session_state.legal_search_manager is None:
        st.session_state.legal_search_manager = LegalSearchManager(
            st.session_state.llm_manager
        )

def init_managers():
    """Initialise les gestionnaires avec les clés API"""
    llm_manager = st.session_state.llm_manager
    
    # Initialiser les clients LLM disponibles
    for provider in LLM_CONFIGS.keys():
        api_key = st.session_state.get(f"{provider.lower()}_api_key")
        if api_key:
            try:
                llm_manager.initialize_client(provider, api_key)
                logger.info(f"Client {provider} initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation {provider}: {e}")

def render_sidebar():
    """Affiche la barre latérale de navigation"""
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1a1a2e/f5f5f5?text=Assistant+Juridique+IA", use_column_width=True)
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        
        for page_name, icon in PAGES.items():
            if st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.markdown("---")
        
        # Statut du système
        st.markdown("### 📊 Statut")
        
        # Modèle actuel
        if st.session_state.llm_manager.current_model:
            st.success(f"🤖 {st.session_state.selected_provider}/{st.session_state.selected_model}")
        else:
            st.warning("⚠️ Aucun modèle configuré")
        
        # APIs juridiques
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.judilibre_enabled:
                st.success("✅ Judilibre")
            else:
                st.error("❌ Judilibre")
        with col2:
            if st.session_state.legifrance_enabled:
                st.success("✅ Légifrance")
            else:
                st.error("❌ Légifrance")
        
        # Statistiques
        st.markdown("---")
        st.markdown("### 📈 Statistiques")
        st.metric("Analyses effectuées", len(st.session_state.analysis_history))
        st.metric("Documents importés", len(st.session_state.doc_manager.imported_documents))
        
        # Informations
        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        st.caption(f"Version 3.0.0")
        st.caption(f"Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Bouton d'aide
        with st.expander("❓ Aide"):
            st.markdown("""
            **Navigation:**
            - Utilisez les boutons ci-dessus pour naviguer
            - Configurez d'abord vos clés API
            
            **Fonctionnalités:**
            - Analyse juridique complète
            - Vérification des jurisprudences
            - Recherche multi-sources
            - Export multi-formats
            
            **Support:**
            - Documentation: [Lien]
            - Contact: support@example.com
            """)

def render_header():
    """Affiche l'en-tête de l'application"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(f"<h1 style='text-align: center;'>{APP_ICON} {APP_TITLE}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Intelligence Artificielle au service du droit pénal des affaires</p>", unsafe_allow_html=True)
    
    st.markdown("---")

def route_to_page():
    """Route vers la page appropriée selon la sélection"""
    current_page = st.session_state.current_page
    
    # Mapping des pages
    page_modules = {
        'Accueil': accueil,
        'Analyse juridique': analyse,
        'Recherche de jurisprudence': recherche,
        'Visualisation': visualisation,
        'Assistant interactif': assistant,
        'Configuration': configuration
    }
    
    # Afficher la page correspondante
    if current_page in page_modules:
        page_modules[current_page].render()
    else:
        st.error(f"Page '{current_page}' non trouvée")

def check_system_ready():
    """Vérifie que le système est prêt"""
    warnings = []
    
    # Vérifier les clés API
    if not any(st.session_state.get(f"{provider.lower()}_api_key") for provider in LLM_CONFIGS.keys()):
        warnings.append("Aucune clé API configurée. Rendez-vous dans Configuration.")
    
    # Vérifier les APIs juridiques
    if not st.session_state.judilibre_enabled and not st.session_state.legifrance_enabled:
        warnings.append("APIs juridiques non configurées. Vérification des jurisprudences limitée.")
    
    # Afficher les avertissements
    if warnings and st.session_state.current_page != 'Configuration':
        container = st.container()
        with container:
            for warning in warnings:
                st.warning(f"⚠️ {warning}")

def main():
    """Fonction principale de l'application"""
    # Initialisation
    init_session_state()
    init_managers()
    
    # Charger les styles CSS personnalisés
    load_custom_css()
    
    # Interface principale
    render_sidebar()
    
    # Zone principale
    render_header()
    
    # Vérifications système
    check_system_ready()
    
    # Router vers la page
    route_to_page()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown(
            "<p style='text-align: center; color: #888; font-size: 0.9em;'>"
            "Assistant Pénal des Affaires IA © 2024 | "
            "Développé avec ❤️ et Streamlit"
            "</p>",
            unsafe_allow_html=True
        )

# Point d'entrée
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        st.error(f"Une erreur critique s'est produite: {e}")
        st.error("Veuillez rafraîchir la page ou contacter le support.")
        
        # Afficher plus de détails en mode debug
        if st.secrets.get("DEBUG", False):
            st.exception(e)