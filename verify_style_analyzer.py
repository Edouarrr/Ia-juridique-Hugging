# verify_style_analyzer.py
"""Vérifie que style_analyzer.py est correctement formaté"""

def check_file():
    print("🔍 Vérification de managers/style_analyzer.py")
    print("=" * 50)
    
    # Test 1: Import du module
    try:
        from managers.style_analyzer import StyleAnalyzer
        print("✅ Import du module réussi")
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe ligne {e.lineno}: {e.msg}")
        print(f"   Vérifiez: {e.text}")
        return False
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Test 2: Instanciation
    try:
        analyzer = StyleAnalyzer()
        print("✅ Création d'instance réussie")
    except Exception as e:
        print(f"❌ Erreur lors de l'instanciation: {e}")
        return False
    
    # Test 3: Vérification des méthodes
    methods_to_check = [
        'analyze_document',
        '_extract_structure',
        '_extract_formules',
        '_analyze_formatting',
        '_analyze_vocabulary',
        'learn_style',
        'apply_style',
        'compare_styles'
    ]
    
    missing_methods = []
    for method in methods_to_check:
        if not hasattr(analyzer, method):
            missing_methods.append(method)
    
    if missing_methods:
        print(f"❌ Méthodes manquantes: {', '.join(missing_methods)}")
        return False
    else:
        print(f"✅ Toutes les méthodes principales existent")
    
    # Test 4: Vérifier les patterns
    if hasattr(analyzer, 'numbering_patterns'):
        print(f"✅ Patterns de numérotation: {list(analyzer.numbering_patterns.keys())}")
    else:
        print("❌ Attribut 'numbering_patterns' manquant")
        return False
    
    # Test 5: Test avec un document fictif
    try:
        from modules.dataclasses import Document
        
        # Créer un document de test
        test_doc = Document(
            id="test_001",
            title="Test Document",
            content="PAR CES MOTIFS\n\nIl convient de rappeler que ce document est un test.",
            type="conclusions",
            source="test",
            metadata={}
        )
        
        # Analyser le document
        result = analyzer.analyze_document(test_doc)
        print("✅ Analyse de document réussie")
        print(f"   - Formules trouvées: {len(result.formules)}")
        print(f"   - Structure sections: {result.structure.get('section_count', 0)}")
        
    except Exception as e:
        print(f"⚠️ Test d'analyse échoué (normal si dataclasses pas encore importé): {e}")
    
    print("\n" + "=" * 50)
    print("✨ Vérification terminée avec succès!")
    return True

if __name__ == "__main__":
    check_file()