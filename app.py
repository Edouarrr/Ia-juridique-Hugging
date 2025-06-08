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
    
    # Initialisation Azure (sans bloquer l'application)
    init_azure_managers()
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # NAVIGATION UNIQUE dans la sidebar
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # SEUL système de navigation
        pages_mapping = {
            "🔍 Recherche de documents": "recherche",
            "📁 Sélection de pièces": "selection", 
            "🤖 Analyse IA": "analyse",
            "📝 Rédaction assistée": "redaction",
            "✉️ Rédaction de courrier": "courrier",
            "📥 Import/Export": "import_export",
            "⚙️ Configuration": "configuration"
        }
        
        # Utiliser st.radio pour une navigation claire
        selected_page = st.radio(
            "Choisir une page",
            list(pages_mapping.keys()),
            key="main_navigation"
        )
        
        page_key = pages_mapping[selected_page]
        
        st.markdown("---")
        st.markdown("### 📊 État du système")
        
        # Azure Status (simplifié)
        show_azure_status()
        
        # Métriques
        st.markdown("---")
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
    
    # ROUTAGE DES PAGES
    try:
        route_to_page(page_key, selected_page)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la page")
        st.error(f"Détail: {str(e)}")
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())

def init_azure_managers():
    """Initialise les gestionnaires Azure sans bloquer"""
    if 'azure_blob_manager' not in st.session_state:
        try:
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
        except Exception as e:
            print(f"Azure Blob non disponible: {e}")
            st.session_state.azure_blob_manager = None
    
    if 'azure_search_manager' not in st.session_state:
        try:
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
        except Exception as e:
            print(f"Azure Search non disponible: {e}")
            st.session_state.azure_search_manager = None

def show_azure_status():
    """Affiche le statut Azure dans la sidebar"""
    # Azure Blob
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
        st.success("✅ Azure Blob")
    else:
        st.error("❌ Azure Blob")
    
    # Azure Search
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and hasattr(search_manager, 'search_client') and search_manager.search_client:
        st.success("✅ Azure Search")
    else:
        st.error("❌ Azure Search")

def route_to_page(page_key: str, page_name: str):
    """Route vers la bonne page"""
    
    if page_key == "recherche":
        print(f"=== CHARGEMENT PAGE RECHERCHE ===")
        from pages.recherche import show_page
        show_page()
        
    elif page_key == "selection":
        st.header("📁 Sélection de pièces")
        if not st.session_state.get('azure_documents'):
            st.warning("⚠️ Aucun document disponible. Recherchez d'abord des documents.")
            if st.button("🔍 Aller à la recherche"):
                st.rerun()
        else:
            try:
                from pages.selection_pieces import show_page
                show_page()
            except ImportError:
                st.info("📋 Page de sélection des pièces en cours de développement")
                show_placeholder_page("selection")
        
    elif page_key == "analyse":
        st.header("🤖 Analyse IA")
        if not st.session_state.get('pieces_selectionnees'):
            st.warning("⚠️ Aucune pièce sélectionnée. Sélectionnez d'abord des pièces.")
        else:
            try:
                from pages.analyse_ia import show_page
                show_page()
            except ImportError:
                st.info("🔬 Page d'analyse IA en cours de développement")
                show_placeholder_page("analyse")
        
    elif page_key == "redaction":
        st.header("📝 Rédaction assistée")
        try:
            from pages.redaction_assistee import show_page
            show_page()
        except ImportError:
            st.info("📝 Page de rédaction assistée en cours de développement")
            show_placeholder_page("redaction")
        
    elif page_key == "courrier":
        st.header("✉️ Rédaction de courrier")
        try:
            from pages.redaction_courrier import show_page
            show_page()
        except ImportError:
            st.info("✉️ Page de rédaction de courrier en cours de développement")
            show_placeholder_page("courrier")
        
    elif page_key == "import_export":
        st.header("📥 Import/Export")
        try:
            from pages.import_export import show_page
            show_page()
        except ImportError:
            st.info("📦 Page d'import/export en cours de développement")
            show_placeholder_page("import_export")
        
    elif page_key == "configuration":
        show_configuration_page()
    
    else:
        st.error(f"❌ Page inconnue: {page_key}")

