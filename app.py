"""Application IA Juridique - Droit Pénal des Affaires - Version optimisée"""

import importlib
import importlib.util
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from services.universal_search_service import UniversalSearchService
from managers.document_manager import DocumentManager
from utils import LEGAL_SUGGESTIONS

import streamlit as st
import streamlit.components.v1 as components

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="IA Juridique - Droit Pénal des Affaires",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1a237e 0%, #3949ab 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .module-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    .module-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .status-ok { color: #4caf50; }
    .status-error { color: #f44336; }
    .status-warning { color: #ff9800; }
</style>
""", unsafe_allow_html=True)

# ========== CONFIGURATION DES MODULES ==========
# Configuration complète de tous les modules existants
MODULES_CONFIG = {
    # Modules d'analyse
    "comparison": {
        "name": "📊 Comparaison de documents",
        "desc": "Analyse comparative avec détection des contradictions",
        "category": "analyse",
        "priority": 1
    },
    "timeline": {
        "name": "📅 Timeline juridique",
        "desc": "Chronologie des infractions et procédures",
        "category": "analyse",
        "priority": 2
    },
    "extraction": {
        "name": "📑 Extraction d'informations",
        "desc": "Extraction des éléments constitutifs",
        "category": "analyse",
        "priority": 3
    },
    "mapping": {
        "name": "🗺️ Cartographie des relations",
        "desc": "Analyse des réseaux d'entités et relations",
        "category": "analyse",
        "priority": 4
    },
    "recherche_analyse_unifiee": {
        "name": "🔍 Recherche & Analyse unifiée",
        "desc": "Recherche intelligente multi-sources avec IA",
        "category": "analyse",
        "priority": 5
    },
    
    # Modules de stratégie
    "strategy": {
        "name": "⚖️ Stratégie de défense",
        "desc": "Élaboration de stratégies pénales",
        "category": "strategie",
        "priority": 1
    },
    "plaidoirie": {
        "name": "🎯 Plaidoirie pénale",
        "desc": "Préparation des plaidoiries",
        "category": "strategie",
        "priority": 2
    },
    "preparation_client": {
        "name": "👤 Préparation client",
        "desc": "Préparer aux interrogatoires",
        "category": "strategie",
        "priority": 3
    },
    
    # Modules de rédaction
    "redaction_unified": {
        "name": "✍️ Rédaction juridique",
        "desc": "Génération de tous types de documents",
        "category": "redaction",
        "priority": 1
    },
    "generation_longue": {
        "name": "📜 Génération longue",
        "desc": "Documents juridiques complexes et détaillés",
        "category": "redaction",
        "priority": 2
    },
    
    # Modules de gestion
    "import_export": {
        "name": "📁 Import/Export",
        "desc": "Gestion des documents et données",
        "category": "gestion",
        "priority": 1
    },
    "pieces_manager": {
        "name": "📎 Gestion des pièces",
        "desc": "Organisation du dossier pénal",
        "category": "gestion",
        "priority": 2
    },
    "dossier_penal": {
        "name": "📂 Dossier pénal unifié",
        "desc": "Vue d'ensemble du dossier",
        "category": "gestion",
        "priority": 3
    },
    
    # Modules spécialisés
    "jurisprudence": {
        "name": "⚖️ Jurisprudence",
        "desc": "Recherche et analyse de jurisprudence",
        "category": "specialise",
        "priority": 1
    },
    "email": {
        "name": "📧 Gestion des emails",
        "desc": "Centre de messagerie juridique avec IA",
        "category": "communication",
        "priority": 1
    }
}

# Modules à vérifier/créer (ceux qui pourraient manquer)
MODULES_TO_CREATE = {
    # Modules possiblement manquants
    "search_module": {
        "name": "🔍 Recherche simple",
        "desc": "Recherche basique dans les documents",
        "category": "analyse",
        "priority": 6
    },
    "contradiction_analysis": {
        "name": "⚡ Analyse contradictions",
        "desc": "Détection automatique des incohérences",
        "category": "analyse",
        "priority": 7
    },
    "conclusions": {
        "name": "📝 Conclusions pénales",
        "desc": "Rédaction de conclusions",
        "category": "redaction",
        "priority": 3
    },
    "courrier_juridique": {
        "name": "✉️ Courriers juridiques",
        "desc": "Correspondances et notifications",
        "category": "redaction",
        "priority": 4
    },
    "bordereau": {
        "name": "📋 Bordereau de pièces",
        "desc": "Génération de bordereaux",
        "category": "redaction",
        "priority": 5
    },
    "calcul_prejudice": {
        "name": "💰 Calcul préjudice",
        "desc": "Évaluation des préjudices",
        "category": "specialise",
        "priority": 2
    },
    "procedure_verification": {
        "name": "✅ Vérification procédure",
        "desc": "Contrôle de conformité procédurale",
        "category": "specialise",
        "priority": 3
    },
    "risk_assessment": {
        "name": "⚠️ Évaluation risques",
        "desc": "Analyse des risques juridiques",
        "category": "specialise",
        "priority": 4
    },
    "evidence_chain": {
        "name": "🔗 Chaîne de preuves",
        "desc": "Gestion et analyse des preuves",
        "category": "specialise",
        "priority": 5
    },
    "negotiation": {
        "name": "🤝 Négociation pénale",
        "desc": "Stratégies de négociation",
        "category": "strategie",
        "priority": 4
    },
    "witness_preparation": {
        "name": "👥 Préparation témoins",
        "desc": "Préparer les témoins",
        "category": "strategie",
        "priority": 5
    },
    "report_generation": {
        "name": "📊 Génération rapports",
        "desc": "Création de rapports juridiques",
        "category": "redaction",
        "priority": 6
    },
    "integration_juridique": {
        "name": "🔌 Intégration juridique",
        "desc": "Intégration avec systèmes externes",
        "category": "technique",
        "priority": 1
    },
    "chat": {
        "name": "💬 Chat juridique",
        "desc": "Assistant conversationnel juridique",
        "category": "communication",
        "priority": 2
    }
}

# ========== GESTIONNAIRE DE MODULES ==========
class ModuleManager:
    """Gestionnaire centralisé des modules"""
    
    def __init__(self):
        self.modules_path = Path(__file__).parent / "modules"
        self.managers_path = Path(__file__).parent / "managers"
        self.loaded_modules = {}
        self.available_modules = {}
        self.load_status = {"success": [], "failed": {}, "warnings": []}
        
    def discover_modules(self):
        """Découvre tous les modules disponibles"""
        # Vérifier l'existence du dossier modules
        if not self.modules_path.exists():
            self.load_status["warnings"].append(f"Dossier modules non trouvé : {self.modules_path}")
            logger.error(f"❌ Dossier modules non trouvé : {self.modules_path}")
            return
        
        logger.info(f"📂 Scan du dossier : {self.modules_path}")
        
        # Scanner les fichiers Python
        module_files = list(self.modules_path.glob("*.py"))
        logger.info(f"📋 Fichiers trouvés : {[f.name for f in module_files]}")
        
        for module_file in module_files:
            if module_file.name.startswith("_"):
                continue
                
            module_name = module_file.stem
            logger.info(f"🔍 Analyse du module : {module_name}")
            
            # Chercher d'abord dans MODULES_CONFIG
            if module_name in MODULES_CONFIG:
                self.available_modules[module_name] = {
                    "path": module_file,
                    "config": MODULES_CONFIG[module_name],
                    "loaded": False
                }
                logger.info(f"✅ Module reconnu : {module_name}")
            # Puis dans MODULES_TO_CREATE (au cas où ils ont été créés)
            elif module_name in MODULES_TO_CREATE:
                self.available_modules[module_name] = {
                    "path": module_file,
                    "config": MODULES_TO_CREATE[module_name],
                    "loaded": False
                }
                logger.info(f"✅ Module optionnel trouvé : {module_name}")
            else:
                logger.warning(f"⚠️ Module non configuré : {module_name}")
                self.load_status["warnings"].append(f"Module {module_name} trouvé mais non configuré")
    
    def load_module(self, module_name: str) -> bool:
        """Charge un module spécifique"""
        if module_name in self.loaded_modules:
            return True
            
        if module_name not in self.available_modules:
            self.load_status["failed"][module_name] = "Module non trouvé dans la configuration"
            return False
            
        module_info = self.available_modules[module_name]
        module_path = module_info["path"]
        
        try:
            # Import dynamique du module - CORRECTION ICI
            spec = importlib.util.spec_from_file_location(
                f"modules.{module_name}",  # Chemin corrigé
                module_path
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"modules.{module_name}"] = module
                spec.loader.exec_module(module)
                
                # Vérifier que le module a une fonction run() exécutable
                if callable(getattr(module, 'run', None)):
                    self.loaded_modules[module_name] = module
                    module_info["loaded"] = True
                    self.load_status["success"].append(module_name)
                    logger.info(f"✅ Module {module_name} chargé avec succès")
                    return True
                else:
                    self.load_status["failed"][module_name] = "Fonction run() non trouvée"
                    logger.error(f"❌ Module {module_name} : pas de fonction run()")
                    return False
            else:
                self.load_status["failed"][module_name] = "Impossible de créer les specs"
                return False
                
        except Exception as e:
            self.load_status["failed"][module_name] = str(e)
            logger.error(f"Erreur chargement {module_name}: {traceback.format_exc()}")
            return False
    
    def run_module(self, module_name: str):
        """Exécute un module"""
        if module_name not in self.loaded_modules:
            if not self.load_module(module_name):
                st.error(f"❌ Impossible de charger le module {module_name}")
                if module_name in self.load_status["failed"]:
                    st.error(f"Erreur : {self.load_status['failed'][module_name]}")
                return
        
        try:
            # Exécuter le module
            self.loaded_modules[module_name].run()
        except Exception as e:
            st.error(f"❌ Erreur lors de l'exécution du module {module_name}")
            st.error(str(e))
            logger.error(f"Erreur exécution {module_name}: {traceback.format_exc()}")
    
    def get_modules_by_category(self) -> Dict[str, List[Dict]]:
        """Retourne les modules groupés par catégorie"""
        modules_by_cat = {}
        
        for name, info in self.available_modules.items():
            config = info["config"]
            category = config.get("category", "autre")
            
            if category not in modules_by_cat:
                modules_by_cat[category] = []
            
            modules_by_cat[category].append({
                "id": name,
                "name": config["name"],
                "desc": config["desc"],
                "loaded": info["loaded"],
                "priority": config.get("priority", 99)
            })
        
        # Trier par priorité
        for category in modules_by_cat:
            modules_by_cat[category].sort(key=lambda x: x["priority"])
        
        return modules_by_cat

# ========== GESTIONNAIRE MULTI-LLM ==========
def load_multi_llm_manager():
    """Charge le gestionnaire multi-LLM"""
    try:
        from managers.multi_llm_manager import MultiLLMManager
        return MultiLLMManager(), True
    except ImportError:
        logger.warning("MultiLLMManager non disponible")
        return None, False
    except Exception as e:
        logger.error(f"Erreur chargement MultiLLMManager: {e}")
        return None, False

# ========== INITIALISATION ==========
def init_session_state():
    """Initialise l'état de session"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_view = 'dashboard'
        st.session_state.module_manager = ModuleManager()
        st.session_state.multi_llm_manager = None
        st.session_state.azure_connected = False

        # Créer les gestionnaires Azure et les stocker
        st.session_state.azure_blob_manager = AzureBlobManager()
        st.session_state.azure_search_manager = AzureSearchManager()

        # Enregistrer les erreurs éventuelles
        st.session_state.azure_blob_error = st.session_state.azure_blob_manager.get_connection_error()
        st.session_state.azure_search_error = st.session_state.azure_search_manager.get_connection_error()

        st.session_state.azure_connected = (
            st.session_state.azure_blob_manager.is_connected()
            and st.session_state.azure_search_manager.is_connected()
        )
        
        # Découvrir les modules
        st.session_state.module_manager.discover_modules()
        
        # Charger le gestionnaire LLM
        llm_manager, llm_success = load_multi_llm_manager()
        if llm_success:
            st.session_state.multi_llm_manager = llm_manager

# ========== INTERFACE PRINCIPALE ==========
def show_dashboard():
    """Affiche le tableau de bord principal"""
    st.markdown('<h1 class="main-header">⚖️ IA Juridique - Droit Pénal des Affaires</h1>', unsafe_allow_html=True)

    # Barre de recherche
    search_query = st.text_input(
        "🔍 Recherche de dossier ou commande",
        placeholder="Ex: @DOSSIER123",
        key="dashboard_search",
    )

    if search_query.startswith("@"):
        st.info(f"Recherche dossier : {search_query[1:]}")

    if search_query:
        suggestion = next(
            (s for s in LEGAL_SUGGESTIONS if s.lower().startswith(search_query.lower())),
            None,
        )
        if suggestion:
            st.markdown(f"💡 Suggestion : *{suggestion}*")

    search_service = UniversalSearchService()

    if search_query:
        query_to_use = search_query

        if search_query.startswith("@"):
            folder = search_query[1:].split()[0]
            st.info(f"Recherche dossier : {folder}")

            # Obtenir le gestionnaire de documents
            doc_manager = st.session_state.get("doc_manager")
            if doc_manager is None:
                doc_manager = DocumentManager()
                st.session_state.doc_manager = doc_manager

            folder_summary = doc_manager.get_summary(folder)
            if folder_summary:
                query_to_use = f"Contexte dossier : {folder_summary}\n\n{search_query}"

        if not search_query.startswith("#"):
            results = search_service.search(query_to_use)
            st.table(results)

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_modules = len(st.session_state.module_manager.available_modules)
        st.metric("📦 Modules disponibles", total_modules, delta="+1" if total_modules > 8 else None)
    
    with col2:
        loaded_modules = len(st.session_state.module_manager.loaded_modules)
        st.metric("✅ Modules chargés", loaded_modules)
    
    with col3:
        llm_status = "✅" if st.session_state.multi_llm_manager else "❌"
        st.metric("🤖 Multi-LLM", llm_status)
    
    with col4:
        missing_count = len([m for m in MODULES_TO_CREATE if not (Path(__file__).parent / "modules" / f"{m}.py").exists()])
        st.metric("📋 À créer", missing_count, delta=f"-{15-missing_count}" if missing_count < 15 else None)
    
    st.markdown("---")
    
    # Afficher les modules non configurés s'il y en a
    show_modules_unconfigured()
    
    # Alerte si des modules manquent
    missing_modules = []
    for module_id in MODULES_TO_CREATE:
        module_path = Path(__file__).parent / "modules" / f"{module_id}.py"
        if not module_path.exists():
            missing_modules.append(module_id)
    
    if missing_modules:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning(f"⚠️ {len(missing_modules)} modules supplémentaires peuvent être créés pour étendre les fonctionnalités")
        with col2:
            if st.button("📋 Voir les détails", key="show_missing"):
                st.session_state.show_missing_details = not st.session_state.get('show_missing_details', False)
        
        if st.session_state.get('show_missing_details', False):
            with st.expander("Modules disponibles à la création", expanded=True):
                for module_id in missing_modules:
                    config = MODULES_TO_CREATE[module_id]
                    st.write(f"• **{config['name']}** - {config['desc']}")
                
                if st.button("🔧 Créer tous les modules manquants", type="primary"):
                    create_missing_modules()
                    st.rerun()
    else:
        st.success("✅ Tous les modules optionnels ont été créés !")
    
    # Modules par catégorie
    modules_by_cat = st.session_state.module_manager.get_modules_by_category()
    
    if not modules_by_cat:
        st.warning("⚠️ Aucun module trouvé. Vérifiez la structure du projet.")
        show_troubleshooting()
        return
    
    # Afficher les modules par catégorie
    categories_display = {
        "analyse": ("📊 Analyse", "Modules d'analyse et extraction"),
        "strategie": ("⚖️ Stratégie", "Modules de stratégie juridique"),
        "redaction": ("✍️ Rédaction", "Modules de génération de documents"),
        "gestion": ("📁 Gestion", "Modules de gestion des dossiers"),
        "specialise": ("🎯 Spécialisé", "Modules spécialisés"),
        "communication": ("💬 Communication", "Modules de communication"),
        "technique": ("🔧 Technique", "Modules techniques"),
        "autre": ("📦 Autres", "Modules divers")
    }
    
    for cat_key, (cat_title, cat_desc) in categories_display.items():
        if cat_key in modules_by_cat:
            st.markdown(f"### {cat_title}")
            st.caption(cat_desc)
            
            cols = st.columns(3)
            for idx, module in enumerate(modules_by_cat[cat_key]):
                with cols[idx % 3]:
                    # Carte de module
                    status_icon = "✅" if module["loaded"] else "⚠️"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="module-card">
                            <h4>{status_icon} {module['name']}</h4>
                            <p style="color: #666; font-size: 0.9em;">{module['desc']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(
                            "Ouvrir", 
                            key=f"open_{module['id']}", 
                            use_container_width=True
                        ):
                            st.session_state.current_view = module['id']
                            st.rerun()
            
            st.markdown("")

def show_sidebar():
    """Affiche la barre latérale"""
    with st.sidebar:
        st.markdown("## ⚖️ Navigation")
        st.markdown(f"📌 Dossier courant : @{st.session_state.selected_folder}")
        st.markdown(f"📌 Module courant : #{st.session_state.selected_module}")

        # Bouton Accueil
        if st.button("🏠 Tableau de bord", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.rerun()
        
        st.markdown("---")
        
        # Modules rapides (seulement ceux qui existent)
        st.markdown("### 🚀 Accès rapide")
        quick_modules = ["recherche_analyse_unifiee", "import_export", "strategy", "redaction_unified", "email", "jurisprudence"]
        
        for module_id in quick_modules:
            if module_id in st.session_state.module_manager.available_modules:
                config = st.session_state.module_manager.available_modules[module_id]["config"]
                if st.button(config["name"], use_container_width=True, key=f"quick_{module_id}"):
                    st.session_state.current_view = module_id
                    st.rerun()
        
        st.markdown("---")
        
        # Statut système
        st.markdown("### 📊 Statut système")
        
        # Modules existants
        available = len(st.session_state.module_manager.available_modules)
        total_possible = len(MODULES_CONFIG) + len(MODULES_TO_CREATE)
        missing = len([m for m in MODULES_TO_CREATE if not (Path(__file__).parent / "modules" / f"{m}.py").exists()])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 Existants", available)
        with col2:
            st.metric("📋 Optionnels", missing)
        
        # Barre de progression
        progress = available / total_possible
        st.progress(progress)
        st.caption(f"{available}/{total_possible} modules")
        
        # Statut des chargements
        status = st.session_state.module_manager.load_status
        if status["success"]:
            st.success(f"✅ {len(status['success'])} chargés")
        if status["failed"]:
            st.error(f"❌ {len(status['failed'])} erreurs")

        # Afficher les erreurs de connexion Azure
        blob_error = None
        search_error = None
        if 'azure_blob_manager' in st.session_state:
            blob_error = st.session_state.azure_blob_manager.get_connection_error()
        if 'azure_search_manager' in st.session_state:
            search_error = st.session_state.azure_search_manager.get_connection_error()

        if blob_error:
            st.error(f"Azure Blob: {blob_error}")
        if search_error:
            st.error(f"Azure Search: {search_error}")
        
        # Boutons d'action
        st.markdown("---")
        
        if st.button("🔧 Diagnostic", use_container_width=True):
            st.session_state.current_view = 'diagnostic'
            st.rerun()
        
        if missing > 0:
            if st.button("➕ Créer modules optionnels", use_container_width=True, type="primary"):
                st.session_state.current_view = 'create_modules'
                st.rerun()

def show_diagnostic():
    """Affiche la page de diagnostic"""
    st.markdown("## 🔧 Diagnostic du système")
    
    # État des modules
    st.markdown("### 📦 État des modules")
    
    manager = st.session_state.module_manager
    
    # Tableau récapitulatif
    data = []
    for name, info in manager.available_modules.items():
        status = "✅ Chargé" if info["loaded"] else "⚠️ Non chargé"
        error = manager.load_status["failed"].get(name, "-")
        data.append({
            "Module": info["config"]["name"],
            "ID": name,
            "Catégorie": info["config"]["category"],
            "État": status,
            "Erreur": error
        })
    
    if data:
        st.dataframe(data, use_container_width=True, hide_index=True)
    
    # Afficher les avertissements
    if manager.load_status["warnings"]:
        st.warning("### ⚠️ Avertissements")
        for warning in manager.load_status["warnings"]:
            st.warning(warning)
    
    # Liste des fichiers Python dans le dossier modules
    st.markdown("### 📁 Fichiers dans le dossier modules")
    if manager.modules_path.exists():
        py_files = sorted([f.stem for f in manager.modules_path.glob("*.py") if not f.name.startswith("_")])
        cols = st.columns(3)
        for i, file_name in enumerate(py_files):
            with cols[i % 3]:
                if file_name in manager.available_modules:
                    st.success(f"✅ {file_name}")
                elif file_name in MODULES_CONFIG or file_name in MODULES_TO_CREATE:
                    st.info(f"📋 {file_name} (configuré)")
                else:
                    st.warning(f"❓ {file_name} (non configuré)")
    
    # Actions de réparation
    st.markdown("### 🛠️ Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recharger tous les modules"):
            manager.discover_modules()
            st.rerun()
    
    with col2:
        if st.button("📋 Créer modules manquants"):
            create_missing_modules()
    
    with col3:
        if st.button("📥 Exporter diagnostic"):
            export_diagnostic()



def show_troubleshooting():
    """Affiche l'aide au dépannage"""
    st.markdown("### 🛠️ Dépannage")
    
    # Vérifier les modules non configurés
    modules_path = Path(__file__).parent / "modules"
    if modules_path.exists():
        all_py_files = [f.stem for f in modules_path.glob("*.py") if not f.name.startswith("_")]
        configured_modules = set(MODULES_CONFIG.keys()) | set(MODULES_TO_CREATE.keys())
        unconfigured = set(all_py_files) - configured_modules
        
        if unconfigured:
            st.warning(f"⚠️ {len(unconfigured)} modules trouvés mais non configurés")
            with st.expander("Voir les modules non configurés"):
                for module in sorted(unconfigured):
                    st.write(f"• {module}.py")
                st.info("Ces modules doivent être ajoutés à MODULES_CONFIG pour être utilisables")
    
    st.info("""
    **Aucun module trouvé ?** Voici les étapes à suivre :
    
    1. **Vérifiez la structure** :
       ```
       votre_projet/
       ├── app.py
       ├── modules/
       │   ├── __init__.py
       │   ├── comparison.py
       │   ├── timeline.py
       │   └── ...
       └── managers/
           ├── __init__.py
           └── multi_llm_manager.py
       ```
    
    2. **Créez le dossier modules** s'il n'existe pas
    
    3. **Vérifiez que chaque module a une fonction run()** :
       ```python
       def run():
           st.write("Module fonctionne!")
       ```
    
    4. **Redémarrez l'application**
    
    5. **Consultez le diagnostic** pour voir les erreurs détaillées
    """)

def show_modules_unconfigured():
    """Affiche les modules non configurés"""
    modules_path = Path(__file__).parent / "modules"
    if modules_path.exists():
        all_py_files = [f.stem for f in modules_path.glob("*.py") if not f.name.startswith("_")]
        configured_modules = set(MODULES_CONFIG.keys()) | set(MODULES_TO_CREATE.keys())
        unconfigured = set(all_py_files) - configured_modules
        
        if unconfigured:
            st.warning(f"### ⚠️ Modules non configurés ({len(unconfigured)})")
            st.info("Ces modules existent mais ne sont pas dans la configuration :")
            
            cols = st.columns(3)
            for i, module in enumerate(sorted(unconfigured)):
                with cols[i % 3]:
                    st.code(f"{module}.py")
            
            st.markdown("""
            **Pour les utiliser :**
            1. Ajoutez-les à `MODULES_CONFIG` dans `app.py`
            2. Spécifiez leur nom, description et catégorie
            3. Redémarrez l'application
            """)
            
            # Proposer un template de configuration
            if st.button("📋 Générer template de configuration"):
                config_template = {}
                for module in sorted(unconfigured):
                    config_template[module] = {
                        "name": f"📄 {module.replace('_', ' ').title()}",
                        "desc": f"Module {module}",
                        "category": "autre",
                        "priority": 10
                    }
                st.code(json.dumps(config_template, indent=2))

def create_missing_modules():
    """Crée les modules manquants avec un template de base"""
    modules_path = Path(__file__).parent / "modules"
    modules_path.mkdir(exist_ok=True)
    
    template = '''"""Module {name}"""
import streamlit as st

def run():
    """Point d'entrée du module"""
    st.title("{title}")
    st.info("Ce module est en cours de développement")
    
    # Interface basique
    st.markdown("### 🚧 En construction")
    st.write("Les fonctionnalités seront bientôt disponibles.")
'''
    
    created = []
    # Créer les modules existants manquants
    for module_id, config in MODULES_CONFIG.items():
        module_path = modules_path / f"{module_id}.py"
        if not module_path.exists():
            content = template.format(
                name=module_id,
                title=config["name"]
            )
            module_path.write_text(content, encoding='utf-8')
            created.append(module_id)
    
    # Créer les modules supplémentaires
    for module_id, config in MODULES_TO_CREATE.items():
        module_path = modules_path / f"{module_id}.py"
        if not module_path.exists():
            content = template.format(
                name=module_id,
                title=config["name"]
            )
            module_path.write_text(content, encoding='utf-8')
            created.append(module_id)
    
    if created:
        st.success(f"✅ {len(created)} modules créés : {', '.join(created)}")
        st.info("Relancez l'application pour charger les nouveaux modules")
    else:
        st.info("Tous les modules existent déjà")

def export_diagnostic():
    """Exporte le diagnostic complet"""
    diagnostic = {
        "timestamp": datetime.now().isoformat(),
        "modules": {},
        "system": {
            "python_version": sys.version,
            "streamlit_version": st.__version__,
            "working_directory": str(Path.cwd()),
            "modules_path": str(Path(__file__).parent / "modules")
        },
        "available_files": []
    }
    
    # État des modules
    for name, info in st.session_state.module_manager.available_modules.items():
        diagnostic["modules"][name] = {
            "config": info["config"],
            "loaded": info["loaded"],
            "error": st.session_state.module_manager.load_status["failed"].get(name),
            "path": str(info["path"])
        }
    
    # Liste des fichiers dans le dossier modules
    modules_path = Path(__file__).parent / "modules"
    if modules_path.exists():
        diagnostic["available_files"] = [
            f.name for f in modules_path.glob("*.py") 
            if not f.name.startswith("_")
        ]
    
    # Téléchargement
    st.download_button(
        "💾 Télécharger diagnostic.json",
        json.dumps(diagnostic, indent=2),
        "diagnostic.json",
        "application/json"
    )

# ========== FONCTION PRINCIPALE ==========
def main():
    """Point d'entrée principal"""
    init_session_state()
    
    # Sidebar
    show_sidebar()
    
    # Router vers la vue appropriée
    current_view = st.session_state.current_view
    
    if current_view == 'dashboard':
        show_dashboard()
    elif current_view == 'diagnostic':
        show_diagnostic()
    elif current_view == 'create_modules':
        st.markdown("## ➕ Création des modules optionnels")
        st.info("""
        Les modules ci-dessous sont **optionnels** et peuvent étendre les fonctionnalités de votre application.
        Vous pouvez les créer maintenant ou plus tard selon vos besoins.
        """)
        
        # Afficher les modules optionnels par catégorie
        missing_by_cat = {}
        for module_id, config in MODULES_TO_CREATE.items():
            module_path = Path(__file__).parent / "modules" / f"{module_id}.py"
            if not module_path.exists():
                cat = config.get('category', 'autre')
                if cat not in missing_by_cat:
                    missing_by_cat[cat] = []
                missing_by_cat[cat].append((module_id, config))
        
        if missing_by_cat:
            for cat, modules in missing_by_cat.items():
                st.markdown(f"### {cat.title()}")
                for module_id, config in modules:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{config['name']}** - {config['desc']}")
                    with col2:
                        if st.button("Créer", key=f"create_{module_id}"):
                            create_single_module(module_id, config)
                            st.success(f"✅ Module {module_id} créé")
            
            st.markdown("---")
            if st.button("🔧 Créer tous les modules", type="primary"):
                create_missing_modules()
                st.rerun()
        else:
            st.success("✅ Tous les modules optionnels ont déjà été créés !")
        
        if st.button("↩️ Retour au tableau de bord"):
            st.session_state.current_view = 'dashboard'
            st.rerun()
    elif current_view in st.session_state.module_manager.available_modules:
        # Charger et exécuter le module
        st.session_state.module_manager.run_module(current_view)
    else:
        show_dashboard()
    
    # Footer
    st.markdown("---")
    modules_count = len(st.session_state.module_manager.available_modules)
    st.markdown(
        f"""<p style='text-align: center; color: #666; font-size: 0.8rem;'>
        IA Juridique v2.0 - Droit Pénal des Affaires • {modules_count} modules disponibles • Système modulaire optimisé
        </p>""",
        unsafe_allow_html=True
    )

def create_single_module(module_id: str, config: dict):
    """Crée un seul module"""
    modules_path = Path(__file__).parent / "modules"
    modules_path.mkdir(exist_ok=True)
    
    template = '''"""Module {name}"""
import streamlit as st

def run():
    """Point d'entrée du module"""
    st.title("{title}")
    st.info("Ce module est en cours de développement")
    
    # Interface basique
    st.markdown("### 🚧 En construction")
    st.write("Les fonctionnalités seront bientôt disponibles.")
'''
    
    module_path = modules_path / f"{module_id}.py"
    if not module_path.exists():
        content = template.format(
            name=module_id,
            title=config["name"]
        )
        module_path.write_text(content, encoding='utf-8')

if __name__ == "__main__":
    main()