"""Application principale avec générateur unifié et compatibilité ascendante"""

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

# ========== NOUVEAU : Import du générateur unifié ==========
UNIFIED_GENERATOR_AVAILABLE = False
try:
    from managers.unified_document_generator import (
        UnifiedDocumentGenerator,
        UnifiedGenerationRequest,
        DocumentLength,
        PlaidoirieDuration
    )
    UNIFIED_GENERATOR_AVAILABLE = True
    logger.info("✅ Générateur unifié disponible")
except ImportError as e:
    logger.warning(f"⚠️ Générateur unifié non disponible: {e}")

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

# Import des dataclasses supplémentaires pour le générateur unifié
if DATACLASSES_AVAILABLE:
    try:
        from modules.dataclasses import (
            TypeDocument, StyleRedaction, Partie, 
            InfractionIdentifiee, DocumentJuridique
        )
    except ImportError:
        logger.warning("⚠️ Certaines dataclasses manquantes")

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
    
    # Génération et rédaction - MODIFIÉ POUR LE GÉNÉRATEUR UNIFIÉ
    'generation_unifiee': {
        'name': '🚀 Génération unifiée',
        'category': 'generation',
        'description': 'Générateur unifié pour tous vos documents juridiques',
        'priority': 0,  # Priorité maximale
        'keywords': ['générer', 'rédiger', 'créer', 'document', 'acte', 'plainte', 'conclusions', 'plaidoirie', 'long']
    },
    'redaction_unified': {
        'name': '✍️ Rédaction assistée',
        'category': 'generation',
        'description': 'Rédaction avec templates et IA',
        'priority': 1,
        'keywords': ['rédiger', 'template', 'modèle', 'assistant']
    },
    'generation_juridique': {
        'name': '📝 Génération classique',
        'category': 'generation',
        'description': 'Génération d\'actes standards',
        'priority': 2,
        'keywords': ['générer', 'acte', 'standard']
    },
    'generation_longue': {
        'name': '📜 Documents longs',
        'category': 'generation',
        'description': 'Documents complexes 25-50+ pages',
        'priority': 3,
        'keywords': ['long', 'complexe', 'exhaustif']
    },
    'plaidoirie': {
        'name': '🎭 Plaidoiries',
        'category': 'generation',
        'description': 'Plaidoiries calibrées 10-120 min',
        'priority': 4,
        'keywords': ['plaidoirie', 'oral', 'audience']
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

# ========== FONCTION DE COMPATIBILITÉ ==========
def create_generation_wrapper(old_module_name):
    """Crée un wrapper pour rediriger vers le générateur unifié"""
    def wrapper_function():
        if UNIFIED_GENERATOR_AVAILABLE:
            show_unified_generation_interface(focus=old_module_name)
        else:
            st.error(f"❌ Module {old_module_name} temporairement indisponible")
    return wrapper_function

# ========== IMPORT DES MODULES AVEC COMPATIBILITÉ ==========
for module_id, config in MODULES_CONFIG.items():
    try:
        # Nouveau module de génération unifiée
        if module_id == 'generation_unifiee':
            if UNIFIED_GENERATOR_AVAILABLE:
                modules_imports[module_id] = lambda: show_unified_generation_interface()
                modules_disponibles[module_id] = config
                logger.info(f"✅ Module {module_id} chargé (unifié)")
            continue
            
        # Modules de génération existants - REDIRECTION VERS UNIFIÉ
        elif module_id in ['generation_juridique', 'generation_longue', 'plaidoirie']:
            if UNIFIED_GENERATOR_AVAILABLE:
                # Créer un wrapper qui redirige vers le générateur unifié
                modules_imports[module_id] = create_generation_wrapper(module_id)
                modules_disponibles[module_id] = config
                logger.info(f"✅ Module {module_id} redirigé vers générateur unifié")
            else:
                # Fallback sur l'ancien système si le nouveau n'est pas disponible
                if module_id == 'generation_juridique':
                    from modules.generation_juridique import show_page as show_generation
                    modules_imports[module_id] = show_generation
                elif module_id == 'generation_longue':
                    from modules.generation_longue import show_generation_longue_interface
                    modules_imports[module_id] = show_generation_longue_interface
                elif module_id == 'plaidoirie':
                    from modules.plaidoirie import process_plaidoirie_request, show_page as show_plaidoirie_page
                    modules_imports[module_id] = show_plaidoirie_page if 'show_plaidoirie_page' in locals() else lambda: process_plaidoirie_request("", {})
                modules_disponibles[module_id] = config
                logger.info(f"✅ Module {module_id} chargé (ancien système)")
            continue
            
        # Autres modules inchangés
        elif module_id == 'pieces_manager':
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
            from modules.email import process_email_request, show_page as show_email_page
            modules_imports[module_id] = show_email_page if 'show_email_page' in locals() else lambda: process_email_request("", {})
        elif module_id == 'preparation_client':
            from modules.preparation_client import process_preparation_request, show_page as show_prep_page
            modules_imports[module_id] = show_prep_page if 'show_prep_page' in locals() else lambda: process_preparation_request("", {})
        elif module_id == 'configuration':
            from modules.configuration import show_configuration_page
            modules_imports[module_id] = show_configuration_page
        elif module_id == 'template':
            from modules.template import show_template_page
            modules_imports[module_id] = show_template_page
        elif module_id == 'integration_juridique':
            from modules.integration_juridique import show_integration_page
            modules_imports[module_id] = show_integration_page
        else:
            continue
            
        modules_disponibles[module_id] = config
        logger.info(f"✅ Module {module_id} chargé avec succès")
        
    except ImportError as e:
        logger.warning(f"⚠️ Module {module_id} non disponible: {e}")
    except Exception as e:
        logger.error(f"❌ Erreur chargement module {module_id}: {e}")

# ========== NOUVELLE FONCTION : Interface du générateur unifié ==========
def show_unified_generation_interface(focus: Optional[str] = None):
    """Interface principale du générateur unifié"""
    
    if not UNIFIED_GENERATOR_AVAILABLE:
        st.error("❌ Le générateur unifié n'est pas disponible")
        st.info("Créez le fichier `managers/unified_document_generator.py`")
        return
        
    st.header("🚀 Générateur Unifié de Documents Juridiques")
    
    # Initialiser le générateur
    if 'unified_generator' not in st.session_state:
        st.session_state.unified_generator = UnifiedDocumentGenerator()
    
    generator = st.session_state.unified_generator
    
    # Afficher les capacités disponibles
    with st.expander("📋 Capacités disponibles", expanded=False):
        capabilities = generator.get_plugin_capabilities()
        for plugin_name, caps in capabilities.items():
            st.write(f"**Plugin {plugin_name}:**")
            st.json(caps)
    
    # Tabs pour différents modes
    if focus == 'generation_longue':
        default_tab = 2
    elif focus == 'plaidoirie':
        default_tab = 3
    else:
        default_tab = 0
        
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Génération Standard",
        "⚡ Génération Rapide",
        "📜 Documents Longs (25-50+ pages)",
        "🎭 Plaidoiries Calibrées"
    ])
    
    with tab1:
        show_standard_generation_interface(generator)
    
    with tab2:
        show_quick_generation_interface(generator)
        
    with tab3:
        show_long_document_interface(generator)
        
    with tab4:
        show_plaidoirie_interface(generator)

