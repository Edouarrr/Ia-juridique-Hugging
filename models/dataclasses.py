# models/dataclasses.py
"""Modèles de données pour l'application juridique - Version adaptée pour le droit pénal des affaires"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from enum import Enum
import re

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
    PLAINTE = "plainte"
    PLAINTE_CPC = "plainte_avec_cpc"
    ASSIGNATION = "assignation"
    CONTRAT = "contrat"
    MEMOIRE = "memoire"
    REQUETE = "requete"
    CONSULTATION = "consultation"
    MISE_EN_DEMEURE = "mise_en_demeure"
    COURRIER = "courrier"

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
    JUGE_INSTRUCTION = "Juge d'instruction"
    PROCUREUR = "Procureur de la République"
    AUTRE = "Autre"

class InfractionAffaires(Enum):
    """Types d'infractions pénales des affaires"""
    ABUS_BIENS_SOCIAUX = "Abus de biens sociaux"
    CORRUPTION = "Corruption"
    TRAFIC_INFLUENCE = "Trafic d'influence"
    FAVORITISME = "Favoritisme"
    PRISE_ILLEGALE_INTERETS = "Prise illégale d'intérêts"
    BLANCHIMENT = "Blanchiment"
    FRAUDE_FISCALE = "Fraude fiscale"
    ESCROQUERIE = "Escroquerie"
    ABUS_CONFIANCE = "Abus de confiance"
    FAUX_USAGE_FAUX = "Faux et usage de faux"
    BANQUEROUTE = "Banqueroute"
    RECEL = "Recel"
    DELIT_INITIE = "Délit d'initié"
    MANIPULATION_COURS = "Manipulation de cours"
    ENTRAVE = "Entrave"
    TRAVAIL_DISSIMULE = "Travail dissimulé"
    MARCHANDAGE = "Marchandage"
    HARCELEMENT = "Harcèlement"
    DISCRIMINATION = "Discrimination"

class LLMProvider(Enum):
    """Fournisseurs de modèles de langage"""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"
    PERPLEXITY = "perplexity"
    MISTRAL = "mistral"
    GROK = "grok"
    GROQ = "groq"

class SearchMode(Enum):
    """Modes de recherche"""
    SIMPLE = "simple"
    ADVANCED = "advanced"
    VECTOR = "vector"
    HYBRID = "hybrid"
    UNIVERSAL = "universal"

class TypeElementProcedure(Enum):
    """Types d'éléments de procédure"""
    ASSIGNATION = "assignation"
    CITATION = "citation"
    CONCLUSIONS = "conclusions"
    REQUETE = "requete"
    ORDONNANCE = "ordonnance"
    JUGEMENT = "jugement"
    ARRET = "arret"
    SIGNIFICATION = "signification"
    MISE_EN_DEMEURE = "mise_en_demeure"
    PROCES_VERBAL = "proces_verbal"
    EXPERTISE = "expertise"
    AUDITION = "audition"
    CONSTAT = "constat"
    NOTIFICATION = "notification"
    APPEL = "appel"
    POURVOI = "pourvoi"
    MEMOIRE = "memoire"
    DIRE = "dire"
    NOTE_PLAIDOIRIE = "note_plaidoirie"

class NaturePiece(Enum):
    """Nature des pièces versées"""
    ORIGINAL = "original"
    COPIE = "copie"
    COPIE_CERTIFIEE = "copie_certifiée_conforme"
    EXTRAIT = "extrait"
    TRADUCTION = "traduction"
    TRANSCRIPTION = "transcription"
    PHOTOGRAPHIE = "photographie"
    ENREGISTREMENT = "enregistrement"
    PLAN = "plan"
    SCHEMA = "schema"

class ForceProbante(Enum):
    """Force probante d'une pièce"""
    FAIBLE = "faible"
    NORMALE = "normale"
    FORTE = "forte"
    IRREFRAGABLE = "irréfragable"

class StyleRedaction(Enum):
    """Styles de rédaction juridique"""
    FORMEL = "formel"
    PERSUASIF = "persuasif"
    TECHNIQUE = "technique"
    SYNTHETIQUE = "synthétique"
    PEDAGOGIQUE = "pédagogique"

class TypeAnalyse(Enum):
    """Types d'analyse juridique"""
    GENERAL = "general_analysis"
    RISQUES = "risk_analysis"
    CONFORMITE = "compliance"
    STRATEGIE = "strategy"
    INFRACTIONS = "infractions"

class TypePartie(Enum):
    """Types de parties dans une affaire"""
    DEMANDEUR = "demandeur"
    DEFENDEUR = "défendeur"
    PLAIGNANT = "plaignant"
    MIS_EN_CAUSE = "mis_en_cause"
    TEMOIN = "témoin"
    EXPERT = "expert"
    TIERS = "tiers"
    PARTIE_CIVILE = "partie_civile"
    PREVENU = "prévenu"
    ACCUSE = "accusé"

# ========== STYLES ET TEMPLATES ==========

@dataclass
class StyleConfig:
    """Configuration d'un style de rédaction"""
    name: str
    description: str
    tone: str
    vocabulary: str
    sentence_structure: str = "complexe"
    formality_level: int = 5  # 1-10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'tone': self.tone,
            'vocabulary': self.vocabulary,
            'sentence_structure': self.sentence_structure,
            'formality_level': self.formality_level
        }

@dataclass
class DocumentTemplate:
    """Template de document juridique"""
    id: str
    name: str
    type: TypeDocument
    structure: List[str]
    style: StyleRedaction
    category: str = "Autre"
    description: str = ""
    variables: List[str] = field(default_factory=list)
    is_builtin: bool = True
    usage_count: int = 0
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    
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
    
    def has_reference(self, ref: str) -> bool:
        """Vérifie si le document contient une référence"""
        ref_clean = ref.replace('@', '').strip().lower()
        return (ref_clean in self.title.lower() or 
                ref_clean in self.source.lower() or
                ref_clean in self.metadata.get('reference', '').lower())
    
    def extract_references(self) -> List[str]:
        """Extrait toutes les références @ du contenu"""
        references = re.findall(r'@(\w+)', self.content)
        return list(set(references))
    
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
class DocumentJuridique(Document):
    """Document juridique spécialisé avec métadonnées supplémentaires"""
    type_document: Optional[TypeDocument] = None
    juridiction: Optional[str] = None
    numero_affaire: Optional[str] = None
    date_document: Optional[datetime] = None
    parties: Dict[str, List[str]] = field(default_factory=dict)
    mots_cles_juridiques: List[str] = field(default_factory=list)
    articles_vises: List[str] = field(default_factory=list)
    jurisprudences_citees: List[str] = field(default_factory=list)
    resume_juridique: Optional[str] = None
    decision: Optional[str] = None  # Pour les arrêts/jugements
    montant: Optional[float] = None  # Si montant en jeu
    avocat_redacteur: Optional[str] = None
    confidentialite: str = "normal"  # normal, confidentiel, secret
    
    def __post_init__(self):
        """Validation post-initialisation spécifique"""
        super().__post_init__()
        
        # Ajouter le type de document aux métadonnées
        if self.type_document:
            self.metadata['type_document'] = self.type_document.value
        
        # Ajouter les infos juridiques aux métadonnées
        self.metadata.update({
            'juridiction': self.juridiction,
            'numero_affaire': self.numero_affaire,
            'date_document': self.date_document.isoformat() if self.date_document else None,
            'confidentialite': self.confidentialite,
            'has_decision': self.decision is not None,
            'has_montant': self.montant is not None
        })
    
    def extract_references_juridiques(self) -> Dict[str, List[str]]:
        """Extrait toutes les références juridiques du document"""
        references = {
            'articles_codes': [],
            'jurisprudences': [],
            'textes_lois': []
        }
        
        # Patterns pour extraire les références
        patterns = {
            'articles_codes': r'(?:article|art\.?)\s+(?:L\.?|R\.?|D\.?)?\s*\d+(?:-\d+)?(?:\s+(?:du|de la|des)\s+[^,\.\n]+)?',
            'jurisprudences': r'(?:Cass\.?|C\.?\s*cass\.?|CA|CE|CC)\s+[^,\.\n]+\d{4}',
            'textes_lois': r'(?:loi|décret|ordonnance|arrêté)\s+(?:n°\s*)?[\d-]+\s+du\s+\d+\s+\w+\s+\d{4}'
        }
        
        for ref_type, pattern in patterns.items():
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            references[ref_type] = list(set(matches))
        
        return references
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire avec champs spécifiques"""
        base_dict = super().to_dict()
        base_dict.update({
            'type_document': self.type_document.value if self.type_document else None,
            'juridiction': self.juridiction,
            'numero_affaire': self.numero_affaire,
            'date_document': self.date_document.isoformat() if self.date_document else None,
            'parties': self.parties,
            'mots_cles_juridiques': self.mots_cles_juridiques,
            'articles_vises': self.articles_vises,
            'jurisprudences_citees': self.jurisprudences_citees,
            'resume_juridique': self.resume_juridique,
            'decision': self.decision,
            'montant': self.montant,
            'avocat_redacteur': self.avocat_redacteur,
            'confidentialite': self.confidentialite
        })
        return base_dict
    
    @classmethod
    def from_document(cls, doc: Document, **kwargs) -> 'DocumentJuridique':
        """Crée un DocumentJuridique à partir d'un Document simple"""
        doc_dict = doc.to_dict()
        doc_dict.update(kwargs)
        return cls.from_dict(doc_dict)

# ========== PARTIES ET AFFAIRES ==========

@dataclass
class Partie:
    """Représente une partie dans une affaire"""
    id: str
    nom: str
    type_partie: TypePartie
    type_personne: str = "morale"  # physique ou morale
    forme_juridique: Optional[str] = None  # SA, SARL, SAS, etc.
    capital_social: Optional[float] = None
    rcs: Optional[str] = None  # Numéro RCS
    siret: Optional[str] = None
    siege_social: Optional[str] = None
    representant_legal: Optional[str] = None
    date_naissance: Optional[datetime] = None  # Pour personnes physiques
    lieu_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    adresse: Optional[str] = None
    avocat: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"partie_{self.nom.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def get_designation_complete(self) -> str:
        """Retourne la désignation complète de la partie"""
        if self.type_personne == "morale":
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
            'designation_complete': self.get_designation_complete()
        }

@dataclass
class CasJuridique:
    """Représente un cas juridique complet avec traçabilité"""
    id: str
    titre: str
    description: str
    type_affaire: str  # pénal, civil, commercial, etc.
    parties: Dict[str, List[Partie]] = field(default_factory=dict)
    juridiction: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    statut: str = "en_cours"  # en_cours, clos, en_appel
    documents: List[str] = field(default_factory=list)  # IDs des documents
    infractions: List[InfractionIdentifiee] = field(default_factory=list)
    montants_enjeu: Dict[str, float] = field(default_factory=dict)
    avocats: Dict[str, str] = field(default_factory=dict)  # partie: avocat
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Champs pour la traçabilité
    chaine_procedure: Optional['ChaineProcedure'] = None
    facts_etablis: List['FactWithSource'] = field(default_factory=list)
    pieces_principales: List['PieceVersee'] = field(default_factory=list)
    
    # Références croisées
    reference_principale: Optional[str] = None
    references_associees: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validation post-initialisation"""
        if not self.id:
            self.id = f"cas_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Initialiser les parties par défaut
        if not self.parties:
            self.parties = {
                'demandeurs': [],
                'defendeurs': [],
                'temoins': [],
                'experts': []
            }
        
        # Initialiser la chaîne de procédure
        if not self.chaine_procedure:
            self.chaine_procedure = ChaineProcedure(
                id=f"chaine_{self.id}",
                affaire_id=self.id
            )
    
    def add_partie(self, partie: Partie):
        """Ajoute une partie au cas"""
        type_key = partie.type_partie.value + 's'
        if type_key not in self.parties:
            self.parties[type_key] = []
        
        # Éviter les doublons
        if not any(p.id == partie.id for p in self.parties[type_key]):
            self.parties[type_key].append(partie)
            self.updated_at = datetime.now()
    
    def get_parties_by_type(self, type_partie: TypePartie) -> List[Partie]:
        """Retourne toutes les parties d'un type donné"""
        type_key = type_partie.value + 's'
        return self.parties.get(type_key, [])
    
    def add_infraction(self, infraction: 'InfractionIdentifiee'):
        """Ajoute une infraction identifiée"""
        self.infractions.append(infraction)
        self.updated_at = datetime.now()
    
    def add_reference(self, reference: str):
        """Ajoute une référence associée"""
        ref_clean = reference.replace('@', '').strip()
        if ref_clean and ref_clean not in self.references_associees:
            self.references_associees.append(ref_clean)
            self.updated_at = datetime.now()
    
    def matches_reference(self, reference: str) -> bool:
        """Vérifie si l'affaire correspond à une référence"""
        ref_clean = reference.replace('@', '').strip().lower()
        
        # Vérifier la référence principale
        if self.reference_principale and ref_clean in self.reference_principale.lower():
            return True
        
        # Vérifier les références associées
        return any(ref_clean in ref.lower() for ref in self.references_associees)
    
    def get_all_parties_names(self) -> List[str]:
        """Retourne tous les noms de parties"""
        names = []
        for parties_list in self.parties.values():
            names.extend([p.nom for p in parties_list])
        return names
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        base_dict = {
            'id': self.id,
            'titre': self.titre,
            'description': self.description,
            'type_affaire': self.type_affaire,
            'parties': {k: [p.to_dict() for p in v] for k, v in self.parties.items()},
            'juridiction': self.juridiction,
            'date_debut': self.date_debut.isoformat() if self.date_debut else None,
            'date_fin': self.date_fin.isoformat() if self.date_fin else None,
            'statut': self.statut,
            'documents': self.documents,
            'infractions': [inf.to_dict() for inf in self.infractions],
            'montants_enjeu': self.montants_enjeu,
            'avocats': self.avocats,
            'decisions': self.decisions,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'reference_principale': self.reference_principale,
            'references_associees': self.references_associees
        }
        
        # Ajouter les informations de traçabilité si disponibles
        if self.chaine_procedure:
            base_dict['regularite_procedure'] = self.chaine_procedure.verifier_regularite()
        
        if self.facts_etablis:
            base_dict['nombre_facts_etablis'] = len(self.facts_etablis)
        
        if self.pieces_principales:
            base_dict['nombre_pieces'] = len(self.pieces_principales)
        
        return base_dict

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

