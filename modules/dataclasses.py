# modules/dataclasses.py
"""Modèles de données pour l'application juridique - Version réorganisée et améliorée"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Import des énumérations centrales
from config.app_config import DocumentType, InfractionAffaires, LLMProvider

# Alias pour compatibilité avec les anciens imports
TypeDocument = DocumentType
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Union

# Imports conditionnels pour éviter les imports circulaires
if TYPE_CHECKING:
    from managers.jurisprudence_verifier import JurisprudenceVerifier
    from managers.legal_search import LegalSearchManager


# ========== ENUMS ==========
from .data_models.enums import (
    ForceProbante,
    NaturePiece,
    PhaseProcedure,
    RiskLevel,
    SearchMode,
    SourceEntreprise,
    SourceJurisprudence,
    StatutProcedural,
    StyleRedaction,
    TypeAnalyse,
    TypeElementProcedure,
    TypeJuridiction,
    TypePartie,
)

# ========== CLASSES JURIDIQUES ==========

# --- Documents et Pièces ---

@dataclass
class Document:
    """Représente un document juridique - VERSION AMÉLIORÉE"""
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
    
    # Nouveaux champs pour la recherche améliorée
    highlights: List[str] = field(default_factory=list)  # Extraits pertinents
    matched_references: List[str] = field(default_factory=list)  # Références @ matchées
    relevance_score: float = 0.0  # Score de pertinence (0-1)
    
    # Informations de style extraites
    style_info: Optional[Dict[str, Any]] = None
    
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
        
        # Ajouter le score de pertinence aux métadonnées
        if self.relevance_score > 0:
            self.metadata['score'] = self.relevance_score
    
    def add_highlight(self, text: str, start_pos: Optional[int] = None, end_pos: Optional[int] = None):
        """Ajoute un passage surligné avec position optionnelle"""
        highlight = {
            'text': text,
            'start': start_pos,
            'end': end_pos
        }
        
        # Stocker comme string simple ou dict selon le cas
        if start_pos is None and end_pos is None:
            self.highlights.append(text)
        else:
            self.highlights.append(highlight)
    
    def has_reference(self, ref: str) -> bool:
        """Vérifie si le document contient une référence"""
        ref_clean = ref.replace('@', '').strip().lower()
        
        # Vérifier dans les références matchées
        if ref_clean in [r.lower() for r in self.matched_references]:
            return True
        
        # Vérifier dans le contenu
        return (ref_clean in self.title.lower() or 
                ref_clean in self.source.lower() or
                ref_clean in self.content.lower() or
                ref_clean in self.metadata.get('reference', '').lower())
    
    def extract_references(self) -> List[str]:
        """Extrait toutes les références @ du contenu"""
        references = re.findall(r'@(\w+)', self.content)
        # Ajouter aussi celles du titre
        references.extend(re.findall(r'@(\w+)', self.title))
        
        # Mettre à jour matched_references
        unique_refs = list(set(references))
        self.matched_references = unique_refs
        
        return unique_refs
    
    def matches_keywords(self, keywords: List[str], threshold: float = 0.3) -> Tuple[bool, float]:
        """
        Vérifie si le document correspond aux mots-clés
        
        Returns:
            Tuple (matches: bool, match_ratio: float)
        """
        if not keywords:
            return False, 0.0
        
        content_lower = self.content.lower()
        title_lower = self.title.lower()
        
        matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Titre compte double
            if keyword_lower in title_lower:
                matches += 2
            if keyword_lower in content_lower:
                matches += 1
        
        # Calculer le ratio de correspondance
        max_possible = len(keywords) * 3  # Max si tous les mots sont dans titre et contenu
        match_ratio = matches / max_possible
        
        return match_ratio >= threshold, match_ratio
    
    def get_preview(self, max_length: int = 200) -> str:
        """Retourne un aperçu du contenu"""
        if len(self.content) <= max_length:
            return self.content
        
        # Si on a des highlights, utiliser le premier
        if self.highlights:
            first_highlight = self.highlights[0]
            if isinstance(first_highlight, dict):
                return first_highlight['text']
            return str(first_highlight)
        
        # Sinon, prendre le début du contenu
        return self.content[:max_length].strip() + "..."
    
    def extract_style_info(self) -> Dict[str, Any]:
        """Extrait les informations de style du document"""
        # Analyser la numérotation des paragraphes
        numbering_patterns = {
            'numeric': r'^\d+\.',
            'roman_upper': r'^[IVX]+\.',
            'roman_lower': r'^[ivx]+\.',
            'alphabetic_upper': r'^[A-Z]\.',
            'alphabetic_lower': r'^[a-z]\.',
            'hierarchical': r'^\d+\.\d+'
        }
        
        style_info = {
            'paragraph_numbering': None,
            'average_sentence_length': 0,
            'formality_indicators': 0,
            'technical_terms_count': 0
        }
        
        # Détecter le style de numérotation
        for style, pattern in numbering_patterns.items():
            if re.search(pattern, self.content, re.MULTILINE):
                style_info['paragraph_numbering'] = style
                break
        
        # Analyser la complexité des phrases
        sentences = self.content.split('.')
        if sentences:
            total_words = sum(len(s.split()) for s in sentences)
            style_info['average_sentence_length'] = total_words / len(sentences)
        
        # Indicateurs de formalité
        formal_markers = [
            'attendu que', 'considérant', 'il appert', 'nonobstant',
            'aux termes de', 'en l\'espèce', 'il échet', 'partant'
        ]
        style_info['formality_indicators'] = sum(
            1 for marker in formal_markers if marker in self.content.lower()
        )
        
        self.style_info = style_info
        return style_info
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        base_dict = {
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
            'mime_type': self.mime_type,
            'style_info': self.style_info
        }
        
        # Ajouter les nouveaux champs s'ils sont présents
        if self.highlights:
            base_dict['highlights'] = self.highlights
        if self.matched_references:
            base_dict['matched_references'] = self.matched_references
        if self.relevance_score > 0:
            base_dict['relevance_score'] = self.relevance_score
        
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Crée un objet depuis un dictionnaire"""
        # Convertir les dates si nécessaire
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def __str__(self):
        return f"{self.type_document.value if hasattr(self, 'type_document') else 'Document'}: {self.title}"

@dataclass  
class PieceProcedure:
    """Représente une pièce de procédure dans un dossier"""
    id: str
    nom: str
    type_piece: str
    date_creation: datetime
    description: Optional[str] = None
    contenu: Optional[str] = None
    numero_ordre: Optional[int] = None
    confidentiel: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"Pièce {self.numero_ordre}: {self.nom}"

@dataclass
class TemplateDocument:
    """Template de document juridique réutilisable"""
    id: str
    nom: str
    type_document: DocumentType
    description: str
    contenu_template: str  # Contenu avec variables {{variable}}
    variables_requises: List[str] = field(default_factory=list)
    variables_optionnelles: List[str] = field(default_factory=list)
    categorie: str = "général"
    tags: List[str] = field(default_factory=list)
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None
    auteur: str = "système"
    version: int = 1
    actif: bool = True
    exemples_utilisation: List[Dict[str, str]] = field(default_factory=list)
    
    def generer_document(self, variables: Dict[str, str]) -> str:
        """Génère un document à partir du template"""
        contenu = self.contenu_template
        for var, valeur in variables.items():
            contenu = contenu.replace(f"{{{{{var}}}}}", str(valeur))
        return contenu

# --- Jurisprudence et Recherche ---

@dataclass
class Jurisprudence:
    """Représente une décision de jurisprudence"""
    id: str
    titre: str
    juridiction: str
    date_decision: datetime
    numero: str
    resume: str
    texte_integral: Optional[str] = None
    mots_cles: List[str] = field(default_factory=list)
    articles_cites: List[str] = field(default_factory=list)
    url_source: Optional[str] = None
    pertinence: float = 0.0
    
    def __str__(self):
        return f"{self.juridiction} - {self.numero} ({self.date_decision.strftime('%d/%m/%Y')})"

@dataclass
class ResultatRecherche:
    """Résultat d'une recherche juridique"""
    id: str
    requete: str
    date_recherche: datetime
    nombre_resultats: int
    resultats: List[Dict[str, Any]] = field(default_factory=list)
    filtres_appliques: Dict[str, Any] = field(default_factory=dict)
    temps_recherche_ms: int = 0
    sources: List[str] = field(default_factory=list)
    pertinence_globale: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    
    def obtenir_top_resultats(self, n: int = 10) -> List[Dict[str, Any]]:
        """Retourne les n meilleurs résultats"""
        return sorted(self.resultats, 
                     key=lambda x: x.get('score', 0), 
                     reverse=True)[:n]

@dataclass
class ConfigurationRecherche:
    """Configuration pour les recherches juridiques"""
    id: str
    nom_configuration: str
    description: str
    sources_activees: List[str] = field(default_factory=list)
    filtres_par_defaut: Dict[str, Any] = field(default_factory=dict)
    taille_resultats: int = 20
    inclure_archives: bool = False
    recherche_floue: bool = True
    seuil_pertinence: float = 0.5
    langues: List[str] = field(default_factory=lambda: ["fr"])
    tri_par: str = "pertinence"  # "pertinence", "date", "source"
    ordre_tri: str = "desc"  # "asc", "desc"
    highlight: bool = True
    agreger_resultats: bool = False
    exclure_sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire"""
        return {
            'sources': self.sources_activees,
            'filtres': self.filtres_par_defaut,
            'size': self.taille_resultats,
            'fuzzy': self.recherche_floue,
            'threshold': self.seuil_pertinence,
            'sort': f"{self.tri_par}:{self.ordre_tri}"
        }

# --- Gestion des Risques et Analyses ---

@dataclass
class Risque:
    """Représente un risque juridique identifié"""
    id: str
    titre: str
    description: str
    niveau_gravite: str  # "faible", "moyen", "élevé", "critique"
    probabilite: str  # "rare", "possible", "probable", "certain"
    impact_financier: Optional[float] = None
    date_identification: datetime = field(default_factory=datetime.now)
    date_echeance: Optional[datetime] = None
    mesures_preventives: List[str] = field(default_factory=list)
    responsable: Optional[str] = None
    statut: str = "actif"  # "actif", "traité", "accepté", "mitigé"
    categories: List[str] = field(default_factory=list)
    dossiers_lies: List[str] = field(default_factory=list)
    
    def score_risque(self) -> float:
        """Calcule un score de risque simple"""
        gravite_scores = {"faible": 1, "moyen": 2, "élevé": 3, "critique": 4}
        probabilite_scores = {"rare": 1, "possible": 2, "probable": 3, "certain": 4}
        
        g = gravite_scores.get(self.niveau_gravite, 2)
        p = probabilite_scores.get(self.probabilite, 2)
        
        return g * p

@dataclass
class AnalyseJuridique:
    """Analyse juridique d'un document ou d'une situation"""
    id: str
    titre: str
    date_analyse: datetime
    type_analyse: str  # "risques", "conformite", "strategie", "jurisprudence"
    objet_analyse: str  # ID du document/dossier analysé
    contenu_analyse: str
    points_cles: List[str] = field(default_factory=list)
    recommandations: List[str] = field(default_factory=list)
    risques_identifies: List[str] = field(default_factory=list)
    opportunites: List[str] = field(default_factory=list)
    references_juridiques: List[str] = field(default_factory=list)
    niveau_confiance: float = 0.0  # 0 à 1
    auteur: str = "IA"
    validee_par: Optional[str] = None
    statut: str = "brouillon"  # "brouillon", "finalisee", "validee"
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Dossiers et Timeline ---

@dataclass
class EvenementTimeline:
    """Représente un événement dans la timeline d'un dossier"""
    id: str
    titre: str
    description: str
    date_evenement: datetime
    type_evenement: str  # "audience", "depot", "decision", "acte", "autre"
    dossier_id: str
    importance: str = "normale"  # "faible", "normale", "haute", "critique"
    documents_lies: List[str] = field(default_factory=list)
    personnes_impliquees: List[str] = field(default_factory=list)
    lieu: Optional[str] = None
    duree_minutes: Optional[int] = None
    statut: str = "realise"  # "prevu", "realise", "annule", "reporte"
    rappels: List[datetime] = field(default_factory=list)
    notes: Optional[str] = None
    
    def est_futur(self) -> bool:
        return self.date_evenement > datetime.now()

@dataclass
class DossierPenal:
    """Représente un dossier pénal complet"""
    id: str
    numero_dossier: str
    titre: str
    description: str
    date_ouverture: datetime
    juridiction: str
    date_cloture: Optional[datetime] = None
    juge_instruction: Optional[str] = None
    procureur: Optional[str] = None
    montant_prejudice: Optional[float] = None
    statut: str = "ouvert"  # "ouvert", "en_cours", "suspendu", "clos"
    parties: Dict[str, List[str]] = field(default_factory=dict)  # {"demandeurs": [...], "defendeurs": [...]}
    infractions: List[str] = field(default_factory=list)
    pieces: List[str] = field(default_factory=list)  # IDs des pièces
    evenements: List[str] = field(default_factory=list)  # IDs des événements
    risques: List[str] = field(default_factory=list)  # IDs des risques
    notes_internes: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def ajouter_partie(self, role: str, nom: str):
        if role not in self.parties:
            self.parties[role] = []
        self.parties[role].append(nom)

# --- Système et Notifications ---

