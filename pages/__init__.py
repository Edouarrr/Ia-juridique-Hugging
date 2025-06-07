# pages/__init__.py
# Les pages Streamlit sont généralement importées dynamiquement
# Ce fichier peut rester vide ou contenir des imports utilitaires

# Optionnel : dictionnaire des pages pour navigation
PAGES_REGISTRY = {
    "accueil": "pages.accueil",
    "analyse": "pages.analyse", 
    "recherche": "pages.recherche",
    "visualisation": "pages.visualisation",
    "assistant": "pages.assistant",
    "configuration": "pages.configuration"
}

# Note: Les pages Streamlit sont souvent chargées dynamiquement
# via st.page() ou importlib, donc pas besoin d'imports explicites ici