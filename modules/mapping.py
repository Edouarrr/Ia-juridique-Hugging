# modules/mapping.py
"""Module de cartographie des relations et entités juridiques avec multi-IA"""

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import streamlit as st

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.text_processing import extract_entities
from utils import clean_key, format_legal_date, truncate_text

import networkx as nx
import plotly.graph_objects as go
import pandas as pd

from managers.multi_llm_manager import MultiLLMManager
from modules.dataclasses import Document, Entity, Relationship


def run():
    """Fonction principale du module - Point d'entrée pour le lazy loading"""
    
    # Initialisation du style personnalisé
    apply_custom_styling()
    
    # Header avec animation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="module-header">
            <h1>🗺️ Cartographie des Relations</h1>
            <p class="module-subtitle">Analyse intelligente des réseaux d'entités et relations juridiques</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialisation des variables de session
    initialize_session_state()
    
    # Vérification des dépendances
    check_dependencies()
    
    # Interface principale en onglets
    tab_icons = ["📤", "🤖", "⚙️", "🚀", "📊", "💾"]
    tab_names = ["Sources", "IA & Modèles", "Configuration", "Analyse", "Résultats", "Export"]
    tabs = st.tabs([f"{icon} {name}" for icon, name in zip(tab_icons, tab_names)])
    
    with tabs[0]:  # Sources
        render_sources_tab()
    
    with tabs[1]:  # IA & Modèles
        render_ai_models_tab()
    
    with tabs[2]:  # Configuration
        render_configuration_tab()
    
    with tabs[3]:  # Analyse
        render_analysis_tab()
    
    with tabs[4]:  # Résultats
        render_results_tab()
    
    with tabs[5]:  # Export
        render_export_tab()

