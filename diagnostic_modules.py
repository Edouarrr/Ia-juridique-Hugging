"""Diagnostic détaillé des modules"""

import os
import sys
import importlib
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnostic_modules():
    """Effectue un diagnostic complet des modules"""
    
    print("\n" + "="*50)
    print("🔍 DIAGNOSTIC DÉTAILLÉ DES MODULES")
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*50 + "\n")
    
    # 1. Vérifier le dossier modules
    modules_dir = 'modules'
    if not os.path.exists(modules_dir):
        print("❌ ERREUR: Le dossier 'modules' n'existe pas!")
        return
    
    # 2. Lister tous les fichiers Python
    py_files = [f for f in os.listdir(modules_dir) if f.endswith('.py') and f != '__init__.py']
    print(f"📁 Fichiers Python trouvés: {len(py_files)}")
    print("-" * 50)
    
    # 3. Tester l'import de chaque module
    success_count = 0
    error_count = 0
    
    for py_file in sorted(py_files):
        module_name = py_file[:-3]  # Enlever .py
        
        # Vérifier les caractères problématiques
        issues = []
        if '-' in module_name:
            issues.append("contient des tirets")
        if any(ord(c) > 127 for c in module_name):
            issues.append("contient des caractères non-ASCII")
        
        print(f"\n📄 Module: {py_file}")
        
        if issues:
            print(f"   ⚠️ Problèmes de nommage: {', '.join(issues)}")
        
        # Tenter l'import
        try:
            module = importlib.import_module(f'modules.{module_name}')
            print(f"   ✅ Import réussi")
            
            # Vérifier les attributs du module
            attributes = [attr for attr in dir(module) if not attr.startswith('_')]
            classes = [attr for attr in attributes if attr[0].isupper()]
            functions = [attr for attr in attributes if attr[0].islower()]
            
            print(f"   📦 Contenu: {len(classes)} classes, {len(functions)} fonctions")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur d'import: {type(e).__name__}: {str(e)[:100]}")
            error_count += 1
    
    # 4. Résumé
    print("\n" + "="*50)
    print("📊 RÉSUMÉ")
    print("="*50)
    print(f"✅ Modules chargés avec succès: {success_count}")
    print(f"❌ Modules en erreur: {error_count}")
    print(f"📈 Taux de réussite: {(success_count/len(py_files)*100):.1f}%")
    
    # 5. Recommandations
    if error_count > 0:
        print("\n⚡ ACTIONS RECOMMANDÉES:")
        print("1. Renommez les fichiers avec des tirets (- → _)")
        print("2. Supprimez les accents des noms de fichiers")
        print("3. Vérifiez les imports dans chaque module en erreur")
        print("4. Assurez-vous que toutes les dépendances sont installées")

if __name__ == "__main__":
    diagnostic_modules()