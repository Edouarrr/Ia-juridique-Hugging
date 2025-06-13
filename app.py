"""Application principale avec interface optimisée et navigation intelligente"""

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
    initial_sidebar_state="collapsed"  # Sidebar fermée par défaut pour plus d'espace
)

# ========== SECTION 1: IMPORTS OPTIMISÉS ==========

# Import du nouveau système de modules
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
    print("⚠️ config.app_config non trouvé")
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
            st.session_state.use_simplified_version = True
            st.session_state.current_tab = "recherche"

try:
    from utils.styles import load_custom_css
except ImportError:
    def load_custom_css():
        pass

# Import du service de recherche
try:
    from managers.universal_search_service import UniversalSearchService
except ImportError:
    class UniversalSearchService:
        async def search(self, query: str, filters: Optional[Dict] = None):
            from types import SimpleNamespace
            return SimpleNamespace(
                total_count=0,
                documents=[],
                suggestions=[],
                facets={}
            )

# ========== SECTION 2: STYLES CSS OPTIMISÉS ==========

st.markdown("""
<style>
    /* === STYLES GLOBAUX === */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Header optimisé */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Barre de recherche moderne */
    .search-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    
    .stTextInput > div > div {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #1a237e;
        box-shadow: 0 0 0 3px rgba(26,35,126,0.1);
    }
    
    /* Navigation intelligente */
    .nav-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .nav-button {
        background: white;
        border: 2px solid transparent;
        padding: 12px 24px;
        border-radius: 8px;
        margin: 0 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .nav-button:hover {
        background: #f0f4ff;
        border-color: #1a237e;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26,35,126,0.15);
    }
    
    .nav-button.active {
        background: #1a237e;
        color: white;
        border-color: #1a237e;
    }
    
    /* Cards et conteneurs */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border: 1px solid #f0f0f0;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        border-color: #1a237e;
    }
    
    /* Status badges améliorés */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .status-badge.connected {
        background: #e8f5e9;
        color: #2e7d32;
    }
    
    .status-badge.disconnected {
        background: #ffebee;
        color: #c62828;
    }
    
    .status-badge.warning {
        background: #fff3e0;
        color: #ef6c00;
    }
    
    /* Quick actions */
    .quick-action-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .quick-action-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .quick-action-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Résultats de recherche optimisés */
    .result-card-modern {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1a237e;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .result-card-modern:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        transform: translateX(5px);
    }
    
    .result-card-modern::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(to bottom, #1a237e, #3949ab);
        transition: width 0.3s ease;
    }
    
    .result-card-modern:hover::before {
        width: 8px;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .nav-button {
            padding: 10px 16px;
            margin: 4px;
            font-size: 0.9rem;
        }
        
        .quick-action-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Sidebar moderne */
    .sidebar-mini {
        position: fixed;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        z-index: 999;
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px 12px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.875rem;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Version indicator moderne */
    .version-badge {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 30px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 1000;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .version-badge:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Statistiques visuelles */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# ========== SECTION 3: FONCTIONS AZURE ==========

def init_azure_managers():
    """Initialise les gestionnaires Azure avec logs détaillés"""
    
    print("=== INITIALISATION AZURE ===")
    
    if not AZURE_AVAILABLE:
        print(f"⚠️ Azure non disponible: {AZURE_ERROR}")
        st.session_state.azure_blob_manager = None
        st.session_state.azure_search_manager = None
        st.session_state.azure_error = AZURE_ERROR
        return
    
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state or st.session_state.azure_blob_manager is None:
        print("Initialisation Azure Blob Manager...")
        try:
            if not os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
                print("⚠️ AZURE_STORAGE_CONNECTION_STRING non définie")
                st.session_state.azure_blob_manager = None
                st.session_state.azure_blob_error = "Connection string non définie"
            else:
                from managers.azure_blob_manager import AzureBlobManager
                manager = AzureBlobManager()
                st.session_state.azure_blob_manager = manager
                
                if hasattr(manager, 'is_connected') and manager.is_connected():
                    print("✅ Azure Blob connecté avec succès")
                else:
                    print("❌ Azure Blob non connecté")
                        
        except Exception as e:
            print(f"❌ Erreur Azure Blob: {e}")
            st.session_state.azure_blob_manager = None
            st.session_state.azure_blob_error = str(e)
    
    # Azure Search Manager  
    if 'azure_search_manager' not in st.session_state or st.session_state.azure_search_manager is None:
        print("Initialisation Azure Search Manager...")
        try:
            if not os.getenv('AZURE_SEARCH_ENDPOINT') or not os.getenv('AZURE_SEARCH_KEY'):
                print("⚠️ Variables Azure Search non définies")
                st.session_state.azure_search_manager = None
                st.session_state.azure_search_error = "Endpoint ou clé non définis"
            else:
                from managers.azure_search_manager import AzureSearchManager
                manager = AzureSearchManager()
                st.session_state.azure_search_manager = manager
                
                if hasattr(manager, 'search_client') and manager.search_client:
                    print("✅ Azure Search connecté avec succès")
                else:
                    print("❌ Azure Search non connecté")
                        
        except Exception as e:
            print(f"❌ Erreur Azure Search: {e}")
            st.session_state.azure_search_manager = None
            st.session_state.azure_search_error = str(e)

def reinit_azure():
    """Force la réinitialisation d'Azure"""
    print("=== RÉINITIALISATION AZURE FORCÉE ===")
    
    for key in ['azure_blob_manager', 'azure_search_manager', 'azure_error', 
                'azure_blob_error', 'azure_search_error']:
        if key in st.session_state:
            del st.session_state[key]
    
    init_azure_managers()
    st.rerun()

# ========== SECTION 4: COMPOSANTS UI ==========

def show_status_bar():
    """Affiche une barre de statut moderne en haut de l'application"""
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # Azure Blob Status
        blob_connected = False
        if st.session_state.get('azure_blob_manager'):
            if hasattr(st.session_state.azure_blob_manager, 'is_connected') and st.session_state.azure_blob_manager.is_connected():
                blob_connected = True
        
        if blob_connected:
            st.markdown('<span class="status-badge connected">🗄️ Blob: Connecté</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge disconnected">🗄️ Blob: Déconnecté</span>', unsafe_allow_html=True)
    
    with col2:
        # Azure Search Status
        search_connected = False
        doc_count = 0
        if st.session_state.get('azure_search_manager'):
            if hasattr(st.session_state.azure_search_manager, 'search_client') and st.session_state.azure_search_manager.search_client:
                search_connected = True
                try:
                    doc_count = st.session_state.azure_search_manager.get_document_count()
                except:
                    pass
        
        if search_connected:
            st.markdown(f'<span class="status-badge connected">🔍 Search: {doc_count:,} docs</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge disconnected">🔍 Search: Déconnecté</span>', unsafe_allow_html=True)
    
    with col3:
        # Modules Status
        if modules:
            loaded = len(modules.get_loaded_modules())
            st.markdown(f'<span class="status-badge connected">📦 Modules: {loaded}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge warning">📦 Modules: Non chargés</span>', unsafe_allow_html=True)
    
    with col4:
        # Settings button
        if st.button("⚙️", help="Paramètres", key="settings_top"):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)

