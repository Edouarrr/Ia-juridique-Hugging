# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
Détection automatique des fonctions disponibles dans chaque module
"""

import inspect
import importlib
import sys
import os
from typing import Dict, Any, List, Tuple, Callable
from datetime import datetime

# Mode debug
DEBUG_MODE = os.environ.get('DEBUG_MODULES', 'false').lower() == 'true'

# Import des dataclasses depuis ce module
try:
    from .dataclasses import *
except ImportError:
    pass

# IMPORTANT: Liste des modules avec les VRAIS noms de fichiers
MODULES_LIST = [
    # Modules principaux (vérifiés dans votre liste)
    'analyse_ia',           # analyse_ia.py ✓
    'bordereau',            # bordereau.py ✓
    'comparison',           # comparison.py ✓
    'configuration',        # configuration.py ✓
    'dataclasses',          # dataclasses.py ✓
    'dossier_penal',        # dossier_penal.py ✓
    'email',                # email.py ✓
    'explorer',             # explorer.py ✓
    'export_juridique',     # export_juridique.py ✓
    'generation_juridique', # generation_juridique.py ✓
    'generation-longue',    # generation-longue.py ✓ (avec tiret!)
    'import_export',        # import_export.py ✓
    'integration_juridique',# integration_juridique.py ✓
    'jurisprudence',        # jurisprudence.py ✓
    'mapping',              # mapping.py ✓
    'pieces_manager',       # pieces_manager.py ✓
    'plaidoirie',           # plaidoirie.py ✓
    'preparation_client',   # preparation_client.py ✓
    'recherche',            # recherche.py ✓
    'redaction',            # redaction.py ✓
    'redaction_unified',    # redaction_unified.py ✓
    'risques',              # risques.py ✓
    'selection_pieces',     # selection_pieces.py ✓
    'synthesis',            # synthesis.py ✓
    'template',             # template.py ✓ (sans 's'!)
    'timeline',             # timeline.py ✓
]

# Dictionnaire pour stocker les erreurs
_import_errors = {}
_function_detection_errors = {}

def safe_import_module(module_name: str):
    """Import sécurisé d'un module avec gestion des noms spéciaux"""
    try:
        # Gérer les modules avec tirets (remplacer par underscore pour l'import)
        import_name = module_name.replace('-', '_')
        
        # Tenter l'import
        if '-' in module_name:
            # Pour les modules avec tirets, utiliser importlib
            module = importlib.import_module(f'.{module_name}', package='modules')
        else:
            # Import normal
            module = importlib.import_module(f'.{module_name}', package='modules')
        
        return module
    except ImportError as e:
        _import_errors[module_name] = str(e)
        return None
    except Exception as e:
        _import_errors[module_name] = f"Erreur inattendue: {str(e)}"
        return None

def get_module_functions(module) -> Dict[str, str]:
    """Détecte automatiquement toutes les fonctions d'un module"""
    functions = {}
    
    try:
        for name, obj in inspect.getmembers(module):
            if (inspect.isfunction(obj) and 
                obj.__module__ == module.__name__ and
                not name.startswith('_')):
                
                doc = inspect.getdoc(obj)
                if doc:
                    description = doc.split('\n')[0].strip()
                    if len(description) > 100:
                        description = description[:97] + "..."
                    description = description.rstrip('"\'')
                else:
                    description = name.replace('_', ' ').title()
                    replacements = {
                        'Display ': 'Afficher ',
                        'Create ': 'Créer ',
                        'Process ': 'Traiter ',
                        'Generate ': 'Générer ',
                        'Export ': 'Exporter ',
                        'Import ': 'Importer ',
                        'Show ': 'Afficher ',
                        'Get ': 'Obtenir ',
                        'Set ': 'Définir ',
                        'Update ': 'Mettre à jour ',
                        'Delete ': 'Supprimer ',
                        'Validate ': 'Valider ',
                    }
                    for eng, fr in replacements.items():
                        description = description.replace(eng, fr)
                
                functions[name] = description
                
    except Exception as e:
        _function_detection_errors[module.__name__] = str(e)
    
    return functions

