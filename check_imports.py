# check_imports.py
"""
Script de diagnostic pour vérifier tous les imports
Exécutez ce script pour identifier les problèmes d'import
"""

import sys
import traceback


def check_import(module_path, items=None):
    """Vérifie qu'un module peut être importé"""
    try:
        if items:
            exec(f"from {module_path} import {', '.join(items)}")
            print(f"✅ {module_path} -> {', '.join(items)}")
        else:
            exec(f"import {module_path}")
            print(f"✅ {module_path}")
        return True
    except Exception as e:
        print(f"❌ {module_path}: {str(e)}")
        return False

def main():
    print("🔍 VÉRIFICATION DES IMPORTS")
    print("=" * 50)
    
    # 1. Vérifier les dataclasses
    print("\n📁 DATACLASSES:")
    print("-" * 30)
    
    # Via modules
    check_import("modules.dataclasses", [
        "TypeDocument",
        "Partie", 
        "InfractionIdentifiee",
        "StyleRedaction",
        "DocumentJuridique"
    ])
    
    # Via models (redirection)
    check_import("models.dataclasses", [
        "TypeDocument",
        "Partie"
    ])
    
    # 2. Vérifier les managers
    print("\n📁 MANAGERS:")
    print("-" * 30)
    
    managers = [
        ("managers.multi_llm_manager", ["MultiLLMManager"]),
        ("managers.template_manager", ["TemplateManager"]),
        ("managers.style_analyzer", ["StyleAnalyzer"]),
        ("managers.jurisprudence_verifier", ["JurisprudenceVerifier"]),
        ("managers.unified_document_generator", [
            "UnifiedDocumentGenerator",
            "UnifiedGenerationRequest",
            "DocumentLength",
            "PlaidoirieDuration"
        ])
    ]
    
    for module, items in managers:
        check_import(module, items)
    
    # 3. Vérifier les modules
    print("\n📁 MODULES:")
    print("-" * 30)
    
    modules = [
        "modules.redaction_acte",
        "modules.plaidoirie",
        "modules.preparation_client"
    ]
    
    for module in modules:
        check_import(module)
    
    # 4. Test d'instanciation
    print("\n🧪 TEST D'INSTANCIATION:")
    print("-" * 30)
    
    try:
        from managers.unified_document_generator import \
            UnifiedDocumentGenerator
        generator = UnifiedDocumentGenerator()
        print("✅ UnifiedDocumentGenerator instancié avec succès")
        
        # Vérifier les plugins
        print(f"   Plugins disponibles: {list(generator.plugins.keys())}")
        
    except Exception as e:
        print(f"❌ Erreur d'instanciation: {str(e)}")
        traceback.print_exc()
    
    # 5. Test des dépendances circulaires
    print("\n🔄 TEST DES DÉPENDANCES CIRCULAIRES:")
    print("-" * 30)
    
    try:
        # Importer dans l'ordre inverse pour détecter les cycles
        import managers.unified_document_generator
        import modules.dataclasses
        import modules.redaction_acte
        print("✅ Pas de dépendances circulaires détectées")
    except Exception as e:
        print(f"❌ Dépendance circulaire possible: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Diagnostic terminé!")

if __name__ == "__main__":
    main()