# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
Détection automatique des fonctions disponibles dans chaque module

Ce fichier détecte automatiquement toutes les fonctions publiques de chaque module
et crée MODULE_FUNCTIONS dynamiquement si nécessaire.

Pour activer le mode debug : 
- Définir la variable d'environnement DEBUG_MODULES=true
- Ou appeler debug_modules_status() après l'import
"""

import inspect
import importlib
import sys
import os
from typing import Dict, Any, List, Tuple, Callable
from datetime import datetime

# Mode debug (activé via variable d'environnement ou streamlit)
DEBUG_MODE = os.environ.get('DEBUG_MODULES', 'false').lower() == 'true'

# Import des dataclasses depuis ce module
try:
    from .dataclasses import *
except ImportError:
    pass

# Liste de tous les modules possibles
MODULES_LIST = [
    'pieces_manager', 'redaction', 'timeline', 'recherche', 'dossier_penal',
    'bordereau', 'plaidoirie', 'mapping', 'email', 'preparation_client',
    'synthesis', 'templates', 'comparison', 'configuration', 'documents_longs',
    'explorer', 'import_export', 'jurisprudence', 'selection_pieces',
    'redaction_unified', 'risques', 'analyse_ia', 'export_juridique',
    'generation_juridique', 'generation_longue', 'integration_juridique'
]

# Dictionnaire pour stocker les erreurs d'import
_import_errors = {}
_function_detection_errors = {}

def get_module_functions(module) -> Dict[str, str]:
    """
    Détecte automatiquement toutes les fonctions d'un module
    et retourne un dictionnaire {nom_fonction: description}
    """
    functions = {}
    
    try:
        # Parcourir tous les membres du module
        for name, obj in inspect.getmembers(module):
            # Vérifier que c'est une fonction définie dans ce module
            if (inspect.isfunction(obj) and 
                obj.__module__ == module.__name__ and
                not name.startswith('_')):  # Ignorer les fonctions privées
                
                # Obtenir la docstring ou créer une description par défaut
                doc = inspect.getdoc(obj)
                if doc:
                    # Prendre la première ligne de la docstring
                    description = doc.split('\n')[0].strip()
                    # Limiter la longueur et enlever les guillemets finaux
                    if len(description) > 100:
                        description = description[:97] + "..."
                    description = description.rstrip('"\'')
                else:
                    # Créer une description basée sur le nom
                    description = name.replace('_', ' ').title()
                    # Améliorer certains patterns courants
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
                        'Search ': 'Rechercher ',
                        'Load ': 'Charger ',
                        'Save ': 'Sauvegarder ',
                        'Init ': 'Initialiser ',
                        'Check ': 'Vérifier ',
                        'Analyze ': 'Analyser ',
                        'Render ': 'Afficher ',
                        'Handle ': 'Gérer ',
                        'Manager': 'Gestionnaire'
                    }
                    for eng, fr in replacements.items():
                        description = description.replace(eng, fr)
                
                functions[name] = description
                
    except Exception as e:
        _function_detection_errors[module.__name__] = str(e)
    
    return functions

def create_stub_module(module_name: str):
    """
    Crée un module stub (vide) pour éviter les erreurs d'import
    """
    import types
    stub_module = types.ModuleType(module_name)
    stub_module.__file__ = f"<stub for {module_name}>"
    stub_module.MODULE_FUNCTIONS = {}
    
    # Fonction par défaut pour les modules stub
    def not_implemented(*args, **kwargs):
        return f"Module {module_name} non implémenté"
    
    stub_module.not_implemented = not_implemented
    return stub_module

# Compteurs pour le suivi
_modules_loaded = 0
_modules_failed = 0
_modules_stubbed = 0
_total_functions = 0

# Import dynamique de tous les modules et configuration automatique
for module_name in MODULES_LIST:
    try:
        # Tenter d'importer le module
        module = importlib.import_module(f'.{module_name}', package='modules')
        
        # Rendre le module disponible globalement
        globals()[module_name] = module
        _modules_loaded += 1
        
        # Si MODULE_FUNCTIONS n'existe pas, le créer automatiquement
        if not hasattr(module, 'MODULE_FUNCTIONS'):
            detected_functions = get_module_functions(module)
            
            # Si des fonctions ont été détectées, les assigner
            if detected_functions:
                setattr(module, 'MODULE_FUNCTIONS', detected_functions)
                _total_functions += len(detected_functions)
                if DEBUG_MODE:
                    print(f"✅ Module {module_name}: {len(detected_functions)} fonctions détectées")
            else:
                # Module sans fonctions ou avec uniquement des classes
                setattr(module, 'MODULE_FUNCTIONS', {})
                if DEBUG_MODE:
                    print(f"ℹ️ Module {module_name}: aucune fonction publique détectée")
        else:
            # MODULE_FUNCTIONS existe déjà
            _total_functions += len(getattr(module, 'MODULE_FUNCTIONS', {}))
            if DEBUG_MODE:
                print(f"✅ Module {module_name}: MODULE_FUNCTIONS existant conservé")
            
    except ImportError as e:
        # Module non trouvé - créer un stub pour éviter les erreurs
        _import_errors[module_name] = str(e)
        _modules_failed += 1
        
        # Créer un module stub
        try:
            stub = create_stub_module(module_name)
            globals()[module_name] = stub
            _modules_stubbed += 1
            if DEBUG_MODE:
                print(f"⚠️ Module {module_name} non trouvé - stub créé: {e}")
        except Exception as stub_error:
            if DEBUG_MODE:
                print(f"❌ Impossible de créer un stub pour {module_name}: {stub_error}")
        continue
        
    except Exception as e:
        # Autre erreur - enregistrer et continuer
        _import_errors[module_name] = str(e)
        _modules_failed += 1
        if DEBUG_MODE:
            print(f"❌ Erreur avec module {module_name}: {e}")
        continue

# Fonction utilitaire pour obtenir tous les modules chargés
def get_loaded_modules() -> Dict[str, Any]:
    """Retourne un dictionnaire de tous les modules chargés avec succès"""
    loaded = {}
    for module_name in MODULES_LIST:
        if module_name in globals():
            loaded[module_name] = globals()[module_name]
    return loaded

# Fonction pour obtenir MODULE_FUNCTIONS d'un module spécifique
def get_module_functions_by_name(module_name: str) -> Dict[str, str]:
    """
    Retourne MODULE_FUNCTIONS pour un module donné
    Retourne un dict vide si le module n'existe pas
    """
    if module_name in globals():
        module = globals()[module_name]
        return getattr(module, 'MODULE_FUNCTIONS', {})
    return {}

# Fonction pour lister tous les modules avec leurs fonctions
def list_all_modules_and_functions() -> Dict[str, Dict[str, str]]:
    """Retourne un dictionnaire de tous les modules et leurs fonctions"""
    result = {}
    for module_name, module in get_loaded_modules().items():
        result[module_name] = getattr(module, 'MODULE_FUNCTIONS', {})
    return result

# Fonction pour forcer la recréation de MODULE_FUNCTIONS
def refresh_module_functions(module_name: str, force: bool = False) -> bool:
    """
    Rafraîchit MODULE_FUNCTIONS pour un module spécifique
    
    Args:
        module_name: Nom du module à rafraîchir
        force: Si True, écrase MODULE_FUNCTIONS même s'il existe
        
    Returns:
        True si le rafraîchissement a réussi, False sinon
    """
    if module_name not in globals():
        return False
    
    module = globals()[module_name]
    
    # Si MODULE_FUNCTIONS existe et force=False, ne rien faire
    if hasattr(module, 'MODULE_FUNCTIONS') and not force:
        return True
    
    # Détecter les fonctions
    detected_functions = get_module_functions(module)
    setattr(module, 'MODULE_FUNCTIONS', detected_functions)
    
    return True

# Fonction pour obtenir l'état d'un module spécifique
def get_module_status(module_name: str) -> Dict[str, Any]:
    """
    Retourne le statut détaillé d'un module
    
    Returns:
        Dict avec 'loaded', 'functions_count', 'functions', 'error', 'is_stub'
    """
    status = {
        'loaded': False,
        'functions_count': 0,
        'functions': {},
        'error': None,
        'is_stub': False
    }
    
    if module_name in globals():
        module = globals()[module_name]
        status['loaded'] = True
        status['functions'] = getattr(module, 'MODULE_FUNCTIONS', {})
        status['functions_count'] = len(status['functions'])
        
        # Vérifier si c'est un stub
        if hasattr(module, '__file__') and module.__file__.startswith('<stub'):
            status['is_stub'] = True
            
        # Ajouter l'erreur d'import si elle existe
        if module_name in _import_errors:
            status['error'] = _import_errors[module_name]
    else:
        status['error'] = f"Module '{module_name}' non chargé"
    
    return status

# Fonction de debug pour afficher l'état des modules
def debug_modules_status(detailed: bool = False, output_to_streamlit: bool = False):
    """
    Affiche le statut de tous les modules (pour debug)
    
    Args:
        detailed: Si True, affiche le détail des fonctions
        output_to_streamlit: Si True, retourne le texte pour Streamlit au lieu de print
    """
    loaded = get_loaded_modules()
    
    output_lines = []
    output_lines.append(f"\n{'='*60}")
    output_lines.append(f"📦 ÉTAT DES MODULES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"{'='*60}")
    output_lines.append(f"Modules chargés: {_modules_loaded}/{len(MODULES_LIST)}")
    output_lines.append(f"Modules en erreur: {_modules_failed}")
    output_lines.append(f"Modules stub: {_modules_stubbed}")
    output_lines.append(f"Total fonctions: {_total_functions}")
    output_lines.append(f"\n📋 Détail par module:")
    output_lines.append(f"{'-'*60}")
    
    # Organiser par statut
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
    
    # Afficher les modules OK
    if modules_ok:
        output_lines.append("\n🟢 Modules chargés avec succès:")
        for module_name, status in sorted(modules_ok):
            output_lines.append(f"  ✅ {module_name:<25} : {status['functions_count']} fonctions")
            if detailed and status['functions']:
                for func_name, desc in sorted(status['functions'].items()):
                    output_lines.append(f"      - {func_name}: {desc[:50]}...")
    
    # Afficher les modules stub
    if modules_stub:
        output_lines.append("\n🟡 Modules stub (fichiers manquants):")
        for module_name, status in sorted(modules_stub):
            output_lines.append(f"  ⚠️  {module_name:<25} : stub créé")
            if status['error']:
                output_lines.append(f"      Erreur: {status['error']}")
    
    # Afficher les modules en erreur
    if modules_error:
        output_lines.append("\n🔴 Modules en erreur:")
        for module_name, status in sorted(modules_error):
            output_lines.append(f"  ❌ {module_name:<25} : non chargé")
            if status['error']:
                output_lines.append(f"      Erreur: {status['error']}")
    
    # Afficher les erreurs de détection de fonctions
    if _function_detection_errors:
        output_lines.append(f"\n⚠️  Erreurs de détection de fonctions:")
        for module_name, error in _function_detection_errors.items():
            output_lines.append(f"  - {module_name}: {error}")
    
    output_lines.append(f"{'-'*60}")
    output_lines.append(f"{'='*60}\n")
    
    output_text = '\n'.join(output_lines)
    
    if output_to_streamlit:
        return output_text
    else:
        print(output_text)

# Fonction pour générer un rapport HTML
def generate_debug_report_html() -> str:
    """Génère un rapport HTML détaillé de l'état des modules"""
    loaded = get_loaded_modules()
    
    html = f"""
    <html>
    <head>
        <title>Rapport Debug Modules - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .module-ok {{ background: #d4edda; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .module-stub {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .module-error {{ background: #f8d7da; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .function-list {{ margin-left: 20px; font-size: 0.9em; }}
            h1, h2, h3 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>📦 Rapport Debug Modules</h1>
        <div class="summary">
            <h2>Résumé</h2>
            <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Modules chargés: {_modules_loaded}/{len(MODULES_LIST)}</p>
            <p>Modules en erreur: {_modules_failed}</p>
            <p>Modules stub: {_modules_stubbed}</p>
            <p>Total fonctions: {_total_functions}</p>
        </div>
    """
    
    # Modules OK
    modules_ok = [(name, get_module_status(name)) for name in MODULES_LIST 
                  if get_module_status(name)['loaded'] and not get_module_status(name)['is_stub']]
    
    if modules_ok:
        html += "<h2>🟢 Modules chargés avec succès</h2>"
        for module_name, status in sorted(modules_ok):
            html += f"""
            <div class="module-ok">
                <strong>{module_name}</strong> - {status['functions_count']} fonctions
                <div class="function-list">
            """
            for func_name, desc in sorted(status['functions'].items()):
                html += f"<br>• {func_name}: {desc}"
            html += "</div></div>"
    
    # Modules stub
    modules_stub = [(name, get_module_status(name)) for name in MODULES_LIST 
                    if get_module_status(name)['is_stub']]
    
    if modules_stub:
        html += "<h2>🟡 Modules stub (fichiers manquants)</h2>"
        for module_name, status in sorted(modules_stub):
            html += f"""
            <div class="module-stub">
                <strong>{module_name}</strong> - stub créé
                {f"<br>Erreur: {status['error']}" if status['error'] else ""}
            </div>
            """
    
    # Modules en erreur
    modules_error = [(name, get_module_status(name)) for name in MODULES_LIST 
                     if not get_module_status(name)['loaded']]
    
    if modules_error:
        html += "<h2>🔴 Modules en erreur</h2>"
        for module_name, status in sorted(modules_error):
            html += f"""
            <div class="module-error">
                <strong>{module_name}</strong> - non chargé
                {f"<br>Erreur: {status['error']}" if status['error'] else ""}
            </div>
            """
    
    html += "</body></html>"
    return html

