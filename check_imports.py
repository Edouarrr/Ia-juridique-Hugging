"""Vérification de tous les imports du projet"""

import sys
import traceback

print("🔍 Vérification des imports...\n")
print("=" * 60)

errors = []
warnings = []

# 1. Vérifier les modèles
print("\n📦 MODELS")
print("-" * 30)

try:
    from models.jurisprudence_models import (
        JurisprudenceReference, VerificationResult, SourceJurisprudence,
        JurisprudenceSearchCriteria, JurisprudenceAnalysis
    )
    print("✅ models.jurisprudence_models OK")
except ImportError as e:
    print(f"❌ models.jurisprudence_models ERREUR")
    errors.append(f"models.jurisprudence_models: {str(e)}")

try:
    from models.dataclasses import (
        Document, PieceSelectionnee, DocumentJuridique,
        AnalyseJuridique, CasJuridique, StylePattern,
        SearchPattern, AnalysisResult, ExportConfig,
        SearchResult, UserPreferences, TaskResult
    )
    print("✅ models.dataclasses OK")
except ImportError as e:
    print(f"❌ models.dataclasses ERREUR")
    errors.append(f"models.dataclasses: {str(e)}")

# 2. Vérifier les managers
print("\n📦 MANAGERS")
print("-" * 30)

managers_to_check = [
    ("managers.legal_search", ["LegalSearchManager", "display_legal_search_interface"]),
    ("managers.dynamic_generators", ["generate_dynamic_search_prompts"]),
    ("managers.jurisprudence_verifier", ["JurisprudenceVerifier"]),
    ("managers.azure_blob_manager", ["AzureBlobManager"]),
    ("managers.azure_search_manager", ["AzureSearchManager"]),
    ("managers.multi_llm_manager", ["MultiLLMManager"]),
    ("managers.document_manager", ["display_import_interface"]),
]

for module_name, imports in managers_to_check:
    try:
        module = __import__(module_name, fromlist=imports)
        for item in imports:
            if hasattr(module, item):
                print(f"✅ {module_name}.{item} OK")
            else:
                print(f"⚠️ {module_name}.{item} non trouvé")
                warnings.append(f"{module_name}.{item} non trouvé dans le module")
    except ImportError as e:
        print(f"❌ {module_name} ERREUR")
        errors.append(f"{module_name}: {str(e)}")
    except Exception as e:
        print(f"❌ {module_name} ERREUR INATTENDUE")
        errors.append(f"{module_name}: {type(e).__name__}: {str(e)}")

# 3. Vérifier la config
print("\n📦 CONFIG")
print("-" * 30)

try:
    from config.app_config import SearchMode, ANALYSIS_PROMPTS_AFFAIRES, LLMProvider
    print("✅ config.app_config OK")
except ImportError as e:
    print(f"❌ config.app_config ERREUR")
    errors.append(f"config.app_config: {str(e)}")

# 4. Vérifier les utils
print("\n📦 UTILS")
print("-" * 30)

try:
    from utils.helpers import clean_key
    print("✅ utils.helpers OK")
except ImportError as e:
    print(f"❌ utils.helpers ERREUR")
    errors.append(f"utils.helpers: {str(e)}")

# 5. Vérifier les bibliothèques externes
print("\n📦 BIBLIOTHÈQUES EXTERNES")
print("-" * 30)

external_libs = {
    "streamlit": "requis",
    "pandas": "optionnel",
    "plotly": "optionnel",
    "networkx": "optionnel",
    "docx": "optionnel",
    "PyPDF2": "optionnel",
    "openpyxl": "optionnel",
}

for lib, status in external_libs.items():
    try:
        __import__(lib)
        print(f"✅ {lib} OK")
    except ImportError:
        if status == "requis":
            print(f"❌ {lib} MANQUANT (REQUIS)")
            errors.append(f"{lib}: bibliothèque requise non installée")
        else:
            print(f"⚠️ {lib} non installé ({status})")
            warnings.append(f"{lib}: bibliothèque optionnelle non installée")

# 6. Vérifier le module principal
print("\n📦 MODULE PRINCIPAL")
print("-" * 30)

try:
    from modules.recherche import show_page
    print("✅ modules.recherche OK")
except SyntaxError as e:
    print(f"❌ modules.recherche ERREUR DE SYNTAXE")
    errors.append(f"modules.recherche: Erreur de syntaxe ligne {e.lineno}: {e.msg}")
except ImportError as e:
    print(f"❌ modules.recherche ERREUR D'IMPORT")
    errors.append(f"modules.recherche: {str(e)}")
except Exception as e:
    print(f"❌ modules.recherche ERREUR INATTENDUE")
    errors.append(f"modules.recherche: {type(e).__name__}: {str(e)}")

# Résumé
print("\n" + "=" * 60)
print("📊 RÉSUMÉ")
print("=" * 60)

if errors:
    print(f"\n❌ {len(errors)} ERREURS CRITIQUES:")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
else:
    print("\n✅ Aucune erreur critique")

if warnings:
    print(f"\n⚠️ {len(warnings)} AVERTISSEMENTS:")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")
else:
    print("\n✅ Aucun avertissement")

print("\n✅ Vérification terminée!")

# Retourner le statut
sys.exit(1 if errors else 0)