def show_navigation_bar():
    """Affiche la barre de navigation intelligente"""
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    # Navigation tabs
    tabs = {
        "recherche": {"icon": "🔍", "label": "Recherche", "desc": "Recherche intelligente"},
        "redaction": {"icon": "✍️", "label": "Rédaction", "desc": "Créer des documents"},
        "analyse": {"icon": "📊", "label": "Analyse", "desc": "Analyse juridique IA"},
        "pieces": {"icon": "📎", "label": "Pièces", "desc": "Gestion des pièces"},
        "timeline": {"icon": "📅", "label": "Timeline", "desc": "Chronologie des événements"},
        "bordereau": {"icon": "📋", "label": "Bordereau", "desc": "Générer des bordereaux"},
        "jurisprudence": {"icon": "⚖️", "label": "Jurisprudence", "desc": "Base de jurisprudence"},
        "outils": {"icon": "🛠️", "label": "Outils", "desc": "Outils avancés"}
    }
    
    # Create columns for navigation buttons
    cols = st.columns(len(tabs))
    
    for idx, (key, info) in enumerate(tabs.items()):
        with cols[idx]:
            # Check if tab is active
            is_active = st.session_state.get('current_tab', 'recherche') == key
            
            # Create button with custom styling
            if st.button(
                f"{info['icon']} {info['label']}", 
                key=f"nav_{key}",
                help=info['desc'],
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_tab = key
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_quick_actions():
    """Affiche les actions rapides contextuelles"""
    st.markdown("### ⚡ Actions rapides")
    
    # Actions based on current tab
    current_tab = st.session_state.get('current_tab', 'recherche')
    
    if current_tab == 'recherche':
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Importer documents", use_container_width=True):
                st.session_state.show_import_modal = True
        
        with col2:
            if st.button("🔄 Recherche avancée", use_container_width=True):
                st.session_state.show_advanced_search = True
        
        with col3:
            if st.button("📊 Statistiques", use_container_width=True):
                st.session_state.show_stats = True
        
        with col4:
            if st.button("💾 Exporter résultats", use_container_width=True):
                st.session_state.show_export = True
                
    elif current_tab == 'redaction':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Nouvelle plainte", use_container_width=True):
                st.session_state.doc_type = "plainte"
                
        with col2:
            if st.button("📄 Nouvelles conclusions", use_container_width=True):
                st.session_state.doc_type = "conclusions"
                
        with col3:
            if st.button("📑 Depuis template", use_container_width=True):
                st.session_state.show_templates = True

def show_search_interface():
    """Interface de recherche optimisée"""
    # Search container
    with st.container():
        st.markdown('<div class="search-section fade-in">', unsafe_allow_html=True)
        
        # Search header
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("### 🔍 Recherche intelligente")
            
            # Get document count if Azure is connected
            doc_count = 0
            if st.session_state.get('azure_search_manager') and hasattr(st.session_state.azure_search_manager, 'search_client'):
                try:
                    doc_count = st.session_state.azure_search_manager.get_document_count()
                except:
                    pass
            
            if doc_count > 0:
                st.caption(f"Recherchez parmi {doc_count:,} documents juridiques")
        
        with col2:
            # Search mode toggle
            search_mode = st.selectbox(
                "Mode",
                ["Simple", "Avancée", "Juridique"],
                key="search_mode",
                label_visibility="collapsed"
            )
        
        # Search form
        with st.form(key="search_form", clear_on_submit=False):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Enhanced search input
                if search_mode == "Simple":
                    placeholder = "Rechercher des documents, parties, infractions..."
                elif search_mode == "Avancée":
                    placeholder = "Utilisez @REF, type:plainte, partie:nom, date:2024..."
                else:
                    placeholder = "Ex: jurisprudence corruption, articles 432-11..."
                
                search_query = st.text_input(
                    "Recherche",
                    placeholder=placeholder,
                    label_visibility="hidden",
                    key="search_input"
                )
            
            with col2:
                search_button = st.form_submit_button(
                    "🔍 Rechercher",
                    use_container_width=True,
                    type="primary"
                )
        
        # Search suggestions
        if search_query:
            suggestions = generate_search_suggestions(search_query)
            if suggestions:
                st.caption("💡 Suggestions:")
                cols = st.columns(min(len(suggestions), 5))
                for idx, suggestion in enumerate(suggestions[:5]):
                    with cols[idx]:
                        if st.button(suggestion, key=f"sugg_{idx}", use_container_width=True):
                            st.session_state.pending_search = search_query + " " + suggestion
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Perform search
        if search_button and search_query:
            perform_search_optimized(search_query, search_mode)

def generate_search_suggestions(query: str) -> List[str]:
    """Génère des suggestions intelligentes basées sur la requête"""
    suggestions = []
    
    if not query:
        return suggestions
    
    # Analyze query
    query_lower = query.lower()
    
    # Legal terms suggestions
    if any(term in query_lower for term in ["corruption", "abus", "fraude"]):
        suggestions.extend(["articles de loi", "jurisprudence", "sanctions"])
    
    # Document type suggestions
    if "@" in query and not re.search(r'@\w+', query):
        suggestions.extend(["@VINCI2024", "@SOGEPROM", "@ABS001"])
    
    # Party suggestions
    if "contre" in query_lower or "vs" in query_lower:
        suggestions.extend(["parties civiles", "prévenus", "témoins"])
    
    # Date suggestions
    if any(year in query for year in ["2023", "2024", "2025"]):
        suggestions.extend(["janvier-mars", "avril-juin", "juillet-septembre"])
    
    return suggestions

def perform_search_optimized(query: str, mode: str):
    """Effectue une recherche optimisée selon le mode"""
    with st.spinner(f"🔍 Recherche en cours..."):
        if st.session_state.get('azure_search_manager') and hasattr(st.session_state.azure_search_manager, 'search_client'):
            try:
                # Azure Search
                results = st.session_state.azure_search_manager.search(
                    query=query,
                    top=50,
                    use_semantic_search=(mode != "Simple")
                )
                
                if results.get("total_count", 0) > 0:
                    display_search_results(results, query)
                else:
                    st.warning("Aucun document trouvé")
                    display_search_help()
                    
            except Exception as e:
                st.error(f"Erreur de recherche: {str(e)}")
        else:
            st.warning("⚠️ Recherche hors ligne - Azure non connecté")
            # Fallback to local search
            display_demo_results(query)

def display_search_results(results: Dict, query: str):
    """Affiche les résultats de recherche de manière optimisée"""
    # Results header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### 📊 {results['total_count']:,} résultats trouvés")
    
    with col2:
        # Sort options
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Date", "Type", "Source"],
            key="sort_results"
        )
    
    with col3:
        # View options
        view_mode = st.radio(
            "Affichage",
            ["Cartes", "Liste", "Compact"],
            horizontal=True,
            key="view_mode"
        )
    
    # Results grid/list
    if view_mode == "Cartes":
        # Card view with 2 columns
        col1, col2 = st.columns(2)
        
        for idx, doc in enumerate(results.get("results", [])[:20]):
            with col1 if idx % 2 == 0 else col2:
                display_result_card(doc, idx)
    
    elif view_mode == "Liste":
        # List view
        for idx, doc in enumerate(results.get("results", [])[:20]):
            display_result_list_item(doc, idx)
    
    else:
        # Compact view
        for idx, doc in enumerate(results.get("results", [])[:30]):
            display_result_compact(doc, idx)

def display_result_card(doc, idx: int):
    """Affiche un résultat sous forme de carte moderne"""
    with st.container():
        st.markdown('<div class="result-card-modern">', unsafe_allow_html=True)
        
        # Title and score
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"#### {doc.title}")
        with col2:
            if hasattr(doc, 'score'):
                score_color = "#4caf50" if doc.score > 15 else "#ff9800" if doc.score > 10 else "#f44336"
                st.markdown(f'<span style="color: {score_color}; font-weight: bold;">⭐ {doc.score:.1f}</span>', unsafe_allow_html=True)
        
        # Metadata badges
        metadata_html = f"""
        <div style="margin: 10px 0;">
            <span class="status-badge connected" style="margin-right: 8px;">📄 {doc.source}</span>
            <span class="status-badge warning" style="margin-right: 8px;">🏷️ {doc.metadata.get('type', 'Document')}</span>
            <span class="status-badge connected">📅 {doc.metadata.get('date', 'N/A')}</span>
        </div>
        """
        st.markdown(metadata_html, unsafe_allow_html=True)
        
        # Content preview with highlights
        if hasattr(doc, 'highlights') and doc.highlights:
            st.markdown("**Extraits pertinents:**")
            for highlight in doc.highlights[:2]:
                st.markdown(f"> *{highlight}*")
        else:
            content_preview = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            st.text(content_preview)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👁️ Voir", key=f"view_{idx}", use_container_width=True):
                st.session_state.selected_document = doc
                st.session_state.show_document_modal = True
        
        with col2:
            if st.button("📎 Sélectionner", key=f"select_{idx}", use_container_width=True):
                if 'selected_documents' not in st.session_state:
                    st.session_state.selected_documents = []
                st.session_state.selected_documents.append(doc)
                st.success("Document sélectionné")
        
        with col3:
            if st.button("🔗 Plus", key=f"more_{idx}", use_container_width=True):
                st.session_state.show_document_actions = idx
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_result_list_item(doc, idx: int):
    """Affiche un résultat en mode liste"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{idx+1}. {doc.title}**")
            st.caption(f"{doc.content[:100]}...")
        
        with col2:
            st.caption(f"📄 {doc.source}")
            st.caption(f"🏷️ {doc.metadata.get('type', 'N/A')}")
        
        with col3:
            if hasattr(doc, 'score'):
                st.metric("Score", f"{doc.score:.1f}", label_visibility="collapsed")
        
        with col4:
            if st.button("Actions", key=f"actions_{idx}"):
                st.session_state.show_document_actions = idx
        
        st.markdown("---")

def display_result_compact(doc, idx: int):
    """Affiche un résultat en mode compact"""
    cols = st.columns([4, 1])
    
    with cols[0]:
        st.write(f"**{idx+1}.** {doc.title[:80]}... - *{doc.source}*")
    
    with cols[1]:
        if st.button("→", key=f"open_{idx}", help="Ouvrir"):
            st.session_state.selected_document = doc

def display_search_help():
    """Affiche l'aide contextuelle pour la recherche"""
    with st.expander("💡 Conseils de recherche", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Syntaxe de recherche:**
            - `@REF` : Rechercher par référence
            - `type:plainte` : Filtrer par type
            - `partie:nom` : Rechercher une partie
            - `date:2024` : Documents de 2024
            - `"phrase exacte"` : Recherche exacte
            """)
        
        with col2:
            st.markdown("""
            **Exemples:**
            - `corruption @VINCI2024`
            - `type:conclusions partie:SOGEPROM`
            - `abus de biens sociaux date:2024`
            - `jurisprudence article 432-11`
            - `préjudice "dommages et intérêts"`
            """)

def display_demo_results(query: str):
    """Affiche des résultats de démonstration"""
    st.info("📌 Mode démonstration - Résultats simulés")
    
    demo_results = [
        {
            "title": f"Conclusions en réponse - Affaire {query.upper()}",
            "content": "Document juridique contenant une analyse approfondie des faits...",
            "source": "Dossier principal",
            "type": "Conclusions",
            "date": "2024-03-15"
        },
        {
            "title": f"Plainte avec constitution de partie civile",
            "content": "Plainte détaillée concernant les infractions relevées...",
            "source": "Pièces adverses", 
            "type": "Plainte",
            "date": "2024-02-20"
        }
    ]
    
    for idx, result in enumerate(demo_results):
        with st.container():
            st.markdown(f"### {idx+1}. {result['title']}")
            st.caption(f"📄 {result['source']} | 🏷️ {result['type']} | 📅 {result['date']}")
            st.text(result['content'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.button("👁️ Voir le document", key=f"demo_view_{idx}", use_container_width=True)
            with col2:
                st.button("📥 Télécharger", key=f"demo_dl_{idx}", use_container_width=True)

# ========== SECTION 5: INTERFACES PAR ONGLET ==========

def show_tab_content():
    """Affiche le contenu selon l'onglet actif"""
    current_tab = st.session_state.get('current_tab', 'recherche')
    
    if current_tab == 'recherche':
        show_search_interface()
        
    elif current_tab == 'redaction':
        show_redaction_interface()
        
    elif current_tab == 'analyse':
        show_analyse_interface()
        
    elif current_tab == 'pieces':
        show_pieces_interface()
        
    elif current_tab == 'timeline':
        show_timeline_interface()
        
    elif current_tab == 'bordereau':
        show_bordereau_interface()
        
    elif current_tab == 'jurisprudence':
        show_jurisprudence_interface()
        
    elif current_tab == 'outils':
        show_outils_interface()

def show_redaction_interface():
    """Interface de rédaction de documents"""
    st.markdown("### ✍️ Rédaction de documents juridiques")
    
    # Document type selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        doc_type = st.selectbox(
            "Type de document",
            ["Plainte", "Conclusions", "Assignation", "Courrier", "Note juridique"],
            key="redaction_doc_type"
        )
    
    with col2:
        template = st.selectbox(
            "Modèle",
            ["Vierge", "Modèle standard", "Modèle complexe", "Personnalisé"],
            key="redaction_template"
        )
    
    # Quick actions for redaction
    st.markdown("#### Actions rapides")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Nouveau document", use_container_width=True):
            st.session_state.new_document = True
    
    with col2:
        if st.button("📂 Ouvrir brouillon", use_container_width=True):
            st.session_state.show_drafts = True
    
    with col3:
        if st.button("🤖 Génération IA", use_container_width=True):
            st.session_state.show_ai_generation = True
    
    with col4:
        if st.button("📑 Templates", use_container_width=True):
            st.session_state.show_templates = True
    
    # Main editor area
    if modules and hasattr(modules, 'redaction'):
        try:
            modules.redaction.show_editor()
        except:
            st.info("Éditeur de documents en cours de chargement...")
    else:
        # Fallback editor
        st.text_area(
            "Contenu du document",
            height=400,
            placeholder="Commencez à rédiger votre document ici...",
            key="doc_content"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("💾 Sauvegarder", use_container_width=True)
        with col2:
            st.button("📤 Exporter", use_container_width=True)
        with col3:
            st.button("🖨️ Imprimer", use_container_width=True)

def show_analyse_interface():
    """Interface d'analyse juridique IA"""
    st.markdown("### 📊 Analyse juridique par IA")
    
    # Analysis type selection
    analysis_type = st.radio(
        "Type d'analyse",
        ["Analyse de risques", "Analyse comparative", "Analyse de jurisprudence", "Analyse contractuelle"],
        horizontal=True,
        key="analysis_type"
    )
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-number">15</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Analyses ce mois</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-number">87%</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Précision moyenne</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-number">3.2s</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Temps moyen</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-number">248</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Documents analysés</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis interface
    if modules and hasattr(modules, 'analyse_ia'):
        try:
            modules.analyse_ia.show_analysis_interface()
        except:
            st.info("Module d'analyse en cours de chargement...")
    else:
        # Fallback interface
        st.markdown("#### Configuration de l'analyse")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.multiselect(
                "Documents à analyser",
                ["Document 1", "Document 2", "Document 3"],
                key="docs_to_analyze"
            )
            
            st.slider(
                "Niveau de détail",
                min_value=1,
                max_value=5,
                value=3,
                key="analysis_detail"
            )
        
        with col2:
            st.multiselect(
                "Points d'attention",
                ["Risques juridiques", "Opportunités", "Points faibles", "Recommandations"],
                default=["Risques juridiques", "Recommandations"],
                key="analysis_focus"
            )
            
            if st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True):
                with st.spinner("Analyse en cours..."):
                    st.success("Analyse terminée !")