# ========== PIÈCES ET PROCÉDURE ==========

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
    source_references: List['SourceReference'] = field(default_factory=list)
    facts_prouve: List['FactWithSource'] = field(default_factory=list)
    force_probante: ForceProbante = ForceProbante.NORMALE
    communicable: bool = True
    confidentiel: bool = False
    
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
    
    def add_source_reference(self, source_ref: 'SourceReference'):
        """Ajoute une référence source"""
        self.source_references.append(source_ref)
    
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
        
        return min(base_score, 1.0)
    
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
            'importance_score': self.get_importance_score()
        }

@dataclass
class BordereauPieces:
    """Bordereau de pièces avec traçabilité complète"""
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
    
    def __post_init__(self):
        if not self.id:
            self.id = f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_piece_with_facts(self, piece: PieceSelectionnee, facts: List['FactWithSource']):
        """Ajoute une pièce avec les faits qu'elle prouve"""
        piece.facts_prouve = facts
        self.pieces.append(piece)
        self.facts_inventory.extend(facts)
    
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
            ))
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

@dataclass
class ElementProcedure:
    """Élément de procédure avec traçabilité"""
    id: str
    type: str  # assignation, conclusions, requête, ordonnance, jugement, etc.
    intitule: str
    date: datetime
    auteur: str  # Partie ou juridiction qui a produit l'acte
    destinataire: Optional[str] = None
    delai: Optional[str] = None  # Délai légal associé
    date_signification: Optional[datetime] = None
    huissier: Optional[str] = None
    source_legale: List[str] = field(default_factory=list)  # Articles CPC/CPP
    pieces_jointes: List[PieceVersee] = field(default_factory=list)
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
class PieceVersee:
    """Pièce versée aux débats avec traçabilité complète"""
    id: str
    numero_ordre: int  # Numéro dans le bordereau
    cote: str  # Ex: "D-1", "P-12"
    intitule: str
    nature: str  # original, copie, copie certifiée conforme, etc.
    date_piece: Optional[datetime] = None
    date_versement: datetime = field(default_factory=datetime.now)
    partie_versante: str = ""
    communicable: bool = True  # Si la pièce est communicable à l'adversaire
    confidentiel: bool = False
    
    # Traçabilité
    document_source: Optional[Document] = None  # Document source s'il existe
    source_references: List['SourceReference'] = field(default_factory=list)
    facts_etablis: List['FactWithSource'] = field(default_factory=list)
    elements_procedure_lies: List[str] = field(default_factory=list)  # IDs des ElementProcedure
    
    # Métadonnées techniques
    hash_document: Optional[str] = None  # Hash pour intégrité
    taille: Optional[int] = None
    format: Optional[str] = None
    nombre_pages: Optional[int] = None
    
    # Analyse
    pertinence_score: float = 0.5  # 0-1
    force_probante: str = "normale"  # faible, normale, forte
    contestee: bool = False
    motif_contestation: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = f"piece_{self.cote}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def marquer_contestee(self, motif: str):
        """Marque la pièce comme contestée"""
        self.contestee = True
        self.motif_contestation = motif
    
    def to_bordereau_entry(self) -> Dict[str, Any]:
        """Formate pour un bordereau"""
        return {
            'numero': self.numero_ordre,
            'cote': self.cote,
            'intitule': self.intitule,
            'nature': self.nature,
            'date': self.date_piece.strftime('%d/%m/%Y') if self.date_piece else "Non datée",
            'pages': self.nombre_pages,
            'communicable': "Oui" if self.communicable else "Non",
            'observations': self.motif_contestation if self.contestee else ""
        }

@dataclass
class ChaineProcedure:
    """Chaîne complète d'actes de procédure"""
    id: str
    affaire_id: str
    elements: List[ElementProcedure] = field(default_factory=list)
    pieces_versees: List[PieceVersee] = field(default_factory=list)
    timeline: List[Tuple[datetime, str, str]] = field(default_factory=list)  # (date, type, description)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"chaine_{self.affaire_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_element(self, element: ElementProcedure):
        """Ajoute un élément à la chaîne"""
        self.elements.append(element)
        self.timeline.append((element.date, element.type, element.get_full_reference()))
        self.timeline.sort(key=lambda x: x[0])
    
    def add_piece(self, piece: PieceVersee):
        """Ajoute une pièce versée"""
        self.pieces_versees.append(piece)
        self.timeline.append((piece.date_versement, "piece_versee", f"Pièce {piece.cote}: {piece.intitule}"))
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
    excerpt: Optional[str] = None  # Extrait court du texte source
    confidence: float = 1.0  # Niveau de confiance dans la source
    
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
    content: str  # Le fait ou l'argument
    category: str  # Type de fait (juridique, factuel, procédural, etc.)
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

# ========== RECHERCHE UNIVERSELLE ==========

@dataclass
class QueryAnalysis:
    """Analyse d'une requête utilisateur universelle"""
    original_query: str
    intent: str  # search, redaction, analysis, etc.
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Champs spécifiques à la recherche universelle
    reference: Optional[str] = None  # Référence @
    action: Optional[str] = None  # Action principale détectée
    subject_matter: Optional[str] = None  # Sujet principal
    document_type: Optional[str] = None  # Type de document demandé
    parties_mentioned: List[str] = field(default_factory=list)
    infractions_mentioned: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.analyze()
    
    def analyze(self):
        """Analyse automatique de la requête"""
        query_lower = self.original_query.lower()
        
        # Extraire la référence @
        ref_match = re.search(r'@(\w+)', self.original_query)
        if ref_match:
            self.reference = ref_match.group(1)
        
        # Détecter l'action principale
        action_keywords = {
            'rédiger': 'redaction',
            'analyser': 'analysis',
            'rechercher': 'search',
            'comparer': 'comparison',
            'créer': 'creation',
            'importer': 'import',
            'exporter': 'export',
            'synthétiser': 'synthesis',
            'chronologie': 'timeline',
            'cartographie': 'mapping',
            'plainte': 'plainte',
            'conclusions': 'conclusions',
            'plaidoirie': 'plaidoirie',
            'préparer': 'preparation'
        }
        
        for keyword, action in action_keywords.items():
            if keyword in query_lower:
                self.action = action
                break
        
        # Détecter les parties mentionnées
        parties_patterns = [
            r'\b(INTERCONSTRUCTION|Interconstruction)\b',
            r'\b(VINCI|Vinci)\b',
            r'\b(SOGEPROM|Sogeprom)\b',
            r'\b(DEMATHIEU BARD|Demathieu Bard)\b',
            r'\b(M\.|Mr|Monsieur)\s+([A-Z][a-z]+)\b',
            r'\b([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)*)\b'  # Sociétés en majuscules
        ]
        
        for pattern in parties_patterns:
            matches = re.findall(pattern, self.original_query)
            self.parties_mentioned.extend(matches)
        
        # Détecter les infractions
        infractions_keywords = {
            'escroquerie': 'Escroquerie',
            'abus de confiance': 'Abus de confiance',
            'abus de biens sociaux': 'Abus de biens sociaux',
            'abs': 'Abus de biens sociaux',
            'faux': 'Faux et usage de faux',
            'corruption': 'Corruption',
            'fraude': 'Fraude',
            'blanchiment': 'Blanchiment (art. 324-1 Code pénal)',
        'fraude fiscale': 'Fraude fiscale (art. 1741 Code général des impôts)',
        'travail dissimulé': 'Travail dissimulé (art. L8221-3 Code du travail)',
        'marchandage': 'Marchandage (art. L8231-1 Code du travail)',
        'entrave': 'Entrave (art. L2328-1 Code du travail)',
        'banqueroute': 'Banqueroute (art. L654-2 Code de commerce)',
        'recel': 'Recel (art. 321-1 Code pénal)'
    }
    
    for keyword, infraction in infractions_keywords.items():
        if keyword in query_lower:
            infractions.append(infraction)
    
    return infractions

def detect_plainte_type(query: str) -> str:
    """Détecte le type de plainte demandé"""
    query_lower = query.lower()
    
    # Détection plainte avec constitution de partie civile
    cpc_keywords = [
        'partie civile', 'constitution de partie civile', 'cpc',
        'doyen', 'juge d\'instruction', 'instruction'
    ]
    
    if any(keyword in query_lower for keyword in cpc_keywords):
        return 'plainte_avec_cpc'
    
    # Par défaut, plainte simple
    return 'plainte_simple'

def create_partie_from_name(nom: str, type_partie: TypePartie, 
                          is_personne_morale: bool = True) -> Partie:
    """Crée une partie à partir d'un nom"""
    partie = Partie(
        id=f"partie_{nom.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        nom=nom,
        type_partie=type_partie,
        type_personne="morale" if is_personne_morale else "physique"
    )
    
    # Déterminer automatiquement certains attributs pour les sociétés connues
    societes_connues = {
        'VINCI': {
            'forme_juridique': 'SA',
            'siege_social': 'Nanterre'
        },
        'INTERCONSTRUCTION': {
            'forme_juridique': 'SAS',
            'siege_social': 'Paris'
        },
        'SOGEPROM RÉALISATIONS': {
            'forme_juridique': 'SAS',
            'siege_social': 'La Défense'
        },
        'DEMATHIEU BARD': {
            'forme_juridique': 'SA',
            'siege_social': 'Montigny-lès-Metz'
        }
    }
    
    if nom in societes_connues:
        for key, value in societes_connues[nom].items():
            setattr(partie, key, value)
    
    # Pour les personnes physiques
    if nom.startswith(('M.', 'Mme', 'Monsieur', 'Madame')):
        partie.type_personne = "physique"
    
    return partie

def calculate_document_relevance(doc: Document, query_analysis: QueryAnalysis) -> float:
    """Calcule la pertinence d'un document par rapport à une requête analysée"""
    score = 0.0
    
    # Vérifier la référence
    if query_analysis.reference and doc.has_reference(query_analysis.reference):
        score += 0.4
    
    # Vérifier les parties mentionnées
    doc_content_lower = doc.content.lower()
    for partie in query_analysis.parties_mentioned:
        if partie.lower() in doc_content_lower:
            score += 0.1
    
    # Vérifier les infractions
    for infraction in query_analysis.infractions_mentioned:
        if infraction.lower() in doc_content_lower:
            score += 0.15
    
    # Vérifier le sujet principal
    if query_analysis.subject_matter and query_analysis.subject_matter in doc_content_lower:
        score += 0.2
    
    return min(score, 1.0)

def group_documents_by_category(documents: List[Document]) -> Dict[str, List[Document]]:
    """Groupe les documents par catégorie"""
    categories = {
        'Procédure': [],
        'Expertise': [],
        'Comptabilité': [],
        'Contrats': [],
        'Correspondance': [],
        'Jurisprudence': [],
        'Autres': []
    }
    
    category_patterns = {
        'Procédure': ['plainte', 'procès-verbal', 'audition', 'conclusions', 'assignation'],
        'Expertise': ['expertise', 'expert', 'rapport technique', 'évaluation'],
        'Comptabilité': ['bilan', 'compte', 'facture', 'comptable', 'fiscal'],
        'Contrats': ['contrat', 'convention', 'accord', 'avenant', 'protocole'],
        'Correspondance': ['courrier', 'email', 'lettre', 'mail', 'courriel'],
        'Jurisprudence': ['arrêt', 'jugement', 'décision', 'cass.', 'cour d\'appel']
    }
    
    for doc in documents:
        categorized = False
        doc_lower = f"{doc.title} {doc.content[:500]}".lower()
        
        for category, keywords in category_patterns.items():
            if any(kw in doc_lower for kw in keywords):
                categories[category].append(doc)
                categorized = True
                break
        
        if not categorized:
            categories['Autres'].append(doc)
    
    # Nettoyer les catégories vides
    return {k: v for k, v in categories.items() if v}

def generate_document_statistics(content: str) -> Dict[str, Any]:
    """Génère des statistiques détaillées sur un document"""
    words = content.split()
    sentences = content.split('.')
    paragraphs = content.split('\n\n')
    
    # Compter les références juridiques
    law_refs = len(re.findall(r'article\s+[LR]?\s*\d+', content, re.IGNORECASE))
    case_refs = len(re.findall(r'(?:Cass|CA|CE|CC)\s+[^,\.\n]+\d{4}', content))
    
    # Analyser la complexité
    avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
    avg_sentence_length = len(words) / max(len(sentences), 1)
    
    # Termes juridiques fréquents
    legal_terms = [
        'considérant', 'attendu', 'droit', 'juridiction', 'procédure',
        'jugement', 'arrêt', 'défendeur', 'demandeur', 'partie'
    ]
    legal_term_count = sum(1 for word in words if word.lower() in legal_terms)
    
    return {
        'word_count': len(words),
        'sentence_count': len(sentences),
        'paragraph_count': len(paragraphs),
        'avg_word_length': round(avg_word_length, 2),
        'avg_sentence_length': round(avg_sentence_length, 2),
        'law_references': law_refs,
        'case_references': case_refs,
        'legal_term_density': round(legal_term_count / max(len(words), 1) * 100, 2),
        'reading_time_minutes': round(len(words) / 200, 1),  # 200 mots/minute
        'complexity_score': calculate_text_complexity(avg_word_length, avg_sentence_length)
    }

def calculate_text_complexity(avg_word_length: float, avg_sentence_length: float) -> str:
    """Calcule le niveau de complexité d'un texte"""
    # Score de complexité simplifié
    score = (avg_word_length - 4) * 10 + (avg_sentence_length - 15) * 0.5
    
    if score < 5:
        return "Simple"
    elif score < 10:
        return "Modéré"
    elif score < 15:
        return "Complexe"
    else:
        return "Très complexe"

def format_date_for_legal_document(date: datetime) -> str:
    """Formate une date pour un document juridique français"""
    months = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }
    
    return f"{date.day} {months[date.month]} {date.year}"

