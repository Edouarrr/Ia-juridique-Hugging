"""
Modules de l'application IA Juridique - Initialisation
"""

import logging
import sys
import importlib
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Définir __all__ pour les exports
__all__ = [
    'ComparisonModule',
    'TimelineModule',
    'ExtractionModule',
    'StrategyModule',
    'ReportModule',
    'get_modules_status'
]

# Dictionnaire des modules disponibles
AVAILABLE_MODULES = {
    'comparison': 'ComparisonModule',
    'timeline': 'TimelineModule',
    'extraction': 'ExtractionModule',
    'strategy': 'StrategyModule',
    'report': 'ReportModule'
}

# État des imports
_import_status = {
    'loaded': [],
    'failed': {}
}

# Import dynamique des modules
for module_name, class_name in AVAILABLE_MODULES.items():
    try:
        # Utiliser importlib pour un import robuste
        module = importlib.import_module(f".{module_name}", package=__package__)
        
        # Extraire la classe et l'ajouter au namespace
        if hasattr(module, class_name):
            globals()[class_name] = getattr(module, class_name)
            _import_status['loaded'].append(class_name)
            logger.info(f"✅ Module chargé : {class_name}")
        else:
            error_msg = f"Classe {class_name} non trouvée dans {module_name}"
            _import_status['failed'][class_name] = error_msg
            logger.warning(f"⚠️ {error_msg}")
            
    except ImportError as e:
        error_msg = f"Module non disponible : {str(e)}"
        _import_status['failed'][class_name] = error_msg
        logger.warning(f"⚠️ {class_name} - {error_msg}")
        
        # Créer une classe placeholder
        exec(f"""
class {class_name}:
    '''Placeholder pour {class_name} non disponible'''
    def __init__(self, *args, **kwargs):
        self.name = "{class_name.replace('Module', '')}"
        self.available = False
        self.error = "{error_msg}"
        self.icon = "❌"
        self.description = "Module non disponible"
        logger.warning("Utilisation du placeholder pour {class_name}")
    
    def render(self):
        import streamlit as st
        st.error(f"Module {{self.name}} non disponible")
        st.info(f"Erreur : {{self.error}}")
        st.markdown("### 🛠️ Actions suggérées")
        st.markdown("1. Vérifiez que le fichier `modules/{module_name}.py` existe")
        st.markdown("2. Vérifiez les imports dans le fichier")
        st.markdown("3. Consultez les logs pour plus de détails")
""", globals())
        
    except Exception as e:
        error_msg = f"Erreur inattendue : {str(e)}"
        _import_status['failed'][class_name] = error_msg
        logger.error(f"❌ {class_name} - {error_msg}")
        
        # Créer une classe placeholder pour l'erreur
        exec(f"""
class {class_name}:
    '''Placeholder pour {class_name} avec erreur'''
    def __init__(self, *args, **kwargs):
        self.name = "{class_name.replace('Module', '')}"
        self.available = False
        self.error = "{error_msg}"
        self.icon = "❌"
        self.description = "Erreur lors du chargement"
    
    def render(self):
        import streamlit as st
        st.error(f"Erreur dans le module {{self.name}}")
        st.code(f"{{self.error}}")
""", globals())

def get_modules_status() -> Dict[str, Any]:
    """Retourne le statut des modules"""
    return {
        'total_modules': len(AVAILABLE_MODULES),
        'loaded_count': len(_import_status['loaded']),
        'failed_count': len(_import_status['failed']),
        'loaded': _import_status['loaded'],
        'failed': _import_status['failed'],
        'available_modules': AVAILABLE_MODULES
    }

def test_modules():
    """Test rapide des modules disponibles"""
    status = get_modules_status()
    print(f"\n📊 Statut des Modules :")
    print(f"Total : {status['total_modules']}")
    print(f"Chargés : {status['loaded_count']} ✅")
    print(f"Échoués : {status['failed_count']} ❌")
    
    if status['loaded']:
        print(f"\n✅ Modules disponibles :")
        for module in status['loaded']:
            print(f"  - {module}")
    
    if status['failed']:
        print(f"\n❌ Modules non disponibles :")
        for module, error in status['failed'].items():
            print(f"  - {module}: {error}")
    
    return status

# Test automatique si exécuté directement
if __name__ == "__main__":
    test_modules()