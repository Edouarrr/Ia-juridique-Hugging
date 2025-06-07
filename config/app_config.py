# config/app_config.py
"""Configuration centralisée de l'application"""

import os

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

# Configuration des LLMs - AJOUT MANQUANT
LLM_CONFIGS = {
    "AZURE_OPENAI": {
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        'key': os.getenv('AZURE_OPENAI_KEY', ''),
        'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
        'api_version': '2024-02-01'
    },
    "CLAUDE_OPUS": {
        'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
        'model': 'claude-3-opus-20240229'
    },
    "CHATGPT_4O": {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'model': 'gpt-4-turbo-preview'
    },
    "GEMINI": {
        'api_key': os.getenv('GOOGLE_API_KEY', ''),
        'model': 'gemini-pro'
    },
    "PERPLEXITY": {
        'api_key': os.getenv('PERPLEXITY_API_KEY', ''),
        'model': 'pplx-70b-online'
    }
}

# Configuration Azure Search
AZURE_SEARCH_CONFIG = {
    'index_name': 'juridique-index',
    'vector_dimension': 1536,
    'endpoint': os.getenv('AZURE_SEARCH_ENDPOINT', ''),
    'key': os.getenv('AZURE_SEARCH_KEY', '')
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

# Messages système
MESSAGES = {
    "welcome": "Bienvenue dans l'Assistant Pénal des Affaires IA",
    "no_documents": "Aucun document sélectionné",
    "analysis_complete": "Analyse terminée avec succès",
    "error_generic": "Une erreur s'est produite",
    "loading": "Chargement en cours..."
}

# Container Azure par défaut
DEFAULT_CONTAINER = "sharepoint-documents"

# Configuration de la pagination
PAGE_SIZE = 10
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB