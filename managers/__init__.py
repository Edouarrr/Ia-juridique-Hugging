"""
Gestionnaires Azure et IA - Initialisation et imports dynamiques
"""

import logging
import os
import sys
from typing import Dict, Any, Optional
import importlib

logger = logging.getLogger(__name__)

# Définir __all__ pour les exports
__all__ = [
    'AzureBlobManager',
    'AzureSearchManager', 
    'AzureOpenAIManager',
    'MultiLLMManager',
    'get_managers_status'
]

# Dictionnaire des managers disponibles
AVAILABLE_MANAGERS = {
    'azure_blob_manager': 'AzureBlobManager',
    'azure_search_manager': 'AzureSearchManager',
    'azure_openai_manager': 'AzureOpenAIManager',
    'multi_llm_manager': 'MultiLLMManager'
}

# État des imports
_import_status = {
    'loaded': [],
    'failed': {}
}

# Import dynamique des managers
for module_name, class_name in AVAILABLE_MANAGERS.items():
    try:
        # Utiliser importlib pour un import robuste
        module = importlib.import_module(f".{module_name}", package=__package__)
        
        # Extraire la classe et l'ajouter au namespace
        if hasattr(module, class_name):
            globals()[class_name] = getattr(module, class_name)
            _import_status['loaded'].append(class_name)
            logger.info(f"✅ Manager chargé : {class_name}")
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
        self.connected = False
        self.error = "{error_msg}"
        self.available = False
        logger.warning("Utilisation du placeholder pour {class_name}")
    
    def __getattr__(self, name):
        logger.warning(f"Tentative d'accès à {{name}} sur {class_name} non disponible")
        return lambda *args, **kwargs: None
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
        self.connected = False
        self.error = "{error_msg}"
        self.available = False
""", globals())

def get_managers_status() -> Dict[str, Any]:
    """Retourne le statut des managers"""
    return {
        'total_managers': len(AVAILABLE_MANAGERS),
        'loaded_count': len(_import_status['loaded']),
        'failed_count': len(_import_status['failed']),
        'loaded': _import_status['loaded'],
        'failed': _import_status['failed'],
        'available_managers': AVAILABLE_MANAGERS
    }

def test_managers():
    """Test rapide des managers disponibles"""
    status = get_managers_status()
    print(f"\n📊 Statut des Managers :")
    print(f"Total : {status['total_managers']}")
    print(f"Chargés : {status['loaded_count']} ✅")
    print(f"Échoués : {status['failed_count']} ❌")
    
    if status['loaded']:
        print(f"\n✅ Managers disponibles :")
        for manager in status['loaded']:
            print(f"  - {manager}")
    
    if status['failed']:
        print(f"\n❌ Managers non disponibles :")
        for manager, error in status['failed'].items():
            print(f"  - {manager}: {error}")
    
    return status

# Test automatique si exécuté directement
if __name__ == "__main__":
    test_managers()