def generate_unique_reference(prefix: str = "REF") -> str:
    """Génère une référence unique pour un document ou une affaire"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(str(ord(c) % 10) for c in timestamp[-4:])
    return f"{prefix}-{timestamp}-{random_suffix}"

def validate_email_address(email: str) -> bool:
    """Valide une adresse email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}anchiment'
        }
        
        for keyword, infraction in infractions_keywords.items():
            if keyword in query_lower:
                self.infractions_mentioned.append(infraction)
        
        # Ajuster la confiance
        self.confidence = 0.5
        if self.reference:
            self.confidence += 0.2
        if self.action:
            self.confidence += 0.2
        if self.parties_mentioned:
            self.confidence += 0.1
    
    def has_reference(self) -> bool:
        """Vérifie si la requête contient une référence @"""
        return self.reference is not None
    
    def get_reference(self) -> Optional[str]:
        """Retourne la référence extraite"""
        return self.reference
    
    def is_redaction_request(self) -> bool:
        """Vérifie si c'est une demande de rédaction"""
        return self.action in ['redaction', 'plainte', 'conclusions', 'creation']
    
    def is_analysis_request(self) -> bool:
        """Vérifie si c'est une demande d'analyse"""
        return self.action == 'analysis'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'original_query': self.original_query,
            'intent': self.intent,
            'entities': self.entities,
            'confidence': self.confidence,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'reference': self.reference,
            'action': self.action,
            'subject_matter': self.subject_matter,
            'document_type': self.document_type,
            'parties_mentioned': self.parties_mentioned,
            'infractions_mentioned': self.infractions_mentioned
        }

@dataclass
class SearchResult:
    """Résultat de recherche unifié"""
    id: str
    title: str
    content: str
    score: float
    source: str
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_type: Optional[str] = None
    relevance_explanation: Optional[str] = None
    matched_references: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Normalise le score"""
        if self.score < 0:
            self.score = 0
        elif self.score > 1:
            self.score = 1
    
    def add_highlight(self, text: str, context: str = ""):
        """Ajoute un passage surligné"""
        highlight = text
        if context:
            highlight = f"...{context}..."
        self.highlights.append(highlight)
    
    def boost_score(self, factor: float):
        """Augmente le score de pertinence"""
        self.score = min(1.0, self.score * factor)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'score': self.score,
            'source': self.source,
            'highlights': self.highlights,
            'metadata': self.metadata,
            'document_type': self.document_type,
            'relevance_explanation': self.relevance_explanation,
            'matched_references': self.matched_references
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

# Alias pour compatibilité
AnalyseJuridique = AnalysisResult

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
    jurisprudence_references: List[JurisprudenceReference] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)  # Réponses des différentes IA
    facts_used: List[FactWithSource] = field(default_factory=list)
    arguments: List[ArgumentStructure] = field(default_factory=list)
    paragraph_sources: Dict[int, List[SourceReference]] = field(default_factory=dict)
    
    # Champs spécifiques pour les plaintes
    parties_demanderesses: List[Partie] = field(default_factory=list)
    parties_defenderesses: List[Partie] = field(default_factory=list)
    infractions_visees: List[InfractionIdentifiee] = field(default_factory=list)
    destinataire: Optional[str] = None
    reference_modele: Optional[str] = None
    
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
            'infractions_count': len(self.infractions_visees)
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
            'statistics': self.get_statistics()
        }

# ========== PLAIDOIRIE ET PRÉPARATION ==========

@dataclass
class PlaidoirieResult:
    """Résultat de génération de plaidoirie"""
    content: str
    type: str  # correctionnelle, assises, civile, commerciale, prudhommes
    style: str  # persuasif, technique, emotionnel, factuel
    duration_estimate: str
    key_points: List[str] = field(default_factory=list)
    structure: Dict[str, List[str]] = field(default_factory=dict)
    oral_markers: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    arguments: List[ArgumentStructure] = field(default_factory=list)
    facts_used: List[FactWithSource] = field(default_factory=list)
    source_mapping: Dict[str, List[SourceReference]] = field(default_factory=dict)
    
    # Éléments rhétoriques
    rhetorical_devices: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    emphasis_points: List[str] = field(default_factory=list)
    
    def get_speaking_time(self) -> int:
        """Estime le temps de parole en minutes"""
        # Environ 150 mots par minute en plaidoirie
        words = len(self.content.split())
        return int(words / 150)
    
    def get_all_sources(self) -> List[SourceReference]:
        """Récupère toutes les sources utilisées"""
        sources = []
        for arg in self.arguments:
            sources.extend(arg.get_all_sources())
        for fact in self.facts_used:
            sources.extend(fact.sources)
        return sources
    
    def add_rhetorical_device(self, device: str, example: str):
        """Ajoute un procédé rhétorique utilisé"""
        self.rhetorical_devices.append({
            'device': device,
            'example': example,
            'position': len(self.content.split(example)[0].split())  # Position en mots
        })
    
    def optimize_for_oral(self):
        """Optimise le texte pour l'oral"""
        # Remplacer les phrases trop longues
        sentences = self.content.split('.')
        optimized = []
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 25:  # Phrase trop longue pour l'oral
                # Diviser en phrases plus courtes
                mid = len(words) // 2
                optimized.append(' '.join(words[:mid]) + '.')
                optimized.append(' '.join(words[mid:]) + '.')
            else:
                optimized.append(sentence + '.')
        
        self.content = ' '.join(optimized)
        
        # Ajouter des marqueurs oraux
        self.add_oral_markers()
    
    def add_oral_markers(self):
        """Ajoute des indications pour l'oral"""
        markers = [
            "[PAUSE]",
            "[EMPHASE]",
            "[REGARDER LES JURÉS]",
            "[RALENTIR]",
            "[VOIX PLUS FORTE]"
        ]
        # Logique pour placer les marqueurs aux endroits stratégiques
        # À implémenter selon les besoins

@dataclass
class PreparationClientResult:
    """Résultat de préparation client"""
    content: str
    prep_type: str  # audition, interrogatoire, comparution, témoignage
    profile: str  # anxieux, confiant, technique, hostile
    strategy: str
    key_qa: List[Dict[str, str]] = field(default_factory=list)
    do_not_say: List[str] = field(default_factory=list)
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    duration_estimate: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    facts_basis: List[FactWithSource] = field(default_factory=list)
    qa_sources: Dict[str, List[SourceReference]] = field(default_factory=dict)
    
    # Éléments psychologiques
    stress_management_tips: List[str] = field(default_factory=list)
    body_language_advice: List[str] = field(default_factory=list)
    trigger_questions: List[Dict[str, str]] = field(default_factory=list)
    
    def get_top_questions(self, n: int = 10) -> List[Dict[str, str]]:
        """Retourne les N questions les plus importantes"""
        return self.key_qa[:n]
    
    def add_qa_with_source(self, question: str, answer: str, sources: List[SourceReference]):
        """Ajoute une Q/R avec ses sources"""
        self.key_qa.append({
            'question': question, 
            'answer': answer,
            'difficulty': self.assess_question_difficulty(question),
            'category': self.categorize_question(question)
        })
        self.qa_sources[question] = sources
    
    def assess_question_difficulty(self, question: str) -> int:
        """Évalue la difficulté d'une question (1-10)"""
        difficulty = 5
        
        # Questions techniques
        if any(term in question.lower() for term in ['expliquez', 'détaillez', 'précisez']):
            difficulty += 2
        
        # Questions piège
        if any(term in question.lower() for term in ['pourquoi', 'comment se fait-il', 'n\'est-il pas vrai']):
            difficulty += 1
        
        # Questions sur les contradictions
        if any(term in question.lower() for term in ['contradiction', 'incohérence', 'différence']):
            difficulty += 3
        
        return min(10, difficulty)
    
    def categorize_question(self, question: str) -> str:
        """Catégorise une question"""
        q_lower = question.lower()
        
        if any(term in q_lower for term in ['qui', 'quoi', 'où', 'quand']):
            return "factuelle"
        elif any(term in q_lower for term in ['pourquoi', 'comment']):
            return "explicative"
        elif any(term in q_lower for term in ['pensez-vous', 'croyez-vous']):
            return "opinion"
        elif any(term in q_lower for term in ['contradiction', 'différence']):
            return "confrontation"
        else:
            return "générale"
    
    def generate_practice_session(self) -> Dict[str, Any]:
        """Génère une session d'entraînement"""
        return {
            'duration': '45 minutes',
            'exercises': [
                {
                    'type': 'questions_simples',
                    'duration': '15 min',
                    'questions': self.key_qa[:5]
                },
                {
                    'type': 'questions_difficiles',
                    'duration': '20 min',
                    'questions': sorted(self.key_qa, 
                                      key=lambda x: x.get('difficulty', 5), 
                                      reverse=True)[:5]
                },
                {
                    'type': 'mise_en_situation',
                    'duration': '10 min',
                    'scenario': 'Confrontation avec la partie adverse'
                }
            ],
            'objectives': [
                'Maîtriser les faits',
                'Rester cohérent',
                'Gérer le stress',
                'Éviter les pièges'
            ]
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
    verified: bool = False
    confidence_score: float = 0.8
    
    def __post_init__(self):
        if self.commentaires is None:
            self.commentaires = []
    
    def get_citation(self) -> str:
        """Retourne la citation formatée"""
        return f"{self.juridiction}, {self.date.strftime('%d %B %Y')}, {self.numero}"
    
    def get_short_citation(self) -> str:
        """Retourne une citation courte"""
        juridiction_abbrev = {
            "Cour de cassation": "Cass.",
            "Conseil d'État": "CE",
            "Conseil constitutionnel": "CC",
            "Cour d'appel": "CA"
        }
        abbrev = juridiction_abbrev.get(self.juridiction, self.juridiction[:4])
        return f"{abbrev} {self.date.strftime('%d/%m/%Y')}, n°{self.numero}"
    
    def matches_pattern(self, pattern: str) -> bool:
        """Vérifie si la jurisprudence correspond à un pattern"""
        pattern_lower = pattern.lower()
        
        # Vérifier dans différents champs
        fields_to_check = [
            self.numero.lower(),
            self.juridiction.lower(),
            self.date.strftime('%d/%m/%Y'),
            self.titre.lower() if self.titre else "",
            ' '.join(self.mots_cles).lower()
        ]
        
        return any(pattern_lower in field for field in fields_to_check)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'numero': self.numero,
            'date': self.date.isoformat(),
            'juridiction': self.juridiction,
            'type_juridiction': self.type_juridiction.value if self.type_juridiction else None,
            'formation': self.formation,
            'titre': self.titre,
            'resume': self.resume,
            'url': self.url,
            'source': self.source.value,
            'mots_cles': self.mots_cles,
            'articles_vises': self.articles_vises,
            'importance': self.importance,
            'solution': self.solution,
            'portee': self.portee,
            'citation': self.get_citation(),
            'citation_courte': self.get_short_citation(),
            'verified': self.verified,
            'confidence_score': self.confidence_score
        }

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
    
    def add_suggestion(self, jurisprudence: JurisprudenceReference):
        """Ajoute une suggestion de jurisprudence similaire"""
        self.suggestions.append(jurisprudence)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'reference': self.reference.to_dict() if self.reference else None,
            'message': self.message,
            'confidence': self.confidence,
            'source_verified': self.source_verified.value if self.source_verified else None,
            'verification_date': self.verification_date.isoformat(),
            'details': self.details,
            'suggestions': [s.to_dict() for s in self.suggestions]
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
    source_references: List[SourceReference] = field(default_factory=list)
    fact_basis: Optional[FactWithSource] = None
    related_events: List[str] = field(default_factory=list)  # IDs d'événements liés
    
    def __post_init__(self):
        """Validation"""
        if self.importance < 1:
            self.importance = 1
        elif self.importance > 10:
            self.importance = 10
        
        # Si un fact_basis est fourni, extraire ses sources
        if self.fact_basis and not self.source_references:
            self.source_references = self.fact_basis.sources.copy()
        
        # Convertir la date si nécessaire
        if isinstance(self.date, str):
            try:
                self.date = datetime.fromisoformat(self.date)
            except:
                pass  # Garder comme string si conversion impossible
    
    def get_date_str(self) -> str:
        """Retourne la date formatée"""
        if isinstance(self.date, datetime):
            return self.date.strftime('%d/%m/%Y %H:%M')
        return str(self.date)
    
    def is_linked_to(self, other_event_id: str) -> bool:
        """Vérifie si l'événement est lié à un autre"""
        return other_event_id in self.related_events
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.get_date_str(),
            'description': self.description,
            'actors': self.actors,
            'location': self.location,
            'category': self.category,
            'importance': self.importance,
            'source': self.source,
            'evidence': self.evidence,
            'sources_count': len(self.source_references),
            'has_fact_basis': self.fact_basis is not None,
            'related_events': self.related_events
        }

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
    role: Optional[str] = None  # demandeur, défendeur, témoin, etc.
    importance: float = 0.5  # 0-1
    
    def add_alias(self, alias: str):
        """Ajoute un alias"""
        if alias not in self.aliases and alias != self.name:
            self.aliases.append(alias)
    
    def add_attribute(self, key: str, value: Any):
        """Ajoute un attribut"""
        self.attributes[key] = value
        
        # Ajuster l'importance selon certains attributs
        if key in ['role', 'position', 'fonction']:
            self.importance = min(1.0, self.importance + 0.1)
    
    def matches(self, text: str) -> bool:
        """Vérifie si le texte correspond à l'entité"""
        text_lower = text.lower()
        if self.name.lower() in text_lower:
            return True
        return any(alias.lower() in text_lower for alias in self.aliases)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'aliases': self.aliases,
            'attributes': self.attributes,
            'mentions_count': self.mentions_count,
            'first_mention': self.first_mention,
            'relationships_count': len(self.relationships),
            'role': self.role,
            'importance': self.importance
        }

@dataclass
class Relationship:
    """Relation entre entités"""
    source: str
    target: str
    type: str  # contractual, hierarchical, familial, conflictual, financial, other
    strength: float = 0.5  # 0-1
    direction: str = "bidirectional"  # unidirectional, bidirectional
    evidence: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    
    def is_active(self, date: Optional[datetime] = None) -> bool:
        """Vérifie si la relation est active à une date donnée"""
        if date is None:
            date = datetime.now()
        
        if self.start_date and date < self.start_date:
            return False
        if self.end_date and date > self.end_date:
            return False
        return True
    
    def add_evidence(self, evidence: str, source: Optional[str] = None):
        """Ajoute une preuve de la relation"""
        evidence_entry = evidence
        if source:
            evidence_entry = f"{evidence} (Source: {source})"
        self.evidence.append(evidence_entry)
        
        # Augmenter la confiance
        self.confidence = min(1.0, self.confidence + 0.05)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'type': self.type,
            'strength': self.strength,
            'direction': self.direction,
            'evidence_count': len(self.evidence),
            'is_active': self.is_active(),
            'duration': self.get_duration(),
            'attributes': self.attributes,
            'confidence': self.confidence
        }
    
    def get_duration(self) -> Optional[str]:
        """Calcule la durée de la relation"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return f"{delta.days} jours"
        return None

# ========== RÉSULTATS SPÉCIALISÉS ==========

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
    
    def get_events_by_date(self) -> List[TimelineEvent]:
        """Retourne les événements triés par date"""
        return sorted(self.events, key=lambda e: e.date if isinstance(e.date, datetime) else datetime.min)
    
    def get_events_by_importance(self) -> List[TimelineEvent]:
        """Retourne les événements triés par importance"""
        return sorted(self.events, key=lambda e: e.importance, reverse=True)
    
    def get_events_by_actor(self, actor: str) -> List[TimelineEvent]:
        """Retourne les événements impliquant un acteur"""
        return [e for e in self.events if actor in e.actors]
    
    def generate_summary(self) -> str:
        """Génère un résumé de la chronologie"""
        total_events = len(self.events)
        if not total_events:
            return "Aucun événement dans la chronologie"
        
        sorted_events = self.get_events_by_date()
        first_event = sorted_events[0]
        last_event = sorted_events[-1]
        
        key_actors = set()
        for event in self.events:
            key_actors.update(event.actors)
        
        summary = f"Chronologie de {total_events} événements\n"
        summary += f"Période : {first_event.get_date_str()} - {last_event.get_date_str()}\n"
        summary += f"Acteurs principaux : {', '.join(list(key_actors)[:5])}"
        
        return summary

@dataclass
class MappingResult:
    """Résultat de cartographie"""
    type: str
    entities: List[Entity]
    relationships: List[Relationship]
    analysis: Dict[str, Any]
    document_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    visualization: Optional[Any] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Trouve une entité par son nom"""
        for entity in self.entities:
            if entity.name == name or name in entity.aliases:
                return entity
        return None
    
    def get_relationships_for_entity(self, entity_name: str) -> List[Relationship]:
        """Retourne toutes les relations d'une entité"""
        return [r for r in self.relationships 
                if r.source == entity_name or r.target == entity_name]
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Calcule des statistiques sur le réseau"""
        # Calculer le degré de chaque nœud
        degrees = {}
        for entity in self.entities:
            relations = self.get_relationships_for_entity(entity.name)
            degrees[entity.name] = len(relations)
        
        # Identifier les hubs
        sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        hubs = [name for name, degree in sorted_degrees[:5]]
        
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'average_degree': sum(degrees.values()) / max(len(degrees), 1),
            'max_degree': max(degrees.values()) if degrees else 0,
            'hubs': hubs,
            'isolated_entities': [e.name for e in self.entities if degrees.get(e.name, 0) == 0]
        }
    
    def to_graph_data(self) -> Dict[str, Any]:
        """Convertit en données pour visualisation graphique"""
        nodes = []
        edges = []
        
        # Créer les nœuds
        for entity in self.entities:
            nodes.append({
                'id': entity.name,
                'label': entity.name,
                'type': entity.type,
                'size': entity.importance * 50,  # Taille proportionnelle à l'importance
                'attributes': entity.attributes
            })
        
        # Créer les arêtes
        for rel in self.relationships:
            edges.append({
                'source': rel.source,
                'target': rel.target,
                'type': rel.type,
                'weight': rel.strength,
                'directed': rel.direction == "unidirectional"
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.get_network_stats()
        }

@dataclass
class ComparisonResult:
    """Résultat de comparaison de documents"""
    type: str  # versions, témoignages, documents, chronologies
    document_count: int
    comparison: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    visualizations: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    differences: List[Dict[str, Any]] = field(default_factory=list)
    similarities: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_difference(self, category: str, doc1_content: str, doc2_content: str, importance: int = 5):
        """Ajoute une différence identifiée"""
        self.differences.append({
            'category': category,
            'doc1': doc1_content,
            'doc2': doc2_content,
            'importance': importance,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_similarity(self, category: str, content: str, confidence: float = 0.8):
        """Ajoute une similarité identifiée"""
        self.similarities.append({
            'category': category,
            'content': content,
            'confidence': confidence
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Génère un résumé de la comparaison"""
        return {
            'documents_compared': self.document_count,
            'differences_found': len(self.differences),
            'similarities_found': len(self.similarities),
            'major_differences': len([d for d in self.differences if d.get('importance', 5) >= 7]),
            'categories': list(set(d['category'] for d in self.differences))
        }

@dataclass
class SynthesisResult:
    """Résultat de synthèse de documents"""
    content: str
    piece_count: int
    categories: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    key_points: List[str] = field(default_factory=list)
    chronology: Optional[List[TimelineEvent]] = None
    legal_points: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    confidence: float = 0.8
    
    def add_key_point(self, point: str, source: Optional[str] = None):
        """Ajoute un point clé"""
        self.key_points.append(point)
        if source and source not in self.sources_used:
            self.sources_used.append(source)
    
    def add_legal_point(self, point: str, articles: List[str] = None):
        """Ajoute un point d'attention juridique"""
        legal_point = point
        if articles:
            legal_point += f" (Articles : {', '.join(articles)})"
        self.legal_points.append(legal_point)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'piece_count': self.piece_count,
            'categories': self.categories,
            'timestamp': self.timestamp.isoformat(),
            'key_points': self.key_points,
            'has_chronology': self.chronology is not None,
            'legal_points': self.legal_points,
            'recommendations': self.recommendations,
            'sources_count': len(self.sources_used),
            'confidence': self.confidence
        }

# ========== SESSION ET COMMUNICATION ==========

