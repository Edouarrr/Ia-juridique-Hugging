"""Package services - Contient tous les services de l'application"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import des services principaux
try:
    from .company_info_service import (CacheSocietes, CompanyInfoService,
                                       InfosSociete, enrichir_parties_acte,
                                       get_company_info_service,
                                       show_enrichissement_interface)
    logger.info("✅ CompanyInfoService importé")
except ImportError as e:
    logger.warning(f"⚠️ CompanyInfoService non disponible: {e}")
    CompanyInfoService = None
    get_company_info_service = None

try:
    from .style_learning_service import Document as StyleDocument
    from .style_learning_service import (StyleLearningResult,
                                         StyleLearningService,
                                         get_style_learning_service)
    logger.info("✅ StyleLearningService importé")
except ImportError as e:
    logger.warning(f"⚠️ StyleLearningService non disponible: {e}")
    StyleLearningService = None
    get_style_learning_service = None

try:
    from .universal_search_service import (Document, Partie, QueryAnalysis,
                                           SearchResult,
                                           UniversalSearchService,
                                           get_universal_search_service)
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

def get_services_status() -> Dict[str, str]:
    """
    Retourne le statut actuel de tous les services
    
    Returns:
        Dict avec le nom du service et son statut
    """
    status = {}
    
    # Vérifier chaque service
    services_check = [
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
    """
    global _services_initialized, _services_instances
    
    # Fermer les services qui ont une méthode close
    for service_name, service_instance in _services_instances.items():
        if hasattr(service_instance, 'close'):
            try:
                # Pour les méthodes async
                import asyncio
                if asyncio.iscoroutinefunction(service_instance.close):
                    asyncio.run(service_instance.close())
                else:
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

def get_service_instance(service_name: str) -> Optional[Any]:
    """
    Récupère une instance de service par son nom
    
    Args:
        service_name: Nom du service ('company_info', 'style_learning', 'universal_search')
        
    Returns:
        Instance du service ou None
    """
    return _services_instances.get(service_name)

def test_services():
    """Test rapide de tous les services"""
    print("🧪 Test des services...")
    
    # Initialiser
    status = initialize_all_services()
    print(f"\n📊 Statut d'initialisation:")
    for service, state in status.items():
        print(f"  - {service}: {state}")
    
    # Test Company Info Service
    if 'company_info' in _services_instances:
        try:
            service = _services_instances['company_info']
            results = service.search_entreprise("Vinci")
            print(f"\n✅ CompanyInfoService: {len(results)} résultats pour 'Vinci'")
        except Exception as e:
            print(f"\n❌ CompanyInfoService: {e}")
    
    # Test Universal Search Service
    if 'universal_search' in _services_instances:
        try:
            service = _services_instances['universal_search']
            import asyncio
            result = asyncio.run(service.search("test"))
            print(f"\n✅ UniversalSearchService: {result.total_count} résultats")
        except Exception as e:
            print(f"\n❌ UniversalSearchService: {e}")
    
    # Test Style Learning Service
    if 'style_learning' in _services_instances:
        try:
            service = _services_instances['style_learning']
            print(f"\n✅ StyleLearningService: {len(service.learned_styles)} styles appris")
        except Exception as e:
            print(f"\n❌ StyleLearningService: {e}")
    
    # Nettoyer
    cleanup_services()
    print("\n🧹 Services nettoyés")

# Auto-initialisation si dans Streamlit
try:
    import streamlit as st
    if 'services_initialized' not in st.session_state:
        st.session_state.services_initialized = True
        initialize_all_services()
except ImportError:
    pass

# Point d'entrée pour les tests
if __name__ == "__main__":
    test_services()