def show_standard_generation_interface(generator):
    """Interface de génération standard"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type de document
        doc_type = st.selectbox(
            "Type de document",
            options=list(TypeDocument),
            format_func=lambda x: x.value.replace('_', ' ').title()
        )
        
        # Style
        style = st.selectbox(
            "Style de rédaction",
            options=list(StyleRedaction),
            format_func=lambda x: x.value.title()
        )
        
    with col2:
        # Longueur
        length = st.selectbox(
            "Longueur du document",
            options=list(DocumentLength),
            format_func=lambda x: f"{x.value.title()} ({get_length_description(x)})"
        )
        
        # Options
        verify_juris = st.checkbox("Vérifier la jurisprudence", value=True)
        ai_enhancement = st.checkbox("Enrichissement IA", value=True)
    
    # Parties
    st.subheader("👥 Parties")
    col1, col2 = st.columns(2)
    
    with col1:
        demandeurs_text = st.text_area(
            "Demandeurs / Plaignants",
            placeholder="Un par ligne",
            height=100
        )
    
    with col2:
        defendeurs_text = st.text_area(
            "Défendeurs / Mis en cause",
            placeholder="Un par ligne",
            height=100
        )
    
    # Infractions
    st.subheader("🚨 Infractions")
    infractions_list = st.multiselect(
        "Sélectionnez les infractions",
        options=[
            "Abus de biens sociaux",
            "Corruption",
            "Escroquerie",
            "Abus de confiance",
            "Blanchiment",
            "Faux et usage de faux",
            "Détournement de fonds publics",
            "Favoritisme",
            "Prise illégale d'intérêts",
            "Trafic d'influence"
        ]
    )
    
    # Contexte
    contexte = st.text_area(
        "Contexte de l'affaire",
        placeholder="Décrivez les faits et le contexte...",
        height=150
    )
    
    # Bouton de génération
    if st.button("🚀 Générer le document", type="primary", use_container_width=True):
        
        # Validation
        if not contexte:
            st.error("Veuillez fournir un contexte")
            return
            
        # Créer les parties
        demandeurs = []
        for ligne in demandeurs_text.split('\n'):
            if ligne.strip():
                demandeurs.append(Partie(nom=ligne.strip(), type_partie="demandeur"))
                
        defendeurs = []
        for ligne in defendeurs_text.split('\n'):
            if ligne.strip():
                defendeurs.append(Partie(nom=ligne.strip(), type_partie="defendeur"))
        
        # Créer les infractions
        infractions = []
        for inf_name in infractions_list:
            infractions.append(InfractionIdentifiee(
                type=inf_name,
                description=f"Infraction de {inf_name}"
            ))
        
        # Créer la requête
        request = UnifiedGenerationRequest(
            document_type=doc_type,
            parties={'demandeurs': demandeurs, 'defendeurs': defendeurs},
            infractions=infractions,
            contexte=contexte,
            style=style,
            length=length,
            options={
                'verify_jurisprudence': verify_juris,
                'ai_enhancement': ai_enhancement
            }
        )
        
        # Générer
        with st.spinner("Génération en cours..."):
            try:
                # Utiliser asyncio pour appeler la méthode async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                document = loop.run_until_complete(generator.generate(request))
                
                # Afficher le résultat
                st.success("✅ Document généré avec succès!")
                
                # Métadonnées
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Nombre de mots", f"{document.metadata.get('word_count', 0):,}")
                with col2:
                    st.metric("Pages estimées", f"~{document.metadata.get('word_count', 0)//500}")
                with col3:
                    st.metric("Temps de génération", "< 1 min")
                
                # Afficher le document
                st.markdown("---")
                st.markdown(f"### {document.titre}")
                st.text_area(
                    "Contenu généré",
                    value=document.contenu,
                    height=600,
                    key="generated_content"
                )
                
                # Options d'export
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📥 Télécharger (TXT)",
                        data=document.contenu,
                        file_name=f"{document.titre}.txt",
                        mime="text/plain"
                    )
                
                # Stocker en session
                st.session_state.last_generated_document = document
                
            except Exception as e:
                st.error(f"Erreur lors de la génération : {str(e)}")
                logger.error(f"Erreur génération: {e}", exc_info=True)

def show_long_document_interface(generator):
    """Interface spécialisée pour documents longs"""
    
    st.info("""
    📜 **Génération de documents longs (25-50+ pages)**
    
    Ce mode est optimisé pour :
    - Plaintes avec constitution de partie civile détaillées
    - Conclusions exhaustives
    - Mémoires approfondis
    - Documents nécessitant une analyse complète
    """)
    
    # Configuration spécifique
    col1, col2 = st.columns(2)
    
    with col1:
        doc_type = st.selectbox(
            "Type de document long",
            options=[
                TypeDocument.PLAINTE,
                TypeDocument.CONCLUSIONS,
                TypeDocument.MEMOIRE
            ],
            format_func=lambda x: x.value.replace('_', ' ').title()
        )
        
        target_length = st.select_slider(
            "Longueur cible",
            options=[
                DocumentLength.LONG,
                DocumentLength.VERY_LONG
            ],
            format_func=lambda x: {
                DocumentLength.LONG: "25-50 pages (~25 000 mots)",
                DocumentLength.VERY_LONG: "50+ pages (~50 000+ mots)"
            }.get(x)
        )
    
    with col2:
        parallel_gen = st.checkbox(
            "Génération parallèle",
            value=True,
            help="Génère plusieurs sections simultanément (plus rapide)"
        )
        
        auto_enrich = st.checkbox(
            "Enrichissement automatique",
            value=True,
            help="Ajoute du contenu si la longueur cible n'est pas atteinte"
        )
    
    # Structure détaillée
    with st.expander("📋 Structure du document", expanded=False):
        st.info("La structure sera adaptée automatiquement selon le type et la longueur")
        
        if doc_type == TypeDocument.PLAINTE:
            st.markdown("""
            1. **En-tête et qualités** (5%)
            2. **Table chronologique** (5%)
            3. **Exposé détaillé des faits** (35%)
            4. **Analyse des mécanismes** (20%)
            5. **Discussion juridique** (25%)
            6. **Préjudices** (8%)
            7. **Demandes** (2%)
            """)
    
    # Reste de l'interface similaire mais adaptée
    # ... (parties, infractions, contexte)
    
    # Contexte enrichi pour documents longs
    contexte = st.text_area(
        "Contexte détaillé de l'affaire",
        placeholder="""Fournissez un maximum de détails :
