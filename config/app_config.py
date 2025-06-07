# config/app_config.py
"""Configuration centralisée de l'application avec toutes les fonctionnalités"""

import os
from enum import Enum

# Informations application
APP_TITLE = "Assistant Pénal des Affaires IA"
APP_VERSION = "3.0.0"
APP_ICON = "⚖️"

# Configuration des pages
PAGES = {
    "Accueil": "🏠",
    "Analyse juridique": "📋",
    "Recherche de jurisprudence": "🔍",
    "Visualisation": "📊", 
    "Assistant interactif": "💬",
    "Configuration": "⚙️"
}

# Types d'infractions en droit pénal des affaires
TYPES_INFRACTIONS = [
    "Abus de biens sociaux",
    "Abus de confiance",
    "Corruption",
    "Trafic d'influence",
    "Prise illégale d'intérêts",
    "Favoritisme",
    "Blanchiment",
    "Fraude fiscale",
    "Escroquerie",
    "Faux et usage de faux",
    "Banqueroute",
    "Délit d'initié",
    "Manipulation de cours",
    "Entrave",
    "Travail dissimulé",
    "Harcèlement moral/sexuel",
    "Mise en danger d'autrui",
    "Blessures involontaires",
    "Atteinte à l'environnement",
    "Autre infraction"
]

# Configuration des modèles LLM
MODELS_CONFIG = {
    "OpenAI": {
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "default": "gpt-4"
    },
    "Anthropic": {
        "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
        "default": "claude-3-opus-20240229"
    },
    "Google": {
        "models": ["gemini-pro"],
        "default": "gemini-pro"
    },
    "Mistral": {
        "models": ["mistral-large-latest", "mistral-medium-latest"],
        "default": "mistral-large-latest"
    },
    "Groq": {
        "models": ["mixtral-8x7b-32768", "llama2-70b-4096"],
        "default": "mixtral-8x7b-32768"
    }
}

# Configuration des LLMs pour MultiLLMManager
class LLMProvider(str):
    AZURE_OPENAI = "Azure OpenAI (GPT-4)"
    CLAUDE_OPUS = "Claude Opus 4"
    CHATGPT_4O = "ChatGPT 4o"
    GEMINI = "Google Gemini"
    PERPLEXITY = "Perplexity AI"

LLM_CONFIGS = {
    LLMProvider.AZURE_OPENAI: {
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        'key': os.getenv('AZURE_OPENAI_KEY', ''),
        'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
        'api_version': '2024-02-01'
    },
    LLMProvider.CLAUDE_OPUS: {
        'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
        'model': 'claude-3-opus-20240229'
    },
    LLMProvider.CHATGPT_4O: {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'model': 'gpt-4-turbo-preview'
    },
    LLMProvider.GEMINI: {
        'api_key': os.getenv('GOOGLE_API_KEY', ''),
        'model': 'gemini-pro'
    },
    LLMProvider.PERPLEXITY: {
        'api_key': os.getenv('PERPLEXITY_API_KEY', ''),
        'model': 'pplx-70b-online'
    }
}

# APIs juridiques
LEGAL_APIS = {
    "Légifrance": {
        "base_url": "https://www.legifrance.gouv.fr/",
        "search_url": "https://www.legifrance.gouv.fr/search/all?tab=all&query=",
        "enabled": True
    },
    "Judilibre": {
        "base_url": "https://www.courdecassation.fr/",
        "search_url": "https://www.courdecassation.fr/recherche-judilibre?search_api_fulltext=",
        "enabled": True
    },
    "Conseil d'État": {
        "base_url": "https://www.conseil-etat.fr/",
        "search_url": "https://www.conseil-etat.fr/arianeweb/",
        "enabled": True
    },
    "EUR-Lex": {
        "base_url": "https://eur-lex.europa.eu/",
        "search_url": "https://eur-lex.europa.eu/search.html?scope=EURLEX&text=",
        "enabled": True
    }
}

# Configuration par défaut
DEFAULT_SETTINGS = {
    "max_tokens": 4000,
    "temperature": 0.7,
    "top_p": 0.9,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0
}

# Formats d'export
EXPORT_FORMATS = {
    "PDF": {"extension": ".pdf", "mime": "application/pdf"},
    "DOCX": {"extension": ".docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "TXT": {"extension": ".txt", "mime": "text/plain"},
    "JSON": {"extension": ".json", "mime": "application/json"}
}

# Configuration du cache
CACHE_CONFIG = {
    "ttl": 3600,
    "max_entries": 1000,
    "persist": True
}

# Messages système
MESSAGES = {
    "welcome": "Bienvenue dans l'Assistant Pénal des Affaires IA",
    "no_documents": "Aucun document sélectionné",
    "analysis_complete": "Analyse terminée avec succès",
    "error_generic": "Une erreur s'est produite",
    "loading": "Chargement en cours..."
}

# Configuration Azure Search
AZURE_SEARCH_CONFIG = {
    'index_name': 'juridique-index',
    'vector_dimension': 1536,
    'endpoint': os.getenv('AZURE_SEARCH_ENDPOINT', ''),
    'key': os.getenv('AZURE_SEARCH_KEY', '')
}

# Container Azure par défaut
DEFAULT_CONTAINER = "sharepoint-documents"

# Formats de citation
CITATION_FORMATS = {
    'jurisprudence': "{juridiction}, {date}, n° {numero}",
    'article_code': "Art. {numero} {code}",
    'doctrine': "{auteur}, « {titre} », {revue} {annee}, n° {numero}, p. {page}",
    'circulaire': "Circ. {reference} du {date}",
    'reponse_ministerielle': "Rép. min. n° {numero}, {date}"
}

# Prompts d'analyse spécialisés
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

# Configuration de la pagination
PAGE_SIZE = 10
MAX_FILE_SIZE = 10 * 1024 * 1024

# Délais de prescription
PRESCRIPTION_CONFIG = {
    "contravention": 1,
    "délit": 6,
    "crime": 20,
    "fraude_fiscale": 6,
    "travail_dissimulé": 6
}