def show_pieces_interface():
    """Interface de gestion des pièces"""
    st.markdown("### 📎 Gestion des pièces")
    
    if modules and hasattr(modules, 'pieces_manager'):
        try:
            modules.pieces_manager.display_pieces_manager()
        except:
            st.info("Gestionnaire de pièces en cours de chargement...")
    else:
        st.info("Module de gestion des pièces non disponible")

def show_timeline_interface():
    """Interface de timeline"""
    st.markdown("### 📅 Chronologie des événements")
    
    if modules and hasattr(modules, 'timeline'):
        try:
            modules.timeline.display_timeline()
        except:
            st.info("Timeline en cours de chargement...")
    else:
        st.info("Module timeline non disponible")

def show_bordereau_interface():
    """Interface de génération de bordereaux"""
    st.markdown("### 📋 Génération de bordereaux")
    
    if modules and hasattr(modules, 'bordereau'):
        try:
            modules.bordereau.creer_bordereau()
        except:
            st.info("Module bordereau en cours de chargement...")
    else:
        st.info("Module bordereau non disponible")

def show_jurisprudence_interface():
    """Interface de recherche de jurisprudence"""
    st.markdown("### ⚖️ Base de jurisprudence")
    
    if modules and hasattr(modules, 'jurisprudence'):
        try:
            modules.jurisprudence.show_jurisprudence_search()
        except:
            st.info("Base de jurisprudence en cours de chargement...")
    else:
        st.info("Module jurisprudence non disponible")

