"""Modèles de données pour la jurisprudence - Version complète"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Tuple
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

class NiveauImportance(Enum):
    """Niveaux d'importance"""
    FONDAMENTAL = 10
    TRES_IMPORTANT = 8
    IMPORTANT = 6
    MOYEN = 5
    FAIBLE = 3
    ANECDOTIQUE = 1

# ========== DATACLASSES ==========

@dataclass
class Document:
    """Document de base (compatibilité)"""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class DocumentJuridique:
    """Document juridique avec métadonnées complètes"""
    id: str
    titre: str
    contenu: str
    type_document: str
    date_creation: datetime
    source: str
    juridiction: Optional[str] = None
    numero_affaire: Optional[str] = None
    parties: Optional[Dict[str, str]] = None
    magistrats: Optional[List[str]] = None
    avocats: Optional[List[str]] = None
    mots_cles: Optional[List[str]] = None
    articles_vises: Optional[List[str]] = None
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    importance: int = 5
    confidentiel: bool = False
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.mots_cles is None:
            self.mots_cles = []
        if self.articles_vises is None:
            self.articles_vises = []
        if self.parties is None:
            self.parties = {}
        if self.magistrats is None:
            self.magistrats = []
        if self.avocats is None:
            self.avocats = []

@dataclass
class JurisprudenceReference:
    """Référence de jurisprudence complète"""
    numero: str
    date: datetime
    juridiction: str
    formation: Optional[str] = None
    titre: Optional[str] = None
    resume: Optional[str] = None
    texte_integral: Optional[str] = None
    url: Optional[str] = None
    source: SourceJurisprudence = SourceJurisprudence.MANUAL
    mots_cles: List[str] = None
    articles_vises: List[str] = None
    decisions_citees: List[str] = None
    importance: int = 5
    solution: Optional[str] = None
    portee: Optional[str] = None
    commentaires: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.mots_cles is None:
            self.mots_cles = []
        if self.articles_vises is None:
            self.articles_vises = []
        if self.decisions_citees is None:
            self.decisions_citees = []
        if self.commentaires is None:
            self.commentaires = []

@dataclass
class VerificationResult:
    """Résultat de vérification d'une jurisprudence"""
    is_valid: bool
    reference: Optional[JurisprudenceReference] = None
    message: str = ""
    confidence: float = 0.0
    source_verified: Optional[SourceJurisprudence] = None
    verification_date: datetime = None
    details: Dict[str, Any] = None
    suggestions: List[JurisprudenceReference] = None
    
    def __post_init__(self):
        if self.verification_date is None:
            self.verification_date = datetime.now()
        if self.details is None:
            self.details = {}
        if self.suggestions is None:
            self.suggestions = []

