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

# Import des configurations de documents
try:
    from models.configurations import DocumentConfigurations
    DOCUMENT_CONFIG_AVAILABLE = True
    print("✅ Configurations de documents chargées")
except ImportError:
    DOCUMENT_CONFIG_AVAILABLE = False
    print("⚠️ models.configurations non disponible")

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

# ========== IMPORTS DES MODULES MÉTIER (RÉORGANISÉS PAR CATÉGORIE) ==========

modules_disponibles = {}

# === 1. RECHERCHE ET ANALYSE ===
# Module unifié de recherche et analyse (PRIORITAIRE)
try:
    from modules.recherche_analyse_unifiee import (
        show_page as show_recherche_analyse_page,
        UnifiedSearchAnalysisInterface,
        NaturalLanguageAnalyzer
    )
    modules_disponibles['recherche_analyse_unifiee'] = True
    print("✅ Module recherche_analyse_unifiee chargé")
except ImportError as e:
    modules_disponibles['recherche_analyse_unifiee'] = False
    print(f"❌ Module recherche_analyse_unifiee non disponible: {e}")

# Module de jurisprudence
try:
    from modules.jurisprudence import (
        show_page as show_jurisprudence_page,
        show_jurisprudence_interface,
        get_jurisprudence_for_document,
        format_jurisprudence_citation,
        verify_and_update_citations
    )
    modules_disponibles['jurisprudence'] = True
    print("✅ Module jurisprudence chargé")
except ImportError:
    modules_disponibles['jurisprudence'] = False

# Module d'analyse des risques
try:
    from modules.risques import display_risques_interface
    modules_disponibles['risques'] = True
except ImportError:
    modules_disponibles['risques'] = False

# === 2. GESTION DOCUMENTAIRE ===
# Module unifié de gestion des pièces (REMPLACE pieces_manager ET bordereau)
try:
    from modules.pieces_manager import (
        display_pieces_interface, 
        init_pieces_manager,
        process_pieces_request,
        process_liste_pieces_request,
        GestionnairePiecesUnifie
    )
    modules_disponibles['pieces_manager'] = True
    if 'gestionnaire_pieces' not in st.session_state:
        init_pieces_manager()
    print("✅ Module pieces_manager unifié chargé (inclut liste des pièces)")
except ImportError as e:
    modules_disponibles['pieces_manager'] = False
    print(f"❌ Module pieces_manager non disponible: {e}")

# Note: Le module bordereau est maintenant intégré dans pieces_manager
# On garde une compatibilité pour les références existantes
modules_disponibles['bordereau'] = modules_disponibles['pieces_manager']

# Module unifié d'import/export
try:
    from modules.import_export import (
        show_import_interface, 
        show_import_export_tabs,
        process_import_request,
        process_export_request,
        show_import_export_interface
    )
    modules_disponibles['import_export'] = True
    print("✅ Module import_export chargé")
except ImportError:
    modules_disponibles['import_export'] = False

# Module explorateur de documents
try:
    from modules.explorer import show_explorer_interface
    modules_disponibles['explorer'] = True
    print("✅ Module explorer chargé")
except ImportError:
    modules_disponibles['explorer'] = False

# Module de dossiers pénaux
try:
    from modules.dossier_penal import display_dossier_penal_interface
    modules_disponibles['dossier_penal'] = True
    print("✅ Module dossier_penal chargé")
except ImportError:
    modules_disponibles['dossier_penal'] = False

# === 3. RÉDACTION ET GÉNÉRATION ===
# Module unifié de rédaction (REMPLACE generation_juridique)
try:
    from modules.redaction_unified import (
        show_page as show_redaction_unified,
        GenerateurActesJuridiques,
        TypeActe,
        StyleRedaction,
        PhaseProcedurale
    )
    modules_disponibles['redaction_unified'] = True
    print("✅ Module redaction_unified chargé")
except ImportError:
    modules_disponibles['redaction_unified'] = False

# Module de génération longue
try:
    from modules.generation_longue import show_generation_longue_interface
    modules_disponibles['generation_longue'] = True
    print("✅ Module generation_longue chargé")
except ImportError:
    modules_disponibles['generation_longue'] = False

# Module de gestion des templates
try:
    from modules.template import show_template_manager
    modules_disponibles['template'] = True
