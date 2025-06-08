"""Classes de données pour l'application juridique"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class Document:
    """Document de base"""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PieceSelectionnee:
    """Pièce sélectionnée pour un dossier"""
    numero: int
    titre: str
    description: str = ""
    categorie: str = "Autre"
    date: Optional[datetime] = None
    source: str = ""
    pertinence: float = 0.5

@dataclass
class DocumentJuridique:
    """Document juridique avec métadonnées"""
    id: str
    titre: str
    contenu: str
    type_document: str
    date_creation: datetime
    source: str
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []

@dataclass
class AnalyseJuridique:
    """Analyse juridique d'un document ou cas"""
    id: str
    document_id: str
    type_analyse: str
    contenu: str
    date_analyse: datetime
    resultats: Dict[str, Any] = None
    recommandations: List[str] = None
    risques_identifies: List[str] = None
    
    def __post_init__(self):
        if self.resultats is None:
            self.resultats = {}
        if self.recommandations is None:
            self.recommandations = []
        if self.risques_identifies is None:
            self.risques_identifies = []

@dataclass
class CasJuridique:
    """Cas juridique complet"""
    id: str
    reference: str
    titre: str
    description: str
    date_ouverture: datetime
    statut: str = "ouvert"
    parties: Dict[str, Any] = None
    documents: List[DocumentJuridique] = None
    analyses: List[AnalyseJuridique] = None
    historique: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.parties is None:
            self.parties = {}
        if self.documents is None:
            self.documents = []
        if self.analyses is None:
            self.analyses = []
        if self.historique is None:
            self.historique = []