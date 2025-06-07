# models/jurisprudence_models.py
"""Modèles de données pour la gestion des jurisprudences"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class SourceJurisprudence(Enum):
    """Sources de jurisprudence disponibles"""
    JUDILIBRE = "judilibre"
    LEGIFRANCE = "legifrance"
    INTERNE = "interne"
    MANUEL = "manuel"

class TypeJuridiction(Enum):
    """Types de juridictions"""
    CASS_CRIM = "Cass. crim."
    CASS_CIV = "Cass. civ."
    CASS_COM = "Cass. com."
    CASS_SOC = "Cass. soc."
    CE = "CE"
    CA = "CA"
    CONS_CONST = "Cons. const."
    CJUE = "CJUE"
    CEDH = "CEDH"

@dataclass
class JurisprudenceReference:
    """Représente une référence de jurisprudence"""
    juridiction: str
    date: str
    numero: str
    
    # Métadonnées optionnelles
    formation: Optional[str] = None
    sommaire: Optional[str] = None
    texte_integral: Optional[str] = None
    mots_cles: List[str] = field(default_factory=list)
    
    # Informations de vérification
    verified: bool = False
    verification_date: Optional[datetime] = None
    found_on: List[str] = field(default_factory=list)
    url_source: Optional[str] = None
    confidence_score: float = 0.0
    
    # Source et provenance
    source_type: SourceJurisprudence = SourceJurisprudence.MANUEL
    ai_proposed: bool = False
    
    def to_citation(self) -> str:
        """Retourne la citation formatée"""
        return f"{self.juridiction}, {self.date}, n° {self.numero}"
    
    def to_search_query(self) -> str:
        """Retourne une requête de recherche optimisée"""
        # Nettoyer le numéro
        numero_clean = self.numero.replace('-', ' ').replace('.', ' ')
        return f"{self.juridiction} {numero_clean}"
    
    def __hash__(self):
        return hash((self.juridiction, self.date, self.numero))

@dataclass
class VerificationResult:
    """Résultat de la vérification d'une jurisprudence"""
    reference: JurisprudenceReference
    status: str  # 'verified', 'not_found', 'error'
    confidence: float
    sources_checked: List[SourceJurisprudence]
    matches: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    verification_timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class JurisprudenceSearch:
    """Paramètres de recherche de jurisprudence"""
    keywords: List[str] = field(default_factory=list)
    infractions: List[str] = field(default_factory=list)
    articles: List[str] = field(default_factory=list)
    juridictions: List[TypeJuridiction] = field(default_factory=list)
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    sources: List[SourceJurisprudence] = field(default_factory=lambda: [
        SourceJurisprudence.JUDILIBRE,
        SourceJurisprudence.LEGIFRANCE
    ])
    max_results: int = 30
    sort_by: str = "pertinence"
    include_sommaire: bool = True
    include_texte_integral: bool = False

@dataclass
class DocumentJuridique:
    """Document juridique enrichi"""
    id: str
    titre: str
    type_document: str  # jurisprudence, article, doctrine, etc.
    contenu: str
    date_document: datetime
    
    # Métadonnées
    source: Optional[str] = None
    url: Optional[str] = None
    mots_cles: List[str] = field(default_factory=list)
    pertinence: float = 1.0
    
    # Référence jurisprudentielle si applicable
    reference: Optional[JurisprudenceReference] = None
    
    # Parties et références
    parties: Dict[str, str] = field(default_factory=dict)
    references_citees: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)