# models/__init__.py
"""
Package models - Redirige vers modules.dataclasses pour la compatibilité
"""

# Import de toutes les classes depuis modules.dataclasses
from modules.dataclasses import *

# Re-exporter tout pour que les imports depuis models fonctionnent
__all__ = [
    # Documents
    'Document',
    'DocumentJuridique',
    'DocumentTemplate',
    'TemplateDocument',
    
    # Parties et affaires
    'Partie',
    'TypePartie',
    'CasJuridique',
    'InformationEntreprise',
    'SourceEntreprise',
    
    # Pièces et procédure
    'PieceSelectionnee',
    'BordereauPieces',
    'ElementProcedure',
    'PieceVersee',
    'PieceProcedure',
    'ChaineProcedure',
    'Piece',  # Alias pour compatibilité
    'BordereauItem',
    
    # Traçabilité
    'FactWithSource',
    'SourceReference',
    'ArgumentStructure',
    'SourceTracker',
    
    # Infractions
    'InfractionIdentifiee',
    'InfractionAffaires',
    
    # Dossiers
    'DossierPenal',
    'EvenementTimeline',
    
    # Enums
    'DocumentType',
    'RiskLevel',
    'SourceJurisprudence',
    'SourceEntreprise',
    'TypeDocument',
    'TypeJuridiction',
    'StatutProcedural',
    'PhaseProcedure',
    'InfractionAffaires',
    'LLMProvider',
    'SearchMode',
    'TypeElementProcedure',
    'NaturePiece',
    'ForceProbante',
    'StyleRedaction',
    'TypeAnalyse',
    'TypePartie',
    'ExportFormat',
    'TimelineType',
    'MappingType',
    'PartyType',
    
    # Styles et templates
    'StyleConfig',
    'StyleLearningResult',
    'StylePattern',
    'LetterheadTemplate',
    
    # Entités
    'Entity',
    
    # Timeline
    'TimelineEvent',
    
    # Recherche universelle
    'QueryAnalysis',
    'SearchResult',
    
    # Analyse et rédaction
    'AnalysisResult',
    'AnalyseJuridique',
    'RedactionResult',
    'JurisprudenceReference',
    'JurisprudenceCase',
    'VerificationResult',
    
    # Gestion des risques
    'Risque',
    'RiskAssessment',
    'AnalyseRisqueResult',
    
    # Notifications et sessions
    'Notification',
    'SessionUtilisateur',
    
    # Recherche
    'Jurisprudence',
    'ResultatRecherche',
    'ConfigurationRecherche',
    
    # Email
    'EmailConfig',
    'EmailMessage',
    'EmailCredentials',
    
    # Mapping
    'Relationship',
    'EntityNode',
    'RelationshipGraph',
    'LegalEntity',
    
    # Plaidoirie
    'PlaidoirieResult',
    'ArgumentJuridique',
    
    # Préparation client
    'PreparationClientResult',
    'QuestionClient',
    
    # Autres
    'GenerationResult',
    'ExportResult',
    'ExportConfig',
    'ComparisonResult',
    'Template',
    'GenerationParams',
    'UserPreferences',
    'ProcessingStatus'
]