# managers/__init__.py
"""
Package managers - Gestionnaires pour l'application juridique
"""

# Import conditionnel des managers disponibles
__all__ = []

# Azure Blob Manager
try:
    from .azure_blob_manager import AzureBlobManager
    __all__.append('AzureBlobManager')
except ImportError:
    pass

# Azure Search Manager  
try:
    from .azure_search_manager import AzureSearchManager
    __all__.append('AzureSearchManager')
except ImportError:
    pass

# Company Info Manager
try:
    from .company_info_manager import CompanyInfoManager
    __all__.append('CompanyInfoManager')
except ImportError:
    pass

# Document Manager
try:
    from .document_manager import DocumentManager
    __all__.append('DocumentManager')
except ImportError:
    pass

# Dynamic Generators
try:
    from .dynamic_generators import DynamicGenerators
    __all__.append('DynamicGenerators')
except ImportError:
    pass

# Export Manager
try:
    from .export_manager import ExportManager
    __all__.append('ExportManager')
except ImportError:
    pass

# Jurisprudence Verifier
try:
    from .jurisprudence_verifier import JurisprudenceVerifier
    __all__.append('JurisprudenceVerifier')
except ImportError:
    pass

# Legal Search
try:
    from .legal_search import LegalSearchManager
    __all__.append('LegalSearchManager')
except ImportError:
    pass

# LLM Manager
try:
    from .llm_manager import LLMManager
    __all__.append('LLMManager')
except ImportError:
    pass

# Multi LLM Manager
try:
    from .multi_llm_manager import MultiLLMManager
    __all__.append('MultiLLMManager')
except ImportError:
    pass

# Style Analyzer
try:
    from .style_analyzer import StyleAnalyzer
    __all__.append('StyleAnalyzer')
except ImportError:
    pass

# Template Manager
try:
    from .template_manager import TemplateManager
    __all__.append('TemplateManager')
except ImportError:
    pass

# Universal Search Interface
try:
    from .UniversalSearchInterface import UniversalSearchInterface
    __all__.append('UniversalSearchInterface')
except ImportError:
    pass

# Universal Search Service
try:
    from .universal_search_service import UniversalSearchService
    __all__.append('UniversalSearchService')
except ImportError:
    pass