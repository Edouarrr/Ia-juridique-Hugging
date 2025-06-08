"""Scanner tous les imports manquants"""

import os
import re

print("🔍 Scan des imports dans tout le projet...\n")

# Parcourir tous les fichiers Python
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Chercher les imports from models.dataclasses
                imports = re.findall(r'from models\.dataclasses import ([^\n]+)', content)
                
                if imports:
                    print(f"\n📄 {filepath}")
                    for imp in imports:
                        classes = [c.strip() for c in imp.split(',')]
                        print(f"   Importe: {', '.join(classes)}")
                        
            except Exception as e:
                pass

print("\n✅ Scan terminé!")