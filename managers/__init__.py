# managers/__init__.py
"""
Centralisation des imports des managers de l'application
"""
from managers.llm_manager import LLMManager, get_llm_manager
from managers.multi_llm_manager import MultiLLMManager
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from managers.document_manager import DocumentManager
from managers.style_analyzer import StyleAnalyzer
from managers.dynamic_generators import generate_dynamic_search_prompts, generate_dynamic_templates
from managers.jurisprudence_verifier import JurisprudenceVerifier
from managers.legal_search import LegalSearchManager
from managers.company_info_manager import CompanyInfoManager, get_company_info_manager
from managers.universal_search_service import UniversalSearchService

__all__ = [
    'LLMManager',
    'get_llm_manager',
    'MultiLLMManager',
    'AzureBlobManager', 
    'AzureSearchManager',
    'DocumentManager',
    'StyleAnalyzer',
    'generate_dynamic_search_prompts',
    'generate_dynamic_templates',
    'JurisprudenceVerifier',
    'LegalSearchManager',
    'CompanyInfoManager',
    'get_company_info_manager',
    'UniversalSearchService'  # Ajout du service de recherche universelle
]

# Initialisation optionnelle des managers singleton
universal_search_service = None

def get_universal_search_service():
    """
    Retourne une instance singleton du service de recherche universelle
    """
    global universal_search_service
    if universal_search_service is None:
        universal_search_service = UniversalSearchService()
    return universal_search_service