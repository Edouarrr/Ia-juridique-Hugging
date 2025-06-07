# app.py
"""
Assistant Pénal des Affaires IA
Point d'entrée principal de l'application Streamlit
"""

import streamlit as st
import sys
from pathlib import Path
import logging
from datetime import datetime

# Configuration de base
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire racine au path pour les imports
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Imports des modules
try:
    from config import APP_TITLE, APP_ICON, PAGES
    from managers import LLMManager, DocumentManager, JurisprudenceVerifier
    from utils import load_custom_css
except ImportError as e:
    st.error(f"""
    ❌ Erreur d'import des modules : {str(e)}
    
    Assurez-vous que tous les modules sont correctement installés :
    - config/
    - managers/
    - models/
    - pages/
    - utils/
    """)
    st.stop()

def initialize_session_state():
    """Initialise les variables de session"""
    # Managers
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = LLMManager()
        logger.info("LLM Manager initialisé")
    
    if 'doc_manager' not in st.session_state:
        st.session_state.doc_manager = DocumentManager()
        logger.info("Document Manager initialisé")
    
    if 'jurisprudence_verifier' not in st.session_state:
        st.session_state.jurisprudence_verifier = JurisprudenceVerifier()
        logger.info("Jurisprudence Verifier initialisé")
    
    # Statistiques
    if 'analyses_count' not in st.session_state:
        st.session_state.analyses_count = 0
    
    if 'verifications_count' not in st.session_state:
        st.session_state.verifications_count = 0
    
    if 'documents_count' not in st.session_state:
        st.session_state.documents_count = 0
    
    if 'messages_count' not in st.session_state:
        st.session_state.messages_count = 0
    
    # Autres
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    
    logger.info("Session state initialisé")

def create_sidebar():
    """Crée la barre latérale de navigation"""
    with st.sidebar:
        # Logo et titre
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1>{APP_ICON}</h1>
            <h3>{APP_TITLE}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        
        # Menu de navigation
        selected_page = None
        for page_name, icon in PAGES.items():
            if st.button(
                f"{icon} {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page_name else "secondary"
            ):
                selected_page = page_name
        
        if selected_page:
            st.session_state.current_page = selected_page
            logger.info(f"Navigation vers : {selected_page}")
        
        st.markdown("---")
        
        # Statistiques rapides
        st.markdown("### 📊 Statistiques")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Analyses", st.session_state.analyses_count)
            st.metric("Documents", st.session_state.documents_count)
        with col2:
            st.metric("Vérifications", st.session_state.verifications_count)
            st.metric("Messages", st.session_state.messages_count)
        
        st.markdown("---")
        
        # Informations
        st.markdown("### ℹ️ Informations")
        st.caption(f"Version 3.0.0")
        st.caption(f"Dernière activité : {datetime.now().strftime('%H:%M')}")
        
        # Liens utiles
        with st.expander("🔗 Liens utiles"):
            st.markdown("""
            - [Documentation](https://docs.assistant-juridique.ai)
            - [Support](mailto:support@assistant-juridique.ai)
            - [GitHub](https://github.com/assistant-juridique)
            """)

def load_page(page_name: str):
    """Charge la page sélectionnée"""
    try:
        # Mapping des pages vers les modules
        page_modules = {
            "Accueil": "pages.accueil",
            "Analyse juridique": "pages.analyse",
            "Recherche de jurisprudence": "pages.recherche",
            "Visualisation": "pages.visualisation",
            "Assistant interactif": "pages.assistant",
            "Configuration": "pages.configuration"
        }
        
        if page_name in page_modules:
            # Import dynamique du module
            module_name = page_modules[page_name]
            logger.info(f"Chargement du module : {module_name}")
            
            # Importer et exécuter la fonction show()
            import importlib
            module = importlib.import_module(module_name)
            
            if hasattr(module, 'show'):
                module.show()
            else:
                st.error(f"La page {page_name} n'a pas de fonction show()")
        else:
            st.error(f"Page non trouvée : {page_name}")
            
    except Exception as e:
        st.error(f"""
        ❌ Erreur lors du chargement de la page '{page_name}' :
        
        {str(e)}
        
        Vérifiez que le fichier correspondant existe dans le dossier 'pages/'
        """)
        logger.error(f"Erreur chargement page {page_name}: {str(e)}", exc_info=True)

def main():
    """Fonction principale"""
    # Charger les styles CSS
    load_custom_css()
    
    # Initialiser la session
    initialize_session_state()
    
    # Créer la sidebar
    create_sidebar()
    
    # Charger la page actuelle
    current_page = st.session_state.current_page
    logger.info(f"Page actuelle : {current_page}")
    
    # Zone principale
    with st.container():
        load_page(current_page)
    
    # Footer global (optionnel)
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.8em;'>
        © 2025 Assistant Pénal des Affaires IA | 
        <a href='#' style='color: gray;'>Mentions légales</a> | 
        <a href='#' style='color: gray;'>Confidentialité</a>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    try:
        logger.info("Démarrage de l'application")
        main()
    except Exception as e:
        st.error(f"""
        ❌ Erreur critique : {str(e)}
        
        Veuillez vérifier :
        1. Que tous les modules sont correctement installés
        2. Que les dépendances sont satisfaites (requirements.txt)
        3. Les logs pour plus de détails
        """)
        logger.error("Erreur critique", exc_info=True)