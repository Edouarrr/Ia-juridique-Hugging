# utils/__init__.py
"""
Package utils contenant les fonctions utilitaires pour l'application juridique
"""

# Import des modules principaux pour faciliter l'accès
from . import helpers
from . import text_processing
from . import file_utils
from . import formatters
from . import validators
from . import legal_utils
from . import date_time
from . import document_utils
from . import exports
from . import test_utils
from . import cache_manager
from . import session
from . import styles
from . import constants

# Version du package
__version__ = '1.0.0'

# Exposer les fonctions les plus utilisées directement
from .helpers import truncate_text, clean_key
from .text_processing import process_text, clean_text
from .file_utils import save_file, load_file
from .formatters import format_date, format_currency
from .validators import validate_email, validate_phone

__all__ = [
    'helpers',
    'text_processing', 
    'file_utils',
    'formatters',
    'validators',
    'legal_utils',
    'date_time',
    'document_utils',
    'exports',
    'test_utils',
    'cache_manager',
    'session',
    'styles',
    'constants',
    # Fonctions exposées directement
    'truncate_text',
    'clean_key',
    'process_text',
    'clean_text',
    'save_file',
    'load_file',
    'format_date',
    'format_currency',
    'validate_email',
    'validate_phone'
]