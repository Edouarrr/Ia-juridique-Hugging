# modules/__init__.py
"""
Package modules contenant tous les modules fonctionnels de l'application juridique
"""

# Import de tous les modules disponibles
from . import comparison
from . import explorer
from . import generation_longue
from . import import_export
from . import jurisprudence
from . import mapping
from . import pieces_manager
from . import plaidoirie
from . import preparation_client
from . import recherche_analyse_unifiee
from . import redaction2
from . import synthesis
from . import template
from . import timeline
from . import email
from . import configuration
from . import dataclasses
from . import dossier_penal
from . import export_manager
from . import integration_juridique
from . import risques
from . import redaction_unified

# Version du package
__version__ = '1.0.0'

# Liste des modules exportés
__all__ = [
    'comparison',
    'explorer',
    'generation_longue',
    'import_export',
    'jurisprudence',
    'mapping',
    'pieces_manager',
    'plaidoirie',
    'preparation_client',
    'recherche_analyse_unifiee',
    'redaction2',
    'synthesis',
    'template',
    'timeline',
    'email',
    'configuration',
    'dataclasses',
    'dossier_penal',
    'export_manager',
    'integration_juridique',
    'risques',
    'redaction_unified'
]

# Fonction utilitaire pour charger un module de manière sûre
def safe_import_module(module_name: str):
    """
    Importe un module de manière sûre en gérant les erreurs.
    
    Args:
        module_name: Nom du module à importer
    
    Returns:
        Le module importé ou None en cas d'erreur
    """
    try:
        return globals()[module_name]
    except KeyError:
        print(f"Module '{module_name}' non trouvé dans modules/")
        return None
    except Exception as e:
        print(f"Erreur lors de l'import du module '{module_name}': {str(e)}")
        return None