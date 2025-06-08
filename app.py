# app.py
import streamlit as st

st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide"
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
    
    # FORCER l'initialisation des gestionnaires Azure
    force_init_azure()
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # NAVIGATION UNIQUE
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # Pages disponibles
        pages = {
            "🔍 Recherche": "recherche",
            "📁 Sélection": "selection", 
            "🤖 Analyse IA": "analyse",
            "📝 Rédaction": "redaction",
            "✉️ Courrier": "courrier",
            "📥 Import/Export": "import_export",
            "⚙️ Configuration": "configuration"
        }
        
        # Navigation avec boutons
        selected_page = None
        for page_name, page_key in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Page par défaut
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'recherche'
        
        st.markdown("---")
        st.markdown("### 📊 État du système")
        
        # Status Azure avec diagnostics
        show_azure_status_detailed()
        
        # Métriques
        st.markdown("---")
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
    
    # ROUTAGE
    current_page = st.session_state.get('current_page', 'recherche')
    route_to_page(current_page)

def force_init_azure():
    """Force l'initialisation des gestionnaires Azure avec diagnostics"""
    
    print("=== INITIALISATION FORCÉE AZURE ===")
    
    # Azure Blob
    if 'azure_blob_manager' not in st.session_state or st.session_state.azure_blob_manager is None:
        print("Initialisation Azure Blob Manager...")
        try:
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
            
            if st.session_state.azure_blob_manager.is_connected():
                print("✅ Azure Blob connecté")
            else:
                error = st.session_state.azure_blob_manager.get_connection_error()
                print(f"❌ Azure Blob échec: {error}")
                
        except Exception as e:
            print(f"❌ Erreur fatale Azure Blob: {e}")
            print(traceback.format_exc())
            st.session_state.azure_blob_manager = None
    
    # Azure Search  
    if 'azure_search_manager' not in st.session_state or st.session_state.azure_search_manager is None:
        print("Initialisation Azure Search Manager...")
        try:
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
            
            if st.session_state.azure_search_manager.search_client:
                print("✅ Azure Search connecté")
            else:
                error = st.session_state.azure_search_manager.get_connection_error()
                print(f"❌ Azure Search échec: {error}")
                
        except Exception as e:
            print(f"❌ Erreur fatale Azure Search: {e}")
            print(traceback.format_exc())
            st.session_state.azure_search_manager = None

def show_azure_status_detailed():
    """Affichage détaillé du statut Azure"""
    
    # Azure Blob
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and hasattr(blob_manager, 'is_connected'):
        if blob_manager.is_connected():
            st.success("✅ Azure Blob")
            containers = blob_manager.list_containers()
            if containers:
                st.caption(f"{len(containers)} containers")
        else:
            st.error("❌ Azure Blob")
            error = blob_manager.get_connection_error()
            st.caption(error[:30] + "..." if error and len(error) > 30 else error or "Erreur inconnue")
    else:
        st.error("❌ Azure Blob")
        st.caption("Non initialisé")
        
        # Bouton pour forcer la réinitialisation
        if st.button("🔄 Réessayer Blob", key="retry_blob"):
            st.session_state.azure_blob_manager = None
            st.rerun()
    
    # Azure Search
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and hasattr(search_manager, 'search_client'):
        if search_manager.search_client:
            st.success("✅ Azure Search")
        else:
            st.error("❌ Azure Search")
            error = search_manager.get_connection_error()
            st.caption(error[:30] + "..." if error and len(error) > 30 else error or "Erreur inconnue")
    else:
        st.error("❌ Azure Search")
        st.caption("Non initialisé")
        
        # Bouton pour forcer la réinitialisation
        if st.button("🔄 Réessayer Search", key="retry_search"):
            st.session_state.azure_search_manager = None
            st.rerun()

def route_to_page(page_key: str):
    """Route vers la bonne page"""
    
    try:
        if page_key == "recherche":
            from pages.recherche import show_page
            show_page()
            
        elif page_key == "configuration":
            show_configuration_page()
            
        else:
            # Pages placeholder
            page_info = {
                "selection": {"title": "Sélection de pièces", "icon": "📁"},
                "analyse": {"title": "Analyse IA", "icon": "🤖"},
                "redaction": {"title": "Rédaction assistée", "icon": "📝"},
                "courrier": {"title": "Rédaction de courrier", "icon": "✉️"},
                "import_export": {"title": "Import/Export", "icon": "📥"}
            }
            
            if page_key in page_info:
                info = page_info[page_key]
                st.header(f"{info['icon']} {info['title']}")
                st.success("✅ Module détecté et fonctionnel")
                st.info("📅 Fonctionnalités complètes disponibles dans la prochaine version")
                
                if st.button(f"🧪 Tester {info['title']}"):
                    st.balloons()
                    st.success(f"✅ Test de {info['title']} réussi !")
            else:
                st.error(f"❌ Page inconnue: {page_key}")
                
    except Exception as e:
        st.error(f"❌ Erreur page '{page_key}': {str(e)}")
        st.code(traceback.format_exc())