@dataclass
class Notification:
    """Notification système pour l'utilisateur"""
    id: str
    titre: str
    message: str
    type_notification: str  # "info", "warning", "error", "success"
    date_creation: datetime = field(default_factory=datetime.now)
    date_lecture: Optional[datetime] = None
    destinataire: str = ""
    source: str = "système"
    action_requise: bool = False
    lien_action: Optional[str] = None
    priorite: str = "normale"  # "basse", "normale", "haute", "urgente"
    expire_le: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def est_lue(self) -> bool:
        return self.date_lecture is not None
    
    @property
    def est_expiree(self) -> bool:
        return self.expire_le and datetime.now() > self.expire_le
    
    def marquer_comme_lue(self):
        self.date_lecture = datetime.now()

@dataclass
class SessionUtilisateur:
    """Session d'un utilisateur de l'application"""
    id: str
    utilisateur_id: str
    date_debut: datetime = field(default_factory=datetime.now)
    date_fin: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    actions_effectuees: List[Dict[str, Any]] = field(default_factory=list)
    recherches: List[str] = field(default_factory=list)
    documents_consultes: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    contexte_actuel: Dict[str, Any] = field(default_factory=dict)
    
    def ajouter_action(self, action: str, details: Dict[str, Any] = None):
        self.actions_effectuees.append({
            'action': action,
            'timestamp': datetime.now(),
            'details': details or {}
        })
    
    def terminer_session(self):
        self.date_fin = datetime.now()
    
    @property
    def duree_session(self) -> Optional[timedelta]:
        if self.date_fin:
            return self.date_fin - self.date_debut
        return datetime.now() - self.date_debut

# ========== CLASSES D'ANALYSE ET EXTRACTION ==========

@dataclass
class Entity:
    """Représente une entité extraite d'un texte (personne, organisation, lieu)"""
    id: str
    name: str
    type: str  # "person", "organization", "location", "date", "amount"
    text: str  # Texte original
    start_pos: int  # Position de début dans le texte
    end_pos: int  # Position de fin dans le texte
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.type}: {self.name}"
    
    def __hash__(self):
        return hash((self.name, self.type))

@dataclass
class QueryAnalysis:
    """Analyse d'une requête utilisateur pour comprendre l'intention - VERSION ÉTENDUE"""
    original_query: str
    query_lower: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Analyse de l'intention
    intent: str = "search"  # "search", "redaction", "analysis", "jurisprudence", etc.
    command_type: Optional[str] = None  # Pour le routing spécifique
    
    # Extraction d'entités
    entities: Dict[str, Any] = field(default_factory=dict)
    reference: Optional[str] = None  # Référence @ extraite
    document_type: Optional[str] = None
    action: Optional[str] = None
    subject_matter: Optional[str] = None
    phase_procedurale: Optional[PhaseProcedure] = None
    
    # Parties identifiées
    parties: Dict[str, List[str]] = field(default_factory=lambda: {'demandeurs': [], 'defendeurs': []})
    
    # Infractions et éléments juridiques
    infractions: List[str] = field(default_factory=list)
    style_request: Optional[str] = None
    date_filter: Optional[Tuple[datetime, datetime]] = None
    
    # Mots-clés et recherche
    keywords: List[str] = field(default_factory=list)
    search_type: str = 'general'  # general, dossier, jurisprudence, partie
    
    # Métadonnées
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialisation pour normaliser les données"""
        if not self.query_lower:
            self.query_lower = self.original_query.lower()
        
        # Si pas d'entités, initialiser avec la structure attendue
        if not self.entities:
            self.entities = {
                'references': [],
                'parties': {'demandeurs': [], 'defendeurs': []},
                'infractions': [],
                'dates': [],
                'documents': []
            }
    
    def has_reference(self) -> bool:
        """Vérifie si la requête contient une référence @"""
        return bool(self.reference or self.entities.get('references'))
    
    def get_document_type(self) -> Optional[str]:
        """Retourne le type de document demandé si applicable"""
        return self.document_type or self.details.get('document_type')
    
    def get_primary_intent(self) -> str:
        """Retourne l'intention principale"""
        return self.command_type or self.intent
    
    def is_high_confidence(self) -> bool:
        """Vérifie si l'analyse est fiable"""
        return self.confidence >= 0.7
    
    def get_all_keywords(self) -> List[str]:
        """Retourne tous les mots-clés (keywords + extraits des parties/infractions)"""
        all_keywords = self.keywords.copy()
        
        # Ajouter les noms de parties
        for parties_list in self.parties.values():
            all_keywords.extend(parties_list)
        
        # Ajouter les infractions
        all_keywords.extend(self.infractions)
        
        # Ajouter la référence si présente
        if self.reference:
            all_keywords.append(self.reference)
        
        # Dédupliquer et retourner
        return list(set(all_keywords))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'query': self.original_query,
            'query_lower': self.query_lower,
            'intent': self.intent,
            'command_type': self.command_type,
            'entities': self.entities,
            'reference': self.reference,
            'document_type': self.document_type,
            'parties': self.parties,
            'infractions': self.infractions,
            'keywords': self.keywords,
            'search_type': self.search_type,
            'confidence': self.confidence,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class CasJuridique:
    """Représente un cas juridique spécifique"""
    id: str
    titre: str
    description: str
    type_cas: str  # "penal", "civil", "commercial", "administratif"
    date_fait: datetime
    lieu_fait: Optional[str] = None
    parties_impliquees: List[str] = field(default_factory=list)
    faits: List[str] = field(default_factory=list)
    questions_juridiques: List[str] = field(default_factory=list)
    infractions_potentielles: List[str] = field(default_factory=list)
    articles_applicables: List[str] = field(default_factory=list)
    jurisprudences_pertinentes: List[str] = field(default_factory=list)
    strategie_proposee: Optional[str] = None
    risque_evaluation: Optional[str] = None
    statut: str = "en_analyse"  # "en_analyse", "actif", "resolu", "archive"
    
    def ajouter_fait(self, fait: str):
        self.faits.append(fait)

@dataclass
class DocumentJuridique:
    """Représente un document juridique formel"""
    id: str
    titre: str
    type_document: str  # "contrat", "assignation", "conclusions", "jugement", etc.
    numero_reference: str
    date_document: datetime
    auteur: str
    destinataires: List[str] = field(default_factory=list)
    contenu: str = ""
    pieces_jointes: List[str] = field(default_factory=list)
    signataires: List[str] = field(default_factory=list)
    date_signature: Optional[datetime] = None
    juridiction: Optional[str] = None
    procedure_liee: Optional[str] = None
    statut_legal: str = "projet"  # "projet", "signe", "depose", "notifie"
    confidentiel: bool = False
    version: int = 1
    historique_versions: List[Dict[str, Any]] = field(default_factory=list)
    
    def est_signe(self) -> bool:
        return self.date_signature is not None and len(self.signataires) > 0

# ========== CLASSES DE STYLE ET APPRENTISSAGE ==========

@dataclass
class StylePattern:
    """Pattern de style extrait d'un document"""
    document_id: str
    type_acte: str
    structure: Dict[str, Any]
    formules: List[str]
    mise_en_forme: Dict[str, Any]
    vocabulaire: Dict[str, Any]
    paragraphes_types: List[str]
    numerotation: Dict[str, Any] = field(default_factory=dict)
    formalite: Dict[str, Any] = field(default_factory=dict)
    argumentation: Dict[str, List[str]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'document_id': self.document_id,
            'type_acte': self.type_acte,
            'structure': self.structure,
            'formules': self.formules,
            'mise_en_forme': self.mise_en_forme,
            'vocabulaire': self.vocabulaire,
            'numerotation': self.numerotation,
            'formalite': self.formalite
        }

@dataclass
class StyleLearningResult:
    """Résultat de l'apprentissage de style"""
    style_name: str
    documents_analyzed: int
    confidence_score: float = 0.0
    average_sentence_length: int = 0
    average_paragraph_length: int = 0
    common_phrases: List[str] = field(default_factory=list)
    transition_words: List[str] = field(default_factory=list)
    argument_patterns: List[str] = field(default_factory=list)
    citation_patterns: List[str] = field(default_factory=list)
    paragraph_numbering_style: Optional[str] = None
    paragraph_numbering_pattern: Optional[str] = None
    formality_score: float = 0.5
    style_config: Optional['StyleConfig'] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_style_config(self) -> 'StyleConfig':
        """Convertit en configuration de style"""
        return StyleConfig(
            name=self.style_name,
            formality_level='formel' if self.formality_score > 0.6 else 'moderne',
            sentence_length_target=self.average_sentence_length,
            paragraph_length_target=self.average_paragraph_length,
            use_numbering=bool(self.paragraph_numbering_style),
            numbering_style=self.paragraph_numbering_style or 'numeric',
            common_phrases=self.common_phrases[:10],
            transition_words=self.transition_words[:10],
            preferred_conjunctions=self._extract_conjunctions(),
            technical_terms_density='high' if self.formality_score > 0.7 else 'medium'
        )
    
    def _extract_conjunctions(self) -> List[str]:
        """Extrait les conjonctions préférées"""
        conjunctions = []
        for word in self.transition_words:
            if word.lower() in ['mais', 'donc', 'or', 'car', 'toutefois', 'néanmoins', 'cependant']:
                conjunctions.append(word)
        return conjunctions[:5]

@dataclass
class StyleConfig:
    """Configuration de style pour la génération de documents"""
    name: str
    formality_level: str = 'formel'  # 'moderne', 'formel', 'tres_formel'
    sentence_length_target: int = 20
    paragraph_length_target: int = 100
    use_numbering: bool = True
    numbering_style: str = 'numeric'  # 'numeric', 'roman', 'alpha', 'dash', 'bullet'
    common_phrases: List[str] = field(default_factory=list)
    transition_words: List[str] = field(default_factory=list)
    preferred_conjunctions: List[str] = field(default_factory=list)
    technical_terms_density: str = 'medium'  # 'low', 'medium', 'high'
    active_voice_preference: float = 0.7  # 0-1, où 1 = toujours voix active
    citation_style: str = 'standard'  # 'standard', 'detailed', 'minimal'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'name': self.name,
            'formality_level': self.formality_level,
            'sentence_length_target': self.sentence_length_target,
            'paragraph_length_target': self.paragraph_length_target,
            'use_numbering': self.use_numbering,
            'numbering_style': self.numbering_style,
            'common_phrases': self.common_phrases,
            'transition_words': self.transition_words,
            'technical_terms_density': self.technical_terms_density
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StyleConfig':
        """Crée depuis un dictionnaire"""
        return cls(**data)
    
    def apply_to_prompt(self, base_prompt: str) -> str:
        """Enrichit un prompt avec les directives de style"""
        style_instructions = f"""
Style requis : {self.name}
- Niveau de formalité : {self.formality_level}
- Longueur cible des phrases : environ {self.sentence_length_target} mots
- Longueur cible des paragraphes : environ {self.paragraph_length_target} mots
- Numérotation : {'Utiliser ' + self.numbering_style if self.use_numbering else 'Pas de numérotation'}
- Densité technique : {self.technical_terms_density}
"""
        
        if self.common_phrases:
            style_instructions += f"\n- Phrases types à utiliser : {', '.join(self.common_phrases[:3])}"
        
        if self.transition_words:
            style_instructions += f"\n- Mots de transition privilégiés : {', '.join(self.transition_words[:5])}"
        
        return f"{base_prompt}\n\n{style_instructions}"

# ========== INFORMATIONS ENTREPRISE ==========

@dataclass
class InformationEntreprise:
    """Informations légales d'une entreprise"""
    # Identifiants
    siren: Optional[str] = None
    siret: Optional[str] = None
    tva_intracommunautaire: Optional[str] = None
    
    # Dénomination
    denomination: Optional[str] = None
    denomination_usuelle: Optional[str] = None
    sigle: Optional[str] = None
    
    # Forme et capital
    forme_juridique: Optional[str] = None
    capital_social: Optional[float] = None
    devise_capital: str = "EUR"
    
    # Dates
    date_creation: Optional[datetime] = None
    date_cloture_exercice: Optional[str] = None
    date_cessation: Optional[datetime] = None
    
    # Adresse
    siege_social: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    pays: str = "France"
    
    # RCS
    rcs_numero: Optional[str] = None
    rcs_ville: Optional[str] = None
    
    # Activité
    code_ape: Optional[str] = None
    code_naf: Optional[str] = None
    activite_principale: Optional[str] = None
    
    # Effectifs et finances
    effectif: Optional[str] = None
    effectif_min: Optional[int] = None
    effectif_max: Optional[int] = None
    chiffre_affaires: Optional[float] = None
    resultat: Optional[float] = None
    
    # Représentants
    representants_legaux: List[Dict[str, str]] = field(default_factory=list)
    
    # Métadonnées
    source: SourceEntreprise = SourceEntreprise.MANUAL
    date_recuperation: datetime = field(default_factory=datetime.now)
    derniere_mise_a_jour: Optional[datetime] = None
    fiable: bool = True
    
    def format_capital(self) -> str:
        """Formate le capital social"""
        if not self.capital_social:
            return ""
        return f"{self.capital_social:,.2f} {self.devise_capital}".replace(",", " ")
    
    def get_immatriculation_complete(self) -> str:
        """Retourne l'immatriculation RCS complète"""
        if self.rcs_numero and self.rcs_ville:
            return f"RCS {self.rcs_ville} {self.rcs_numero}"
        return ""
    
    def get_representant_principal(self) -> Optional[Dict[str, str]]:
        """Retourne le représentant légal principal"""
        if self.representants_legaux:
            return self.representants_legaux[0]
        return None
    
    def to_legal_string(self, style: str = "complet") -> str:
        """Convertit en chaîne pour document juridique"""
        if style == "simple":
            return self.denomination or ""
        
        parts = [self.denomination]
        if self.forme_juridique:
            parts.append(f", {self.forme_juridique}")
        if self.capital_social:
            parts.append(f" au capital de {self.format_capital()}")
        if self.get_immatriculation_complete():
            parts.append(f", {self.get_immatriculation_complete()}")
        if self.siege_social:
            parts.append(f", dont le siège social est sis {self.siege_social}")
            
        return "".join(parts)
    
    def get_denomination_complete(self) -> str:
        """Retourne la dénomination complète avec forme juridique"""
        if self.forme_juridique:
            return f"{self.denomination} ({self.forme_juridique})"
        return self.denomination
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'siren': self.siren,
            'siret': self.siret,
            'denomination': self.denomination,
            'forme_juridique': self.forme_juridique,
            'capital_social': self.capital_social,
            'siege_social': self.siege_social,
            'rcs': self.get_immatriculation_complete(),
            'representants': self.representants_legaux,
            'source': self.source.value,
            'date_recuperation': self.date_recuperation.isoformat()
        }

@dataclass
class Partie:
    """Représente une partie dans un dossier juridique"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nom: str = ""
    type_partie: TypePartie = TypePartie.DEMANDEUR
    type_personne: str = "morale"  # "morale" ou "physique"
    phase_procedure: PhaseProcedure = PhaseProcedure.ENQUETE_PRELIMINAIRE
    statut_procedural: StatutProcedural = StatutProcedural.MIS_EN_CAUSE
    
    # Pour les personnes morales
    info_entreprise: Optional[InformationEntreprise] = None
    
    # Pour les personnes physiques
    prenom: Optional[str] = None
    date_naissance: Optional[datetime] = None
    lieu_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    profession: Optional[str] = None
    
    # Coordonnées
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    
    # Représentation
    avocat: Optional[str] = None
    avocat_barreau: Optional[str] = None
    
    # Métadonnées
    date_ajout: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)
    documents_lies: List[str] = field(default_factory=list)
    
    # Compatibilité avec l'ancienne structure
    forme_juridique: Optional[str] = None
    capital_social: Optional[float] = None
    rcs: Optional[str] = None
    siret: Optional[str] = None
    siege_social: Optional[str] = None
    representant_legal: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"partie_{self.nom.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Déterminer automatiquement le statut selon la phase et le type
        self._auto_determine_statut()
    
    def _auto_determine_statut(self):
        """Détermine automatiquement le statut procédural selon la phase"""
        if self.type_partie == TypePartie.PLAIGNANT:
            self.statut_procedural = StatutProcedural.PLAIGNANT
        elif self.type_partie == TypePartie.PARTIE_CIVILE:
            self.statut_procedural = StatutProcedural.PARTIE_CIVILE
        elif self.type_partie == TypePartie.TEMOIN:
            self.statut_procedural = StatutProcedural.TEMOIN
        elif self.phase_procedure in [PhaseProcedure.ENQUETE_PRELIMINAIRE, PhaseProcedure.ENQUETE_FLAGRANCE]:
            if self.type_partie in [TypePartie.MIS_EN_CAUSE, TypePartie.DEFENDEUR]:
                self.statut_procedural = StatutProcedural.MIS_EN_CAUSE
        elif self.phase_procedure == PhaseProcedure.INSTRUCTION:
            if self.type_partie in [TypePartie.MIS_EN_CAUSE, TypePartie.DEFENDEUR]:
                self.statut_procedural = StatutProcedural.MIS_EN_EXAMEN
        elif self.phase_procedure == PhaseProcedure.JUGEMENT:
            if self.type_partie == TypePartie.PREVENU:
                self.statut_procedural = StatutProcedural.PREVENU
    
    def update_from_entreprise_info(self, info: InformationEntreprise):
        """Met à jour avec les informations d'entreprise"""
        self.info_entreprise = info
        self.forme_juridique = info.forme_juridique
        self.capital_social = info.capital_social
        self.siret = info.siret
        self.siege_social = info.siege_social
        if info.representants_legaux:
            self.representant_legal = info.representants_legaux[0].get('nom', '')
        if info.rcs_numero and info.rcs_ville:
            self.rcs = f"{info.rcs_ville} {info.rcs_numero}"
        if info.siege_social:
            self.adresse = info.siege_social
        if info.code_postal:
            self.code_postal = info.code_postal
        if info.ville:
            self.ville = info.ville
    
    def get_designation_procedurale(self) -> str:
        """Retourne la désignation selon le statut procédural"""
        if self.phase_procedure == PhaseProcedure.ENQUETE_PRELIMINAIRE:
            if self.statut_procedural == StatutProcedural.MIS_EN_CAUSE:
                return f"{self.nom} (mis en cause)"
            elif self.statut_procedural == StatutProcedural.SUSPECT:
                return f"{self.nom} (suspect)"
        elif self.phase_procedure == PhaseProcedure.INSTRUCTION:
            if self.statut_procedural == StatutProcedural.MIS_EN_EXAMEN:
                return f"{self.nom} (mis en examen)"
            elif self.statut_procedural == StatutProcedural.TEMOIN_ASSISTE:
                return f"{self.nom} (témoin assisté)"
        elif self.phase_procedure == PhaseProcedure.JUGEMENT:
            if self.statut_procedural == StatutProcedural.PREVENU:
                return f"{self.nom} (prévenu)"
        
        return self.nom
    
    def get_designation_complete(self) -> str:
        """Retourne la désignation complète de la partie"""
        if self.type_personne == "morale":
            # Utiliser les infos entreprise si disponibles
            if self.info_entreprise:
                designation = self.info_entreprise.get_denomination_complete()
                if self.info_entreprise.capital_social:
                    designation += f" au capital de {self.info_entreprise.format_capital()}"
                if self.info_entreprise.get_immatriculation_complete():
                    designation += f", {self.info_entreprise.get_immatriculation_complete()}"
                if self.info_entreprise.siege_social:
                    designation += f", dont le siège social est situé {self.info_entreprise.siege_social}"
            else:
                # Fallback sur les infos manuelles
                designation = f"{self.nom}"
                if self.forme_juridique:
                    designation += f", {self.forme_juridique}"
                if self.capital_social:
                    designation += f" au capital de {self.capital_social:,.0f} euros"
                if self.rcs:
                    designation += f", RCS {self.rcs}"
                if self.siege_social:
                    designation += f", dont le siège social est situé {self.siege_social}"
            
            if self.representant_legal:
                designation += f", représentée par {self.representant_legal}"
        else:
            designation = f"{self.nom}"
            if self.prenom:
                designation = f"{self.prenom} {self.nom}"
            if self.date_naissance:
                designation += f", né(e) le {self.date_naissance.strftime('%d/%m/%Y')}"
            if self.lieu_naissance:
                designation += f" à {self.lieu_naissance}"
            if self.nationalite:
                designation += f", de nationalité {self.nationalite}"
            if self.adresse:
                designation += f", demeurant {self.adresse}"
        
        return designation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nom': self.nom,
            'type_partie': self.type_partie.value,
            'type_personne': self.type_personne,
            'phase_procedure': self.phase_procedure.value,
            'statut_procedural': self.statut_procedural.value,
            'forme_juridique': self.forme_juridique,
            'capital_social': self.capital_social,
            'rcs': self.rcs,
            'siret': self.siret,
            'siege_social': self.siege_social,
            'representant_legal': self.representant_legal,
            'date_naissance': self.date_naissance.isoformat() if self.date_naissance else None,
            'lieu_naissance': self.lieu_naissance,
            'nationalite': self.nationalite,
            'adresse': self.adresse,
            'avocat': self.avocat,
            'metadata': self.metadata,
            'designation_complete': self.get_designation_complete(),
            'designation_procedurale': self.get_designation_procedurale(),
            'has_entreprise_info': self.info_entreprise is not None
        }

# Fonction helper pour créer une partie avec lookup automatique
def create_partie_from_name_with_lookup(
    nom: str,
    type_partie: TypePartie = TypePartie.DEMANDEUR,
    phase: Optional[PhaseProcedure] = None
) -> Partie:
    """
    Crée une partie et détermine automatiquement si c'est une personne morale ou physique
    
    Args:
        nom: Nom de la partie
        type_partie: Type de partie (demandeur, défendeur, etc.)
        phase: Phase de la procédure
        
    Returns:
        Partie créée
    """
    # Patterns pour identifier une personne morale
    patterns_morales = [
        r'\b(SAS|SARL|SA|SCI|EURL|SNC|GIE|ASSOCIATION|FONDATION)\b',
        r'\b(SOCIETE|COMPAGNIE|ENTREPRISE|GROUPE|HOLDING)\b',
        r'\b(STE|CIE|ETS|ETABLISSEMENTS)\b',
    ]
    
    # Patterns pour identifier une personne physique
    patterns_physiques = [
        r'^(M\.|Mme|Mlle|Me|Dr|Pr)\s+',
        r'\b(Monsieur|Madame|Mademoiselle|Maître|Docteur|Professeur)\b',
    ]
    
    # Déterminer le type
    type_personne = "physique"
    
    # Vérifier les patterns de personne morale
    for pattern in patterns_morales:
        if re.search(pattern, nom, re.IGNORECASE):
            type_personne = "morale"
            break
    
    # Si pas trouvé comme morale, vérifier si c'est explicitement physique
    if type_personne == "physique":
        for pattern in patterns_physiques:
            if re.search(pattern, nom, re.IGNORECASE):
                break
        else:
            # Si le nom est en majuscules et contient certains mots, c'est probablement une société
            if nom.isupper() and len(nom.split()) > 1:
                type_personne = "morale"
    
    # Créer la partie
    partie = Partie(
        nom=nom,
        type_partie=type_partie,
        type_personne=type_personne,
        phase_procedure=phase or PhaseProcedure.ENQUETE_PRELIMINAIRE
    )
    
    # Pour une personne physique, essayer d'extraire le prénom
    if type_personne == "physique":
        # Retirer les civilités
        nom_clean = re.sub(r'^(M\.|Mme|Mlle|Me|Dr|Pr|Monsieur|Madame|Mademoiselle|Maître|Docteur|Professeur)\s+', '', nom, flags=re.IGNORECASE)
        parts = nom_clean.split()
        if len(parts) >= 2:
            partie.prenom = parts[0]
            partie.nom = ' '.join(parts[1:])
    
    return partie

# ========== STYLES ET TEMPLATES ==========

@dataclass
class DocumentTemplate:
    """Template de document juridique"""
    id: str
    name: str
    type: DocumentType
    structure: List[str]
    style: StyleRedaction
    category: str = "Autre"
    description: str = ""
    variables: List[str] = field(default_factory=list)
    is_builtin: bool = True
    usage_count: int = 0
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    
    # Style personnalisé appris
    custom_style: Optional[StyleConfig] = None
    
    def __post_init__(self):
        self.extract_variables()
    
    def extract_variables(self):
        """Extrait les variables du template"""
        variables = set()
        for line in self.structure:
            # Chercher les patterns [Variable]
            matches = re.findall(r'\[([^\]]+)\]', line)
            variables.update(matches)
        self.variables = sorted(list(variables))
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Valide les données par rapport au template"""
        missing = []
        for field in self.required_fields:
            if field not in data or not data[field]:
                missing.append(field)
        return len(missing) == 0, missing

@dataclass
class LetterheadTemplate:
    """Template pour papier en-tête"""
    name: str
    header_content: str
    footer_content: str
    logo_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Styles avancés
    header_style: Dict[str, Any] = field(default_factory=dict)
    footer_style: Dict[str, Any] = field(default_factory=dict)
    page_margins: Dict[str, float] = field(default_factory=dict)
    font_family: str = "Arial"
    font_size: int = 11
    line_spacing: float = 1.5
    
    def __post_init__(self):
        if not self.header_style:
            self.header_style = {
                'text-align': 'center',
                'font-weight': 'bold',
                'margin-bottom': '20px'
            }
        
        if not self.footer_style:
            self.footer_style = {
                'text-align': 'center',
                'font-size': '10px',
                'margin-top': '20px'
            }
        
        if not self.page_margins:
            self.page_margins = {
                'top': 2.5,
                'bottom': 2.5,
                'left': 2.5,
                'right': 2.5
            }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'header_content': self.header_content,
            'footer_content': self.footer_content,
            'logo_path': self.logo_path,
            'created_at': self.created_at.isoformat(),
            'header_style': self.header_style,
            'footer_style': self.footer_style,
            'page_margins': self.page_margins,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'line_spacing': self.line_spacing
        }

# ========== INFRACTIONS ==========

@dataclass
class InfractionIdentifiee:
    """Infraction identifiée dans les documents"""
    type: InfractionAffaires
    description: str
    elements_constitutifs: List[str] = field(default_factory=list)
    preuves: List[str] = field(default_factory=list)
    articles_code_penal: List[str] = field(default_factory=list)
    sanctions_encourues: Dict[str, str] = field(default_factory=dict)
    personnes_impliquees: List[str] = field(default_factory=list)
    prescription: Optional[str] = None
    gravite: int = 5  # 1-10
    montant_prejudice: Optional[float] = None
    circonstances_aggravantes: List[str] = field(default_factory=list)
    date_faits: Optional[datetime] = None
    lieu_faits: Optional[str] = None
    
    def __post_init__(self):
        # Ajouter automatiquement les articles selon le type d'infraction
        if not self.articles_code_penal:
            self.articles_code_penal = self.get_articles_applicables()
    
    def get_articles_applicables(self) -> List[str]:
        """Retourne les articles applicables selon le type d'infraction"""
        articles_map = {
            InfractionAffaires.ESCROQUERIE: ["313-1 Code pénal"],
            InfractionAffaires.ABUS_CONFIANCE: ["314-1 Code pénal"],
            InfractionAffaires.ABUS_BIENS_SOCIAUX: ["L241-3 Code de commerce", "L242-6 Code de commerce"],
            InfractionAffaires.FAUX_USAGE_FAUX: ["441-1 Code pénal"],
            InfractionAffaires.CORRUPTION: ["432-11 Code pénal", "433-1 Code pénal"],
            InfractionAffaires.TRAFIC_INFLUENCE: ["432-11 Code pénal", "433-2 Code pénal"],
            InfractionAffaires.FAVORITISME: ["432-14 Code pénal"],
            InfractionAffaires.PRISE_ILLEGALE_INTERETS: ["432-12 Code pénal"],
            InfractionAffaires.BLANCHIMENT: ["324-1 Code pénal"],
            InfractionAffaires.FRAUDE_FISCALE: ["1741 Code général des impôts"],
            InfractionAffaires.TRAVAIL_DISSIMULE: ["L8221-3 Code du travail"],
            InfractionAffaires.MARCHANDAGE: ["L8231-1 Code du travail"],
            InfractionAffaires.ENTRAVE: ["L2328-1 Code du travail"],
            InfractionAffaires.BANQUEROUTE: ["L654-2 Code de commerce"],
            InfractionAffaires.RECEL: ["321-1 Code pénal"],
            InfractionAffaires.DELIT_INITIE: ["L465-1 Code monétaire et financier"],
            InfractionAffaires.MANIPULATION_COURS: ["L465-3-1 Code monétaire et financier"]
        }
        return articles_map.get(self.type, [])
    
    def get_sanctions_maximales(self) -> Dict[str, str]:
        """Retourne les sanctions maximales encourues"""
        sanctions_map = {
            InfractionAffaires.ESCROQUERIE: {
                "prison": "5 ans",
                "amende": "375 000 €",
                "personnes_morales": "1 875 000 €"
            },
            InfractionAffaires.ABUS_BIENS_SOCIAUX: {
                "prison": "5 ans",
                "amende": "375 000 €",
                "interdictions": "Interdiction de gérer"
            },
            InfractionAffaires.CORRUPTION: {
                "prison": "10 ans",
                "amende": "1 000 000 €",
                "complementaires": "Interdiction des droits civiques"
            }
            # Ajouter d'autres infractions selon les besoins
        }
        return sanctions_map.get(self.type, {"prison": "Variable", "amende": "Variable"})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'type': self.type.value,
            'description': self.description,
            'elements_constitutifs': self.elements_constitutifs,
            'preuves': self.preuves,
            'articles_code_penal': self.articles_code_penal,
            'sanctions_encourues': self.sanctions_encourues or self.get_sanctions_maximales(),
            'personnes_impliquees': self.personnes_impliquees,
            'prescription': self.prescription,
            'gravite': self.gravite,
            'montant_prejudice': self.montant_prejudice,
            'circonstances_aggravantes': self.circonstances_aggravantes,
            'date_faits': self.date_faits.isoformat() if self.date_faits else None,
            'lieu_faits': self.lieu_faits
        }

