# models/dataclasses.py
"""Modèles de données pour l'application juridique"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

@dataclass
class Document:
    """Représente un document juridique"""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    author: Optional[str] = None
    reference: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    
    def __post_init__(self):
        """Validation post-initialisation"""
        if not self.id:
            self.id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        if not self.metadata:
            self.metadata = {}
        
        # Ajouter des métadonnées par défaut
        self.metadata.update({
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'word_count': len(self.content.split()),
            'char_count': len(self.content)
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'category': self.category,
            'author': self.author,
            'reference': self.reference,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Crée un objet depuis un dictionnaire"""
        # Convertir les dates si nécessaire
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)

@dataclass
class PieceSelectionnee:
    """Représente une pièce sélectionnée pour un bordereau"""
    numero: int
    titre: str
    description: str = ""
    categorie: str = "Autre"
    date: Optional[datetime] = None
    source: str = ""
    pertinence: float = 0.5
    pages: Optional[int] = None
    format: Optional[str] = None
    taille: Optional[int] = None
    cote: Optional[str] = None  # Numéro de cote pour le bordereau
    
    def __post_init__(self):
        """Validation et formatage"""
        if self.pertinence < 0:
            self.pertinence = 0
        elif self.pertinence > 1:
            self.pertinence = 1
        
        # Générer une cote si non fournie
        if not self.cote:
            self.cote = f"P-{self.numero:03d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'numero': self.numero,
            'titre': self.titre,
            'description': self.description,
            'categorie': self.categorie,
            'date': self.date.isoformat() if self.date else None,
            'source': self.source,
            'pertinence': self.pertinence,
            'pages': self.pages,
            'format': self.format,
            'taille': self.taille,
            'cote': self.cote
        }

@dataclass
class SearchResult:
    """Résultat de recherche"""
    id: str
    title: str
    content: str
    score: float
    source: str
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_type: Optional[str] = None
    relevance_explanation: Optional[str] = None
    
    def __post_init__(self):
        """Normalise le score"""
        if self.score < 0:
            self.score = 0
        elif self.score > 1:
            self.score = 1

@dataclass
class AnalysisResult:
    """Résultat d'analyse IA"""
    type: str  # risk_analysis, compliance, strategy, general
    content: str
    query: str
    document_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    provider: Optional[str] = None
    confidence: float = 0.8
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'type': self.type,
            'content': self.content,
            'query': self.query,
            'document_count': self.document_count,
            'timestamp': self.timestamp.isoformat(),
            'provider': self.provider,
            'confidence': self.confidence,
            'key_findings': self.key_findings,
            'recommendations': self.recommendations,
            'sources': self.sources
        }

@dataclass
class TimelineEvent:
    """Événement dans une chronologie"""
    date: Union[datetime, str]
    description: str
    actors: List[str] = field(default_factory=list)
    location: Optional[str] = None
    category: Optional[str] = None
    importance: int = 5  # 1-10
    source: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validation"""
        if self.importance < 1:
            self.importance = 1
        elif self.importance > 10:
            self.importance = 10

@dataclass
class Entity:
    """Entité (personne, organisation, etc.)"""
    name: str
    type: str  # person, company, organization, location, other
    aliases: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    mentions_count: int = 0
    first_mention: Optional[str] = None
    relationships: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class Relationship:
    """Relation entre entités"""
    source: str
    target: str
    type: str  # contractual, hierarchical, familial, conflictual, other
    strength: float = 0.5  # 0-1
    direction: str = "bidirectional"  # unidirectional, bidirectional
    evidence: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

@dataclass
class JurisprudenceCase:
    """Décision de jurisprudence"""
    id: str
    title: str
    jurisdiction: str
    date: datetime
    reference: str
    summary: str
    full_text: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    legal_basis: List[str] = field(default_factory=list)
    url: Optional[str] = None
    relevance_score: float = 0.0
    
    def get_citation(self) -> str:
        """Retourne la citation formatée"""
        return f"{self.jurisdiction}, {self.date.strftime('%d %B %Y')}, {self.reference}"

@dataclass
class RedactionResult:
    """Résultat de rédaction de document"""
    type: str  # conclusions, plainte, etc.
    document: str
    provider: str
    timestamp: datetime = field(default_factory=datetime.now)
    style: str = "formel"
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    jurisprudence_used: bool = False
    jurisprudence_references: List[JurisprudenceCase] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)  # Réponses des différentes IA
    
    def __post_init__(self):
        """Calcule le nombre de mots"""
        if self.document and not self.word_count:
            self.word_count = len(self.document.split())

@dataclass
class EmailConfig:
    """Configuration d'envoi d'email"""
    to: List[str]
    subject: str
    body: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    reply_to: Optional[str] = None
    priority: str = "normal"  # low, normal, high
    
    def add_attachment(self, filename: str, data: bytes, mime_type: str = "application/octet-stream"):
        """Ajoute une pièce jointe"""
        self.attachments.append({
            'filename': filename,
            'data': data,
            'mime_type': mime_type
        })

@dataclass
class PlaidoirieResult:
    """Résultat de génération de plaidoirie"""
    content: str
    type: str  # correctionnelle, assises, civile, etc.
    style: str
    duration_estimate: str
    key_points: List[str] = field(default_factory=list)
    structure: Dict[str, List[str]] = field(default_factory=dict)
    oral_markers: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_speaking_time(self) -> int:
        """Estime le temps de parole en minutes"""
        # Environ 150 mots par minute en plaidoirie
        words = len(self.content.split())
        return int(words / 150)

@dataclass
class PreparationClientResult:
    """Résultat de préparation client"""
    content: str
    prep_type: str  # audition, interrogatoire, comparution
    profile: str  # anxieux, confiant, technique, etc.
    strategy: str
    key_qa: List[Dict[str, str]] = field(default_factory=list)
    do_not_say: List[str] = field(default_factory=list)
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    duration_estimate: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_top_questions(self, n: int = 10) -> List[Dict[str, str]]:
        """Retourne les N questions les plus importantes"""
        return self.key_qa[:n]

@dataclass
class Template:
    """Template de document"""
    id: str
    name: str
    type: str
    structure: List[str]
    style: str = "formel"
    category: str = "Autre"
    description: str = ""
    variables: List[str] = field(default_factory=list)
    is_builtin: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    
    def extract_variables(self):
        """Extrait les variables du template"""
        import re
        variables = set()
        for line in self.structure:
            # Chercher les patterns [Variable]
            matches = re.findall(r'\[([^\]]+)\]', line)
            variables.update(matches)
        self.variables = list(variables)

@dataclass
class QueryAnalysis:
    """Analyse d'une requête utilisateur"""
    original_query: str
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def has_reference(self) -> bool:
        """Vérifie si la requête contient une référence @"""
        return '@' in self.original_query
    
    def get_reference(self) -> Optional[str]:
        """Extrait la référence de la requête"""
        import re
        match = re.search(r'@(\w+)', self.original_query)
        return match.group(1) if match else None

@dataclass
class Session:
    """Session utilisateur"""
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    documents: Dict[str, Document] = field(default_factory=dict)
    search_history: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Vérifie si la session a expiré"""
        return (datetime.now() - self.last_activity).seconds > timeout_minutes * 60
    
    def update_activity(self):
        """Met à jour l'heure de dernière activité"""
        self.last_activity = datetime.now()

# Types personnalisés pour les annotations
DocumentDict = Dict[str, Document]
SearchResults = List[SearchResult]
TimelineEvents = List[TimelineEvent]
EntityList = List[Entity]
RelationshipList = List[Relationship]