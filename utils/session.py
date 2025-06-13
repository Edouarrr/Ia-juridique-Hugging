# utils/session.py
"""
Gestion de la session Streamlit
"""

import streamlit as st
from typing import Dict, Any, List


def initialize_session_state():
    """Initialise les variables de session Streamlit"""
    
    # Configuration générale
    defaults = {
        'initialized': False,
        'current_page': 'Accueil',
        'current_view': 'accueil',
        'current_module': None,
        'search_mode': 'simple',
        
        # Documents et données
        'azure_documents': {},
        'imported_documents': {},
        'pieces_selectionnees': {},
        'selected_pieces': [],
        
        # Résultats
        'search_results': [],
        'search_history': [],
        'current_bordereau': None,
        'synthesis_result': None,
        'redaction_result': None,
        'plaidoirie_result': None,
        
        # Managers
        'azure_blob_manager': None,
        'azure_search_manager': None,
        
        # Templates
        'saved_templates': {},
        
        # Workflow
        'workflow_active': None,
        'multi_ia_active': True,
        'theme': 'light',
        'recent_actions': [],
        'favorites': [],
        
        # Module juridique
        'acte_genere': None,
        'current_dossier': None,
        'infractions_selectionnees': [],
        'parties_dict': {'demandeurs': [], 'defendeurs': []},
        'enrichissement_results': {},
    }
    
    # Préférences utilisateur
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'results_per_page': 20,
            'default_view': 'Compact',
            'auto_jurisprudence': True,
            'create_hyperlinks': True,
            'default_doc_length': 'Très détaillé',
            'cache_enabled': True,
            'auto_save': True,
            'language': 'fr'
        }
    
    # Initialiser avec les valeurs par défaut
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Marquer comme initialisé
    st.session_state.initialized = True


def get_session_value(key: str, default: Any = None) -> Any:
    """Récupère une valeur de session de manière sûre"""
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any):
    """Définit une valeur de session"""
    st.session_state[key] = value


def update_session_values(updates: Dict[str, Any]):
    """Met à jour plusieurs valeurs de session"""
    for key, value in updates.items():
        st.session_state[key] = value


def clear_session_results():
    """Efface les résultats de session"""
    results_keys = [
        'search_results', 'synthesis_result', 
        'redaction_result', 'plaidoirie_result',
        'acte_genere', 'enrichissement_results'
    ]
    for key in results_keys:
        if key in st.session_state:
            st.session_state[key] = [] if key.endswith('results') else None


def add_to_history(action: str, details: Dict[str, Any]):
    """Ajoute une action à l'historique"""
    if 'recent_actions' not in st.session_state:
        st.session_state.recent_actions = []
    
    from datetime import datetime
    
    action_entry = {
        'action': action,
        'timestamp': datetime.now(),
        'details': details
    }
    
    st.session_state.recent_actions.insert(0, action_entry)
    
    # Limiter l'historique à 50 entrées
    st.session_state.recent_actions = st.session_state.recent_actions[:50]


def toggle_favorite(item_id: str, item_type: str):
    """Ajoute/retire un élément des favoris"""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    favorite = {
        'id': item_id,
        'type': item_type
    }
    
    # Chercher si déjà en favoris
    existing = next((f for f in st.session_state.favorites 
                    if f['id'] == item_id), None)
    
    if existing:
        st.session_state.favorites.remove(existing)
        return False
    else:
        st.session_state.favorites.append(favorite)
        return True


def is_favorite(item_id: str) -> bool:
    """Vérifie si un élément est en favoris"""
    if 'favorites' not in st.session_state:
        return False
    
    return any(f['id'] == item_id for f in st.session_state.favorites)


def get_user_preference(key: str, default: Any = None) -> Any:
    """Récupère une préférence utilisateur"""
    if 'user_preferences' not in st.session_state:
        return default
    
    return st.session_state.user_preferences.get(key, default)


def set_user_preference(key: str, value: Any):
    """Définit une préférence utilisateur"""
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {}
    
    st.session_state.user_preferences[key] = value


def reset_session():
    """Réinitialise complètement la session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    initialize_session_state()