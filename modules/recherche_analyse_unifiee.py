# modules/recherche_analyse_unifiee.py
"""Module unifié de recherche universelle et analyse IA avec compréhension du langage naturel"""

import asyncio
import html
import re
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from streamlit_shortcuts import add_keyboard_shortcuts

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
try:
    from utils import clean_key, format_legal_date, truncate_text
except ImportError:
    # Les utilitaires ne sont pas disponibles
    pass
from utils import clean_key, format_legal_date, truncate_text
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# ========================= LAZY LOADING & IMPORTS =========================

# Variables globales pour le lazy loading
_imports_loaded = False
_modules_cache = {}

def lazy_load_imports():
    """Charge les imports de manière lazy pour améliorer les performances"""
    global _imports_loaded
    if _imports_loaded:
        return
    
    # Progress bar pour le chargement
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Configuration et dataclasses
        status.text("⏳ Chargement des configurations...")
        progress_bar.progress(10)
        
        from config.app_config import (ANALYSIS_PROMPTS_AFFAIRES,
                                       InfractionAffaires, LLMProvider)
        _modules_cache['config'] = {
            'InfractionAffaires': InfractionAffaires,
            'ANALYSIS_PROMPTS_AFFAIRES': ANALYSIS_PROMPTS_AFFAIRES,
            'LLMProvider': LLMProvider
        }
        
        # Services de recherche
        status.text("⏳ Chargement des services de recherche...")
        progress_bar.progress(25)
        
        try:
            from managers.universal_search_service import (
                UniversalSearchService, get_universal_search_service)
            _modules_cache['search_service'] = {
                'UniversalSearchService': UniversalSearchService,
                'get_universal_search_service': get_universal_search_service,
                'available': True
            }
        except ImportError:
            _modules_cache['search_service'] = {'available': False}
        
        # Managers IA
        status.text("⏳ Chargement des managers IA...")
        progress_bar.progress(40)
        
        try:
            from managers.multi_llm_manager import MultiLLMManager
            _modules_cache['multi_llm'] = {'MultiLLMManager': MultiLLMManager, 'available': True}
        except ImportError:
            _modules_cache['multi_llm'] = {'available': False}
        
        try:
            from managers.jurisprudence_verifier import (
                JurisprudenceVerifier, display_jurisprudence_verification)
            _modules_cache['jurisprudence'] = {
                'JurisprudenceVerifier': JurisprudenceVerifier,
                'display_jurisprudence_verification': display_jurisprudence_verification,
                'available': True
            }
        except ImportError:
            _modules_cache['jurisprudence'] = {'available': False}
        
        # APIs et utils
        status.text("⏳ Chargement des APIs...")
        progress_bar.progress(60)
        
        try:
            from utils.api_utils import call_llm_api, get_available_models
            _modules_cache['api_utils'] = {
                'get_available_models': get_available_models,
                'call_llm_api': call_llm_api,
                'available': True
            }
        except ImportError:
            _modules_cache['api_utils'] = {'available': False}
        
        # Modules juridiques
        status.text("⏳ Chargement des modules juridiques...")
        progress_bar.progress(80)
        
        try:
            from modules.generation_longue import (
                GenerateurDocumentsLongs, show_generation_longue_interface)
            _modules_cache['generation_longue'] = {
                'GenerateurDocumentsLongs': GenerateurDocumentsLongs,
                'show_generation_longue_interface': show_generation_longue_interface,
                'available': True
            }
        except ImportError:
            _modules_cache['generation_longue'] = {'available': False}
        
        # Finalisation
        progress_bar.progress(100)
        status.text("✅ Modules chargés avec succès!")
        time.sleep(0.5)
        
        _imports_loaded = True
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des modules : {str(e)}")
    finally:
        progress_bar.empty()
        status.empty()

def get_module(module_name, item_name=None):
    """Récupère un module ou un élément de module de manière lazy"""
    if not _imports_loaded:
        lazy_load_imports()
    
    module = _modules_cache.get(module_name, {})
    if item_name:
        return module.get(item_name)
    return module

# ========================= FONCTION PRINCIPALE RUN =========================

