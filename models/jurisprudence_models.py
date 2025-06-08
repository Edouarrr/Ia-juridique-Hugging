"""Modèles de données pour la jurisprudence"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class SourceJurisprudence(Enum):
    """Sources de jurisprudence disponibles"""
    LEGIFRANCE = "legifrance"
    DOCTRINE = "doctrine"
    DALLOZ = "dalloz"
    LEXIS = "lexis"
    INTERNAL = "internal"
    MANUAL = "manual"

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
    
    def __post_init__(self):
        if self.mots_cles is None:
            self.mots_cles = []

@dataclass
class VerificationResult:
    """Résultat de vérification d'une jurisprudence"""
    is_valid: bool
    reference: Optional[JurisprudenceReference] = None
    message: str = ""
    confidence: float = 0.0
    source_verified: Optional[SourceJurisprudence] = None
    verification_date: datetime = None
    
    def __post_init__(self):
        if self.verification_date is None:
            self.verification_date = datetime.now()