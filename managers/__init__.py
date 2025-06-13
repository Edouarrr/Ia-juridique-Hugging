# managers/__init__.py
"""
Package managers - Gestionnaires pour l'application juridique
"""

import logging

logger = logging.getLogger(__name__)

# Définition des managers à importer
MANAGERS = [
    ('azure_blob_manager', 'AzureBlobManager'),
    ('azure_search_manager', 'AzureSearchManager'),
    ('company_info_manager', 'CompanyInfoManager'),
    ('document_manager', 'DocumentManager'),
    ('dynamic_generators', 'DynamicGenerators'),
    ('export_manager', 'ExportManager'),
    ('jurisprudence_verifier', 'JurisprudenceVerifier'),
    ('legal_search', 'LegalSearchManager'),
    ('llm_manager', 'LLMManager'),
    ('multi_llm_manager', 'MultiLLMManager'),
    ('style_analyzer', 'StyleAnalyzer'),
    ('template_manager', 'TemplateManager'),
    ('UniversalSearchInterface', 'UniversalSearchInterface'),
    ('universal_search_service', 'UniversalSearchService'),
    ('unified_document_generator', 'UnifiedDocumentGenerator'),
]

# Import dynamique des managers disponibles
__all__ = []
_available_managers = {}

for module_name, class_name in MANAGERS:
    try:
        module = __import__(f'.{module_name}', fromlist=[class_name], package=__name__)
        manager_class = getattr(module, class_name)
        
        # Rendre le manager disponible dans le namespace
        globals()[class_name] = manager_class
        _available_managers[class_name] = manager_class
        __all__.append(class_name)
        
    except ImportError as e:
        logger.debug(f"Manager {class_name} non disponible: {e}")
    except AttributeError as e:
        logger.warning(f"Classe {class_name} introuvable dans {module_name}: {e}")

# Fonction utilitaire pour vérifier la disponibilité d'un manager
def is_manager_available(manager_name: str) -> bool:
    """Vérifie si un manager est disponible"""
    return manager_name in _available_managers

# Fonction pour obtenir la liste des managers disponibles
def get_available_managers() -> list:
    """Retourne la liste des managers disponibles"""
    return list(_available_managers.keys())

# Ajouter les fonctions utilitaires à __all__
__all__.extend(['is_manager_available', 'get_available_managers'])