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

# Types d'infractions
TYPES_INFRACTIONS = [
    "Abus de biens sociaux",
    "Abus de confiance", 
    "Banqueroute",
    "Blanchiment",
    "Corruption",
    "Délit d'initié",
    "Escroquerie",
    "Extorsion",
    "Faux et usage de faux",
    "Fraude fiscale",
    "Harcèlement moral",
    "Prise illégale d'intérêts",
    "Recel",
    "Trafic d'influence",
    "Travail dissimulé",
    "Vol",
    "Entente et pratiques anticoncurrentielles",
    "Contrefaçon"
]

# Configuration des modèles
MODELS_CONFIG = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
    "mistral": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "open-mistral-7b"],
    "groq": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
}

# Configuration des APIs juridiques
LEGAL_APIS = {
    "judilibre": {
        "enabled": True,
        "base_url": "https://api.piste.gouv.fr/cassation/judilibre/v1.0",
        "api_key": "votre_cle_api_judilibre",  # À remplacer
        "endpoints": {
            "search": "/search",
            "decision": "/decision",
            "export": "/export"
        }
    },
    "legifrance": {
        "enabled": True,
        "base_url": "https://api.aife.economie.gouv.fr/dila/legifrance-beta/lf-engine-app",
        "oauth_url": "https://oauth.aife.economie.gouv.fr/api/oauth/token",
        "client_id": "votre_client_id_legifrance",  # À remplacer
        "client_secret": "votre_client_secret_legifrance",  # À remplacer
        "endpoints": {
            "search": "/search/all",
            "consult": "/consult",
            "juri": "/consult/juri"
        }
    }
}

# Paramètres par défaut
DEFAULT_SETTINGS = {
    "temperature": 0.7,
    "max_tokens": 4000,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

# Formats d'export
EXPORT_FORMATS = ["PDF", "DOCX", "XLSX", "JSON", "TXT"]

# Configuration du cache
CACHE_CONFIG = {
    "ttl": 3600,  # 1 heure
    "max_size": 100
}

# Messages système
MESSAGES = {
    "welcome": "Bienvenue dans l'Assistant Pénal des Affaires IA ! 🎯",
    "loading": "Traitement en cours...",
    "error": "Une erreur est survenue. Veuillez réessayer.",
    "success": "Opération réussie !",
    "no_api_key": "Veuillez configurer votre clé API dans la page Configuration.",
    "no_results": "Aucun résultat trouvé.",
    "verification_in_progress": "Vérification des jurisprudences en cours..."
}