@dataclass
class JurisprudenceSearchCriteria:
    """Critères de recherche de jurisprudence étendus"""
    keywords: List[str] = None
    juridictions: List[str] = None
    formations: List[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    articles: List[str] = None
    importance_min: int = 1
    sources: List[SourceJurisprudence] = None
    max_results: int = 50
    include_resume: bool = True
    include_texte_integral: bool = False
    sort_by: str = "date"
    sort_order: str = "desc"
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.juridictions is None:
            self.juridictions = []
        if self.formations is None:
            self.formations = []
        if self.articles is None:
            self.articles = []
        if self.sources is None:
            self.sources = []

@dataclass
class JurisprudenceAnalysis:
    """Analyse approfondie d'une jurisprudence"""
    reference_id: str
    principes_degages: List[str]
    impact_juridique: str
    evolution_jurisprudentielle: str
    cas_similaires: List[str] = None
    cas_contradictoires: List[str] = None
    recommandations: List[str] = None
    risques_identifies: List[str] = None
    opportunites: List[str] = None
    date_analyse: datetime = None
    analyste: Optional[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.cas_similaires is None:
            self.cas_similaires = []
        if self.cas_contradictoires is None:
            self.cas_contradictoires = []
        if self.recommandations is None:
            self.recommandations = []
        if self.risques_identifies is None:
            self.risques_identifies = []
        if self.opportunites is None:
            self.opportunites = []
        if self.date_analyse is None:
            self.date_analyse = datetime.now()

@dataclass
class JurisprudenceSearch:
    """Recherche de jurisprudence avec résultats"""
    query: str
    criteria: JurisprudenceSearchCriteria
    results: List[JurisprudenceReference] = None
    total_results: int = 0
    search_date: datetime = None
    search_duration: float = 0.0
    metadata: Dict[str, Any] = None
    facets: Dict[str, Dict[str, int]] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.search_date is None:
            self.search_date = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.facets is None:
            self.facets = {}
    
    def add_result(self, reference: JurisprudenceReference):
        """Ajoute un résultat à la recherche"""
        self.results.append(reference)
        self.total_results = len(self.results)
    
    def filter_by_juridiction(self, juridiction: str) -> List[JurisprudenceReference]:
        """Filtre les résultats par juridiction"""
        return [r for r in self.results if r.juridiction == juridiction]
    
    def filter_by_date_range(self, start: datetime, end: datetime) -> List[JurisprudenceReference]:
        """Filtre les résultats par plage de dates"""
        return [r for r in self.results if start <= r.date <= end]
    
    def sort_by_date(self, reverse: bool = True) -> List[JurisprudenceReference]:
        """Trie les résultats par date"""
        return sorted(self.results, key=lambda x: x.date, reverse=reverse)
    
    def sort_by_importance(self, reverse: bool = True) -> List[JurisprudenceReference]:
        """Trie les résultats par importance"""
        return sorted(self.results, key=lambda x: x.importance, reverse=reverse)
    
    def get_facets(self) -> Dict[str, Dict[str, int]]:
        """Calcule les facettes de recherche"""
        self.facets = {
            'juridictions': {},
            'years': {},
            'importance': {}
        }
        
        for result in self.results:
            # Juridictions
            jur = result.juridiction
            self.facets['juridictions'][jur] = self.facets['juridictions'].get(jur, 0) + 1
            
            # Années
            year = str(result.date.year)
            self.facets['years'][year] = self.facets['years'].get(year, 0) + 1
            
            # Importance
            imp = str(result.importance)
            self.facets['importance'][imp] = self.facets['importance'].get(imp, 0) + 1
        
        return self.facets

@dataclass
class JurisprudenceStats:
    """Statistiques détaillées sur la jurisprudence"""
    total_decisions: int = 0
    by_juridiction: Dict[str, int] = None
    by_year: Dict[int, int] = None
    by_month: Dict[str, int] = None
    by_source: Dict[str, int] = None
    by_importance: Dict[int, int] = None
    most_cited_articles: List[Tuple[str, int]] = None
    most_cited_decisions: List[Tuple[str, int]] = None
    trending_topics: List[str] = None
    recent_updates: List[str] = None
    last_update: datetime = None
    
    def __post_init__(self):
        if self.by_juridiction is None:
            self.by_juridiction = {}
        if self.by_year is None:
            self.by_year = {}
        if self.by_month is None:
            self.by_month = {}
        if self.by_source is None:
            self.by_source = {}
        if self.by_importance is None:
            self.by_importance = {}
        if self.most_cited_articles is None:
            self.most_cited_articles = []
        if self.most_cited_decisions is None:
            self.most_cited_decisions = []
        if self.trending_topics is None:
            self.trending_topics = []
        if self.recent_updates is None:
            self.recent_updates = []
        if self.last_update is None:
            self.last_update = datetime.now()

@dataclass
class JurisprudenceAlert:
    """Alerte jurisprudence avec configuration complète"""
    id: str
    name: str
    description: Optional[str] = None
    criteria: JurisprudenceSearchCriteria = None
    frequency: str = "daily"  # "realtime", "daily", "weekly", "monthly"
    active: bool = True
    created_date: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    recipients: List[str] = None
    notification_methods: List[str] = None  # "email", "sms", "app"
    results_count: int = 0
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.recipients is None:
            self.recipients = []
        if self.notification_methods is None:
            self.notification_methods = ["email"]
        if self.criteria is None:
            self.criteria = JurisprudenceSearchCriteria()

# ========== CLASSES SUPPLEMENTAIRES ==========

@dataclass
class AnalyseJuridique:
    """Analyse juridique (alias pour compatibilité)"""
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
    """Cas juridique (alias pour compatibilité)"""
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