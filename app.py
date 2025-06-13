# app.py
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

# ========== SECTION 2: GESTIONNAIRES AZURE ==========

def init_azure_managers():
    """Initialise les gestionnaires Azure si disponibles"""
    if not AZURE_AVAILABLE:
        return
    
    # Azure Blob Manager
    if app_config.enable_azure_storage and 'azure_blob_manager' not in st.session_state:
        try:
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
            print("✅ Azure Blob Manager initialisé")
        except Exception as e:
            print(f"❌ Erreur Azure Blob Manager: {e}")
    
    # Azure Search Manager
    if app_config.enable_azure_search and 'azure_search_manager' not in st.session_state:
        try:
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
            print("✅ Azure Search Manager initialisé")
        except Exception as e:
            print(f"❌ Erreur Azure Search Manager: {e}")

# ========== SECTION 3: IMPORTS DES MODULES ==========

# Dictionnaire pour tracker la disponibilité des modules
modules_disponibles = {}

# === 1. MODULES DE BASE ===
# Module de configuration
try:
    from modules.configuration import show_configuration_page
    modules_disponibles['configuration'] = True
except ImportError:
    modules_disponibles['configuration'] = False

# Module export manager
try:
    from managers.export_manager import ExportManager
    modules_disponibles['export_manager'] = True
    print("✅ Export Manager disponible")
except ImportError:
    modules_disponibles['export_manager'] = False
    print("⚠️ Export Manager non disponible")

# === 2. RECHERCHE ET ANALYSE ===
# Module de recherche et analyse unifié (REMPLACE recherche + analyse_ia)
try:
    from modules.recherche_analyse_unifiee import (
        show_recherche_analyse_page,
        process_search_analysis_query
    )
    modules_disponibles['recherche_analyse_unifiee'] = True
    print("✅ Module recherche_analyse_unifiee chargé")
except ImportError:
    modules_disponibles['recherche_analyse_unifiee'] = False
    print("❌ Module recherche_analyse_unifiee non disponible")

# Module de jurisprudence
try:
    from modules.jurisprudence import (
        show_jurisprudence_interface,
        process_jurisprudence_request
    )
    modules_disponibles['jurisprudence'] = True
    print("✅ Module jurisprudence chargé")
except ImportError:
    modules_disponibles['jurisprudence'] = False

# Module d'analyse des risques
try:
    from modules.risques import display_risques_interface
    modules_disponibles['risques'] = True
    print("✅ Module risques chargé")
except ImportError:
    modules_disponibles['risques'] = False

# === GESTION DOCUMENTAIRE ===
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

# === 4. VISUALISATION ET ANALYSE ===
# Module timeline
try:
    from modules.timeline import show_timeline_page, process_timeline_request
    modules_disponibles['timeline'] = True
    print("✅ Module timeline chargé")
except ImportError:
    modules_disponibles['timeline'] = False

# Module comparison
try:
    from modules.comparison import show_comparison_page
    modules_disponibles['comparison'] = True
except ImportError:
    modules_disponibles['comparison'] = False

# Module synthesis
try:
    from modules.synthesis import show_synthesis_page
    modules_disponibles['synthesis'] = True
except ImportError:
    modules_disponibles['synthesis'] = False

# Module mapping
try:
    from modules.mapping import process_mapping_request
    modules_disponibles['mapping'] = True
except ImportError:
    modules_disponibles['mapping'] = False

# === 5. COMMUNICATION ET COLLABORATION ===
# Module email
try:
    from modules.email import show_email_page
    modules_disponibles['email'] = True
except ImportError:
    modules_disponibles['email'] = False

# Module preparation client
try:
    from modules.preparation_client import (
        show_preparation_page,
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

print(f"\n📊 Modules chargés : {sum(1 for v in modules_disponibles.values() if v)}/{len(modules_disponibles)}")

# ========== SECTION 4: STYLES CSS ==========

def load_custom_css():
    """Charge les styles CSS personnalisés"""
    st.markdown("""
    <style>
    /* Navigation moderne */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 20px;
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"][data-selected="true"] {
        background-color: #1e40af;
        color: white;
        border-color: #1e40af;
    }
    
    /* Boutons modernes */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Cards et containers */
    div[data-testid="stExpander"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* Métriques améliorées */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Sidebar moderne */
    .css-1d391kg {
        background-color: #1e293b;
    }
    
    .css-1d391kg .stButton > button {
        width: 100%;
        background-color: transparent;
        border: 1px solid #475569;
        color: white;
    }
    
    .css-1d391kg .stButton > button:hover {
        background-color: #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# ========== SECTION 5: NAVIGATION ==========

def show_modern_navigation():
    """Affiche la navigation principale moderne"""
    
    # Header avec logo et infos
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col1:
        st.markdown("⚖️", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <h1 style='text-align: center; margin: 0; font-size: 2rem;'>
        Assistant Pénal des Affaires IA
        </h1>
        """, unsafe_allow_html=True)
    
    with col3:
        # Menu utilisateur
        if st.button("👤", help="Profil utilisateur"):
            st.session_state.show_profile = not st.session_state.get('show_profile', False)
    
    # Barre de recherche universelle
    search_container = st.container()
    with search_container:
        col1, col2 = st.columns([10, 1])
        
        with col1:
            query = st.text_input(
                "",
                placeholder="🔍 Recherchez une jurisprudence, analysez un document, créez un acte...",
                key="universal_search",
                label_visibility="collapsed"
            )
        
        with col2:
            if st.button("🚀", type="primary", help="Lancer la recherche"):
                if query:
                    process_universal_query(query)

def show_modern_sidebar():
    """Affiche la sidebar moderne avec navigation par catégories"""
    
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        # Bouton retour accueil
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.current_view = 'accueil'
            st.session_state.current_module = None
        
        st.markdown("---")
        
        # Section Recherche & Analyse
        st.markdown("#### 🔍 Recherche & Analyse")
        
        if modules_disponibles.get('recherche_analyse_unifiee'):
            if st.button("🤖 Recherche IA", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'recherche_analyse_unifiee' else "secondary"):
                st.session_state.current_view = 'recherche_analyse'
                st.session_state.current_module = 'recherche_analyse_unifiee'
        
        if modules_disponibles.get('jurisprudence'):
            if st.button("⚖️ Jurisprudence", use_container_width=True,
                        type="primary" if st.session_state.get('current_module') == 'jurisprudence' else "secondary"):
                st.session_state.current_view = 'jurisprudence'
                st.session_state.current_module = 'jurisprudence'
        
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
            ("📅 Timeline", "timeline"),
            ("🔄 Comparaison", "comparison"),
            ("📊 Synthèse", "synthesis"),
            ("🗺️ Cartographie", "mapping")
        ]
        
        for label, module in tools:
            if modules_disponibles.get(module):
                if st.button(label, use_container_width=True,
                            type="primary" if st.session_state.get('current_module') == module else "secondary"):
                    st.session_state.current_view = module
                    st.session_state.current_module = module
        
        # Section Communication
        st.markdown("#### 💬 Communication")
        
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
        
        # Configuration
        st.markdown("---")
        if st.button("⚙️ Configuration", use_container_width=True):
            st.session_state.current_view = 'configuration'
            st.session_state.current_module = 'configuration'

# ========== SECTION 6: PAGE D'ACCUEIL ==========

def show_home_page():
    """Affiche la page d'accueil avec tableau de bord"""
    
    # Message de bienvenue
    st.markdown("""
    ### 👋 Bienvenue dans votre Assistant Juridique IA
    
    Explorez les fonctionnalités via la **barre de recherche** ci-dessus ou utilisez le **menu latéral**.
    """)
    
    # Cartes de démarrage rapide
    st.markdown("#### 🚀 Démarrage rapide")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container():
            st.markdown("""
            <div style='background: #f0f9ff; padding: 1.5rem; border-radius: 10px; height: 180px;'>
                <h4>🔍 Rechercher</h4>
                <p>Jurisprudence, documents, analyses IA</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Commencer", key="start_search", use_container_width=True):
                st.session_state.current_module = 'recherche_analyse_unifiee'
                st.rerun()
    
    with col2:
        with st.container():
            st.markdown("""
            <div style='background: #fef3c7; padding: 1.5rem; border-radius: 10px; height: 180px;'>
                <h4>✍️ Rédiger</h4>
                <p>Actes, conclusions, assignations</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Commencer", key="start_write", use_container_width=True):
                st.session_state.current_module = 'redaction_unified'
                st.rerun()
    
    with col3:
        with st.container():
            st.markdown("""
            <div style='background: #ede9fe; padding: 1.5rem; border-radius: 10px; height: 180px;'>
                <h4>📎 Gérer</h4>
                <p>Pièces, dossiers, documents</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Commencer", key="start_manage", use_container_width=True):
                st.session_state.current_module = 'pieces_manager'
                st.rerun()
    
    with col4:
        with st.container():
            st.markdown("""
            <div style='background: #dcfce7; padding: 1.5rem; border-radius: 10px; height: 180px;'>
                <h4>📊 Analyser</h4>
                <p>Risques, timeline, synthèses</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Commencer", key="start_analyze", use_container_width=True):
                st.session_state.current_module = 'risques'
                st.rerun()
    
    # Statistiques et activité récente
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📈 Statistiques")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            nb_docs = len(st.session_state.get('imported_documents', {}))
            st.metric("Documents", nb_docs)
        
        with col_b:
            nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
            st.metric("Pièces", nb_pieces)
        
        with col_c:
            nb_analyses = len(st.session_state.get('search_history', []))
            st.metric("Analyses", nb_analyses)
        
        with col_d:
            nb_modules = sum(1 for v in modules_disponibles.values() if v)
            st.metric("Modules actifs", f"{nb_modules}/{len(modules_disponibles)}")
    
    with col2:
        st.markdown("#### 🕐 Activité récente")
        
        history = st.session_state.get('search_history', [])
        if history:
            for item in history[-5:]:
                st.caption(f"• {item}")
        else:
            st.info("Aucune activité récente")

# ========== SECTION 7: TRAITEMENT DES REQUÊTES ==========

def process_universal_query(query: str):
    """Traite une requête universelle et route vers le bon module"""
    
    # Analyser la requête
    query_lower = query.lower()
    
    # Patterns de détection avec priorités
    patterns = {
        'recherche': {
            'keywords': ['rechercher', 'recherche', 'chercher', 'trouver', 'analyser', 'analyse'],
            'module': 'recherche_analyse_unifiee',
            'view': 'recherche_analyse'
        },
        'timeline': {
            'keywords': ['timeline', 'chronologie', 'dates', 'événements', 'temporel', 'calendrier'],
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

# ========== SECTION 8: AFFICHAGE DES MODULES ==========

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

# ========== SECTION 9: FONCTION PRINCIPALE ==========

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