# ========== PIÈCES ET PROCÉDURE (VERSION FUSIONNÉE) ==========

@dataclass
class PieceSelectionnee:
    """Représente une pièce sélectionnée pour un bordereau - VERSION FUSIONNÉE"""
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
    source_references: List['SourceReference'] = field(default_factory=list)
    facts_prouve: List['FactWithSource'] = field(default_factory=list)
    force_probante: ForceProbante = ForceProbante.NORMALE
    communicable: bool = True
    confidentiel: bool = False
    
    # Lien direct vers la source et footnote
    source_link: Optional[str] = None
    footnote_text: Optional[str] = None
    
    # Métadonnées techniques
    hash_document: Optional[str] = None
    nature: NaturePiece = NaturePiece.COPIE
    document_source: Optional[Document] = None  # Document source s'il existe
    
    def __post_init__(self):
        """Validation et formatage"""
        if self.pertinence < 0:
            self.pertinence = 0
        elif self.pertinence > 1:
            self.pertinence = 1
        
        # Générer une cote si non fournie
        if not self.cote:
            prefix = self.categorie[:1].upper() if self.categorie else "P"
            self.cote = f"{prefix}-{self.numero:03d}"
        
        # Générer le footnote text si non fourni
        if not self.footnote_text:
            self.footnote_text = f"Pièce n°{self.numero} : {self.titre}"
            if self.date:
                self.footnote_text += f" du {self.date.strftime('%d/%m/%Y')}"
    
    def add_source_reference(self, source_ref: 'SourceReference'):
        """Ajoute une référence source"""
        self.source_references.append(source_ref)
        # Mettre à jour le lien source
        if not self.source_link:
            self.source_link = source_ref.get_link()
    
    def add_fact_prouve(self, fact: 'FactWithSource'):
        """Ajoute un fait que cette pièce prouve"""
        self.facts_prouve.append(fact)
    
    def get_importance_score(self) -> float:
        """Calcule un score d'importance combiné"""
        base_score = self.pertinence
        
        # Bonus pour force probante
        if self.force_probante == ForceProbante.FORTE:
            base_score += 0.2
        elif self.force_probante == ForceProbante.IRREFRAGABLE:
            base_score += 0.3
        
        # Bonus pour nombre de faits prouvés
        base_score += min(len(self.facts_prouve) * 0.05, 0.2)
        
        # Bonus pour nature de la pièce
        if self.nature == NaturePiece.ORIGINAL:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def get_formatted_reference(self) -> str:
        """Retourne une référence formatée avec lien et footnote"""
        if self.source_link:
            return f"[{self.cote}]({self.source_link})[^{self.numero}]"
        else:
            return f"{self.cote}[^{self.numero}]"
    
    def get_footnote(self) -> str:
        """Retourne la footnote formatée"""
        return f"[^{self.numero}]: {self.footnote_text}"
    
    def marquer_contestee(self, motif: str):
        """Marque la pièce comme contestée"""
        self.confidentiel = True
        self.communicable = False
        self.description += f" [CONTESTÉE: {motif}]"
    
    def to_bordereau_entry(self) -> Dict[str, Any]:
        """Formate pour un bordereau"""
        return {
            'numero': self.numero,
            'cote': self.cote,
            'intitule': self.titre,
            'nature': self.nature.value,
            'date': self.date.strftime('%d/%m/%Y') if self.date else "Non datée",
            'pages': self.pages,
            'communicable': "Oui" if self.communicable else "Non",
            'observations': self.description,
            'reference_formatee': self.get_formatted_reference(),
            'footnote': self.get_footnote()
        }
    
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
            'cote': self.cote,
            'source_references': [s.get_citation() for s in self.source_references],
            'facts_count': len(self.facts_prouve),
            'force_probante': self.force_probante.value,
            'communicable': self.communicable,
            'confidentiel': self.confidentiel,
            'importance_score': self.get_importance_score(),
            'source_link': self.source_link,
            'footnote_text': self.footnote_text,
            'nature': self.nature.value,
            'hash_document': self.hash_document
        }
    
    @staticmethod
    def create_piece_from_document(doc: Document, numero: int, 
                                   categorie: Optional[str] = None,
                                   pertinence: float = 0.5,
                                   force_probante: Optional[ForceProbante] = None,
                                   nature: Optional[NaturePiece] = None) -> 'PieceSelectionnee':
        """
        Crée une pièce à partir d'un document
        
        Args:
            doc: Le document source
            numero: Le numéro de la pièce
            categorie: La catégorie de la pièce (optionnel)
            pertinence: Score de pertinence (0-1)
            force_probante: Force probante de la pièce
            nature: Nature de la pièce (original, copie, etc.)
            
        Returns:
            Une nouvelle PieceSelectionnee
        """
        # Déterminer la catégorie
        if not categorie:
            # Essayer de déduire la catégorie du document
            if hasattr(doc, 'category') and doc.category:
                categorie = doc.category
            elif hasattr(doc, 'metadata') and doc.metadata:
                categorie = doc.metadata.get('category', 'Autre')
            else:
                categorie = 'Autre'
        
        # Extraire la date
        date = None
        if hasattr(doc, 'metadata') and doc.metadata:
            date_value = doc.metadata.get('date')
            if date_value:
                if isinstance(date_value, datetime):
                    date = date_value
                elif isinstance(date_value, str):
                    try:
                        date = datetime.fromisoformat(date_value)
                    except:
                        pass
        
        # Si c'est un DocumentJuridique, utiliser date_document
        if hasattr(doc, 'date_document') and doc.date_document:
            date = doc.date_document
        
        # Créer la description
        max_desc_length = 200
        if len(doc.content) > max_desc_length:
            description = doc.content[:max_desc_length].strip() + '...'
        else:
            description = doc.content.strip()
        
        # Déterminer le format et la taille
        format_doc = None
        taille = None
        pages = None
        
        if hasattr(doc, 'metadata') and doc.metadata:
            format_doc = doc.metadata.get('mime_type') or doc.metadata.get('format')
            taille = doc.metadata.get('file_size')
            pages = doc.metadata.get('pages') or doc.metadata.get('page_count')
        
        # Créer la pièce
        piece = PieceSelectionnee(
            numero=numero,
            titre=doc.title,
            description=description,
            categorie=categorie,
            date=date,
            source=doc.source,
            pertinence=pertinence,
            pages=pages,
            format=format_doc,
            taille=taille,
            source_link=f"#doc_{doc.id}",
            force_probante=force_probante or ForceProbante.NORMALE,
            nature=nature or NaturePiece.COPIE,
            document_source=doc
        )
        
        # Ajouter une référence source si possible
        if hasattr(doc, 'id') and hasattr(doc, 'title'):
            source_ref = SourceReference(
                document_id=doc.id,
                document_title=doc.title,
                confidence=1.0
            )
            piece.add_source_reference(source_ref)
        
        return piece

