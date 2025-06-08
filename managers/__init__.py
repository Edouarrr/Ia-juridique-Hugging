# managers/__init__.py
from managers.multi_llm_manager import MultiLLMManager
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from managers.document_manager import DocumentManager
from managers.style_analyzer import StyleAnalyzer
from managers.dynamic_generators import generate_dynamic_search_prompts, generate_dynamic_templates
from managers.jurisprudence_verifier import JurisprudenceVerifier
from managers.legal_search import LegalSearchManager
from managers.company_info_manager import CompanyInfoManager, get_company_info_manager

__all__ = [
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
    'get_company_info_manager'
]