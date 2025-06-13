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
    initial_sidebar_state="collapsed"
)

# ========== SECTION 1: IMPORTS CENTRALISÉS ==========

# Import des gestionnaires Azure
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
    CONFIG_AVAILABLE = True
except ImportError:
    print("⚠️ config.app_config non trouvé")
    CONFIG_AVAILABLE = False
    class DefaultConfig:
        version = "2.0.0"
        debug = False
        max_file_size_mb = 10
        max_files_per_upload = 5
        enable_azure_storage = False
        enable_azure_search = False
        enable_multi_llm = True
        enable_email = False
    
    app_config = DefaultConfig()
    api_config = {}

# Import des utilitaires de base
try:
    from utils.helpers import initialize_session_state, truncate_text
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
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
            st.session_state.current_view = "accueil"
            st.session_state.current_module = None
            st.session_state.workflow_active = None
            st.session_state.multi_ia_active = True

try:
    from utils.styles import load_custom_css
except ImportError:
    def load_custom_css():
        pass

# Import du service de recherche universelle
try:
    from managers.universal_search_service import UniversalSearchService
    SEARCH_SERVICE_AVAILABLE = True
except ImportError:
    SEARCH_SERVICE_AVAILABLE = False
    class UniversalSearchService:
        async def search(self, query: str, filters: Optional[Dict] = None):
            from types import SimpleNamespace
            return SimpleNamespace(
                total_count=0,
                documents=[],
                suggestions=[],
                facets={}
            )

# Import des managers principaux
try:
    from managers.multi_llm_manager import MultiLLMManager
    MULTI_LLM_AVAILABLE = True
except ImportError:
    MULTI_LLM_AVAILABLE = False

# Import des dataclasses
try:
    from models.dataclasses import (
        Document, PieceSelectionnee, PieceProcedure,
        EmailConfig, Relationship, PlaidoirieResult, 
        PreparationClientResult
    )
    DATACLASSES_AVAILABLE = True
except ImportError:
    DATACLASSES_AVAILABLE = False
    print("⚠️ models.dataclasses non disponible")

# ========== IMPORTS DES MODULES MÉTIER ==========

modules_disponibles = {}

# Module unifié de gestion des pièces (fusion de pieces_manager et selection_pieces)
try:
    from modules.pieces_manager import display_pieces_interface, init_pieces_manager
    modules_disponibles['pieces_manager'] = True
    # Initialiser le gestionnaire de pièces
    if 'gestionnaire_pieces' not in st.session_state:
        init_pieces_manager()
except ImportError:
    modules_disponibles['pieces_manager'] = False

# Module unifié d'import/export
try:
    from modules.import_export import process_import_request, process_export_request, show_import_export_interface
    modules_disponibles['import_export'] = True
except ImportError:
    modules_disponibles['import_export'] = False

# Modules de gestion documentaire
try:
    from modules.dossier_penal import display_dossier_penal_interface
    modules_disponibles['dossier_penal'] = True
except ImportError:
    modules_disponibles['dossier_penal'] = False

try:
    from modules.export_juridique import GestionnaireExport
    modules_disponibles['export_juridique'] = True
except ImportError:
    modules_disponibles['export_juridique'] = False

try:
    from modules.explorer import show_explorer_interface
    modules_disponibles['explorer'] = True
except ImportError:
    modules_disponibles['explorer'] = False

# Modules de recherche et analyse
try:
    from modules.recherche import show_page as show_recherche_page
    modules_disponibles['recherche'] = True
except ImportError:
    modules_disponibles['recherche'] = False

try:
    from modules.analyse_ia import show_page as show_analyse_ia
    modules_disponibles['analyse_ia'] = True
except ImportError:
    modules_disponibles['analyse_ia'] = False

try:
    from modules.jurisprudence import show_page as show_jurisprudence_page
    modules_disponibles['jurisprudence'] = True
except ImportError:
    modules_disponibles['jurisprudence'] = False

try:
    from modules.risques import display_risques_interface
    modules_disponibles['risques'] = True
except ImportError:
    modules_disponibles['risques'] = False

# Modules de génération et rédaction
try:
    from modules.generation_juridique import GenerateurActesJuridiques, show_page as show_generation
    modules_disponibles['generation'] = True
except ImportError:
    modules_disponibles['generation'] = False

try:
    from modules.generation_longue import show_generation_longue_interface
    modules_disponibles['generation_longue'] = True
except ImportError:
    modules_disponibles['generation_longue'] = False

try:
    from modules.redaction_unified import show_page as show_redaction_unified
    modules_disponibles['redaction_unified'] = True
except ImportError:
    modules_disponibles['redaction_unified'] = False

try:
    from modules.plaidoirie import process_plaidoirie_request
    modules_disponibles['plaidoirie'] = True
except ImportError:
    modules_disponibles['plaidoirie'] = False

# Modules de visualisation et comparaison
try:
    from modules.mapping import process_mapping_request
    modules_disponibles['mapping'] = True
except ImportError:
    modules_disponibles['mapping'] = False

try:
    from modules.timeline import show_page as show_timeline_page
    modules_disponibles['timeline'] = True
except ImportError:
    modules_disponibles['timeline'] = False

try:
    from modules.comparison import process_comparison_request, show_page as show_comparison_page
    modules_disponibles['comparison'] = True
except ImportError:
    modules_disponibles['comparison'] = False

try:
    from modules.synthesis import show_page as show_synthesis_page
    modules_disponibles['synthesis'] = True
except ImportError:
    modules_disponibles['synthesis'] = False

# Modules de communication et support
try:
    from modules.bordereau import process_bordereau_request, show_page as show_bordereau_page
    modules_disponibles['bordereau'] = True
except ImportError:
    modules_disponibles['bordereau'] = False

try:
    from modules.email import process_email_request, show_email_interface, show_page as show_email_page
    modules_disponibles['email'] = True
except ImportError:
    modules_disponibles['email'] = False

try:
    from modules.preparation_client import show_page as show_preparation_page
    modules_disponibles['preparation_client'] = True
except ImportError:
    modules_disponibles['preparation_client'] = False

# Modules de configuration et outils
try:
    from modules.configuration import show_page as show_configuration_page
    modules_disponibles['configuration'] = True
except ImportError:
    modules_disponibles['configuration'] = False

try:
    from modules.template import show_template_manager
    modules_disponibles['template'] = True
except ImportError:
    modules_disponibles['template'] = False

try:
    from modules.integration_juridique import show_page as show_integration_page
    modules_disponibles['integration_juridique'] = True
except ImportError:
    modules_disponibles['integration_juridique'] = False

# ========== SECTION 2: STYLES CSS MODERNES ==========

st.markdown("""
<style>
    /* === DESIGN MODERNE ET ÉPURÉ === */
    .main {
        padding: 0;
        max-width: 100%;
    }
    
    /* Navigation principale moderne */
    .main-nav {
        background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%);
        padding: 1rem 2rem;
        margin: 0 -1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    /* Conteneur principal avec sidebar */
    .app-container {
        display: flex;
        min-height: calc(100vh - 80px);
        gap: 0;
    }
    
    /* Sidebar moderne */
    .modern-sidebar {
        width: 280px;
        background: #f8f9fa;
        border-right: 1px solid #e0e0e0;
        padding: 1.5rem 1rem;
        overflow-y: auto;
        transition: all 0.3s ease;
    }
    
    .modern-sidebar.collapsed {
        width: 60px;
    }
    
    /* Menu items */
    .menu-section {
        margin-bottom: 2rem;
    }
    
    .menu-section-title {
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
        padding-left: 0.5rem;
    }
    
    .menu-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #333;
        text-decoration: none;
    }
    
    .menu-item:hover {
        background: #e3f2fd;
        color: #1976d2;
        transform: translateX(4px);
    }
    
    .menu-item.active {
        background: #1976d2;
        color: white;
    }
    
    .menu-item .icon {
        font-size: 1.2rem;
        width: 24px;
        text-align: center;
    }
    
    /* Contenu principal */
    .main-content {
        flex: 1;
        padding: 2rem;
        background: #ffffff;
        overflow-y: auto;
    }
    
    /* Recherche universelle prominente */
    .universal-search-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    
    .universal-search-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.3; }
    }
    
    /* Cards modernes */
    .module-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 1px solid #f0f0f0;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .module-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        border-color: #667eea;
    }
    
    .module-card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
    }
    
    .module-card-icon {
        font-size: 2rem;
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .module-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1f3a;
        margin: 0;
    }
    
    .module-card-description {
        color: #666;
        font-size: 0.9rem;
        flex-grow: 1;
        margin-bottom: 1rem;
    }
    
    /* Quick access grid */
    .quick-access-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    /* Workflow cards */
    .workflow-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .workflow-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .workflow-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.15);
    }
    
    .workflow-card:hover::after {
        transform: scaleX(1);
    }
    
    /* Status indicators */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    
    .status-dot.online { background: #4caf50; }
    .status-dot.offline { background: #f44336; }
    .status-dot.warning { background: #ff9800; }
    
    /* Progress steps */
    .progress-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2rem;
        margin: 2rem 0;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }
    
    .progress-step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: #666;
        transition: all 0.3s ease;
    }
    
    .progress-step.active .progress-step-circle {
        background: #667eea;
        color: white;
        transform: scale(1.1);
    }
    
    .progress-step.completed .progress-step-circle {
        background: #4caf50;
        color: white;
    }
    
    .progress-step-label {
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #666;
    }
    
    .progress-line {
        position: absolute;
        top: 20px;
        left: 40px;
        width: calc(100% + 2rem);
        height: 2px;
        background: #e0e0e0;
        z-index: -1;
    }
    
    .progress-line.completed {
        background: #4caf50;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .modern-sidebar {
            position: fixed;
            left: -280px;
            height: 100vh;
            z-index: 200;
        }
        
        .modern-sidebar.open {
            left: 0;
        }
        
        .main-content {
            padding: 1rem;
        }
        
        .universal-search-hero {
            padding: 2rem 1rem;
        }
    }
    
    /* Animations fluides */
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
    
    /* Tooltips modernes */
    .tooltip-modern {
        position: relative;
    }
    
    .tooltip-modern::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.85rem;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
    }
    
    .tooltip-modern:hover::after {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# ========== SECTION 3: GESTIONNAIRES AZURE ==========

def init_azure_managers():
    """Initialise les gestionnaires Azure avec logs détaillés"""
    
    if not AZURE_AVAILABLE:
        print(f"⚠️ Azure non disponible: {AZURE_ERROR}")
        st.session_state.azure_blob_manager = None
        st.session_state.azure_search_manager = None
        st.session_state.azure_error = AZURE_ERROR
        return
    
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state or st.session_state.azure_blob_manager is None:
        try:
            if not os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
                st.session_state.azure_blob_manager = None
                st.session_state.azure_blob_error = "Connection string non définie"
            else:
                from managers.azure_blob_manager import AzureBlobManager
                manager = AzureBlobManager()
                st.session_state.azure_blob_manager = manager
                print("✅ Azure Blob connecté")
        except Exception as e:
            print(f"❌ Erreur Azure Blob: {e}")
            st.session_state.azure_blob_manager = None
            st.session_state.azure_blob_error = str(e)
    
    # Azure Search Manager  
    if 'azure_search_manager' not in st.session_state or st.session_state.azure_search_manager is None:
        try:
            if not os.getenv('AZURE_SEARCH_ENDPOINT') or not os.getenv('AZURE_SEARCH_KEY'):
                st.session_state.azure_search_manager = None
                st.session_state.azure_search_error = "Endpoint ou clé non définis"
            else:
                from managers.azure_search_manager import AzureSearchManager
                manager = AzureSearchManager()
                st.session_state.azure_search_manager = manager
                print("✅ Azure Search connecté")
        except Exception as e:
            print(f"❌ Erreur Azure Search: {e}")
            st.session_state.azure_search_manager = None
            st.session_state.azure_search_error = str(e)

# ========== SECTION 4: NAVIGATION MODERNE ==========

def show_modern_navigation():
    """Affiche la navigation principale moderne"""
    st.markdown('<div class="main-nav">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([3, 4, 2, 1])
    
    with col1:
        st.markdown("# ⚖️ Assistant Juridique IA")
    
    with col2:
        # Barre de recherche rapide dans la nav
        search_query = st.text_input(
            "Recherche rapide",
            placeholder="Tapez votre recherche...",
            key="nav_search",
            label_visibility="collapsed"
        )
    
    with col3:
        # Indicateurs de statut
        azure_connected = bool(st.session_state.get('azure_blob_manager') or st.session_state.get('azure_search_manager'))
        multi_ia = st.session_state.get('multi_ia_active', True)
        
        status_html = f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-top: 8px;">
            <span><span class="status-dot {'online' if azure_connected else 'offline'}"></span>Azure</span>
            <span><span class="status-dot {'online' if multi_ia else 'offline'}"></span>Multi-IA</span>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    
    with col4:
        if st.button("⚙️", help="Paramètres"):
            st.session_state.current_module = 'configuration'
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Traiter la recherche rapide
    if search_query and st.session_state.get('nav_search') != st.session_state.get('last_nav_search'):
        st.session_state.last_nav_search = search_query
        st.session_state.universal_search_query = search_query
        st.session_state.current_view = 'recherche'

def show_modern_sidebar():
    """Affiche la sidebar moderne avec menu organisé"""
    with st.sidebar:
        # Logo/Titre
        st.markdown("### 📚 Menu Principal")
        
        # Accueil
        if st.button("🏠 Accueil", use_container_width=True, 
                    type="primary" if st.session_state.get('current_view') == 'accueil' else "secondary"):
            st.session_state.current_view = 'accueil'
            st.session_state.current_module = None
        
        # Section Gestion documentaire
        st.markdown("#### 📁 Gestion documentaire")
        
        if st.button("📎 Gestion des pièces", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'pieces_manager' else "secondary"):
            st.session_state.current_view = 'pieces'
            st.session_state.current_module = 'pieces_manager'
        
        if st.button("📥 Import/Export", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'import_export' else "secondary"):
            st.session_state.current_view = 'import_export'
            st.session_state.current_module = 'import_export'
        
        if modules_disponibles.get('dossier_penal'):
            if st.button("📂 Dossiers pénaux", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'dossier_penal' else "secondary"):
                st.session_state.current_view = 'dossiers'
                st.session_state.current_module = 'dossier_penal'
        
        if modules_disponibles.get('explorer'):
            if st.button("🗂️ Explorateur", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'explorer' else "secondary"):
                st.session_state.current_view = 'explorer'
                st.session_state.current_module = 'explorer'
        
        # Section Analyse & Recherche
        st.markdown("#### 🔍 Analyse & Recherche")
        
        if st.button("🔍 Recherche intelligente", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'recherche' else "secondary"):
            st.session_state.current_view = 'recherche'
            st.session_state.current_module = 'recherche'
        
        if st.button("📊 Analyse IA", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'analyse_ia' else "secondary"):
            st.session_state.current_view = 'analyse'
            st.session_state.current_module = 'analyse_ia'
        
        if st.button("⚖️ Jurisprudence", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'jurisprudence' else "secondary"):
            st.session_state.current_view = 'jurisprudence'
            st.session_state.current_module = 'jurisprudence'
        
        if modules_disponibles.get('risques'):
            if st.button("⚠️ Analyse des risques", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'risques' else "secondary"):
                st.session_state.current_view = 'risques'
                st.session_state.current_module = 'risques'
        
        # Section Rédaction
        st.markdown("#### ✍️ Rédaction")
        
        if st.button("✍️ Rédaction unifiée", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'redaction_unified' else "secondary"):
            st.session_state.current_view = 'redaction'
            st.session_state.current_module = 'redaction_unified'
        
        # Section Visualisation
        st.markdown("#### 📊 Visualisation")
        
        tools = [
            ("📋 Bordereau", "bordereau", "bordereau"),
            ("📅 Timeline", "timeline", "timeline"),
            ("🔄 Comparaison", "comparison", "comparison"),
            ("🗺️ Cartographie", "mapping", "mapping"),
        ]
        
        for label, view, module in tools:
            if modules_disponibles.get(module):
                if st.button(label, use_container_width=True,
                            type="primary" if st.session_state.get('current_module') == module else "secondary"):
                    st.session_state.current_view = view
                    st.session_state.current_module = module
        
        # Section Communication
        st.markdown("#### 📧 Communication")
        
        if modules_disponibles.get('email'):
            if st.button("📧 Emails", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'email' else "secondary"):
                st.session_state.current_view = 'email'
                st.session_state.current_module = 'email'
        
        if modules_disponibles.get('preparation_client'):
            if st.button("👥 Préparation client", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'preparation_client' else "secondary"):
                st.session_state.current_view = 'preparation_client'
                st.session_state.current_module = 'preparation_client'
        
        # Section Configuration
        st.markdown("#### ⚙️ Configuration")
        
        if st.button("📋 Templates", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'template' else "secondary"):
            st.session_state.current_module = 'template'
        
        if st.button("🔧 Paramètres", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'configuration' else "secondary"):
            st.session_state.current_module = 'configuration'

# ========== SECTION 5: PAGE D'ACCUEIL ==========

def show_home_page():
    """Page d'accueil moderne avec recherche universelle et accès rapide"""
    
    # Hero section avec recherche universelle
    st.markdown('<div class="universal-search-hero fade-in">', unsafe_allow_html=True)
    st.markdown("## 🔍 Recherche Intelligente Universelle")
    st.markdown("Décrivez ce que vous voulez faire en langage naturel")
    
    query = st.text_area(
        "Votre requête",
        placeholder="Ex: J'ai besoin de préparer l'audience de demain pour l'affaire Martin...\n"
                   "Ou: Rédige une plainte pour abus de biens sociaux contre la société XYZ...\n"
                   "Ou: Analyse tous les documents concernant la corruption...",
        height=100,
        key="universal_search",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔍 Rechercher", type="primary", use_container_width=True):
            if query:
                handle_universal_search(query)
    
    with col3:
        if st.button("🎲 Exemple", use_container_width=True):
            examples = [
                "Rédige une plainte avec constitution de partie civile pour abus de biens sociaux",
                "Analyse les risques juridiques dans le dossier @VINCI2024",
                "Trouve la jurisprudence sur la corruption dans le secteur public",
                "Prépare un bordereau de communication pour l'audience du 15 janvier",
                "Compare les témoignages de Martin et Dupont dans l'affaire ABC",
                "Import tous les documents PDF du dossier Dupont",
                "Sélectionne toutes les pièces importantes pour la communication"
            ]
            import random
            st.session_state.universal_search = random.choice(examples)
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Workflows principaux
    st.markdown("### 🎯 Workflows principaux")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container():
            st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
            st.markdown("#### 📎 Gestion des pièces")
            st.markdown("Organisez et sélectionnez vos pièces")
            if st.button("Ouvrir", key="start_pieces", use_container_width=True):
                st.session_state.current_view = "pieces"
                st.session_state.current_module = "pieces_manager"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
            st.markdown("#### 📥 Import/Export")
            st.markdown("Importez et exportez vos documents")
            if st.button("Ouvrir", key="start_import_export", use_container_width=True):
                st.session_state.current_view = "import_export"
                st.session_state.current_module = "import_export"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
            st.markdown("#### 📊 Analyse IA")
            st.markdown("Analysez vos documents avec l'IA")
            if st.button("Ouvrir", key="start_analyse", use_container_width=True):
                st.session_state.current_view = "analyse"
                st.session_state.current_module = "analyse_ia"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        with st.container():
            st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
            st.markdown("#### ✍️ Rédaction")
            st.markdown("Générez des actes juridiques")
            if st.button("Ouvrir", key="start_redaction", use_container_width=True):
                st.session_state.current_view = "redaction"
                st.session_state.current_module = "redaction_unified"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Accès rapide aux modules
    st.markdown("### ⚡ Accès rapide")
    
    st.markdown('<div class="quick-access-grid">', unsafe_allow_html=True)
    
    modules_quick = [
        ("🔍", "Recherche", "Recherche intelligente", "recherche"),
        ("⚖️", "Jurisprudence", "Base de jurisprudence", "jurisprudence"),
        ("📋", "Bordereau", "Créer un bordereau", "bordereau"),
        ("📅", "Timeline", "Chronologie des événements", "timeline"),
        ("🔄", "Comparaison", "Comparer des documents", "comparison"),
        ("📧", "Emails", "Gestion des emails", "email"),
        ("⚠️", "Risques", "Analyse des risques", "risques"),
        ("🗂️", "Explorer", "Explorer les fichiers", "explorer"),
        ("📂", "Dossiers", "Dossiers pénaux", "dossier_penal"),
    ]
    
    cols = st.columns(3)
    for idx, (icon, title, desc, module) in enumerate(modules_quick):
        if modules_disponibles.get(module):
            with cols[idx % 3]:
                with st.container():
                    st.markdown('<div class="module-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="module-card-header">', unsafe_allow_html=True)
                    st.markdown(f'<div class="module-card-icon">{icon}</div>', unsafe_allow_html=True)
                    st.markdown(f'<h3 class="module-card-title">{title}</h3>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown(f'<p class="module-card-description">{desc}</p>', unsafe_allow_html=True)
                    if st.button("Ouvrir", key=f"quick_{module}", use_container_width=True):
                        st.session_state.current_module = module
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== SECTION 6: GESTION DE LA RECHERCHE UNIVERSELLE ==========

def handle_universal_search(query: str):
    """Traite la recherche universelle et redirige vers le bon module"""
    query_lower = query.lower()
    
    # Analyse de l'intention avec des patterns plus sophistiqués
    patterns = {
        'import': {
            'keywords': ['import', 'importer', 'charger', 'upload', 'télécharger', 'ajouter des documents', 'pdf', 'xlsx', 'csv'],
            'module': 'import_export',
            'view': 'import_export'
        },
        'export': {
            'keywords': ['export', 'exporter', 'télécharger', 'sauvegarder', 'extraire', 'download'],
            'module': 'import_export',
            'view': 'import_export'
        },
        'pieces': {
            'keywords': ['pièce', 'document', 'fichier', 'gérer les pièces', 'organiser', 'sélectionner', 'sélection', 'communication'],
            'module': 'pieces_manager',
            'view': 'pieces'
        },
        'redaction': {
            'keywords': ['rédiger', 'rédige', 'créer', 'générer', 'préparer', 'établir', 'plainte', 'conclusions', 'assignation'],
            'module': 'redaction_unified',
            'view': 'redaction'
        },
        'analyse': {
            'keywords': ['analyser', 'analyse', 'examiner', 'étudier', 'risque', 'identifier'],
            'module': 'analyse_ia',
            'view': 'analyse'
        },
        'jurisprudence': {
            'keywords': ['jurisprudence', 'arrêt', 'décision', 'cour de cassation', 'juridique'],
            'module': 'jurisprudence',
            'view': 'jurisprudence'
        },
        'bordereau': {
            'keywords': ['bordereau', 'communication de pièces', 'liste des pièces'],
            'module': 'bordereau',
            'view': 'bordereau'
        },
        'comparison': {
            'keywords': ['comparer', 'différence', 'comparaison', 'confronter'],
            'module': 'comparison',
            'view': 'comparison'
        },
        'timeline': {
            'keywords': ['chronologie', 'timeline', 'calendrier', 'dates', 'événements'],
            'module': 'timeline',
            'view': 'timeline'
        },
        'email': {
            'keywords': ['email', 'mail', 'courrier', 'envoyer', 'correspondance'],
            'module': 'email',
            'view': 'email'
        },
        'risques': {
            'keywords': ['risque', 'danger', 'menace', 'vulnérabilité', 'évaluation des risques'],
            'module': 'risques',
            'view': 'risques'
        },
        'dossier': {
            'keywords': ['dossier', 'affaire', 'dossier pénal', 'organiser dossier'],
            'module': 'dossier_penal',
            'view': 'dossiers'
        }
    }
    
    # Détection du module approprié
    best_match = None
    best_score = 0
    
    for pattern_name, pattern_data in patterns.items():
        score = sum(1 for keyword in pattern_data['keywords'] if keyword in query_lower)
        if score > best_score:
            best_score = score
            best_match = pattern_data
    
    if best_match and best_score > 0:
        st.session_state.current_view = best_match['view']
        st.session_state.current_module = best_match['module']
        st.session_state.search_context = query
    else:
        # Par défaut, utiliser le module de recherche
        st.session_state.current_view = 'recherche'
        st.session_state.current_module = 'recherche'
        st.session_state.search_query = query
    
    st.rerun()

# ========== SECTION 7: AFFICHAGE DES MODULES ==========

def show_module_content():
    """Affiche le contenu du module actuel"""
    module = st.session_state.get('current_module')
    
    if not module:
        return
    
    # Titre du module avec breadcrumb
    module_titles = {
        'pieces_manager': "📎 Gestion des pièces",
        'import_export': "📥📤 Import/Export",
        'analyse_ia': "📊 Analyse IA",
        'redaction_unified': "✍️ Rédaction d'actes",
        'jurisprudence': "⚖️ Recherche de jurisprudence",
        'bordereau': "📋 Création de bordereau",
        'timeline': "📅 Timeline des événements",
        'comparison': "🔄 Comparaison de documents",
        'email': "📧 Gestion des emails",
        'risques': "⚠️ Analyse des risques",
        'recherche': "🔍 Recherche avancée",
        'dossier_penal': "📂 Dossiers pénaux",
        'explorer': "🗂️ Explorateur de fichiers",
        'configuration': "⚙️ Configuration",
        'template': "📋 Gestion des templates",
        'preparation_client': "👥 Préparation client"
    }
    
    if module in module_titles:
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"## {module_titles[module]}")
        with col2:
            if st.button("❌", help="Fermer"):
                st.session_state.current_module = None
                st.session_state.current_view = 'accueil'
                st.rerun()
    
    # Afficher le module
    try:
        if module == 'pieces_manager' and modules_disponibles.get('pieces_manager'):
            display_pieces_interface()
            
        elif module == 'import_export' and modules_disponibles.get('import_export'):
            show_import_export_interface()
            
        elif module == 'analyse_ia' and modules_disponibles.get('analyse_ia'):
            show_analyse_ia()
            
        elif module == 'redaction_unified' and modules_disponibles.get('redaction_unified'):
            show_redaction_unified()
            
        elif module == 'jurisprudence' and modules_disponibles.get('jurisprudence'):
            show_jurisprudence_page()
            
        elif module == 'bordereau' and modules_disponibles.get('bordereau'):
            show_bordereau_page()
            
        elif module == 'timeline' and modules_disponibles.get('timeline'):
            show_timeline_page()
            
        elif module == 'comparison' and modules_disponibles.get('comparison'):
            show_comparison_page()
            
        elif module == 'email' and modules_disponibles.get('email'):
            show_email_page()
            
        elif module == 'risques' and modules_disponibles.get('risques'):
            display_risques_interface()
            
        elif module == 'recherche' and modules_disponibles.get('recherche'):
            show_recherche_page()
            
        elif module == 'dossier_penal' and modules_disponibles.get('dossier_penal'):
            display_dossier_penal_interface()
            
        elif module == 'explorer' and modules_disponibles.get('explorer'):
            show_explorer_interface()
            
        elif module == 'configuration' and modules_disponibles.get('configuration'):
            show_configuration_page()
            
        elif module == 'template' and modules_disponibles.get('template'):
            show_template_manager()
            
        elif module == 'generation' and modules_disponibles.get('generation'):
            show_generation()
            
        elif module == 'generation_longue' and modules_disponibles.get('generation_longue'):
            show_generation_longue_interface()
            
        elif module == 'plaidoirie' and modules_disponibles.get('plaidoirie'):
            query = st.text_input("Décrivez la plaidoirie souhaitée")
            if query:
                process_plaidoirie_request(query, {})
                
        elif module == 'mapping' and modules_disponibles.get('mapping'):
            query = st.text_input("Décrivez la cartographie souhaitée")
            if query:
                process_mapping_request(query, {})
                
        elif module == 'synthesis' and modules_disponibles.get('synthesis'):
            show_synthesis_page()
            
        elif module == 'preparation_client' and modules_disponibles.get('preparation_client'):
            show_preparation_page()
            
        elif module == 'integration_juridique' and modules_disponibles.get('integration_juridique'):
            show_integration_page()
            
        elif module == 'export_juridique' and modules_disponibles.get('export_juridique'):
            gestionnaire = GestionnaireExport()
            st.info("Module d'export juridique chargé")
            
        else:
            st.error(f"Module {module} non disponible ou non reconnu")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement du module : {str(e)}")
        if app_config.debug:
            st.code(traceback.format_exc())

# ========== SECTION 8: FONCTION PRINCIPALE ==========

def main():
    """Fonction principale avec interface moderne et navigation intuitive"""
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    init_azure_managers()
    
    # Navigation principale
    show_modern_navigation()
    
    # Layout avec sidebar
    show_modern_sidebar()
    
    # Contenu principal
    if st.session_state.get('current_view') == 'accueil' and not st.session_state.get('current_module'):
        show_home_page()
    else:
        show_module_content()
    
    # Footer minimal
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(f"© 2024 Assistant Juridique IA v{app_config.version} - {datetime.now().strftime('%H:%M')}")
    
    # Mode développeur (caché par défaut)
    if st.checkbox("🔧 Mode développeur", key="dev_mode", value=False):
        with st.expander("Informations système"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Modules disponibles:**")
                available = sum(1 for v in modules_disponibles.values() if v)
                st.metric("Modules actifs", f"{available}/{len(modules_disponibles)}")
                
                # Liste détaillée
                for module, status in sorted(modules_disponibles.items()):
                    st.write(f"{'✅' if status else '❌'} {module}")
            
            with col2:
                st.write("**État système:**")
                st.write(f"- Azure Blob: {'✅' if st.session_state.get('azure_blob_manager') else '❌'}")
                st.write(f"- Azure Search: {'✅' if st.session_state.get('azure_search_manager') else '❌'}")
                st.write(f"- Multi-IA: {'✅' if st.session_state.get('multi_ia_active') else '❌'}")
                st.write(f"- Vue actuelle: {st.session_state.get('current_view', 'N/A')}")
                st.write(f"- Module actuel: {st.session_state.get('current_module', 'N/A')}")
                st.write(f"- Gestionnaire pièces: {'✅' if st.session_state.get('gestionnaire_pieces') else '❌'}")

# Point d'entrée
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ Erreur critique")
        st.code(str(e))
        with st.expander("Détails complets"):
            st.code(traceback.format_exc())