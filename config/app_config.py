# config/app_config.py
"""Configuration principale de l'application juridique"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


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
    PLAINTE_CPC = "plainte_avec_cpc"
    CONSTITUTION_PC = "constitution_pc"
    MISE_EN_DEMEURE = "mise_en_demeure"
    ASSIGNATION = "assignation"
    REQUETE = "requete"
    MEMOIRE = "memoire"
    COURRIER = "courrier"
    NOTE = "note"
    CONTRAT = "contrat"
    PLAIDOIRIE = "plaidoirie"
    DECISION = "decision"
    ARRET = "arret"
    ORDONNANCE = "ordonnance"
    JUGEMENT = "jugement"
    AVIS = "avis"
    RAPPORT = "rapport"
    COMMENTAIRE = "commentaire"
    CONSULTATION = "consultation"

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

# Configuration des APIs juridiques externes
LEGAL_APIS = {
    'doctrine': {
        'name': 'Doctrine.fr',
        'base_url': 'https://api.doctrine.fr/v1/',
        'api_key': os.getenv('DOCTRINE_API_KEY', ''),
        'endpoints': {
            'search': 'search',
            'decision': 'decisions',
            'article': 'articles'
        }
    },
    'legifrance': {
        'name': 'Légifrance',
        'base_url': 'https://api.piste.gouv.fr/cassation/judilibre/v1.0/',
        'api_key': os.getenv('LEGIFRANCE_API_KEY', ''),
        'endpoints': {
            'search': 'search',
            'decision': 'decision',
            'export': 'export'
        }
    },
    'juricaf': {
        'name': 'Juricaf',
        'base_url': 'https://api.juricaf.org/',
        'api_key': os.getenv('JURICAF_API_KEY', ''),
        'endpoints': {
            'search': 'recherche',
            'decision': 'arret'
        }
    },
    'dalloz': {
        'name': 'Dalloz',
        'base_url': 'https://api.dalloz.fr/v1/',
        'api_key': os.getenv('DALLOZ_API_KEY', ''),
        'endpoints': {
            'search': 'search',
            'document': 'documents'
        }
    }
}

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
- Urgence d'action""",
    
    "analyse_infractions_economiques": """Analyse ces documents pour identifier toute infraction économique.
Examine particulièrement :
- Abus de biens sociaux (usage contraire à l'intérêt social)
- Corruption et trafic d'influence
- Fraude fiscale et blanchiment
- Escroquerie et abus de confiance
- Faux et usage de faux
- Infractions boursières
Pour chaque infraction détectée, précise :
1. Qualification juridique exacte
2. Articles du Code pénal ou autres codes applicables
3. Éléments matériels caractérisés
4. Élément intentionnel
5. Préjudice identifié
6. Personnes potentiellement responsables
7. Sanctions encourues""",
    
    "analyse_responsabilites_penales": """Détermine les responsabilités pénales.
Distingue :
1. PERSONNES PHYSIQUES
   - Auteurs principaux
   - Coauteurs
   - Complices
   - Receleurs
2. PERSONNES MORALES
   - Conditions de mise en cause
   - Organes ou représentants impliqués
   - Actes commis pour leur compte
3. CHAÎNE DE RESPONSABILITÉ
   - Liens hiérarchiques
   - Délégations de pouvoir
   - Cumul de responsabilités""",
   
   # Ajout des prompts simplifiés demandés
   'general': "Analyse générale du dossier",
   'risques': "Identification des risques juridiques", 
   'strategie': "Stratégie de défense"
}