def create_stub_module(module_name: str):
    """Crée un module stub pour éviter les erreurs"""
    import types
    stub_module = types.ModuleType(module_name)
    stub_module.__file__ = f"<stub for {module_name}>"
    stub_module.MODULE_FUNCTIONS = {}
    
    def not_implemented(*args, **kwargs):
        return f"Module {module_name} non implémenté"
    
    stub_module.not_implemented = not_implemented
    return stub_module

# Gestion des imports manquants dans dataclasses
def patch_missing_dataclasses():
    """Ajoute les dataclasses manquantes si nécessaire"""
    try:
        import modules.dataclasses as dc
        
        # Ajouter les classes manquantes si elles n'existent pas
        if not hasattr(dc, 'EmailConfig'):
            class EmailConfig:
                def __init__(self):
                    self.smtp_server = ""
                    self.smtp_port = 587
                    self.sender = ""
            setattr(dc, 'EmailConfig', EmailConfig)
        
        if not hasattr(dc, 'Relationship'):
            class Relationship:
                def __init__(self, source="", target="", type=""):
                    self.source = source
                    self.target = target
                    self.type = type
            setattr(dc, 'Relationship', Relationship)
        
        if not hasattr(dc, 'PlaidoirieResult'):
            class PlaidoirieResult:
                def __init__(self, content="", success=False):
                    self.content = content
                    self.success = success
            setattr(dc, 'PlaidoirieResult', PlaidoirieResult)
        
        if not hasattr(dc, 'PreparationClientResult'):
            class PreparationClientResult:
                def __init__(self, documents=None, notes=""):
                    self.documents = documents or []
                    self.notes = notes
            setattr(dc, 'PreparationClientResult', PreparationClientResult)
            
    except Exception as e:
        print(f"Erreur lors du patch des dataclasses: {e}")

# Gestion des imports manquants dans utils.helpers
def patch_missing_helpers():
    """Ajoute les fonctions manquantes dans helpers si nécessaire"""
    try:
        import utils.helpers as helpers
        
        if not hasattr(helpers, 'truncate_text'):
            def truncate_text(text: str, max_length: int = 100) -> str:
                """Tronque un texte à une longueur maximale"""
                if len(text) <= max_length:
                    return text
                return text[:max_length-3] + "..."
            setattr(helpers, 'truncate_text', truncate_text)
            
    except Exception as e:
        print(f"Erreur lors du patch des helpers: {e}")

# Appliquer les patches
patch_missing_dataclasses()
patch_missing_helpers()

# Compteurs
_modules_loaded = 0
_modules_failed = 0
_modules_stubbed = 0
_total_functions = 0

# Import dynamique de tous les modules
for module_name in MODULES_LIST:
    try:
        # Import sécurisé
        module = safe_import_module(module_name)
        
        if module:
            # Rendre le module disponible (remplacer les tirets par underscores pour l'accès)
            access_name = module_name.replace('-', '_')
            globals()[access_name] = module
            _modules_loaded += 1
            
            # Créer MODULE_FUNCTIONS si absent
            if not hasattr(module, 'MODULE_FUNCTIONS'):
                detected_functions = get_module_functions(module)
                
                if detected_functions:
                    setattr(module, 'MODULE_FUNCTIONS', detected_functions)
                    _total_functions += len(detected_functions)
                    if DEBUG_MODE:
                        print(f"✅ Module {module_name}: {len(detected_functions)} fonctions détectées")
                else:
                    setattr(module, 'MODULE_FUNCTIONS', {})
                    if DEBUG_MODE:
                        print(f"ℹ️ Module {module_name}: aucune fonction publique détectée")
            else:
                _total_functions += len(getattr(module, 'MODULE_FUNCTIONS', {}))
                if DEBUG_MODE:
                    print(f"✅ Module {module_name}: MODULE_FUNCTIONS existant conservé")
        else:
            # Créer un stub pour éviter les erreurs
            _modules_failed += 1
            access_name = module_name.replace('-', '_')
            
            try:
                stub = create_stub_module(module_name)
                globals()[access_name] = stub
                _modules_stubbed += 1
                if DEBUG_MODE:
                    print(f"⚠️ Module {module_name} non trouvé - stub créé")
            except Exception as stub_error:
                if DEBUG_MODE:
                    print(f"❌ Impossible de créer un stub pour {module_name}: {stub_error}")
            
    except Exception as e:
        _import_errors[module_name] = str(e)
        _modules_failed += 1
        if DEBUG_MODE:
            print(f"❌ Erreur avec module {module_name}: {e}")

