"""Module de comparaison de documents juridiques v3 - Lazy Loading avec Multi-IA"""

import base64
import hashlib
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import streamlit as st
from config.ai_models import AI_MODELS

# Configuration du logger
logger = logging.getLogger(__name__)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append(str(Path(__file__).parent.parent))
from utils import clean_key, format_legal_date, truncate_text
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# ============= CONFIGURATION DES MODÈLES IA =============

# Modèles IA importés depuis config.ai_models

# ============= FONCTION PRINCIPALE (OBLIGATOIRE POUR LAZY LOADING) =============

def run():
    """Fonction principale du module - OBLIGATOIRE pour le lazy loading"""
    
    # Configuration de la page
    st.markdown("""
    <style>
    /* Animations fluides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
    }
    
    /* Cartes avec effet de survol */
    .comparison-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    
    .comparison-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        border-color: rgba(99,102,241,0.5);
    }
    
    /* Badges colorés */
    .severity-critical { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
    }
    
    .severity-important { 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
    }
    
    .severity-minor { 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
    }
    
    /* Progress bars améliorées */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #6366f1 100%);
        background-size: 200% 100%;
        animation: shimmer 2s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    
    /* Metrics cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # En-tête avec animation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                       -webkit-background-clip: text; 
                       -webkit-text-fill-color: transparent;
                       font-size: 2.5em;
                       font-weight: 800;">
                📊 Module de Comparaison Juridique
            </h1>
            <p style="color: #94a3b8; font-size: 1.2em; margin-top: 10px;">
                Analysez et comparez vos documents avec l'intelligence artificielle
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialisation de l'état de session
    initialize_session_state()
    
    # Menu principal avec onglets stylisés
    tabs = st.tabs([
        "🔍 Nouvelle comparaison",
        "📊 Comparaisons actives", 
        "📜 Historique",
        "💾 Sauvegardes",
        "⚙️ Configuration IA",
        "📈 Statistiques",
        "❓ Aide"
    ])
    
    with tabs[0]:
        render_new_comparison()
    
    with tabs[1]:
        render_active_comparisons()
    
    with tabs[2]:
        render_history()
    
    with tabs[3]:
        render_saved_comparisons()
    
    with tabs[4]:
        render_ai_configuration()
    
    with tabs[5]:
        render_statistics()
    
    with tabs[6]:
        render_help()

# ============= INITIALISATION =============

def initialize_session_state():
    """Initialise les variables de session nécessaires"""
    defaults = {
        'comparison_history': [],
        'saved_comparisons': {},
        'active_comparisons': {},
        'ai_models_config': {
            'selected_models': ['gpt-4'],
            'fusion_mode': 'consensus',
            'temperature': 0.3,
            'max_tokens': 2000
        },
        'comparison_stats': {
            'total_comparisons': 0,
            'total_documents': 0,
            'average_similarity': 0,
            'most_used_models': Counter()
        }
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# ============= NOUVELLE COMPARAISON =============

def render_new_comparison():
    """Interface pour créer une nouvelle comparaison"""
    
    # Workflow en étapes
    if 'comparison_step' not in st.session_state:
        st.session_state.comparison_step = 1
    
    # Indicateur de progression
    progress_cols = st.columns(5)
    steps = ["📄 Documents", "🎯 Type", "🤖 IA", "⚙️ Options", "🚀 Lancer"]
    
    for i, (col, step) in enumerate(zip(progress_cols, steps)):
        with col:
            if i + 1 < st.session_state.comparison_step:
                st.success(step, icon="✅")
            elif i + 1 == st.session_state.comparison_step:
                st.info(step, icon="👉")
            else:
                st.caption(step)
    
    st.markdown("---")
    
    # Contenu selon l'étape
    if st.session_state.comparison_step == 1:
        render_step_documents()
    elif st.session_state.comparison_step == 2:
        render_step_comparison_type()
    elif st.session_state.comparison_step == 3:
        render_step_ai_selection()
    elif st.session_state.comparison_step == 4:
        render_step_options()
    elif st.session_state.comparison_step == 5:
        render_step_launch()

def render_step_documents():
    """Étape 1 : Sélection des documents"""
    st.markdown("### 📄 Sélection des documents à comparer")
    
    # Mode de sélection avec cartes visuelles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Documents chargés", use_container_width=True, help="Utiliser des documents déjà importés"):
            st.session_state.doc_source = "loaded"
    
    with col2:
        if st.button("✍️ Saisie directe", use_container_width=True, help="Saisir ou coller du texte"):
            st.session_state.doc_source = "manual"
    
    with col3:
        if st.button("⚡ Templates", use_container_width=True, help="Utiliser des exemples pré-définis"):
            st.session_state.doc_source = "templates"
    
    # Interface selon le mode choisi
    if 'doc_source' in st.session_state:
        st.markdown("---")
        
        if st.session_state.doc_source == "loaded":
            documents = select_loaded_documents()
        elif st.session_state.doc_source == "manual":
            documents = input_manual_documents()
        else:
            documents = select_template_documents()
        
        # Validation et passage à l'étape suivante
        if len(documents) >= 2:
            st.session_state.selected_documents = documents
            
            # Aperçu des documents sélectionnés
            st.markdown("#### 📋 Documents sélectionnés")
            for i, doc in enumerate(documents):
                with st.expander(f"{doc['title']} ({len(doc['content'])} caractères)", expanded=False):
                    st.caption(f"Source: {doc['source']}")
                    st.text(truncate_text(doc['content'], 500))
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Suivant ➡️", type="primary", use_container_width=True):
                    st.session_state.comparison_step = 2
                    st.rerun()
        else:
            st.warning("⚠️ Sélectionnez au moins 2 documents pour continuer")

def render_step_comparison_type():
    """Étape 2 : Type de comparaison"""
    st.markdown("### 🎯 Type d'analyse")
    
    # Cartes de sélection avec descriptions détaillées
    comparison_types = {
        "intelligent": {
            "title": "🧠 Analyse intelligente",
            "description": "L'IA détermine automatiquement la meilleure approche",
            "best_for": "Recommandé pour la plupart des cas",
            "icon": "🌟"
        },
        "chronological": {
            "title": "📅 Analyse chronologique",
            "description": "Compare l'évolution temporelle des faits",
            "best_for": "Témoignages, déclarations successives",
            "icon": "⏱️"
        },
        "contradictions": {
            "title": "⚠️ Détection de contradictions",
            "description": "Identifie les incohérences et conflits",
            "best_for": "Litiges, enquêtes",
            "icon": "🔍"
        },
        "evolution": {
            "title": "📈 Analyse d'évolution",
            "description": "Suit les changements entre versions",
            "best_for": "Contrats, documents révisés",
            "icon": "📊"
        },
        "structural": {
            "title": "🏗️ Comparaison structurelle",
            "description": "Compare l'organisation et la structure",
            "best_for": "Documents techniques, rapports",
            "icon": "📐"
        },
        "semantic": {
            "title": "💭 Analyse sémantique",
            "description": "Compare le sens profond et les idées",
            "best_for": "Expertises, argumentaires",
            "icon": "🎭"
        }
    }
    
    # Affichage en grille
    cols = st.columns(3)
    selected_type = None
    
    for i, (key, info) in enumerate(comparison_types.items()):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="comparison-card">
                <h4>{info['icon']} {info['title']}</h4>
                <p style="color: #94a3b8; font-size: 0.9em;">{info['description']}</p>
                <p style="color: #6366f1; font-size: 0.85em; font-weight: 600;">
                    Idéal pour : {info['best_for']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Sélectionner", key=f"select_type_{key}", use_container_width=True):
                st.session_state.comparison_type = key
                selected_type = key
    
    # Navigation
    if 'comparison_type' in st.session_state:
        st.success(f"Type sélectionné : {comparison_types[st.session_state.comparison_type]['title']}")
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("⬅️ Précédent", use_container_width=True):
                st.session_state.comparison_step = 1
                st.rerun()
        with col3:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                st.session_state.comparison_step = 3
                st.rerun()

def render_step_ai_selection():
    """Étape 3 : Sélection des modèles IA"""
    st.markdown("### 🤖 Configuration de l'Intelligence Artificielle")
    
    # Mode de sélection
    ai_mode = st.radio(
        "Mode d'utilisation",
        ["🎯 Modèle unique", "🔀 Multi-modèles avec fusion"],
        horizontal=True,
        help="Le mode fusion combine les analyses de plusieurs IA pour plus de fiabilité"
    )
    
    if ai_mode == "🎯 Modèle unique":
        render_single_model_selection()
    else:
        render_multi_model_selection()
    
    # Navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.comparison_step = 2
            st.rerun()
    with col3:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            st.session_state.comparison_step = 4
            st.rerun()

def render_single_model_selection():
    """Sélection d'un modèle unique"""
    st.markdown("#### 🎯 Choisir un modèle")
    
    # Affichage des modèles en cartes
    cols = st.columns(3)
    
    for i, (model_id, model_info) in enumerate(AI_MODELS.items()):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="comparison-card" style="text-align: center;">
                <h3>{model_info['icon']}</h3>
                <h5>{model_info['name']}</h5>
                <p style="font-size: 0.85em; color: #94a3b8;">{model_info['description']}</p>
                <div style="margin-top: 10px;">
                    {''.join([f'<span style="font-size: 0.8em; background: rgba(99,102,241,0.2); padding: 2px 8px; border-radius: 12px; margin: 2px;">{s}</span>' for s in model_info['strengths']])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Utiliser {model_info['name']}", key=f"use_{model_id}", use_container_width=True):
                st.session_state.ai_models_config['selected_models'] = [model_id]
                st.success(f"✅ {model_info['name']} sélectionné")

def render_multi_model_selection():
    """Sélection multi-modèles avec fusion"""
    st.markdown("#### 🔀 Sélection des modèles pour la fusion")
    
    # Sélection multiple
    selected_models = []
    
    cols = st.columns(3)
    for i, (model_id, model_info) in enumerate(AI_MODELS.items()):
        with cols[i % 3]:
            is_selected = st.checkbox(
                f"{model_info['icon']} {model_info['name']}",
                key=f"check_{model_id}",
                value=model_id in st.session_state.ai_models_config.get('selected_models', []),
                help=model_info['description']
            )
            if is_selected:
                selected_models.append(model_id)
    
    if selected_models:
        st.session_state.ai_models_config['selected_models'] = selected_models
        
        # Mode de fusion
        st.markdown("#### 🔀 Mode de fusion des analyses")
        
        fusion_modes = {
            "consensus": {
                "name": "🤝 Consensus",
                "description": "Retient les points sur lesquels la majorité des modèles s'accordent"
            },
            "comprehensive": {
                "name": "📚 Exhaustif",
                "description": "Combine toutes les analyses pour une vue complète"
            },
            "critical": {
                "name": "🔍 Critique",
                "description": "Met en évidence les divergences entre modèles"
            },
            "weighted": {
                "name": "⚖️ Pondéré",
                "description": "Donne plus de poids aux modèles spécialisés selon le contexte"
            }
        }
        
        fusion_mode = st.select_slider(
            "Mode de fusion",
            options=list(fusion_modes.keys()),
            format_func=lambda x: fusion_modes[x]['name'],
            value=st.session_state.ai_models_config.get('fusion_mode', 'consensus')
        )
        
        st.info(fusion_modes[fusion_mode]['description'])
        st.session_state.ai_models_config['fusion_mode'] = fusion_mode
        
        # Aperçu de la configuration
        st.success(f"✅ {len(selected_models)} modèles sélectionnés en mode {fusion_modes[fusion_mode]['name']}")
    else:
        st.warning("⚠️ Sélectionnez au moins un modèle")

def render_step_options():
    """Étape 4 : Options avancées"""
    st.markdown("### ⚙️ Options d'analyse")
    
    # Organisation en colonnes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Niveau d'analyse")
        
        detail_level = st.select_slider(
            "Niveau de détail",
            options=["Synthèse", "Standard", "Détaillé", "Exhaustif"],
            value="Détaillé",
            help="Détermine la profondeur de l'analyse"
        )
        
        st.markdown("#### 🎯 Focus de l'analyse")
        
        focus_differences = st.checkbox(
            "🔍 Mettre en évidence les différences",
            value=True,
            help="Accentue les divergences entre documents"
        )
        
        highlight_contradictions = st.checkbox(
            "⚠️ Signaler les contradictions",
            value=True,
            help="Identifie les incohérences majeures"
        )
        
        extract_entities = st.checkbox(
            "👥 Extraire les entités nommées",
            value=True,
            help="Personnes, lieux, dates, montants..."
        )
    
    with col2:
        st.markdown("#### 🔧 Paramètres techniques")
        
        similarity_threshold = st.slider(
            "Seuil de similarité",
            0.0, 1.0, 0.7,
            help="Pour détecter les passages similaires"
        )
        
        temperature = st.slider(
            "Température IA",
            0.0, 1.0, 0.3,
            help="0 = Factuel, 1 = Créatif"
        )
        
        max_tokens = st.number_input(
            "Tokens maximum",
            min_value=500,
            max_value=4000,
            value=2000,
            step=100,
            help="Longueur maximale de l'analyse"
        )
    
    # Sauvegarder les options
    st.session_state.comparison_config = {
        'detail_level': detail_level,
        'focus_differences': focus_differences,
        'highlight_contradictions': highlight_contradictions,
        'extract_entities': extract_entities,
        'similarity_threshold': similarity_threshold,
        'temperature': temperature,
        'max_tokens': max_tokens
    }
    
    # Navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.comparison_step = 3
            st.rerun()
    with col3:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            st.session_state.comparison_step = 5
            st.rerun()

def render_step_launch():
    """Étape 5 : Lancement de la comparaison"""
    st.markdown("### 🚀 Récapitulatif et lancement")
    
    # Récapitulatif visuel
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📋 Configuration de votre analyse")
        
        # Documents
        st.markdown(f"""
        <div class="comparison-card">
            <h5>📄 Documents ({len(st.session_state.selected_documents)})</h5>
            <ul style="margin: 10px 0;">
                {''.join([f'<li>{doc["title"]}</li>' for doc in st.session_state.selected_documents[:5]])}
                {f'<li>... et {len(st.session_state.selected_documents) - 5} autres</li>' if len(st.session_state.selected_documents) > 5 else ''}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Type d'analyse
        comparison_types = {
            "intelligent": "🧠 Analyse intelligente",
            "chronological": "📅 Analyse chronologique",
            "contradictions": "⚠️ Détection de contradictions",
            "evolution": "📈 Analyse d'évolution",
            "structural": "🏗️ Comparaison structurelle",
            "semantic": "💭 Analyse sémantique"
        }
        
        st.markdown(f"""
        <div class="comparison-card">
            <h5>🎯 Type d'analyse</h5>
            <p>{comparison_types.get(st.session_state.comparison_type, 'Non défini')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Modèles IA
        selected_models = st.session_state.ai_models_config['selected_models']
        st.markdown(f"""
        <div class="comparison-card">
            <h5>🤖 Intelligence Artificielle</h5>
            <p>{''.join([f'{AI_MODELS[m]["icon"]} {AI_MODELS[m]["name"]} ' for m in selected_models])}</p>
            {f'<p style="font-size: 0.9em; color: #94a3b8;">Mode fusion : {st.session_state.ai_models_config["fusion_mode"]}</p>' if len(selected_models) > 1 else ''}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Estimation du temps
        st.markdown("#### ⏱️ Estimation")
        
        # Calcul basé sur la complexité
        base_time = 30  # secondes
        time_per_doc = 10
        time_per_model = 15
        
        estimated_time = base_time + (len(st.session_state.selected_documents) * time_per_doc) + (len(selected_models) * time_per_model)
        
        st.metric(
            "Durée estimée",
            f"{estimated_time // 60}m {estimated_time % 60}s",
            help="Estimation basée sur la configuration"
        )
        
        # Coût estimé (fictif pour la démo)
        estimated_cost = len(selected_models) * 0.02 * len(st.session_state.selected_documents)
        st.metric(
            "Coût estimé",
            f"{estimated_cost:.2f} €",
            help="Basé sur l'utilisation des API"
        )
    
    # Actions
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.comparison_step = 4
            st.rerun()
    
    with col2:
        if st.button("💾 Sauvegarder config", use_container_width=True):
            save_configuration()
    
    with col3:
        if st.button("🔄 Recommencer", use_container_width=True):
            st.session_state.comparison_step = 1
            if 'doc_source' in st.session_state:
                del st.session_state.doc_source
            st.rerun()
    
    with col4:
        if st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True):
            launch_comparison()

# ============= COMPARAISONS ACTIVES =============

def render_active_comparisons():
    """Affiche les comparaisons en cours"""
    st.markdown("### 📊 Comparaisons actives")
    
    if not st.session_state.active_comparisons:
        st.info("Aucune comparaison en cours. Créez-en une nouvelle dans l'onglet 'Nouvelle comparaison'.")
        return
    
    # Vue en grille des comparaisons actives
    for comp_id, comparison in st.session_state.active_comparisons.items():
        with st.container():
            st.markdown(f"""
            <div class="comparison-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>{comparison['title']}</h4>
                        <p style="color: #94a3b8; margin: 5px 0;">
                            {comparison['type']} • {len(comparison['documents'])} documents • 
                            Démarré {comparison['started_at']}
                        </p>
                    </div>
                    <div>
                        {render_status_badge(comparison['status'])}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar si en cours
            if comparison['status'] == 'processing':
                progress = comparison.get('progress', 0)
                st.progress(progress / 100)
                st.caption(f"{comparison.get('current_step', 'Traitement...')}")
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if comparison['status'] == 'completed':
                    if st.button("👁️ Voir résultats", key=f"view_{comp_id}"):
                        display_comparison_results(comparison['results'])
            
            with col2:
                if comparison['status'] in ['completed', 'error']:
                    if st.button("📊 Rapport", key=f"report_{comp_id}"):
                        generate_report(comparison)
            
            with col3:
                if comparison['status'] == 'processing':
                    if st.button("⏸️ Pause", key=f"pause_{comp_id}"):
                        pause_comparison(comp_id)
                else:
                    if st.button("🔄 Relancer", key=f"restart_{comp_id}"):
                        restart_comparison(comp_id)
            
            with col4:
                if st.button("🗑️ Supprimer", key=f"delete_{comp_id}"):
                    if st.confirm("Confirmer la suppression ?"):
                        del st.session_state.active_comparisons[comp_id]
                        st.rerun()

# ============= HISTORIQUE =============

def render_history():
    """Affiche l'historique des comparaisons"""
    st.markdown("### 📜 Historique des comparaisons")
    
    if not st.session_state.comparison_history:
        st.info("Aucune comparaison dans l'historique.")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_filter = st.date_input(
            "Période",
            value=(datetime.now().date(), datetime.now().date()),
            help="Filtrer par date"
        )
    
    with col2:
        type_filter = st.selectbox(
            "Type d'analyse",
            ["Tous"] + list(set(h['type'] for h in st.session_state.comparison_history))
        )
    
    with col3:
        search_filter = st.text_input("🔍 Rechercher", placeholder="Titre, documents...")
    
    # Tableau avec pagination
    filtered_history = filter_history(date_filter, type_filter, search_filter)
    
    if filtered_history:
        # Pagination
        items_per_page = 10
        total_pages = (len(filtered_history) - 1) // items_per_page + 1
        
        current_page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            label_visibility="collapsed"
        )
        
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        # Affichage
        for item in filtered_history[start_idx:end_idx]:
            render_history_item(item)
        
        # Navigation
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.caption(f"Page {current_page} sur {total_pages}")
    else:
        st.warning("Aucun résultat trouvé avec ces filtres.")

# ============= CONFIGURATION IA =============

def render_ai_configuration():
    """Configuration avancée des modèles IA"""
    st.markdown("### ⚙️ Configuration de l'Intelligence Artificielle")
    
    # Onglets de configuration
    config_tabs = st.tabs(["🔧 Paramètres globaux", "🤖 Modèles", "🔑 API Keys", "📊 Performances"])
    
    with config_tabs[0]:
        render_global_ai_settings()
    
    with config_tabs[1]:
        render_model_configuration()
    
    with config_tabs[2]:
        render_api_keys_configuration()
    
    with config_tabs[3]:
        render_ai_performance_metrics()

def render_global_ai_settings():
    """Paramètres globaux de l'IA"""
    st.markdown("#### 🔧 Paramètres globaux")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mode par défaut
        default_mode = st.selectbox(
            "Mode par défaut",
            ["Modèle unique", "Multi-modèles"],
            help="Mode utilisé pour les nouvelles comparaisons"
        )
        
        # Température par défaut
        default_temp = st.slider(
            "Température par défaut",
            0.0, 1.0, 
            value=st.session_state.ai_models_config.get('temperature', 0.3),
            help="0 = Déterministe, 1 = Créatif"
        )
        
        # Timeout
        timeout = st.number_input(
            "Timeout API (secondes)",
            min_value=10,
            max_value=300,
            value=60,
            help="Délai maximum d'attente des réponses"
        )
    
    with col2:
        # Retry policy
        max_retries = st.number_input(
            "Nombre de tentatives",
            min_value=1,
            max_value=5,
            value=3,
            help="En cas d'erreur API"
        )
        
        # Cache
        enable_cache = st.checkbox(
            "Activer le cache",
            value=True,
            help="Mémorise les réponses pour économiser les coûts"
        )
        
        if enable_cache:
            cache_duration = st.number_input(
                "Durée du cache (heures)",
                min_value=1,
                max_value=168,
                value=24
            )
    
    # Sauvegarder
    if st.button("💾 Sauvegarder les paramètres", type="primary"):
        save_global_ai_settings({
            'default_mode': default_mode,
            'default_temperature': default_temp,
            'timeout': timeout,
            'max_retries': max_retries,
            'enable_cache': enable_cache,
            'cache_duration': cache_duration if enable_cache else None
        })
        st.success("✅ Paramètres sauvegardés")

def render_model_configuration():
    """Configuration individuelle des modèles"""
    st.markdown("#### 🤖 Configuration des modèles")
    
    # Sélecteur de modèle
    selected_model = st.selectbox(
        "Sélectionner un modèle",
        options=list(AI_MODELS.keys()),
        format_func=lambda x: f"{AI_MODELS[x]['icon']} {AI_MODELS[x]['name']}"
    )
    
    if selected_model:
        model_info = AI_MODELS[selected_model]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="comparison-card">
                <h4>{model_info['icon']} {model_info['name']}</h4>
                <p>{model_info['description']}</p>
                <p><strong>Fournisseur:</strong> {model_info['provider']}</p>
                <p><strong>Points forts:</strong> {', '.join(model_info['strengths'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Paramètres spécifiques
            st.markdown("##### Paramètres spécifiques")
            
            model_temp = st.slider(
                f"Température pour {model_info['name']}",
                0.0, 1.0, 0.3,
                key=f"temp_{selected_model}"
            )
            
            model_tokens = st.number_input(
                "Tokens maximum",
                min_value=100,
                max_value=8000,
                value=2000,
                key=f"tokens_{selected_model}"
            )
            
            # Rôles préférés
            st.multiselect(
                "Utiliser ce modèle pour",
                ["Analyse juridique", "Détection de contradictions", "Synthèse", "Extraction d'entités"],
                key=f"roles_{selected_model}"
            )
        
        with col2:
            # Statistiques d'utilisation
            st.markdown("##### 📊 Statistiques")
            
            stats = get_model_stats(selected_model)
            
            st.metric("Utilisations", stats.get('usage_count', 0))
            st.metric("Taux de succès", f"{stats.get('success_rate', 100):.1f}%")
            st.metric("Temps moyen", f"{stats.get('avg_time', 0):.1f}s")
            st.metric("Coût total", f"{stats.get('total_cost', 0):.2f}€")
            
            # Actions
            if st.button("🔄 Réinitialiser stats", key=f"reset_{selected_model}"):
                reset_model_stats(selected_model)
                st.success("Stats réinitialisées")

# ============= STATISTIQUES =============

def render_statistics():
    """Affiche les statistiques d'utilisation"""
    st.markdown("### 📈 Statistiques d'utilisation")
    
    stats = st.session_state.comparison_stats
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total comparaisons",
            stats['total_comparisons'],
            delta=f"+{get_weekly_change('comparisons')}% cette semaine"
        )
    
    with col2:
        st.metric(
            "Documents analysés",
            stats['total_documents'],
            delta=f"Moyenne: {stats['total_documents'] / max(stats['total_comparisons'], 1):.1f}/comparaison"
        )
    
    with col3:
        st.metric(
            "Similarité moyenne",
            f"{stats['average_similarity']:.0%}",
            delta="Entre documents"
        )
    
    with col4:
        most_used_model = stats['most_used_models'].most_common(1)
        if most_used_model:
            model_id, count = most_used_model[0]
            st.metric(
                "Modèle favori",
                AI_MODELS[model_id]['name'],
                delta=f"{count} utilisations"
            )
    
    # Graphiques
    st.markdown("---")

    # Graphique d'utilisation dans le temps
    fig1 = create_usage_timeline()
    if fig1:
        st.plotly_chart(fig1, use_container_width=True)

    # Répartition par type d'analyse
    fig2 = create_analysis_type_distribution()
    if fig2:
        st.plotly_chart(fig2, use_container_width=True)

    # Performance des modèles
    fig3 = create_model_performance_chart()
    if fig3:
        st.plotly_chart(fig3, use_container_width=True)

# ============= AIDE =============

def render_help():
    """Affiche l'aide et la documentation"""
    st.markdown("### ❓ Aide et documentation")
    
    # FAQ en accordéon
    with st.expander("🤔 Questions fréquentes", expanded=True):
        st.markdown("""
        **Q: Quelle est la différence entre les modes d'analyse ?**
        
        R: Chaque mode est optimisé pour un type de comparaison :
        - **Intelligent** : S'adapte automatiquement
        - **Chronologique** : Pour l'évolution temporelle
        - **Contradictions** : Pour identifier les conflits
        - **Evolution** : Pour suivre les changements
        - **Structurel** : Pour comparer l'organisation
        - **Sémantique** : Pour analyser le sens
        
        **Q: Comment fonctionne le mode fusion multi-modèles ?**
        
        R: Le mode fusion interroge plusieurs IA et combine leurs analyses selon la méthode choisie :
        - **Consensus** : Points communs
        - **Exhaustif** : Toutes les analyses
        - **Critique** : Met en évidence les divergences
        - **Pondéré** : Privilégie certains modèles selon le contexte
        
        **Q: Combien coûte une analyse ?**
        
        R: Le coût dépend des modèles utilisés et du nombre de documents. Une estimation est fournie avant chaque analyse.
        """)
    
    with st.expander("📚 Guide d'utilisation"):
        st.markdown("""
        ### Workflow recommandé
        
        1. **Préparez vos documents**
           - Format texte, PDF ou Word
           - Évitez les documents trop longs (> 50 pages)
           
        2. **Choisissez le bon type d'analyse**
           - En cas de doute, utilisez l'analyse intelligente
           
        3. **Sélectionnez les modèles IA**
           - Un seul modèle pour la rapidité
           - Multi-modèles pour la fiabilité
           
        4. **Configurez les options**
           - Niveau de détail selon vos besoins
           - Options spécifiques au type de document
           
        5. **Analysez les résultats**
           - Focus sur les divergences critiques
           - Vérifiez les sources en cas de doute
        """)
    
    with st.expander("🚀 Astuces avancées"):
        st.markdown("""
        - **Templates personnalisés** : Créez vos propres templates pour des analyses récurrentes
        - **Fusion pondérée** : Attribuez plus de poids aux modèles spécialisés
        - **Export automatique** : Configurez l'export automatique des rapports
        - **Intégration API** : Utilisez notre API pour automatiser les comparaisons
        """)
    
    # Support
    st.markdown("---")
    st.markdown("### 🆘 Support")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="comparison-card" style="text-align: center;">
            <h3>📧</h3>
            <h5>Email</h5>
            <p>support@nexora-law.ai</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="comparison-card" style="text-align: center;">
            <h3>💬</h3>
            <h5>Chat</h5>
            <p>Disponible 9h-18h</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="comparison-card" style="text-align: center;">
            <h3>📖</h3>
            <h5>Documentation</h5>
            <p>docs.nexora-law.ai</p>
        </div>
        """, unsafe_allow_html=True)

# ============= FONCTIONS UTILITAIRES =============

def select_loaded_documents():
    """Sélectionne des documents déjà chargés"""
    documents = []
    
    # Simuler des documents chargés
    if 'loaded_documents' not in st.session_state:
        st.session_state.loaded_documents = [
            {
                'id': 'doc1',
                'title': 'Contrat de prestation v1',
                'content': 'Contenu du contrat initial...',
                'source': 'Import',
                'date': '2024-01-15'
            },
            {
                'id': 'doc2',
                'title': 'Contrat de prestation v2',
                'content': 'Contenu du contrat révisé...',
                'source': 'Import',
                'date': '2024-02-20'
            }
        ]
    
    st.markdown("#### 📁 Documents disponibles")
    
    for doc in st.session_state.loaded_documents:
        if st.checkbox(f"{doc['title']} ({doc['date']})", key=f"select_{doc['id']}"):
            documents.append(doc)
    
    return documents

def input_manual_documents():
    """Interface de saisie manuelle"""
    documents = []
    
    num_docs = st.number_input(
        "Nombre de documents",
        min_value=2,
        max_value=10,
        value=2
    )
    
    for i in range(num_docs):
        with st.expander(f"📄 Document {i+1}", expanded=i<2):
            title = st.text_input(
                "Titre",
                value=f"Document {i+1}",
                key=f"manual_title_{i}"
            )
            
            content = st.text_area(
                "Contenu",
                height=200,
                key=f"manual_content_{i}",
                placeholder="Collez ou saisissez le contenu..."
            )
            
            if content:
                documents.append({
                    'id': f'manual_{i}',
                    'title': title,
                    'content': content,
                    'source': 'Saisie manuelle'
                })
    
    return documents

def select_template_documents():
    """Sélection de documents templates"""
    templates = {
        "Témoignages contradictoires": [
            {
                'title': 'Témoignage A',
                'content': 'Le véhicule bleu roulait à grande vitesse...'
            },
            {
                'title': 'Témoignage B',
                'content': 'Les deux véhicules roulaient normalement...'
            }
        ],
        "Versions de contrat": [
            {
                'title': 'Version initiale',
                'content': 'Article 1: Objet - Développement web...'
            },
            {
                'title': 'Version amendée',
                'content': 'Article 1: Objet - Développement web et mobile...'
            }
        ]
    }
    
    template_type = st.selectbox(
        "Choisir un template",
        list(templates.keys())
    )
    
    documents = []
    for i, template in enumerate(templates[template_type]):
        doc = {
            'id': f'template_{i}',
            'title': template['title'],
            'content': template['content'],
            'source': 'Template'
        }
        documents.append(doc)
    
    # Aperçu modifiable
    for i, doc in enumerate(documents):
        with st.expander(f"📄 {doc['title']}", expanded=True):
            content = st.text_area(
                "Contenu (modifiable)",
                value=doc['content'],
                height=150,
                key=f"template_content_{i}"
            )
            documents[i]['content'] = content
    
    return documents

def launch_comparison():
    """Lance une nouvelle comparaison"""
    # Créer un ID unique
    comp_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Préparer la comparaison
    comparison = {
        'id': comp_id,
        'title': f"Comparaison {len(st.session_state.selected_documents)} documents",
        'type': st.session_state.comparison_type,
        'documents': st.session_state.selected_documents,
        'config': st.session_state.comparison_config,
        'ai_config': st.session_state.ai_models_config,
        'status': 'processing',
        'progress': 0,
        'started_at': datetime.now().strftime('%H:%M'),
        'current_step': 'Initialisation...'
    }
    
    # Ajouter aux comparaisons actives
    st.session_state.active_comparisons[comp_id] = comparison
    
    # Rediriger vers l'onglet des comparaisons actives
    st.success("✅ Comparaison lancée ! Redirection...")
    time.sleep(1)
    
    # Simuler le traitement (dans la vraie app, ce serait asynchrone)
    simulate_comparison_processing(comp_id)
    
    # Réinitialiser le workflow
    st.session_state.comparison_step = 1
    if 'doc_source' in st.session_state:
        del st.session_state.doc_source
    
    st.rerun()

def simulate_comparison_processing(comp_id: str):
    """Simule le traitement d'une comparaison"""
    # Dans une vraie application, ceci serait fait de manière asynchrone
    comparison = st.session_state.active_comparisons[comp_id]
    
    # Simuler les étapes
    steps = [
        ("Préparation des documents", 10),
        ("Extraction des entités", 20),
        ("Analyse par IA", 50),
        ("Fusion des résultats", 70),
        ("Génération du rapport", 90),
        ("Finalisation", 100)
    ]
    
    for step, progress in steps:
        comparison['current_step'] = step
        comparison['progress'] = progress
        time.sleep(0.5)  # Simulation
    
    # Marquer comme terminé
    comparison['status'] = 'completed'
    comparison['completed_at'] = datetime.now().strftime('%H:%M')
    
    # Générer des résultats fictifs
    comparison['results'] = generate_mock_results(comparison)
    
    # Ajouter à l'historique
    st.session_state.comparison_history.append({
        'id': comp_id,
        'title': comparison['title'],
        'type': comparison['type'],
        'date': datetime.now(),
        'documents': [d['title'] for d in comparison['documents']],
        'results': comparison['results']
    })
    
    # Mettre à jour les statistiques
    update_statistics(comparison)

def generate_mock_results(comparison: Dict[str, Any]) -> Dict[str, Any]:
    """Génère des résultats fictifs pour la démo"""
    return {
        'summary': {
            'convergences': 12,
            'divergences': 5,
            'reliability_score': 0.78,
            'entities_found': 23
        },
        'convergences': [
            {
                'point': 'Date de l\'incident',
                'details': 'Tous les documents s\'accordent sur le 15 janvier 2024',
                'confidence': 0.95
            },
            {
                'point': 'Lieu de l\'événement',
                'details': 'Paris, 8ème arrondissement mentionné uniformément',
                'confidence': 0.90
            }
        ],
        'divergences': [
            {
                'point': 'Heure exacte',
                'details': 'Document A: 14h30, Document B: 15h00',
                'severity': 'important',
                'documents': ['Document A', 'Document B']
            }
        ],
        'ai_analysis': """
        L'analyse comparative révèle une cohérence globale forte (78%) entre les documents.
        Les principaux points de convergence concernent les faits objectifs (dates, lieux).
        Les divergences portent principalement sur des détails temporels et des appréciations subjectives.
        
        Recommandations :
        - Vérifier les horaires avec des sources tierces
        - Clarifier les témoignages sur les points divergents
        - Considérer le contexte de chaque déclaration
        """,
        'entities': {
            'persons': ['M. Dupont', 'Mme Martin'],
            'locations': ['Paris', '8ème arrondissement'],
            'dates': ['15 janvier 2024'],
            'organizations': ['Société ABC']
        }
    }

def display_comparison_results(results: Dict[str, Any]):
    """Affiche les résultats d'une comparaison"""
    st.markdown("### 📊 Résultats de l'analyse")
    
    # Métriques principales
    summary = results.get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "✅ Convergences",
            summary.get('convergences', 0),
            delta="Points communs"
        )
    
    with col2:
        st.metric(
            "❌ Divergences",
            summary.get('divergences', 0),
            delta="Différences",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "📈 Fiabilité",
            f"{summary.get('reliability_score', 0):.0%}",
            delta="Score global"
        )
    
    with col4:
        st.metric(
            "👥 Entités",
            summary.get('entities_found', 0),
            delta="Identifiées"
        )
    
    # Détails en onglets
    result_tabs = st.tabs([
        "📋 Synthèse",
        "✅ Convergences",
        "❌ Divergences",
        "🤖 Analyse IA",
        "👥 Entités",
        "📊 Visualisations"
    ])
    
    with result_tabs[0]:
        st.markdown("#### Synthèse de l'analyse")
        st.info(results.get('ai_analysis', 'Analyse non disponible'))
    
    with result_tabs[1]:
        st.markdown("#### Points de convergence")
        for conv in results.get('convergences', []):
            st.success(f"**{conv['point']}**\n\n{conv['details']}")
    
    with result_tabs[2]:
        st.markdown("#### Points de divergence")
        for div in results.get('divergences', []):
            severity_color = {
                'critical': 'red',
                'important': 'orange',
                'minor': 'blue'
            }.get(div.get('severity', 'minor'), 'blue')
            
            st.markdown(f"""
            <div style="border-left: 4px solid {severity_color}; padding-left: 10px; margin: 10px 0;">
                <strong>{div['point']}</strong><br>
                {div['details']}<br>
                <small>Documents concernés : {', '.join(div.get('documents', []))}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Télécharger PDF", use_container_width=True):
            st.info("Génération du PDF...")
    
    with col2:
        if st.button("📊 Export Excel", use_container_width=True):
            st.info("Export Excel en cours...")
    
    with col3:
        if st.button("🔗 Partager", use_container_width=True):
            st.info("Lien de partage généré")

def render_status_badge(status: str) -> str:
    """Génère un badge de statut HTML"""
    badges = {
        'processing': '<span class="severity-minor">⏳ En cours</span>',
        'completed': '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 16px;">✅ Terminé</span>',
        'error': '<span class="severity-critical">❌ Erreur</span>',
        'paused': '<span class="severity-important">⏸️ En pause</span>'
    }
    return badges.get(status, status)

def save_configuration():
    """Sauvegarde la configuration actuelle"""
    config_name = f"Config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if 'saved_configs' not in st.session_state:
        st.session_state.saved_configs = {}
    
    st.session_state.saved_configs[config_name] = {
        'comparison_type': st.session_state.get('comparison_type'),
        'ai_config': st.session_state.get('ai_models_config'),
        'comparison_config': st.session_state.get('comparison_config')
    }
    
    st.success(f"✅ Configuration sauvegardée : {config_name}")

def update_statistics(comparison: Dict[str, Any]):
    """Met à jour les statistiques globales"""
    stats = st.session_state.comparison_stats
    
    stats['total_comparisons'] += 1
    stats['total_documents'] += len(comparison['documents'])
    
    # Mettre à jour les modèles utilisés
    for model in comparison['ai_config']['selected_models']:
        stats['most_used_models'][model] += 1
    
    # Calculer la similarité moyenne (fictif pour la démo)
    if comparison['results']:
        similarity = comparison['results']['summary']['reliability_score']
        current_avg = stats['average_similarity']
        total = stats['total_comparisons']
        stats['average_similarity'] = (current_avg * (total - 1) + similarity) / total

# Fonctions helpers additionnelles

def get_weekly_change(metric_type: str) -> int:
    """Calcule le changement hebdomadaire (fictif pour la démo)"""
    import random
    return random.randint(-20, 50)

def filter_history(date_filter, type_filter, search_filter):
    """Filtre l'historique selon les critères"""
    history = st.session_state.comparison_history
    
    # Filtrer par date
    if date_filter:
        start_date, end_date = date_filter
        history = [h for h in history if start_date <= h['date'].date() <= end_date]
    
    # Filtrer par type
    if type_filter != "Tous":
        history = [h for h in history if h['type'] == type_filter]
    
    # Filtrer par recherche
    if search_filter:
        search_lower = search_filter.lower()
        history = [h for h in history if 
                  search_lower in h['title'].lower() or
                  any(search_lower in doc.lower() for doc in h['documents'])]
    
    return history

def render_history_item(item: Dict[str, Any]):
    """Affiche un élément d'historique"""
    with st.expander(
        f"📊 {item['title']} - {item['date'].strftime('%d/%m/%Y %H:%M')}",
        expanded=False
    ):
        st.write(f"**Type:** {item['type']}")
        st.write(f"**Documents:** {', '.join(item['documents'])}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️ Voir", key=f"view_hist_{item['id']}"):
                display_comparison_results(item['results'])
        
        with col2:
            if st.button("📋 Copier config", key=f"copy_hist_{item['id']}"):
                st.info("Configuration copiée")
        
        with col3:
            if st.button("🗑️ Supprimer", key=f"del_hist_{item['id']}"):
                st.session_state.comparison_history.remove(item)
                st.rerun()

def get_model_stats(model_id: str) -> Dict[str, Any]:
    """Récupère les statistiques d'un modèle (fictif pour la démo)"""
    import random
    return {
        'usage_count': random.randint(10, 500),
        'success_rate': random.uniform(95, 99.9),
        'avg_time': random.uniform(2, 10),
        'total_cost': random.uniform(5, 100)
    }

def create_usage_timeline():
    """Crée un graphique timeline."""
    
    # Données fictives
    import random
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    values = [random.randint(5, 20) for _ in range(30)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Comparaisons',
        line=dict(color='#6366f1', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Utilisation sur 30 jours",
        xaxis_title="Date",
        yaxis_title="Nombre de comparaisons",
        height=400,
        template="plotly_dark"
    )
    
    return fig

def reset_model_stats(model_id: str):
    """Réinitialise les statistiques d'un modèle"""
    # Logique de réinitialisation
    pass

def save_global_ai_settings(settings: Dict[str, Any]):
    """Sauvegarde les paramètres globaux de l'IA"""
    if 'global_ai_settings' not in st.session_state:
        st.session_state.global_ai_settings = {}
    
    st.session_state.global_ai_settings.update(settings)

# ============= POINT D'ENTRÉE POUR COMPATIBILITY =============

def render():
    """Point d'entrée pour compatibilité avec l'ancien système"""
    run()

# Pour les tests directs
if __name__ == "__main__":
    run()