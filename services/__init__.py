"""Package services - Contient tous les services de l'application"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import des services principaux
try:
    from .config_service import ConfigService, get_config_service
    logger.info("✅ ConfigService importé")
except ImportError as e:
    logger.warning(f"⚠️ ConfigService non disponible: {e}")
    ConfigService = None
    get_config_service = None

try:
    from .cache_service import CacheService, get_cache_service
    logger.info("✅ CacheService importé")
except ImportError as e:
    logger.warning(f"⚠️ CacheService non disponible: {e}")
    CacheService = None
    get_cache_service = None

try:
    from .company_info_service import CompanyInfoService, get_company_info_service
    logger.info("✅ CompanyInfoService importé")
except ImportError as e:
    logger.warning(f"⚠️ CompanyInfoService non disponible: {e}")
    CompanyInfoService = None
    get_company_info_service = None

try:
    from .style_learning_service import StyleLearningService, get_style_learning_service
    logger.info("✅ StyleLearningService importé")
except ImportError as e:
    logger.warning(f"⚠️ StyleLearningService non disponible: {e}")
    StyleLearningService = None
    get_style_learning_service = None

try:
    from .universal_search_service import UniversalSearchService, get_universal_search_service
    logger.info("✅ UniversalSearchService importé")
except ImportError as e:
    logger.warning(f"⚠️ UniversalSearchService non disponible: {e}")
    UniversalSearchService = None
    get_universal_search_service = None

# Liste des services exportés
__all__ = [
    # Services de base
    'ConfigService',
    'get_config_service',
    'CacheService',
    'get_cache_service',
    
    # Services métier
    'CompanyInfoService',
    'get_company_info_service',
    'StyleLearningService',
    'get_style_learning_service',
    'UniversalSearchService',
    'get_universal_search_service',
    
    # Fonctions utilitaires
    'initialize_all_services',
    'get_services_status',
    'cleanup_services'
]

# État global des services
_services_initialized = False
_services_instances = {}

def initialize_all_services(config: Optional[dict] = None) -> dict:
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
    
    # 1. Config Service (prioritaire)
    try:
        if get_config_service:
            _services_instances['config'] = get_config_service()
            status['config'] = 'OK'
            logger.info("✅ ConfigService initialisé")
    except Exception as e:
        status['config'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur ConfigService: {e}")
    
    # 2. Cache Service
    try:
        if get_cache_service:
            _services_instances['cache'] = get_cache_service()
            status['cache'] = 'OK'
            logger.info("✅ CacheService initialisé")
    except Exception as e:
        status['cache'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur CacheService: {e}")
    
    # 3. Company Info Service
    try:
        if get_company_info_service:
            _services_instances['company_info'] = get_company_info_service()
            status['company_info'] = 'OK'
            logger.info("✅ CompanyInfoService initialisé")
    except Exception as e:
        status['company_info'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur CompanyInfoService: {e}")
    
    # 4. Style Learning Service
    try:
        if get_style_learning_service:
            _services_instances['style_learning'] = get_style_learning_service()
            status['style_learning'] = 'OK'
            logger.info("✅ StyleLearningService initialisé")
    except Exception as e:
        status['style_learning'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur StyleLearningService: {e}")
    
    # 5. Universal Search Service
    try:
        if get_universal_search_service:
            _services_instances['universal_search'] = get_universal_search_service()
            status['universal_search'] = 'OK'
            logger.info("✅ UniversalSearchService initialisé")
    except Exception as e:
        status['universal_search'] = f'Erreur: {e}'
        logger.error(f"❌ Erreur UniversalSearchService: {e}")
    
    _services_initialized = True
    logger.info(f"📊 Services initialisés: {sum(1 for v in status.values() if v == 'OK')}/{len(status)}")
    
    return status

def get_services_status() -> dict:
    """
    Retourne le statut actuel de tous les services
    
    Returns:
        Dict avec le nom du service et son statut
    """
    status = {}
    
    # Vérifier chaque service
    services_check = [
        ('config', ConfigService, get_config_service),
        ('cache', CacheService, get_cache_service),
        ('company_info', CompanyInfoService, get_company_info_service),
        ('style_learning', StyleLearningService, get_style_learning_service),
        ('universal_search', UniversalSearchService, get_universal_search_service)
    ]
    
    for service_name, service_class, getter_func in services_check:
        if service_class is None:
            status[service_name] = 'Non importé'
        elif service_name in _services_instances:
            status[service_name] = 'Actif'
        else:
            status[service_name] = 'Non initialisé'
    
    return status

def cleanup_services():
    """
    Nettoie et ferme proprement tous les services
    Utile pour les tests ou l'arrêt de l'application
    """
    global _services_initialized, _services_instances
    
    # Fermer les services qui ont une méthode close
    for service_name, service_instance in _services_instances.items():
        if hasattr(service_instance, 'close'):
            try:
                service_instance.close()
                logger.info(f"✅ {service_name} fermé proprement")
            except Exception as e:
                logger.error(f"❌ Erreur fermeture {service_name}: {e}")
        
        if hasattr(service_instance, 'cleanup'):
            try:
                service_instance.cleanup()
                logger.info(f"✅ {service_name} nettoyé")
            except Exception as e:
                logger.error(f"❌ Erreur nettoyage {service_name}: {e}")
    
    # Réinitialiser
    _services_instances.clear()
    _services_initialized = False
    logger.info("🧹 Tous les services ont été fermés")

# Auto-initialisation si dans Streamlit
try:
    import streamlit as st
    if 'services_initialized' not in st.session_state:
        st.session_state.services_initialized = True
        initialize_all_services()
except ImportError:
    pass