# Créer des alias pour les modules manquants
# documents_longs n'existe pas, créer un stub
if 'documents_longs' not in globals():
    globals()['documents_longs'] = create_stub_module('documents_longs')

# templates -> template (alias)
if 'template' in globals() and 'templates' not in globals():
    globals()['templates'] = globals()['template']

# generation_longue -> generation-longue (alias)
if 'generation_longue' in globals():
    globals()['generation-longue'] = globals()['generation_longue']

# Fonctions utilitaires
def get_loaded_modules() -> Dict[str, Any]:
    """Retourne un dictionnaire de tous les modules chargés avec succès"""
    loaded = {}
    # Inclure tous les noms possibles (avec tirets et underscores)
    for module_name in MODULES_LIST:
        access_name = module_name.replace('-', '_')
        if access_name in globals():
            loaded[access_name] = globals()[access_name]
        if module_name in globals():
            loaded[module_name] = globals()[module_name]
    return loaded

def get_module_functions_by_name(module_name: str) -> Dict[str, str]:
    """Retourne MODULE_FUNCTIONS pour un module donné"""
    # Essayer avec le nom original et avec underscore
    access_name = module_name.replace('-', '_')
    
    for name in [module_name, access_name]:
        if name in globals():
            module = globals()[name]
            return getattr(module, 'MODULE_FUNCTIONS', {})
    return {}

def list_all_modules_and_functions() -> Dict[str, Dict[str, str]]:
    """Retourne un dictionnaire de tous les modules et leurs fonctions"""
    result = {}
    for module_name, module in get_loaded_modules().items():
        result[module_name] = getattr(module, 'MODULE_FUNCTIONS', {})
    return result

def get_module_status(module_name: str) -> Dict[str, Any]:
    """Retourne le statut détaillé d'un module"""
    status = {
        'loaded': False,
        'functions_count': 0,
        'functions': {},
        'error': None,
        'is_stub': False
    }
    
    # Essayer les deux noms
    access_name = module_name.replace('-', '_')
    
    for name in [module_name, access_name]:
        if name in globals():
            module = globals()[name]
            status['loaded'] = True
            status['functions'] = getattr(module, 'MODULE_FUNCTIONS', {})
            status['functions_count'] = len(status['functions'])
            
            if hasattr(module, '__file__') and module.__file__.startswith('<stub'):
                status['is_stub'] = True
                
            if module_name in _import_errors:
                status['error'] = _import_errors[module_name]
            
            return status
    
    status['error'] = _import_errors.get(module_name, f"Module '{module_name}' non chargé")
    return status

