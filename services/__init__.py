"""Package services - Contient les services de l'application"""

# Import des services principaux pour faciliter l'accès
from .company_info_service import CompanyInfoService, get_company_info_service
from .style_learning_service import StyleLearningService

# Import conditionnel pour éviter les erreurs circulaires
try:
    from .universal_search_service import UniversalSearchService
except ImportError:
    # Si le service n'est pas disponible ou redirige vers managers
    UniversalSearchService = None

# Liste des services exportés
__all__ = [
    'CompanyInfoService',
    'get_company_info_service',
    'StyleLearningService',
    'UniversalSearchService'
]

# Initialisation des singletons si nécessaire
_services_initialized = False

def initialize_services():
    """Initialise tous les services au démarrage"""
    global _services_initialized
    if not _services_initialized:
        # Initialiser les services qui en ont besoin
        _services_initialized = True