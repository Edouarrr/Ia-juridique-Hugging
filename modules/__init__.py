"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
"""

import os
import sys
from pathlib import Path

# Import des dataclasses depuis ce module pour faciliter l'accès
try:
    from .dataclasses import *
except ImportError as e:
    print(f"Erreur lors de l'import des dataclasses: {e}")

# Liste des modules disponibles
__all__ = ['dataclasses']

# Liste des modules RÉELLEMENT présents (basée sur votre capture d'écran)
modules_list = [
    'comparison',
    'configuration', 
    'dossier_penal',
    'email',
    'explorer',
    'export_manager',  # Corrigé (pas export_juridique)
    'generation_longue',  # Corrigé (pas generation-longue)
    'import_export',
    'integration_juridique',
    'jurisprudence',
    'mapping',
    'pieces_manager',
    'plaidoirie',
    'preparation_client',
    'recherche_analyse_unifiee',  # Ajouté
    'redaction',
    'redaction_unified',
    'risques',
    'synthesis',
    'template',
    'timeline'
]

# Liste pour tracker les modules chargés avec succès
loaded_modules = []

# Import conditionnel de chaque module
for module_name in modules_list:
    try:
        # Import normal pour tous les modules
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
        if module in loaded_modules:
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