# Fonction pour tester l'import d'un module spécifique
def test_module_import(module_name: str, verbose: bool = True) -> Tuple[bool, str]:
    """
    Teste l'import d'un module spécifique et retourne le résultat
    
    Returns:
        Tuple (succès: bool, message: str)
    """
    try:
        # Réimporter le module
        module = importlib.import_module(f'.{module_name}', package='modules')
        
        # Détecter les fonctions
        functions = get_module_functions(module)
        
        if verbose:
            message = f"✅ Module {module_name} importé avec succès\n"
            message += f"   Fonctions détectées: {len(functions)}\n"
            if functions:
                message += "   Liste des fonctions:\n"
                for func_name, desc in functions.items():
                    message += f"     - {func_name}: {desc}\n"
        else:
            message = f"Module {module_name}: OK ({len(functions)} fonctions)"
        
        return True, message
        
    except Exception as e:
        message = f"❌ Erreur avec {module_name}: {str(e)}"
        return False, message

# Export de tous les modules disponibles et fonctions utilitaires
__all__ = [
    'dataclasses', 
    'get_loaded_modules', 
    'get_module_functions_by_name',
    'list_all_modules_and_functions', 
    'debug_modules_status',
    'refresh_module_functions', 
    'get_module_status',
    'generate_debug_report_html',
    'test_module_import',
    'get_module_functions',
    'create_stub_module'
] + MODULES_LIST

