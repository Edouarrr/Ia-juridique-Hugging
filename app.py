"""Application principale avec gestion Azure et interface de recherche améliorée"""

import streamlit as st
from datetime import datetime
import asyncio
from typing import Dict, List, Optional
import re
import sys
import os
import traceback

print("=== DÉMARRAGE APPLICATION ===")

# Configuration de la page
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SECTION 1: IMPORTS OPTIMISÉS ==========

# Import du nouveau système de modules avec gestion d'erreur
try:
    import modules
    print(f"✅ Modules importés : {len(modules.get_loaded_modules())} modules chargés")
except ImportError as e:
    print(f"❌ Erreur import modules : {e}")
    modules = None

# Vérifier la disponibilité des modules Azure
AZURE_AVAILABLE = False
AZURE_ERROR = None

try:
    import azure.search.documents
    import azure.storage.blob
    import azure.core
    AZURE_AVAILABLE = True
    print("✅ Modules Azure disponibles")
except ImportError as e:
    AZURE_ERROR = str(e)
    print(f"⚠️ Modules Azure non disponibles: {AZURE_ERROR}")

# Import de la configuration
try:
    from config.app_config import app_config, api_config
except ImportError:
    print("⚠️ config.app_config non trouvé, utilisation de la configuration par défaut")
    class DefaultConfig:
        version = "1.0.0"
        debug = False
        max_file_size_mb = 10
        max_files_per_upload = 5
        enable_azure_storage = False
        enable_azure_search = False
        enable_multi_llm = True
        enable_email = False
    
    app_config = DefaultConfig()
    api_config = {}

# Import des utilitaires
try:
    from utils.helpers import initialize_session_state
