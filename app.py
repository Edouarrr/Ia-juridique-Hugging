"""Application IA Juridique - Droit Pénal des Affaires - Version optimisée"""

import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import time
import logging
import traceback
import importlib
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

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
MODULES_CONFIG = {
    # Modules d'analyse
    "search_unified": {
        "name": "🔍 Recherche & Analyse unifiée",
        "desc": "Recherche intelligente multi-sources avec IA",
        "category": "analyse",
        "priority": 1
    },
    "comparison": {
        "name": "📊 Comparaison de documents",
        "desc": "Analyse comparative avec détection des contradictions",
        "category": "analyse",
        "priority": 2
    },
    "timeline_juridique": {
        "name": "📅 Timeline juridique",
        "desc": "Chronologie des infractions et procédures",
        "category": "analyse",
        "priority": 3
    },
    "extract_information": {
        "name": "📑 Extraction d'informations",
        "desc": "Extraction des éléments constitutifs",
        "category": "analyse",
        "priority": 4
    },
    "contradiction_analysis": {
        "name": "⚡ Analyse des contradictions",
        "desc": "Détection automatique des incohérences",
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
    "conclusions": {
        "name": "📝 Conclusions pénales",
        "desc": "Rédaction de conclusions",
        "category": "redaction",
        "priority": 2
    },
    "courrier": {
        "name": "📧 Courriers juridiques",
        "desc": "Correspondances et notifications",
        "category": "redaction",
        "priority": 3
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
            return
            
        # Scanner les fichiers Python
        for module_file in self.modules_path.glob("*.py"):
            if module_file.name.startswith("_"):
                continue
                
            module_name = module_file.stem
            if module_name in MODULES_CONFIG:
                self.available_modules[module_name] = {
                    "path": module_file,
                    "config": MODULES_CONFIG[module_name],
                    "loaded": False
                }
    
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
            # Import dynamique du module
            spec = importlib.util.spec_from_file_location(
                f"modules.{module_name}", 
                module_path
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"modules.{module_name}"] = module
                spec.loader.exec_module(module)
                
                # Vérifier que le module a une fonction run()
                if hasattr(module, 'run'):
                    self.loaded_modules[module_name] = module
                    module_info["loaded"] = True
                    self.load_status["success"].append(module_name)
                    return True
                else:
                    self.load_status["failed"][module_name] = "Fonction run() non trouvée"
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
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_modules = len(st.session_state.module_manager.available_modules)
        st.metric("📦 Modules disponibles", total_modules)
    
    with col2:
        loaded_modules = len(st.session_state.module_manager.loaded_modules)
        st.metric("✅ Modules chargés", loaded_modules)
    
    with col3:
        llm_status = "✅" if st.session_state.multi_llm_manager else "❌"
        st.metric("🤖 Multi-LLM", llm_status)
    
    with col4:
        azure_status = "✅" if st.session_state.azure_connected else "❌"
        st.metric("☁️ Azure", azure_status)
    
    st.markdown("---")
    
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
        "gestion": ("📁 Gestion", "Modules de gestion des dossiers")
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
        
        # Bouton Accueil
        if st.button("🏠 Tableau de bord", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.rerun()
        
        st.markdown("---")
        
        # Modules rapides
        st.markdown("### 🚀 Accès rapide")
        quick_modules = ["search_unified", "import_export", "strategy", "redaction_unified"]
        
        for module_id in quick_modules:
            if module_id in st.session_state.module_manager.available_modules:
                config = st.session_state.module_manager.available_modules[module_id]["config"]
                if st.button(config["name"], use_container_width=True, key=f"quick_{module_id}"):
                    st.session_state.current_view = module_id
                    st.rerun()
        
        st.markdown("---")
        
        # Statut système
        st.markdown("### 📊 Statut système")
        
        # Statut des modules
        status = st.session_state.module_manager.load_status
        if status["success"]:
            st.success(f"✅ {len(status['success'])} modules OK")
        if status["failed"]:
            st.error(f"❌ {len(status['failed'])} erreurs")
        if status["warnings"]:
            st.warning(f"⚠️ {len(status['warnings'])} avertissements")
        
        # Bouton diagnostic
        if st.button("🔧 Diagnostic", use_container_width=True):
            st.session_state.current_view = 'diagnostic'
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
    
    st.info("""
    **Aucun module trouvé ?** Voici les étapes à suivre :
    
    1. **Vérifiez la structure** :
       ```
       votre_projet/
       ├── app.py
       ├── modules/
       │   ├── __init__.py
       │   ├── search_unified.py
       │   └── ...
       └── managers/
           ├── __init__.py
           └── multi_llm_manager.py
       ```
    
    2. **Créez le dossier modules** s'il n'existe pas
    
    3. **Ajoutez un module test** :
       Créez `modules/test.py` avec :
       ```python
       import streamlit as st
       
       def run():
           st.write("Module test fonctionne!")
       ```
    
    4. **Redémarrez l'application**
    """)

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
    for module_id, config in MODULES_CONFIG.items():
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
            "working_directory": str(Path.cwd())
        }
    }
    
    # État des modules
    for name, info in st.session_state.module_manager.available_modules.items():
        diagnostic["modules"][name] = {
            "config": info["config"],
            "loaded": info["loaded"],
            "error": st.session_state.module_manager.load_status["failed"].get(name)
        }
    
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
    elif current_view in st.session_state.module_manager.available_modules:
        # Charger et exécuter le module
        st.session_state.module_manager.run_module(current_view)
    else:
        show_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: #666; font-size: 0.8rem;'>
        IA Juridique v2.0 - Droit Pénal des Affaires • Système modulaire optimisé
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()