# Prompts d'analyse spécialisés pour les infractions
ANALYSIS_PROMPTS_INFRACTIONS = {
    'abus_biens_sociaux': {
        'detection': """Analyse ces documents pour détecter des indices d'abus de biens sociaux.
Recherche:
1. Utilisation de biens sociaux contraire à l'intérêt social
2. Usage personnel des biens de la société
3. Mauvaise foi du dirigeant
4. Préjudice causé à la société
Articles: L241-3 et L242-6 Code de commerce""",
        'elements': ['usage contraire', 'intérêt personnel', 'mauvaise foi', 'préjudice']
    },
    
    'corruption': {
        'detection': """Analyse ces documents pour identifier des faits de corruption.
Recherche:
1. Sollicitation ou agrément d'offres/promesses
2. Dons ou présents
3. Abus d'influence
4. Contrepartie indue
Articles: 432-11, 433-1, 435-1 Code pénal""",
        'elements': ['sollicitation', 'avantage indu', 'contrepartie', 'abus fonction']
    },
    
    'fraude_fiscale': {
        'detection': """Identifie les éléments constitutifs de fraude fiscale.
Recherche:
1. Soustraction frauduleuse à l'impôt
2. Dissimulation de sommes imposables
3. Organisation d'insolvabilité
4. Fausses écritures comptables
Article: 1741 Code général des impôts""",
        'elements': ['dissimulation', 'fausses écritures', 'minoration recettes', 'majoration charges']
    },
    
    'blanchiment': {
        'detection': """Recherche des opérations de blanchiment.
Examine:
1. Facilitation de justification mensongère
2. Concours à placement/dissimulation
3. Produits d'infraction
4. Conversion de biens
Articles: 324-1 et suivants Code pénal""",
        'elements': ['origine frauduleuse', 'dissimulation', 'conversion', 'justification mensongère']
    },
    
    # Ajout des prompts simplifiés demandés
    'identification': "Identifier les infractions",
    'elements_constitutifs': "Analyser les éléments constitutifs",
    'sanctions': "Évaluer les sanctions encourues"
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
    },
    'plainte_avec_cpc': {
        'name': 'Plainte avec constitution de partie civile',
        'type': DocumentType.CONSTITUTION_PC,
        'structure': [
            'Monsieur le Doyen des Juges d\'Instruction',
            'Tribunal Judiciaire de [Ville]',
            '',
            'PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE',
            '',
            'POUR :',
            '[Identité complète du plaignant]',
            'Ayant pour conseil : [Avocat]',
            '',
            'CONTRE :',
            '[Identité du/des mis en cause ou X]',
            '',
            'OBJET : Constitution de partie civile des chefs de [infractions]',
            '',
            'Monsieur le Doyen,',
            '',
            'J\'ai l\'honneur de déposer plainte avec constitution de partie civile entre vos mains.',
            '',
            'I. EXPOSÉ DES FAITS',
            '[Récit chronologique et détaillé]',
            '',
            'II. QUALIFICATION JURIDIQUE',
            '[Analyse juridique des infractions]',
            '',
            'III. PRÉJUDICES',
            'A. Préjudice matériel',
            'B. Préjudice moral',
            'C. Préjudice financier',
            '',
            'IV. DEMANDES',
            '- Constater la constitution de partie civile',
            '- Ordonner une information judiciaire',
            '- Procéder à tous actes utiles',
            '',
            'V. CONSIGNATION',
            'Je verse la consignation fixée',
            '',
            'PIÈCES COMMUNIQUÉES',
            '[Liste numérotée des pièces]',
            '',
            'Veuillez agréer...'
        ],
        'style': 'formel',
        'min_length': 4000
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

# Configuration des durées de prescription
PRESCRIPTIONS = {
    'delit': {
        'duree': 6,
        'unite': 'ans',
        'depart': 'commission des faits'
    },
    'crime': {
        'duree': 20,
        'unite': 'ans',
        'depart': 'commission des faits'
    },
    'contravention': {
        'duree': 1,
        'unite': 'an',
        'depart': 'commission des faits'
    }
}

# Sanctions types par infraction
SANCTIONS_TYPES = {
    'abus_biens_sociaux': {
        'emprisonnement': '5 ans',
        'amende': '375 000 €',
        'complementaires': ['interdiction de gérer', 'interdiction droits civiques']
    },
    'corruption': {
        'emprisonnement': '10 ans',
        'amende': '1 000 000 €',
        'complementaires': ['confiscation', 'interdiction fonction publique']
    },
    'fraude_fiscale': {
        'emprisonnement': '5 ans',
        'amende': '500 000 €',
        'complementaires': ['publication jugement', 'interdiction droits civiques']
    },
    'blanchiment': {
        'emprisonnement': '5 ans',
        'amende': '375 000 €',
        'complementaires': ['confiscation', 'interdiction exercice professionnel']
    },
    'escroquerie': {
        'emprisonnement': '5 ans',
        'amende': '375 000 €',
        'complementaires': ['interdiction chéquier', 'interdiction droits civiques']
    }
}

# Configuration des catégories de documents
DOCUMENT_CATEGORIES = [
    "Procédure",
    "Pièces comptables",
    "Correspondances",
    "Expertises",
    "Témoignages",
    "Contrats",
    "Décisions de justice",
    "Rapports",
    "Auditions",
    "Perquisitions",
    "Commissions rogatoires",
    "Autre"
]

# Configuration des juridictions
JURIDICTIONS = [
    "Tribunal judiciaire",
    "Tribunal de commerce", 
    "Tribunal correctionnel",
    "Cour d'appel",
    "Cour de cassation",
    "Conseil d'État",
    "Tribunal administratif",
    "Cour administrative d'appel",
    "Conseil constitutionnel",
    "Cour d'assises",
    "Tribunal de police",
    "Conseil de prud'hommes",
    "Juge d'instruction",
    "Chambre de l'instruction",
    "Parquet",
    "Parquet National Financier"
]

# Configuration pour l'analyse des risques
RISK_LEVELS = {
    'critical': {
        'label': 'Critique',
        'color': '#FF0000',
        'threshold': 0.8
    },
    'high': {
        'label': 'Élevé',
        'color': '#FF6600',
        'threshold': 0.6
    },
    'medium': {
        'label': 'Moyen',
        'color': '#FFAA00',
        'threshold': 0.4
    },
    'low': {
        'label': 'Faible',
        'color': '#00AA00',
        'threshold': 0.2
    }
}

# Instance globale de configuration
app_config = AppConfig()
api_config = APIConfig()

# Export pour compatibilité avec les imports existants
__all__ = [
    'SearchMode',
    'LLMProvider',
    'DocumentType',
    'IntentType',
    'InfractionAffaires',
    'APIConfig',
    'AppConfig',
    'app_config',
    'api_config',
    'LEGAL_APIS',
    'ANALYSIS_PROMPTS_AFFAIRES',
    'ANALYSIS_PROMPTS_INFRACTIONS',
    'REDACTION_STYLES',
    'DOCUMENT_TEMPLATES',
    'LEGAL_PHRASES',
    'ANALYSIS_CONFIG',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'PRESCRIPTIONS',
    'SANCTIONS_TYPES',
    'DOCUMENT_CATEGORIES',
    'JURIDICTIONS',
    'RISK_LEVELS'
]