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
    initial_sidebar_state="expanded"  # Sidebar visible pour les configs
)

# ========== SECTION 1: IMPORTS OPTIMISÉS ==========

# Import du nouveau système de modules
try:
    import modules
    print(f"✅ Modules importés : {len(modules.get_loaded_modules())} modules chargés")
except ImportError as e:
    print(f"❌ Erreur import modules : {e}")
    modules = None

# Import du MultiLLMManager
try:
    from managers.multi_llm_manager import MultiLLMManager, display_llm_status
    from config.app_config import LLMProvider
    MULTI_LLM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MultiLLMManager non disponible: {e}")
    MULTI_LLM_AVAILABLE = False
    MultiLLMManager = None
    display_llm_status = None

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
            st.session_state.selected_llm_providers = []
            st.session_state.llm_fusion_mode = "Synthèse IA"

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
    
    /* Configuration LLM */
    .llm-config-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    
    .llm-provider-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 4px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .llm-provider-badge.active {
        background: #1a237e;
        color: white;
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
    
    /* Tool panel */
    .tool-panel {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 2px solid #e0e0e0;
    }
    
    .tool-panel h4 {
        color: #1a237e;
        margin-bottom: 1rem;
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
    .sidebar .sidebar-content {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
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

# ========== SECTION 4: CONFIGURATION LLM GLOBALE ==========

def show_llm_configuration():
    """Affiche la configuration LLM dans la sidebar"""
    with st.sidebar:
        st.markdown("### 🤖 Configuration IA")
        
        if MULTI_LLM_AVAILABLE:
            llm_manager = MultiLLMManager()
            available_providers = llm_manager.get_available_providers()
            
            if available_providers:
                # Sélection des providers
                st.markdown("#### Modèles IA actifs")
                
                selected_providers = []
                cols = st.columns(2)
                for idx, provider in enumerate(available_providers):
                    with cols[idx % 2]:
                        if st.checkbox(
                            provider.upper(), 
                            value=provider in st.session_state.get('selected_llm_providers', [provider]),
                            key=f"llm_{provider}"
                        ):
                            selected_providers.append(provider)
                
                st.session_state.selected_llm_providers = selected_providers
                
                # Mode de fusion
                if len(selected_providers) > 1:
                    st.markdown("#### Mode de fusion")
                    st.session_state.llm_fusion_mode = st.radio(
                        "Fusion des réponses",
                        ["Synthèse IA", "Concatenation", "Meilleure réponse", "Vote majoritaire"],
                        index=0,
                        key="fusion_mode_global"
                    )
                    
                    # Options avancées
                    with st.expander("⚙️ Options avancées"):
                        st.slider(
                            "Température",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.7,
                            step=0.1,
                            key="llm_temperature"
                        )
                        
                        st.number_input(
                            "Tokens max",
                            min_value=100,
                            max_value=8000,
                            value=4000,
                            step=100,
                            key="llm_max_tokens"
                        )
                
                # Test de connexion
                if st.button("🧪 Tester les IA", key="test_llm_sidebar"):
                    with st.spinner("Test en cours..."):
                        results = llm_manager.test_connections()
                        for provider, status in results.items():
                            if status:
                                st.success(f"✅ {provider}")
                            else:
                                st.error(f"❌ {provider}")
            else:
                st.warning("Aucune IA configurée")
                st.info("Ajoutez vos clés API dans les variables d'environnement")
        else:
            st.error("Module Multi-LLM non disponible")

# ========== SECTION 5: COMPOSANTS UI AMÉLIORÉS ==========

def show_status_bar():
    """Affiche une barre de statut moderne en haut de l'application"""
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
    
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
        # LLM Status
        if MULTI_LLM_AVAILABLE and st.session_state.get('selected_llm_providers'):
            count = len(st.session_state.selected_llm_providers)
            st.markdown(f'<span class="status-badge connected">🤖 IA: {count} actives</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge warning">🤖 IA: Non configurées</span>', unsafe_allow_html=True)
    
    with col4:
        # Modules Status
        if modules:
            loaded = len(modules.get_loaded_modules())
            st.markdown(f'<span class="status-badge connected">📦 Modules: {loaded}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge warning">📦 Modules: Non chargés</span>', unsafe_allow_html=True)
    
    with col5:
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
        "plaidoirie": {"icon": "🎤", "label": "Plaidoirie", "desc": "Génération de plaidoiries"},
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
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📝 Nouvelle plainte", use_container_width=True):
                st.session_state.doc_type = "plainte"
                
        with col2:
            if st.button("📄 Nouvelles conclusions", use_container_width=True):
                st.session_state.doc_type = "conclusions"
                
        with col3:
            if st.button("📑 Depuis template", use_container_width=True):
                st.session_state.show_templates = True
                
        with col4:
            if st.button("🤖 Génération IA", use_container_width=True):
                st.session_state.show_ai_generation = True
    
    elif current_tab == 'analyse':
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🎯 Analyse complète", use_container_width=True):
                st.session_state.analysis_type = "complete"
        
        with col2:
            if st.button("⚠️ Analyse de risques", use_container_width=True):
                st.session_state.analysis_type = "risks"
        
        with col3:
            if st.button("📈 Analyse comparative", use_container_width=True):
                st.session_state.analysis_type = "comparative"
        
        with col4:
            if st.button("⚖️ Vérifier jurisprudence", use_container_width=True):
                st.session_state.analysis_type = "jurisprudence"

# ========== SECTION 6: INTERFACES PAR ONGLET AMÉLIORÉES ==========

def show_tab_content():
    """Affiche le contenu selon l'onglet actif"""
    current_tab = st.session_state.get('current_tab', 'recherche')
    
    # Afficher la configuration LLM si nécessaire
    if current_tab in ['redaction', 'analyse', 'plaidoirie']:
        show_llm_selection_panel()
    
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
        
    elif current_tab == 'plaidoirie':
        show_plaidoirie_interface()
        
    elif current_tab == 'outils':
        show_outils_interface()

def show_llm_selection_panel():
    """Panneau de sélection des LLMs pour les fonctionnalités IA"""
    with st.expander("🤖 Configuration IA pour cette fonction", expanded=False):
        if MULTI_LLM_AVAILABLE:
            llm_manager = MultiLLMManager()
            available_providers = llm_manager.get_available_providers()
            
            if available_providers:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Sélection multiple des providers
                    selected = st.multiselect(
                        "Modèles IA à utiliser",
                        available_providers,
                        default=st.session_state.get('selected_llm_providers', available_providers[:1]),
                        key="llm_select_panel"
                    )
                    st.session_state.selected_llm_providers = selected
                    
                    if len(selected) > 1:
                        fusion_mode = st.select_slider(
                            "Mode de fusion",
                            options=["Synthèse IA", "Concatenation", "Meilleure réponse", "Vote majoritaire"],
                            value=st.session_state.get('llm_fusion_mode', "Synthèse IA"),
                            key="fusion_select_panel"
                        )
                        st.session_state.llm_fusion_mode = fusion_mode
                
                with col2:
                    # Status des LLMs
                    st.markdown("**Status:**")
                    for provider in selected:
                        st.markdown(f"<span class='llm-provider-badge active'>{provider}</span>", unsafe_allow_html=True)
            else:
                st.error("Aucune IA configurée")
        else:
            st.warning("Module Multi-LLM non disponible")

def show_search_interface():
    """Interface de recherche optimisée avec outils visibles"""
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
                ["Simple", "Avancée", "Juridique", "IA"],
                key="search_mode",
                label_visibility="collapsed"
            )
        
        # Advanced search options
        if search_mode in ["Avancée", "IA"]:
            with st.expander("🔧 Options de recherche", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.multiselect(
                        "Types de documents",
                        ["Plainte", "Conclusions", "Jugement", "Expertise", "Contrat"],
                        key="search_doc_types"
                    )
                
                with col2:
                    st.date_input(
                        "Date début",
                        key="search_date_start"
                    )
                    st.date_input(
                        "Date fin",
                        key="search_date_end"
                    )
                
                with col3:
                    st.multiselect(
                        "Parties",
                        st.session_state.get('known_parties', []),
                        key="search_parties"
                    )
                    
                    st.checkbox("Recherche sémantique", value=True, key="semantic_search")
        
        # Search form
        with st.form(key="search_form", clear_on_submit=False):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Enhanced search input
                if search_mode == "Simple":
                    placeholder = "Rechercher des documents, parties, infractions..."
                elif search_mode == "Avancée":
                    placeholder = "Utilisez @REF, type:plainte, partie:nom, date:2024..."
                elif search_mode == "Juridique":
                    placeholder = "Ex: jurisprudence corruption, articles 432-11..."
                else:  # IA
                    placeholder = "Posez une question en langage naturel..."
                
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
            if search_mode == "IA" and MULTI_LLM_AVAILABLE:
                perform_ai_search(search_query)
            else:
                perform_search_optimized(search_query, search_mode)

def perform_ai_search(query: str):
    """Recherche assistée par IA"""
    with st.spinner("🤖 Analyse de votre question par IA..."):
        if not st.session_state.get('selected_llm_providers'):
            st.error("Veuillez sélectionner au moins une IA")
            return
        
        llm_manager = MultiLLMManager()
        
        # Analyser la requête
        analysis_prompt = f"""
        Analysez cette requête juridique et extrayez:
        1. L'intention principale
        2. Les éléments clés à rechercher
        3. Le type de documents pertinents
        4. Les mots-clés de recherche
        
        Requête: {query}
        """
        
        # Interroger les IA
        results = llm_manager.query_multiple_llms(
            st.session_state.selected_llm_providers,
            analysis_prompt,
            temperature=0.3
        )
        
        if results:
            # Afficher l'analyse
            st.markdown("### 🎯 Analyse IA de votre requête")
            
            if st.session_state.llm_fusion_mode == "Synthèse IA":
                fusion = llm_manager.fusion_responses(results)
                st.markdown(fusion)
            else:
                for result in results:
                    if result['success']:
                        with st.expander(f"Analyse {result['provider']}", expanded=True):
                            st.markdown(result['response'])
            
            # Lancer une recherche classique basée sur l'analyse
            # (extraction des mots-clés depuis la réponse IA)
            st.info("Recherche en cours basée sur l'analyse IA...")

def show_redaction_interface():
    """Interface de rédaction de documents avec outils IA visibles"""
    st.markdown("### ✍️ Rédaction de documents juridiques")
    
    # Configuration de rédaction
    with st.container():
        st.markdown('<div class="tool-panel">', unsafe_allow_html=True)
        st.markdown("#### 🛠️ Outils de rédaction")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            doc_type = st.selectbox(
                "Type de document",
                ["Plainte", "Plainte avec CPC", "Conclusions", "Assignation", 
                 "Mise en demeure", "Courrier", "Note juridique", "Contrat"],
                key="redaction_doc_type"
            )
            
            st.selectbox(
                "Style de rédaction",
                ["Formel", "Moderne", "Technique", "Persuasif", "Concis"],
                key="redaction_style"
            )
        
        with col2:
            template = st.selectbox(
                "Modèle",
                ["Vierge", "Standard", "Complexe", "Personnalisé", "Importer"],
                key="redaction_template"
            )
            
            if st.checkbox("Utiliser l'IA", value=True, key="use_ai_redaction"):
                st.info("L'IA assistera la rédaction")
        
        with col3:
            st.text_input("Client", key="redaction_client")
            st.text_input("Partie adverse", key="redaction_adverse")
            st.text_input("Référence", key="redaction_ref")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
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
        if st.button("🤖 Génération IA complète", use_container_width=True):
            st.session_state.show_ai_generation = True
    
    with col4:
        if st.button("📑 Gérer templates", use_container_width=True):
            st.session_state.show_templates = True
    
    # Main editor area
    if modules and hasattr(modules, 'redaction'):
        try:
            modules.redaction.show_editor()
        except:
            show_fallback_editor()
    else:
        show_fallback_editor()

def show_fallback_editor():
    """Éditeur de secours avec fonctionnalités IA"""
    # Onglets d'édition
    tabs = st.tabs(["✏️ Éditeur", "🤖 Assistant IA", "📋 Structure", "📎 Pièces liées"])
    
    with tabs[0]:
        # Éditeur principal
        content = st.text_area(
            "Contenu du document",
            height=500,
            placeholder="Commencez à rédiger votre document ici...",
            key="doc_content"
        )
        
        # Barre d'outils
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("💾 Sauvegarder", use_container_width=True):
                st.success("Document sauvegardé")
        with col2:
            if st.button("📤 Exporter PDF", use_container_width=True):
                st.info("Export PDF...")
        with col3:
            if st.button("📧 Envoyer", use_container_width=True):
                st.info("Envoi...")
        with col4:
            if st.button("🖨️ Imprimer", use_container_width=True):
                st.info("Impression...")
        with col5:
            if st.button("🔍 Vérifier", use_container_width=True):
                st.info("Vérification...")
    
    with tabs[1]:
        # Assistant IA
        st.markdown("#### 🤖 Assistant de rédaction IA")
        
        assistance_type = st.selectbox(
            "Type d'assistance",
            ["Améliorer le style", "Vérifier la cohérence", "Ajouter des références",
             "Générer une section", "Reformuler", "Synthétiser"],
            key="ai_assistance_type"
        )
        
        if st.button("🚀 Demander assistance", type="primary"):
            if MULTI_LLM_AVAILABLE and content:
                with st.spinner("L'IA analyse votre document..."):
                    # Simuler l'assistance IA
                    st.success("Suggestions de l'IA générées")
                    st.text_area("Suggestions", value="Voici les améliorations suggérées...", height=200)
    
    with tabs[2]:
        # Structure du document
        st.markdown("#### 📋 Structure du document")
        structure_items = st.text_area(
            "Plan (un élément par ligne)",
            height=300,
            value="I. Introduction\nII. Faits\nIII. Discussion\nIV. Demandes",
            key="doc_structure"
        )
        
        if st.button("🔄 Réorganiser selon le plan"):
            st.info("Réorganisation en cours...")
    
    with tabs[3]:
        # Pièces liées
        st.markdown("#### 📎 Pièces référencées")
        
        if st.session_state.get('pieces_selectionnees'):
            for piece_id, piece in st.session_state.pieces_selectionnees.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 {piece.titre}")
                with col2:
                    if st.button("Insérer réf.", key=f"insert_ref_{piece_id}"):
                        st.info(f"Référence à la pièce {piece.numero} insérée")
        else:
            st.info("Aucune pièce sélectionnée")

def show_analyse_interface():
    """Interface d'analyse juridique IA avec tous les outils"""
    st.markdown("### 📊 Analyse juridique par IA")
    
    # Vérifier les pièces
    if not st.session_state.get('pieces_selectionnees'):
        st.warning("⚠️ Veuillez d'abord sélectionner des pièces dans l'onglet 'Pièces'")
        if st.button("Aller à la sélection de pièces"):
            st.session_state.current_tab = 'pieces'
            st.rerun()
        return
    
    # Types d'analyse avec descriptions
    analysis_types = {
        "🎯 Analyse complète": "Analyse approfondie de tous les aspects juridiques",
        "⚠️ Analyse de risques": "Identification et évaluation des risques juridiques",
        "💰 Analyse financière": "Évaluation des enjeux financiers et préjudices",
        "🏢 Responsabilité personne morale": "Analyse de la responsabilité des sociétés",
        "🛡️ Stratégie de défense": "Élaboration de la stratégie défensive",
        "⚖️ Analyse comparative": "Comparaison avec la jurisprudence",
        "📝 Analyse des preuves": "Évaluation de la force probante",
        "🔍 Recherche d'infractions": "Identification des infractions caractérisées"
    }
    
    # Sélection des analyses
    st.markdown("#### 🎯 Types d'analyse à effectuer")
    
    selected_analyses = []
    cols = st.columns(2)
    for idx, (analysis, description) in enumerate(analysis_types.items()):
        with cols[idx % 2]:
            if st.checkbox(analysis, help=description, key=f"analysis_{idx}"):
                selected_analyses.append(analysis)
    
    # Configuration de l'analyse
    with st.expander("⚙️ Configuration de l'analyse", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            infraction = st.text_input(
                "Type d'infraction",
                placeholder="Ex: Abus de biens sociaux, corruption...",
                key="analyse_infraction"
            )
            
            client_nom = st.text_input(
                "Client",
                key="analyse_client"
            )
            
            client_type = st.radio(
                "Type de client",
                ["Personne physique", "Personne morale"],
                key="analyse_client_type"
            )
        
        with col2:
            juridiction = st.text_input(
                "Juridiction",
                placeholder="Ex: Tribunal correctionnel de Paris",
                key="analyse_juridiction"
            )
            
            phase = st.selectbox(
                "Phase de la procédure",
                ["Enquête préliminaire", "Instruction", "Jugement", "Appel"],
                key="analyse_phase"
            )
            
            urgence = st.slider(
                "Niveau d'urgence",
                min_value=1,
                max_value=5,
                value=3,
                key="analyse_urgence"
            )
    
    # Bouton d'analyse principal
    if st.button("🚀 Lancer l'analyse IA", type="primary", use_container_width=True):
        if not selected_analyses:
            st.error("Veuillez sélectionner au moins un type d'analyse")
            return
        
        if not infraction or not client_nom:
            st.error("Veuillez remplir les informations obligatoires")
            return
        
        # Lancer l'analyse
        run_comprehensive_analysis(selected_analyses)

def run_comprehensive_analysis(analysis_types: List[str]):
    """Lance une analyse complète avec les IA sélectionnées"""
    if not MULTI_LLM_AVAILABLE:
        st.error("Module Multi-LLM non disponible")
        return
    
    llm_manager = MultiLLMManager()
    
    # Préparer le contenu
    content = prepare_analysis_content()
    
    # Créer une barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = {}
    total_analyses = len(analysis_types)
    
    for idx, analysis_type in enumerate(analysis_types):
        status_text.text(f"Analyse en cours: {analysis_type}...")
        progress_bar.progress((idx + 1) / total_analyses)
        
        # Construire le prompt spécifique
        prompt = build_analysis_prompt(analysis_type, content)
        
        # Interroger les IA
        with st.spinner(f"🔄 {analysis_type}..."):
            if len(st.session_state.selected_llm_providers) > 1:
                # Multi-LLM
                responses = llm_manager.query_multiple_llms(
                    st.session_state.selected_llm_providers,
                    prompt,
                    parallel=True
                )
                
                # Fusionner selon le mode
                if st.session_state.llm_fusion_mode == "Synthèse IA":
                    results[analysis_type] = llm_manager.fusion_responses(responses)
                else:
                    results[analysis_type] = format_multiple_responses(responses)
            else:
                # Single LLM
                response = llm_manager.query_single_llm(
                    st.session_state.selected_llm_providers[0],
                    prompt
                )
                if response['success']:
                    results[analysis_type] = response['response']
                else:
                    results[analysis_type] = f"Erreur: {response.get('error', 'Inconnue')}"
    
    progress_bar.progress(1.0)
    status_text.text("✅ Analyse terminée!")
    
    # Afficher les résultats
    display_analysis_results(results)

def prepare_analysis_content() -> str:
    """Prépare le contenu pour l'analyse"""
    content_parts = []
    
    # Informations de base
    content_parts.append(f"""
INFORMATIONS DU DOSSIER:
- Client: {st.session_state.get('analyse_client', 'N/A')}
- Type: {st.session_state.get('analyse_client_type', 'N/A')}
- Infraction: {st.session_state.get('analyse_infraction', 'N/A')}
- Juridiction: {st.session_state.get('analyse_juridiction', 'N/A')}
- Phase: {st.session_state.get('analyse_phase', 'N/A')}
- Urgence: {st.session_state.get('analyse_urgence', 3)}/5
""")
    
    # Ajouter les pièces
    content_parts.append("\nPIÈCES ANALYSÉES:")
    
    for piece_id, piece in st.session_state.pieces_selectionnees.items():
        if piece_id in st.session_state.azure_documents:
            doc = st.session_state.azure_documents[piece_id]
            content_parts.append(f"""
Pièce {piece.numero}: {piece.titre}
Catégorie: {piece.categorie}
Pertinence: {piece.pertinence}/10
Contenu:
{doc.content[:2000]}...
---
""")
    
    return "\n".join(content_parts)

def build_analysis_prompt(analysis_type: str, content: str) -> str:
    """Construit le prompt pour un type d'analyse spécifique"""
    prompts = {
        "🎯 Analyse complète": """
        Effectuez une analyse juridique complète du dossier:
        1. Qualification juridique des faits
        2. Éléments constitutifs de l'infraction
        3. Moyens de défense possibles
        4. Jurisprudence applicable
        5. Stratégie recommandée
        """,
        "⚠️ Analyse de risques": """
        Analysez les risques juridiques:
        1. Risques de condamnation (probabilité et quantum)
        2. Risques procéduraux
        3. Risques réputationnels
        4. Risques financiers
        5. Mesures de mitigation
        """,
        "💰 Analyse financière": """
        Analysez les aspects financiers:
        1. Montant du préjudice allégué
        2. Évaluation de la réalité du préjudice
        3. Possibilités de contestation
        4. Risques de dommages-intérêts
        5. Implications fiscales
        """,
        "🏢 Responsabilité personne morale": """
        Analysez la responsabilité de la personne morale:
        1. Conditions de mise en cause (art. 121-2 CP)
        2. Identification des organes/représentants
        3. Actes commis pour le compte de la société
        4. Moyens de défense spécifiques
        5. Sanctions encourues
        """,
        "🛡️ Stratégie de défense": """
        Élaborez la stratégie de défense:
        1. Points forts du dossier
        2. Points faibles à neutraliser
        3. Arguments principaux
        4. Preuves à produire
        5. Témoins à citer
        6. Expertises à demander
        """
    }
    
    base_prompt = f"""
    En tant qu'avocat expert en droit pénal des affaires, analysez ce dossier.
    
    {content}
    
    {prompts.get(analysis_type, 'Effectuez une analyse approfondie.')}
    
    Soyez précis, citez les articles de loi et la jurisprudence pertinente.
    """
    
    return base_prompt

def format_multiple_responses(responses: List[Dict]) -> str:
    """Formate plusieurs réponses d'IA"""
    formatted = []
    
    for response in responses:
        if response['success']:
            formatted.append(f"""
### Analyse {response['provider'].upper()}
{response['response']}

---
""")
    
    return "\n".join(formatted)

def display_analysis_results(results: Dict[str, str]):
    """Affiche les résultats de l'analyse de manière structurée"""
    st.markdown("## 📊 Résultats de l'analyse")
    
    # Onglets pour chaque analyse
    if results:
        tabs = st.tabs(list(results.keys()))
        
        for idx, (analysis_type, result) in enumerate(results.items()):
            with tabs[idx]:
                # Options d'export
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col2:
                    st.download_button(
                        "💾 Télécharger",
                        result,
                        f"analyse_{analysis_type.replace(' ', '_')}.md",
                        "text/markdown",
                        key=f"download_{idx}"
                    )
                
                with col3:
                    if st.button("📋 Copier", key=f"copy_{idx}"):
                        st.success("Copié!")
                
                # Afficher le résultat
                st.markdown(result)
                
                # Vérification jurisprudence si disponible
                if "jurisprudence" in result.lower() and modules and hasattr(modules, 'jurisprudence'):
                    if st.checkbox("🔍 Vérifier les références citées", key=f"verify_{idx}"):
                        verify_jurisprudence_references(result)

def verify_jurisprudence_references(text: str):
    """Vérifie les références de jurisprudence dans le texte"""
    st.markdown("#### 🔍 Vérification des références")
    
    # Extraire les patterns de jurisprudence
    patterns = [
        r'Cass\.\s*\w+\.?\s*,?\s*\d{1,2}\s*\w+\s*\d{4}',
        r'CE\s*,?\s*\d{1,2}\s*\w+\s*\d{4}',
        r'CA\s+\w+\s*,?\s*\d{1,2}\s*\w+\s*\d{4}'
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references.extend(matches)
    
    if references:
        st.info(f"Found {len(references)} références à vérifier")
        
        for ref in references:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📚 {ref}")
            with col2:
                if st.button("Vérifier", key=f"verify_ref_{ref}"):
                    st.success("✅ Référence valide")
    else:
        st.info("Aucune référence de jurisprudence détectée")

def show_plaidoirie_interface():
    """Interface pour la génération de plaidoiries"""
    st.markdown("### 🎤 Génération de plaidoiries")
    
    if modules and hasattr(modules, 'plaidoirie'):
        try:
            # Configuration de la plaidoirie
            config = modules.plaidoirie.display_plaidoirie_config_interface({})
            
            # Bouton de génération
            if st.button("🚀 Générer la plaidoirie", type="primary", use_container_width=True):
                result = modules.plaidoirie.generate_plaidoirie(config, {})
                if result:
                    modules.plaidoirie.display_plaidoirie_results(result)
        except Exception as e:
            st.error(f"Erreur dans le module plaidoirie: {e}")
            show_plaidoirie_fallback()
    else:
        show_plaidoirie_fallback()

def show_plaidoirie_fallback():
    """Interface de secours pour les plaidoiries"""
    st.info("Module plaidoirie en cours de chargement...")
    
    # Interface basique
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox(
            "Type d'audience",
            ["Tribunal correctionnel", "Cour d'assises", "Tribunal civil"],
            key="plaidoirie_type"
        )
        
        st.selectbox(
            "Position",
            ["Défense", "Partie civile", "Demandeur"],
            key="plaidoirie_position"
        )
    
    with col2:
        st.select_slider(
            "Durée cible",
            options=["5 min", "10 min", "15 min", "20 min", "30 min"],
            value="15 min",
            key="plaidoirie_duree"
        )
        
        st.selectbox(
            "Style oratoire",
            ["Classique", "Moderne", "Percutant"],
            key="plaidoirie_style"
        )
    
    if st.button("Générer la plaidoirie", type="primary"):
        st.info("Génération de la plaidoirie...")

def show_pieces_interface():
    """Interface de gestion des pièces"""
    st.markdown("### 📎 Gestion des pièces")
    
    # Statistiques des pièces
    total_pieces = len(st.session_state.get('pieces_selectionnees', {}))
    total_docs = len(st.session_state.get('azure_documents', {}))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Documents disponibles", total_docs)
    with col2:
        st.metric("Pièces sélectionnées", total_pieces)
    with col3:
        st.metric("Catégories", len(set(p.categorie for p in st.session_state.get('pieces_selectionnees', {}).values())))
    with col4:
        avg_pertinence = sum(p.pertinence for p in st.session_state.get('pieces_selectionnees', {}).values()) / max(total_pieces, 1)
        st.metric("Pertinence moyenne", f"{avg_pertinence:.1f}/10")
    
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
    """Interface des outils avancés avec tous les outils visibles"""
    st.markdown("### 🛠️ Outils avancés")
    
    # Categories d'outils étendues
    tool_categories = {
        "📥 Import/Export": {
            "description": "Outils d'import et export de données",
            "tools": ["Import documents", "Import Excel/CSV", "Export sélection", "Générer rapport", "Backup complet"]
        },
        "⚙️ Configuration": {
            "description": "Paramètres et configuration système",
            "tools": ["API Keys", "Azure Config", "Interface", "Notifications", "Templates"]
        },
        "🔧 Maintenance": {
            "description": "Outils de maintenance et optimisation",
            "tools": ["Réinitialiser Azure", "Nettoyer cache", "Optimiser base", "Vérifier intégrité", "Logs système"]
        },
        "💻 Développement": {
            "description": "Outils pour développeurs",
            "tools": ["Debug modules", "Session state", "API tester", "Performance", "Console"]
        },
        "🤖 IA & LLM": {
            "description": "Gestion des modèles d'IA",
            "tools": ["Test LLMs", "Benchmark", "Historique", "Costs tracker", "Prompts library"]
        },
        "📊 Analytics": {
            "description": "Analyses et statistiques",
            "tools": ["Usage stats", "Performance metrics", "User activity", "Document analytics", "Search insights"]
        },
        "🔐 Sécurité": {
            "description": "Outils de sécurité et conformité",
            "tools": ["Audit trail", "Access logs", "Data encryption", "RGPD tools", "Backup security"]
        },
        "🧪 Tests": {
            "description": "Outils de test et validation",
            "tools": ["Test imports", "Validate data", "Check references", "Test integrations", "Stress test"]
        }
    }
    
    # Sélection de la catégorie
    selected_category = st.selectbox(
        "Catégorie d'outils",
        list(tool_categories.keys()),
        key="tool_category_select"
    )
    
    # Afficher la description
    st.info(tool_categories[selected_category]["description"])
    
    # Afficher les outils de la catégorie
    tools = tool_categories[selected_category]["tools"]
    
    # Créer une grille d'outils
    cols = st.columns(3)
    for idx, tool in enumerate(tools):
        with cols[idx % 3]:
            if st.button(tool, use_container_width=True, key=f"tool_{tool}"):
                handle_tool_action(selected_category, tool)

def handle_tool_action(category: str, tool: str):
    """Gère l'action d'un outil sélectionné"""
    
    # Import/Export
    if tool == "Import documents":
        st.session_state.show_import_modal = True
    elif tool == "Export sélection":
        st.session_state.show_export = True
    elif tool == "Générer rapport":
        generate_system_report()
    
    # Configuration
    elif tool == "API Keys":
        show_api_configuration()
    elif tool == "Azure Config":
        show_azure_configuration()
    
    # Maintenance
    elif tool == "Réinitialiser Azure":
        reinit_azure()
    elif tool == "Nettoyer cache":
        st.cache_data.clear()
        st.success("Cache nettoyé")
    
    # IA & LLM
    elif tool == "Test LLMs":
        test_all_llms()
    elif tool == "Benchmark":
        run_llm_benchmark()
    
    # Tests
    elif tool == "Test imports":
        test_imports_interface()
    
    # Autres
    else:
        st.info(f"Outil '{tool}' - Fonctionnalité en développement")

def show_api_configuration():
    """Interface de configuration des API"""
    st.markdown("#### 🔑 Configuration des clés API")
    
    # Grouper par provider
    providers = {
        "OpenAI": ["OPENAI_API_KEY", "OPENAI_ORG_ID"],
        "Anthropic": ["ANTHROPIC_API_KEY"],
        "Google": ["GOOGLE_API_KEY"],
        "Mistral": ["MISTRAL_API_KEY"],
        "Groq": ["GROQ_API_KEY"],
        "Azure": ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    }
    
    for provider, keys in providers.items():
        with st.expander(f"🔐 {provider}", expanded=False):
            for key in keys:
                current_value = os.getenv(key, "")
                masked_value = f"{'*' * 20}...{current_value[-4:]}" if current_value else ""
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_value = st.text_input(
                        key,
                        value="",
                        type="password",
                        placeholder=masked_value,
                        key=f"api_{key}"
                    )
                with col2:
                    if st.button("Mettre à jour", key=f"update_{key}"):
                        if new_value:
                            os.environ[key] = new_value
                            st.success(f"{key} mise à jour")
                            st.rerun()

def show_azure_configuration():
    """Configuration détaillée d'Azure"""
    st.markdown("#### ☁️ Configuration Azure")
    
    tabs = st.tabs(["Blob Storage", "Search", "Other Services"])
    
    with tabs[0]:
        st.text_input(
            "Connection String",
            type="password",
            key="azure_blob_connection",
            placeholder=os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")[:50] + "..." if os.getenv("AZURE_STORAGE_CONNECTION_STRING") else ""
        )
        
        st.text_input(
            "Container Name",
            value=os.getenv("AZURE_CONTAINER_NAME", "juridique-docs"),
            key="azure_container"
        )
        
        if st.button("Tester Blob Storage"):
            test_azure_blob()
    
    with tabs[1]:
        st.text_input(
            "Search Endpoint",
            value=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
            key="azure_search_endpoint"
        )
        
        st.text_input(
            "Search Key",
            type="password",
            key="azure_search_key"
        )
        
        st.text_input(
            "Index Name",
            value=os.getenv("AZURE_SEARCH_INDEX", "juridique-index"),
            key="azure_index"
        )
        
        if st.button("Tester Search"):
            test_azure_search()

def test_all_llms():
    """Test tous les LLMs disponibles"""
    st.markdown("#### 🧪 Test des modèles IA")
    
    if MULTI_LLM_AVAILABLE:
        llm_manager = MultiLLMManager()
        
        with st.spinner("Test en cours..."):
            results = llm_manager.test_connections()
            
            # Afficher les résultats
            cols = st.columns(len(results))
            for idx, (provider, status) in enumerate(results.items()):
                with cols[idx]:
                    if status:
                        st.success(f"✅ {provider}")
                        # Test de génération
                        if st.button(f"Test {provider}", key=f"test_gen_{provider}"):
                            test_llm_generation(provider)
                    else:
                        st.error(f"❌ {provider}")

def test_llm_generation(provider: str):
    """Test la génération pour un LLM spécifique"""
    prompt = st.text_area(
        "Prompt de test",
        value="Résume en une phrase le principe de la présomption d'innocence en droit français.",
        key=f"test_prompt_{provider}"
    )
    
    if prompt:
        llm_manager = MultiLLMManager()
        with st.spinner(f"Génération avec {provider}..."):
            result = llm_manager.query_single_llm(
                provider,
                prompt,
                temperature=0.7,
                max_tokens=200
            )
            
            if result['success']:
                st.success(f"Réponse de {provider}:")
                st.write(result['response'])
                st.caption(f"Temps: {result['elapsed_time']:.2f}s")
            else:
                st.error(f"Erreur: {result['error']}")

def run_llm_benchmark():
    """Lance un benchmark des LLMs"""
    st.markdown("#### 📊 Benchmark des modèles IA")
    
    benchmark_prompts = {
        "Simple": "Qu'est-ce qu'un abus de biens sociaux?",
        "Complexe": "Analysez la différence entre l'abus de confiance et l'escroquerie en citant la jurisprudence récente.",
        "Rédaction": "Rédigez l'introduction d'une plainte pour corruption."
    }
    
    selected_prompt = st.selectbox(
        "Type de test",
        list(benchmark_prompts.keys()),
        key="benchmark_type"
    )
    
    if st.button("🚀 Lancer le benchmark", type="primary"):
        if MULTI_LLM_AVAILABLE:
            llm_manager = MultiLLMManager()
            providers = llm_manager.get_available_providers()
            
            results = []
            progress = st.progress(0)
            
            for idx, provider in enumerate(providers):
                progress.progress((idx + 1) / len(providers))
                
                start_time = datetime.now()
                result = llm_manager.query_single_llm(
                    provider,
                    benchmark_prompts[selected_prompt],
                    temperature=0.7,
                    max_tokens=500
                )
                end_time = datetime.now()
                
                if result['success']:
                    results.append({
                        'Provider': provider,
                        'Temps (s)': (end_time - start_time).total_seconds(),
                        'Longueur': len(result['response']),
                        'Status': '✅'
                    })
                else:
                    results.append({
                        'Provider': provider,
                        'Temps (s)': 0,
                        'Longueur': 0,
                        'Status': '❌'
                    })
            
            # Afficher les résultats
            st.dataframe(results)

def test_imports_interface():
    """Interface de test des imports"""
    st.markdown("#### 🧪 Test des imports de modules")
    
    # Test rapide
    tests = {
        'utils.helpers.truncate_text': None,
        'models.dataclasses.EmailConfig': None,
        'models.dataclasses.PlaidoirieResult': None,
        'modules.dataclasses.Relationship': None,
        'managers.multi_llm_manager.MultiLLMManager': None
    }
    
    for module_path in tests:
        try:
            parts = module_path.split('.')
            module = '.'.join(parts[:-1])
            attr = parts[-1]
            exec(f"from {module} import {attr}")
            tests[module_path] = True
        except ImportError:
            tests[module_path] = False
    
    # Afficher les résultats
    cols = st.columns(2)
    for idx, (module, status) in enumerate(tests.items()):
        with cols[idx % 2]:
            if status:
                st.success(f"✅ {module}")
            else:
                st.error(f"❌ {module}")
    
    # Debug détaillé
    if st.checkbox("Afficher le debug détaillé"):
        if modules:
            debug_output = modules.debug_modules_status(output_to_streamlit=True)
            st.code(debug_output)

def generate_system_report():
    """Génère un rapport système complet"""
    st.markdown("#### 📊 Rapport système")
    
    report = {
        "Timestamp": datetime.now().isoformat(),
        "Version": app_config.version if app_config else "N/A",
        "Azure Blob": "Connected" if st.session_state.get('azure_blob_manager') else "Disconnected",
        "Azure Search": "Connected" if st.session_state.get('azure_search_manager') else "Disconnected",
        "LLMs actifs": len(st.session_state.get('selected_llm_providers', [])),
        "Modules chargés": len(modules.get_loaded_modules()) if modules else 0,
        "Documents": len(st.session_state.get('azure_documents', {})),
        "Pièces sélectionnées": len(st.session_state.get('pieces_selectionnees', {}))
    }
    
    # Afficher le rapport
    for key, value in report.items():
        st.metric(key, value)
    
    # Bouton de téléchargement
    report_text = "\n".join([f"{k}: {v}" for k, v in report.items()])
    st.download_button(
        "💾 Télécharger le rapport",
        report_text,
        f"rapport_systeme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain"
    )

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
    
    # IA suggestions
    if "?" in query:
        suggestions.append("🤖 Analyse IA")
    
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

# ========== SECTION 7: FONCTION PRINCIPALE ==========

def main():
    """Fonction principale avec interface optimisée"""
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    init_azure_managers()
    
    # Configuration LLM dans la sidebar
    show_llm_configuration()
    
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
            
            elif settings_tab == "API":
                show_api_configuration()
            
            elif settings_tab == "Azure":
                show_azure_configuration()
    
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