# config/app_config.py
"""Configuration centralisée de l'application"""

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

# Container Azure par défaut
DEFAULT_CONTAINER = "sharepoint-documents"

# Configuration de la pagination
PAGE_SIZE = 10
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB