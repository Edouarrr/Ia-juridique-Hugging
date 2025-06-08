"""Modèles de données pour la jurisprudence"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class SourceJurisprudence(Enum):
    """Sources de jurisprudence disponibles"""
    LEGIFRANCE = "legifrance"
    DOCTRINE = "doctrine"
    DALLOZ = "dalloz"
    LEXIS = "lexis"
    INTERNAL = "internal"
    MANUAL = "manual"
    COURDECASSATION = "courdecassation"
    CONSEILDETAT = "conseildetat"
    CONSEILCONSTITUTIONNEL = "conseilconstitutionnel"

@dataclass
class JurisprudenceReference:
    """Référence de jurisprudence"""
    numero: str
    date: datetime
    juridiction: str
    formation: Optional[str] = None
    titre: Optional[str] = None
    resume: Optional[str] = None
    texte_integral: Optional[str] = None
    url: Optional[str] = None
    source: SourceJurisprudence = SourceJurisprudence.MANUAL
    mots_cles: List[str] = None
    articles_vises: List[str] = None
    decisions_citees: List[str] = None
    importance: int = 5  # 1-10
    
    def __post_init__(self):
        if self.mots_cles is None:
            self.mots_cles = []
        if self.articles_vises is None:
            self.articles_vises = []
        if self.decisions_citees is None:
            self.decisions_citees = []

@dataclass
class VerificationResult:
    """Résultat de vérification d'une jurisprudence"""
    is_valid: bool
    reference: Optional[JurisprudenceReference] = None
    message: str = ""
    confidence: float = 0.0
    source_verified: Optional[SourceJurisprudence] = None
    verification_date: datetime = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.verification_date is None:
            self.verification_date = datetime.now()
        if self.details is None:
            self.details = {}

@dataclass
class JurisprudenceSearchCriteria:
    """Critères de recherche de jurisprudence"""
    keywords: List[str] = None
    juridictions: List[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    articles: List[str] = None
    importance_min: int = 1
    sources: List[SourceJurisprudence] = None
    max_results: int = 50
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.juridictions is None:
            self.juridictions = []
        if self.articles is None:
            self.articles = []
        if self.sources is None:
            self.sources = []

@dataclass
class JurisprudenceAnalysis:
    """Analyse d'une jurisprudence"""
    reference_id: str
    principes_degages: List[str]
    impact_juridique: str
    evolution_jurisprudentielle: str
    cas_similaires: List[str] = None
    recommandations: List[str] = None
    date_analyse: datetime = None
    
    def __post_init__(self):
        if self.cas_similaires is None:
            self.cas_similaires = []
        if self.recommandations is None:
            self.recommandations = []
        if self.date_analyse is None:
            self.date_analyse = datetime.now()