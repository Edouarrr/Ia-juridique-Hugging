# check_llm_imports.py
"""
Script pour vérifier quels fichiers utilisent quel manager
et s'assurer que tout est cohérent
"""

import os
import re

def check_llm_usage():
    """Vérifie l'utilisation des managers LLM dans le projet"""
    
    # Patterns à rechercher
    patterns = {
        'multi_llm': [
            r'from managers\.multi_llm_manager import',
            r'import managers\.multi_llm_manager',
            r'MultiLLMManager'
        ],
        'llm_simple': [
            r'from managers\.llm_manager import',
            r'import managers\.llm_manager',
            r'LLMManager(?!\w)'  # LLMManager mais pas MultiLLMManager
        ]
    }
    
    # Dossiers à scanner
    directories = ['managers', 'modules', 'utils']
    
    results = {
        'multi_llm_users': [],
        'llm_simple_users': [],
        'both_users': []
    }
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.endswith('.py'):
                filepath = os.path.join(directory, filename)
                
                # Skip les fichiers eux-mêmes
                if filename in ['llm_manager.py', 'multi_llm_manager.py']:
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    uses_multi = any(re.search(p, content) for p in patterns['multi_llm'])
                    uses_simple = any(re.search(p, content) for p in patterns['llm_simple'])
                    
                    if uses_multi and uses_simple:
                        results['both_users'].append(filepath)
                    elif uses_multi:
                        results['multi_llm_users'].append(filepath)
                    elif uses_simple:
                        results['llm_simple_users'].append(filepath)
                        
                except Exception as e:
                    print(f"Erreur lecture {filepath}: {e}")
    
    return results

def print_report(results):
    """Affiche le rapport d'utilisation"""
    
    print("📊 RAPPORT D'UTILISATION DES MANAGERS LLM")
    print("=" * 50)
    
    print(f"\n🚀 Fichiers utilisant MultiLLMManager ({len(results['multi_llm_users'])}):")
    for file in results['multi_llm_users']:
        print(f"   - {file}")
    
    print(f"\n📦 Fichiers utilisant LLMManager simple ({len(results['llm_simple_users'])}):")
    for file in results['llm_simple_users']:
        print(f"   - {file}")
    
    print(f"\n🔄 Fichiers utilisant les deux ({len(results['both_users'])}):")
    for file in results['both_users']:
        print(f"   - {file}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    print("=" * 50)
    
    if results['llm_simple_users']:
        print("\n1. Fichiers utilisant LLMManager simple :")
        print("   ✅ Pas de modification nécessaire")
        print("   ℹ️ Ils utiliseront MultiLLMManager via llm_manager.py")
    
    if results['both_users']:
        print("\n2. Fichiers utilisant les deux :")
        print("   ⚠️ Vérifier qu'il n'y a pas de conflit")
        print("   💡 Considérer utiliser seulement MultiLLMManager")
    
    print("\n3. Architecture recommandée :")
    print("   - Nouveaux modules → MultiLLMManager")
    print("   - Anciens modules → LLMManager (compatibilité)")
    print("   - Garder les deux fichiers pour flexibilité")

if __name__ == "__main__":
    results = check_llm_usage()
    print_report(results)
    
    # Test que les imports fonctionnent
    print("\n" + "=" * 50)
    print("🧪 TEST DES IMPORTS")
    print("=" * 50)
    
    try:
        from managers.llm_manager import LLMManager
        print("✅ Import LLMManager OK")
    except Exception as e:
        print(f"❌ Import LLMManager : {e}")
    
    try:
        from managers.multi_llm_manager import MultiLLMManager
        print("✅ Import MultiLLMManager OK")
    except Exception as e:
        print(f"❌ Import MultiLLMManager : {e}")
    
    try:
        from managers.llm_manager import LLMManager
        llm = LLMManager()
        if hasattr(llm, 'use_multi') and llm.use_multi:
            print("✅ LLMManager utilise bien MultiLLMManager en interne")
        else:
            print("⚠️ LLMManager en mode autonome")
    except Exception as e:
        print(f"❌ Test intégration : {e}")