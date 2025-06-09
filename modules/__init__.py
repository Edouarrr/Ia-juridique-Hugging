"""
Package models - Contient tous les modèles de données de l'application
"""

# Import des dataclasses
from .dataclasses import (
    Document,
    DocumentType,
    Jurisprudence,
    PieceProcedure,
    Risque,
    RiskLevel,
    EvenementTimeline,
    DossierPenal,
    TemplateDocument,
    ResultatRecherche,
    AnalyseJuridique,
    ConfigurationRecherche,
    Notification,
    SessionUtilisateur
)

# Import des modèles de jurisprudence (si le fichier existe)
try:
    from .jurisprudence_models import *
except ImportError:
    pass

# Export de tous les symboles
__all__ = [
    # Enums
    'DocumentType',
    'RiskLevel',
    
    # Dataclasses principales
    'Document',
    'Jurisprudence',
    'PieceProcedure',
    'Risque',
    'EvenementTimeline',
    'DossierPenal',
    'TemplateDocument',
    'ResultatRecherche',
    'AnalyseJuridique',
    'ConfigurationRecherche',
    
    # Classes utilitaires
    'Notification',
    'SessionUtilisateur'
]