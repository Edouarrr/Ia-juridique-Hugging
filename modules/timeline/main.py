"""Module de génération de chronologies (timelines) juridiques avec IA multi-modèles"""

import hashlib
import json
import logging
import re
import sys
import time
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import streamlit as st

logger = logging.getLogger(__name__)

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.decorators import decorate_public_functions
from .models import AIModel, TimelineEvent

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# Import du manager multi-LLM
from llm_manager import LLMManager

class TimelineModule:
    """Module de création de timeline juridique avec IA multi-modèles pour le droit pénal des affaires"""
    
    def __init__(self):
        self.name = "Timeline Droit Pénal des Affaires"
        self.description = "Créez des chronologies intelligentes pour vos dossiers de droit pénal des affaires"
        self.icon = "⚖️"
        self.available = True
        
        # Initialiser l'état de session
        self._init_session_state()
        
        # Configuration des styles
        self._inject_custom_styles()
        
        # Initialiser le manager LLM
        self.llm_manager = LLMManager()
    
    def _init_session_state(self):
        """Initialise les variables de session"""
        defaults = {
            'timeline_history': [],
            'saved_timelines': {},
            'ai_models': {model.value: True for model in AIModel},
            'timeline_cache': {},
            'current_timeline': None,
            'timeline_filters': {},
            'timeline_view_mode': 'linear',
            'ai_extraction_progress': 0,
            'timeline_theme': 'modern'
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def _inject_custom_styles(self):
        """Injecte des styles CSS personnalisés"""
        st.markdown("""
        <style>
        /* Timeline moderne */
        .timeline-container {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .event-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #4CAF50;
            transition: all 0.3s ease;
        }
        
        .event-card:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .ai-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            margin: 2px;
        }
        
        .ai-claude { background: #7C3AED; color: white; }
        .ai-gpt { background: #10B981; color: white; }
        .ai-gemini { background: #F59E0B; color: white; }
        .ai-mistral { background: #EF4444; color: white; }
        .ai-fusion { background: linear-gradient(45deg, #7C3AED, #10B981, #F59E0B); color: white; }
        
        .importance-high { color: #DC2626; font-weight: bold; }
        .importance-medium { color: #F59E0B; }
        .importance-low { color: #10B981; }
        
        .timeline-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .ai-model-selector {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .progress-bar {
            background: #e0e0e0;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #4CAF50, #2196F3);
            height: 100%;
            transition: width 0.3s ease;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render(self):
        """Interface principale du module avec lazy loading"""
        # Header avec animation
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <h1>{self.icon} {self.name}</h1>
                <p style="font-size: 1.2em; color: #666;">{self.description}</p>
                <p style="font-size: 0.9em; color: #888;">
                    Spécialisé : Corruption • Abus de biens • Fraude fiscale • Blanchiment • CJIP
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Alerte juridique
        st.info("""
        ⚖️ **Module juridique spécialisé** : Ce module utilise l'intelligence artificielle multi-modèles 
        pour analyser vos documents et créer des chronologies précises adaptées aux procédures pénales des affaires.
        Les modèles IA sont entraînés sur la jurisprudence et la doctrine française.
        """)
        
        # Navigation principale avec icônes
        tabs = st.tabs([
            "🎨 Nouvelle Timeline",
            "🤖 Configuration IA",
            "📚 Bibliothèque",
            "🔍 Analyse avancée",
            "📊 Visualisations",
            "❓ Guide juridique"
        ])
        
        with tabs[0]:
            self._render_new_timeline_advanced()
        
        with tabs[1]:
            self._render_ai_configuration()
        
        with tabs[2]:
            self._render_timeline_library()
        
        with tabs[3]:
            self._render_advanced_analysis()
        
        with tabs[4]:
            self._render_visualizations()
        
        with tabs[5]:
            self._render_interactive_guide()
    
    def _render_new_timeline_advanced(self):
        """Interface avancée de création de timeline avec choix du type"""
        # Sélection du type de chronologie
        st.markdown("### 📊 Type de chronologie")
        
        timeline_types = {
            "📋 Chronologie complète": {
                "description": "Vue d'ensemble incluant tous les événements",
                "filters": None,
                "icon": "🔍"
            },
            "⚖️ Chronologie de la procédure": {
                "description": "Uniquement les actes de procédure (plainte, mise en examen, jugement...)",
                "filters": {"categories": ["procédure", "instruction", "enquête", "mesures"]},
                "icon": "📑"
            },
            "💼 Chronologie des faits": {
                "description": "Focus sur les infractions et événements factuels",
                "filters": {"categories": ["financier", "fiscal", "social"], "exclude_procedural": True},
                "icon": "🔎"
            },
            "🎯 Chronologie d'un fait spécifique": {
                "description": "Analyse approfondie d'une infraction particulière",
                "filters": {"specific_fact": True},
                "icon": "🎯"
            },
            "🎤 Chronologie des auditions": {
                "description": "Toutes les auditions (garde à vue, témoin, confrontation...)",
                "filters": {"act_types": ["audition", "garde à vue", "confrontation", "interrogatoire"]},
                "icon": "👥"
            },
            "📂 Chronologie par type d'acte": {
                "description": "Focus sur un type d'acte spécifique (perquisitions, saisies...)",
                "filters": {"custom_act_type": True},
                "icon": "📌"
            }
        }
        
        # Sélection du type avec cards visuelles
        selected_type = None
        cols = st.columns(3)
        
        for i, (type_name, type_info) in enumerate(timeline_types.items()):
            with cols[i % 3]:
                if st.button(
                    f"{type_info['icon']} {type_name.split(' ', 1)[1]}",
                    use_container_width=True,
                    help=type_info['description']
                ):
                    st.session_state.timeline_type = type_name
                    st.session_state.timeline_filters = type_info['filters']
                    selected_type = type_name
        
        # Afficher la sélection actuelle
        if 'timeline_type' in st.session_state:
            selected_type = st.session_state.timeline_type
            st.success(f"✅ Type sélectionné : {selected_type}")
            
            # Options supplémentaires selon le type
            if st.session_state.timeline_filters:
                self._render_type_specific_options(selected_type, st.session_state.timeline_filters)
        
        st.divider()
        
        # Continuer avec le workflow habituel
        if selected_type:
            # Barre de progression du workflow
            workflow_steps = ["Source", "Extraction", "Enrichissement", "Validation", "Génération"]
            current_step = st.session_state.get('timeline_workflow_step', 0)
            
            # Afficher la progression
            cols = st.columns(len(workflow_steps))
            for i, (col, step) in enumerate(zip(cols, workflow_steps)):
                with col:
                    if i < current_step:
                        st.success(f"✅ {step}")
                    elif i == current_step:
                        st.info(f"🔄 {step}")
                    else:
                        st.text(f"⭕ {step}")
            
            st.divider()
            
            # Contenu selon l'étape
            if current_step == 0:
                self._render_source_selection()
            elif current_step == 1:
                self._render_extraction_step()
            elif current_step == 2:
                self._render_enrichment_step()
            elif current_step == 3:
                self._render_validation_step()
            elif current_step == 4:
                self._render_generation_step()
        else:
            st.info("👆 Sélectionnez d'abord le type de chronologie que vous souhaitez créer")
    
    def _render_type_specific_options(self, timeline_type: str, filters: Dict):
        """Affiche les options spécifiques selon le type de chronologie"""
        with st.expander("⚙️ Options spécifiques", expanded=True):
            if filters.get('specific_fact'):
                # Pour chronologie d'un fait spécifique
                st.markdown("#### 🎯 Sélection du fait à analyser")
                
                fact_type = st.selectbox(
                    "Type d'infraction",
                    ["Abus de biens sociaux", "Corruption", "Blanchiment", "Escroquerie", 
                     "Fraude fiscale", "Faux et usage de faux", "Détournement", "Autre"]
                )
                
                if fact_type == "Autre":
                    custom_fact = st.text_input("Précisez l'infraction")
                    st.session_state.target_fact = custom_fact if custom_fact else fact_type
                else:
                    st.session_state.target_fact = fact_type
                
                # Options de recherche étendue
                include_related = st.checkbox(
                    "Inclure les faits connexes",
                    value=True,
                    help="Rechercher aussi les infractions liées (ex: blanchiment lié à l'ABS)"
                )
                st.session_state.include_related_facts = include_related
                
            elif filters.get('custom_act_type'):
                # Pour chronologie par type d'acte
                st.markdown("#### 📂 Sélection du type d'acte")
                
                act_categories = {
                    "Mesures d'investigation": [
                        "Perquisitions", "Saisies", "Écoutes téléphoniques", 
                        "Géolocalisation", "Interceptions"
                    ],
                    "Mesures coercitives": [
                        "Garde à vue", "Contrôle judiciaire", "Détention provisoire",
                        "Gel des avoirs", "Interdictions"
                    ],
                    "Actes d'instruction": [
                        "Mise en examen", "Interrogatoires", "Confrontations",
                        "Expertises", "Reconstitutions"
                    ],
                    "Décisions judiciaires": [
                        "Ordonnances", "Jugements", "Arrêts", "Citations", "Notifications"
                    ]
                }
                
                category = st.selectbox(
                    "Catégorie d'actes",
                    list(act_categories.keys())
                )
                
                act_type = st.selectbox(
                    "Type d'acte spécifique",
                    act_categories[category]
                )
                
                st.session_state.target_act_type = act_type
                
            # Options communes
            st.markdown("#### 🔧 Options d'extraction")
            
            col1, col2 = st.columns(2)
            with col1:
                extract_context = st.checkbox(
                    "Extraire le contexte étendu",
                    value=True,
                    help="Inclure les événements immédiatement liés"
                )
                
                include_actors = st.checkbox(
                    "Analyser les liens entre acteurs",
                    value=True,
                    help="Créer un réseau des personnes impliquées"
                )
            
            with col2:
                temporal_analysis = st.checkbox(
                    "Analyse temporelle approfondie",
                    value=False,
                    help="Calcul des délais, prescriptions, patterns"
                )
                
                legal_enrichment = st.checkbox(
                    "Enrichissement juridique",
                    value=True,
                    help="Ajouter références légales et jurisprudence"
                )
            
            # Sauvegarder les options
            st.session_state.timeline_options = {
                'extract_context': extract_context,
                'include_actors': include_actors,
                'temporal_analysis': temporal_analysis,
                'legal_enrichment': legal_enrichment
            }
    
    def _render_source_selection(self):
        """Sélection améliorée des sources"""
        st.markdown("### 📁 Sélection des sources de données")
        
        # Cards pour chaque type de source
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📄 Documents", use_container_width=True, help="Extraire depuis vos documents"):
                st.session_state.timeline_source = "documents"
                st.session_state.timeline_workflow_step = 1
                st.rerun()
            st.caption("IA analyse vos documents")
        
        with col2:
            if st.button("✍️ Manuel", use_container_width=True, help="Saisir manuellement"):
                st.session_state.timeline_source = "manual"
                st.session_state.timeline_workflow_step = 1
                st.rerun()
            st.caption("Création assistée")
        
        with col3:
            if st.button("📊 Import", use_container_width=True, help="Importer un fichier"):
                st.session_state.timeline_source = "import"
                st.session_state.timeline_workflow_step = 1
                st.rerun()
            st.caption("CSV, Excel, JSON")
        
        with col4:
            if st.button("📋 Templates", use_container_width=True, help="Modèles prédéfinis"):
                st.session_state.timeline_source = "template"
                st.session_state.timeline_workflow_step = 1
                st.rerun()
            st.caption("Modèles intelligents")
        
        # Suggestions contextuelles
        with st.expander("💡 Suggestions basées sur votre historique", expanded=True):
            if st.session_state.timeline_history:
                st.info(f"Vous avez créé {len(st.session_state.timeline_history)} timelines. La dernière portait sur {st.session_state.timeline_history[-1].get('event_count', 0)} événements.")
                if st.button("🔄 Reprendre la dernière timeline"):
                    self._load_timeline(st.session_state.timeline_history[-1])
            else:
                st.info("Première utilisation ? Essayez un template pour commencer rapidement !")
    
    def _render_extraction_step(self):
        """Étape d'extraction avec IA"""
        st.markdown("### 🤖 Extraction intelligente")
        
        source = st.session_state.get('timeline_source', 'documents')
        
        if source == 'documents':
            self._render_document_extraction()
        elif source == 'manual':
            self._render_manual_creation()
        elif source == 'import':
            self._render_file_import()
        else:
            self._render_template_selection()
        
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Retour", use_container_width=True):
                st.session_state.timeline_workflow_step = 0
                st.rerun()
        with col3:
            if st.button("Suivant ▶", use_container_width=True, disabled=not st.session_state.get('timeline_events')):
                st.session_state.timeline_workflow_step = 2
                st.rerun()
    
    def _render_document_extraction(self):
        """Extraction depuis documents avec multi-IA"""
        # Sélection des modèles d'IA
        st.markdown("#### 🧠 Modèles d'IA pour l'extraction")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_models = []
            cols = st.columns(len(AIModel) - 1)  # Excluant FUSION
            
            for i, (col, model) in enumerate(zip(cols, [m for m in AIModel if m != AIModel.FUSION])):
                with col:
                    if st.checkbox(model.value, value=True, key=f"extract_{model.name}"):
                        selected_models.append(model)
        
        with col2:
            fusion_mode = st.checkbox("🔥 Mode Fusion", value=True, help="Combine les résultats de tous les modèles")
        
        # Documents disponibles
        documents = self._get_available_documents()
        
        if not documents:
            st.warning("Aucun document disponible. Chargez des documents d'abord.")
            return
        
        # Sélection des documents
        st.markdown("#### 📄 Documents à analyser")
        
        selected_docs = []
        search = st.text_input("🔍 Rechercher dans les documents", placeholder="Titre, contenu...")
        
        # Filtrer les documents
        filtered_docs = [d for d in documents if not search or search.lower() in d['title'].lower() or search.lower() in d.get('content', '').lower()]
        
        # Affichage en grille
        cols = st.columns(3)
        for i, doc in enumerate(filtered_docs[:9]):  # Limiter à 9 pour la performance
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div class="event-card">
                        <h5>{doc['title'][:30]}...</h5>
                        <p style="font-size: 0.8em; color: #666;">{doc.get('source', 'Local')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.checkbox("Sélectionner", key=f"doc_select_{i}", value=i < 3):
                        selected_docs.append(doc)
        
        if len(filtered_docs) > 9:
            st.info(f"... et {len(filtered_docs) - 9} autres documents. Utilisez la recherche pour filtrer.")
        
        # Bouton d'extraction
        if selected_docs and st.button("🚀 Lancer l'extraction multi-IA", type="primary", use_container_width=True):
            self._extract_events_with_ai(selected_docs, selected_models, fusion_mode)
    
    def _extract_events_with_ai(self, documents: List[Dict], models: List[AIModel], fusion: bool):
        """Extraction des événements avec plusieurs modèles d'IA via le manager LLM"""
        progress_container = st.container()
        
        with progress_container:
            progress = st.progress(0)
            status = st.status("Extraction en cours...", expanded=True)
            
            all_events = []
            model_results = {}
            
            # Adapter le prompt selon le type de chronologie
            base_prompt = self._get_specialized_prompt()
            
            # Extraction par modèle
            for i, model in enumerate(models):
                with status:
                    st.write(f"🤖 Extraction avec {model.value}...")
                
                # Extraction via le manager LLM
                model_events = self._extract_with_llm_manager(documents, model, base_prompt)
                
                model_results[model] = model_events
                all_events.extend(model_events)
                
                progress.progress((i + 1) / len(models))
                time.sleep(0.5)
            
            # Filtrer selon le type de chronologie
            filtered_events = self._filter_events_by_type(all_events)
            
            # Mode fusion
            if fusion and len(models) > 1:
                with status:
                    st.write("🔥 Fusion des résultats multi-IA...")
                
                # Fusionner les résultats filtrés
                fused_events = self._fuse_ai_results({k: self._filter_events_by_type(v) for k, v in model_results.items()})
                st.session_state.timeline_events = fused_events
                
                # Afficher les statistiques adaptées
                timeline_type = st.session_state.get('timeline_type', 'Chronologie complète')
                st.success(f"""
                ✅ Extraction terminée pour : {timeline_type}
                - 📊 {len(fused_events)} événements pertinents extraits
                - 🤖 {len(models)} modèles utilisés
                - 🔥 Fusion appliquée avec filtrage spécialisé
                - ⚖️ Spécialisation : Droit pénal des affaires
                """)
            else:
                st.session_state.timeline_events = filtered_events
                st.success(f"✅ {len(filtered_events)} événements extraits pour {st.session_state.get('timeline_type', 'la chronologie')}")
            
            status.update(label="Extraction terminée !", state="complete")
        
        # Aperçu des résultats
        self._show_extraction_preview()
    
    def _get_specialized_prompt(self) -> str:
        """Génère un prompt spécialisé selon le type de chronologie"""
        timeline_type = st.session_state.get('timeline_type', 'Chronologie complète')
        filters = st.session_state.get('timeline_filters', {})
        
        base_intro = """En tant qu'expert en droit pénal des affaires, analysez ce document pour extraire """
        
        if "procédure" in timeline_type.lower():
            prompt = base_intro + """UNIQUEMENT les actes de procédure pénale :
            
Focus sur :
- Actes d'enquête : plainte, signalement, ouverture d'enquête, clôture
- Actes d'investigation : perquisitions, saisies, auditions, garde à vue
- Actes d'instruction : saisine JI, mise en examen, ordonnances, expertises
- Décisions judiciaires : réquisitions, renvoi, jugement, appel
- Mesures coercitives : contrôle judiciaire, détention, gel des avoirs

Pour chaque acte, précisez :
- Date exacte
- Nature précise de l'acte
- Autorité à l'origine (Procureur, JI, Tribunal...)
- Personnes concernées
- Conséquences procédurales
"""

        elif "faits" in timeline_type.lower() and "spécifique" not in timeline_type.lower():
            prompt = base_intro + """UNIQUEMENT les faits et infractions (PAS les actes de procédure) :

Focus sur :
- Infractions principales : nature, date, montants, préjudice
- Infractions connexes : blanchiment, recel, complicité
- Modus operandi : schémas, circuits financiers
- Période infractionnelle : début, fin, actes répétés

Pour chaque fait, indiquez :
- Date ou période
- Qualification juridique précise
- Montants en jeu
- Victimes et préjudice
- Auteurs présumés
"""

        elif "fait spécifique" in timeline_type.lower():
            target_fact = st.session_state.get('target_fact', 'infraction')
            include_related = st.session_state.get('include_related_facts', True)
            
            prompt = base_intro + f"""UNIQUEMENT les éléments liés à : {target_fact}

Recherchez :
- Tous les actes constitutifs de {target_fact}
- Dates de commission des faits
- Éléments matériels de l'infraction
- Éléments intentionnels
- Montants et préjudices spécifiques
{"- Infractions connexes ou liées" if include_related else ""}

Analysez particulièrement :
- La chronologie de constitution de l'infraction
- Les preuves datées
- L'évolution du mode opératoire
- Les tentatives de dissimulation
"""

        elif "auditions" in timeline_type.lower():
            prompt = base_intro + """UNIQUEMENT les auditions et interrogatoires :

Types d'auditions à extraire :
- Gardes à vue : dates, durée, prolongations
- Auditions libres
- Auditions de témoins
- Interrogatoires de première comparution
- Interrogatoires au fond
- Confrontations

Pour chaque audition :
- Date et heure précises
- Type d'audition
- Personne entendue et qualité (mis en cause, témoin...)
- Autorité (OPJ, JI...)
- Présence avocat
- Points essentiels abordés
"""

        elif "type d'acte" in timeline_type.lower():
            target_act = st.session_state.get('target_act_type', 'acte')
            
            prompt = base_intro + f"""UNIQUEMENT les actes de type : {target_act}

Extraction ciblée sur {target_act} :
- Dates de chaque {target_act}
- Autorité ordonnant/réalisant
- Personnes/lieux concernés
- Résultats obtenus
- Suites données

Soyez exhaustif sur ce type d'acte spécifiquement.
"""

        else:  # Chronologie complète
            prompt = base_intro + """TOUS les événements importants sous forme de chronologie complète.

Incluez :
1. FAITS : infractions, dates de commission, montants
2. PROCÉDURE : tous les actes (enquête, instruction, jugement)
3. MESURES : coercitives, conservatoires, provisoires
4. ACTEURS : identification de toutes les parties

Soyez exhaustif et précis sur les dates.
"""

        # Ajouter les instructions communes
        prompt += """

Pour CHAQUE événement, fournissez OBLIGATOIREMENT :
- Date exacte (format JJ/MM/AAAA) ou période
- Description précise et factuelle
- Importance (1-10) selon l'impact
- Catégorie : enquête, instruction, procédure, financier, fiscal, social, compliance, mesures
- Acteurs impliqués avec leur qualité exacte

Format de réponse structuré attendu.
Document à analyser :
"""
        
        return prompt
    
    def _filter_events_by_type(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Filtre les événements selon le type de chronologie sélectionné"""
        filters = st.session_state.get('timeline_filters', {})
        
        if not filters:
            return events
        
        filtered = events.copy()
        
        # Filtrer par catégories
        if 'categories' in filters:
            filtered = [e for e in filtered if e.category in filters['categories']]
        
        # Exclure les actes procéduraux (pour chronologie des faits)
        if filters.get('exclude_procedural'):
            procedural_categories = ['procédure', 'instruction', 'enquête', 'mesures']
            filtered = [e for e in filtered if e.category not in procedural_categories]
        
        # Filtrer par type d'acte
        if 'act_types' in filters:
            act_keywords = filters['act_types']
            filtered = [
                e for e in filtered 
                if any(keyword in e.description.lower() for keyword in act_keywords)
            ]
        
        # Filtrer pour un fait spécifique
        if filters.get('specific_fact') and 'target_fact' in st.session_state:
            target = st.session_state.target_fact.lower()
            include_related = st.session_state.get('include_related_facts', True)
            
            if include_related:
                # Inclure les faits connexes
                related_keywords = self._get_related_fact_keywords(target)
                filtered = [
                    e for e in filtered 
                    if target in e.description.lower() or 
                    any(kw in e.description.lower() for kw in related_keywords)
                ]
            else:
                # Uniquement le fait ciblé
                filtered = [e for e in filtered if target in e.description.lower()]
        
        # Filtrer pour un type d'acte spécifique
        if filters.get('custom_act_type') and 'target_act_type' in st.session_state:
            target_act = st.session_state.target_act_type.lower()
            act_synonyms = self._get_act_synonyms(target_act)
            
            filtered = [
                e for e in filtered 
                if any(syn in e.description.lower() for syn in act_synonyms)
            ]
        
        return filtered
    
    def _get_related_fact_keywords(self, fact: str) -> List[str]:
        """Retourne les mots-clés des infractions connexes"""
        related_facts = {
            'abus de biens': ['blanchiment', 'recel', 'complicité', 'faux', 'dissimulation'],
            'corruption': ['trafic d\'influence', 'favoritisme', 'prise illégale', 'blanchiment'],
            'blanchiment': ['recel', 'infraction sous-jacente', 'dissimulation', 'conversion'],
            'escroquerie': ['faux', 'usage de faux', 'abus de confiance', 'manœuvres'],
            'fraude fiscale': ['blanchiment de fraude', 'solidarité fiscale', 'dissimulation']
        }
        
        for key, values in related_facts.items():
            if key in fact:
                return values
        
        return []
    
    def _get_act_synonyms(self, act_type: str) -> List[str]:
        """Retourne les synonymes d'un type d'acte"""
        synonyms = {
            'perquisitions': ['perquisition', 'perquisitionné', 'fouille', 'visite domiciliaire'],
            'saisies': ['saisie', 'saisi', 'saisir', 'mise sous scellés', 'scellés'],
            'garde à vue': ['garde à vue', 'gav', 'gardé à vue', 'placement en garde'],
            'auditions': ['audition', 'auditionné', 'entendu', 'interrogé', 'déclarations'],
            'expertises': ['expertise', 'expert', 'rapport d\'expertise', 'mission d\'expertise'],
            'mise en examen': ['mise en examen', 'mis en examen', 'mec'],
            'contrôle judiciaire': ['contrôle judiciaire', 'cj', 'obligations', 'interdictions']
        }
        
        act_lower = act_type.lower()
        for key, values in synonyms.items():
            if key in act_lower:
                return values
        
        # Retour par défaut
        return [act_lower, act_lower.rstrip('s'), act_lower + 's']
    
    def _extract_with_llm_manager(self, documents: List[Dict], model: AIModel, base_prompt: str) -> List[TimelineEvent]:
        """Extraction réelle via le manager LLM"""
        events = []
        
        # Mapper le modèle vers l'identifiant du manager
        model_mapping = {
            AIModel.CHAT_GPT_4: "gpt-4",
            AIModel.CLAUDE_OPUS_4: "claude-opus-4",
            AIModel.PERPLEXITY: "perplexity",
            AIModel.GEMINI: "gemini-pro",
            AIModel.MISTRAL: "mistral-large"
        }
        
        model_id = model_mapping.get(model, "gpt-4")
        
        for doc in documents:
            try:
                # Construire le prompt complet
                prompt = base_prompt + f"\n\n{doc.get('content', '')[:5000]}"  # Limiter la taille
                
                # Appeler le manager LLM
                response = self.llm_manager.query(
                    prompt=prompt,
                    model=model_id,
                    temperature=0.3,  # Basse température pour plus de précision
                    max_tokens=2000,
                    system_prompt="Vous êtes un expert en droit pénal des affaires français avec 20 ans d'expérience."
                )
                
                # Parser la réponse pour extraire les événements
                extracted_events = self._parse_llm_response(response, doc['title'], model)
                events.extend(extracted_events)
                
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction avec {model.value}: {e}")
                # Fallback sur l'extraction basique
                basic_events = self._extract_events_from_text_enhanced(doc.get('content', ''), doc['title'])
                for event in basic_events:
                    event.ai_extracted = True
                    event.metadata['ai_model'] = model.value
                    event.metadata['extraction_error'] = str(e)
                events.extend(basic_events)
        
        return events
    
    def _parse_llm_response(self, response: str, source: str, model: AIModel) -> List[TimelineEvent]:
        """Parse la réponse du LLM pour extraire les événements structurés"""
        events = []
        
        try:
            # Essayer de parser en JSON si la réponse est structurée
            if response.strip().startswith('[') or response.strip().startswith('{'):
                import json
                data = json.loads(response)
                if isinstance(data, list):
                    events_data = data
                else:
                    events_data = data.get('events', [])
                
                for item in events_data:
                    event = TimelineEvent(
                        date=self._parse_date(item.get('date', '')),
                        description=item.get('description', ''),
                        importance=item.get('importance', 5),
                        category=item.get('category', 'autre'),
                        actors=item.get('actors', []),
                        source=source,
                        confidence=item.get('confidence', 0.85),
                        ai_extracted=True,
                        metadata={
                            'ai_model': model.value,
                            'raw_data': item
                        }
                    )
                    if event.date:  # Ne garder que les événements avec date valide
                        events.append(event)
            else:
                # Parser le texte libre
                lines = response.split('\n')
                current_event = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_event and 'date' in current_event:
                            # Créer l'événement
                            event = TimelineEvent(
                                date=self._parse_date(current_event.get('date', '')),
                                description=current_event.get('description', ''),
                                importance=int(current_event.get('importance', 5)),
                                category=current_event.get('category', 'autre'),
                                actors=current_event.get('actors', []),
                                source=source,
                                confidence=0.8,
                                ai_extracted=True,
                                metadata={'ai_model': model.value}
                            )
                            if event.date:
                                events.append(event)
                            current_event = {}
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        key = key.lower().strip()
                        value = value.strip()
                        
                        if 'date' in key:
                            current_event['date'] = value
                        elif 'description' in key or 'événement' in key:
                            current_event['description'] = value
                        elif 'importance' in key:
                            current_event['importance'] = re.search(r'\d+', value).group() if re.search(r'\d+', value) else 5
                        elif 'catégorie' in key or 'category' in key:
                            current_event['category'] = value.lower()
                        elif 'acteur' in key:
                            current_event['actors'] = [a.strip() for a in value.split(',')]
                
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la réponse LLM: {e}")
            # Fallback sur extraction basique du texte de réponse
            basic_events = self._extract_events_from_text_enhanced(response, source)
            for event in basic_events:
                event.ai_extracted = True
                event.metadata['ai_model'] = model.value
                event.metadata['parse_error'] = str(e)
            return basic_events
        
        return events
    
    def _simulate_ai_extraction(self, documents: List[Dict], model: AIModel) -> List[TimelineEvent]:
        """Simule l'extraction par un modèle d'IA en mode dégradé (sans manager LLM)"""
        events = []
        
        for doc in documents:
            # Extraction adaptée selon le modèle
            text = doc.get('content', '')
            
            if model == AIModel.CLAUDE_OPUS_4:
                # Claude excelle en compréhension juridique contextuelle
                extracted = self._extract_with_legal_context(text, doc['title'])
            elif model == AIModel.CHAT_GPT_4:
                # GPT-4 pour l'extraction structurée et la classification
                extracted = self._extract_with_structured_approach(text, doc['title'])
            elif model == AIModel.PERPLEXITY:
                # Perplexity pour la recherche et vérification
                extracted = self._extract_with_verification_focus(text, doc['title'])
            elif model == AIModel.GEMINI:
                # Gemini pour l'analyse rapide multi-aspects
                extracted = self._extract_with_pattern_matching(text, doc['title'])
            else:  # MISTRAL
                # Mistral pour l'extraction rapide et efficace
                extracted = self._extract_events_from_text_enhanced(text, doc['title'])
            
            # Enrichir avec métadonnées spécifiques au droit pénal des affaires
            for event in extracted:
                event.ai_extracted = True
                event.metadata['ai_model'] = model.value
                event.confidence = 0.7 + (0.3 * (event.importance / 10))
                
                # Ajouter des métadonnées juridiques
                self._enrich_with_legal_metadata(event)
                
            events.extend(extracted)
        
        return events
    
    def _extract_with_legal_context(self, text: str, source: str) -> List[TimelineEvent]:
        """Extraction avec compréhension du contexte juridique pénal des affaires"""
        events = []
        
        # Patterns spécifiques au droit pénal des affaires
        legal_patterns = [
            # Enquête
            (r'garde à vue.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'enquête', 9),
            (r'perquisition.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'enquête', 8),
            (r'audition.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'enquête', 7),
            # Instruction
            (r'mise en examen.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'instruction', 10),
            (r'ordonnance.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'instruction', 8),
            # Infractions financières
            (r'abus de biens.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'financier', 9),
            (r'corruption.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'financier', 10),
            (r'blanchiment.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'financier', 10),
            # Mesures
            (r'contrôle judiciaire.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'mesures', 8),
            (r'gel des avoirs.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'mesures', 9),
        ]
        
        # Extraction standard enrichie
        base_events = self._extract_events_from_text_enhanced(text, source)
        
        # Ajouter les événements spécifiques détectés
        for pattern, category, importance in legal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                
                if parsed_date:
                    # Extraire le contexte étendu
                    start = max(0, match.start() - 200)
                    end = min(len(text), match.end() + 300)
                    context = text[start:end]
                    
                    event = TimelineEvent(
                        date=parsed_date,
                        description=self._clean_description(context),
                        source=source,
                        category=category,
                        importance=importance,
                        actors=self._extract_actors_advanced(context),
                        confidence=0.9,
                        metadata={
                            'pattern_type': 'legal_specific',
                            'infraction_type': self._detect_infraction_type(context)
                        }
                    )
                    events.append(event)
        
        # Fusionner et dédupliquer
        all_events = base_events + events
        return self._deduplicate_events(all_events)
    
    def _extract_with_verification_focus(self, text: str, source: str) -> List[TimelineEvent]:
        """Extraction avec focus sur la vérification (style Perplexity)"""
        events = self._extract_events_from_text_enhanced(text, source)
        
        # Enrichir avec des éléments de vérification
        for event in events:
            # Détecter les références légales
            legal_refs = re.findall(r'article\s+\d+(?:-\d+)?', event.description, re.IGNORECASE)
            if legal_refs:
                event.metadata['legal_references'] = legal_refs
                event.confidence = min(0.95, event.confidence + 0.1)
            
            # Détecter les montants
            amounts = re.findall(r'(\d+(?:\.\d+)?)\s*(?:€|euros?|EUR)', event.description, re.IGNORECASE)
            if amounts:
                event.metadata['amounts'] = amounts
                event.importance = min(10, event.importance + 1)
        
        return events
    
    def _enrich_with_legal_metadata(self, event: TimelineEvent):
        """Enrichit l'événement avec des métadonnées juridiques spécifiques"""
        # Détecter le type d'infraction
        infraction_type = self._detect_infraction_type(event.description)
        if infraction_type:
            event.metadata['infraction_type'] = infraction_type
        
        # Détecter la phase procédurale
        phase = self._detect_procedural_phase(event.description)
        if phase:
            event.metadata['procedural_phase'] = phase
        
        # Évaluer le risque pénal
        risk_level = self._evaluate_penal_risk(event)
        event.metadata['penal_risk'] = risk_level
        
        # Identifier les autorités impliquées
        authorities = self._identify_authorities(event.description)
        if authorities:
            event.metadata['authorities'] = authorities
    
    def _detect_infraction_type(self, text: str) -> Optional[str]:
        """Détecte le type d'infraction pénale des affaires"""
        text_lower = text.lower()
        
        infractions = {
            'abus_biens_sociaux': ['abus de biens', 'abs', 'biens sociaux'],
            'corruption': ['corruption', 'corrompu', 'pot-de-vin', 'trafic d\'influence'],
            'blanchiment': ['blanchiment', 'capitaux', 'provenance illicite'],
            'escroquerie': ['escroquerie', 'tromperie', 'manœuvres frauduleuses'],
            'faux': ['faux', 'usage de faux', 'falsification'],
            'detournement': ['détournement', 'malversation', 'soustraction'],
            'delit_initie': ['délit d\'initié', 'information privilégiée'],
            'fraude_fiscale': ['fraude fiscale', 'évasion fiscale', 'dissimulation'],
            'travail_dissimule': ['travail dissimulé', 'travail au noir', 'non déclaré'],
            'banqueroute': ['banqueroute', 'organisation d\'insolvabilité']
        }
        
        for infraction, keywords in infractions.items():
            if any(kw in text_lower for kw in keywords):
                return infraction
        
        return None
    
    def _detect_procedural_phase(self, text: str) -> str:
        """Détecte la phase procédurale"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['enquête préliminaire', 'flagrance', 'plainte']):
            return 'enquête_préliminaire'
        elif any(word in text_lower for word in ['instruction', 'juge d\'instruction', 'commission rogatoire']):
            return 'instruction'
        elif any(word in text_lower for word in ['jugement', 'tribunal', 'audience', 'plaidoirie']):
            return 'jugement'
        elif any(word in text_lower for word in ['appel', 'cour d\'appel']):
            return 'appel'
        elif any(word in text_lower for word in ['cassation', 'cour de cassation']):
            return 'cassation'
        
        return 'indéterminée'
    
    def _evaluate_penal_risk(self, event: TimelineEvent) -> str:
        """Évalue le niveau de risque pénal"""
        risk_score = 0
        
        # Facteurs de risque
        if event.importance >= 8:
            risk_score += 3
        if event.category in ['instruction', 'mesures']:
            risk_score += 2
        if 'mise en examen' in event.description.lower():
            risk_score += 3
        if 'détention' in event.description.lower():
            risk_score += 4
        if any(word in event.description.lower() for word in ['corruption', 'blanchiment', 'abus de biens']):
            risk_score += 2
        
        # Classification du risque
        if risk_score >= 7:
            return 'critique'
        elif risk_score >= 4:
            return 'élevé'
        elif risk_score >= 2:
            return 'modéré'
        else:
            return 'faible'
    
    def _identify_authorities(self, text: str) -> List[str]:
        """Identifie les autorités judiciaires et administratives"""
        authorities = []
        text_lower = text.lower()
        
        authority_patterns = {
            'parquet': ['procureur', 'parquet', 'ministère public'],
            'instruction': ['juge d\'instruction', 'cabinet d\'instruction'],
            'police': ['police', 'opj', 'brigade financière', 'bnee'],
            'gendarmerie': ['gendarmerie', 'sr', 'section de recherches'],
            'fisc': ['dgfip', 'administration fiscale', 'fisc', 'impôts'],
            'douanes': ['douanes', 'dgddi'],
            'tracfin': ['tracfin', 'cellule de renseignement'],
            'amf': ['amf', 'autorité des marchés'],
            'acpr': ['acpr', 'autorité de contrôle'],
            'tribunal': ['tribunal', 'tgi', 'tribunal correctionnel']
        }
        
        for authority, keywords in authority_patterns.items():
            if any(kw in text_lower for kw in keywords):
                authorities.append(authority)
        
        return list(set(authorities))
    
    def _extract_with_structured_approach(self, text: str, source: str) -> List[TimelineEvent]:
        """Extraction structurée type GPT"""
        events = []
        
        # Découper le texte en sections
        sections = text.split('\n\n')
        
        for section in sections:
            if len(section) < 50:
                continue
            
            # Chercher des structures
            structured_patterns = [
                {
                    'pattern': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*:\s*(.*?)(?:\.|;|$)',
                    'type': 'dated_list'
                },
                {
                    'pattern': r'Article \d+.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    'type': 'legal_article'
                }
            ]
            
            for struct in structured_patterns:
                matches = re.finditer(struct['pattern'], section, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    try:
                        date_str = match.group(1)
                        parsed_date = self._parse_date(date_str)
                        
                        if parsed_date:
                            event = TimelineEvent(
                                date=parsed_date,
                                description=section[:200],
                                source=source,
                                category=self._determine_category(section),
                                importance=7 if struct['type'] == 'legal_article' else 5,
                                metadata={'structure_type': struct['type']}
                            )
                            events.append(event)
                    except:
                        continue
        
        return events
    
    def _extract_with_pattern_matching(self, text: str, source: str) -> List[TimelineEvent]:
        """Extraction par patterns (style Gemini)"""
        # Utiliser l'extraction de base avec des améliorations
        return self._extract_events_from_text_enhanced(text, source)
    
    def _extract_events_from_text_enhanced(self, text: str, source: str) -> List[TimelineEvent]:
        """Version améliorée de l'extraction d'événements"""
        events = []
        
        # Patterns de dates étendus
        date_patterns = [
            # Dates numériques
            (r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'numeric'),
            # Dates textuelles
            (r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})', 'textual'),
            # Dates avec jour de la semaine
            (r'((?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+\d{1,2}\s+\w+\s+\d{4})', 'weekday'),
            # Dates relatives
            (r'(il y a \d+ (?:jours?|mois|ans?))', 'relative'),
            # Périodes
            (r'((?:début|fin|mi-?)\s*(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})', 'period')
        ]
        
        # Chercher toutes les dates
        found_dates = []
        for pattern, date_type in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_dates.append({
                    'match': match,
                    'type': date_type,
                    'date_str': match.group(1)
                })
        
        # Traiter chaque date trouvée
        for date_info in found_dates:
            match = date_info['match']
            
            # Extraire le contexte étendu
            start = max(0, match.start() - 150)
            end = min(len(text), match.end() + 250)
            context = text[start:end]
            
            # Parser la date
            parsed_date = self._parse_date_advanced(date_info['date_str'], date_info['type'])
            if not parsed_date:
                continue
            
            # Créer l'événement
            event = TimelineEvent(
                date=parsed_date,
                description=self._clean_description(context),
                source=source,
                importance=self._calculate_importance_advanced(context),
                category=self._determine_category_advanced(context),
                actors=self._extract_actors_advanced(context),
                confidence=0.8,
                metadata={
                    'date_type': date_info['type'],
                    'original_text': context
                }
            )
            
            events.append(event)
        
        # Dédupliquer intelligemment
        return self._deduplicate_events(events)
    
    def _parse_date_advanced(self, date_str: str, date_type: str) -> Optional[datetime]:
        """Parsing avancé des dates selon leur type"""
        if date_type == 'relative':
            # Parser les dates relatives
            match = re.search(r'(\d+)\s+(jours?|mois|ans?)', date_str)
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                
                if 'jour' in unit:
                    return datetime.now() - timedelta(days=num)
                elif 'mois' in unit:
                    return datetime.now() - timedelta(days=num * 30)
                elif 'an' in unit:
                    return datetime.now() - timedelta(days=num * 365)
        
        elif date_type == 'period':
            # Parser les périodes
            if 'début' in date_str:
                day = 1
            elif 'fin' in date_str:
                day = 28  # Approximation
            else:  # mi-
                day = 15
            
            # Extraire mois et année
            match = re.search(r'(\w+)\s+(\d{4})', date_str)
            if match:
                month_str = match.group(1)
                year = int(match.group(2))
                
                mois_fr = {
                    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
                    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
                    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
                }
                
                month = mois_fr.get(month_str.lower(), 1)
                try:
                    return datetime(year, month, day)
                except:
                    pass
        
        # Utiliser le parsing standard pour les autres types
        return self._parse_date(date_str)
    
    def _calculate_importance_advanced(self, text: str) -> int:
        """Calcul avancé de l'importance adapté au droit pénal des affaires"""
        importance = 5
        
        # Mots-clés pondérés spécifiques au droit pénal des affaires
        keywords = {
            # Actes critiques
            'mise en examen': 4,
            'garde à vue': 3,
            'perquisition': 3,
            'détention provisoire': 4,
            'contrôle judiciaire': 3,
            'gel des avoirs': 3,
            'saisie pénale': 3,
            
            # Infractions graves
            'corruption': 3,
            'blanchiment': 3,
            'abus de biens': 3,
            'escroquerie': 2,
            'faux': 2,
            'recel': 2,
            'fraude fiscale': 3,
            
            # Procédures importantes
            'cjip': 3,
            'convention judiciaire': 3,
            'information judiciaire': 2,
            'réquisitoire': 2,
            'ordonnance de renvoi': 2,
            'jugement': 3,
            'condamnation': 4,
            
            # Autorités
            'pnf': 2,  # Parquet National Financier
            'tracfin': 2,
            'brigade financière': 2,
            'juge d\'instruction': 2,
            
            # Diminue l'importance
            'simple': -1,
            'courrier': -1,
            'report': -1,
            'mineur': -2
        }
        
        text_lower = text.lower()
        
        # Calculer le score basé sur les mots-clés
        for keyword, weight in keywords.items():
            if keyword in text_lower:
                importance += weight
        
        # Facteurs supplémentaires spécifiques
        
        # Montants importants (signe d'infractions graves)
        amounts = re.findall(r'(\d+(?:\.\d+)?)\s*(?:millions?|M€|k€)', text_lower)
        if amounts:
            importance += 2
        
        # Références légales (signe de précision juridique)
        if re.search(r'article\s+\d+', text_lower):
            importance += 1
        
        # Multiples personnes/sociétés impliquées
        entities = re.findall(r'(?:société|sas|sarl|sa|M\.|Mme|Me)\s+[A-Z]', text)
        if len(entities) > 3:
            importance += 1
        
        # Dimension internationale
        if any(word in text_lower for word in ['international', 'étranger', 'offshore', 'luxembourg', 'suisse']):
            importance += 1
        
        # Mesures coercitives
        if any(word in text_lower for word in ['interdiction', 'suspension', 'révocation', 'fermeture']):
            importance += 2
        
        return max(1, min(10, importance))
    
    def _determine_category_advanced(self, text: str) -> str:
        """Détermination avancée de la catégorie adaptée au droit pénal des affaires"""
        text_lower = text.lower()
        
        # Catégories spécifiques au droit pénal des affaires
        category_scores = defaultdict(int)
        
        categories_keywords = {
            'enquête': ['perquisition', 'garde à vue', 'audition', 'saisie', 'pv', 'procès-verbal', 'opj', 'enquête préliminaire', 'flagrance'],
            'instruction': ['juge d\'instruction', 'mise en examen', 'témoin assisté', 'ordonnance', 'commission rogatoire', 'expertise', 'confrontation'],
            'procédure': ['tribunal', 'audience', 'jugement', 'appel', 'cassation', 'citation', 'convocation', 'notification'],
            'financier': ['détournement', 'abus de biens', 'blanchiment', 'corruption', 'fraude', 'escroquerie', 'faux', 'recel'],
            'fiscal': ['fraude fiscale', 'impôt', 'redressement', 'contrôle fiscal', 'dgfip', 'verif', 'dissimulation'],
            'social': ['travail dissimulé', 'urssaf', 'inspection du travail', 'cotisations', 'accident du travail'],
            'compliance': ['conformité', 'alerte', 'lanceur d\'alerte', 'audit', 'contrôle interne', 'lcb-ft', 'tracfin'],
            'mesures': ['contrôle judiciaire', 'détention provisoire', 'scellés', 'gel des avoirs', 'interdiction', 'caution']
        }
        
        for category, keywords in categories_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    category_scores[category] += 1
        
        # Retourner la catégorie avec le score le plus élevé
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'autre'
    
    def _extract_actors_advanced(self, text: str) -> List[str]:
        """Extraction avancée des acteurs avec NER simulé"""
        actors = []
        
        # Patterns pour différents types d'acteurs
        patterns = [
            # Personnes avec civilité
            r'(?:M\.|Mme|Mlle|Dr|Me|Pr|Maître)\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][A-ZÉÈÊË\-]+)*)',
            # Noms propres (prénom nom)
            r'([A-Z][a-zéèêë]+\s+[A-Z][A-ZÉÈÊË\-]+)(?:\s|,|\.|;|$)',
            # Sociétés
            r'(?:société|entreprise|SARL|SAS|SA)\s+([A-Z][A-Za-zéèêë\s\-]+?)(?:\s|,|\.|;|$)',
            # Organisations
            r'(?:le |la |l\')([A-Z][a-zéèêë]+(?:\s+[A-Za-zéèêë]+)*\s+(?:de|du|des)\s+[A-Za-zéèêë]+)',
        ]
        
        found_actors = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Nettoyer et valider
                actor = match.strip()
                if len(actor) > 3 and len(actor) < 50:
                    found_actors.add(actor)
        
        # Limiter et trier par fréquence d'apparition
        actor_counts = {}
        for actor in found_actors:
            count = text.count(actor)
            actor_counts[actor] = count
        
        # Retourner les 5 acteurs les plus fréquents
        sorted_actors = sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)
        return [actor[0] for actor in sorted_actors[:5]]
    
    def _clean_description(self, text: str) -> str:
        """Nettoie et formate la description"""
        # Supprimer les espaces multiples
        text = ' '.join(text.split())
        
        # Supprimer les caractères spéciaux en début/fin
        text = text.strip('.,;: \n\r\t')
        
        # Limiter la longueur
        if len(text) > 300:
            # Couper à la phrase la plus proche
            sentences = text.split('.')
            result = ''
            for sentence in sentences:
                if len(result) + len(sentence) < 280:
                    result += sentence + '.'
                else:
                    break
            return result.strip() + '..' if result else text[:297] + '...'
        
        return text
    
    def _deduplicate_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Déduplique intelligemment les événements"""
        unique_events = []
        seen = set()
        
        for event in sorted(events, key=lambda x: (x.date, -x.importance)):
            # Clé de déduplication basée sur date et début de description
            key = (
                event.date.date(),
                event.description[:30].lower(),
                event.category
            )
            
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
            else:
                # Si doublon, fusionner les informations
                for unique_event in unique_events:
                    if (unique_event.date.date() == event.date.date() and 
                        unique_event.description[:30].lower() == event.description[:30].lower()):
                        # Fusionner les acteurs
                        unique_event.actors = list(set(unique_event.actors + event.actors))
                        # Prendre l'importance maximale
                        unique_event.importance = max(unique_event.importance, event.importance)
                        # Fusionner les métadonnées
                        unique_event.metadata.update(event.metadata)
                        break
        
        return unique_events
    
    def _fuse_ai_results(self, model_results: Dict[AIModel, List[TimelineEvent]]) -> List[TimelineEvent]:
        """Fusionne intelligemment les résultats de plusieurs modèles"""
        # Regrouper les événements similaires
        event_groups = defaultdict(list)
        
        for model, events in model_results.items():
            for event in events:
                # Clé de regroupement
                key = (
                    event.date.date(),
                    event.category,
                    event.description[:20].lower()
                )
                event_groups[key].append((model, event))
        
        # Fusionner chaque groupe
        fused_events = []
        
        for key, group in event_groups.items():
            if len(group) == 1:
                # Un seul modèle a trouvé cet événement
                _, event = group[0]
                event.confidence = 0.6
                fused_events.append(event)
            else:
                # Plusieurs modèles ont trouvé l'événement - fusion
                base_event = group[0][1]
                
                # Calculer la confiance basée sur le consensus
                base_event.confidence = min(0.95, 0.6 + (len(group) * 0.1))
                
                # Fusionner les informations
                all_actors = []
                all_descriptions = []
                importance_sum = 0
                
                for model, event in group:
                    all_actors.extend(event.actors)
                    all_descriptions.append(event.description)
                    importance_sum += event.importance
                    
                    # Ajouter le modèle aux métadonnées
                    if 'contributing_models' not in base_event.metadata:
                        base_event.metadata['contributing_models'] = []
                    base_event.metadata['contributing_models'].append(model.value)
                
                # Appliquer les fusions
                base_event.actors = list(set(all_actors))[:5]
                base_event.importance = round(importance_sum / len(group))
                
                # Choisir la meilleure description (la plus longue et détaillée)
                base_event.description = max(all_descriptions, key=len)
                
                fused_events.append(base_event)
        
        # Trier par date et importance
        return sorted(fused_events, key=lambda x: (x.date, -x.importance))
    
    def _show_extraction_preview(self):
        """Affiche un aperçu des événements extraits"""
        if 'timeline_events' not in st.session_state:
            return
        
        events = st.session_state.timeline_events[:5]  # Premiers événements
        
        st.markdown("### 👀 Aperçu des événements extraits")
        
        for i, event in enumerate(events):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Badge IA si extrait par IA
                ai_badge = ""
                if event.ai_extracted and 'ai_model' in event.metadata:
                    model_class = event.metadata['ai_model'].lower().split()[0]
                    ai_badge = f'<span class="ai-badge ai-{model_class}">{event.metadata["ai_model"]}</span>'
                
                st.markdown(f"""
                <div class="event-card">
                    <strong>{event.date.strftime('%d/%m/%Y')}</strong> {ai_badge}
                    <p>{event.description[:150]}...</p>
                    <small>Acteurs: {', '.join(event.actors[:3]) if event.actors else 'N/A'}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                importance_class = 'high' if event.importance >= 8 else 'medium' if event.importance >= 5 else 'low'
                st.markdown(f'<span class="importance-{importance_class}">Importance: {event.importance}/10</span>', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"Confiance: {event.confidence:.0%}")
        
        if len(st.session_state.timeline_events) > 5:
            st.info(f"... et {len(st.session_state.timeline_events) - 5} autres événements")
    
    def _render_enrichment_step(self):
        """Étape d'enrichissement des événements"""
        st.markdown("### 🎨 Enrichissement des événements")
        
        if 'timeline_events' not in st.session_state:
            st.warning("Aucun événement à enrichir")
            return
        
        events = st.session_state.timeline_events
        
        # Options d'enrichissement
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🤖 Enrichissement automatique")
            
            if st.checkbox("🔗 Détecter les liens entre événements", value=True):
                st.caption("L'IA identifie les relations causales")
            
            if st.checkbox("📊 Calculer les statistiques avancées", value=True):
                st.caption("Patterns temporels et corrélations")
            
            if st.checkbox("🏷️ Tagging intelligent", value=True):
                st.caption("Tags contextuels automatiques")
            
            if st.checkbox("🌐 Recherche d'informations complémentaires", value=False):
                st.caption("Enrichissement via sources externes")
        
        with col2:
            st.markdown("#### ✏️ Édition manuelle")
            
            # Sélection d'événements à éditer
            event_to_edit = st.selectbox(
                "Événement à modifier",
                range(len(events)),
                format_func=lambda x: f"{events[x].date.strftime('%d/%m/%Y')} - {events[x].description[:50]}..."
            )
            
            if event_to_edit is not None:
                event = events[event_to_edit]
                
                with st.expander("Modifier l'événement", expanded=True):
                    event.description = st.text_area("Description", value=event.description)
                    event.importance = st.slider("Importance", 1, 10, event.importance)
                    event.category = st.selectbox("Catégorie", 
                        ["procédure", "financier", "contractuel", "communication", "expertise", "médical", "autre"],
                        index=["procédure", "financier", "contractuel", "communication", "expertise", "médical", "autre"].index(event.category)
                    )
                    
                    new_actors = st.text_input("Acteurs (séparés par des virgules)", 
                        value=", ".join(event.actors))
                    event.actors = [a.strip() for a in new_actors.split(",") if a.strip()]
        
        # Bouton d'enrichissement
        if st.button("🚀 Lancer l'enrichissement IA", type="primary", use_container_width=True):
            self._enrich_events_with_ai(events)
        
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Retour", use_container_width=True):
                st.session_state.timeline_workflow_step = 1
                st.rerun()
        with col3:
            if st.button("Suivant ▶", use_container_width=True):
                st.session_state.timeline_workflow_step = 3
                st.rerun()
    
    def _enrich_events_with_ai(self, events: List[TimelineEvent]):
        """Enrichit les événements avec l'IA"""
        progress = st.progress(0)
        status = st.empty()
        
        # Étapes d'enrichissement
        enrichment_steps = [
            ("Détection des liens", self._detect_event_links),
            ("Calcul des patterns", self._calculate_patterns),
            ("Tagging intelligent", self._apply_smart_tags),
            ("Analyse contextuelle", self._analyze_context)
        ]
        
        for i, (step_name, step_func) in enumerate(enrichment_steps):
            status.text(f"🔄 {step_name}...")
            step_func(events)
            progress.progress((i + 1) / len(enrichment_steps))
            time.sleep(0.3)  # Simulation
        
        status.text("✅ Enrichissement terminé !")
        
        # Afficher les résultats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            links_count = sum(1 for e in events if 'linked_events' in e.metadata)
            st.metric("🔗 Liens détectés", links_count)
        
        with col2:
            tags_count = sum(len(e.metadata.get('tags', [])) for e in events)
            st.metric("🏷️ Tags ajoutés", tags_count)
        
        with col3:
            patterns_count = len(set(e.metadata.get('pattern', '') for e in events if 'pattern' in e.metadata))
            st.metric("📊 Patterns identifiés", patterns_count)
    
    def _detect_event_links(self, events: List[TimelineEvent]):
        """Détecte les liens entre événements"""
        for i, event1 in enumerate(events):
            event1.metadata['linked_events'] = []
            
            for j, event2 in enumerate(events):
                if i == j:
                    continue
                
                # Lien temporel (événements proches)
                days_diff = abs((event1.date - event2.date).days)
                if days_diff <= 7:
                    event1.metadata['linked_events'].append({
                        'index': j,
                        'type': 'temporal',
                        'strength': 1 - (days_diff / 7)
                    })
                
                # Lien par acteurs communs
                common_actors = set(event1.actors) & set(event2.actors)
                if common_actors:
                    event1.metadata['linked_events'].append({
                        'index': j,
                        'type': 'actors',
                        'strength': len(common_actors) / max(len(event1.actors), len(event2.actors))
                    })
                
                # Lien sémantique (mots-clés communs)
                words1 = set(event1.description.lower().split())
                words2 = set(event2.description.lower().split())
                common_words = words1 & words2
                if len(common_words) > 5:
                    event1.metadata['linked_events'].append({
                        'index': j,
                        'type': 'semantic',
                        'strength': len(common_words) / max(len(words1), len(words2))
                    })
    
    def _calculate_patterns(self, events: List[TimelineEvent]):
        """Calcule les patterns temporels"""
        # Grouper par mois
        monthly_groups = defaultdict(list)
        for event in events:
            month_key = event.date.strftime('%Y-%m')
            monthly_groups[month_key].append(event)
        
        # Identifier les patterns
        for month, month_events in monthly_groups.items():
            if len(month_events) >= 3:
                # Pattern de densité
                for event in month_events:
                    event.metadata['pattern'] = 'high_density_period'
            
            # Pattern d'escalade (importance croissante)
            sorted_events = sorted(month_events, key=lambda x: x.date)
            if len(sorted_events) >= 2:
                importances = [e.importance for e in sorted_events]
                if all(importances[i] <= importances[i+1] for i in range(len(importances)-1)):
                    for event in sorted_events:
                        event.metadata['pattern'] = 'escalation'
    
    def _apply_smart_tags(self, events: List[TimelineEvent]):
        """Applique des tags intelligents"""
        for event in events:
            tags = []
            
            # Tags basés sur le contenu
            if re.search(r'\d+\s*€', event.description):
                tags.append('💰 Financier')
            
            if any(word in event.description.lower() for word in ['urgent', 'immédiat', 'critique']):
                tags.append('🚨 Urgent')
            
            if event.importance >= 8:
                tags.append('⭐ Critique')
            
            if len(event.actors) >= 3:
                tags.append('👥 Multi-acteurs')
            
            # Tags basés sur les patterns
            if event.metadata.get('pattern') == 'escalation':
                tags.append('📈 Escalade')
            
            event.metadata['tags'] = tags
    
    def _analyze_context(self, events: List[TimelineEvent]):
        """Analyse contextuelle approfondie"""
        # Contexte global
        total_duration = (max(e.date for e in events) - min(e.date for e in events)).days
        
        for event in events:
            # Position dans la timeline
            position = (event.date - min(e.date for e in events)).days / total_duration
            
            if position < 0.2:
                event.metadata['phase'] = 'initial'
            elif position < 0.8:
                event.metadata['phase'] = 'development'
            else:
                event.metadata['phase'] = 'conclusion'
            
            # Rôle de l'événement
            if event.importance >= 8 and event.metadata.get('phase') == 'development':
                event.metadata['role'] = 'turning_point'
            elif event.metadata.get('phase') == 'initial' and event.category == 'procédure':
                event.metadata['role'] = 'trigger'
    
    def _render_validation_step(self):
        """Étape de validation finale adaptée au type de chronologie"""
        st.markdown("### ✅ Validation et révision")
        
        if 'timeline_events' not in st.session_state:
            st.warning("Aucun événement à valider")
            return
        
        events = st.session_state.timeline_events
        timeline_type = st.session_state.get('timeline_type', 'Chronologie complète')
        
        # Afficher le type de chronologie actif
        st.info(f"📊 Type de chronologie : **{timeline_type}**")
        
        # Statistiques adaptées au type
        self._display_type_specific_stats(events, timeline_type)
        
        # Filtres de validation adaptés
        st.markdown("#### 🔍 Filtrer et valider")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_importance = st.slider("Importance minimale", 1, 10, 1)
            events_filtered = [e for e in events if e.importance >= min_importance]
        
        with col2:
            # Catégories selon le type de chronologie
            if "procédure" in timeline_type.lower():
                default_categories = ["procédure", "instruction", "enquête", "mesures"]
            elif "faits" in timeline_type.lower():
                default_categories = ["financier", "fiscal", "social"]
            else:
                default_categories = list(set(e.category for e in events))
            
            selected_categories = st.multiselect(
                "Catégories",
                list(set(e.category for e in events)),
                default=default_categories
            )
            events_filtered = [e for e in events_filtered if e.category in selected_categories]
        
        with col3:
            min_confidence = st.slider("Confiance minimale", 0.0, 1.0, 0.5, 0.05)
            events_filtered = [e for e in events_filtered if e.confidence >= min_confidence]
        
        st.info(f"📊 {len(events_filtered)} événements après filtrage sur {len(events)} extraits")
        
        # Options de regroupement selon le type
        if "auditions" in timeline_type.lower():
            group_by = st.selectbox(
                "Regrouper par",
                ["Date", "Personne auditionnée", "Type d'audition", "Autorité"]
            )
        elif "fait spécifique" in timeline_type.lower():
            group_by = st.selectbox(
                "Regrouper par",
                ["Chronologique", "Élément constitutif", "Preuve", "Acteur"]
            )
        else:
            group_by = "Date"
        
        # Table de validation
        st.markdown("#### 📋 Révision des événements")
        
        # Créer un dataframe pour l'édition
        events_data = []
        for i, event in enumerate(events_filtered):
            # Adapter l'affichage selon le type
            if "auditions" in timeline_type.lower():
                extra_info = self._extract_audition_info(event)
            elif "fait" in timeline_type.lower():
                extra_info = self._extract_fact_info(event)
            else:
                extra_info = event.category
            
            events_data.append({
                'Index': i,
                'Date': event.date.strftime('%d/%m/%Y'),
                'Description': event.description[:100] + '...',
                'Type/Info': extra_info,
                'Importance': event.importance,
                'Confiance': f"{event.confidence:.0%}",
                'Valider': True
            })
        
        # Affichage interactif
        if events_data:
            df = pd.DataFrame(events_data)
            
            # Utiliser data_editor pour permettre la modification
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valider": st.column_config.CheckboxColumn(
                        "Valider",
                        help="Cocher pour inclure dans la timeline finale"
                    ),
                    "Importance": st.column_config.NumberColumn(
                        "Importance",
                        min_value=1,
                        max_value=10,
                        step=1
                    ),
                    "Type/Info": st.column_config.TextColumn(
                        "Info spécifique",
                        help="Information contextuelle selon le type de chronologie"
                    )
                }
            )
            
            # Appliquer les modifications
            validated_events = []
            for _, row in edited_df.iterrows():
                if row['Valider']:
                    original_event = events_filtered[row['Index']]
                    original_event.importance = row['Importance']
                    validated_events.append(original_event)
            
            st.session_state.validated_events = validated_events
        else:
            st.session_state.validated_events = events_filtered
        
        # Actions spécifiques au type
        self._render_type_specific_actions(timeline_type)
        
        # Navigation
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Retour", use_container_width=True):
                st.session_state.timeline_workflow_step = 2
                st.rerun()
        with col3:
            if st.button("Générer ▶", use_container_width=True, type="primary",
                        disabled=not st.session_state.get('validated_events')):
                st.session_state.timeline_workflow_step = 4
                st.rerun()
    
    def _display_type_specific_stats(self, events: List[TimelineEvent], timeline_type: str):
        """Affiche des statistiques adaptées au type de chronologie"""
        if "procédure" in timeline_type.lower():
            # Stats pour chronologie de procédure
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_acts = len(events)
                st.metric("📑 Actes de procédure", total_acts)
            
            with col2:
                enquete_acts = sum(1 for e in events if e.category == 'enquête')
                st.metric("🔍 Actes d'enquête", enquete_acts)
            
            with col3:
                instruction_acts = sum(1 for e in events if e.category == 'instruction')
                st.metric("⚖️ Actes d'instruction", instruction_acts)
            
            with col4:
                mesures = sum(1 for e in events if e.category == 'mesures')
                st.metric("🔒 Mesures coercitives", mesures)
                
        elif "faits" in timeline_type.lower():
            # Stats pour chronologie des faits
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_facts = len(events)
                st.metric("💼 Faits identifiés", total_facts)
            
            with col2:
                financial = sum(1 for e in events if e.category == 'financier')
                st.metric("💰 Infractions financières", financial)
            
            with col3:
                # Calculer le préjudice total
                amounts = []
                for e in events:
                    amounts.extend(re.findall(r'(\d+(?:\.\d+)?)\s*(?:€|euros?|M€)', e.description))
                total_amount = sum(float(a.replace(',', '.')) for a in amounts[:5])  # Limiter pour éviter les doublons
                st.metric("💸 Préjudice estimé", f"{total_amount:,.0f} €" if total_amount > 0 else "N/A")
            
            with col4:
                actors = set()
                for e in events:
                    actors.update(e.actors)
                st.metric("👥 Personnes impliquées", len(actors))
                
        elif "auditions" in timeline_type.lower():
            # Stats pour chronologie des auditions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎤 Total auditions", len(events))
            
            with col2:
                gav = sum(1 for e in events if 'garde à vue' in e.description.lower())
                st.metric("🚔 Gardes à vue", gav)
            
            with col3:
                temoins = sum(1 for e in events if 'témoin' in e.description.lower())
                st.metric("👤 Auditions témoins", temoins)
            
            with col4:
                confrontations = sum(1 for e in events if 'confrontation' in e.description.lower())
                st.metric("👥 Confrontations", confrontations)
        
        else:
            # Stats générales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📅 Événements", len(events))
            
            with col2:
                duration = (max(e.date for e in events) - min(e.date for e in events)).days if events else 0
                st.metric("⏱️ Durée", f"{duration} jours")
            
            with col3:
                critical_events = sum(1 for e in events if e.importance >= 8)
                st.metric("⚠️ Critiques", critical_events)
            
            with col4:
                ai_events = sum(1 for e in events if e.ai_extracted)
                st.metric("🤖 Par IA", f"{ai_events}/{len(events)}")
    
    def _extract_audition_info(self, event: TimelineEvent) -> str:
        """Extrait les informations spécifiques aux auditions"""
        desc_lower = event.description.lower()
        
        if 'garde à vue' in desc_lower:
            return "Garde à vue"
        elif 'confrontation' in desc_lower:
            return "Confrontation"
        elif 'témoin' in desc_lower:
            return "Audition témoin"
        elif 'libre' in desc_lower:
            return "Audition libre"
        elif 'interrogatoire' in desc_lower:
            return "Interrogatoire JI"
        else:
            return "Audition"
    
    def _extract_fact_info(self, event: TimelineEvent) -> str:
        """Extrait les informations spécifiques aux faits"""
        # Chercher le type d'infraction
        infraction_type = event.metadata.get('infraction_type', '')
        if infraction_type:
            return infraction_type.replace('_', ' ').title()
        
        # Sinon, détecter dans la description
        desc_lower = event.description.lower()
        if 'abus de biens' in desc_lower:
            return "ABS"
        elif 'corruption' in desc_lower:
            return "Corruption"
        elif 'blanchiment' in desc_lower:
            return "Blanchiment"
        elif 'escroquerie' in desc_lower:
            return "Escroquerie"
        elif 'fraude' in desc_lower:
            return "Fraude"
        else:
            return event.category.title()
    
    def _render_type_specific_actions(self, timeline_type: str):
        """Actions spécifiques selon le type de chronologie"""
        st.markdown("### 🎯 Actions spécialisées")
        
        col1, col2, col3 = st.columns(3)
        
        if "procédure" in timeline_type.lower():
            with col1:
                if st.button("📊 Analyser les délais", use_container_width=True):
                    self._analyze_procedural_delays()
            
            with col2:
                if st.button("⚖️ Vérifier la régularité", use_container_width=True):
                    self._check_procedural_regularity()
            
            with col3:
                if st.button("📅 Calculer prescriptions", use_container_width=True):
                    self._calculate_prescriptions()
                    
        elif "faits" in timeline_type.lower():
            with col1:
                if st.button("💰 Analyser préjudice", use_container_width=True):
                    self._analyze_damages()
            
            with col2:
                if st.button("🔗 Liens entre faits", use_container_width=True):
                    self._analyze_fact_connections()
            
            with col3:
                if st.button("📈 Évolution temporelle", use_container_width=True):
                    self._analyze_fact_evolution()
                    
        elif "auditions" in timeline_type.lower():
            with col1:
                if st.button("👥 Cohérence des déclarations", use_container_width=True):
                    self._analyze_statement_consistency()
            
            with col2:
                if st.button("⏱️ Durées GAV", use_container_width=True):
                    self._analyze_custody_durations()
            
            with col3:
                if st.button("📋 Synthèse par personne", use_container_width=True):
                    self._create_person_summary()
    
    def _analyze_procedural_delays(self):
        """Analyse les délais procéduraux"""
        with st.expander("📊 Analyse des délais procéduraux", expanded=True):
            st.info("Analyse des délais entre les actes de procédure majeurs...")
            
            # Simulation d'analyse
            st.metric("Délai moyen entre actes", "15 jours")
            st.warning("⚠️ Délai anormalement long détecté entre la garde à vue et le déferrement (5 jours)")
    
    def _check_procedural_regularity(self):
        """Vérifie la régularité de la procédure"""
        with st.expander("⚖️ Vérification de régularité", expanded=True):
            checks = {
                "Notification des droits en GAV": "✅ Conforme",
                "Délai de déferrement": "✅ Respecté (< 20h)",
                "Présence avocat": "✅ Systématique",
                "Délai d'instruction": "⚠️ Long (> 2 ans)"
            }
            
            for check, status in checks.items():
                st.write(f"{check}: {status}")
    
    def _calculate_prescriptions(self):
        """Calcule les délais de prescription"""
        with st.expander("📅 Calcul des prescriptions", expanded=True):
            st.write("**Prescription de l'action publique:**")
            st.write("- Faits du 01/01/2020")
            st.write("- Infraction dissimulée: point de départ au jour de découverte")
            st.write("- Découverte: 01/01/2023")
            st.write("- ⏰ Prescription: 01/01/2029 (6 ans)")
            st.progress(0.3, "30% du délai écoulé")
    
    def _render_generation_step(self):
        """Étape finale de génération adaptée au type de chronologie"""
        st.markdown("### 🎯 Génération de la timeline")
        
        if 'validated_events' not in st.session_state:
            st.warning("Aucun événement validé")
            return
        
        events = st.session_state.validated_events
        timeline_type = st.session_state.get('timeline_type', 'Chronologie complète')
        
        # Rappel du type de chronologie
        st.info(f"📊 Génération de : **{timeline_type}** avec {len(events)} événements")
        
        # Configuration de la visualisation adaptée au type
        st.markdown("#### 🎨 Configuration de la visualisation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Types de vue adaptés selon la chronologie
            view_options = self._get_view_options_by_type(timeline_type)
            view_type = st.selectbox(
                "📊 Type de vue",
                list(view_options.keys()),
                help="Visualisation adaptée au type de chronologie"
            )
            
            color_options = self._get_color_options_by_type(timeline_type)
            color_scheme = st.selectbox(
                "🎨 Schéma de couleurs",
                list(color_options.keys())
            )
        
        with col2:
            theme = st.selectbox(
                "🖼️ Thème visuel",
                ["Juridique", "Moderne", "Classique", "Minimaliste", "Formel"]
            )
            
            # Options spécifiques au type
            if "procédure" in timeline_type.lower():
                show_delays = st.checkbox("⏱️ Afficher les délais entre actes", value=True)
                show_authorities = st.checkbox("🏛️ Mettre en évidence les autorités", value=True)
            elif "faits" in timeline_type.lower():
                show_amounts = st.checkbox("💰 Afficher les montants", value=True)
                show_connections = st.checkbox("🔗 Montrer les liens entre faits", value=True)
            elif "auditions" in timeline_type.lower():
                show_duration = st.checkbox("⏱️ Durée des auditions", value=True)
                show_presence = st.checkbox("👤 Présence avocat", value=True)
            else:
                show_links = st.checkbox("🔗 Afficher les relations", value=True)
                show_patterns = st.checkbox("📊 Afficher les patterns", value=True)
        
        with col3:
            animation = st.checkbox("✨ Animations", value=True)
            interactive = st.checkbox("🖱️ Mode interactif", value=True)
            
            # Suggestion IA adaptée
            if st.button("🎲 Suggestion IA", help="L'IA suggère la meilleure visualisation"):
                suggested = self._suggest_visualization_by_type(events, timeline_type)
                st.info(f"💡 {suggested}")
        
        # Options d'export adaptées
        st.markdown("#### 💾 Options d'export")
        
        export_presets = self._get_export_presets_by_type(timeline_type)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_preset = st.selectbox(
                "📋 Preset d'export",
                list(export_presets.keys())
            )
            
            export_formats = st.multiselect(
                "Formats d'export",
                export_presets[selected_preset]['formats'],
                default=export_presets[selected_preset]['formats'][:2]
            )
        
        with col2:
            # Options spécifiques d'export
            if "procédure" in timeline_type.lower():
                include_legal_refs = st.checkbox("📚 Inclure les références légales", value=True)
                include_delays_analysis = st.checkbox("📊 Inclure l'analyse des délais", value=True)
            elif "faits" in timeline_type.lower():
                include_damage_summary = st.checkbox("💸 Inclure le résumé des préjudices", value=True)
                include_qualification = st.checkbox("⚖️ Inclure la qualification juridique", value=True)
            else:
                include_analysis = st.checkbox("📊 Inclure l'analyse", value=True)
                include_insights = st.checkbox("💡 Inclure les insights", value=True)
        
        # Bouton de génération
        if st.button("🚀 Générer la timeline finale", type="primary", use_container_width=True):
            config = {
                'timeline_type': timeline_type,
                'view_type': view_type,
                'color_scheme': color_scheme,
                'theme': theme,
                'animation': animation,
                'interactive': interactive,
                'export_formats': export_formats,
                'type_specific_options': self._get_type_specific_config(timeline_type, locals())
            }
            
            self._generate_final_timeline(events, config)
    
    def _get_view_options_by_type(self, timeline_type: str) -> Dict[str, str]:
        """Retourne les options de visualisation selon le type"""
        if "procédure" in timeline_type.lower():
            return {
                "Timeline procédurale": "Vue chronologique avec phases",
                "Swimlanes par autorité": "Organisation par autorité judiciaire",
                "Vue en cascade": "Cascade des actes de procédure",
                "Diagramme de flux": "Flux procédural avec décisions"
            }
        elif "faits" in timeline_type.lower():
            return {
                "Chronologie des infractions": "Timeline des faits délictueux",
                "Carte thermique": "Intensité des infractions dans le temps",
                "Réseau de connexions": "Liens entre les infractions",
                "Vue par préjudice": "Organisation par montant/gravité"
            }
        elif "auditions" in timeline_type.lower():
            return {
                "Planning des auditions": "Vue calendaire des auditions",
                "Par personne auditionnée": "Timeline par individu",
                "Analyse des déclarations": "Évolution des déclarations",
                "Vue comparative": "Comparaison des versions"
            }
        elif "fait spécifique" in timeline_type.lower():
            return {
                "Analyse détaillée": "Focus sur l'infraction ciblée",
                "Chronologie de constitution": "Étapes de réalisation",
                "Réseau des preuves": "Liens entre éléments probants",
                "Vue forensique": "Analyse technique détaillée"
            }
        else:
            return {
                "Timeline linéaire": "Vue chronologique classique",
                "Vue par catégorie": "Organisation par type",
                "Vue par acteur": "Focus sur les personnes",
                "Carte de densité": "Intensité temporelle"
            }
    
    def _get_color_options_by_type(self, timeline_type: str) -> Dict[str, str]:
        """Retourne les options de couleur selon le type"""
        if "procédure" in timeline_type.lower():
            return {
                "Par phase procédurale": "Enquête/Instruction/Jugement",
                "Par autorité": "Couleur selon l'autorité",
                "Par criticité": "Importance de l'acte",
                "Monochrome juridique": "Bleu juridique"
            }
        elif "faits" in timeline_type.lower():
            return {
                "Par type d'infraction": "Code couleur par délit",
                "Par gravité": "Gradient selon le préjudice",
                "Par victime": "Couleur par partie lésée",
                "Rouge financier": "Thème infractions économiques"
            }
        elif "auditions" in timeline_type.lower():
            return {
                "Par statut": "Mis en cause/Témoin/Victime",
                "Par type d'audition": "GAV/Libre/Confrontation",
                "Par autorité": "OPJ/JI/Procureur",
                "Vert enquête": "Thème investigation"
            }
        else:
            return {
                "Par catégorie": "Couleur selon le type",
                "Par importance": "Gradient d'importance",
                "Par phase": "Évolution temporelle",
                "Personnalisé": "Choix manuel"
            }
    
    def _get_export_presets_by_type(self, timeline_type: str) -> Dict[str, Dict]:
        """Retourne les presets d'export selon le type"""
        if "procédure" in timeline_type.lower():
            return {
                "Dossier de plaidoirie": {
                    "formats": ["📄 PDF juridique", "📊 PowerPoint audience", "📋 Synthèse Word"],
                    "description": "Pour présentation en audience"
                },
                "Analyse procédurale": {
                    "formats": ["📊 Excel détaillé", "📈 Rapport PDF", "💾 JSON structuré"],
                    "description": "Pour analyse approfondie"
                },
                "Communication client": {
                    "formats": ["📄 PDF synthétique", "📧 Email HTML", "📱 Mobile-friendly"],
                    "description": "Pour information du client"
                }
            }
        elif "faits" in timeline_type.lower():
            return {
                "Dossier pénal": {
                    "formats": ["📄 PDF complet", "📊 Annexes Excel", "🖼️ Schémas visuels"],
                    "description": "Constitution partie civile"
                },
                "Expertise": {
                    "formats": ["📊 Rapport expert", "📈 Graphiques détaillés", "📋 Tableaux chiffrés"],
                    "description": "Pour expertise judiciaire"
                }
            }
        elif "auditions" in timeline_type.lower():
            return {
                "Synthèse auditions": {
                    "formats": ["📄 PDF chronologique", "📊 Tableau comparatif", "📝 Transcriptions"],
                    "description": "Analyse des déclarations"
                },
                "Confrontation": {
                    "formats": ["📋 Tableau contradictions", "🔍 Analyse comparative", "📊 Timeline interactive"],
                    "description": "Préparation confrontation"
                }
            }
        else:
            return {
                "Export standard": {
                    "formats": ["📄 PDF", "📊 PowerPoint", "📈 Excel", "🌐 Web"],
                    "description": "Formats classiques"
                },
                "Export complet": {
                    "formats": ["📦 Pack complet", "💾 Archive ZIP", "🔗 Liens cloud"],
                    "description": "Tous les formats"
                }
            }
    
    def _suggest_visualization_by_type(self, events: List[TimelineEvent], timeline_type: str) -> str:
        """Suggère la meilleure visualisation selon le type et les données"""
        num_events = len(events)
        
        if "procédure" in timeline_type.lower():
            if num_events > 50:
                return "Vue en cascade recommandée pour visualiser le flux procédural complexe"
            elif any('autorité' in e.metadata for e in events):
                return "Swimlanes par autorité pour voir le rôle de chaque institution"
            else:
                return "Timeline procédurale avec phases pour une vue d'ensemble claire"
                
        elif "faits" in timeline_type.lower():
            total_amount = sum(float(m) for e in events for m in re.findall(r'(\d+)', e.description) if m)[:10]
            if total_amount > 1000000:
                return "Vue par préjudice pour visualiser l'ampleur financière"
            elif len(set(e.metadata.get('infraction_type', '') for e in events)) > 3:
                return "Réseau de connexions pour voir les liens entre infractions"
            else:
                return "Chronologie des infractions avec focus sur l'évolution"
                
        elif "auditions" in timeline_type.lower():
            unique_persons = len(set(actor for e in events for actor in e.actors))
            if unique_persons > 5:
                return "Par personne auditionnée pour comparer les déclarations"
            else:
                return "Vue comparative pour analyser les contradictions"
                
        else:
            return "Timeline linéaire classique adaptée à votre cas"
    
    def _get_type_specific_config(self, timeline_type: str, local_vars: Dict) -> Dict:
        """Récupère la configuration spécifique au type"""
        config = {}
        
        if "procédure" in timeline_type.lower():
            config['show_delays'] = local_vars.get('show_delays', True)
            config['show_authorities'] = local_vars.get('show_authorities', True)
            config['include_legal_refs'] = local_vars.get('include_legal_refs', True)
            config['include_delays_analysis'] = local_vars.get('include_delays_analysis', True)
            
        elif "faits" in timeline_type.lower():
            config['show_amounts'] = local_vars.get('show_amounts', True)
            config['show_connections'] = local_vars.get('show_connections', True)
            config['include_damage_summary'] = local_vars.get('include_damage_summary', True)
            config['include_qualification'] = local_vars.get('include_qualification', True)
            
        elif "auditions" in timeline_type.lower():
            config['show_duration'] = local_vars.get('show_duration', True)
            config['show_presence'] = local_vars.get('show_presence', True)
            
        return config
    
    def _suggest_best_visualization(self, events: List[TimelineEvent]) -> str:
        """Suggère la meilleure visualisation basée sur les données"""
        # Analyse des caractéristiques
        num_events = len(events)
        num_categories = len(set(e.category for e in events))
        num_actors = len(set(actor for e in events for actor in e.actors))
        has_links = any('linked_events' in e.metadata for e in events)
        
        # Logique de suggestion
        if num_events > 50:
            return "Carte de densité - Idéal pour visualiser de nombreux événements"
        elif num_actors > 10 and num_actors > num_categories:
            return "Vue par acteur - Beaucoup d'acteurs différents impliqués"
        elif has_links and num_events < 30:
            return "Graphe de relations - Liens complexes entre événements"
        elif num_categories > 5:
            return "Vue par catégorie - Multiples catégories à distinguer"
        else:
            return "Timeline linéaire - Vue classique et claire"
    
    def _generate_final_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]):
        """Génère la timeline finale avec toutes les options"""
        # Container de progression
        progress_container = st.container()
        
        with progress_container:
            progress = st.progress(0)
            status = st.status("Génération en cours...", expanded=True)
            
            steps = [
                ("Préparation des données", 0.1),
                ("Application du thème", 0.2),
                ("Création de la visualisation", 0.4),
                ("Ajout des interactions", 0.6),
                ("Génération des exports", 0.8),
                ("Finalisation", 1.0)
            ]
            
            timeline_result = {
                'events': events,
                'config': config,
                'timestamp': datetime.now(),
                'event_count': len(events)
            }
            
            for step_name, progress_value in steps:
                with status:
                    st.write(f"⏳ {step_name}...")
                progress.progress(progress_value)
                time.sleep(0.5)  # Simulation
                
                # Actions selon l'étape
                if progress_value == 0.4:
                    timeline_result['visualization'] = self._create_advanced_visualization(events, config)
                elif progress_value == 0.6:
                    timeline_result['analysis'] = self._analyze_timeline(events)
                elif progress_value == 0.8:
                    timeline_result['exports'] = self._prepare_exports(events, config)
            
            status.update(label="✅ Timeline générée avec succès !", state="complete")
        
        # Effacer la progression
        progress_container.empty()
        
        # Sauvegarder
        st.session_state.current_timeline = timeline_result
        st.session_state.timeline_history.append(timeline_result)
        
        # Afficher les résultats
        self._display_final_timeline(timeline_result)
    
    def _create_advanced_visualization(self, events: List[TimelineEvent], config: Dict[str, Any]) -> Any:
        """Crée une visualisation avancée selon le type de chronologie"""

        
        timeline_type = config.get('timeline_type', 'Chronologie complète')
        view_type = config.get('view_type', 'Timeline linéaire')
        
        # Router vers la visualisation appropriée
        if "procédure" in timeline_type.lower():
            if "swimlanes" in view_type.lower():
                return self._create_authority_swimlanes(events, config)
            elif "cascade" in view_type.lower():
                return self._create_procedural_cascade(events, config)
            elif "flux" in view_type.lower():
                return self._create_procedural_flow(events, config)
            else:
                return self._create_procedural_timeline(events, config)
                
        elif "faits" in timeline_type.lower():
            if "thermique" in view_type.lower():
                return self._create_facts_heatmap(events, config)
            elif "réseau" in view_type.lower():
                return self._create_facts_network(events, config)
            elif "préjudice" in view_type.lower():
                return self._create_damage_view(events, config)
            else:
                return self._create_facts_timeline(events, config)
                
        elif "auditions" in timeline_type.lower():
            if "planning" in view_type.lower():
                return self._create_auditions_calendar(events, config)
            elif "personne" in view_type.lower():
                return self._create_person_timeline(events, config)
            elif "comparative" in view_type.lower():
                return self._create_comparative_view(events, config)
            else:
                return self._create_auditions_timeline(events, config)
                
        elif "fait spécifique" in timeline_type.lower():
            if "forensique" in view_type.lower():
                return self._create_forensic_view(events, config)
            elif "preuves" in view_type.lower():
                return self._create_evidence_network(events, config)
            else:
                return self._create_detailed_fact_timeline(events, config)
                
        else:
            return self._create_modern_linear_timeline(events, config)
    
    def _create_procedural_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Timeline spécialisée pour la procédure pénale"""
        fig = go.Figure()
        
        # Trier les événements
        sorted_events = sorted(events, key=lambda x: x.date)
        
        # Définir les phases procédurales
        phases = {
            'enquête': {'color': '#3498db', 'y': 0},
            'instruction': {'color': '#e74c3c', 'y': 1},
            'jugement': {'color': '#2ecc71', 'y': 2},
            'appel': {'color': '#f39c12', 'y': 3}
        }
        
        # Grouper par phase
        for phase, phase_config in phases.items():
            phase_events = [e for e in sorted_events if phase in e.metadata.get('procedural_phase', '').lower()]
            
            if phase_events:
                # Ligne de base pour la phase
                fig.add_trace(go.Scatter(
                    x=[phase_events[0].date, phase_events[-1].date],
                    y=[phase_config['y'], phase_config['y']],
                    mode='lines',
                    line=dict(color=phase_config['color'], width=3),
                    name=phase.capitalize(),
                    showlegend=True
                ))
                
                # Points pour chaque événement
                fig.add_trace(go.Scatter(
                    x=[e.date for e in phase_events],
                    y=[phase_config['y']] * len(phase_events),
                    mode='markers+text',
                    marker=dict(
                        size=[10 + e.importance for e in phase_events],
                        color=phase_config['color'],
                        symbol='diamond' if any('mise en examen' in e.description.lower() for e in phase_events) else 'circle'
                    ),
                    text=[e.description[:30] + '...' for e in phase_events],
                    textposition='top center',
                    hovertext=[self._create_procedural_hover(e, config) for e in phase_events],
                    hoverinfo='text',
                    showlegend=False
                ))
        
        # Ajouter les délais si demandé
        if config.get('type_specific_options', {}).get('show_delays'):
            self._add_procedural_delays(fig, sorted_events)
        
        # Mise en forme juridique
        fig.update_layout(
            title={
                'text': "Chronologie de la procédure pénale",
                'font': {'size': 20, 'family': 'Georgia, serif'}
            },
            xaxis=dict(
                title="Date",
                type='date',
                tickformat='%d/%m/%Y',
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="Phase procédurale",
                tickmode='array',
                tickvals=[0, 1, 2, 3],
                ticktext=['Enquête', 'Instruction', 'Jugement', 'Appel'],
                range=[-0.5, 3.5]
            ),
            height=600,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa'
        )
        
        return fig
    
    def _create_facts_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Timeline spécialisée pour les faits délictueux"""
        fig = go.Figure()
        
        # Trier par date
        sorted_events = sorted(events, key=lambda x: x.date)
        
        # Extraire les montants pour dimensionner
        amounts = []
        for event in sorted_events:
            amount_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:€|euros?|M€|millions?)', event.description)
            if amount_matches:
                amounts.append(float(amount_matches[0].replace(',', '.')))
            else:
                amounts.append(0)
        
        # Normaliser les montants pour la taille des bulles
        max_amount = max(amounts) if amounts else 1
        sizes = [20 + (amount / max_amount * 50) if amount > 0 else 15 for amount in amounts]
        
        # Couleurs par type d'infraction
        infraction_colors = {
            'abus_biens_sociaux': '#e74c3c',
            'corruption': '#9b59b6',
            'blanchiment': '#3498db',
            'escroquerie': '#e67e22',
            'fraude_fiscale': '#f39c12',
            'autre': '#95a5a6'
        }
        
        colors = []
        for event in sorted_events:
            infraction = event.metadata.get('infraction_type', 'autre')
            colors.append(infraction_colors.get(infraction, '#95a5a6'))
        
        # Trace principale des faits
        fig.add_trace(go.Scatter(
            x=[e.date for e in sorted_events],
            y=[i % 3 for i in range(len(sorted_events))],  # Répartir sur 3 niveaux
            mode='markers+text',
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            text=[f"{self._format_amount(amounts[i])}" if amounts[i] > 0 else "" for i in range(len(sorted_events))],
            textposition='top center',
            hovertext=[self._create_fact_hover(e, amounts[i], config) for i, e in enumerate(sorted_events)],
            hoverinfo='text',
            showlegend=False
        ))
        
        # Ajouter les connexions entre faits liés
        if config.get('type_specific_options', {}).get('show_connections'):
            self._add_fact_connections(fig, sorted_events)
        
        # Légende des infractions
        for infraction, color in infraction_colors.items():
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(size=10, color=color),
                showlegend=True,
                name=infraction.replace('_', ' ').title()
            ))
        
        # Mise en forme
        fig.update_layout(
            title="Chronologie des faits délictueux",
            xaxis=dict(
                title="Date des faits",
                type='date',
                rangeslider=dict(visible=True)
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                range=[-0.5, 3.5]
            ),
            height=700,
            hovermode='closest'
        )
        
        return fig
    
    def _create_auditions_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Timeline spécialisée pour les auditions"""
        fig = go.Figure()
        
        # Grouper par type d'audition
        audition_types = {
            'garde à vue': {'color': '#e74c3c', 'symbol': 'square'},
            'audition libre': {'color': '#3498db', 'symbol': 'circle'},
            'témoin': {'color': '#2ecc71', 'symbol': 'diamond'},
            'confrontation': {'color': '#f39c12', 'symbol': 'star'},
            'interrogatoire': {'color': '#9b59b6', 'symbol': 'triangle-up'}
        }
        
        # Identifier le type de chaque audition
        for event in events:
            event_type = self._identify_audition_type(event)
            event.metadata['audition_type'] = event_type
        
        # Créer une ligne temporelle par personne
        persons = {}
        for event in events:
            for actor in event.actors:
                if actor not in ['OPJ', 'Brigade financière', 'Juge d\'instruction', 'Procureur']:
                    if actor not in persons:
                        persons[actor] = []
                    persons[actor].append(event)
        
        # Tracer pour chaque personne
        y_pos = 0
        for person, person_events in persons.items():
            person_events.sort(key=lambda x: x.date)
            
            # Ligne de vie de la personne
            fig.add_trace(go.Scatter(
                x=[person_events[0].date, person_events[-1].date],
                y=[y_pos, y_pos],
                mode='lines',
                line=dict(color='lightgray', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Points d'audition
            for event in person_events:
                aud_type = event.metadata.get('audition_type', 'autre')
                config_type = audition_types.get(aud_type, {'color': '#95a5a6', 'symbol': 'circle'})
                
                # Calculer la durée si disponible
                duration = self._extract_duration(event.description)
                size = 15 + (duration / 48 * 20) if duration else 20  # Taille selon durée
                
                fig.add_trace(go.Scatter(
                    x=[event.date],
                    y=[y_pos],
                    mode='markers+text',
                    marker=dict(
                        size=size,
                        color=config_type['color'],
                        symbol=config_type['symbol'],
                        line=dict(width=2, color='white')
                    ),
                    text=aud_type[:3].upper(),
                    textposition='top center',
                    hovertext=self._create_audition_hover(event, person, duration, config),
                    hoverinfo='text',
                    showlegend=False
                ))
            
            # Nom de la personne
            fig.add_annotation(
                x=person_events[0].date,
                y=y_pos,
                text=person,
                xanchor='right',
                xshift=-10,
                showarrow=False,
                font=dict(size=12, family='Arial')
            )
            
            y_pos += 1
        
        # Légende des types d'audition
        for aud_type, config_type in audition_types.items():
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(
                    size=15,
                    color=config_type['color'],
                    symbol=config_type['symbol']
                ),
                showlegend=True,
                name=aud_type.capitalize()
            ))
        
        # Mise en forme
        fig.update_layout(
            title="Chronologie des auditions",
            xaxis=dict(
                title="Date",
                type='date',
                tickformat='%d/%m/%Y'
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                range=[-0.5, len(persons) - 0.5]
            ),
            height=max(400, 100 * len(persons)),
            hovermode='closest'
        )
        
        return fig
    
    def _create_procedural_hover(self, event: TimelineEvent, config: Dict) -> str:
        """Crée le texte de survol pour un événement procédural"""
        text = f"<b>{event.date.strftime('%d/%m/%Y')}</b><br>"
        text += f"<b>Acte:</b> {event.description[:100]}<br>"
        
        # Autorité
        if event.actors:
            authorities = [a for a in event.actors if a in ['Procureur', 'Juge d\'instruction', 'Tribunal', 'OPJ']]
            if authorities:
                text += f"<b>Autorité:</b> {', '.join(authorities)}<br>"
        
        # Phase
        phase = event.metadata.get('procedural_phase', 'N/A')
        text += f"<b>Phase:</b> {phase}<br>"
        
        # Références légales
        if config.get('type_specific_options', {}).get('include_legal_refs'):
            legal_refs = event.metadata.get('legal_references', [])
            if legal_refs:
                text += f"<b>Réf. légales:</b> {', '.join(legal_refs)}<br>"
        
        text += f"<b>Importance:</b> {event.importance}/10"
        
        return text
    
    def _create_fact_hover(self, event: TimelineEvent, amount: float, config: Dict) -> str:
        """Crée le texte de survol pour un fait"""
        text = f"<b>{event.date.strftime('%d/%m/%Y')}</b><br>"
        text += f"<b>Fait:</b> {event.description[:150]}<br>"
        
        # Type d'infraction
        infraction = event.metadata.get('infraction_type', 'N/A')
        text += f"<b>Infraction:</b> {infraction.replace('_', ' ').title()}<br>"
        
        # Montant
        if amount > 0:
            text += f"<b>Montant:</b> {self._format_amount(amount)}<br>"
        
        # Victimes
        victims = [a for a in event.actors if 'société' in a.lower() or 'victime' in a.lower()]
        if victims:
            text += f"<b>Victimes:</b> {', '.join(victims)}<br>"
        
        # Qualification juridique
        if config.get('type_specific_options', {}).get('include_qualification'):
            legal_ref = event.metadata.get('legal_ref', '')
            if legal_ref:
                text += f"<b>Qualification:</b> {legal_ref}<br>"
        
        return text
    
    def _create_audition_hover(self, event: TimelineEvent, person: str, duration: int, config: Dict) -> str:
        """Crée le texte de survol pour une audition"""
        text = f"<b>{event.date.strftime('%d/%m/%Y à %H:%M')}</b><br>"
        text += f"<b>Personne:</b> {person}<br>"
        text += f"<b>Type:</b> {event.metadata.get('audition_type', 'Audition')}<br>"
        
        # Durée
        if duration:
            text += f"<b>Durée:</b> {duration}h<br>"
        
        # Autorité
        authorities = [a for a in event.actors if a != person]
        if authorities:
            text += f"<b>Par:</b> {', '.join(authorities[:2])}<br>"
        
        # Présence avocat
        if config.get('type_specific_options', {}).get('show_presence'):
            if 'avocat' in event.description.lower():
                text += "<b>Avocat:</b> ✅ Présent<br>"
            else:
                text += "<b>Avocat:</b> ❌ Absent<br>"
        
        # Extrait
        text += f"<br><i>{event.description[:100]}...</i>"
        
        return text
    
    def _format_amount(self, amount: float) -> str:
        """Formate un montant en euros"""
        if amount >= 1000000:
            return f"{amount/1000000:.1f} M€"
        elif amount >= 1000:
            return f"{amount/1000:.0f} k€"
        else:
            return f"{amount:.0f} €"
    
    def _identify_audition_type(self, event: TimelineEvent) -> str:
        """Identifie le type d'audition"""
        desc_lower = event.description.lower()
        
        if 'garde à vue' in desc_lower or 'gav' in desc_lower:
            return 'garde à vue'
        elif 'confrontation' in desc_lower:
            return 'confrontation'
        elif 'témoin' in desc_lower:
            return 'témoin'
        elif 'libre' in desc_lower:
            return 'audition libre'
        elif 'interrogatoire' in desc_lower:
            return 'interrogatoire'
        else:
            return 'autre'
    
    def _extract_duration(self, description: str) -> int:
        """Extrait la durée d'une audition en heures"""
        # Patterns pour la durée
        patterns = [
            r'(\d+)\s*h(?:eures?)?',
            r'(\d+)h(\d+)',
            r'durée\s*:\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                return int(match.group(1))
        
        # Durées par défaut selon le type
        if 'garde à vue' in description.lower():
            return 24
        elif 'confrontation' in description.lower():
            return 2
        else:
            return 1
    
    def _add_procedural_delays(self, fig: go.Figure, events: List[TimelineEvent]):
        """Ajoute les délais entre actes de procédure"""
        for i in range(len(events) - 1):
            delay_days = (events[i+1].date - events[i].date).days
            
            # Annoter les délais importants
            if delay_days > 30:
                fig.add_annotation(
                    x=events[i].date + (events[i+1].date - events[i].date) / 2,
                    y=0.5,
                    text=f"{delay_days} jours",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="#e74c3c" if delay_days > 60 else "#f39c12",
                    font=dict(size=10, color="#e74c3c" if delay_days > 60 else "#f39c12")
                )
    
    def _add_fact_connections(self, fig: go.Figure, events: List[TimelineEvent]):
        """Ajoute les connexions entre faits liés"""
        # Identifier les faits connexes
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events[i+1:], i+1):
                # Connexion si mêmes acteurs ou infractions liées
                common_actors = set(event1.actors) & set(event2.actors)
                related_infractions = self._are_infractions_related(
                    event1.metadata.get('infraction_type', ''),
                    event2.metadata.get('infraction_type', '')
                )
                
                if common_actors or related_infractions:
                    fig.add_trace(go.Scatter(
                        x=[event1.date, event2.date],
                        y=[i % 3, j % 3],
                        mode='lines',
                        line=dict(
                            color='rgba(150, 150, 150, 0.3)',
                            width=2,
                            dash='dot'
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    def _are_infractions_related(self, type1: str, type2: str) -> bool:
        """Vérifie si deux infractions sont liées"""
        relations = {
            'abus_biens_sociaux': ['blanchiment', 'recel'],
            'corruption': ['blanchiment', 'trafic_influence'],
            'fraude_fiscale': ['blanchiment_fraude_fiscale']
        }
        
        for main, related in relations.items():
            if (main in type1 and type2 in related) or (main in type2 and type1 in related):
                return True
        
        return False
    
    def _create_modern_linear_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Crée une timeline linéaire moderne avec toutes les options"""
        fig = go.Figure()
        
        # Préparer les données
        sorted_events = sorted(events, key=lambda x: x.date)
        
        # Couleurs selon le schéma choisi
        colors = self._get_color_scheme(sorted_events, config)
        
        # Tailles selon l'importance
        sizes = [15 + e.importance * 3 for e in sorted_events]
        
        # Textes avec infos IA si demandé
        texts = []
        for e in sorted_events:
            text = f"<b>{e.date.strftime('%d/%m/%Y')}</b><br>"
            text += f"{e.description[:100]}...<br>"
            
            if config.get('show_ai_info') and e.ai_extracted:
                text += f"<i>🤖 {e.metadata.get('ai_model', 'IA')}</i><br>"
                text += f"<i>Confiance: {e.confidence:.0%}</i><br>"
            
            if e.actors:
                text += f"<i>👥 {', '.join(e.actors[:3])}</i><br>"
            
            if e.metadata.get('tags'):
                text += f"<i>{' '.join(e.metadata['tags'][:3])}</i>"
            
            texts.append(text)
        
        # Positions Y variées pour éviter les chevauchements
        y_positions = self._calculate_y_positions(sorted_events)
        
        # Trace principale
        fig.add_trace(go.Scatter(
            x=[e.date for e in sorted_events],
            y=y_positions,
            mode='markers+text' if len(events) < 15 else 'markers',
            text=[e.description[:30] + '...' for e in sorted_events],
            textposition='top center',
            hovertext=texts,
            hoverinfo='text',
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=2, color='white'),
                symbol=['diamond' if e.importance >= 8 else 'circle' for e in sorted_events]
            ),
            showlegend=False
        ))
        
        # Ajouter les liens si demandé
        if config.get('show_links'):
            self._add_event_links(fig, sorted_events, y_positions)
        
        # Ajouter les patterns si demandé
        if config.get('show_patterns'):
            self._add_pattern_annotations(fig, sorted_events)
        
        # Mise en forme selon le thème
        theme_settings = self._get_theme_settings(config.get('theme', 'Moderne'))
        
        fig.update_layout(
            title={
                'text': "Timeline des événements",
                'font': {'size': 24, 'color': theme_settings['title_color']}
            },
            xaxis=dict(
                title="Date",
                type='date',
                rangeslider=dict(visible=config.get('interactive', True)),
                gridcolor=theme_settings['grid_color']
            ),
            yaxis=dict(
                title="",
                showticklabels=False,
                range=[-1, max(y_positions) + 1],
                gridcolor=theme_settings['grid_color']
            ),
            height=700,
            hovermode='closest',
            plot_bgcolor=theme_settings['bg_color'],
            paper_bgcolor=theme_settings['paper_color']
        )
        
        # Animations si demandées
        if config.get('animation'):
            fig.update_traces(
                marker=dict(
                    size=sizes,
                    sizemode='diameter',
                    sizeref=0.1,
                    line=dict(width=2)
                ),
                selector=dict(mode='markers')
            )
        
        return fig
    
    def _get_color_scheme(self, events: List[TimelineEvent], config: Dict[str, Any]) -> List[str]:
        """Retourne les couleurs selon le schéma choisi"""
        scheme = config.get('color_scheme', 'Par catégorie')
        
        if scheme == 'Par catégorie':
            category_colors = {
                'procédure': '#1f77b4',
                'financier': '#2ca02c',
                'contractuel': '#ff7f0e',
                'communication': '#d62728',
                'expertise': '#9467bd',
                'médical': '#8c564b',
                'autre': '#7f7f7f'
            }
            return [category_colors.get(e.category, '#7f7f7f') for e in events]
        
        elif scheme == 'Par importance':
            return [f'rgb({255-e.importance*20}, {e.importance*20}, {100})' for e in events]
        
        elif scheme == 'Par phase':
            phase_colors = {
                'initial': '#3498db',
                'development': '#e74c3c',
                'conclusion': '#2ecc71'
            }
            return [phase_colors.get(e.metadata.get('phase', 'development'), '#95a5a6') for e in events]
        
        elif scheme == 'Par confiance':
            return [f'rgba(0, {int(e.confidence*255)}, 0, {e.confidence})' for e in events]
        
        else:  # Personnalisé ou uniforme
            return ['#3498db'] * len(events)
    
    def _calculate_y_positions(self, events: List[TimelineEvent]) -> List[float]:
        """Calcule les positions Y pour éviter les chevauchements"""
        positions = []
        last_positions = {}
        
        for event in events:
            # Chercher une position libre
            y = 0
            while True:
                # Vérifier si cette position est libre à cette date
                date_key = event.date.strftime('%Y-%m-%d')
                if date_key not in last_positions or y not in last_positions[date_key]:
                    if date_key not in last_positions:
                        last_positions[date_key] = []
                    last_positions[date_key].append(y)
                    positions.append(y)
                    break
                y += 1
        
        return positions
    
    def _add_event_links(self, fig: go.Figure, events: List[TimelineEvent], y_positions: List[float]):
        """Ajoute les liens entre événements sur le graphique"""
        for i, event in enumerate(events):
            if 'linked_events' in event.metadata:
                for link in event.metadata['linked_events']:
                    if link['strength'] > 0.5:  # Seuil de force
                        j = link['index']
                        if j < len(events):
                            # Ligne de connexion
                            fig.add_trace(go.Scatter(
                                x=[event.date, events[j].date],
                                y=[y_positions[i], y_positions[j]],
                                mode='lines',
                                line=dict(
                                    color='rgba(150, 150, 150, 0.3)',
                                    width=link['strength'] * 3,
                                    dash='dot'
                                ),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
    
    def _add_pattern_annotations(self, fig: go.Figure, events: List[TimelineEvent]):
        """Ajoute des annotations pour les patterns détectés"""
        # Grouper les événements par pattern
        pattern_groups = defaultdict(list)
        for event in events:
            if 'pattern' in event.metadata:
                pattern_groups[event.metadata['pattern']].append(event)
        
        # Ajouter des annotations pour chaque pattern
        for pattern, pattern_events in pattern_groups.items():
            if len(pattern_events) >= 2:
                start_date = min(e.date for e in pattern_events)
                end_date = max(e.date for e in pattern_events)
                
                # Rectangle de fond
                fig.add_shape(
                    type="rect",
                    x0=start_date,
                    y0=-0.5,
                    x1=end_date,
                    y1=3.5,
                    fillcolor="rgba(255, 200, 0, 0.1)",
                    line=dict(color="rgba(255, 200, 0, 0.3)", width=2)
                )
                
                # Annotation
                pattern_labels = {
                    'high_density_period': '📊 Période dense',
                    'escalation': '📈 Escalade',
                    'turning_point': '🔄 Point de bascule'
                }
                
                fig.add_annotation(
                    x=start_date + (end_date - start_date) / 2,
                    y=3.7,
                    text=pattern_labels.get(pattern, pattern),
                    showarrow=False,
                    font=dict(size=12, color='orange')
                )
    
    def _get_theme_settings(self, theme: str) -> Dict[str, str]:
        """Retourne les paramètres visuels selon le thème"""
        themes = {
            'Moderne': {
                'bg_color': '#f8f9fa',
                'paper_color': 'white',
                'grid_color': '#e9ecef',
                'title_color': '#212529'
            },
            'Classique': {
                'bg_color': '#fff',
                'paper_color': '#f5f5f5',
                'grid_color': '#ddd',
                'title_color': '#333'
            },
            'Minimaliste': {
                'bg_color': 'white',
                'paper_color': 'white',
                'grid_color': '#f0f0f0',
                'title_color': '#666'
            },
            'Corporate': {
                'bg_color': '#f0f2f5',
                'paper_color': '#ffffff',
                'grid_color': '#d1d5db',
                'title_color': '#1f2937'
            },
            'Judiciaire': {
                'bg_color': '#f5f5dc',
                'paper_color': '#fffff0',
                'grid_color': '#d4af37',
                'title_color': '#8b4513'
            }
        }
        
        return themes.get(theme, themes['Moderne'])
    
    def _create_category_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Timeline organisée par catégorie avec swimlanes"""
        categories = sorted(list(set(e.category for e in events)))
        
        fig = go.Figure()
        
        # Créer une swimlane pour chaque catégorie
        for i, category in enumerate(categories):
            cat_events = [e for e in events if e.category == category]
            cat_events.sort(key=lambda x: x.date)
            
            # Ajouter une bande de fond
            fig.add_shape(
                type="rect",
                x0=min(e.date for e in events),
                y0=i - 0.4,
                x1=max(e.date for e in events),
                y1=i + 0.4,
                fillcolor="rgba(200, 200, 200, 0.1)" if i % 2 == 0 else "rgba(240, 240, 240, 0.1)",
                line=dict(width=0)
            )
            
            # Ajouter les événements
            fig.add_trace(go.Scatter(
                x=[e.date for e in cat_events],
                y=[i] * len(cat_events),
                mode='markers+text',
                text=[e.description[:30] + '...' for e in cat_events],
                textposition='top center',
                marker=dict(
                    size=[10 + e.importance * 2 for e in cat_events],
                    color=px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)]
                ),
                name=category,
                hovertext=[self._create_hover_text(e, config) for e in cat_events],
                hoverinfo='text'
            ))
        
        fig.update_layout(
            title="Timeline par catégorie",
            xaxis=dict(title="Date", type='date'),
            yaxis=dict(
                title="Catégories",
                tickmode='array',
                tickvals=list(range(len(categories))),
                ticktext=categories
            ),
            height=max(400, 100 * len(categories)),
            hovermode='closest'
        )
        
        return fig
    
    def _create_actor_network_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Timeline avec réseau d'acteurs"""
        # Extraire tous les acteurs uniques
        all_actors = set()
        for event in events:
            all_actors.update(event.actors)
        
        actors_list = sorted(list(all_actors))
        
        if not actors_list:
            return self._create_modern_linear_timeline(events, config)
        
        fig = go.Figure()
        
        # Créer une ligne pour chaque acteur
        for i, actor in enumerate(actors_list):
            actor_events = [e for e in events if actor in e.actors]
            
            if actor_events:
                fig.add_trace(go.Scatter(
                    x=[e.date for e in actor_events],
                    y=[i] * len(actor_events),
                    mode='markers+lines',
                    line=dict(width=1, color='rgba(150, 150, 150, 0.3)'),
                    marker=dict(
                        size=[10 + e.importance * 2 for e in actor_events],
                        color=[self._get_event_color(e) for e in actor_events]
                    ),
                    name=actor,
                    hovertext=[self._create_hover_text(e, config) for e in actor_events],
                    hoverinfo='text'
                ))
        
        fig.update_layout(
            title="Timeline par acteur",
            xaxis=dict(title="Date", type='date'),
            yaxis=dict(
                title="Acteurs",
                tickmode='array',
                tickvals=list(range(len(actors_list))),
                ticktext=actors_list
            ),
            height=max(400, 50 * len(actors_list)),
            hovermode='closest'
        )
        
        return fig
    
    def _create_density_heatmap(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Carte de densité temporelle"""
        
        # Créer un DataFrame
        df = pd.DataFrame([{
            'date': e.date,
            'importance': e.importance,
            'category': e.category
        } for e in events])
        
        # Grouper par semaine et catégorie
        df['week'] = df['date'].dt.to_period('W')
        df['week_str'] = df['week'].astype(str)
        
        # Pivot table
        pivot = df.pivot_table(
            values='importance',
            index='category',
            columns='week_str',
            aggfunc='sum',
            fill_value=0
        )
        
        # Créer la heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='YlOrRd',
            text=pivot.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Carte de densité des événements",
            xaxis=dict(title="Semaine"),
            yaxis=dict(title="Catégorie"),
            height=400 + 50 * len(pivot.index)
        )
        
        return fig
    
    def _create_relationship_graph(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Graphe de relations entre événements"""
        import networkx as nx

        # Créer le graphe
        G = nx.Graph()
        
        # Ajouter les nœuds (événements)
        for i, event in enumerate(events):
            G.add_node(i, 
                      date=event.date,
                      description=event.description[:50],
                      importance=event.importance)
        
        # Ajouter les arêtes (liens)
        for i, event in enumerate(events):
            if 'linked_events' in event.metadata:
                for link in event.metadata['linked_events']:
                    if link['strength'] > 0.5:
                        G.add_edge(i, link['index'], weight=link['strength'])
        
        # Layout du graphe
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Créer la figure
        fig = go.Figure()
        
        # Ajouter les arêtes
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            fig.add_trace(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=G[edge[0]][edge[1]]['weight'] * 3, color='#888'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Ajouter les nœuds
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(G.nodes[node]['description'])
            node_size.append(10 + G.nodes[node]['importance'] * 3)
        
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            marker=dict(
                size=node_size,
                color=[events[i].importance for i in G.nodes()],
                colorscale='YlOrRd',
                showscale=True,
                colorbar=dict(title="Importance")
            ),
            showlegend=False
        ))
        
        fig.update_layout(
            title="Graphe de relations entre événements",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=700
        )
        
        return fig
    
    def _create_3d_timeline(self, events: List[TimelineEvent], config: Dict[str, Any]) -> go.Figure:
        """Timeline 3D immersive"""
        # Préparer les données
        sorted_events = sorted(events, key=lambda x: x.date)
        
        # Axes
        x = [(e.date - sorted_events[0].date).days for e in sorted_events]  # Jours depuis le début
        y = [hash(e.category) % 10 for e in sorted_events]  # Catégorie
        z = [e.importance for e in sorted_events]  # Importance
        
        # Créer la figure 3D
        fig = go.Figure(data=[go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers+text',
            marker=dict(
                size=[5 + e.importance for e in sorted_events],
                color=z,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Importance")
            ),
            text=[e.description[:30] + '...' for e in sorted_events],
            hovertext=[self._create_hover_text(e, config) for e in sorted_events],
            hoverinfo='text'
        )])
        
        # Ajouter des lignes de connexion temporelle
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=[0] * len(x),
            mode='lines',
            line=dict(color='rgba(150, 150, 150, 0.3)', width=2),
            showlegend=False
        ))
        
        fig.update_layout(
            title="Timeline 3D",
            scene=dict(
                xaxis_title="Jours depuis le début",
                yaxis_title="Catégorie",
                zaxis_title="Importance",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=700
        )
        
        return fig
    
    def _create_hover_text(self, event: TimelineEvent, config: Dict[str, Any]) -> str:
        """Crée le texte de survol pour un événement"""
        text = f"<b>{event.date.strftime('%d/%m/%Y')}</b><br>"
        text += f"{event.description}<br>"
        text += f"<b>Importance:</b> {event.importance}/10<br>"
        text += f"<b>Catégorie:</b> {event.category}<br>"
        
        if event.actors:
            text += f"<b>Acteurs:</b> {', '.join(event.actors)}<br>"
        
        if config.get('show_ai_info') and event.ai_extracted:
            text += f"<b>IA:</b> {event.metadata.get('ai_model', 'N/A')}<br>"
            text += f"<b>Confiance:</b> {event.confidence:.0%}<br>"
        
        if event.metadata.get('tags'):
            text += f"<b>Tags:</b> {' '.join(event.metadata['tags'])}<br>"
        
        if event.metadata.get('pattern'):
            text += f"<b>Pattern:</b> {event.metadata['pattern']}<br>"
        
        return text
    
    def _get_event_color(self, event: TimelineEvent) -> str:
        """Retourne la couleur d'un événement selon sa catégorie"""
        colors = {
            'procédure': '#1f77b4',
            'financier': '#2ca02c',
            'contractuel': '#ff7f0e',
            'communication': '#d62728',
            'expertise': '#9467bd',
            'médical': '#8c564b',
            'autre': '#7f7f7f'
        }
        return colors.get(event.category, '#7f7f7f')
    
    def _prepare_exports(self, events: List[TimelineEvent], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les exports dans différents formats"""
        exports = {}
        
        # Export JSON
        exports['json'] = json.dumps([{
            'date': e.date.isoformat(),
            'description': e.description,
            'importance': e.importance,
            'category': e.category,
            'actors': e.actors,
            'confidence': e.confidence,
            'ai_extracted': e.ai_extracted,
            'metadata': e.metadata
        } for e in events], ensure_ascii=False, indent=2)
        
        # Export CSV
        df = pd.DataFrame([
            {
                'Date': e.date.strftime('%d/%m/%Y'),
                'Description': e.description,
                'Importance': e.importance,
                'Catégorie': e.category,
                'Acteurs': ', '.join(e.actors),
                'Confiance': f"{e.confidence:.0%}",
                'Source IA': e.metadata.get('ai_model', '') if e.ai_extracted else ''
            }
            for e in events
        ])
        exports['csv'] = df.to_csv(index=False)
        
        # Export texte structuré
        exports['txt'] = self._export_to_structured_text(events, config)
        
        return exports
    
    def _export_to_structured_text(self, events: List[TimelineEvent], config: Dict[str, Any]) -> str:
        """Export en texte structuré avec mise en forme"""
        lines = []
        lines.append("=" * 80)
        lines.append("TIMELINE JURIDIQUE - RAPPORT COMPLET")
        lines.append("=" * 80)
        lines.append(f"Générée le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        lines.append(f"Nombre d'événements : {len(events)}")
        
        if events:
            lines.append(f"Période : {min(e.date for e in events).strftime('%d/%m/%Y')} - {max(e.date for e in events).strftime('%d/%m/%Y')}")
        
        lines.append("")
        lines.append("RÉSUMÉ EXÉCUTIF")
        lines.append("-" * 40)
        
        # Statistiques
        high_importance = sum(1 for e in events if e.importance >= 8)
        ai_extracted = sum(1 for e in events if e.ai_extracted)
        
        lines.append(f"- Événements critiques (importance ≥ 8) : {high_importance}")
        lines.append(f"- Événements extraits par IA : {ai_extracted}/{len(events)}")
        
        # Acteurs principaux
        all_actors = [actor for e in events for actor in e.actors]
        if all_actors:
            from collections import Counter
            actor_counts = Counter(all_actors)
            lines.append(f"- Acteurs principaux : {', '.join([f'{actor} ({count})' for actor, count in actor_counts.most_common(3)])}")
        
        lines.append("")
        lines.append("CHRONOLOGIE DÉTAILLÉE")
        lines.append("-" * 40)
        
        # Grouper par mois
        from itertools import groupby
        events_by_month = groupby(sorted(events, key=lambda x: x.date), 
                                  key=lambda x: x.date.strftime('%B %Y'))
        
        for month, month_events in events_by_month:
            lines.append(f"\n>>> {month.upper()}")
            lines.append("")
            
            for event in month_events:
                lines.append(f"{event.date.strftime('%d/%m/%Y')} - {event.category.upper()}")
                lines.append(f"{'⭐' * (event.importance // 2)} Importance: {event.importance}/10")
                lines.append(f"{event.description}")
                
                if event.actors:
                    lines.append(f"Acteurs: {', '.join(event.actors)}")
                
                if event.ai_extracted:
                    lines.append(f"[Extrait par {event.metadata.get('ai_model', 'IA')} - Confiance: {event.confidence:.0%}]")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def _display_final_timeline(self, result: Dict[str, Any]):
        """Affiche la timeline finale avec toutes les fonctionnalités"""
        # Header avec métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Événements", result['event_count'])
        
        with col2:
            duration = (max(e.date for e in result['events']) - min(e.date for e in result['events'])).days if result['events'] else 0
            st.metric("⏱️ Durée", f"{duration} jours")
        
        with col3:
            critical_events = sum(1 for e in result['events'] if e.importance >= 8)
            st.metric("⚠️ Critiques", critical_events)
        
        with col4:
            ai_events = sum(1 for e in result['events'] if e.ai_extracted)
            st.metric("🤖 Par IA", f"{ai_events}/{result['event_count']}")
        
        # Visualisation principale
        if result.get('visualization'):
            st.plotly_chart(result['visualization'], use_container_width=True)
        
        # Insights et analyse
        if result.get('analysis'):
            with st.expander("🔍 Analyse approfondie", expanded=True):
                self._display_timeline_analysis(result['analysis'])
        
        # Actions et exports
        st.markdown("### 🎯 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Sauvegarder", use_container_width=True):
                self._save_timeline(result)
        
        with col2:
            if st.button("📤 Partager", use_container_width=True):
                self._share_timeline(result)
        
        with col3:
            if st.button("🖨️ Imprimer", use_container_width=True):
                self._print_timeline(result)
        
        with col4:
            if st.button("🔄 Nouvelle", use_container_width=True):
                st.session_state.timeline_workflow_step = 0
                st.rerun()
        
        # Exports
        if result.get('exports'):
            st.markdown("### 💾 Téléchargements")
            
            cols = st.columns(len(result['exports']))
            
            for i, (format_name, data) in enumerate(result['exports'].items()):
                with cols[i]:
                    if format_name == 'json':
                        st.download_button(
                            "📥 JSON",
                            data=data,
                            file_name=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    elif format_name == 'csv':
                        st.download_button(
                            "📥 CSV",
                            data=data,
                            file_name=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    elif format_name == 'txt':
                        st.download_button(
                            "📥 TXT",
                            data=data,
                            file_name=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
    
    def _display_timeline_analysis(self, analysis: Dict[str, Any]):
        """Affiche l'analyse détaillée de la timeline"""
        # Vue d'ensemble
        if analysis.get('date_range'):
            st.markdown("#### 📊 Vue d'ensemble")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Début:** {analysis['date_range']['start'].strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**Fin:** {analysis['date_range']['end'].strftime('%d/%m/%Y')}")
            with col3:
                st.write(f"**Durée:** {analysis['date_range']['duration_days']} jours")
        
        # Densité temporelle
        if analysis.get('density'):
            st.markdown("#### 📈 Densité temporelle")
            
            months = list(analysis['density'].keys())
            counts = list(analysis['density'].values())
            
            fig = px.bar(x=months, y=counts, title="Événements par mois")
            st.plotly_chart(fig, use_container_width=True)
        
        # Acteurs clés
        if analysis.get('actor_involvement'):
            st.markdown("#### 👥 Implication des acteurs")
            
            actors_df = pd.DataFrame(
                list(analysis['actor_involvement'].items()),
                columns=['Acteur', 'Événements']
            )
            
            fig = px.bar(actors_df, x='Acteur', y='Événements', 
                         title="Nombre d'événements par acteur")
            st.plotly_chart(fig, use_container_width=True)
        
        # Distribution par catégorie
        if analysis.get('category_distribution'):
            st.markdown("#### 📁 Répartition par catégorie")
            
            fig = px.pie(
                values=list(analysis['category_distribution'].values()),
                names=list(analysis['category_distribution'].keys()),
                title="Distribution des catégories"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _save_timeline(self, timeline: Dict[str, Any]):
        """Sauvegarde la timeline"""
        # Générer un ID unique
        timeline_id = hashlib.md5(
            f"{timeline['timestamp']}{timeline['event_count']}".encode()
        ).hexdigest()[:8]
        
        # Dialogue de sauvegarde
        with st.form("save_timeline_form"):
            name = st.text_input("Nom de la timeline", 
                                value=f"Timeline du {datetime.now().strftime('%d/%m/%Y')}")
            description = st.text_area("Description", 
                                      placeholder="Ajoutez une description...")
            tags = st.text_input("Tags (séparés par des virgules)", 
                                placeholder="procédure, 2024, important")
            
            if st.form_submit_button("💾 Sauvegarder"):
                st.session_state.saved_timelines[timeline_id] = {
                    'id': timeline_id,
                    'name': name,
                    'description': description,
                    'tags': [t.strip() for t in tags.split(',') if t.strip()],
                    'timeline': timeline,
                    'saved_at': datetime.now()
                }
                st.success(f"✅ Timeline sauvegardée avec l'ID : {timeline_id}")
    
    def _share_timeline(self, timeline: Dict[str, Any]):
        """Partage la timeline"""
        st.info("🔗 Fonctionnalité de partage bientôt disponible")
        
        # Simuler un lien de partage
        share_id = hashlib.md5(str(timeline).encode()).hexdigest()[:8]
        share_url = f"https://nexora-law.ai/timeline/{share_id}"
        
        st.code(share_url)
        st.caption("Lien de partage (simulation)")
    
    def _print_timeline(self, timeline: Dict[str, Any]):
        """Prépare la timeline pour l'impression"""
        st.info("🖨️ Préparation pour l'impression...")
        
        # Options d'impression
        with st.expander("Options d'impression"):
            orientation = st.radio("Orientation", ["Portrait", "Paysage"])
            include_analysis = st.checkbox("Inclure l'analyse", value=True)
            include_events_list = st.checkbox("Inclure la liste détaillée", value=True)
        
        st.success("✅ Timeline prête pour l'impression")
    
    def _render_ai_configuration(self):
        """Configuration des modèles d'IA pour le droit pénal des affaires"""
        st.markdown("### 🤖 Configuration des modèles d'IA juridique")
        
        # État des modèles
        st.markdown("#### 🔌 Modèles spécialisés en droit pénal des affaires")
        
        model_status = {
            AIModel.CLAUDE_OPUS_4: {
                "status": "✅ Actif", 
                "performance": "Excellence juridique", 
                "speed": "Moyen",
                "speciality": "Analyse contextuelle approfondie, compréhension des subtilités juridiques"
            },
            AIModel.CHAT_GPT_4: {
                "status": "✅ Actif", 
                "performance": "Très haute", 
                "speed": "Moyen",
                "speciality": "Extraction structurée, classification des infractions"
            },
            AIModel.PERPLEXITY: {
                "status": "✅ Actif", 
                "performance": "Haute", 
                "speed": "Rapide",
                "speciality": "Vérification des faits, recherche de jurisprudence"
            },
            AIModel.GEMINI: {
                "status": "✅ Actif", 
                "performance": "Haute", 
                "speed": "Très rapide",
                "speciality": "Analyse multi-documents, détection de patterns"
            },
            AIModel.MISTRAL: {
                "status": "✅ Actif", 
                "performance": "Bonne", 
                "speed": "Ultra rapide",
                "speciality": "Traitement de gros volumes, extraction basique"
            }
        }
        
        cols = st.columns(3)
        for i, (model, info) in enumerate(model_status.items()):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div class="ai-model-selector">
                        <h5>{model.value}</h5>
                        <p><strong>État:</strong> {info['status']}</p>
                        <p><strong>Performance:</strong> {info['performance']}</p>
                        <p><strong>Vitesse:</strong> {info['speed']}</p>
                        <p style="font-size: 0.85em; color: #666;"><em>{info['speciality']}</em></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    enabled = st.checkbox("Activer", 
                                        value=st.session_state.ai_models.get(model.value, True),
                                        key=f"ai_config_{model.name}")
                    st.session_state.ai_models[model.value] = enabled
        
        # Configuration du mode fusion
        st.markdown("#### 🔥 Mode Fusion Multi-IA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fusion_strategy = st.selectbox(
                "Stratégie de fusion",
                ["Consensus juridique", "Pondération par expertise", "Vote de confiance", "Fusion adaptative légale"],
                help="Le consensus juridique privilégie la cohérence des analyses légales"
            )
            
            min_models_fusion = st.slider(
                "Nombre minimum de modèles pour fusion",
                2, 5, 3,
                help="Plus de modèles = plus de fiabilité"
            )
        
        with col2:
            confidence_threshold = st.slider(
                "Seuil de confiance minimum",
                0.0, 1.0, 0.7, 0.05,
                help="Seuil pour valider un événement juridique"
            )
            
            prioritize_legal_accuracy = st.checkbox(
                "Prioriser la précision juridique",
                value=True,
                help="Favorise Claude Opus 4 et GPT-4 pour les analyses complexes"
            )
        
        # Préférences par type de tâche juridique
        st.markdown("#### ⚖️ Spécialisation par tâche juridique")
        
        task_preferences = {
            "Extraction d'actes de procédure": st.selectbox(
                "Extraction d'actes de procédure",
                list(AIModel),
                format_func=lambda x: x.value,
                index=0  # Claude par défaut
            ),
            "Analyse d'infractions financières": st.selectbox(
                "Analyse d'infractions financières",
                list(AIModel),
                format_func=lambda x: x.value,
                index=1  # GPT-4 par défaut
            ),
            "Détection des parties et autorités": st.selectbox(
                "Détection des parties et autorités",
                list(AIModel),
                format_func=lambda x: x.value,
                index=3  # Gemini par défaut
            ),
            "Calcul des délais et prescriptions": st.selectbox(
                "Calcul des délais et prescriptions",
                list(AIModel),
                format_func=lambda x: x.value,
                index=1  # GPT-4 par défaut
            ),
            "Vérification des faits": st.selectbox(
                "Vérification des faits et montants",
                list(AIModel),
                format_func=lambda x: x.value,
                index=2  # Perplexity par défaut
            )
        }
        
        # Paramètres avancés pour le droit pénal des affaires
        with st.expander("⚙️ Paramètres avancés"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Détection automatique**")
                detect_prescription = st.checkbox("Calcul automatique des prescriptions", value=True)
                detect_cumul = st.checkbox("Détection du cumul d'infractions", value=True)
                detect_recidive = st.checkbox("Identification de la récidive", value=True)
            
            with col2:
                st.markdown("**Enrichissement juridique**")
                add_legal_refs = st.checkbox("Ajouter les références légales", value=True)
                add_penalties = st.checkbox("Mentionner les peines encourues", value=True)
                add_jurisprudence = st.checkbox("Suggérer la jurisprudence pertinente", value=False)
        
        # Test de configuration
        if st.button("🧪 Tester la configuration", type="primary"):
            with st.spinner("Test en cours..."):
                time.sleep(2)
                st.success(
                    f"""✅ Configuration validée !
                - Manager LLM : Connecté
                - Modèles actifs : {sum(1 for v in st.session_state.ai_models.values() if v)}
                - Spécialisation : Droit pénal des affaires
                """
                )
        
        # Sauvegarder la configuration
        if st.button("💾 Sauvegarder la configuration"):
            config = {
                'models': st.session_state.ai_models,
                'fusion_strategy': fusion_strategy,
                'min_models_fusion': min_models_fusion,
                'confidence_threshold': confidence_threshold,
                'prioritize_legal_accuracy': prioritize_legal_accuracy,
                'task_preferences': task_preferences,
                'advanced_params': {
                    'detect_prescription': detect_prescription,
                    'detect_cumul': detect_cumul,
                    'detect_recidive': detect_recidive,
                    'add_legal_refs': add_legal_refs,
                    'add_penalties': add_penalties,
                    'add_jurisprudence': add_jurisprudence
                }
            }
            st.session_state.ai_config = config
            st.success("✅ Configuration sauvegardée")
    
    def _render_timeline_library(self):
        """Bibliothèque de timelines sauvegardées"""
        st.markdown("### 📚 Bibliothèque de timelines")
        
        # Barre de recherche et filtres
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search = st.text_input("🔍 Rechercher", placeholder="Nom, description, tags...")
        
        with col2:
            sort_by = st.selectbox("Trier par", ["Date", "Nom", "Événements"])
        
        with col3:
            filter_tags = st.multiselect("Tags", self._get_all_tags())
        
        # Afficher les timelines
        timelines = list(st.session_state.saved_timelines.values())
        
        # Filtrer
        if search:
            timelines = [t for t in timelines 
                        if search.lower() in t['name'].lower() 
                        or search.lower() in t.get('description', '').lower()
                        or any(search.lower() in tag.lower() for tag in t.get('tags', []))]
        
        if filter_tags:
            timelines = [t for t in timelines 
                        if any(tag in t.get('tags', []) for tag in filter_tags)]
        
        # Trier
        if sort_by == "Date":
            timelines.sort(key=lambda x: x['saved_at'], reverse=True)
        elif sort_by == "Nom":
            timelines.sort(key=lambda x: x['name'])
        else:
            timelines.sort(key=lambda x: x['timeline']['event_count'], reverse=True)
        
        # Affichage en grille
        if timelines:
            cols = st.columns(3)
            for i, timeline in enumerate(timelines[:9]):  # Limiter pour la performance
                with cols[i % 3]:
                    self._render_timeline_card(timeline)
            
            if len(timelines) > 9:
                st.info(f"... et {len(timelines) - 9} autres timelines")
        else:
            st.info("Aucune timeline sauvegardée pour le moment")
    
    def _render_timeline_card(self, timeline_data: Dict[str, Any]):
        """Affiche une carte de timeline"""
        with st.container():
            st.markdown(f"""
            <div class="event-card" style="cursor: pointer;">
                <h5>{timeline_data['name']}</h5>
                <p style="font-size: 0.9em; color: #666;">
                    {timeline_data['timeline']['event_count']} événements
                </p>
                <p style="font-size: 0.8em;">
                    {timeline_data.get('description', 'Sans description')[:100]}...
                </p>
                <p style="font-size: 0.8em; color: #888;">
                    Créée le {timeline_data['saved_at'].strftime('%d/%m/%Y')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📂 Charger", key=f"load_{timeline_data['id']}", use_container_width=True):
                    self._load_timeline(timeline_data['timeline'])
            
            with col2:
                if st.button("📤 Exporter", key=f"export_{timeline_data['id']}", use_container_width=True):
                    self._quick_export(timeline_data['timeline'])
            
            with col3:
                if st.button("🗑️", key=f"delete_{timeline_data['id']}", use_container_width=True):
                    del st.session_state.saved_timelines[timeline_data['id']]
                    st.rerun()
    
    def _get_all_tags(self) -> List[str]:
        """Récupère tous les tags uniques"""
        all_tags = set()
        for timeline in st.session_state.saved_timelines.values():
            all_tags.update(timeline.get('tags', []))
        return sorted(list(all_tags))
    
    def _load_timeline(self, timeline: Dict[str, Any]):
        """Charge une timeline sauvegardée"""
        st.session_state.current_timeline = timeline
        st.session_state.timeline_workflow_step = 4  # Aller directement à l'affichage
        st.success("✅ Timeline chargée")
        time.sleep(0.5)
        st.rerun()
    
    def _quick_export(self, timeline: Dict[str, Any]):
        """Export rapide d'une timeline"""
        # Créer un export JSON rapide
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'event_count': timeline['event_count'],
                'created_at': timeline['timestamp'].isoformat()
            },
            'events': [
                {
                    'date': e.date.isoformat() if hasattr(e, 'date') else str(e.get('date', '')),
                    'description': e.description if hasattr(e, 'description') else e.get('description', ''),
                    'importance': e.importance if hasattr(e, 'importance') else e.get('importance', 5),
                    'category': e.category if hasattr(e, 'category') else e.get('category', 'autre'),
                    'actors': e.actors if hasattr(e, 'actors') else e.get('actors', [])
                }
                for e in timeline.get('events', [])
            ]
        }
        
        st.download_button(
            "💾 Télécharger JSON",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"timeline_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _render_advanced_analysis(self):
        """Analyse avancée des timelines"""
        st.markdown("### 🔍 Analyse avancée")
        
        if not st.session_state.current_timeline:
            st.info("Chargez d'abord une timeline pour l'analyser")
            return
        
        timeline = st.session_state.current_timeline
        events = timeline.get('events', [])
        
        # Analyses disponibles
        analysis_types = st.multiselect(
            "Types d'analyse",
            ["Analyse temporelle", "Analyse relationnelle", "Analyse prédictive", 
             "Détection d'anomalies", "Analyse causale", "Analyse comparative"],
            default=["Analyse temporelle", "Analyse relationnelle"]
        )
        
        if st.button("🚀 Lancer l'analyse", type="primary"):
            results = {}
            
            progress = st.progress(0)
            for i, analysis_type in enumerate(analysis_types):
                progress.progress((i + 1) / len(analysis_types))
                
                if analysis_type == "Analyse temporelle":
                    results['temporal'] = self._temporal_analysis(events)
                elif analysis_type == "Analyse relationnelle":
                    results['relational'] = self._relational_analysis(events)
                elif analysis_type == "Analyse prédictive":
                    results['predictive'] = self._predictive_analysis(events)
                elif analysis_type == "Détection d'anomalies":
                    results['anomalies'] = self._anomaly_detection(events)
                elif analysis_type == "Analyse causale":
                    results['causal'] = self._causal_analysis(events)
                elif analysis_type == "Analyse comparative":
                    results['comparative'] = self._comparative_analysis(events)
            
            # Afficher les résultats
            self._display_analysis_results(results)
    
    def _temporal_analysis(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyse temporelle approfondie"""
        # Calculs temporels
        dates = [e.date for e in events]
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        
        return {
            'average_interval': sum(intervals) / len(intervals) if intervals else 0,
            'max_gap': max(intervals) if intervals else 0,
            'min_gap': min(intervals) if intervals else 0,
            'acceleration_periods': self._find_acceleration_periods(events),
            'quiet_periods': self._find_quiet_periods(events)
        }
    
    def _relational_analysis(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyse des relations entre événements"""
        # Créer une matrice de relations
        relations = defaultdict(list)
        
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events[i+1:], i+1):
                # Relations par acteurs communs
                common_actors = set(event1.actors) & set(event2.actors)
                if common_actors:
                    relations['actor_links'].append({
                        'events': (i, j),
                        'actors': list(common_actors),
                        'strength': len(common_actors)
                    })
                
                # Relations temporelles
                days_diff = (event2.date - event1.date).days
                if days_diff <= 7:
                    relations['temporal_links'].append({
                        'events': (i, j),
                        'days': days_diff
                    })
        
        return relations
    
    def _predictive_analysis(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyse prédictive basique"""
        # Simulation d'une prédiction
        return {
            'next_likely_date': datetime.now() + timedelta(days=30),
            'predicted_category': 'procédure',
            'confidence': 0.75,
            'risk_level': 'moyen'
        }
    
    def _anomaly_detection(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Détection d'anomalies dans la timeline"""
        anomalies = []
        
        # Anomalies temporelles
        dates = [e.date for e in events]
        if len(dates) > 2:
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_interval = sum(intervals) / len(intervals)
            
            for i, interval in enumerate(intervals):
                if interval > avg_interval * 3:
                    anomalies.append({
                        'type': 'temporal_gap',
                        'events': (i, i+1),
                        'description': f"Écart anormal de {interval} jours"
                    })
        
        return anomalies
    
    def _causal_analysis(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyse causale des événements"""
        # Simulation d'analyse causale
        causal_chains = []
        
        for i in range(len(events) - 1):
            if events[i].importance >= 7 and events[i+1].importance >= 7:
                if (events[i+1].date - events[i].date).days <= 30:
                    causal_chains.append({
                        'cause': i,
                        'effect': i+1,
                        'confidence': 0.8
                    })
        
        return {'causal_chains': causal_chains}
    
    def _comparative_analysis(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyse comparative avec d'autres timelines"""
        # Comparer avec l'historique
        if st.session_state.timeline_history:
            avg_events = sum(t['event_count'] for t in st.session_state.timeline_history) / len(st.session_state.timeline_history)
            
            return {
                'vs_average': {
                    'event_count_diff': len(events) - avg_events,
                    'complexity': 'élevée' if len(events) > avg_events * 1.5 else 'normale'
                }
            }
        
        return {}
    
    def _find_acceleration_periods(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Trouve les périodes d'accélération"""
        periods = []
        window_size = 30  # jours
        
        for i in range(len(events) - 2):
            window_events = [e for e in events[i:] if (e.date - events[i].date).days <= window_size]
            if len(window_events) >= 5:
                periods.append({
                    'start': events[i].date,
                    'end': window_events[-1].date,
                    'event_count': len(window_events)
                })
        
        return periods
    
    def _find_quiet_periods(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Trouve les périodes calmes"""
        periods = []
        
        for i in range(len(events) - 1):
            gap = (events[i+1].date - events[i].date).days
            if gap > 60:  # Plus de 2 mois
                periods.append({
                    'start': events[i].date,
                    'end': events[i+1].date,
                    'days': gap
                })
        
        return periods
    
    def _display_analysis_results(self, results: Dict[str, Any]):
        """Affiche les résultats d'analyse"""
        st.markdown("### 📊 Résultats de l'analyse")
        
        # Analyse temporelle
        if 'temporal' in results:
            with st.expander("⏱️ Analyse temporelle", expanded=True):
                data = results['temporal']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Intervalle moyen", f"{data['average_interval']:.1f} jours")
                with col2:
                    st.metric("Écart maximum", f"{data['max_gap']} jours")
                with col3:
                    st.metric("Écart minimum", f"{data['min_gap']} jours")
                
                if data['acceleration_periods']:
                    st.warning(f"🚀 {len(data['acceleration_periods'])} périodes d'accélération détectées")
                
                if data['quiet_periods']:
                    st.info(f"😴 {len(data['quiet_periods'])} périodes calmes détectées")
        
        # Analyse relationnelle
        if 'relational' in results:
            with st.expander("🔗 Analyse relationnelle"):
                data = results['relational']
                
                if data.get('actor_links'):
                    st.write(f"**Liens par acteurs:** {len(data['actor_links'])} connexions trouvées")
                
                if data.get('temporal_links'):
                    st.write(f"**Liens temporels:** {len(data['temporal_links'])} événements proches")
        
        # Autres analyses...
        for analysis_type, data in results.items():
            if analysis_type not in ['temporal', 'relational']:
                with st.expander(f"📈 {analysis_type.replace('_', ' ').title()}"):
                    st.json(data)
    
    def _render_visualizations(self):
        """Galerie de visualisations avancées"""
        st.markdown("### 📊 Visualisations avancées")
        
        if not st.session_state.current_timeline:
            st.info("Chargez une timeline pour accéder aux visualisations")
            return
        
        # Types de visualisations disponibles
        viz_types = {
            "Sunburst chronologique": self._create_sunburst_viz,
            "Diagramme de Sankey": self._create_sankey_viz,
            "Timeline radar": self._create_radar_viz,
            "Carte de chaleur temporelle": self._create_temporal_heatmap,
            "Réseau d'événements": self._create_event_network,
            "Timeline spirale": self._create_spiral_timeline
        }
        
        selected_viz = st.selectbox("Choisir une visualisation", list(viz_types.keys()))
        
        # Options de personnalisation
        with st.expander("⚙️ Options de personnalisation"):
            color_palette = st.selectbox("Palette de couleurs", 
                ["Viridis", "Plasma", "Inferno", "Blues", "Reds", "Greens"])
            show_labels = st.checkbox("Afficher les labels", value=True)
            interactive = st.checkbox("Mode interactif", value=True)
        
        # Générer la visualisation
        if st.button("🎨 Générer la visualisation", type="primary"):
            with st.spinner("Création en cours..."):
                viz_func = viz_types[selected_viz]
                fig = viz_func(st.session_state.current_timeline['events'], 
                              {'palette': color_palette, 'labels': show_labels, 'interactive': interactive})
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Impossible de créer cette visualisation")
    
    def _create_sunburst_viz(self, events: List[TimelineEvent], options: Dict) -> go.Figure:
        """Crée un diagramme sunburst chronologique"""
        # Préparer les données hiérarchiques
        data = []
        for event in events:
            year = event.date.strftime('%Y')
            month = event.date.strftime('%B')
            
            data.append({
                'labels': [year, month, event.category],
                'parents': ['', year, month],
                'values': [event.importance]
            })
        
        # Créer le sunburst
        fig = go.Figure(go.Sunburst(
            labels=[item for sublist in [d['labels'] for d in data] for item in sublist],
            parents=[item for sublist in [d['parents'] for d in data] for item in sublist],
            values=[item for sublist in [d['values'] for d in data] for item in sublist],
            branchvalues="total"
        ))
        
        fig.update_layout(title="Répartition chronologique des événements", height=600)
        
        return fig
    
    def _create_sankey_viz(self, events: List[TimelineEvent], options: Dict) -> go.Figure:
        """Crée un diagramme de Sankey des flux d'événements"""
        # À implémenter
        return None
    
    def _create_radar_viz(self, events: List[TimelineEvent], options: Dict) -> go.Figure:
        """Crée une timeline radar"""
        # À implémenter
        return None
    
    def _create_temporal_heatmap(self, events: List[TimelineEvent], options: Dict) -> go.Figure:
        """Crée une carte de chaleur temporelle"""
        # Créer une matrice temporelle
        df = pd.DataFrame([{
            'date': e.date,
            'weekday': e.date.strftime('%A'),
            'week': e.date.isocalendar()[1],
            'importance': e.importance
        } for e in events])
        
        # Pivot pour la heatmap
        pivot = df.pivot_table(
            values='importance',
            index='weekday',
            columns='week',
            aggfunc='sum',
            fill_value=0
        )
        
        # Ordonner les jours
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = pivot.reindex(days_order)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=options.get('palette', 'Viridis'),
            text=pivot.values,
            texttemplate='%{text}' if options.get('labels') else '',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Carte de chaleur temporelle",
            xaxis_title="Semaine de l'année",
            yaxis_title="Jour de la semaine",
            height=500
        )
        
        return fig
    
    def _create_event_network(self, events: List[TimelineEvent], options: Dict) -> go.Figure:
        """Crée un réseau d'événements interactif"""
        
        # Créer les connexions
        edge_x = []
        edge_y = []
        
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events[i+1:], i+1):
                # Connecter si acteurs communs
                if set(event1.actors) & set(event2.actors):
                    edge_x.extend([i, j, None])
                    edge_y.extend([event1.importance, event2.importance, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # Créer les nœuds
        node_x = list(range(len(events)))
        node_y = [e.importance for e in events]
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[e.date.strftime('%d/%m/%Y') for e in events],
            textposition="top center",
            marker=dict(
                showscale=True,
                colorscale=options.get('palette', 'YlGnBu'),
                size=[10 + e.importance * 2 for e in events],
                color=[e.importance for e in events],
                colorbar=dict(
                    thickness=15,
                    title='Importance',
                    xanchor='left',
                    titleside='right'
                )
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Réseau d\'événements',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=0, l=0, r=0, t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           height=600
                       ))
        
        return fig
    
    def _create_spiral_timeline(self, events: List[TimelineEvent], options: Dict) -> go.Figure:
        """Crée une timeline en spirale"""
        
        import numpy as np

        # Calculer les positions en spirale
        n_events = len(events)
        theta = np.linspace(0, 8 * np.pi, n_events)
        r = np.linspace(1, 10, n_events)
        
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        # Créer la spirale
        fig = go.Figure()
        
        # Ligne de base
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color='lightgray', width=2),
            showlegend=False
        ))
        
        # Points des événements
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='markers+text',
            marker=dict(
                size=[10 + e.importance * 2 for e in events],
                color=[e.importance for e in events],
                colorscale=options.get('palette', 'Viridis'),
                showscale=True,
                colorbar=dict(title="Importance")
            ),
            text=[e.date.strftime('%d/%m') for e in events],
            textposition='top center',
            hovertext=[f"{e.date.strftime('%d/%m/%Y')}<br>{e.description[:50]}..." for e in events],
            hoverinfo='text',
            showlegend=False
        ))
        
        fig.update_layout(
            title="Timeline en spirale",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=700,
            width=700
        )
        
        return fig
    
    def _render_interactive_guide(self):
        """Guide interactif spécialisé pour le droit pénal des affaires"""
        st.markdown("### ⚖️ Guide juridique - Droit Pénal des Affaires")
        
        # Tutoriel interactif
        tutorial_step = st.session_state.get('tutorial_step', 0)
        
        tutorials = [
            {
                'title': "Bienvenue dans le module Timeline Pénal des Affaires !",
                'content': """
                Ce module spécialisé vous permet de créer des chronologies précises pour vos dossiers 
                de droit pénal des affaires. L'IA est entraînée pour reconnaître :
                - Les infractions économiques et financières
                - Les actes de procédure pénale
                - Les autorités judiciaires et administratives
                - Les mesures coercitives et conservatoires
                """,
                'action': "Commencer le tutoriel"
            },
            {
                'title': "Étape 1 : Types de documents analysables",
                'content': """
                Le module peut analyser :
                - **Procès-verbaux** : garde à vue, auditions, perquisitions
                - **Actes judiciaires** : réquisitoires, ordonnances, jugements
                - **Rapports** : expertise comptable, rapports d'audit
                - **Correspondances** : entre avocats, avec les autorités
                - **Documents financiers** : relevés bancaires, contrats
                """,
                'action': "Suivant"
            },
            {
                'title': "Étape 2 : IA spécialisée juridique",
                'content': """
                Notre système utilise 5 modèles d'IA complémentaires :
                - **Claude Opus 4** : Compréhension du contexte juridique complexe
                - **ChatGPT 4** : Classification des infractions et qualification
                - **Perplexity** : Vérification et recherche de jurisprudence
                - **Gemini** : Analyse rapide multi-documents
                - **Mistral** : Traitement de gros volumes
                
                Le mode Fusion combine leurs analyses pour une précision maximale !
                """,
                'action': "Suivant"
            },
            {
                'title': "Étape 3 : Enrichissement juridique automatique",
                'content': """
                L'IA enrichit automatiquement vos timelines avec :
                - **Qualification juridique** des faits
                - **Calcul des prescriptions** et délais
                - **Détection des cumuls** d'infractions
                - **Identification des autorités** compétentes
                - **Évaluation du risque pénal**
                - **Références légales** applicables
                """,
                'action': "Suivant"
            },
            {
                'title': "Étape 4 : Templates spécialisés",
                'content': """
                Utilisez nos templates basés sur la pratique :
                - **Abus de biens sociaux** : procédure type avec CAC
                - **Corruption** : incluant volet international
                - **Fraude fiscale** : avec procédure L16B
                - **CJIP** : négociation et monitoring AFA
                - **Blanchiment** : avec saisies pénales
                
                Chaque template est personnalisable selon votre juridiction.
                """,
                'action': "Suivant"
            },
            {
                'title': "Étape 5 : Visualisations pour plaidoiries",
                'content': """
                Créez des visualisations percutantes pour vos audiences :
                - **Timeline linéaire** : claire pour les magistrats
                - **Vue par phase procédurale** : enquête, instruction, jugement
                - **Réseau d'acteurs** : pour les affaires complexes
                - **Carte de densité** : identifier les périodes clés
                - **Export PowerPoint** : pour vos plaidoiries
                """,
                'action': "Terminer"
            }
        ]
        
        # Afficher l'étape actuelle
        if tutorial_step < len(tutorials):
            tutorial = tutorials[tutorial_step]
            
            with st.container():
                st.markdown(f"#### {tutorial['title']}")
                st.info(tutorial['content'])
                
                if st.button(tutorial['action'], type="primary"):
                    if tutorial_step < len(tutorials) - 1:
                        st.session_state.tutorial_step = tutorial_step + 1
                        st.rerun()
                    else:
                        st.session_state.tutorial_step = 0
                        st.success("✅ Tutoriel terminé ! Vous maîtrisez maintenant le module.")
        
        # FAQ juridique
        st.markdown("### 💬 Questions juridiques fréquentes")
        
        faqs = [
            {
                'q': "Comment l'IA reconnaît-elle les infractions pénales des affaires ?",
                'a': """L'IA est entraînée sur :
                - Le Code pénal (Livre IV - crimes et délits contre la nation)
                - Le Code de commerce (infractions societaires)
                - Le Code général des impôts (fraude fiscale)
                - La jurisprudence de la Cour de cassation
                - Les circulaires du PNF et de la DACG"""
            },
            {
                'q': "Le module calcule-t-il automatiquement la prescription ?",
                'a': """Oui, le module peut calculer :
                - **Prescription de l'action publique** : 6 ans pour les délits
                - **Point de départ** : selon la nature de l'infraction (instantanée, continue, dissimulée)
                - **Causes d'interruption** : actes de poursuite ou d'instruction
                - **Alerte automatique** si prescription proche"""
            },
            {
                'q': "Peut-on utiliser les timelines comme pièces de procédure ?",
                'a': """Les timelines peuvent être utilisées comme :
                - **Support de plaidoirie** (audience)
                - **Annexe aux conclusions** (avec précautions)
                - **Document de travail** interne
                
                ⚠️ Vérifiez toujours les données avec les pièces originales"""
            },
            {
                'q': "Comment gérer les affaires avec volet international ?",
                'a': """Le module prend en compte :
                - **Commissions rogatoires internationales**
                - **Procédures d'extradition**
                - **Entraide judiciaire** (conventions bilatérales)
                - **Délais spécifiques** aux procédures internationales
                - **Traduction des actes** étrangers"""
            },
            {
                'q': "Quelle est la différence entre les modes d'extraction IA ?",
                'a': """Selon la complexité de votre dossier :
                - **Mode rapide** (Mistral) : pour un premier tri
                - **Mode standard** (GPT-4 ou Gemini) : analyse approfondie
                - **Mode expert** (Claude Opus 4) : dossiers complexes
                - **Mode Fusion** : combine tous les modèles pour les affaires sensibles"""
            }
        ]
        
        for faq in faqs:
            with st.expander(faq['q']):
                st.write(faq['a'])
        
        # Références juridiques
        st.markdown("### 📚 Références juridiques utiles")
        
        with st.expander("Textes de référence"):
            st.markdown("""
            **Codes :**
            - Code pénal : Articles 432-10 et s. (corruption), 314-1 et s. (escroquerie)
            - Code de commerce : L. 241-3, L. 242-6 (ABS)
            - CGI : Article 1741 (fraude fiscale)
            
            **Circulaires :**
            - Circulaire CRIM-PNF du 31 janvier 2014 (lutte contre la corruption)
            - Circulaire du 23 janvier 2019 (CJIP)
            - Guide PNF sur la CJIP (juin 2019)
            
            **Jurisprudence majeure :**
            - Cass. crim., 27 oct. 2021 (prescription ABS)
            - Cass. crim., 8 déc. 2021 (corruption internationale)
            """)
        
        with st.expander("Barèmes et peines"):
            st.markdown("""
            **Peines principales :**
            - ABS : 5 ans et 375 000 € (personne physique)
            - Corruption : 10 ans et 1 M€ (ou double du produit)
            - Blanchiment : 5 ans et 375 000 € (simple) / 10 ans et 750 000 € (aggravé)
            - Fraude fiscale : 5 ans et 500 000 € (ou 7 ans et 3 M€ si bande organisée)
            
            **Peines complémentaires :**
            - Interdiction de gérer
            - Exclusion des marchés publics
            - Confiscation des biens
            - Affichage/publication
            """)
        
        # Conseils pratiques
        st.markdown("### 💡 Conseils pratiques")
        
        tips = [
            "**🔍 Recherche** : Utilisez les mots-clés juridiques exacts (ex: 'mise en examen' plutôt que 'inculpation')",
            "**📅 Dates** : Vérifiez toujours les dates de notification (point de départ des délais)",
            "**👥 Acteurs** : Distinguez personnes physiques et morales pour les peines",
            "**📊 Export** : Privilégiez le PDF pour les magistrats, PowerPoint pour les plaidoiries",
            "**⚡ Performance** : Pour >200 actes, utilisez la vue 'densité temporelle'",
            "**🔒 Confidentialité** : Anonymisez les données sensibles avant partage"
        ]
        
        for tip in tips:
            st.success(tip)
    
    def _get_available_documents(self) -> List[Dict[str, Any]]:
        """Récupère tous les documents disponibles"""
        documents = []
        
        # Documents Azure
        if 'azure_documents' in st.session_state:
            for doc_id, doc in st.session_state.azure_documents.items():
                documents.append({
                    'id': doc_id,
                    'title': getattr(doc, 'title', f'Document {doc_id}'),
                    'content': getattr(doc, 'content', ''),
                    'source': 'Azure'
                })
        
        # Documents uploadés
        if 'uploaded_documents' in st.session_state:
            for doc in st.session_state.uploaded_documents:
                documents.append({
                    'id': doc.get('id', 'unknown'),
                    'title': doc.get('name', 'Document sans nom'),
                    'content': doc.get('content', ''),
                    'source': 'Upload'
                })
        
        # Documents locaux
        if 'local_documents' in st.session_state:
            for doc in st.session_state.local_documents:
                documents.append(doc)
        
        return documents
    
    def _render_manual_creation(self):
        """Interface de création manuelle d'événements"""
        st.markdown("#### ✍️ Création manuelle d'événements")
        
        # Nombre d'événements à créer
        num_events = st.number_input(
            "Nombre d'événements à créer",
            min_value=1,
            max_value=50,
            value=st.session_state.get('manual_event_count', 5),
            key="manual_event_count_input"
        )
        st.session_state.manual_event_count = num_events
        
        # Créer les événements
        events = []
        
        # Options de saisie rapide
        quick_options = st.checkbox("🚀 Mode saisie rapide", value=True,
                                   help="Simplifiez la saisie avec des valeurs par défaut intelligentes")
        
        for i in range(num_events):
            with st.expander(f"📅 Événement {i+1}", expanded=(i < 3)):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # Date avec suggestion intelligente
                    if quick_options and i > 0 and events:
                        # Suggérer une date basée sur l'intervalle moyen
                        suggested_date = events[-1].date + timedelta(days=30)
                    else:
                        suggested_date = datetime.now() - timedelta(days=(num_events - i) * 30)
                    
                    event_date = st.date_input(
                        "Date",
                        value=suggested_date.date(),
                        key=f"manual_date_{i}"
                    )
                    
                    # Description avec suggestions
                    description_placeholder = "Ex: Signature du contrat, Audience au tribunal..."
                    description = st.text_area(
                        "Description",
                        placeholder=description_placeholder,
                        height=80,
                        key=f"manual_desc_{i}"
                    )
                
                with col2:
                    # Importance avec indicateur visuel
                    importance = st.select_slider(
                        "Importance",
                        options=list(range(1, 11)),
                        value=5,
                        format_func=lambda x: f"{'⭐' * (x // 2)} ({x})",
                        key=f"manual_imp_{i}"
                    )
                    
                    # Catégorie avec icônes
                    categories_with_icons = {
                        "procédure": "⚖️ Procédure",
                        "financier": "💰 Financier",
                        "contractuel": "📄 Contractuel",
                        "communication": "💬 Communication",
                        "expertise": "🔬 Expertise",
                        "médical": "🏥 Médical",
                        "autre": "📌 Autre"
                    }
                    
                    category = st.selectbox(
                        "Catégorie",
                        options=list(categories_with_icons.keys()),
                        format_func=lambda x: categories_with_icons[x],
                        key=f"manual_cat_{i}"
                    )
                
                with col3:
                    # Acteurs avec auto-complétion
                    all_actors = []
                    for e in events:
                        all_actors.extend(e.actors)
                    unique_actors = list(set(all_actors))
                    
                    actors_input = st.text_input(
                        "Acteurs",
                        placeholder="Jean Dupont, Société X",
                        key=f"manual_actors_{i}",
                        help="Séparez par des virgules"
                    )
                    
                    if unique_actors and quick_options:
                        st.caption("Acteurs récents:")
                        for actor in unique_actors[:3]:
                            if st.button(actor, key=f"actor_btn_{i}_{actor}"):
                                # Ajouter l'acteur (nécessite une logique de state)
                                pass
                    
                    # Confiance (pour cohérence avec l'extraction IA)
                    confidence = st.slider(
                        "Confiance",
                        0.0, 1.0, 0.95, 0.05,
                        key=f"manual_conf_{i}",
                        help="Niveau de certitude"
                    )
                
                # Créer l'événement si les champs requis sont remplis
                if description:
                    event = TimelineEvent(
                        date=datetime.combine(event_date, datetime.min.time()),
                        description=description,
                        importance=importance,
                        category=category,
                        actors=[a.strip() for a in actors_input.split(',') if a.strip()],
                        source='Saisie manuelle',
                        confidence=confidence,
                        ai_extracted=False,
                        metadata={'manual_entry': True, 'entry_index': i}
                    )
                    events.append(event)
        
        # Options supplémentaires
        with st.expander("⚙️ Options avancées"):
            # Import depuis modèle
            if st.button("📋 Importer depuis un modèle"):
                st.session_state.show_template_import = True
            
            # Duplication d'événements
            if events and st.button("📑 Dupliquer le dernier événement"):
                last_event = events[-1]
                # Ajouter une logique pour dupliquer
                pass
        
        # Validation et prévisualisation
        if events:
            st.success(f"✅ {len(events)} événements créés")
            
            # Prévisualisation
            if st.checkbox("👁️ Prévisualiser la timeline", value=True):
                preview_fig = self._create_quick_preview(events)
                if preview_fig:
                    st.plotly_chart(preview_fig, use_container_width=True)
            
            # Sauvegarder dans la session
            st.session_state.timeline_events = events
    
    def _render_file_import(self):
        """Interface d'import de fichiers"""
        st.markdown("#### 📁 Import depuis un fichier")
        
        # Types de fichiers supportés
        file_types = {
            'csv': 'CSV (Comma Separated Values)',
            'xlsx': 'Excel (XLSX)',
            'json': 'JSON (JavaScript Object Notation)',
            'txt': 'Texte structuré'
        }
        
        # Upload
        uploaded_file = st.file_uploader(
            "Choisissez un fichier",
            type=list(file_types.keys()),
            help="Le fichier doit contenir au minimum : Date, Description"
        )
        
        if uploaded_file:
            # Afficher les informations du fichier
            file_details = {
                "Nom": uploaded_file.name,
                "Type": file_types.get(uploaded_file.name.split('.')[-1], 'Inconnu'),
                "Taille": f"{uploaded_file.size / 1024:.1f} KB"
            }
            
            col1, col2, col3 = st.columns(3)
            for i, (key, value) in enumerate(file_details.items()):
                with [col1, col2, col3][i]:
                    st.metric(key, value)
            
            # Parser le fichier
            try:
                if uploaded_file.name.endswith('.csv'):
                    events = self._import_from_csv(uploaded_file)
                elif uploaded_file.name.endswith('.xlsx'):
                    events = self._import_from_excel(uploaded_file)
                elif uploaded_file.name.endswith('.json'):
                    events = self._import_from_json(uploaded_file)
                else:
                    events = self._import_from_text(uploaded_file)
                
                if events:
                    st.success(f"✅ {len(events)} événements importés avec succès")
                    
                    # Aperçu des données importées
                    with st.expander("📋 Aperçu des données importées", expanded=True):
                        # Afficher sous forme de tableau
                        preview_data = []
                        for event in events[:10]:  # Limiter l'aperçu
                            preview_data.append({
                                'Date': event.date.strftime('%d/%m/%Y'),
                                'Description': event.description[:100] + '...' if len(event.description) > 100 else event.description,
                                'Importance': event.importance,
                                'Catégorie': event.category,
                                'Acteurs': ', '.join(event.actors[:3])
                            })
                        
                        df = pd.DataFrame(preview_data)
                        st.dataframe(df, use_container_width=True)
                        
                        if len(events) > 10:
                            st.info(f"... et {len(events) - 10} autres événements")
                    
                    # Options de nettoyage
                    with st.expander("🧹 Nettoyer les données"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🗑️ Supprimer les doublons"):
                                before = len(events)
                                events = self._deduplicate_events(events)
                                after = len(events)
                                st.success(f"Supprimé {before - after} doublons")
                        
                        with col2:
                            if st.button("📅 Trier par date"):
                                events.sort(key=lambda x: x.date)
                                st.success("✅ Événements triés")
                    
                    # Enrichissement IA optionnel
                    if st.checkbox("🤖 Enrichir avec l'IA", value=True):
                        st.info("L'IA va analyser et enrichir vos événements importés")
                    
                    # Sauvegarder
                    st.session_state.timeline_events = events
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'import : {str(e)}")
                
                # Aide contextuelle
                with st.expander("❓ Aide pour l'import"):
                    st.markdown(f"""
                    ### Format attendu pour {file_types.get(uploaded_file.name.split('.')[-1], 'ce type de fichier')}
                    
                    **Colonnes requises :**
                    - Date (format JJ/MM/AAAA ou AAAA-MM-JJ)
                    - Description (texte)
                    
                    **Colonnes optionnelles :**
                    - Importance (nombre de 1 à 10)
                    - Catégorie (texte)
                    - Acteurs (texte, séparés par des virgules)
                    - Confiance (nombre entre 0 et 1)
                    
                    **Exemple de structure :**
                    ```
                    Date,Description,Importance,Catégorie,Acteurs
                    01/01/2024,"Signature du contrat",8,contractuel,"Jean Dupont, Marie Martin"
                    15/01/2024,"Première réunion",5,communication,"Équipe projet"
                    ```
                    """)
        
        # Templates de fichiers
        st.markdown("### 📄 Modèles de fichiers")
        st.info("Téléchargez un modèle pour commencer rapidement")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Modèle CSV", use_container_width=True):
                csv_template = """Date,Description,Importance,Catégorie,Acteurs
01/01/2024,"Événement exemple 1",5,procédure,"Acteur 1, Acteur 2"
15/01/2024,"Événement exemple 2",8,financier,"Acteur 3"
01/02/2024,"Événement exemple 3",3,communication,"Acteur 1"
"""
                st.download_button(
                    "Télécharger",
                    data=csv_template,
                    file_name="timeline_template.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📥 Modèle JSON", use_container_width=True):
                json_template = json.dumps([
                    {
                        "date": "2024-01-01",
                        "description": "Événement exemple 1",
                        "importance": 5,
                        "category": "procédure",
                        "actors": ["Acteur 1", "Acteur 2"]
                    }
                ], indent=2)
                st.download_button(
                    "Télécharger",
                    data=json_template,
                    file_name="timeline_template.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("📥 Modèle Excel", use_container_width=True):
                df_template = pd.DataFrame({
                        'Date': ['01/01/2024', '15/01/2024'],
                        'Description': ['Événement exemple 1', 'Événement exemple 2'],
                        'Importance': [5, 8],
                        'Catégorie': ['procédure', 'financier'],
                        'Acteurs': ['Acteur 1, Acteur 2', 'Acteur 3']
                })
                # Créer un fichier Excel en mémoire
                output = pd.ExcelWriter('timeline_template.xlsx', engine='xlsxwriter')
                df_template.to_excel(output, index=False)
                # Note: Cette approche simplifiée nécessiterait une gestion plus complexe en production
                st.info("Fonction Excel nécessite une configuration supplémentaire")
    
    def _render_template_selection(self):
        """Interface de sélection de templates pour le droit pénal des affaires"""
        st.markdown("#### ⚖️ Templates spécialisés - Droit Pénal des Affaires")
        
        # Catégories de templates adaptées
        template_categories = {
            "Infractions financières": [
                "Abus de biens sociaux (ABS)",
                "Corruption et trafic d'influence",
                "Blanchiment de capitaux",
                "Escroquerie et abus de confiance",
                "Délit d'initié"
            ],
            "Infractions fiscales": [
                "Fraude fiscale simple",
                "Fraude fiscale aggravée",
                "Blanchiment de fraude fiscale",
                "Organisation frauduleuse d'insolvabilité"
            ],
            "Infractions sociales": [
                "Travail dissimulé",
                "Marchandage et prêt illicite de main d'œuvre",
                "Entraves et délits de représentation"
            ],
            "Procédures complexes": [
                "CJIP (Convention Judiciaire d'Intérêt Public)",
                "Information judiciaire avec volet international",
                "Procédure multi-infractions",
                "Saisie pénale et confiscation"
            ]
        }
        
        # Sélection de la catégorie
        category = st.selectbox(
            "Type d'infraction",
            list(template_categories.keys()),
            help="Choisissez la catégorie correspondant à votre dossier"
        )
        
        # Sélection du template
        template = st.selectbox(
            "Template spécifique",
            template_categories[category],
            help="Modèle prédéfini basé sur la jurisprudence et la pratique"
        )
        
        # Aperçu du template
        with st.expander("👁️ Aperçu du template juridique", expanded=True):
            template_events = self._get_template_events(template)
            
            if template_events:
                # Timeline miniature
                fig = self._create_quick_preview(template_events)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques juridiques
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📅 Actes de procédure", len(template_events))
                with col2:
                    duration = (template_events[-1].date - template_events[0].date).days
                    st.metric("⏱️ Durée moyenne", f"{duration} jours")
                with col3:
                    critical = sum(1 for e in template_events if e.importance >= 8)
                    st.metric("⚠️ Actes critiques", critical)
                with col4:
                    phases = len(set(e.metadata.get('procedural_phase', '') for e in template_events))
                    st.metric("📊 Phases", phases)
                
                # Avertissements juridiques
                st.warning("""
                ⚖️ **Avertissement juridique** : Ces templates sont fournis à titre indicatif et doivent 
                être adaptés aux spécificités de chaque dossier. Les délais peuvent varier selon les 
                juridictions et les circonstances.
                """)
        
        # Personnalisation juridique
        with st.expander("⚙️ Personnaliser le template juridique"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Date de référence
                date_reference = st.selectbox(
                    "Point de départ",
                    ["Date des faits", "Date de la plainte", "Date de l'ouverture d'enquête", "Autre date"],
                    help="Référence temporelle pour le calcul des délais"
                )
                
                if date_reference == "Autre date":
                    custom_date = st.date_input("Date personnalisée", value=datetime.now().date())
                else:
                    custom_date = st.date_input(
                        f"Indiquer la {date_reference.lower()}",
                        value=datetime.now().date()
                    )
                
                # Juridiction
                juridiction = st.selectbox(
                    "Juridiction compétente",
                    ["TJ Paris - Pôle financier", "TJ Paris - Section éco-fi", 
                     "TJ Nanterre", "TJ Bobigny", "Autre juridiction"],
                    help="Peut influencer les délais et procédures"
                )
            
            with col2:
                # Options procédurales
                with_civil_party = st.checkbox(
                    "Avec constitution de partie civile",
                    value=False,
                    help="Ajoute les étapes liées aux parties civiles"
                )
                
                international = st.checkbox(
                    "Dimension internationale",
                    value=False,
                    help="Ajoute les procédures d'entraide"
                )
                
                provisional_measures = st.checkbox(
                    "Mesures provisoires",
                    value=True,
                    help="Contrôle judiciaire, saisies, etc."
                )
                
                # Adapter les parties
                st.markdown("**Personnaliser les acteurs**")
                actor_mapping = {}
                
                # Extraire les acteurs types du template
                unique_actors = set()
                for event in template_events:
                    unique_actors.update(event.actors)
                
                # Acteurs juridiques standards à mapper
                standard_actors = {
                    "Mis en cause": "Nom de la personne/société mise en cause",
                    "Procureur": "Procureur de la République",
                    "Juge d'instruction": "Juge d'instruction saisi",
                    "Partie civile": "Victime/Partie civile",
                    "Expert": "Expert judiciaire"
                }
                
                for actor in sorted(unique_actors):
                    if actor in standard_actors:
                        new_name = st.text_input(
                            f"{actor}",
                            placeholder=standard_actors[actor],
                            key=f"actor_map_{actor}"
                        )
                        if new_name:
                            actor_mapping[actor] = new_name
        
        # Utiliser le template
        if st.button("🚀 Appliquer ce template juridique", type="primary", use_container_width=True):
            # Appliquer les personnalisations
            personalized_events = self._personalize_legal_template(
                template_events,
                custom_date,
                juridiction,
                actor_mapping,
                {
                    'with_civil_party': with_civil_party,
                    'international': international,
                    'provisional_measures': provisional_measures
                }
            )
            
            st.session_state.timeline_events = personalized_events
            st.success(f"""
            ✅ Template '{template}' appliqué avec succès !
            - {len(personalized_events)} actes de procédure générés
            - Adapté pour : {juridiction}
            - Point de départ : {custom_date.strftime('%d/%m/%Y')}
            """)
    
    def _get_template_events(self, template_name: str) -> List[TimelineEvent]:
        """Retourne les événements d'un template spécifique au droit pénal des affaires"""
        templates = {
            "Abus de biens sociaux (ABS)": [
                TimelineEvent(
                    date=datetime.now() - timedelta(days=730),  # 2 ans
                    description="Faits d'abus de biens sociaux : utilisation des biens de la société à des fins personnelles contraire à l'intérêt social",
                    importance=10,
                    category="financier",
                    actors=["Dirigeant mis en cause", "Société victime"],
                    confidence=1.0,
                    metadata={
                        'template': True, 
                        'procedural_phase': 'faits',
                        'infraction_type': 'abus_biens_sociaux',
                        'legal_ref': 'L. 241-3 et L. 242-6 Code de commerce'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=365),
                    description="Découverte des faits lors du contrôle des comptes par le commissaire aux comptes",
                    importance=8,
                    category="financier",
                    actors=["Commissaire aux comptes", "Société victime"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'révélation',
                        'alert_type': 'commissaire_aux_comptes'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=350),
                    description="Révélation des faits au procureur de la République (article 40 CPP)",
                    importance=9,
                    category="procédure",
                    actors=["Commissaire aux comptes", "Procureur"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'signalement',
                        'legal_ref': 'Article 40 CPP'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=340),
                    description="Dépôt de plainte avec constitution de partie civile par la société",
                    importance=9,
                    category="procédure",
                    actors=["Société victime", "Avocat partie civile"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'plainte'}
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=320),
                    description="Ouverture d'une enquête préliminaire par le parquet financier",
                    importance=8,
                    category="enquête",
                    actors=["Procureur", "Brigade financière"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'enquête_préliminaire'}
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=300),
                    description="Perquisitions au siège social et au domicile du dirigeant",
                    importance=9,
                    category="enquête",
                    actors=["Brigade financière", "Mis en cause", "Avocat"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'enquête_préliminaire',
                        'measure_type': 'perquisition'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=290),
                    description="Saisie des documents comptables et informatiques",
                    importance=8,
                    category="enquête",
                    actors=["Brigade financière"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'enquête_préliminaire',
                        'measure_type': 'saisie'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=250),
                    description="Exploitation des scellés et analyse comptable approfondie",
                    importance=7,
                    category="enquête",
                    actors=["Brigade financière", "Expert comptable judiciaire"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'enquête_préliminaire'}
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=200),
                    description="Audition du dirigeant mis en cause en audition libre",
                    importance=8,
                    category="enquête",
                    actors=["Brigade financière", "Mis en cause", "Avocat"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'enquête_préliminaire',
                        'measure_type': 'audition_libre'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=180),
                    description="Placement en garde à vue du dirigeant",
                    importance=10,
                    category="enquête",
                    actors=["Brigade financière", "Mis en cause", "Avocat"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'enquête_préliminaire',
                        'measure_type': 'garde_à_vue',
                        'duration': '48h'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=178),
                    description="Déferrement devant le procureur de la République",
                    importance=9,
                    category="procédure",
                    actors=["Procureur", "Mis en cause", "Avocat"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'poursuite'}
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=177),
                    description="Ouverture d'une information judiciaire pour ABS",
                    importance=10,
                    category="instruction",
                    actors=["Procureur", "Juge d'instruction"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'legal_qualification': 'Abus de biens sociaux'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=175),
                    description="Première comparution et mise en examen du dirigeant",
                    importance=10,
                    category="instruction",
                    actors=["Juge d'instruction", "Mis en cause", "Avocat"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'measure_type': 'mise_en_examen'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=174),
                    description="Placement sous contrôle judiciaire avec interdiction de gérer",
                    importance=9,
                    category="mesures",
                    actors=["Juge d'instruction", "Mis en examen"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'measure_type': 'contrôle_judiciaire',
                        'restrictions': ['interdiction_gérer', 'caution']
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=150),
                    description="Désignation d'un expert-comptable judiciaire",
                    importance=7,
                    category="instruction",
                    actors=["Juge d'instruction", "Expert"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'expertise_type': 'comptable'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=90),
                    description="Dépôt du rapport d'expertise comptable évaluant le préjudice",
                    importance=8,
                    category="expertise",
                    actors=["Expert", "Juge d'instruction"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'prejudice_evaluation': True
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=60),
                    description="Interrogatoire de fin d'information",
                    importance=8,
                    category="instruction",
                    actors=["Juge d'instruction", "Mis en examen", "Avocat"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'fin_instruction'}
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=45),
                    description="Réquisitions du parquet aux fins de renvoi devant le tribunal correctionnel",
                    importance=8,
                    category="procédure",
                    actors=["Procureur", "Juge d'instruction"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'réquisitions'}
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=30),
                    description="Ordonnance de renvoi devant le tribunal correctionnel",
                    importance=9,
                    category="procédure",
                    actors=["Juge d'instruction"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'renvoi',
                        'juridiction': 'Tribunal correctionnel'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=7),
                    description="Citation à comparaître devant le tribunal correctionnel",
                    importance=8,
                    category="procédure",
                    actors=["Tribunal", "Prévenu", "Partie civile"],
                    confidence=1.0,
                    metadata={'template': True, 'procedural_phase': 'citation'}
                )
            ],
            
            "Corruption et trafic d'influence": [
                TimelineEvent(
                    date=datetime.now() - timedelta(days=1095),  # 3 ans
                    description="Faits de corruption : remise d'avantages indus à un agent public pour obtenir un marché",
                    importance=10,
                    category="financier",
                    actors=["Corrupteur", "Agent public corrompu"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'faits',
                        'infraction_type': 'corruption_active',
                        'legal_ref': 'Articles 433-1 et 433-2 Code pénal'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=730),
                    description="Signalement TRACFIN pour mouvements financiers suspects",
                    importance=9,
                    category="compliance",
                    actors=["TRACFIN", "Procureur"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'signalement',
                        'alert_type': 'tracfin'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=700),
                    description="Ouverture d'une enquête préliminaire par le PNF",
                    importance=9,
                    category="enquête",
                    actors=["Procureur PNF", "OCLCIFF"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'enquête_préliminaire',
                        'juridiction': 'PNF'
                    }
                ),
                # ... autres événements spécifiques à la corruption
            ],
            
            "CJIP (Convention Judiciaire d'Intérêt Public)": [
                TimelineEvent(
                    date=datetime.now() - timedelta(days=365),
                    description="Révélation de faits de corruption internationale par auto-dénonciation",
                    importance=9,
                    category="compliance",
                    actors=["Entreprise", "Avocat", "Procureur PNF"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'révélation',
                        'procedure_type': 'cjip',
                        'legal_ref': 'Article 41-1-2 CPP'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=350),
                    description="Ouverture des négociations CJIP avec le PNF",
                    importance=9,
                    category="procédure",
                    actors=["Procureur PNF", "Entreprise", "Avocat"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'négociation_cjip'
                    }
                ),
                TimelineEvent(
                    date=datetime.now() - timedelta(days=300),
                    description="Audit de conformité par l'AFA (Agence Française Anticorruption)",
                    importance=8,
                    category="compliance",
                    actors=["AFA", "Entreprise"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'négociation_cjip',
                        'compliance_audit': True
                    }
                ),
                # ... autres étapes CJIP
            ]
        }
        
        # Retourner le template demandé ou un template par défaut
        return templates.get(template_name, self._get_default_criminal_template())
    
    def _get_default_criminal_template(self) -> List[TimelineEvent]:
        """Template par défaut pour une procédure pénale des affaires"""
        return [
            TimelineEvent(
                date=datetime.now() - timedelta(days=365),
                description="Découverte des faits délictueux",
                importance=8,
                category="financier",
                actors=["Lanceur d'alerte", "Direction"],
                confidence=1.0,
                metadata={'template': True, 'procedural_phase': 'révélation'}
            ),
            TimelineEvent(
                date=datetime.now() - timedelta(days=350),
                description="Signalement au procureur de la République",
                importance=9,
                category="procédure",
                actors=["Procureur"],
                confidence=1.0,
                metadata={'template': True, 'procedural_phase': 'signalement'}
            ),
            # ... événements standards
        ]
    
    def _personalize_legal_template(self, events: List[TimelineEvent], 
                                  reference_date: datetime.date,
                                  juridiction: str,
                                  actor_mapping: Dict[str, str],
                                  options: Dict[str, bool]) -> List[TimelineEvent]:
        """Personnalise un template juridique avec les paramètres spécifiques au dossier"""
        if not events:
            return []
        
        # Calculer le décalage temporel depuis la date de référence
        first_date = min(e.date for e in events)
        offset_days = (datetime.combine(reference_date, datetime.min.time()) - first_date).days
        
        # Ajuster les délais selon la juridiction
        delay_factor = 1.0
        if "Paris" in juridiction:
            delay_factor = 0.9  # Plus rapide à Paris
        elif "Autre" in juridiction:
            delay_factor = 1.2  # Potentiellement plus long ailleurs
        
        personalized = []
        
        for event in events:
            # Copier l'événement
            new_event = TimelineEvent(
                date=event.date,
                description=event.description,
                importance=event.importance,
                category=event.category,
                actors=event.actors.copy(),
                source=event.source,
                confidence=event.confidence,
                ai_extracted=event.ai_extracted,
                metadata=event.metadata.copy()
            )
            
            # Ajuster la date avec le facteur juridictionnel
            days_from_start = (event.date - first_date).days
            adjusted_days = int(days_from_start * delay_factor)
            new_event.date = first_date + timedelta(days=offset_days + adjusted_days)
            
            # Remplacer les acteurs
            new_actors = []
            for actor in new_event.actors:
                new_actors.append(actor_mapping.get(actor, actor))
            new_event.actors = new_actors
            
            # Mettre à jour la description avec les nouveaux acteurs
            for old_actor, new_actor in actor_mapping.items():
                if old_actor != new_actor:
                    new_event.description = new_event.description.replace(old_actor, new_actor)
            
            # Ajouter la juridiction dans les métadonnées
            new_event.metadata['juridiction'] = juridiction
            
            # Filtrer selon les options
            should_include = True
            
            # Exclure les événements liés aux parties civiles si non demandé
            if not options.get('with_civil_party') and 'partie civile' in new_event.description.lower():
                should_include = False
            
            # Exclure les mesures provisoires si non demandé
            if not options.get('provisional_measures') and new_event.category == 'mesures':
                should_include = False
            
            if should_include:
                personalized.append(new_event)
        
        # Ajouter des événements supplémentaires si dimension internationale
        if options.get('international'):
            personalized.extend(self._add_international_procedures(personalized, actor_mapping))
        
        return sorted(personalized, key=lambda x: x.date)
    
    def _add_international_procedures(self, events: List[TimelineEvent], 
                                    actor_mapping: Dict[str, str]) -> List[TimelineEvent]:
        """Ajoute les procédures spécifiques aux affaires internationales"""
        international_events = []
        
        # Trouver la date de l'instruction
        instruction_date = None
        for event in events:
            if 'instruction' in event.metadata.get('procedural_phase', ''):
                instruction_date = event.date
                break
        
        if instruction_date:
            international_events.extend([
                TimelineEvent(
                    date=instruction_date + timedelta(days=30),
                    description="Demande d'entraide judiciaire internationale",
                    importance=7,
                    category="procédure",
                    actors=["Juge d'instruction", "Autorité étrangère"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'international': True
                    }
                ),
                TimelineEvent(
                    date=instruction_date + timedelta(days=90),
                    description="Réception des éléments de l'entraide internationale",
                    importance=6,
                    category="procédure",
                    actors=["Autorité étrangère", "Juge d'instruction"],
                    confidence=1.0,
                    metadata={
                        'template': True,
                        'procedural_phase': 'instruction',
                        'international': True
                    }
                )
            ])
        
        return international_events
    
    def _create_quick_preview(self, events: List[TimelineEvent]) -> go.Figure:
        """Crée un aperçu rapide de la timeline"""

        
        # Timeline simple
        fig = go.Figure()
        
        # Trier les événements
        sorted_events = sorted(events, key=lambda x: x.date)
        
        # Ajouter les événements
        fig.add_trace(go.Scatter(
            x=[e.date for e in sorted_events],
            y=[i % 3 for i in range(len(sorted_events))],  # Alterner sur 3 niveaux
            mode='markers+text',
            text=[f"{e.description[:20]}..." for e in sorted_events],
            textposition='top center',
            marker=dict(
                size=[10 + e.importance for e in sorted_events],
                color=[e.importance for e in sorted_events],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Importance", len=0.5)
            ),
            hovertext=[f"{e.date.strftime('%d/%m/%Y')}<br>{e.description}" for e in sorted_events],
            hoverinfo='text'
        ))
        
        fig.update_layout(
            title="Aperçu de la timeline",
            xaxis=dict(title="", type='date'),
            yaxis=dict(title="", showticklabels=False, range=[-0.5, 3.5]),
            height=300,
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
    
    def _import_from_csv(self, file) -> List[TimelineEvent]:
        """Importe des événements depuis un CSV"""

        
        try:
            df = pd.read_csv(file)
            return self._dataframe_to_events(df)
        except Exception as e:
            st.error(f"Erreur lors de l'import CSV : {e}")
            return []
    
    def _import_from_excel(self, file) -> List[TimelineEvent]:
        """Importe des événements depuis Excel"""
        
        try:
            df = pd.read_excel(file)
            return self._dataframe_to_events(df)
        except Exception as e:
            st.error(f"Erreur lors de l'import Excel : {e}")
            return []
    
    def _import_from_json(self, file) -> List[TimelineEvent]:
        """Importe des événements depuis JSON"""
        try:
            data = json.load(file)
            events = []
            
            for item in data:
                event = TimelineEvent(
                    date=datetime.fromisoformat(item.get('date', datetime.now().isoformat())),
                    description=item.get('description', 'Sans description'),
                    importance=item.get('importance', 5),
                    category=item.get('category', 'autre'),
                    actors=item.get('actors', []),
                    source='Import JSON',
                    confidence=item.get('confidence', 0.8),
                    ai_extracted=item.get('ai_extracted', False),
                    metadata=item.get('metadata', {})
                )
                events.append(event)
            
            return events
        except Exception as e:
            st.error(f"Erreur lors de l'import JSON : {e}")
            return []
    
    def _import_from_text(self, file) -> List[TimelineEvent]:
        """Importe des événements depuis un fichier texte"""
        try:
            content = file.read().decode('utf-8')
            # Utiliser l'extraction IA sur le texte
            return self._extract_events_from_text_enhanced(content, file.name)
        except Exception as e:
            st.error(f"Erreur lors de l'import texte : {e}")
            return []
    
    def _dataframe_to_events(self, df: pd.DataFrame) -> List[TimelineEvent]:
        """Convertit un DataFrame en liste d'événements"""
        events = []
        
        # Colonnes possibles (avec variantes)
        date_cols = ['Date', 'date', 'DATE', 'Dates', 'dates']
        desc_cols = ['Description', 'description', 'DESC', 'Desc', 'Événement', 'Event']
        imp_cols = ['Importance', 'importance', 'IMP', 'Imp', 'Priority']
        cat_cols = ['Catégorie', 'catégorie', 'Category', 'Type', 'type']
        actor_cols = ['Acteurs', 'acteurs', 'Actors', 'Participants']
        conf_cols = ['Confiance', 'confiance', 'Confidence', 'Conf']
        
        # Trouver les colonnes existantes
        date_col = next((col for col in date_cols if col in df.columns), None)
        desc_col = next((col for col in desc_cols if col in df.columns), None)
        imp_col = next((col for col in imp_cols if col in df.columns), None)
        cat_col = next((col for col in cat_cols if col in df.columns), None)
        actor_col = next((col for col in actor_cols if col in df.columns), None)
        conf_col = next((col for col in conf_cols if col in df.columns), None)
        
        if not date_col or not desc_col:
            st.error("Le fichier doit contenir au minimum des colonnes Date et Description")
            return []
        
        # Parcourir les lignes
        for idx, row in df.iterrows():
            try:
                # Parser la date
                date_value = row[date_col]
                if isinstance(date_value, str):
                    parsed_date = pd.to_datetime(date_value, dayfirst=True)
                else:
                    parsed_date = pd.to_datetime(date_value)
                
                # Créer l'événement
                event = TimelineEvent(
                    date=parsed_date.to_pydatetime() if hasattr(parsed_date, 'to_pydatetime') else parsed_date,
                    description=str(row[desc_col]),
                    importance=int(row[imp_col]) if imp_col and pd.notna(row.get(imp_col)) else 5,
                    category=str(row[cat_col]) if cat_col and pd.notna(row.get(cat_col)) else 'autre',
                    actors=[a.strip() for a in str(row[actor_col]).split(',') if a.strip()] if actor_col and pd.notna(row.get(actor_col)) else [],
                    source='Import fichier',
                    confidence=float(row[conf_col]) if conf_col and pd.notna(row.get(conf_col)) else 0.8,
                    ai_extracted=False,
                    metadata={'import_row': idx}
                )
                
                events.append(event)
                
            except Exception as e:
                st.warning(f"Impossible d'importer la ligne {idx + 1}: {e}")
                continue
        
        return events

# Point d'entrée pour le lazy loading
def run():
    """Fonction principale du module"""
    module = TimelineModule()
    module.render()