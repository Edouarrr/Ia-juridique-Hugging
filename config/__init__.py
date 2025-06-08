# config/__init__.py
"""Module de configuration"""

from .app_config import app_config, api_config, DEFAULT_TEMPLATES, DOCUMENT_CATEGORIES, JURIDICTIONS

__all__ = [
    'app_config',
    'api_config', 
    'DEFAULT_TEMPLATES',
    'DOCUMENT_CATEGORIES',
    'JURIDICTIONS'
]