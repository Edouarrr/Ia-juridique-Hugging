"""Package services - Contient tous les services de l'application"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Import des services principaux
try:
    from .company_info_service import (
        CompanyInfoService, 
        get_company_info_service,
        InfosSociete,
        CacheSocietes,
        show_enrichissement_interface,
        enrichir_parties_acte
    )
    logger.info("✅ CompanyInfoService importé")
except ImportError as e:
    logger.warning(f"⚠️ CompanyInfoService non disponible: {e}")
    CompanyInfoService = None
    get_company_info_service = None

try:
    from .style_learning_service import (
        StyleLearningService, 
        get_style_learning_service,
        StyleLearningResult,
        Document as StyleDocument
    )
    logger.info("✅ StyleLearningService importé")
except ImportError as e:
    logger.warning(f"⚠️ StyleLearningService non disponible: {e}")
    StyleLearningService = None
    get_style_learning_service = None

try:
    from .universal_search_service import (
        UniversalSearchService, 
        get_universal_search_service,
        Document,
        QueryAnalysis,
        SearchResult,
        Partie
    )
    logger.info("✅ UniversalSearchService importé")
except ImportError as e:
    logger.warning(f"⚠️ UniversalSearchService non disponible: {e}")
    UniversalSearchService = None
    get_universal_search_service = None

# Alias pour compatibilité avec l'ancien code
try:
    if CompanyInfoService:
        PappersService = CompanyInfoService
        EnrichisseurSocietes = CompanyInfoService
except:
    pass

# Liste des exports
__all__ = [
    # Services principaux
    'CompanyInfoService',
    'get_company_info_service',
    'StyleLearningService',
    'get_style_learning_service',
    'UniversalSearchService',
    'get_universal_search_service',
    
    # Classes de données
    'InfosSociete',
    'CacheSocietes',
    'StyleLearningResult',
    'Document',
    'QueryAnalysis',
    'SearchResult',
    'Partie',
    
    # Fonctions utilitaires
    'show_enrichissement_interface',
    'enrichir_parties_acte',
    'initialize_all_services',
    'get_services_status',
    'cleanup_services',
    
    # Alias pour compatibilité
    'PappersService',
    'EnrichisseurSocietes'
]

# État global des services
_services_initialized = False
_services_instances = {}

def initialize_all_services(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Initialise tous les services au démarrage de l'application
    
    Args:
        config: Configuration optionnelle à passer aux services
        
    Returns:
        Dict avec le statut de chaque service
    """
    global _services_initialized, _services_instances
    
    if _services_initialized:
        return get_services_status()
    
    status = {}
    
    # 1. Company Info Service (fusion Pappers + company info)
    try:
        if get_company_info_service:
            _services_instances['company_info'] = get_company_info_service()
            status['company_info'] = 'OK'
            logger.info("✅ CompanyInfoService initialisé")
    except Exception as e:
        status['company_info'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur CompanyInfoService: {e}")
    
    # 2. Style Learning Service
    try:
        if get_style_learning_service:
            _services_instances['style_learning'] = get_style_learning_service()
            status['style_learning'] = 'OK'
            logger.info("✅ StyleLearningService initialisé")
    except Exception as e:
        status['style_learning'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur StyleLearningService: {e}")
    
    # 3. Universal Search Service
    try: