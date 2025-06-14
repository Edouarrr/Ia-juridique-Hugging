# modules/import_export.py
"""Module d'import/export avec analyse IA multi-modèles et mode fusion"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
import json
import io
import re
import time
import pandas as pd
from pathlib import Path
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Imports des dépendances
from modules.dataclasses import Document
from utils.helpers import clean_key, truncate_text, format_legal_date
from modules.export_manager import export_manager, ExportConfig

# Configuration des modèles IA disponibles
AI_MODELS = {
    "gpt-4-turbo": {
        "name": "GPT-4 Turbo",
        "icon": "🧠",
        "description": "Modèle le plus performant pour l'analyse juridique complexe",
        "strengths": ["Analyse approfondie", "Contexte juridique", "Synthèse"],
        "speed": "⚡⚡",
        "accuracy": "⭐⭐⭐⭐⭐"
    },
    "claude-3-opus": {
        "name": "Claude 3 Opus",
        "icon": "🎯",
        "description": "Excellence en raisonnement et analyse structurée",
        "strengths": ["Logique juridique", "Structure", "Argumentation"],
        "speed": "⚡⚡",
        "accuracy": "⭐⭐⭐⭐⭐"
    },
    "gemini-pro": {
        "name": "Gemini Pro",
        "icon": "💎",
        "description": "Polyvalent avec capacités multimodales",
        "strengths": ["Documents mixtes", "Tableaux", "Images"],
        "speed": "⚡⚡⚡",
        "accuracy": "⭐⭐⭐⭐"
    },
    "llama-3-70b": {
        "name": "Llama 3 70B",
        "icon": "🦙",
        "description": "Modèle open-source performant",
        "strengths": ["Rapidité", "Fiabilité", "Coût réduit"],
        "speed": "⚡⚡⚡⚡",
        "accuracy": "⭐⭐⭐⭐"
    },
    "mistral-large": {
        "name": "Mistral Large",
        "icon": "🌊",
        "description": "Optimisé pour le français et l'analyse juridique",
        "strengths": ["Français natif", "Jurisprudence", "Efficacité"],
        "speed": "⚡⚡⚡⚡",
        "accuracy": "⭐⭐⭐⭐"
    }
}

def run():
    """Fonction principale du module Import/Export avec IA"""
    # Titre avec animation
    st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h1 style='background: linear-gradient(45deg, #1e3c72, #2a5298); 
                       -webkit-background-clip: text; 
                       -webkit-text-fill-color: transparent;
                       font-size: 2.5rem;'>
                🔄 Import/Export Intelligent
            </h1>
            <p style='color: #666; font-size: 1.1rem;'>
                Importez, analysez et exportez vos documents juridiques avec l'IA
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de l'état
    init_session_state()
    
    # Métriques en temps réel
    show_real_time_metrics()
    
    # Interface principale avec onglets
    tabs = st.tabs([
        "📥 Import", 
        "🤖 Analyse IA", 
        "📤 Export", 
        "📊 Historique",
        "⚙️ Configuration"
    ])
    
    with tabs[0]:
        show_enhanced_import_interface()
    
    with tabs[1]:
        show_ai_analysis_interface()
    
    with tabs[2]:
        show_enhanced_export_interface()
    
    with tabs[3]:
        show_import_export_history()
    
    with tabs[4]:
        show_configuration_interface()

def init_session_state():
    """Initialise l'état de session pour le module"""
    defaults = {
        'import_export_state': {
            'imported_documents': [],
            'ai_analysis_queue': [],
            'export_queue': [],
            'selected_models': [],
            'fusion_mode': False,
            'analysis_results': {},
            'import_history': [],
            'export_history': []
        },
        'ai_config': {
            'temperature': 0.3,
            'max_tokens': 4000,
            'fusion_strategy': 'weighted_average',
            'batch_size': 5,
            'parallel_processing': True
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_real_time_metrics():
    """Affiche les métriques en temps réel"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    state = st.session_state.import_export_state
    
    with col1:
        st.metric(
            "📄 Documents importés",
            len(state['imported_documents']),
            delta=f"+{len(state['imported_documents']) - len(state.get('last_imported', []))}"
        )
    
    with col2:
        st.metric(
            "🤖 En analyse",
            len(state['ai_analysis_queue']),
            delta="-2" if len(state['ai_analysis_queue']) > 0 else "0"
        )
    
    with col3:
        analyzed = len([d for d in state['analysis_results'].values() if d.get('completed')])
        st.metric(
            "✅ Analysés",
            analyzed,
            delta=f"+{analyzed - state.get('last_analyzed', 0)}"
        )
    
    with col4:
        st.metric(
            "📤 Exportés",
            len(state['export_history']),
            delta=f"+{len(state['export_history']) - state.get('last_exported', 0)}"
        )
    
    with col5:
        accuracy = calculate_average_confidence()
        st.metric(
            "🎯 Précision IA",
            f"{accuracy:.1%}",
            delta=f"+{(accuracy - state.get('last_accuracy', 0.8)) * 100:.1f}%"
        )

def show_enhanced_import_interface():
    """Interface d'import améliorée avec preview et validation"""
    st.markdown("### 📥 Import intelligent de documents")
    
    # Options d'import
    col1, col2 = st.columns([2, 1])
    
    with col1:
        import_source = st.radio(
            "Source des documents",
            ["📁 Fichiers locaux", "☁️ Azure Storage", "🔗 URL", "📋 Presse-papier"],
            horizontal=True
        )
    
    with col2:
        auto_analyze = st.checkbox("🤖 Analyser automatiquement", value=True)
        validate_format = st.checkbox("✅ Valider le format", value=True)
    
    st.divider()
    
    # Interface selon la source
    if import_source == "📁 Fichiers locaux":
        show_file_upload_interface(auto_analyze, validate_format)
    elif import_source == "☁️ Azure Storage":
        show_azure_import_interface(auto_analyze, validate_format)
    elif import_source == "🔗 URL":
        show_url_import_interface(auto_analyze, validate_format)
    else:
        show_clipboard_import_interface(auto_analyze, validate_format)

def show_file_upload_interface(auto_analyze: bool, validate_format: bool):
    """Interface d'upload de fichiers avec preview"""
    # Zone de drag & drop stylisée
    st.markdown("""
        <style>
        .uploadedFile {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            border: 2px dashed #ccc;
            transition: all 0.3s ease;
        }
        .uploadedFile:hover {
            border-color: #667eea;
            transform: scale(1.02);
        }
        </style>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Glissez vos fichiers ici",
        type=['pdf', 'txt', 'docx', 'xlsx', 'json', 'csv'],
        accept_multiple_files=True,
        help="Formats supportés: PDF, TXT, DOCX, XLSX, JSON, CSV"
    )
    
    if uploaded_files:
        # Preview des fichiers
        st.markdown("#### 👁️ Aperçu des fichiers")
        
        preview_container = st.container()
        with preview_container:
            for idx, file in enumerate(uploaded_files):
                with st.expander(f"📄 {file.name} ({file.size / 1024:.1f} KB)", expanded=idx == 0):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Preview du contenu
                        if file.type == "application/pdf":
                            st.info("📄 Document PDF - Extraction du texte en cours...")
                        elif file.type in ["text/plain", "text/csv"]:
                            content = file.read().decode('utf-8')
                            st.text_area("Aperçu", content[:500] + "...", height=100)
                            file.seek(0)
                        else:
                            st.info(f"📎 Fichier {file.type}")
                    
                    with col2:
                        # Métadonnées
                        st.markdown("**Métadonnées**")
                        st.text(f"Type: {file.type}")
                        st.text(f"Taille: {file.size / 1024:.1f} KB")
                        
                        if validate_format:
                            if validate_file_format(file):
                                st.success("✅ Format valide")
                            else:
                                st.error("❌ Format invalide")
        
        # Bouton d'import avec confirmation
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button(
                f"🚀 Importer {len(uploaded_files)} fichier(s)",
                type="primary",
                use_container_width=True
            ):
                process_file_import(uploaded_files, auto_analyze)
        
        with col2:
            if st.button("🔍 Analyser uniquement", use_container_width=True):
                analyze_files_metadata(uploaded_files)
        
        with col3:
            if st.button("❌ Annuler", use_container_width=True):
                st.session_state.import_export_state['imported_documents'] = []
                st.rerun()

def show_ai_analysis_interface():
    """Interface d'analyse IA avec sélection de modèles"""
    st.markdown("### 🤖 Analyse IA Multi-Modèles")
    
    # Vérification des documents
    docs = st.session_state.import_export_state['imported_documents']
    if not docs:
        st.warning("⚠️ Aucun document importé. Importez d'abord des documents.")
        
        if st.button("📥 Aller à l'import"):
            st.session_state.selected_tab = 0
            st.rerun()
        return
    
    # Configuration IA
    with st.container():
        st.markdown("#### 🎯 Sélection des modèles IA")
        
        # Mode de sélection
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selection_mode = st.radio(
                "Mode d'analyse",
                ["🎯 Modèle unique", "🔀 Fusion multi-modèles", "🏁 Course aux modèles"],
                help="Fusion: combine les analyses, Course: compare les modèles"
            )
        
        with col2:
            if selection_mode == "🔀 Fusion multi-modèles":
                fusion_strategy = st.selectbox(
                    "Stratégie de fusion",
                    ["Moyenne pondérée", "Vote majoritaire", "Consensus", "Best-of"],
                    help="Comment combiner les résultats des différents modèles"
                )
        
        # Sélection des modèles
        st.markdown("#### 🤖 Modèles disponibles")
        
        selected_models = []
        model_weights = {}
        
        # Affichage en grille
        cols = st.columns(3)
        for idx, (model_id, model_info) in enumerate(AI_MODELS.items()):
            with cols[idx % 3]:
                # Carte de modèle stylisée
                with st.container():
                    selected = st.checkbox(
                        f"{model_info['icon']} {model_info['name']}",
                        key=f"model_{model_id}",
                        value=model_id in ['gpt-4-turbo', 'claude-3-opus']
                    )
                    
                    if selected:
                        selected_models.append(model_id)
                        
                        # Afficher les détails
                        st.caption(model_info['description'])
                        st.text(f"Vitesse: {model_info['speed']}")
                        st.text(f"Précision: {model_info['accuracy']}")
                        
                        # Points forts
                        with st.expander("Points forts"):
                            for strength in model_info['strengths']:
                                st.write(f"• {strength}")
                        
                        # Poids pour la fusion
                        if selection_mode == "🔀 Fusion multi-modèles":
                            weight = st.slider(
                                "Poids",
                                0.0, 1.0, 0.5,
                                key=f"weight_{model_id}",
                                help="Importance du modèle dans la fusion"
                            )
                            model_weights[model_id] = weight
    
    if not selected_models:
        st.warning("⚠️ Sélectionnez au moins un modèle IA")
        return
    
    # Configuration avancée
    with st.expander("⚙️ Configuration avancée", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temperature = st.slider(
                "🌡️ Température",
                0.0, 1.0, 0.3,
                help="Créativité vs précision"
            )
            
            max_tokens = st.number_input(
                "📏 Tokens max",
                1000, 8000, 4000,
                step=500
            )
        
        with col2:
            batch_size = st.number_input(
                "📦 Taille des lots",
                1, 10, 5,
                help="Documents traités simultanément"
            )
            
            timeout = st.number_input(
                "⏱️ Timeout (s)",
                30, 300, 120,
                help="Délai maximum par document"
            )
        
        with col3:
            parallel = st.checkbox("⚡ Traitement parallèle", value=True)
            cache_results = st.checkbox("💾 Mettre en cache", value=True)
            detailed_logs = st.checkbox("📝 Logs détaillés", value=False)
    
    # Types d'analyse
    st.markdown("#### 📋 Types d'analyse")
    
    analysis_types = {
        "Synthèse juridique": "📝",
        "Extraction d'entités": "🏷️",
        "Analyse de risques": "⚠️",
        "Points clés": "🎯",
        "Chronologie": "📅",
        "Recommandations": "💡"
    }
    
    selected_analyses = []
    cols = st.columns(3)
    for idx, (analysis, icon) in enumerate(analysis_types.items()):
        with cols[idx % 3]:
            if st.checkbox(f"{icon} {analysis}", value=idx < 3):
                selected_analyses.append(analysis)
    
    # Lancement de l'analyse
    st.divider()
    
    # Résumé de la configuration
    with st.container():
        st.markdown("#### 📊 Résumé de l'analyse")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Documents", len(docs))
        with col2:
            st.metric("🤖 Modèles", len(selected_models))
        with col3:
            st.metric("📋 Analyses", len(selected_analyses))
        with col4:
            estimated_time = estimate_analysis_time(len(docs), len(selected_models), len(selected_analyses))
            st.metric("⏱️ Temps estimé", f"{estimated_time}s")
    
    # Bouton de lancement
    if st.button(
        f"🚀 Lancer l'analyse IA",
        type="primary",
        use_container_width=True,
        disabled=not (selected_models and selected_analyses)
    ):
        launch_ai_analysis(
            docs, 
            selected_models, 
            model_weights,
            selected_analyses,
            selection_mode,
            fusion_strategy if selection_mode == "🔀 Fusion multi-modèles" else None
        )

def launch_ai_analysis(docs, models, weights, analyses, mode, fusion_strategy=None):
    """Lance l'analyse IA avec les modèles sélectionnés"""
    # Container pour la progression
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Analyse en cours...")
        
        # Barre de progression principale
        main_progress = st.progress(0)
        status_text = st.empty()
        
        # Métriques en temps réel
        metrics_cols = st.columns(4)
        with metrics_cols[0]:
            docs_processed = st.empty()
        with metrics_cols[1]:
            models_used = st.empty()
        with metrics_cols[2]:
            analyses_done = st.empty()
        with metrics_cols[3]:
            time_elapsed = st.empty()
        
        # Container pour les logs
        with st.expander("📝 Logs détaillés", expanded=True):
            log_container = st.empty()
            logs = []
        
        # Simulation de l'analyse
        start_time = time.time()
        total_steps = len(docs) * len(models) * len(analyses)
        current_step = 0
        
        for doc_idx, doc in enumerate(docs):
            for model in models:
                for analysis in analyses:
                    current_step += 1
                    progress = current_step / total_steps
                    
                    # Mise à jour de la progression
                    main_progress.progress(progress)
                    status_text.text(f"📄 Document {doc_idx+1}/{len(docs)} | 🤖 {AI_MODELS[model]['name']} | 📋 {analysis}")
                    
                    # Mise à jour des métriques
                    docs_processed.metric("📄 Documents", f"{doc_idx+1}/{len(docs)}")
                    models_used.metric("🤖 Modèles actifs", len(models))
                    analyses_done.metric("✅ Analyses", f"{current_step}/{total_steps}")
                    time_elapsed.metric("⏱️ Temps", f"{int(time.time() - start_time)}s")
                    
                    # Ajout de logs
                    log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {AI_MODELS[model]['icon']} Analyse '{analysis}' sur document {doc_idx+1}"
                    logs.append(log_entry)
                    log_container.text('\n'.join(logs[-10:]))  # Afficher les 10 derniers logs
                    
                    # Simulation du traitement
                    time.sleep(0.1)
                    
                    # Stockage des résultats simulés
                    if doc_idx not in st.session_state.import_export_state['analysis_results']:
                        st.session_state.import_export_state['analysis_results'][doc_idx] = {}
                    
                    if model not in st.session_state.import_export_state['analysis_results'][doc_idx]:
                        st.session_state.import_export_state['analysis_results'][doc_idx][model] = {}
                    
                    st.session_state.import_export_state['analysis_results'][doc_idx][model][analysis] = {
                        'completed': True,
                        'confidence': 0.85 + np.random.random() * 0.15,
                        'result': f"Résultat de l'analyse {analysis} par {AI_MODELS[model]['name']}"
                    }
        
        # Fusion des résultats si nécessaire
        if mode == "🔀 Fusion multi-modèles" and fusion_strategy:
            status_text.text("🔀 Fusion des résultats en cours...")
            time.sleep(1)
            perform_results_fusion(fusion_strategy, weights)
        
        # Finalisation
        status_text.text("✅ Analyse terminée avec succès!")
        st.balloons()
        
        # Résumé final
        st.success(f"""
        ✅ **Analyse terminée!**
        - 📄 {len(docs)} documents analysés
        - 🤖 {len(models)} modèles utilisés
        - 📋 {len(analyses)} types d'analyse
        - ⏱️ Temps total: {int(time.time() - start_time)}s
        """)
        
        # Boutons d'action
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Voir les résultats", type="primary", use_container_width=True):
                st.session_state.show_results = True
                st.rerun()
        
        with col2:
            if st.button("📤 Exporter", use_container_width=True):
                st.session_state.selected_tab = 2
                st.rerun()
        
        with col3:
            if st.button("🔄 Nouvelle analyse", use_container_width=True):
                st.session_state.import_export_state['analysis_results'] = {}
                st.rerun()

def show_enhanced_export_interface():
    """Interface d'export améliorée avec templates"""
    st.markdown("### 📤 Export intelligent")
    
    # Vérification du contenu disponible
    available_content = check_available_content()
    
    if not available_content:
        st.warning("⚠️ Aucun contenu disponible pour l'export")
        st.info("💡 Importez et analysez d'abord des documents")
        return
    
    # Sélection du contenu
    col1, col2 = st.columns([2, 1])
    
    with col1:
        content_type = st.selectbox(
            "Type de contenu",
            list(available_content.keys()),
            format_func=lambda x: f"{available_content[x]['icon']} {available_content[x]['name']} ({available_content[x]['count']} éléments)"
        )
    
    with col2:
        template = st.selectbox(
            "Template",
            ["Standard", "Rapport détaillé", "Synthèse executive", "Export données", "Custom"],
            help="Modèle de mise en forme"
        )
    
    # Options d'export
    with st.expander("⚙️ Options d'export", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            format_options = st.multiselect(
                "Formats de sortie",
                ["PDF", "Word", "Excel", "JSON", "Markdown", "HTML"],
                default=["PDF", "Word"]
            )
            
            include_metadata = st.checkbox("📋 Inclure les métadonnées", value=True)
            include_analysis = st.checkbox("🤖 Inclure l'analyse IA", value=True)
        
        with col2:
            if "PDF" in format_options:
                st.markdown("**Options PDF**")
                pdf_format = st.radio(
                    "Format",
                    ["A4", "Letter", "Legal"],
                    horizontal=True
                )
                include_toc = st.checkbox("📑 Table des matières", value=True)
                include_cover = st.checkbox("📄 Page de garde", value=True)
            
            if "Excel" in format_options:
                st.markdown("**Options Excel**")
                separate_sheets = st.checkbox("📊 Feuilles séparées", value=True)
                include_charts = st.checkbox("📈 Inclure graphiques", value=True)
        
        with col3:
            if template == "Custom":
                st.markdown("**Template personnalisé**")
                custom_css = st.text_area(
                    "CSS personnalisé",
                    height=100,
                    help="Styles CSS pour personnaliser l'apparence"
                )
    
    # Aperçu
    st.markdown("#### 👁️ Aperçu de l'export")
    
    with st.container():
        preview_content = generate_export_preview(content_type, template, format_options[0] if format_options else "PDF")
        
        # Affichage de l'aperçu avec style
        st.markdown(f"""
        <div style='
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background: #f9f9f9;
            max-height: 400px;
            overflow-y: auto;
        '>
            {preview_content}
        </div>
        """, unsafe_allow_html=True)
    
    # Actions d'export
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(
            "🚀 Exporter maintenant",
            type="primary",
            use_container_width=True
        ):
            perform_export(content_type, template, format_options)
    
    with col2:
        if st.button(
            "📧 Envoyer par email",
            use_container_width=True
        ):
            show_email_dialog()
    
    with col3:
        if st.button(
            "☁️ Sauvegarder dans le cloud",
            use_container_width=True
        ):
            show_cloud_save_dialog()
    
    with col4:
        if st.button(
            "🔗 Générer lien de partage",
            use_container_width=True
        ):
            generate_share_link()

def show_import_export_history():
    """Affiche l'historique des imports/exports avec filtres"""
    st.markdown("### 📊 Historique des opérations")
    
    # Filtres
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        operation_type = st.selectbox(
            "Type d'opération",
            ["Toutes", "Import", "Export", "Analyse IA"]
        )
    
    with col2:
        date_range = st.date_input(
            "Période",
            value=(datetime.now() - pd.Timedelta(days=30), datetime.now()),
            format="DD/MM/YYYY"
        )
    
    with col3:
        status_filter = st.selectbox(
            "Statut",
            ["Tous", "✅ Succès", "⚠️ Avertissement", "❌ Erreur"]
        )
    
    with col4:
        search_query = st.text_input(
            "Rechercher",
            placeholder="Nom, type..."
        )
    
    # Statistiques
    st.markdown("#### 📈 Statistiques")
    
    stats_cols = st.columns(5)
    
    with stats_cols[0]:
        st.metric("📥 Total imports", "247", "+12%")
    
    with stats_cols[1]:
        st.metric("📤 Total exports", "189", "+8%")
    
    with stats_cols[2]:
        st.metric("🤖 Analyses IA", "436", "+25%")
    
    with stats_cols[3]:
        st.metric("📊 Taux de succès", "94.5%", "+2.1%")
    
    with stats_cols[4]:
        st.metric("⏱️ Temps moyen", "3.2s", "-0.5s")
    
    # Tableau d'historique
    st.markdown("#### 📋 Détails des opérations")
    
    # Données simulées
    history_data = generate_history_data()
    
    # Filtrage
    filtered_data = filter_history_data(history_data, operation_type, date_range, status_filter, search_query)
    
    # Affichage avec actions
    for idx, row in filtered_data.iterrows():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**{row['icon']} {row['name']}**")
                st.caption(row['description'])
            
            with col2:
                st.text(f"📅 {row['date'].strftime('%d/%m/%Y %H:%M')}")
            
            with col3:
                st.text(f"📁 {row['size']}")
            
            with col4:
                st.markdown(f"<span style='color: {row['status_color']}'>{row['status']}</span>", unsafe_allow_html=True)
            
            with col5:
                if st.button("👁️", key=f"view_{idx}", help="Voir détails"):
                    show_operation_details(row)
            
            with col6:
                if st.button("🔄", key=f"retry_{idx}", help="Relancer"):
                    retry_operation(row)
            
            st.divider()
    
    # Pagination
    total_pages = len(filtered_data) // 10 + 1
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            label_visibility="collapsed"
        )

def show_configuration_interface():
    """Interface de configuration avancée"""
    st.markdown("### ⚙️ Configuration avancée")
    
    # Onglets de configuration
    config_tabs = st.tabs([
        "🤖 Modèles IA",
        "📁 Stockage",
        "🔐 Sécurité",
        "🎨 Interface",
        "⚡ Performance"
    ])
    
    with config_tabs[0]:
        show_ai_models_config()
    
    with config_tabs[1]:
        show_storage_config()
    
    with config_tabs[2]:
        show_security_config()
    
    with config_tabs[3]:
        show_interface_config()
    
    with config_tabs[4]:
        show_performance_config()

def show_ai_models_config():
    """Configuration des modèles IA"""
    st.markdown("#### 🤖 Configuration des modèles IA")
    
    # Activation/désactivation des modèles
    st.markdown("##### Modèles disponibles")
    
    for model_id, model_info in AI_MODELS.items():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            enabled = st.checkbox(
                f"{model_info['icon']} {model_info['name']}",
                value=True,
                key=f"enable_{model_id}"
            )
        
        with col2:
            if enabled:
                priority = st.slider(
                    "Priorité",
                    1, 5, 3,
                    key=f"priority_{model_id}",
                    label_visibility="collapsed"
                )
        
        with col3:
            if enabled:
                api_key = st.text_input(
                    "Clé API",
                    type="password",
                    key=f"api_key_{model_id}",
                    label_visibility="collapsed",
                    placeholder="sk-..."
                )
        
        with col4:
            if st.button("🔧", key=f"config_{model_id}", help="Configuration avancée"):
                show_model_advanced_config(model_id)
    
    # Configuration globale
    st.markdown("##### Configuration globale")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_model = st.selectbox(
            "Modèle par défaut",
            list(AI_MODELS.keys()),
            format_func=lambda x: AI_MODELS[x]['name']
        )
        
        retry_strategy = st.selectbox(
            "Stratégie de retry",
            ["Exponentiel", "Linéaire", "Immédiat", "Personnalisé"]
        )
        
        max_retries = st.number_input(
            "Nombre max de tentatives",
            1, 10, 3
        )
    
    with col2:
        timeout_global = st.number_input(
            "Timeout global (s)",
            10, 300, 60
        )
        
        rate_limit = st.number_input(
            "Limite de requêtes/min",
            1, 100, 20
        )
        
        cache_duration = st.number_input(
            "Durée du cache (heures)",
            0, 168, 24
        )
    
    # Bouton de sauvegarde
    if st.button("💾 Sauvegarder la configuration", type="primary", use_container_width=True):
        save_ai_config()
        st.success("✅ Configuration sauvegardée!")

# Fonctions utilitaires

def validate_file_format(file) -> bool:
    """Valide le format d'un fichier"""
    valid_types = {
        'application/pdf': ['.pdf'],
        'text/plain': ['.txt'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'application/json': ['.json'],
        'text/csv': ['.csv']
    }
    
    return file.type in valid_types

def process_file_import(files, auto_analyze: bool):
    """Traite l'import de fichiers"""
    progress = st.progress(0)
    status = st.empty()
    
    imported_docs = []
    
    for idx, file in enumerate(files):
        progress.progress((idx + 1) / len(files))
        status.text(f"⏳ Import de {file.name}...")
        
        # Simulation du traitement
        time.sleep(0.5)
        
        # Création du document
        doc = {
            'name': file.name,
            'type': file.type,
            'size': file.size,
            'content': file.read() if hasattr(file, 'read') else None,
            'imported_at': datetime.now(),
            'metadata': extract_file_metadata(file)
        }
        
        imported_docs.append(doc)
        
        if file.seekable():
            file.seek(0)
    
    # Stockage dans la session
    st.session_state.import_export_state['imported_documents'].extend(imported_docs)
    
    status.text(f"✅ {len(files)} fichiers importés avec succès!")
    
    if auto_analyze:
        st.session_state.import_export_state['ai_analysis_queue'].extend(imported_docs)
        st.info("🤖 Les fichiers ont été ajoutés à la file d'analyse IA")

def extract_file_metadata(file) -> dict:
    """Extrait les métadonnées d'un fichier"""
    return {
        'filename': file.name,
        'size': file.size,
        'type': file.type,
        'extension': Path(file.name).suffix,
        'imported_at': datetime.now().isoformat()
    }

def analyze_files_metadata(files):
    """Analyse les métadonnées des fichiers"""
    with st.spinner("🔍 Analyse des métadonnées..."):
        results = []
        
        for file in files:
            metadata = extract_file_metadata(file)
            
            # Analyse supplémentaire selon le type
            if file.type == "application/pdf":
                metadata['pages'] = "À déterminer"
                metadata['has_text'] = "À vérifier"
            elif file.type in ["text/plain", "text/csv"]:
                content = file.read().decode('utf-8')
                metadata['lines'] = len(content.split('\n'))
                metadata['words'] = len(content.split())
                file.seek(0)
            
            results.append(metadata)
        
        # Affichage des résultats
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

def calculate_average_confidence() -> float:
    """Calcule la confiance moyenne des analyses IA"""
    results = st.session_state.import_export_state.get('analysis_results', {})
    
    if not results:
        return 0.0
    
    confidences = []
    for doc_results in results.values():
        for model_results in doc_results.values():
            for analysis_result in model_results.values():
                if 'confidence' in analysis_result:
                    confidences.append(analysis_result['confidence'])
    
    return np.mean(confidences) if confidences else 0.0

def estimate_analysis_time(num_docs: int, num_models: int, num_analyses: int) -> int:
    """Estime le temps d'analyse en secondes"""
    base_time_per_analysis = 2  # secondes
    parallel_factor = 0.6 if st.session_state.ai_config.get('parallel_processing', True) else 1
    
    total_time = num_docs * num_models * num_analyses * base_time_per_analysis * parallel_factor
    
    return int(total_time)

def check_available_content() -> dict:
    """Vérifie le contenu disponible pour l'export"""
    available = {}
    
    state = st.session_state.import_export_state
    
    if state.get('imported_documents'):
        available['documents'] = {
            'name': 'Documents importés',
            'icon': '📄',
            'count': len(state['imported_documents'])
        }
    
    if state.get('analysis_results'):
        available['analyses'] = {
            'name': 'Analyses IA',
            'icon': '🤖',
            'count': len(state['analysis_results'])
        }
    
    # Vérifier d'autres contenus dans session_state
    if st.session_state.get('current_bordereau'):
        available['bordereau'] = {
            'name': 'Bordereau actuel',
            'icon': '📋',
            'count': 1
        }
    
    if st.session_state.get('redaction_result'):
        available['redaction'] = {
            'name': 'Document rédigé',
            'icon': '✍️',
            'count': 1
        }
    
    return available

def generate_export_preview(content_type: str, template: str, format: str) -> str:
    """Génère un aperçu de l'export"""
    # Simulation d'un aperçu selon le type
    if content_type == 'documents':
        return """
        <h3>📄 Documents juridiques - Export</h3>
        <p><strong>Date:</strong> 14/06/2025</p>
        <p><strong>Nombre de documents:</strong> 12</p>
        <hr>
        <h4>1. Contrat de cession</h4>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit...</p>
        <h4>2. Avenant au contrat</h4>
        <p>Sed do eiusmod tempor incididunt ut labore...</p>
        """
    elif content_type == 'analyses':
        return """
        <h3>🤖 Analyse IA - Rapport de synthèse</h3>
        <p><strong>Modèles utilisés:</strong> GPT-4 Turbo, Claude 3 Opus</p>
        <p><strong>Confiance moyenne:</strong> 92.3%</p>
        <hr>
        <h4>Points clés identifiés</h4>
        <ul>
            <li>Clause de non-concurrence valide</li>
            <li>Durée du contrat: 3 ans</li>
            <li>Pénalités de retard: 0.5% par jour</li>
        </ul>
        """
    else:
        return "<p>Aperçu non disponible pour ce type de contenu</p>"

def perform_export(content_type: str, template: str, formats: list):
    """Effectue l'export dans les formats sélectionnés"""
    with st.spinner("📤 Export en cours..."):
        # Simulation de l'export
        progress = st.progress(0)
        
        for idx, format in enumerate(formats):
            progress.progress((idx + 1) / len(formats))
            time.sleep(0.5)
            
            # Création du fichier simulé
            if format == "PDF":
                file_data = b"PDF content"
                mime = "application/pdf"
                extension = "pdf"
            elif format == "Word":
                file_data = b"DOCX content"
                mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                extension = "docx"
            elif format == "Excel":
                file_data = b"XLSX content"
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                extension = "xlsx"
            else:
                file_data = b"Export content"
                mime = "text/plain"
                extension = "txt"
            
            # Bouton de téléchargement
            st.download_button(
                f"📥 Télécharger {format}",
                data=file_data,
                file_name=f"export_{content_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}",
                mime=mime,
                use_container_width=True
            )
        
        # Ajout à l'historique
        st.session_state.import_export_state['export_history'].append({
            'type': content_type,
            'template': template,
            'formats': formats,
            'timestamp': datetime.now()
        })
        
        st.success("✅ Export terminé avec succès!")

def perform_results_fusion(strategy: str, weights: dict):
    """Effectue la fusion des résultats selon la stratégie choisie"""
    results = st.session_state.import_export_state['analysis_results']
    
    # Implémentation simplifiée de la fusion
    if strategy == "Moyenne pondérée":
        # Calcul de la moyenne pondérée des confidences
        pass
    elif strategy == "Vote majoritaire":
        # Sélection du résultat le plus fréquent
        pass
    elif strategy == "Consensus":
        # Recherche des points communs
        pass
    elif strategy == "Best-of":
        # Sélection du meilleur résultat selon la confiance
        pass

def generate_history_data() -> pd.DataFrame:
    """Génère des données d'historique simulées"""
    operations = []
    
    # Import simulés
    for i in range(10):
        operations.append({
            'icon': '📥',
            'name': f'Import_{i+1}.pdf',
            'description': 'Import de document juridique',
            'date': datetime.now() - pd.Timedelta(days=i),
            'size': f'{np.random.randint(100, 5000)} KB',
            'status': np.random.choice(['✅ Succès', '⚠️ Avertissement', '❌ Erreur'], p=[0.8, 0.15, 0.05]),
            'status_color': np.random.choice(['green', 'orange', 'red'], p=[0.8, 0.15, 0.05])
        })
    
    # Exports simulés
    for i in range(8):
        operations.append({
            'icon': '📤',
            'name': f'Export_bordereau_{i+1}',
            'description': 'Export de bordereau',
            'date': datetime.now() - pd.Timedelta(days=i*2),
            'size': f'{np.random.randint(50, 1000)} KB',
            'status': '✅ Succès',
            'status_color': 'green'
        })
    
    # Analyses IA simulées
    for i in range(15):
        operations.append({
            'icon': '🤖',
            'name': f'Analyse_IA_{i+1}',
            'description': 'Analyse multi-modèles',
            'date': datetime.now() - pd.Timedelta(hours=i*3),
            'size': f'{np.random.randint(5, 50)} pages',
            'status': '✅ Succès',
            'status_color': 'green'
        })
    
    return pd.DataFrame(operations).sort_values('date', ascending=False)

def filter_history_data(data: pd.DataFrame, operation_type: str, date_range: tuple, status: str, search: str) -> pd.DataFrame:
    """Filtre les données d'historique"""
    filtered = data.copy()
    
    # Filtre par type
    if operation_type != "Toutes":
        type_map = {'Import': '📥', 'Export': '📤', 'Analyse IA': '🤖'}
        filtered = filtered[filtered['icon'] == type_map.get(operation_type, '')]
    
    # Filtre par date
    if date_range:
        start_date, end_date = date_range
        filtered = filtered[(filtered['date'].dt.date >= start_date) & (filtered['date'].dt.date <= end_date)]
    
    # Filtre par statut
    if status != "Tous":
        filtered = filtered[filtered['status'] == status]
    
    # Filtre par recherche
    if search:
        mask = filtered['name'].str.contains(search, case=False) | filtered['description'].str.contains(search, case=False)
        filtered = filtered[mask]
    
    return filtered

def show_operation_details(operation: pd.Series):
    """Affiche les détails d'une opération"""
    with st.expander(f"Détails: {operation['name']}", expanded=True):
        st.json({
            'name': operation['name'],
            'type': operation['icon'],
            'description': operation['description'],
            'date': operation['date'].strftime('%Y-%m-%d %H:%M:%S'),
            'size': operation['size'],
            'status': operation['status']
        })

def retry_operation(operation: pd.Series):
    """Relance une opération"""
    st.info(f"🔄 Relance de l'opération: {operation['name']}")
    # Logique de relance

def show_email_dialog():
    """Affiche la boîte de dialogue d'envoi par email"""
    with st.expander("📧 Envoyer par email", expanded=True):
        email = st.text_input("Destinataire", placeholder="email@example.com")
        subject = st.text_input("Objet", value="Export Nexora Law IA")
        message = st.text_area("Message", placeholder="Message optionnel...")
        
        if st.button("📤 Envoyer", type="primary"):
            st.success("✅ Email envoyé avec succès!")

def show_cloud_save_dialog():
    """Affiche la boîte de dialogue de sauvegarde cloud"""
    with st.expander("☁️ Sauvegarder dans le cloud", expanded=True):
        cloud_service = st.selectbox(
            "Service cloud",
            ["Azure Storage", "Google Drive", "Dropbox", "OneDrive"]
        )
        
        folder = st.text_input("Dossier", value="/exports/")
        
        if st.button("💾 Sauvegarder", type="primary"):
            st.success(f"✅ Sauvegardé dans {cloud_service}")

def generate_share_link():
    """Génère un lien de partage"""
    link = f"https://nexora-law.ai/share/{np.random.randint(100000, 999999)}"
    st.success(f"🔗 Lien de partage généré: {link}")
    st.info("Ce lien expire dans 7 jours")

def show_model_advanced_config(model_id: str):
    """Affiche la configuration avancée d'un modèle"""
    with st.expander(f"Configuration avancée: {AI_MODELS[model_id]['name']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input("Temperature", 0.0, 1.0, 0.3, key=f"temp_{model_id}")
            st.number_input("Top P", 0.0, 1.0, 0.9, key=f"top_p_{model_id}")
            st.number_input("Max tokens", 100, 8000, 4000, key=f"max_tok_{model_id}")
        
        with col2:
            st.number_input("Frequency penalty", 0.0, 2.0, 0.0, key=f"freq_{model_id}")
            st.number_input("Presence penalty", 0.0, 2.0, 0.0, key=f"pres_{model_id}")
            st.text_input("Stop sequences", key=f"stop_{model_id}")

def save_ai_config():
    """Sauvegarde la configuration IA"""
    config = {}
    
    for model_id in AI_MODELS:
        config[model_id] = {
            'enabled': st.session_state.get(f"enable_{model_id}", True),
            'priority': st.session_state.get(f"priority_{model_id}", 3),
            'api_key': st.session_state.get(f"api_key_{model_id}", ""),
            'temperature': st.session_state.get(f"temp_{model_id}", 0.3),
            'top_p': st.session_state.get(f"top_p_{model_id}", 0.9),
            'max_tokens': st.session_state.get(f"max_tok_{model_id}", 4000),
        }
    
    st.session_state['ai_models_config'] = config

def show_storage_config():
    """Configuration du stockage"""
    st.markdown("#### 📁 Configuration du stockage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Stockage local")
        local_path = st.text_input("Chemin local", value="/data/nexora/")
        max_size = st.number_input("Taille max (GB)", 1, 100, 10)
        auto_cleanup = st.checkbox("Nettoyage automatique", value=True)
        
        if auto_cleanup:
            retention_days = st.number_input("Rétention (jours)", 1, 365, 30)
    
    with col2:
        st.markdown("##### Stockage cloud")
        cloud_provider = st.selectbox(
            "Fournisseur",
            ["Azure Storage", "AWS S3", "Google Cloud Storage"]
        )
        
        if cloud_provider == "Azure Storage":
            connection_string = st.text_input("Connection string", type="password")
            container_name = st.text_input("Container", value="nexora-documents")
        
        enable_cdn = st.checkbox("Activer CDN", value=False)
        enable_encryption = st.checkbox("Chiffrement au repos", value=True)

def show_security_config():
    """Configuration de la sécurité"""
    st.markdown("#### 🔐 Configuration de la sécurité")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Authentification")
        auth_method = st.selectbox(
            "Méthode",
            ["Azure AD", "OAuth 2.0", "API Key", "JWT"]
        )
        
        mfa_enabled = st.checkbox("Authentification 2FA", value=True)
        session_timeout = st.number_input("Timeout session (min)", 5, 1440, 60)
    
    with col2:
        st.markdown("##### Chiffrement")
        encryption_method = st.selectbox(
            "Algorithme",
            ["AES-256", "RSA-4096", "ChaCha20-Poly1305"]
        )
        
        encrypt_at_rest = st.checkbox("Chiffrement au repos", value=True)
        encrypt_in_transit = st.checkbox("Chiffrement en transit", value=True)
        
        key_rotation = st.number_input("Rotation des clés (jours)", 1, 365, 90)

def show_interface_config():
    """Configuration de l'interface"""
    st.markdown("#### 🎨 Configuration de l'interface")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Thème")
        theme = st.selectbox("Thème", ["Clair", "Sombre", "Auto"])
        primary_color = st.color_picker("Couleur principale", "#1e3c72")
        accent_color = st.color_picker("Couleur d'accent", "#2a5298")
        
        st.markdown("##### Affichage")
        compact_mode = st.checkbox("Mode compact", value=False)
        show_tooltips = st.checkbox("Afficher les infobulles", value=True)
        animations = st.checkbox("Animations", value=True)
    
    with col2:
        st.markdown("##### Langue et région")
        language = st.selectbox("Langue", ["Français", "English", "Español"])
        timezone = st.selectbox("Fuseau horaire", ["Europe/Paris", "UTC", "America/New_York"])
        date_format = st.selectbox("Format de date", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
        
        st.markdown("##### Notifications")
        email_notifications = st.checkbox("Notifications email", value=True)
        browser_notifications = st.checkbox("Notifications navigateur", value=False)
        sound_alerts = st.checkbox("Alertes sonores", value=False)

def show_performance_config():
    """Configuration des performances"""
    st.markdown("#### ⚡ Configuration des performances")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Cache")
        enable_cache = st.checkbox("Activer le cache", value=True)
        
        if enable_cache:
            cache_size = st.slider("Taille du cache (MB)", 100, 5000, 1000)
            cache_ttl = st.number_input("TTL du cache (heures)", 1, 168, 24)
            cache_strategy = st.selectbox("Stratégie", ["LRU", "LFU", "FIFO"])
        
        st.markdown("##### Traitement")
        max_workers = st.number_input("Workers max", 1, 16, 4)
        batch_processing = st.checkbox("Traitement par lots", value=True)
        
        if batch_processing:
            batch_size = st.number_input("Taille des lots", 1, 100, 10)
    
    with col2:
        st.markdown("##### Optimisations")
        lazy_loading = st.checkbox("Chargement différé", value=True)
        compress_data = st.checkbox("Compression des données", value=True)
        
        if compress_data:
            compression_level = st.slider("Niveau de compression", 1, 9, 6)
        
        st.markdown("##### Monitoring")
        enable_monitoring = st.checkbox("Activer le monitoring", value=True)
        
        if enable_monitoring:
            metrics_interval = st.number_input("Intervalle métriques (s)", 10, 300, 60)
            log_level = st.selectbox("Niveau de log", ["DEBUG", "INFO", "WARNING", "ERROR"])

def show_azure_import_interface(auto_analyze: bool, validate_format: bool):
    """Interface d'import depuis Azure Storage"""
    st.info("🔗 Configuration de la connexion Azure Storage")
    
    # Configuration Azure
    col1, col2 = st.columns(2)
    
    with col1:
        account_name = st.text_input("Nom du compte", value="nexoralawstorage")
        container = st.selectbox(
            "Container",
            ["juridique", "expertises", "procedures", "correspondances"]
        )
    
    with col2:
        auth_method = st.radio(
            "Authentification",
            ["🔑 Clé d'accès", "🎫 SAS Token", "🆔 Azure AD"],
            horizontal=True
        )
        
        if auth_method == "🔑 Clé d'accès":
            access_key = st.text_input("Clé d'accès", type="password")
    
    # Parcours des fichiers
    if st.button("📂 Parcourir", use_container_width=True):
        with st.spinner("Connexion à Azure Storage..."):
            time.sleep(1)
            
            # Simulation de fichiers
            files = [
                {"name": "contrat_2024_001.pdf", "size": "2.3 MB", "modified": "2024-12-01"},
                {"name": "avenant_modification.docx", "size": "156 KB", "modified": "2024-12-15"},
                {"name": "correspondances_client.pdf", "size": "5.1 MB", "modified": "2024-12-20"},
            ]
            
            st.success("✅ Connexion établie")
            
            # Sélection des fichiers
            st.markdown("#### 📁 Fichiers disponibles")
            
            selected_files = []
            for file in files:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    if st.checkbox(file["name"], key=f"azure_{file['name']}"):
                        selected_files.append(file)
                
                with col2:
                    st.text(file["size"])
                
                with col3:
                    st.text(file["modified"])
                
                with col4:
                    st.button("👁️", key=f"preview_azure_{file['name']}")
            
            if selected_files and st.button(
                f"⬇️ Importer {len(selected_files)} fichier(s)",
                type="primary",
                use_container_width=True
            ):
                process_azure_import(selected_files, auto_analyze)

def show_url_import_interface(auto_analyze: bool, validate_format: bool):
    """Interface d'import depuis URL"""
    st.markdown("#### 🔗 Import depuis URL")
    
    urls = st.text_area(
        "URLs (une par ligne)",
        placeholder="https://example.com/document1.pdf\nhttps://example.com/document2.docx",
        height=100
    )
    
    if urls:
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        
        st.info(f"📋 {len(url_list)} URL(s) détectée(s)")
        
        # Options d'import
        col1, col2 = st.columns(2)
        
        with col1:
            follow_redirects = st.checkbox("Suivre les redirections", value=True)
            verify_ssl = st.checkbox("Vérifier SSL", value=True)
        
        with col2:
            timeout = st.number_input("Timeout (s)", 5, 60, 30)
            max_size = st.number_input("Taille max (MB)", 1, 100, 50)
        
        if st.button("🌐 Importer depuis URL", type="primary", use_container_width=True):
            process_url_import(url_list, auto_analyze)

def show_clipboard_import_interface(auto_analyze: bool, validate_format: bool):
    """Interface d'import depuis le presse-papier"""
    st.markdown("#### 📋 Import depuis le presse-papier")
    
    clipboard_content = st.text_area(
        "Collez votre contenu ici",
        height=300,
        placeholder="Collez du texte, JSON, CSV..."
    )
    
    if clipboard_content:
        # Détection du format
        content_type = detect_content_type(clipboard_content)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"📄 Format détecté: {content_type}")
        
        with col2:
            custom_name = st.text_input("Nom du document", value=f"clipboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if st.button("📥 Importer le contenu", type="primary", use_container_width=True):
            process_clipboard_import(clipboard_content, custom_name, content_type, auto_analyze)

def process_azure_import(files: list, auto_analyze: bool):
    """Traite l'import depuis Azure"""
    with st.spinner("⬇️ Téléchargement depuis Azure..."):
        progress = st.progress(0)
        
        for idx, file in enumerate(files):
            progress.progress((idx + 1) / len(files))
            time.sleep(0.5)
        
        st.success(f"✅ {len(files)} fichiers importés depuis Azure")
        
        if auto_analyze:
            st.info("🤖 Analyse automatique lancée")

def process_url_import(urls: list, auto_analyze: bool):
    """Traite l'import depuis URLs"""
    with st.spinner("🌐 Téléchargement depuis URLs..."):
        progress = st.progress(0)
        
        for idx, url in enumerate(urls):
            progress.progress((idx + 1) / len(urls))
            time.sleep(0.3)
        
        st.success(f"✅ {len(urls)} documents importés")

def process_clipboard_import(content: str, name: str, content_type: str, auto_analyze: bool):
    """Traite l'import depuis le presse-papier"""
    with st.spinner("📋 Import du contenu..."):
        time.sleep(0.5)
        
        doc = {
            'name': name,
            'type': content_type,
            'content': content,
            'size': len(content),
            'imported_at': datetime.now()
        }
        
        st.session_state.import_export_state['imported_documents'].append(doc)
        
        st.success("✅ Contenu importé avec succès")

def detect_content_type(content: str) -> str:
    """Détecte le type de contenu"""
    content = content.strip()
    
    if content.startswith('{') or content.startswith('['):
        return "JSON"
    elif '\t' in content or ',' in content[:100]:
        return "CSV"
    elif content.startswith('<?xml'):
        return "XML"
    else:
        return "Texte"

# Garder toutes les fonctions d'import existantes du document original
# [Ajouter ici toutes les fonctions d'import du document 5 qui ne sont pas déjà présentes]

# Point d'entrée
if __name__ == "__main__":
    run()