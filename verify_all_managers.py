# verify_all_managers.py
"""
Vérifie l'état de tous les managers et leurs imports
"""

import os
import re

def verify_all_managers():
    """Vérifie tous les fichiers managers"""
    
    print("🔍 VÉRIFICATION COMPLÈTE DES MANAGERS")
    print("=" * 50)
    
    managers_status = {
        'ok': [],
        'need_fix': [],
        'missing': []
    }
    
    # Liste des managers attendus
    expected_managers = [
        'azure_blob_manager.py',
        'company_info_manager.py',
        'document_manager.py',
        'export_manager.py',
        'jurisprudence_verifier.py',
        'legal_search.py',
        'multi_llm_manager.py',
        'unified_document_generator.py',
        'universal_search_service.py',
        'llm_manager.py',
        'template_manager.py',
        'style_analyzer.py',
        'azure_search_manager.py',
        'dynamic_generators.py'
    ]
    
    # Managers qui doivent être modifiés
    need_modification = ['jurisprudence_verifier.py', 'legal_search.py']
    
    for manager in expected_managers:
        filepath = os.path.join('managers', manager)
        
        if os.path.exists(filepath):
            # Vérifier les imports
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les imports problématiques
            has_model_import = bool(re.search(r'from models\.[^.]+dataclasses import', content))
            has_jurisprudence_import = bool(re.search(r'from models\.jurisprudence_models import', content))
            
            if manager in need_modification and (has_model_import or has_jurisprudence_import):
                managers_status['need_fix'].append(manager)
            else:
                managers_status['ok'].append(manager)
        else:
            managers_status['missing'].append(manager)
    
    # Afficher le rapport
    print(f"\n✅ Managers OK ({len(managers_status['ok'])}):")
    for m in managers_status['ok']:
        print(f"   ✓ {m}")
    
    print(f"\n⚠️ Managers à modifier ({len(managers_status['need_fix'])}):")
    for m in managers_status['need_fix']:
        print(f"   ! {m} - Changer 'from models.' en 'from modules.'")
    
    print(f"\n❌ Managers manquants ({len(managers_status['missing'])}):")
    for m in managers_status['missing']:
        print(f"   × {m}")
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ:")
    print(f"   Total attendu : {len(expected_managers)}")
    print(f"   Présents OK : {len(managers_status['ok'])}")
    print(f"   À modifier : {len(managers_status['need_fix'])}")
    print(f"   Manquants : {len(managers_status['missing'])}")
    
    if managers_status['need_fix']:
        print("\n⚠️ ACTION REQUISE:")
        print("   Modifiez les imports dans les fichiers listés ci-dessus")
    
    if managers_status['missing']:
        print("\n💡 SUGGESTION:")
        print("   Ajoutez les managers manquants depuis les artifacts fournis")

if __name__ == "__main__":
    verify_all_managers()