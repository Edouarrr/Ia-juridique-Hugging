"""Module d'analyse IA avancée avec multi-modèles et fusion - Nexora Law IA"""

import asyncio
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import clean_key, format_legal_date, truncate_text
from utils.file_utils import get_file_icon
from config.ai_models import AI_MODELS
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# ========================= CONFIGURATION =========================


# Thèmes de couleurs
THEMES = {
    "Juridique": {
        "primary": "#8B0000",
        "secondary": "#4B0000",
        "accent": "#FFD700",
        "background": "#F5F5F5",
        "text": "#333333",
        "success": "#28A745",
        "warning": "#FFC107",
        "error": "#DC3545"
    },
    "Moderne": {
        "primary": "#2E86AB",
        "secondary": "#A23B72",
        "accent": "#F18F01",
        "background": "#FFFFFF",
        "text": "#2D3436",
        "success": "#00B894",
        "warning": "#FDCB6E",
        "error": "#D63031"
    },
    "Sombre": {
        "primary": "#BB86FC",
        "secondary": "#03DAC6",
        "accent": "#CF6679",
        "background": "#121212",
        "text": "#FFFFFF",
        "success": "#03DAC6",
        "warning": "#F4B400",
        "error": "#CF6679"
    }
}

# ========================= ÉTAT ET INITIALISATION =========================

def init_session_state():
    """Initialise l'état de session avec lazy loading"""
    
    # État principal du module
    if 'module_state' not in st.session_state:
        st.session_state.module_state = {
            'initialized': False,
            'results': None,
            'config': {},
            'selected_models': [],
            'fusion_mode': 'consensus',
            'analysis_history': [],
            'cache': {},
            'theme': 'Juridique',
            'animations_enabled': True,
            'current_step': 0,
            'processing': False,
            'ai_responses': {},
            'comparison_mode': False
        }
    
    # Cache pour les résultats d'IA
    if 'ai_cache' not in st.session_state:
        st.session_state.ai_cache = {}
    
    # Métriques de performance
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {
            'total_analyses': 0,
            'avg_response_time': 0,
            'model_usage': {model: 0 for model in AI_MODELS.keys()},
            'fusion_accuracy': []
        }

def get_cache_key(content: str, models: List[str], params: Dict) -> str:
    """Génère une clé de cache unique"""
    cache_data = {
        'content': content[:1000],  # Premiers 1000 caractères
        'models': sorted(models),
        'params': params
    }
    return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

# ========================= INTERFACE UTILISATEUR =========================

def run():
    """Fonction principale du module avec UI moderne"""
    
    # Initialisation
    init_session_state()
    
    # CSS personnalisé avec animations
    apply_custom_css()
    
    # En-tête moderne avec animations
    render_header()
    
    # Navigation par étapes
    steps = ["📤 Données", "🤖 Modèles IA", "⚙️ Configuration", "🚀 Analyse", "📊 Résultats"]
    current_step = st.session_state.module_state['current_step']
    
    # Barre de progression visuelle
    render_progress_bar(current_step, len(steps))
    
    # Conteneur principal avec animation
    with st.container():
        if st.session_state.module_state['animations_enabled']:
            st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        
        # Navigation par onglets modernisée
        tabs = st.tabs(steps)
        
        # 1. Onglet Données
        with tabs[0]:
            render_data_input_tab()
        
        # 2. Onglet Modèles IA
        with tabs[1]:
            render_ai_models_tab()
        
        # 3. Onglet Configuration
        with tabs[2]:
            render_configuration_tab()
        
        # 4. Onglet Analyse
        with tabs[3]:
            render_analysis_tab()
        
        # 5. Onglet Résultats
        with tabs[4]:
            render_results_tab()
        
        if st.session_state.module_state['animations_enabled']:
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Barre latérale avec infos et aide
    render_sidebar()
    
    # Footer avec métriques
    render_footer()

