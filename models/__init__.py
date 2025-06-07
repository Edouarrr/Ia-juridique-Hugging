# models/dataclasses.py
"""Modèles de données pour l'application"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

class TypePersonne(Enum):
    """Types de personnes impliquées"""
    PHYSIQUE = "Personne physique"
    MORALE = "Personne morale"
    DIRIGEANT = "Dirigeant"
    SALARIE = "Salarié"
    ASSOCIE = "Associé"
    TIERS = "Tiers"

class TypeSanction(Enum):
    """Types de sanctions"""
    AMENDE = "Amende"
    EMPRISONNEMENT = "Emprisonnement"
    INTERDICTION = "Interdiction"
    CONFISCATION = "Confiscation"
    PUBLICATION = "Publication"

@dataclass
class Personne:
    """Représente une personne impliquée dans l'affaire"""
    nom: str
    type_personne: TypePersonne
    role: str
    fonction: Optional[str] = None
    entreprise: Optional[str] = None
    details: Optional[str] = None

@dataclass
class Infraction:
    """Représente une infraction pénale"""
    nom: str
    qualification: str
    articles: List[str]
    elements_constitutifs: List[str]
    sanctions: Dict[str, Any]
    prescription: str
    jurisprudences: List[str] = field(default_factory=list)
    
@dataclass
class AnalyseJuridique:
    """Résultat d'une analyse juridique"""
    id: str
    date_analyse: datetime
    description_cas: str
    infractions_identifiees: List[Infraction]
    personnes_impliquees: List[Personne]
    elements_factuels: List[str]
    qualification_juridique: str
    regime_responsabilite: str
    sanctions_encourues: Dict[str, Any]
    jurisprudences_citees: List[str]
    recommandations: List[str]
    niveau_risque: str
    model_used: str
    
@dataclass
class DocumentJuridique:
    """Représente un document juridique"""
    id: str
    titre: str
    type_document: str  # "jurisprudence", "doctrine", "legislation"
    date: datetime
    contenu: str
    source: str
    url: Optional[str] = None
    mots_cles: List[str] = field(default_factory=list)
    pertinence: float = 0.0
    
@dataclass
class RechercheJuridique:
    """Résultat d'une recherche juridique"""
    id: str
    date_recherche: datetime
    requete: str
    type_recherche: str
    sources_consultees: List[str]
    resultats: List[DocumentJuridique]
    nombre_resultats: int
    temps_recherche: float
    
@dataclass
class CasJuridique:
    """Représente un cas juridique complet"""
    id: str
    titre: str
    date_creation: datetime
    description: str
    type_affaire: str
    infractions: List[str]
    personnes: List[Personne]
    chronologie: List[Dict[str, Any]]
    pieces_jointes: List[str]
    analyses: List[AnalyseJuridique]
    statut: str = "En cours"
    notes: str = ""
    
@dataclass
class Sanction:
    """Détail d'une sanction"""
    type_sanction: TypeSanction
    montant_min: Optional[float] = None
    montant_max: Optional[float] = None
    duree_min: Optional[int] = None  # en mois
    duree_max: Optional[int] = None  # en mois
    conditions: List[str] = field(default_factory=list)
    aggravations: List[str] = field(default_factory=list)
    
@dataclass
class ElementConstitutif:
    """Élément constitutif d'une infraction"""
    categorie: str  # "matériel" ou "intentionnel"
    description: str
    preuves_necessaires: List[str]
    present: bool = False
    justification: str = ""
    
@dataclass
class Prescription:
    """Information sur la prescription"""
    delai: int  # en années
    point_depart: str
    interruptions: List[str]
    suspensions: List[str]
    date_faits: Optional[datetime] = None
    prescrit: bool = False
    
@dataclass
class AnalyseRisque:
    """Analyse de risque pénal"""
    niveau_global: str  # "Faible", "Modéré", "Élevé", "Critique"
    facteurs_risque: List[str]
    facteurs_attenuants: List[str]
    probabilite_poursuite: float  # 0 à 1
    impact_potentiel: str
    recommandations_prioritaires: List[str]