except ImportError:
    modules_disponibles['template'] = False

# === 4. PRODUCTION ET VISUALISATION ===
# Module Timeline
try:
    from modules.timeline import process_timeline_request
    modules_disponibles['timeline'] = True
    print("✅ Module timeline chargé")
    
    def show_timeline_page():
        """Page principale du module timeline"""
        st.markdown("## 📅 Timeline des événements")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_area(
                "Décrivez la chronologie souhaitée",
                placeholder="Ex: Créer une timeline des événements financiers dans le dossier VINCI\n"
                           "Ou: Chronologie des auditions et témoignages\n"
                           "Ou: Timeline procédurale de l'affaire",
                height=100,
                key="timeline_query"
            )
        
        with col2:
            st.markdown("#### Options rapides")
            if st.button("📅 Timeline complète", use_container_width=True):
                st.session_state.timeline_query = "Créer une timeline complète de tous les événements"
            if st.button("⚖️ Timeline procédurale", use_container_width=True):
                st.session_state.timeline_query = "Timeline des événements procéduraux"
            if st.button("💰 Timeline financière", use_container_width=True):
                st.session_state.timeline_query = "Timeline des transactions financiers"
        
        if query and st.button("🚀 Générer la timeline", type="primary", use_container_width=True):
            process_timeline_request(query, {'reference': query})
        
        if st.session_state.get('timeline_result'):
            st.markdown("---")
            st.markdown("### 📊 Timeline générée")
            from modules.timeline import display_timeline_results
            display_timeline_results(st.session_state.timeline_result)
            
except ImportError:
    modules_disponibles['timeline'] = False
    def show_timeline_page():
        st.error("Module timeline non disponible")

# Module Comparison
try:
    from modules.comparison import process_comparison_request
    modules_disponibles['comparison'] = True
    print("✅ Module comparison chargé")
    
    def show_comparison_page():
        """Page principale du module comparison"""
        st.markdown("## 🔄 Comparaison de documents")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_area(
                "Décrivez la comparaison souhaitée",
                placeholder="Ex: Comparer les témoignages de Martin et Dupont\n"
                           "Ou: Analyser les divergences entre les expertises\n"
                           "Ou: Comparer les versions du contrat",
                height=100,
                key="comparison_query"
            )
        
        with col2:
            st.markdown("#### Comparaisons types")
            if st.button("📋 Auditions", use_container_width=True):
                st.session_state.comparison_query = "Comparer toutes les auditions"
            if st.button("🔬 Expertises", use_container_width=True):
                st.session_state.comparison_query = "Comparer les rapports d'expertise"
            if st.button("📄 Versions", use_container_width=True):
                st.session_state.comparison_query = "Comparer les versions des documents"
        
        if query and st.button("🚀 Lancer la comparaison", type="primary", use_container_width=True):
            process_comparison_request(query, {'reference': query})
        
        if st.session_state.get('comparison_result'):
            st.markdown("---")
            st.markdown("### 📊 Résultats de la comparaison")
            from modules.comparison import display_comparison_results
            display_comparison_results(st.session_state.comparison_result)
            
except ImportError:
    modules_disponibles['comparison'] = False
    def show_comparison_page():
        st.error("Module comparison non disponible")

# Module de cartographie (mapping)
try:
    from modules.mapping import process_mapping_request
    modules_disponibles['mapping'] = True
except ImportError:
    modules_disponibles['mapping'] = False

# Module de synthèse
try:
    from modules.synthesis import show_page as show_synthesis_page
    modules_disponibles['synthesis'] = True
except ImportError:
    modules_disponibles['synthesis'] = False

# === 5. EXPORT ET COMMUNICATION ===
# Module unifié d'export (REMPLACE export_juridique)
try:
    from modules.export_manager import export_manager, ExportConfig
    modules_disponibles['export_manager'] = True
    print("✅ Module export_manager chargé")
except ImportError as e:
    modules_disponibles['export_manager'] = False
    print(f"❌ Module export_manager non disponible: {e}")

# Module Email
try:
    from modules.email import (
        process_email_request, 
        show_email_interface,
        prepare_and_send_document
    )
    modules_disponibles['email'] = True
    print("✅ Module email chargé")
    
    def show_email_page():
        """Page principale du module email"""
        show_email_interface()
        