def debug_modules_status(detailed: bool = False, output_to_streamlit: bool = False):
    """Affiche le statut de tous les modules"""
    loaded = get_loaded_modules()
    
    output_lines = []
    output_lines.append(f"\n{'='*60}")
    output_lines.append(f"📦 ÉTAT DES MODULES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"{'='*60}")
    output_lines.append(f"Modules chargés: {_modules_loaded}/{len(MODULES_LIST)}")
    output_lines.append(f"Modules en erreur: {_modules_failed}")
    output_lines.append(f"Modules stub: {_modules_stubbed}")
    output_lines.append(f"Total fonctions: {_total_functions}")
    
    if _import_errors:
        output_lines.append(f"\n❌ Erreurs d'import:")
        for module_name, error in _import_errors.items():
            output_lines.append(f"  - {module_name}: {error}")
    
    output_lines.append(f"\n📋 Détail par module:")
    output_lines.append(f"{'-'*60}")
    
    modules_ok = []
    modules_stub = []
    modules_error = []
    
    for module_name in MODULES_LIST:
        status = get_module_status(module_name)
        if status['loaded'] and not status['is_stub']:
            modules_ok.append((module_name, status))
        elif status['is_stub']:
            modules_stub.append((module_name, status))
        else:
            modules_error.append((module_name, status))
    
    if modules_ok:
        output_lines.append("\n🟢 Modules chargés avec succès:")
        for module_name, status in sorted(modules_ok):
            output_lines.append(f"  ✅ {module_name:<25} : {status['functions_count']} fonctions")
    
    if modules_stub:
        output_lines.append("\n🟡 Modules stub:")
        for module_name, status in sorted(modules_stub):
            output_lines.append(f"  ⚠️  {module_name:<25} : stub créé")
    
    if modules_error:
        output_lines.append("\n🔴 Modules en erreur:")
        for module_name, status in sorted(modules_error):
            output_lines.append(f"  ❌ {module_name:<25} : {status['error']}")
    
    output_lines.append(f"{'-'*60}")
    output_lines.append(f"{'='*60}\n")
    
    output_text = '\n'.join(output_lines)
    
    if output_to_streamlit:
        return output_text
    else:
        print(output_text)

# Export
__all__ = [
    'dataclasses',
    'get_loaded_modules',
    'get_module_functions_by_name',
    'list_all_modules_and_functions',
    'debug_modules_status',
    'get_module_status',
    'create_stub_module'
] + [name.replace('-', '_') for name in MODULES_LIST] + ['documents_longs', 'templates']

# Fonction pour Streamlit
def create_streamlit_debug_page():
    """Crée une page de debug pour Streamlit"""
    import streamlit as st
    
    st.title("🔧 Debug des Modules")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Modules chargés", f"{_modules_loaded}/{len(MODULES_LIST)}")
    with col2:
        st.metric("Modules en erreur", _modules_failed)
    with col3:
        st.metric("Modules stub", _modules_stubbed)
    with col4:
        st.metric("Total fonctions", _total_functions)
    
    tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "❌ Erreurs", "🔍 Détails"])
    
    with tab1:
        st.subheader("État des modules")
        
        with st.expander(f"✅ Modules OK ({_modules_loaded - _modules_stubbed})", expanded=True):
            for module_name in sorted(MODULES_LIST):
                status = get_module_status(module_name)
                if status['loaded'] and not status['is_stub']:
                    st.success(f"{module_name}: {status['functions_count']} fonctions")
        
        with st.expander(f"⚠️ Modules Stub ({_modules_stubbed})"):
            for module_name in sorted(MODULES_LIST):
                status = get_module_status(module_name)
                if status['is_stub']:
                    st.warning(f"{module_name}: stub créé")
    
    with tab2:
        st.subheader("Erreurs d'import détaillées")
        
        if _import_errors:
            for module_name, error in _import_errors.items():
                with st.expander(f"❌ {module_name}"):
                    st.error(error)
                    
                    # Suggestions de correction
                    if "No module named" in error:
                        st.info("💡 Ce module n'existe pas. Vérifiez le nom du fichier.")
                    elif "cannot import name" in error:
                        st.info("💡 La classe/fonction importée n'existe pas dans le module cible.")
                        st.code(f"# Ajoutez cette classe dans {error.split('from')[1].strip()}")
        else:
            st.success("Aucune erreur d'import !")
    
    with tab3:
        st.subheader("Détails des modules")
        
        selected_module = st.selectbox(
            "Sélectionner un module",
            options=MODULES_LIST,
            format_func=lambda x: f"{x} {'✅' if get_module_status(x)['loaded'] else '❌'}"
        )
        
        if selected_module:
            status = get_module_status(selected_module)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**État:** {'Chargé' if status['loaded'] else 'Non chargé'}")
                st.write(f"**Type:** {'Stub' if status['is_stub'] else 'Normal'}")
                st.write(f"**Fonctions:** {status['functions_count']}")
            
            with col2:
                if status['error']:
                    st.error(f"**Erreur:** {status['error']}")
            
            if status['functions']:
                st.write("**Liste des fonctions:**")
                for func_name, desc in sorted(status['functions'].items()):
                    st.write(f"- `{func_name}`: {desc}")

# Debug au chargement si activé
if DEBUG_MODE and __name__ != '__main__':
    debug_modules_status()

# Test
if __name__ == '__main__':
    print("Test du système de modules...")
    debug_modules_status(detailed=True)