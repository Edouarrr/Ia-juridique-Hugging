# app.py
import streamlit as st

# PREMIÈRE commande Streamlit OBLIGATOIREMENT
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration de l'encodage pour les emojis
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# PAS de dotenv sur Hugging Face Spaces - les variables sont dans Settings > Variables and secrets

import os
from config.app_config import APP_CONFIG
from utils.styles import load_custom_css
from utils.helpers import initialize_session_state
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager

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
            [
                "Recherche de documents",
                "Sélection de pièces", 
                "Analyse IA",
                "Rédaction assistée",
                "Rédaction de courrier",
                "Import/Export",
                "Configuration"
            ],
            format_func=lambda x: f"{APP_CONFIG['PAGES'].get(x, '📄')} {x}",
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### 📊 État du système")
        
        # État Azure
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.get('azure_blob_manager') and st.session_state.azure_blob_manager.is_connected():
                st.success("✅ Azure Blob")
            else:
                st.error("❌ Azure Blob")
        
        with col2:
            if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
                st.success("✅ Azure Search")
            else:
                st.warning("⚠️ Azure Search")
        
        # Métriques
        st.markdown("### 📈 Métriques")
        
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
        
        # Informations supplémentaires
        if st.session_state.get('dossier_actif'):
            st.markdown("### 📁 Dossier actif")
            st.info(st.session_state.dossier_actif)
        
        # Bouton de réinitialisation
        st.markdown("---")
        if st.button("🔄 Réinitialiser", key="reset_app"):
            for key in list(st.session_state.keys()):
                if key != 'initialized':
                    del st.session_state[key]
            st.rerun()
        
        # Info version
        st.markdown("---")
        st.caption(f"Version {APP_CONFIG['VERSION']}")
        st.caption("© 2024 Assistant Juridique IA")
    
    # Charger la page sélectionnée
    if page == "Recherche de documents":
        from pages.recherche import show_page
        show_page()
    
    elif page == "Sélection de pièces":
        # Vérifier qu'il y a des documents
        if not st.session_state.get('azure_documents'):
            st.warning("⚠️ Aucun document disponible. Commencez par rechercher des documents.")
            if st.button("🔍 Aller à la recherche"):
                st.session_state.navigation = "Recherche de documents"
                st.rerun()
        else:
            # Importer et afficher la page si elle existe
            try:
                from pages.selection_pieces import show_page
                show_page()
            except ImportError:
                st.error("❌ Module 'selection_pieces' non disponible")
                st.info("Cette fonctionnalité est en cours de développement")
    
    elif page == "Analyse IA":
        # Vérifier qu'il y a des pièces sélectionnées
        if not st.session_state.get('pieces_selectionnees'):
            st.warning("⚠️ Aucune pièce sélectionnée. Sélectionnez d'abord des pièces.")
            if st.button("📁 Aller à la sélection"):
                st.session_state.navigation = "Sélection de pièces"
                st.rerun()
        else:
            try:
                from pages.analyse_ia import show_page
                show_page()
            except ImportError:
                st.error("❌ Module 'analyse_ia' non disponible")
                st.info("Cette fonctionnalité est en cours de développement")
    
    elif page == "Rédaction assistée":
        try:
            from pages.redaction_assistee import show_page
            show_page()
        except ImportError:
            st.error("❌ Module 'redaction_assistee' non disponible")
            st.info("Cette fonctionnalité est en cours de développement")
    
    elif page == "Rédaction de courrier":
        try:
            from pages.redaction_courrier import show_page
            show_page()
        except ImportError:
            st.error("❌ Module 'redaction_courrier' non disponible")
            st.info("Cette fonctionnalité est en cours de développement")
    
    elif page == "Import/Export":
        try:
            from pages.import_export import show_page
            show_page()
        except ImportError:
            st.error("❌ Module 'import_export' non disponible")
            st.info("Cette fonctionnalité est en cours de développement")
    
    elif page == "Configuration":
        try:
            from pages.configuration import show_page
            show_page()
        except ImportError:
            st.error("❌ Module 'configuration' non disponible")
            # Afficher une configuration basique
            st.header("⚙️ Configuration")
            st.markdown("### 🔑 Variables d'environnement")
            
            # Vérifier les variables
            vars_to_check = [
                "AZURE_STORAGE_CONNECTION_STRING",
                "AZURE_SEARCH_ENDPOINT",
                "AZURE_SEARCH_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_KEY",
                "ANTHROPIC_API_KEY",
                "OPENAI_API_KEY"
            ]
            
            for var in vars_to_check:
                if os.getenv(var):
                    st.success(f"✅ {var}")
                else:
                    st.error(f"❌ {var}")

if __name__ == "__main__":
    main()