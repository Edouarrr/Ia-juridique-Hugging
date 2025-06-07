# app.py
import streamlit as st

st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
import os
import traceback

from config.app_config import APP_CONFIG
from utils.helpers import initialize_session_state
from utils.styles import load_custom_css

def main():
    """Interface principale de l'application"""
    
    initialize_session_state()
    load_custom_css()
    
    # Initialiser les gestionnaires Azure avec diagnostics détaillés
    if 'azure_blob_manager' not in st.session_state:
        try:
            print("=== INITIALISATION AZURE BLOB ===")
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
            
            if st.session_state.azure_blob_manager.is_connected():
                print("✅ Azure Blob Manager connecté avec succès")
            else:
                error = st.session_state.azure_blob_manager.get_connection_error()
                print(f"❌ Azure Blob Manager non connecté: {error}")
                
        except Exception as e:
            print(f"❌ Erreur fatale Azure Blob Manager: {traceback.format_exc()}")
            st.session_state.azure_blob_manager = None
    
    if 'azure_search_manager' not in st.session_state:
        try:
            print("=== INITIALISATION AZURE SEARCH ===")
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
            
            if st.session_state.azure_search_manager.search_client:
                print("✅ Azure Search Manager connecté avec succès")
            else:
                error = st.session_state.azure_search_manager.get_connection_error()
                print(f"❌ Azure Search Manager non connecté: {error}")
                
        except Exception as e:
            print(f"❌ Erreur fatale Azure Search Manager: {traceback.format_exc()}")
            st.session_state.azure_search_manager = None
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar avec diagnostics Azure détaillés
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
        
        # Azure Blob avec détails d'erreur
        blob_manager = st.session_state.get('azure_blob_manager')
        if blob_manager:
            if blob_manager.is_connected():
                st.success("✅ Azure Blob Storage")
                containers = blob_manager.list_containers()
                if containers:
                    st.caption(f"{len(containers)} containers")
            else:
                st.error("❌ Azure Blob Storage")
                error = blob_manager.get_connection_error()
                if error:
                    st.caption(error[:50] + "..." if len(error) > 50 else error)
        else:
            st.error("❌ Azure Blob Storage")
            st.caption("Non initialisé")
        
        # Azure Search avec détails d'erreur
        search_manager = st.session_state.get('azure_search_manager')
        if search_manager:
            if search_manager.search_client:
                st.success("✅ Azure Search")
                st.caption("Index: juridique-index")
            else:
                st.error("❌ Azure Search")
                error = search_manager.get_connection_error()
                if error:
                    st.caption(error[:50] + "..." if len(error) > 50 else error)
        else:
            st.error("❌ Azure Search")
            st.caption("Non initialisé")
        
        # Métriques
        st.markdown("---")
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
    
    # Charger la page sélectionnée
    try:
        if page == "Recherche de documents":
            from pages.recherche import show_page
            show_page()
            
        elif page == "Configuration":
            st.header("⚙️ Configuration")
            
            # Diagnostics Azure détaillés
            st.subheader("🔍 Diagnostics Azure")
            
            # Azure Blob
            with st.expander("Azure Blob Storage", expanded=True):
                blob_manager = st.session_state.get('azure_blob_manager')
                if blob_manager:
                    if blob_manager.is_connected():
                        st.success("✅ Connecté")
                        containers = blob_manager.list_containers()
                        st.write(f"Containers trouvés: {containers}")
                    else:
                        st.error("❌ Non connecté")
                        error = blob_manager.get_connection_error()
                        st.error(f"Erreur: {error}")
                else:
                    st.error("❌ Non initialisé")
            
            # Azure Search
            with st.expander("Azure Search", expanded=True):
                search_manager = st.session_state.get('azure_search_manager')
                if search_manager:
                    if search_manager.search_client:
                        st.success("✅ Connecté")
                        st.write(f"Index: {search_manager.index_name}")
                    else:
                        st.error("❌ Non connecté")
                        error = search_manager.get_connection_error()
                        st.error(f"Erreur: {error}")
                else:
                    st.error("❌ Non initialisé")
        
        else:
            st.info(f"📄 {page}")
            st.write("Cette fonctionnalité est en cours de développement")
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la page '{page}'")
        st.error(f"Détail: {str(e)}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()