except ImportError:
    modules_disponibles['email'] = False
    def show_email_page():
        st.error("Module email non disponible")

# === 6. PRÉPARATION ET SUPPORT CLIENT ===
# Module de préparation client
try:
    from modules.preparation_client import (
        show_page as show_preparation_page,
        process_preparation_client_request
    )
    modules_disponibles['preparation_client'] = True
    print("✅ Module preparation_client chargé")
except ImportError:
    modules_disponibles['preparation_client'] = False

# Module plaidoirie
try:
    from modules.plaidoirie import process_plaidoirie_request
    modules_disponibles['plaidoirie'] = True
except ImportError:
    modules_disponibles['plaidoirie'] = False

# === 7. CONFIGURATION ===
# Module de configuration
try:
    from modules.configuration import show_page as show_configuration_page
    modules_disponibles['configuration'] = True
    print("✅ Module configuration chargé")
except ImportError:
    modules_disponibles['configuration'] = False

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
        export_manager_ok = modules_disponibles.get('export_manager', False)
        recherche_unifiee_ok = modules_disponibles.get('recherche_analyse_unifiee', False)
        
        status_html = f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-top: 8px;">
            <span><span class="status-dot {'online' if azure_connected else 'offline'}"></span>Azure</span>
            <span><span class="status-dot {'online' if multi_ia else 'offline'}"></span>Multi-IA</span>
            <span><span class="status-dot {'online' if recherche_unifiee_ok else 'offline'}"></span>Recherche IA</span>
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
        st.session_state.current_view = 'recherche_analyse'

