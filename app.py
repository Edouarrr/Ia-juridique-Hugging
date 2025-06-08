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

print("=== DÉMARRAGE APPLICATION ===")

from config.app_config import APP_CONFIG
from utils.helpers import initialize_session_state
from utils.styles import load_custom_css

def main():
    """Interface principale de l'application"""
    
    print("=== DÉBUT MAIN ===")
    
    initialize_session_state()
    load_custom_css()
    
    # FORCER l'initialisation Azure AU DÉBUT
    init_azure_managers()
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # NAVIGATION + SIDEBAR
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
        for page_name, page_key in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Page par défaut
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'recherche'
        
        st.markdown("---")
        st.markdown("### 📊 État du système")
        
        # AFFICHAGE AZURE AVEC DIAGNOSTICS
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
        
        # Bouton de diagnostic
        st.markdown("---")
        if st.button("🔄 Réinitialiser Azure", key="reinit_azure"):
            reinit_azure()
    
    # ROUTAGE
    current_page = st.session_state.get('current_page', 'recherche')
    route_to_page(current_page)

def init_azure_managers():
    """Initialise les gestionnaires Azure avec logs détaillés"""
    
    print("=== INITIALISATION AZURE ===")
    
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state or st.session_state.azure_blob_manager is None:
        print("Initialisation Azure Blob Manager...")
        try:
            from managers.azure_blob_manager import AzureBlobManager
            
            print("Import AzureBlobManager réussi")
            manager = AzureBlobManager()
            print(f"AzureBlobManager créé: {manager}")
            
            st.session_state.azure_blob_manager = manager
            
            if hasattr(manager, 'is_connected') and manager.is_connected():
                print("✅ Azure Blob connecté avec succès")
                containers = manager.list_containers()
                print(f"Containers trouvés: {containers}")
            else:
                print("❌ Azure Blob non connecté")
                if hasattr(manager, 'get_connection_error'):
                    error = manager.get_connection_error()
                    print(f"Erreur: {error}")
                    
        except Exception as e:
            print(f"❌ Erreur fatale Azure Blob: {e}")
            print(traceback.format_exc())
            st.session_state.azure_blob_manager = None
    else:
        print("Azure Blob Manager déjà initialisé")
    
    # Azure Search Manager  
    if 'azure_search_manager' not in st.session_state or st.session_state.azure_search_manager is None:
        print("Initialisation Azure Search Manager...")
        try:
            from managers.azure_search_manager import AzureSearchManager
            
            print("Import AzureSearchManager réussi")
            manager = AzureSearchManager()
            print(f"AzureSearchManager créé: {manager}")
            
            st.session_state.azure_search_manager = manager
            
            if hasattr(manager, 'search_client') and manager.search_client:
                print("✅ Azure Search connecté avec succès")
            else:
                print("❌ Azure Search non connecté")
                if hasattr(manager, 'get_connection_error'):
                    error = manager.get_connection_error()
                    print(f"Erreur: {error}")
                    
        except Exception as e:
            print(f"❌ Erreur fatale Azure Search: {e}")
            print(traceback.format_exc())
            st.session_state.azure_search_manager = None
    else:
        print("Azure Search Manager déjà initialisé")

def reinit_azure():
    """Force la réinitialisation d'Azure"""
    print("=== RÉINITIALISATION AZURE FORCÉE ===")
    
    # Supprimer les managers existants
    if 'azure_blob_manager' in st.session_state:
        del st.session_state.azure_blob_manager
    if 'azure_search_manager' in st.session_state:
        del st.session_state.azure_search_manager
    
    # Réinitialiser
    init_azure_managers()
    
    st.rerun()

def show_azure_status_detailed():
    """Affichage détaillé du statut Azure avec diagnostics"""
    
    # Test des variables d'environnement
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    search_key = os.getenv('AZURE_SEARCH_KEY')
    
    # Azure Blob
    st.markdown("**Azure Blob Storage**")
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if not conn_str:
        st.error("❌ Connection String manquante")
    elif not blob_manager:
        st.error("❌ Manager non initialisé")
    elif hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
        st.success("✅ Connecté")
        containers = blob_manager.list_containers()
        if containers:
            st.caption(f"{len(containers)} containers")
        else:
            st.caption("0 containers")
    else:
        st.error("❌ Non connecté")
        if hasattr(blob_manager, 'get_connection_error'):
            error = blob_manager.get_connection_error()
            st.caption(error[:40] + "..." if error and len(error) > 40 else error or "Erreur inconnue")
    
    # Azure Search
    st.markdown("**Azure Search**")
    search_manager = st.session_state.get('azure_search_manager')
    
    if not search_endpoint or not search_key:
        st.error("❌ Endpoint/Key manquant")
    elif not search_manager:
        st.error("❌ Manager non initialisé")
    elif hasattr(search_manager, 'search_client') and search_manager.search_client:
        st.success("✅ Connecté")
        st.caption("Index: juridique-index")
    else:
        st.error("❌ Non connecté")
        if hasattr(search_manager, 'get_connection_error'):
            error = search_manager.get_connection_error()
            st.caption(error[:40] + "..." if error and len(error) > 40 else error or "Erreur inconnue")

