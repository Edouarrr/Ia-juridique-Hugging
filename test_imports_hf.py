# test_imports_hf.py
"""
Test rapide des imports pour Hugging Face
Créez ce fichier temporairement pour tester
"""

try:
    print("Test 1: Import depuis models.jurisprudence_models...")
    from models.jurisprudence_models import JurisprudenceReference
    print("✅ OK")
except Exception as e:
    print(f"❌ Erreur: {e}")

try:
    print("\nTest 2: Import depuis modules.dataclasses...")
    from modules.dataclasses import JurisprudenceReference as JR2
    print("✅ OK")
except Exception as e:
    print(f"❌ Erreur: {e}")

try:
    print("\nTest 3: Vérification que c'est la même classe...")
    if 'JurisprudenceReference' in locals() and 'JR2' in locals():
        if JurisprudenceReference is JR2:
            print("✅ Les classes sont identiques (redirection OK)")
        else:
            print("❌ Les classes sont différentes")
except Exception as e:
    print(f"❌ Erreur: {e}")

try:
    print("\nTest 4: Import des managers...")
    from managers.jurisprudence_verifier import JurisprudenceVerifier
    print("✅ JurisprudenceVerifier OK")
    from managers.legal_search import LegalSearchManager  
    print("✅ LegalSearchManager OK")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n✨ Tests terminés!")