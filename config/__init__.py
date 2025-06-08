# config/__init__.py
"""Module de configuration"""

from .app_config import (
    app_config, 
    api_config, 
    DOCUMENT_TEMPLATES,  # Changé de DEFAULT_TEMPLATES à DOCUMENT_TEMPLATES
    DOCUMENT_CATEGORIES, 
    JURIDICTIONS,
    REDACTION_STYLES,
    LEGAL_PHRASES,
    ANALYSIS_CONFIG,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    PRESCRIPTIONS,
    SANCTIONS_TYPES,
    RISK_LEVELS,
    ANALYSIS_PROMPTS_AFFAIRES,
    ANALYSIS_PROMPTS_INFRACTIONS,
    SearchMode,
    LLMProvider,
    DocumentType,
    IntentType,
    InfractionAffaires
)

# Pour la compatibilité avec l'ancien nom
DEFAULT_TEMPLATES = DOCUMENT_TEMPLATES

__all__ = [
    'app_config',
    'api_config', 
    'DOCUMENT_TEMPLATES',
    'DEFAULT_TEMPLATES',  # Gardé pour compatibilité
    'DOCUMENT_CATEGORIES',
    'JURIDICTIONS',
    'REDACTION_STYLES',
    'LEGAL_PHRASES',
    'ANALYSIS_CONFIG',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'PRESCRIPTIONS',
    'SANCTIONS_TYPES',
    'RISK_LEVELS',
    'ANALYSIS_PROMPTS_AFFAIRES',
    'ANALYSIS_PROMPTS_INFRACTIONS',
    'SearchMode',
    'LLMProvider',
    'DocumentType',
    'IntentType',
    'InfractionAffaires'
]