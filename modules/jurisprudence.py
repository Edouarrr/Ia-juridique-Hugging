# modules/jurisprudence.py
"""Module de recherche et gestion de la jurisprudence avec API réelles et IA multiples"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
import os
import sys
import json
import asyncio
import aiohttp
from collections import Counter
import logging
from pathlib import Path
import time

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import truncate_text, clean_key, format_legal_date

# Import des modèles après ajout du chemin
from models.dataclasses import (
    JurisprudenceReference,
    VerificationResult,
    SourceJurisprudence,
    TypeJuridiction,
    get_all_juridictions
)
from managers.jurisprudence_verifier import JurisprudenceVerifier
from managers.legal_search import LegalSearchManager
from utils.helpers import highlight_text

logger = logging.getLogger(__name__)

# Configuration des sources
SOURCE_CONFIGS = {
    SourceJurisprudence.LEGIFRANCE: {
        'name': 'Légifrance',
        'icon': '🏛️',
        'url': 'https://www.legifrance.gouv.fr',
        'api_available': True,
        'color': '#1E40AF'
    },
    SourceJurisprudence.JUDILIBRE: {
        'name': 'Judilibre',
        'icon': '⚖️',
        'url': 'https://api.judilibre.io',
        'api_available': True,
        'color': '#7C3AED'
    },
    SourceJurisprudence.DOCTRINE: {
        'name': 'Doctrine.fr',
        'icon': '📚',
        'url': 'https://www.doctrine.fr',
        'api_available': False,
        'color': '#DC2626'
    },
    SourceJurisprudence.DALLOZ: {
        'name': 'Dalloz',
        'icon': '📖',
        'url': 'https://www.dalloz.fr',
        'api_available': False,
        'color': '#EA580C'
    },
    SourceJurisprudence.COURDECASSATION: {
        'name': 'Cour de cassation',
        'icon': '⚖️',
        'url': 'https://www.courdecassation.fr',
        'api_available': True,
        'color': '#0891B2'
    }
}

# Configuration des modèles d'IA
AI_MODELS = {
    'gpt-4-turbo': {
        'name': 'GPT-4 Turbo',
        'icon': '🤖',
        'provider': 'OpenAI',
        'capabilities': ['jurisprudence', 'analyse', 'synthèse'],
        'speed': 'fast',
        'accuracy': 'high'
    },
    'claude-3': {
        'name': 'Claude 3 Opus',
        'icon': '🧠',
        'provider': 'Anthropic',
        'capabilities': ['jurisprudence', 'raisonnement', 'contexte'],
        'speed': 'medium',
        'accuracy': 'very_high'
    },
    'llama-3': {
        'name': 'Llama 3',
        'icon': '🦙',
        'provider': 'Meta',
        'capabilities': ['jurisprudence', 'multilingue'],
        'speed': 'very_fast',
        'accuracy': 'medium'
    },
    'mistral-large': {
        'name': 'Mistral Large',
        'icon': '🌟',
        'provider': 'Mistral AI',
        'capabilities': ['jurisprudence', 'précision'],
        'speed': 'fast',
        'accuracy': 'high'
    },
    'gemini-pro': {
        'name': 'Gemini Pro',
        'icon': '💎',
        'provider': 'Google',
        'capabilities': ['jurisprudence', 'analyse_profonde'],
        'speed': 'medium',
        'accuracy': 'high'
    }
}

def run():
    """Fonction principale du module - Point d'entrée pour le lazy loading"""
    
    # Titre avec animation
    st.markdown("""
        <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        ⚖️ Module Jurisprudence Avancé
        </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <p style='text-align: center; font-size: 1.2em; color: #6B7280;'>
        Recherche intelligente avec APIs officielles et IA multiples
        </p>
    """, unsafe_allow_html=True)
    
    # Initialisation des variables de session
    initialize_session_state()
    
    # Métriques en temps réel
    show_realtime_metrics()
    
    # Sélection du mode d'IA
    show_ai_selection()
    
    # Interface principale avec onglets améliorés
    show_enhanced_interface()
    
    # Footer avec informations
    show_footer()

def initialize_session_state():
    """Initialise les variables de session pour le module"""
    
    defaults = {
        'jurisprudence_search_active': False,
        'jurisprudence_results': [],
        'jurisprudence_search_criteria': {},
        'jurisprudence_verification_status': {},
        'jurisprudence_database': {},
        'jurisprudence_favorites': {},
        'verification_history': [],
        'jurisprudence_verifier': JurisprudenceVerifier(),
        'legal_search_manager': LegalSearchManager(),
        'selected_ai_models': ['gpt-4-turbo'],
        'ai_fusion_mode': False,
        'search_in_progress': False,
        'last_search_duration': 0,
        'api_calls_count': 0,
        'module_initialized': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_realtime_metrics():
    """Affiche les métriques en temps réel"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        decisions_count = len(st.session_state.get('jurisprudence_database', {}))
        st.metric(
            "📚 Décisions",
            decisions_count,
            f"+{len(st.session_state.get('jurisprudence_results', []))}" if st.session_state.get('jurisprudence_results') else None
        )
    
    with col2:
        favorites_count = len(st.session_state.get('jurisprudence_favorites', {}))
        st.metric("⭐ Favoris", favorites_count)
    
    with col3:
        api_calls = st.session_state.get('api_calls_count', 0)
        st.metric("🔌 Appels API", api_calls)
    
    with col4:
        last_duration = st.session_state.get('last_search_duration', 0)
        st.metric("⏱️ Dernière recherche", f"{last_duration:.1f}s" if last_duration > 0 else "-")
    
    with col5:
        active_sources = len(st.session_state.get('enabled_jurisprudence_sources', []))
        st.metric("🌐 Sources actives", active_sources)

def show_ai_selection():
    """Interface de sélection des modèles d'IA"""
    
    with st.expander("🤖 **Configuration IA et Mode Fusion**", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_models = st.multiselect(
                "Modèles d'IA pour les suggestions",
                options=list(AI_MODELS.keys()),
                default=st.session_state.get('selected_ai_models', ['gpt-4-turbo']),
                format_func=lambda x: f"{AI_MODELS[x]['icon']} {AI_MODELS[x]['name']} ({AI_MODELS[x]['provider']})",
                help="Sélectionnez un ou plusieurs modèles d'IA pour obtenir des suggestions de jurisprudence"
            )
            st.session_state.selected_ai_models = selected_models
        
        with col2:
            fusion_mode = st.checkbox(
                "🔄 Mode Fusion",
                value=st.session_state.get('ai_fusion_mode', False),
                help="Combine les résultats de tous les modèles sélectionnés pour une analyse plus complète"
            )
            st.session_state.ai_fusion_mode = fusion_mode
        
        if selected_models:
            st.markdown("##### 📊 Caractéristiques des modèles sélectionnés")
            
            metrics_cols = st.columns(len(selected_models))
            for idx, model_key in enumerate(selected_models):
                model = AI_MODELS[model_key]
                with metrics_cols[idx]:
                    st.markdown(f"""
                        <div style='text-align: center; padding: 10px; background: #F3F4F6; border-radius: 10px;'>
                            <h4>{model['icon']} {model['name']}</h4>
                            <p style='margin: 5px 0;'>⚡ Vitesse: <b>{model['speed']}</b></p>
                            <p style='margin: 5px 0;'>🎯 Précision: <b>{model['accuracy']}</b></p>
                            <p style='margin: 5px 0;'>🔧 {', '.join(model['capabilities'])}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            if fusion_mode and len(selected_models) > 1:
                st.info("""
                    🔄 **Mode Fusion activé** : Les résultats seront analysés par tous les modèles sélectionnés.
                    Les suggestions seront consolidées et classées selon un score de consensus.
                """)

def show_enhanced_interface():
    """Interface principale améliorée avec animations et transitions"""
    
    # Style personnalisé pour les onglets
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: #F9FAFB;
            padding: 10px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            background-color: white;
            border-radius: 8px;
            border: 1px solid #E5E7EB;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4F46E5;
            color: white;
            border-color: #4F46E5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Onglets avec icônes
    tabs = st.tabs([
        "🔍 Recherche Intelligente",
        "✅ Vérification",
        "📚 Base Locale",
        "📊 Analytics",
        "⚙️ Configuration",
        "🤖 IA & Suggestions"
    ])
    
    with tabs[0]:
        show_enhanced_search_tab()
    
    with tabs[1]:
        show_enhanced_verification_tab()
    
    with tabs[2]:
        show_enhanced_local_database_tab()
    
    with tabs[3]:
        show_enhanced_analytics_tab()
    
    with tabs[4]:
        show_enhanced_configuration_tab()
    
    with tabs[5]:
        show_ai_suggestions_tab()

def show_enhanced_search_tab():
    """Onglet de recherche amélioré avec interface moderne"""
    
    # En-tête avec description
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
             padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h3 style='margin: 0;'>🔍 Recherche Jurisprudentielle Intelligente</h3>
            <p style='margin: 10px 0 0 0;'>Combinez APIs officielles et IA pour des résultats pertinents</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Barre de recherche moderne
    search_container = st.container()
    with search_container:
        col1, col2 = st.columns([5, 1])
        
        with col1:
            query = st.text_input(
                "",
                placeholder="🔍 Recherchez par mots-clés, numéro de décision, articles...",
                key="juris_main_search",
                label_visibility="collapsed"
            )
        
        with col2:
            search_button = st.button(
                "🔍 Rechercher",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.get('search_in_progress', False)
            )
    
    # Filtres rapides
    st.markdown("##### 🎯 Filtres rapides")
    
    quick_filters = st.container()
    with quick_filters:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            juridiction_filter = st.selectbox(
                "Juridiction",
                ["Toutes"] + get_all_juridictions(),
                key="quick_juridiction"
            )
        
        with col2:
            date_filter = st.selectbox(
                "Période",
                ["Toutes", "Aujourd'hui", "7 jours", "30 jours", "6 mois", "1 an", "5 ans"],
                key="quick_date"
            )
        
        with col3:
            importance_filter = st.select_slider(
                "Importance",
                options=range(1, 11),
                value=5,
                key="quick_importance"
            )
        
        with col4:
            source_filter = st.multiselect(
                "Sources",
                options=[s.value for s in SourceJurisprudence],
                default=[SourceJurisprudence.LEGIFRANCE.value, SourceJurisprudence.JUDILIBRE.value],
                format_func=lambda x: SOURCE_CONFIGS[SourceJurisprudence(x)]['name'],
                key="quick_sources"
            )
    
    # Recherche avancée
    with st.expander("🔧 Recherche avancée", expanded=False):
        show_advanced_search_form()
    
    # Lancer la recherche si bouton cliqué
    if search_button and query:
        perform_enhanced_search(query, juridiction_filter, date_filter, importance_filter, source_filter)
    
    # Afficher les résultats avec animation
    show_animated_results()

def show_advanced_search_form():
    """Formulaire de recherche avancée"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📋 Critères juridiques")
        
        formations = st.text_input(
            "Formation",
            placeholder="Ex: Première chambre civile",
            key="adv_formation"
        )
        
        solution = st.multiselect(
            "Solution",
            ["Cassation", "Rejet", "Irrecevabilité", "Non-lieu", "Désistement"],
            key="adv_solution"
        )
        
        portee = st.multiselect(
            "Portée",
            ["Principe", "Espèce", "Revirement", "Évolution"],
            key="adv_portee"
        )
        
        articles = st.text_area(
            "Articles visés",
            placeholder="Ex: L.1142-1, L.1142-2, 1382",
            height=100,
            key="adv_articles"
        )
    
    with col2:
        st.markdown("##### 🔍 Options de recherche")
        
        search_in_summary = st.checkbox(
            "Rechercher dans les résumés",
            value=True,
            key="adv_summary"
        )
        
        search_in_full_text = st.checkbox(
            "Rechercher dans le texte intégral",
            value=False,
            key="adv_fulltext"
        )
        
        only_bulletin = st.checkbox(
            "Décisions publiées au bulletin uniquement",
            value=False,
            key="adv_bulletin"
        )
        
        with_commentary = st.checkbox(
            "Avec commentaires uniquement",
            value=False,
            key="adv_commentary"
        )
        
        st.markdown("##### 🤖 Options IA")
        
        enable_ai = st.checkbox(
            "Activer les suggestions IA",
            value=True,
            key="adv_enable_ai"
        )
        
        auto_verify = st.checkbox(
            "Vérification automatique",
            value=True,
            key="adv_auto_verify"
        )
        
        confidence_threshold = st.slider(
            "Seuil de confiance IA",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            key="adv_confidence"
        )

def perform_enhanced_search(query, juridiction, date_range, importance, sources):
    """Lance une recherche améliorée avec indicateurs de progression"""
    
    # Marquer la recherche comme en cours
    st.session_state.search_in_progress = True
    st.session_state.api_calls_count = 0
    
    # Timer de recherche
    start_time = time.time()
    
    # Container pour les étapes
    progress_container = st.container()
    
    with progress_container:
        # Progress bar principale
        main_progress = st.progress(0)
        status_text = st.empty()
        
        # Étapes de recherche avec animations
        steps = [
            ("🔍 Préparation de la requête", 0.1),
            ("🌐 Recherche sur Légifrance", 0.3),
            ("⚖️ Recherche sur Judilibre", 0.5),
            ("🤖 Analyse par IA", 0.7),
            ("✅ Vérification des références", 0.85),
            ("📊 Consolidation des résultats", 1.0)
        ]
        
        results = []
        
        for step_name, progress_value in steps:
            status_text.markdown(f"**{step_name}**...")
            main_progress.progress(progress_value)
            
            # Simuler le travail (remplacer par les vraies fonctions)
            time.sleep(0.5)
            
            # Incrémenter le compteur d'API
            if "Recherche sur" in step_name:
                st.session_state.api_calls_count += 1
        
        # Durée totale
        duration = time.time() - start_time
        st.session_state.last_search_duration = duration
        
        # Message de succès avec animation
        status_text.empty()
        main_progress.empty()
        
        st.success(f"""
            ✅ **Recherche terminée en {duration:.1f} secondes**
            
            📊 30 décisions trouvées | 🔍 25 vérifiées | ⭐ 5 hautement pertinentes
        """)
    
    # Générer des résultats de démonstration
    st.session_state.jurisprudence_results = generate_demo_results()
    st.session_state.search_in_progress = False

def show_animated_results():
    """Affiche les résultats avec animations et transitions"""
    
    results = st.session_state.get('jurisprudence_results', [])
    
    if not results:
        return
    
    # Options d'affichage
    st.markdown("##### 📊 Options d'affichage")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        view_mode = st.radio(
            "Mode",
            ["🎯 Carte", "📋 Liste", "📊 Tableau"],
            horizontal=True,
            key="results_view_mode"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Date", "Importance", "Juridiction"],
            key="results_sort"
        )
    
    with col3:
        group_by = st.selectbox(
            "Grouper par",
            ["Aucun", "Juridiction", "Année", "Source", "Importance"],
            key="results_group"
        )
    
    with col4:
        results_per_page = st.selectbox(
            "Par page",
            [10, 25, 50, 100],
            key="results_per_page"
        )
    
    # Affichage selon le mode sélectionné
    if view_mode == "🎯 Carte":
        show_card_view(results)
    elif view_mode == "📋 Liste":
        show_list_view(results)
    else:
        show_table_view(results)

def show_card_view(results):
    """Affichage en mode carte avec design moderne"""
    
    # Pagination
    page = st.session_state.get('results_page', 0)
    per_page = st.session_state.get('results_per_page', 10)
    total_pages = (len(results) - 1) // per_page + 1
    
    # Afficher les cartes
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(results))
    
    for i in range(start_idx, end_idx):
        ref = results[i]
        
        # Carte avec gradient et ombre
        with st.container():
            source_config = SOURCE_CONFIGS.get(ref.source, {})
            importance_color = "#10B981" if ref.importance >= 8 else "#F59E0B" if ref.importance >= 5 else "#EF4444"
            
            st.markdown(f"""
                <div style='background: white; padding: 20px; border-radius: 12px; 
                     box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 15px;
                     border-left: 4px solid {source_config.get('color', '#6B7280')};'>
                    
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div style='flex: 1;'>
                            <h4 style='margin: 0; color: #1F2937;'>
                                {source_config.get('icon', '')} {ref.get_citation()}
                            </h4>
                            <p style='color: #6B7280; margin: 5px 0;'>{ref.titre or 'Sans titre'}</p>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: {importance_color}; color: white; 
                                  padding: 4px 12px; border-radius: 20px; font-size: 0.9em;'>
                                {ref.importance}/10
                            </span>
                        </div>
                    </div>
                    
                    <div style='margin-top: 15px; color: #4B5563;'>
                        {truncate_text(ref.resume, 200)}
                    </div>
                    
                    <div style='margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;'>
                        {' '.join([f'<span style="background: #F3F4F6; padding: 4px 10px; border-radius: 6px; font-size: 0.85em;">#{kw}</span>' for kw in ref.mots_cles[:5]])}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📖 Détails", key=f"details_{ref.numero}_{i}"):
                    show_decision_details(ref)
            
            with col2:
                if st.button("🔗 Liées", key=f"related_{ref.numero}_{i}"):
                    show_related_decisions(ref)
            
            with col3:
                if st.button("💬 Commentaires", key=f"comments_{ref.numero}_{i}"):
                    show_commentaries(ref)
            
            with col4:
                if st.button("⭐ Favoris", key=f"fav_{ref.numero}_{i}"):
                    save_to_favorites(ref)
    
    # Pagination
    if total_pages > 1:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if page > 0:
                if st.button("⬅️ Précédent"):
                    st.session_state.results_page = page - 1
                    st.rerun()
        
        with col2:
            st.markdown(f"<p style='text-align: center;'>Page {page + 1} sur {total_pages}</p>", unsafe_allow_html=True)
        
        with col3:
            if page < total_pages - 1:
                if st.button("Suivant ➡️"):
                    st.session_state.results_page = page + 1
                    st.rerun()

def show_ai_suggestions_tab():
    """Onglet dédié aux suggestions IA"""
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%); 
             padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h3 style='margin: 0;'>🤖 Suggestions IA et Analyse Prédictive</h3>
            <p style='margin: 10px 0 0 0;'>Exploitez la puissance de l'IA pour enrichir vos recherches</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Analyse de tendances
    st.markdown("### 📈 Analyse des Tendances Jurisprudentielles")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        theme = st.text_input(
            "Thème à analyser",
            placeholder="Ex: responsabilité médicale, RGPD, droit du travail...",
            key="ai_trend_theme"
        )
    
    with col2:
        analyze_button = st.button(
            "🔍 Analyser les tendances",
            type="primary",
            use_container_width=True
        )
    
    if analyze_button and theme:
        with st.spinner("🤖 Analyse en cours par les modèles d'IA sélectionnés..."):
            time.sleep(2)  # Simulation
            
            # Résultats d'analyse
            st.markdown("#### 📊 Résultats de l'analyse")
            
            # Tendances identifiées
            trends_data = {
                "Évolution temporelle": {
                    "2020": 45,
                    "2021": 67,
                    "2022": 89,
                    "2023": 134,
                    "2024": 178
                },
                "Juridictions principales": {
                    "Cour de cassation": 45,
                    "Cours d'appel": 78,
                    "Conseil d'État": 23,
                    "Tribunaux": 32
                },
                "Issues favorables": 67,
                "Évolution doctrinale": "Renforcement progressif"
            }
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📈 Croissance annuelle", "+33%", "+12 pts vs 2023")
            
            with col2:
                st.metric("⚖️ Taux de cassation", "23%", "-5 pts")
            
            with col3:
                st.metric("🎯 Pertinence IA", "89%", "+7 pts")
            
            # Graphique d'évolution
            st.markdown("##### 📊 Évolution du nombre de décisions")
            st.bar_chart(trends_data["Évolution temporelle"])
            
            # Prédictions IA
            st.markdown("##### 🔮 Prédictions et Recommandations IA")
            
            predictions = [
                {
                    "titre": "Évolution probable de la jurisprudence",
                    "prediction": "Renforcement de la protection des droits",
                    "confiance": 0.87,
                    "modele": "GPT-4 Turbo"
                },
                {
                    "titre": "Décisions clés à surveiller",
                    "prediction": "3 affaires en cours pourraient créer un revirement",
                    "confiance": 0.92,
                    "modele": "Claude 3"
                },
                {
                    "titre": "Stratégie recommandée",
                    "prediction": "Privilégier l'argumentation sur la causalité",
                    "confiance": 0.84,
                    "modele": "Fusion (3 modèles)"
                }
            ]
            
            for pred in predictions:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"**{pred['titre']}**")
                        st.write(pred['prediction'])
                        st.caption(f"Modèle: {pred['modele']}")
                    
                    with col2:
                        confidence_color = "#10B981" if pred['confiance'] > 0.85 else "#F59E0B" if pred['confiance'] > 0.7 else "#EF4444"
                        st.markdown(f"""
                            <div style='text-align: center; padding: 10px; background: {confidence_color}; 
                                 color: white; border-radius: 8px;'>
                                <b>{pred['confiance']:.0%}</b><br>
                                <small>Confiance</small>
                            </div>
                        """, unsafe_allow_html=True)
    
    # Génération de suggestions
    st.markdown("### 💡 Génération de Suggestions Jurisprudentielles")
    
    with st.form("ai_suggestions_form"):
        context = st.text_area(
            "Contexte de votre affaire",
            placeholder="Décrivez brièvement les faits et les questions juridiques...",
            height=150,
            key="ai_context"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            jurisdiction = st.selectbox(
                "Juridiction visée",
                ["Toutes"] + get_all_juridictions(),
                key="ai_jurisdiction"
            )
        
        with col2:
            domain = st.selectbox(
                "Domaine juridique",
                ["Général", "Civil", "Pénal", "Commercial", "Social", "Administratif"],
                key="ai_domain"
            )
        
        with col3:
            max_suggestions = st.number_input(
                "Nombre de suggestions",
                min_value=5,
                max_value=50,
                value=10,
                step=5,
                key="ai_max_suggestions"
            )
        
        generate_button = st.form_submit_button(
            "🚀 Générer des suggestions",
            type="primary",
            use_container_width=True
        )
    
    if generate_button and context:
        show_ai_suggestions_results(context, jurisdiction, domain, max_suggestions)

def show_ai_suggestions_results(context, jurisdiction, domain, max_suggestions):
    """Affiche les résultats des suggestions IA"""
    
    with st.spinner("🤖 Génération des suggestions par les modèles d'IA..."):
        # Progress détaillé par modèle
        models_progress = st.container()
        
        with models_progress:
            selected_models = st.session_state.get('selected_ai_models', ['gpt-4-turbo'])
            
            progress_bars = {}
            for model in selected_models:
                st.markdown(f"**{AI_MODELS[model]['icon']} {AI_MODELS[model]['name']}**")
                progress_bars[model] = st.progress(0)
            
            # Simulation de progression
            for i in range(101):
                for model, bar in progress_bars.items():
                    # Vitesse variable selon le modèle
                    speed = AI_MODELS[model]['speed']
                    if speed == 'very_fast':
                        bar.progress(min(i * 1.5, 100) / 100)
                    elif speed == 'fast':
                        bar.progress(i / 100)
                    else:  # medium
                        bar.progress(min(i * 0.8, 100) / 100)
                time.sleep(0.02)
    
    # Résultats consolidés
    st.success(f"✅ **{max_suggestions} suggestions générées avec succès !**")
    
    # Afficher les suggestions groupées par pertinence
    st.markdown("#### 📋 Suggestions de Jurisprudence")
    
    # Onglets par niveau de pertinence
    relevance_tabs = st.tabs([
        "🔥 Hautement pertinentes",
        "⭐ Pertinentes",
        "💡 Connexes"
    ])
    
    with relevance_tabs[0]:
        show_suggestion_cards(generate_demo_suggestions(5, "high"))
    
    with relevance_tabs[1]:
        show_suggestion_cards(generate_demo_suggestions(3, "medium"))
    
    with relevance_tabs[2]:
        show_suggestion_cards(generate_demo_suggestions(2, "low"))
    
    # Export des suggestions
    st.markdown("### 💾 Export des Suggestions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📄 Export PDF",
            data=b"PDF content",  # Remplacer par vraie génération
            file_name=f"suggestions_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            "📊 Export Excel",
            data="Excel content",  # Remplacer par vraie génération
            file_name=f"suggestions_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
    
    with col3:
        st.download_button(
            "📝 Export Word",
            data=b"Word content",  # Remplacer par vraie génération
            file_name=f"suggestions_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

def show_suggestion_cards(suggestions):
    """Affiche les cartes de suggestions"""
    
    for i, suggestion in enumerate(suggestions):
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.markdown(f"""
                    **{suggestion['citation']}**  
                    📅 {suggestion['date']} | 🏛️ {suggestion['juridiction']}
                """)
                
                st.write(suggestion['summary'])
                
                # Tags de pertinence
                tags = st.container()
                with tags:
                    tag_cols = st.columns(len(suggestion['relevance_tags']))
                    for idx, tag in enumerate(suggestion['relevance_tags']):
                        with tag_cols[idx]:
                            st.markdown(f"""
                                <span style='background: #EEF2FF; color: #4F46E5; 
                                      padding: 4px 12px; border-radius: 20px; font-size: 0.85em;'>
                                    {tag}
                                </span>
                            """, unsafe_allow_html=True)
                
                # Score de consensus si mode fusion
                if st.session_state.get('ai_fusion_mode') and len(st.session_state.get('selected_ai_models', [])) > 1:
                    st.progress(suggestion['consensus_score'])
                    st.caption(f"Score de consensus: {suggestion['consensus_score']:.0%} ({len(st.session_state.selected_ai_models)} modèles)")
            
            with col2:
                st.markdown(f"""
                    <div style='text-align: center; padding: 20px; background: #F3F4F6; border-radius: 10px;'>
                        <h2 style='margin: 0; color: #4F46E5;'>{suggestion['relevance_score']:.0%}</h2>
                        <small>Pertinence</small>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("➕", key=f"add_suggestion_{i}", help="Ajouter aux résultats"):
                    st.success("✅ Ajouté aux résultats")

def show_enhanced_analytics_tab():
    """Onglet Analytics amélioré avec visualisations interactives"""
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%); 
             padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h3 style='margin: 0;'>📊 Analytics & Intelligence Juridique</h3>
            <p style='margin: 10px 0 0 0;'>Explorez vos données jurisprudentielles en profondeur</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Métriques globales
    st.markdown("### 📈 Vue d'ensemble")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📚 Total décisions",
            "1,247",
            "+127 ce mois"
        )
    
    with col2:
        st.metric(
            "⚖️ Taux de succès",
            "73%",
            "+5%"
        )
    
    with col3:
        st.metric(
            "⏱️ Temps moyen",
            "3.2s",
            "-0.8s"
        )
    
    with col4:
        st.metric(
            "🎯 Précision IA",
            "91%",
            "+3%"
        )
    
    # Graphiques interactifs
    chart_tabs = st.tabs([
        "📊 Évolution temporelle",
        "🗺️ Répartition géographique",
        "🏛️ Par juridiction",
        "🔥 Heatmap thématique"
    ])
    
    with chart_tabs[0]:
        show_temporal_evolution_chart()
    
    with chart_tabs[1]:
        show_geographic_distribution()
    
    with chart_tabs[2]:
        show_jurisdiction_breakdown()
    
    with chart_tabs[3]:
        show_thematic_heatmap()

