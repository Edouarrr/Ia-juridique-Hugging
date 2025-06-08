# models/dataclasses.py
"""Modèles de données pour l'application juridique - Version complète"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum

# ========== ENUMS ==========

class SourceJurisprudence(Enum):
    """Sources de jurisprudence disponibles"""
    LEGIFRANCE = "legifrance"
    DOCTRINE = "doctrine"
    DALLOZ = "dalloz"
    LEXIS = "lexis"
    INTERNAL = "internal"
    MANUAL = "manual"
    COURDECASSATION = "courdecassation"
    CONSEILDETAT = "conseildetat"
    CONSEILCONSTITUTIONNEL = "conseilconstitutionnel"

class TypeDocument(Enum):
    """Types de documents juridiques"""
    DECISION = "decision"
    ARRET = "arret"
    ORDONNANCE = "ordonnance"
    JUGEMENT = "jugement"
    AVIS = "avis"
    RAPPORT = "rapport"
    CONCLUSIONS = "conclusions"
    NOTE = "note"
    COMMENTAIRE = "commentaire"

class TypeJuridiction(Enum):
    """Types de juridictions"""
    COUR_DE_CASSATION = "Cour de cassation"
    CONSEIL_ETAT = "Conseil d'État"
    CONSEIL_CONSTITUTIONNEL = "Conseil constitutionnel"
    COUR_APPEL = "Cour d'appel"
    TRIBUNAL_JUDICIAIRE = "Tribunal judiciaire"
    TRIBUNAL_COMMERCE = "Tribunal de commerce"
    TRIBUNAL_ADMINISTRATIF = "Tribunal administratif"
    COUR_ADMINISTRATIVE_APPEL = "Cour administrative d'appel"
    TRIBUNAL_CORRECTIONNEL = "Tribunal correctionnel"
    COUR_ASSISES = "Cour d'assises"
    CONSEIL_PRUDHOMMES = "Conseil de prud'hommes"
    TRIBUNAL_POLICE = "Tribunal de police"
    JURIDICTION_PROXIMITE = "Juridiction de proximité"
    AUTRE = "Autre"

# ========== DATACLASSES DE BASE ==========

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

# ========== JURISPRUDENCE ==========

@dataclass
class JurisprudenceReference:
    """Référence de jurisprudence complète"""
    numero: str
    date: datetime
    juridiction: str
    type_juridiction: Optional[TypeJuridiction] = None
    formation: Optional[str] = None
    titre: Optional[str] = None
    resume: Optional[str] = None
    texte_integral: Optional[str] = None
    url: Optional[str] = None
    source: SourceJurisprudence = SourceJurisprudence.MANUAL
    mots_cles: List[str] = field(default_factory=list)
    articles_vises: List[str] = field(default_factory=list)
    decisions_citees: List[str] = field(default_factory=list)
    importance: int = 5
    solution: Optional[str] = None
    portee: Optional[str] = None
    commentaires: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.commentaires is None:
            self.commentaires = []
    
    def get_citation(self) -> str:
        """Retourne la citation formatée"""
        return f"{self.juridiction}, {self.date.strftime('%d %B %Y')}, {self.numero}"

@dataclass
class VerificationResult:
    """Résultat de vérification d'une jurisprudence"""
    is_valid: bool
    reference: Optional[JurisprudenceReference] = None
    message: str = ""
    confidence: float = 0.0
    source_verified: Optional[SourceJurisprudence] = None
    verification_date: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[JurisprudenceReference] = field(default_factory=list)

# ========== RECHERCHE ET ANALYSE ==========

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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'original_query': self.original_query,
            'intent': self.intent,
            'entities': self.entities,
            'confidence': self.confidence,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'reference': self.get_reference()
        }

# ========== TIMELINE ET MAPPING ==========

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

# ========== RÉDACTION ==========

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
    jurisprudence_references: List[JurisprudenceReference] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)  # Réponses des différentes IA
    
    def __post_init__(self):
        """Calcule le nombre de mots"""
        if self.document and not self.word_count:
            self.word_count = len(self.document.split())

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
    config: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    
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
    config: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    
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

# ========== COMMUNICATION ==========

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

# ========== SESSION ==========

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

# ========== COMPARISON ==========

@dataclass
class ComparisonResult:
    """Résultat de comparaison de documents"""
    type: str  # versions, témoignages, etc.
    document_count: int
    comparison: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    visualizations: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)

# ========== TIMELINE ==========

@dataclass
class TimelineResult:
    """Résultat de génération de chronologie"""
    type: str
    events: List[TimelineEvent]
    document_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    visualization: Optional[Any] = None
    analysis: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)

# ========== MAPPING ==========

@dataclass
class MappingResult:
    """Résultat de cartographie"""
    type: str
    entities: List[Entity]
    relationships: List[Relationship]
    analysis: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    visualization: Optional[Any] = None
    document_count: int
    config: Dict[str, Any] = field(default_factory=dict)

# ========== HELPERS ==========

def get_all_juridictions() -> List[str]:
    """Retourne la liste de toutes les juridictions"""
    return [j.value for j in TypeJuridiction]

def get_juridiction_type(juridiction_name: str) -> Optional[TypeJuridiction]:
    """Retourne le type de juridiction à partir du nom"""
    for jur_type in TypeJuridiction:
        if jur_type.value.lower() == juridiction_name.lower():
            return jur_type
    return None

# Types personnalisés pour les annotations
DocumentDict = Dict[str, Document]
SearchResults = List[SearchResult]
TimelineEvents = List[TimelineEvent]
EntityList = List[Entity]
RelationshipList = List[Relationship]