# Fonction pour créer une page de debug dans Streamlit
def create_streamlit_debug_page():
    """
    Crée une page de debug complète pour Streamlit
    À utiliser dans votre app.py
    """
    import streamlit as st
    
    st.title("🔧 Debug des Modules")
    
    # Résumé
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Modules chargés", f"{_modules_loaded}/{len(MODULES_LIST)}")
    with col2:
        st.metric("Modules en erreur", _modules_failed)
    with col3:
        st.metric("Modules stub", _modules_stubbed)
    with col4:
        st.metric("Total fonctions", _total_functions)
    
    # Tabs pour différentes vues
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Vue d'ensemble", "🔍 Détails", "🧪 Tests", "📄 Rapport"])
    
    with tab1:
        st.subheader("État des modules")
        
        # Utiliser des expanders pour chaque catégorie
        with st.expander(f"✅ Modules OK ({_modules_loaded - _modules_stubbed})", expanded=True):
            for module_name in sorted(MODULES_LIST):
                status = get_module_status(module_name)
                if status['loaded'] and not status['is_stub']:
                    st.success(f"{module_name}: {status['functions_count']} fonctions")
        
        with st.expander(f"⚠️ Modules Stub ({_modules_stubbed})"):
            for module_name in sorted(MODULES_LIST):
                status = get_module_status(module_name)
                if status['is_stub']:
                    st.warning(f"{module_name}: {status['error'] or 'Fichier manquant'}")
        
        with st.expander(f"❌ Modules en erreur ({_modules_failed - _modules_stubbed})"):
            for module_name in sorted(MODULES_LIST):
                status = get_module_status(module_name)
                if not status['loaded']:
                    st.error(f"{module_name}: {status['error'] or 'Erreur inconnue'}")
    
    with tab2:
        st.subheader("Détails des modules")
        
        # Sélecteur de module
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
    
    with tab3:
        st.subheader("Tests d'import")
        
        test_module = st.selectbox(
            "Module à tester",
            options=MODULES_LIST,
            key="test_module"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🧪 Tester l'import"):
                success, message = test_module_import(test_module)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        with col2:
            if st.button("🔄 Rafraîchir les fonctions"):
                if refresh_module_functions(test_module, force=True):
                    st.success(f"Fonctions rafraîchies pour {test_module}")
                else:
                    st.error(f"Impossible de rafraîchir {test_module}")
    
    with tab4:
        st.subheader("Rapport complet")
        
        if st.button("📊 Générer le rapport texte"):
            report = debug_modules_status(detailed=True, output_to_streamlit=True)
            st.code(report, language="text")
        
        if st.button("📄 Générer le rapport HTML"):
            html_report = generate_debug_report_html()
            st.download_button(
                label="💾 Télécharger le rapport HTML",
                data=html_report,
                file_name=f"debug_modules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )

# Afficher le debug au chargement si activé
if DEBUG_MODE and __name__ != '__main__':
    debug_modules_status()

# Exemple de test pour vérifier l'import
if __name__ == '__main__':
    print("Test du système de modules...")
    debug_modules_status(detailed=True)
    
    # Tester l'accès à un module spécifique
    print("\n" + "="*60)
    print("Test d'import du module redaction:")
    success, message = test_module_import('redaction')
    print(message)