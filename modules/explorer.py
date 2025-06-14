"""Module explorateur de fichiers et documents avec IA intégrée"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Configuration pour imports
sys.path.append(str(Path(__file__).parent.parent))

from managers.azure_blob_manager import AzureBlobManager
from models.dataclasses import Document
from utils.text_processing import calculate_read_time
from utils.file_utils import get_file_icon, sanitize_filename
try:
    from utils import clean_key, format_file_size, format_legal_date, truncate_text
except Exception:  # pragma: no cover - fallback for standalone use
    from utils.fallback import clean_key, format_legal_date, truncate_text
    from utils import format_file_size
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# Configuration de l'explorateur
EXPLORER_CONFIG = {
    'files_per_page': 20,
    'preview_chars': 500,
    'supported_extensions': ['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.json', '.xml'],
    'image_extensions': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    'max_file_size_mb': 100,
    'ai_models': {
        'gpt-4': {'name': 'GPT-4', 'icon': '🧠', 'provider': 'OpenAI'},
        'claude-3': {'name': 'Claude 3', 'icon': '🤖', 'provider': 'Anthropic'},
        'gemini-pro': {'name': 'Gemini Pro', 'icon': '✨', 'provider': 'Google'},
        'llama-2': {'name': 'Llama 2', 'icon': '🦙', 'provider': 'Meta'},
        'mistral': {'name': 'Mistral', 'icon': '🌊', 'provider': 'Mistral AI'}
    }
}

def run():
    """Fonction principale du module explorateur - Point d'entrée pour lazy loading"""
    
    # Titre avec animation
    st.markdown("""
        <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .explorer-title {
            animation: fadeIn 0.5s ease-out;
        }
        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .stats-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .doc-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            margin: 10px 0;
            transition: all 0.3s ease;
        }
        .doc-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="explorer-title">📁 Explorateur Intelligent de Documents</h1>', unsafe_allow_html=True)
    st.markdown("Explorez, analysez et gérez vos documents avec l'aide de l'IA")
    
    # Initialisation de l'état du module
    init_explorer_state()
    
    # Métriques rapides en haut
    show_quick_stats()
    
    # Interface principale avec onglets
    main_tabs = st.tabs([
        "🔍 Explorer", 
        "🤖 Analyse IA", 
        "📊 Visualisations", 
        "🔗 Sources", 
        "⚙️ Configuration"
    ])
    
    with main_tabs[0]:  # Explorer
        show_enhanced_explorer()
    
    with main_tabs[1]:  # Analyse IA
        show_ai_analysis_interface()
    
    with main_tabs[2]:  # Visualisations
        show_advanced_visualizations()
    
    with main_tabs[3]:  # Sources
        show_sources_management()
    
    with main_tabs[4]:  # Configuration
        show_explorer_configuration()

def init_explorer_state():
    """Initialise l'état du module explorateur"""
    if 'explorer_state' not in st.session_state:
        st.session_state.explorer_state = {
            'initialized': True,
            'current_view': 'list',
            'selected_docs': [],
            'ai_analysis_queue': [],
            'active_filters': {},
            'search_history': [],
            'favorite_docs': [],
            'recent_docs': [],
            'ai_models_config': {
                'selected_models': ['gpt-4'],
                'fusion_mode': False,
                'analysis_depth': 'standard'
            }
        }
    
    # Charger les documents en lazy loading
    if 'documents_loaded' not in st.session_state:
        with st.spinner("Chargement des documents..."):
            load_documents_lazy()

def load_documents_lazy():
    """Charge les documents de manière asynchrone"""
    # Simuler le chargement lazy
    if 'azure_documents' not in st.session_state:
        st.session_state.azure_documents = {}
    
    st.session_state.documents_loaded = True

def show_quick_stats():
    """Affiche les statistiques rapides en haut"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_docs = len(st.session_state.get('azure_documents', {}))
    recent_docs = sum(1 for doc in st.session_state.get('azure_documents', {}).values() 
                     if (datetime.now() - doc.created_at).days < 7)
    
    with col1:
        st.markdown(f"""
            <div class="stats-card">
                <h3>{total_docs}</h3>
                <p>Documents totaux</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="stats-card">
                <h3>{recent_docs}</h3>
                <p>Récents (7j)</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        sources_count = len(get_available_sources())
        st.markdown(f"""
            <div class="stats-card">
                <h3>{sources_count}</h3>
                <p>Sources actives</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        ai_queue = len(st.session_state.explorer_state.get('ai_analysis_queue', []))
        st.markdown(f"""
            <div class="stats-card">
                <h3>{ai_queue}</h3>
                <p>En analyse IA</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        favorites = len(st.session_state.explorer_state.get('favorite_docs', []))
        st.markdown(f"""
            <div class="stats-card">
                <h3>{favorites}</h3>
                <p>Favoris</p>
            </div>
        """, unsafe_allow_html=True)

def show_enhanced_explorer():
    """Interface explorer améliorée avec filtres avancés"""
    
    # Barre de recherche intelligente avec suggestions
    search_col, filter_col, action_col = st.columns([3, 1, 1])
    
    with search_col:
        search_query = st.text_input(
            "🔍 Recherche intelligente",
            placeholder="Titre, contenu, tags, auteur... (IA activée)",
            key="smart_search",
            help="Utilisez @ pour rechercher par ID, # pour les tags, ~ pour la recherche sémantique"
        )
        
        # Suggestions de recherche
        if search_query:
            show_search_suggestions(search_query)
    
    with filter_col:
        # Filtres rapides
        quick_filter = st.selectbox(
            "Filtre rapide",
            ["Tous", "📅 Cette semaine", "⭐ Favoris", "🏷️ Avec tags", "🤖 Analysés", "📎 Non classés"],
            key="quick_filter"
        )
    
    with action_col:
        # Actions globales
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄", help="Actualiser", key="refresh_main"):
                st.rerun()
        with col2:
            if st.button("⚡", help="Mode turbo", key="turbo_mode"):
                st.session_state.turbo_mode = not st.session_state.get('turbo_mode', False)
    
    # Filtres avancés dans un expander
    with st.expander("🎛️ Filtres avancés", expanded=False):
        show_advanced_filters()
    
    # Sélection de la vue
    view_cols = st.columns(6)
    views = [
        ("📋 Liste", "list"),
        ("📊 Grille", "grid"),
        ("🗂️ Kanban", "kanban"),
        ("📈 Timeline", "timeline"),
        ("🌳 Arbre", "tree"),
        ("🧠 Mind Map", "mindmap")
    ]
    
    for i, (label, view_type) in enumerate(views):
        with view_cols[i]:
            if st.button(label, key=f"view_{view_type}", 
                        type="primary" if st.session_state.explorer_state['current_view'] == view_type else "secondary",
                        use_container_width=True):
                st.session_state.explorer_state['current_view'] = view_type
                st.rerun()
    
    # Affichage selon la vue sélectionnée
    documents = get_filtered_documents(search_query, quick_filter)
    
    if st.session_state.explorer_state['current_view'] == 'list':
        show_enhanced_list_view(documents)
    elif st.session_state.explorer_state['current_view'] == 'grid':
        show_enhanced_grid_view(documents)
    elif st.session_state.explorer_state['current_view'] == 'kanban':
        show_kanban_view(documents)
    elif st.session_state.explorer_state['current_view'] == 'timeline':
        show_timeline_view(documents)
    elif st.session_state.explorer_state['current_view'] == 'tree':
        show_tree_view(documents)
    elif st.session_state.explorer_state['current_view'] == 'mindmap':
        show_mindmap_view(documents)

def show_search_suggestions(query: str):
    """Affiche des suggestions de recherche basées sur l'historique et l'IA"""
    suggestions = []
    
    # Suggestions basées sur l'historique
    history = st.session_state.explorer_state.get('search_history', [])
    for hist in history[-5:]:
        if query.lower() in hist.lower():
            suggestions.append(f"📜 {hist}")
    
    # Suggestions basées sur les tags
    all_tags = set()
    for doc in st.session_state.get('azure_documents', {}).values():
        all_tags.update(doc.tags)
    
    for tag in all_tags:
        if query.lower() in tag.lower():
            suggestions.append(f"🏷️ #{tag}")
    
    # Afficher les suggestions
    if suggestions:
        st.caption("💡 Suggestions :")
        cols = st.columns(min(len(suggestions), 3))
        for i, suggestion in enumerate(suggestions[:3]):
            with cols[i]:
                if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                    st.session_state.smart_search = suggestion.split(' ', 1)[1]
                    st.rerun()

def show_advanced_filters():
    """Affiche les filtres avancés"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtre par date
        date_filter = st.date_input(
            "📅 Période",
            value=(datetime.now().date(), datetime.now().date()),
            key="date_filter"
        )
        
        # Filtre par taille
        size_range = st.slider(
            "📏 Taille (KB)",
            0, 10000, (0, 10000),
            key="size_filter"
        )
    
    with col2:
        # Filtre par type
        doc_types = ["Tous"] + get_document_types(st.session_state.get('azure_documents', {}))
        selected_types = st.multiselect(
            "📄 Types de documents",
            doc_types,
            default=["Tous"],
            key="type_filter"
        )
        
        # Filtre par source
        sources = ["Toutes"] + get_available_sources()
        selected_sources = st.multiselect(
            "📂 Sources",
            sources,
            default=["Toutes"],
            key="source_filter"
        )
    
    with col3:
        # Filtre par statut d'analyse
        analysis_status = st.selectbox(
            "🤖 Statut IA",
            ["Tous", "Analysés", "Non analysés", "En cours"],
            key="analysis_filter"
        )
        
        # Filtre par tags
        all_tags = set()
        for doc in st.session_state.get('azure_documents', {}).values():
            all_tags.update(doc.tags)
        
        selected_tags = st.multiselect(
            "🏷️ Tags",
            sorted(all_tags),
            key="tags_filter"
        )

def show_enhanced_list_view(documents: Dict[str, Document]):
    """Vue liste améliorée avec animations et interactions"""
    
    # Options d'affichage
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        compact_mode = st.checkbox("Mode compact", key="compact_mode")
    
    with col2:
        show_preview = st.checkbox("Aperçus", value=True, key="show_preview")
    
    with col3:
        show_ai_insights = st.checkbox("Insights IA", key="show_ai_insights")
    
    # Tri des documents
    sort_options = {
        "Date ↓": lambda x: x[1].created_at,
        "Date ↑": lambda x: x[1].created_at,
        "Titre A-Z": lambda x: x[1].title.lower(),
        "Titre Z-A": lambda x: x[1].title.lower(),
        "Taille ↓": lambda x: len(x[1].content),
        "Taille ↑": lambda x: len(x[1].content),
        "Pertinence IA": lambda x: x[1].metadata.get('ai_relevance_score', 0)
    }
    
    sort_by = st.selectbox("Trier par", list(sort_options.keys()), key="sort_by")
    
    # Trier les documents
    sorted_docs = sorted(
        documents.items(),
        key=sort_options[sort_by],
        reverse="↓" in sort_by or "Z-A" in sort_by or "IA" in sort_by
    )
    
    # Pagination améliorée
    items_per_page = 10 if not compact_mode else 20
    total_pages = (len(sorted_docs) - 1) // items_per_page + 1 if sorted_docs else 1
    
    # Navigation paginée
    if total_pages > 1:
        page = st.slider(
            "Page",
            1, total_pages,
            st.session_state.get('explorer_page', 1),
            key="page_slider"
        )
        st.session_state.explorer_page = page
    else:
        page = 1
    
    # Documents de la page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_docs = sorted_docs[start_idx:end_idx]
    
    # Affichage des documents
    for doc_id, doc in page_docs:
        show_enhanced_document_item(doc_id, doc, compact_mode, show_preview, show_ai_insights)

def show_enhanced_document_item(doc_id: str, doc: Document, compact: bool, preview: bool, ai_insights: bool):
    """Affiche un document avec interface améliorée"""
    
    is_favorite = doc_id in st.session_state.explorer_state.get('favorite_docs', [])
    is_selected = doc_id in st.session_state.explorer_state.get('selected_docs', [])
    
    # Container principal avec style
    container_class = "doc-card"
    if is_selected:
        container_class += " selected"
    
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    if compact:
        # Mode compact
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1, 1, 1])
        
        with col1:
            # Checkbox de sélection
            if st.checkbox("", key=f"select_{doc_id}", value=is_selected):
                toggle_document_selection(doc_id)
        
        with col2:
            # Titre et métadonnées
            icon = get_file_icon(doc.title)
            st.markdown(f"**{icon} {doc.title}**")
            
            meta_parts = []
            if doc.source:
                meta_parts.append(f"📂 {doc.source}")
            meta_parts.append(f"📅 {doc.created_at.strftime('%d/%m/%Y')}")
            meta_parts.append(f"📏 {format_file_size(len(doc.content))}")
            
            st.caption(" • ".join(meta_parts))
        
        with col3:
            # Tags
            if doc.tags:
                st.caption(f"🏷️ {len(doc.tags)} tags")
        
        with col4:
            # Statut IA
            if doc.metadata.get('ai_analyzed'):
                st.success("🤖 IA ✓")
            else:
                st.info("🤖 -")
        
        with col5:
            # Actions rapides
            action_cols = st.columns(4)
            
            with action_cols[0]:
                if st.button("⭐" if not is_favorite else "★", 
                           key=f"fav_{doc_id}",
                           help="Favori"):
                    toggle_favorite(doc_id)
            
            with action_cols[1]:
                if st.button("👁️", key=f"view_{doc_id}", help="Voir"):
                    show_document_modal(doc_id, doc)
            
            with action_cols[2]:
                if st.button("🤖", key=f"ai_{doc_id}", help="Analyser"):
                    add_to_ai_queue(doc_id, doc)
            
            with action_cols[3]:
                if st.button("⋮", key=f"more_{doc_id}", help="Plus"):
                    show_document_menu(doc_id, doc)
    
    else:
        # Mode détaillé
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # En-tête
            header_cols = st.columns([0.5, 4, 1])
            
            with header_cols[0]:
                if st.checkbox("", key=f"select_detail_{doc_id}", value=is_selected):
                    toggle_document_selection(doc_id)
            
            with header_cols[1]:
                icon = get_file_icon(doc.title)
                st.markdown(f"### {icon} {doc.title}")
            
            with header_cols[2]:
                if st.button("⭐" if not is_favorite else "★", 
                           key=f"fav_detail_{doc_id}"):
                    toggle_favorite(doc_id)
            
            # Métadonnées détaillées
            meta_cols = st.columns(4)
            
            with meta_cols[0]:
                st.metric("Source", doc.source or "Non spécifié")
            
            with meta_cols[1]:
                st.metric("Taille", format_file_size(len(doc.content)))
            
            with meta_cols[2]:
                st.metric("Mots", f"{len(doc.content.split()):,}")
            
            with meta_cols[3]:
                read_time = calculate_read_time(doc.content)
                st.metric("Lecture", f"{read_time} min")
            
            # Tags
            if doc.tags:
                st.write("🏷️ **Tags:** " + ", ".join([f"`{tag}`" for tag in doc.tags]))
            
            # Aperçu si activé
            if preview and doc.content:
                with st.expander("📄 Aperçu du contenu", expanded=False):
                    preview_text = doc.content[:500]
                    if len(doc.content) > 500:
                        preview_text += "..."
                    st.text(preview_text)
            
            # Insights IA si activés
            if ai_insights and doc.metadata.get('ai_summary'):
                with st.expander("🧠 Insights IA", expanded=False):
                    st.write(doc.metadata['ai_summary'])
                    
                    if doc.metadata.get('ai_keywords'):
                        st.write("**Mots-clés:** " + ", ".join(doc.metadata['ai_keywords']))
                    
                    if doc.metadata.get('ai_sentiment'):
                        sentiment = doc.metadata['ai_sentiment']
                        sentiment_color = {
                            'positive': 'green',
                            'neutral': 'gray',
                            'negative': 'red'
                        }.get(sentiment, 'gray')
                        st.markdown(f"**Sentiment:** <span style='color: {sentiment_color}'>{sentiment}</span>", 
                                  unsafe_allow_html=True)
        
        with col2:
            # Actions
            st.markdown("### Actions")
            
            if st.button("👁️ Voir", key=f"view_detail_{doc_id}", use_container_width=True):
                show_document_modal(doc_id, doc)
            
            if st.button("📝 Éditer", key=f"edit_detail_{doc_id}", use_container_width=True):
                edit_document_modal(doc_id, doc)
            
            if st.button("🤖 Analyser IA", key=f"ai_detail_{doc_id}", use_container_width=True):
                add_to_ai_queue(doc_id, doc)
            
            if st.button("📊 Statistiques", key=f"stats_detail_{doc_id}", use_container_width=True):
                show_document_stats(doc_id, doc)
            
            if st.button("🔗 Relations", key=f"rel_detail_{doc_id}", use_container_width=True):
                show_document_relations(doc_id, doc)
            
            if st.button("💾 Exporter", key=f"export_detail_{doc_id}", use_container_width=True):
                export_single_document(doc_id, doc)
            
            if st.button("🗑️ Supprimer", key=f"delete_detail_{doc_id}", use_container_width=True):
                if confirm_delete_document(doc_id):
                    delete_document(doc_id)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Séparateur avec style
    st.markdown("<hr style='margin: 10px 0; opacity: 0.3;'>", unsafe_allow_html=True)

def show_ai_analysis_interface():
    """Interface d'analyse IA avancée"""
    
    st.markdown("### 🤖 Centre d'Analyse IA")
    
    # Configuration des modèles
    with st.expander("⚙️ Configuration des modèles IA", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Sélection des modèles
            selected_models = st.multiselect(
                "Modèles IA à utiliser",
                list(EXPLORER_CONFIG['ai_models'].keys()),
                default=st.session_state.explorer_state['ai_models_config']['selected_models'],
                format_func=lambda x: f"{EXPLORER_CONFIG['ai_models'][x]['icon']} {EXPLORER_CONFIG['ai_models'][x]['name']}",
                key="ai_models_select"
            )
            st.session_state.explorer_state['ai_models_config']['selected_models'] = selected_models
        
        with col2:
            # Mode fusion
            fusion_mode = st.checkbox(
                "🔀 Mode Fusion",
                value=st.session_state.explorer_state['ai_models_config']['fusion_mode'],
                help="Combine les résultats de plusieurs modèles pour une analyse enrichie"
            )
            st.session_state.explorer_state['ai_models_config']['fusion_mode'] = fusion_mode
        
        with col3:
            # Profondeur d'analyse
            depth = st.select_slider(
                "Profondeur d'analyse",
                ["Rapide", "Standard", "Approfondie", "Expert"],
                value=st.session_state.explorer_state['ai_models_config']['analysis_depth']
            )
            st.session_state.explorer_state['ai_models_config']['analysis_depth'] = depth
    
    # File d'attente d'analyse
    queue = st.session_state.explorer_state.get('ai_analysis_queue', [])
    
    if queue:
        st.markdown("### 📋 File d'attente d'analyse")
        
        # Afficher la file
        for i, (doc_id, doc) in enumerate(queue):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"{i+1}. {doc.title}")
            
            with col2:
                st.caption(format_file_size(len(doc.content)))
            
            with col3:
                if st.button("❌", key=f"remove_queue_{doc_id}"):
                    remove_from_ai_queue(doc_id)
        
        # Bouton de lancement
        if st.button("🚀 Lancer l'analyse IA", type="primary", use_container_width=True):
            run_ai_analysis()
    else:
        st.info("📭 Aucun document en attente d'analyse. Sélectionnez des documents depuis l'explorateur.")
    
    # Résultats d'analyse
    if st.session_state.get('ai_analysis_results'):
        st.markdown("### 📊 Résultats d'analyse")
        show_ai_analysis_results()

def run_ai_analysis():
    """Lance l'analyse IA sur les documents en file"""
    queue = st.session_state.explorer_state.get('ai_analysis_queue', [])
    
    if not queue:
        return
    
    # Barre de progression
    progress = st.progress(0)
    status = st.empty()
    results_container = st.container()
    
    selected_models = st.session_state.explorer_state['ai_models_config']['selected_models']
    fusion_mode = st.session_state.explorer_state['ai_models_config']['fusion_mode']
    
    results = {}
    
    for i, (doc_id, doc) in enumerate(queue):
        status.text(f"⏳ Analyse de {doc.title}...")
        
        # Simuler l'analyse par chaque modèle
        doc_results = {}
        
        for model_id in selected_models:
            model_info = EXPLORER_CONFIG['ai_models'][model_id]
            status.text(f"🔄 Analyse avec {model_info['name']}...")
            
            # Simulation d'analyse (remplacer par vraie API)
            time.sleep(0.5)
            
            doc_results[model_id] = {
                'summary': f"Résumé généré par {model_info['name']}: {doc.title[:50]}...",
                'keywords': ['mot-clé1', 'mot-clé2', 'mot-clé3'],
                'sentiment': 'positive',
                'category': 'Document juridique',
                'relevance_score': 0.85,
                'insights': [
                    "Point important 1",
                    "Point important 2",
                    "Point important 3"
                ]
            }
        
        # Fusion des résultats si activée
        if fusion_mode and len(selected_models) > 1:
            doc_results['fusion'] = merge_ai_results(doc_results)
        
        results[doc_id] = doc_results
        
        # Mettre à jour les métadonnées du document
        if doc_id in st.session_state.azure_documents:
            st.session_state.azure_documents[doc_id].metadata['ai_analyzed'] = True
            st.session_state.azure_documents[doc_id].metadata['ai_results'] = doc_results
        
        progress.progress((i + 1) / len(queue))
    
    # Stocker les résultats
    st.session_state.ai_analysis_results = results
    
    # Vider la file
    st.session_state.explorer_state['ai_analysis_queue'] = []
    
    status.text("✅ Analyse terminée !")
    time.sleep(1)
    status.empty()
    progress.empty()
    
    # Afficher les résultats
    with results_container:
        show_ai_analysis_results()

def merge_ai_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Fusionne les résultats de plusieurs modèles IA"""
    # Logique de fusion simple (à améliorer avec de vraies techniques)
    merged = {
        'summary': "Synthèse fusionnée des analyses...",
        'keywords': [],
        'sentiment': 'neutral',
        'insights': [],
        'confidence': 0.0
    }
    
    # Collecter tous les mots-clés uniques
    all_keywords = set()
    for model_results in results.values():
        all_keywords.update(model_results.get('keywords', []))
    merged['keywords'] = list(all_keywords)[:5]
    
    # Calculer le sentiment moyen
    sentiments = [r.get('sentiment') for r in results.values()]
    if sentiments:
        # Logique simple de vote majoritaire
        merged['sentiment'] = max(set(sentiments), key=sentiments.count)
    
    # Fusionner les insights
    for model_results in results.values():
        merged['insights'].extend(model_results.get('insights', []))
    
    # Score de confiance basé sur la convergence
    merged['confidence'] = 0.85  # Placeholder
    
    return merged

def show_ai_analysis_results():
    """Affiche les résultats d'analyse IA"""
    results = st.session_state.get('ai_analysis_results', {})
    
    for doc_id, doc_results in results.items():
        doc = st.session_state.azure_documents.get(doc_id)
        if not doc:
            continue
        
        with st.expander(f"📄 {doc.title}", expanded=True):
            # Afficher les résultats par modèle
            tabs = []
            for model_id in doc_results:
                if model_id == 'fusion':
                    tabs.append("🔀 Fusion")
                else:
                    model_info = EXPLORER_CONFIG['ai_models'].get(model_id, {})
                    tabs.append(f"{model_info.get('icon', '')} {model_info.get('name', model_id)}")
            
            result_tabs = st.tabs(tabs)
            
            for i, (model_id, results) in enumerate(doc_results.items()):
                with result_tabs[i]:
                    # Résumé
                    st.markdown("**📝 Résumé:**")
                    st.write(results.get('summary', 'Non disponible'))
                    
                    # Métriques
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        sentiment = results.get('sentiment', 'neutral')
                        sentiment_emoji = {
                            'positive': '😊',
                            'neutral': '😐',
                            'negative': '😟'
                        }.get(sentiment, '😐')
                        st.metric("Sentiment", f"{sentiment_emoji} {sentiment.capitalize()}")
                    
                    with col2:
                        score = results.get('relevance_score', 0)
                        st.metric("Pertinence", f"{score:.0%}")
                    
                    with col3:
                        category = results.get('category', 'Non catégorisé')
                        st.metric("Catégorie", category)
                    
                    # Mots-clés
                    if results.get('keywords'):
                        st.markdown("**🏷️ Mots-clés:**")
                        keywords_html = " ".join([f"<span style='background-color: #e1e4e8; padding: 2px 8px; border-radius: 12px; margin: 2px;'>{kw}</span>" for kw in results['keywords']])
                        st.markdown(keywords_html, unsafe_allow_html=True)
                    
                    # Insights
                    if results.get('insights'):
                        st.markdown("**💡 Points clés:**")
                        for insight in results['insights']:
                            st.write(f"• {insight}")
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("💾 Sauvegarder", key=f"save_ai_{doc_id}_{model_id}"):
                            save_ai_results(doc_id, model_id, results)
                    
                    with col2:
                        if st.button("📊 Visualiser", key=f"viz_ai_{doc_id}_{model_id}"):
                            visualize_ai_results(doc_id, results)
                    
                    with col3:
                        if st.button("🔄 Réanalyser", key=f"rerun_ai_{doc_id}_{model_id}"):
                            add_to_ai_queue(doc_id, doc)

def show_advanced_visualizations():
    """Affiche des visualisations avancées des documents"""
    
    st.markdown("### 📊 Centre de Visualisation")
    
    viz_tabs = st.tabs([
        "📈 Statistiques globales",
        "🕐 Timeline",
        "🌐 Réseau de documents",
        "☁️ Nuage de mots",
        "🎯 Heatmap d'activité"
    ])
    
    documents = st.session_state.get('azure_documents', {})
    
    with viz_tabs[0]:  # Statistiques globales
        show_global_statistics(documents)
    
    with viz_tabs[1]:  # Timeline
        show_document_timeline(documents)
    
    with viz_tabs[2]:  # Réseau
        show_document_network(documents)
    
    with viz_tabs[3]:  # Nuage de mots
        show_word_cloud(documents)
    
    with viz_tabs[4]:  # Heatmap
        show_activity_heatmap(documents)

def show_global_statistics(documents: Dict[str, Document]):
    """Affiche des statistiques globales sur les documents"""
    
    if not documents:
        st.info("Aucun document à analyser")
        return
    
    # Préparer les données
    df_data = []
    for doc_id, doc in documents.items():
        df_data.append({
            'Titre': doc.title,
            'Taille': len(doc.content),
            'Mots': len(doc.content.split()),
            'Date': doc.created_at,
            'Source': doc.source or 'Non spécifié',
            'Type': get_document_type(doc),
            'Tags': len(doc.tags),
            'Analysé': doc.metadata.get('ai_analyzed', False)
        })
    
    df = pd.DataFrame(df_data)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Total documents", len(documents))
        st.metric("📏 Taille moyenne", format_file_size(int(df['Taille'].mean())))
    
    with col2:
        st.metric("📝 Total mots", f"{df['Mots'].sum():,}")
        st.metric("📊 Mots/document", f"{int(df['Mots'].mean()):,}")
    
    with col3:
        analyzed = df['Analysé'].sum()
        st.metric("🤖 Analysés par IA", f"{analyzed}/{len(documents)}")
        st.metric("🏷️ Avec tags", df[df['Tags'] > 0].shape[0])
    
    with col4:
        types_count = df['Type'].nunique()
        st.metric("📁 Types différents", types_count)
        sources_count = df['Source'].nunique()
        st.metric("📂 Sources", sources_count)
    
    # Graphiques
    import plotly.express as px
    import plotly.graph_objects as go

    # Répartition par type
    fig1 = px.pie(
        df.groupby('Type').size().reset_index(name='count'),
        values='count',
        names='Type',
        title="Répartition par type de document"
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Distribution des tailles
    fig2 = px.histogram(
        df,
        x='Taille',
        nbins=30,
        title="Distribution des tailles de documents",
        labels={'Taille': 'Taille (octets)', 'count': 'Nombre de documents'}
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Top 10 des plus gros documents
    top_docs = df.nlargest(10, 'Taille')[['Titre', 'Taille', 'Mots']]
    st.markdown("### 📊 Top 10 des documents les plus volumineux")
    st.dataframe(top_docs, use_container_width=True)

def show_kanban_view(documents: Dict[str, Document]):
    """Affiche une vue Kanban des documents"""
    
    # Colonnes Kanban par statut
    statuses = ["📥 Non traités", "🔄 En cours", "✅ Traités", "⭐ Favoris"]
    
    cols = st.columns(len(statuses))
    
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"### {status}")
            
            # Filtrer les documents pour cette colonne
            if status == "⭐ Favoris":
                filtered_docs = [(doc_id, doc) for doc_id, doc in documents.items() 
                               if doc_id in st.session_state.explorer_state.get('favorite_docs', [])]
            elif status == "✅ Traités":
                filtered_docs = [(doc_id, doc) for doc_id, doc in documents.items() 
                               if doc.metadata.get('ai_analyzed', False)]
            elif status == "🔄 En cours":
                queue_ids = [doc_id for doc_id, _ in st.session_state.explorer_state.get('ai_analysis_queue', [])]
                filtered_docs = [(doc_id, doc) for doc_id, doc in documents.items() 
                               if doc_id in queue_ids]
            else:  # Non traités
                filtered_docs = [(doc_id, doc) for doc_id, doc in documents.items() 
                               if not doc.metadata.get('ai_analyzed', False) 
                               and doc_id not in [qid for qid, _ in st.session_state.explorer_state.get('ai_analysis_queue', [])]]
            
            # Afficher les cartes
            for doc_id, doc in filtered_docs[:5]:  # Limiter à 5 par colonne
                with st.container():
                    st.markdown(f"""
                        <div style='background: white; padding: 10px; border-radius: 5px; 
                                   margin-bottom: 10px; border-left: 3px solid #667eea;'>
                            <strong>{get_file_icon(doc.title)} {truncate_text(doc.title, 25)}</strong><br>
                            <small>{format_file_size(len(doc.content))} • {doc.created_at.strftime('%d/%m')}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Actions rapides
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("👁️", key=f"kb_view_{doc_id}"):
                            show_document_modal(doc_id, doc)
                    with col2:
                        if st.button("🤖", key=f"kb_ai_{doc_id}"):
                            add_to_ai_queue(doc_id, doc)
                    with col3:
                        if st.button("→", key=f"kb_move_{doc_id}"):
                            # Logique de déplacement
                            pass
            
            if len(filtered_docs) > 5:
                st.caption(f"... et {len(filtered_docs) - 5} autres")

def show_sources_management():
    """Gestion des sources de documents"""
    
    st.markdown("### 🔗 Gestion des Sources")
    
    # Sources actuelles
    sources = get_available_sources()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_source = st.selectbox(
            "Source active",
            sources,
            key="source_management_select"
        )
    
    with col2:
        if st.button("➕ Nouvelle source", use_container_width=True):
            st.session_state.show_add_source = True
    
    # Détails de la source sélectionnée
    if selected_source == "Azure Blob Storage":
        show_azure_source_details()
    elif selected_source == "Documents locaux":
        show_local_source_details()
    elif selected_source == "Google Drive":
        show_google_drive_details()
    elif selected_source == "OneDrive":
        show_onedrive_details()
    
    # Ajouter une nouvelle source
    if st.session_state.get('show_add_source'):
        with st.expander("➕ Ajouter une nouvelle source", expanded=True):
            source_type = st.selectbox(
                "Type de source",
                ["Azure Blob Storage", "Google Drive", "OneDrive", "SharePoint", "Dropbox"]
            )
            
            if source_type == "Azure Blob Storage":
                connection_string = st.text_input(
                    "Chaîne de connexion",
                    type="password",
                    help="Format: DefaultEndpointsProtocol=https;AccountName=..."
                )
                
                if st.button("🔗 Connecter"):
                    # Logique de connexion
                    st.success("✅ Source ajoutée avec succès")
                    st.session_state.show_add_source = False

def show_explorer_configuration():
    """Configuration de l'explorateur"""
    
    st.markdown("### ⚙️ Configuration de l'Explorateur")
    
    # Préférences d'affichage
    with st.expander("🎨 Préférences d'affichage", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.number_input(
                "Documents par page",
                min_value=5,
                max_value=50,
                value=EXPLORER_CONFIG['files_per_page'],
                step=5,
                key="config_files_per_page"
            )
            
            st.number_input(
                "Caractères d'aperçu",
                min_value=100,
                max_value=1000,
                value=EXPLORER_CONFIG['preview_chars'],
                step=100,
                key="config_preview_chars"
            )
        
        with col2:
            st.selectbox(
                "Vue par défaut",
                ["list", "grid", "kanban", "timeline"],
                index=0,
                key="config_default_view"
            )
            
            st.selectbox(
                "Tri par défaut",
                ["Date ↓", "Date ↑", "Titre A-Z", "Titre Z-A"],
                key="config_default_sort"
            )
        
        with col3:
            st.checkbox("Aperçus automatiques", value=True, key="config_auto_preview")
            st.checkbox("Insights IA automatiques", value=False, key="config_auto_ai")
            st.checkbox("Mode sombre", value=False, key="config_dark_mode")
    
    # Configuration IA
    with st.expander("🤖 Configuration IA", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.multiselect(
                "Modèles IA par défaut",
                list(EXPLORER_CONFIG['ai_models'].keys()),
                default=['gpt-4'],
                format_func=lambda x: f"{EXPLORER_CONFIG['ai_models'][x]['icon']} {EXPLORER_CONFIG['ai_models'][x]['name']}",
                key="config_default_models"
            )
            
            st.selectbox(
                "Profondeur d'analyse par défaut",
                ["Rapide", "Standard", "Approfondie", "Expert"],
                index=1,
                key="config_default_depth"
            )
        
        with col2:
            st.checkbox("Mode fusion par défaut", value=False, key="config_default_fusion")
            st.checkbox("Analyse automatique à l'import", value=False, key="config_auto_analyze")
            
            st.number_input(
                "Limite de documents en analyse simultanée",
                min_value=1,
                max_value=20,
                value=5,
                key="config_max_concurrent_analysis"
            )
    
    # Extensions de fichiers
    with st.expander("📄 Types de fichiers supportés", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.multiselect(
                "Extensions documents",
                ['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.json', '.xml', '.rtf', '.odt'],
                default=EXPLORER_CONFIG['supported_extensions'],
                key="config_doc_extensions"
            )
        
        with col2:
            st.multiselect(
                "Extensions images",
                ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'],
                default=EXPLORER_CONFIG['image_extensions'],
                key="config_img_extensions"
            )
        
        st.number_input(
            "Taille maximale par fichier (MB)",
            min_value=1,
            max_value=500,
            value=EXPLORER_CONFIG['max_file_size_mb'],
            key="config_max_file_size"
        )
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
            save_explorer_config()
    
    with col2:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            reset_explorer_config()
    
    with col3:
        if st.button("📤 Exporter config", use_container_width=True):
            export_explorer_config()

# Fonctions utilitaires

def get_available_sources() -> List[str]:
    """Récupère les sources disponibles"""
    sources = []
    
    if st.session_state.get('azure_documents'):
        sources.append("Documents locaux")
    
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and blob_manager.is_connected():
        sources.append("Azure Blob Storage")
    
    if st.session_state.get('google_drive_connected'):
        sources.append("Google Drive")
    
    if st.session_state.get('onedrive_connected'):
        sources.append("OneDrive")
    
    if not sources:
        sources = ["Documents locaux"]
    
    return sources

def get_filtered_documents(search_query: str, quick_filter: str) -> Dict[str, Document]:
    """Filtre les documents selon les critères"""
    documents = st.session_state.get('azure_documents', {})
    
    if not search_query and quick_filter == "Tous":
        return documents
    
    filtered = {}
    
    for doc_id, doc in documents.items():
        # Filtre rapide
        if quick_filter == "📅 Cette semaine":
            if (datetime.now() - doc.created_at).days > 7:
                continue
        elif quick_filter == "⭐ Favoris":
            if doc_id not in st.session_state.explorer_state.get('favorite_docs', []):
                continue
        elif quick_filter == "🏷️ Avec tags":
            if not doc.tags:
                continue
        elif quick_filter == "🤖 Analysés":
            if not doc.metadata.get('ai_analyzed'):
                continue
        elif quick_filter == "📎 Non classés":
            if doc.tags or doc.source:
                continue
        
        # Recherche
        if search_query:
            search_lower = search_query.lower()
            
            # Recherche spéciale
            if search_query.startswith('@'):
                # Recherche par ID
                if search_lower[1:] not in doc_id.lower():
                    continue
            elif search_query.startswith('#'):
                # Recherche par tag
                tag_search = search_lower[1:]
                if not any(tag_search in tag.lower() for tag in doc.tags):
                    continue
            elif search_query.startswith('~'):
                # Recherche sémantique (placeholder)
                # Implémenter avec embeddings
                pass
            else:
                # Recherche normale
                searchable = f"{doc.title} {doc.content[:1000]} {' '.join(doc.tags)} {doc.source or ''}".lower()
                if search_lower not in searchable:
                    continue
        
        filtered[doc_id] = doc
    
    return filtered

def toggle_document_selection(doc_id: str):
    """Bascule la sélection d'un document"""
    selected = st.session_state.explorer_state.get('selected_docs', [])
    
    if doc_id in selected:
        selected.remove(doc_id)
    else:
        selected.append(doc_id)
    
    st.session_state.explorer_state['selected_docs'] = selected

def toggle_favorite(doc_id: str):
    """Bascule le statut favori d'un document"""
    favorites = st.session_state.explorer_state.get('favorite_docs', [])
    
    if doc_id in favorites:
        favorites.remove(doc_id)
        st.toast(f"⭐ Retiré des favoris")
    else:
        favorites.append(doc_id)
        st.toast(f"⭐ Ajouté aux favoris")
    
    st.session_state.explorer_state['favorite_docs'] = favorites
    st.rerun()

def add_to_ai_queue(doc_id: str, doc: Document):
    """Ajoute un document à la file d'analyse IA"""
    queue = st.session_state.explorer_state.get('ai_analysis_queue', [])
    
    # Vérifier si déjà dans la file
    if any(qid == doc_id for qid, _ in queue):
        st.warning("Document déjà dans la file d'attente")
        return
    
    queue.append((doc_id, doc))
    st.session_state.explorer_state['ai_analysis_queue'] = queue
    
    st.success(f"✅ '{doc.title}' ajouté à la file d'analyse IA")
    st.rerun()

def remove_from_ai_queue(doc_id: str):
    """Retire un document de la file d'analyse"""
    queue = st.session_state.explorer_state.get('ai_analysis_queue', [])
    queue = [(qid, doc) for qid, doc in queue if qid != doc_id]
    st.session_state.explorer_state['ai_analysis_queue'] = queue
    st.rerun()

def show_document_modal(doc_id: str, doc: Document):
    """Affiche un document dans une fenêtre modale"""
    st.session_state.current_document = {
        'id': doc_id,
        'document': doc
    }
    st.session_state.show_document_detail = True

def edit_document_modal(doc_id: str, doc: Document):
    """Ouvre l'éditeur de document"""
    st.session_state.editing_document = {
        'id': doc_id,
        'document': doc
    }

def show_document_menu(doc_id: str, doc: Document):
    """Affiche le menu d'actions pour un document"""
    # Utiliser un popover ou selectbox pour les actions supplémentaires
    pass

def show_document_stats(doc_id: str, doc: Document):
    """Affiche les statistiques détaillées d'un document"""
    with st.expander(f"📊 Statistiques - {doc.title}", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Caractères", f"{len(doc.content):,}")
            st.metric("Mots", f"{len(doc.content.split()):,}")
            st.metric("Lignes", f"{len(doc.content.splitlines()):,}")
        
        with col2:
            st.metric("Paragraphes", f"{len([p for p in doc.content.split('\n\n') if p.strip()]):,}")
            st.metric("Phrases (approx.)", f"{doc.content.count('.') + doc.content.count('!') + doc.content.count('?'):,}")
            read_time = calculate_read_time(doc.content)
            st.metric("Temps de lecture", f"{read_time} min")
        
        with col3:
            st.metric("Taille", format_file_size(len(doc.content)))
            st.metric("Tags", len(doc.tags))
            st.metric("Créé il y a", f"{(datetime.now() - doc.created_at).days} jours")

def show_document_relations(doc_id: str, doc: Document):
    """Affiche les relations entre documents"""
    st.info("🚧 Fonctionnalité en développement - Graphe de relations à venir")

def export_single_document(doc_id: str, doc: Document):
    """Exporte un document unique"""
    export_format = st.selectbox(
        "Format d'export",
        ["JSON", "TXT", "PDF", "DOCX"],
        key=f"export_format_{doc_id}"
    )
    
    if export_format == "JSON":
        data = doc.to_dict()
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        st.download_button(
            "💾 Télécharger JSON",
            json_str,
            f"{sanitize_filename(doc.title)}.json",
            "application/json",
            key=f"download_json_{doc_id}"
        )
    
    elif export_format == "TXT":
        st.download_button(
            "💾 Télécharger TXT",
            doc.content,
            f"{sanitize_filename(doc.title)}.txt",
            "text/plain",
            key=f"download_txt_{doc_id}"
        )

def save_ai_results(doc_id: str, model_id: str, results: Dict[str, Any]):
    """Sauvegarde les résultats d'analyse IA"""
    if doc_id in st.session_state.azure_documents:
        doc = st.session_state.azure_documents[doc_id]
        
        if 'ai_results' not in doc.metadata:
            doc.metadata['ai_results'] = {}
        
        doc.metadata['ai_results'][model_id] = results
        doc.metadata['ai_results_saved'] = datetime.now().isoformat()
        
        st.success("✅ Résultats sauvegardés")

def visualize_ai_results(doc_id: str, results: Dict[str, Any]):
    """Visualise les résultats d'analyse IA"""
    st.info("🚧 Visualisations IA en développement")

def delete_document(doc_id: str):
    """Supprime un document"""
    if doc_id in st.session_state.azure_documents:
        del st.session_state.azure_documents[doc_id]
        
        # Retirer des favoris et sélections
        if doc_id in st.session_state.explorer_state.get('favorite_docs', []):
            st.session_state.explorer_state['favorite_docs'].remove(doc_id)
        
        if doc_id in st.session_state.explorer_state.get('selected_docs', []):
            st.session_state.explorer_state['selected_docs'].remove(doc_id)
        
        st.success("✅ Document supprimé")
        st.rerun()

def get_document_types(documents: Dict[str, Document]) -> List[str]:
    """Récupère les types de documents uniques"""
    types = set()
    
    for doc in documents.values():
        doc_type = get_document_type(doc)
        types.add(doc_type)
    
    return sorted(list(types))

def get_document_type(doc: Document) -> str:
    """Détermine le type d'un document"""
    if doc.mime_type:
        if 'pdf' in doc.mime_type:
            return "PDF"
        elif 'word' in doc.mime_type or 'document' in doc.mime_type:
            return "Word"
        elif 'sheet' in doc.mime_type or 'excel' in doc.mime_type:
            return "Excel"
        elif 'text' in doc.mime_type:
            return "Texte"
    
    # Déduction depuis le titre
    title_lower = doc.title.lower()
    if title_lower.endswith('.pdf'):
        return "PDF"
    elif title_lower.endswith(('.doc', '.docx')):
        return "Word"
    elif title_lower.endswith(('.xls', '.xlsx')):
        return "Excel"
    elif title_lower.endswith('.txt'):
        return "Texte"
    
    return "Autre"

def confirm_delete_document(doc_id: str) -> bool:
    """Demande confirmation pour supprimer un document"""
    return st.checkbox(f"Confirmer la suppression", key=f"confirm_del_{doc_id}")

def save_explorer_config():
    """Sauvegarde la configuration de l'explorateur"""
    # Collecter toutes les valeurs de configuration
    config = {
        'files_per_page': st.session_state.get('config_files_per_page', 20),
        'preview_chars': st.session_state.get('config_preview_chars', 500),
        'default_view': st.session_state.get('config_default_view', 'list'),
        'default_sort': st.session_state.get('config_default_sort', 'Date ↓'),
        'auto_preview': st.session_state.get('config_auto_preview', True),
        'auto_ai': st.session_state.get('config_auto_ai', False),
        'dark_mode': st.session_state.get('config_dark_mode', False),
        'default_models': st.session_state.get('config_default_models', ['gpt-4']),
        'default_depth': st.session_state.get('config_default_depth', 'Standard'),
        'default_fusion': st.session_state.get('config_default_fusion', False),
        'auto_analyze': st.session_state.get('config_auto_analyze', False)
    }
    
    st.session_state.explorer_config = config
    st.success("✅ Configuration sauvegardée")

def reset_explorer_config():
    """Réinitialise la configuration par défaut"""
    if st.button("⚠️ Confirmer la réinitialisation"):
        st.session_state.explorer_config = EXPLORER_CONFIG
        st.success("✅ Configuration réinitialisée")
        st.rerun()

def export_explorer_config():
    """Exporte la configuration actuelle"""
    config = st.session_state.get('explorer_config', EXPLORER_CONFIG)
    config_json = json.dumps(config, indent=2)
    
    st.download_button(
        "💾 Télécharger configuration",
        config_json,
        "explorer_config.json",
        "application/json"
    )

# Point d'entrée pour le lazy loading
if __name__ == "__main__":
    run()