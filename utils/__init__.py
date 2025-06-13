# utils/__init__.py
"""
Package utils - Fonctions utilitaires pour l'application juridique
"""

# Imports simplifiés par module
from .session import initialize_session_state
from .text_processing import *
from .date_time import *
from .document_utils import *
from .legal_utils import *
from .file_utils import *
from .cache_manager import CacheJuridique, get_cache, cache_result, cache_streamlit
from .formatters import *
from .styles import load_custom_css

# Alias pour compatibilité
init_session_state = initialize_session_state

__version__ = "1.0.0"