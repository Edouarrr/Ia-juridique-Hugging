# config/__init__.py
from .app_config import *
from .llm_config import LLM_CONFIGS, get_llm_client
from .prompts import PROMPTS

# models/__init__.py
from .dataclasses import *
from .jurisprudence_models import *

# managers/__init__.py
from .llm_manager import LLMManager
from .document_manager import DocumentManager
from .jurisprudence_verifier import JurisprudenceVerifier
from .legal_search import LegalSearchManager

# pages/__init__.py
# Les pages sont importées dynamiquement par Streamlit

# utils/__init__.py
from .helpers import *
from .styles import load_custom_css, get_custom_styles