# models/dataclasses.py
"""Classes de données pour l'application"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

@dataclass
class Document:
    """Représente un document juridique"""
    id: str
    title: str
    content: str
    source: str = 'local'
    page_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    folder_path: Optional[str] = None
    selected: bool = False
    embedding: Optional[List[float]] = None

@dataclass
class PieceSelectionnee:
    """Pièce sélectionnée pour un dossier"""
    document_id: str
    titre: str
    categorie: str
    date_selection: datetime = field(default_factory=datetime.now)
    notes: str = ""
    pertinence: int = 5

@dataclass
class StylePattern:
    """Modèle de style extrait d'un document"""
    document_id: str
    type_acte: str
    structure: Dict[str, Any]
    formules: List[str]
    mise_en_forme: Dict[str, Any]
    vocabulaire: Dict[str, int]
    paragraphes_types: List[str]

@dataclass
class LetterheadTemplate:
    """Template de papier en-tête"""
    name: str
    header_content: str
    footer_content: str
    logo_path: Optional[str] = None
    margins: Dict[str, float] = field(default_factory=lambda: {
        'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5
    })
    font_family: str = "Arial"
    font_size: int = 11
    line_spacing: float = 1.5
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InfractionIdentifiee:
    """Représente une infraction identifiée dans l'analyse"""
    nom: str
    qualification: str
    articles: List[str]
    elements_constitutifs: List[str]
    sanctions: Dict[str, str]
    prescription: str
    niveau_gravite: str = "Moyen"

@dataclass
class CasJuridique:
    """Représente un cas juridique à analyser"""
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    titre: str = ""
    description: str = ""
    date_faits: Optional[datetime] = None
    parties: Dict[str, str] = field(default_factory=dict)
    contexte: str = ""
    pieces_jointes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class DocumentJuridique:
    """Document juridique enrichi"""
    id: str
    titre: str
    type_document: str
    contenu: str
    date_document: datetime
    parties: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalyseJuridique:
    """Résultat complet d'une analyse juridique"""
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    description_cas: str = ""
    qualification_juridique: str = ""
    infractions_identifiees: List[InfractionIdentifiee] = field(default_factory=list)
    regime_responsabilite: str = ""
    sanctions_encourues: Dict[str, str] = field(default_factory=dict)
    jurisprudences_citees: List[str] = field(default_factory=list)
    recommandations: List[str] = field(default_factory=list)
    niveau_risque: str = "Moyen"
    date_analyse: datetime = field(default_factory=datetime.now)
    model_used: str = ""
    confidence_score: float = 0.0