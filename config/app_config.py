# config/app_config.py
"""Configuration centralisée de l'application"""

import os
from enum import Enum

# Configuration de l'application
APP_CONFIG = {
    'TITLE': 'Assistant Pénal des Affaires IA',
    'VERSION': '3.0.0',
    'ICON': '⚖️',
    'PAGES': {
        'Recherche de documents': '🔍',
        'Sélection de pièces': '📁',
        'Analyse IA': '🤖',
        'Rédaction assistée': '📝',
        'Rédaction de courrier': '✉️',
        'Import/Export': '📥',
        'Configuration': '⚙️'
    },
    'PAGE_SIZE': 10,
    'MAX_FILE_SIZE': 10 * 1024 * 1024,
    'DEFAULT_CONTAINER': 'sharepoint-documents',
    'EXPORT_FORMAT': '%Y%m%d_%H%M%S',
    'SEARCH_INDEX_NAME': 'juridique-index',
    'VECTOR_DIMENSION': 1536
}

# Configuration des APIs juridiques avec clés intégrées
LEGAL_APIS = {
    "judilibre": {
        "enabled": True,
        "base_url": "https://api.piste.gouv.fr/cassation/judilibre/v1",
        "api_key": "ac72ad69-ef21-4af2-b3e2-6fa1132a8348",
        "client_secret": "ec344bdb-c1f0-482c-ac1e-bb9254ae6adb",
        "endpoints": {
            "search": "/search",
            "decision": "/decision",
            "export": "/export"
        }
    },
    "legifrance": {
        "enabled": True,
        "base_url": "https://api.piste.gouv.fr/dila/legifrance/v1",
        "oauth_url": "https://oauth.piste.gouv.fr/api/oauth/token",
        "client_id": "ac72ad69-ef21-4af2-b3e2-6fa1132a8348",
        "client_secret": "ec344bdb-c1f0-482c-ac1e-bb9254ae6adb",
        "endpoints": {
            "search": "/search",
            "consult": "/consult",
            "download": "/download"
        }
    }
}

# Délais de prescription
PRESCRIPTION_CONFIG = {
    'CONTRAVENTION': 1,  # an
    'DELIT': 6,  # ans
    'CRIME': 20,  # ans
    'FRAUDE_FISCALE': 6,  # ans
    'TRAVAIL_DISSIMULE': 6  # ans
}

# Formats de citation
CITATION_FORMATS = {
    'jurisprudence': "{juridiction}, {date}, n° {numero}",
    'article_code': "Art. {numero} {code}",
    'doctrine': "{auteur}, « {titre} », {revue} {annee}, n° {numero}, p. {page}",
    'circulaire': "Circ. {reference} du {date}",
    'reponse_ministerielle': "Rép. min. n° {numero}, {date}"
}

# Types d'infractions
class InfractionAffaires(Enum):
    """Types d'infractions en droit pénal des affaires"""
    ABS = "Abus de biens sociaux"
    ABUS_CONFIANCE = "Abus de confiance"
    CORRUPTION = "Corruption"
    TRAFIC_INFLUENCE = "Trafic d'influence"
    PRISE_ILLEGALE = "Prise illégale d'intérêts"
    FAVORITISME = "Favoritisme"
    BLANCHIMENT = "Blanchiment"
    FRAUDE_FISCALE = "Fraude fiscale"
    ESCROQUERIE = "Escroquerie"
    FAUX_USAGE_FAUX = "Faux et usage de faux"
    BANQUEROUTE = "Banqueroute"
    DELIT_INITIE = "Délit d'initié"
    MANIPULATION_COURS = "Manipulation de cours"
    ENTRAVE = "Entrave"
    TRAVAIL_DISSIMULE = "Travail dissimulé"
    HARCELEMENT = "Harcèlement moral/sexuel"
    MISE_DANGER = "Mise en danger d'autrui"
    BLESSURES_INVOLONTAIRES = "Blessures involontaires"
    POLLUTION = "Atteinte à l'environnement"
    AUTRE = "Autre infraction"

# Modes de recherche
class SearchMode(Enum):
    """Modes de recherche disponibles"""
    HYBRID = "Recherche hybride (textuelle + sémantique)"
    TEXT_ONLY = "Recherche textuelle uniquement"
    VECTOR_ONLY = "Recherche vectorielle uniquement"
    LOCAL = "Recherche locale uniquement"

# Providers LLM
class LLMProvider(Enum):
    """Providers LLM disponibles"""
    AZURE_OPENAI = "Azure OpenAI (GPT-4)"
    CLAUDE_OPUS = "Claude Opus 4"
    CHATGPT_4O = "ChatGPT 4o"
    GEMINI = "Google Gemini"
    PERPLEXITY = "Perplexity AI"

# Configuration des LLMs
def get_llm_configs():
    """Retourne la configuration des LLMs"""
    return {
        LLMProvider.AZURE_OPENAI: {
            'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'key': os.getenv('AZURE_OPENAI_KEY'),
            'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
            'api_version': '2024-02-01'
        },
        LLMProvider.CLAUDE_OPUS: {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'model': 'claude-3-opus-20240229'
        },
        LLMProvider.CHATGPT_4O: {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': 'gpt-4-turbo-preview'
        },
        LLMProvider.GEMINI: {
            'api_key': os.getenv('GOOGLE_API_KEY'),
            'model': 'gemini-pro'
        },
        LLMProvider.PERPLEXITY: {
            'api_key': os.getenv('PERPLEXITY_API_KEY'),
            'model': 'pplx-70b-online'
        }
    }

# Prompts d'analyse
ANALYSIS_PROMPTS_AFFAIRES = {
    "🎯 Analyse infractions économiques": [
        "Analysez précisément les éléments constitutifs de l'infraction reprochée",
        "Identifiez l'élément intentionnel et les moyens de le contester",
        "Recherchez les causes d'exonération ou d'atténuation",
        "Proposez une stratégie axée sur la bonne foi et l'intérêt social"
    ],
    "🏢 Responsabilité personne morale": [
        "Vérifiez les conditions d'imputation à la personne morale",
        "Analysez si les faits ont été commis pour le compte de la PM",
        "Examinez le rôle des organes et représentants",
        "Évaluez l'impact d'une éventuelle délégation de pouvoirs"
    ],
    "🛡️ Moyens de défense affaires": [
        "Valorisez le programme de conformité existant",
        "Démontrez les mesures correctives prises",
        "Argumentez sur l'absence d'enrichissement personnel",
        "Mettez en avant la transparence et la bonne gouvernance"
    ],
    "💰 Enjeux financiers": [
        "Calculez précisément le préjudice allégué",
        "Contestez les méthodes de calcul du préjudice",
        "Évaluez l'impact financier des sanctions encourues",
        "Proposez des modalités de réparation adaptées"
    ]
}