# config/app_config.py
"""Configuration principale de l'application juridique"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import os

# Énumérations
class SearchMode(Enum):
    """Modes de recherche disponibles"""
    SIMPLE = "simple"
    ADVANCED = "advanced"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    LEGAL = "legal"

class LLMProvider(Enum):
    """Fournisseurs d'IA disponibles"""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic Claude"
    MISTRAL = "Mistral AI"
    GROQ = "Groq"
    GOOGLE = "Google Gemini"
    LOCAL = "Local LLM"

class DocumentType(Enum):
    """Types de documents juridiques"""
    CONCLUSIONS = "conclusions"
    PLAINTE = "plainte"
    CONSTITUTION_PC = "constitution_pc"
    MISE_EN_DEMEURE = "mise_en_demeure"
    ASSIGNATION = "assignation"
    REQUETE = "requete"
    MEMOIRE = "memoire"
    COURRIER = "courrier"
    NOTE = "note"
    CONTRAT = "contrat"

class IntentType(Enum):
    """Types d'intentions détectées"""
    REDACTION = "redaction"
    RECHERCHE = "recherche"
    ANALYSE = "analyse"
    TIMELINE = "timeline"
    MAPPING = "mapping"
    COMPARISON = "comparison"
    IMPORT = "import"
    EXPORT = "export"
    EMAIL = "email"
    PIECES = "pieces"
    BORDEREAU = "bordereau"
    SYNTHESE = "synthese"
    TEMPLATE = "template"
    JURISPRUDENCE = "jurisprudence"
    PLAIDOIRIE = "plaidoirie"
    PREPARATION_CLIENT = "preparation_client"
    QUESTIONS_REPONSES = "questions_reponses"

# Prompts d'analyse pour les affaires
ANALYSIS_PROMPTS_AFFAIRES = {
    "identification_parties": """Identifie toutes les parties mentionnées dans ces documents.
Pour chaque partie, précise :
- Nom complet
- Rôle (demandeur, défendeur, témoin, expert, etc.)
- Type (personne physique, morale, autorité)
- Coordonnées si disponibles
- Relations avec les autres parties""",
    
    "chronologie_faits": """Établis une chronologie détaillée des faits.
Pour chaque événement :
- Date précise ou période
- Description de l'événement
- Parties impliquées
- Lieu
- Sources/preuves
- Importance juridique""",
    
    "analyse_infractions": """Analyse les infractions potentielles.
Pour chaque infraction :
- Qualification juridique précise
- Articles de loi applicables
- Éléments constitutifs
- Preuves disponibles
- Parties concernées
- Sanctions encourues""",
    
    "evaluation_preuves": """Évalue les preuves disponibles.
Pour chaque preuve :
- Type (document, témoignage, expertise, etc.)
- Force probante
- Admissibilité
- Parties concernées
- Points à prouver
- Faiblesses éventuelles""",
    
    "strategie_defense": """Propose une stratégie de défense.
Inclure :
- Moyens de défense principaux
- Arguments subsidiaires
- Exceptions de procédure
- Demandes reconventionnelles
- Preuves à produire
- Témoins à citer""",
    
    "risques_juridiques": """Identifie tous les risques juridiques.
Pour chaque risque :
- Nature du risque
- Probabilité (faible/moyenne/élevée)
- Impact potentiel
- Mesures préventives
- Stratégies d'atténuation
- Urgence d'action"""
}

# Configuration des endpoints
@dataclass
class APIConfig:
    """Configuration des API externes"""
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 4000
    
    # Anthropic
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = "claude-3-opus-20240229"
    anthropic_temperature: float = 0.7
    anthropic_max_tokens: int = 4000
    
    # Mistral
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    mistral_model: str = "mistral-large-latest"
    mistral_temperature: float = 0.7
    mistral_max_tokens: int = 4000
    
    # Groq
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = "mixtral-8x7b-32768"
    groq_temperature: float = 0.7
    groq_max_tokens: int = 32768
    
    # Google
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_model: str = "gemini-pro"
    google_temperature: float = 0.7
    google_max_tokens: int = 4000
    
    # Azure
    azure_storage_connection: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    azure_search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    azure_search_key: str = os.getenv("AZURE_SEARCH_KEY", "")
    azure_search_index: str = os.getenv("AZURE_SEARCH_INDEX", "default-index")

# Configuration de l'application
@dataclass
class AppConfig:
    """Configuration générale de l'application"""
    app_name: str = "LegalAI Assistant"
    version: str = "2.0.0"
    debug: bool = False
    
    # Limites
    max_file_size_mb: int = 50
    max_files_per_upload: int = 10
    max_search_results: int = 100
    max_document_length: int = 1000000
    
    # Temps
    cache_ttl_seconds: int = 3600
    session_timeout_minutes: int = 60
    
    # Features flags
    enable_azure_storage: bool = True
    enable_azure_search: bool = True
    enable_multi_llm: bool = True
    enable_jurisprudence: bool = True
    enable_email: bool = True
    
    # Chemins
    temp_dir: str = "/tmp/legalai"
    upload_dir: str = "/tmp/legalai/uploads"
    export_dir: str = "/tmp/legalai/exports"
    
    # Email
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")

# Styles de rédaction
REDACTION_STYLES = {
    'formel': {
        'name': 'Formel',
        'description': 'Style juridique classique et solennel',
        'tone': 'respectueux et distant',
        'vocabulary': 'technique et précis',
        'structure': 'rigoureuse et hiérarchisée'
    },
    'persuasif': {
        'name': 'Persuasif', 
        'description': 'Style argumentatif et convaincant',
        'tone': 'assertif et engagé',
        'vocabulary': 'percutant et imagé',
        'structure': 'dynamique et progressive'
    },
    'technique': {
        'name': 'Technique',
        'description': 'Style factuel et détaillé',
        'tone': 'neutre et objectif',
        'vocabulary': 'spécialisé et exhaustif',
        'structure': 'analytique et méthodique'
    },
    'synthétique': {
        'name': 'Synthétique',
        'description': 'Style concis et efficace',
        'tone': 'direct et clair',
        'vocabulary': 'simple et précis',
        'structure': 'condensée et essentielle'
    },
    'pédagogique': {
        'name': 'Pédagogique',
        'description': 'Style explicatif et accessible',
        'tone': 'bienveillant et didactique',
        'vocabulary': 'vulgarisé et illustré',
        'structure': 'progressive et exemplifiée'
    }
}

# Templates de documents juridiques
DOCUMENT_TEMPLATES = {
    'conclusions_defense': {
        'name': 'Conclusions en défense',
        'type': DocumentType.CONCLUSIONS,
        'structure': [
            'POUR : [Client]',
            'CONTRE : [Partie adverse]',
            'DEVANT : [Juridiction]',
            '',
            'PLAISE AU TRIBUNAL',
            '',
            'I. FAITS ET PROCÉDURE',
            '   A. Rappel des faits',
            '   B. Procédure antérieure',
            '',
            'II. DISCUSSION',
            '   A. Sur la recevabilité',
            '   B. Sur le fond',
            '      1. Sur la qualification juridique',
            '      2. Sur l\'absence d\'élément intentionnel',
            '      3. Sur l\'absence de préjudice',
            '',
            'III. SUR LES DEMANDES ADVERSES',
            '',
            'PAR CES MOTIFS',
            '',
            'Il est demandé au Tribunal de :',
            '- REJETER l\'ensemble des demandes adverses',
            '- RELAXER purement et simplement le prévenu',
            '- CONDAMNER la partie civile aux dépens'
        ],
        'style': 'formel',
        'min_length': 3000
    },
    'plainte_simple': {
        'name': 'Plainte simple',
        'type': DocumentType.PLAINTE,
        'structure': [
            'Monsieur le Procureur de la République',
            'Tribunal Judiciaire de [Ville]',
            '',
            'OBJET : Dépôt de plainte',
            '',
            'Monsieur le Procureur,',
            '',
            'J\'ai l\'honneur de porter plainte contre :',
            '[Identité du mis en cause ou X]',
            '',
            'EXPOSÉ DES FAITS',
            '',
            'QUALIFICATION JURIDIQUE',
            '',
            'PRÉJUDICES SUBIS',
            '',
            'DEMANDES',
            '',
            'PIÈCES JOINTES',
            '',
            'Je me tiens à votre disposition...',
            '',
            'Veuillez agréer...'
        ],
        'style': 'formel',
        'min_length': 1500
    }
}

# Phrases types juridiques
LEGAL_PHRASES = {
    'introductions': [
        "Il résulte des pièces du dossier que",
        "Il est constant que",
        "Force est de constater que",
        "Il convient de relever que",
        "Il y a lieu de considérer que"
    ],
    'transitions': [
        "Au surplus",
        "En outre",
        "Par ailleurs",
        "De surcroît",
        "Au demeurant"
    ],
    'conclusions': [
        "En conséquence",
        "Dès lors",
        "Il s'ensuit que",
        "Partant",
        "Au vu de ce qui précède"
    ],
    'refutations': [
        "Contrairement à ce qui est soutenu",
        "C'est à tort que",
        "Il ne saurait être sérieusement contesté que",
        "L'argumentation adverse ne résiste pas à l'analyse",
        "Cette prétention doit être écartée"
    ]
}

# Configuration des analyses
ANALYSIS_CONFIG = {
    'timeline': {
        'max_events': 100,
        'date_formats': ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'],
        'keywords': ['le', 'en date du', 'à la date du', 'depuis le', 'jusqu\'au']
    },
    'mapping': {
        'entity_types': ['personne', 'société', 'organisation', 'lieu', 'juridiction'],
        'relation_types': ['contractuelle', 'hiérarchique', 'familiale', 'conflictuelle'],
        'min_confidence': 0.7
    },
    'comparison': {
        'similarity_threshold': 0.8,
        'key_sections': ['faits', 'moyens', 'dispositif', 'demandes'],
        'comparison_metrics': ['convergence', 'divergence', 'contradiction']
    }
}

# Messages d'erreur
ERROR_MESSAGES = {
    'no_llm': "❌ Aucune IA n'est configurée. Veuillez ajouter des clés API.",
    'no_documents': "⚠️ Aucun document disponible pour cette opération.",
    'invalid_format': "❌ Format de fichier non supporté.",
    'size_limit': "❌ Le fichier dépasse la taille limite autorisée.",
    'processing_error': "❌ Erreur lors du traitement. Veuillez réessayer.",
    'connection_error': "❌ Erreur de connexion. Vérifiez votre connexion internet."
}

# Messages de succès
SUCCESS_MESSAGES = {
    'import_complete': "✅ Import terminé avec succès",
    'export_complete': "✅ Export généré avec succès",
    'analysis_complete': "✅ Analyse terminée",
    'document_created': "✅ Document créé avec succès",
    'email_sent': "✅ Email envoyé avec succès"
}

# Instance globale de configuration
app_config = AppConfig()
api_config = APIConfig()