except ImportError:
    print("⚠️ utils.helpers non trouvé, utilisation de la fonction par défaut")
    def initialize_session_state():
        """Initialisation basique de session_state"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.search_history = []
            st.session_state.azure_documents = {}
            st.session_state.imported_documents = {}
            st.session_state.pieces_selectionnees = {}
            st.session_state.azure_blob_manager = None
            st.session_state.azure_search_manager = None
            # IMPORTANT: Interface unifiée par défaut
            st.session_state.use_simplified_version = True

try:
    from utils.styles import load_custom_css
except ImportError:
    print("⚠️ utils.styles non trouvé")
    def load_custom_css():
        pass

# Import du service de recherche universel
try:
    from managers.universal_search_service import UniversalSearchService
except ImportError:
    print("⚠️ managers.universal_search_service non trouvé")
    class UniversalSearchService:
        async def search(self, query: str, filters: Optional[Dict] = None):
            from types import SimpleNamespace
            return SimpleNamespace(
                total_count=0,
                documents=[],
                suggestions=[],
                facets={}
            )
        
        async def get_search_statistics(self):
            return {
                'total_searches': 0,
                'average_results': 0,
                'cache_size': 0,
                'popular_keywords': {}
            }

# ========== SECTION 2: STYLES CSS ==========

st.markdown("""
<style>
    /* Styles de base */
    .main-title {
        text-align: center;
        padding: 2rem 0;
    }
    
    .main-title h1 {
        color: #1a237e;
        font-size: 3rem;
    }
    
    .main-title p {
        color: #666;
        font-size: 1.2rem;
    }
    
    /* Version indicator optimisé */
    .version-indicator {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
        margin: 15px auto;
        max-width: 300px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .version-indicator.classic {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    /* Styles pour la barre de recherche */
    .search-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* Style pour les résultats */
    .result-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .result-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    
    /* Azure status optimisé */
    .azure-status {
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    
    .azure-connected {
        background-color: #d4edda;
        color: #155724;
    }
    
    .azure-disconnected {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Sidebar optimisée */
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    
    /* Boutons optimisés */
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1557a0;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# ========== SECTION 3: FONCTIONS AZURE ==========

def init_azure_managers():
    """Initialise les gestionnaires Azure de manière optimisée"""
    if not AZURE_AVAILABLE:
        st.session_state.azure_blob_manager = None
        st.session_state.azure_search_manager = None
        st.session_state.azure_error = AZURE_ERROR
        return
    
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state:
        try:
            if os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
                from managers.azure_blob_manager import AzureBlobManager
                st.session_state.azure_blob_manager = AzureBlobManager()
            else:
                st.session_state.azure_blob_manager = None
        except Exception as e:
            st.session_state.azure_blob_manager = None
            st.session_state.azure_blob_error = str(e)
    
    # Azure Search Manager
    if 'azure_search_manager' not in st.session_state:
        try:
            if os.getenv('AZURE_SEARCH_ENDPOINT') and os.getenv('AZURE_SEARCH_KEY'):
                from managers.azure_search_manager import AzureSearchManager
                st.session_state.azure_search_manager = AzureSearchManager()
            else:
                st.session_state.azure_search_manager = None
        except Exception as e:
            st.session_state.azure_search_manager = None
            st.session_state.azure_search_error = str(e)

def show_azure_status_compact():
    """Affichage compact du statut Azure dans la sidebar"""
    st.markdown("### 📊 État Azure")
    
    # Azure Blob
    blob_status = "❌ Non connecté"
    blob_class = "azure-disconnected"
    if st.session_state.get('azure_blob_manager'):
        if hasattr(st.session_state.azure_blob_manager, 'is_connected') and st.session_state.azure_blob_manager.is_connected():
            blob_status = "✅ Connecté"
            blob_class = "azure-connected"
    
    st.markdown(f'<div class="azure-status {blob_class}">🗄️ Blob Storage: {blob_status}</div>', unsafe_allow_html=True)
    
    # Azure Search
    search_status = "❌ Non connecté"
    search_class = "azure-disconnected"
    doc_count = 0
    
    if st.session_state.get('azure_search_manager'):
        if hasattr(st.session_state.azure_search_manager, 'search_client') and st.session_state.azure_search_manager.search_client:
            search_status = "✅ Connecté"
            search_class = "azure-connected"
            try:
                doc_count = st.session_state.azure_search_manager.get_document_count()
                search_status = f"✅ {doc_count:,} docs"
            except:
                pass
    
    st.markdown(f'<div class="azure-status {search_class}">🔍 Search: {search_status}</div>', unsafe_allow_html=True)

# ========== SECTION 4: INTERFACE UNIFIÉE ==========

def show_unified_search():
    """Affiche l'interface de recherche unifiée optimisée"""
    if not modules or not hasattr(modules, 'recherche'):
        st.error("❌ Module recherche unifié non disponible")
        st.info("Vérifiez que le fichier modules/recherche.py existe")
        
        # Bouton pour basculer vers la version classique
        if st.button("🔄 Utiliser la version classique"):
            st.session_state.use_simplified_version = False
            st.rerun()
        return
    
    try:
        # Indicateur de version
        st.markdown('<div class="version-indicator">✨ INTERFACE UNIFIÉE</div>', unsafe_allow_html=True)
        
        # Afficher l'interface unifiée
        modules.recherche.show_page()
        
    except Exception as e:
        st.error(f"❌ Erreur dans l'interface unifiée: {str(e)}")
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())
        
        if st.button("🔄 Basculer vers la version classique"):
            st.session_state.use_simplified_version = False
            st.rerun()

# ========== SECTION 5: INTERFACE CLASSIQUE ==========

def show_classic_search():
    """Affiche l'interface de recherche classique"""
    # Indicateur de version
    st.markdown('<div class="version-indicator classic">📋 INTERFACE CLASSIQUE</div>', unsafe_allow_html=True)
    
    # Zone de recherche principale
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    
    # Message informatif si Azure est connecté
    if st.session_state.get('azure_search_manager'):
        try:
            doc_count = st.session_state.azure_search_manager.get_document_count()
            if doc_count > 0:
                st.info(f"🎯 **{doc_count:,} documents juridiques** disponibles pour la recherche")
        except:
            pass
    
    # Barre de recherche
    with st.form(key="search_form", clear_on_submit=False):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            search_query = st.text_input(
                "Rechercher",
                placeholder="Ex: @VINCI2024 conclusions, abus de biens sociaux...",
                label_visibility="hidden",
                key="search_input"
            )
        
        with col2:
            search_button = st.form_submit_button(
                "🔍 Rechercher",
                use_container_width=True,
                type="primary"
            )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Effectuer la recherche
    if search_button and search_query:
        with st.spinner(f"🔍 Recherche en cours : **{search_query}**"):
            # TODO: Implémenter la logique de recherche classique
            st.info("Recherche classique en cours d'implémentation...")

# ========== SECTION 6: FONCTION PRINCIPALE ==========

def main():
    """Interface principale optimisée"""
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    init_azure_managers()
    
    # Titre principal
    st.markdown("""
    <div class='main-title'>
        <h1>⚖️ Assistant Pénal des Affaires IA</h1>
        <p>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== SIDEBAR OPTIMISÉE ==========
    with st.sidebar:
        # Section 1: Choix de version
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.header("🎨 Interface")
        
        # Toggle pour changer de version (unifié par défaut)
        use_classic = st.toggle(
            "Utiliser la version classique",
            value=not st.session_state.get('use_simplified_version', True),
            help="Basculer vers l'interface classique"
        )
        
        # Inverser la valeur pour la logique interne
        st.session_state.use_simplified_version = not use_classic
        
        if st.session_state.use_simplified_version:
            st.success("✨ Interface unifiée")
            st.caption("Toutes les fonctionnalités en une seule interface")
        else:
            st.info("📋 Interface classique")
            st.caption("Interface de recherche traditionnelle")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Section 2: État du système
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        show_azure_status_compact()
        
        # Métriques simples (pas de colonnes dans la sidebar)
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        st.metric("📄 Pièces sélectionnées", nb_pieces)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Section 3: Actions rapides
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.header("⚡ Actions rapides")
        
        if st.button("🔄 Réinitialiser Azure", use_container_width=True):
            init_azure_managers()
            st.rerun()
        
        if st.button("📊 État des modules", use_container_width=True):
            st.session_state.show_modules_debug = True
        
        if st.button("⚙️ Configuration", use_container_width=True):
            st.session_state.show_config_modal = True
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Section 4: Outils de développement
        with st.expander("🔧 Outils de développement"):
            if modules:
                # Afficher un résumé des modules
                loaded = modules.get_loaded_modules()
                st.write(f"**Modules chargés:** {len(loaded)}")
                
                # Vérifications rapides
                if st.button("🔍 Vérifier modules", use_container_width=True):
                    status = modules.debug_modules_status(output_to_streamlit=True)
                    st.code(status)
                
                if st.button("🧪 Test recherche unifié", use_container_width=True):
                    if hasattr(modules, 'recherche'):
                        st.success("✅ Module recherche disponible")
                        funcs = modules.get_module_functions_by_name('recherche')
                        st.write(f"Fonctions: {len(funcs)}")
                    else:
                        st.error("❌ Module recherche non chargé")
            else:
                st.error("❌ Système de modules non disponible")
        
        # Section 5: Aide
        with st.expander("📚 Aide"):
            if st.session_state.use_simplified_version:
                st.markdown("""
                **Interface unifiée :**
                - ✅ Analyse intelligente des requêtes
                - ✅ Enrichissement automatique
                - ✅ Toutes les fonctionnalités intégrées
                
                **Exemples :**
                - `rédiger plainte contre Vinci`
                - `analyser risques @dossier_2024`
                - `créer bordereau`
                """)
            else:
                st.markdown("""
                **Interface classique :**
                - Recherche simple par mots-clés
                - Filtres manuels
                - Export des résultats
                
                **Syntaxe :**
                - `@REF` : référence dossier
                - `type:plainte` : filtrer par type
                """)
    
    # ========== CONTENU PRINCIPAL ==========
    
    # Afficher l'interface selon le choix
    if st.session_state.use_simplified_version:
        show_unified_search()
    else:
        show_classic_search()
    
    # ========== MODALS ==========
    
    # Modal debug modules
    if st.session_state.get('show_modules_debug'):
        with st.container():
            st.markdown("---")
            st.header("📊 État des modules")
            
            if modules:
                # Utiliser la fonction de debug intégrée
                modules.create_streamlit_debug_page()
            else:
                st.error("Système de modules non disponible")
            
            if st.button("❌ Fermer", key="close_modules_debug"):
                st.session_state.show_modules_debug = False
                st.rerun()
    
    # Modal configuration
    if st.session_state.get('show_config_modal'):
        with st.container():
            st.markdown("---")
            st.header("⚙️ Configuration")
            
            tabs = st.tabs(["🔑 Variables", "🔧 Azure", "📦 Modules"])
            
            with tabs[0]:
                st.subheader("Variables d'environnement")
                vars_to_check = [
                    ("AZURE_STORAGE_CONNECTION_STRING", "Azure Blob", "🗄️"),
                    ("AZURE_SEARCH_ENDPOINT", "Azure Search", "🔍"),
                    ("AZURE_SEARCH_KEY", "Azure Key", "🔑"),
                    ("ANTHROPIC_API_KEY", "Claude API", "🤖"),
                    ("OPENAI_API_KEY", "OpenAI API", "🧠"),
                    ("GOOGLE_API_KEY", "Gemini API", "✨")
                ]
                
                for var, desc, icon in vars_to_check:
                    if os.getenv(var):
                        st.success(f"{icon} {desc} ✅")
                    else:
                        st.error(f"{icon} {desc} ❌")
            
            with tabs[1]:
                st.subheader("État Azure")
                if not AZURE_AVAILABLE:
                    st.error("SDK Azure non disponible")
                    st.code(AZURE_ERROR)
                else:
                    # Test Blob
                    if st.button("🧪 Tester Blob Storage"):
                        with st.spinner("Test en cours..."):
                            # TODO: Implémenter le test
                            st.info("Test à implémenter")
                    
                    # Test Search
                    if st.button("🧪 Tester Search"):
                        with st.spinner("Test en cours..."):
                            # TODO: Implémenter le test
                            st.info("Test à implémenter")
            
            with tabs[2]:
                st.subheader("Modules chargés")
                if modules:
                    loaded = modules.get_loaded_modules()
                    for name in sorted(loaded.keys()):
                        status = modules.get_module_status(name)
                        if status['is_stub']:
                            st.warning(f"⚠️ {name} (stub)")
                        else:
                            st.success(f"✅ {name} ({status['functions_count']} fonctions)")
                else:
                    st.error("Système de modules non disponible")
            
            if st.button("❌ Fermer", key="close_config"):
                st.session_state.show_config_modal = False
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# ========== POINT D'ENTRÉE ==========

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ ERREUR FATALE")
        st.code(str(e))
        st.code(traceback.format_exc())
        print("ERREUR FATALE:")
        print(traceback.format_exc())