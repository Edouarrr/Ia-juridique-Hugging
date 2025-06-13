"""
Module d'initialisation des modules de l'application IA Juridique
"""
import logging
from typing import Dict, Any, Optional
import importlib
import sys

logger = logging.getLogger(__name__)

# Liste des modules à importer
MODULES_CONFIG = {
    'comparison': 'modules.comparison',
    'configuration': 'modules.configuration', 
    'dataclasses': 'modules.dataclasses',
    'dossier_penal': 'modules.dossier_penal',
    'email': 'modules.email',
    'explorer': 'modules.explorer',
    'export_manager': 'modules.export_manager',
    'generation_longue': 'modules.generation_longue',
    'import_export': 'modules.import_export',
    'integration_juridique': 'modules.integration_juridique',
    'jurisprudence': 'modules.jurisprudence',
    'mapping': 'modules.mapping',
    'pieces_manager': 'modules.pieces_manager',
    'plaidoirie': 'modules.plaidoirie',
    'preparation_client': 'modules.preparation_client',
    'recherche_analyse_unifiee': 'modules.recherche_analyse_unifiee',
    'redaction_unified': 'modules.redaction_unified',
    'risques': 'modules.risques',
    'redaction2': 'modules.redaction2',
    'synthesis': 'modules.synthesis',
    'template': 'modules.template',
    'timeline': 'modules.timeline'
}

# Dictionnaires pour stocker les modules
loaded_modules = {}
failed_modules = {}

def load_module(module_name: str, module_path: str) -> Optional[Any]:
    """Charge un module de manière sécurisée"""
    try:
        # Utiliser importlib qui est plus moderne et fiable
        module = importlib.import_module(module_path)
        return module
    except ImportError as e:
        logger.error(f"❌ Impossible d'importer le module {module_name} depuis {module_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du module {module_name}: {e}")
        return None

# Charger tous les modules
for name, path in MODULES_CONFIG.items():
    module = load_module(name, path)
    if module:
        loaded_modules[name] = module
        # Rendre le module disponible dans le namespace
        globals()[name] = module
        logger.info(f"✅ Module {name} chargé avec succès")
    else:
        failed_modules[name] = f"Échec du chargement depuis {path}"

def get_modules_status() -> Dict[str, Any]:
    """Retourne le statut de chargement des modules"""
    return {
        'loaded': list(loaded_modules.keys()),
        'failed': failed_modules,
        'total_modules': len(MODULES_CONFIG),
        'loaded_count': len(loaded_modules),
        'failed_count': len(failed_modules)
    }

def get_module(module_name: str) -> Optional[Any]:
    """Récupère un module chargé par son nom"""
    return loaded_modules.get(module_name)

def reload_module(module_name: str) -> bool:
    """Recharge un module"""
    if module_name in MODULES_CONFIG:
        module_path = MODULES_CONFIG[module_name]
        try:
            # Si le module est déjà chargé, le recharger
            if module_name in loaded_modules:
                importlib.reload(loaded_modules[module_name])
            else:
                module = load_module(module_name, module_path)
                if module:
                    loaded_modules[module_name] = module
                    globals()[module_name] = module
            logger.info(f"✅ Module {module_name} rechargé avec succès")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors du rechargement du module {module_name}: {e}")
            return False
    return False

# Exporter les fonctions utiles
__all__ = [
    'get_modules_status',
    'get_module',
    'reload_module',
    'loaded_modules',
    'failed_modules'
] + list(loaded_modules.keys())

# Log du statut initial
status = get_modules_status()
logger.info(f"📊 Initialisation des modules terminée")
logger.info(f"✅ Modules chargés: {status['loaded_count']}/{status['total_modules']}")

if status['failed_count'] > 0:
    logger.warning(f"⚠️ {status['failed_count']} modules en erreur")
    for name, error in failed_modules.items():
        logger.warning(f"  - {name}: {error}")