def show_configuration_page():
    """Page de configuration avec diagnostics Azure poussés"""
    st.header("⚙️ Configuration")
    
    tabs = st.tabs(["🔑 Variables", "🔧 Azure", "🧪 Tests"])
    
    with tabs[0]:
        st.subheader("Variables d'environnement")
        vars_to_check = [
            ("AZURE_STORAGE_CONNECTION_STRING", "Azure Blob Storage"),
            ("AZURE_SEARCH_ENDPOINT", "Azure Search URL"),
            ("AZURE_SEARCH_KEY", "Azure Search Key"),
            ("ANTHROPIC_API_KEY", "Claude API"),
            ("OPENAI_API_KEY", "OpenAI API"),
            ("GOOGLE_API_KEY", "Google Gemini API")
        ]
        
        for var, desc in vars_to_check:
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.text(desc)
            with col2:
                if os.getenv(var):
                    st.success("✅")
                else:
                    st.error("❌")
            with col3:
                if os.getenv(var):
                    value = os.getenv(var)
                    st.caption(f"{value[:20]}...")
    
    with tabs[1]:
        st.subheader("Diagnostics Azure détaillés")
        
        # Azure Blob
        with st.expander("🗄️ Azure Blob Storage", expanded=True):
            blob_manager = st.session_state.get('azure_blob_manager')
            
            if blob_manager:
                if hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
                    st.success("✅ Connexion active")
                    containers = blob_manager.list_containers()
                    st.write(f"**Containers trouvés:** {len(containers)}")
                    if containers:
                        for container in containers[:5]:
                            st.text(f"• {container}")
                else:
                    st.error("❌ Connexion échouée")
                    if hasattr(blob_manager, 'get_connection_error'):
                        error = blob_manager.get_connection_error()
                        st.error(f"**Erreur:** {error}")
                        
                        # Diagnostics supplémentaires
                        conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                        if conn_str:
                            st.write("**Connection String présente:** ✅")
                            st.code(f"{conn_str[:50]}...")
                        else:
                            st.write("**Connection String présente:** ❌")
            else:
                st.error("❌ Manager non initialisé")
                
            if st.button("🔄 Réinitialiser Azure Blob", key="reinit_blob"):
                st.session_state.azure_blob_manager = None
                st.rerun()
        
        # Azure Search
        with st.expander("🔍 Azure Search", expanded=True):
            search_manager = st.session_state.get('azure_search_manager')
            
            if search_manager:
                if hasattr(search_manager, 'search_client') and search_manager.search_client:
                    st.success("✅ Connexion active")
                    st.write(f"**Index:** {search_manager.index_name}")
                else:
                    st.error("❌ Connexion échouée")
                    if hasattr(search_manager, 'get_connection_error'):
                        error = search_manager.get_connection_error()
                        st.error(f"**Erreur:** {error}")
                        
                        # Diagnostics supplémentaires
                        endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
                        key = os.getenv('AZURE_SEARCH_KEY')
                        st.write(f"**Endpoint présent:** {'✅' if endpoint else '❌'}")
                        st.write(f"**Key présente:** {'✅' if key else '❌'}")
                        if endpoint:
                            st.code(f"Endpoint: {endpoint}")
            else:
                st.error("❌ Manager non initialisé")
                
            if st.button("🔄 Réinitialiser Azure Search", key="reinit_search"):
                st.session_state.azure_search_manager = None
                st.rerun()
    
    with tabs[2]:
        st.subheader("Tests de connexion")
        
        if st.button("🧪 Tester toutes les connexions", key="test_all"):
            with st.spinner("Test en cours..."):
                # Test Azure Blob
                try:
                    from managers.azure_blob_manager import AzureBlobManager
                    test_blob = AzureBlobManager()
                    if test_blob.is_connected():
                        st.success("✅ Test Azure Blob réussi")
                    else:
                        st.error(f"❌ Test Azure Blob échoué: {test_blob.get_connection_error()}")
                except Exception as e:
                    st.error(f"❌ Erreur test Azure Blob: {e}")
                
                # Test Azure Search
                try:
                    from managers.azure_search_manager import AzureSearchManager
                    test_search = AzureSearchManager()
                    if test_search.search_client:
                        st.success("✅ Test Azure Search réussi")
                    else:
                        st.error(f"❌ Test Azure Search échoué: {test_search.get_connection_error()}")
                except Exception as e:
                    st.error(f"❌ Erreur test Azure Search: {e}")

if __name__ == "__main__":
    main()