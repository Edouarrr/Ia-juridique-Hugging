"""Application principale avec interface optimisée et navigation intelligente"""

import streamlit as st
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Tuple
import re
import sys
import os
import traceback
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IMPORTANT: Charger les variables d'environnement
load_dotenv()

print("=== DÉMARRAGE APPLICATION ===")
print(f"Azure Storage Connection: {'✅' if os.getenv('AZURE_STORAGE_CONNECTION_STRING') else '❌'}")
print(f"Azure Search Endpoint: {'✅' if os.getenv('AZURE_SEARCH_ENDPOINT') else '❌'}")

# Configuration de la page
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SECTION 1: IMPORTS CENTRALISÉS ==========

# Import des gestionnaires Azure
AZURE_AVAILABLE = False
AZURE_ERROR = None

try:
    import azure.search.documents
    import azure.storage.blob
    import azure.core
    from azure.core.exceptions import AzureError
    AZURE_AVAILABLE = True
    logger.info("✅ Modules Azure disponibles")
except ImportError as e:
    AZURE_ERROR = str(e)
    logger.warning(f"⚠️ Modules Azure non disponibles: {AZURE_ERROR}")

# Import de la configuration
try:
    from config.app_config import app_config, api_config
    CONFIG_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ config.app_config non trouvé")
    CONFIG_AVAILABLE = False
    class DefaultConfig:
        version = "2.0.0"
        debug = True
        max_file_size_mb = 10
        max_files_per_upload = 5
        enable_azure_storage = True
        enable_azure_search = True
        enable_multi_llm = True
        enable_email = True
    
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
        defaults = {
            'initialized': True,
            'search_history': [],
            'azure_documents': {},
            'imported_documents': {},
            'pieces_selectionnees': {},
            'azure_blob_manager': None,
            'azure_search_manager': None,
            'current_view': "accueil",
            'current_module': None,
            'workflow_active': None,
            'multi_ia_active': True,
            'theme': 'light',
            'user_preferences': {},
            'recent_actions': [],
            'favorites': []
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

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
    logger.warning("⚠️ models.dataclasses non disponible")

# ========== SECTION 2: DICTIONNAIRE DES MODULES ==========

# Structure unifiée pour tous les modules
MODULES_CONFIG = {
    # Gestion documentaire
    'pieces_manager': {
        'name': '📎 Gestion des pièces',
        'category': 'documents',
        'description': 'Importez, organisez et gérez vos pièces de procédure',
        'priority': 1,
        'keywords': ['pièce', 'document', 'fichier', 'import', 'organiser', 'classer']
    },
    'dossier_penal': {
        'name': '📂 Dossiers pénaux',
        'category': 'documents',
        'description': 'Gérez vos dossiers pénaux complets',
        'priority': 2,
        'keywords': ['dossier', 'pénal', 'affaire', 'procédure']
    },
    'import_export': {
        'name': '📥 Import/Export',
        'category': 'documents',
        'description': 'Importez et exportez vos documents',
        'priority': 3,
        'keywords': ['import', 'export', 'télécharger', 'uploader']
    },
    'explorer': {
        'name': '🗂️ Explorateur',
        'category': 'documents',
        'description': 'Explorez vos fichiers et documents',
        'priority': 4,
        'keywords': ['explorer', 'naviguer', 'parcourir', 'fichier']
    },
    
    # Recherche et analyse
    'recherche': {
        'name': '🔍 Recherche avancée',
        'category': 'analyse',
        'description': 'Recherche intelligente dans vos documents',
        'priority': 1,
        'keywords': ['rechercher', 'trouver', 'chercher', 'localiser']
    },
    'analyse_ia': {
        'name': '📊 Analyse IA',
        'category': 'analyse',
        'description': 'Analysez vos documents avec l\'IA',
        'priority': 2,
        'keywords': ['analyser', 'analyse', 'examiner', 'étudier', 'ia']
    },
    'jurisprudence': {
        'name': '⚖️ Jurisprudence',
        'category': 'analyse',
        'description': 'Recherche de jurisprudence pertinente',
        'priority': 3,
        'keywords': ['jurisprudence', 'arrêt', 'décision', 'cour', 'cassation']
    },
    'risques': {
        'name': '⚠️ Analyse des risques',
        'category': 'analyse',
        'description': 'Évaluez les risques juridiques',
        'priority': 4,
        'keywords': ['risque', 'danger', 'menace', 'vulnérabilité', 'évaluation']
    },
    
    # Génération et rédaction
    'redaction_unified': {
        'name': '✍️ Rédaction unifiée',
        'category': 'generation',
        'description': 'Rédigez tous vos actes juridiques',
        'priority': 1,
        'keywords': ['rédiger', 'rédige', 'créer', 'générer', 'préparer', 'plainte', 'conclusions']
    },
    'generation_juridique': {
        'name': '📝 Génération d\'actes',
        'category': 'generation',
        'description': 'Génération automatique d\'actes juridiques',
        'priority': 2,
        'keywords': ['générer', 'acte', 'automatique', 'modèle']
    },
    'generation_longue': {
        'name': '📜 Documents longs',
        'category': 'generation',
        'description': 'Génération de documents complexes',
        'priority': 3,
        'keywords': ['long', 'complexe', 'mémoire', 'rapport']
    },
    'plaidoirie': {
        'name': '🎭 Plaidoiries',
        'category': 'generation',
        'description': 'Préparez vos plaidoiries',
        'priority': 4,
        'keywords': ['plaidoirie', 'plaidoyer', 'audience', 'oral']
    },
    
    # Visualisation et outils
    'timeline': {
        'name': '📅 Timeline',
        'category': 'outils',
        'description': 'Chronologie des événements',
        'priority': 1,
        'keywords': ['chronologie', 'timeline', 'calendrier', 'dates', 'événements']
    },
    'comparison': {
        'name': '🔄 Comparaison',
        'category': 'outils',
        'description': 'Comparez vos documents',
        'priority': 2,
        'keywords': ['comparer', 'différence', 'comparaison', 'confronter']
    },
    'mapping': {
        'name': '🗺️ Cartographie',
        'category': 'outils',
        'description': 'Cartographiez vos relations',
        'priority': 3,
        'keywords': ['carte', 'mapping', 'relation', 'lien', 'réseau']
    },
    'synthesis': {
        'name': '📊 Synthèse',
        'category': 'outils',
        'description': 'Synthétisez vos informations',
        'priority': 4,
        'keywords': ['synthèse', 'résumé', 'condensé', 'essentiel']
    },
    
    # Communication
    'bordereau': {
        'name': '📋 Bordereau',
        'category': 'communication',
        'description': 'Créez vos bordereaux de communication',
        'priority': 1,
        'keywords': ['bordereau', 'communication', 'liste', 'pièces']
    },
    'email': {
        'name': '📧 Emails',
        'category': 'communication',
        'description': 'Gérez vos communications email',
        'priority': 2,
        'keywords': ['email', 'mail', 'courrier', 'envoyer', 'correspondance']
    },
    'preparation_client': {
        'name': '👥 Préparation client',
        'category': 'communication',
        'description': 'Préparez vos rendez-vous clients',
        'priority': 3,
        'keywords': ['client', 'rendez-vous', 'préparation', 'réunion']
    },
    
    # Configuration
    'configuration': {
        'name': '⚙️ Configuration',
        'category': 'system',
        'description': 'Paramètres de l\'application',
        'priority': 1,
        'keywords': ['paramètre', 'configuration', 'réglage', 'option']
    },
    'template': {
        'name': '📋 Templates',
        'category': 'system',
        'description': 'Gérez vos modèles',
        'priority': 2,
        'keywords': ['template', 'modèle', 'gabarit', 'patron']
    },
    'integration_juridique': {
        'name': '🔗 Intégrations',
        'category': 'system',
        'description': 'Intégrations avec services externes',
        'priority': 3,
        'keywords': ['intégration', 'api', 'connecteur', 'externe']
    }
}

# Import dynamique des modules
modules_disponibles = {}
modules_imports = {}

for module_id, config in MODULES_CONFIG.items():
    try:
        if module_id == 'pieces_manager':
            from modules.pieces_manager import PiecesManager, display_pieces_interface
            modules_imports[module_id] = display_pieces_interface
        elif module_id == 'dossier_penal':
            from modules.dossier_penal import display_dossier_penal_interface
            modules_imports[module_id] = display_dossier_penal_interface
        elif module_id == 'import_export':
            from modules.import_export import show_import_export_interface
            modules_imports[module_id] = show_import_export_interface
        elif module_id == 'explorer':
            from modules.explorer import show_explorer_interface
            modules_imports[module_id] = show_explorer_interface
        elif module_id == 'recherche':
            from modules.recherche import show_page as show_recherche_page
            modules_imports[module_id] = show_recherche_page
        elif module_id == 'analyse_ia':
            from modules.analyse_ia import show_page as show_analyse_ia
            modules_imports[module_id] = show_analyse_ia
        elif module_id == 'jurisprudence':
            from modules.jurisprudence import show_page as show_jurisprudence_page
            modules_imports[module_id] = show_jurisprudence_page
        elif module_id == 'risques':
            from modules.risques import display_risques_interface
            modules_imports[module_id] = display_risques_interface
        elif module_id == 'redaction_unified':
            from modules.redaction_unified import show_page as show_redaction_unified
            modules_imports[module_id] = show_redaction_unified
        elif module_id == 'generation_juridique':
            from modules.generation_juridique import show_page as show_generation
            modules_imports[module_id] = show_generation
        elif module_id == 'generation_longue':
            from modules.generation_longue import show_generation_longue_interface
            modules_imports[module_id] = show_generation_longue_interface
        elif module_id == 'plaidoirie':
            from modules.plaidoirie import process_plaidoirie_request, show_page as show_plaidoirie_page
            modules_imports[module_id] = show_plaidoirie_page if 'show_plaidoirie_page' in locals() else lambda: process_plaidoirie_request("", {})
        elif module_id == 'timeline':
            from modules.timeline import show_page as show_timeline_page
            modules_imports[module_id] = show_timeline_page
        elif module_id == 'comparison':
            from modules.comparison import show_page as show_comparison_page
            modules_imports[module_id] = show_comparison_page
        elif module_id == 'mapping':
            from modules.mapping import process_mapping_request, show_page as show_mapping_page
            modules_imports[module_id] = show_mapping_page if 'show_mapping_page' in locals() else lambda: process_mapping_request("", {})
        elif module_id == 'synthesis':
            from modules.synthesis import show_page as show_synthesis_page
            modules_imports[module_id] = show_synthesis_page
        elif module_id == 'bordereau':
            from modules.bordereau import show_page as show_bordereau_page
            modules_imports[module_id] = show_bordereau_page
        elif module_id == 'email':
            from modules.email import show_page as show_email_page
            modules_imports[module_id] = show_email_page
        elif module_id == 'preparation_client':
            from modules.preparation_client import show_page as show_preparation_page
            modules_imports[module_id] = show_preparation_page
        elif module_id == 'configuration':
            from modules.configuration import show_page as show_configuration_page
            modules_imports[module_id] = show_configuration_page
        elif module_id == 'template':
            from modules.template import show_template_manager
            modules_imports[module_id] = show_template_manager
        elif module_id == 'integration_juridique':
            from modules.integration_juridique import show_page as show_integration_page
            modules_imports[module_id] = show_integration_page
            
        modules_disponibles[module_id] = True
        logger.info(f"✅ Module {module_id} chargé")
    except ImportError as e:
        modules_disponibles[module_id] = False
        logger.warning(f"❌ Module {module_id} non disponible: {e}")

# ========== SECTION 3: STYLES CSS MODERNES ==========

def load_modern_css():
    """Charge les styles CSS modernes et adaptatifs"""
    st.markdown("""
    <style>
        /* === VARIABLES CSS === */
        :root {
            --primary-color: #1976d2;
            --primary-dark: #115293;
            --primary-light: #4fc3f7;
            --secondary-color: #667eea;
            --secondary-dark: #5a67d8;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --danger-color: #f44336;
            --info-color: #2196f3;
            
            --bg-primary: #ffffff;
            --bg-secondary: #f5f7fa;
            --bg-tertiary: #e8eaf6;
            
            --text-primary: #1a1f3a;
            --text-secondary: #666666;
            --text-tertiary: #999999;
            
            --border-color: #e0e0e0;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.12);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.16);
            
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
        }
        
        /* === RESET ET BASE === */
        .main {
            padding: 0;
            max-width: 100%;
            background: var(--bg-primary);
        }
        
        /* === HEADER PRINCIPAL === */
        .main-header {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 1.5rem 2rem;
            margin: -1rem -1rem 2rem -1rem;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 999;
        }
        
        .main-header h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        /* === SIDEBAR MODERNE === */
        section[data-testid="sidebar"] {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            padding-top: 2rem;
        }
        
        section[data-testid="sidebar"] .element-container {
            padding: 0 1rem;
        }
        
        /* === NAVIGATION CARDS === */
        .nav-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .nav-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            border-color: var(--primary-color);
        }
        
        .nav-card.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        /* === MODULE CARDS === */
        .module-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            height: 100%;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .module-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        
        .module-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        .module-card:hover::before {
            transform: scaleX(1);
        }
        
        /* === SEARCH HERO === */
        .search-hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            border-radius: var(--radius-xl);
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .search-hero::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 0.3; }
        }
        
        /* === WORKFLOW STEPS === */
        .workflow-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 2rem 0;
            position: relative;
        }
        
        .workflow-step {
            flex: 1;
            text-align: center;
            position: relative;
            z-index: 1;
        }
        
        .workflow-step-circle {
            width: 60px;
            height: 60px;
            margin: 0 auto 1rem;
            border-radius: 50%;
            background: var(--bg-tertiary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .workflow-step.active .workflow-step-circle {
            background: var(--primary-color);
            color: white;
            transform: scale(1.1);
            box-shadow: var(--shadow-md);
        }
        
        .workflow-step.completed .workflow-step-circle {
            background: var(--success-color);
            color: white;
        }
        
        .workflow-connector {
            position: absolute;
            top: 30px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--border-color);
            z-index: 0;
        }
        
        /* === QUICK ACTIONS === */
        .quick-action {
            background: var(--bg-secondary);
            border-radius: var(--radius-md);
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .quick-action:hover {
            background: var(--bg-tertiary);
            transform: translateY(-2px);
        }
        
        .quick-action-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        /* === STATUS INDICATORS === */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-badge.success {
            background: rgba(76, 175, 80, 0.1);
            color: var(--success-color);
        }
        
        .status-badge.warning {
            background: rgba(255, 152, 0, 0.1);
            color: var(--warning-color);
        }
        
        .status-badge.danger {
            background: rgba(244, 67, 54, 0.1);
            color: var(--danger-color);
        }
        
        /* === TOOLTIPS === */
        [data-tooltip] {
            position: relative;
        }
        
        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
            white-space: nowrap;
            margin-bottom: 0.5rem;
            opacity: 1;
            pointer-events: none;
            animation: fadeIn 0.3s ease;
        }
        
        /* === ANIMATIONS === */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        .slide-in {
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(-20px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        /* === RESPONSIVE === */
        @media (max-width: 768px) {
            .workflow-container {
                flex-direction: column;
                gap: 2rem;
            }
            
            .workflow-connector {
                display: none;
            }
            
            .main-header {
                padding: 1rem;
            }
            
            .main-header h1 {
                font-size: 1.5rem;
            }
            
            .search-hero {
                padding: 2rem 1rem;
            }
        }
        
        /* === DARK MODE === */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #1a1f3a;
                --bg-secondary: #232841;
                --bg-tertiary: #2d3250;
                --text-primary: #ffffff;
                --text-secondary: #b0b7c3;
                --text-tertiary: #8892a0;
                --border-color: #3a4159;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# ========== SECTION 4: GESTIONNAIRES AZURE ==========

def init_azure_managers():
    """Initialise les gestionnaires Azure avec gestion d'erreurs robuste"""
    
    if not AZURE_AVAILABLE:
        logger.warning(f"⚠️ Azure non disponible: {AZURE_ERROR}")
        st.session_state.azure_blob_manager = None
        st.session_state.azure_search_manager = None
        st.session_state.azure_status = {
            'blob': {'connected': False, 'error': AZURE_ERROR},
            'search': {'connected': False, 'error': AZURE_ERROR}
        }
        return
    
    # Initialiser le statut
    if 'azure_status' not in st.session_state:
        st.session_state.azure_status = {
            'blob': {'connected': False, 'error': None},
            'search': {'connected': False, 'error': None}
        }
    
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state or st.session_state.azure_blob_manager is None:
        try:
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                raise ValueError("AZURE_STORAGE_CONNECTION_STRING non définie")
                
            from managers.azure_blob_manager import AzureBlobManager
            manager = AzureBlobManager()
            
            # Test de connexion
            try:
                manager.container_client.exists()
                st.session_state.azure_blob_manager = manager
                st.session_state.azure_status['blob'] = {'connected': True, 'error': None}
                logger.info("✅ Azure Blob connecté")
            except Exception as e:
                st.session_state.azure_blob_manager = None
                st.session_state.azure_status['blob'] = {'connected': False, 'error': f"Erreur de connexion: {str(e)}"}
                logger.error(f"❌ Erreur connexion Azure Blob: {e}")
                
        except Exception as e:
            logger.error(f"❌ Erreur Azure Blob Manager: {e}")
            st.session_state.azure_blob_manager = None
            st.session_state.azure_status['blob'] = {'connected': False, 'error': str(e)}
    
    # Azure Search Manager  
    if 'azure_search_manager' not in st.session_state or st.session_state.azure_search_manager is None:
        try:
            endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            key = os.getenv('AZURE_SEARCH_KEY')
            
            if not endpoint or not key:
                raise ValueError("AZURE_SEARCH_ENDPOINT ou AZURE_SEARCH_KEY non définis")
                
            from managers.azure_search_manager import AzureSearchManager
            manager = AzureSearchManager()
            
            # Test de connexion
            try:
                # Vérifier que l'index existe
                manager.search_client.search("test", search_mode="all", top=1)
                st.session_state.azure_search_manager = manager
                st.session_state.azure_status['search'] = {'connected': True, 'error': None}
                logger.info("✅ Azure Search connecté")
            except Exception as e:
                st.session_state.azure_search_manager = None
                st.session_state.azure_status['search'] = {'connected': False, 'error': f"Erreur de connexion: {str(e)}"}
                logger.error(f"❌ Erreur connexion Azure Search: {e}")
                
        except Exception as e:
            logger.error(f"❌ Erreur Azure Search Manager: {e}")
            st.session_state.azure_search_manager = None
            st.session_state.azure_status['search'] = {'connected': False, 'error': str(e)}

# ========== SECTION 5: NAVIGATION ET INTERFACE ==========

def show_header_with_status():
    """Affiche l'en-tête avec indicateurs de statut"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        st.markdown("# ⚖️ Assistant Juridique IA")
    
    with col2:
        # Statut des services
        azure_blob_status = st.session_state.get('azure_status', {}).get('blob', {}).get('connected', False)
        azure_search_status = st.session_state.get('azure_status', {}).get('search', {}).get('connected', False)
        multi_ia_status = st.session_state.get('multi_ia_active', False)
        
        status_html = f"""
        <div style="display: flex; gap: 1rem; align-items: center; margin-top: 8px;">
            <span class="status-badge {'success' if azure_blob_status else 'danger'}">
                {'✅' if azure_blob_status else '❌'} Stockage
            </span>
            <span class="status-badge {'success' if azure_search_status else 'danger'}">
                {'✅' if azure_search_status else '❌'} Recherche
            </span>
            <span class="status-badge {'success' if multi_ia_status else 'warning'}">
                {'✅' if multi_ia_status else '⚠️'} Multi-IA
            </span>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    
    with col3:
        # Actions rapides
        cols = st.columns(3)
        with cols[0]:
            if st.button("🔄", help="Rafraîchir", use_container_width=True):
                st.rerun()
        with cols[1]:
            if st.button("❓", help="Aide", use_container_width=True):
                st.session_state.show_help = True
        with cols[2]:
            if st.button("⚙️", help="Configuration", use_container_width=True):
                st.session_state.current_module = 'configuration'
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_sidebar_navigation():
    """Affiche la navigation sidebar organisée par catégories"""
    with st.sidebar:
        # Logo et titre
        st.markdown("## 📚 Navigation")
        
        # Bouton Accueil
        if st.button("🏠 Accueil", use_container_width=True, 
                    type="primary" if st.session_state.get('current_view') == 'accueil' else "secondary"):
            st.session_state.current_view = 'accueil'
            st.session_state.current_module = None
            st.rerun()
        
        st.markdown("---")
        
        # Grouper les modules par catégorie
        categories = {
            'documents': '📁 Gestion documentaire',
            'analyse': '🔍 Recherche & Analyse',
            'generation': '✍️ Génération & Rédaction',
            'outils': '🛠️ Outils & Visualisation',
            'communication': '📧 Communication',
            'system': '⚙️ Configuration'
        }
        
        for cat_id, cat_name in categories.items():
            # Récupérer les modules de cette catégorie
            cat_modules = [
                (mod_id, mod_config) 
                for mod_id, mod_config in MODULES_CONFIG.items() 
                if mod_config['category'] == cat_id and modules_disponibles.get(mod_id, False)
            ]
            
            if cat_modules:
                st.markdown(f"### {cat_name}")
                
                # Trier par priorité
                cat_modules.sort(key=lambda x: x[1]['priority'])
                
                for mod_id, mod_config in cat_modules:
                    button_type = "primary" if st.session_state.get('current_module') == mod_id else "secondary"
                    
                    if st.button(mod_config['name'], 
                               use_container_width=True,
                               type=button_type,
                               help=mod_config['description']):
                        st.session_state.current_module = mod_id
                        st.session_state.current_view = 'module'
                        st.rerun()
        
        # Section d'aide
        st.markdown("---")
        st.markdown("### 💡 Aide rapide")
        st.info("""
        **Raccourcis:**
        - 🔍 Recherche universelle
        - 📎 Glisser-déposer de fichiers
        - ⌨️ Ctrl+K : Recherche rapide
        """)
        
        # Favoris
        if st.session_state.get('favorites'):
            st.markdown("### ⭐ Favoris")
            for fav in st.session_state.favorites:
                if st.button(f"⭐ {fav['name']}", use_container_width=True):
                    st.session_state.current_module = fav['module']
                    st.rerun()

def show_search_hero():
    """Affiche le hero de recherche universelle"""
    st.markdown('<div class="search-hero fade-in">', unsafe_allow_html=True)
    st.markdown("## 🔍 Recherche Intelligente Universelle")
    st.markdown("### Décrivez votre besoin en langage naturel")
    
    # Suggestions contextuelles
    suggestions = get_contextual_suggestions()
    if suggestions:
        st.markdown("**Suggestions basées sur votre activité récente:**")
        cols = st.columns(len(suggestions[:3]))
        for idx, suggestion in enumerate(suggestions[:3]):
            with cols[idx]:
                if st.button(suggestion, use_container_width=True):
                    st.session_state.universal_search = suggestion
                    st.rerun()
    
    # Zone de recherche
    query = st.text_area(
        "Votre requête",
        placeholder="Ex: J'ai besoin de préparer l'audience de demain pour l'affaire Martin...\n"
                   "Ou: Rédige une plainte pour abus de biens sociaux...\n"
                   "Ou: Analyse les risques dans le dossier XYZ...",
        height=120,
        key="universal_search",
        label_visibility="collapsed"
    )
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        search_clicked = st.button("🔍 Rechercher", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🎲 Exemple aléatoire", use_container_width=True):
            examples = [
                "Rédige une plainte avec constitution de partie civile pour abus de biens sociaux contre la société ABC",
                "Analyse les risques juridiques dans tous les documents du dossier VINCI-2024",
                "Trouve toute la jurisprudence pertinente sur la corruption d'agent public",
                "Prépare un bordereau de communication pour l'audience du 15 janvier 2025",
                "Compare les dépositions des témoins Martin et Dupont dans l'affaire XYZ",
                "Génère une synthèse de tous les éléments à charge dans le dossier",
                "Crée une timeline des événements basée sur les documents disponibles",
                "Prépare les questions pour l'interrogatoire du témoin principal"
            ]
            import random
            st.session_state.universal_search = random.choice(examples)
            st.rerun()
    
    with col3:
        if st.button("📋 Utiliser un template", use_container_width=True):
            st.session_state.show_templates = True
    
    with col4:
        if st.button("🎤 Dictée vocale", use_container_width=True):
            st.info("Fonction de dictée vocale bientôt disponible")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Traiter la recherche
    if search_clicked and query:
        handle_universal_search(query)

def get_contextual_suggestions() -> List[str]:
    """Génère des suggestions basées sur l'historique et le contexte"""
    suggestions = []
    
    # Basé sur les actions récentes
    recent_actions = st.session_state.get('recent_actions', [])
    if recent_actions:
        last_action = recent_actions[-1]
        if last_action.get('type') == 'document_upload':
            suggestions.append(f"Analyser le document {last_action.get('name', 'récent')}")
        elif last_action.get('type') == 'search':
            suggestions.append(f"Approfondir la recherche sur {last_action.get('query', '')}")
    
    # Basé sur les pièces sélectionnées
    if st.session_state.get('pieces_selectionnees'):
        suggestions.append("Créer un bordereau avec les pièces sélectionnées")
        suggestions.append("Analyser les risques dans les pièces sélectionnées")
    
    # Suggestions générales contextuelles
    current_hour = datetime.now().hour
    if 8 <= current_hour < 12:
        suggestions.append("Préparer le planning de la journée")
    elif 14 <= current_hour < 18:
        suggestions.append("Faire le point sur les dossiers en cours")
    
    return suggestions[:3]  # Limiter à 3 suggestions

def handle_universal_search(query: str):
    """Traite la recherche universelle avec IA améliorée"""
    query_lower = query.lower()
    
    # Analyse améliorée de l'intention avec score
    intentions = analyze_search_intent(query_lower)
    
    # Prendre la meilleure intention
    best_intent = max(intentions.items(), key=lambda x: x[1]['score'])
    
    if best_intent[1]['score'] > 0.5:  # Seuil de confiance
        module_id = best_intent[1]['module']
        st.session_state.current_module = module_id
        st.session_state.current_view = 'module'
        st.session_state.search_context = query
        
        # Ajouter à l'historique
        add_to_recent_actions({
            'type': 'search',
            'query': query,
            'module': module_id,
            'timestamp': datetime.now()
        })
    else:
        # Si aucune intention claire, utiliser le module de recherche
        st.session_state.current_module = 'recherche'
        st.session_state.current_view = 'module'
        st.session_state.search_query = query
    
    st.rerun()

def analyze_search_intent(query: str) -> Dict[str, Dict]:
    """Analyse l'intention de recherche avec scoring intelligent"""
    intentions = {}
    
    for module_id, config in MODULES_CONFIG.items():
        score = 0
        keywords = config.get('keywords', [])
        
        # Score basé sur les mots-clés
        for keyword in keywords:
            if keyword in query:
                score += 1
                # Bonus si le mot-clé est au début
                if query.startswith(keyword):
                    score += 0.5
        
        # Normaliser le score
        if keywords:
            score = score / len(keywords)
        
        intentions[module_id] = {
            'score': score,
            'module': module_id
        }
    
    return intentions

def add_to_recent_actions(action: Dict):
    """Ajoute une action à l'historique récent"""
    if 'recent_actions' not in st.session_state:
        st.session_state.recent_actions = []
    
    st.session_state.recent_actions.append(action)
    
    # Garder seulement les 20 dernières actions
    st.session_state.recent_actions = st.session_state.recent_actions[-20:]

# ========== SECTION 6: AFFICHAGE DES MODULES ==========

def show_module_content():
    """Affiche le contenu du module actuel avec navigation améliorée"""
    module_id = st.session_state.get('current_module')
    
    if not module_id or module_id not in modules_disponibles:
        return
    
    # Header du module avec navigation
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col1:
        if st.button("← Retour", use_container_width=True):
            st.session_state.current_module = None
            st.session_state.current_view = 'accueil'
            st.rerun()
    
    with col2:
        module_config = MODULES_CONFIG.get(module_id, {})
        st.markdown(f"## {module_config.get('name', module_id)}")
        st.markdown(f"*{module_config.get('description', '')}*")
    
    with col3:
        # Ajouter aux favoris
        is_favorite = any(fav['module'] == module_id for fav in st.session_state.get('favorites', []))
        if st.button("⭐" if is_favorite else "☆", 
                    help="Retirer des favoris" if is_favorite else "Ajouter aux favoris",
                    use_container_width=True):
            toggle_favorite(module_id)
            st.rerun()
    
    # Barre de progression si workflow
    if st.session_state.get('workflow_active'):
        show_workflow_progress()
    
    # Contenu du module
    st.markdown("---")
    
    try:
        # Appeler la fonction du module
        if module_id in modules_imports:
            modules_imports[module_id]()
        else:
            st.error(f"Module {module_id} non trouvé dans les imports")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement du module : {str(e)}")
        if app_config.debug:
            with st.expander("Détails de l'erreur"):
                st.code(traceback.format_exc())

def toggle_favorite(module_id: str):
    """Ajoute ou retire un module des favoris"""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    # Vérifier si déjà favori
    existing = next((fav for fav in st.session_state.favorites if fav['module'] == module_id), None)
    
    if existing:
        st.session_state.favorites.remove(existing)
    else:
        module_config = MODULES_CONFIG.get(module_id, {})
        st.session_state.favorites.append({
            'module': module_id,
            'name': module_config.get('name', module_id)
        })

def show_workflow_progress():
    """Affiche la progression du workflow actif"""
    workflow = st.session_state.get('workflow_active')
    if not workflow:
        return
    
    st.markdown('<div class="workflow-container">', unsafe_allow_html=True)
    st.markdown('<div class="workflow-connector"></div>', unsafe_allow_html=True)
    
    cols = st.columns(len(workflow['steps']))
    
    for idx, step in enumerate(workflow['steps']):
        with cols[idx]:
            status = "active" if idx == workflow['current'] else "completed" if idx < workflow['current'] else ""
            
            st.markdown(f'''
            <div class="workflow-step {status}">
                <div class="workflow-step-circle">{step['icon']}</div>
                <div>{step['name']}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== SECTION 7: PAGE D'ACCUEIL ==========

def show_home_page():
    """Page d'accueil avec workflows et accès rapide"""
    
    # Hero de recherche
    show_search_hero()
    
    # Workflows recommandés
    st.markdown("## 🎯 Workflows recommandés")
    
    workflows = [
        {
            'id': 'preparation_audience',
            'name': '⚖️ Préparer une audience',
            'description': 'Workflow complet pour préparer efficacement votre prochaine audience',
            'steps': ['Importer les pièces', 'Analyser le dossier', 'Préparer les arguments', 'Créer le bordereau'],
            'modules': ['pieces_manager', 'analyse_ia', 'plaidoirie', 'bordereau']
        },
        {
            'id': 'redaction_acte',
            'name': '✍️ Rédiger un acte',
            'description': 'Assistant de rédaction pour tous vos actes juridiques',
            'steps': ['Choisir le type', 'Renseigner les infos', 'Générer le document', 'Réviser et finaliser'],
            'modules': ['redaction_unified']
        },
        {
            'id': 'analyse_dossier',
            'name': '📊 Analyser un dossier',
            'description': 'Analyse complète avec identification des risques et opportunités',
            'steps': ['Importer documents', 'Analyse IA', 'Risques juridiques', 'Synthèse'],
            'modules': ['pieces_manager', 'analyse_ia', 'risques', 'synthesis']
        }
    ]
    
    cols = st.columns(3)
    for idx, workflow in enumerate(workflows):
        with cols[idx]:
            with st.container():
                st.markdown(f"### {workflow['name']}")
                st.markdown(workflow['description'])
                st.markdown(f"**Étapes:** {len(workflow['steps'])}")
                
                if st.button(f"Démarrer", key=f"workflow_{workflow['id']}", use_container_width=True):
                    start_workflow(workflow)
                    st.rerun()
    
    # Accès rapide aux modules favoris
    if st.session_state.get('favorites'):
        st.markdown("## ⭐ Vos favoris")
        cols = st.columns(4)
        for idx, fav in enumerate(st.session_state.favorites):
            with cols[idx % 4]:
                if st.button(fav['name'], key=f"fav_{idx}", use_container_width=True):
                    st.session_state.current_module = fav['module']
                    st.session_state.current_view = 'module'
                    st.rerun()
    
    # Statistiques et aperçu
    st.markdown("## 📈 Tableau de bord")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pieces_count = len(st.session_state.get('pieces_selectionnees', {}))
        st.metric("📎 Pièces", pieces_count)
    
    with col2:
        docs_count = len(st.session_state.get('azure_documents', {}))
        st.metric("📄 Documents", docs_count)
    
    with col3:
        searches_count = len(st.session_state.get('search_history', []))
        st.metric("🔍 Recherches", searches_count)
    
    with col4:
        actions_count = len(st.session_state.get('recent_actions', []))
        st.metric("⚡ Actions récentes", actions_count)
    
    # Actions récentes
    if st.session_state.get('recent_actions'):
        st.markdown("### ⏱️ Actions récentes")
        
        recent = st.session_state.recent_actions[-5:][::-1]  # 5 dernières, inversées
        
        for action in recent:
            col1, col2 = st.columns([4, 1])
            with col1:
                action_type = action.get('type', 'unknown')
                action_desc = {
                    'search': f"🔍 Recherche: {action.get('query', 'N/A')}",
                    'document_upload': f"📎 Upload: {action.get('name', 'N/A')}",
                    'module_access': f"📱 Module: {action.get('module', 'N/A')}",
                }.get(action_type, f"❓ {action_type}")
                
                st.write(action_desc)
            
            with col2:
                timestamp = action.get('timestamp', datetime.now())
                if isinstance(timestamp, datetime):
                    st.caption(timestamp.strftime("%H:%M"))

def start_workflow(workflow: Dict):
    """Démarre un workflow guidé"""
    st.session_state.workflow_active = {
        'id': workflow['id'],
        'name': workflow['name'],
        'steps': [
            {'name': step, 'icon': '📝'} 
            for step in workflow['steps']
        ],
        'modules': workflow['modules'],
        'current': 0
    }
    
    # Aller au premier module du workflow
    if workflow['modules']:
        st.session_state.current_module = workflow['modules'][0]
        st.session_state.current_view = 'module'

# ========== SECTION 8: FONCTION PRINCIPALE ==========

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    initialize_session_state()
    load_modern_css()
    
    # Initialiser Azure
    init_azure_managers()
    
    # Header avec statut
    show_header_with_status()
    
    # Layout principal
    show_sidebar_navigation()
    
    # Contenu principal
    if st.session_state.get('current_view') == 'accueil':
        show_home_page()
    elif st.session_state.get('current_view') == 'module':
        show_module_content()
    
    # Modal d'aide si demandée
    if st.session_state.get('show_help'):
        show_help_modal()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        st.caption(f"© 2024 Assistant Juridique IA v{app_config.version} | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Mode debug (caché)
    with st.expander("🔧 Mode développeur", expanded=False):
        show_debug_info()

def show_help_modal():
    """Affiche une modal d'aide contextuelle"""
    with st.container():
        st.markdown("## 💡 Aide")
        
        tabs = st.tabs(["Démarrage rapide", "Fonctionnalités", "Raccourcis", "Support"])
        
        with tabs[0]:
            st.markdown("""
            ### 🚀 Démarrage rapide
            
            1. **Recherche universelle** : Décrivez votre besoin en langage naturel
            2. **Workflows guidés** : Suivez les étapes recommandées
            3. **Modules directs** : Accédez directement via la sidebar
            
            ### 💡 Conseils
            - Utilisez des termes juridiques précis pour de meilleurs résultats
            - Sauvegardez vos documents importants dans Azure
            - Utilisez les favoris pour un accès rapide
            """)
        
        with tabs[1]:
            st.markdown("""
            ### 📋 Fonctionnalités principales
            
            - **Gestion documentaire** : Import, classification, recherche
            - **Analyse IA** : Extraction d'informations, résumés, risques
            - **Génération** : Actes, conclusions, courriers
            - **Collaboration** : Partage, annotations, versions
            """)
        
        with tabs[2]:
            st.markdown("""
            ### ⌨️ Raccourcis clavier
            
            - `Ctrl+K` : Recherche rapide
            - `Ctrl+N` : Nouveau document
            - `Ctrl+S` : Sauvegarder
            - `Esc` : Fermer les modals
            """)
        
        with tabs[3]:
            st.markdown("""
            ### 🆘 Support
            
            - Email : support@assistant-juridique.ai
            - Documentation : [docs.assistant-juridique.ai](https://docs.assistant-juridique.ai)
            - FAQ : [faq.assistant-juridique.ai](https://faq.assistant-juridique.ai)
            """)
        
        if st.button("Fermer", use_container_width=True):
            st.session_state.show_help = False
            st.rerun()

def show_debug_info():
    """Affiche les informations de debug"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 État système")
        
        # Services
        services = {
            'Azure Blob': st.session_state.get('azure_status', {}).get('blob', {}).get('connected', False),
            'Azure Search': st.session_state.get('azure_status', {}).get('search', {}).get('connected', False),
            'Multi-IA': st.session_state.get('multi_ia_active', False),
            'Config': CONFIG_AVAILABLE,
            'Utils': UTILS_AVAILABLE
        }
        
        for service, status in services.items():
            st.write(f"{'✅' if status else '❌'} {service}")
        
        # Modules
        st.markdown("### 📦 Modules")
        available = sum(1 for v in modules_disponibles.values() if v)
        st.metric("Modules actifs", f"{available}/{len(modules_disponibles)}")
        
        # Détails des modules
        with st.expander("Détails des modules"):
            for module_id, available in sorted(modules_disponibles.items()):
                config = MODULES_CONFIG.get(module_id, {})
                st.write(f"{'✅' if available else '❌'} {config.get('name', module_id)}")
    
    with col2:
        st.markdown("### 🔧 Configuration")
        
        # Variables d'environnement
        env_vars = {
            'AZURE_STORAGE_CONNECTION_STRING': bool(os.getenv('AZURE_STORAGE_CONNECTION_STRING')),
            'AZURE_SEARCH_ENDPOINT': bool(os.getenv('AZURE_SEARCH_ENDPOINT')),
            'AZURE_SEARCH_KEY': bool(os.getenv('AZURE_SEARCH_KEY')),
            'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
            'ANTHROPIC_API_KEY': bool(os.getenv('ANTHROPIC_API_KEY'))
        }
        
        st.markdown("**Variables d'environnement:**")
        for var, exists in env_vars.items():
            st.write(f"{'✅' if exists else '❌'} {var}")
        
        # Session state
        st.markdown("### 💾 Session State")
        state_info = {
            'Vue actuelle': st.session_state.get('current_view', 'N/A'),
            'Module actuel': st.session_state.get('current_module', 'N/A'),
            'Workflow actif': bool(st.session_state.get('workflow_active')),
            'Pièces sélectionnées': len(st.session_state.get('pieces_selectionnees', {})),
            'Documents Azure': len(st.session_state.get('azure_documents', {})),
            'Historique recherche': len(st.session_state.get('search_history', []))
        }
        
        for key, value in state_info.items():
            st.write(f"**{key}:** {value}")
    
    # Logs en temps réel
    if st.checkbox("Afficher les logs en temps réel"):
        log_container = st.empty()
        # Ici vous pourriez implémenter un système de logs en temps réel

# ========== POINT D'ENTRÉE ==========

if __name__ == "__main__":
    try:
        # Définir le niveau de log selon le mode debug
        if hasattr(app_config, 'debug') and app_config.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        main()
        
    except Exception as e:
        st.error("❌ Erreur critique dans l'application")
        st.error(str(e))
        
        if hasattr(app_config, 'debug') and app_config.debug:
            st.markdown("### Traceback complet:")
            st.code(traceback.format_exc())
        
        # Proposer des actions de récupération
        st.markdown("### 🔧 Actions de récupération")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Recharger", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Réinitialiser session", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.button("📧 Signaler", use_container_width=True):
                st.info("Envoyez le rapport d'erreur à support@assistant-juridique.ai")