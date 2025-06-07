# app.py
import streamlit as st

# PREMIÈRE commande Streamlit OBLIGATOIREMENT
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
import os
import traceback

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("Application démarrée avec succès")

from config.app_config import APP_CONFIG
from utils.helpers import initialize_session_state
from utils.styles import load_custom_css

def main():
    """Interface principale de l'application"""
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    
    # Initialiser les gestionnaires Azure
    if 'azure_blob_manager' not in st.session_state:
        try:
            print("Initialisation Azure Blob Manager...")
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
            print(f"Azure Blob Manager connecté: {st.session_state.azure_blob_manager.is_connected()}")
        except Exception as e:
            print(f"Erreur Azure Blob Manager: {traceback.format_exc()}")
            st.session_state.azure_blob_manager = None
    
    if 'azure_search_manager' not in st.session_state:
        try:
            print("Initialisation Azure Search Manager...")
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
            print("Azure Search Manager initialisé")
        except Exception as e:
            print(f"Erreur Azure Search Manager: {traceback.format_exc()}")
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
        
        # Azure Blob
        if st.session_state.get('azure_blob_manager'):
            if hasattr(st.session_state.azure_blob_manager, 'is_connected') and st.session_state.azure_blob_manager.is_connected():
                st.success("✅ Azure Blob Storage")
            else:
                st.warning("⚠️ Azure Blob Storage")
        else:
            st.error("❌ Azure Blob Storage")
        
        # Azure Search  
        if st.session_state.get('azure_search_manager'):
            if hasattr(st.session_state.azure_search_manager, 'search_client') and st.session_state.azure_search_manager.search_client:
                st.success("✅ Azure Search")
            else:
                st.warning("⚠️ Azure Search")
        else:
            st.error("❌ Azure Search")
        
        # Métriques
        st.markdown("---")
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
    
    # Charger la page sélectionnée avec gestion d'erreur
    try:
        if page == "Recherche de documents":
            print(f"Chargement de la page: {page}")
            from pages.recherche import show_page
            show_page()
            
        elif page == "Configuration":
            st.header("⚙️ Configuration")
            st.markdown("### 🔑 Variables d'environnement")
            
            vars_to_check = [
                ("AZURE_STORAGE_CONNECTION_STRING", "Azure Blob Storage"),
                ("AZURE_SEARCH_ENDPOINT", "Azure Search URL"),
                ("AZURE_SEARCH_KEY", "Azure Search Key"),
                ("ANTHROPIC_API_KEY", "Claude API"),
                ("OPENAI_API_KEY", "OpenAI API"),
                ("GOOGLE_API_KEY", "Google Gemini API")
            ]
            
            for var, desc in vars_to_check:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(desc)
                with col2:
                    if os.getenv(var):
                        st.success("✅")
                    else:
                        st.error("❌")
        
        else:
            # Pages non implémentées
            st.info(f"📄 {page}")
            st.write("Cette fonctionnalité est en cours de développement")
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la page '{page}'")
        st.error(f"Détail: {str(e)}")
        st.code(traceback.format_exc())
        print(f"ERREUR PAGE {page}:")
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ ERREUR FATALE")
        st.code(str(e))
        st.code(traceback.format_exc())
        print("ERREUR FATALE:")
        print(traceback.format_exc())