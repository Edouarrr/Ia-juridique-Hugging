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

# DIAGNOSTIC COMPLET AU DÉMARRAGE
print("="*50)
print("DIAGNOSTIC DÉMARRAGE APPLICATION")
print("="*50)
print(f"Python version: {sys.version}")
print(f"Streamlit version: {st.__version__}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

# Vérifier les imports critiques
try:
    import config.app_config
    print("✓ config.app_config importé")
except Exception as e:
    print(f"✗ Erreur import config.app_config: {e}")
    st.error(f"Impossible d'importer config.app_config: {e}")

try:
    import utils.helpers
    print("✓ utils.helpers importé")
except Exception as e:
    print(f"✗ Erreur import utils.helpers: {e}")
    st.error(f"Impossible d'importer utils.helpers: {e}")

try:
    import utils.styles
    print("✓ utils.styles importé")
except Exception as e:
    print(f"✗ Erreur import utils.styles: {e}")

# Variables d'environnement
print("\nVARIABLES D'ENVIRONNEMENT AZURE:")
print(f"AZURE_STORAGE_CONNECTION_STRING: {'✓' if os.getenv('AZURE_STORAGE_CONNECTION_STRING') else '✗'}")
print(f"AZURE_SEARCH_ENDPOINT: {'✓' if os.getenv('AZURE_SEARCH_ENDPOINT') else '✗'}")
print(f"AZURE_SEARCH_KEY: {'✓' if os.getenv('AZURE_SEARCH_KEY') else '✗'}")

def safe_import(module_path, display_name=None):
    """Import sécurisé avec gestion d'erreur"""
    try:
        module = __import__(module_path, fromlist=[''])
        print(f"✓ {display_name or module_path} importé")
        return module
    except Exception as e:
        print(f"✗ Erreur import {display_name or module_path}: {e}")
        print(traceback.format_exc())
        return None

def main():
    """Interface principale de l'application"""
    
    # Imports sécurisés
    app_config = safe_import('config.app_config', 'Configuration')
    helpers = safe_import('utils.helpers', 'Helpers')
    styles = safe_import('utils.styles', 'Styles')
    
    # Si les imports critiques échouent, afficher une page d'erreur
    if not app_config or not helpers:
        st.error("❌ Erreur critique : Impossible de charger les modules de base")
        st.code(f"""
Modules dans le répertoire actuel:
{os.listdir('.')}

Contenu du dossier config:
{os.listdir('config') if os.path.exists('config') else 'Dossier config non trouvé'}

Contenu du dossier utils:
{os.listdir('utils') if os.path.exists('utils') else 'Dossier utils non trouvé'}

Contenu du dossier pages:
{os.listdir('pages') if os.path.exists('pages') else 'Dossier pages non trouvé'}
        """)
        return
    
    # Initialisation
    try:
        helpers.initialize_session_state()
        print("✓ Session state initialisé")
    except Exception as e:
        print(f"✗ Erreur initialisation session state: {e}")
        st.error(f"Erreur initialisation: {e}")
    
    # Charger les styles
    if styles and hasattr(styles, 'load_custom_css'):
        try:
            styles.load_custom_css()
            print("✓ CSS chargé")
        except Exception as e:
            print(f"✗ Erreur chargement CSS: {e}")
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Diagnostic dans l'interface
    with st.expander("🔧 Diagnostic système", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Modules", f"{len([m for m in sys.modules if m.startswith('pages')])}")
        
        with col2:
            st.metric("Azure vars", f"{sum(1 for v in ['AZURE_STORAGE_CONNECTION_STRING', 'AZURE_SEARCH_ENDPOINT', 'AZURE_SEARCH_KEY'] if os.getenv(v))}/3")
        
        with col3:
            st.metric("Session state", len(st.session_state))
    
    # Navigation simplifiée
    pages = ["Recherche", "Configuration", "Test"]
    page = st.selectbox("Page", pages)
    
    if page == "Recherche":
        try:
            # Tentative d'import de la page recherche
            recherche = safe_import('pages.recherche', 'Page Recherche')
            if recherche and hasattr(recherche, 'show_page'):
                recherche.show_page()
            else:
                st.error("❌ Impossible de charger la page recherche")
                st.info("Vérifiez que le fichier pages/recherche.py existe et contient une fonction show_page()")
        except Exception as e:
            st.error(f"Erreur page recherche: {e}")
            st.code(traceback.format_exc())
    
    elif page == "Configuration":
        st.header("⚙️ Configuration")
        
        # Liste tous les fichiers Python trouvés
        st.subheader("📁 Structure des fichiers")
        
        for root, dirs, files in os.walk('.'):
            # Ignorer les dossiers cachés et __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 2 * level
            st.text(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if file.endswith('.py'):
                    st.text(f"{subindent}{file}")
    
    elif page == "Test":
        st.header("🧪 Page de test")
        st.success("✅ L'application Streamlit fonctionne!")
        
        # Test d'import des managers
        st.subheader("Test des imports managers")
        
        managers_to_test = [
            'managers.azure_blob_manager',
            'managers.azure_search_manager',
            'managers.multi_llm_manager',
            'managers.document_manager',
            'managers.dynamic_generators',
            'managers.legal_search'
        ]
        
        for manager in managers_to_test:
            result = safe_import(manager)
            if result:
                st.success(f"✅ {manager}")
            else:
                st.error(f"❌ {manager}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ ERREUR FATALE")
        st.code(str(e))
        st.code(traceback.format_exc())
        
        # Log complet
        print("ERREUR FATALE:")
        print(traceback.format_exc())