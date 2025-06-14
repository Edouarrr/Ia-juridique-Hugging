# modules/plaidoirie.py
"""Module de génération et gestion des plaidoiries avec IA multiple et mode fusion"""

import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Ajouter le chemin parent pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from config.app_config import REDACTION_STYLES, LLMProvider
from managers.multi_llm_manager import MultiLLMManager
from models.dataclasses import Document, PlaidoirieResult
from utils.text_processing import extract_section
try:
    from utils import clean_key, format_duration, format_legal_date, truncate_text
except Exception:  # pragma: no cover - fallback for standalone use
    from utils.fallback import clean_key, format_legal_date, truncate_text
    from utils import format_duration


def run():
    """Fonction principale du module pour le lazy loading"""
    # Configuration de la page
    st.title("🎤 Générateur de Plaidoiries IA")
    st.markdown("""
    Module avancé de génération de plaidoiries judiciaires utilisant l'intelligence artificielle.
    Créez des plaidoiries percutantes adaptées à votre style et votre audience.
    """)
    
    # Initialisation de l'état de session
    init_session_state()
    
    # Tabs principaux
    tabs = st.tabs([
        "📂 Documents & Analyse", 
        "⚙️ Configuration", 
        "🤖 Modèles IA",
        "🚀 Génération", 
        "📊 Résultats",
        "🎬 Mode Répétition"
    ])
    
    with tabs[0]:  # Documents & Analyse
        render_documents_tab()
    
    with tabs[1]:  # Configuration
        render_configuration_tab()
    
    with tabs[2]:  # Modèles IA
        render_ai_models_tab()
    
    with tabs[3]:  # Génération
        render_generation_tab()
    
    with tabs[4]:  # Résultats
        render_results_tab()
    
    with tabs[5]:  # Mode Répétition
        render_rehearsal_tab()
    
    # Sidebar avec aide et statistiques
    render_sidebar()

def init_session_state():
    """Initialise les variables de session"""
    if 'plaidoirie_state' not in st.session_state:
        st.session_state.plaidoirie_state = {
            'initialized': True,
            'config': {},
            'selected_documents': [],
            'analysis': {},
            'selected_models': [],
            'generation_mode': 'single',
            'results': None,
            'history': [],
            'rehearsal_section': 0,
            'timer_start': None
        }

def render_documents_tab():
    """Onglet de sélection et analyse des documents"""
    st.markdown("### 📂 Sélection des documents du dossier")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sélection depuis Azure
        st.markdown("#### 📥 Documents disponibles")
        
        # Récupérer les documents disponibles
        available_docs = get_available_documents()
        
        if available_docs:
            # Filtres
            doc_types = list(set(doc.get('type', 'Autre') for doc in available_docs))
            selected_types = st.multiselect(
                "Filtrer par type",
                doc_types,
                default=doc_types,
                key="doc_type_filter"
            )
            
            # Tableau de sélection
            filtered_docs = [doc for doc in available_docs if doc.get('type', 'Autre') in selected_types]
            
            doc_df = pd.DataFrame(filtered_docs)
            
            # Sélection interactive
            selected_indices = st.multiselect(
                "Sélectionner les documents pour la plaidoirie",
                range(len(filtered_docs)),
                format_func=lambda x: f"{filtered_docs[x]['title']} ({filtered_docs[x]['type']})",
                default=list(range(min(5, len(filtered_docs)))),
                key="doc_selection"
            )
            
            st.session_state.plaidoirie_state['selected_documents'] = [
                filtered_docs[i] for i in selected_indices
            ]
            
            # Aperçu des documents sélectionnés
            if st.session_state.plaidoirie_state['selected_documents']:
                st.markdown(f"**{len(st.session_state.plaidoirie_state['selected_documents'])} documents sélectionnés**")
                
                with st.expander("📋 Aperçu des documents sélectionnés", expanded=False):
                    for doc in st.session_state.plaidoirie_state['selected_documents']:
                        st.markdown(f"- **{doc['title']}** ({doc['type']})")
                        if 'content' in doc:
                            st.caption(truncate_text(doc['content'], 150))
        else:
            st.info("Aucun document disponible. Chargez des documents depuis Azure.")
    
    with col2:
        # Analyse rapide
        st.markdown("#### 📊 Analyse du dossier")
        
        if st.session_state.plaidoirie_state['selected_documents']:
            # Bouton d'analyse
            if st.button("🔍 Analyser le dossier", type="primary", use_container_width=True):
                with st.spinner("Analyse en cours..."):
                    analysis = analyze_documents(st.session_state.plaidoirie_state['selected_documents'])
                    st.session_state.plaidoirie_state['analysis'] = analysis
            
            # Afficher l'analyse si disponible
            if st.session_state.plaidoirie_state['analysis']:
                analysis = st.session_state.plaidoirie_state['analysis']
                
                st.success("✅ Analyse terminée")
                
                # Métriques
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Documents analysés", len(st.session_state.plaidoirie_state['selected_documents']))
                with col2:
                    st.metric("Points clés identifiés", analysis.get('key_points_count', 0))
                
                # Résumé
                if 'summary' in analysis:
                    st.markdown("**Résumé de l'affaire:**")
                    st.info(analysis['summary'])
                
                # Points forts/faibles
                if 'strengths' in analysis:
                    st.markdown("**💪 Points forts:**")
                    for point in analysis['strengths'][:3]:
                        st.write(f"• {point}")
                
                if 'weaknesses' in analysis:
                    st.markdown("**⚠️ Points d'attention:**")
                    for point in analysis['weaknesses'][:3]:
                        st.write(f"• {point}")
        else:
            st.info("Sélectionnez des documents pour lancer l'analyse")

