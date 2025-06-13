from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

# Énumérations
class DocumentType(Enum):
    """Types de documents juridiques"""
    CONCLUSIONS = "conclusions"
    PLAINTE = "plainte"
    ASSIGNATION = "assignation"
    MEMOIRE = "memoire"
    ORDONNANCE = "ordonnance"
    JUGEMENT = "jugement"
    ARRET = "arret"
    REQUETE = "requete"
    COURRIER = "courrier"
    CONSTITUTION_PC = "constitution_partie_civile"
    BORDEREAU = "bordereau"
    PIECE = "piece"
    OTHER = "autre"

class PartyType(Enum):
    """Types de parties"""
    DEMANDEUR = "demandeur"
    DEFENDEUR = "defendeur"
    PARTIE_CIVILE = "partie_civile"
    PREVENU = "prevenu"
    MIS_EN_EXAMEN = "mis_en_examen"
    TEMOIN = "temoin"
    EXPERT = "expert"
    AVOCAT = "avocat"
    MAGISTRAT = "magistrat"

class TimelineType(Enum):
    """Types de chronologies"""
    FAITS = "faits"
    PROCEDURE = "procedure"
    COMPLETE = "complete"

class MappingType(Enum):
    """Types de cartographies"""
    SOCIETES = "societes"
    PERSONNES = "personnes"
    FLUX_FINANCIERS = "flux_financiers"
    COMPLETE = "complete"

class ExportFormat(Enum):
    """Formats d'export"""
    DOCX = "docx"
    PDF = "pdf"
    XLSX = "xlsx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"

# Classes de données
@dataclass
class Document:
    """Représente un document dans le système"""
    id: str
    title: str
    content: str
    source: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)

@dataclass
class SearchResult:
    """Résultat de recherche"""
    id: str
    title: str
    content: str
    score: float
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    document_type: str = ""

@dataclass
class Piece:
    """Représente une pièce juridique"""
    numero: str
    titre: str
    description: str = ""
    source: str = ""
    date: Optional[datetime] = None
    type_piece: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.date, str) and self.date:
            try:
                self.date = datetime.fromisoformat(self.date)
            except:
                self.date = None

@dataclass
class QueryAnalysis:
    """Analyse d'une requête utilisateur"""
    original_query: str
    intent: str
    entities: Dict[str, Any]
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TimelineEvent:
    """Événement dans une chronologie"""
    date: datetime
    title: str
    description: str
    category: str = ""
    actors: List[str] = field(default_factory=list)
    location: str = ""
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = datetime.fromisoformat(self.date)

@dataclass
class LegalEntity:
    """Entité juridique (personne ou organisation)"""
    id: str
    name: str
    type: str  # personne, societe, organisation
    role: str = ""
    description: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class EmailConfig:
    """Configuration pour l'envoi d'emails"""
    sender: str
    recipients: List[str]
    subject: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    reply_to: Optional[str] = None

@dataclass
class EmailCredentials:
    """Identifiants pour l'envoi d'emails"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True

@dataclass
class PlaidoirieResult:
    """Résultat de génération de plaidoirie"""
    title: str
    content: str
    structure: Dict[str, Any]
    duration_estimated: int  # en minutes
    key_points: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JurisprudenceCase:
    """Cas de jurisprudence"""
    id: str
    title: str
    court: str
    date: datetime
    summary: str
    full_text: str = ""
    references: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = datetime.fromisoformat(self.date)

@dataclass
class Template:
    """Modèle de document"""
    id: str
    name: str
    description: str
    content: str
    category: str
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)

@dataclass
class GenerationParams:
    """Paramètres pour la génération de documents"""
    style: str = "formel"
    length: str = "normal"
    tone: str = "professionnel"
    include_citations: bool = True
    include_jurisprudence: bool = True
    language: str = "fr"
    additional_instructions: str = ""

@dataclass
class AnalysisResult:
    """Résultat d'analyse de document"""
    document_id: str
    analysis_type: str
    results: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

@dataclass
class ComparisonResult:
    """Résultat de comparaison de documents"""
    doc1_id: str
    doc2_id: str
    similarity_score: float
    differences: List[Dict[str, Any]]
    common_elements: List[Dict[str, Any]]
    analysis: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RiskAssessment:
    """Évaluation des risques juridiques"""
    risk_level: str  # low, medium, high, critical
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    legal_basis: List[str]
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BordereauItem:
    """Élément d'un bordereau de communication"""
    numero: str
    designation: str
    nature: str = ""
    pages: str = ""
    observations: str = ""

@dataclass
class ExportConfig:
    """Configuration pour l'export de documents"""
    format: ExportFormat
    include_metadata: bool = True
    include_annotations: bool = False
    merge_documents: bool = False
    template: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserPreferences:
    """Préférences utilisateur"""
    results_per_page: int = 20
    default_view: str = "Compact"
    auto_jurisprudence: bool = True
    create_hyperlinks: bool = True
    default_doc_length: str = "Très détaillé"
    email_signature: str = ""
    default_export_format: ExportFormat = ExportFormat.DOCX

@dataclass
class ProcessingStatus:
    """Statut de traitement d'une opération"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    message: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.started_at, str):
            self.started_at = datetime.fromisoformat(self.started_at)
        if isinstance(self.completed_at, str) and self.completed_at:
            self.completed_at = datetime.fromisoformat(self.completed_at)