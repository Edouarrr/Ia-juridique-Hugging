# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
"""

# Import des dataclasses depuis ce module pour faciliter l'accès
try:
    from .dataclasses import *
except ImportError as e:
    print(f"Erreur lors de l'import des dataclasses: {e}")

# Liste des modules disponibles
__all__ = ['dataclasses']

# Import conditionnel des autres modules
modules_list = [
    'analyse_ia',
    'bordereau',
    'comparison',
    'configuration',
    'dossier_penal',
    'email',
    'explorer',
    'export_juridique',
    'generation_juridique',
    'generation-longue',
    'import_export',
    'integration_juridique',
    'jurisprudence',
    'mapping',
    'pieces_manager',
    'plaidoirie',
    'preparation_client',
    'recherche',
    'redaction',
    'redaction_unified',
    'risques',
    'selection_pieces',
    'synthesis',
    'template',
    'timeline'
]

# Import conditionnel de chaque module
for module_name in modules_list:
    try:
        # Gérer les modules avec tirets
        import_name = module_name.replace('-', '_')
        exec(f"from . import {module_name}")
        __all__.append(module_name)
    except ImportError:
        # Module non disponible, continuer
        pass