def render_configuration_tab():
    """Onglet de configuration de la plaidoirie"""
    st.markdown("### ⚙️ Configuration de la plaidoirie")
    
    # Configuration en colonnes
    col1, col2, col3 = st.columns(3)
    
    config = st.session_state.plaidoirie_state['config']
    
    with col1:
        st.markdown("#### ⚖️ Contexte judiciaire")
        
        config['audience_type'] = st.selectbox(
            "Type d'audience",
            ["correctionnelle", "assises", "civile", "commerciale", "prud'homale", "administrative"],
            format_func=lambda x: {
                "correctionnelle": "Tribunal correctionnel",
                "assises": "Cour d'assises",
                "civile": "Tribunal civil",
                "commerciale": "Tribunal de commerce",
                "prud_homale": "Conseil de prud'hommes",
                "administrative": "Tribunal administratif"
            }.get(x, x.title()),
            key="audience_type_config",
            help="Le type d'audience détermine le ton et la structure de la plaidoirie"
        )
        
        config['position'] = st.radio(
            "Position dans l'affaire",
            ["defense", "partie_civile", "demandeur", "defendeur"],
            format_func=lambda x: {
                "defense": "🛡️ Défense",
                "partie_civile": "⚖️ Partie civile",
                "demandeur": "📋 Demandeur",
                "defendeur": "🛡️ Défendeur"
            }.get(x, x.title()),
            key="position_config"
        )
        
        config['juridiction'] = st.text_input(
            "🏛️ Juridiction",
            value=config.get('juridiction', 'Tribunal de Grande Instance'),
            key="juridiction_config"
        )
    
    with col2:
        st.markdown("#### 🎯 Paramètres oratoires")
        
        config['duree'] = st.select_slider(
            "⏱️ Durée cible",
            options=["5 min", "10 min", "15 min", "20 min", "30 min", "45 min", "1h", "1h30", "2h"],
            value=config.get('duree', "20 min"),
            key="duree_config",
            help="Durée approximative de la plaidoirie"
        )
        
        config['style'] = st.selectbox(
            "🎭 Style oratoire",
            ["classique", "moderne", "emotionnel", "technique", "percutant", "mixte"],
            format_func=lambda x: {
                "classique": "Classique - Solennel et structuré",
                "moderne": "Moderne - Direct et accessible",
                "emotionnel": "Émotionnel - Touchant et empathique",
                "technique": "Technique - Précis et factuel",
                "percutant": "Percutant - Dynamique et mémorable",
                "mixte": "Mixte - Adaptatif selon les sections"
            }.get(x, x.title()),
            key="style_config"
        )
        
        config['niveau_detail'] = st.select_slider(
            "📊 Niveau de détail",
            options=["Synthétique", "Standard", "Détaillé", "Très détaillé"],
            value=config.get('niveau_detail', "Standard"),
            key="niveau_detail_config"
        )
    
    with col3:
        st.markdown("#### 🎨 Options avancées")
        
        config['avec_replique'] = st.checkbox(
            "💬 Inclure section réplique",
            value=config.get('avec_replique', True),
            help="Préparer des réponses aux arguments adverses",
            key="avec_replique_config"
        )
        
        config['avec_notes'] = st.checkbox(
            "📝 Notes pour l'oral",
            value=config.get('avec_notes', True),
            help="Ajouter des indications de ton, pauses, gestes",
            key="avec_notes_config"
        )
        
        config['client_present'] = st.checkbox(
            "👥 Client présent à l'audience",
            value=config.get('client_present', True),
            help="Adapter le discours si le client est présent",
            key="client_present_config"
        )
        
        config['citations_juridiques'] = st.checkbox(
            "📚 Inclure citations juridiques",
            value=config.get('citations_juridiques', True),
            help="Ajouter des références à la jurisprudence",
            key="citations_juridiques_config"
        )
        
        config['effets_dramatiques'] = st.checkbox(
            "🎬 Effets dramatiques",
            value=config.get('effets_dramatiques', False),
            help="Ajouter des effets de style pour marquer les esprits",
            key="effets_dramatiques_config"
        )
    
    # Informations sur les parties
    st.markdown("---")
    st.markdown("#### 👥 Informations sur les parties")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        config['client_name'] = st.text_input(
            "👤 Nom du client",
            value=config.get('client_name', ''),
            placeholder="M./Mme ...",
            key="client_name_config"
        )
        
        config['client_profession'] = st.text_input(
            "💼 Profession du client",
            value=config.get('client_profession', ''),
            key="client_profession_config"
        )
    
    with col2:
        config['adversaire'] = st.text_input(
            "⚔️ Partie adverse",
            value=config.get('adversaire', ''),
            placeholder="Nom de la partie adverse",
            key="adversaire_config"
        )
        
        config['avocat_adverse'] = st.text_input(
            "⚖️ Avocat adverse",
            value=config.get('avocat_adverse', ''),
            placeholder="Me ...",
            key="avocat_adverse_config"
        )
    
    with col3:
        config['juge'] = st.text_input(
            "👨‍⚖️ Président/Juge",
            value=config.get('juge', ''),
            placeholder="M./Mme le/la Président(e)",
            key="juge_config"
        )
        
        config['numero_affaire'] = st.text_input(
            "📋 N° d'affaire",
            value=config.get('numero_affaire', ''),
            key="numero_affaire_config"
        )
    
    # Points clés à développer
    st.markdown("---")
    config['points_cles'] = st.text_area(
        "🎯 Points clés à développer",
        value=config.get('points_cles', ''),
        placeholder="- Premier argument fort\n- Deuxième point crucial\n- Réfutation principale\n- Demande finale",
        height=150,
        key="points_cles_config",
        help="Listez les points essentiels à aborder dans la plaidoirie"
    )
    
    # Sauvegarder la configuration
    st.session_state.plaidoirie_state['config'] = config

def render_ai_models_tab():
    """Onglet de sélection et configuration des modèles IA"""
    st.markdown("### 🤖 Configuration des modèles IA")
    
    llm_manager = MultiLLMManager()
    available_providers = list(llm_manager.clients.keys()) if llm_manager.clients else []
    
    if not available_providers:
        st.error("❌ Aucun modèle IA disponible. Veuillez configurer vos clés API.")
        return
    
    # Mode de génération
    st.markdown("#### 🎯 Mode de génération")
    
    generation_mode = st.radio(
        "Choisir le mode",
        ["single", "multi", "fusion"],
        format_func=lambda x: {
            "single": "🎯 Modèle unique - Rapide et efficace",
            "multi": "🔄 Multi-modèles - Comparaison des résultats",
            "fusion": "🔥 Mode Fusion - Combine le meilleur de chaque IA"
        }.get(x),
        key="generation_mode_radio",
        help="Le mode fusion combine les forces de plusieurs IA pour un résultat optimal"
    )
    
    st.session_state.plaidoirie_state['generation_mode'] = generation_mode
    
    # Sélection des modèles
    st.markdown("#### 🤖 Sélection des modèles")
    
    if generation_mode == "single":
        selected_model = st.selectbox(
            "Choisir le modèle",
            available_providers,
            format_func=lambda x: {
                LLMProvider.OPENAI: "🧠 OpenAI GPT-4",
                LLMProvider.ANTHROPIC: "🎯 Anthropic Claude",
                LLMProvider.GROQ: "⚡ Groq",
                LLMProvider.GOOGLE: "🔷 Google Gemini",
                LLMProvider.COHERE: "🌟 Cohere",
                LLMProvider.OPENROUTER: "🌐 OpenRouter",
                LLMProvider.XAI: "🚀 X.AI Grok"
            }.get(x, x.value),
            key="single_model_select"
        )
        st.session_state.plaidoirie_state['selected_models'] = [selected_model]
        
    else:  # multi ou fusion
        selected_models = st.multiselect(
            "Sélectionner les modèles à utiliser",
            available_providers,
            default=available_providers[:3] if len(available_providers) >= 3 else available_providers,
            format_func=lambda x: {
                LLMProvider.OPENAI: "🧠 OpenAI GPT-4",
                LLMProvider.ANTHROPIC: "🎯 Anthropic Claude",
                LLMProvider.GROQ: "⚡ Groq",
                LLMProvider.GOOGLE: "🔷 Google Gemini",
                LLMProvider.COHERE: "🌟 Cohere",
                LLMProvider.OPENROUTER: "🌐 OpenRouter",
                LLMProvider.XAI: "🚀 X.AI Grok"
            }.get(x, x.value),
            key="multi_model_select",
            help="Sélectionnez au moins 2 modèles pour le mode multi/fusion"
        )
        st.session_state.plaidoirie_state['selected_models'] = selected_models
    
    # Configuration avancée
    with st.expander("⚙️ Configuration avancée des modèles", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "🌡️ Température (créativité)",
                0.0, 1.0, 0.8,
                help="Plus élevé = plus créatif, plus bas = plus factuel",
                key="temperature_slider"
            )
            
            max_tokens = st.number_input(
                "📏 Tokens maximum",
                1000, 15000, 5000,
                step=500,
                help="Limite de longueur de la réponse",
                key="max_tokens_input"
            )
        
        with col2:
            top_p = st.slider(
                "🎯 Top P",
                0.0, 1.0, 0.9,
                help="Contrôle la diversité du vocabulaire",
                key="top_p_slider"
            )
            
            frequency_penalty = st.slider(
                "🔄 Pénalité de fréquence",
                0.0, 2.0, 0.3,
                help="Réduit les répétitions",
                key="frequency_penalty_slider"
            )
        
        # Sauvegarder les paramètres
        st.session_state.plaidoirie_state['model_params'] = {
            'temperature': temperature,
            'max_tokens': max_tokens,
            'top_p': top_p,
            'frequency_penalty': frequency_penalty
        }
    
    # Aperçu de la configuration
    if st.session_state.plaidoirie_state['selected_models']:
        st.markdown("#### 📋 Configuration actuelle")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Mode", generation_mode.title())
        
        with col2:
            st.metric("Modèles sélectionnés", len(st.session_state.plaidoirie_state['selected_models']))
        
        with col3:
            estimated_time = estimate_generation_time(generation_mode, len(st.session_state.plaidoirie_state['selected_models']))
            st.metric("Temps estimé", estimated_time)
        
        # Coût estimé
        if generation_mode != "single":
            st.info(f"💡 Le mode {generation_mode} utilisera {len(st.session_state.plaidoirie_state['selected_models'])} requêtes IA")