def apply_custom_styling():
    """Applique le style CSS personnalisé pour le module"""
    st.markdown("""
    <style>
    .module-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        animation: fadeIn 0.5s ease-in;
    }
    
    .module-header h1 {
        color: white;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .module-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .config-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .config-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .ai-model-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .ai-model-card:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .result-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
    }
    
    .progress-step {
        background: #e9ecef;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        margin: 0.2rem 0;
        transition: all 0.3s ease;
    }
    
    .progress-step.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(10px);
    }
    
    .network-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .entity-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
        transition: all 0.2s ease;
    }
    
    .entity-badge:hover {
        transform: scale(1.1);
    }
    
    .entity-badge.person {
        background: #FF6B6B;
        color: white;
    }
    
    .entity-badge.company {
        background: #4ECDC4;
        color: white;
    }
    
    .entity-badge.organization {
        background: #45B7D1;
        color: white;
    }
    
    .relation-line {
        stroke: #999;
        stroke-width: 2;
        fill: none;
        transition: all 0.3s ease;
    }
    
    .relation-line:hover {
        stroke: #667eea;
        stroke-width: 4;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialise les variables de session pour le module"""
    if 'mapping_state' not in st.session_state:
        st.session_state.mapping_state = {
            'initialized': True,
            'selected_documents': [],
            'selected_models': [],
            'fusion_mode': 'consensus',
            'config': {
                'mapping_type': 'complete',
                'depth': 2,
                'min_strength': 0.3,
                'layout': 'spring',
                'show_labels': True,
                'show_weights': False,
                'color_by': 'type',
                'entity_types': ['personne', 'société'],
                'exclude_entities': '',
                'focus_entities': ''
            },
            'analysis_status': 'idle',
            'results': None,
            'ai_results': {},
            'fusion_result': None
        }

def check_dependencies():
    """Vérifie et affiche l'état des dépendances"""
    with st.expander("📦 État des dépendances", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ NetworkX installé")

        with col2:
            st.success("✅ Plotly installé")

        with col3:
            st.success("✅ Pandas installé")

def render_sources_tab():
    """Rendu de l'onglet Sources"""
    st.markdown("### 📤 Sélection des sources de données")
    
    # Méthode de sélection
    source_method = st.radio(
        "Méthode de sélection",
        ["📁 Documents Azure", "📤 Upload de fichiers", "🔍 Recherche intelligente", "📚 Sélection multiple"],
        horizontal=True
    )
    
    selected_docs = []
    
    if source_method == "📁 Documents Azure":
        # Sélection depuis Azure
        if 'azure_documents' in st.session_state and st.session_state.azure_documents:
            st.markdown("#### Documents disponibles")
            
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                doc_type_filter = st.multiselect(
                    "Type de document",
                    ["Contrat", "Procédure", "Correspondance", "Expertise"],
                    default=[]
                )
            with col2:
                date_filter = st.date_input(
                    "Date après le",
                    value=None
                )
            with col3:
                search_filter = st.text_input(
                    "Rechercher dans les titres",
                    placeholder="Mots-clés..."
                )
            
            # Liste des documents avec sélection améliorée
            st.markdown("#### Sélectionner les documents")
            
            # Boutons de sélection rapide
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Tout sélectionner", use_container_width=True):
                    st.session_state.mapping_state['selected_documents'] = list(st.session_state.azure_documents.keys())
            with col2:
                if st.button("❌ Tout désélectionner", use_container_width=True):
                    st.session_state.mapping_state['selected_documents'] = []
            with col3:
                if st.button("🔄 Inverser sélection", use_container_width=True):
                    current = st.session_state.mapping_state['selected_documents']
                    all_docs = list(st.session_state.azure_documents.keys())
                    st.session_state.mapping_state['selected_documents'] = [d for d in all_docs if d not in current]
            
            # Affichage des documents
            for doc_id, doc in st.session_state.azure_documents.items():
                # Appliquer les filtres
                if doc_type_filter and doc.metadata.get('type') not in doc_type_filter:
                    continue
                if search_filter and search_filter.lower() not in doc.title.lower():
                    continue
                
                # Carte de document
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        is_selected = st.checkbox(
                            "Sélectionner",
                            key=f"select_doc_{doc_id}",
                            value=doc_id in st.session_state.mapping_state.get('selected_documents', [])
                        )
                        
                        if is_selected and doc_id not in st.session_state.mapping_state['selected_documents']:
                            st.session_state.mapping_state['selected_documents'].append(doc_id)
                        elif not is_selected and doc_id in st.session_state.mapping_state['selected_documents']:
                            st.session_state.mapping_state['selected_documents'].remove(doc_id)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="config-card">
                            <h4>📄 {doc.title}</h4>
                            <p><small>Source: {doc.source} | Taille: {len(doc.content)} caractères</small></p>
                            <p>{truncate_text(doc.content, 150)}</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Résumé de la sélection
            if st.session_state.mapping_state['selected_documents']:
                st.success(f"✅ {len(st.session_state.mapping_state['selected_documents'])} documents sélectionnés")
            else:
                st.warning("⚠️ Aucun document sélectionné")
        else:
            st.info("ℹ️ Aucun document Azure disponible. Veuillez d'abord charger des documents.")
    
    elif source_method == "📤 Upload de fichiers":
        uploaded_files = st.file_uploader(
            "Chargez vos fichiers",
            type=['pdf', 'txt', 'docx', 'rtf'],
            accept_multiple_files=True,
            help="Formats supportés : PDF, TXT, DOCX, RTF"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} fichiers chargés")
            # Traiter les fichiers uploadés
            for file in uploaded_files:
                with st.expander(f"📄 {file.name}"):
                    st.write(f"Type: {file.type}")
                    st.write(f"Taille: {file.size} octets")
    
    elif source_method == "🔍 Recherche intelligente":
        st.markdown("#### Recherche avancée dans la base documentaire")
        
        # Interface de recherche avancée
        search_query = st.text_area(
            "Requête de recherche",
            placeholder="Ex: Tous les contrats mentionnant 'société XYZ' ET 'acquisition' signés après 2023",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            search_scope = st.multiselect(
                "Chercher dans",
                ["Titre", "Contenu", "Métadonnées", "Parties prenantes"],
                default=["Titre", "Contenu"]
            )
        
        with col2:
            search_operator = st.radio(
                "Opérateur",
                ["ET (tous les termes)", "OU (au moins un terme)", "Expression exacte"],
                horizontal=True
            )
        
        if st.button("🔍 Lancer la recherche", type="primary", use_container_width=True):
            with st.spinner("Recherche en cours..."):
                time.sleep(1)  # Simulation
                st.info("🔍 Recherche simulée - Fonctionnalité à implémenter")

def render_ai_models_tab():
    """Rendu de l'onglet IA & Modèles"""
    st.markdown("### 🤖 Configuration des modèles d'IA")
    
    # Gestion multi-LLM
    llm_manager = MultiLLMManager()
    available_providers = list(llm_manager.clients.keys()) if llm_manager.clients else []
    
    if not available_providers:
        st.error("❌ Aucun modèle d'IA configuré. Veuillez configurer au moins un fournisseur.")
        return
    
    # Mode de traitement
    col1, col2 = st.columns([2, 1])
    
    with col1:
        analysis_mode = st.radio(
            "Mode d'analyse",
            ["🎯 Modèle unique", "🔀 Multi-modèles parallèle", "🧬 Fusion intelligente"],
            horizontal=True,
            help="""
            - **Modèle unique** : Utilise un seul modèle pour l'analyse
            - **Multi-modèles parallèle** : Interroge plusieurs modèles en parallèle
            - **Fusion intelligente** : Combine les résultats de plusieurs modèles
            """
        )
    
    with col2:
        if analysis_mode == "🧬 Fusion intelligente":
            fusion_strategy = st.selectbox(
                "Stratégie de fusion",
                ["consensus", "weighted", "best_confidence", "union", "intersection"],
                format_func=lambda x: {
                    "consensus": "🤝 Consensus majoritaire",
                    "weighted": "⚖️ Moyenne pondérée",
                    "best_confidence": "🎯 Meilleure confiance",
                    "union": "➕ Union (tous)",
                    "intersection": "🔗 Intersection (commun)"
                }.get(x, x)
            )
            st.session_state.mapping_state['fusion_mode'] = fusion_strategy
    
    # Sélection des modèles
    st.markdown("#### Sélection des modèles")
    
    if analysis_mode == "🎯 Modèle unique":
        selected_model = st.selectbox(
            "Choisir le modèle",
            available_providers,
            format_func=lambda x: f"🤖 {x.upper()}"
        )
        st.session_state.mapping_state['selected_models'] = [selected_model]
    else:
        # Multi-sélection avec interface améliorée
        st.markdown("Sélectionnez les modèles à utiliser :")
        
        # Grille de modèles
        cols = st.columns(min(3, len(available_providers)))
        selected_models = []
        
        for idx, provider in enumerate(available_providers):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                # Carte de modèle stylisée
                is_selected = st.checkbox(
                    f"🤖 {provider.upper()}",
                    key=f"model_{provider}",
                    value=provider in st.session_state.mapping_state.get('selected_models', [])
                )
                
                if is_selected:
                    selected_models.append(provider)
                
                # Informations sur le modèle
                with st.expander(f"ℹ️ Info {provider}", expanded=False):
                    model_info = llm_manager.get_model_info(provider)
                    if model_info:
                        st.write(f"**Modèle :** {model_info.get('model', 'N/A')}")
                        st.write(f"**Température :** {model_info.get('temperature', 0.3)}")
                        st.write(f"**Tokens max :** {model_info.get('max_tokens', 'N/A')}")
        
        st.session_state.mapping_state['selected_models'] = selected_models
        
        if selected_models:
            st.success(f"✅ {len(selected_models)} modèles sélectionnés : {', '.join(selected_models)}")
        else:
            st.warning("⚠️ Veuillez sélectionner au moins un modèle")
    
    # Configuration avancée des modèles
    with st.expander("⚙️ Configuration avancée des modèles", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temperature = st.slider(
                "Température",
                0.0, 1.0, 0.3,
                help="Contrôle la créativité des réponses"
            )
        
        with col2:
            max_tokens = st.number_input(
                "Tokens max",
                min_value=100,
                max_value=4000,
                value=1500,
                step=100
            )
        
        with col3:
            retry_attempts = st.number_input(
                "Tentatives en cas d'échec",
                min_value=1,
                max_value=5,
                value=3
            )
    
    # Prompt personnalisé
    st.markdown("#### Personnalisation du prompt")
    
    use_custom_prompt = st.checkbox("Utiliser un prompt personnalisé", value=False)
    
    if use_custom_prompt:
        custom_prompt = st.text_area(
            "Prompt personnalisé",
            value="""Analyse ces documents pour identifier TOUTES les entités et relations.
Focus sur : {mapping_type}
Profondeur d'analyse : {depth}

Instructions spécifiques :
- Identifier toutes les personnes, sociétés et organisations
- Extraire toutes les relations avec leur type et force
- Fournir des preuves textuelles pour chaque relation
""",
            height=200,
            help="Utilisez {mapping_type} et {depth} comme variables"
        )

def render_configuration_tab():
    """Rendu de l'onglet Configuration"""
    st.markdown("### ⚙️ Configuration de l'analyse")
    
    # Configuration principale dans des cartes
    st.markdown("#### 🎯 Paramètres principaux")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            
            # Type de cartographie avec descriptions
            mapping_type = st.selectbox(
                "🗺️ Type de cartographie",
                ["complete", "personnes", "societes", "flux_financiers", "hierarchique"],
                format_func=lambda x: {
                    "complete": "🌐 Cartographie complète - Toutes les relations",
                    "personnes": "👥 Relations entre personnes - Liens familiaux et professionnels",
                    "societes": "🏢 Structure sociétaire - Participations et filiales",
                    "flux_financiers": "💰 Flux financiers - Virements et transactions",
                    "hierarchique": "📊 Relations hiérarchiques - Organigrammes"
                }.get(x, x.title()),
                key="mapping_type_config"
            )
            st.session_state.mapping_state['config']['mapping_type'] = mapping_type
            
            # Profondeur d'analyse avec visualisation
            depth = st.select_slider(
                "🔍 Profondeur d'analyse",
                options=[1, 2, 3],
                value=st.session_state.mapping_state['config']['depth'],
                format_func=lambda x: {
                    1: "🔸 Niveau 1 - Relations directes uniquement",
                    2: "🔸🔸 Niveau 2 - Relations directes + indirectes",
                    3: "🔸🔸🔸 Niveau 3 - Réseau complet"
                }.get(x),
                key="depth_config"
            )
            st.session_state.mapping_state['config']['depth'] = depth
            
            # Indicateur visuel de profondeur
            st.progress(depth / 3)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            
            # Force minimale des relations
            min_strength = st.slider(
                "💪 Force minimale des relations",
                0.0, 1.0,
                st.session_state.mapping_state['config']['min_strength'],
                0.05,
                help="Filtrer les relations faibles",
                key="min_strength_config"
            )
            st.session_state.mapping_state['config']['min_strength'] = min_strength
            
            # Visualisation du seuil
            strength_levels = ["Très faible", "Faible", "Moyenne", "Forte", "Très forte"]
            strength_index = int(min_strength * 4)
            st.info(f"Seuil actuel : {strength_levels[strength_index]} ({min_strength:.0%})")
            
            # Layout du graphe
            layout = st.selectbox(
                "📐 Disposition du réseau",
                ["spring", "circular", "hierarchical", "kamada_kawai"],
                format_func=lambda x: {
                    "spring": "🌸 Spring - Disposition organique naturelle",
                    "circular": "⭕ Circulaire - Nœuds en cercle",
                    "hierarchical": "📊 Hiérarchique - Niveaux verticaux",
                    "kamada_kawai": "🎯 Kamada-Kawai - Optimisé"
                }.get(x, x.title()),
                key="layout_config"
            )
            st.session_state.mapping_state['config']['layout'] = layout
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Options d'affichage
    st.markdown("#### 🎨 Options d'affichage")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_labels = st.checkbox(
            "🏷️ Afficher les labels",
            value=st.session_state.mapping_state['config']['show_labels'],
            key="show_labels_config"
        )
        st.session_state.mapping_state['config']['show_labels'] = show_labels
        
        show_weights = st.checkbox(
            "📊 Afficher les poids",
            value=st.session_state.mapping_state['config']['show_weights'],
            key="show_weights_config"
        )
        st.session_state.mapping_state['config']['show_weights'] = show_weights
    
    with col2:
        color_by = st.radio(
            "🎨 Coloration des nœuds",
            ["type", "centrality", "community"],
            format_func=lambda x: {
                "type": "📌 Par type d'entité",
                "centrality": "🎯 Par centralité",
                "community": "👥 Par communauté"
            }.get(x, x.title()),
            key="color_by_config"
        )
        st.session_state.mapping_state['config']['color_by'] = color_by
    
    with col3:
        # Taille des nœuds
        node_size_factor = st.slider(
            "📏 Taille des nœuds",
            0.5, 2.0, 1.0, 0.1,
            help="Facteur de taille des nœuds"
        )
    
    # Filtres avancés
    with st.expander("🔍 Filtres avancés", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Types d'entités
            entity_types = st.multiselect(
                "Types d'entités à inclure",
                ["personne", "société", "organisation", "lieu", "compte", "autre"],
                default=st.session_state.mapping_state['config']['entity_types'],
                key="entity_types_config"
            )
            st.session_state.mapping_state['config']['entity_types'] = entity_types
            
            # Focus sur certaines entités
            focus_entities = st.text_input(
                "🎯 Focus sur ces entités (séparées par des virgules)",
                value=st.session_state.mapping_state['config']['focus_entities'],
                placeholder="Ex: Jean Dupont, Société XYZ",
                key="focus_entities_config"
            )
            st.session_state.mapping_state['config']['focus_entities'] = focus_entities
        
        with col2:
            # Entités à exclure
            exclude_entities = st.text_area(
                "❌ Entités à exclure (une par ligne)",
                value=st.session_state.mapping_state['config']['exclude_entities'],
                placeholder="Ex:\nFrance\nParis\nEurope",
                height=100,
                key="exclude_entities_config"
            )
            st.session_state.mapping_state['config']['exclude_entities'] = exclude_entities
            
            # Relations à filtrer
            relation_types = st.multiselect(
                "Types de relations",
                ["hierarchical", "contractual", "financial", "familial", "business", "ownership"],
                help="Laisser vide pour toutes les relations"
            )
    
    # Aperçu de la configuration
    st.markdown("#### 👁️ Aperçu de la configuration")
    
    config_summary = f"""
    <div class="result-card">
        <h4>Configuration actuelle :</h4>
        <ul>
            <li><strong>Type :</strong> {mapping_type.replace('_', ' ').title()}</li>
            <li><strong>Profondeur :</strong> Niveau {depth}</li>
            <li><strong>Seuil de force :</strong> {min_strength:.0%}</li>
            <li><strong>Layout :</strong> {layout.title()}</li>
            <li><strong>Types d'entités :</strong> {', '.join(entity_types)}</li>
            <li><strong>Modèles IA :</strong> {len(st.session_state.mapping_state['selected_models'])} sélectionnés</li>
        </ul>
    </div>
    """
    st.markdown(config_summary, unsafe_allow_html=True)

def render_analysis_tab():
    """Rendu de l'onglet Analyse"""
    st.markdown("### 🚀 Lancement de l'analyse")
    
    # Vérifications pré-analyse
    ready_to_analyze = True
    checks = []
    
    # Vérifier les documents
    if not st.session_state.mapping_state['selected_documents']:
        checks.append("❌ Aucun document sélectionné")
        ready_to_analyze = False
    else:
        checks.append(f"✅ {len(st.session_state.mapping_state['selected_documents'])} documents sélectionnés")
    
    # Vérifier les modèles
    if not st.session_state.mapping_state['selected_models']:
        checks.append("❌ Aucun modèle IA sélectionné")
        ready_to_analyze = False
    else:
        checks.append(f"✅ {len(st.session_state.mapping_state['selected_models'])} modèles sélectionnés")
    
    # Vérifier la configuration
    if st.session_state.mapping_state['config']:
        checks.append("✅ Configuration définie")
    else:
        checks.append("❌ Configuration manquante")
        ready_to_analyze = False
    
    # Afficher les vérifications
    for check in checks:
        st.write(check)
    
    # Estimation du temps
    if ready_to_analyze:
        doc_count = len(st.session_state.mapping_state['selected_documents'])
        model_count = len(st.session_state.mapping_state['selected_models'])
        depth = st.session_state.mapping_state['config']['depth']
        
        # Estimation basique
        base_time = 5  # secondes par document
        model_factor = 1 if model_count == 1 else 0.7 * model_count  # Parallélisation
        depth_factor = depth * 0.5
        
        estimated_time = int(doc_count * base_time * model_factor * depth_factor)
        
        st.info(f"⏱️ Temps estimé : {estimated_time // 60} min {estimated_time % 60} sec")
    
    # Bouton de lancement
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button(
            "🚀 Lancer l'analyse",
            type="primary",
            use_container_width=True,
            disabled=not ready_to_analyze
        ):
            st.session_state.mapping_state['analysis_status'] = 'running'
            run_mapping_analysis()
    
    # Affichage du statut d'analyse
    if st.session_state.mapping_state['analysis_status'] == 'running':
        display_analysis_progress()
    elif st.session_state.mapping_state['analysis_status'] == 'completed':
        st.success("✅ Analyse terminée avec succès !")
        st.balloons()
    elif st.session_state.mapping_state['analysis_status'] == 'failed':
        st.error("❌ L'analyse a échoué. Veuillez réessayer.")

def run_mapping_analysis():
    """Lance l'analyse de cartographie"""
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        details_text = st.empty()
        
        # Phases d'analyse
        phases = [
            ("Initialisation", 5),
            ("Chargement des documents", 10),
            ("Extraction des entités", 25),
            ("Analyse des relations", 40),
            ("Enrichissement IA", 70),
            ("Fusion des résultats", 85),
            ("Génération de la visualisation", 95),
            ("Finalisation", 100)
        ]
        
        try:
            # Collecter les documents
            documents = []
            for doc_id in st.session_state.mapping_state['selected_documents']:
                if doc_id in st.session_state.azure_documents:
                    doc = st.session_state.azure_documents[doc_id]
                    documents.append({
                        'id': doc_id,
                        'title': doc.title,
                        'content': doc.content,
                        'source': doc.source,
                        'metadata': doc.metadata
                    })
            
            # Simulation de l'analyse avec progression
            for phase, progress_value in phases:
                status_text.text(f"⏳ {phase}...")
                details_text.text(f"Traitement en cours... {progress_value}%")
                progress_bar.progress(progress_value / 100)
                
                if phase == "Extraction des entités":
                    # Extraction réelle des entités
                    entities, relationships = extract_entities_and_relationships(
                        documents, 
                        st.session_state.mapping_state['config']
                    )
                    details_text.text(f"✅ {len(entities)} entités trouvées")
                
                elif phase == "Analyse des relations":
                    # Analyse des relations
                    details_text.text(f"✅ {len(relationships)} relations identifiées")
                
                elif phase == "Enrichissement IA":
                    # Enrichissement avec les modèles sélectionnés
                    if len(st.session_state.mapping_state['selected_models']) > 0:
                        ai_results = process_with_multiple_models(
                            documents, entities, relationships,
                            st.session_state.mapping_state['selected_models'],
                            st.session_state.mapping_state['config']
                        )
                        st.session_state.mapping_state['ai_results'] = ai_results
                
                elif phase == "Fusion des résultats":
                    # Fusion si multi-modèles
                    if len(st.session_state.mapping_state['selected_models']) > 1:
                        fusion_result = fuse_ai_results(
                            st.session_state.mapping_state['ai_results'],
                            st.session_state.mapping_state['fusion_mode']
                        )
                        st.session_state.mapping_state['fusion_result'] = fusion_result
                
                time.sleep(0.5)  # Simulation du temps de traitement
            
            # Générer le résultat final
            mapping_result = generate_final_mapping_result(
                documents, entities, relationships,
                st.session_state.mapping_state['config'],
                st.session_state.mapping_state.get('fusion_result')
            )
            
            st.session_state.mapping_state['results'] = mapping_result
            st.session_state.mapping_state['analysis_status'] = 'completed'
            
            status_text.text("✅ Analyse terminée !")
            details_text.text("")
            
        except Exception as e:
            st.session_state.mapping_state['analysis_status'] = 'failed'
            status_text.text("❌ Erreur lors de l'analyse")
            details_text.text(str(e))
            st.error(f"Erreur : {str(e)}")

def display_analysis_progress():
    """Affiche la progression de l'analyse en temps réel"""
    # Cette fonction serait appelée pendant l'analyse pour afficher la progression
    st.info("🔄 Analyse en cours...")

def process_with_multiple_models(documents, entities, relationships, selected_models, config):
    """Traite l'analyse avec plusieurs modèles IA"""
    llm_manager = MultiLLMManager()
    results = {}
    
    for model in selected_models:
        if model in llm_manager.clients:
            # Enrichir avec ce modèle spécifique
            model_entities, model_relationships = enrich_with_specific_model(
                documents, entities, relationships, config, model, llm_manager
            )
            
            results[model] = {
                'entities': model_entities,
                'relationships': model_relationships,
                'confidence': 0.8  # Simulé
            }
    
    return results

def enrich_with_specific_model(documents, entities, relationships, config, model, llm_manager):
    """Enrichit l'analyse avec un modèle spécifique"""
    # Construction du prompt
    prompt = f"""Analyse ces documents pour identifier TOUTES les entités et relations de type {config['mapping_type']}.

DOCUMENTS:
"""
    
    for doc in documents[:3]:  # Limiter pour la démo
        prompt += f"\n--- {doc['title']} ---\n{doc['content'][:1000]}...\n"
    
    prompt += f"""
Identifie:
1. ENTITÉS (personnes, sociétés, organisations)
   - Nom complet
   - Type
   - Rôle/fonction
   - Attributs importants

2. RELATIONS
   - Entité source -> Entité cible
   - Type de relation
   - Description
   - Force (0-1)

Focus sur les relations de type : {config['mapping_type']}
Profondeur : {config['depth']}
"""
    
    # Interroger le modèle
    response = llm_manager.query_single_llm(
        model,
        prompt,
        "Tu es un expert en analyse de réseaux et relations dans les documents juridiques.",
        temperature=0.3
    )
    
    if response['success']:
        # Parser la réponse
        new_entities, new_relationships = parse_ai_mapping_response(response['response'])
        
        # Fusionner avec l'existant
        all_entities = merge_entities(entities, new_entities)
        all_relationships = relationships + new_relationships
        
        return all_entities, consolidate_relationships(all_relationships)
    
    return entities, relationships

def fuse_ai_results(ai_results, fusion_mode):
    """Fusionne les résultats de plusieurs modèles IA"""
    if not ai_results:
        return None
    
    if fusion_mode == "consensus":
        # Fusion par consensus majoritaire
        return fuse_by_consensus(ai_results)
    elif fusion_mode == "weighted":
        # Fusion pondérée par confiance
        return fuse_by_weighted_average(ai_results)
    elif fusion_mode == "best_confidence":
        # Prendre le modèle avec la meilleure confiance
        return fuse_by_best_confidence(ai_results)
    elif fusion_mode == "union":
        # Union de tous les résultats
        return fuse_by_union(ai_results)
    elif fusion_mode == "intersection":
        # Intersection des résultats
        return fuse_by_intersection(ai_results)
    
    return None

def fuse_by_consensus(ai_results):
    """Fusion par consensus majoritaire"""
    # Compter les occurrences de chaque entité et relation
    entity_votes = defaultdict(int)
    relation_votes = defaultdict(int)
    
    for model, result in ai_results.items():
        for entity in result['entities']:
            entity_votes[entity.name] += 1
        
        for rel in result['relationships']:
            rel_key = (rel.source, rel.target, rel.type)
            relation_votes[rel_key] += 1
    
    # Seuil de consensus (majorité)
    threshold = len(ai_results) / 2
    
    # Entités consensuelles
    consensus_entities = []
    for entity_name, votes in entity_votes.items():
        if votes >= threshold:
            # Récupérer l'entité depuis n'importe quel modèle
            for result in ai_results.values():
                for entity in result['entities']:
                    if entity.name == entity_name:
                        consensus_entities.append(entity)
                        break
                else:
                    continue
                break
    
    # Relations consensuelles
    consensus_relationships = []
    for rel_key, votes in relation_votes.items():
        if votes >= threshold:
            source, target, rel_type = rel_key
            # Créer la relation
            consensus_relationships.append(Relationship(
                source=source,
                target=target,
                type=rel_type,
                strength=votes / len(ai_results)
            ))
    
    return {
        'entities': consensus_entities,
        'relationships': consensus_relationships,
        'fusion_method': 'consensus',
        'model_count': len(ai_results)
    }

def fuse_by_weighted_average(ai_results):
    """Fusion pondérée par la confiance des modèles"""
    # Implémenter la fusion pondérée
    # Pour la démo, on retourne le premier résultat
    return list(ai_results.values())[0] if ai_results else None

def fuse_by_best_confidence(ai_results):
    """Sélectionne le résultat du modèle avec la meilleure confiance"""
    best_model = max(ai_results.items(), key=lambda x: x[1].get('confidence', 0))
    return best_model[1]

def fuse_by_union(ai_results):
    """Union de tous les résultats"""
    all_entities = []
    all_relationships = []
    
    for result in ai_results.values():
        all_entities.extend(result['entities'])
        all_relationships.extend(result['relationships'])
    
    # Dédupliquer
    unique_entities = list({e.name: e for e in all_entities}.values())
    unique_relationships = consolidate_relationships(all_relationships)
    
    return {
        'entities': unique_entities,
        'relationships': unique_relationships,
        'fusion_method': 'union'
    }

def fuse_by_intersection(ai_results):
    """Intersection des résultats"""
    # Pour l'intersection, on ne garde que ce qui est présent dans tous les modèles
    if not ai_results:
        return None
    
    # Initialiser avec le premier résultat
    first_result = list(ai_results.values())[0]
    common_entities = set(e.name for e in first_result['entities'])
    common_relations = set((r.source, r.target, r.type) for r in first_result['relationships'])
    
    # Intersection avec les autres
    for result in list(ai_results.values())[1:]:
        entity_names = set(e.name for e in result['entities'])
        relation_keys = set((r.source, r.target, r.type) for r in result['relationships'])
        
        common_entities &= entity_names
        common_relations &= relation_keys
    
    # Reconstruire les objets
    final_entities = []
    final_relationships = []
    
    for result in ai_results.values():
        for entity in result['entities']:
            if entity.name in common_entities and entity.name not in [e.name for e in final_entities]:
                final_entities.append(entity)
        
        for rel in result['relationships']:
            rel_key = (rel.source, rel.target, rel.type)
            if rel_key in common_relations and rel_key not in [(r.source, r.target, r.type) for r in final_relationships]:
                final_relationships.append(rel)
    
    return {
        'entities': final_entities,
        'relationships': final_relationships,
        'fusion_method': 'intersection'
    }

def generate_final_mapping_result(documents, entities, relationships, config, fusion_result=None):
    """Génère le résultat final de la cartographie"""
    # Utiliser le résultat de fusion si disponible
    if fusion_result:
        entities = fusion_result.get('entities', entities)
        relationships = fusion_result.get('relationships', relationships)
    
    # Filtrer selon la configuration
    filtered_entities, filtered_relationships = filter_mapping_data(entities, relationships, config)
    
    # Analyser le réseau
    network_analysis = analyze_network(filtered_entities, filtered_relationships)
    
    # Créer la visualisation
    visualization = create_network_visualization(filtered_entities, filtered_relationships, config, network_analysis)
    
    return {
        'type': config['mapping_type'],
        'entities': filtered_entities,
        'relationships': filtered_relationships,
        'analysis': network_analysis,
        'visualization': visualization,
        'document_count': len(documents),
        'config': config,
        'timestamp': datetime.now(),
        'fusion_info': fusion_result if fusion_result else None
    }

def render_results_tab():
    """Rendu de l'onglet Résultats"""
    if not st.session_state.mapping_state.get('results'):
        st.info("👆 Lancez d'abord l'analyse pour voir les résultats")
        return
    
    results = st.session_state.mapping_state['results']
    
    st.markdown("### 📊 Résultats de la cartographie")
    
    # Métriques principales avec style
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{results['analysis']['node_count']}</h2>
            <p>Entités</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{results['analysis']['edge_count']}</h2>
            <p>Relations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        density_pct = results['analysis']['density'] * 100
        st.markdown(f"""
        <div class="metric-card">
            <h2>{density_pct:.1f}%</h2>
            <p>Densité</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        components = len(results['analysis'].get('components', []))
        st.markdown(f"""
        <div class="metric-card">
            <h2>{components}</h2>
            <p>Composantes</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Information sur la fusion si applicable
    if results.get('fusion_info'):
        fusion_info = results['fusion_info']
        st.info(f"🧬 Résultats fusionnés de {fusion_info.get('model_count', 0)} modèles - Méthode : {fusion_info.get('fusion_method', 'N/A')}")
    
    # Visualisation principale
    st.markdown("#### 🗺️ Visualisation du réseau")
    
    if results.get('visualization'):
        with st.container():
            st.markdown('<div class="network-container">', unsafe_allow_html=True)
            st.plotly_chart(results['visualization'], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Visualisation non disponible - Installez plotly pour les graphiques")
    
    # Onglets détaillés
    detail_tabs = st.tabs(["🎯 Acteurs clés", "👥 Entités", "🔗 Relations", "📊 Analyse", "🌐 Communautés"])
    
    with detail_tabs[0]:  # Acteurs clés
        display_key_players(results['analysis'])
    
    with detail_tabs[1]:  # Entités
        display_entities_detailed(results['entities'], results['analysis'])
    
    with detail_tabs[2]:  # Relations
        display_relationships_detailed(results['relationships'])
    
    with detail_tabs[3]:  # Analyse
        display_network_metrics(results['analysis'])
    
    with detail_tabs[4]:  # Communautés
        display_communities(results['analysis'])

def display_key_players(analysis):
    """Affiche les acteurs clés du réseau"""
    st.markdown("#### 🎯 Acteurs principaux du réseau")
    
    if 'key_players' in analysis and analysis['key_players']:
        for i, player in enumerate(analysis['key_players'][:10], 1):
            centrality = analysis.get('degree_centrality', {}).get(player, 0)
            betweenness = analysis.get('betweenness_centrality', {}).get(player, 0)
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{i}. {player}**")
            
            with col2:
                st.progress(centrality)
                st.caption(f"Centralité: {centrality:.3f}")
            
            with col3:
                st.progress(betweenness)
                st.caption(f"Intermédiarité: {betweenness:.3f}")
            
            with col4:
                if centrality > 0.5:
                    st.markdown("🔴 **Crucial**")
                elif centrality > 0.3:
                    st.markdown("🟡 **Important**")
                else:
                    st.markdown("🟢 **Normal**")
    else:
        st.info("Aucun acteur clé identifié")

def display_entities_detailed(entities, analysis):
    """Affiche le détail des entités"""
    st.markdown("#### 👥 Liste détaillée des entités")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entity_type_filter = st.multiselect(
            "Filtrer par type",
            list(set(e.type for e in entities)),
            default=[]
        )
    
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Nom", "Type", "Mentions", "Centralité"]
        )
    
    with col3:
        search_entity = st.text_input(
            "Rechercher",
            placeholder="Nom de l'entité..."
        )
    
    # Filtrer et trier
    filtered_entities = entities
    
    if entity_type_filter:
        filtered_entities = [e for e in filtered_entities if e.type in entity_type_filter]
    
    if search_entity:
        filtered_entities = [e for e in filtered_entities if search_entity.lower() in e.name.lower()]
    
    # Trier
    if sort_by == "Nom":
        filtered_entities = sorted(filtered_entities, key=lambda e: e.name)
    elif sort_by == "Type":
        filtered_entities = sorted(filtered_entities, key=lambda e: (e.type, e.name))
    elif sort_by == "Mentions":
        filtered_entities = sorted(filtered_entities, key=lambda e: e.mentions_count, reverse=True)
    else:  # Centralité
        centrality = analysis.get('degree_centrality', {})
        filtered_entities = sorted(filtered_entities, key=lambda e: centrality.get(e.name, 0), reverse=True)
    
    # Affichage en grille
    for i in range(0, len(filtered_entities), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(filtered_entities):
                entity = filtered_entities[i + j]
                with col:
                    # Badge de type
                    type_class = entity.type.lower().replace(' ', '-')
                    st.markdown(f'<span class="entity-badge {type_class}">{entity.type.upper()}</span>', unsafe_allow_html=True)
                    
                    st.markdown(f"**{entity.name}**")
                    
                    if 'degree_centrality' in analysis:
                        centrality = analysis['degree_centrality'].get(entity.name, 0)
                        st.progress(centrality)
                        st.caption(f"Centralité: {centrality:.3f}")
                    
                    st.caption(f"Mentions: {entity.mentions_count}")
                    
                    if entity.attributes:
                        with st.expander("Plus d'infos"):
                            for key, value in entity.attributes.items():
                                st.write(f"**{key}:** {value}")

def display_relationships_detailed(relationships):
    """Affiche le détail des relations"""
    st.markdown("#### 🔗 Analyse des relations")
    
    # Statistiques par type
    rel_types = Counter(r.type for r in relationships)

    # Graphique des types de relations
    if rel_types:
        fig = go.Figure(data=[
            go.Bar(
                x=list(rel_types.keys()),
                y=list(rel_types.values()),
                marker_color='rgb(102, 126, 234)'
            )
        ])
        fig.update_layout(
            title="Distribution des types de relations",
            xaxis_title="Type de relation",
            yaxis_title="Nombre",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top relations par force
    st.markdown("##### 💪 Relations les plus fortes")
    
    top_relations = sorted(relationships, key=lambda r: r.strength, reverse=True)[:10]
    
    for rel in top_relations:
        strength_bar = "🟩" * int(rel.strength * 5) + "⬜" * (5 - int(rel.strength * 5))
        
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.write(f"**{rel.source}** → **{rel.target}**")
        
        with col2:
            st.write(f"{strength_bar} ({rel.strength:.2f})")
        
        with col3:
            st.caption(rel.type.replace('_', ' ').title())

def display_network_metrics(analysis):
    """Affiche les métriques détaillées du réseau"""
    st.markdown("#### 📊 Métriques du réseau")
    
    # Métriques en colonnes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🌐 Métriques globales")
        
        metrics = {
            "Nœuds": analysis.get('node_count', 0),
            "Arêtes": analysis.get('edge_count', 0),
            "Densité": f"{analysis.get('density', 0):.3f}",
            "Connecté": "✅ Oui" if analysis.get('is_connected') else "❌ Non"
        }
        
        if 'average_shortest_path' in analysis:
            metrics["Chemin moyen"] = f"{analysis['average_shortest_path']:.2f}"
        
        if 'diameter' in analysis:
            metrics["Diamètre"] = analysis['diameter']
        
        for metric, value in metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.markdown("##### 📈 Distribution des degrés")
        
        if 'degree_centrality' in analysis:
            degrees = list(analysis['degree_centrality'].values())
            
            fig = go.Figure(data=[go.Histogram(
                x=degrees,
                nbinsx=20,
                marker_color='rgb(102, 126, 234)'
            )])
            fig.update_layout(
                xaxis_title="Centralité de degré",
                yaxis_title="Nombre de nœuds",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

def display_communities(analysis):
    """Affiche les communautés détectées"""
    st.markdown("#### 🌐 Communautés détectées")
    
    if 'communities' in analysis and analysis['communities']:
        st.write(f"**Nombre de communautés :** {len(analysis['communities'])}")
        
        if 'modularity' in analysis:
            st.metric("Modularité", f"{analysis['modularity']:.3f}")
        
        # Afficher chaque communauté
        for i, community in enumerate(analysis['communities'], 1):
            with st.expander(f"Communauté {i} - {len(community)} membres"):
                # Afficher les membres en badges
                for member in sorted(community):
                    st.markdown(f'<span class="entity-badge">{member}</span>', unsafe_allow_html=True)
    else:
        st.info("Aucune communauté détectée. Activez NetworkX pour cette fonctionnalité.")

def render_export_tab():
    """Rendu de l'onglet Export"""
    if not st.session_state.mapping_state.get('results'):
        st.info("👆 Lancez d'abord l'analyse pour exporter les résultats")
        return
    
    st.markdown("### 💾 Export des résultats")
    
    results = st.session_state.mapping_state['results']
    
    # Options d'export
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Formats de document")
        
        # Rapport textuel
        if st.button("📝 Générer rapport texte", use_container_width=True):
            report = generate_mapping_report(results)
            st.download_button(
                "💾 Télécharger rapport TXT",
                report.encode('utf-8'),
                f"rapport_cartographie_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                use_container_width=True
            )
        
        # Rapport PDF (simulé)
        if st.button("📑 Générer rapport PDF", use_container_width=True):
            st.info("🚧 Export PDF en cours de développement")
        
        # Rapport Word (simulé)
        if st.button("📘 Générer rapport Word", use_container_width=True):
            st.info("🚧 Export Word en cours de développement")
    
    with col2:
        st.markdown("#### 📊 Formats de données")
        
        # Export Excel
        if st.button("📊 Générer fichier Excel", use_container_width=True):
            excel_data = export_mapping_to_excel(results)
            st.download_button(
                "💾 Télécharger Excel",
                excel_data,
                f"cartographie_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        
        # Export JSON
        if st.button("🗂️ Exporter en JSON", use_container_width=True):
            json_data = export_to_json(results)
            st.download_button(
                "💾 Télécharger JSON",
                json_data,
                f"cartographie_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )
        
        # Export GraphML (pour NetworkX)
        if st.button("🔗 Exporter GraphML", use_container_width=True):
            graphml_data = export_to_graphml(results)
            if graphml_data:
                st.download_button(
                    "💾 Télécharger GraphML",
                    graphml_data,
                    f"reseau_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.graphml",
                    "application/xml",
                    use_container_width=True,
                )
    
    # Export de la visualisation
    st.markdown("#### 🖼️ Export de la visualisation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if results.get('visualization'):
            if st.button("🖼️ Exporter en PNG", use_container_width=True):
                # Exporter la figure Plotly en PNG
                img_bytes = results['visualization'].to_image(format="png", width=1200, height=800)
                st.download_button(
                    "💾 Télécharger PNG",
                    img_bytes,
                    f"cartographie_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    "image/png",
                    use_container_width=True
                )
    
    with col2:
        if results.get('visualization'):
            if st.button("🎨 Exporter en SVG", use_container_width=True):
                # Exporter en SVG
                svg_str = results['visualization'].to_image(format="svg").decode()
                st.download_button(
                    "💾 Télécharger SVG",
                    svg_str,
                    f"cartographie_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                    "image/svg+xml",
                    use_container_width=True
                )
    
    with col3:
        if results.get('visualization'):
            if st.button("📄 Exporter HTML interactif", use_container_width=True):
                # Exporter en HTML interactif
                html_str = results['visualization'].to_html(include_plotlyjs='cdn')
                st.download_button(
                    "💾 Télécharger HTML",
                    html_str,
                    f"cartographie_{results['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    "text/html",
                    use_container_width=True
                )

def export_to_json(results):
    """Exporte les résultats en JSON"""
    export_data = {
        'metadata': {
            'type': results['type'],
            'timestamp': results['timestamp'].isoformat(),
            'document_count': results['document_count'],
            'config': results['config']
        },
        'entities': [
            {
                'name': e.name,
                'type': e.type,
                'mentions_count': e.mentions_count,
                'attributes': e.attributes
            } for e in results['entities']
        ],
        'relationships': [
            {
                'source': r.source,
                'target': r.target,
                'type': r.type,
                'strength': r.strength,
                'direction': r.direction,
                'evidence': r.evidence
            } for r in results['relationships']
        ],
        'analysis': {
            k: v for k, v in results['analysis'].items()
            if isinstance(v, (int, float, str, list))
        }
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def export_to_graphml(results):
    """Exporte le réseau au format GraphML"""
    
    # Recréer le graphe
    G = nx.DiGraph()
    
    # Ajouter les nœuds
    for entity in results['entities']:
        G.add_node(
            entity.name,
            type=entity.type,
            mentions=entity.mentions_count
        )
    
    # Ajouter les arêtes
    for rel in results['relationships']:
        G.add_edge(
            rel.source,
            rel.target,
            type=rel.type,
            weight=rel.strength
        )
    
    # Exporter en GraphML
    import io
    buffer = io.StringIO()
    nx.write_graphml(G, buffer)
    return buffer.getvalue()

# ===== FONCTIONS UTILITAIRES DU MODULE ORIGINAL =====

def extract_entities_and_relationships(documents: List[Dict[str, Any]], config: dict) -> Tuple[List[Entity], List[Relationship]]:
    """Extrait les entités et relations des documents"""
    
    all_entities = {}  # nom -> Entity
    all_relationships = []
    
    for doc in documents:
        # Extraire les entités du document
        doc_entities = extract_document_entities(doc, config)
        
        # Fusionner avec les entités existantes
        for entity in doc_entities:
            if entity.name in all_entities:
                # Fusionner les informations
                existing = all_entities[entity.name]
                existing.mentions_count += entity.mentions_count
                existing.aliases.extend(entity.aliases)
                existing.aliases = list(set(existing.aliases))
            else:
                all_entities[entity.name] = entity
        
        # Extraire les relations
        doc_relationships = extract_document_relationships(doc, doc_entities, config)
        all_relationships.extend(doc_relationships)
    
    # Consolider les relations
    consolidated_relationships = consolidate_relationships(all_relationships)
    
    return list(all_entities.values()), consolidated_relationships

def extract_document_entities(doc: Dict[str, Any], config: dict) -> List[Entity]:
    """Extrait les entités d'un document"""
    
    content = doc['content']
    entities = []
    
    # Utiliser la fonction helper pour extraire les entités de base
    basic_entities = extract_entities(content)
    
    # Convertir en objets Entity selon le type de mapping
    if config['mapping_type'] in ['personnes', 'complete']:
        for person in basic_entities.get('persons', []):
            entity = Entity(
                name=person,
                type='person',
                mentions_count=content.count(person),
                first_mention=doc.get('title', 'Document')
            )
            entities.append(entity)
    
    if config['mapping_type'] in ['societes', 'complete', 'flux_financiers']:
        for org in basic_entities.get('organizations', []):
            entity = Entity(
                name=org,
                type='company',
                mentions_count=content.count(org),
                first_mention=doc.get('title', 'Document')
            )
            entities.append(entity)
    
    # Extraction spécifique selon le type
    if config['mapping_type'] == 'flux_financiers':
        # Extraire les comptes bancaires
        account_pattern = r'\b(?:compte|IBAN|RIB)\s*:?\s*([A-Z0-9]+)'
        accounts = re.findall(account_pattern, content)
        for account in accounts:
            entity = Entity(
                name=f"Compte {account[:8]}...",
                type='account',
                mentions_count=1,
                first_mention=doc.get('title', 'Document')
            )
            entities.append(entity)
    
    return entities

def extract_document_relationships(doc: Dict[str, Any], entities: List[Entity], config: dict) -> List[Relationship]:
    """Extrait les relations d'un document"""
    
    content = doc['content']
    relationships = []
    
    # Créer un mapping nom -> entité
    entity_map = {e.name.lower(): e for e in entities}
    
    # Patterns de relations selon le type
    relation_patterns = get_relation_patterns(config['mapping_type'])
    
    for pattern_info in relation_patterns:
        pattern = pattern_info['pattern']
        rel_type = pattern_info['type']
        
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            # Extraire les entités de la relation
            source_entity, target_entity = extract_entities_from_match(match, entity_map, entities)
            
            if source_entity and target_entity:
                relationship = Relationship(
                    source=source_entity.name,
                    target=target_entity.name,
                    type=rel_type,
                    strength=calculate_relationship_strength(match.group(0), doc),
                    evidence=[doc.get('title', 'Document')]
                )
                relationships.append(relationship)
    
    # Relations de proximité
    proximity_relationships = extract_proximity_relationships(content, entities, config)
    relationships.extend(proximity_relationships)
    
    return relationships

def get_relation_patterns(mapping_type: str) -> List[Dict[str, Any]]:
    """Retourne les patterns de relations selon le type de mapping"""
    
    patterns = {
        'complete': [
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:est|était)\s+(?:le|la|l\')\s+(\w+)\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'hierarchical'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+et\s+(\w+(?:\s+\w+)*)\s+ont\s+(?:signé|conclu)',
                'type': 'contractual'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:verse|transfère|paie)\s+.*\s+à\s+(\w+(?:\s+\w+)*)',
                'type': 'financial'
            }
        ],
        'personnes': [
            {
                'pattern': r'(\w+\s+\w+)\s+(?:époux|épouse|conjoint|marié)',
                'type': 'familial'
            },
            {
                'pattern': r'(\w+\s+\w+)\s+(?:fils|fille|enfant|parent)\s+de\s+(\w+\s+\w+)',
                'type': 'familial'
            },
            {
                'pattern': r'(\w+\s+\w+)\s+(?:associé|partenaire)\s+(?:de|avec)\s+(\w+\s+\w+)',
                'type': 'business'
            }
        ],
        'societes': [
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:filiale|succursale)\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'subsidiary'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:détient|possède|contrôle)\s+.*\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'ownership'
            },
            {
                'pattern': r'fusion\s+(?:entre|de)\s+(\w+(?:\s+\w+)*)\s+et\s+(\w+(?:\s+\w+)*)',
                'type': 'merger'
            }
        ],
        'flux_financiers': [
            {
                'pattern': r'virement\s+de\s+([0-9,.\s]+)\s*€?\s+(?:de|depuis)\s+(\w+(?:\s+\w+)*)\s+(?:à|vers)\s+(\w+(?:\s+\w+)*)',
                'type': 'transfer'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:doit|verse|paie)\s+([0-9,.\s]+)\s*€?\s+à\s+(\w+(?:\s+\w+)*)',
                'type': 'payment'
            }
        ],
        'hierarchique': [
            {
                'pattern': r'(\w+\s+\w+)\s+(?:directeur|président|gérant)\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'manages'
            },
            {
                'pattern': r'(\w+\s+\w+)\s+(?:employé|salarié|travaille)\s+(?:chez|pour)\s+(\w+(?:\s+\w+)*)',
                'type': 'employed_by'
            }
        ]
    }
    
    return patterns.get(mapping_type, patterns['complete'])

def extract_entities_from_match(match, entity_map: Dict[str, Entity], all_entities: List[Entity]) -> Tuple[Optional[Entity], Optional[Entity]]:
    """Extrait les entités source et cible d'un match de pattern"""
    
    groups = match.groups()
    if len(groups) < 2:
        return None, None
    
    # Chercher les entités dans les groupes
    source_text = groups[0].lower() if groups[0] else ""
    target_text = groups[-1].lower() if groups[-1] else ""
    
    source_entity = None
    target_entity = None
    
    # Recherche exacte d'abord
    source_entity = entity_map.get(source_text)
    target_entity = entity_map.get(target_text)
    
    # Si pas trouvé, recherche partielle
    if not source_entity:
        for entity in all_entities:
            if source_text in entity.name.lower() or entity.name.lower() in source_text:
                source_entity = entity
                break
    
    if not target_entity:
        for entity in all_entities:
            if target_text in entity.name.lower() or entity.name.lower() in target_text:
                target_entity = entity
                break
    
    return source_entity, target_entity

def extract_proximity_relationships(content: str, entities: List[Entity], config: dict) -> List[Relationship]:
    """Extrait les relations basées sur la proximité dans le texte"""
    
    relationships = []
    
    # Paramètres de proximité
    window_size = 100  # caractères
    min_occurrences = 2  # minimum d'occurrences proches
    
    # Trouver les positions de chaque entité
    entity_positions = {}
    for entity in entities:
        positions = []
        for match in re.finditer(re.escape(entity.name), content, re.IGNORECASE):
            positions.append(match.start())
        entity_positions[entity.name] = positions
    
    # Analyser les proximités
    for i, entity1 in enumerate(entities):
        for entity2 in entities[i+1:]:
            if entity1.name == entity2.name:
                continue
            
            # Compter les occurrences proches
            close_occurrences = 0
            
            for pos1 in entity_positions[entity1.name]:
                for pos2 in entity_positions[entity2.name]:
                    if abs(pos1 - pos2) <= window_size:
                        close_occurrences += 1
            
            if close_occurrences >= min_occurrences:
                relationship = Relationship(
                    source=entity1.name,
                    target=entity2.name,
                    type='proximity',
                    strength=min(close_occurrences / 10, 1.0),
                    evidence=[f"Proximité textuelle ({close_occurrences} occurrences)"]
                )
                relationships.append(relationship)
    
    return relationships

def calculate_relationship_strength(context: str, doc: Dict[str, Any]) -> float:
    """Calcule la force d'une relation"""
    
    strength = 0.5  # Base
    
    # Mots renforçant la relation
    strong_words = ['principal', 'majoritaire', 'exclusif', 'unique', 'total', 'complet']
    weak_words = ['possible', 'éventuel', 'partiel', 'minoritaire', 'accessoire']
    
    context_lower = context.lower()
    
    for word in strong_words:
        if word in context_lower:
            strength += 0.1
    
    for word in weak_words:
        if word in context_lower:
            strength -= 0.1
    
    # Montants élevés renforcent les relations financières
    amounts = re.findall(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*€', context)
    if amounts:
        for amount_str in amounts:
            try:
                amount = float(amount_str.replace('.', '').replace(',', '.'))
                if amount > 100000:
                    strength += 0.2
            except:
                pass
    
    return max(0.1, min(1.0, strength))

def consolidate_relationships(relationships: List[Relationship]) -> List[Relationship]:
    """Consolide les relations dupliquées"""
    
    # Grouper les relations identiques
    rel_groups = defaultdict(list)
    
    for rel in relationships:
        # Clé normalisée (ignorer la direction pour certains types)
        if rel.type in ['contractual', 'business', 'proximity']:
            key = tuple(sorted([rel.source, rel.target])) + (rel.type,)
        else:
            key = (rel.source, rel.target, rel.type)
        
        rel_groups[key].append(rel)
    
    # Consolider
    consolidated = []
    
    for key, group in rel_groups.items():
        if len(group) == 1:
            consolidated.append(group[0])
        else:
            # Fusionner les relations
            merged = Relationship(
                source=group[0].source,
                target=group[0].target,
                type=group[0].type,
                strength=sum(r.strength for r in group) / len(group),
                direction=group[0].direction,
                evidence=list(set(sum([r.evidence for r in group], [])))
            )
            consolidated.append(merged)
    
    return consolidated

def parse_ai_mapping_response(response: str) -> Tuple[List[Entity], List[Relationship]]:
    """Parse la réponse de l'IA pour extraire entités et relations"""
    
    entities = []
    relationships = []
    
    lines = response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if 'ENTITÉ' in line.upper():
            current_section = 'entities'
        elif 'RELATION' in line.upper():
            current_section = 'relationships'
        elif current_section == 'entities' and line.startswith('-'):
            # Parser une entité
            entity_match = re.match(r'-\s*([^:]+):\s*(.+)', line)
            if entity_match:
                name = entity_match.group(1).strip()
                details = entity_match.group(2).strip()
                
                # Déterminer le type
                entity_type = 'person' if any(word in details.lower() for word in ['directeur', 'président', 'gérant']) else 'company'
                
                entities.append(Entity(
                    name=name,
                    type=entity_type,
                    attributes={'details': details}
                ))
        
        elif current_section == 'relationships' and '->' in line:
            # Parser une relation
            rel_match = re.match(r'([^->]+)\s*->\s*([^:]+):\s*(.+)', line)
            if rel_match:
                source = rel_match.group(1).strip()
                target = rel_match.group(2).strip()
                rel_type = rel_match.group(3).strip()
                
                relationships.append(Relationship(
                    source=source,
                    target=target,
                    type=rel_type,
                    strength=0.7
                ))
    
    return entities, relationships

def merge_entities(existing: List[Entity], new: List[Entity]) -> List[Entity]:
    """Fusionne les listes d'entités"""
    
    entity_map = {e.name.lower(): e for e in existing}
    
    for new_entity in new:
        key = new_entity.name.lower()
        if key in entity_map:
            # Fusionner les attributs
            entity_map[key].attributes.update(new_entity.attributes)
        else:
            entity_map[key] = new_entity
    
    return list(entity_map.values())

def filter_mapping_data(entities: List[Entity], relationships: List[Relationship], 
                       config: dict) -> Tuple[List[Entity], List[Relationship]]:
    """Filtre les données selon la configuration"""
    
    # Filtrer les entités
    filtered_entities = entities
    
    # Par type
    if config.get('entity_types'):
        filtered_entities = [e for e in filtered_entities if e.type in config['entity_types']]
    
    # Exclure certaines entités
    if config.get('exclude_entities'):
        exclude_list = [e.strip().lower() for e in config['exclude_entities'].split('\n') if e.strip()]
        filtered_entities = [e for e in filtered_entities if e.name.lower() not in exclude_list]
    
    # Focus sur certaines entités
    if config.get('focus_entities'):
        focus_list = [e.strip().lower() for e in config['focus_entities'].split(',') if e.strip()]
        if focus_list:
            # Garder les entités focus et leurs voisins directs
            focus_entities = {e.name for e in filtered_entities if e.name.lower() in focus_list}
            
            # Ajouter les voisins
            for rel in relationships:
                if rel.source in focus_entities:
                    focus_entities.add(rel.target)
                if rel.target in focus_entities:
                    focus_entities.add(rel.source)
            
            filtered_entities = [e for e in filtered_entities if e.name in focus_entities]
    
    # Filtrer les relations
    entity_names = {e.name for e in filtered_entities}
    filtered_relationships = [
        r for r in relationships 
        if r.source in entity_names and r.target in entity_names
        and r.strength >= config.get('min_strength', 0)
    ]
    
    return filtered_entities, filtered_relationships

def analyze_network(entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
    """Analyse le réseau avec NetworkX"""
    
    # Créer le graphe
    G = nx.Graph() if any(r.direction == 'bidirectional' for r in relationships) else nx.DiGraph()
    
    # Ajouter les nœuds
    for entity in entities:
        G.add_node(entity.name, **entity.attributes, type=entity.type)
    
    # Ajouter les arêtes
    for rel in relationships:
        if rel.direction == 'bidirectional' or isinstance(G, nx.Graph):
            G.add_edge(rel.source, rel.target, weight=rel.strength, type=rel.type)
        else:
            G.add_edge(rel.source, rel.target, weight=rel.strength, type=rel.type)
    
    # Analyses
    analysis = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'density': nx.density(G),
        'components': list(nx.connected_components(G.to_undirected())) if isinstance(G, nx.DiGraph) else list(nx.connected_components(G)),
        'is_connected': nx.is_connected(G.to_undirected()) if isinstance(G, nx.DiGraph) else nx.is_connected(G)
    }
    
    # Centralités
    try:
        analysis['degree_centrality'] = nx.degree_centrality(G)
        analysis['betweenness_centrality'] = nx.betweenness_centrality(G)
        
        if isinstance(G, nx.DiGraph):
            analysis['in_degree_centrality'] = nx.in_degree_centrality(G)
            analysis['out_degree_centrality'] = nx.out_degree_centrality(G)
    except:
        pass
    
    # Acteurs clés (top 5 par centralité)
    if 'degree_centrality' in analysis:
        sorted_centrality = sorted(analysis['degree_centrality'].items(), key=lambda x: x[1], reverse=True)
        analysis['key_players'] = [node for node, _ in sorted_centrality[:5]]
    
    # Communautés
    try:
        if isinstance(G, nx.Graph):
            communities = nx.community.greedy_modularity_communities(G)
            analysis['communities'] = [list(c) for c in communities]
            analysis['modularity'] = nx.community.modularity(G, communities)
    except:
        pass
    
    # Chemins
    if G.number_of_nodes() > 1:
        try:
            if nx.is_connected(G.to_undirected() if isinstance(G, nx.DiGraph) else G):
                analysis['average_shortest_path'] = nx.average_shortest_path_length(G)
                analysis['diameter'] = nx.diameter(G.to_undirected() if isinstance(G, nx.DiGraph) else G)
        except:
            pass
    
    return analysis

def basic_network_analysis(entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
    """Analyse basique du réseau sans NetworkX"""
    
    # Compter les connexions par entité
    connections = defaultdict(int)
    for rel in relationships:
        connections[rel.source] += 1
        connections[rel.target] += 1
    
    # Acteurs clés (plus de connexions)
    sorted_connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'node_count': len(entities),
        'edge_count': len(relationships),
        'density': len(relationships) / (len(entities) * (len(entities) - 1) / 2) if len(entities) > 1 else 0,
        'key_players': [node for node, _ in sorted_connections[:5]],
        'components': [],  # Non calculé sans NetworkX
        'is_connected': None
    }

def create_network_visualization(entities: List[Entity], relationships: List[Relationship], 
                                config: dict, analysis: Dict[str, Any]) -> go.Figure:
    """Crée la visualisation du réseau avec Plotly"""
    
    # Calculer les positions des nœuds
    pos = calculate_node_positions(entities, relationships, config['layout'])
    
    # Préparer les données pour Plotly
    edge_trace = create_edge_trace(relationships, pos)
    node_trace = create_node_trace(entities, pos, config, analysis)
    
    # Créer la figure
    fig = go.Figure(data=[edge_trace, node_trace])
    
    # Mise en forme
    fig.update_layout(
        title=f"Cartographie {config['mapping_type'].replace('_', ' ').title()}",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    # Ajouter les labels si demandé
    if config.get('show_labels'):
        for entity, (x, y) in pos.items():
            fig.add_annotation(
                x=x, y=y,
                text=entity,
                showarrow=False,
                font=dict(size=10)
            )
    
    return fig

def calculate_node_positions(entities: List[Entity], relationships: List[Relationship], layout: str) -> Dict[str, Tuple[float, float]]:
    """Calcule les positions des nœuds selon le layout"""

    # Créer un graphe NetworkX temporaire
    G = nx.Graph()
    G.add_nodes_from([e.name for e in entities])
    G.add_edges_from([(r.source, r.target) for r in relationships])

    # Calculer les positions selon le layout
    if layout == 'spring':
        pos = nx.spring_layout(G, k=1, iterations=50)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'hierarchical':
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except Exception:
            pos = nx.spring_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G)
    
    return pos

def create_edge_trace(relationships: List[Relationship], pos: Dict[str, Tuple[float, float]]) -> go.Scatter:
    """Crée le trace des arêtes pour Plotly"""
    
    edge_x = []
    edge_y = []
    
    for rel in relationships:
        if rel.source in pos and rel.target in pos:
            x0, y0 = pos[rel.source]
            x1, y1 = pos[rel.target]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    return edge_trace

def create_node_trace(entities: List[Entity], pos: Dict[str, Tuple[float, float]], 
                     config: dict, analysis: Dict[str, Any]) -> go.Scatter:
    """Crée le trace des nœuds pour Plotly"""
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    
    # Couleurs par défaut
    type_colors = {
        'person': '#FF6B6B',
        'company': '#4ECDC4',
        'organization': '#45B7D1',
        'account': '#96CEB4',
        'other': '#DDA0DD'
    }
    
    for entity in entities:
        if entity.name in pos:
            x, y = pos[entity.name]
            node_x.append(x)
            node_y.append(y)
            
            # Texte du hover
            text = f"<b>{entity.name}</b><br>"
            text += f"Type: {entity.type}<br>"
            text += f"Mentions: {entity.mentions_count}"
            node_text.append(text)
            
            # Couleur selon la configuration
            if config['color_by'] == 'type':
                color = type_colors.get(entity.type, '#DDA0DD')
            elif config['color_by'] == 'centrality' and 'degree_centrality' in analysis:
                # Gradient selon la centralité
                centrality = analysis['degree_centrality'].get(entity.name, 0)
                color = centrality * 100  # Pour la colorscale
            else:
                color = '#1f77b4'
            
            node_color.append(color)
            
            # Taille selon les mentions ou la centralité
            if 'degree_centrality' in analysis:
                size = 10 + analysis['degree_centrality'].get(entity.name, 0) * 50
            else:
                size = 10 + min(entity.mentions_count, 20) * 2
            
            node_size.append(size)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=config['color_by'] == 'centrality',
            colorscale='Viridis',
            size=node_size,
            color=node_color,
            line_width=2,
            colorbar=dict(
                thickness=15,
                title='Centralité',
                xanchor='left',
                titleside='right'
            ) if config['color_by'] == 'centrality' else None
        )
    )
    
    return node_trace

def generate_mapping_report(mapping_result: Dict[str, Any]) -> str:
    """Génère un rapport textuel de la cartographie"""
    
    report = f"RAPPORT DE CARTOGRAPHIE - {mapping_result['type'].upper()}\n"
    report += "=" * 60 + "\n\n"
    
    report += f"Généré le : {mapping_result['timestamp'].strftime('%d/%m/%Y à %H:%M')}\n"
    report += f"Documents analysés : {mapping_result['document_count']}\n\n"
    
    # Résumé
    analysis = mapping_result['analysis']
    report += "RÉSUMÉ DU RÉSEAU\n"
    report += "-" * 30 + "\n"
    report += f"Nombre d'entités : {analysis['node_count']}\n"
    report += f"Nombre de relations : {analysis['edge_count']}\n"
    report += f"Densité du réseau : {analysis['density']:.2%}\n"
    report += f"Réseau connecté : {'Oui' if analysis.get('is_connected') else 'Non (fragmenté)'}\n\n"
    
    # Acteurs clés
    if 'key_players' in analysis:
        report += "ACTEURS PRINCIPAUX\n"
        report += "-" * 30 + "\n"
        for i, player in enumerate(analysis['key_players'], 1):
            report += f"{i}. {player}\n"
        report += "\n"
    
    # Entités par type
    type_counts = Counter(e.type for e in mapping_result['entities'])
    report += "RÉPARTITION DES ENTITÉS\n"
    report += "-" * 30 + "\n"
    for entity_type, count in type_counts.items():
        report += f"{entity_type.title()} : {count}\n"
    report += "\n"
    
    # Relations par type
    rel_type_counts = Counter(r.type for r in mapping_result['relationships'])
    report += "TYPES DE RELATIONS\n"
    report += "-" * 30 + "\n"
    for rel_type, count in rel_type_counts.items():
        report += f"{rel_type.replace('_', ' ').title()} : {count}\n"
    report += "\n"
    
    # Communautés détectées
    if 'communities' in analysis and analysis['communities']:
        report += "COMMUNAUTÉS DÉTECTÉES\n"
        report += "-" * 30 + "\n"
        for i, community in enumerate(analysis['communities'], 1):
            report += f"Communauté {i} : {len(community)} membres\n"
            report += f"Membres : {', '.join(list(community)[:5])}"
            if len(community) > 5:
                report += "..."
            report += "\n\n"
    
    return report

def export_mapping_to_excel(mapping_result: Dict[str, Any]) -> bytes:
    """Exporte la cartographie vers Excel"""
    
    import io
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Feuille des entités
        entities_data = []
        for entity in mapping_result['entities']:
            entities_data.append({
                'Nom': entity.name,
                'Type': entity.type,
                'Mentions': entity.mentions_count,
                'Première mention': entity.first_mention or '',
                'Centralité': mapping_result['analysis'].get('degree_centrality', {}).get(entity.name, 0)
            })
        
        df_entities = pd.DataFrame(entities_data)
        df_entities.to_excel(writer, sheet_name='Entités', index=False)
        
        # Feuille des relations
        relations_data = []
        for rel in mapping_result['relationships']:
            relations_data.append({
                'Source': rel.source,
                'Cible': rel.target,
                'Type': rel.type,
                'Force': rel.strength,
                'Direction': rel.direction,
                'Sources': ', '.join(rel.evidence) if rel.evidence else ''
            })
        
        df_relations = pd.DataFrame(relations_data)
        df_relations.to_excel(writer, sheet_name='Relations', index=False)
        
        # Feuille d'analyse
        analysis_data = []
        for key, value in mapping_result['analysis'].items():
            if isinstance(value, (int, float, str)):
                analysis_data.append({'Métrique': key, 'Valeur': value})
        
        if analysis_data:
            df_analysis = pd.DataFrame(analysis_data)
            df_analysis.to_excel(writer, sheet_name='Analyse', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

# Point d'entrée pour le lazy loading
if __name__ == "__main__":
    run()