# app.py
"""Application principale modulaire avec gestion des modules optionnels"""

import streamlit as st
import os
import sys

# Configuration de l'encodage pour les emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Import avec gestion d'erreur
try:
    from config.app_config import APP_TITLE, APP_ICON, PAGES
except ImportError as e:
    st.error(f"Erreur d'import config: {e}")
    APP_TITLE = "Assistant Pénal des Affaires IA"
    APP_ICON = "⚖️"
    PAGES = {
        "Accueil": "🏠",
        "Analyse juridique": "📋",
        "Recherche de jurisprudence": "🔍",
        "Visualisation": "📊", 
        "Assistant interactif": "💬",
        "Configuration": "⚙️"
    }

# Configuration de la page - DOIT être la première commande Streamlit
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import des styles avec gestion d'erreur
try:
    from utils.styles import load_custom_css
    load_custom_css()
except ImportError:
    st.warning("Module de styles non disponible")


def initialize_session_state():
    """Initialise toutes les variables de session"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.azure_documents = {}
        st.session_state.pieces_selectionnees = {}
        st.session_state.search_query = ""
        st.session_state.current_folder_path = ""
        st.session_state.learned_styles = {}
        st.session_state.letterhead_template = None


def initialize_managers_safe():
    """Initialise les gestionnaires avec gestion d'erreur"""
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state:
        try:
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
        except Exception as e:
            st.error(f"Erreur initialisation Azure Blob: {e}")
            st.session_state.azure_blob_manager = None
    
    # Azure Search Manager
    if 'azure_search_manager' not in st.session_state:
        try:
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
        except Exception as e:
            st.error(f"Erreur initialisation Azure Search: {e}")
            st.session_state.azure_search_manager = None
    
    # Multi-LLM Manager
    if 'multi_llm_manager' not in st.session_state:
        try:
            from managers.multi_llm_manager import MultiLLMManager
            st.session_state.multi_llm_manager = MultiLLMManager()
        except Exception as e:
            st.error(f"Erreur initialisation Multi-LLM: {e}")
            st.session_state.multi_llm_manager = None
    
    # Style Analyzer
    if 'style_analyzer' not in st.session_state:
        try:
            from managers.style_analyzer import StyleAnalyzer
            st.session_state.style_analyzer = StyleAnalyzer()
        except Exception as e:
            st.error(f"Erreur initialisation Style Analyzer: {e}")
            st.session_state.style_analyzer = None


def main():
    """Application principale"""
    # Initialisation
    initialize_session_state()
    
    # Initialiser les managers (optionnel)
    initialize_managers_safe()
    
    # Titre principal
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>{APP_ICON} {APP_TITLE}</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar avec navigation
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # Définir les modules de pages
        page_modules = {
            "Accueil": "pages.accueil",
            "Analyse juridique": "pages.analyse",
            "Recherche de jurisprudence": "pages.recherche",
            "Visualisation": "pages.visualisation",
            "Assistant interactif": "pages.assistant",
            "Configuration": "pages.configuration"
        }
        
        # Sélection de la page
        selected_page = st.selectbox(
            "Choisir une fonctionnalité",
            list(page_modules.keys()),
            format_func=lambda x: f"{PAGES.get(x, '📄')} {x}"
        )
        
        st.markdown("---")
        
        # État du système simplifié
        st.markdown("### 📊 État du système")
        
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        st.metric("Documents", nb_docs)
        st.metric("Pièces", nb_pieces)
    
    # Zone principale - Afficher la page sélectionnée
    try:
        # Import dynamique du module de la page
        module = __import__(page_modules[selected_page], fromlist=['show'])
        
        # Appeler la fonction show() du module
        module.show()
        
    except ImportError as e:
        st.error(f"❌ Impossible de charger la page '{selected_page}'")
        st.error(f"Module manquant : {page_modules[selected_page]}")
        
        # Page d'accueil par défaut
        st.markdown("## 🏠 Bienvenue")
        st.info("""
        Certains modules ne sont pas encore installés.
        
        **Modules disponibles :**
        - Configuration de base ✅
        - Interface utilisateur ✅
        
        **Modules à installer :**
        - Gestionnaires Azure
        - Analyseurs de style
        - Multi-LLM
        """)
        
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        with st.expander("Détails de l'erreur"):
            st.exception(e)


if __name__ == "__main__":
    main()