@dataclass
class Session:
    """Session utilisateur avec état de travail"""
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    documents: Dict[str, Document] = field(default_factory=dict)
    search_history: List[QueryAnalysis] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    # État de travail
    current_case: Optional[CasJuridique] = None
    selected_pieces: List[PieceSelectionnee] = field(default_factory=list)
    draft_documents: Dict[str, RedactionResult] = field(default_factory=dict)
    analysis_results: Dict[str, AnalysisResult] = field(default_factory=dict)
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Vérifie si la session a expiré"""
        return (datetime.now() - self.last_activity).seconds > timeout_minutes * 60
    
    def update_activity(self):
        """Met à jour l'heure de dernière activité"""
        self.last_activity = datetime.now()
    
    def add_search(self, query_analysis: QueryAnalysis):
        """Ajoute une recherche à l'historique"""
        self.search_history.append(query_analysis)
        self.update_activity()
    
    def save_draft(self, doc_type: str, result: RedactionResult):
        """Sauvegarde un brouillon de document"""
        self.draft_documents[doc_type] = result
        self.update_activity()
    
    def get_recent_searches(self, n: int = 10) -> List[QueryAnalysis]:
        """Retourne les N dernières recherches"""
        return self.search_history[-n:]
    
    def export_work(self) -> Dict[str, Any]:
        """Exporte tout le travail de la session"""
        return {
            'session_id': self.id,
            'created_at': self.created_at.isoformat(),
            'duration_minutes': int((self.last_activity - self.created_at).seconds / 60),
            'documents_count': len(self.documents),
            'searches_count': len(self.search_history),
            'drafts_count': len(self.draft_documents),
            'analyses_count': len(self.analysis_results),
            'current_case': self.current_case.to_dict() if self.current_case else None,
            'selected_pieces_count': len(self.selected_pieces)
        }

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
    is_encrypted: bool = False
    requires_receipt: bool = False
    
    def add_attachment(self, filename: str, data: bytes, mime_type: str = "application/octet-stream"):
        """Ajoute une pièce jointe"""
        self.attachments.append({
            'filename': filename,
            'data': data,
            'mime_type': mime_type,
            'size': len(data)
        })
    
    def add_document_attachment(self, doc: Document):
        """Ajoute un document comme pièce jointe"""
        self.add_attachment(
            f"{doc.title}.txt",
            doc.content.encode('utf-8'),
            'text/plain'
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Valide la configuration email"""
        errors = []
        
        if not self.to:
            errors.append("Au moins un destinataire requis")
        
        if not self.subject:
            errors.append("Objet requis")
        
        if not self.body:
            errors.append("Corps du message requis")
        
        # Vérifier les adresses email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in self.to + self.cc + self.bcc:
            if not re.match(email_pattern, email):
                errors.append(f"Adresse email invalide : {email}")
        
        return len(errors) == 0, errors

# ========== HELPERS ET UTILITIES ==========

class SourceTracker:
    """Classe helper pour gérer la traçabilité complète des sources"""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.facts: Dict[str, FactWithSource] = {}
        self.source_cache: Dict[str, SourceReference] = {}
        self.elements_procedure: Dict[str, ElementProcedure] = {}
        self.pieces_versees: Dict[str, PieceVersee] = {}
        self.cas_juridiques: Dict[str, CasJuridique] = {}
    
    def register_document(self, doc: Document) -> str:
        """Enregistre un document et retourne son ID"""
        self.documents[doc.id] = doc
        return doc.id
    
    def create_source_reference(self, document_id: str, **kwargs) -> SourceReference:
        """Crée une référence de source"""
        if document_id not in self.documents:
            raise ValueError(f"Document {document_id} non trouvé")
        
        doc = self.documents[document_id]
        source_ref = SourceReference(
            document_id=document_id,
            document_title=doc.title,
            **kwargs
        )
        
        # Cache pour éviter les doublons
        cache_key = f"{document_id}_{kwargs.get('page')}_{kwargs.get('paragraph')}"
        self.source_cache[cache_key] = source_ref
        
        return source_ref
    
    def create_fact(self, content: str, category: str, source_refs: List[SourceReference]) -> FactWithSource:
        """Crée un fait avec ses sources"""
        fact = FactWithSource(
            id=f"fact_{len(self.facts)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            content=content,
            category=category,
            sources=source_refs,
            verified=bool(source_refs)
        )
        self.facts[fact.id] = fact
        return fact
    
    def create_element_procedure(self, type_acte: str, intitule: str, 
                               date: datetime, auteur: str, **kwargs) -> ElementProcedure:
        """Crée un élément de procédure tracé"""
        element = ElementProcedure(
            id=f"proc_{type_acte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=type_acte,
            intitule=intitule,
            date=date,
            auteur=auteur,
            **kwargs
        )
        self.elements_procedure[element.id] = element
        return element
    
    def create_piece_versee(self, numero: int, cote: str, intitule: str, 
                          partie_versante: str, **kwargs) -> PieceVersee:
        """Crée une pièce versée aux débats"""
        piece = PieceVersee(
            id=f"piece_{cote}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            numero_ordre=numero,
            cote=cote,
            intitule=intitule,
            partie_versante=partie_versante,
            **kwargs
        )
        self.pieces_versees[piece.id] = piece
        return piece
    
    def link_piece_to_facts(self, piece_id: str, fact_ids: List[str]):
        """Lie une pièce aux faits qu'elle établit"""
        if piece_id not in self.pieces_versees:
            raise ValueError(f"Pièce {piece_id} non trouvée")
        
        piece = self.pieces_versees[piece_id]
        for fact_id in fact_ids:
            if fact_id in self.facts:
                piece.facts_etablis.append(self.facts[fact_id])
    
    def link_element_to_sources(self, element_id: str, source_refs: List[SourceReference]):
        """Lie un élément de procédure à ses sources"""
        if element_id not in self.elements_procedure:
            raise ValueError(f"Élément {element_id} non trouvé")
        
        element = self.elements_procedure[element_id]
        element.source_references.extend(source_refs)
    
    def find_documents_by_reference(self, reference: str) -> List[Document]:
        """Trouve tous les documents correspondant à une référence @"""
        ref_clean = reference.replace('@', '').strip().lower()
        matching_docs = []
        
        for doc in self.documents.values():
            if doc.has_reference(ref_clean):
                matching_docs.append(doc)
        
        return matching_docs
    
    def generate_source_report(self) -> Dict[str, Any]:
        """Génère un rapport global sur les sources utilisées"""
        return {
            'total_documents': len(self.documents),
            'total_facts': len(self.facts),
            'facts_with_sources': len([f for f in self.facts.values() if f.sources]),
            'facts_without_sources': len([f for f in self.facts.values() if not f.sources]),
            'total_elements_procedure': len(self.elements_procedure),
            'total_pieces_versees': len(self.pieces_versees),
            'pieces_contestees': len([p for p in self.pieces_versees.values() if p.contestee]),
            'source_distribution': self._get_source_distribution(),
            'procedure_distribution': {
                type_acte: len([e for e in self.elements_procedure.values() if e.type == type_acte])
                for type_acte in set(e.type for e in self.elements_procedure.values())
            }
        }
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """Analyse la distribution des sources"""
        distribution = {}
        
        # Sources des faits
        for fact in self.facts.values():
            for source in fact.sources:
                doc_title = source.document_title
                distribution[doc_title] = distribution.get(doc_title, 0) + 1
        
        # Sources des éléments de procédure
        for element in self.elements_procedure.values():
            for source in element.source_references:
                doc_title = source.document_title
                distribution[doc_title] = distribution.get(doc_title, 0) + 1
        
        # Sources des pièces
        for piece in self.pieces_versees.values():
            for source in piece.source_references:
                doc_title = source.document_title
                distribution[doc_title] = distribution.get(doc_title, 0) + 1
        
        return distribution

class DocumentFormatter:
    """Classe pour formater les documents avec liens sources"""
    
    def __init__(self, source_tracker: SourceTracker):
        self.tracker = source_tracker
    
    def format_with_sources(self, content: str, fact_ids: List[str]) -> str:
        """Formate un contenu en ajoutant les liens vers les sources"""
        fact_map = {fid: self.tracker.facts[fid] for fid in fact_ids if fid in self.tracker.facts}
        return inject_source_links(content, fact_map)
    
    def format_plaidoirie_with_sources(self, plaidoirie: PlaidoirieResult) -> str:
        """Formate une plaidoirie avec tous les liens sources"""
        content = plaidoirie.content
        
        # Ajouter les liens pour chaque paragraphe
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for i, para in enumerate(paragraphs):
            # Si des sources sont mappées pour ce paragraphe
            if i in plaidoirie.source_mapping:
                sources = plaidoirie.source_mapping[i]
                # Ajouter une note de bas de page avec les sources
                source_notes = []
                for j, source in enumerate(sources):
                    note_num = f"{i+1}.{j+1}"
                    para += f"[^{note_num}]"
                    source_notes.append(f"[^{note_num}]: {source.get_citation()}")
                
                formatted_paragraphs.append(para)
                if source_notes:
                    formatted_paragraphs.append("\n".join(source_notes))
            else:
                formatted_paragraphs.append(para)
        
        return "\n\n".join(formatted_paragraphs)
    
    def generate_source_footnotes(self, sources: List[SourceReference]) -> str:
        """Génère des notes de bas de page pour les sources"""
        footnotes = []
        for i, source in enumerate(sources, 1):
            citation = source.get_citation()
            if source.excerpt:
                citation += f' - "{source.excerpt}"'
            footnotes.append(f"[^{i}]: {citation}")
        
        return "\n".join(footnotes)
    
    def create_hyperlinked_document(self, doc_type: str, content: str, 
                                  sources: List[SourceReference]) -> str:
        """Crée un document avec hyperliens vers les sources"""
        header = f"# {doc_type.upper()}\n\n"
        header += f"*Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n\n"
        
        # Ajouter un sommaire des sources
        header += "## Sources utilisées\n\n"
        for i, source in enumerate(sources, 1):
            header += f"{i}. {source.get_citation()}\n"
        header += "\n---\n\n"
        
        # Contenu avec notes
        footer = "\n\n---\n\n## Notes et références\n\n"
        footer += self.generate_source_footnotes(sources)
        
        return header + content + footer

# ========== FONCTIONS HELPER ==========

def get_all_juridictions() -> List[str]:
    """Retourne la liste de toutes les juridictions"""
    return [j.value for j in TypeJuridiction]

def get_juridiction_type(juridiction_name: str) -> Optional[TypeJuridiction]:
    """Retourne le type de juridiction à partir du nom"""
    for jur_type in TypeJuridiction:
        if jur_type.value.lower() == juridiction_name.lower():
            return jur_type
    return None

def format_source_link(source_ref: SourceReference, text: str) -> str:
    """Formate un texte avec un lien vers sa source"""
    # Format : [texte](source:document_id#page_X_para_Y)
    link_parts = [f"source:{source_ref.document_id}"]
    if source_ref.page:
        link_parts.append(f"page_{source_ref.page}")
    if source_ref.paragraph:
        link_parts.append(f"para_{source_ref.paragraph}")
    
    link = "#".join(link_parts)
    return f"[{text}]({link})"

def format_piece_link(piece: PieceVersee, text: str) -> str:
    """Formate un texte avec un lien vers une pièce"""
    # Format : [texte](piece:cote)
    return f"[{text}](piece:{piece.cote})"

def format_procedure_link(element: ElementProcedure, text: str) -> str:
    """Formate un texte avec un lien vers un élément de procédure"""
    # Format : [texte](procedure:element_id)
    return f"[{text}](procedure:{element.id})"

def parse_source_link(link: str) -> Optional[Dict[str, Any]]:
    """Parse un lien source pour extraire ses composants"""
    # Pattern : [texte](type:reference#details)
    pattern = r'\[([^\]]+)\]\((\w+):([^#\)]+)(?:#([^\)]+))?\)'
    match = re.match(pattern, link)
    
    if not match:
        return None
    
    text, link_type, reference, details = match.groups()
    
    result = {
        'text': text,
        'type': link_type,
        'reference': reference
    }
    
    # Parser les détails si présents
    if details:
        detail_parts = details.split('_')
        if 'page' in details:
            result['page'] = int(detail_parts[1])
        if 'para' in details:
            result['paragraph'] = int(detail_parts[-1])
    
    return result

def inject_source_links(text: str, fact_map: Dict[str, FactWithSource]) -> str:
    """Injecte automatiquement les liens sources dans un texte"""
    # Cette fonction recherche les faits dans le texte et ajoute les liens
    for fact_id, fact in fact_map.items():
        if fact.content in text and fact.sources:
            # Prendre la première source
            source = fact.sources[0]
            linked_text = format_source_link(source, fact.content)
            text = text.replace(fact.content, linked_text, 1)
    
    return text

def extract_parties_from_query(query: str) -> Dict[str, List[str]]:
    """Extrait les parties mentionnées dans une requête"""
    parties = {
        'demandeurs': [],
        'defendeurs': []
    }
    
    query_lower = query.lower()
    
    # Patterns pour les demandeurs (entreprises BTP principalement)
    demandeurs_patterns = [
        ('interconstruction', 'INTERCONSTRUCTION'),
        ('vinci', 'VINCI'),
        ('sogeprom', 'SOGEPROM RÉALISATIONS'),
        ('demathieu bard', 'DEMATHIEU BARD'),
        ('bouygues', 'BOUYGUES'),
        ('eiffage', 'EIFFAGE'),
        ('spie', 'SPIE BATIGNOLLES'),
        ('leon grosse', 'LEON GROSSE'),
        ('fayat', 'FAYAT'),
        ('colas', 'COLAS'),
        ('eurovia', 'EUROVIA'),
        ('razel-bec', 'RAZEL-BEC'),
        ('nge', 'NGE'),
        ('gtm', 'GTM Bâtiment')
    ]
    
    # Patterns pour les défendeurs
    defendeurs_patterns = [
        ('perinet', 'M. PERINET'),
        ('périnet', 'M. PÉRINET'),
        ('vp invest', 'VP INVEST'),
        ('perraud', 'M. PERRAUD'),
        ('martin', 'M. MARTIN'),
        ('dupont', 'M. DUPONT'),
        ('durand', 'M. DURAND'),
        ('laurent', 'M. LAURENT'),
        ('michel', 'M. MICHEL')
    ]
    
    # Analyser la structure de la requête
    if ' pour ' in query_lower and ' contre ' in query_lower:
        # Extraire les parties selon la structure
        partie_pour = query_lower.split(' pour ')[1].split(' contre ')[0]
        partie_contre = query_lower.split(' contre ')[1]
        
        # Chercher les demandeurs
        for keyword, nom_formate in demandeurs_patterns:
            if keyword in partie_pour:
                parties['demandeurs'].append(nom_formate)
        
        # Chercher les défendeurs
        for keyword, nom_formate in defendeurs_patterns:
            if keyword in partie_contre:
                parties['defendeurs'].append(nom_formate)
    else:
        # Recherche globale
        if ' contre ' in query_lower:
            partie_contre = query_lower.split(' contre ')[1]
            for keyword, nom_formate in defendeurs_patterns:
                if keyword in partie_contre:
                    parties['defendeurs'].append(nom_formate)
        
        # Chercher les demandeurs dans le reste
        for keyword, nom_formate in demandeurs_patterns:
            if keyword in query_lower and nom_formate not in parties['defendeurs']:
                if ' contre ' not in query_lower or keyword not in query_lower.split(' contre ')[1]:
                    parties['demandeurs'].append(nom_formate)
    
    return parties

def extract_infractions_from_query(query: str) -> List[str]:
    """Extrait les infractions mentionnées dans une requête"""
    query_lower = query.lower()
    infractions = []
    
    infractions_keywords = {
        'escroquerie': 'Escroquerie (art. 313-1 Code pénal)',
        'abus de confiance': 'Abus de confiance (art. 314-1 Code pénal)',
        'abus de biens sociaux': 'Abus de biens sociaux (art. L241-3 et L242-6 Code de commerce)',
        'abs': 'Abus de biens sociaux (art. L241-3 et L242-6 Code de commerce)',
        'faux': 'Faux et usage de faux (art. 441-1 Code pénal)',
        'corruption': 'Corruption (art. 432-11 et 433-1 Code pénal)',
        'trafic d\'influence': 'Trafic d\'influence (art. 432-11 et 433-2 Code pénal)',
        'favoritisme': 'Favoritisme (art. 432-14 Code pénal)',
        'prise illégale': 'Prise illégale d\'intérêts (art. 432-12 Code pénal)',
        'blanchiment': 'Bl
    return bool(re.match(pattern, email))

def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour le rendre compatible avec tous les OS"""
    # Remplacer les caractères interdits
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limiter la longueur
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}.{ext}" if ext else name

def estimate_reading_time(text: str, words_per_minute: int = 200) -> Dict[str, int]:
    """Estime le temps de lecture d'un texte"""
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    
    return {
        'minutes': int(minutes),
        'seconds': int((minutes % 1) * 60),
        'words': word_count
    }

def extract_monetary_amounts(text: str) -> List[Dict[str, Any]]:
    """Extrait les montants monétaires d'un texte"""
    amounts = []
    
    # Patterns pour les montants en euros
    patterns = [
        r'(\d{1,3}(?:\s?\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
        r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
        r'(?:€|EUR)\s*(\d{1,3}(?:\s?\d{3})*(?:,\d{2})?)'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount_str = match.group(1)
            # Nettoyer et convertir
            amount_clean = amount_str.replace(' ', '').replace('.', '').replace(',', '.')
            try:
                amount_float = float(amount_clean)
                amounts.append({
                    'original': match.group(0),
                    'amount': amount_float,
                    'position': match.start()
                })
            except ValueError:
                continue
    
    return amounts

def create_document_hash(content: str) -> str:
    """Crée un hash unique pour un document"""
    import hashlib
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def merge_duplicate_facts(facts: List[FactWithSource]) -> List[FactWithSource]:
    """Fusionne les faits en double en combinant leurs sources"""
    unique_facts = {}
    
    for fact in facts:
        # Clé basée sur le contenu normalisé
        key = fact.content.strip().lower()
        
        if key in unique_facts:
            # Fusionner les sources
            existing = unique_facts[key]
            for source in fact.sources:
                if source not in existing.sources:
                    existing.add_source(source)
            # Prendre l'importance maximale
            existing.importance = max(existing.importance, fact.importance)
        else:
            unique_facts[key] = fact
    
    return list(unique_facts.values())

def rank_documents_by_relevance(documents: List[Document], 
                               query_analysis: QueryAnalysis) -> List[Tuple[Document, float]]:
    """Classe les documents par pertinence par rapport à une requête"""
    scored_docs = []
    
    for doc in documents:
        score = calculate_document_relevance(doc, query_analysis)
        scored_docs.append((doc, score))
    
    # Trier par score décroissant
    return sorted(scored_docs, key=lambda x: x[1], reverse=True)

def create_legal_summary(text: str, max_length: int = 500) -> str:
    """Crée un résumé juridique d'un texte"""
    sentences = text.split('.')
    summary = []
    current_length = 0
    
    # Prioriser les phrases contenant des termes juridiques importants
    priority_terms = [
        'condamne', 'décide', 'ordonne', 'rejette', 'déclare',
        'considérant', 'attendu', 'motifs', 'dispositif'
    ]
    
    # Trier les phrases par importance
    scored_sentences = []
    for sentence in sentences:
        score = sum(1 for term in priority_terms if term in sentence.lower())
        scored_sentences.append((sentence, score))
    
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # Construire le résumé
    for sentence, _ in scored_sentences:
        sentence = sentence.strip()
        if sentence and current_length + len(sentence) <= max_length:
            summary.append(sentence)
            current_length += len(sentence) + 1
    
    return '. '.join(summary) + '.' if summary else text[:max_length] + '...'

# ========== TEMPLATES PREDÉFINIS ==========

DOCUMENT_TEMPLATES_DEFAULTS = {
    'plainte_simple': DocumentTemplate(
        id='plainte_simple',
        name='Plainte simple',
        type=TypeDocument.PLAINTE,
        structure=[
            'Monsieur le Procureur de la République',
            'Tribunal judiciaire de [VILLE]',
            '[ADRESSE_TRIBUNAL]',
            '',
            '[LIEU], le [DATE]',
            '',
            'Objet : Plainte',
            '',
            'Monsieur le Procureur de la République,',
            '',
            'Je soussigné(e) [NOM_PLAIGNANT], [QUALITE], demeurant [ADRESSE_PLAIGNANT],',
            '',
            'Ai l\'honneur de porter plainte contre :',
            '[IDENTITE_MIS_EN_CAUSE]',
            '',
            'Pour les faits suivants :',
            '',
            'I. EXPOSÉ DES FAITS',
            '[FAITS_DETAILLES]',
            '',
            'II. QUALIFICATION JURIDIQUE',
            '[INFRACTIONS_VISEES]',
            '',
            'III. PRÉJUDICES SUBIS',
            '[PREJUDICES]',
            '',
            'IV. DEMANDES',
            'Je sollicite l\'ouverture d\'une enquête...',
            '',
            'V. PIÈCES JOINTES',
            '[LISTE_PIECES]',
            '',
            'Je me tiens à votre disposition...',
            '',
            '[SIGNATURE]'
        ],
        style=StyleRedaction.FORMEL,
        required_fields=['NOM_PLAIGNANT', 'ADRESSE_PLAIGNANT', 'FAITS_DETAILLES'],
        optional_fields=['QUALITE', 'IDENTITE_MIS_EN_CAUSE', 'PREJUDICES']
    ),
    
    'plainte_avec_cpc': DocumentTemplate(
        id='plainte_avec_cpc',
        name='Plainte avec constitution de partie civile',
        type=TypeDocument.PLAINTE_CPC,
        structure=[
            'Monsieur le Doyen des Juges d\'Instruction',
            'Tribunal judiciaire de [VILLE]',
            '[ADRESSE_TRIBUNAL]',
            '',
            '[LIEU], le [DATE]',
            '',
            'OBJET : PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE',
            '',
            'POUR :',
            '[IDENTITE_COMPLETE_PLAIGNANTS]',
            '',
            'Ayant pour conseil :',
            'Maître [NOM_AVOCAT], Avocat au Barreau de [VILLE]',
            '[ADRESSE_CABINET]',
            '',
            'CONTRE :',
            '[IDENTITE_MIS_EN_CAUSE]',
            '',
            'ET CONTRE :',
            'Toute autre personne que l\'instruction révélerait...',
            '',
            'I. EXPOSÉ EXHAUSTIF DES FAITS',
            'A. CONTEXTE GÉNÉRAL',
            '[CONTEXTE]',
            '',
            'B. CHRONOLOGIE DÉTAILLÉE',
            '[CHRONOLOGIE]',
            '',
            'C. MÉCANISME FRAUDULEUX',
            '[MECANISME]',
            '',
            'II. QUALIFICATION JURIDIQUE APPROFONDIE',
            '[QUALIFICATIONS_DETAILLEES]',
            '',
            'III. ÉLÉMENTS CONSTITUTIFS',
            'A. ÉLÉMENT MATÉRIEL',
            '[ELEMENT_MATERIEL]',
            '',
            'B. ÉLÉMENT INTENTIONNEL',
            '[ELEMENT_INTENTIONNEL]',
            '',
            'IV. PRÉJUDICES',
            '[EVALUATION_PREJUDICES]',
            '',
            'V. CONSTITUTION DE PARTIE CIVILE',
            'Les plaignants déclarent expressément se constituer partie civile...',
            '',
            'VI. DEMANDES D\'ACTES',
            '[ACTES_INSTRUCTION]',
            '',
            'PAR CES MOTIFS',
            '[DEMANDES_FINALES]',
            '',
            'SOUS TOUTES RÉSERVES',
            '',
            'BORDEREAU DE PIÈCES',
            '[BORDEREAU_PIECES]'
        ],
        style=StyleRedaction.FORMEL,
        required_fields=[
            'IDENTITE_COMPLETE_PLAIGNANTS', 'CONTEXTE', 'CHRONOLOGIE',
            'QUALIFICATIONS_DETAILLEES', 'EVALUATION_PREJUDICES'
        ]
    ),
    
    'conclusions_defense': DocumentTemplate(
        id='conclusions_defense',
        name='Conclusions en défense',
        type=TypeDocument.CONCLUSIONS,
        structure=[
            'TRIBUNAL [TYPE_JURIDICTION] DE [VILLE]',
            '[NUMERO_RG]',
            '',
            'CONCLUSIONS EN DÉFENSE',
            '',
            'POUR :',
            '[IDENTITE_DEFENDEUR]',
            '',
            'CONTRE :',
            '[IDENTITE_DEMANDEUR]',
            '',
            'PLAISE AU TRIBUNAL',
            '',
            'I. RAPPEL DES FAITS ET DE LA PROCÉDURE',
            'A. Les faits',
            '[RAPPEL_FAITS]',
            '',
            'B. La procédure',
            '[RAPPEL_PROCEDURE]',
            '',
            'II. DISCUSSION',
            'A. Sur la recevabilité',
            '[MOYENS_IRRECEVABILITE]',
            '',
            'B. Sur le fond',
            '1. Sur l\'élément matériel',
            '[CONTESTATION_MATERIEL]',
            '',
            '2. Sur l\'élément intentionnel',
            '[CONTESTATION_INTENTIONNEL]',
            '',
            '3. Sur le préjudice allégué',
            '[CONTESTATION_PREJUDICE]',
            '',
            'III. SUR LA DEMANDE DE DOMMAGES-INTÉRÊTS',
            '[CONTESTATION_DOMMAGES]',
            '',
            'PAR CES MOTIFS',
            '',
            'Il est demandé au Tribunal de :',
            '[DEMANDES]',
            '',
            'SOUS TOUTES RÉSERVES',
            '',
            'BORDEREAU DE PIÈCES EN DÉFENSE',
            '[BORDEREAU]'
        ],
        style=StyleRedaction.FORMEL,
        required_fields=['IDENTITE_DEFENDEUR', 'IDENTITE_DEMANDEUR', 'RAPPEL_FAITS']
    )
}

# ========== CONFIGURATION PAR DÉFAUT ==========

DEFAULT_STYLE_CONFIGS = {
    StyleRedaction.FORMEL: StyleConfig(
        name="Formel",
        description="Style juridique classique et solennel",
        tone="respectueux et distant",
        vocabulary="technique et précis",
        sentence_structure="complexe",
        formality_level=9
    ),
    StyleRedaction.PERSUASIF: StyleConfig(
        name="Persuasif",
        description="Style argumentatif et convaincant",
        tone="assertif et engagé",
        vocabulary="percutant et imagé",
        sentence_structure="variée",
        formality_level=7
    ),
    StyleRedaction.TECHNIQUE: StyleConfig(
        name="Technique",
        description="Style factuel et détaillé",
        tone="neutre et objectif",
        vocabulary="spécialisé et exhaustif",
        sentence_structure="structurée",
        formality_level=8
    ),
    StyleRedaction.SYNTHETIQUE: StyleConfig(
        name="Synthétique",
        description="Style concis et efficace",
        tone="direct et clair",
        vocabulary="simple et précis",
        sentence_structure="courte",
        formality_level=6
    ),
    StyleRedaction.PEDAGOGIQUE: StyleConfig(
        name="Pédagogique",
        description="Style explicatif et accessible",
        tone="bienveillant et didactique",
        vocabulary="vulgarisé et illustré",
        sentence_structure="simple",
        formality_level=5
    )
}

# ========== TYPES EXPORTÉS ==========

# Types personnalisés pour les annotations
DocumentDict = Dict[str, Document]
SearchResults = List[SearchResult]
TimelineEvents = List[TimelineEvent]
EntityList = List[Entity]
RelationshipList = List[Relationship]
PartiesList = List[Partie]
InfractionsList = List[InfractionIdentifiee]

# ========== FIN DU MODULE ==========anchiment'
        }
        
        for keyword, infraction in infractions_keywords.items():
            if keyword in query_lower:
                self.infractions_mentioned.append(infraction)
        
        # Ajuster la confiance
        self.confidence = 0.5
        if self.reference:
            self.confidence += 0.2
        if self.action:
            self.confidence += 0.2
        if self.parties_mentioned:
            self.confidence += 0.1
    
    def has_reference(self) -> bool:
        """Vérifie si la requête contient une référence @"""
        return self.reference is not None
    
    def get_reference(self) -> Optional[str]:
        """Retourne la référence extraite"""
        return self.reference
    
    def is_redaction_request(self) -> bool:
        """Vérifie si c'est une demande de rédaction"""
        return self.action in ['redaction', 'plainte', 'conclusions', 'creation']
    
    def is_analysis_request(self) -> bool:
        """Vérifie si c'est une demande d'analyse"""
        return self.action == 'analysis'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'original_query': self.original_query,
            'intent': self.intent,
            'entities': self.entities,
            'confidence': self.confidence,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'reference': self.reference,
            'action': self.action,
            'subject_matter': self.subject_matter,
            'document_type': self.document_type,
            'parties_mentioned': self.parties_mentioned,
            'infractions_mentioned': self.infractions_mentioned
        }

@dataclass
class SearchResult:
    """Résultat de recherche unifié"""
    id: str
    title: str
    content: str
    score: float
    source: str
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_type: Optional[str] = None
    relevance_explanation: Optional[str] = None
    matched_references: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Normalise le score"""
        if self.score < 0:
            self.score = 0
        elif self.score > 1:
            self.score = 1
    
    def add_highlight(self, text: str, context: str = ""):
        """Ajoute un passage surligné"""
        highlight = text
        if context:
            highlight = f"...{context}..."
        self.highlights.append(highlight)
    
    def boost_score(self, factor: float):
        """Augmente le score de pertinence"""
        self.score = min(1.0, self.score * factor)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'score': self.score,
            'source': self.source,
            'highlights': self.highlights,
            'metadata': self.metadata,
            'document_type': self.document_type,
            'relevance_explanation': self.relevance_explanation,
            'matched_references': self.matched_references
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

# Alias pour compatibilité
AnalyseJuridique = AnalysisResult

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
    jurisprudence_references: List[JurisprudenceReference] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)  # Réponses des différentes IA
    facts_used: List[FactWithSource] = field(default_factory=list)
    arguments: List[ArgumentStructure] = field(default_factory=list)
    paragraph_sources: Dict[int, List[SourceReference]] = field(default_factory=dict)
    
    # Champs spécifiques pour les plaintes
    parties_demanderesses: List[Partie] = field(default_factory=list)
    parties_defenderesses: List[Partie] = field(default_factory=list)
    infractions_visees: List[InfractionIdentifiee] = field(default_factory=list)
    destinataire: Optional[str] = None
    reference_modele: Optional[str] = None
    
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
            'infractions_count': len(self.infractions_visees)
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
            'statistics': self.get_statistics()
        }

# ========== PLAIDOIRIE ET PRÉPARATION ==========

@dataclass
class PlaidoirieResult:
    """Résultat de génération de plaidoirie"""
    content: str
    type: str  # correctionnelle, assises, civile, commerciale, prudhommes
    style: str  # persuasif, technique, emotionnel, factuel
    duration_estimate: str
    key_points: List[str] = field(default_factory=list)
    structure: Dict[str, List[str]] = field(default_factory=dict)
    oral_markers: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    arguments: List[ArgumentStructure] = field(default_factory=list)
    facts_used: List[FactWithSource] = field(default_factory=list)
    source_mapping: Dict[str, List[SourceReference]] = field(default_factory=dict)
    
    # Éléments rhétoriques
    rhetorical_devices: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    emphasis_points: List[str] = field(default_factory=list)
    
    def get_speaking_time(self) -> int:
        """Estime le temps de parole en minutes"""
        # Environ 150 mots par minute en plaidoirie
        words = len(self.content.split())
        return int(words / 150)
    
    def get_all_sources(self) -> List[SourceReference]:
        """Récupère toutes les sources utilisées"""
        sources = []
        for arg in self.arguments:
            sources.extend(arg.get_all_sources())
        for fact in self.facts_used:
            sources.extend(fact.sources)
        return sources
    
    def add_rhetorical_device(self, device: str, example: str):
        """Ajoute un procédé rhétorique utilisé"""
        self.rhetorical_devices.append({
            'device': device,
            'example': example,
            'position': len(self.content.split(example)[0].split())  # Position en mots
        })
    
    def optimize_for_oral(self):
        """Optimise le texte pour l'oral"""
        # Remplacer les phrases trop longues
        sentences = self.content.split('.')
        optimized = []
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 25:  # Phrase trop longue pour l'oral
                # Diviser en phrases plus courtes
                mid = len(words) // 2
                optimized.append(' '.join(words[:mid]) + '.')
                optimized.append(' '.join(words[mid:]) + '.')
            else:
                optimized.append(sentence + '.')
        
        self.content = ' '.join(optimized)
        
        # Ajouter des marqueurs oraux
        self.add_oral_markers()
    
    def add_oral_markers(self):
        """Ajoute des indications pour l'oral"""
        markers = [
            "[PAUSE]",
            "[EMPHASE]",
            "[REGARDER LES JURÉS]",
            "[RALENTIR]",
            "[VOIX PLUS FORTE]"
        ]
        # Logique pour placer les marqueurs aux endroits stratégiques
        # À implémenter selon les besoins

@dataclass
class PreparationClientResult:
    """Résultat de préparation client"""
    content: str
    prep_type: str  # audition, interrogatoire, comparution, témoignage
    profile: str  # anxieux, confiant, technique, hostile
    strategy: str
    key_qa: List[Dict[str, str]] = field(default_factory=list)
    do_not_say: List[str] = field(default_factory=list)
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    duration_estimate: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    facts_basis: List[FactWithSource] = field(default_factory=list)
    qa_sources: Dict[str, List[SourceReference]] = field(default_factory=dict)
    
    # Éléments psychologiques
    stress_management_tips: List[str] = field(default_factory=list)
    body_language_advice: List[str] = field(default_factory=list)
    trigger_questions: List[Dict[str, str]] = field(default_factory=list)
    
    def get_top_questions(self, n: int = 10) -> List[Dict[str, str]]:
        """Retourne les N questions les plus importantes"""
        return self.key_qa[:n]
    
    def add_qa_with_source(self, question: str, answer: str, sources: List[SourceReference]):
        """Ajoute une Q/R avec ses sources"""
        self.key_qa.append({
            'question': question, 
            'answer': answer,
            'difficulty': self.assess_question_difficulty(question),
            'category': self.categorize_question(question)
        })
        self.qa_sources[question] = sources
    
    def assess_question_difficulty(self, question: str) -> int:
        """Évalue la difficulté d'une question (1-10)"""
        difficulty = 5
        
        # Questions techniques
        if any(term in question.lower() for term in ['expliquez', 'détaillez', 'précisez']):
            difficulty += 2
        
        # Questions piège
        if any(term in question.lower() for term in ['pourquoi', 'comment se fait-il', 'n\'est-il pas vrai']):
            difficulty += 1
        
        # Questions sur les contradictions
        if any(term in question.lower() for term in ['contradiction', 'incohérence', 'différence']):
            difficulty += 3
        
        return min(10, difficulty)
    
    def categorize_question(self, question: str) -> str:
        """Catégorise une question"""
        q_lower = question.lower()
        
        if any(term in q_lower for term in ['qui', 'quoi', 'où', 'quand']):
            return "factuelle"
        elif any(term in q_lower for term in ['pourquoi', 'comment']):
            return "explicative"
        elif any(term in q_lower for term in ['pensez-vous', 'croyez-vous']):
            return "opinion"
        elif any(term in q_lower for term in ['contradiction', 'différence']):
            return "confrontation"
        else:
            return "générale"
    
    def generate_practice_session(self) -> Dict[str, Any]:
        """Génère une session d'entraînement"""
        return {
            'duration': '45 minutes',
            'exercises': [
                {
                    'type': 'questions_simples',
                    'duration': '15 min',
                    'questions': self.key_qa[:5]
                },
                {
                    'type': 'questions_difficiles',
                    'duration': '20 min',
                    'questions': sorted(self.key_qa, 
                                      key=lambda x: x.get('difficulty', 5), 
                                      reverse=True)[:5]
                },
                {
                    'type': 'mise_en_situation',
                    'duration': '10 min',
                    'scenario': 'Confrontation avec la partie adverse'
                }
            ],
            'objectives': [
                'Maîtriser les faits',
                'Rester cohérent',
                'Gérer le stress',
                'Éviter les pièges'
            ]
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
    verified: bool = False
    confidence_score: float = 0.8
    
    def __post_init__(self):
        if self.commentaires is None:
            self.commentaires = []
    
    def get_citation(self) -> str:
        """Retourne la citation formatée"""
        return f"{self.juridiction}, {self.date.strftime('%d %B %Y')}, {self.numero}"
    
    def get_short_citation(self) -> str:
        """Retourne une citation courte"""
        juridiction_abbrev = {
            "Cour de cassation": "Cass.",
            "Conseil d'État": "CE",
            "Conseil constitutionnel": "CC",
            "Cour d'appel": "CA"
        }
        abbrev = juridiction_abbrev.get(self.juridiction, self.juridiction[:4])
        return f"{abbrev} {self.date.strftime('%d/%m/%Y')}, n°{self.numero}"
    
    def matches_pattern(self, pattern: str) -> bool:
        """Vérifie si la jurisprudence correspond à un pattern"""
        pattern_lower = pattern.lower()
        
        # Vérifier dans différents champs
        fields_to_check = [
            self.numero.lower(),
            self.juridiction.lower(),
            self.date.strftime('%d/%m/%Y'),
            self.titre.lower() if self.titre else "",
            ' '.join(self.mots_cles).lower()
        ]
        
        return any(pattern_lower in field for field in fields_to_check)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'numero': self.numero,
            'date': self.date.isoformat(),
            'juridiction': self.juridiction,
            'type_juridiction': self.type_juridiction.value if self.type_juridiction else None,
            'formation': self.formation,
            'titre': self.titre,
            'resume': self.resume,
            'url': self.url,
            'source': self.source.value,
            'mots_cles': self.mots_cles,
            'articles_vises': self.articles_vises,
            'importance': self.importance,
            'solution': self.solution,
            'portee': self.portee,
            'citation': self.get_citation(),
            'citation_courte': self.get_short_citation(),
            'verified': self.verified,
            'confidence_score': self.confidence_score
        }

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
    
    def add_suggestion(self, jurisprudence: JurisprudenceReference):
        """Ajoute une suggestion de jurisprudence similaire"""
        self.suggestions.append(jurisprudence)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'reference': self.reference.to_dict() if self.reference else None,
            'message': self.message,
            'confidence': self.confidence,
            'source_verified': self.source_verified.value if self.source_verified else None,
            'verification_date': self.verification_date.isoformat(),
            'details': self.details,
            'suggestions': [s.to_dict() for s in self.suggestions]
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
    source_references: List[SourceReference] = field(default_factory=list)
    fact_basis: Optional[FactWithSource] = None
    related_events: List[str] = field(default_factory=list)  # IDs d'événements liés
    
    def __post_init__(self):
        """Validation"""
        if self.importance < 1:
            self.importance = 1
        elif self.importance > 10:
            self.importance = 10
        
        # Si un fact_basis est fourni, extraire ses sources
        if self.fact_basis and not self.source_references:
            self.source_references = self.fact_basis.sources.copy()
        
        # Convertir la date si nécessaire
        if isinstance(self.date, str):
            try:
                self.date = datetime.fromisoformat(self.date)
            except:
                pass  # Garder comme string si conversion impossible
    
    def get_date_str(self) -> str:
        """Retourne la date formatée"""
        if isinstance(self.date, datetime):
            return self.date.strftime('%d/%m/%Y %H:%M')
        return str(self.date)
    
    def is_linked_to(self, other_event_id: str) -> bool:
        """Vérifie si l'événement est lié à un autre"""
        return other_event_id in self.related_events
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.get_date_str(),
            'description': self.description,
            'actors': self.actors,
            'location': self.location,
            'category': self.category,
            'importance': self.importance,
            'source': self.source,
            'evidence': self.evidence,
            'sources_count': len(self.source_references),
            'has_fact_basis': self.fact_basis is not None,
            'related_events': self.related_events
        }

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
    role: Optional[str] = None  # demandeur, défendeur, témoin, etc.
    importance: float = 0.5  # 0-1
    
    def add_alias(self, alias: str):
        """Ajoute un alias"""
        if alias not in self.aliases and alias != self.name:
            self.aliases.append(alias)
    
    def add_attribute(self, key: str, value: Any):
        """Ajoute un attribut"""
        self.attributes[key] = value
        
        # Ajuster l'importance selon certains attributs
        if key in ['role', 'position', 'fonction']:
            self.importance = min(1.0, self.importance + 0.1)
    
    def matches(self, text: str) -> bool:
        """Vérifie si le texte correspond à l'entité"""
        text_lower = text.lower()
        if self.name.lower() in text_lower:
            return True
        return any(alias.lower() in text_lower for alias in self.aliases)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'aliases': self.aliases,
            'attributes': self.attributes,
            'mentions_count': self.mentions_count,
            'first_mention': self.first_mention,
            'relationships_count': len(self.relationships),
            'role': self.role,
            'importance': self.importance
        }

