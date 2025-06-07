# models/jurisprudence_models.py
"""Modèles spécifiques pour la gestion des jurisprudences"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class SourceJurisprudence(Enum):
    """Sources de jurisprudence"""
    JUDILIBRE = "judilibre"
    LEGIFRANCE = "legifrance"
    AI_PROPOSED = "ai_proposed"
    MANUAL = "manual"
    DOCTRINE = "doctrine"

class TypeJuridiction(Enum):
    """Types de juridictions"""
    CASS_CRIM = "Cass. crim."
    CASS_CIV = "Cass. civ."
    CASS_COM = "Cass. com."
    CASS_SOC = "Cass. soc."
    CE = "CE"
    CC = "Cons. const."
    CA = "CA"
    TC = "TC"
    CJUE = "CJUE"
    CEDH = "CEDH"

@dataclass
class JurisprudenceReference:
    """Référence complète d'une jurisprudence"""
    juridiction: str
    date: str  # Format: "12 janvier 2023"
    numero: str  # Ex: "22-81.234"
    sommaire: Optional[str] = None
    texte_integral: Optional[str] = None
    url_source: Optional[str] = None
    verified: bool = False
    found_on: List[str] = field(default_factory=list)
    ai_proposed: bool = True
    verification_date: Optional[datetime] = None
    mots_cles: List[str] = field(default_factory=list)
    principe: Optional[str] = None
    solution: Optional[str] = None
    portee: Optional[str] = None
    
    def to_citation(self) -> str:
        """Format standard de citation"""
        return f"{self.juridiction}, {self.date}, n° {self.numero}"
    
    def to_search_query(self) -> str:
        """Requête optimisée pour recherche"""
        clean_numero = self.numero.replace("n°", "").strip()
        return f"{self.juridiction} {clean_numero}"

@dataclass
class JurisprudenceDetail:
    """Détails complets d'une décision"""
    reference: JurisprudenceReference
    formation: Optional[str] = None  # "Chambre criminelle", "Assemblée plénière"
    president: Optional[str] = None
    rapporteur: Optional[str] = None
    avocat_general: Optional[str] = None
    avocats: List[str] = field(default_factory=list)
    parties: Dict[str, str] = field(default_factory=dict)  # {"demandeur": "X", "défendeur": "Y"}
    faits: Optional[str] = None
    procedure: Optional[str] = None
    moyens: List[str] = field(default_factory=list)
    motivation: Optional[str] = None
    dispositif: Optional[str] = None
    doctrine_references: List[str] = field(default_factory=list)
    decisions_citees: List[str] = field(default_factory=list)
    legislation_appliquee: List[str] = field(default_factory=list)

@dataclass
class VerificationResult:
    """Résultat de vérification d'une jurisprudence"""
    reference: JurisprudenceReference
    status: str  # "verified", "not_found", "partial", "error"
    confidence: float  # 0.0 à 1.0
    sources_checked: List[SourceJurisprudence]
    matches: List[Dict[str, any]]
    discrepancies: List[str] = field(default_factory=list)
    suggestions: List[JurisprudenceReference] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
@dataclass
class JurisprudenceSearch:
    """Paramètres de recherche de jurisprudence"""
    keywords: List[str]
    juridictions: List[TypeJuridiction] = field(default_factory=list)
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    infractions: List[str] = field(default_factory=list)
    articles: List[str] = field(default_factory=list)
    sources: List[SourceJurisprudence] = field(default_factory=lambda: [SourceJurisprudence.JUDILIBRE, SourceJurisprudence.LEGIFRANCE])
    max_results: int = 50
    sort_by: str = "pertinence"  # "pertinence", "date", "juridiction"
    
@dataclass
class JurisprudenceAnalysis:
    """Analyse d'une jurisprudence"""
    reference: JurisprudenceReference
    importance: str  # "principe", "confirmation", "evolution", "revirement"
    domaines: List[str]  # ["abus de biens sociaux", "élément intentionnel"]
    concepts_cles: List[str]
    evolution_jurisprudentielle: Optional[str] = None
    impact: Optional[str] = None
    critiques_doctrine: List[str] = field(default_factory=list)
    decisions_posterieures: List[str] = field(default_factory=list)
    
@dataclass 
class JurisprudenceCollection:
    """Collection de jurisprudences sur un thème"""
    titre: str
    description: str
    theme: str
    infractions: List[str]
    jurisprudences: List[JurisprudenceReference]
    synthese: Optional[str] = None
    derniere_mise_a_jour: datetime = field(default_factory=datetime.now)
    auteur: Optional[str] = None
    tags: List[str] = field(default_factory=list)