- Chronologie précise des faits
- Montants en jeu
- Documents disponibles
- Éléments de preuve
- Contexte économique/social
- Historique des relations entre parties...""",
        height=250
    )
    
    # Génération
    if st.button("🚀 Générer document long", type="primary", use_container_width=True):
        
        if len(contexte) < 200:
            st.warning("⚠️ Pour un document long, fournissez plus de contexte")
            return
        
        # Créer la requête avec options spécifiques
        request = UnifiedGenerationRequest(
            document_type=doc_type,
            parties={'demandeurs': [], 'defendeurs': []},  # À remplir
            infractions=[],  # À remplir
            contexte=contexte,
            style=StyleRedaction.EXHAUSTIF,
            length=target_length,
            enrichissement_auto=auto_enrich,
            generation_parallele=parallel_gen
        )
        
        # Afficher la progression
        progress = st.progress(0)
        status = st.empty()
        
        with st.spinner("Génération d'un document long en cours..."):
            try:
                # Simuler la progression (à remplacer par vraie progression)
                for i in range(101):
                    progress.progress(i)
                    if i % 20 == 0:
                        status.text(f"Génération en cours... {i}%")
                
                # Générer
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                document = loop.run_until_complete(generator.generate(request))
                
                # Afficher le résultat
                st.success(f"""
                ✅ Document long généré avec succès!
                - {document.metadata.get('word_count', 0):,} mots
                - ~{document.metadata.get('word_count', 0)//500} pages
                """)
                
                # Afficher par sections pour les longs documents
                st.markdown("---")
                st.markdown(f"### {document.titre}")
                
                # Découper en sections pour meilleure lisibilité
                sections = extract_sections_from_document(document.contenu)
                
                for section_name, section_content in sections.items():
                    with st.expander(f"📄 {section_name}", expanded=False):
                        st.text_area(
                            "",
                            value=section_content,
                            height=400,
                            key=f"section_{section_name}"
                        )
                
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

def show_plaidoirie_interface(generator):
    """Interface spécialisée pour plaidoiries"""
    
    st.info("""
    🎭 **Génération de plaidoiries calibrées**
    
    Créez des plaidoiries adaptées à votre temps de parole :
    - Style oral optimisé
    - Marqueurs temporels
    - Points d'emphase
    - Transitions naturelles
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Durée
        duration = st.selectbox(
            "⏱️ Durée de plaidoirie",
            options=list(PlaidoirieDuration),
            format_func=lambda x: f"{x.value} minutes"
        )
        
    with col2:
        # Type d'audience
        audience_type = st.selectbox(
            "Type d'audience",
            ["Correctionnelle", "Assises", "Civile", "Commerciale"],
            key="audience_type_plaidoirie"
        )
        
    with col3:
        # Position
        position = st.radio(
            "Position",
            ["Demande", "Défense"],
            horizontal=True
        )
    
    # Support de conclusions
    use_conclusions = st.checkbox(
        "S'appuyer sur des conclusions existantes",
        help="La plaidoirie sera adaptée depuis vos conclusions écrites"
    )
    
    if use_conclusions:
        # Permettre de sélectionner ou coller des conclusions
        conclusions_ref = st.text_area(
            "Conclusions de référence",
            placeholder="Collez vos conclusions ici ou référencez un document...",
            height=150
        )
    
    # Points forts à développer
    st.subheader("💡 Points forts pour l'oral")
    
    points_forts = []
    for i in range(3):
        point = st.text_input(
            f"Point fort {i+1}",
            placeholder="Ex: Absence totale de preuve directe",
            key=f"point_fort_{i}"
        )
        if point:
            points_forts.append(point)
    
    # Contexte et affaire
    contexte = st.text_area(
        "Contexte de l'affaire",
        placeholder="Résumé des faits et enjeux principaux...",
        height=150
    )
    
    # Style oratoire
    with st.expander("🎯 Options de style", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            style_oratoire = st.select_slider(
                "Ton",
                options=["Sobre", "Modéré", "Passionné"],
                value="Modéré"
            )
            
        with col2:
            use_metaphors = st.checkbox("Utiliser des métaphores", value=True)
            use_questions = st.checkbox("Questions rhétoriques", value=True)
    
    # Générer
    if st.button("🎤 Générer la plaidoirie", type="primary", use_container_width=True):
        
        if not contexte:
            st.error("Veuillez fournir le contexte")
            return
        
        # Créer la requête spécialisée plaidoirie
        request = UnifiedGenerationRequest(
            document_type=TypeDocument.PLAIDOIRIE,
            parties={'demandeurs': [], 'defendeurs': []},
            infractions=[],
            contexte=contexte,
            style=StyleRedaction.PERSUASIF,
            length=DocumentLength.STANDARD,  # Sera adapté selon durée
            plaidoirie_duration=duration,
            points_forts_oraux=points_forts,
            options={
                'audience_type': audience_type,
                'position': position,
                'style_oratoire': style_oratoire,
                'use_metaphors': use_metaphors,
                'use_questions': use_questions
            }
        )
        
        with st.spinner(f"Génération d'une plaidoirie de {duration.value} minutes..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                document = loop.run_until_complete(generator.generate(request))
                
                # Afficher avec indications spéciales plaidoirie
                st.success("✅ Plaidoirie générée et calibrée!")
                
                # Métriques de plaidoirie
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Durée estimée", f"{duration.value} min")
                with col2:
                    words = document.metadata.get('word_count', 0)
                    st.metric("Nombre de mots", f"{words:,}")
                with col3:
                    st.metric("Vitesse requise", f"{words//duration.value} mots/min")
                
                # Afficher avec marqueurs temporels
                st.markdown("---")
                st.markdown(f"### {document.titre}")
                
                # Instructions orateur
                with st.expander("🎯 Instructions pour l'orateur", expanded=True):
                    st.markdown("""
                    **Conseils de présentation :**
                    - 🎯 Les passages en **[EMPHASE]** doivent être prononcés avec force
                    - ⏸️ Les **[PAUSE]** indiquent une pause dramatique
                    - 🎭 Les **[REGARD PUBLIC]** signalent un moment de connexion visuelle
                    - ⏱️ Les **[TEMPS: X min]** indiquent le temps écoulé
                    """)
                
                # Contenu avec coloration syntaxique pour les marqueurs
                content_display = st.text_area(
                    "Texte de la plaidoirie",
                    value=document.contenu,
                    height=600,
                    key="plaidoirie_content"
                )
                
                # Options d'export spéciales
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        "📥 Version orateur (avec marqueurs)",
                        data=document.contenu,
                        file_name=f"plaidoirie_{duration.value}min_orateur.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    # Version épurée sans marqueurs
                    clean_content = remove_oral_markers(document.contenu)
                    st.download_button(
                        "📥 Version épurée (sans marqueurs)",
                        data=clean_content,
                        file_name=f"plaidoirie_{duration.value}min_clean.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

def show_quick_generation_interface(generator):
    """Interface de génération rapide par prompt"""
    
    st.markdown("""
    ⚡ **Génération rapide par instruction**
    
    Décrivez simplement ce que vous voulez générer.
    """)
    
    # Exemples de prompts
    examples = [
        "Rédige une plainte pour escroquerie contre la société XYZ pour un préjudice de 50 000€",
        "Génère des conclusions de nullité pour vice de procédure dans l'affaire ABC",
        "Crée une plaidoirie de 20 minutes pour défendre M. Martin accusé d'abus de biens sociaux",
        "Prépare une assignation en référé pour obtenir des mesures conservatoires"
    ]
    
    selected_example = st.selectbox(
        "Exemples de demandes",
        [""] + examples,
        key="quick_gen_examples"
    )
    
    # Zone de prompt
    prompt = st.text_area(
        "Votre demande",
        value=selected_example,
        placeholder="Décrivez le document juridique que vous souhaitez générer...",
        height=100,
        key="quick_gen_prompt"
    )
    
    # Options rapides
    col1, col2, col3 = st.columns(3)
    
    with col1:
        urgency = st.checkbox("🚨 Urgent", key="quick_urgency")
    
    with col2:
        detailed = st.checkbox("📚 Version détaillée", key="quick_detailed")
    
    with col3:
        formal = st.checkbox("🎩 Style très formel", key="quick_formal")
    
    if st.button("⚡ Générer rapidement", type="primary", use_container_width=True):
        
        if not prompt:
            st.error("Veuillez décrire votre demande")
            return
            
        with st.spinner("Analyse de votre demande..."):
            # Analyser le prompt pour extraire les informations
            # (Cette partie pourrait utiliser un LLM pour parser le prompt)
            
            # Pour la démo, création basique
            request = UnifiedGenerationRequest(
                document_type=TypeDocument.PLAINTE,  # À déterminer depuis le prompt
                parties={'demandeurs': [], 'defendeurs': []},
                infractions=[],
                contexte=prompt,
                style=StyleRedaction.FORMEL if formal else StyleRedaction.MODERNE,
                length=DocumentLength.MEDIUM if detailed else DocumentLength.STANDARD,
                options={
                    'urgent': urgency,
                    'from_prompt': True
                }
            )
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                document = loop.run_until_complete(generator.generate(request))
                
                st.success("✅ Document généré!")
                
                # Affichage simple
                st.text_area(
                    "Document généré",
                    value=document.contenu,
                    height=500
                )
                
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

# ========== FONCTIONS UTILITAIRES ==========

def get_length_description(length: DocumentLength) -> str:
    """Retourne la description d'une longueur de document"""
    descriptions = {
        DocumentLength.SHORT: "< 5 pages",
        DocumentLength.STANDARD: "5-15 pages",
        DocumentLength.MEDIUM: "15-25 pages",
        DocumentLength.LONG: "25-50 pages",
        DocumentLength.VERY_LONG: "50+ pages"
    }
    return descriptions.get(length, "")

def extract_sections_from_document(content: str) -> Dict[str, str]:
    """Extrait les sections d'un document long"""
    sections = {}
    current_section = "Introduction"
    current_content = []
    
    for line in content.split('\n'):
        # Détecter les titres de section (en majuscules ou numérotés)
        if re.match(r'^[IVX]+\.|^[A-Z][A-Z\s]+$|^\d+\.', line):
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = line.strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Ajouter la dernière section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    return sections

def remove_oral_markers(content: str) -> str:
    """Supprime les marqueurs oraux d'une plaidoirie"""
    markers = [
        r'\[PAUSE\]',
        r'\[EMPHASE\]',
        r'\[REGARD PUBLIC\]',
        r'\[TEMPS:.*?\]',
        r'\[.*?\]'  # Tous les marqueurs entre crochets
    ]
    
    clean_content = content
    for marker in markers:
        clean_content = re.sub(marker, '', clean_content)
    
    # Nettoyer les espaces multiples
    clean_content = re.sub(r'\s+', ' ', clean_content)
    
    return clean_content.strip()

# ========== SECTION 3: INITIALISATION ==========

# Initialiser session state
initialize_session_state()

# Charger CSS personnalisé
load_custom_css()

# Initialiser les services Azure si disponibles
if 'azure_initialized' not in st.session_state:
    st.session_state.azure_initialized = False
    st.session_state.azure_status = {
        'blob': {'connected': False, 'error': None},
        'search': {'connected': False, 'error': None}
    }

if not st.session_state.azure_initialized and AZURE_AVAILABLE:
    # Initialiser Azure Blob Storage
    if app_config.enable_azure_storage and os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
        try:
            from managers.azure_blob_manager import AzureBlobManager
            manager = AzureBlobManager()
            
            # Test de connexion
            try:
                manager.blob_service_client.get_service_properties()
                st.session_state.azure_blob_manager = manager
                st.session_state.azure_status['blob'] = {'connected': True, 'error': None}
                logger.info("✅ Azure Blob Storage connecté")
            except Exception as e:
                st.session_state.azure_blob_manager = None
                st.session_state.azure_status['blob'] = {'connected': False, 'error': str(e)}
                logger.error(f"❌ Erreur connexion Azure Blob: {e}")
                
        except Exception as e:
            logger.error(f"❌ Erreur import Azure Blob Manager: {e}")
            st.session_state.azure_blob_manager = None
            st.session_state.azure_status['blob'] = {'connected': False, 'error': str(e)}
    
    # Initialiser Azure Search
    if app_config.enable_azure_search:
        try:
            endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            key = os.getenv("AZURE_SEARCH_KEY")
            
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

# ========== SECTION 4: NAVIGATION ET INTERFACE ==========

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
        unified_gen_status = UNIFIED_GENERATOR_AVAILABLE
        
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
            <span class="status-badge {'success' if unified_gen_status else 'warning'}">
                {'✅' if unified_gen_status else '⚠️'} Gen. Unifié
            </span>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    
    with col3:
        # Actions rapides
        cols = st.columns(3)
        with cols[0]:
            if st.button("🏠", help="Accueil", key="home_button"):
                st.session_state.current_view = "accueil"
                st.session_state.current_module = None
                st.rerun()
        with cols[1]:
            if st.button("🔍", help="Recherche", key="search_button"):
                st.session_state.current_module = "recherche"
                st.session_state.current_view = "module"
                st.rerun()
        with cols[2]:
            if st.button("⚙️", help="Configuration", key="config_button"):
                st.session_state.current_module = "configuration"
                st.session_state.current_view = "module"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

def show_main_interface():
    """Interface principale avec navigation intelligente"""
    
    # En-tête avec statut
    show_header_with_status()
    
    # Barre de recherche universelle
    search_container = st.container()
    with search_container:
        col1, col2 = st.columns([5, 1])
        
        with col1:
            query = st.text_input(
                "🔍 Que souhaitez-vous faire ?",
                placeholder="Ex: Rédiger une plainte pour escroquerie, Analyser un contrat, Rechercher jurisprudence...",
                key="universal_search",
                label_visibility="collapsed"
            )
        
        with col2:
            search_clicked = st.button("→", key="search_execute", type="primary", use_container_width=True)
    
    # Traiter la recherche
    if (query and search_clicked) or (query and st.session_state.get('search_auto_submit')):
        process_universal_query(query)
        st.session_state.search_auto_submit = False
    
    # Navigation principale selon la vue
    if st.session_state.current_view == "accueil":
        show_home_dashboard()
    elif st.session_state.current_view == "module":
        show_module_content()
    elif st.session_state.current_view == "workflow":
        show_workflow_interface()

def show_home_dashboard():
    """Affiche le tableau de bord d'accueil avec toutes les catégories"""
    
    # Message de bienvenue personnalisé
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Bonjour"
    elif hour < 18:
        greeting = "Bon après-midi"
    else:
        greeting = "Bonsoir"
    
    st.markdown(f"### {greeting} ! Comment puis-je vous aider aujourd'hui ?")
    
    # Afficher les modules par catégorie
    categories = {}
    for module_id, config in modules_disponibles.items():
        category = config.get('category', 'autre')
        if category not in categories:
            categories[category] = []
        categories[category].append((module_id, config))
    
    # Ordre des catégories
    category_order = ['generation', 'documents', 'analyse', 'outils', 'communication', 'system']
    category_icons = {
        'generation': '✨',
        'documents': '📁',
        'analyse': '🔍',
        'outils': '🛠️',
        'communication': '💬',
        'system': '⚙️'
    }
    
    # Mettre en avant le générateur unifié si disponible
    if UNIFIED_GENERATOR_AVAILABLE and 'generation' in categories:
        st.markdown("### 🚀 Nouveau : Générateur Unifié")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(
                "📝 Génération Standard",
                help="Documents juridiques classiques",
                use_container_width=True,
                key="quick_standard"
            ):
                st.session_state.current_module = 'generation_unifiee'
                st.session_state.current_view = 'module'
                st.rerun()
        
        with col2:
            if st.button(
                "📜 Documents Longs",
                help="25-50+ pages",
                use_container_width=True,
                key="quick_long"
            ):
                st.session_state.current_module = 'generation_unifiee'
                st.session_state.current_view = 'module'
                st.session_state.generation_focus = 'long'
                st.rerun()
        
        with col3:
            if st.button(
                "🎭 Plaidoiries",
                help="10-120 minutes",
                use_container_width=True,
                key="quick_plaidoirie"
            ):
                st.session_state.current_module = 'generation_unifiee'
                st.session_state.current_view = 'module'
                st.session_state.generation_focus = 'plaidoirie'
                st.rerun()
        
        st.markdown("---")
    
    # Afficher les catégories
    for category in category_order:
        if category in categories:
            modules = sorted(categories[category], key=lambda x: x[1].get('priority', 999))
            
            st.markdown(f"### {category_icons.get(category, '📌')} {category.title()}")
            
            # Afficher en colonnes
            cols = st.columns(min(3, len(modules)))
            
            for idx, (module_id, config) in enumerate(modules):
                col = cols[idx % 3]
                
                with col:
                    # Carte de module
                    with st.container():
                        if st.button(
                            config['name'],
                            help=config['description'],
                            use_container_width=True,
                            key=f"module_{module_id}"
                        ):
                            st.session_state.current_module = module_id
                            st.session_state.current_view = 'module'
                            st.rerun()
                        
                        st.caption(config['description'])
            
            st.markdown("")

def process_universal_query(query: str):
    """Traite une requête universelle et route vers le bon module"""
    
    # Analyser la requête pour déterminer l'intention
    query_lower = query.lower()
    
    # Mots-clés pour la génération unifiée
    generation_keywords = {
        'unified': ['générer', 'rédiger', 'créer', 'préparer', 'document', 'acte'],
        'long': ['long', 'exhaustif', 'détaillé', 'complet', '50 pages', '25 pages'],
        'plaidoirie': ['plaidoirie', 'plaider', 'audience', 'oral', 'minutes']
    }
    
    # Détecter le type de génération
    if UNIFIED_GENERATOR_AVAILABLE:
        for gen_type, keywords in generation_keywords.items():
            if any(kw in query_lower for kw in keywords):
                st.session_state.current_module = 'generation_unifiee'
                st.session_state.current_view = 'module'
                st.session_state.generation_context = query
                
                if gen_type == 'long':
                    st.session_state.generation_focus = 'long'
                elif gen_type == 'plaidoirie':
                    st.session_state.generation_focus = 'plaidoirie'
                
                st.rerun()
                return
    
    # Analyser pour les autres modules
    best_match = None
    best_score = 0
    
    for module_id, config in modules_disponibles.items():
        score = 0
        keywords = config.get('keywords', [])
        
        for keyword in keywords:
            if keyword in query_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = module_id
    
    if best_match:
        st.session_state.current_module = best_match
        st.session_state.current_view = 'module'
        st.session_state.search_query = query
    else:
        # Si aucune intention claire, utiliser le module de recherche
        st.session_state.current_module = 'recherche'
        st.session_state.current_view = 'module'
        st.session_state.search_query = query
    
    st.rerun()

def show_module_content():
    """Affiche le contenu du module actuel"""
    module_id = st.session_state.get('current_module')
    
    if not module_id or module_id not in modules_disponibles:
        st.error("Module non trouvé")
        if st.button("Retour à l'accueil"):
            st.session_state.current_view = 'accueil'
            st.rerun()
        return
    
    # Header du module
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col1:
        if st.button("← Retour", use_container_width=True):
            st.session_state.current_module = None
            st.session_state.current_view = 'accueil'
            st.rerun()
    
    with col2:
        module_config = modules_disponibles[module_id]
        st.markdown(f"## {module_config['name']}")
        st.markdown(f"*{module_config['description']}*")
    
    st.markdown("---")
    
    # Contenu du module
    if module_id in modules_imports:
        try:
            # Appeler la fonction d'affichage du module
            modules_imports[module_id]()
        except Exception as e:
            st.error(f"Erreur lors du chargement du module : {str(e)}")
            logger.error(f"Erreur module {module_id}: {e}", exc_info=True)
            
            # Afficher plus d'informations en mode debug
            if app_config.debug:
                st.exception(e)
    else:
        st.error(f"Module {module_id} non implémenté")

def show_workflow_interface():
    """Interface pour les workflows guidés"""
    st.info("Workflows guidés - En construction")

# ========== SECTION 5: LANCEMENT DE L'APPLICATION ==========

def main():
    """Point d'entrée principal de l'application"""
    try:
        # Vérifier l'initialisation
        if 'initialized' not in st.session_state:
            initialize_session_state()
        
        # Afficher l'interface principale
        show_main_interface()
        
    except Exception as e:
        st.error(f"Une erreur inattendue s'est produite : {str(e)}")
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        
        if app_config.debug:
            st.exception(e)
        
        # Bouton de réinitialisation en cas d'erreur
        if st.button("🔄 Réinitialiser l'application"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()