@dataclass
class Relationship:
    """Relation entre entités"""
    source: str
    target: str
    type: str  # contractual, hierarchical, familial, conflictual, financial, other
    strength: float = 0.5  # 0-1
    direction: str = "bidirectional"  # unidirectional, bidirectional
    evidence: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    
    def is_active(self, date: Optional[datetime] = None) -> bool:
        """Vérifie si la relation est active à une date donnée"""
        if date is None:
            date = datetime.now()
        
        if self.start_date and date < self.start_date:
            return False
        if self.end_date and date > self.end_date:
            return False
        return True
    
    def add_evidence(self, evidence: str, source: Optional[str] = None):
        """Ajoute une preuve de la relation"""
        evidence_entry = evidence
        if source:
            evidence_entry = f"{evidence} (Source: {source})"
        self.evidence.append(evidence_entry)
        
        # Augmenter la confiance
        self.confidence = min(1.0, self.confidence + 0.05)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'type': self.type,
            'strength': self.strength,
            'direction': self.direction,
            'evidence_count': len(self.evidence),
            'is_active': self.is_active(),
            'duration': self.get_duration(),
            'attributes': self.attributes,
            'confidence': self.confidence
        }
    
    def get_duration(self) -> Optional[str]:
        """Calcule la durée de la relation"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return f"{delta.days} jours"
        return None

# ========== RÉSULTATS SPÉCIALISÉS ==========

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
    
    def get_events_by_date(self) -> List[TimelineEvent]:
        """Retourne les événements triés par date"""
        return sorted(self.events, key=lambda e: e.date if isinstance(e.date, datetime) else datetime.min)
    
    def get_events_by_importance(self) -> List[TimelineEvent]:
        """Retourne les événements triés par importance"""
        return sorted(self.events, key=lambda e: e.importance, reverse=True)
    
    def get_events_by_actor(self, actor: str) -> List[TimelineEvent]:
        """Retourne les événements impliquant un acteur"""
        return [e for e in self.events if actor in e.actors]
    
    def generate_summary(self) -> str:
        """Génère un résumé de la chronologie"""
        total_events = len(self.events)
        if not total_events:
            return "Aucun événement dans la chronologie"
        
        sorted_events = self.get_events_by_date()
        first_event = sorted_events[0]
        last_event = sorted_events[-1]
        
        key_actors = set()
        for event in self.events:
            key_actors.update(event.actors)
        
        summary = f"Chronologie de {total_events} événements\n"
        summary += f"Période : {first_event.get_date_str()} - {last_event.get_date_str()}\n"
        summary += f"Acteurs principaux : {', '.join(list(key_actors)[:5])}"
        
        return summary

@dataclass
class MappingResult:
    """Résultat de cartographie"""
    type: str
    entities: List[Entity]
    relationships: List[Relationship]
    analysis: Dict[str, Any]
    document_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    visualization: Optional[Any] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Trouve une entité par son nom"""
        for entity in self.entities:
            if entity.name == name or name in entity.aliases:
                return entity
        return None
    
    def get_relationships_for_entity(self, entity_name: str) -> List[Relationship]:
        """Retourne toutes les relations d'une entité"""
        return [r for r in self.relationships 
                if r.source == entity_name or r.target == entity_name]
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Calcule des statistiques sur le réseau"""
        # Calculer le degré de chaque nœud
        degrees = {}
        for entity in self.entities:
            relations = self.get_relationships_for_entity(entity.name)
            degrees[entity.name] = len(relations)
        
        # Identifier les hubs
        sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        hubs = [name for name, degree in sorted_degrees[:5]]
        
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'average_degree': sum(degrees.values()) / max(len(degrees), 1),
            'max_degree': max(degrees.values()) if degrees else 0,
            'hubs': hubs,
            'isolated_entities': [e.name for e in self.entities if degrees.get(e.name, 0) == 0]
        }
    
    def to_graph_data(self) -> Dict[str, Any]:
        """Convertit en données pour visualisation graphique"""
        nodes = []
        edges = []
        
        # Créer les nœuds
        for entity in self.entities:
            nodes.append({
                'id': entity.name,
                'label': entity.name,
                'type': entity.type,
                'size': entity.importance * 50,  # Taille proportionnelle à l'importance
                'attributes': entity.attributes
            })
        
        # Créer les arêtes
        for rel in self.relationships:
            edges.append({
                'source': rel.source,
                'target': rel.target,
                'type': rel.type,
                'weight': rel.strength,
                'directed': rel.direction == "unidirectional"
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.get_network_stats()
        }

@dataclass
class ComparisonResult:
    """Résultat de comparaison de documents"""
    type: str  # versions, témoignages, documents, chronologies
    document_count: int
    comparison: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    visualizations: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    differences: List[Dict[str, Any]] = field(default_factory=list)
    similarities: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_difference(self, category: str, doc1_content: str, doc2_content: str, importance: int = 5):
        """Ajoute une différence identifiée"""
        self.differences.append({
            'category': category,
            'doc1': doc1_content,
            'doc2': doc2_content,
            'importance': importance,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_similarity(self, category: str, content: str, confidence: float = 0.8):
        """Ajoute une similarité identifiée"""
        self.similarities.append({
            'category': category,
            'content': content,
            'confidence': confidence
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Génère un résumé de la comparaison"""
        return {
            'documents_compared': self.document_count,
            'differences_found': len(self.differences),
            'similarities_found': len(self.similarities),
            'major_differences': len([d for d in self.differences if d.get('importance', 5) >= 7]),
            'categories': list(set(d['category'] for d in self.differences))
        }

@dataclass
class SynthesisResult:
    """Résultat de synthèse de documents"""
    content: str
    piece_count: int
    categories: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    key_points: List[str] = field(default_factory=list)
    chronology: Optional[List[TimelineEvent]] = None
    legal_points: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    confidence: float = 0.8
    
    def add_key_point(self, point: str, source: Optional[str] = None):
        """Ajoute un point clé"""
        self.key_points.append(point)
        if source and source not in self.sources_used:
            self.sources_used.append(source)
    
    def add_legal_point(self, point: str, articles: List[str] = None):
        """Ajoute un point d'attention juridique"""
        legal_point = point
        if articles:
            legal_point += f" (Articles : {', '.join(articles)})"
        self.legal_points.append(legal_point)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'piece_count': self.piece_count,
            'categories': self.categories,
            'timestamp': self.timestamp.isoformat(),
            'key_points': self.key_points,
            'has_chronology': self.chronology is not None,
            'legal_points': self.legal_points,
            'recommendations': self.recommendations,
            'sources_count': len(self.sources_used),
            'confidence': self.confidence
        }

# ========== SESSION ET COMMUNICATION ==========

@dataclass
class Session:
    """Session utilisateur avec état de travail"""
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    documents: Dict[str, Document] = field(default_factory=dict)
    search_history: List[QueryAnalysis] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    # État de travail
    current_case: Optional[CasJuridique] = None
    selected_pieces: List[PieceSelectionnee] = field(default_factory=list)
    draft_documents: Dict[str, RedactionResult] = field(default_factory=dict)
    analysis_results: Dict[str, AnalysisResult] = field(default_factory=dict)
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Vérifie si la session a expiré"""
        return (datetime.now() - self.last_activity).seconds > timeout_minutes * 60
    
    def update_activity(self):
        """Met à jour l'heure de dernière activité"""
        self.last_activity = datetime.now()
    
    def add_search(self, query_analysis: QueryAnalysis):
        """Ajoute une recherche à l'historique"""
        self.search_history.append(query_analysis)
        self.update_activity()
    
    def save_draft(self, doc_type: str, result: RedactionResult):
        """Sauvegarde un brouillon de document"""
        self.draft_documents[doc_type] = result
        self.update_activity()
    
    def get_recent_searches(self, n: int = 10) -> List[QueryAnalysis]:
        """Retourne les N dernières recherches"""
        return self.search_history[-n:]
    
    def export_work(self) -> Dict[str, Any]:
        """Exporte tout le travail de la session"""
        return {
            'session_id': self.id,
            'created_at': self.created_at.isoformat(),
            'duration_minutes': int((self.last_activity - self.created_at).seconds / 60),
            'documents_count': len(self.documents),
            'searches_count': len(self.search_history),
            'drafts_count': len(self.draft_documents),
            'analyses_count': len(self.analysis_results),
            'current_case': self.current_case.to_dict() if self.current_case else None,
            'selected_pieces_count': len(self.selected_pieces)
        }

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
    is_encrypted: bool = False
    requires_receipt: bool = False
    
    def add_attachment(self, filename: str, data: bytes, mime_type: str = "application/octet-stream"):
        """Ajoute une pièce jointe"""
        self.attachments.append({
            'filename': filename,
            'data': data,
            'mime_type': mime_type,
            'size': len(data)
        })
    
    def add_document_attachment(self, doc: Document):
        """Ajoute un document comme pièce jointe"""
        self.add_attachment(
            f"{doc.title}.txt",
            doc.content.encode('utf-8'),
            'text/plain'
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Valide la configuration email"""
        errors = []
        
        if not self.to:
            errors.append("Au moins un destinataire requis")
        
        if not self.subject:
            errors.append("Objet requis")
        
        if not self.body:
            errors.append("Corps du message requis")
        
        # Vérifier les adresses email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in self.to + self.cc + self.bcc:
            if not re.match(email_pattern, email):
                errors.append(f"Adresse email invalide : {email}")
        
        return len(errors) == 0, errors

# ========== HELPERS ET UTILITIES ==========

class SourceTracker:
    """Classe helper pour gérer la traçabilité complète des sources"""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.facts: Dict[str, FactWithSource] = {}
        self.source_cache: Dict[str, SourceReference] = {}
        self.elements_procedure: Dict[str, ElementProcedure] = {}
        self.pieces_versees: Dict[str, PieceVersee] = {}
        self.cas_juridiques: Dict[str, CasJuridique] = {}
    
    def register_document(self, doc: Document) -> str:
        """Enregistre un document et retourne son ID"""
        self.documents[doc.id] = doc
        return doc.id
    
    def create_source_reference(self, document_id: str, **kwargs) -> SourceReference:
        """Crée une référence de source"""
        if document_id not in self.documents:
            raise ValueError(f"Document {document_id} non trouvé")
        
        doc = self.documents[document_id]
        source_ref = SourceReference(
            document_id=document_id,
            document_title=doc.title,
            **kwargs
        )
        
        # Cache pour éviter les doublons
        cache_key = f"{document_id}_{kwargs.get('page')}_{kwargs.get('paragraph')}"
        self.source_cache[cache_key] = source_ref
        
        return source_ref
    
    def create_fact(self, content: str, category: str, source_refs: List[SourceReference]) -> FactWithSource:
        """Crée un fait avec ses sources"""
        fact = FactWithSource(
            id=f"fact_{len(self.facts)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            content=content,
            category=category,
            sources=source_refs,
            verified=bool(source_refs)
        )
        self.facts[fact.id] = fact
        return fact
    
    def create_element_procedure(self, type_acte: str, intitule: str, 
                               date: datetime, auteur: str, **kwargs) -> ElementProcedure:
        """Crée un élément de procédure tracé"""
        element = ElementProcedure(
            id=f"proc_{type_acte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=type_acte,
            intitule=intitule,
            date=date,
            auteur=auteur,
            **kwargs
        )
        self.elements_procedure[element.id] = element
        return element
    
    def create_piece_versee(self, numero: int, cote: str, intitule: str, 
                          partie_versante: str, **kwargs) -> PieceVersee:
        """Crée une pièce versée aux débats"""
        piece = PieceVersee(
            id=f"piece_{cote}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            numero_ordre=numero,
            cote=cote,
            intitule=intitule,
            partie_versante=partie_versante,
            **kwargs
        )
        self.pieces_versees[piece.id] = piece
        return piece
    
    def link_piece_to_facts(self, piece_id: str, fact_ids: List[str]):
        """Lie une pièce aux faits qu'elle établit"""
        if piece_id not in self.pieces_versees:
            raise ValueError(f"Pièce {piece_id} non trouvée")
        
        piece = self.pieces_versees[piece_id]
        for fact_id in fact_ids:
            if fact_id in self.facts:
                piece.facts_etablis.append(self.facts[fact_id])
    
    def link_element_to_sources(self, element_id: str, source_refs: List[SourceReference]):
        """Lie un élément de procédure à ses sources"""
        if element_id not in self.elements_procedure:
            raise ValueError(f"Élément {element_id} non trouvé")
        
        element = self.elements_procedure[element_id]
        element.source_references.extend(source_refs)
    
    def find_documents_by_reference(self, reference: str) -> List[Document]:
        """Trouve tous les documents correspondant à une référence @"""
        ref_clean = reference.replace('@', '').strip().lower()
        matching_docs = []
        
        for doc in self.documents.values():
            if doc.has_reference(ref_clean):
                matching_docs.append(doc)
        
        return matching_docs
    
    def generate_source_report(self) -> Dict[str, Any]:
        """Génère un rapport global sur les sources utilisées"""
        return {
            'total_documents': len(self.documents),
            'total_facts': len(self.facts),
            'facts_with_sources': len([f for f in self.facts.values() if f.sources]),
            'facts_without_sources': len([f for f in self.facts.values() if not f.sources]),
            'total_elements_procedure': len(self.elements_procedure),
            'total_pieces_versees': len(self.pieces_versees),
            'pieces_contestees': len([p for p in self.pieces_versees.values() if p.contestee]),
            'source_distribution': self._get_source_distribution(),
            'procedure_distribution': {
                type_acte: len([e for e in self.elements_procedure.values() if e.type == type_acte])
                for type_acte in set(e.type for e in self.elements_procedure.values())
            }
        }
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """Analyse la distribution des sources"""
        distribution = {}
        
        # Sources des faits
        for fact in self.facts.values():
            for source in fact.sources:
                doc_title = source.document_title
                distribution[doc_title] = distribution.get(doc_title, 0) + 1
        
        # Sources des éléments de procédure
        for element in self.elements_procedure.values():
            for source in element.source_references:
                doc_title = source.document_title
                distribution[doc_title] = distribution.get(doc_title, 0) + 1
        
        # Sources des pièces
        for piece in self.pieces_versees.values():
            for source in piece.source_references:
                doc_title = source.document_title
                distribution[doc_title] = distribution.get(doc_title, 0) + 1
        
        return distribution

class DocumentFormatter:
    """Classe pour formater les documents avec liens sources"""
    
    def __init__(self, source_tracker: SourceTracker):
        self.tracker = source_tracker
    
    def format_with_sources(self, content: str, fact_ids: List[str]) -> str:
        """Formate un contenu en ajoutant les liens vers les sources"""
        fact_map = {fid: self.tracker.facts[fid] for fid in fact_ids if fid in self.tracker.facts}
        return inject_source_links(content, fact_map)
    
    def format_plaidoirie_with_sources(self, plaidoirie: PlaidoirieResult) -> str:
        """Formate une plaidoirie avec tous les liens sources"""
        content = plaidoirie.content
        
        # Ajouter les liens pour chaque paragraphe
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for i, para in enumerate(paragraphs):
            # Si des sources sont mappées pour ce paragraphe
            if i in plaidoirie.source_mapping:
                sources = plaidoirie.source_mapping[i]
                # Ajouter une note de bas de page avec les sources
                source_notes = []
                for j, source in enumerate(sources):
                    note_num = f"{i+1}.{j+1}"
                    para += f"[^{note_num}]"
                    source_notes.append(f"[^{note_num}]: {source.get_citation()}")
                
                formatted_paragraphs.append(para)
                if source_notes:
                    formatted_paragraphs.append("\n".join(source_notes))
            else:
                formatted_paragraphs.append(para)
        
        return "\n\n".join(formatted_paragraphs)
    
    def generate_source_footnotes(self, sources: List[SourceReference]) -> str:
        """Génère des notes de bas de page pour les sources"""
        footnotes = []
        for i, source in enumerate(sources, 1):
            citation = source.get_citation()
            if source.excerpt:
                citation += f' - "{source.excerpt}"'
            footnotes.append(f"[^{i}]: {citation}")
        
        return "\n".join(footnotes)
    
    def create_hyperlinked_document(self, doc_type: str, content: str, 
                                  sources: List[SourceReference]) -> str:
        """Crée un document avec hyperliens vers les sources"""
        header = f"# {doc_type.upper()}\n\n"
        header += f"*Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n\n"
        
        # Ajouter un sommaire des sources
        header += "## Sources utilisées\n\n"
        for i, source in enumerate(sources, 1):
            header += f"{i}. {source.get_citation()}\n"
        header += "\n---\n\n"
        
        # Contenu avec notes
        footer = "\n\n---\n\n## Notes et références\n\n"
        footer += self.generate_source_footnotes(sources)
        
        return header + content + footer

# ========== FONCTIONS HELPER ==========

def get_all_juridictions() -> List[str]:
    """Retourne la liste de toutes les juridictions"""
    return [j.value for j in TypeJuridiction]

def get_juridiction_type(juridiction_name: str) -> Optional[TypeJuridiction]:
    """Retourne le type de juridiction à partir du nom"""
    for jur_type in TypeJuridiction:
        if jur_type.value.lower() == juridiction_name.lower():
            return jur_type
    return None

def format_source_link(source_ref: SourceReference, text: str) -> str:
    """Formate un texte avec un lien vers sa source"""
    # Format : [texte](source:document_id#page_X_para_Y)
    link_parts = [f"source:{source_ref.document_id}"]
    if source_ref.page:
        link_parts.append(f"page_{source_ref.page}")
    if source_ref.paragraph:
        link_parts.append(f"para_{source_ref.paragraph}")
    
    link = "#".join(link_parts)
    return f"[{text}]({link})"

def format_piece_link(piece: PieceVersee, text: str) -> str:
    """Formate un texte avec un lien vers une pièce"""
    # Format : [texte](piece:cote)
    return f"[{text}](piece:{piece.cote})"

def format_procedure_link(element: ElementProcedure, text: str) -> str:
    """Formate un texte avec un lien vers un élément de procédure"""
    # Format : [texte](procedure:element_id)
    return f"[{text}](procedure:{element.id})"

def parse_source_link(link: str) -> Optional[Dict[str, Any]]:
    """Parse un lien source pour extraire ses composants"""
    # Pattern : [texte](type:reference#details)
    pattern = r'\[([^\]]+)\]\((\w+):([^#\)]+)(?:#([^\)]+))?\)'
    match = re.match(pattern, link)
    
    if not match:
        return None
    
    text, link_type, reference, details = match.groups()
    
    result = {
        'text': text,
        'type': link_type,
        'reference': reference
    }
    
    # Parser les détails si présents
    if details:
        detail_parts = details.split('_')
        if 'page' in details:
            result['page'] = int(detail_parts[1])
        if 'para' in details:
            result['paragraph'] = int(detail_parts[-1])
    
    return result

def inject_source_links(text: str, fact_map: Dict[str, FactWithSource]) -> str:
    """Injecte automatiquement les liens sources dans un texte"""
    # Cette fonction recherche les faits dans le texte et ajoute les liens
    for fact_id, fact in fact_map.items():
        if fact.content in text and fact.sources:
            # Prendre la première source
            source = fact.sources[0]
            linked_text = format_source_link(source, fact.content)
            text = text.replace(fact.content, linked_text, 1)
    
    return text

def extract_parties_from_query(query: str) -> Dict[str, List[str]]:
    """Extrait les parties mentionnées dans une requête"""
    parties = {
        'demandeurs': [],
        'defendeurs': []
    }
    
    query_lower = query.lower()
    
    # Patterns pour les demandeurs (entreprises BTP principalement)
    demandeurs_patterns = [
        ('interconstruction', 'INTERCONSTRUCTION'),
        ('vinci', 'VINCI'),
        ('sogeprom', 'SOGEPROM RÉALISATIONS'),
        ('demathieu bard', 'DEMATHIEU BARD'),
        ('bouygues', 'BOUYGUES'),
        ('eiffage', 'EIFFAGE'),
        ('spie', 'SPIE BATIGNOLLES'),
        ('leon grosse', 'LEON GROSSE'),
        ('fayat', 'FAYAT'),
        ('colas', 'COLAS'),
        ('eurovia', 'EUROVIA'),
        ('razel-bec', 'RAZEL-BEC'),
        ('nge', 'NGE'),
        ('gtm', 'GTM Bâtiment')
    ]
    
    # Patterns pour les défendeurs
    defendeurs_patterns = [
        ('perinet', 'M. PERINET'),
        ('périnet', 'M. PÉRINET'),
        ('vp invest', 'VP INVEST'),
        ('perraud', 'M. PERRAUD'),
        ('martin', 'M. MARTIN'),
        ('dupont', 'M. DUPONT'),
        ('durand', 'M. DURAND'),
        ('laurent', 'M. LAURENT'),
        ('michel', 'M. MICHEL')
    ]
    
    # Analyser la structure de la requête
    if ' pour ' in query_lower and ' contre ' in query_lower:
        # Extraire les parties selon la structure
        partie_pour = query_lower.split(' pour ')[1].split(' contre ')[0]
        partie_contre = query_lower.split(' contre ')[1]
        
        # Chercher les demandeurs
        for keyword, nom_formate in demandeurs_patterns:
            if keyword in partie_pour:
                parties['demandeurs'].append(nom_formate)
        
        # Chercher les défendeurs
        for keyword, nom_formate in defendeurs_patterns:
            if keyword in partie_contre:
                parties['defendeurs'].append(nom_formate)
    else:
        # Recherche globale
        if ' contre ' in query_lower:
            partie_contre = query_lower.split(' contre ')[1]
            for keyword, nom_formate in defendeurs_patterns:
                if keyword in partie_contre:
                    parties['defendeurs'].append(nom_formate)
        
        # Chercher les demandeurs dans le reste
        for keyword, nom_formate in demandeurs_patterns:
            if keyword in query_lower and nom_formate not in parties['defendeurs']:
                if ' contre ' not in query_lower or keyword not in query_lower.split(' contre ')[1]:
                    parties['demandeurs'].append(nom_formate)
    
    return parties

def extract_infractions_from_query(query: str) -> List[str]:
    """Extrait les infractions mentionnées dans une requête"""
    query_lower = query.lower()
    infractions = []
    
    infractions_keywords = {
        'escroquerie': 'Escroquerie (art. 313-1 Code pénal)',
        'abus de confiance': 'Abus de confiance (art. 314-1 Code pénal)',
        'abus de biens sociaux': 'Abus de biens sociaux (art. L241-3 et L242-6 Code de commerce)',
        'abs': 'Abus de biens sociaux (art. L241-3 et L242-6 Code de commerce)',
        'faux': 'Faux et usage de faux (art. 441-1 Code pénal)',
        'corruption': 'Corruption (art. 432-11 et 433-1 Code pénal)',
        'trafic d\'influence': 'Trafic d\'influence (art. 432-11 et 433-2 Code pénal)',
        'favoritisme': 'Favoritisme (art. 432-14 Code pénal)',
        'prise illégale': 'Prise illégale d\'intérêts (art. 432-12 Code pénal)',
        'blanchiment': 'Bl