def run():
    """Fonction principale du module - Point d'entrée pour le lazy loading"""
    
    # Chargement lazy des imports
    if not _imports_loaded:
        with st.spinner("🚀 Initialisation du module de recherche avancée..."):
            lazy_load_imports()
    
    # CSS personnalisé pour améliorer le design
    st.markdown("""
    <style>
    /* Animation de fade-in pour les éléments */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        font-weight: 500;
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Cards effect */
    .result-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease-out;
    }
    
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #4285f4;
    }
    
    /* Progress indicators */
    .progress-step {
        display: flex;
        align-items: center;
        padding: 12px;
        margin: 8px 0;
        background: #f0f7ff;
        border-radius: 8px;
        animation: fadeIn 0.3s ease-out;
    }
    
    .progress-step.active {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .progress-step.completed {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    
    /* Search bar enhancement */
    .search-container {
        position: relative;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* AI model selector */
    .ai-model-card {
        padding: 16px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .ai-model-card:hover {
        border-color: #4285f4;
        background: #f8f9fa;
    }
    
    .ai-model-card.selected {
        border-color: #4285f4;
        background: #e3f2fd;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header avec titre et description
    st.title("🔍 Recherche & Analyse Unifiée avec IA")
    st.markdown("""
    <div style="animation: fadeIn 0.6s ease-out;">
        <p style="font-size: 1.1em; color: #666;">
        Exploitez la puissance de l'IA pour rechercher, analyser et générer du contenu juridique.
        Écrivez naturellement ce que vous souhaitez faire.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialiser l'interface si nécessaire
    if 'unified_interface' not in st.session_state:
        st.session_state.unified_interface = UnifiedSearchAnalysisInterface()
    
    # Options de configuration rapide
    with st.expander("⚙️ Configuration rapide", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.show_nl_analysis = st.checkbox(
                "🧠 Afficher l'analyse IA",
                value=st.session_state.get('show_nl_analysis', False),
                help="Voir comment l'IA comprend votre requête"
            )
        
        with col2:
            st.session_state.auto_enhance = st.checkbox(
                "✨ Amélioration automatique",
                value=st.session_state.get('auto_enhance', True),
                help="L'IA améliore automatiquement vos requêtes"
            )
        
        with col3:
            st.session_state.multi_ai_mode = st.checkbox(
                "🤖 Mode Multi-IA",
                value=st.session_state.get('multi_ai_mode', False),
                help="Utiliser plusieurs IA simultanément"
            )
    
    # Actions rapides avec design amélioré
    st.markdown("### 🚀 Actions rapides")
    show_enhanced_quick_actions()
    
    # Interface principale en onglets
    tabs = st.tabs([
        "🔍 Recherche & Analyse",
        "📝 Génération",
        "🤖 Multi-IA",
        "📊 Résultats",
        "🔧 Avancé"
    ])
    
    with tabs[0]:  # Recherche & Analyse
        show_search_analysis_tab()
    
    with tabs[1]:  # Génération
        show_generation_tab()
    
    with tabs[2]:  # Multi-IA
        show_multi_ai_tab()
    
    with tabs[3]:  # Résultats
        show_results_tab()
    
    with tabs[4]:  # Avancé
        show_advanced_tab()
    
    # Footer avec informations
    show_enhanced_footer()

# ========================= INTERFACES PAR ONGLETS =========================

def show_search_analysis_tab():
    """Onglet de recherche et analyse"""
    
    # Interface de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Formulaire de recherche avec design amélioré
        with st.form(key='main_search_form', clear_on_submit=False):
            query = st.text_area(
                "🔍 Votre demande",
                value=st.session_state.get('universal_query', ''),
                placeholder="""Exemples :
• Analyser les risques dans l'affaire Martin
• Rechercher tous les contrats de 2024
• Préparer mon client pour l'audience de demain
• Rédiger une plainte exhaustive contre Vinci""",
                height=120,
                key="search_query_input"
            )
            
            col_form1, col_form2, col_form3 = st.columns([2, 1, 1])
            
            with col_form1:
                search_type = st.selectbox(
                    "Type de recherche",
                    ["🔍 Universelle", "📚 Juridique", "📄 Documents", "🎯 Spécifique"],
                    key="search_type_select"
                )
            
            with col_form2:
                submit = st.form_submit_button(
                    "🚀 Lancer",
                    type="primary",
                    use_container_width=True
                )
            
            with col_form3:
                clear = st.form_submit_button(
                    "🔄 Effacer",
                    use_container_width=True
                )
    
    with col2:
        # Suggestions contextuelles
        st.markdown("### 💡 Suggestions")
        if st.button("📋 Plainte", use_container_width=True):
            st.session_state.pending_query = "Rédiger une plainte contre"
            st.rerun()
        
        if st.button("📊 Analyse", use_container_width=True):
            st.session_state.pending_query = "Analyser les risques"
            st.rerun()
        
        if st.button("📝 Synthèse", use_container_width=True):
            st.session_state.pending_query = "Faire une synthèse"
            st.rerun()
    
    # Traitement de la requête
    if submit and query:
        with st.spinner("🔄 Traitement de votre demande..."):
            # Animation de progression
            progress_container = st.container()
            with progress_container:
                show_processing_animation(query)
            
            # Traitement asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                interface = st.session_state.unified_interface
                loop.run_until_complete(interface.process_universal_query(query))
            finally:
                loop.close()
    
    # Affichage des résultats en temps réel
    if st.session_state.get('search_results') or st.session_state.get('analysis_results'):
        show_enhanced_results()

def show_generation_tab():
    """Onglet de génération de documents"""
    
    st.markdown("### 📝 Génération de documents juridiques")
    
    # Sélection du type de document
    col1, col2 = st.columns([2, 1])
    
    with col1:
        doc_type = st.selectbox(
            "Type de document",
            [
                "📋 Plainte avec constitution de partie civile",
                "📑 Conclusions",
                "📄 Mémoire",
                "✉️ Courrier",
                "📜 Citation directe",
                "🔖 Requête",
                "📊 Rapport d'expertise"
            ],
            key="generation_doc_type"
        )
    
    with col2:
        complexity = st.radio(
            "Complexité",
            ["⚡ Simple", "📄 Standard", "📚 Exhaustif"],
            key="generation_complexity"
        )
    
    # Configuration de la génération
    with st.expander("⚙️ Configuration avancée", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Parties**")
            demandeurs = st.text_area(
                "Demandeurs",
                placeholder="Un par ligne",
                height=100,
                key="gen_demandeurs"
            )
            
            defendeurs = st.text_area(
                "Défendeurs",
                placeholder="Un par ligne",
                height=100,
                key="gen_defendeurs"
            )
        
        with col2:
            st.markdown("**🎯 Éléments juridiques**")
            infractions = st.text_area(
                "Infractions",
                placeholder="Une par ligne",
                height=100,
                key="gen_infractions"
            )
            
            reference = st.text_input(
                "Référence dossier",
                placeholder="Ex: MARTIN_2024",
                key="gen_reference"
            )
        
        with col3:
            st.markdown("**🤖 Modèles IA**")
            
            # Sélection des modèles avec design amélioré
            available_models = get_available_ai_models()
            selected_models = []
            
            for model in available_models:
                col_model = st.container()
                with col_model:
                    if st.checkbox(
                        f"{model['icon']} {model['name']}",
                        value=model['default'],
                        key=f"model_{model['id']}"
                    ):
                        selected_models.append(model['id'])
            
            fusion_mode = st.radio(
                "Mode de fusion",
                ["🧬 Synthèse IA", "📑 Concaténation", "🏆 Meilleur résultat"],
                key="gen_fusion_mode"
            )
    
    # Options supplémentaires
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_jurisprudence = st.checkbox(
            "📚 Inclure jurisprudences",
            value=True,
            key="gen_include_juris"
        )
    
    with col2:
        include_chronologie = st.checkbox(
            "📅 Chronologie détaillée",
            value=True,
            key="gen_include_chrono"
        )
    
    with col3:
        enrich_parties = st.checkbox(
            "🏢 Enrichir les sociétés",
            value=True,
            key="gen_enrich_parties"
        )
    
    # Bouton de génération avec style
    if st.button(
        "🚀 Générer le document",
        type="primary",
        use_container_width=True,
        key="generate_document_btn"
    ):
        if selected_models:
            generate_with_multi_ai(
                doc_type=doc_type,
                complexity=complexity,
                models=selected_models,
                config={
                    'demandeurs': demandeurs.split('\n') if demandeurs else [],
                    'defendeurs': defendeurs.split('\n') if defendeurs else [],
                    'infractions': infractions.split('\n') if infractions else [],
                    'reference': reference,
                    'include_jurisprudence': include_jurisprudence,
                    'include_chronologie': include_chronologie,
                    'enrich_parties': enrich_parties,
                    'fusion_mode': fusion_mode
                }
            )
        else:
            st.error("❌ Veuillez sélectionner au moins un modèle IA")

def show_multi_ai_tab():
    """Onglet de comparaison multi-IA"""
    
    st.markdown("### 🤖 Comparaison Multi-IA")
    
    # Interface de prompt
    prompt = st.text_area(
        "📝 Votre prompt",
        placeholder="Entrez votre demande pour comparer les réponses de différentes IA",
        height=150,
        key="multi_ai_prompt"
    )
    
    # Sélection des modèles avec cards visuelles
    st.markdown("#### 🤖 Sélectionnez les modèles à comparer")
    
    models = get_available_ai_models()
    selected_models = []
    
    cols = st.columns(3)
    for idx, model in enumerate(models):
        with cols[idx % 3]:
            # Card pour chaque modèle
            with st.container():
                st.markdown(f"""
                <div class="ai-model-card" id="model_{model['id']}">
                    <h4>{model['icon']} {model['name']}</h4>
                    <p style="color: #666; font-size: 0.9em;">{model['description']}</p>
                    <p style="color: #888; font-size: 0.8em;">
                        Vitesse: {model['speed']} | Qualité: {model['quality']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.checkbox(
                    "Utiliser",
                    key=f"multi_select_{model['id']}",
                    label_visibility="collapsed"
                ):
                    selected_models.append(model)
    
    # Options de comparaison
    with st.expander("⚙️ Options de comparaison", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            comparison_mode = st.selectbox(
                "Mode de comparaison",
                ["⚡ Parallèle", "🔄 Séquentiel", "🏆 Tournoi", "🧬 Consensus"],
                help="""
                • Parallèle : Tous en même temps
                • Séquentiel : Un par un avec amélioration
                • Tournoi : Élimination progressive
                • Consensus : Trouve le meilleur compromis
                """
            )
        
        with col2:
            metrics = st.multiselect(
                "Métriques d'évaluation",
                ["📊 Qualité", "🎯 Pertinence", "💡 Créativité", 
                 "📏 Cohérence", "⚡ Rapidité", "📚 Exhaustivité"],
                default=["📊 Qualité", "🎯 Pertinence"]
            )
        
        with col3:
            temperature = st.slider(
                "🌡️ Température",
                0.0, 1.0, 0.3, 0.1,
                help="Plus bas = Plus factuel | Plus haut = Plus créatif"
            )
    
    # Lancement de la comparaison
    if st.button(
        "🚀 Lancer la comparaison",
        type="primary",
        use_container_width=True,
        disabled=not (prompt and selected_models)
    ):
        run_multi_ai_comparison(
            prompt=prompt,
            models=selected_models,
            mode=comparison_mode,
            metrics=metrics,
            temperature=temperature
        )

def show_results_tab():
    """Onglet des résultats"""
    
    # Vérifier s'il y a des résultats
    has_results = any([
        st.session_state.get('search_results'),
        st.session_state.get('analysis_results'),
        st.session_state.get('generated_content'),
        st.session_state.get('multi_ai_results')
    ])
    
    if not has_results:
        st.info("📊 Aucun résultat disponible. Lancez d'abord une recherche, analyse ou génération.")
        return
    
    # Navigation entre les différents types de résultats
    result_types = []
    if st.session_state.get('search_results'):
        result_types.append("🔍 Recherche")
    if st.session_state.get('analysis_results'):
        result_types.append("📊 Analyse")
    if st.session_state.get('generated_content'):
        result_types.append("📝 Génération")
    if st.session_state.get('multi_ai_results'):
        result_types.append("🤖 Multi-IA")
    
    selected_result = st.radio(
        "Type de résultat",
        result_types,
        horizontal=True,
        key="result_type_selector"
    )
    
    # Affichage selon le type sélectionné
    if "🔍 Recherche" in selected_result:
        show_search_results_enhanced()
    elif "📊 Analyse" in selected_result:
        show_analysis_results_enhanced()
    elif "📝 Génération" in selected_result:
        show_generation_results_enhanced()
    elif "🤖 Multi-IA" in selected_result:
        show_multi_ai_results_enhanced()
    
    # Actions globales sur les résultats
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Tout sauvegarder", use_container_width=True):
            save_all_results()
    
    with col2:
        if st.button("📤 Exporter", use_container_width=True):
            export_results_dialog()
    
    with col3:
        if st.button("🔗 Partager", use_container_width=True):
            share_results_dialog()
    
    with col4:
        if st.button("🗑️ Effacer tout", use_container_width=True):
            if st.button("⚠️ Confirmer", key="confirm_clear"):
                clear_all_results()
                st.rerun()

def show_advanced_tab():
    """Onglet des fonctionnalités avancées"""
    
    st.markdown("### 🔧 Fonctionnalités avancées")
    
    # Sous-onglets pour les différentes fonctionnalités
    sub_tabs = st.tabs([
        "📊 Statistiques",
        "🔍 Recherche avancée",
        "🧬 Fusion IA",
        "📈 Analytics",
        "⚙️ Configuration"
    ])
    
    with sub_tabs[0]:  # Statistiques
        show_work_statistics_enhanced()
    
    with sub_tabs[1]:  # Recherche avancée
        show_advanced_search_interface()
    
    with sub_tabs[2]:  # Fusion IA
        show_ai_fusion_interface()
    
    with sub_tabs[3]:  # Analytics
        show_analytics_dashboard()
    
    with sub_tabs[4]:  # Configuration
        show_configuration_interface()

# ========================= FONCTIONS D'INTERFACE AMÉLIORÉES =========================

def show_enhanced_quick_actions():
    """Actions rapides avec design amélioré"""
    
    # Container avec animation
    with st.container():
        st.markdown("""
        <div style="animation: fadeIn 0.8s ease-out;">
        """, unsafe_allow_html=True)
        
        cols = st.columns(6)
        
        actions = [
            ("📝 Rédaction", "Créer un document", "primary"),
            ("🤖 Analyse IA", "Analyser avec l'IA", "secondary"),
            ("🔍 Recherche", "Rechercher", "secondary"),
            ("📊 Synthèse", "Synthétiser", "secondary"),
            ("📋 Bordereau", "Créer bordereau", "secondary"),
            ("⚖️ Juridique", "Actes juridiques", "primary")
        ]
        
        for idx, (icon_text, help_text, button_type) in enumerate(actions):
            with cols[idx]:
                if button_type == "primary":
                    if st.button(
                        icon_text,
                        help=help_text,
                        use_container_width=True,
                        type="primary",
                        key=f"quick_action_{idx}"
                    ):
                        handle_quick_action(icon_text)
                else:
                    if st.button(
                        icon_text,
                        help=help_text,
                        use_container_width=True,
                        key=f"quick_action_{idx}"
                    ):
                        handle_quick_action(icon_text)
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_processing_animation(query: str):
    """Animation de traitement avec étapes visuelles"""
    
    steps = [
        ("🧠 Analyse de votre demande", 20),
        ("🔍 Recherche dans la base", 40),
        ("🤖 Traitement par l'IA", 60),
        ("📊 Préparation des résultats", 80),
        ("✅ Finalisation", 100)
    ]
    
    progress = st.progress(0)
    status_container = st.empty()
    
    for step_text, progress_value in steps:
        status_container.markdown(f"""
        <div class="progress-step {'active' if progress_value < 100 else 'completed'}">
            <span style="font-size: 1.2em; margin-right: 10px;">
                {'⏳' if progress_value < 100 else '✅'}
            </span>
            <span>{step_text}</span>
        </div>
        """, unsafe_allow_html=True)
        
        progress.progress(progress_value / 100)
        time.sleep(0.5)
    
    # Nettoyer après l'animation
    progress.empty()
    status_container.empty()

def show_enhanced_results():
    """Affichage amélioré des résultats avec animations"""
    
    results = st.session_state.get('search_results', [])
    
    if not results:
        return
    
    st.markdown("### 📊 Résultats")
    
    # Métriques de résultats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Documents trouvés",
            len(results),
            delta=f"+{len(results)}" if len(results) > 0 else None
        )
    
    with col2:
        avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
        st.metric(
            "Pertinence moyenne",
            f"{avg_score:.0%}"
        )
    
    with col3:
        categories = set(r.get('category', 'Autre') for r in results)
        st.metric(
            "Catégories",
            len(categories)
        )
    
    with col4:
        recent = sum(1 for r in results if is_recent_document(r))
        st.metric(
            "Documents récents",
            recent
        )
    
    # Filtres dynamiques
    with st.expander("🔍 Filtres", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            category_filter = st.multiselect(
                "Catégories",
                list(categories),
                key="filter_categories"
            )
        
        with col2:
            score_filter = st.slider(
                "Pertinence minimale",
                0, 100, 0,
                format="%d%%",
                key="filter_score"
            )
        
        with col3:
            sort_by = st.selectbox(
                "Trier par",
                ["Pertinence", "Date", "Titre", "Catégorie"],
                key="sort_results_by"
            )
    
    # Affichage des résultats avec cards
    filtered_results = filter_results(results, category_filter, score_filter)
    sorted_results = sort_results(filtered_results, sort_by)
    
    for idx, result in enumerate(sorted_results[:20]):
        display_result_card(result, idx)

def display_result_card(result: dict, index: int):
    """Affiche un résultat sous forme de card interactive"""
    
    with st.container():
        st.markdown(f"""
        <div class="result-card" style="animation-delay: {index * 0.1}s;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            st.markdown(f"**{result.get('title', 'Sans titre')}**")
            
            # Tags et métadonnées
            tags_html = ""
            if result.get('category'):
                tags_html += f'<span class="tag">{result["category"]}</span> '
            if result.get('date'):
                tags_html += f'<span class="tag">📅 {format_legal_date(result["date"])}</span> '
            if result.get('score'):
                score_class = "high" if result['score'] > 0.8 else "medium" if result['score'] > 0.5 else "low"
                tags_html += f'<span class="tag score-{score_class}">🎯 {result["score"]:.0%}</span>'
            
            st.markdown(tags_html, unsafe_allow_html=True)
            
            # Extrait avec highlights
            if result.get('highlights'):
                for highlight in result['highlights'][:2]:
                    st.markdown(f"📌 *...{highlight}...*")
            else:
                st.text(truncate_text(result.get('content', ''), 200))
        
        with col2:
            if st.button("👁️ Voir", key=f"view_{index}", use_container_width=True):
                show_document_detail(result)
        
        with col3:
            if st.button("📥 Utiliser", key=f"use_{index}", use_container_width=True):
                use_document_in_context(result)
        
        st.markdown("</div>", unsafe_allow_html=True)

def get_available_ai_models():
    """Récupère les modèles IA disponibles avec leurs métadonnées"""
    
    # Configuration des modèles avec icônes et métadonnées
    models_config = [
        {
            'id': 'claude-3-opus',
            'name': 'Claude 3 Opus',
            'icon': '🎭',
            'description': 'Le plus puissant pour les tâches complexes',
            'speed': '⚡⚡',
            'quality': '⭐⭐⭐⭐⭐',
            'default': True
        },
        {
            'id': 'claude-3-sonnet',
            'name': 'Claude 3 Sonnet',
            'icon': '🎵',
            'description': 'Équilibre parfait entre vitesse et qualité',
            'speed': '⚡⚡⚡',
            'quality': '⭐⭐⭐⭐',
            'default': True
        },
        {
            'id': 'gpt-4-turbo',
            'name': 'GPT-4 Turbo',
            'icon': '🚀',
            'description': 'Excellent pour la créativité et l\'analyse',
            'speed': '⚡⚡',
            'quality': '⭐⭐⭐⭐⭐',
            'default': False
        },
        {
            'id': 'gpt-3.5-turbo',
            'name': 'GPT-3.5 Turbo',
            'icon': '⚡',
            'description': 'Rapide et efficace pour les tâches simples',
            'speed': '⚡⚡⚡⚡',
            'quality': '⭐⭐⭐',
            'default': False
        },
        {
            'id': 'mistral-large',
            'name': 'Mistral Large',
            'icon': '🌪️',
            'description': 'Spécialisé dans le raisonnement juridique',
            'speed': '⚡⚡⚡',
            'quality': '⭐⭐⭐⭐',
            'default': False
        }
    ]
    
    # Filtrer selon les modèles réellement disponibles
    if _modules_cache.get('api_utils', {}).get('available'):
        available = _modules_cache['api_utils']['get_available_models']()
        models_config = [m for m in models_config if m['id'] in available]
    
    return models_config

def generate_with_multi_ai(doc_type, complexity, models, config):
    """Génère un document avec plusieurs IA"""
    
    with st.spinner("🚀 Génération en cours avec plusieurs IA..."):
        # Container pour les résultats
        results_container = st.container()
        
        # Progress tracking
        progress = st.progress(0)
        status = st.empty()
        
        results = {}
        
        for idx, model_id in enumerate(models):
            status.text(f"🤖 Génération avec {model_id}...")
            progress.progress((idx + 1) / len(models))
            
            # Simuler la génération (remplacer par l'appel réel)
            time.sleep(1)
            
            # Stocker le résultat
            results[model_id] = f"Contenu généré par {model_id}"
        
        # Fusion des résultats selon le mode
        status.text("🧬 Fusion des résultats...")
        
        if config['fusion_mode'] == "🧬 Synthèse IA":
            final_result = ai_synthesis_fusion(results)
        elif config['fusion_mode'] == "🏆 Meilleur résultat":
            final_result = select_best_result(results)
        else:
            final_result = concatenate_results(results)
        
        # Afficher le résultat final
        progress.empty()
        status.empty()
        
        with results_container:
            st.success("✅ Génération terminée!")
            
            # Afficher le document généré
            st.text_area(
                "📄 Document généré",
                value=final_result,
                height=400,
                key="generated_document_display"
            )
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    "💾 Télécharger",
                    final_result,
                    file_name=f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            with col2:
                if st.button("📊 Voir détails"):
                    show_generation_details(results, config)
            
            with col3:
                if st.button("🔄 Regénérer"):
                    st.rerun()

def run_multi_ai_comparison(prompt, models, mode, metrics, temperature):
    """Lance une comparaison multi-IA"""
    
    results_container = st.container()
    
    with st.spinner("🤖 Comparaison en cours..."):
        # Animation de progression
        progress = st.progress(0)
        
        # Container pour les résultats en temps réel
        live_results = {}
        
        # Colonnes pour afficher les résultats en parallèle
        cols = st.columns(len(models))
        
        for idx, model in enumerate(models):
            with cols[idx]:
                st.markdown(f"### {model['icon']} {model['name']}")
                
                # Placeholder pour le résultat
                result_placeholder = st.empty()
                
                # Simuler la génération
                with result_placeholder.container():
                    st.info("⏳ En cours...")
                
                # Attendre un peu (remplacer par l'appel API réel)
                time.sleep(1 + idx * 0.5)
                
                # Afficher le résultat
                with result_placeholder.container():
                    result_text = f"Réponse de {model['name']} pour: {prompt[:50]}..."
                    st.success("✅ Terminé")
                    st.text_area(
                        "Résultat",
                        value=result_text,
                        height=200,
                        key=f"result_{model['id']}"
                    )
                
                # Métriques
                if metrics:
                    st.markdown("**Scores:**")
                    for metric in metrics:
                        score = 0.7 + (idx * 0.05)  # Simulation
                        st.progress(score)
                        st.caption(f"{metric}: {score:.0%}")
                
                live_results[model['id']] = {
                    'content': result_text,
                    'scores': {m: 0.7 + (idx * 0.05) for m in metrics}
                }
            
            progress.progress((idx + 1) / len(models))
        
        # Analyse comparative
        st.markdown("---")
        st.markdown("### 📊 Analyse comparative")
        
        # Graphique de comparaison
        if metrics:
            comparison_data = []
            for model_id, result in live_results.items():
                for metric, score in result['scores'].items():
                    comparison_data.append({
                        'Modèle': model_id,
                        'Métrique': metric,
                        'Score': score
                    })
            
            df = pd.DataFrame(comparison_data)
            
            # Pivot pour affichage
            pivot_df = df.pivot(index='Modèle', columns='Métrique', values='Score')
            st.dataframe(pivot_df.style.format("{:.0%}"), use_container_width=True)
        
        # Recommandation
        best_model = max(live_results.items(), 
                        key=lambda x: sum(x[1]['scores'].values()))[0]
        
        st.success(f"🏆 Meilleur modèle selon les critères : **{best_model}**")
        
        # Actions finales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder la comparaison"):
                save_comparison_results(live_results, prompt, metrics)
        
        with col2:
            if st.button("📤 Exporter les résultats"):
                export_comparison_results(live_results)
        
        with col3:
            if st.button("🔄 Nouvelle comparaison"):
                st.rerun()

def show_enhanced_footer():
    """Footer avec informations et liens utiles"""
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**🚀 Performance**")
        if 'unified_interface' in st.session_state:
            interface = st.session_state.unified_interface
            st.caption(f"Cache: {len(getattr(interface, 'cache', {}))} entrées")
            st.caption(f"Requêtes: {st.session_state.get('query_count', 0)}")
    
    with col2:
        st.markdown("**📊 Statistiques**")
        docs_count = len(st.session_state.get('azure_documents', {}))
        st.caption(f"Documents: {docs_count}")
        st.caption(f"Analyses: {st.session_state.get('analysis_count', 0)}")
    
    with col3:
        st.markdown("**🔧 Modules actifs**")
        active_modules = sum(1 for v in _modules_cache.values() if v.get('available'))
        st.caption(f"Modules: {active_modules}/{len(_modules_cache)}")
        if st.button("Voir détails", key="show_modules_footer"):
            show_modules_status_dialog()
    
    with col4:
        st.markdown("**ℹ️ Aide**")
        if st.button("📖 Guide", key="show_guide"):
            show_user_guide()
        if st.button("💬 Support", key="show_support"):
            st.info("Support: support@nexora-law.ai")

# ========================= FONCTIONS UTILITAIRES =========================

def handle_quick_action(action: str):
    """Gère les actions rapides"""
    
    action_map = {
        "📝 Rédaction": "rédiger ",
        "🤖 Analyse IA": "analyser ",
        "🔍 Recherche": "rechercher ",
        "📊 Synthèse": "synthétiser ",
        "📋 Bordereau": "créer bordereau ",
        "⚖️ Juridique": "plainte "
    }
    
    if action in action_map:
        st.session_state.pending_query = action_map[action]
        st.session_state.active_tab = 0  # Retour à l'onglet recherche
        st.rerun()

def is_recent_document(doc: dict) -> bool:
    """Vérifie si un document est récent"""
    if not doc.get('date'):
        return False
    
    try:
        doc_date = datetime.fromisoformat(str(doc['date']))
        days_old = (datetime.now() - doc_date).days
        return days_old < 30
    except:
        return False

def filter_results(results: list, categories: list, min_score: int) -> list:
    """Filtre les résultats selon les critères"""
    filtered = results
    
    if categories:
        filtered = [r for r in filtered if r.get('category') in categories]
    
    if min_score > 0:
        filtered = [r for r in filtered if r.get('score', 0) * 100 >= min_score]
    
    return filtered

def sort_results(results: list, sort_by: str) -> list:
    """Trie les résultats selon le critère"""
    if sort_by == "Pertinence":
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    elif sort_by == "Date":
        return sorted(results, key=lambda x: x.get('date', ''), reverse=True)
    elif sort_by == "Titre":
        return sorted(results, key=lambda x: x.get('title', ''))
    elif sort_by == "Catégorie":
        return sorted(results, key=lambda x: x.get('category', ''))
    return results

def ai_synthesis_fusion(results: dict) -> str:
    """Fusionne les résultats avec une synthèse IA"""
    # Simulation - remplacer par l'appel réel à l'IA
    synthesis = "SYNTHÈSE DES GÉNÉRATIONS MULTI-IA\n\n"
    synthesis += "Les différents modèles ont généré des contenus complémentaires:\n\n"
    
    for model, content in results.items():
        synthesis += f"- {model}: Points clés extraits\n"
    
    synthesis += "\nSYNTHÈSE FINALE:\n"
    synthesis += "Contenu fusionné et optimisé par l'IA..."
    
    return synthesis

def select_best_result(results: dict) -> str:
    """Sélectionne le meilleur résultat selon des critères"""
    # Simulation - implémenter la logique réelle
    best_model = list(results.keys())[0]
    return f"MEILLEUR RÉSULTAT (sélectionné: {best_model}):\n\n{results[best_model]}"

def concatenate_results(results: dict) -> str:
    """Concatène simplement les résultats"""
    concatenated = "RÉSULTATS CONCATÉNÉS:\n\n"
    
    for model, content in results.items():
        concatenated += f"=== {model} ===\n{content}\n\n"
    
    return concatenated

def save_comparison_results(results: dict, prompt: str, metrics: list):
    """Sauvegarde les résultats de comparaison"""
    st.success("✅ Comparaison sauvegardée!")
    
    # Implémenter la logique de sauvegarde
    st.session_state.saved_comparisons = st.session_state.get('saved_comparisons', [])
    st.session_state.saved_comparisons.append({
        'timestamp': datetime.now(),
        'prompt': prompt,
        'results': results,
        'metrics': metrics
    })

def export_comparison_results(results: dict):
    """Exporte les résultats de comparaison"""
    # Créer un rapport
    report = "RAPPORT DE COMPARAISON MULTI-IA\n"
    report += f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    for model, data in results.items():
        report += f"=== {model} ===\n"
        report += f"Contenu: {data['content'][:200]}...\n"
        report += "Scores:\n"
        for metric, score in data['scores'].items():
            report += f"  - {metric}: {score:.0%}\n"
        report += "\n"
    
    st.download_button(
        "💾 Télécharger le rapport",
        report,
        file_name=f"comparaison_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

def show_modules_status_dialog():
    """Affiche le statut détaillé des modules"""
    with st.expander("🔧 État détaillé des modules", expanded=True):
        for module_name, module_data in _modules_cache.items():
            if module_data.get('available'):
                st.success(f"✅ {module_name}")
            else:
                st.error(f"❌ {module_name}")

def show_user_guide():
    """Affiche le guide utilisateur"""
    with st.expander("📖 Guide d'utilisation", expanded=True):
        st.markdown("""
        ### 🚀 Démarrage rapide
        
        1. **Recherche naturelle** : Écrivez ce que vous voulez faire
        2. **Actions rapides** : Utilisez les boutons pour des actions courantes
        3. **Multi-IA** : Comparez les réponses de plusieurs IA
        4. **Génération** : Créez des documents juridiques complets
        
        ### 💡 Conseils
        
        - Utilisez @ pour référencer un dossier (ex: @Martin)
        - Activez le mode Multi-IA pour des résultats optimaux
        - Les documents longs utilisent automatiquement le module approprié
        
        ### 🎯 Exemples de requêtes
        
        - "Analyser les risques dans l'affaire Martin"
        - "Rédiger une plainte exhaustive contre Vinci"
        - "Préparer mon client pour l'audience de demain"
        - "Synthétiser tous les échanges avec l'avocat adverse"
        """)

# ========================= CLASSES ET INTERFACES PRINCIPALES =========================

class UnifiedSearchAnalysisInterface:
    """Interface unifiée pour la recherche et l'analyse avec IA"""
    
    def __init__(self):
        """Initialisation avec chargement lazy des composants"""
        self.search_service = None
        self.nl_analyzer = None
        self.llm_manager = None
        self.jurisprudence_verifier = None
        self.cache = {}
        
        # Initialiser les composants de manière lazy
        self._init_components_lazy()
    
    def _init_components_lazy(self):
        """Initialise les composants uniquement quand nécessaire"""
        # Les composants seront chargés à la demande
        pass
    
    def get_search_service(self):
        """Récupère le service de recherche (lazy loading)"""
        if not self.search_service:
            search_module = get_module('search_service')
            if search_module.get('available'):
                self.search_service = search_module['get_universal_search_service']()
        return self.search_service
    
    def get_nl_analyzer(self):
        """Récupère l'analyseur de langage naturel (lazy loading)"""
        if not self.nl_analyzer:
            self.nl_analyzer = NaturalLanguageAnalyzer()
        return self.nl_analyzer
    
    async def process_universal_query(self, query: str):
        """Traite une requête universelle avec IA"""
        
        # Incrémenter le compteur
        st.session_state.query_count = st.session_state.get('query_count', 0) + 1
        
        # Sauvegarder la requête
        st.session_state.last_universal_query = query
        
        # Analyse en langage naturel
        nl_analyzer = self.get_nl_analyzer()
        nl_analysis = await nl_analyzer.analyze_natural_query(query)
        st.session_state.nl_analysis = nl_analysis
        
        # Afficher l'analyse si demandé
        if st.session_state.get('show_nl_analysis', False):
            with st.expander("🧠 Analyse IA de votre requête", expanded=True):
                st.json(nl_analysis)
        
        # Routage intelligent selon l'intention
        await self.route_by_intention(query, nl_analysis)
    
    async def route_by_intention(self, query: str, nl_analysis: dict):
        """Route la requête selon l'intention détectée"""
        
        intention = nl_analysis.get('intention', 'search')
        
        # Map des intentions vers les handlers
        intention_handlers = {
            'analyze': self._process_analysis_request,
            'create': self._process_create_request,
            'prepare': self._process_preparation_request,
            'synthesize': self._process_synthesis_request,
            'search': self._process_search_request
        }
        
        handler = intention_handlers.get(intention, self._process_search_request)
        await handler(query, nl_analysis)
    
    async def _process_analysis_request(self, query: str, nl_analysis: dict):
        """Traite une demande d'analyse"""
        st.session_state.analysis_context = nl_analysis
        st.session_state.analysis_count = st.session_state.get('analysis_count', 0) + 1
        
        # Rediriger vers l'interface d'analyse
        await self.show_analyse_ia_interface(nl_analysis)
    
    async def _process_create_request(self, query: str, nl_analysis: dict):
        """Traite une demande de création de document"""
        
        # Vérifier la complexité du document
        if nl_analysis.get('document_complexite') in ['exhaustif', 'long']:
            # Documents longs
            if get_module('generation_longue', 'available'):
                st.info("📜 Redirection vers le module de génération longue...")
                st.session_state.show_generation_longue = True
                st.session_state.juridique_context = nl_analysis
                st.rerun()
                return
        
        # Documents standards
        st.session_state.generation_context = nl_analysis
        await self.generate_standard_document(nl_analysis)
    
    async def _process_preparation_request(self, query: str, nl_analysis: dict):
        """Traite une demande de préparation"""
        st.info("📋 Module de préparation client")
        # Implémenter la logique de préparation
    
    async def _process_synthesis_request(self, query: str, nl_analysis: dict):
        """Traite une demande de synthèse"""
        st.info("📑 Génération de synthèse")
        # Implémenter la logique de synthèse
    
    async def _process_search_request(self, query: str, nl_analysis: dict):
        """Traite une demande de recherche"""
        
        # Enrichir la requête
        enhanced_query = self._enhance_query_from_nl(query, nl_analysis)
        
        # Effectuer la recherche
        search_service = self.get_search_service()
        if search_service:
            results = await search_service.search(enhanced_query)
            st.session_state.search_results = results.documents if hasattr(results, 'documents') else results
            
            if results:
                st.success(f"✅ {len(st.session_state.search_results)} résultats trouvés")
            else:
                st.warning("⚠️ Aucun résultat trouvé")
        else:
            st.error("❌ Service de recherche non disponible")
    
    def _enhance_query_from_nl(self, query: str, nl_analysis: dict) -> str:
        """Enrichit la requête avec l'analyse NL"""
        
        enhanced = nl_analysis.get('requete_reformulee', query)
        
        # Ajouter la référence si présente
        if nl_analysis.get('reference_dossier') and '@' not in enhanced:
            enhanced = f"@{nl_analysis['reference_dossier']} {enhanced}"
        
        # Ajouter les mots-clés importants
        if nl_analysis.get('mots_cles_importants'):
            for mot in nl_analysis['mots_cles_importants']:
                if mot.lower() not in enhanced.lower():
                    enhanced += f" {mot}"
        
        return enhanced
    
    async def show_analyse_ia_interface(self, nl_analysis: dict):
        """Interface d'analyse IA"""
        
        st.header("🤖 Analyse IA des documents")
        
        # Configuration de l'analyse dans un container élégant
        with st.container():
            st.markdown("""
            <div class="result-card">
            """, unsafe_allow_html=True)
            
            # Configuration en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                infraction = st.text_input(
                    "🎯 Type d'infraction",
                    value=nl_analysis.get('elements_juridiques', [''])[0] if nl_analysis.get('elements_juridiques') else '',
                    placeholder="Ex: Abus de biens sociaux"
                )
                
                client_nom = st.text_input(
                    "👤 Nom du client",
                    value=nl_analysis.get('reference_dossier', ''),
                    placeholder="Personne physique ou morale"
                )
            
            with col2:
                # Sélection des modèles IA
                models = get_available_ai_models()
                selected_models = st.multiselect(
                    "🤖 Modèles IA",
                    [m['name'] for m in models],
                    default=[models[0]['name']] if models else []
                )
                
                fusion_mode = st.radio(
                    "🧬 Mode de fusion",
                    ["Synthèse IA", "Meilleur résultat", "Consensus"],
                    horizontal=True
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Sélection des analyses
        st.markdown("### 🎯 Types d'analyses")
        
        analysis_types = list(get_module('config', 'ANALYSIS_PROMPTS_AFFAIRES').keys())
        selected_analyses = st.multiselect(
            "Sélectionnez les analyses",
            analysis_types,
            default=analysis_types[:2] if len(analysis_types) >= 2 else analysis_types
        )
        
        # Bouton d'analyse avec style
        if st.button("🚀 Lancer l'analyse IA", type="primary", use_container_width=True):
            if infraction and client_nom and selected_models and selected_analyses:
                await self.run_ai_analysis(
                    infraction=infraction,
                    client_nom=client_nom,
                    models=selected_models,
                    analyses=selected_analyses,
                    fusion_mode=fusion_mode
                )
            else:
                st.error("❌ Veuillez remplir tous les champs")
    
    async def run_ai_analysis(self, infraction: str, client_nom: str, 
                             models: list, analyses: list, fusion_mode: str):
        """Lance l'analyse IA avec les paramètres"""
        
        with st.spinner("🤖 Analyse IA en cours..."):
            # Simulation - remplacer par les appels réels
            results = {}
            
            progress = st.progress(0)
            for idx, analysis_type in enumerate(analyses):
                results[analysis_type] = f"Résultat de l'analyse {analysis_type}"
                progress.progress((idx + 1) / len(analyses))
            
            # Stocker les résultats
            st.session_state.analysis_results = results
            
            # Afficher les résultats
            st.success("✅ Analyse terminée!")
            
            for analysis_type, result in results.items():
                with st.expander(analysis_type, expanded=True):
                    st.markdown(result)
    
    async def generate_standard_document(self, nl_analysis: dict):
        """Génère un document standard"""
        
        doc_type = nl_analysis.get('type_document', 'document')
        
        st.info(f"📝 Génération d'un {doc_type} en cours...")
        
        # Simulation de génération
        with st.spinner("Génération..."):
            time.sleep(2)
            
            content = f"""DOCUMENT GÉNÉRÉ
Type: {doc_type}
Date: {datetime.now().strftime('%d/%m/%Y')}
Référence: {nl_analysis.get('reference_dossier', 'REF')}

[Contenu du document généré par l'IA]
"""
            
            st.session_state.generated_content = content
            
            # Afficher le résultat
            st.text_area(
                "Document généré",
                value=content,
                height=400
            )

class NaturalLanguageAnalyzer:
    """Analyseur de langage naturel pour comprendre les requêtes"""
    
    def __init__(self):
        self.llm_manager = None
        self._init_llm_lazy()
    
    def _init_llm_lazy(self):
        """Initialise le LLM de manière lazy"""
        # Le LLM sera chargé uniquement si nécessaire
        pass
    
    async def analyze_natural_query(self, query: str) -> dict:
        """Analyse une requête en langage naturel"""
        
        # Pour la démo, utiliser une analyse basique
        # Remplacer par l'appel réel à l'IA
        return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> dict:
        """Analyse de fallback basée sur des règles"""
        
        query_lower = query.lower()
        
        # Détection de l'intention
        intention = "search"
        if any(word in query_lower for word in ['analyser', 'analyse']):
            intention = "analyze"
        elif any(word in query_lower for word in ['rédiger', 'créer', 'générer']):
            intention = "create"
        elif any(word in query_lower for word in ['préparer', 'préparation']):
            intention = "prepare"
        elif any(word in query_lower for word in ['synthèse', 'synthétiser']):
            intention = "synthesize"
        
        # Détection du type de document
        type_document = None
        if 'plainte' in query_lower:
            type_document = 'plainte'
        elif 'conclusions' in query_lower:
            type_document = 'conclusions'
        elif 'mémoire' in query_lower:
            type_document = 'mémoire'
        
        # Détection de la complexité
        document_complexite = "standard"
        if any(word in query_lower for word in ['exhaustif', 'complet', 'long']):
            document_complexite = "exhaustif"
        
        # Extraction de la référence
        reference = None
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            reference = ref_match.group(1)
        
        return {
            "intention": intention,
            "action_principale": f"{intention} detected",
            "reference_dossier": reference,
            "type_document": type_document,
            "document_complexite": document_complexite,
            "longueur_estimee": "longue" if document_complexite == "exhaustif" else "moyenne",
            "parties": {"demandeurs": [], "defendeurs": []},
            "contexte": "normal",
            "elements_juridiques": [],
            "contraintes_temporelles": None,
            "mots_cles_importants": query.split()[:5],
            "indicateurs_complexite": [],
            "requete_reformulee": query
        }

# ========================= FONCTIONS HELPER =========================

def clear_all_results():
    """Efface tous les résultats"""
    keys_to_clear = [
        'search_results', 'analysis_results', 'generated_content',
        'multi_ai_results', 'synthesis_result', 'nl_analysis'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def save_all_results():
    """Sauvegarde tous les résultats"""
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'search_results': st.session_state.get('search_results'),
        'analysis_results': st.session_state.get('analysis_results'),
        'generated_content': st.session_state.get('generated_content'),
        'multi_ai_results': st.session_state.get('multi_ai_results')
    }
    
    # Créer un fichier JSON
    import json
    json_str = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    
    st.download_button(
        "💾 Télécharger tous les résultats",
        json_str,
        file_name=f"resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def export_results_dialog():
    """Dialog d'export des résultats"""
    with st.expander("📤 Options d'export", expanded=True):
        format_export = st.selectbox(
            "Format",
            ["JSON", "PDF", "Word", "Excel"]
        )
        
        if st.button("Exporter", type="primary"):
            st.success(f"✅ Export en {format_export} en cours...")

def share_results_dialog():
    """Dialog de partage des résultats"""
    with st.expander("🔗 Partager les résultats", expanded=True):
        share_link = f"https://nexora-law.ai/share/{datetime.now().timestamp()}"
        st.code(share_link)
        
        if st.button("📋 Copier le lien"):
            st.success("✅ Lien copié!")

def show_document_detail(document: dict):
    """Affiche le détail d'un document"""
    with st.expander(f"📄 {document.get('title', 'Document')}", expanded=True):
        st.markdown(f"**Catégorie:** {document.get('category', 'Non catégorisé')}")
        st.markdown(f"**Date:** {format_legal_date(document.get('date', ''))}")
        st.markdown("---")
        st.text(document.get('content', 'Contenu non disponible'))

def use_document_in_context(document: dict):
    """Utilise un document dans le contexte actuel"""
    st.session_state.selected_document = document
    st.success(f"✅ Document '{document.get('title', 'Sans titre')}' sélectionné")

def show_search_results_enhanced():
    """Affiche les résultats de recherche améliorés"""
    results = st.session_state.get('search_results', [])
    
    if not results:
        st.info("Aucun résultat de recherche")
        return
    
    st.markdown(f"### 🔍 {len(results)} résultats trouvés")
    
    for idx, result in enumerate(results[:10]):
        display_result_card(result, idx)

def show_analysis_results_enhanced():
    """Affiche les résultats d'analyse améliorés"""
    results = st.session_state.get('analysis_results', {})
    
    if not results:
        st.info("Aucun résultat d'analyse")
        return
    
    for analysis_type, content in results.items():
        with st.expander(analysis_type, expanded=True):
            st.markdown(content)

def show_generation_results_enhanced():
    """Affiche les résultats de génération améliorés"""
    content = st.session_state.get('generated_content', '')
    
    if not content:
        st.info("Aucun contenu généré")
        return
    
    st.text_area(
        "Document généré",
        value=content,
        height=400
    )

def show_multi_ai_results_enhanced():
    """Affiche les résultats multi-IA améliorés"""
    results = st.session_state.get('multi_ai_results', {})
    
    if not results:
        st.info("Aucun résultat multi-IA")
        return
    
    for model, data in results.items():
        with st.expander(f"🤖 {model}", expanded=True):
            st.markdown(data.get('content', ''))

def show_work_statistics_enhanced():
    """Affiche les statistiques de travail améliorées"""
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📄 Documents",
            len(st.session_state.get('azure_documents', {}))
        )
    
    with col2:
        st.metric(
            "🔍 Recherches",
            st.session_state.get('query_count', 0)
        )
    
    with col3:
        st.metric(
            "📊 Analyses",
            st.session_state.get('analysis_count', 0)
        )
    
    with col4:
        st.metric(
            "📝 Générations",
            st.session_state.get('generation_count', 0)
        )
    
    # Graphiques
    st.markdown("### 📈 Évolution de l'activité")
    st.info("Graphiques d'activité à implémenter")

def show_advanced_search_interface():
    """Interface de recherche avancée"""
    
    st.markdown("### 🔍 Recherche avancée")
    
    # Constructeur de requête
    col1, col2 = st.columns(2)
    
    with col1:
        search_field = st.selectbox(
            "Champ",
            ["Tous", "Titre", "Contenu", "Métadonnées"]
        )
        
        operator = st.selectbox(
            "Opérateur",
            ["Contient", "Égal à", "Commence par", "Finit par"]
        )
    
    with col2:
        search_value = st.text_input(
            "Valeur",
            placeholder="Terme de recherche"
        )
        
        add_condition = st.button("➕ Ajouter condition")
    
    # Affichage des conditions
    if 'search_conditions' not in st.session_state:
        st.session_state.search_conditions = []
    
    if add_condition and search_value:
        st.session_state.search_conditions.append({
            'field': search_field,
            'operator': operator,
            'value': search_value
        })
    
    if st.session_state.search_conditions:
        st.markdown("**Conditions de recherche:**")
        for idx, condition in enumerate(st.session_state.search_conditions):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"{condition['field']} {condition['operator']} '{condition['value']}'")
            with col2:
                if st.button("❌", key=f"remove_cond_{idx}"):
                    st.session_state.search_conditions.pop(idx)
                    st.rerun()

def show_ai_fusion_interface():
    """Interface de fusion des résultats IA"""
    
    st.markdown("### 🧬 Fusion des résultats IA")
    
    st.info("Interface de fusion avancée à implémenter")

def show_analytics_dashboard():
    """Tableau de bord analytique"""
    
    st.markdown("### 📈 Analytics")
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Efficacité moyenne",
            "87%",
            "+5%"
        )
    
    with col2:
        st.metric(
            "Temps moyen",
            "2.3s",
            "-0.5s"
        )
    
    with col3:
        st.metric(
            "Satisfaction",
            "4.8/5",
            "+0.2"
        )

def show_configuration_interface():
    """Interface de configuration"""
    
    st.markdown("### ⚙️ Configuration")
    
    # Paramètres généraux
    with st.expander("Paramètres généraux", expanded=True):
        st.slider("Limite de résultats", 10, 100, 20)
        st.slider("Timeout API (secondes)", 5, 60, 30)
        st.checkbox("Mode debug", value=False)
    
    # Paramètres IA
    with st.expander("Paramètres IA", expanded=True):
        st.slider("Température par défaut", 0.0, 1.0, 0.3)
        st.number_input("Tokens maximum", 100, 8000, 2000)

def show_generation_details(results: dict, config: dict):
    """Affiche les détails de génération"""
    
    with st.expander("📊 Détails de génération", expanded=True):
        # Afficher les résultats par modèle
        for model, content in results.items():
            st.markdown(f"**{model}**")
            st.text_area(
                "Contenu",
                value=content[:500] + "...",
                height=200,
                key=f"detail_{model}"
            )
        
        # Configuration utilisée
        st.markdown("**Configuration:**")
        st.json(config)

# ========================= EXPORT ET COMPATIBILITÉ =========================

# Fonction pour compatibilité avec l'ancien système
def show_page():
    """Fonction de compatibilité pour l'ancien système"""
    run()

# Point d'entrée principal
if __name__ == "__main__":
    run()