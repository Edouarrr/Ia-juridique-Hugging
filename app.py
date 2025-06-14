import streamlit as st
import os
import sys
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import time
import pandas as pd
import asyncio
from typing import Dict, List, Optional, Any
import re

# Configuration de la page
st.set_page_config(
    page_title="STERU BARATTE AARPI - Assistant Juridique",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation minimale de l'état de session
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.active_module = None
    st.session_state.search_performed = False
    st.session_state.documents_count = {'local': 0, 'containers': {}}
    st.session_state.selected_modules = []
    st.session_state.search_mode = 'global'
    st.session_state.ai_models = {
        'claude-opus-4': True,
        'gpt-4-turbo': False,
        'perplexity': False,
        'gemini-pro': False,
        'azure-openai': False
    }
    st.session_state.search_history = []
    st.session_state.active_container = None
    st.session_state.current_results = None
    st.session_state.show_guided_search = False
    st.session_state.advanced_mode = False
    st.session_state.favorites = []
    st.session_state.multi_ia_mode = False

# CSS professionnel avec dégradés de bleu - CORRIGÉ
st.markdown("""
<style>
    /* Variables de couleurs - Bleu marine */
    :root {
        --navy-blue: #0a1628;
        --primary-blue: #1e3a8a;
        --secondary-blue: #3b82f6;
        --light-blue: #dbeafe;
        --bg-blue: #f0f9ff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
    }
    
    /* Styles généraux */
    .main { padding: 0 !important; }
    .block-container { padding: 2rem 1rem !important; max-width: 1400px !important; }
    
    /* Barre latérale stylisée */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #0a1628 100%);
    }
    
    /* Texte blanc dans la sidebar */
    section[data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Conteneur principal avec gradient bleu marine */
    .search-container {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 50%, #3b82f6 100%);
        border-radius: 20px;
        padding: 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(10, 22, 40, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .search-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        animation: pulse-bg 10s ease-in-out infinite;
    }
    
    @keyframes pulse-bg {
        0%, 100% { transform: scale(1) rotate(0deg); }
        50% { transform: scale(1.1) rotate(180deg); }
    }
    
    /* Titre principal */
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        letter-spacing: 2px;
        position: relative;
        z-index: 1;
    }
    
    .subtitle {
        font-size: 1.4rem;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 1;
    }
    
    /* Zone de recherche principale */
    .stTextArea textarea {
        min-height: 120px !important;
        font-size: 16px !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        background: rgba(255, 255, 255, 0.95) !important;
        transition: all 0.3s ease !important;
        line-height: 1.6 !important;
        box-shadow: 0 4px 16px rgba(10, 22, 40, 0.1) !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3), 0 4px 16px rgba(10, 22, 40, 0.2) !important;
        background: white !important;
    }
    
    /* Compteur de documents */
    .doc-counter {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 249, 255, 0.95) 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid rgba(30, 58, 138, 0.1);
        box-shadow: 0 4px 20px rgba(10, 22, 40, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .doc-count-item {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        border-radius: 12px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(10, 22, 40, 0.2);
    }
    
    .doc-count-item:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(10, 22, 40, 0.3);
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    }
    
    .doc-count-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .doc-count-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Badges de mode */
    .mode-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border: 1px solid #1e3a8a;
        border-radius: 20px;
        color: #0a1628;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .mode-badge.active {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        color: white;
        border-color: #0a1628;
        box-shadow: 0 2px 8px rgba(10, 22, 40, 0.3);
    }
    
    /* Cartes de modules */
    .module-card {
        background: linear-gradient(135deg, white 0%, #f0f9ff 100%);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(30, 58, 138, 0.2);
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(10, 22, 40, 0.1);
    }
    
    .module-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0a1628 0%, #1e3a8a 50%, #3b82f6 100%);
        transform: translateX(-100%);
        transition: transform 0.3s ease;
    }
    
    .module-card:hover::before {
        transform: translateX(0);
    }
    
    .module-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 32px rgba(10, 22, 40, 0.2);
        border-color: #1e3a8a;
        background: linear-gradient(135deg, white 0%, #e0f2fe 100%);
    }
    
    .module-card.selected {
        border: 2px solid #0a1628;
        background: linear-gradient(135deg, #f0f9ff 0%, #dbeafe 100%);
        box-shadow: 0 8px 24px rgba(10, 22, 40, 0.15);
    }
    
    .module-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
        filter: drop-shadow(0 2px 4px rgba(10, 22, 40, 0.2));
    }
    
    .module-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #0a1628;
        margin-bottom: 0.5rem;
    }
    
    .module-description {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .module-features {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .module-features li {
        color: #64748b;
        font-size: 0.85rem;
        padding: 0.25rem 0;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .module-features li:before {
        content: "→";
        position: absolute;
        left: 0;
        color: #1e3a8a;
        font-weight: bold;
    }
    
    /* Indicateurs de statut */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-active {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.2);
    }
    
    .status-ready {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
    }
    
    .status-processing {
        background: linear-gradient(135deg, #93c5fd 0%, #dbeafe 100%);
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Historique de recherche */
    .search-history-item {
        background: linear-gradient(135deg, white 0%, #f0f9ff 100%);
        border: 1px solid rgba(30, 58, 138, 0.2);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .search-history-item:hover {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-color: #1e3a8a;
        transform: translateX(4px);
    }
    
    /* Instructions de recherche */
    .search-instructions {
        background: linear-gradient(135deg, rgba(240, 249, 255, 0.9) 0%, rgba(224, 242, 254, 0.9) 100%);
        border: 1px solid rgba(30, 58, 138, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* Criticalité avec dégradés de bleu marine */
    .criticality-high {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        display: inline-block;
        font-weight: 600;
    }
    
    .criticality-medium {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        display: inline-block;
        font-weight: 500;
    }
    
    .criticality-low {
        background: linear-gradient(135deg, #93c5fd 0%, #dbeafe 100%);
        color: #0a1628;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    /* Modèles IA */
    .ai-model-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        background: white;
        border: 2px solid rgba(30, 58, 138, 0.3);
        border-radius: 10px;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .ai-model-badge.active {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        color: white;
        border-color: #0a1628;
        box-shadow: 0 4px 12px rgba(10, 22, 40, 0.3);
    }
    
    .ai-model-badge:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(10, 22, 40, 0.2);
        border-color: #1e3a8a;
    }
    
    /* Recherche guidée */
    .guided-search-container {
        background: linear-gradient(135deg, white 0%, #f0f9ff 100%);
        border: 1px solid rgba(30, 58, 138, 0.2);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 4px 16px rgba(10, 22, 40, 0.1);
    }
    
    /* Boutons personnalisés */
    .stButton > button {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(10, 22, 40, 0.4);
    }
    
    /* Bouton primary */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 100%);
        box-shadow: 0 4px 16px rgba(10, 22, 40, 0.4);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(10, 22, 40, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# Fonction de chargement paresseux des modules
@st.cache_resource
def load_module(module_name):
    """Charge un module de manière paresseuse"""
    try:
        module_path = Path(f"modules/{module_name}.py")
        if not module_path.exists():
            module_path = Path(f"modules/{module_name.replace('-', '_')}.py")
        
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement du module {module_name}: {str(e)}")
        return None

# Fonction pour compter les documents avec cache
@st.cache_data(ttl=300)
def count_documents():
    """Compte les documents locaux et dans les containers Azure"""
    counts = {'local': 0, 'containers': {}}
    
    # Documents locaux
    local_docs_path = Path("documents")
    if local_docs_path.exists():
        counts['local'] = sum(1 for f in local_docs_path.rglob("*") if f.is_file())
    
    # Simulation containers Azure
    counts['containers'] = {
        'juridique': 156,
        'expertises': 89,
        'procedures': 234,
        'correspondances': 412,
        'factures': 98,
        'archives': 1245
    }
    
    return counts

# Définition complète des modules
MODULES = {
    'analyse_contradictions': {
        'title': 'Analyse des Contradictions',
        'icon': '🔍',
        'description': 'Détectez automatiquement les incohérences entre vos documents',
        'features': ['Détection automatique des contradictions', 'Analyse des concordances', 'Timeline comparative', 'Export des différences'],
        'tags': ['analyse', 'contradictions', 'cohérence']
    },
    'synthese_chronologique': {
        'title': 'Synthèse Chronologique',
        'icon': '📅',
        'description': 'Créez des chronologies détaillées de vos affaires',
        'features': ['Timeline interactive', 'Extraction automatique des dates', 'Visualisation temporelle', 'Export en formats multiples'],
        'tags': ['timeline', 'chronologie', 'dates', 'temps']
    },
    'extraction_preuves': {
        'title': 'Extraction de Preuves',
        'icon': '📋',
        'description': 'Identifiez et organisez les éléments probants',
        'features': ['Identification automatique', 'Classification par pertinence', 'Analyse de force probante', 'Export structuré'],
        'tags': ['preuves', 'extraction', 'classification', 'éléments probants']
    },
    'comparaison_documents': {
        'title': 'Comparaison de Documents',
        'icon': '📊',
        'description': 'Identifiez les contradictions et concordances entre documents',
        'features': ['Détection automatique des contradictions', 'Analyse des concordances', 'Timeline comparative', 'Export des différences'],
        'tags': ['comparaison', 'analyse', 'différences']
    },
    'analyse_risques': {
        'title': 'Analyse des Risques',
        'icon': '⚠️',
        'description': 'Évaluez les risques juridiques de vos dossiers',
        'features': ['Scoring des risques', 'Matrice de criticité', 'Alertes automatiques', 'Recommandations personnalisées'],
        'tags': ['risques', 'évaluation', 'alertes', 'scoring']
    },
    'generation_documents': {
        'title': 'Génération de Documents',
        'icon': '📝',
        'description': 'Créez automatiquement vos documents juridiques',
        'features': ['Modèles personnalisés', 'Génération intelligente', 'Multi-formats', 'Gestion des variables'],
        'tags': ['génération', 'documents', 'modèles', 'automatisation']
    },
    'recherche_jurisprudence': {
        'title': 'Recherche Jurisprudence',
        'icon': '⚖️',
        'description': 'Trouvez rapidement la jurisprudence pertinente',
        'features': ['Base de données étendue', 'Recherche sémantique', 'Analyse de pertinence', 'Citations automatiques'],
        'tags': ['jurisprudence', 'recherche', 'précédents', 'décisions']
    },
    'redaction_unifiee': {
        'title': 'Rédaction Unifiée',
        'icon': '✍️',
        'description': 'Rédigez vos documents avec l\'assistance de l\'IA',
        'features': ['Suggestions contextuelles', 'Vérification juridique', 'Modèles intégrés', 'Collaboration temps réel'],
        'tags': ['rédaction', 'écriture', 'collaboration']
    },
    'pieces_manager': {
        'title': 'Gestion des Pièces',
        'icon': '📁',
        'description': 'Organisez et gérez vos pièces de procédure',
        'features': ['Classification automatique', 'Numérotation intelligente', 'Bordereau automatique', 'Vérification complétude'],
        'tags': ['pièces', 'gestion', 'organisation', 'bordereau']
    },
    'mapping': {
        'title': 'Cartographie Juridique',
        'icon': '🗺️',
        'description': 'Visualisez les relations entre les éléments de votre dossier',
        'features': ['Graphes interactifs', 'Relations automatiques', 'Export visuel', 'Analyse de réseau'],
        'tags': ['cartographie', 'visualisation', 'relations', 'graphe']
    },
    'integration_juridique': {
        'title': 'Intégration Juridique',
        'icon': '🔗',
        'description': 'Connectez vos outils et bases de données juridiques',
        'features': ['APIs juridiques', 'Synchronisation', 'Import/Export', 'Workflows automatisés'],
        'tags': ['intégration', 'API', 'connexion', 'automatisation']
    },
    'generation_longue': {
        'title': 'Génération Longue',
        'icon': '📚',
        'description': 'Générez des documents longs et complexes',
        'features': ['Documents multi-sections', 'Cohérence globale', 'Références croisées', 'Table des matières auto'],
        'tags': ['génération', 'documents longs', 'rapports']
    }
}

# Parser de requête avancée amélioré
def parse_advanced_query(query):
    """Parse une requête avec syntaxe avancée (@container, opérateurs, etc.)"""
    result = {
        'container': None,
        'modules': [],
        'terms': [],
        'operators': [],
        'ai_models': [],
        'date_filter': None,
        'type_filter': None,
        'raw_query': query
    }
    
    # Détection du container (@xxx)
    container_matches = re.findall(r'@(\w+)', query)
    if container_matches:
        result['container'] = container_matches[0]
        st.session_state.active_container = result['container']
        for match in container_matches:
            query = query.replace(f'@{match}', '')
    
    # Détection des modules (#module)
    module_matches = re.findall(r'#(\w+)', query)
    result['modules'] = module_matches
    for module in module_matches:
        query = query.replace(f'#{module}', '')
    
    # Détection des modèles IA (!model)
    model_matches = re.findall(r'!(\w+)', query)
    result['ai_models'] = model_matches
    for model in model_matches:
        query = query.replace(f'!{model}', '')
    
    # Détection des dates (DATE:YYYY ou DATE:DD/MM/YYYY)
    date_matches = re.findall(r'DATE:(\d{4}|\d{2}/\d{2}/\d{4})', query)
    if date_matches:
        result['date_filter'] = date_matches[0]
        query = re.sub(r'DATE:\d{4}|\d{2}/\d{2}/\d{4}', '', query)
    
    # Extraction des termes entre guillemets
    quoted_terms = re.findall(r'"([^"]+)"', query)
    result['terms'].extend(quoted_terms)
    for term in quoted_terms:
        query = query.replace(f'"{term}"', '')
    
    # Extraction des opérateurs
    for op in ['ET', 'OU', 'SAUF', 'PRES DE', 'AVANT', 'APRES']:
        if op in query:
            result['operators'].append(op)
    
    # Termes restants
    remaining_terms = query.split()
    result['terms'].extend([t.strip() for t in remaining_terms if t.strip() and t not in ['ET', 'OU', 'SAUF', 'PRES DE', 'AVANT', 'APRES']])
    
    return result

# Recherche multi-IA simulée
async def multi_ia_search(query, models):
    """Effectue une recherche avec plusieurs modèles IA"""
    results = {}
    
    # Simulation de recherche asynchrone
    for model in models:
        if st.session_state.ai_models.get(model, False):
            # Simulation d'appel API
            await asyncio.sleep(0.5)
            results[model] = {
                'response': f"Réponse de {model} pour: {query}",
                'confidence': 0.85 + (0.1 if model == 'claude-opus-4' else 0),
                'sources': ['Document A', 'Document B'],
                'processing_time': 1.2
            }
    
    return results

# Barre latérale améliorée
with st.sidebar:
    st.markdown("## ⚖️ STERU BARATTE AARPI")
    
    # Profil utilisateur
    with st.expander("👤 Profil", expanded=False):
        user_name = st.text_input("Nom", value="Avocat")
        user_speciality = st.selectbox("Spécialité", ["Droit civil", "Droit pénal", "Droit des affaires", "Droit social"])
        user_cabinet = st.text_input("Cabinet", value="Cabinet Juridique")
    
    # Mode de recherche
    st.markdown("### 🔍 Mode de recherche")
    search_mode = st.radio(
        "",
        ["🌐 Recherche globale", "📁 Dans un container", "🔧 Modules spécifiques", "🤖 Multi-IA"],
        index=0,
        label_visibility="collapsed"
    )
    
    if search_mode == "📁 Dans un container":
        container = st.selectbox(
            "Container actif",
            list(count_documents()['containers'].keys()),
            help="Sélectionnez un container pour limiter la recherche"
        )
        st.session_state.active_container = container
        
        # Options de filtre pour le container
        with st.expander("⚙️ Options de filtre"):
            date_range = st.date_input(
                "Période",
                value=[],
                help="Laissez vide pour toutes les dates"
            )
            doc_types = st.multiselect(
                "Types de documents",
                ["PDF", "DOCX", "TXT", "XLSX"],
                default=["PDF", "DOCX"]
            )
    
    elif search_mode == "🔧 Modules spécifiques":
        st.markdown("Sélectionnez les modules :")
        for key, module in MODULES.items():
            if st.checkbox(f"{module['icon']} {module['title']}", key=f"cb_{key}"):
                if key not in st.session_state.selected_modules:
                    st.session_state.selected_modules.append(key)
            else:
                if key in st.session_state.selected_modules:
                    st.session_state.selected_modules.remove(key)
    
    elif search_mode == "🤖 Multi-IA":
        st.session_state.multi_ia_mode = True
        st.markdown("Sélectionnez les modèles IA :")
        
        models_info = {
            'claude-opus-4': {'name': 'Claude Opus 4', 'desc': 'Le plus puissant pour l\'analyse juridique'},
            'gpt-4-turbo': {'name': 'GPT-4 Turbo', 'desc': 'Excellent pour la génération de texte'},
            'perplexity': {'name': 'Perplexity', 'desc': 'Recherche web en temps réel'},
            'gemini-pro': {'name': 'Gemini Pro', 'desc': 'Analyse multimodale avancée'},
            'azure-openai': {'name': 'Azure OpenAI', 'desc': 'Solution entreprise sécurisée'}
        }
        
        for model_key, model_info in models_info.items():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.session_state.ai_models[model_key] = st.checkbox(
                    "",
                    value=st.session_state.ai_models.get(model_key, model_key == 'claude-opus-4'),
                    key=f"ai_{model_key}"
                )
            with col2:
                st.markdown(f"**{model_info['name']}**  \n{model_info['desc']}")
    
    # Paramètres avancés
    with st.expander("⚙️ Paramètres avancés"):
        st.markdown("### 🎯 Options de recherche")
        
        search_depth = st.select_slider(
            "Profondeur d'analyse",
            options=["Rapide", "Standard", "Approfondie", "Exhaustive"],
            value="Standard"
        )
        
        include_archives = st.checkbox("Inclure les archives", value=False)
        semantic_search = st.checkbox("Recherche sémantique", value=True)
        cross_reference = st.checkbox("Références croisées", value=True)
        
        st.markdown("### 🔐 Sécurité")
        anonymize = st.checkbox("Anonymiser les résultats", value=False)
        watermark = st.checkbox("Ajouter filigrane", value=False)
    
    # Historique de recherche amélioré
    st.markdown("### 📜 Historique récent")
    if st.session_state.search_history:
        for i, search in enumerate(st.session_state.search_history[-5:][::-1]):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"🔄 {search[:30]}...", key=f"history_{i}", use_container_width=True):
                    st.session_state.search_query = search
            with col2:
                if st.button("⭐", key=f"fav_{i}", help="Ajouter aux favoris"):
                    if search not in st.session_state.favorites:
                        st.session_state.favorites.append(search)
    else:
        st.info("Aucune recherche récente")
    
    # Favoris
    if st.session_state.favorites:
        st.markdown("### ⭐ Favoris")
        for i, fav in enumerate(st.session_state.favorites):
            if st.button(f"★ {fav[:30]}...", key=f"favorite_{i}", use_container_width=True):
                st.session_state.search_query = fav
    
    # Statistiques améliorées
    st.markdown("### 📊 Statistiques")
    doc_counts = count_documents()
    total_docs = doc_counts['local'] + sum(doc_counts['containers'].values())
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total documents", f"{total_docs:,}")
        st.metric("Recherches aujourd'hui", "24")
    with col2:
        st.metric("Containers actifs", len(doc_counts['containers']))
        st.metric("Temps moyen", "2.3s")
    
    # Progression d'utilisation
    usage_progress = st.progress(0.7)
    st.caption("70% du quota mensuel utilisé")
    
    # Mode avancé
    st.markdown("---")
    st.session_state.advanced_mode = st.toggle("🚀 Mode avancé", value=False)

# Interface principale
if st.session_state.active_module:
    # Affichage d'un module spécifique
    module = load_module(st.session_state.active_module)
    if module and hasattr(module, 'run'):
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if st.button("← Retour", key="back_button"):
                st.session_state.active_module = None
                st.rerun()
        with col3:
            # Bouton favori pour le module
            module_info = MODULES.get(st.session_state.active_module, {})
            is_favorite = st.session_state.active_module in st.session_state.favorites
            if st.button("⭐" if not is_favorite else "★", key="module_fav"):
                if is_favorite:
                    st.session_state.favorites.remove(st.session_state.active_module)
                else:
                    st.session_state.favorites.append(st.session_state.active_module)
                st.rerun()
        
        module.run()
else:
    # Page d'accueil
    st.markdown('<h1 class="main-title">STERU BARATTE AARPI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Cabinet d\'avocats - Assistant juridique intelligent</p>', unsafe_allow_html=True)
    
    # Conteneur de recherche principal
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Zone de recherche avec détection d'Entrée
    search_container = st.container()
    with search_container:
        # Zone de texte principale
        search_query = st.text_area(
            "",
            placeholder="Posez votre question juridique ou utilisez la syntaxe avancée...\n\nExemples :\n• Quelles sont les contradictions entre les témoignages ?\n• @expertises, analyse des risques financiers\n• #jurisprudence responsabilité civile accident\n• !perplexity dernières décisions cour de cassation",
            height=120,
            key="main_search",
            label_visibility="collapsed",
            help="Appuyez sur Entrée pour rechercher"
        )
        
        # Détection de la touche Entrée (quand il n'y a qu'une seule ligne sans saut)
        if search_query and search_query.count('\n') == 0 and len(search_query) > 0:
            st.session_state.search_performed = True
        
        # Boutons d'action
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            search_button = st.button(
                "🔍 Rechercher",
                type="primary",
                use_container_width=True,
                disabled=not search_query
            )
        with col2:
            if st.button("🎯 Recherche guidée", use_container_width=True):
                st.session_state.show_guided_search = not st.session_state.show_guided_search
        with col3:
            if st.button("📝 Modèles", use_container_width=True):
                st.session_state.show_templates = True
        with col4:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                for key in ['search_query', 'active_container', 'selected_modules', 'current_results']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Modes actifs et syntaxe
    if st.session_state.active_container or st.session_state.selected_modules or any(st.session_state.ai_models.values()):
        st.markdown("### 🎯 Modes actifs")
        
        cols = st.columns(6)
        col_index = 0
        
        if st.session_state.active_container:
            with cols[col_index % 6]:
                st.markdown(f'<span class="mode-badge active">📁 @{st.session_state.active_container}</span>', unsafe_allow_html=True)
            col_index += 1
        
        for module in st.session_state.selected_modules:
            if col_index < 6:
                with cols[col_index % 6]:
                    module_info = MODULES.get(module, {})
                    st.markdown(f'<span class="mode-badge active">{module_info.get("icon", "")} #{module}</span>', unsafe_allow_html=True)
                col_index += 1
        
        # Affichage des modèles IA actifs
        if st.session_state.multi_ia_mode:
            for model, active in st.session_state.ai_models.items():
                if active and col_index < 6:
                    with cols[col_index % 6]:
                        st.markdown(f'<span class="mode-badge active">🤖 !{model}</span>', unsafe_allow_html=True)
                    col_index += 1
    
    # Recherche guidée
    if st.session_state.get('show_guided_search', False):
        with st.container():
            st.markdown("### 🎯 Recherche guidée")
            
            guided_col1, guided_col2 = st.columns(2)
            
            with guided_col1:
                guided_type = st.selectbox(
                    "Type de recherche",
                    ["Analyse de contradictions", "Recherche de jurisprudence", "Extraction de preuves", "Génération de document"]
                )
                
                guided_container = st.selectbox(
                    "Dans quel container ?",
                    ["Tous"] + list(count_documents()['containers'].keys())
                )
            
            with guided_col2:
                guided_date = st.date_input("Période concernée", value=None)
                
                guided_keywords = st.text_input(
                    "Mots-clés principaux",
                    placeholder="Ex: accident, responsabilité, préjudice..."
                )
            
            if st.button("🚀 Lancer la recherche guidée", type="primary", use_container_width=True):
                # Construction de la requête
                query_parts = []
                if guided_container != "Tous":
                    query_parts.append(f"@{guided_container}")
                if guided_type == "Analyse de contradictions":
                    query_parts.append("#contradictions")
                elif guided_type == "Recherche de jurisprudence":
                    query_parts.append("#jurisprudence")
                if guided_keywords:
                    query_parts.append(guided_keywords)
                
                st.session_state.search_query = ", ".join(query_parts)
                st.session_state.search_performed = True
    
    # Traitement de la recherche
    if (search_button or st.session_state.search_performed) and search_query:
        st.session_state.search_history.append(search_query)
        parsed_query = parse_advanced_query(search_query)
        
        # Affichage de l'analyse de la requête si mode avancé
        if st.session_state.advanced_mode:
            with st.expander("🔍 Analyse de la requête", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Container ciblé:**")
                    st.info(parsed_query['container'] or "Tous")
                with col2:
                    st.markdown("**Modules détectés:**")
                    st.info(", ".join(parsed_query['modules']) if parsed_query['modules'] else "Aucun")
                with col3:
                    st.markdown("**Modèles IA:**")
                    st.info(", ".join(parsed_query['ai_models']) if parsed_query['ai_models'] else "Par défaut")
        
        # Recherche multi-IA si activée
        if st.session_state.multi_ia_mode and any(st.session_state.ai_models.values()):
            st.markdown("### 🤖 Recherche Multi-IA")
            
            # Conteneur pour les résultats
            results_container = st.container()
            
            with st.spinner("🔍 Interrogation des modèles IA..."):
                # Simulation de recherche asynchrone
                progress = st.progress(0)
                active_models = [k for k, v in st.session_state.ai_models.items() if v]
                
                for i, model in enumerate(active_models):
                    progress.progress((i + 1) / len(active_models))
                    time.sleep(0.5)
                
                # Affichage des résultats par modèle
                tabs = st.tabs([f"🤖 {model}" for model in active_models])
                
                for idx, (tab, model) in enumerate(zip(tabs, active_models)):
                    with tab:
                        st.markdown(f"#### Résultats de {model}")
                        
                        # Métriques du modèle
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confiance", f"{85 + idx * 3}%")
                        with col2:
                            st.metric("Temps", f"{1.2 + idx * 0.3:.1f}s")
                        with col3:
                            st.metric("Sources", f"{3 + idx}")
                        
                        # Réponse simulée
                        st.markdown("**Analyse:**")
                        st.info(f"Analyse de {model} pour votre requête '{search_query}'...")
                        
                        # Sources
                        with st.expander("📚 Sources utilisées"):
                            for i in range(3):
                                st.markdown(f"- Document {i+1} - Container {parsed_query.get('container', 'juridique')}")
        else:
            # Recherche simple
            with st.spinner(f"🔍 Analyse en cours avec Claude Opus 4..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress.progress(i + 1)
                
                # Résultats simulés
                st.success("✅ Recherche terminée !")
                
                # Affichage contextuel des résultats
                if parsed_query['container']:
                    st.info(f"📁 Recherche effectuée dans le container **{parsed_query['container']}**")
                
                if parsed_query['modules']:
                    st.info(f"🔧 Modules utilisés : {', '.join(parsed_query['modules'])}")
                
                # Résultats principaux
                st.markdown("### 📊 Résultats de la recherche")
                
                # Métriques de recherche
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Documents analysés", "47")
                with col2:
                    st.metric("Pertinence moyenne", "89%")
                with col3:
                    st.metric("Temps d'analyse", "2.3s")
                with col4:
                    st.metric("Suggestions", "12")
        
        # Suggestions de modules pertinents
        st.markdown("### 🎯 Actions suggérées")
        
        # Déterminer les modules suggérés en fonction de la requête
        suggested_modules = []
        query_lower = search_query.lower()
        
        if any(term in query_lower for term in ['contradiction', 'incohérence', 'divergence']):
            suggested_modules.append('analyse_contradictions')
        if any(term in query_lower for term in ['chronologie', 'timeline', 'date', 'temps']):
            suggested_modules.append('synthese_chronologique')
        if any(term in query_lower for term in ['preuve', 'élément', 'probant']):
            suggested_modules.append('extraction_preuves')
        if any(term in query_lower for term in ['jurisprudence', 'décision', 'arrêt']):
            suggested_modules.append('recherche_jurisprudence')
        if any(term in query_lower for term in ['risque', 'danger', 'alerte']):
            suggested_modules.append('analyse_risques')
        
        # Si pas de suggestion spécifique, proposer les 3 plus populaires
        if not suggested_modules:
            suggested_modules = ['analyse_contradictions', 'synthese_chronologique', 'extraction_preuves']
        
        cols = st.columns(min(3, len(suggested_modules)))
        for idx, module_key in enumerate(suggested_modules[:3]):
            with cols[idx]:
                module_info = MODULES.get(module_key, {})
                if st.button(
                    f"{module_info['icon']} {module_info['title']}",
                    key=f"suggest_{module_key}",
                    use_container_width=True,
                    help=module_info['description']
                ):
                    st.session_state.active_module = module_key
                    st.rerun()
        
        # Résultats détaillés
        with st.expander("📋 Voir les résultats détaillés", expanded=False):
            # Tableau de résultats
            results_data = {
                'Document': ['PV_audition_2024.pdf', 'Expertise_medicale.pdf', 'Conclusions_adversaire.pdf'],
                'Container': ['juridique', 'expertises', 'procedures'],
                'Pertinence': [95, 87, 78],
                'Date': ['15/03/2024', '10/03/2024', '20/03/2024'],
                'Extraits': ['...contradiction sur l\'heure...', '...évaluation du préjudice...', '...responsabilité contestée...']
            }
            
            df_results = pd.DataFrame(results_data)
            st.dataframe(
                df_results,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pertinence": st.column_config.ProgressColumn(
                        "Pertinence",
                        help="Score de pertinence",
                        min_value=0,
                        max_value=100,
                    )
                }
            )
    
    # Compteur de documents interactif
    st.markdown("### 📊 Vos documents")
    doc_counts = count_documents()
    
    st.markdown('<div class="doc-counter">', unsafe_allow_html=True)
    
    # Calcul du nombre de colonnes nécessaires
    num_containers = len(doc_counts['containers']) + 1
    cols = st.columns(min(6, num_containers))
    
    # Documents locaux
    with cols[0]:
        if st.button(
            f"**{doc_counts['local']:,}**\n📁 Documents locaux",
            key="local_docs_btn",
            use_container_width=True,
            help="Cliquer pour voir les documents locaux"
        ):
            st.session_state.active_container = "local"
    
    # Containers Azure
    for idx, (container, count) in enumerate(doc_counts['containers'].items()):
        if idx + 1 < len(cols):
            with cols[idx + 1]:
                if st.button(
                    f"**{count:,}**\n☁️ {container.capitalize()}",
                    key=f"container_btn_{container}",
                    use_container_width=True,
                    help=f"Cliquer pour explorer {container}"
                ):
                    st.session_state.active_container = container
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Grille des modules avec filtre et recherche
    st.markdown("### 🚀 Modules disponibles")
    
    # Barre de filtre et recherche
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        module_filter = st.text_input(
            "🔍 Rechercher un module",
            placeholder="Ex: contradiction, chronologie, preuve...",
            key="module_search"
        )
    with col2:
        tag_filter = st.multiselect(
            "Tags",
            ["analyse", "génération", "recherche", "visualisation", "gestion"],
            default=[]
        )
    with col3:
        view_mode = st.radio(
            "Vue",
            ["Grille", "Liste"],
            horizontal=True,
            index=0
        )
    
    # Affichage des modules
    filtered_modules = {}
    for key, module in MODULES.items():
        # Filtrage par texte
        if module_filter:
            search_text = module_filter.lower()
            if not any(search_text in str(v).lower() for v in module.values()):
                continue
        
        # Filtrage par tags
        if tag_filter:
            module_tags = module.get('tags', [])
            if not any(tag in tag_filter for tag in module_tags):
                continue
        
        filtered_modules[key] = module
    
    if view_mode == "Grille":
        # Vue en grille
        cols = st.columns(3)
        for idx, (module_key, module_info) in enumerate(filtered_modules.items()):
            with cols[idx % 3]:
                # Container pour la carte
                module_container = st.container()
                with module_container:
                    # Carte cliquable avec HTML
                    card_html = f"""
                    <div class="module-card">
                        <div class="module-icon">{module_info['icon']}</div>
                        <div class="module-title">{module_info['title']}</div>
                        <div class="module-description">{module_info['description']}</div>
                        <ul class="module-features">
                    """
                    
                    for feature in module_info.get('features', [])[:3]:
                        card_html += f"<li>{feature}</li>"
                    
                    card_html += "</ul></div>"
                    
                    if st.button(
                        f"{module_info['icon']} **{module_info['title']}**\n\n{module_info['description']}",
                        key=f"module_{module_key}",
                        use_container_width=True,
                        help=f"Tags: {', '.join(module_info.get('tags', []))}"
                    ):
                        st.session_state.active_module = module_key
                        st.rerun()
    else:
        # Vue en liste
        for module_key, module_info in filtered_modules.items():
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                st.markdown(f"### {module_info['icon']}")
            
            with col2:
                st.markdown(f"**{module_info['title']}**")
                st.caption(module_info['description'])
                
                # Tags
                tag_html = ""
                for tag in module_info.get('tags', []):
                    tag_html += f'<span class="mode-badge">{tag}</span> '
                st.markdown(tag_html, unsafe_allow_html=True)
            
            with col3:
                if st.button("Ouvrir →", key=f"open_{module_key}"):
                    st.session_state.active_module = module_key
                    st.rerun()
            
            st.markdown("---")
    
    # Instructions avancées
    with st.expander("📚 Guide complet d'utilisation", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["Syntaxe", "Exemples", "Raccourcis", "API"])
        
        with tab1:
            st.markdown("""
            ### 🔍 Syntaxe de recherche avancée
            
            #### Sélecteurs
            - **`@container`** : Recherche dans un container spécifique
            - **`#module`** : Active un module particulier
            - **`!model`** : Utilise un modèle IA spécifique
            - **`"terme exact"`** : Recherche exacte
            
            #### Opérateurs logiques
            - **`ET`** : Tous les termes doivent être présents
            - **`OU`** : Au moins un terme doit être présent
            - **`SAUF`** : Exclut les documents contenant ce terme
            - **`PRES DE`** : Termes proches (dans le même paragraphe)
            - **`AVANT`** : Ordre chronologique
            - **`APRES`** : Ordre chronologique inverse
            
            #### Filtres temporels
            - **`DATE:2024`** : Documents de 2024
            - **`DATE:15/03/2024`** : Date spécifique
            - **`DEPUIS:01/01/2024`** : Après cette date
            - **`AVANT:31/12/2024`** : Avant cette date
            """)
        
        with tab2:
            st.markdown("""
            ### 📝 Exemples concrets
            
            **Recherches simples :**
            ```
            responsabilité civile accident
            préjudice moral ET corporel
            contrat de bail commercial
            ```
            
            **Recherches dans un container :**
            ```
            @juridique, procédure civile
            @expertises, évaluation préjudice
            @archives DATE:2023
            ```
            
            **Utilisation des modules :**
            ```
            #contradictions témoignages
            #timeline @procedures
            #jurisprudence "responsabilité médicale"
            ```
            
            **Multi-IA avancé :**
            ```
            !perplexity dernières décisions cassation
            !claude-opus-4 !gpt-4 analyse comparative
            !gemini-pro analyse image preuve
            ```
            
            **Requêtes complexes :**
            ```
            @expertises, #contradictions "préjudice corporel" ET DATE:2024 SAUF provisoire
            @juridique @procedures, #timeline accident PRES DE responsabilité
            !multi-ia #jurisprudence "faute inexcusable" DEPUIS:01/01/2023
            ```
            """)
        
        with tab3:
            st.markdown("""
            ### ⌨️ Raccourcis clavier
            
            - **`Entrée`** : Lance la recherche
            - **`Ctrl + K`** : Focus sur la recherche
            - **`Ctrl + M`** : Ouvre les modules
            - **`Ctrl + H`** : Historique
            - **`Ctrl + D`** : Télécharge les résultats
            - **`Esc`** : Ferme les dialogues
            
            ### 🎯 Astuces pro
            
            1. **Recherche incrémentale** : Commencez large puis affinez
            2. **Favoris intelligents** : Sauvegardez vos requêtes complexes
            3. **Templates** : Utilisez les modèles pour gagner du temps
            4. **Export groupé** : Sélectionnez plusieurs résultats
            5. **Mode comparaison** : Comparez jusqu'à 4 documents
            """)
        
        with tab4:
            st.markdown("""
            ### 🔌 Intégration API
            
            **Endpoint principal :**
            ```
            POST /api/v1/search
            Authorization: Bearer YOUR_API_KEY
            ```
            
            **Exemple de requête :**
            ```json
            {
                "query": "@juridique, #contradictions accident",
                "models": ["claude-opus-4", "gpt-4-turbo"],
                "options": {
                    "depth": "approfondie",
                    "include_sources": true,
                    "max_results": 50
                }
            }
            ```
            
            **Webhooks disponibles :**
            - Notification de fin d'analyse
            - Alerte sur contradictions critiques
            - Rapport quotidien automatique
            
            [Documentation complète →](https://docs.steru-baratte.fr)
            """)

# Footer avec informations système
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    # Version et statut
    st.caption("v2.0.3 | Stable | STERU BARATTE AARPI")

with col2:
    # Modèles actifs et performances
    active_models = [k for k, v in st.session_state.ai_models.items() if v]
    if active_models:
        models_text = f"Modèles actifs: {', '.join(active_models)}"
    else:
        models_text = "Modèle par défaut: Claude Opus 4"
    
    st.markdown(
        f'<div style="text-align: center; color: #94a3b8;">{models_text} | Latence: 1.2s | {datetime.now().strftime("%H:%M")}</div>',
        unsafe_allow_html=True
    )

with col3:
    # Actions rapides
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💬 Support", use_container_width=True, key="footer_support"):
            st.info("support@steru-baratte.fr")
    with col_b:
        if st.button("📖 Docs", use_container_width=True, key="footer_docs"):
            st.info("docs.steru-baratte.fr")

# Script pour gérer l'appui sur Entrée
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.querySelector('textarea[aria-label="main_search"]');
    if (textarea) {
        textarea.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const button = document.querySelector('button[kind="primary"]');
                if (button) button.click();
            }
        });
    }
});
</script>
""", unsafe_allow_html=True)

# Initialisation complète différée
if not st.session_state.initialized:
    st.session_state.initialized = True