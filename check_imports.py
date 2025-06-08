"""Vérification des imports"""

try:
    from models.jurisprudence_models import JurisprudenceReference
    print("✅ models.jurisprudence_models OK")
except ImportError as e:
    print(f"❌ {e}")

try:
    from models.dataclasses import Document
    print("✅ models.dataclasses OK")
except ImportError as e:
    print(f"❌ {e}")

# Ajoutez d'autres vérifications