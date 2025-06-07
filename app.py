# app.py
import streamlit as st
import sys

# PREMIÈRE commande Streamlit OBLIGATOIREMENT
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration de l'encodage pour les emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from config.app_config import APP_CONFIG
from utils.styles import load_custom_css
from utils.helpers import initialize_session_state, clean_env_for_azure
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager

# Fix pour Hugging Face Spaces
clean_env_for_azure()

def main():
    """Interface principale de l'application"""
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    
    # Initialiser les gestionnaires Azure dans session state
    if 'azure_blob_manager' not in st.session_state:
        try:
            st.session_state.azure_blob_manager = AzureBlobManager()
        except Exception as e:
            st.warning(f"Azure Blob non disponible: {e}")
            st.session_state.azure_blob_manager = None
    
    if 'azure_search_manager' not in st.session_state:
        try:
            st.session_state.azure_search_manager = AzureSearchManager()
        except Exception as e:
            st.warning(f"Azure Search non disponible: {e}")
            st.session_state.azure_search_manager = None
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        page = st.selectbox(
            "Choisir une fonctionnalité",
            list(APP_CONFIG['PAGES'].keys()),
            format_func=lambda x: f"{APP_CONFIG['PAGES'][x]} {x}"
        )
        
        st.markdown("---")
        st.markdown("### 📊 État du système")
        
        # État Azure
        if st.session_state.get('azure_blob_manager') and st.session_state.azure_blob_manager.is_connected():
            st.success("✅ Azure Blob connecté")
        else:
            st.error("❌ Azure Blob non connecté")
        
        if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
            st.success("✅ Azure Search connecté")
        else:
            st.warning("⚠️ Azure Search non disponible")
        
        # Métriques
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        st.metric("Documents disponibles", nb_docs)
        st.metric("Pièces sélectionnées", nb_pieces)
    
    # Charger la page sélectionnée
    if page == "Recherche de documents":
        from pages.recherche import show_page
        show_page()
    elif page == "Sélection de pièces":
        from pages.selection_pieces import show_page
        show_page()
    elif page == "Analyse IA":
        from pages.analyse_ia import show_page
        show_page()
    elif page == "Rédaction assistée":
        from pages.redaction_assistee import show_page
        show_page()
    elif page == "Rédaction de courrier":
        from pages.redaction_courrier import show_page
        show_page()
    elif page == "Configuration":
        from pages.configuration import show_page
        show_page()

if __name__ == "__main__":
    main()