def show_outils_interface():
    """Interface des outils avancés"""
    st.markdown("### 🛠️ Outils avancés")
    
    # Tool categories - AJOUT de "Test Imports" dans la liste
    tool_category = st.selectbox(
        "Catégorie d'outils",
        ["Import/Export", "Configuration", "Maintenance", "Développement", "Test Imports"],
        key="tool_category"
    )
    
    if tool_category == "Import/Export":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Import")
            if st.button("📥 Importer des documents", use_container_width=True):
                st.session_state.show_import = True
            if st.button("📊 Importer Excel/CSV", use_container_width=True):
                st.session_state.show_data_import = True
        
        with col2:
            st.markdown("#### Export")
            if st.button("📤 Exporter la sélection", use_container_width=True):
                st.session_state.show_export = True
            if st.button("📑 Générer rapport", use_container_width=True):
                st.session_state.show_report = True
    
    elif tool_category == "Configuration":
        show_configuration_interface()
    
    elif tool_category == "Maintenance":
        show_maintenance_interface()
    
    elif tool_category == "Développement":
        show_development_interface()
    
    elif tool_category == "Test Imports":
        st.markdown("### 🧪 Test rapide des imports")
        
        if modules:
            loaded = modules.get_loaded_modules()
            st.success(f"✅ {len(loaded)} modules chargés")
            
            # Test truncate_text
            try:
                from utils.helpers import truncate_text
                st.success("✅ truncate_text disponible")
            except:
                st.error("❌ truncate_text manquant")
                
            # Test des classes dataclasses
            st.markdown("#### Test des classes dataclasses")
            classes_to_test = [
                ('EmailConfig', 'models.dataclasses'),
                ('Relationship', 'models.dataclasses'),
                ('PlaidoirieResult', 'models.dataclasses'),
                ('PreparationClientResult', 'models.dataclasses')
            ]
            
            col1, col2 = st.columns(2)
            for i, (class_name, module_path) in enumerate(classes_to_test):
                with col1 if i % 2 == 0 else col2:
                    try:
                        exec(f"from {module_path} import {class_name}")
                        st.success(f"✅ {class_name}")
                    except ImportError:
                        st.error(f"❌ {class_name}")
                        
            # Afficher les modules avec erreurs
            if st.checkbox("Voir les détails des modules"):
                modules.create_streamlit_debug_page()
                
        else:
            st.error("❌ Système de modules non chargé")

