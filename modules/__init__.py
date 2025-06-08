# modules/__init__.py
"""
Modules de l'application Assistant Pénal des Affaires IA
Contient toutes les pages et fonctionnalités de l'application
"""

# Imports des modules disponibles
try:
    from .recherche import show_page as show_recherche_page
    RECHERCHE_AVAILABLE = True
except ImportError:
    RECHERCHE_AVAILABLE = False

# Liste des modules disponibles
AVAILABLE_MODULES = []

if RECHERCHE_AVAILABLE:
    AVAILABLE_MODULES.append('recherche')

# Export des modules
__all__ = ['show_recherche_page'] if RECHERCHE_AVAILABLE else []