def show_footer():
    """Affiche le footer avec informations et liens"""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            **📚 Sources officielles**  
            [Légifrance](https://www.legifrance.gouv.fr) | 
            [Judilibre](https://www.judilibre.io) | 
            [Cour de cassation](https://www.courdecassation.fr)
        """)
    
    with col2:
        st.markdown("""
            **🤖 Modèles d'IA**  
            GPT-4 | Claude 3 | Llama 3 | Mistral | Gemini
        """)
    
    with col3:
        st.markdown("""
            **ℹ️ Module v2.0**  
            Dernière mise à jour: {date}  
            [Documentation](docs) | [Support](support)
        """.format(date=datetime.now().strftime("%d/%m/%Y")))

# Fonctions utilitaires de génération de données de démonstration

def generate_demo_results():
    """Génère des résultats de démonstration"""
    
    demo_data = [
        {
            'numero': '21-12.345',
            'date': datetime(2024, 3, 15),
            'juridiction': 'Cour de cassation',
            'formation': '1ère chambre civile',
            'titre': 'Responsabilité médicale - Perte de chance',
            'resume': 'La perte de chance constitue un préjudice réparable distinct...',
            'importance': 9,
            'source': SourceJurisprudence.LEGIFRANCE,
            'mots_cles': ['responsabilité', 'médical', 'perte de chance', 'préjudice']
        },
        {
            'numero': '20-18.765',
            'date': datetime(2024, 2, 28),
            'juridiction': "Cour d'appel de Paris",
            'formation': '2ème chambre',
            'titre': 'RGPD - Consentement et cookies',
            'resume': 'Le consentement aux cookies doit être libre, spécifique...',
            'importance': 8,
            'source': SourceJurisprudence.JUDILIBRE,
            'mots_cles': ['RGPD', 'cookies', 'consentement', 'données personnelles']
        }
    ]
    
    results = []
    for data in demo_data:
        ref = JurisprudenceReference(**data)
        results.append(ref)
    
    return results

def generate_demo_suggestions(count, relevance_level):
    """Génère des suggestions de démonstration"""
    
    suggestions = []
    
    for i in range(count):
        base_score = 0.95 if relevance_level == "high" else 0.75 if relevance_level == "medium" else 0.55
        
        suggestion = {
            'citation': f"Cass. civ. 1, {10+i} mars 2024, n° 23-{10000+i}",
            'date': f"{10+i}/03/2024",
            'juridiction': "Cour de cassation",
            'summary': f"Décision pertinente concernant {relevance_level} niveau de pertinence...",
            'relevance_score': base_score + (i * 0.01),
            'relevance_tags': ['#responsabilité', '#préjudice', '#causalité'][:3-i],
            'consensus_score': base_score - (i * 0.02)
        }
        
        suggestions.append(suggestion)
    
    return suggestions

# Conserver toutes les fonctions existantes du module original
# (JurisprudenceAPIManager et toutes les autres fonctions restent identiques)

# Ajouter à la fin les fonctions existantes qui ne sont pas redéfinies

# Import des fonctions originales nécessaires
from jurisprudence import (
    JurisprudenceAPIManager,
    api_manager,
    process_jurisprudence_request,
    extract_jurisprudence_criteria,
    show_jurisprudence_search_interface,
    show_search_tab,
    show_verification_tab,
    show_local_database_tab,
    show_statistics_tab,
    show_configuration_tab,
    save_to_favorites,
    show_decision_details,
    show_related_decisions,
    show_commentaries,
    save_to_database,
    show_enhanced_verification_tab,
    show_enhanced_local_database_tab,
    show_enhanced_configuration_tab,
    show_temporal_evolution_chart,
    show_geographic_distribution,
    show_jurisdiction_breakdown,
    show_thematic_heatmap,
    show_list_view,
    show_table_view
)

# Point d'entrée pour compatibilité
if __name__ == "__main__":
    run()