def show_configuration_interface():
    """Interface de configuration"""
    st.markdown("#### ⚙️ Configuration")
    
    tabs = st.tabs(["🔑 API", "🌐 Azure", "🎨 Interface", "📧 Notifications"])
    
    with tabs[0]:
        st.text_input("Claude API Key", type="password", key="config_claude_key")
        st.text_input("OpenAI API Key", type="password", key="config_openai_key")
        st.text_input("Google API Key", type="password", key="config_google_key")
    
    with tabs[1]:
        st.text_input("Azure Storage Connection", type="password", key="config_azure_storage")
        st.text_input("Azure Search Endpoint", key="config_azure_endpoint")
        st.text_input("Azure Search Key", type="password", key="config_azure_key")
    
    with tabs[2]:
        st.selectbox("Thème", ["Clair", "Sombre", "Auto"], key="config_theme")
        st.slider("Taille de police", 12, 20, 16, key="config_font_size")
        st.checkbox("Animations", value=True, key="config_animations")
    
    with tabs[3]:
        st.checkbox("Notifications email", key="config_email_notif")
        st.checkbox("Notifications push", key="config_push_notif")
        st.text_input("Email de notification", key="config_notif_email")

def show_maintenance_interface():
    """Interface de maintenance"""
    st.markdown("#### 🔧 Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Réinitialiser Azure", use_container_width=True):
            reinit_azure()
        
        if st.button("🧹 Nettoyer le cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache nettoyé")
        
        if st.button("📊 Optimiser la base", use_container_width=True):
            st.info("Optimisation en cours...")
    
    with col2:
        if st.button("🔍 Vérifier l'intégrité", use_container_width=True):
            st.info("Vérification en cours...")
        
        if st.button("💾 Sauvegarder", use_container_width=True):
            st.info("Sauvegarde en cours...")
        
        if st.button("📈 Statistiques système", use_container_width=True):
            st.session_state.show_system_stats = True

