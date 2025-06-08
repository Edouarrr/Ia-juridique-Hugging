"""Vérification de tous les imports du projet"""

print("🔍 Vérification des imports...\n")

# 1. Vérifier les modèles
print("=== MODELS ===")
try:
    from models.jurisprudence_models import JurisprudenceReference, VerificationResult, SourceJurisprudence
    print("✅ models.jurisprudence_models OK")
except ImportError as e:
    print(f"❌ models.jurisprudence_models MANQUANT: {e}")

try:
    from models.dataclasses import Document, PieceSelectionnee
    print("✅ models.dataclasses OK")
except ImportError as e:
    print(f"❌ models.dataclasses MANQUANT: {e}")

# 2. Vérifier les managers
print("\n=== MANAGERS ===")
try:
    from managers.legal_search import LegalSearchManager, display_legal_search_interface
    print("✅ managers.legal_search OK")
except ImportError as e:
    print(f"❌ managers.legal_search MANQUANT: {e}")

try:
    from managers.dynamic_generators import generate_dynamic_search_prompts
    print("✅ managers.dynamic_generators OK")
except ImportError as e:
    print(f"❌ managers.dynamic_generators MANQUANT: {e}")

try:
    from managers.jurisprudence_verifier import JurisprudenceVerifier
    print("✅ managers.jurisprudence_verifier OK")
except ImportError as e:
    print(f"❌ managers.jurisprudence_verifier PROBLÈME: {e}")

try:
    from managers.azure_blob_manager import AzureBlobManager
    print("✅ managers.azure_blob_manager OK")
except ImportError as e:
    print(f"❌ managers.azure_blob_manager MANQUANT: {e}")

try:
    from managers.azure_search_manager import AzureSearchManager
    print("✅ managers.azure_search_manager OK")
except ImportError as e:
    print(f"❌ managers.azure_search_manager MANQUANT: {e}")

try:
    from managers.multi_llm_manager import MultiLLMManager
    print("✅ managers.multi_llm_manager OK")
except ImportError as e:
    print(f"❌ managers.multi_llm_manager MANQUANT: {e}")

try:
    from managers.document_manager import display_import_interface
    print("✅ managers.document_manager OK")
except ImportError as e:
    print(f"❌ managers.document_manager MANQUANT: {e}")

# 3. Vérifier la config
print("\n=== CONFIG ===")
try:
    from config.app_config import SearchMode, ANALYSIS_PROMPTS_AFFAIRES, LLMProvider
    print("✅ config.app_config OK")
except ImportError as e:
    print(f"❌ config.app_config MANQUANT: {e}")

# 4. Vérifier les utils
print("\n=== UTILS ===")
try:
    from utils.helpers import clean_key
    print("✅ utils.helpers OK")
except ImportError as e:
    print(f"❌ utils.helpers MANQUANT: {e}")

# 5. Vérifier les bibliothèques externes
print("\n=== BIBLIOTHÈQUES EXTERNES ===")
try:
    import pandas as pd
    print("✅ pandas OK")
except ImportError:
    print("⚠️ pandas non installé (optionnel)")

try:
    import plotly.graph_objects as go
    print("✅ plotly OK")
except ImportError:
    print("⚠️ plotly non installé (optionnel)")

try:
    import networkx as nx
    print("✅ networkx OK")
except ImportError:
    print("⚠️ networkx non installé (optionnel)")

try:
    import docx
    print("✅ python-docx OK")
except ImportError:
    print("⚠️ python-docx non installé (optionnel)")

print("\n✅ Vérification terminée !")