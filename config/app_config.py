# models/dataclasses.py
"""Modèles de données enrichis avec toutes les fonctionnalités"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class TypePersonne(Enum):
    """Types de personnes"""
    PHYSIQUE = "Personne physique"
    MORALE = "Personne morale"
    AVOCAT = "Avocat"
    MAGISTRAT = "Magistrat"
    EXPERT = "Expert"
    TEMOIN = "Témoin"
    AUTRE = "Autre"


class TypeSanction(Enum):
    """Types de sanctions"""
    AMENDE = "Amende"
    EMPRISONNEMENT = "Emprisonnement"
    INTERDICTION = "Interdiction"
    CONFISCATION = "Confiscation"
    PUBLICATION = "Publication"
    AUTRE = "Autre"


@dataclass
class Personne:
    """Représente une personne (physique ou morale)"""
    nom: str
    type: TypePersonne
    role: str = ""
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Infraction:
    """Représente une infraction pénale"""
    type: str
    description: str
    articles: List[str] = field(default_factory=list)
    date_faits: Optional[datetime] = None
    lieu: str = ""
    elements_constitutifs: Dict[str, str] = field(default_factory=dict)
    sanctions_encourues: List['Sanction'] = field(default_factory=list)


@dataclass
class Document:
    """Représente un document juridique enrichi"""
    id: str
    title: str
    content: str
    source: str = 'local'
    page_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    folder_path: Optional[str] = None
    selected: bool = False
    embedding: Optional[List[float]] = None  # Vecteur pour la recherche
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le document en dictionnaire"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'page_number': self.page_number,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'folder_path': self.folder_path,
            'selected': self.selected,
            'embedding': self.embedding
        }


@dataclass
class StylePattern:
    """Modèle de style extrait d'un document"""
    document_id: str
    type_acte: str
    structure: Dict[str, Any]  # Structure du document
    formules: List[str]  # Formules types extraites
    mise_en_forme: Dict[str, Any]  # Paramètres de mise en forme
    vocabulaire: Dict[str, int]  # Fréquence des mots
    paragraphes_types: List[str]  # Exemples de paragraphes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le pattern en dictionnaire"""
        return {
            'document_id': self.document_id,
            'type_acte': self.type_acte,
            'structure': self.structure,
            'formules': self.formules,
            'mise_en_forme': self.mise_en_forme,
            'vocabulaire': self.vocabulaire,
            'paragraphes_types': self.paragraphes_types
        }


@dataclass
class LetterheadTemplate:
    """Template de papier en-tête"""
    name: str
    header_content: str  # Contenu HTML/Markdown de l'en-tête
    footer_content: str  # Contenu HTML/Markdown du pied de page
    logo_path: Optional[str] = None
    margins: Dict[str, float] = field(default_factory=lambda: {
        'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5
    })
    font_family: str = "Arial"
    font_size: int = 11
    line_spacing: float = 1.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PieceSelectionnee:
    """Pièce sélectionnée pour un dossier enrichie"""
    document_id: str
    titre: str
    categorie: str
    date_selection: datetime = field(default_factory=datetime.now)
    notes: str = ""
    pertinence: int = 5  # Score de 1 à 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la pièce en dictionnaire"""
        return {
            'document_id': self.document_id,
            'titre': self.titre,
            'categorie': self.categorie,
            'date_selection': self.date_selection.isoformat() if self.date_selection else None,
            'notes': self.notes,
            'pertinence': self.pertinence
        }


@dataclass
class AnalyseJuridique:
    """Résultat d'une analyse juridique"""
    id: str
    date: datetime
    type_analyse: str
    infraction: Infraction
    client: Personne
    documents_analyses: List[str]  # IDs des documents
    resultats: Dict[str, Any]
    recommandations: List[str]
    risques: List['AnalyseRisque']
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentJuridique:
    """Document juridique généré"""
    type: str  # Plainte, conclusions, etc.
    titre: str
    contenu: str
    destinataire: Optional[Personne] = None
    expediteur: Optional[Personne] = None
    date_creation: datetime = field(default_factory=datetime.now)
    pieces_jointes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RechercheJuridique:
    """Résultat d'une recherche juridique"""
    query: str
    date: datetime
    sources: List[str]
    resultats: List[Dict[str, Any]]
    nombre_resultats: int
    filtres_appliques: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CasJuridique:
    """Cas juridique complet"""
    id: str
    nom: str
    client: Personne
    infractions: List[Infraction]
    parties: List[Personne]
    documents: List[str]  # IDs des documents
    analyses: List[str]  # IDs des analyses
    statut: str = "En cours"
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: datetime = field(default_factory=datetime.now)
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Sanction:
    """Sanction pénale"""
    type: TypeSanction
    montant_min: Optional[float] = None
    montant_max: Optional[float] = None
    duree_min: Optional[int] = None  # En mois
    duree_max: Optional[int] = None  # En mois
    description: str = ""
    articles: List[str] = field(default_factory=list)


@dataclass
class ElementConstitutif:
    """Élément constitutif d'une infraction"""
    type: str  # matériel, intentionnel, légal
    description: str
    preuves_necessaires: List[str] = field(default_factory=list)
    jurisprudences: List[str] = field(default_factory=list)


@dataclass
class Prescription:
    """Délais de prescription"""
    type_infraction: str
    delai_annees: int
    point_depart: str
    interruptions: List[str] = field(default_factory=list)
    suspensions: List[str] = field(default_factory=list)


@dataclass
class AnalyseRisque:
    """Analyse de risque juridique"""
    type: str
    niveau: str  # Faible, Moyen, Élevé, Critique
    description: str
    probabilite: float  # 0-1
    impact: str
    mesures_preventives: List[str] = field(default_factory=list)
    mesures_correctives: List[str] = field(default_factory=list)


# Types pour la recherche Azure
@dataclass
class SearchResult:
    """Résultat de recherche Azure"""
    id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)