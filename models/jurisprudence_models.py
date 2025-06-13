# models/jurisprudence_models.py
"""
Fichier de redirection pour les modèles de jurisprudence
Redirige vers modules.dataclasses où se trouvent les vraies définitions
"""

# Import et réexport de toutes les classes liées à la jurisprudence
from modules.dataclasses import (
    # Classes principales de jurisprudence
    JurisprudenceReference,
    JurisprudenceSearch,
    VerificationResult,
    SourceJurisprudence,
    TypeJuridiction,
    TypeDocument,
    DocumentJuridique,
    
    # Classes associées
    AnalyseJuridique,
    CasJuridique,
    JurisprudenceCase,
    
    # Énumérations
    SourceEntreprise,
    RiskLevel,
    DocumentType,
    
    # Autres classes potentiellement utilisées
    QueryAnalysis,
    Document,
    SearchResult
)

# Pour la compatibilité complète
from modules.dataclasses import *