def render_generation_tab():
    """Onglet de génération de la plaidoirie"""
    st.markdown("### 🚀 Génération de la plaidoirie")
    
    # Vérifications préalables
    ready = True
    missing = []
    
    if not st.session_state.plaidoirie_state['selected_documents']:
        ready = False
        missing.append("Documents à analyser")
    
    if not st.session_state.plaidoirie_state['config'].get('client_name'):
        ready = False
        missing.append("Nom du client")
    
    if not st.session_state.plaidoirie_state['selected_models']:
        ready = False
        missing.append("Modèle(s) IA")
    
    if not ready:
        st.warning(f"⚠️ Veuillez compléter : {', '.join(missing)}")
    
    # Résumé de la configuration
    with st.expander("📋 Résumé de la configuration", expanded=True):
        config = st.session_state.plaidoirie_state['config']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏛️ Contexte**")
            st.write(f"• Type: {config.get('audience_type', 'Non défini')}")
            st.write(f"• Position: {config.get('position', 'Non défini')}")
            st.write(f"• Client: {config.get('client_name', 'Non défini')}")
        
        with col2:
            st.markdown("**⏱️ Format**")
            st.write(f"• Durée: {config.get('duree', '20 min')}")
            st.write(f"• Style: {config.get('style', 'classique')}")
            st.write(f"• Documents: {len(st.session_state.plaidoirie_state['selected_documents'])}")
        
        with col3:
            st.markdown("**🤖 IA**")
            st.write(f"• Mode: {st.session_state.plaidoirie_state['generation_mode']}")
            st.write(f"• Modèles: {len(st.session_state.plaidoirie_state['selected_models'])}")
            st.write(f"• Temp: {st.session_state.plaidoirie_state.get('model_params', {}).get('temperature', 0.8)}")
    
    # Bouton de génération
    if st.button(
        "🚀 Générer la plaidoirie",
        type="primary",
        use_container_width=True,
        disabled=not ready,
        key="generate_plaidoirie_button"
    ):
        generate_plaidoirie_with_progress()
    
    # Historique des générations
    if st.session_state.plaidoirie_state['history']:
        st.markdown("---")
        st.markdown("### 📜 Historique des générations")
        
        for i, item in enumerate(reversed(st.session_state.plaidoirie_state['history'][-5:])):
            with st.expander(f"🕐 {item['timestamp']} - {item['type']} ({item['duration']})", expanded=False):
                st.write(f"**Style:** {item['style']}")
                st.write(f"**Mode:** {item['mode']}")
                st.write(f"**Modèles:** {', '.join(item['models'])}")
                
                if st.button(f"📥 Charger", key=f"load_history_{i}"):
                    st.session_state.plaidoirie_state['results'] = item['result']
                    st.success("✅ Plaidoirie chargée")
                    st.rerun()

def generate_plaidoirie_with_progress():
    """Génère la plaidoirie avec barre de progression"""
    
    config = st.session_state.plaidoirie_state['config']
    analysis = st.session_state.plaidoirie_state['analysis']
    mode = st.session_state.plaidoirie_state['generation_mode']
    selected_models = st.session_state.plaidoirie_state['selected_models']
    
    # Container pour les mises à jour
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Phases de génération
        if mode == "single":
            phases = [
                ("Préparation du contexte", 0.2),
                ("Génération de la plaidoirie", 0.8),
                ("Finalisation", 1.0)
            ]
        elif mode == "multi":
            phases = [
                ("Préparation du contexte", 0.1),
                *[(f"Génération {model.value}", 0.1 + (i+1) * 0.8/len(selected_models)) 
                  for i, model in enumerate(selected_models)],
                ("Compilation des résultats", 1.0)
            ]
        else:  # fusion
            phases = [
                ("Préparation du contexte", 0.1),
                *[(f"Génération {model.value}", 0.1 + (i+1) * 0.6/len(selected_models)) 
                  for i, model in enumerate(selected_models)],
                ("Analyse des résultats", 0.8),
                ("Fusion intelligente", 0.95),
                ("Optimisation finale", 1.0)
            ]
        
        results = []
        
        for phase_name, progress_value in phases:
            status_text.text(f"⏳ {phase_name}...")
            progress_bar.progress(progress_value)
            
            # Exécution réelle selon la phase
            if "Préparation" in phase_name:
                time.sleep(0.5)  # Simulation
                prompt = build_enhanced_plaidoirie_prompt(config, analysis)
                system_prompt = build_enhanced_system_prompt(config)
                
            elif "Génération" in phase_name and mode != "fusion":
                # Extraire le nom du modèle
                for model in selected_models:
                    if model.value in phase_name:
                        result = generate_with_model(
                            model, 
                            prompt, 
                            system_prompt,
                            st.session_state.plaidoirie_state.get('model_params', {})
                        )
                        if result:
                            results.append(result)
                        break
            
            elif "Génération" in phase_name and mode == "fusion":
                # Mode fusion : génération parallèle
                for model in selected_models:
                    if model.value in phase_name:
                        result = generate_with_model(
                            model, 
                            prompt, 
                            system_prompt,
                            st.session_state.plaidoirie_state.get('model_params', {})
                        )
                        if result:
                            results.append(result)
                        break
            
            elif "Fusion intelligente" in phase_name:
                # Fusionner les résultats
                if results:
                    final_result = fusion_plaidoiries(results, config)
                    results = [final_result]
            
            time.sleep(0.3)  # Petit délai pour l'UX
        
        status_text.text("✅ Génération terminée!")
        
        # Stocker les résultats
        if results:
            if mode == "single" or mode == "fusion":
                st.session_state.plaidoirie_state['results'] = results[0]
            else:  # multi
                st.session_state.plaidoirie_state['results'] = results
            
            # Ajouter à l'historique
            add_to_history(results[0] if mode != "multi" else results, config, mode, selected_models)
            
            st.success("✅ Plaidoirie générée avec succès!")
            st.balloons()
        else:
            st.error("❌ Erreur lors de la génération")

def render_results_tab():
    """Onglet d'affichage des résultats"""
    st.markdown("### 📊 Résultats de la génération")
    
    results = st.session_state.plaidoirie_state.get('results')
    
    if not results:
        st.info("👆 Lancez d'abord la génération de plaidoirie")
        return
    
    # Mode multi : plusieurs résultats
    if isinstance(results, list) and st.session_state.plaidoirie_state['generation_mode'] == "multi":
        render_multi_results(results)
    else:
        # Mode single ou fusion : un seul résultat
        render_single_result(results)

def render_single_result(result: PlaidoirieResult):
    """Affiche un résultat unique"""
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Type", result.type.title())
    
    with col2:
        st.metric("⏱️ Durée", result.duration_estimate)
    
    with col3:
        st.metric("🎭 Style", result.style.title())
    
    with col4:
        word_count = len(result.content.split())
        st.metric("📊 Mots", f"{word_count:,}")
    
    # Options d'affichage
    view_mode = st.radio(
        "Mode d'affichage",
        ["📄 Texte complet", "🎯 Points clés", "📊 Structure", "📈 Analyse"],
        horizontal=True,
        key="result_view_mode"
    )
    
    if view_mode == "📄 Texte complet":
        render_full_text(result)
    
    elif view_mode == "🎯 Points clés":
        render_key_points(result)
    
    elif view_mode == "📊 Structure":
        render_structure(result)
    
    else:  # Analyse
        render_analysis(result)
    
    # Actions
    render_actions(result)

def render_multi_results(results: List[PlaidoirieResult]):
    """Affiche plusieurs résultats pour comparaison"""
    st.markdown("### 🔄 Comparaison des modèles")
    
    # Tabs pour chaque résultat
    tabs = st.tabs([f"🤖 {r.metadata.get('provider', 'Modèle')}" for r in results])
    
    for i, (tab, result) in enumerate(zip(tabs, results)):
        with tab:
            render_single_result(result)
    
    # Analyse comparative
    with st.expander("📊 Analyse comparative", expanded=True):
        render_comparative_analysis(results)