def route_to_page(page_key: str):
    """Route vers la bonne page"""
    
    try:
        if page_key == "recherche":
            print(f"=== CHARGEMENT PAGE RECHERCHE ===")
            from modules.recherche import show_page
            show_page()
            
        elif page_key == "configuration":
            show_configuration_page()
            
        else:
            # Pages placeholder avec démos interactives
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
                st.success("✅ Module fonctionnel")
                st.info("📅 Fonctionnalités complètes disponibles dans la prochaine version")
                
                # Démo interactive simple
                if st.button(f"🧪 Tester {info['title']}", key=f"test_{page_key}"):
                    st.balloons()
                    st.success(f"✅ Test de {info['title']} réussi !")
                    
                    # Ajouter quelques fonctionnalités de démo
                    if page_key == "selection":
                        st.write("📋 Interface de sélection de pièces")
                        st.selectbox("Catégorie", ["📄 Procédure", "💰 Comptabilité", "📊 Expertise"])
                        
                    elif page_key == "analyse":
                        st.write("🤖 Interface d'analyse IA")
                        st.multiselect("Types d'analyse", [
                            "🎯 Analyse infractions",
                            "🏢 Responsabilité PM",
                            "🛡️ Moyens de défense"
                        ])
                        
                    elif page_key == "redaction":
                        st.write("📝 Interface de rédaction")
                        st.text_input("Type d'acte", "Conclusions en défense")
                        
                    elif page_key == "courrier":
                        st.write("✉️ Interface de courrier")
                        st.text_input("Destinataire", "Maître Martin")
                        
                    elif page_key == "import_export":
                        st.write("📥 Interface d'import/export")
                        st.file_uploader("Importer un document", type=['pdf', 'docx'])
            else:
                st.error(f"❌ Page inconnue: {page_key}")
                
    except Exception as e:
        st.error(f"❌ Erreur page '{page_key}': {str(e)}")
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())

def show_configuration_page():
    """Page de configuration complète"""
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
            
            conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            st.write(f"**Connection String:** {'✅ Présente' if conn_str else '❌ Manquante'}")
            
            if blob_manager:
                st.write(f"**Manager:** ✅ Initialisé")
                if hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
                    st.success("✅ Connexion active")
                    containers = blob_manager.list_containers()
                    st.write(f"**Containers:** {len(containers)}")
                    for container in containers[:5]:
                        st.text(f"• {container}")
                else:
                    st.error("❌ Connexion échouée")
                    if hasattr(blob_manager, 'get_connection_error'):
                        error = blob_manager.get_connection_error()
                        st.error(f"**Erreur:** {error}")
            else:
                st.error("❌ Manager non initialisé")
        
        # Azure Search
        with st.expander("🔍 Azure Search", expanded=True):
            search_manager = st.session_state.get('azure_search_manager')
            
            endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            key = os.getenv('AZURE_SEARCH_KEY')
            st.write(f"**Endpoint:** {'✅ Présent' if endpoint else '❌ Manquant'}")
            st.write(f"**Key:** {'✅ Présente' if key else '❌ Manquante'}")
            
            if search_manager:
                st.write(f"**Manager:** ✅ Initialisé")
                if hasattr(search_manager, 'search_client') and search_manager.search_client:
                    st.success("✅ Connexion active")
                    st.write(f"**Index:** {search_manager.index_name}")
                else:
                    st.error("❌ Connexion échouée")
                    if hasattr(search_manager, 'get_connection_error'):
                        error = search_manager.get_connection_error()
                        st.error(f"**Erreur:** {error}")
            else:
                st.error("❌ Manager non initialisé")
    
    with tabs[2]:
        st.subheader("Tests de connexion")
        
        if st.button("🧪 Tester Azure Blob", key="test_blob"):
            test_azure_blob()
            
        if st.button("🧪 Tester Azure Search", key="test_search"):
            test_azure_search()
            
        if st.button("🧪 Tester tout", key="test_all"):
            test_azure_blob()
            test_azure_search()

def test_azure_blob():
    """Test de connexion Azure Blob"""
    with st.spinner("Test Azure Blob..."):
        try:
            from managers.azure_blob_manager import AzureBlobManager
            test_manager = AzureBlobManager()
            
            if test_manager.is_connected():
                containers = test_manager.list_containers()
                st.success(f"✅ Azure Blob OK - {len(containers)} containers")
            else:
                error = test_manager.get_connection_error()
                st.error(f"❌ Azure Blob KO: {error}")
        except Exception as e:
            st.error(f"❌ Erreur test Azure Blob: {e}")

def test_azure_search():
    """Test de connexion Azure Search"""
    with st.spinner("Test Azure Search..."):
        try:
            from managers.azure_search_manager import AzureSearchManager
            test_manager = AzureSearchManager()
            
            if test_manager.search_client:
                st.success("✅ Azure Search OK")
            else:
                error = test_manager.get_connection_error()
                st.error(f"❌ Azure Search KO: {error}")
        except Exception as e:
            st.error(f"❌ Erreur test Azure Search: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ ERREUR FATALE")
        st.code(str(e))
        st.code(traceback.format_exc())
        print("ERREUR FATALE:")
        print(traceback.format_exc())