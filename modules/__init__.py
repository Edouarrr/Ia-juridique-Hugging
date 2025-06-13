"""
Module d'initialisation des modules de l'application IA Juridique
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import des modules principaux
modules_to_import = {
    # Modules de base
    'comparison': 'comparison',
    'configuration': 'configuration',
    'dataclasses': 'dataclasses',
    'dossier_penal': 'dossier_penal',
    'email': 'email',
    'explorer': 'explorer',
    'export_manager': 'export_manager',
    'generation_longue': 'generation_longue',
    'import_export': 'import_export',
    'integration_juridique': 'integration_juridique',
    'jurisprudence': 'jurisprudence',
    'mapping': 'mapping',
    'pieces_manager': 'pieces_manager',
    'plaidoirie': 'plaidoirie',
    'preparation_client': 'preparation_client',
    'recherche_analyse_unifiee': 'recherche_analyse_unifiee',
    'redaction_unified': 'redaction_unified',
    'risques': 'risques',
    'redaction': 'redaction',
    'redaction2': 'redaction2',  # L'ancien rédaction.py
    'synthesis': 'synthesis',
    'template': 'template',
    'timeline': 'timeline'
}

# Import dynamique avec gestion d'erreurs
loaded_modules = {}
failed_modules = {}

for module_name, module_path in modules_to_import.items():
    try:
        module = __import__(f'modules.{module_path}', fromlist=[module_path])
        loaded_modules[module_name] = module
        logger.info(f"✅ Module {module_name} chargé avec succès")
    except Exception as e:
        failed_modules[module_name] = str(e)
        logger.error(f"❌ Erreur lors du chargement du module {module_name}: {e}")

# Export des modules chargés
for name, module in loaded_modules.items():
    globals()[name] = module

# Informations de diagnostic
def get_modules_status() -> Dict[str, Any]:
    """Retourne le statut de chargement des modules"""
    return {
        'loaded': list(loaded_modules.keys()),
        'failed': failed_modules,
        'total_modules': len(modules_to_import),
        'loaded_count': len(loaded_modules),
        'failed_count': len(failed_modules)
    }

# Liste des modules exportés
__all__ = list(loaded_modules.keys()) + ['get_modules_status']

# Log du statut au chargement
status = get_modules_status()
logger.info(f"📊 Modules chargés: {status['loaded_count']}/{status['total_modules']}")
if status['failed_count'] > 0:
    logger.warning(f"⚠️ Modules en erreur: {list(status['failed'].keys())}")