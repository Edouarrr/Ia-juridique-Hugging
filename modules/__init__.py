# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
"""

import os
import sys
import importlib.util
from pathlib import Path

# Import des dataclasses depuis ce module pour faciliter l'accès
try:
    from .dataclasses import *
except ImportError as e:
    print(f"Erreur lors de l'import des dataclasses: {e}")

# Liste des modules disponibles
__all__ = ['dataclasses']

# Liste des modules à importer
modules_list = [
    'analyse_ia',
    'bordereau',
    'comparison',
    'configuration',
    'dossier_penal',
    'email',
    'explorer',
    'export_juridique',
    'generation_juridique',
    'generation-longue',  # Module avec tiret
    'import_export',
    'integration_juridique',
    'jurisprudence',
    'mapping',
    'pieces_manager',
    'plaidoirie',
    'preparation_client',
    'recherche',
    'redaction',
    'redaction_unified',
    'risques',
    'selection_pieces',
    'synthesis',
    'template',
    'timeline'
]

# Liste pour tracker les modules chargés avec succès
loaded_modules = []

# Import conditionnel de chaque module
for module_name in modules_list:
    try:
        # Gérer les modules avec tirets
        if '-' in module_name:
            # Pour les modules avec tirets, on doit utiliser importlib
            import_name = module_name.replace('-', '_')
            current_dir = Path(__file__).parent
            module_file = current_dir / f"{module_name}.py"
            
            if module_file.exists():
                # Charger le module manuellement
                spec = importlib.util.spec_from_file_location(import_name, module_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"modules.{import_name}"] = module
                    spec.loader.exec_module(module)
                    
                    # Ajouter le module au namespace local
                    globals()[import_name] = module
                    setattr(sys.modules[__name__], import_name, module)
                    
                    __all__.append(import_name)
                    loaded_modules.append(import_name)
                    print(f"✓ Module {import_name} (depuis {module_name}.py) importé avec succès")
                else:
                    print(f"⚠️ Impossible de créer la spec pour {module_name}")
            else:
                print(f"⚠️ Fichier {module_name}.py non trouvé")
        else:
            # Import normal pour les modules sans tirets
            exec(f"from . import {module_name}")
            __all__.append(module_name)
            loaded_modules.append(module_name)
            print(f"✓ Module {module_name} importé avec succès")
            
    except ImportError as e:
        # Module non disponible, continuer
        print(f"⚠️ Module {module_name} non disponible: {e}")
    except Exception as e:
        # Autre erreur
        print(f"❌ Erreur lors de l'import de {module_name}: {e}")

# Fonctions utilitaires
def get_loaded_modules():
    """Retourne la liste des modules chargés avec succès"""
    return loaded_modules

def debug_modules_status(output_to_streamlit=False):
    """Affiche le statut de tous les modules"""
    output = []
    output.append("=== STATUT DES MODULES ===")
    output.append(f"Modules chargés: {len(loaded_modules)}/{len(modules_list)}")
    output.append("")
    
    for module in modules_list:
        # Vérifier avec le nom importé (tirets remplacés par underscores)
        import_name = module.replace('-', '_')
        if import_name in loaded_modules:
            output.append(f"✓ {module}")
        else:
            output.append(f"✗ {module}")
    
    debug_text = "\n".join(output)
    
    if output_to_streamlit:
        return debug_text
    else:
        print(debug_text)
        
    return debug_text

# Ajouter les fonctions utilitaires à __all__
__all__.extend(['get_loaded_modules', 'debug_modules_status'])

# Afficher le résumé au chargement
print(f"\n📦 Modules chargés: {len(loaded_modules)}/{len(modules_list)}")