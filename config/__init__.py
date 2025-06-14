# config/__init__.py
"""Module de configuration"""

# Import depuis app_config.py
from .app_config import (ANALYSIS_CONFIG, ANALYSIS_PROMPTS_AFFAIRES,
                         ANALYSIS_PROMPTS_INFRACTIONS, DOCUMENT_CATEGORIES,
                         DOCUMENT_TEMPLATES, ERROR_MESSAGES, JURIDICTIONS,
                         LEGAL_APIS, LEGAL_PHRASES, PRESCRIPTIONS,
                         REDACTION_STYLES, RISK_LEVELS, SANCTIONS_TYPES,
                         SUCCESS_MESSAGES, APIConfig, AppConfig, DocumentType,
                         InfractionAffaires, IntentType, LLMProvider,
                         SearchMode, api_config, app_config)
# Import depuis cahier_des_charges.py
from .cahier_des_charges import (CABINET_INFO, FORMULES_JURIDIQUES,
                                 FORMULES_POLITESSE, HIERARCHIE_NUMEROTATION,
                                 INFRACTIONS_PENALES, JURISPRUDENCES_REFERENCE,
                                 MESSAGES_ERREUR, PIECES_TYPES,
                                 PROMPTS_GENERATION, REGLES_VALIDATION,
                                 STRUCTURES_ACTES, STYLE_DOCUMENT,
                                 TEMPLATES_SECTIONS, get_config_for_acte,
                                 get_infraction_details,
                                 get_jurisprudences_for_theme, validate_acte)

# Pour la compatibilité avec l'ancien nom
DEFAULT_TEMPLATES = DOCUMENT_TEMPLATES

__all__ = [
    # Depuis app_config.py
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
    'InfractionAffaires',
    'LEGAL_APIS',
    'APIConfig',
    'AppConfig',
    
    # Depuis cahier_des_charges.py
    'CABINET_INFO',
    'STYLE_DOCUMENT',
    'HIERARCHIE_NUMEROTATION',
    'STRUCTURES_ACTES',
    'TEMPLATES_SECTIONS',
    'FORMULES_JURIDIQUES',
    'INFRACTIONS_PENALES',
    'JURISPRUDENCES_REFERENCE',
    'PIECES_TYPES',
    'FORMULES_POLITESSE',
    'REGLES_VALIDATION',
    'MESSAGES_ERREUR',
    'PROMPTS_GENERATION',
    'get_config_for_acte',
    'get_infraction_details',
    'get_jurisprudences_for_theme',
    'validate_acte'
]