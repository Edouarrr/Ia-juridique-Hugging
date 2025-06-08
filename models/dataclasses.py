"""Classes de données principales"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Document:
    """Document juridique"""
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