def show_development_interface():
    """Interface de développement"""
    st.markdown("#### 💻 Outils de développement")
    
    if modules:
        # Module debug
        if st.checkbox("🔍 Debug des modules"):
            modules.create_streamlit_debug_page()
        
        # Session state viewer
        if st.checkbox("📊 Voir session state"):
            st.json({k: str(v)[:100] + "..." if len(str(v)) > 100 else str(v) 
                    for k, v in st.session_state.items()})
        
        # API tester
        if st.checkbox("🧪 Testeur d'API"):
            api_choice = st.selectbox("API à tester", ["Azure Blob", "Azure Search", "Claude", "OpenAI"])
            if st.button("Tester", key="test_api"):
                with st.spinner("Test en cours..."):
                    st.info(f"Test de {api_choice}...")

# ========== SECTION 6: FONCTION PRINCIPALE ==========

def main():
    """Fonction principale avec interface optimisée"""
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    init_azure_managers()
    
    # Version badge (floating)
    version_type = "Unifiée" if st.session_state.get('use_simplified_version', True) else "Classique"
    st.markdown(f'<div class="version-badge">v{app_config.version} - {version_type}</div>', unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header moderne
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ Assistant Pénal des Affaires IA</h1>
        <p>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status bar
    show_status_bar()
    
    # Navigation bar
    show_navigation_bar()
    
    # Quick actions (contextual)
    with st.expander("⚡ Actions rapides", expanded=False):
        show_quick_actions()
    
    # Main content area
    show_tab_content()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== MODALS & OVERLAYS ==========
    
    # Settings modal
    if st.session_state.get('show_settings'):
        with st.container():
            st.markdown("---")
            st.markdown("### ⚙️ Paramètres")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                settings_tab = st.selectbox(
                    "Section",
                    ["Général", "Interface", "Azure", "API", "Avancé"],
                    key="settings_section"
                )
            
            with col2:
                if st.button("❌ Fermer", key="close_settings"):
                    st.session_state.show_settings = False
                    st.rerun()
            
            if settings_tab == "Interface":
                # Interface toggle
                use_classic = st.toggle(
                    "Utiliser l'interface classique",
                    value=not st.session_state.get('use_simplified_version', True),
                    help="Basculer entre l'interface unifiée et classique"
                )
                st.session_state.use_simplified_version = not use_classic
                
                if st.button("Appliquer et recharger"):
                    st.rerun()
    
    # Document modal
    if st.session_state.get('show_document_modal') and st.session_state.get('selected_document'):
        show_document_modal_optimized()
    
    # Import modal
    if st.session_state.get('show_import_modal'):
        show_import_modal()
    
    # Footer minimal
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(f"© 2024 Assistant Pénal IA - Dernière mise à jour : {datetime.now().strftime('%H:%M')}")

def show_document_modal_optimized():
    """Modal optimisé pour l'affichage des documents"""
    doc = st.session_state.selected_document
    
    with st.container():
        st.markdown("---")
        
        # Modal header
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"## 📄 {doc.title}")
        
        with col2:
            if st.button("❌", key="close_doc_modal"):
                st.session_state.show_document_modal = False
                st.session_state.selected_document = None
                st.rerun()
        
        # Document info
        info_cols = st.columns(4)
        with info_cols[0]:
            st.metric("Source", doc.source)
        with info_cols[1]:
            st.metric("Type", doc.metadata.get('type', 'Document'))
        with info_cols[2]:
            st.metric("Date", doc.metadata.get('date', 'N/A'))
        with info_cols[3]:
            if hasattr(doc, 'score'):
                st.metric("Score", f"{doc.score:.1f}")
        
        # Document content
        st.markdown("### Contenu")
        
        # Display with syntax highlighting if applicable
        if doc.metadata.get('type') == 'Code':
            st.code(doc.content, language='python')
        else:
            # Regular text with highlights
            content = doc.content
            if hasattr(doc, 'highlights') and doc.highlights:
                for highlight in doc.highlights:
                    content = content.replace(
                        highlight,
                        f'<mark style="background-color: #ffd93d;">{highlight}</mark>'
                    )
            st.markdown(content, unsafe_allow_html=True)
        
        # Actions
        st.markdown("### Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Télécharger", use_container_width=True):
                st.info("Téléchargement...")
        
        with col2:
            if st.button("📧 Envoyer", use_container_width=True):
                st.info("Envoi par email...")
        
        with col3:
            if st.button("🖨️ Imprimer", use_container_width=True):
                st.info("Impression...")
        
        with col4:
            if st.button("📎 Ajouter aux pièces", use_container_width=True):
                if 'pieces_selectionnees' not in st.session_state:
                    st.session_state.pieces_selectionnees = {}
                st.session_state.pieces_selectionnees[doc.id] = doc
                st.success("Ajouté aux pièces")

def show_import_modal():
    """Modal d'import de documents"""
    with st.container():
        st.markdown("---")
        st.markdown("### 📥 Importer des documents")
        
        # Import method
        import_method = st.radio(
            "Méthode d'import",
            ["Fichiers locaux", "Azure Blob", "URL", "Texte direct"],
            horizontal=True,
            key="import_method"
        )
        
        if import_method == "Fichiers locaux":
            uploaded_files = st.file_uploader(
                "Sélectionner des fichiers",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt', 'xlsx', 'csv'],
                key="file_uploader"
            )
            
            if uploaded_files:
                st.success(f"{len(uploaded_files)} fichiers sélectionnés")
                
                if st.button("📤 Importer", type="primary"):
                    with st.spinner("Import en cours..."):
                        st.success("Import terminé !")
        
        elif import_method == "Azure Blob":
            if st.session_state.get('azure_blob_manager'):
                st.info("Connexion à Azure Blob Storage...")
            else:
                st.warning("Azure Blob non configuré")
        
        if st.button("❌ Fermer", key="close_import"):
            st.session_state.show_import_modal = False
            st.rerun()

# Point d'entrée
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ Erreur critique")
        st.code(str(e))
        with st.expander("Détails complets"):
            st.code(traceback.format_exc())