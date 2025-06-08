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

@dataclass
class StylePattern:
    """Modèle de style d'écriture"""
    id: str
    nom: str
    description: str
    caracteristiques: Dict[str, Any] = None
    exemples: List[str] = None
    mots_cles: List[str] = None
    ton: str = "neutre"
    formalite: str = "standard"
    complexite: int = 5  # 1-10
    
    def __post_init__(self):
        if self.caracteristiques is None:
            self.caracteristiques = {}
        if self.exemples is None:
            self.exemples = []
        if self.mots_cles is None:
            self.mots_cles = []

@dataclass
class SearchPattern:
    """Modèle de recherche"""
    pattern: str
    type: str
    priority: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AnalysisResult:
    """Résultat d'analyse"""
    type: str
    content: str
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ExportConfig:
    """Configuration d'export"""
    format: str
    include_metadata: bool = True
    include_styles: bool = True
    include_annotations: bool = False
    custom_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_options is None:
            self.custom_options = {}

@dataclass
class SearchResult:
    """Résultat de recherche"""
    id: str
    title: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any] = None
    highlights: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.highlights is None:
            self.highlights = []

@dataclass
class UserPreferences:
    """Préférences utilisateur"""
    language: str = "fr"
    theme: str = "light"
    default_search_mode: str = "semantic"
    results_per_page: int = 20
    auto_save: bool = True
    export_format: str = "docx"
    ai_providers: List[str] = None
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.ai_providers is None:
            self.ai_providers = []
        if self.custom_settings is None:
            self.custom_settings = {}

@dataclass
class TaskResult:
    """Résultat d'une tâche"""
    task_id: str
    task_type: str
    status: str
    result: Any = None
    error: Optional[str] = None
    started_at: datetime = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}