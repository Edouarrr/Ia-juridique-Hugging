# app.py
"""Application principale modulaire avec toutes les fonctionnalités"""

import streamlit as st
import os
import sys

# Configuration de l'encodage pour les emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from config.app_config import APP_TITLE, APP_ICON, PAGES
from utils.styles import load_custom_css

# Configuration de la page - DOIT être la première commande Streamlit
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)


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
        st.session_state.selected_container = None
        st.session_state.dossier_actif = None
        st.session_state.dynamic_search_prompts = {}
        st.session_state.dynamic_templates = {}


def initialize_azure_managers():
    """Initialise les gestionnaires Azure dans la session"""
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


def display_system_status():
    """Affiche l'état du système dans la sidebar"""
    st.markdown("### 📊 État du système")
    
    # État Azure Blob
    if st.session_state.get('azure_blob_manager') and st.session_state.azure_blob_manager.is_connected():
        st.success("✅ Azure Blob connecté")
    else:
        st.error("❌ Azure Blob non connecté")
    
    # État Azure Search
    if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
        st.success("✅ Azure Search actif")
    else:
        st.warning("⚠️ Azure Search non disponible")
    
    # État Multi-LLM
    if st.session_state.get('multi_llm_manager'):
        nb_llms = len(st.session_state.multi_llm_manager.clients)
        if nb_llms > 0:
            st.success(f"✅ {nb_llms} IA disponibles")
        else:
            st.warning("⚠️ Aucune IA configurée")
    else:
        st.error("❌ Multi-LLM non disponible")
    
    # Métriques
    st.markdown("### 📈 Métriques")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nb_docs = len(st.session_state.get('azure_documents', {}))
        st.metric("Documents", nb_docs)
        
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        st.metric("Pièces", nb_pieces)
    
    with col2:
        nb_styles = len(st.session_state.get('learned_styles', {}))
        st.metric("Styles", nb_styles)
        
        # Papier en-tête
        if st.session_state.get('letterhead_template'):
            st.metric("Papier en-tête", "✅")
        else:
            st.metric("Papier en-tête", "❌")


def main():
    """Application principale"""
    # Initialisation
    initialize_session_state()
    
    # Charger les styles CSS
    try:
        load_custom_css()
    except Exception as e:
        st.warning(f"Impossible de charger les styles CSS: {e}")
    
    # Initialiser les managers Azure
    initialize_azure_managers()
    
    # Titre principal avec style
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: #1a237e; font-size: 3rem; margin-bottom: 0.5rem;'>{APP_ICON} {APP_TITLE}</h1>
        <p style='color: #666; font-size: 1.2rem; margin: 0;'>Intelligence artificielle au service du droit pénal économique</p>
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
            format_func=lambda x: f"{PAGES[x]} {x}"
        )
        
        st.markdown("---")
        
        # Mode debug pour Hugging Face
        debug_mode = st.checkbox("🐛 Mode Debug", value=False, key="debug_mode")
        
        if debug_mode:
            st.markdown("### 🔍 Debug Info")
            st.code(f"Page: {selected_page}")
            st.code(f"Module: {page_modules.get(selected_page)}")
            st.code(f"Working dir: {os.getcwd()}")
        
        st.markdown("---")
        
        # État du système
        display_system_status()
        
        # Informations supplémentaires
        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        st.info("""
        **Version**: 3.0.0
        **Dernière mise à jour**: Juin 2025
        
        📧 **Support**: contact@assistant-penal.ai
        📚 **Documentation**: [Voir la doc](https://docs.assistant-penal.ai)
        """)
    
    # Zone principale - Afficher la page sélectionnée
    try:
        # Import spécifique pour Hugging Face
        if selected_page == "Accueil":
            # Import direct pour éviter les problèmes sur Hugging Face
            try:
                from pages import accueil
                if hasattr(accueil, 'show'):
                    accueil.show()
                else:
                    st.error("La fonction show() n'est pas trouvée dans pages.accueil")
                    # Page de secours minimale
                    st.header("🏠 Bienvenue")
                    st.info("Utilisez le menu de navigation pour accéder aux fonctionnalités")
            except Exception as e:
                st.error(f"Erreur lors du chargement de la page d'accueil: {e}")
                if debug_mode:
                    st.exception(e)
        else:
            # Import dynamique pour les autres pages
            module = __import__(page_modules[selected_page], fromlist=['show'])
            if hasattr(module, 'show'):
                module.show()
            else:
                st.error(f"❌ La page '{selected_page}' n'a pas de fonction 'show()'")
        
    except ImportError as e:
        st.error(f"❌ Impossible de charger la page '{selected_page}'")
        st.error(f"Erreur d'import : {str(e)}")
        
        # Afficher les détails de l'erreur en mode debug
        if debug_mode:
            with st.expander("🐛 Détails de l'erreur"):
                st.exception(e)
                
                # Vérifier les imports
                st.markdown("**Vérification des imports :**")
                
                # Essayer d'importer chaque module individuellement
                modules_to_check = [
                    "config.app_config",
                    "utils.styles",
                    "utils.helpers",
                    "models.dataclasses",
                    page_modules[selected_page]
                ]
                
                for module_name in modules_to_check:
                    try:
                        __import__(module_name)
                        st.success(f"✅ {module_name}")
                    except ImportError as import_error:
                        st.error(f"❌ {module_name}: {str(import_error)}")
        
        # Page de secours
        st.markdown("### 🏠 Navigation rapide")
        st.info("""
        L'application rencontre un problème de chargement.
        
        **Fonctionnalités disponibles :**
        - 🔍 Recherche de documents
        - 📋 Analyse juridique
        - 💬 Assistant interactif
        - 📊 Visualisation
        - ⚙️ Configuration
        
        Essayez de sélectionner une autre page dans le menu.
        """)
    
    except AttributeError as e:
        st.error(f"❌ La page '{selected_page}' n'a pas de fonction 'show()'")
        if debug_mode:
            st.error(f"Erreur : {str(e)}")
            st.exception(e)
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la page : {str(e)}")
        
        # Afficher plus de détails si mode debug
        if debug_mode:
            with st.expander("🐛 Détails de l'erreur"):
                st.exception(e)
                
                # Lister les fichiers pour debug
                st.markdown("**Structure des fichiers:**")
                for root, dirs, files in os.walk("."):
                    level = root.replace(".", "", 1).count(os.sep)
                    indent = " " * 2 * level
                    st.text(f"{indent}{os.path.basename(root)}/")
                    subindent = " " * 2 * (level + 1)
                    for file in files[:5]:  # Limiter à 5 fichiers par dossier
                        if not file.startswith('.'):
                            st.text(f"{subindent}{file}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>© 2025 Assistant Pénal des Affaires IA - Tous droits réservés</p>
            <p style='font-size: 0.9rem;'>Développé avec ❤️ pour les professionnels du droit</p>
        </div>
        """, 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()