"""Script pour créer la structure de dossiers nécessaire"""

import os

# Créer les dossiers nécessaires
folders = [
    "config",
    "modules", 
    "utils",
    "managers",
    "models"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    
    # Créer un fichier __init__.py dans chaque dossier
    init_file = os.path.join(folder, "__init__.py")
    with open(init_file, "w") as f:
        f.write("# Permet à Python de reconnaître ce dossier comme un package\n")
    
    print(f"✅ Créé : {folder}/__init__.py")

print("\n✅ Structure de dossiers créée avec succès!")