def render_rehearsal_tab():
    """Onglet mode répétition"""
    st.markdown("### 🎬 Mode répétition")
    
    result = st.session_state.plaidoirie_state.get('results')
    
    if not result:
        st.info("👆 Générez d'abord une plaidoirie pour accéder au mode répétition")
        return
    
    # Si résultats multiples, choisir
    if isinstance(result, list):
        selected_idx = st.selectbox(
            "Choisir la plaidoirie à répéter",
            range(len(result)),
            format_func=lambda x: f"{result[x].metadata.get('provider', f'Modèle {x+1}')}",
            key="rehearsal_select"
        )
        result = result[selected_idx]
    
    # Interface de répétition
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Diviser en sections
        sections = split_plaidoirie_sections(result.content)
        
        # Navigation
        current_section = st.session_state.plaidoirie_state.get('rehearsal_section', 0)
        
        # Affichage de la section
        st.markdown(f"#### Section {current_section + 1} / {len(sections)}")
        
        # Zone de texte pour la section
        section_container = st.container()
        with section_container:
            st.markdown(
                f"""
                <div style="
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    min-height: 400px;
                    font-size: 18px;
                    line-height: 1.8;
                ">
                {format_for_rehearsal(sections[current_section])}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Contrôles de navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        
        with nav_col1:
            if st.button("⬅️ Précédent", use_container_width=True, disabled=current_section == 0):
                st.session_state.plaidoirie_state['rehearsal_section'] = current_section - 1
                st.rerun()
        
        with nav_col2:
            progress = (current_section + 1) / len(sections)
            st.progress(progress)
            st.caption(f"Progression : {progress * 100:.0f}%")
        
        with nav_col3:
            if st.button("Suivant ➡️", use_container_width=True, disabled=current_section >= len(sections) - 1):
                st.session_state.plaidoirie_state['rehearsal_section'] = current_section + 1
                st.rerun()
    
    with col2:
        # Timer et outils
        st.markdown("#### ⏱️ Chronomètre")
        
        timer_state = st.session_state.plaidoirie_state.get('timer_start')
        
        if st.button("▶️ Démarrer" if not timer_state else "⏸️ Pause", use_container_width=True, type="primary"):
            if not timer_state:
                st.session_state.plaidoirie_state['timer_start'] = time.time()
            else:
                elapsed = time.time() - timer_state
                st.session_state.plaidoirie_state['timer_start'] = None
                st.success(f"Temps : {int(elapsed//60)}:{int(elapsed%60):02d}")
        
        if timer_state:
            # Affichage du temps en cours
            placeholder = st.empty()
            while st.session_state.plaidoirie_state.get('timer_start'):
                elapsed = time.time() - st.session_state.plaidoirie_state['timer_start']
                placeholder.metric("Temps écoulé", f"{int(elapsed//60)}:{int(elapsed%60):02d}")
                time.sleep(1)
        
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.plaidoirie_state['timer_start'] = None
            st.session_state.plaidoirie_state['rehearsal_section'] = 0
            st.rerun()
        
        # Conseils
        with st.expander("💡 Conseils", expanded=True):
            st.markdown("""
            **Pour une répétition efficace :**
            
            • 🎤 Répétez debout
            • 🎭 Variez les tons
            • ⏸️ Marquez les pauses
            • 👐 Utilisez les gestes
            • 🎯 Regardez votre public
            • 📱 Enregistrez-vous
            """)
        
        # Notes personnelles
        st.text_area(
            "📝 Notes personnelles",
            height=150,
            key=f"rehearsal_notes_{current_section}",
            placeholder="Notez vos observations..."
        )

def render_sidebar():
    """Affiche la sidebar avec aide et statistiques"""
    with st.sidebar:
        st.markdown("## 🎤 Aide Plaidoirie")
        
        with st.expander("📚 Guide rapide", expanded=False):
            st.markdown("""
            **Étapes de création :**
            1. 📂 Sélectionnez vos documents
            2. ⚙️ Configurez la plaidoirie
            3. 🤖 Choisissez les modèles IA
            4. 🚀 Générez
            5. 📊 Analysez et exportez
            
            **Modes disponibles :**
            - **Single** : Rapide avec un modèle
            - **Multi** : Compare plusieurs IA
            - **Fusion** : Combine le meilleur
            """)
        
        with st.expander("🎯 Conseils pro", expanded=False):
            st.markdown("""
            **Pour une plaidoirie percutante :**
            
            • **Structure** : Introduction → Développement → Péroraison
            • **Rythme** : Alternez arguments forts et moments de respiration
            • **Émotion** : Dosez selon le contexte
            • **Preuves** : Citez précisément vos pièces
            • **Conclusion** : Terminez sur une note mémorable
            
            **Erreurs à éviter :**
            - Trop de détails techniques
            - Manque de structure claire
            - Ton monotone
            - Arguments trop nombreux
            """)
        
        # Statistiques de session
        if st.session_state.plaidoirie_state.get('results'):
            st.markdown("---")
            st.markdown("### 📊 Statistiques")
            
            if isinstance(st.session_state.plaidoirie_state['results'], list):
                st.metric("Plaidoiries générées", len(st.session_state.plaidoirie_state['results']))
            else:
                result = st.session_state.plaidoirie_state['results']
                st.metric("Mots", f"{len(result.content.split()):,}")
                st.metric("Temps estimé", f"{len(result.content.split()) / 150:.0f} min")
            
            st.metric("Documents utilisés", len(st.session_state.plaidoirie_state.get('selected_documents', [])))
            st.metric("Générations totales", len(st.session_state.plaidoirie_state.get('history', [])))

# Fonctions utilitaires améliorées

def get_available_documents() -> List[Dict[str, Any]]:
    """Récupère les documents disponibles depuis la session"""
    documents = []
    
    # Documents Azure de la session
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        doc_type = detect_document_type(doc.title, doc.content)
        
        documents.append({
            'id': doc_id,
            'title': doc.title,
            'type': doc_type,
            'content': doc.content[:500],  # Preview
            'relevance': calculate_relevance_score(doc_type)
        })
    
    # Trier par pertinence
    documents.sort(key=lambda x: x['relevance'], reverse=True)
    
    return documents

def analyze_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyse approfondie des documents sélectionnés"""
    
    # Simulation d'analyse (remplacer par vraie analyse IA)
    analysis = {
        'summary': "Affaire complexe impliquant des questions de responsabilité contractuelle et de préjudice commercial.",
        'key_points_count': len(documents) * 3,
        'strengths': [
            "Documentation solide sur les manquements contractuels",
            "Preuves tangibles du préjudice subi",
            "Témoignages concordants"
        ],
        'weaknesses': [
            "Délai de prescription à vérifier",
            "Clause limitative de responsabilité à analyser"
        ],
        'client': "M. Dupont",
        'adversaire': "Société XYZ",
        'juridiction': "Tribunal de Commerce"
    }
    
    return analysis

def generate_with_model(
    provider: LLMProvider,
    prompt: str,
    system_prompt: str,
    params: Dict[str, Any]
) -> Optional[PlaidoirieResult]:
    """Génère une plaidoirie avec un modèle spécifique"""
    
    llm_manager = MultiLLMManager()
    
    # Paramètres de génération
    generation_params = {
        'temperature': params.get('temperature', 0.8),
        'max_tokens': params.get('max_tokens', 5000),
        'top_p': params.get('top_p', 0.9),
        'frequency_penalty': params.get('frequency_penalty', 0.3)
    }
    
    response = llm_manager.query_single_llm(
        provider,
        prompt,
        system_prompt,
        **generation_params
    )
    
    if response['success']:
        content = response['response']
        
        # Créer le résultat
        result = PlaidoirieResult(
            content=content,
            type=st.session_state.plaidoirie_state['config'].get('audience_type', 'correctionnelle'),
            style=st.session_state.plaidoirie_state['config'].get('style', 'classique'),
            duration_estimate=st.session_state.plaidoirie_state['config'].get('duree', '20 min'),
            key_points=extract_key_points(content),
            structure=extract_plaidoirie_structure(content),
            oral_markers=extract_oral_markers(content),
            metadata={
                'provider': provider.value,
                'timestamp': datetime.now().isoformat(),
                **st.session_state.plaidoirie_state['config']
            }
        )
        
        return result
    
    return None

def fusion_plaidoiries(results: List[PlaidoirieResult], config: Dict[str, Any]) -> PlaidoirieResult:
    """Fusionne intelligemment plusieurs plaidoiries"""
    
    # Extraire les meilleures parties de chaque plaidoirie
    best_parts = {
        'introduction': [],
        'development': [],
        'conclusion': [],
        'key_points': [],
        'citations': []
    }
    
    for result in results:
        # Extraire les sections
        sections = extract_sections_for_fusion(result.content)
        
        for section, content in sections.items():
            if content:
                best_parts[section].append({
                    'content': content,
                    'provider': result.metadata.get('provider', 'Unknown'),
                    'score': evaluate_section_quality(content, section)
                })
    
    # Sélectionner les meilleures parties
    final_content = build_fused_plaidoirie(best_parts, config)
    
    # Créer le résultat fusionné
    return PlaidoirieResult(
        content=final_content,
        type=config.get('audience_type', 'correctionnelle'),
        style=config.get('style', 'mixte'),
        duration_estimate=config.get('duree', '20 min'),
        key_points=extract_key_points(final_content),
        structure=extract_plaidoirie_structure(final_content),
        oral_markers=extract_oral_markers(final_content),
        metadata={
            'provider': 'Fusion',
            'sources': [r.metadata.get('provider') for r in results],
            'timestamp': datetime.now().isoformat(),
            **config
        }
    )

def build_enhanced_plaidoirie_prompt(config: dict, analysis: dict) -> str:
    """Construit un prompt amélioré pour la génération"""
    
    # Base du prompt original
    prompt = build_plaidoirie_prompt(config, analysis)
    
    # Ajouts pour l'amélioration
    enhancements = """
EXIGENCES SUPPLÉMENTAIRES POUR L'EXCELLENCE:

1. IMPACT ÉMOTIONNEL
   - Créer des moments de silence calculés pour l'impact
   - Utiliser des images mentales puissantes
   - Construire une progression émotionnelle

2. STRUCTURE RHÉTORIQUE
   - Questions rhétoriques percutantes
   - Anaphores pour marquer les esprits
   - Gradations dans l'argumentation

3. MODERNITÉ
   - Références contemporaines pertinentes
   - Langage accessible sans perdre en solennité
   - Équilibre tradition/innovation

4. PERSONNALISATION
   - Adapter au profil du juge si connu
   - Tenir compte de la jurisprudence locale
   - Anticiper les sensibilités de l'audience

5. MÉMORABILITÉ
   - Formules marquantes (soundbites)
   - Structure en 3 points maximum par section
   - Conclusion inoubliable
"""
    
    return prompt + enhancements

def build_enhanced_system_prompt(config: dict) -> str:
    """Prompt système amélioré"""
    
    base = build_plaidoirie_system_prompt(config)
    
    enhancement = """
Tu combines l'éloquence classique des grands orateurs avec les techniques modernes de communication. 
Tu maîtrises l'art de créer des moments de pure émotion tout en restant rigoureusement juridique.
Chaque plaidoirie que tu crées doit être une œuvre d'art oratoire, mémorable et efficace.
Tu sais adapter ton style à chaque contexte tout en gardant une signature unique.
"""
    
    return base + enhancement

# Fonctions d'affichage détaillées

def render_full_text(result: PlaidoirieResult):
    """Affiche le texte complet avec formatage"""
    
    # Options d'affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_markers = st.checkbox("🎭 Afficher les marqueurs oraux", value=True)
    with col2:
        show_sections = st.checkbox("📑 Numéroter les sections", value=False)
    with col3:
        text_size = st.select_slider("📏 Taille du texte", ["Petit", "Normal", "Grand"], "Normal")
    
    # Formatage du contenu
    formatted_content = format_plaidoirie_display(result.content, show_markers, show_sections)
    
    # Affichage avec style
    font_sizes = {"Petit": "14px", "Normal": "16px", "Grand": "18px"}
    
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            font-size: {font_sizes[text_size]};
            line-height: 1.8;
            font-family: 'Georgia', serif;
        ">
        {formatted_content}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_key_points(result: PlaidoirieResult):
    """Affiche les points clés de manière visuelle"""
    st.markdown("### 🎯 Points clés de la plaidoirie")
    
    # Regrouper par importance
    if result.key_points:
        # Points principaux
        st.markdown("#### 🌟 Arguments principaux")
        for i, point in enumerate(result.key_points[:3], 1):
            st.info(f"**{i}.** {point}")
        
        # Points secondaires
        if len(result.key_points) > 3:
            st.markdown("#### 💡 Arguments complémentaires")
            for i, point in enumerate(result.key_points[3:6], 4):
                st.write(f"**{i}.** {point}")
        
        # Points de réfutation
        if len(result.key_points) > 6:
            st.markdown("#### 🛡️ Points de réfutation")
            for i, point in enumerate(result.key_points[6:], 7):
                st.caption(f"**{i}.** {point}")
    else:
        st.warning("Aucun point clé extrait")

def render_structure(result: PlaidoirieResult):
    """Affiche la structure hiérarchique"""
    st.markdown("### 📊 Structure de la plaidoirie")
    
    if result.structure:
        # Visualisation en arbre
        for section, subsections in result.structure.items():
            with st.expander(f"📌 {section}", expanded=True):
                if subsections:
                    for subsection in subsections:
                        st.write(f"└── {subsection}")
                else:
                    st.caption("Section sans sous-parties détaillées")
        
        # Statistiques de structure
        st.markdown("#### 📈 Analyse structurelle")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sections principales", len(result.structure))
        
        with col2:
            total_subsections = sum(len(subs) for subs in result.structure.values())
            st.metric("Sous-sections", total_subsections)
        
        with col3:
            avg_subsections = total_subsections / max(len(result.structure), 1)
            st.metric("Moyenne sous-sections", f"{avg_subsections:.1f}")
    else:
        st.warning("Structure non analysée")

def render_analysis(result: PlaidoirieResult):
    """Affiche une analyse détaillée de la plaidoirie"""
    st.markdown("### 📈 Analyse approfondie")
    
    # Analyse textuelle
    content_analysis = analyze_plaidoirie_content(result.content)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Mots", f"{content_analysis['word_count']:,}")
        st.metric("📄 Paragraphes", content_analysis['paragraph_count'])
    
    with col2:
        st.metric("⏱️ Temps oral", f"{content_analysis['speaking_time']} min")
        st.metric("📊 Mots/minute", content_analysis['words_per_minute'])
    
    with col3:
        st.metric("❓ Questions", content_analysis['questions'])
        st.metric("❗ Exclamations", content_analysis['exclamations'])
    
    with col4:
        st.metric("🎭 Marqueurs oraux", len(result.oral_markers))
        st.metric("📚 Densité juridique", f"{content_analysis['legal_density']:.1%}")
    
    # Graphiques
    tabs = st.tabs(["📊 Répartition", "🎭 Tonalité", "⚡ Rythme"])
    
    with tabs[0]:
        render_section_distribution(result)
    
    with tabs[1]:
        render_tone_analysis(result)
    
    with tabs[2]:
        render_rhythm_analysis(result)

def render_actions(result: PlaidoirieResult):
    """Affiche les actions disponibles"""
    st.markdown("---")
    st.markdown("### 💾 Actions et exports")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Export PDF", use_container_width=True):
            pdf_content = generate_pdf_export(result)
            st.download_button(
                "💾 Télécharger PDF",
                pdf_content,
                f"plaidoirie_{result.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "application/pdf"
            )
    
    with col2:
        if st.button("🎤 Notes orateur", use_container_width=True):
            speaker_notes = create_enhanced_speaker_notes(result)
            st.download_button(
                "💾 Télécharger notes",
                speaker_notes.encode('utf-8'),
                f"notes_orateur_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )
    
    with col3:
        if st.button("📊 Rapport analyse", use_container_width=True):
            analysis_report = generate_analysis_report(result)
            st.download_button(
                "💾 Télécharger rapport",
                analysis_report.encode('utf-8'),
                f"analyse_plaidoirie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                "text/markdown"
            )
    
    with col4:
        if st.button("🎬 Mode présentation", use_container_width=True):
            st.session_state.plaidoirie_state['rehearsal_section'] = 0
            st.info("👆 Accédez à l'onglet 'Mode Répétition'")

# Fonctions helper supplémentaires

def detect_document_type(title: str, content: str) -> str:
    """Détecte le type d'un document juridique"""
    title_lower = title.lower()
    content_preview = content[:1000].lower()
    
    patterns = {
        'temoignage': ['audition', 'interrogatoire', 'garde à vue', 'déposition'],
        'expertise': ['expertise', 'expert', 'rapport d\'expertise', 'évaluation'],
        'procedure': ['pv', 'procès-verbal', 'constat', 'signification'],
        'jugement': ['jugement', 'arrêt', 'ordonnance', 'décision'],
        'contrat': ['contrat', 'convention', 'accord', 'bail'],
        'correspondance': ['lettre', 'courrier', 'mail', 'courriel']
    }
    
    for doc_type, keywords in patterns.items():
        if any(kw in title_lower or kw in content_preview for kw in keywords):
            return doc_type.title()
    
    return "Autre"

def calculate_relevance_score(doc_type: str) -> float:
    """Calcule un score de pertinence selon le type de document"""
    relevance_map = {
        'Temoignage': 0.9,
        'Expertise': 0.95,
        'Procedure': 0.8,
        'Jugement': 0.85,
        'Contrat': 0.7,
        'Correspondance': 0.6,
        'Autre': 0.5
    }
    return relevance_map.get(doc_type, 0.5)

def estimate_generation_time(mode: str, model_count: int) -> str:
    """Estime le temps de génération"""
    base_times = {
        'single': 15,
        'multi': 20 * model_count,
        'fusion': 25 * model_count + 10
    }
    
    seconds = base_times.get(mode, 30)
    
    if seconds < 60:
        return f"{seconds}s"
    else:
        return f"{seconds // 60}m {seconds % 60}s"

def split_plaidoirie_sections(content: str) -> List[str]:
    """Divise la plaidoirie en sections pour la répétition"""
    # Diviser par sections principales ou paragraphes longs
    sections = re.split(r'\n\n+|(?=[IVX]+\.)|(?=#{2,3})', content)
    
    # Filtrer les sections vides et regrouper les trop courtes
    cleaned_sections = []
    current_section = ""
    
    for section in sections:
        section = section.strip()
        if len(section) < 100:  # Trop court
            current_section += "\n\n" + section
        else:
            if current_section:
                cleaned_sections.append(current_section.strip())
                current_section = ""
            cleaned_sections.append(section)
    
    if current_section:
        cleaned_sections.append(current_section.strip())
    
    return cleaned_sections or [content]

def format_for_rehearsal(text: str) -> str:
    """Formate le texte pour le mode répétition"""
    # Remplacer les marqueurs par des émojis visibles
    formatted = text
    
    # Marqueurs de pause
    formatted = re.sub(r'\[pause\]', '<span style="color: #007bff;">⏸️ [PAUSE]</span>', formatted)
    formatted = re.sub(r'\[silence\]', '<span style="color: #6c757d;">🤫 [SILENCE]</span>', formatted)
    
    # Marqueurs d'emphase
    formatted = re.sub(r'\[insister\](.*?)(?=\[|$)', r'<strong style="color: #dc3545;">\1</strong>', formatted)
    
    # Marqueurs de ton
    formatted = re.sub(r'\[ton:\s*(.*?)\]', r'<em style="color: #28a745;">🎭 (\1)</em>', formatted)
    
    # Marqueurs de geste
    formatted = re.sub(r'\[geste:\s*(.*?)\]', r'<span style="color: #ffc107;">👐 (\1)</span>', formatted)
    
    # Convertir les retours à la ligne
    formatted = formatted.replace('\n', '<br>')
    
    return formatted

def add_to_history(result, config, mode, models):
    """Ajoute une génération à l'historique"""
    history_item = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'type': config.get('audience_type', 'correctionnelle'),
        'style': config.get('style', 'classique'),
        'duration': config.get('duree', '20 min'),
        'mode': mode,
        'models': [m.value for m in models],
        'result': result
    }
    
    if 'history' not in st.session_state.plaidoirie_state:
        st.session_state.plaidoirie_state['history'] = []
    
    st.session_state.plaidoirie_state['history'].append(history_item)
    
    # Limiter l'historique à 10 éléments
    if len(st.session_state.plaidoirie_state['history']) > 10:
        st.session_state.plaidoirie_state['history'] = st.session_state.plaidoirie_state['history'][-10:]

def format_plaidoirie_display(content: str, show_markers: bool, show_sections: bool) -> str:
    """Formate le contenu pour l'affichage"""
    formatted = content
    
    if not show_markers:
        # Supprimer les marqueurs
        formatted = re.sub(r'\[.*?\]', '', formatted)
    else:
        # Formater les marqueurs
        formatted = re.sub(r'\[pause\]', '<span class="oral-marker pause">⏸️</span>', formatted)
        formatted = re.sub(r'\[silence\]', '<span class="oral-marker silence">🤫</span>', formatted)
        formatted = re.sub(r'\[insister\]', '<span class="oral-marker emphasis">💪</span>', formatted)
        formatted = re.sub(r'\[ton:\s*(.*?)\]', r'<span class="oral-marker tone">🎭 \1</span>', formatted)
        formatted = re.sub(r'\[geste:\s*(.*?)\]', r'<span class="oral-marker gesture">👐 \1</span>', formatted)
    
    if show_sections:
        # Numéroter les sections
        section_counter = 1
        formatted = re.sub(
            r'^([IVX]+\.|#{2,3})\s*',
            lambda m: f"<strong>{section_counter}.</strong> ",
            formatted,
            flags=re.MULTILINE
        )
    
    # Convertir en HTML
    formatted = formatted.replace('\n\n', '</p><p>')
    formatted = formatted.replace('\n', '<br>')
    formatted = f"<p>{formatted}</p>"
    
    return formatted

def analyze_plaidoirie_content(content: str) -> Dict[str, Any]:
    """Analyse détaillée du contenu"""
    
    # Nettoyage pour l'analyse
    clean_content = re.sub(r'\[.*?\]', '', content)
    
    words = clean_content.split()
    sentences = re.split(r'[.!?]+', clean_content)
    paragraphs = clean_content.split('\n\n')
    
    # Calculs
    word_count = len(words)
    speaking_time = word_count / 150  # Mots par minute moyen
    
    # Analyse juridique
    legal_terms = ['considérant', 'attendu', 'article', 'jurisprudence', 'doctrine', 
                   'précédent', 'principe', 'règle', 'disposition', 'alinéa']
    legal_count = sum(1 for word in words if word.lower() in legal_terms)
    
    return {
        'word_count': word_count,
        'sentence_count': len(sentences),
        'paragraph_count': len(paragraphs),
        'speaking_time': round(speaking_time),
        'words_per_minute': 150,
        'questions': content.count('?'),
        'exclamations': content.count('!'),
        'legal_density': legal_count / max(word_count, 1),
        'avg_sentence_length': word_count / max(len(sentences), 1)
    }

def render_comparative_analysis(results: List[PlaidoirieResult]):
    """Analyse comparative des résultats multi-modèles"""
    
    st.markdown("#### 🔍 Analyse comparative détaillée")
    
    # Tableau comparatif
    comparison_data = []
    
    for result in results:
        analysis = analyze_plaidoirie_content(result.content)
        
        comparison_data.append({
            'Modèle': result.metadata.get('provider', 'Unknown'),
            'Mots': analysis['word_count'],
            'Temps (min)': analysis['speaking_time'],
            'Questions': analysis['questions'],
            'Points clés': len(result.key_points),
            'Densité juridique': f"{analysis['legal_density']:.1%}"
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Recommandation
    st.markdown("#### 💡 Recommandation")
    
    # Calculer les scores
    scores = []
    for i, result in enumerate(results):
        analysis = analyze_plaidoirie_content(result.content)
        score = calculate_plaidoirie_score(result, analysis)
        scores.append((i, score, result.metadata.get('provider', 'Unknown')))
    
    # Trier par score
    scores.sort(key=lambda x: x[1], reverse=True)
    
    if scores:
        best_idx, best_score, best_provider = scores[0]
        
        st.success(f"🏆 **Meilleure plaidoirie : {best_provider}** (Score: {best_score:.1f}/100)")
        
        # Détails du choix
        with st.expander("📊 Détails de l'évaluation"):
            st.write("**Critères d'évaluation :**")
            st.write("• Structure et organisation")
            st.write("• Richesse argumentative") 
            st.write("• Équilibre émotionnel")
            st.write("• Précision juridique")
            st.write("• Impact oratoire")

def calculate_plaidoirie_score(result: PlaidoirieResult, analysis: Dict[str, Any]) -> float:
    """Calcule un score de qualité pour une plaidoirie"""
    
    score = 0
    
    # Structure (20 points)
    if result.structure:
        score += min(20, len(result.structure) * 4)
    
    # Points clés (20 points)
    score += min(20, len(result.key_points) * 2)
    
    # Longueur appropriée (20 points)
    target_words = {'5 min': 750, '10 min': 1500, '15 min': 2250, '20 min': 3000, 
                   '30 min': 4500, '45 min': 6750, '1h': 9000}
    target = target_words.get(result.duration_estimate, 3000)
    
    deviation = abs(analysis['word_count'] - target) / target
    score += max(0, 20 - (deviation * 40))
    
    # Équilibre questions/affirmations (20 points)
    question_ratio = analysis['questions'] / max(analysis['sentence_count'], 1)
    if 0.05 <= question_ratio <= 0.15:
        score += 20
    else:
        score += max(0, 20 - abs(question_ratio - 0.1) * 100)
    
    # Densité juridique (20 points)
    if 0.02 <= analysis['legal_density'] <= 0.08:
        score += 20
    else:
        score += max(0, 20 - abs(analysis['legal_density'] - 0.05) * 200)
    
    return min(100, score)

def extract_sections_for_fusion(content: str) -> Dict[str, str]:
    """Extrait les sections pour la fusion"""
    sections = {
        'introduction': '',
        'development': '',
        'conclusion': '',
        'citations': []
    }
    
    # Patterns pour identifier les sections
    intro_pattern = r'(Monsieur|Madame|Messieurs).*?(Président|Cour|Tribunal)'
    conclusion_pattern = r'(En conclusion|Pour conclure|Par ces motifs|C\'est pourquoi)'
    
    # Extraction simplifiée
    lines = content.split('\n')
    current_section = 'introduction'
    
    for line in lines:
        if re.search(conclusion_pattern, line, re.IGNORECASE):
            current_section = 'conclusion'
        elif current_section == 'introduction' and len(sections['introduction']) > 500:
            current_section = 'development'
        
        sections[current_section] += line + '\n'
    
    return sections

def evaluate_section_quality(content: str, section_type: str) -> float:
    """Évalue la qualité d'une section"""
    score = 0.5  # Score de base
    
    # Critères par section
    if section_type == 'introduction':
        # Vérifier la présence des éléments clés
        if re.search(r'(Monsieur|Madame).*?(Président|Juge)', content, re.IGNORECASE):
            score += 0.1
        if len(content.split()) > 100:
            score += 0.1
        if '?' in content:  # Question rhétorique
            score += 0.1
    
    elif section_type == 'development':
        # Richesse argumentative
        if len(content.split()) > 500:
            score += 0.1
        if content.count('\n\n') > 3:  # Bonne structure
            score += 0.1
        if re.findall(r'(premièrement|deuxièmement|enfin)', content, re.IGNORECASE):
            score += 0.1
    
    elif section_type == 'conclusion':
        # Force de la conclusion
        if re.search(r'(demande|requiert|sollicite)', content, re.IGNORECASE):
            score += 0.1
        if len(content.split()) > 100:
            score += 0.1
        if content.count('!') > 0:  # Emphase
            score += 0.1
    
    return min(1.0, score)

def build_fused_plaidoirie(best_parts: Dict[str, List[Dict]], config: Dict[str, Any]) -> str:
    """Construit la plaidoirie fusionnée"""
    
    # Sélectionner les meilleures parties
    final_parts = {}
    
    for section, candidates in best_parts.items():
        if candidates and section != 'citations':
            # Trier par score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Prendre le meilleur ou fusionner les top 2
            if len(candidates) >= 2 and candidates[0]['score'] - candidates[1]['score'] < 0.1:
                # Scores proches : fusionner
                final_parts[section] = merge_similar_content(
                    candidates[0]['content'],
                    candidates[1]['content'],
                    section
                )
            else:
                # Score clair : prendre le meilleur
                final_parts[section] = candidates[0]['content']
    
    # Assembler la plaidoirie
    plaidoirie = ""
    
    # Introduction
    if 'introduction' in final_parts:
        plaidoirie += final_parts['introduction'].strip() + "\n\n"
    
    # Développement
    if 'development' in final_parts:
        plaidoirie += final_parts['development'].strip() + "\n\n"
    
    # Conclusion
    if 'conclusion' in final_parts:
        plaidoirie += final_parts['conclusion'].strip()
    
    # Polissage final
    plaidoirie = polish_fused_content(plaidoirie, config)
    
    return plaidoirie

def merge_similar_content(content1: str, content2: str, section_type: str) -> str:
    """Fusionne deux contenus similaires"""
    
    # Stratégie simple : prendre le début du premier et la fin du second
    # Dans une vraie implémentation, utiliser une IA pour fusionner intelligemment
    
    if section_type == 'introduction':
        # Garder la meilleure accroche
        return content1.split('\n\n')[0] + '\n\n' + content2
    
    elif section_type == 'development':
        # Alterner les paragraphes
        para1 = content1.split('\n\n')
        para2 = content2.split('\n\n')
        
        merged = []
        for i in range(max(len(para1), len(para2))):
            if i < len(para1) and i % 2 == 0:
                merged.append(para1[i])
            elif i < len(para2):
                merged.append(para2[i])
        
        return '\n\n'.join(merged)
    
    else:  # conclusion
        # Garder la plus percutante
        return content1 if len(content1) > len(content2) else content2

def polish_fused_content(content: str, config: Dict[str, Any]) -> str:
    """Polit le contenu fusionné"""
    
    # Éliminer les répétitions
    lines = content.split('\n')
    seen = set()
    polished_lines = []
    
    for line in lines:
        # Hash simplifié pour détecter les répétitions
        line_hash = ' '.join(line.lower().split()[:5])
        
        if line_hash not in seen or len(line.strip()) < 10:
            seen.add(line_hash)
            polished_lines.append(line)
    
    polished = '\n'.join(polished_lines)
    
    # Assurer la cohérence des transitions
    transitions = {
        'Premièrement': 'Deuxièmement',
        'Deuxièmement': 'Troisièmement',
        'D\'une part': 'D\'autre part',
        'En premier lieu': 'En second lieu'
    }
    
    for first, second in transitions.items():
        if first in polished and second not in polished:
            # Ajouter la transition manquante si nécessaire
            pass
    
    return polished

# Fonctions d'export améliorées

def generate_pdf_export(result: PlaidoirieResult) -> bytes:
    """Génère un export PDF professionnel"""
    
    # Version simplifiée - dans la vraie app, utiliser reportlab ou weasyprint
    content = f"""PLAIDOIRIE
================================================================================

TYPE D'AUDIENCE : {result.type.upper()}
DURÉE ESTIMÉE : {result.duration_estimate}
STYLE ORATOIRE : {result.style.upper()}
DATE : {datetime.now().strftime('%d/%m/%Y')}

================================================================================

{result.content}

================================================================================

POINTS CLÉS À RETENIR :
"""
    
    for i, point in enumerate(result.key_points, 1):
        content += f"\n{i}. {point}"
    
    content += f"""

================================================================================

STRUCTURE DE LA PLAIDOIRIE :
"""
    
    for section, subsections in result.structure.items():
        content += f"\n\n{section}"
        for sub in subsections:
            content += f"\n  - {sub}"
    
    return content.encode('utf-8')

def create_enhanced_speaker_notes(result: PlaidoirieResult) -> str:
    """Crée des notes améliorées pour l'orateur"""
    
    notes = f"""NOTES POUR L'ORATEUR - PLAIDOIRIE
{'=' * 80}

INFORMATIONS GÉNÉRALES
----------------------
Type d'audience : {result.type}
Durée cible : {result.duration_estimate}
Style oratoire : {result.style}
Nombre de mots : {len(result.content.split())}
Temps de parole estimé : {len(result.content.split()) / 150:.0f} minutes

CONSEILS PERSONNALISÉS
----------------------
"""
    
    # Conseils selon le style
    style_tips = {
        'classique': """
- Maintenir une posture droite et solennelle
- Utiliser des formules consacrées
- Respecter les temps de pause traditionnels
- Voix posée et grave
""",
        'moderne': """
- Établir un contact visuel direct
- Utiliser des exemples concrets
- Varier le rythme de parole
- Gestes naturels et ouverts
""",
        'emotionnel': """
- Moduler la voix selon l'émotion
- Marquer des silences pour l'impact
- Regarder les jurés/juges dans les yeux
- Respirer profondément avant les passages clés
""",
        'technique': """
- Articuler clairement chaque terme juridique
- Utiliser des supports visuels si possible
- Structurer visuellement (compter sur les doigts)
- Ton neutre et factuel
""",
        'percutant': """
- Commencer fort, finir plus fort
- Utiliser l'espace (se déplacer)
- Varier volume et rythme
- Gestes amples et expressifs
"""
    }
    
    notes += style_tips.get(result.style, "- Adapter selon le contexte\n")
    
    notes += f"""
POINTS CLÉS À MARTELER
----------------------
"""
    
    for i, point in enumerate(result.key_points[:5], 1):
        notes += f"{i}. {point}\n   → Insister et ralentir\n\n"
    
    notes += f"""
STRUCTURE AVEC TIMINGS
----------------------
"""
    
    # Estimation des timings par section
    total_words = len(result.content.split())
    
    for section in result.structure:
        section_words = len(section.split()) * 20  # Estimation
        section_time = section_words / 150
        notes += f"\n{section} (~{section_time:.1f} min)"
        notes += f"\n   ⏱️ Checkpoint : regarder l'heure"
    
    notes += f"""

MARQUEURS ORAUX
---------------
Total : {len(result.oral_markers)} marqueurs
"""
    
    marker_counts = {}
    for marker in result.oral_markers:
        marker_type = marker.split(':')[0] if ':' in marker else marker
        marker_counts[marker_type] = marker_counts.get(marker_type, 0) + 1
    
    for marker_type, count in marker_counts.items():
        notes += f"- {marker_type} : {count} occurrences\n"
    
    notes += f"""

TEXTE ANNOTÉ POUR LA PRATIQUE
{'=' * 80}

{result.content}
"""
    
    return notes

def generate_analysis_report(result: PlaidoirieResult) -> str:
    """Génère un rapport d'analyse détaillé"""
    
    analysis = analyze_plaidoirie_content(result.content)
    score = calculate_plaidoirie_score(result, analysis)
    
    report = f"""# Rapport d'Analyse - Plaidoirie

## Métadonnées
- **Type** : {result.type}
- **Durée cible** : {result.duration_estimate}
- **Style** : {result.style}
- **Date de génération** : {datetime.now().strftime('%d/%m/%Y %H:%M')}
- **Modèle IA** : {result.metadata.get('provider', 'Non spécifié')}

## Analyse quantitative

### Métriques textuelles
- **Nombre de mots** : {analysis['word_count']:,}
- **Nombre de phrases** : {analysis['sentence_count']}
- **Nombre de paragraphes** : {analysis['paragraph_count']}
- **Longueur moyenne des phrases** : {analysis['avg_sentence_length']:.1f} mots

### Métriques oratoires
- **Temps de parole estimé** : {analysis['speaking_time']} minutes
- **Cadence** : {analysis['words_per_minute']} mots/minute
- **Questions rhétoriques** : {analysis['questions']}
- **Points d'exclamation** : {analysis['exclamations']}

### Métriques juridiques
- **Densité juridique** : {analysis['legal_density']:.1%}
- **Marqueurs oraux** : {len(result.oral_markers)}
- **Points clés identifiés** : {len(result.key_points)}

## Analyse qualitative

### Structure
"""
    
    for section, subsections in result.structure.items():
        report += f"\n#### {section}\n"
        if subsections:
            for sub in subsections:
                report += f"- {sub}\n"
    
    report += f"""

### Points forts
1. **Cohérence structurelle** : {"Excellente" if len(result.structure) >= 3 else "À améliorer"}
2. **Richesse argumentative** : {"Très bonne" if len(result.key_points) >= 5 else "Correcte"}
3. **Équilibre émotionnel** : {"Adapté au style" if result.style in ['emotionnel', 'percutant'] else "Mesuré"}

### Recommandations d'amélioration
"""
    
    if analysis['avg_sentence_length'] > 25:
        report += "- Raccourcir certaines phrases pour faciliter la respiration\n"
    
    if analysis['legal_density'] > 0.1:
        report += "- Réduire le jargon juridique pour plus d'accessibilité\n"
    
    if analysis['questions'] < 3:
        report += "- Ajouter des questions rhétoriques pour engager l'auditoire\n"
    
    if len(result.oral_markers) < 10:
        report += "- Enrichir avec plus d'indications orales (pauses, emphases)\n"
    
    report += f"""

## Score global

**{score:.1f} / 100**

### Décomposition du score
- Structure et organisation : {min(20, len(result.structure) * 4)}/20
- Points clés : {min(20, len(result.key_points) * 2)}/20
- Longueur appropriée : {max(0, 20 - abs(analysis['word_count'] - 3000) / 150):.0f}/20
- Équilibre questions : {20 if 0.05 <= analysis['questions']/max(analysis['sentence_count'],1) <= 0.15 else 10}/20
- Densité juridique : {20 if 0.02 <= analysis['legal_density'] <= 0.08 else 10}/20

## Conseils d'utilisation

1. **Répétition** : Prévoir {int(analysis['speaking_time'] * 1.5)} minutes avec les pauses
2. **Mémorisation** : Focus sur les {min(3, len(result.key_points))} points clés principaux
3. **Adaptation** : Ajuster le rythme selon les réactions de l'auditoire
4. **Support** : Préparer des notes avec les transitions principales

---
*Rapport généré automatiquement par Nexora Law IA*
"""
    
    return report

def render_section_distribution(result: PlaidoirieResult):
    """Affiche la distribution des sections"""
    # Calculer la répartition
    section_sizes = {}
    total_size = len(result.content)
    
    for section in result.structure:
        # Estimation basique
        section_sizes[section] = len(str(result.structure[section])) / total_size * 100
    
    # Affichage simple avec progress bars
    for section, percentage in section_sizes.items():
        st.write(f"**{section}**")
        st.progress(percentage / 100)
        st.caption(f"{percentage:.1f}% du contenu")

def render_tone_analysis(result: PlaidoirieResult):
    """Analyse de la tonalité"""
    st.write("**Analyse de la tonalité émotionnelle**")
    
    # Analyse basique des émotions
    content_lower = result.content.lower()
    
    emotions = {
        "Conviction": len(re.findall(r'(certain|évident|manifeste|incontestable)', content_lower)),
        "Empathie": len(re.findall(r'(comprendre|souffrance|douleur|victime)', content_lower)),
        "Indignation": len(re.findall(r'(inacceptable|scandaleux|révoltant|choquant)', content_lower)),
        "Espoir": len(re.findall(r'(justice|réparer|avenir|reconstruction)', content_lower))
    }
    
    # Affichage
    for emotion, count in emotions.items():
        st.write(f"{emotion}: {count} occurrences")
        st.progress(min(count / 10, 1.0))

def render_rhythm_analysis(result: PlaidoirieResult):
    """Analyse du rythme oratoire"""
    st.write("**Analyse du rythme et de la cadence**")
    
    # Analyser les variations de longueur de phrase
    sentences = re.split(r'[.!?]+', result.content)
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    
    if sentence_lengths:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Phrase la plus courte", f"{min(sentence_lengths)} mots")
        
        with col2:
            st.metric("Phrase moyenne", f"{sum(sentence_lengths)/len(sentence_lengths):.0f} mots")
        
        with col3:
            st.metric("Phrase la plus longue", f"{max(sentence_lengths)} mots")
        
        # Conseils
        if max(sentence_lengths) > 40:
            st.warning("⚠️ Certaines phrases sont très longues. Pensez à respirer!")
        
        if min(sentence_lengths) < 5:
            st.success("✅ Bonnes phrases courtes pour l'impact")

# Point d'entrée principal
if __name__ == "__main__":
    run()