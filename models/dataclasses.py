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