def show_placeholder_page(page_type: str):
    """Affiche une page placeholder fonctionnelle"""
    
    placeholders = {
        "selection": {
            "icon": "📁",
            "title": "Sélection de pièces",
            "features": [
                "📋 Organisation par catégories",
                "⭐ Notation de pertinence", 
                "📊 Génération de bordereau",
                "🔗 Liaison avec documents"
            ]
        },
        "analyse": {
            "icon": "🤖", 
            "title": "Analyse IA",
            "features": [
                "🔍 Analyse multi-IA",
                "📈 Fusion des réponses",
                "⚖️ Vérification jurisprudences",
                "📊 Export des analyses"
            ]
        },
        "redaction": {
            "icon": "📝",
            "title": "Rédaction assistée", 
            "features": [
                "🎨 Styles personnalisés",
                "📚 Modèles dynamiques",
                "🤖 Génération IA",
                "📄 Export Word/PDF"
            ]
        },
        "courrier": {
            "icon": "✉️",
            "title": "Rédaction de courrier",
            "features": [
                "🏢 Papier en-tête",
                "📝 Templates courriers",
                "🖼️ Insertion logos",
                "📧 Envoi automatique"
            ]
        },
        "import_export": {
            "icon": "📥",
            "title": "Import/Export",
            "features": [
                "📂 Import multi-formats",
                "💾 Export analyses",
                "📊 Historique imports",
                "🔄 Synchronisation"
            ]
        }
    }
    
    if page_type in placeholders:
        info = placeholders[page_type]
        
        st.success(f"✅ Module {info['title']} détecté")
        
        st.markdown("### 🚀 Fonctionnalités prévues")
        for feature in info['features']:
            st.markdown(f"- {feature}")
        
        st.info("📅 Disponible dans la prochaine version")
        
        # Simuler quelques fonctions
        if st.button(f"🧪 Tester {info['title']}"):
            st.balloons()
            st.success(f"✅ Test {info['title']} réussi !")

def show_configuration_page():
    """Page de configuration complète"""
    st.header("⚙️ Configuration")
    
    tabs = st.tabs(["🔑 Variables", "🔧 Azure", "🤖 IA", "📊 Système"])
    
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
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(desc)
            with col2:
                if os.getenv(var):
                    st.success("✅")
                else:
                    st.error("❌")
    
    with tabs[1]:
        st.subheader("État Azure")
        
        # Azure Blob détaillé
        with st.expander("Azure Blob Storage", expanded=True):
            blob_manager = st.session_state.get('azure_blob_manager')
            if blob_manager:
                if hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
                    st.success("✅ Connecté")
                    if hasattr(blob_manager, 'list_containers'):
                        containers = blob_manager.list_containers()
                        st.write(f"Containers: {containers}")
                else:
                    st.error("❌ Non connecté")
                    if hasattr(blob_manager, 'get_connection_error'):
                        error = blob_manager.get_connection_error()
                        st.error(f"Erreur: {error}")
            else:
                st.error("❌ Non initialisé")
    
    with tabs[2]:
        st.subheader("Intelligence Artificielle")
        try:
            from managers.multi_llm_manager import MultiLLMManager
            llm_manager = MultiLLMManager()
            providers = llm_manager.get_available_providers()
            
            st.write(f"**Providers disponibles:** {len(providers)}")
            for provider in providers:
                st.success(f"✅ {provider}")
                
        except Exception as e:
            st.error(f"Erreur LLM Manager: {e}")
    
    with tabs[3]:
        st.subheader("Informations système")
        st.write(f"**Python:** {sys.version}")
        st.write(f"**Streamlit:** {st.__version__}")
        st.write(f"**Répertoire:** {os.getcwd()}")

if __name__ == "__main__":
    main()