@dataclass
class BordereauPieces:
    """Bordereau de pièces avec traçabilité complète - VERSION FUSIONNÉE"""
    id: str
    titre: str
    affaire: str
    date_creation: datetime = field(default_factory=datetime.now)
    pieces: List[PieceSelectionnee] = field(default_factory=list)
    facts_inventory: List['FactWithSource'] = field(default_factory=list)
    argument_structure: Optional['ArgumentStructure'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    destinataire: Optional[str] = None
    expediteur: Optional[str] = None
    
    # Champs additionnels pour la traçabilité
    source_tracker: Optional['SourceTracker'] = None
    timeline: List[Tuple[datetime, str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_piece_with_facts(self, piece: PieceSelectionnee, facts: List['FactWithSource']):
        """Ajoute une pièce avec les faits qu'elle prouve"""
        piece.facts_prouve = facts
        self.pieces.append(piece)
        self.facts_inventory.extend(facts)
        
        # Ajouter à la timeline
        self.timeline.append((
            datetime.now(),
            "piece_ajoutee",
            f"Ajout de la pièce {piece.cote}: {piece.titre}"
        ))
    
    def add_piece(self, piece: PieceSelectionnee):
        """Ajoute une pièce simple"""
        self.pieces.append(piece)
        self.timeline.append((
            datetime.now(),
            "piece_ajoutee",
            f"Ajout de la pièce {piece.cote}: {piece.titre}"
        ))
    
    def get_facts_by_category(self, category: str) -> List['FactWithSource']:
        """Retourne tous les faits d'une catégorie"""
        return [f for f in self.facts_inventory if f.category == category]
    
    def organize_by_category(self) -> Dict[str, List[PieceSelectionnee]]:
        """Organise les pièces par catégorie"""
        organized = {}
        for piece in self.pieces:
            if piece.categorie not in organized:
                organized[piece.categorie] = []
            organized[piece.categorie].append(piece)
        return organized
    
    def verifier_completude(self) -> Dict[str, Any]:
        """Vérifie la complétude du bordereau"""
        completude = {
            'complet': True,
            'manquants': [],
            'alertes': []
        }
        
        # Vérifier les pièces essentielles selon l'affaire
        categories_presentes = set(p.categorie for p in self.pieces)
        categories_essentielles = ['Procédure', 'Expertise', 'Contrats']
        
        for cat in categories_essentielles:
            if cat not in categories_presentes:
                completude['manquants'].append(f"Aucune pièce de type {cat}")
                completude['complet'] = False
        
        # Vérifier les pièces non communicables
        pieces_non_comm = [p for p in self.pieces if not p.communicable]
        if pieces_non_comm:
            completude['alertes'].append(
                f"{len(pieces_non_comm)} pièces non communicables"
            )
        
        return completude
    
    def generate_summary(self) -> Dict[str, Any]:
        """Génère un résumé du bordereau"""
        return {
            'id': self.id,
            'titre': self.titre,
            'affaire': self.affaire,
            'date': self.date_creation.isoformat(),
            'total_pieces': len(self.pieces),
            'total_facts': len(self.facts_inventory),
            'facts_by_category': {
                cat: len(self.get_facts_by_category(cat))
                for cat in set(f.category for f in self.facts_inventory)
            },
            'pieces_by_category': {
                cat: len(pieces) 
                for cat, pieces in self.organize_by_category().items()
            },
            'sources_count': len(set(
                s.document_id 
                for f in self.facts_inventory 
                for s in f.sources
            )),
            'completude': self.verifier_completude()
        }
    
    def export_to_text(self) -> str:
        """Exporte le bordereau au format texte"""
        lines = [
            f"BORDEREAU DE COMMUNICATION DE PIÈCES",
            f"",
            f"AFFAIRE : {self.affaire}",
            f"DATE : {self.date_creation.strftime('%d/%m/%Y')}",
            f"NOMBRE DE PIÈCES : {len(self.pieces)}",
            f"",
            f"{'='*60}",
            f""
        ]
        
        # Grouper par catégorie
        by_category = self.organize_by_category()
        
        for category, pieces in sorted(by_category.items()):
            lines.append(f"\n{category.upper()} ({len(pieces)} pièces)")
            lines.append("-" * 40)
            
            for piece in sorted(pieces, key=lambda p: p.numero):
                lines.append(f"\n{piece.cote} - {piece.titre}")
                if piece.description:
                    lines.append(f"   Description : {piece.description}")
                if piece.date:
                    lines.append(f"   Date : {piece.date.strftime('%d/%m/%Y')}")
                if piece.pages:
                    lines.append(f"   Pages : {piece.pages}")
                if piece.facts_prouve:
                    lines.append(f"   Établit : {len(piece.facts_prouve)} fait(s)")
                lines.append(f"   Force probante : {piece.force_probante.value}")
                lines.append(f"   Nature : {piece.nature.value}")
                if piece.source_link:
                    lines.append(f"   Source : {piece.source_link}")
                if not piece.communicable:
                    lines.append(f"   ⚠️ NON COMMUNICABLE")
        
        lines.extend([
            f"",
            f"{'='*60}",
            f"",
            f"Je certifie que les pièces communiquées sont conformes aux originaux.",
            f"",
            f"Fait le {datetime.now().strftime('%d/%m/%Y')}",
            f"",
            f"{self.expediteur or '[Signature]'}"
        ])
        
        return "\n".join(lines)
    
    def export_to_markdown_with_links(self) -> str:
        """Exporte le bordereau au format Markdown avec liens et footnotes"""
        lines = [
            f"# BORDEREAU DE COMMUNICATION DE PIÈCES",
            f"",
            f"**AFFAIRE :** {self.affaire}  ",
            f"**DATE :** {self.date_creation.strftime('%d/%m/%Y')}  ",
            f"**NOMBRE DE PIÈCES :** {len(self.pieces)}",
            f"",
            f"---",
            f""
        ]
        
        # Vérification de complétude
        completude = self.verifier_completude()
        if not completude['complet']:
            lines.append("## ⚠️ ALERTES")
            for alerte in completude['manquants']:
                lines.append(f"- {alerte}")
            lines.append("")
        
        # Grouper par catégorie
        by_category = self.organize_by_category()
        
        for category, pieces in sorted(by_category.items()):
            lines.append(f"## {category.upper()} ({len(pieces)} pièces)")
            lines.append("")
            
            # Tableau pour cette catégorie
            lines.append("| N° | Cote | Titre | Date | Pages | Force probante | Communicable |")
            lines.append("|---|------|-------|------|-------|----------------|--------------|")
            
            for piece in sorted(pieces, key=lambda p: p.numero):
                comm = "✅" if piece.communicable else "❌"
                date_str = piece.date.strftime('%d/%m/%Y') if piece.date else "-"
                pages_str = str(piece.pages) if piece.pages else "-"
                
                lines.append(
                    f"| {piece.numero} | {piece.get_formatted_reference()} | "
                    f"{piece.titre} | {date_str} | {pages_str} | "
                    f"{piece.force_probante.value} | {comm} |"
                )
            
            lines.append("")
        
        # Statistiques
        lines.extend([
            f"## 📊 Statistiques",
            f"",
            f"- **Pièces originales :** {sum(1 for p in self.pieces if p.nature == NaturePiece.ORIGINAL)}",
            f"- **Pièces avec force probante forte :** {sum(1 for p in self.pieces if p.force_probante in [ForceProbante.FORTE, ForceProbante.IRREFRAGABLE])}",
            f"- **Faits établis :** {len(self.facts_inventory)}",
            f""
        ])
        
        # Ajouter les footnotes
        lines.extend([
            f"---",
            f"",
            f"## Notes de bas de page",
            f""
        ])
        
        for piece in sorted(self.pieces, key=lambda p: p.numero):
            lines.append(piece.get_footnote())
        
        lines.extend([
            f"",
            f"---",
            f"",
            f"*Je certifie que les pièces communiquées sont conformes aux originaux.*",
            f"",
            f"Fait le {datetime.now().strftime('%d/%m/%Y')}",
            f"",
            f"**{self.expediteur or '[Signature]'}**"
        ])
        
        return "\n".join(lines)
    
    def export_with_full_traceability(self) -> str:
        """Exporte avec traçabilité complète des sources"""
        content = self.export_to_markdown_with_links()
        
        if self.source_tracker:
            lines = [content, "", "## 🔍 Traçabilité complète", ""]
            
            for piece in self.pieces:
                if piece.source_references:
                    lines.append(f"### {piece.cote} - {piece.titre}")
                    lines.append("")
                    lines.append("**Sources documentaires:**")
                    
                    for ref in piece.source_references:
                        lines.append(f"- {ref.get_citation()}")
                        if ref.excerpt:
                            lines.append(f"  > *{ref.excerpt}*")
                    
                    if piece.facts_prouve:
                        lines.append("")
                        lines.append("**Faits établis:**")
                        for fact in piece.facts_prouve:
                            lines.append(f"- {fact.content}")
                    
                    lines.append("")
            
            content = "\n".join(lines)
        
        return content

@dataclass
class PieceVersee:
    """Pièce versée aux débats - Classe simplifiée pour compatibilité"""
    id: str
    numero_ordre: int
    cote: str
    intitule: str
    nature: str
    date_piece: Optional[datetime] = None
    date_versement: datetime = field(default_factory=datetime.now)
    partie_versante: str = ""
    communicable: bool = True
    confidentiel: bool = False
    
    def to_piece_selectionnee(self) -> PieceSelectionnee:
        """Convertit en PieceSelectionnee pour compatibilité"""
        return PieceSelectionnee(
            numero=self.numero_ordre,
            titre=self.intitule,
            cote=self.cote,
            date=self.date_piece,
            communicable=self.communicable,
            confidentiel=self.confidentiel,
            nature=NaturePiece(self.nature) if self.nature in [n.value for n in NaturePiece] else NaturePiece.COPIE
        )

@dataclass
class ElementProcedure:
    """Élément de procédure avec traçabilité"""
    id: str
    type: str
    intitule: str
    date: datetime
    auteur: str
    destinataire: Optional[str] = None
    delai: Optional[str] = None
    date_signification: Optional[datetime] = None
    huissier: Optional[str] = None
    source_legale: List[str] = field(default_factory=list)
    pieces_jointes: List[PieceSelectionnee] = field(default_factory=list)
    source_references: List['SourceReference'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"proc_{self.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def is_dans_delai(self) -> bool:
        """Vérifie si l'acte est dans les délais"""
        # Logique de vérification des délais selon le type d'acte
        return True  # À implémenter selon les règles de procédure
    
    def get_full_reference(self) -> str:
        """Retourne la référence complète de l'acte"""
        ref = f"{self.type.upper()} du {self.date.strftime('%d/%m/%Y')}"
        if self.auteur:
            ref += f" par {self.auteur}"
        return ref

@dataclass
class ChaineProcedure:
    """Chaîne complète d'actes de procédure"""
    id: str
    affaire_id: str
    elements: List[ElementProcedure] = field(default_factory=list)
    pieces_versees: List[PieceSelectionnee] = field(default_factory=list)
    timeline: List[Tuple[datetime, str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"chaine_{self.affaire_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_element(self, element: ElementProcedure):
        """Ajoute un élément à la chaîne"""
        self.elements.append(element)
        self.timeline.append((element.date, element.type, element.get_full_reference()))
        self.timeline.sort(key=lambda x: x[0])
    
    def add_piece(self, piece: PieceSelectionnee):
        """Ajoute une pièce versée"""
        self.pieces_versees.append(piece)
        self.timeline.append((
            piece.date or datetime.now(),
            "piece_versee",
            f"Pièce {piece.cote}: {piece.titre}"
        ))
        self.timeline.sort(key=lambda x: x[0])
    
    def verifier_regularite(self) -> Dict[str, Any]:
        """Vérifie la régularité de la procédure"""
        irregularites = []
        
        # Vérifier les délais
        for element in self.elements:
            if not element.is_dans_delai():
                irregularites.append(f"Délai dépassé pour {element.get_full_reference()}")
        
        # Vérifier la communication des pièces
        pieces_non_communiquees = [p for p in self.pieces_versees if not p.communicable]
        if pieces_non_communiquees:
            irregularites.append(f"{len(pieces_non_communiquees)} pièces non communiquées")
        
        return {
            'reguliere': len(irregularites) == 0,
            'irregularites': irregularites,
            'nombre_actes': len(self.elements),
            'nombre_pieces': len(self.pieces_versees)
        }

# ========== TRAÇABILITÉ ET SOURCES ==========

@dataclass
class SourceReference:
    """Référence à une source documentaire"""
    document_id: str
    document_title: str
    page: Optional[int] = None
    paragraph: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    excerpt: Optional[str] = None
    confidence: float = 1.0
    
    def get_citation(self) -> str:
        """Retourne une citation formatée"""
        citation = f"{self.document_title}"
        if self.page:
            citation += f", p. {self.page}"
        if self.paragraph:
            citation += f", §{self.paragraph}"
        return citation
    
    def get_link(self) -> str:
        """Retourne un lien formaté vers la source"""
        link_parts = [f"source:{self.document_id}"]
        if self.page:
            link_parts.append(f"page_{self.page}")
        if self.paragraph:
            link_parts.append(f"para_{self.paragraph}")
        return "#".join(link_parts)

@dataclass
class FactWithSource:
    """Fait ou argument avec sa source"""
    id: str
    content: str
    category: str
    sources: List[SourceReference] = field(default_factory=list)
    importance: int = 5  # 1-10
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    
    def __post_init__(self):
        if not self.id:
            self.id = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def add_source(self, source: SourceReference):
        """Ajoute une source au fait"""
        self.sources.append(source)
        self.verified = True
        # Ajuster le score de confiance
        self.confidence_score = min(1.0, self.confidence_score + 0.1)
    
    def get_formatted_content(self) -> str:
        """Retourne le contenu formaté avec liens sources"""
        if not self.sources:
            return self.content
        
        # Ajouter les numéros de référence
        refs = [f"[{i+1}]" for i in range(len(self.sources))]
        return f"{self.content} {' '.join(refs)}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'category': self.category,
            'sources': [{'document_id': s.document_id, 
                        'citation': s.get_citation(),
                        'excerpt': s.excerpt,
                        'confidence': s.confidence} for s in self.sources],
            'importance': self.importance,
            'verified': self.verified,
            'created_at': self.created_at.isoformat(),
            'tags': self.tags,
            'confidence_score': self.confidence_score
        }

@dataclass
class ArgumentStructure:
    """Structure d'argumentation avec sources"""
    id: str
    title: str
    thesis: str  # Thèse principale
    facts: List[FactWithSource] = field(default_factory=list)
    sub_arguments: List['ArgumentStructure'] = field(default_factory=list)
    conclusion: Optional[str] = None
    strength: float = 0.5  # Force de l'argument 0-1
    counter_arguments: List['ArgumentStructure'] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"arg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def add_fact(self, fact: FactWithSource):
        """Ajoute un fait à l'argumentation"""
        self.facts.append(fact)
        # Recalculer la force
        self.recalculate_strength()
    
    def add_sub_argument(self, sub_arg: 'ArgumentStructure'):
        """Ajoute un sous-argument"""
        self.sub_arguments.append(sub_arg)
        self.recalculate_strength()
    
    def recalculate_strength(self):
        """Recalcule la force de l'argument"""
        base_strength = 0.5
        
        # Bonus pour les faits vérifiés
        verified_facts = sum(1 for f in self.facts if f.verified)
        base_strength += verified_facts * 0.05
        
        # Bonus pour les sous-arguments
        if self.sub_arguments:
            avg_sub_strength = sum(s.strength for s in self.sub_arguments) / len(self.sub_arguments)
            base_strength += avg_sub_strength * 0.2
        
        # Malus pour les contre-arguments
        if self.counter_arguments:
            avg_counter_strength = sum(c.strength for c in self.counter_arguments) / len(self.counter_arguments)
            base_strength -= avg_counter_strength * 0.15
        
        self.strength = max(0.1, min(1.0, base_strength))
    
    def get_all_sources(self) -> List[SourceReference]:
        """Récupère toutes les sources utilisées"""
        sources = []
        for fact in self.facts:
            sources.extend(fact.sources)
        for sub_arg in self.sub_arguments:
            sources.extend(sub_arg.get_all_sources())
        return sources
    
    def to_outline(self, level: int = 0) -> str:
        """Génère un plan de l'argumentation"""
        indent = "  " * level
        lines = [f"{indent}• {self.title} (force: {self.strength:.2f})"]
        
        if self.thesis:
            lines.append(f"{indent}  Thèse: {self.thesis}")
        
        if self.facts:
            lines.append(f"{indent}  Faits ({len(self.facts)}):")
            for fact in self.facts[:3]:  # Limiter l'affichage
                lines.append(f"{indent}    - {fact.content[:80]}...")
        
        if self.sub_arguments:
            lines.append(f"{indent}  Arguments ({len(self.sub_arguments)}):")
            for sub in self.sub_arguments:
                lines.extend(sub.to_outline(level + 2).split('\n'))
        
        return '\n'.join(lines)

@dataclass
class SourceTracker:
    """Suivi des sources documentaires pour la traçabilité complète"""
    sources: Dict[str, SourceReference] = field(default_factory=dict)
    documents: Dict[str, Document] = field(default_factory=dict)
    facts: List[FactWithSource] = field(default_factory=list)
    references_map: Dict[str, List[str]] = field(default_factory=dict)  # doc_id -> [fact_ids]
    
    def add_source(self, source_ref: SourceReference):
        """Ajoute une référence source"""
        self.sources[source_ref.document_id] = source_ref
    
    def add_document(self, document: Document):
        """Ajoute un document au tracker"""
        self.documents[document.id] = document
    
    def add_fact(self, fact: FactWithSource):
        """Ajoute un fait avec ses sources"""
        self.facts.append(fact)
        # Mettre à jour la carte des références
        for source in fact.sources:
            if source.document_id not in self.references_map:
                self.references_map[source.document_id] = []
            self.references_map[source.document_id].append(fact.id)
    
    def get_source_for_document(self, doc_id: str) -> Optional[SourceReference]:
        """Récupère la source pour un document"""
        return self.sources.get(doc_id)
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Récupère un document par son ID"""
        return self.documents.get(doc_id)
    
    def get_facts_for_document(self, doc_id: str) -> List[FactWithSource]:
        """Récupère tous les faits sourcés par un document"""
        fact_ids = self.references_map.get(doc_id, [])
        return [f for f in self.facts if f.id in fact_ids]
    
    def get_all_sources_for_facts(self, facts: List[FactWithSource]) -> List[SourceReference]:
        """Récupère toutes les sources pour une liste de faits"""
        sources = []
        for fact in facts:
            sources.extend(fact.sources)
        # Dédupliquer par document_id
        unique_sources = {}
        for source in sources:
            unique_sources[source.document_id] = source
        return list(unique_sources.values())
    
    def generate_citation_report(self) -> Dict[str, Any]:
        """Génère un rapport sur les citations"""
        return {
            'total_sources': len(self.sources),
            'total_documents': len(self.documents),
            'total_facts': len(self.facts),
            'documents_with_facts': len(self.references_map),
            'average_facts_per_document': sum(len(facts) for facts in self.references_map.values()) / max(len(self.references_map), 1),
            'most_cited_documents': sorted(
                [(doc_id, len(fact_ids)) for doc_id, fact_ids in self.references_map.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

# ========== TIMELINE ==========

@dataclass
class TimelineEvent:
    """Événement pour la timeline"""
    date: datetime
    titre: str
    description: str
    type: str  # audience, deadline, rdv, etc.
    importance: str  # haute, moyenne, basse
    documents_lies: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    lieu: str = ""
    statut: str = "à venir"  # passé, à venir, en cours
    
    # Champs additionnels pour compatibilité
    actors: List[str] = field(default_factory=list)
    location: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Synchroniser les champs pour compatibilité
        if self.participants and not self.actors:
            self.actors = self.participants
        elif self.actors and not self.participants:
            self.participants = self.actors
            
        if self.lieu and not self.location:
            self.location = self.lieu
        elif self.location and not self.lieu:
            self.lieu = self.location
            
        if self.type and not self.category:
            self.category = self.type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'date': self.date.isoformat(),
            'titre': self.titre,
            'description': self.description,
            'type': self.type,
            'importance': self.importance,
            'documents_lies': self.documents_lies,
            'participants': self.participants,
            'lieu': self.lieu,
            'statut': self.statut,
            'actors': self.actors,
            'location': self.location,
            'category': self.category,
            'source': self.source,
            'evidence': self.evidence,
            'related_events': self.related_events,
            'metadata': self.metadata
        }

# ========== RECHERCHE ==========

@dataclass
class SearchResult:
    """Résultat de recherche enrichi avec métadonnées et suggestions"""
    documents: List[Document]
    query: str
    total_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    search_duration_ms: Optional[int] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation post-initialisation"""
        # S'assurer que total_count est cohérent
        if self.total_count < len(self.documents):
            self.total_count = len(self.documents)
    
    def get_facet(self, facet_name: str) -> Dict[str, int]:
        """Récupère une facette spécifique"""
        return self.facets.get(facet_name, {})
    
    def get_top_documents(self, n: int = 10) -> List[Document]:
        """Retourne les n premiers documents"""
        return self.documents[:n]
    
    def has_results(self) -> bool:
        """Vérifie s'il y a des résultats"""
        return len(self.documents) > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les résultats"""
        stats = {
            'total': self.total_count,
            'returned': len(self.documents),
            'has_facets': bool(self.facets),
            'has_suggestions': bool(self.suggestions),
            'search_duration_ms': self.search_duration_ms
        }
        
        # Statistiques sur les scores si disponibles
        if self.documents:
            scores = [doc.metadata.get('score', 0) for doc in self.documents if hasattr(doc, 'metadata')]
            if scores:
                stats['avg_score'] = sum(scores) / len(scores)
                stats['max_score'] = max(scores)
                stats['min_score'] = min(scores)
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'query': self.query,
            'total_count': self.total_count,
            'document_count': len(self.documents),
            'timestamp': self.timestamp.isoformat(),
            'facets': self.facets,
            'suggestions': self.suggestions,
            'search_duration_ms': self.search_duration_ms,
            'filters_applied': self.filters_applied,
            'statistics': self.get_statistics()
        }

# ========== ANALYSE ET RÉDACTION ==========

@dataclass
class AnalysisResult:
    """Résultat d'analyse IA enrichi"""
    type: str  # risk_analysis, compliance, strategy, general, infractions
    content: str
    query: str
    document_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    provider: Optional[str] = None
    confidence: float = 0.8
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    infractions_identifiees: List[InfractionIdentifiee] = field(default_factory=list)
    risk_assessment: Optional[Dict[str, Any]] = None
    compliance_gaps: List[str] = field(default_factory=list)
    strategic_options: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_key_finding(self, finding: str, source: Optional[str] = None):
        """Ajoute une conclusion clé"""
        self.key_findings.append(finding)
        if source:
            self.sources.append(source)
    
    def add_recommendation(self, recommendation: str, priority: int = 5):
        """Ajoute une recommandation"""
        self.recommendations.append({
            'text': recommendation,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_executive_summary(self) -> str:
        """Génère un résumé exécutif"""
        summary = []
        
        # Type d'analyse
        type_labels = {
            'risk_analysis': "Analyse des risques",
            'compliance': "Analyse de conformité",
            'strategy': "Analyse stratégique",
            'infractions': "Analyse des infractions",
            'general_analysis': "Analyse générale"
        }
        summary.append(f"**Type:** {type_labels.get(self.type, self.type)}")
        
        # Statistiques
        summary.append(f"**Documents analysés:** {self.document_count}")
        summary.append(f"**Niveau de confiance:** {self.confidence:.0%}")
        
        # Conclusions principales
        if self.key_findings:
            summary.append("\n**Principales conclusions:**")
            for i, finding in enumerate(self.key_findings[:3], 1):
                summary.append(f"{i}. {finding}")
        
        # Recommandations prioritaires
        if self.recommendations:
            summary.append("\n**Recommandations prioritaires:**")
            sorted_recs = sorted(self.recommendations, 
                               key=lambda x: x.get('priority', 5), 
                               reverse=True)
            for i, rec in enumerate(sorted_recs[:3], 1):
                summary.append(f"{i}. {rec['text']}")
        
        return "\n".join(summary)
    
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
            'sources': self.sources,
            'infractions_identifiees': [inf.to_dict() for inf in self.infractions_identifiees],
            'risk_assessment': self.risk_assessment,
            'compliance_gaps': self.compliance_gaps,
            'strategic_options': self.strategic_options,
            'executive_summary': self.get_executive_summary()
        }

@dataclass
class RedactionResult:
    """Résultat de rédaction de document enrichi"""
    type: str  # conclusions, plainte, plainte_avec_cpc, mise_en_demeure, etc.
    document: str
    provider: str
    timestamp: datetime = field(default_factory=datetime.now)
    style: str = "formel"
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    jurisprudence_used: bool = False
    jurisprudence_references: List['JurisprudenceReference'] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    facts_used: List[FactWithSource] = field(default_factory=list)
    arguments: List[ArgumentStructure] = field(default_factory=list)
    paragraph_sources: Dict[int, List[SourceReference]] = field(default_factory=dict)
    
    # Champs spécifiques pour les plaintes
    parties_demanderesses: List[Partie] = field(default_factory=list)
    parties_defenderesses: List[Partie] = field(default_factory=list)
    infractions_visees: List[InfractionIdentifiee] = field(default_factory=list)
    destinataire: Optional[str] = None
    reference_modele: Optional[str] = None
    
    # Style appris
    style_learning_applied: Optional[StyleLearningResult] = None
    
    def __post_init__(self):
        """Calcule le nombre de mots et autres métadonnées"""
        if self.document and not self.word_count:
            self.word_count = len(self.document.split())
        
        # Déterminer le destinataire selon le type
        if not self.destinataire:
            if self.type == 'plainte_avec_cpc':
                self.destinataire = "Monsieur le Doyen des Juges d'Instruction"
            elif self.type == 'plainte':
                self.destinataire = "Monsieur le Procureur de la République"
    
    def add_paragraph_source(self, paragraph_num: int, sources: List[SourceReference]):
        """Ajoute des sources pour un paragraphe spécifique"""
        if paragraph_num not in self.paragraph_sources:
            self.paragraph_sources[paragraph_num] = []
        self.paragraph_sources[paragraph_num].extend(sources)
    
    def add_partie(self, partie: Partie, is_demandeur: bool = True):
        """Ajoute une partie au document"""
        if is_demandeur:
            self.parties_demanderesses.append(partie)
        else:
            self.parties_defenderesses.append(partie)
    
    def add_infraction(self, infraction: InfractionIdentifiee):
        """Ajoute une infraction visée"""
        self.infractions_visees.append(infraction)
    
    def apply_learned_style(self, style_result: StyleLearningResult):
        """Applique un style appris au document"""
        self.style_learning_applied = style_result
        self.style = "personnalisé"
        
        # Appliquer la numérotation des paragraphes
        if style_result.paragraph_numbering_pattern:
            self.document = self._apply_paragraph_numbering(
                self.document, 
                style_result.paragraph_numbering_pattern
            )
    
    def _apply_paragraph_numbering(self, text: str, pattern: str) -> str:
        """Applique un style de numérotation aux paragraphes"""
        # Logique d'application du pattern de numérotation
        # À implémenter selon les besoins
        return text
    
    def get_all_sources(self) -> List[SourceReference]:
        """Récupère toutes les sources utilisées"""
        sources = []
        for fact in self.facts_used:
            sources.extend(fact.sources)
        for arg in self.arguments:
            sources.extend(arg.get_all_sources())
        for para_sources in self.paragraph_sources.values():
            sources.extend(para_sources)
        return sources
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le document"""
        paragraphs = self.document.split('\n\n')
        sentences = self.document.split('.')
        
        return {
            'word_count': self.word_count,
            'char_count': len(self.document),
            'paragraph_count': len(paragraphs),
            'sentence_count': len(sentences),
            'avg_words_per_sentence': self.word_count / max(len(sentences), 1),
            'sources_count': len(self.get_all_sources()),
            'facts_count': len(self.facts_used),
            'jurisprudence_count': len(self.jurisprudence_references),
            'parties_count': len(self.parties_demanderesses) + len(self.parties_defenderesses),
            'infractions_count': len(self.infractions_visees),
            'style_applied': self.style_learning_applied is not None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'type': self.type,
            'document': self.document,
            'provider': self.provider,
            'timestamp': self.timestamp.isoformat(),
            'style': self.style,
            'word_count': self.word_count,
            'metadata': self.metadata,
            'jurisprudence_used': self.jurisprudence_used,
            'jurisprudence_references': [j.get_citation() for j in self.jurisprudence_references],
            'facts_used_count': len(self.facts_used),
            'arguments_count': len(self.arguments),
            'sources_count': len(self.get_all_sources()),
            'parties_demanderesses': [p.get_designation_complete() for p in self.parties_demanderesses],
            'parties_defenderesses': [p.get_designation_complete() for p in self.parties_defenderesses],
            'infractions_visees': [i.type.value for i in self.infractions_visees],
            'destinataire': self.destinataire,
            'reference_modele': self.reference_modele,
            'statistics': self.get_statistics(),
            'style_learning_applied': self.style_learning_applied.style_name if self.style_learning_applied else None
        }

# ========== JURISPRUDENCE ==========

@dataclass
class JurisprudenceReference:
    """Référence de jurisprudence"""
    numero: str
    date: datetime
    juridiction: str
    type_juridiction: Optional[TypeJuridiction] = None
    formation: Optional[str] = None
    titre: Optional[str] = None
    resume: Optional[str] = None
    url: Optional[str] = None
    source: SourceJurisprudence = SourceJurisprudence.MANUAL
    mots_cles: List[str] = field(default_factory=list)
    articles_vises: List[str] = field(default_factory=list)
    decisions_citees: List[str] = field(default_factory=list)
    importance: int = 5  # 1-10
    solution: Optional[str] = None  # cassation, rejet, etc.
    portee: Optional[str] = None  # principe, espèce
    commentaires: List[str] = field(default_factory=list)
    texte_integral: Optional[str] = None
    
    # Ajout pour compatibilité avec jurisprudence.py
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Synchroniser summary et resume
        if self.resume and not self.summary:
            self.summary = self.resume
        elif self.summary and not self.resume:
            self.resume = self.summary
        
        # Synchroniser keywords et mots_cles
        if self.mots_cles and not self.keywords:
            self.keywords = self.mots_cles
        elif self.keywords and not self.mots_cles:
            self.mots_cles = self.keywords
    
    def get_citation(self) -> str:
        """Retourne la citation formatée"""
        parts = [self.juridiction]
        if self.formation:
            parts.append(self.formation)
        parts.append(self.date.strftime('%d %B %Y'))
        parts.append(f"n°{self.numero}")
        return ", ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'numero': self.numero,
            'date': self.date.isoformat(),
            'juridiction': self.juridiction,
            'type_juridiction': self.type_juridiction.value if self.type_juridiction else None,
            'formation': self.formation,
            'titre': self.titre,
            'resume': self.resume,
            'summary': self.summary,
            'url': self.url,
            'source': self.source.value,
            'mots_cles': self.mots_cles,
            'keywords': self.keywords,
            'articles_vises': self.articles_vises,
            'decisions_citees': self.decisions_citees,
            'importance': self.importance,
            'solution': self.solution,
            'portee': self.portee,
            'commentaires': self.commentaires,
            'citation': self.get_citation()
        }

# Alias pour compatibilité
JurisprudenceCase = JurisprudenceReference

@dataclass
class VerificationResult:
    """Résultat de vérification de jurisprudence"""
    is_valid: bool
    confidence: float = 0.0
    message: Optional[str] = None
    reference: Optional[JurisprudenceReference] = None
    source_verified: Optional[SourceJurisprudence] = None
    suggestions: List[JurisprudenceReference] = field(default_factory=list)

# ========== CLASSES POUR EMAIL ==========
@dataclass
class EmailConfig:
    """Configuration complète d'un email et des paramètres SMTP"""
    # Paramètres du message
    to: List[str] = field(default_factory=list)
    subject: str = ""
    body: str = ""
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "normal"
    ai_enhanced: bool = False
    ai_model: str = ""
    tone: str = "professionnel"

    # Paramètres SMTP
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender: str = ""
    password: str = ""
    use_tls: bool = True

    def add_attachment(self, filename: str, data: bytes, mimetype: str) -> None:
        """Ajoute une pièce jointe."""
        self.attachments.append({
            "filename": filename,
            "data": data,
            "mimetype": mimetype,
        })

@dataclass
class EmailMessage:
    """Message email"""
    to: List[str]
    subject: str
    body: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    html: bool = False

# ========== CLASSES POUR MAPPING ==========
@dataclass
class Relationship:
    """Relation entre deux entités"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0

@dataclass
class EntityNode:
    """Nœud d'entité dans le graphe"""
    id: str
    name: str
    type: str  # personne, société, lieu, etc.
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RelationshipGraph:
    """Graphe de relations"""
    nodes: List[EntityNode] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

# ========== CLASSES POUR PLAIDOIRIE ==========
@dataclass
class PlaidoirieResult:
    """Résultat de génération de plaidoirie"""
    content: str
    success: bool
    structure: Dict[str, str] = field(default_factory=dict)
    arguments_principaux: List[str] = field(default_factory=list)
    duree_estimee: int = 30  # en minutes
    tone: str = "professionnel"  # professionnel, passionné, factuel
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ArgumentJuridique:
    """Argument juridique pour plaidoirie"""
    titre: str
    contenu: str
    fondements: List[str] = field(default_factory=list)  # articles, jurisprudences
    force: int = 5  # de 1 à 10
    ordre: int = 0

# ========== CLASSES POUR PREPARATION CLIENT ==========
@dataclass
class PreparationClientResult:
    """Résultat de préparation client"""
    documents: List[Document] = field(default_factory=list)
    notes: str = ""
    questions_cles: List[str] = field(default_factory=list)
    points_attention: List[str] = field(default_factory=list)
    recommandations: List[str] = field(default_factory=list)
    duree_estimee: int = 60  # en minutes
    agenda: Dict[str, str] = field(default_factory=dict)

@dataclass
class QuestionClient:
    """Question à poser au client"""
    question: str
    categorie: str  # factuelle, juridique, stratégique
    importance: str  # haute, moyenne, basse
    reponse_attendue: str = ""
    notes: str = ""

# ========== CLASSES SUPPLÉMENTAIRES UTILES ==========
@dataclass
class AnalyseRisqueResult:
    """Résultat d'analyse de risque"""
    niveau_global: str  # faible, moyen, élevé, critique
    risques: List[Risque] = field(default_factory=list)
    opportunites: List[str] = field(default_factory=list)
    recommandations: List[str] = field(default_factory=list)
    score: float = 0.0

@dataclass
class GenerationResult:
    """Résultat générique de génération"""
    content: str
    success: bool
    type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    generation_time: float = 0.0

@dataclass
class ExportResult:
    """Résultat d'export"""
    success: bool
    file_path: str = ""
    format: str = "pdf"
    size: int = 0
    error: str = ""

# ========== CLASSES POUR COMPATIBILITÉ AVEC utils/helpers.py ==========
@dataclass
class EmailCredentials:
    """Identifiants pour l'envoi d'emails"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True

@dataclass
class Template:
    """Modèle de document - Alias pour compatibilité"""
    id: str
    name: str
    description: str
    content: str
    category: str
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

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

# ========== FONCTIONS HELPER ==========

def get_all_juridictions() -> List[str]:
    """Retourne toutes les juridictions disponibles"""
    return [j.value for j in TypeJuridiction]

def get_statut_by_phase_and_role(phase: PhaseProcedure, role: str) -> StatutProcedural:
    """Détermine le statut procédural approprié selon la phase et le rôle"""
    if role.lower() in ['plaignant', 'victime']:
        return StatutProcedural.PLAIGNANT
    
    if phase in [PhaseProcedure.ENQUETE_PRELIMINAIRE, PhaseProcedure.ENQUETE_FLAGRANCE]:
        if role.lower() in ['défendeur', 'accusé']:
            return StatutProcedural.MIS_EN_CAUSE
        elif role.lower() == 'témoin':
            return StatutProcedural.TEMOIN
    elif phase == PhaseProcedure.INSTRUCTION:
        if role.lower() in ['défendeur', 'accusé']:
            return StatutProcedural.MIS_EN_EXAMEN
        elif role.lower() == 'témoin':
            return StatutProcedural.TEMOIN_ASSISTE
        elif role.lower() == 'partie civile':
            return StatutProcedural.PARTIE_CIVILE
    elif phase == PhaseProcedure.JUGEMENT:
        if role.lower() in ['défendeur', 'accusé']:
            return StatutProcedural.PREVENU
        elif role.lower() == 'partie civile':
            return StatutProcedural.PARTIE_CIVILE
    
    return StatutProcedural.TIERS

def format_partie_designation_by_phase(partie: Partie) -> str:
    """Formate la désignation d'une partie selon la phase procédurale"""
    base = partie.get_designation_complete()
    
    # Ajouter le statut procédural approprié
    if partie.phase_procedure == PhaseProcedure.ENQUETE_PRELIMINAIRE:
        if partie.statut_procedural == StatutProcedural.MIS_EN_CAUSE:
            return f"{base}, actuellement mis en cause"
        elif partie.statut_procedural == StatutProcedural.SUSPECT:
            return f"{base}, actuellement suspect"
    elif partie.phase_procedure == PhaseProcedure.INSTRUCTION:
        if partie.statut_procedural == StatutProcedural.MIS_EN_EXAMEN:
            return f"{base}, mis en examen"
        elif partie.statut_procedural == StatutProcedural.TEMOIN_ASSISTE:
            return f"{base}, témoin assisté"
    elif partie.phase_procedure == PhaseProcedure.JUGEMENT:
        if partie.statut_procedural == StatutProcedural.PREVENU:
            return f"{base}, prévenu"
    
    return base

def extract_paragraph_numbering_style(text: str) -> Optional[str]:
    """Extrait le style de numérotation des paragraphes d'un texte"""
    patterns = {
        r'^\d+\.': 'numeric',  # 1. 2. 3.
        r'^[IVX]+\.': 'roman_upper',  # I. II. III.
        r'^[ivx]+\.': 'roman_lower',  # i. ii. iii.
        r'^[A-Z]\.': 'alpha_upper',  # A. B. C.
        r'^[a-z]\.': 'alpha_lower',  # a. b. c.
        r'^\d+\.\d+': 'hierarchical',  # 1.1 1.2 2.1
        r'^\d+\)': 'numeric_paren',  # 1) 2) 3)
        r'^[A-Z]\)': 'alpha_paren',  # A) B) C)
        r'^-': 'dash',  # - item
        r'^•': 'bullet',  # • item
        r'^§\s*\d+': 'section'  # § 1
    }
    
    lines = text.split('\n')
    style_counts = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        for pattern, style in patterns.items():
            if re.match(pattern, line):
                style_counts[style] = style_counts.get(style, 0) + 1
                break
    
    if style_counts:
        # Retourner le style le plus fréquent
        return max(style_counts, key=style_counts.get)
    
    return None

def learn_document_style(documents: List[Document]) -> StyleLearningResult:
    """Apprend le style de rédaction à partir de plusieurs documents"""
    result = StyleLearningResult(
        style_name=f"Style personnalisé basé sur {len(documents)} documents",
        documents_analyzed=len(documents)
    )
    
    # Analyser chaque document
    all_sentences = []
    all_paragraphs = []
    paragraph_styles = []
    formality_indicators = []
    technical_terms = []
    
    for doc in documents:
        # Extraire les infos de style si pas déjà fait
        if not doc.style_info:
            doc.extract_style_info()
        
        # Collecter les données
        sentences = doc.content.split('.')
        paragraphs = doc.content.split('\n\n')
        
        all_sentences.extend(sentences)
        all_paragraphs.extend(paragraphs)
        
        if doc.style_info:
            if doc.style_info.get('paragraph_numbering'):
                paragraph_styles.append(doc.style_info['paragraph_numbering'])
            formality_indicators.append(doc.style_info.get('formality_indicators', 0))
    
    # Calculer les moyennes
    if all_sentences:
        total_words = sum(len(s.split()) for s in all_sentences)
        result.average_sentence_length = int(total_words / len(all_sentences))
    
    if all_paragraphs:
        total_para_words = sum(len(p.split()) for p in all_paragraphs)
        result.average_paragraph_length = int(total_para_words / len(all_paragraphs))
    
    # Déterminer le style de numérotation dominant
    if paragraph_styles:
        style_counts = {}
        for style in paragraph_styles:
            style_counts[style] = style_counts.get(style, 0) + 1
        result.paragraph_numbering_style = max(style_counts, key=style_counts.get)
        
        # Déterminer le pattern exact
        style_patterns = {
            'numeric': '1.',
            'roman_upper': 'I.',
            'roman_lower': 'i.',
            'alphabetic_upper': 'A.',
            'alphabetic_lower': 'a.',
            'hierarchical': '1.1'
        }
        result.paragraph_numbering_pattern = style_patterns.get(
            result.paragraph_numbering_style, 
            '1.'
        )
    
    # Calculer le score de formalité
    if formality_indicators:
        result.formality_score = min(1.0, sum(formality_indicators) / (len(formality_indicators) * 5))
    
    # Extraire les phrases et transitions communes
    sentence_starters = []
    for para in all_paragraphs[:50]:  # Limiter l'analyse
        sentences = para.split('.')
        for sent in sentences:
            sent = sent.strip()
            if sent and len(sent.split()) > 5:
                # Extraire les premiers mots
                words = sent.split()[:3]
                starter = ' '.join(words)
                sentence_starters.append(starter)
    
    # Identifier les patterns récurrents
    starter_counts = {}
    for starter in sentence_starters:
        starter_counts[starter] = starter_counts.get(starter, 0) + 1
    
    # Garder les plus fréquents
    common_starters = sorted(starter_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    result.common_phrases = [starter for starter, count in common_starters if count > 1]
    
    # Identifier les mots de transition
    transition_words = [
        'toutefois', 'cependant', 'néanmoins', 'par ailleurs', 'en outre',
        'de plus', 'ainsi', 'donc', 'par conséquent', 'dès lors',
        'en effet', 'or', 'mais', 'enfin', 'd\'une part', 'd\'autre part'
    ]
    
    text_combined = ' '.join(doc.content.lower() for doc in documents)
    found_transitions = []
    for word in transition_words:
        if word in text_combined:
            count = text_combined.count(word)
            if count > len(documents):  # Au moins une fois par document en moyenne
                found_transitions.append(word)
    
    result.transition_words = found_transitions
    
    # Déterminer les patterns d'argumentation
    argument_markers = [
        'il convient de', 'il résulte de', 'il apparaît que', 'force est de constater',
        'il en découle', 'partant', 'au surplus', 'subsidiairement', 'à titre principal',
        'en tout état de cause', 'quoi qu\'il en soit'
    ]
    
    found_patterns = []
    for marker in argument_markers:
        if marker in text_combined:
            found_patterns.append(marker)
    
    result.argument_patterns = found_patterns
    
    return result

def format_piece_with_source_and_footnote(piece: PieceSelectionnee, 
                                        source_doc: Optional[Document] = None) -> str:
    """Formate une référence de pièce avec lien source et footnote"""
    # Créer le lien source si document disponible
    if source_doc and not piece.source_link:
        piece.source_link = f"#doc_{source_doc.id}"
    
    # Générer la référence formatée
    ref = piece.get_formatted_reference()
    
    # Ajouter des informations contextuelles dans la footnote
    if source_doc:
        piece.footnote_text += f" (Source: {source_doc.title})"
    
    return ref

def generate_bordereau_with_full_links(bordereau: BordereauPieces, 
                                     source_tracker: SourceTracker) -> str:
    """Génère un bordereau avec tous les liens et footnotes"""
    # Utiliser la méthode export_to_markdown_with_links
    content = bordereau.export_to_markdown_with_links()
    
    # Enrichir avec les informations du tracker si disponible
    if source_tracker:
        # Ajouter des métadonnées supplémentaires
        enriched_lines = []
        enriched_lines.append(content)
        enriched_lines.append("\n\n## Traçabilité complète\n")
        
        for piece in bordereau.pieces:
            if piece.source_references:
                enriched_lines.append(f"\n### {piece.cote}")
                for ref in piece.source_references:
                    enriched_lines.append(f"- {ref.get_citation()}")
                    if ref.excerpt:
                        enriched_lines.append(f"  > {ref.excerpt}")
        
        content = "\n".join(enriched_lines)
    
    return content

def format_company_for_legal_document(info: InformationEntreprise, style: str = 'complet') -> str:
    """
    Formate les informations d'entreprise pour un document juridique
    
    Args:
        info: Les informations de l'entreprise
        style: Le style de formatage ('complet', 'simple', 'standard')
        
    Returns:
        La désignation formatée de l'entreprise
    """
    if style == 'complet':
        # Format complet avec toutes les informations
        designation = info.get_denomination_complete()
        if info.capital_social:
            designation += f" au capital de {info.format_capital()}"
        if info.get_immatriculation_complete():
            designation += f", {info.get_immatriculation_complete()}"
        if info.siege_social:
            designation += f", dont le siège social est situé {info.siege_social}"
        if info.representants_legaux:
            rep = info.representants_legaux[0]
            designation += f", représentée par {rep.get('nom', 'N/A')}"
        return designation
    elif style == 'simple':
        # Format simple : juste la dénomination
        return info.denomination
    elif style == 'standard':
        # Format standard : dénomination + forme juridique
        return info.get_denomination_complete()
    elif style == 'immatriculation':
        # Format avec focus sur l'immatriculation
        base = info.get_denomination_complete()
        if info.get_immatriculation_complete():
            base += f", {info.get_immatriculation_complete()}"
        return base
    else:
        # Par défaut, retourner le format standard
        return info.get_denomination_complete()

def get_phase_from_string(phase_str: str) -> PhaseProcedure:
    """
    Convertit une string en PhaseProcedure
    
    Args:
        phase_str: La chaîne représentant la phase
        
    Returns:
        L'enum PhaseProcedure correspondant
    """
    # Nettoyer la string
    phase_clean = phase_str.lower().strip().replace(' ', '_').replace("'", "")
    
    # Mapping des différentes variantes possibles
    phase_map = {
        # Variantes standards
        'enquete_preliminaire': PhaseProcedure.ENQUETE_PRELIMINAIRE,
        'enquête_préliminaire': PhaseProcedure.ENQUETE_PRELIMINAIRE,
        'enquete_flagrance': PhaseProcedure.ENQUETE_FLAGRANCE,
        'enquête_de_flagrance': PhaseProcedure.ENQUETE_FLAGRANCE,
        'instruction': PhaseProcedure.INSTRUCTION,
        'jugement': PhaseProcedure.JUGEMENT,
        'appel': PhaseProcedure.APPEL,
        'cassation': PhaseProcedure.CASSATION,
        'execution': PhaseProcedure.EXECUTION,
        'exécution': PhaseProcedure.EXECUTION,
        
        # Variantes alternatives
        'préliminaire': PhaseProcedure.ENQUETE_PRELIMINAIRE,
        'flagrance': PhaseProcedure.ENQUETE_FLAGRANCE,
        'juge_instruction': PhaseProcedure.INSTRUCTION,
        'première_instance': PhaseProcedure.JUGEMENT,
        'cour_appel': PhaseProcedure.APPEL,
        'cour_cassation': PhaseProcedure.CASSATION,
        
        # Valeurs directes de l'enum
        PhaseProcedure.ENQUETE_PRELIMINAIRE.value: PhaseProcedure.ENQUETE_PRELIMINAIRE,
        PhaseProcedure.ENQUETE_FLAGRANCE.value: PhaseProcedure.ENQUETE_FLAGRANCE,
        PhaseProcedure.INSTRUCTION.value: PhaseProcedure.INSTRUCTION,
        PhaseProcedure.JUGEMENT.value: PhaseProcedure.JUGEMENT,
        PhaseProcedure.APPEL.value: PhaseProcedure.APPEL,
        PhaseProcedure.CASSATION.value: PhaseProcedure.CASSATION,
        PhaseProcedure.EXECUTION.value: PhaseProcedure.EXECUTION,
    }
    
    # Recherche dans le mapping
    phase = phase_map.get(phase_clean)
    if phase:
        return phase
    
    # Recherche par valeur d'enum
    for p in PhaseProcedure:
        if p.value.lower() == phase_clean:
            return p
    
    # Par défaut, retourner enquête préliminaire
    return PhaseProcedure.ENQUETE_PRELIMINAIRE

def get_type_partie_from_string(type_str: str) -> TypePartie:
    """
    Convertit une string en TypePartie
    
    Args:
        type_str: La chaîne représentant le type de partie
        
    Returns:
        L'enum TypePartie correspondant
    """
    type_clean = type_str.lower().strip()
    
    type_map = {
        'demandeur': TypePartie.DEMANDEUR,
        'defendeur': TypePartie.DEFENDEUR,
        'défendeur': TypePartie.DEFENDEUR,
        'plaignant': TypePartie.PLAIGNANT,
        'mis_en_cause': TypePartie.MIS_EN_CAUSE,
        'mis en cause': TypePartie.MIS_EN_CAUSE,
        'temoin': TypePartie.TEMOIN,
        'témoin': TypePartie.TEMOIN,
        'expert': TypePartie.EXPERT,
        'tiers': TypePartie.TIERS,
        'partie_civile': TypePartie.PARTIE_CIVILE,
        'partie civile': TypePartie.PARTIE_CIVILE,
        'prevenu': TypePartie.PREVENU,
        'prévenu': TypePartie.PREVENU,
        'accuse': TypePartie.ACCUSE,
        'accusé': TypePartie.ACCUSE,
    }
    
    # Recherche dans le mapping
    type_partie = type_map.get(type_clean)
    if type_partie:
        return type_partie
    
    # Recherche par valeur d'enum
    for tp in TypePartie:
        if tp.value.lower() == type_clean:
            return tp
    
    # Par défaut
    return TypePartie.TIERS

def ensure_document_object(doc_data: Any) -> Document:
    """
    S'assure qu'on a bien un objet Document
    
    Args:
        doc_data: Les données du document (dict ou Document)
        
    Returns:
        Un objet Document
        
    Raises:
        ValueError: Si le type n'est pas supporté
    """
    if isinstance(doc_data, Document):
        return doc_data
    elif isinstance(doc_data, dict):
        # Document simple
        return Document(
            id=doc_data.get('id', f"doc_{datetime.now().timestamp()}"),
            title=doc_data.get('title', 'Sans titre'),
            content=doc_data.get('content', ''),
            source=doc_data.get('source', ''),
            metadata=doc_data.get('metadata', {}),
            created_at=doc_data.get('created_at', datetime.now()) if not isinstance(doc_data.get('created_at'), str) else datetime.fromisoformat(doc_data.get('created_at')),
            tags=doc_data.get('tags', []),
            category=doc_data.get('category'),
            author=doc_data.get('author'),
            reference=doc_data.get('reference')
        )
    else:
        raise ValueError(f"Type de document non supporté: {type(doc_data)}")

# ========== FONCTIONS D'INTÉGRATION ENTREPRISES ==========

async def fetch_company_info_pappers(company_name: str, api_key: str) -> Optional[InformationEntreprise]:
    """
    Récupère les informations d'une entreprise via l'API Pappers
    
    Note: Cette fonction est un placeholder. L'implémentation réelle nécessite:
    - Un compte Pappers avec clé API
    - La bibliothèque requests ou httpx pour les appels API
    """
    # Placeholder pour l'implémentation
    # Dans la vraie implémentation :
    # 1. Appeler l'API Pappers avec le nom de l'entreprise
    # 2. Parser la réponse JSON
    # 3. Créer un objet InformationEntreprise
    
    # Exemple de structure attendue :
    # response = requests.get(
    #     f"https://api.pappers.fr/v2/entreprise",
    #     params={"q": company_name, "api_token": api_key}
    # )
    # if response.status_code == 200:
    #     data = response.json()
    #     return InformationEntreprise(
    #         siren=data.get("siren"),
    #         denomination=data.get("denomination"),
    #         forme_juridique=data.get("forme_juridique"),
    #         capital_social=data.get("capital"),
    #         siege_social=data.get("siege", {}).get("adresse_ligne_1"),
    #         rcs_numero=data.get("numero_rcs"),
    #         rcs_ville=data.get("greffe"),
    #         source=SourceEntreprise.PAPPERS
    #     )
    
    return None

async def fetch_company_info_societe(company_name: str) -> Optional[InformationEntreprise]:
    """
    Récupère les informations d'une entreprise via societe.com (scraping)
    
    Note: Cette fonction est un placeholder. L'implémentation réelle nécessite:
    - BeautifulSoup ou playwright pour le scraping
    - Gestion des rate limits et éthique du scraping
    """
    # Placeholder pour l'implémentation
    # Dans la vraie implémentation :
    # 1. Rechercher l'entreprise sur societe.com
    # 2. Parser la page HTML
    # 3. Extraire les informations pertinentes
    # 4. Créer un objet InformationEntreprise
    
    return None

# ========== FONCTION MANQUANTE : collect_available_documents ==========

def collect_available_documents() -> List[Document]:
    """
    Collecte tous les documents disponibles dans le système
    
    Returns:
        Liste des documents disponibles
    """
    # Cette fonction est un placeholder
    # Dans une implémentation réelle, elle devrait :
    # 1. Scanner le répertoire des documents
    # 2. Charger depuis une base de données
    # 3. Récupérer depuis un système de stockage
    
    documents = []
    
    # Pour l'instant, retourner une liste vide
    # ou des documents de test si nécessaire
    return documents

# ========== FONCTION MANQUANTE : group_documents_by_category ==========

def group_documents_by_category(documents: List[Document]) -> Dict[str, List[Document]]:
    """
    Groupe les documents par catégorie
    
    Args:
        documents: Liste des documents à grouper
        
    Returns:
        Dictionnaire avec les catégories comme clés et les listes de documents comme valeurs
    """
    grouped = {}
    
    for doc in documents:
        # Déterminer la catégorie
        category = doc.category if doc.category else "Autre"
        
        # Ajouter au groupe
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(doc)
    
    # Trier les documents dans chaque catégorie par date
    for category in grouped:
        grouped[category].sort(key=lambda d: d.created_at, reverse=True)
    
    return grouped

# ========== EXPORTS ==========
__all__ = [
    # Documents
    'Document',
    'DocumentJuridique',
    
    # Parties et affaires
    'Partie',
    'TypePartie',
    'CasJuridique',
    'InformationEntreprise',
    'SourceEntreprise',
    
    # Pièces et procédure
    'PieceSelectionnee',
    'BordereauPieces',
    'ElementProcedure',
    'PieceVersee',
    'PieceProcedure',
    'ChaineProcedure',
    
    # Traçabilité
    'FactWithSource',
    'SourceReference',
    'ArgumentStructure',
    'SourceTracker',
    
    # Infractions
    'InfractionIdentifiee',
    'InfractionAffaires',
    
    # Dossiers
    'DossierPenal',
    'EvenementTimeline',
    
    # Enums
    'DocumentType',
    'RiskLevel',
    'SourceJurisprudence',
    'SourceEntreprise',
    'TypeDocument',
    'TypeJuridiction',
    'StatutProcedural',
    'PhaseProcedure',
    'InfractionAffaires',
    'LLMProvider',
    'SearchMode',
    'TypeElementProcedure',
    'NaturePiece',
    'ForceProbante',
    'StyleRedaction',
    'TypeAnalyse',
    'TypePartie',
    
    # Styles et templates
    'StyleConfig',
    'StyleLearningResult',
    'StylePattern',
    'DocumentTemplate',
    'LetterheadTemplate',
    'TemplateDocument',
    
    # Entités
    'Entity',
    
    # Timeline
    'TimelineEvent',
    
    # Recherche universelle
    'QueryAnalysis',
    'SearchResult',
    
    # Analyse et rédaction
    'AnalysisResult',
    'AnalyseJuridique',  # Alias
    'RedactionResult',
    'JurisprudenceReference',
    'JurisprudenceCase',  # Alias
    'VerificationResult',
    
    # Gestion des risques
    'Risque',
    
    # Notifications et sessions
    'Notification',
    'SessionUtilisateur',
    
    # Recherche
    'Jurisprudence',
    'ResultatRecherche',
    'ConfigurationRecherche',
    
    # Classes Email
    'EmailConfig',
    'EmailMessage',
    'EmailCredentials',
    
    # Classes Mapping
    'Relationship',
    'EntityNode',
    'RelationshipGraph',
    
    # Classes Plaidoirie
    'PlaidoirieResult',
    'ArgumentJuridique',
    
    # Classes Préparation Client
    'PreparationClientResult',
    'QuestionClient',
    
    # Classes supplémentaires
    'AnalyseRisqueResult',
    'GenerationResult',
    'ExportResult',
    'Template',
    'GenerationParams',
    'ProcessingStatus',
    
    # Fonctions helper
    'get_all_juridictions',
    'get_statut_by_phase_and_role',
    'format_partie_designation_by_phase',
    'create_partie_from_name_with_lookup',
    'extract_paragraph_numbering_style',
    'learn_document_style',
    'format_piece_with_source_and_footnote',
    'generate_bordereau_with_full_links',
    'format_company_for_legal_document',
    'get_phase_from_string',
    'get_type_partie_from_string',
    'ensure_document_object',
    'fetch_company_info_pappers',
    'fetch_company_info_societe',
    'collect_available_documents',
    'group_documents_by_category',
]