def apply_custom_css():
    """Applique le CSS personnalisé avec animations et thème"""
    
    theme = THEMES[st.session_state.module_state['theme']]
    
    st.markdown(f"""
    <style>
    /* Variables CSS du thème */
    :root {{
        --primary: {theme['primary']};
        --secondary: {theme['secondary']};
        --accent: {theme['accent']};
        --background: {theme['background']};
        --text: {theme['text']};
        --success: {theme['success']};
        --warning: {theme['warning']};
        --error: {theme['error']};
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateX(-100%); }}
        to {{ transform: translateX(0); }}
    }}
    
    @keyframes glow {{
        0% {{ box-shadow: 0 0 5px var(--primary); }}
        50% {{ box-shadow: 0 0 20px var(--primary), 0 0 30px var(--primary); }}
        100% {{ box-shadow: 0 0 5px var(--primary); }}
    }}
    
    /* Classes d'animation */
    .fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
    
    .pulse {{
        animation: pulse 2s infinite;
    }}
    
    .slide-in {{
        animation: slideIn 0.3s ease-out;
    }}
    
    .glow {{
        animation: glow 2s infinite;
    }}
    
    /* Composants stylisés */
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }}
    
    /* Cartes modernes */
    .model-card {{
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }}
    
    .model-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        border-color: var(--primary);
    }}
    
    .model-card.selected {{
        border-color: var(--primary);
        background: linear-gradient(135deg, rgba(139,0,0,0.05), rgba(139,0,0,0.1));
    }}
    
    /* Barre de progression */
    .progress-container {{
        background: #e0e0e0;
        border-radius: 10px;
        height: 10px;
        margin: 20px 0;
        overflow: hidden;
    }}
    
    .progress-bar {{
        background: linear-gradient(90deg, var(--primary), var(--accent));
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }}
    
    /* Métriques améliorées */
    .metric-card {{
        background: linear-gradient(135deg, white, #f8f9fa);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
    }}
    
    .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary);
        margin: 0.5rem 0;
    }}
    
    .metric-label {{
        color: var(--text);
        opacity: 0.8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Tooltips */
    .tooltip {{
        position: relative;
        display: inline-block;
    }}
    
    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 200px;
        background-color: #333;
        color: #fff;
        text-align: center;
        padding: 5px 10px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }}
    
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
    
    /* Comparaison de modèles */
    .comparison-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }}
    
    .comparison-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    /* Loading spinner moderne */
    .spinner {{
        width: 50px;
        height: 50px;
        margin: 20px auto;
        border: 5px solid #f3f3f3;
        border-top: 5px solid var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    /* Badges */
    .badge {{
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 20px;
        margin: 0.2rem;
    }}
    
    .badge-success {{
        background: var(--success);
        color: white;
    }}
    
    .badge-warning {{
        background: var(--warning);
        color: #333;
    }}
    
    .badge-error {{
        background: var(--error);
        color: white;
    }}
    
    /* Timeline */
    .timeline {{
        position: relative;
        padding: 20px 0;
    }}
    
    .timeline::before {{
        content: '';
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 2px;
        background: var(--primary);
    }}
    
    .timeline-item {{
        position: relative;
        padding: 20px 0;
    }}
    
    .timeline-marker {{
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 20px;
        background: var(--primary);
        border-radius: 50%;
        border: 4px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Affiche l'en-tête moderne avec animations"""
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("""
        <div class="fade-in" style="text-align: center;">
            <h1 style="color: var(--primary); font-size: 3rem; margin-bottom: 0;">
                🚀 Analyse IA Multi-Modèles
            </h1>
            <p style="color: var(--text); opacity: 0.8; font-size: 1.2rem;">
                Combinez la puissance de plusieurs IA pour des analyses juridiques avancées
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Switch de thème
        theme_options = list(THEMES.keys())
        current_theme = st.session_state.module_state['theme']
        new_theme = st.selectbox(
            "🎨",
            theme_options,
            index=theme_options.index(current_theme),
            key="theme_selector"
        )
        
        if new_theme != current_theme:
            st.session_state.module_state['theme'] = new_theme
            st.rerun()

def render_progress_bar(current_step: int, total_steps: int):
    """Affiche une barre de progression visuelle"""
    
    progress = (current_step / (total_steps - 1)) * 100
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress}%;"></div>
    </div>
    """, unsafe_allow_html=True)

def render_data_input_tab():
    """Onglet de sélection des données avec UI améliorée"""
    
    st.markdown("### 📤 Sélection des données")
    
    # Options d'entrée avec icônes
    input_method = st.radio(
        "Méthode d'entrée",
        ["☁️ Container Azure", "📁 Upload de fichiers", "🔍 Recherche", "✍️ Texte direct"],
        horizontal=True,
        key="input_method"
    )
    
    data_loaded = False
    
    if "☁️" in input_method:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            container = st.selectbox(
                "Sélectionner un container",
                ["juridique", "expertises", "procedures", "correspondances"],
                format_func=lambda x: f"📂 {x.capitalize()}",
                key="container_select"
            )
        
        with col2:
            st.markdown("&nbsp;")
            if st.button("Parcourir", key="browse_container"):
                with st.spinner("Chargement des fichiers..."):
                    # Simulation du chargement
                    time.sleep(1)
                    st.success("✅ 15 documents trouvés")
                    data_loaded = True
    
    elif "📁" in input_method:
        uploaded_files = st.file_uploader(
            "Glissez vos fichiers ici",
            type=['pdf', 'txt', 'docx', 'xlsx'],
            accept_multiple_files=True,
            key="file_uploader",
            help="Formats supportés : PDF, TXT, DOCX, XLSX"
        )
        
        if uploaded_files:
            # Affichage des fichiers avec preview
            st.markdown("#### 📋 Fichiers sélectionnés")
            
            for file in uploaded_files:
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    file_icon = get_file_icon(file.name)
                    st.markdown(f"<div style='font-size: 2rem;'>{file_icon}</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**{file.name}**")
                    st.caption(f"Taille : {file.size / 1024:.1f} Ko")
                
                with col3:
                    if st.button("👁️", key=f"preview_{file.name}"):
                        # Preview du fichier
                        st.text(file.read()[:500].decode('utf-8', errors='ignore') + "...")
            
            data_loaded = True
    
    elif "🔍" in input_method:
        search_query = st.text_input(
            "Rechercher dans la base de données",
            placeholder="Ex: contrat de vente, jurisprudence 2024...",
            key="search_input"
        )
        
        # Filtres avancés
        with st.expander("🔧 Filtres avancés"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    "Période",
                    value=(datetime.now().replace(day=1), datetime.now()),
                    key="date_filter"
                )
            
            with col2:
                doc_types = st.multiselect(
                    "Types de documents",
                    ["Contrats", "Jurisprudence", "Doctrine", "Législation"],
                    key="doc_types"
                )
            
            with col3:
                jurisdictions = st.multiselect(
                    "Juridictions",
                    ["Cour de cassation", "Conseil d'État", "Cours d'appel"],
                    key="jurisdictions"
                )
        
        if st.button("🔍 Rechercher", type="primary", key="search_button"):
            with st.spinner("Recherche en cours..."):
                time.sleep(1.5)
                st.success("✅ 42 documents trouvés")
                data_loaded = True
    
    else:  # Texte direct
        text_input = st.text_area(
            "Entrez votre texte",
            height=300,
            placeholder="Collez votre texte juridique ici...",
            key="text_input"
        )
        
        if text_input:
            # Statistiques du texte
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Mots", len(text_input.split()))
            with col2:
                st.metric("Caractères", len(text_input))
            with col3:
                st.metric("Paragraphes", len(text_input.split('\n\n')))
            
            data_loaded = True
    
    # Validation et passage à l'étape suivante
    if data_loaded:
        st.success("✅ Données chargées avec succès")
        
        if st.button("Continuer vers la sélection des modèles →", type="primary", key="next_step_1"):
            st.session_state.module_state['current_step'] = 1
            st.rerun()

def render_ai_models_tab():
    """Onglet de sélection des modèles IA avec comparaison"""
    
    st.markdown("### 🤖 Sélection des modèles d'IA")
    
    # Mode de sélection
    selection_mode = st.radio(
        "Mode de sélection",
        ["🎯 Sélection manuelle", "🎲 Sélection automatique", "⚡ Profils prédéfinis"],
        horizontal=True,
        key="selection_mode"
    )
    
    selected_models = st.session_state.module_state.get('selected_models', [])
    
    if "🎯" in selection_mode:
        # Grille de modèles avec cartes interactives
        st.markdown("#### Cliquez pour sélectionner les modèles")
        
        cols = st.columns(3)
        
        for idx, (model_id, model) in enumerate(AI_MODELS.items()):
            with cols[idx % 3]:
                # Carte de modèle interactive
                is_selected = model_id in selected_models
                
                card_class = "model-card selected" if is_selected else "model-card"
                
                if st.button(
                    f"{model['icon']} {model['display_name']}",
                    key=f"model_{model_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    if is_selected:
                        selected_models.remove(model_id)
                    else:
                        selected_models.append(model_id)
                    st.session_state.module_state['selected_models'] = selected_models
                    st.rerun()
                
                # Détails du modèle
                st.markdown(f"""
                <div class="{card_class}">
                    <p style="margin: 0.5rem 0; font-size: 0.9rem; color: var(--text); opacity: 0.8;">
                        {model['description']}
                    </p>
                    <div style="margin-top: 0.5rem;">
                """, unsafe_allow_html=True)
                
                for strength in model['strengths']:
                    st.markdown(f"""
                        <span class="badge badge-success">{strength}</span>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
    
    elif "🎲" in selection_mode:
        # Sélection automatique basée sur le type d'analyse
        analysis_type = st.selectbox(
            "Type d'analyse",
            [
                "📜 Analyse contractuelle",
                "⚖️ Recherche jurisprudentielle",
                "📊 Due diligence",
                "🔍 Conformité réglementaire",
                "💡 Conseil juridique"
            ],
            key="analysis_type"
        )
        
        # Recommandations automatiques
        recommendations = get_model_recommendations(analysis_type)
        
        st.info(f"🤖 Modèles recommandés pour {analysis_type}")
        
        for model_id in recommendations:
            model = AI_MODELS[model_id]
            st.markdown(f"- **{model['icon']} {model['display_name']}** : {model['description']}")
        
        if st.button("Utiliser ces modèles", type="primary", key="use_recommendations"):
            st.session_state.module_state['selected_models'] = recommendations
            st.rerun()
    
    else:  # Profils prédéfinis
        profiles = {
            "🚀 Performance maximale": ["gpt4", "claude3", "gemini"],
            "⚡ Rapidité": ["gemini", "mistral"],
            "🇫🇷 Focus français": ["mistral", "claude3"],
            "💰 Économique": ["llama", "mistral"],
            "🔬 Analyse approfondie": ["claude3", "gpt4"]
        }
        
        selected_profile = st.selectbox(
            "Choisir un profil",
            list(profiles.keys()),
            key="profile_select"
        )
        
        st.markdown(f"**Modèles du profil {selected_profile} :**")
        
        profile_models = profiles[selected_profile]
        for model_id in profile_models:
            model = AI_MODELS[model_id]
            st.markdown(f"- {model['icon']} {model['display_name']}")
        
        if st.button(f"Utiliser le profil {selected_profile}", type="primary", key="use_profile"):
            st.session_state.module_state['selected_models'] = profile_models
            st.rerun()
    
    # Affichage des modèles sélectionnés
    if selected_models:
        st.markdown("---")
        st.markdown("#### ✅ Modèles sélectionnés")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            model_tags = " ".join([f"{AI_MODELS[m]['icon']} {AI_MODELS[m]['display_name']}" for m in selected_models])
            st.markdown(f"<div class='fade-in'>{model_tags}</div>", unsafe_allow_html=True)
        
        with col2:
            if st.button("🔄 Réinitialiser", key="reset_models"):
                st.session_state.module_state['selected_models'] = []
                st.rerun()
        
        # Mode de fusion
        st.markdown("#### 🔀 Mode de fusion des résultats")
        
        fusion_mode = st.select_slider(
            "Stratégie de fusion",
            options=[
                "Vote majoritaire",
                "Consensus pondéré",
                "Meilleure réponse",
                "Synthèse créative",
                "Analyse comparative"
            ],
            value=st.session_state.module_state.get('fusion_mode', 'Consensus pondéré'),
            key="fusion_mode_select"
        )
        
        st.session_state.module_state['fusion_mode'] = fusion_mode
        
        # Explication du mode
        fusion_explanations = {
            "Vote majoritaire": "Les modèles votent et la réponse majoritaire est retenue",
            "Consensus pondéré": "Les réponses sont pondérées selon la performance des modèles",
            "Meilleure réponse": "La réponse la plus complète et précise est sélectionnée",
            "Synthèse créative": "Une nouvelle réponse est créée en combinant les meilleures parties",
            "Analyse comparative": "Toutes les réponses sont présentées avec leurs différences"
        }
        
        st.info(f"💡 {fusion_explanations[fusion_mode]}")
        
        # Bouton suivant
        if st.button("Continuer vers la configuration →", type="primary", key="next_step_2"):
            st.session_state.module_state['current_step'] = 2
            st.rerun()
    else:
        st.warning("⚠️ Veuillez sélectionner au moins un modèle")

def render_configuration_tab():
    """Onglet de configuration avancée"""
    
    st.markdown("### ⚙️ Configuration de l'analyse")
    
    # Configuration par modèle
    selected_models = st.session_state.module_state.get('selected_models', [])
    
    if not selected_models:
        st.warning("⚠️ Aucun modèle sélectionné. Retournez à l'étape précédente.")
        return
    
    # Paramètres globaux
    st.markdown("#### 🌐 Paramètres globaux")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_length = st.slider(
            "Longueur maximale des réponses",
            100, 5000, 1000,
            step=100,
            key="max_length",
            help="Nombre de mots maximum par réponse"
        )
    
    with col2:
        language = st.selectbox(
            "Langue de sortie",
            ["🇫🇷 Français", "🇬🇧 Anglais", "🇪🇸 Espagnol", "🇩🇪 Allemand"],
            key="output_language"
        )
    
    with col3:
        detail_level = st.select_slider(
            "Niveau de détail",
            options=["Synthétique", "Standard", "Détaillé", "Exhaustif"],
            value="Standard",
            key="detail_level"
        )
    
    # Configuration par modèle avec accordéon
    st.markdown("#### 🎛️ Configuration individuelle des modèles")
    
    model_configs = {}
    
    for model_id in selected_models:
        model = AI_MODELS[model_id]
        
        with st.expander(f"{model['icon']} {model['display_name']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                temp = st.slider(
                    "Température (créativité)",
                    0.0, 1.0, model.get('temperature', 0.7),
                    step=0.1,
                    key=f"temp_{model_id}",
                    help="0 = Déterministe, 1 = Très créatif"
                )
                
                tokens = st.number_input(
                    "Tokens maximum",
                    100, 8000, model.get('max_tokens', 4096),
                    step=100,
                    key=f"tokens_{model_id}"
                )
            
            with col2:
                top_p = st.slider(
                    "Top P (diversité)",
                    0.0, 1.0, 0.9,
                    step=0.1,
                    key=f"top_p_{model_id}"
                )
                
                weight = st.slider(
                    "Poids dans la fusion",
                    0.0, 2.0, 1.0,
                    step=0.1,
                    key=f"weight_{model_id}",
                    help="Importance relative dans le mode fusion"
                )
            
            model_configs[model_id] = {
                'temperature': temp,
                'max_tokens': tokens,
                'top_p': top_p,
                'weight': weight
            }
    
    st.session_state.module_state['model_configs'] = model_configs
    
    # Options d'analyse spécifiques
    st.markdown("#### 🎯 Options d'analyse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_options = st.multiselect(
            "Types d'analyse",
            [
                "📝 Résumé exécutif",
                "🔍 Points clés",
                "⚠️ Risques identifiés",
                "💡 Recommandations",
                "📊 Analyse comparative",
                "🎯 Actions suggérées"
            ],
            default=["📝 Résumé exécutif", "🔍 Points clés", "💡 Recommandations"],
            key="analysis_options"
        )
    
    with col2:
        output_formats = st.multiselect(
            "Formats de sortie",
            ["📄 Document structuré", "📊 Tableau comparatif", "🗂️ Fiches synthétiques", "📈 Visualisations"],
            default=["📄 Document structuré"],
            key="output_formats"
        )
    
    # Modèles de prompt personnalisés
    with st.expander("✏️ Prompts personnalisés (optionnel)", expanded=False):
        custom_prompt = st.text_area(
            "Instructions supplémentaires pour l'analyse",
            placeholder="Ex: Concentrez-vous sur les aspects fiscaux et les clauses de responsabilité...",
            height=100,
            key="custom_prompt"
        )
    
    # Sauvegarder la configuration
    if st.button("💾 Sauvegarder cette configuration", key="save_config"):
        config_name = st.text_input("Nom de la configuration", key="config_name")
        if config_name:
            # Sauvegarder dans session state
            st.success(f"✅ Configuration '{config_name}' sauvegardée")
    
    # Bouton suivant
    st.markdown("---")
    
    if st.button("Lancer l'analyse →", type="primary", key="next_step_3", use_container_width=True):
        st.session_state.module_state['current_step'] = 3
        st.session_state.module_state['processing'] = True
        st.rerun()

def render_analysis_tab():
    """Onglet d'analyse avec visualisation en temps réel"""
    
    st.markdown("### 🚀 Analyse en cours")
    
    if not st.session_state.module_state.get('processing', False):
        st.info("💡 Configurez d'abord votre analyse dans les onglets précédents")
        return
    
    selected_models = st.session_state.module_state.get('selected_models', [])
    
    # Container pour l'animation de traitement
    processing_container = st.container()
    
    with processing_container:
        # Timeline des modèles
        st.markdown("#### 📊 Progression de l'analyse")
        
        # Créer les placeholders pour chaque modèle
        model_placeholders = {}
        progress_bars = {}
        
        for model_id in selected_models:
            model = AI_MODELS[model_id]
            
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{model['icon']}</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{model['display_name']}**")
                progress_bars[model_id] = st.progress(0)
                model_placeholders[model_id] = st.empty()
            
            with col3:
                status_placeholder = st.empty()
                status_placeholder.markdown("⏳ En attente...")
        
        # Simulation de l'analyse asynchrone
        st.markdown("---")
        
        # Logs en temps réel
        with st.expander("📝 Logs détaillés", expanded=True):
            log_container = st.empty()
            logs = []
        
        # Métriques en temps réel
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            metric1 = st.empty()
        with col2:
            metric2 = st.empty()
        with col3:
            metric3 = st.empty()
        with col4:
            metric4 = st.empty()
        
        # Simulation du traitement
        start_time = time.time()
        
        for i in range(101):
            # Mise à jour des barres de progression
            for idx, model_id in enumerate(selected_models):
                # Progression différente pour chaque modèle
                model_progress = min(100, i + (idx * 5))
                progress_bars[model_id].progress(model_progress / 100)
                
                # Statuts
                if model_progress < 30:
                    model_placeholders[model_id].info("🔄 Initialisation...")
                elif model_progress < 60:
                    model_placeholders[model_id].warning("⚡ Analyse en cours...")
                elif model_progress < 90:
                    model_placeholders[model_id].info("🔍 Finalisation...")
                else:
                    model_placeholders[model_id].success("✅ Terminé!")
            
            # Mise à jour des logs
            if i % 10 == 0:
                logs.append(f"[{time.strftime('%H:%M:%S')}] Traitement: {i}% complété")
                log_container.text('\n'.join(logs[-10:]))  # Garder les 10 derniers logs
            
            # Mise à jour des métriques
            elapsed = time.time() - start_time
            metric1.metric("⏱️ Temps écoulé", f"{elapsed:.1f}s")
            metric2.metric("📊 Progression", f"{i}%")
            metric3.metric("🔄 Modèles actifs", len(selected_models))
            metric4.metric("💾 Mémoire", f"{np.random.randint(100, 500)} MB")
            
            time.sleep(0.05)  # Simulation du délai
        
        # Résultats disponibles
        st.success("✅ Analyse terminée avec succès!")
        
        # Aperçu des résultats
        st.markdown("#### 👀 Aperçu des résultats")
        
        # Graphique de comparaison des scores
        scores = {AI_MODELS[m]['display_name']: np.random.uniform(0.7, 0.95) for m in selected_models}
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(scores.keys()),
                y=list(scores.values()),
                marker_color=['#8B0000', '#4B0000', '#FFD700', '#28A745', '#FFC107'][:len(scores)]
            )
        ])
        
        fig.update_layout(
            title="Scores de confiance par modèle",
            yaxis_title="Score",
            yaxis=dict(range=[0, 1]),
            showlegend=False,
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Enregistrer les résultats
        st.session_state.module_state['results'] = {
            'scores': scores,
            'processing_time': elapsed,
            'timestamp': datetime.now()
        }
        
        # Bouton pour voir les résultats complets
        if st.button("Voir les résultats détaillés →", type="primary", key="view_results", use_container_width=True):
            st.session_state.module_state['current_step'] = 4
            st.session_state.module_state['processing'] = False
            st.rerun()

def render_results_tab():
    """Onglet des résultats avec visualisations avancées"""
    
    st.markdown("### 📊 Résultats de l'analyse")
    
    results = st.session_state.module_state.get('results')
    
    if not results:
        st.info("💡 Aucun résultat disponible. Lancez d'abord une analyse.")
        return
    
    # Mode d'affichage
    view_mode = st.radio(
        "Mode d'affichage",
        ["📄 Vue synthétique", "🔍 Vue détaillée", "📊 Vue comparative", "📈 Visualisations"],
        horizontal=True,
        key="view_mode"
    )
    
    if "📄" in view_mode:
        render_synthetic_view(results)
    elif "🔍" in view_mode:
        render_detailed_view(results)
    elif "📊" in view_mode:
        render_comparative_view(results)
    else:
        render_visualizations(results)
    
    # Actions d'export
    st.markdown("---")
    st.markdown("### 💾 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Export Word", key="export_word", use_container_width=True):
            # Utiliser l'export manager
            st.info("Export Word en cours...")
    
    with col2:
        if st.button("📊 Export Excel", key="export_excel", use_container_width=True):
            st.info("Export Excel en cours...")
    
    with col3:
        if st.button("📧 Envoyer par email", key="send_email", use_container_width=True):
            st.info("Préparation de l'email...")
    
    with col4:
        if st.button("🔄 Nouvelle analyse", key="new_analysis", use_container_width=True):
            # Réinitialiser
            st.session_state.module_state['current_step'] = 0
            st.session_state.module_state['results'] = None
            st.session_state.module_state['processing'] = False
            st.rerun()

def render_synthetic_view(results):
    """Vue synthétique des résultats"""
    
    # Résumé exécutif
    st.markdown("#### 📝 Résumé exécutif")
    
    st.markdown("""
    <div class="model-card">
        <h5>Points clés de l'analyse</h5>
        <ul>
            <li><strong>Conclusion principale :</strong> Les clauses contractuelles sont conformes aux normes en vigueur</li>
            <li><strong>Risques identifiés :</strong> 3 points d'attention mineurs</li>
            <li><strong>Recommandations :</strong> 5 actions suggérées</li>
            <li><strong>Niveau de confiance :</strong> 92% (Très élevé)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques clés
    st.markdown("#### 📊 Métriques clés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Documents analysés</div>
            <div class="metric-value">15</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Temps d'analyse</div>
            <div class="metric-value">2.3s</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Modèles utilisés</div>
            <div class="metric-value">3</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Score moyen</div>
            <div class="metric-value">88%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Points d'attention
    st.markdown("#### ⚠️ Points d'attention")
    
    alerts = [
        ("⚡ Moyen", "Clause de limitation de responsabilité à préciser", "Article 7.2"),
        ("💡 Faible", "Délai de préavis pourrait être allongé", "Article 12.1"),
        ("💡 Faible", "Mention des données personnelles à compléter", "Annexe B")
    ]
    
    for level, message, ref in alerts:
        st.warning(f"{level} - {message} (Réf: {ref})")

def render_detailed_view(results):
    """Vue détaillée par modèle"""
    
    selected_models = st.session_state.module_state.get('selected_models', [])
    
    for model_id in selected_models:
        model = AI_MODELS[model_id]

        with st.expander(f"{model['icon']} Analyse de {model['display_name']}", expanded=True):
            # Tabs pour chaque section
            tabs = st.tabs(["Résumé", "Points clés", "Risques", "Recommandations"])
            
            with tabs[0]:
                st.markdown("""
                **Analyse générale :**
                
                Le document analysé présente une structure juridique solide avec des clauses bien définies.
                L'ensemble respecte les normes légales en vigueur, avec quelques points d'amélioration possibles
                pour renforcer la protection des parties.
                """)
            
            with tabs[1]:
                st.markdown("""
                - ✅ Clauses contractuelles complètes
                - ✅ Obligations clairement définies
                - ✅ Mécanismes de résolution des conflits prévus
                - ⚠️ Délais de notification à préciser
                """)
            
            with tabs[2]:
                risk_data = {
                    'Risque': ['Responsabilité', 'Confidentialité', 'Résiliation'],
                    'Niveau': ['Moyen', 'Faible', 'Faible'],
                    'Impact': ['Financier', 'Réputation', 'Opérationnel'],
                    'Probabilité': ['30%', '15%', '20%']
                }
                st.dataframe(pd.DataFrame(risk_data), use_container_width=True)
            
            with tabs[3]:
                st.markdown("""
                1. **Réviser la clause de limitation de responsabilité**
                   - Ajouter des plafonds spécifiques
                   - Clarifier les exclusions
                
                2. **Renforcer les clauses de confidentialité**
                   - Étendre la durée post-contractuelle
                   - Préciser les sanctions
                """)

def render_comparative_view(results):
    """Vue comparative entre modèles"""
    
    st.markdown("#### 🔍 Comparaison des analyses")
    
    # Tableau comparatif
    comparison_data = {
        'Critère': ['Complétude', 'Précision', 'Pertinence', 'Clarté', 'Temps'],
        'GPT-4': [95, 92, 94, 90, 2.1],
        'Claude 3': [93, 94, 95, 92, 2.3],
        'Gemini': [90, 91, 89, 88, 1.8]
    }
    
    df = pd.DataFrame(comparison_data)
    
    # Graphique radar
    fig = go.Figure()
    
    for col in df.columns[1:]:
        fig.add_trace(go.Scatterpolar(
            r=df[col],
            theta=df['Critère'],
            fill='toself',
            name=col
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Comparaison des performances par modèle"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Points de divergence
    st.markdown("#### 🔀 Points de divergence")
    
    divergences = [
        {
            'Point': 'Interprétation de la clause 5.3',
            'GPT-4': 'Restrictive',
            'Claude 3': 'Modérée',
            'Gemini': 'Permissive'
        },
        {
            'Point': 'Niveau de risque global',
            'GPT-4': 'Faible',
            'Claude 3': 'Moyen',
            'Gemini': 'Faible'
        }
    ]
    
    st.dataframe(pd.DataFrame(divergences), use_container_width=True)

def render_visualizations(results):
    """Visualisations avancées des résultats"""
    
    # Distribution des scores
    st.markdown("#### 📊 Distribution des scores d'analyse")
    
    scores_data = np.random.normal(85, 10, 100)
    
    fig = go.Figure(data=[go.Histogram(x=scores_data, nbinsx=20)])
    fig.update_layout(
        title="Distribution des scores de confiance",
        xaxis_title="Score (%)",
        yaxis_title="Fréquence",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap des corrélations
    st.markdown("#### 🔥 Matrice de corrélation des critères")
    
    criteria = ['Clarté', 'Précision', 'Complétude', 'Pertinence', 'Cohérence']
    corr_matrix = np.random.rand(5, 5)
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    np.fill_diagonal(corr_matrix, 1)
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=criteria,
        y=criteria,
        colorscale='RdBu'
    ))
    
    fig.update_layout(title="Corrélations entre critères d'analyse")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline d'analyse
    st.markdown("#### ⏱️ Chronologie de l'analyse")
    
    timeline_data = []
    base_time = datetime.now()
    
    for i, model in enumerate(['GPT-4', 'Claude 3', 'Gemini']):
        timeline_data.append({
            'Modèle': model,
            'Début': base_time,
            'Fin': base_time.replace(second=base_time.second + np.random.randint(1, 4))
        })
    
    fig = px.timeline(
        timeline_data,
        x_start="Début",
        x_end="Fin",
        y="Modèle",
        title="Temps d'exécution par modèle"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_sidebar():
    """Barre latérale avec aide et informations"""
    
    with st.sidebar:
        st.markdown("### 💡 Aide & Informations")
        
        # Guide rapide
        with st.expander("📖 Guide rapide", expanded=False):
            st.markdown("""
            1. **Chargez vos données** dans l'onglet Données
            2. **Sélectionnez les modèles** d'IA à utiliser
            3. **Configurez** les paramètres d'analyse
            4. **Lancez** l'analyse
            5. **Consultez** et exportez les résultats
            """)
        
        # Statistiques d'utilisation
        st.markdown("### 📊 Statistiques")
        
        metrics = st.session_state.performance_metrics
        
        st.metric("Analyses totales", metrics['total_analyses'])
        st.metric("Temps moyen", f"{metrics['avg_response_time']:.1f}s")
        
        # Modèles les plus utilisés
        st.markdown("#### 🏆 Modèles populaires")
        
        model_usage = metrics['model_usage']
        if any(model_usage.values()):
            sorted_models = sorted(model_usage.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for model_id, count in sorted_models:
                if count > 0:
                    model = AI_MODELS[model_id]
                    st.markdown(f"{model['icon']} {model['display_name']}: **{count}** utilisations")
        
        # Raccourcis
        st.markdown("### ⌨️ Raccourcis")
        
        shortcuts = [
            ("Ctrl+N", "Nouvelle analyse"),
            ("Ctrl+S", "Sauvegarder"),
            ("Ctrl+E", "Exporter"),
            ("F1", "Aide")
        ]
        
        for key, action in shortcuts:
            st.markdown(f"`{key}` : {action}")
        
        # Support
        st.markdown("### 🆘 Support")
        
        if st.button("💬 Contacter le support", use_container_width=True):
            st.info("Support : support@nexora-law.ai")
        
        if st.button("📚 Documentation", use_container_width=True):
            st.info("docs.nexora-law.ai")

def render_footer():
    """Footer avec informations et métriques"""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.caption("© 2024 Nexora Law IA")
    
    with col2:
        # Mini métriques de performance
        if st.session_state.module_state.get('results'):
            processing_time = st.session_state.module_state['results'].get('processing_time', 0)
            st.caption(f"⚡ Dernière analyse : {processing_time:.1f}s | 💾 Cache actif | 🟢 Tous systèmes opérationnels")
    
    with col3:
        st.caption(f"Version 2.0 | {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ========================= FONCTIONS UTILITAIRES =========================

def get_model_recommendations(analysis_type: str) -> List[str]:
    """Recommande des modèles selon le type d'analyse"""
    
    recommendations = {
        "📜 Analyse contractuelle": ["claude3", "gpt4", "mistral"],
        "⚖️ Recherche jurisprudentielle": ["gpt4", "claude3"],
        "📊 Due diligence": ["gpt4", "gemini", "claude3"],
        "🔍 Conformité réglementaire": ["claude3", "mistral", "gpt4"],
        "💡 Conseil juridique": ["claude3", "gpt4"]
    }
    
    return recommendations.get(analysis_type, ["gpt4", "claude3"])

async def process_with_model(model_id: str, content: str, config: Dict) -> Dict:
    """Traite le contenu avec un modèle spécifique (simulation)"""
    
    # Simulation d'appel API
    await asyncio.sleep(np.random.uniform(1, 3))
    
    # Résultat simulé
    return {
        'model_id': model_id,
        'response': f"Analyse par {AI_MODELS[model_id]['display_name']}",
        'confidence': np.random.uniform(0.7, 0.95),
        'tokens_used': np.random.randint(500, 2000),
        'processing_time': np.random.uniform(1, 3)
    }

def apply_fusion_strategy(responses: List[Dict], strategy: str) -> Dict:
    """Applique la stratégie de fusion sélectionnée"""
    
    if strategy == "Vote majoritaire":
        # Logique de vote
        return {'fused_response': "Résultat du vote majoritaire", 'method': strategy}
    
    elif strategy == "Consensus pondéré":
        # Pondération selon les scores
        return {'fused_response': "Résultat du consensus pondéré", 'method': strategy}
    
    elif strategy == "Meilleure réponse":
        # Sélection de la meilleure
        best = max(responses, key=lambda x: x.get('confidence', 0))
        return {'fused_response': best['response'], 'method': strategy, 'selected_model': best['model_id']}
    
    elif strategy == "Synthèse créative":
        # Création d'une nouvelle réponse
        return {'fused_response': "Synthèse créative des réponses", 'method': strategy}
    
    else:  # Analyse comparative
        return {'responses': responses, 'method': strategy}

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    run()