def show_modern_sidebar():
    """Affiche la sidebar moderne avec menu organisé et optimisé"""
    with st.sidebar:
        # Logo/Titre
        st.markdown("### 📚 Menu Principal")
        
        # Accueil
        if st.button("🏠 Accueil", use_container_width=True, 
                    type="primary" if st.session_state.get('current_view') == 'accueil' else "secondary"):
            st.session_state.current_view = 'accueil'
            st.session_state.current_module = None
        
        # Section Recherche & Analyse IA
        st.markdown("#### 🔍 Recherche & Analyse")
        
        if st.button("🤖 Recherche & Analyse IA", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'recherche_analyse_unifiee' else "secondary"):
            st.session_state.current_view = 'recherche_analyse'
            st.session_state.current_module = 'recherche_analyse_unifiee'
        
        if st.button("⚖️ Jurisprudence", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'jurisprudence' else "secondary"):
            st.session_state.current_view = 'jurisprudence'
            st.session_state.current_module = 'jurisprudence'
        
        if modules_disponibles.get('risques'):
            if st.button("⚠️ Analyse des risques", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'risques' else "secondary"):
                st.session_state.current_view = 'risques'
                st.session_state.current_module = 'risques'
        
        # Section Gestion documentaire
        st.markdown("#### 📁 Documents & Pièces")
        
        if st.button("📎 Gestion des pièces", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'pieces_manager' else "secondary"):
            st.session_state.current_view = 'pieces'
            st.session_state.current_module = 'pieces_manager'
        
        if st.button("📋 Liste des pièces", use_container_width=True,
                    type="primary" if st.session_state.get('current_view') == 'liste_pieces' else "secondary"):
            st.session_state.current_view = 'liste_pieces'
            st.session_state.current_module = 'pieces_manager'
            st.session_state.show_liste_pieces_view = True
        
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
        
        # Section Rédaction
        st.markdown("#### ✍️ Rédaction & Production")
        
        if st.button("✍️ Rédaction d'actes", use_container_width=True,
                    type="primary" if st.session_state.get('current_module') == 'redaction_unified' else "secondary"):
            st.session_state.current_view = 'redaction'
            st.session_state.current_module = 'redaction_unified'
        
        if modules_disponibles.get('generation_longue'):
            if st.button("📜 Documents longs", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'generation_longue' else "secondary"):
                st.session_state.current_view = 'generation_longue'
                st.session_state.current_module = 'generation_longue'
        
        # Section Visualisation & Analyse
        st.markdown("#### 📊 Visualisation")
        
        tools = [
            ("📅 Timeline", "timeline", "timeline"),
            ("🔄 Comparaison", "comparison", "comparison"),
            ("🗺️ Cartographie", "mapping", "mapping"),
            ("📊 Synthèse", "synthesis", "synthesis"),
        ]
        
        for label, view, module in tools:
            if modules_disponibles.get(module):
                if st.button(label, use_container_width=True,
                            type="primary" if st.session_state.get('current_module') == module else "secondary"):
                    st.session_state.current_view = view
                    st.session_state.current_module = module
        
        # Section Communication & Support
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
        
        if modules_disponibles.get('plaidoirie'):
            if st.button("🎤 Plaidoirie", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'plaidoirie' else "secondary"):
                st.session_state.current_view = 'plaidoirie'
                st.session_state.current_module = 'plaidoirie'
        
        # Section Configuration
        st.markdown("#### ⚙️ Configuration")
        
        if modules_disponibles.get('template'):
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
    st.markdown("## 🔍 Recherche Intelligente Universelle avec IA")
    st.markdown("Décrivez ce que vous voulez faire en langage naturel")
    
    query = st.text_area(
        "Votre requête",
        placeholder="Ex: J'ai besoin de préparer l'audience de demain pour l'affaire Martin...\n"
                   "Ou: Rédige une plainte pour abus de biens sociaux contre la société XYZ...\n"
                   "Ou: Analyse tous les documents concernant la corruption...\n"
                   "Ou: Créer une liste de pièces pour communiquer au tribunal...",
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
                "Rédige une plainte avec constitution de partie civile pour abus de biens sociaux de 50 pages",
                "Explore tous les documents du dossier VINCI",
                "Analyse les risques juridiques dans le dossier @VINCI2024",
                "Trouve la jurisprudence sur la corruption dans le secteur public",
                "Prépare une liste des pièces pour l'audience du 15 janvier",
                "Compare les témoignages de Martin et Dupont dans l'affaire ABC",
                "Import tous les documents PDF du dossier Dupont",
                "Créer une timeline des événements financiers",
                "Prépare mon client pour son audition de demain",
                "Créer une liste de communication des pièces pour le tribunal"
            ]
            import random
            st.session_state.universal_search = random.choice(examples)
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Workflows principaux réorganisés
    st.markdown("### 🎯 Workflows principaux")
    
    workflows = [
        {
            'icon': '🔍',
            'title': 'Recherche & Analyse',
            'description': 'Recherche IA, jurisprudence et analyse des risques',
            'modules': ['recherche_analyse_unifiee', 'jurisprudence', 'risques'],
            'primary': 'recherche_analyse_unifiee'
        },
        {
            'icon': '📁',
            'title': 'Gestion documentaire',
            'description': 'Import, organisation et liste des pièces',
            'modules': ['pieces_manager', 'import_export', 'dossier_penal'],
            'primary': 'pieces_manager'
        },
        {
            'icon': '✍️',
            'title': 'Rédaction & Production',
            'description': 'Rédaction d\'actes et documents longs',
            'modules': ['redaction_unified', 'generation_longue'],
            'primary': 'redaction_unified'
        },
        {
            'icon': '📊',
            'title': 'Visualisation & Export',
            'description': 'Timeline, comparaisons et exports',
            'modules': ['timeline', 'comparison', 'export_manager'],
            'primary': 'timeline'
        }
    ]
    
    cols = st.columns(4)
    for idx, workflow in enumerate(workflows):
        with cols[idx]:
            with st.container():
                st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
                st.markdown(f"#### {workflow['icon']} {workflow['title']}")
                st.markdown(workflow['description'])
                
                # Vérifier la disponibilité des modules
                available = sum(1 for m in workflow['modules'] if modules_disponibles.get(m, False))
                total = len(workflow['modules'])
                
                if available > 0:
                    st.caption(f"✅ {available}/{total} modules actifs")
                    if st.button("Commencer", key=f"start_{workflow['primary']}", use_container_width=True):
                        st.session_state.current_module = workflow['primary']
                        st.rerun()
                else:
                    st.caption(f"❌ Modules non disponibles")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Accès rapide aux modules (réorganisé et simplifié)
    st.markdown("### ⚡ Accès rapide aux fonctionnalités")
    
    # Nouvelle organisation par catégories optimisées
    categories = {
        "Intelligence Artificielle": [
            ("🤖", "Recherche & Analyse IA", "Recherche et analyse unifiées par IA", "recherche_analyse_unifiee"),
            ("⚖️", "Jurisprudence", "Base de jurisprudence avec vérification", "jurisprudence"),
            ("⚠️", "Risques", "Analyse des risques juridiques", "risques"),
            ("📊", "Synthèse", "Synthèse automatique", "synthesis"),
        ],
        "Documents & Dossiers": [
            ("📎", "Gestion des pièces", "Organisez vos pièces et créez des listes", "pieces_manager"),
            ("📥", "Import/Export", "Import/Export unifié de documents", "import_export"),
            ("📂", "Dossiers pénaux", "Gestion des dossiers", "dossier_penal"),
            ("🗂️", "Explorateur", "Explorez vos fichiers", "explorer"),
        ],
        "Production": [
            ("✍️", "Rédaction", "Rédaction d'actes juridiques avec IA", "redaction_unified"),
            ("📜", "Documents longs", "Documents de 25-50+ pages", "generation_longue"),
            ("📋", "Templates", "Gestion des modèles", "template"),
        ],
        "Analyse & Communication": [
            ("📅", "Timeline", "Chronologies visuelles", "timeline"),
            ("🔄", "Comparaison", "Comparez des documents", "comparison"),
            ("📧", "Emails", "Gestion des emails", "email"),
            ("👥", "Préparation client", "Préparez vos clients (audition, interrogatoire)", "preparation_client"),
        ]
    }
    
    for cat_name, modules in categories.items():
        st.markdown(f"#### {cat_name}")
        cols = st.columns(4)
        
        for idx, (icon, title, desc, module) in enumerate(modules):
            if modules_disponibles.get(module):
                with cols[idx % 4]:
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

# ========== SECTION 6: GESTION DE LA RECHERCHE UNIVERSELLE ==========

def handle_universal_search(query: str):
    """Traite la recherche universelle et redirige vers le bon module"""
    query_lower = query.lower()
    
    # Si le module recherche unifié est disponible, l'utiliser directement
    if modules_disponibles.get('recherche_analyse_unifiee'):
        st.session_state.current_view = 'recherche_analyse'
        st.session_state.current_module = 'recherche_analyse_unifiee'
        st.session_state.universal_search_query = query
        st.session_state.pending_query = query
        st.rerun()
        return
    
    # Sinon, utiliser l'analyse de patterns comme fallback
    patterns = {
        'import': {
            'keywords': ['import', 'importer', 'charger', 'upload', 'télécharger', 'ajouter des documents', 'pdf', 'xlsx', 'csv'],
            'module': 'import_export',
            'view': 'import_export'
        },
        'export': {
            'keywords': ['export', 'exporter', 'télécharger', 'sauvegarder', 'extraire', 'download', 'word', 'excel'],
            'module': 'import_export',
            'view': 'import_export',
            'context': 'export'
        },
        'timeline': {
            'keywords': ['timeline', 'chronologie', 'calendrier', 'événements', 'dates', 'temporel', 'historique'],
            'module': 'timeline',
            'view': 'timeline'
        },
        'comparison': {
            'keywords': ['comparer', 'comparaison', 'différence', 'confronter', 'analyser les divergences', 'témoignages'],
            'module': 'comparison',
            'view': 'comparison'
        },
        'email': {
            'keywords': ['email', 'mail', 'envoyer', 'courrier', 'correspondance', 'transmettre', 'destinataire'],
            'module': 'email',
            'view': 'email'
        },
        'pieces': {
            'keywords': ['pièce', 'document', 'fichier', 'gérer les pièces', 'organiser', 'sélectionner', 'sélection', 'communication'],
            'module': 'pieces_manager',
            'view': 'pieces'
        },
        'liste_pieces': {
            'keywords': ['liste des pièces', 'bordereau', 'communication des pièces', 'inventaire', 'liste de pièces'],
            'module': 'pieces_manager',
            'view': 'liste_pieces',
            'context': 'liste'
        },
        'redaction': {
            'keywords': ['rédiger', 'rédige', 'créer', 'générer', 'préparer', 'établir', 'plainte', 'conclusions', 'assignation'],
            'module': 'redaction_unified',
            'view': 'redaction'
        },
        'preparation': {
            'keywords': ['préparer', 'préparation', 'client', 'audition', 'interrogatoire', 'audience', 'rendez-vous'],
            'module': 'preparation_client',
            'view': 'preparation_client'
        },
        'jurisprudence': {
            'keywords': ['jurisprudence', 'arrêt', 'décision', 'cour de cassation', 'juridique', 'judilibre', 'légifrance'],
            'module': 'jurisprudence',
            'view': 'jurisprudence'
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
    
    # Cas spécial : documents longs
    if any(word in query_lower for word in ['50 pages', '40 pages', 'long', 'exhaustif']):
        best_match = {'module': 'generation_longue', 'view': 'generation_longue'}
        best_score = 10
    
    if best_match and best_score > 0:
        st.session_state.current_view = best_match['view']
        st.session_state.current_module = best_match['module']
        st.session_state.search_context = query
        if 'context' in best_match:
            st.session_state.module_context = best_match['context']
    else:
        # Par défaut, utiliser le module de recherche unifié
        st.session_state.current_view = 'recherche_analyse'
        st.session_state.current_module = 'recherche_analyse_unifiee'
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
        'recherche_analyse_unifiee': "🤖 Recherche & Analyse IA",
        'jurisprudence': "⚖️ Recherche de jurisprudence",
        'risques': "⚠️ Analyse des risques",
        'pieces_manager': "📎 Gestion des pièces",
        'import_export': "📥📤 Import/Export",
        'dossier_penal': "📂 Dossiers pénaux",
        'explorer': "🗂️ Explorateur de documents",
        'redaction_unified': "✍️ Rédaction d'actes juridiques",
        'generation_longue': "📜 Génération de documents longs",
        'template': "📋 Gestion des templates",
        'timeline': "📅 Timeline des événements",
        'comparison': "🔄 Comparaison de documents",
        'synthesis': "📊 Synthèse",
        'email': "📧 Gestion des emails",
        'preparation_client': "👥 Préparation client",
        'plaidoirie': "🎤 Plaidoirie",
        'mapping': "🗺️ Cartographie",
        'configuration': "⚙️ Configuration"
    }
    
    # Gérer les cas spéciaux pour pieces_manager
    if module == 'pieces_manager' and st.session_state.get('current_view') == 'liste_pieces':
        module_titles['pieces_manager'] = "📋 Liste des pièces"
    
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
        # === Modules de recherche et analyse ===
        if module == 'recherche_analyse_unifiee' and modules_disponibles.get('recherche_analyse_unifiee'):
            show_recherche_analyse_page()
            
        elif module == 'jurisprudence' and modules_disponibles.get('jurisprudence'):
            # Passer la requête si elle existe
            query = st.session_state.get('search_context', '')
            show_jurisprudence_interface(query)
            
        elif module == 'risques' and modules_disponibles.get('risques'):
            display_risques_interface()
            
        # === Modules de gestion documentaire ===
        elif module == 'pieces_manager' and modules_disponibles.get('pieces_manager'):
            # Vérifier si on doit afficher la vue liste des pièces
            if st.session_state.get('current_view') == 'liste_pieces' or st.session_state.get('show_liste_pieces_view'):
                # Créer une analyse factice si nécessaire
                analysis = st.session_state.get('current_analysis', {
                    'reference': '',
                    'client': '',
                    'adversaire': '',
                    'juridiction': '',
                    'action_type': 'liste_pieces'
                })
                process_liste_pieces_request("Créer une liste des pièces", analysis)
            else:
                display_pieces_interface()
            
        elif module == 'import_export' and modules_disponibles.get('import_export'):
            if 'show_import_export_tabs' in globals():
                show_import_export_tabs()
            elif 'show_import_export_interface' in globals():
                show_import_export_interface()
            else:
                show_import_interface()
            
        elif module == 'dossier_penal' and modules_disponibles.get('dossier_penal'):
            display_dossier_penal_interface()
            
        elif module == 'explorer' and modules_disponibles.get('explorer'):
            show_explorer_interface()
            
        # === Modules de rédaction ===
        elif module == 'redaction_unified' and modules_disponibles.get('redaction_unified'):
            show_redaction_unified()
            
        elif module == 'generation_longue' and modules_disponibles.get('generation_longue'):
            show_generation_longue_interface()
            
        elif module == 'template' and modules_disponibles.get('template'):
            show_template_manager()
            
        # === Modules de visualisation ===
        elif module == 'timeline' and modules_disponibles.get('timeline'):
            show_timeline_page()
            
        elif module == 'comparison' and modules_disponibles.get('comparison'):
            show_comparison_page()
            
        elif module == 'synthesis' and modules_disponibles.get('synthesis'):
            show_synthesis_page()
            
        elif module == 'mapping' and modules_disponibles.get('mapping'):
            query = st.text_input("Décrivez la cartographie souhaitée")
            if query:
                process_mapping_request(query, {})
                
        # === Modules de communication ===
        elif module == 'email' and modules_disponibles.get('email'):
            show_email_page()
            
        elif module == 'preparation_client' and modules_disponibles.get('preparation_client'):
            # Passer la requête si elle existe
            query = st.session_state.get('search_context', '')
            if query:
                process_preparation_client_request(query, {'query': query})
            else:
                show_preparation_page()
            
        elif module == 'plaidoirie' and modules_disponibles.get('plaidoirie'):
            st.markdown("## 🎤 Génération de plaidoirie")
            query = st.text_area(
                "Décrivez la plaidoirie souhaitée",
                placeholder="Ex: Plaidoirie pour la défense dans l'affaire d'abus de biens sociaux...",
                height=100
            )
            if query and st.button("🚀 Générer la plaidoirie", type="primary"):
                process_plaidoirie_request(query, {})
                
        # === Configuration ===
        elif module == 'configuration' and modules_disponibles.get('configuration'):
            show_configuration_page()
            
        else:
            st.error(f"Module {module} non disponible ou non reconnu")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement du module : {str(e)}")
        if app_config.debug:
            st.code(traceback.format_exc())
    finally:
        # Nettoyer les états temporaires
        if 'show_liste_pieces_view' in st.session_state:
            del st.session_state.show_liste_pieces_view

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
                st.write(f"- Export Manager: {'✅' if modules_disponibles.get('export_manager') else '❌'}")
                st.write(f"- Recherche IA unifiée: {'✅' if modules_disponibles.get('recherche_analyse_unifiee') else '❌'}")
                st.write(f"- Jurisprudence: {'✅' if modules_disponibles.get('jurisprudence') else '❌'}")
                st.write(f"- Préparation client: {'✅' if modules_disponibles.get('preparation_client') else '❌'}")
                st.write(f"- Rédaction unifiée: {'✅' if modules_disponibles.get('redaction_unified') else '❌'}")
                st.write(f"- Configurations: {'✅' if DOCUMENT_CONFIG_AVAILABLE else '❌'}")
                st.write(f"- Vue actuelle: {st.session_state.get('current_view', 'N/A')}")
                st.write(f"- Module actuel: {st.session_state.get('current_module', 'N/A')}")
                
                # Notes d'optimisation
                st.write("\n**Notes d'optimisation:**")
                st.success("""
                ✅ recherche_analyse_unifiee remplace recherche + analyse_ia
                ✅ redaction_unified remplace generation_juridique  
                ✅ import_export unifie import et export
                ✅ pieces_manager intègre maintenant la gestion ET les listes de pièces (ex-bordereau)
                ✅ jurisprudence avec API Judilibre/Légifrance
                ✅ preparation_client avec plans de séances détaillés
                """)
                
                # Signaler les redondances
                st.write("\n**🔍 Redondances détectées et résolues:**")
                st.info("""
                • **Bordereau + Pieces Manager** → Fusionnés dans pieces_manager
                  - La création de listes de pièces est maintenant intégrée
                  - Accès via "Gestion des pièces" ou "Liste des pièces"
                  
                • **Export dispersé** → Centralisé dans export_manager
                  - Tous les exports passent par le module unifié
                  - Formats: Word, PDF, Excel, JSON
                """)

# Point d'entrée
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("❌ Erreur critique")
        st.code(str(e))
        with st.expander("Détails complets"):
            st.code(traceback.format_exc())