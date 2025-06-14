"""Module de génération de rapports juridiques avec IA multi-modèles"""

import json
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from config.ai_models import AI_MODELS

# Configuration du logger
logger = logging.getLogger(__name__)

# Configuration de la page pour une meilleure expérience
def configure_page():
    """Configure les paramètres de la page pour une meilleure UX"""
    st.set_page_config(
        page_title="Génération de Rapports - Nexora Law IA",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # CSS personnalisé pour améliorer le design
    st.markdown("""
    <style>
    /* Animation d'entrée */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main > div {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Cards améliorées */
    .report-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .report-card:hover {
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* Boutons améliorés */
    .stButton > button {
        transition: all 0.3s ease;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Progress bars custom */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tabs personnalisés */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        background-color: rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255,255,255,0.2);
    }
    
    /* Métriques améliorées */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Animations de chargement */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    </style>
    """, unsafe_allow_html=True)

# Templates de rapports enrichis
REPORT_TEMPLATES = {
    'synthese': {
        'name': 'Synthèse d\'analyse',
        'icon': '📊',
        'sections': ['Résumé exécutif', 'Faits', 'Analyse', 'Conclusions', 'Recommandations'],
        'tone': 'professionnel',
        'description': 'Vue d\'ensemble complète d\'une affaire avec recommandations',
        'duration': '10-15 min',
        'ai_models': ['GPT-4', 'Claude', 'Gemini']
    },
    'plaidoirie': {
        'name': 'Note de plaidoirie',
        'icon': '⚖️',
        'sections': ['En fait', 'En droit', 'Discussion', 'Par ces motifs'],
        'tone': 'formel',
        'description': 'Document structuré pour plaider devant une juridiction',
        'duration': '20-30 min',
        'ai_models': ['Claude', 'GPT-4', 'Mistral']
    },
    'memo': {
        'name': 'Mémo juridique',
        'icon': '📝',
        'sections': ['Objet', 'Contexte', 'Analyse', 'Risques', 'Actions'],
        'tone': 'concis',
        'description': 'Communication interne rapide et efficace',
        'duration': '5-10 min',
        'ai_models': ['GPT-3.5', 'Claude', 'Llama']
    },
    'conclusions': {
        'name': 'Conclusions',
        'icon': '📜',
        'sections': ['Rappel procédure', 'Faits', 'Moyens', 'Demandes'],
        'tone': 'très formel',
        'description': 'Document procédural respectant les formes juridiques',
        'duration': '30-45 min',
        'ai_models': ['GPT-4', 'Claude', 'Gemini']
    },
    'expertise': {
        'name': 'Rapport d\'expertise',
        'icon': '🔬',
        'sections': ['Mission', 'Méthodologie', 'Constatations', 'Analyse', 'Conclusions'],
        'tone': 'technique',
        'description': 'Analyse technique détaillée avec méthodologie',
        'duration': '45-60 min',
        'ai_models': ['GPT-4', 'Claude', 'Gemini', 'Mistral']
    }
}

# Modèles d'IA disponibles
# Modèles IA importés depuis config.ai_models

def run():
    """Fonction principale du module - Point d'entrée pour le lazy loading"""
    configure_page()
    
    # Header avec animation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                📄 Génération de Rapports Juridiques
            </h1>
            <p style="font-size: 1.2rem; color: #666; margin-top: 1rem;">
                Créez automatiquement des rapports professionnels avec l'IA
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialisation de l'état
    initialize_session_state()
    
    # Barre de progression globale
    if 'generation_progress' in st.session_state and st.session_state.generation_progress > 0:
        progress_bar = st.progress(st.session_state.generation_progress)
        progress_text = st.empty()
        progress_text.text(f"Génération en cours... {st.session_state.generation_progress}%")
    
    # Navigation principale
    tabs = st.tabs([
        "🚀 Nouveau rapport",
        "🤖 Modèles IA",
        "📚 Bibliothèque",
        "🔄 Fusion",
        "📊 Historique",
        "⚙️ Paramètres"
    ])
    
    with tabs[0]:
        render_new_report()
    
    with tabs[1]:
        render_ai_models()
    
    with tabs[2]:
        render_templates_library()
    
    with tabs[3]:
        render_merge_reports()
    
    with tabs[4]:
        render_history()
    
    with tabs[5]:
        render_settings()

def initialize_session_state():
    """Initialise les variables de session"""
    defaults = {
        'report_history': [],
        'custom_templates': {},
        'ai_preferences': {},
        'generation_progress': 0,
        'current_report': None,
        'selected_models': ['GPT-4'],
        'fusion_mode': False,
        'auto_save': True,
        'theme': 'light'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_new_report():
    """Interface de création de nouveau rapport"""
    # Sélection rapide du type
    st.markdown("### 📋 Choisissez votre type de document")
    
    # Cards pour les types de rapports
    cols = st.columns(3)
    selected_type = None
    
    for i, (key, template) in enumerate(REPORT_TEMPLATES.items()):
        with cols[i % 3]:
            if render_template_card(key, template):
                selected_type = key
    
    if selected_type:
        st.session_state.selected_template = selected_type
    
    # Configuration détaillée
    if 'selected_template' in st.session_state:
        st.markdown("---")
        render_report_configuration(st.session_state.selected_template)

def render_template_card(template_id: str, template: Dict[str, Any]) -> bool:
    """Affiche une carte de template"""
    clicked = False
    
    card_html = f"""
    <div class="report-card">
        <h3>{template['icon']} {template['name']}</h3>
        <p style="color: #666; font-size: 0.9rem;">{template['description']}</p>
        <div style="margin-top: 1rem;">
            <span style="background: #e0e7ff; color: #4c51bf; padding: 0.25rem 0.5rem; 
                         border-radius: 4px; font-size: 0.8rem;">
                ⏱️ {template['duration']}
            </span>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    if st.button(f"Sélectionner", key=f"select_{template_id}", use_container_width=True):
        clicked = True
    
    return clicked

def render_report_configuration(template_id: str):
    """Configure les détails du rapport"""
    template = REPORT_TEMPLATES[template_id]
    
    st.markdown(f"### ⚙️ Configuration : {template['icon']} {template['name']}")
    
    # Configuration en colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Informations générales
        with st.expander("📋 Informations générales", expanded=True):
            title = st.text_input(
                "Titre du document",
                placeholder=f"Ex: {template['name']} - Affaire X c/ Y",
                help="Le titre apparaîtra en en-tête du document"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                client = st.text_input("Client/Demandeur", placeholder="Nom du client")
                case_ref = st.text_input("Référence", placeholder="RG n° XX/XXXXX")
            
            with col_b:
                jurisdiction = st.text_input("Juridiction", placeholder="Ex: TGI Paris")
                author = st.text_input("Auteur", value="Me. [Votre nom]")
        
        # Sources de contenu
        with st.expander("📚 Sources de contenu", expanded=True):
            content_source = st.radio(
                "Utiliser",
                ["🗂️ Données de session", "✍️ Saisie manuelle", "📤 Import fichier", "🤖 Génération IA"],
                horizontal=True
            )
            
            content_data = get_content_data(content_source, template_id)
        
        # Sections du rapport
        with st.expander("📑 Sections à inclure", expanded=True):
            selected_sections = []
            cols = st.columns(2)
            
            for i, section in enumerate(template['sections']):
                with cols[i % 2]:
                    if st.checkbox(section, value=True, key=f"section_{template_id}_{section}"):
                        selected_sections.append(section)
                        
                        # Options par section
                        if content_source == "🤖 Génération IA":
                            length = st.select_slider(
                                f"Détail pour '{section}'",
                                ["Concis", "Standard", "Détaillé"],
                                value="Standard",
                                key=f"length_{template_id}_{section}"
                            )
    
    with col2:
        # Paramètres de génération
        st.markdown("### 🎯 Paramètres")
        
        # Modèles IA
        st.markdown("#### 🤖 Modèles IA")
        if st.checkbox("Mode fusion multi-IA", value=False, help="Combine plusieurs modèles pour un meilleur résultat"):
            st.session_state.fusion_mode = True
            selected_models = st.multiselect(
                "Sélectionner les modèles",
                list(AI_MODELS.keys()),
                default=['GPT-4', 'Claude'],
                help="Les modèles seront utilisés en parallèle puis fusionnés"
            )
            
            fusion_strategy = st.radio(
                "Stratégie de fusion",
                ["🏆 Meilleur résultat", "🤝 Consensus", "🎨 Créativité maximale"],
                help="Comment combiner les résultats des différents modèles"
            )
        else:
            st.session_state.fusion_mode = False
            selected_models = [st.selectbox(
                "Modèle principal",
                list(AI_MODELS.keys()),
                index=0
            )]
        
        st.session_state.selected_models = selected_models
        
        # Afficher les caractéristiques des modèles sélectionnés
        for model in selected_models:
            with st.expander(f"{AI_MODELS[model]['icon']} {model}", expanded=False):
                st.write(f"**Fournisseur:** {AI_MODELS[model]['provider']}")
                st.write(f"**Vitesse:** {AI_MODELS[model]['speed']}")
                st.write(f"**Qualité:** {'⭐' * AI_MODELS[model]['quality']}")
                st.write("**Points forts:**")
                for strength in AI_MODELS[model]['strengths']:
                    st.write(f"• {strength}")
        
        # Style et formatage
        st.markdown("#### 🎨 Style")
        tone = st.select_slider(
            "Ton",
            ["Très formel", "Formel", "Professionnel", "Neutre", "Accessible"],
            value="Professionnel"
        )
        
        length_multiplier = st.slider(
            "Longueur globale",
            0.5, 2.0, 1.0, 0.1,
            help="Ajuste la longueur de toutes les sections"
        )
        
        # Options avancées
        with st.expander("⚙️ Options avancées"):
            include_toc = st.checkbox("Table des matières", value=True)
            include_citations = st.checkbox("Citations automatiques", value=True)
            include_watermark = st.checkbox("Filigrane", value=False)
            auto_translate = st.checkbox("Traduction multilingue", value=False)
            
            if auto_translate:
                languages = st.multiselect(
                    "Langues",
                    ["Anglais", "Espagnol", "Allemand", "Italien"],
                    default=["Anglais"]
                )
    
    # Bouton de génération principal
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button(
            f"🚀 Générer le rapport avec {len(selected_models)} modèle(s)",
            type="primary",
            use_container_width=True,
            disabled=not title
        ):
            if title and selected_sections:
                config = {
                    'type': template_id,
                    'title': title,
                    'client': client,
                    'case_ref': case_ref,
                    'jurisdiction': jurisdiction,
                    'author': author,
                    'date': datetime.now(),
                    'tone': tone,
                    'length_multiplier': length_multiplier,
                    'sections': selected_sections,
                    'content_data': content_data,
                    'ai_models': selected_models,
                    'fusion_mode': st.session_state.fusion_mode,
                    'fusion_strategy': fusion_strategy if st.session_state.fusion_mode else None,
                    'options': {
                        'toc': include_toc,
                        'citations': include_citations,
                        'watermark': include_watermark,
                        'translations': languages if auto_translate else []
                    }
                }
                
                generate_report_with_ai(config)
            else:
                st.error("⚠️ Veuillez remplir au minimum le titre et sélectionner des sections")

def get_content_data(source: str, report_type: str) -> Dict[str, Any]:
    """Récupère les données selon la source"""
    content_data = {}
    
    if source == "🗂️ Données de session":
        available_data = check_session_data()
        if available_data:
            st.success(f"✅ {len(available_data)} sources de données disponibles")
            
            # Sélection des données à utiliser
            for data_type, info in available_data.items():
                if st.checkbox(f"Utiliser {info['name']} ({info['count']} éléments)", value=True):
                    content_data[data_type] = info['data']
        else:
            st.info("💡 Aucune donnée de session disponible. Effectuez d'abord des analyses.")
    
    elif source == "✍️ Saisie manuelle":
        template = REPORT_TEMPLATES[report_type]
        for section in template['sections']:
            with st.expander(f"📝 {section}", expanded=False):
                content = st.text_area(
                    f"Contenu",
                    height=150,
                    key=f"manual_{report_type}_{section}",
                    placeholder=f"Saisissez le contenu pour la section '{section}'..."
                )
                if content:
                    content_data[section] = content
    
    elif source == "📤 Import fichier":
        uploaded_files = st.file_uploader(
            "Choisir des fichiers",
            type=['txt', 'docx', 'pdf', 'json'],
            accept_multiple_files=True,
            help="Les contenus seront extraits et analysés"
        )
        
        if uploaded_files:
            content_data['files'] = []
            for file in uploaded_files:
                with st.spinner(f"Traitement de {file.name}..."):
                    # Simulation du traitement
                    time.sleep(0.5)
                    content_data['files'].append({
                        'name': file.name,
                        'size': file.size,
                        'type': file.type,
                        'content': f"Contenu extrait de {file.name}..."
                    })
            st.success(f"✅ {len(uploaded_files)} fichiers importés")
    
    else:  # Génération IA
        st.info("🤖 L'IA générera automatiquement le contenu selon vos paramètres")
        
        col1, col2 = st.columns(2)
        with col1:
            creativity = st.slider(
                "Créativité",
                0.0, 1.0, 0.3,
                help="0 = Factuel strict, 1 = Très créatif"
            )
            
            focus_points = st.multiselect(
                "Points d'attention",
                ["Faits précis", "Argumentation solide", "Jurisprudence récente", 
                 "Stratégie gagnante", "Risques identifiés"],
                default=["Faits précis", "Argumentation solide"]
            )
        
        with col2:
            research_depth = st.select_slider(
                "Profondeur de recherche",
                ["Basique", "Standard", "Approfondie", "Exhaustive"],
                value="Standard"
            )
            
            include_examples = st.checkbox("Inclure des exemples", value=True)
            include_citations = st.checkbox("Ajouter des citations", value=True)
        
        content_data['ai_params'] = {
            'creativity': creativity,
            'focus_points': focus_points,
            'research_depth': research_depth,
            'include_examples': include_examples,
            'include_citations': include_citations
        }
    
    return content_data

def check_session_data() -> Dict[str, Any]:
    """Vérifie les données disponibles en session"""
    available = {}
    
    data_mappings = {
        'selected_documents': {'name': '📄 Documents', 'icon': '📄'},
        'comparison_history': {'name': '📊 Comparaisons', 'icon': '📊'},
        'timeline_history': {'name': '📅 Timelines', 'icon': '📅'},
        'extraction_history': {'name': '📑 Extractions', 'icon': '📑'},
        'strategy_history': {'name': '⚖️ Stratégies', 'icon': '⚖️'}
    }
    
    for key, info in data_mappings.items():
        if key in st.session_state and st.session_state[key]:
            available[key] = {
                'name': info['name'],
                'count': len(st.session_state[key]),
                'data': st.session_state[key]
            }
    
    return available

def generate_report_with_ai(config: Dict[str, Any]):
    """Génère le rapport avec les modèles IA sélectionnés"""
    # Réinitialiser la progression
    st.session_state.generation_progress = 0
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Container pour les résultats
    results_container = st.container()
    
    with st.spinner("Initialisation de la génération..."):
        report = {
            'id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'created_at': datetime.now(),
            'config': config,
            'content': {},
            'ai_results': {},
            'metadata': {}
        }
        
        total_steps = len(config['sections']) * len(config['ai_models'])
        current_step = 0
        
        # Génération avec chaque modèle
        for model in config['ai_models']:
            model_results = {}
            status_placeholder.info(f"🤖 Génération avec {AI_MODELS[model]['name']}...")
            
            for section in config['sections']:
                current_step += 1
                progress = int((current_step / total_steps) * 100)
                st.session_state.generation_progress = progress
                progress_placeholder.progress(progress)
                
                # Simulation de génération
                time.sleep(0.5)  # Remplacer par l'appel API réel
                
                content = generate_section_content(section, config, model)
                model_results[section] = content
            
            report['ai_results'][model] = model_results
        
        # Fusion des résultats si mode fusion activé
        if config['fusion_mode']:
            status_placeholder.info("🔄 Fusion des résultats multi-IA...")
            report['content'] = merge_ai_results(report['ai_results'], config['fusion_strategy'])
        else:
            # Utiliser le résultat du modèle unique
            report['content'] = report['ai_results'][config['ai_models'][0]]
        
        # Calcul des métadonnées
        report['metadata'] = calculate_report_metadata(report)
        
        # Sauvegarder le rapport
        st.session_state.report_history.append(report)
        st.session_state.current_report = report
        
        # Afficher le succès
        status_placeholder.success("✅ Rapport généré avec succès!")
        progress_placeholder.progress(100)
        
        # Afficher le rapport
        with results_container:
            display_generated_report(report)

def generate_section_content(section: str, config: Dict[str, Any], model: str) -> str:
    """Génère le contenu d'une section avec un modèle spécifique"""
    # Simulation de génération - À remplacer par les appels API réels
    
    base_content = f"[Contenu généré par {model}]\n\n"
    
    # Templates par section
    templates = {
        "Résumé exécutif": f"""
Le présent document constitue une {config['type']} dans l'affaire {config.get('case_ref', '[Référence]')}.

Points clés :
• Analyse approfondie des éléments factuels
• Évaluation des risques juridiques
• Recommandations stratégiques adaptées

Cette synthèse a été élaborée avec {AI_MODELS[model]['name']} pour garantir 
{', '.join(AI_MODELS[model]['strengths'][:2]).lower()}.
        """,
        
        "Faits": f"""
Les faits de l'espèce, analysés par {AI_MODELS[model]['name']}, peuvent être résumés comme suit :

1. Origine du litige
   - Date de survenance : [À préciser]
   - Parties impliquées : {config.get('client', '[Client]')} c/ [Partie adverse]
   - Nature du différend : [Description]

2. Développement chronologique
   - Phase initiale : [Détails]
   - Évolution : [Détails]
   - Situation actuelle : [Détails]

3. Éléments de preuve
   - Documents disponibles : [Liste]
   - Témoignages : [Si applicable]
   - Expertises : [Si applicable]
        """,
        
        "Analyse": f"""
L'analyse juridique approfondie révèle plusieurs éléments déterminants :

**Qualification juridique**
{AI_MODELS[model]['name']} identifie la qualification suivante : [Qualification]

**Fondements textuels**
- Article X du Code Y : [Application]
- Jurisprudence constante : [Références]

**Points de droit essentiels**
1. [Premier point]
2. [Deuxième point]
3. [Troisième point]

Cette analyse bénéficie des capacités de {model} en matière de {AI_MODELS[model]['strengths'][0].lower()}.
        """
    }
    
    # Récupérer le template ou générer un contenu par défaut
    content = templates.get(section, f"{base_content}Contenu de la section '{section}'...")
    
    # Ajuster selon la longueur demandée
    if config.get('length_multiplier', 1.0) > 1.5:
        content += f"\n\n**Développements complémentaires**\n[Contenu étendu généré par {model}...]"
    
    return content

def merge_ai_results(ai_results: Dict[str, Dict[str, str]], strategy: str) -> Dict[str, str]:
    """Fusionne les résultats de plusieurs modèles IA"""
    merged_content = {}
    
    # Récupérer toutes les sections
    all_sections = set()
    for model_results in ai_results.values():
        all_sections.update(model_results.keys())
    
    for section in all_sections:
        contents = []
        for model, results in ai_results.items():
            if section in results:
                contents.append((model, results[section]))
        
        if strategy == "🏆 Meilleur résultat":
            # Sélectionner le contenu le plus long/détaillé
            best_content = max(contents, key=lambda x: len(x[1]))
            merged_content[section] = f"{best_content[1]}\n\n_[Sélectionné depuis {best_content[0]}]_"
        
        elif strategy == "🤝 Consensus":
            # Combiner les éléments communs
            consensus = f"**Synthèse consensuelle de {len(contents)} modèles :**\n\n"
            
            # Extraire les points clés de chaque contenu
            for model, content in contents:
                lines = content.split('\n')
                key_points = [l for l in lines if l.strip() and (l.startswith('•') or l.startswith('-'))][:3]
                if key_points:
                    consensus += f"\n**{model} souligne :**\n"
                    consensus += '\n'.join(key_points) + '\n'
            
            merged_content[section] = consensus
        
        else:  # Créativité maximale
            # Combiner tous les contenus de manière créative
            creative_merge = "**Fusion créative multi-IA :**\n\n"
            
            for i, (model, content) in enumerate(contents):
                if i > 0:
                    creative_merge += "\n\n---\n\n"
                creative_merge += f"**Perspective {AI_MODELS[model]['icon']} {model} :**\n{content}"
            
            merged_content[section] = creative_merge
    
    return merged_content

def calculate_report_metadata(report: Dict[str, Any]) -> Dict[str, Any]:
    """Calcule les métadonnées du rapport"""
    total_words = sum(len(content.split()) for content in report['content'].values())
    
    metadata = {
        'word_count': total_words,
        'page_estimate': max(1, total_words // 250),
        'reading_time': max(1, total_words // 200),
        'ai_models_used': report['config']['ai_models'],
        'sections_count': len(report['content']),
        'generation_time': datetime.now(),
        'quality_score': calculate_quality_score(report)
    }
    
    return metadata

def calculate_quality_score(report: Dict[str, Any]) -> float:
    """Calcule un score de qualité pour le rapport"""
    score = 0.0
    
    # Score basé sur les modèles utilisés
    for model in report['config']['ai_models']:
        score += AI_MODELS[model]['quality'] * 0.2
    
    # Score basé sur la complétude
    if len(report['content']) >= 4:
        score += 1.0
    
    # Score basé sur la longueur
    word_count = report['metadata']['word_count']
    if word_count > 1000:
        score += 1.0
    elif word_count > 500:
        score += 0.5
    
    # Normaliser sur 5
    return min(5.0, score)

def display_generated_report(report: Dict[str, Any]):
    """Affiche le rapport généré avec options interactives"""
    st.markdown("---")
    st.markdown("## 📄 Rapport généré")
    
    # Métadonnées et métriques
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📝 Mots", f"{report['metadata']['word_count']:,}")
    
    with col2:
        st.metric("📄 Pages", report['metadata']['page_estimate'])
    
    with col3:
        st.metric("⏱️ Lecture", f"{report['metadata']['reading_time']} min")
    
    with col4:
        st.metric("🤖 Modèles", len(report['metadata']['ai_models_used']))
    
    with col5:
        quality = report['metadata']['quality_score']
        st.metric("⭐ Qualité", f"{quality:.1f}/5.0")
    
    # Options d'affichage
    display_mode = st.radio(
        "Mode d'affichage",
        ["📖 Lecture", "✏️ Édition", "🔍 Analyse", "📱 Aperçu mobile"],
        horizontal=True
    )
    
    # Container principal pour le rapport
    report_container = st.container()
    
    with report_container:
        if display_mode == "📖 Lecture":
            display_reading_mode(report)
        elif display_mode == "✏️ Édition":
            display_edit_mode(report)
        elif display_mode == "🔍 Analyse":
            display_analysis_mode(report)
        else:
            display_mobile_preview(report)
    
    # Actions sur le rapport
    st.markdown("---")
    st.markdown("### 🛠️ Actions")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💾 Sauvegarder", use_container_width=True):
            save_report(report)
    
    with col2:
        if st.button("📧 Envoyer", use_container_width=True):
            send_report(report)
    
    with col3:
        if st.button("🖨️ Imprimer", use_container_width=True):
            st.info("Utilisez Ctrl+P ou Cmd+P")
    
    with col4:
        export_format = st.selectbox("Format", ["PDF", "Word", "HTML", "Markdown"])
    
    with col5:
        if st.button(f"⬇️ Exporter {export_format}", use_container_width=True):
            export_report(report, export_format)

def display_reading_mode(report: Dict[str, Any]):
    """Affiche le rapport en mode lecture"""
    # En-tête stylisé
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: #2d3748; margin: 0;">{report['config']['title']}</h1>
        <p style="color: #718096; margin: 0.5rem 0;">
            {report['config'].get('case_ref', '')}
        </p>
        <p style="color: #718096; font-size: 0.9rem;">
            {report['config']['date'].strftime('%d %B %Y')} | 
            {report['config'].get('author', 'Auteur')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Table des matières si activée
    if report['config']['options'].get('toc', False):
        with st.expander("📑 Table des matières", expanded=False):
            for i, section in enumerate(report['config']['sections'], 1):
                st.markdown(f"{i}. [{section}](#{section.lower().replace(' ', '-')})")
    
    # Contenu du rapport
    for section, content in report['content'].items():
        st.markdown(f"### {section}")
        st.markdown(content)
        
        # Séparateur entre sections
        st.markdown("---")

def display_edit_mode(report: Dict[str, Any]):
    """Mode édition du rapport"""
    st.info("✏️ Mode édition - Modifiez directement le contenu")
    
    edited_content = {}
    
    for section, content in report['content'].items():
        with st.expander(f"📝 {section}", expanded=True):
            edited = st.text_area(
                "Contenu",
                value=content,
                height=300,
                key=f"edit_{section}",
                label_visibility="collapsed"
            )
            edited_content[section] = edited
            
            # Outils d'édition
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Régénérer", key=f"regen_{section}"):
                    st.info("Régénération de la section...")
            with col2:
                if st.button("🎨 Reformuler", key=f"rephrase_{section}"):
                    st.info("Reformulation en cours...")
            with col3:
                if st.button("📏 Ajuster longueur", key=f"adjust_{section}"):
                    st.info("Ajustement de la longueur...")
    
    # Boutons de sauvegarde
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Sauvegarder les modifications", type="primary", use_container_width=True):
            report['content'] = edited_content
            report['metadata'] = calculate_report_metadata(report)
            st.success("✅ Modifications sauvegardées")
            st.rerun()
    
    with col2:
        if st.button("❌ Annuler", use_container_width=True):
            st.rerun()

def display_analysis_mode(report: Dict[str, Any]):
    """Mode analyse du rapport"""
    st.markdown("### 🔍 Analyse du rapport")
    
    # Statistiques détaillées
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Statistiques du contenu")
        
        # Analyse par section
        section_stats = []
        for section, content in report['content'].items():
            words = len(content.split())
            sentences = len(re.split(r'[.!?]+', content))
            section_stats.append({
                'Section': section,
                'Mots': words,
                'Phrases': sentences,
                'Moy. mots/phrase': round(words/max(1, sentences), 1)
            })
        
        df_stats = pd.DataFrame(section_stats)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
        
        # Graphique de distribution
        st.markdown("#### 📈 Distribution du contenu")
        chart_data = pd.DataFrame({
            'Section': [s['Section'] for s in section_stats],
            'Mots': [s['Mots'] for s in section_stats]
        })
        st.bar_chart(chart_data.set_index('Section'))
    
    with col2:
        st.markdown("#### 🤖 Analyse IA")
        
        # Contribution par modèle
        if report['config'].get('fusion_mode', False):
            st.markdown("**Contribution par modèle:**")
            for model in report['config']['ai_models']:
                st.write(f"• {AI_MODELS[model]['icon']} {model}")
        
        # Score de qualité détaillé
        st.markdown("**Analyse qualitative:**")
        quality_aspects = {
            'Complétude': min(5, len(report['content']) * 1.25),
            'Cohérence': 4.2,  # Simulation
            'Clarté': 4.5,     # Simulation
            'Pertinence': 4.8,  # Simulation
            'Format': 5.0 if report['config']['options'].get('toc', False) else 4.0
        }
        
        for aspect, score in quality_aspects.items():
            st.metric(aspect, f"{score:.1f}/5.0", f"{(score/5*100):.0f}%")
        
        # Suggestions d'amélioration
        st.markdown("**💡 Suggestions d'amélioration:**")
        suggestions = [
            "Ajouter plus de jurisprudence dans la section 'Analyse'",
            "Développer les recommandations avec des actions concrètes",
            "Inclure une timeline visuelle des événements"
        ]
        for suggestion in suggestions:
            st.write(f"• {suggestion}")

def display_mobile_preview(report: Dict[str, Any]):
    """Aperçu mobile du rapport"""
    st.markdown("### 📱 Aperçu mobile")
    
    # Container simulant un écran mobile
    mobile_container = st.container()
    
    with mobile_container:
        st.markdown("""
        <div style="max-width: 375px; margin: 0 auto; border: 2px solid #ddd; 
                    border-radius: 20px; padding: 20px; background: #f8f9fa;">
        """, unsafe_allow_html=True)
        
        # En-tête mobile
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <h3 style="margin: 0; font-size: 1.2rem;">{report['config']['title']}</h3>
            <p style="margin: 0.5rem 0; font-size: 0.8rem; color: #666;">
                {report['config']['date'].strftime('%d/%m/%Y')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation mobile
        st.markdown("""
        <div style="display: flex; gap: 0.5rem; margin: 1rem 0; overflow-x: auto;">
        """, unsafe_allow_html=True)
        
        for section in report['config']['sections'][:3]:
            st.markdown(f"""
            <div style="background: #e2e8f0; padding: 0.5rem 1rem; border-radius: 20px; 
                        white-space: nowrap; font-size: 0.9rem;">
                {section}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Contenu mobile (aperçu)
        first_section = list(report['content'].keys())[0]
        preview_content = report['content'][first_section][:200] + "..."
        
        st.markdown(f"""
        <div style="padding: 1rem 0; font-size: 0.9rem; line-height: 1.6;">
            <h4 style="font-size: 1rem; margin-bottom: 0.5rem;">{first_section}</h4>
            <p>{preview_content}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def render_ai_models():
    """Interface de gestion des modèles IA"""
    st.markdown("### 🤖 Modèles d'Intelligence Artificielle")
    
    # Vue d'ensemble des modèles
    st.markdown("#### 📊 Comparaison des modèles")
    
    # Tableau comparatif
    models_data = []
    for model_id, model_info in AI_MODELS.items():
        models_data.append({
            'Modèle': f"{model_info['icon']} {model_info['name']}",
            'Fournisseur': model_info['provider'],
            'Vitesse': model_info['speed'],
            'Qualité': '⭐' * model_info['quality'],
            'Points forts': ', '.join(model_info['strengths'][:2])
        })
    
    df_models = pd.DataFrame(models_data)
    st.dataframe(df_models, use_container_width=True, hide_index=True)
    
    # Configuration des préférences
    st.markdown("#### ⚙️ Préférences par type de document")
    
    col1, col2 = st.columns(2)
    
    with col1:
        for template_id, template in list(REPORT_TEMPLATES.items())[:3]:
            with st.expander(f"{template['icon']} {template['name']}"):
                preferred_models = st.multiselect(
                    "Modèles préférés",
                    list(AI_MODELS.keys()),
                    default=template['ai_models'][:2],
                    key=f"pref_{template_id}"
                )
                
                if st.button(f"💾 Sauvegarder", key=f"save_pref_{template_id}"):
                    if 'ai_preferences' not in st.session_state:
                        st.session_state.ai_preferences = {}
                    st.session_state.ai_preferences[template_id] = preferred_models
                    st.success("Préférences sauvegardées")
    
    with col2:
        for template_id, template in list(REPORT_TEMPLATES.items())[3:]:
            with st.expander(f"{template['icon']} {template['name']}"):
                preferred_models = st.multiselect(
                    "Modèles préférés",
                    list(AI_MODELS.keys()),
                    default=template['ai_models'][:2],
                    key=f"pref_{template_id}"
                )
                
                if st.button(f"💾 Sauvegarder", key=f"save_pref_{template_id}"):
                    if 'ai_preferences' not in st.session_state:
                        st.session_state.ai_preferences = {}
                    st.session_state.ai_preferences[template_id] = preferred_models
                    st.success("Préférences sauvegardées")
    
    # Tests de performance
    st.markdown("#### 🏃 Tests de performance")
    
    if st.button("🚀 Lancer un test de performance", use_container_width=True):
        run_performance_test()

def run_performance_test():
    """Execute un test de performance des modèles"""
    progress = st.progress(0)
    status = st.empty()
    results = {}
    
    test_prompt = "Générez un court résumé juridique sur la responsabilité contractuelle"
    
    for i, (model_id, model_info) in enumerate(AI_MODELS.items()):
        status.text(f"Test de {model_info['name']}...")
        progress.progress((i + 1) / len(AI_MODELS))
        
        # Simulation du test
        start_time = time.time()
        time.sleep(0.5 + (5 - model_info['quality']) * 0.2)  # Simulation
        end_time = time.time()
        
        results[model_id] = {
            'time': end_time - start_time,
            'quality': model_info['quality'],
            'tokens': 150 + model_info['quality'] * 50  # Simulation
        }
    
    status.success("✅ Tests terminés!")
    
    # Affichage des résultats
    st.markdown("##### 📊 Résultats des tests")
    
    col1, col2, col3 = st.columns(3)
    
    # Meilleure vitesse
    fastest = min(results.items(), key=lambda x: x[1]['time'])
    with col1:
        st.metric(
            "⚡ Plus rapide",
            AI_MODELS[fastest[0]]['name'],
            f"{fastest[1]['time']:.2f}s"
        )
    
    # Meilleure qualité
    best_quality = max(results.items(), key=lambda x: x[1]['quality'])
    with col2:
        st.metric(
            "⭐ Meilleure qualité",
            AI_MODELS[best_quality[0]]['name'],
            f"{best_quality[1]['quality']}/5"
        )
    
    # Meilleur ratio
    best_ratio = max(results.items(), key=lambda x: x[1]['quality'] / x[1]['time'])
    with col3:
        st.metric(
            "🏆 Meilleur ratio",
            AI_MODELS[best_ratio[0]]['name'],
            f"Score: {(best_ratio[1]['quality'] / best_ratio[1]['time']):.2f}"
        )

def render_templates_library():
    """Bibliothèque de templates"""
    st.markdown("### 📚 Bibliothèque de modèles")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.multiselect(
            "Type de document",
            list(REPORT_TEMPLATES.keys()),
            format_func=lambda x: REPORT_TEMPLATES[x]['name']
        )
    
    with col2:
        filter_duration = st.select_slider(
            "Durée de génération",
            ["Tous", "< 15 min", "15-30 min", "> 30 min"],
            value="Tous"
        )
    
    with col3:
        search = st.text_input("🔍 Rechercher", placeholder="Nom ou description...")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Standards", "⭐ Favoris", "🎨 Personnalisés"])
    
    with tab1:
        display_standard_templates(filter_type, filter_duration, search)
    
    with tab2:
        display_favorite_templates()
    
    with tab3:
        display_custom_templates()

def display_standard_templates(filter_type, filter_duration, search):
    """Affiche les templates standards avec filtres"""
    templates_to_show = REPORT_TEMPLATES.copy()
    
    # Appliquer les filtres
    if filter_type:
        templates_to_show = {k: v for k, v in templates_to_show.items() if k in filter_type}
    
    if search:
        templates_to_show = {
            k: v for k, v in templates_to_show.items() 
            if search.lower() in v['name'].lower() or search.lower() in v['description'].lower()
        }
    
    # Affichage en grille
    cols = st.columns(2)
    for i, (template_id, template) in enumerate(templates_to_show.items()):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"""
                <div class="report-card">
                    <h4>{template['icon']} {template['name']}</h4>
                    <p style="color: #666;">{template['description']}</p>
                    <div style="margin: 1rem 0;">
                        <span style="background: #e0e7ff; padding: 0.25rem 0.5rem; 
                                     border-radius: 4px; font-size: 0.8rem;">
                            ⏱️ {template['duration']}
                        </span>
                        <span style="background: #fef3c7; padding: 0.25rem 0.5rem; 
                                     border-radius: 4px; font-size: 0.8rem; margin-left: 0.5rem;">
                            📝 {len(template['sections'])} sections
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("👁️ Aperçu", key=f"preview_{template_id}"):
                        show_template_preview(template_id, template)
                
                with col_b:
                    if st.button("📝 Utiliser", key=f"use_{template_id}"):
                        st.session_state.selected_template = template_id
                        st.info(f"Template '{template['name']}' sélectionné")
                
                with col_c:
                    if st.button("⭐ Favoris", key=f"fav_{template_id}"):
                        add_to_favorites(template_id)

def show_template_preview(template_id: str, template: Dict[str, Any]):
    """Affiche un aperçu détaillé du template"""
    with st.expander(f"Aperçu : {template['name']}", expanded=True):
        st.markdown(f"**Description :** {template['description']}")
        st.markdown(f"**Durée estimée :** {template['duration']}")
        st.markdown(f"**Ton recommandé :** {template['tone']}")
        
        st.markdown("**Structure du document :**")
        for i, section in enumerate(template['sections'], 1):
            st.markdown(f"{i}. {section}")
        
        st.markdown("**Modèles IA recommandés :**")
        for model in template['ai_models']:
            st.write(f"• {AI_MODELS[model]['icon']} {model}")

def add_to_favorites(template_id: str):
    """Ajoute un template aux favoris"""
    if 'favorite_templates' not in st.session_state:
        st.session_state.favorite_templates = []
    
    if template_id not in st.session_state.favorite_templates:
        st.session_state.favorite_templates.append(template_id)
        st.success("✅ Ajouté aux favoris")
    else:
        st.info("Déjà dans les favoris")

def display_favorite_templates():
    """Affiche les templates favoris"""
    if 'favorite_templates' not in st.session_state or not st.session_state.favorite_templates:
        st.info("⭐ Aucun favori. Ajoutez des templates à vos favoris pour les retrouver ici.")
        return
    
    for template_id in st.session_state.favorite_templates:
        if template_id in REPORT_TEMPLATES:
            template = REPORT_TEMPLATES[template_id]
            with st.expander(f"{template['icon']} {template['name']}", expanded=False):
                st.write(template['description'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📝 Utiliser", key=f"use_fav_{template_id}"):
                        st.session_state.selected_template = template_id
                        st.success("Template sélectionné")
                
                with col2:
                    if st.button(f"❌ Retirer", key=f"remove_fav_{template_id}"):
                        st.session_state.favorite_templates.remove(template_id)
                        st.rerun()

def display_custom_templates():
    """Affiche les templates personnalisés"""
    if 'custom_templates' not in st.session_state or not st.session_state.custom_templates:
        st.info("🎨 Aucun template personnalisé. Créez-en un en sauvegardant un rapport comme modèle.")
        
        if st.button("➕ Créer un template personnalisé"):
            create_custom_template()
        return
    
    for template_id, template in st.session_state.custom_templates.items():
        with st.expander(
            f"{template.get('icon', '📄')} {template['name']} - {template['created_at'].strftime('%d/%m/%Y')}",
            expanded=False
        ):
            st.write(f"**Type de base :** {template.get('base_type', 'Personnalisé')}")
            st.write(f"**Sections :** {len(template['sections'])}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📝 Utiliser", key=f"use_custom_{template_id}"):
                    use_custom_template(template)
            
            with col2:
                if st.button("✏️ Modifier", key=f"edit_custom_{template_id}"):
                    edit_custom_template(template_id, template)
            
            with col3:
                if st.button("🗑️ Supprimer", key=f"del_custom_{template_id}"):
                    if st.checkbox(f"Confirmer suppression", key=f"confirm_del_{template_id}"):
                        del st.session_state.custom_templates[template_id]
                        st.success("Template supprimé")
                        st.rerun()

def create_custom_template():
    """Interface de création de template personnalisé"""
    with st.form("create_custom_template"):
        st.markdown("### ➕ Créer un template personnalisé")
        
        name = st.text_input("Nom du template", placeholder="Ex: Rapport d'audit spécialisé")
        
        base_type = st.selectbox(
            "Basé sur",
            ["Nouveau"] + list(REPORT_TEMPLATES.keys()),
            format_func=lambda x: "Partir de zéro" if x == "Nouveau" else REPORT_TEMPLATES[x]['name']
        )
        
        if base_type != "Nouveau":
            sections = st.multiselect(
                "Sections à inclure",
                REPORT_TEMPLATES[base_type]['sections'],
                default=REPORT_TEMPLATES[base_type]['sections']
            )
        else:
            num_sections = st.number_input("Nombre de sections", min_value=1, max_value=10, value=3)
            sections = []
            for i in range(num_sections):
                section = st.text_input(f"Section {i+1}", key=f"custom_section_{i}")
                if section:
                    sections.append(section)
        
        description = st.text_area("Description", placeholder="Décrivez l'usage de ce template...")
        
        icon = st.selectbox("Icône", ["📄", "📊", "📈", "📑", "📜", "🎯", "💼", "⚖️"])
        
        if st.form_submit_button("Créer le template", type="primary"):
            if name and sections:
                template_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                st.session_state.custom_templates[template_id] = {
                    'name': name,
                    'icon': icon,
                    'description': description,
                    'sections': sections,
                    'base_type': base_type if base_type != "Nouveau" else None,
                    'created_at': datetime.now()
                }
                
                st.success(f"✅ Template '{name}' créé avec succès!")
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs requis")

def render_merge_reports():
    """Interface de fusion de rapports"""
    st.markdown("### 🔄 Fusion de rapports")
    
    if 'report_history' not in st.session_state or len(st.session_state.report_history) < 2:
        st.info("📊 Au moins 2 rapports sont nécessaires pour effectuer une fusion.")
        st.markdown("**Conseil :** Générez plusieurs rapports puis revenez ici pour les fusionner.")
        return
    
    # Sélection des rapports
    st.markdown("#### 1️⃣ Sélectionner les rapports à fusionner")
    
    report_options = []
    for i, report in enumerate(st.session_state.report_history):
        report_options.append({
            'index': i,
            'title': report['config']['title'],
            'date': report['created_at'].strftime('%d/%m/%Y %H:%M'),
            'type': REPORT_TEMPLATES.get(report['config']['type'], {}).get('name', report['config']['type']),
            'sections': len(report['content']),
            'words': report['metadata']['word_count']
        })
    
    # Affichage en tableau pour sélection
    selected_reports = []
    for opt in report_options:
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1, 1])
        
        with col1:
            if st.checkbox("", key=f"merge_select_{opt['index']}"):
                selected_reports.append(opt['index'])
        
        with col2:
            st.write(f"**{opt['title']}**")
        
        with col3:
            st.write(f"{opt['type']} - {opt['date']}")
        
        with col4:
            st.write(f"{opt['sections']} sections")
        
        with col5:
            st.write(f"{opt['words']:,} mots")
    
    if len(selected_reports) >= 2:
        st.success(f"✅ {len(selected_reports)} rapports sélectionnés")
        
        # Options de fusion
        st.markdown("#### 2️⃣ Configurer la fusion")
        
        col1, col2 = st.columns(2)
        
        with col1:
            merge_strategy = st.selectbox(
                "Stratégie de fusion",
                [
                    "📑 Concaténation simple",
                    "🎯 Synthèse intelligente",
                    "🔍 Analyse comparative",
                    "💎 Consolidation avancée"
                ],
                help="Comment combiner les contenus des rapports"
            )
            
            new_title = st.text_input(
                "Titre du rapport fusionné",
                value=f"Rapport consolidé - {datetime.now().strftime('%d/%m/%Y')}"
            )
        
        with col2:
            section_strategy = st.radio(
                "Gestion des sections",
                ["Fusionner sections identiques", "Conserver toutes les sections", "Sélection manuelle"],
                help="Comment traiter les sections communes"
            )
            
            use_ai = st.checkbox(
                "Utiliser l'IA pour optimiser la fusion",
                value=True,
                help="L'IA améliore la cohérence et évite les redondances"
            )
        
        # Aperçu de la structure
        if section_strategy == "Sélection manuelle":
            st.markdown("#### 3️⃣ Sélectionner les sections")
            
            # Collecter toutes les sections uniques
            all_sections = set()
            for idx in selected_reports:
                all_sections.update(st.session_state.report_history[idx]['config']['sections'])
            
            selected_sections = []
            cols = st.columns(3)
            for i, section in enumerate(sorted(all_sections)):
                with cols[i % 3]:
                    if st.checkbox(section, value=True, key=f"merge_section_{section}"):
                        selected_sections.append(section)
        
        # Bouton de fusion
        st.markdown("---")
        
        if st.button("🔄 Lancer la fusion", type="primary", use_container_width=True):
            perform_advanced_merge(
                selected_reports,
                merge_strategy,
                new_title,
                section_strategy,
                selected_sections if section_strategy == "Sélection manuelle" else None,
                use_ai
            )

def perform_advanced_merge(selected_indices, strategy, title, section_strategy, selected_sections, use_ai):
    """Effectue une fusion avancée des rapports"""
    progress = st.progress(0)
    status = st.empty()
    
    # Récupérer les rapports
    reports = [st.session_state.report_history[i] for i in selected_indices]
    
    # Créer le rapport fusionné
    merged_report = {
        'id': f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'created_at': datetime.now(),
        'config': {
            'title': title,
            'type': 'merged',
            'merge_strategy': strategy,
            'source_reports': len(reports),
            'use_ai': use_ai,
            'ai_models': ['GPT-4', 'Claude'] if use_ai else [],
            'sections': [],
            'options': reports[0]['config'].get('options', {})
        },
        'content': {},
        'metadata': {}
    }
    
    status.text("📊 Analyse des rapports sources...")
    progress.progress(20)
    time.sleep(0.5)
    
    # Appliquer la stratégie de fusion
    if "Concaténation" in strategy:
        merged_content = merge_concatenate_advanced(reports, section_strategy, selected_sections)
    elif "Synthèse" in strategy:
        status.text("🤖 Synthèse intelligente en cours...")
        progress.progress(40)
        merged_content = merge_synthesize_advanced(reports, section_strategy, use_ai)
    elif "comparative" in strategy:
        status.text("🔍 Analyse comparative...")
        progress.progress(40)
        merged_content = merge_compare_advanced(reports, section_strategy)
    else:  # Consolidation
        status.text("💎 Consolidation avancée...")
        progress.progress(40)
        merged_content = merge_consolidate_advanced(reports, section_strategy, use_ai)
    
    progress.progress(80)
    
    # Optimisation avec IA si activée
    if use_ai:
        status.text("🎯 Optimisation IA du contenu...")
        time.sleep(1)
        merged_content = optimize_merged_content(merged_content)
    
    merged_report['content'] = merged_content
    merged_report['config']['sections'] = list(merged_content.keys())
    
    # Calculer les métadonnées
    merged_report['metadata'] = calculate_report_metadata(merged_report)
    
    # Sauvegarder
    st.session_state.report_history.append(merged_report)
    
    progress.progress(100)
    status.success("✅ Fusion terminée avec succès!")
    
    # Afficher le résultat
    display_generated_report(merged_report)

def merge_concatenate_advanced(reports, section_strategy, selected_sections=None):
    """Concaténation avancée avec gestion intelligente des sections"""
    merged = defaultdict(list)
    
    for i, report in enumerate(reports):
        # Ajouter un en-tête de source
        source_header = f"\n\n**[Source : {report['config']['title']}]**\n\n"
        
        for section, content in report['content'].items():
            if selected_sections and section not in selected_sections:
                continue
                
            if section_strategy == "Fusionner sections identiques":
                if i > 0:
                    merged[section].append(source_header)
                merged[section].append(content)
            else:
                # Créer des sections uniques
                unique_section = f"{section} - Rapport {i+1}"
                merged[unique_section].append(content)
    
    return {section: "\n".join(contents) for section, contents in merged.items()}

def merge_synthesize_advanced(reports, section_strategy, use_ai):
    """Synthèse intelligente avec extraction des points clés"""
    synthesized = {}
    
    # Regrouper par section
    sections_content = defaultdict(list)
    for report in reports:
        for section, content in report['content'].items():
            sections_content[section].append({
                'source': report['config']['title'],
                'content': content
            })
    
    # Synthétiser chaque section
    for section, contents in sections_content.items():
        if len(contents) == 1:
            synthesized[section] = contents[0]['content']
        else:
            # Créer une synthèse
            synthesis = [f"### Synthèse : {section}\n"]
            synthesis.append(f"*Basée sur {len(contents)} sources*\n")
            
            # Points clés de chaque source
            synthesis.append("#### Points clés par source:\n")
            
            for item in contents:
                synthesis.append(f"\n**{item['source']}:**")
                
                # Extraire les points clés (simulation)
                lines = item['content'].split('\n')
                key_points = []
                
                for line in lines:
                    if line.strip() and (line.startswith('•') or line.startswith('-') or 
                                       line.startswith('1.') or line.startswith('2.')):
                        key_points.append(line)
                
                if not key_points:
                    # Prendre les premières phrases significatives
                    sentences = [s.strip() for s in item['content'].split('.') if s.strip()][:3]
                    key_points = [f"• {s}." for s in sentences if s]
                
                synthesis.extend(key_points[:5])  # Max 5 points par source
            
            # Analyse consolidée
            if use_ai:
                synthesis.append("\n#### Analyse consolidée:\n")
                synthesis.append("*[Analyse IA de la convergence et des divergences entre les sources]*")
            
            synthesized[section] = "\n".join(synthesis)
    
    return synthesized

def merge_compare_advanced(reports, section_strategy):
    """Comparaison avancée avec tableau comparatif"""
    compared = {}
    
    # Introduction comparative
    intro = [
        f"# Analyse comparative de {len(reports)} rapports\n",
        f"*Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n",
        "\n## Rapports analysés:\n"
    ]
    
    for i, report in enumerate(reports):
        intro.append(f"{i+1}. **{report['config']['title']}** - {report['config']['date'].strftime('%d/%m/%Y')}")
    
    compared['Introduction comparative'] = "\n".join(intro)
    
    # Comparaison par section
    all_sections = set()
    for report in reports:
        all_sections.update(report['content'].keys())
    
    for section in sorted(all_sections):
        comparison = [f"\n## Comparaison : {section}\n"]
        
        # Tableau comparatif
        comparison.append("| Rapport | Contenu clé | Différences notables |")
        comparison.append("|---------|-------------|---------------------|")
        
        section_contents = []
        for i, report in enumerate(reports):
            if section in report['content']:
                content = report['content'][section]
                # Extraire le résumé (premières lignes)
                summary = ' '.join(content.split('\n')[:3])[:100] + "..."
                section_contents.append(content)
                
                # Identifier les différences (simulation)
                differences = "Points spécifiques identifiés"
                
                comparison.append(f"| Rapport {i+1} | {summary} | {differences} |")
            else:
                comparison.append(f"| Rapport {i+1} | *Section absente* | - |")
        
        # Analyse des convergences/divergences
        if len(section_contents) > 1:
            comparison.append("\n### Analyse des convergences et divergences:")
            comparison.append("• **Points de convergence:** [Analyse des éléments communs]")
            comparison.append("• **Points de divergence:** [Analyse des différences]")
            comparison.append("• **Recommandation:** [Synthèse et recommandation basée sur la comparaison]")
        
        compared[f"Comparaison - {section}"] = "\n".join(comparison)
    
    return compared

def merge_consolidate_advanced(reports, section_strategy, use_ai):
    """Consolidation avancée avec déduplication intelligente"""
    consolidated = {}
    
    # Phase 1: Extraction et catégorisation
    all_content = defaultdict(lambda: defaultdict(list))
    
    for report in reports:
        for section, content in report['content'].items():
            # Catégoriser le contenu
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Catégoriser (simulation)
                    if any(word in para.lower() for word in ['fait', 'date', 'événement']):
                        category = 'facts'
                    elif any(word in para.lower() for word in ['article', 'loi', 'jurisprudence']):
                        category = 'legal'
                    elif any(word in para.lower() for word in ['recommand', 'conseil', 'suggér']):
                        category = 'recommendations'
                    else:
                        category = 'analysis'
                    
                    all_content[section][category].append({
                        'content': para,
                        'source': report['config']['title']
                    })
    
    # Phase 2: Consolidation par section
    for section, categories in all_content.items():
        section_content = [f"## {section}\n"]
        
        # Traiter chaque catégorie
        for category, items in categories.items():
            if not items:
                continue
            
            category_names = {
                'facts': '### Éléments factuels',
                'legal': '### Fondements juridiques',
                'analysis': '### Analyse',
                'recommendations': '### Recommandations'
            }
            
            section_content.append(f"\n{category_names.get(category, '### ' + category)}\n")
            
            # Déduplication (simulation simple)
            seen_content = set()
            unique_items = []
            
            for item in items:
                # Hash simple du contenu pour détecter les doublons
                content_hash = item['content'][:50].lower()
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_items.append(item)
            
            # Ajouter le contenu unique
            if len(unique_items) == 1:
                section_content.append(unique_items[0]['content'])
            else:
                for item in unique_items:
                    section_content.append(f"{item['content']}")
                    if len(set(i['source'] for i in items)) > 1:
                        section_content.append(f"*[Source: {item['source']}]*\n")
        
        consolidated[section] = "\n".join(section_content)
    
    # Phase 3: Optimisation finale
    if use_ai:
        # Ajouter une section de synthèse globale
        consolidated['Synthèse consolidée'] = """
## Synthèse consolidée

Cette section présente une vue d'ensemble unifiée basée sur l'analyse de tous les rapports sources.

### Points clés consolidés
• Synthèse des éléments factuels convergents
• Analyse juridique harmonisée
• Recommandations prioritaires issues de l'ensemble des analyses

### Cohérence et qualité
L'analyse par IA a permis d'identifier et d'éliminer les redondances tout en préservant 
les nuances importantes de chaque rapport source.
        """
    
    return consolidated

def optimize_merged_content(content):
    """Optimise le contenu fusionné avec l'IA"""
    # Simulation d'optimisation IA
    optimized = {}
    
    for section, text in content.items():
        # Ajouter des améliorations
        optimized[section] = text
        
        # Ajouter des métadonnées d'optimisation
        if "synthèse" not in section.lower():
            optimized[section] += "\n\n*[Contenu optimisé par IA pour cohérence et clarté]*"
    
    return optimized

def render_history():
    """Affiche l'historique des rapports"""
    st.markdown("### 📊 Historique des rapports")
    
    if not st.session_state.report_history:
        st.info("📝 Aucun rapport généré. Créez votre premier rapport pour le voir apparaître ici.")
        return
    
    # Statistiques globales
    col1, col2, col3, col4 = st.columns(4)
    
    total_reports = len(st.session_state.report_history)
    total_words = sum(r['metadata']['word_count'] for r in st.session_state.report_history)
    avg_quality = sum(r['metadata'].get('quality_score', 0) for r in st.session_state.report_history) / total_reports
    
    with col1:
        st.metric("📄 Total rapports", total_reports)
    
    with col2:
        st.metric("📝 Total mots", f"{total_words:,}")
    
    with col3:
        st.metric("⭐ Qualité moyenne", f"{avg_quality:.1f}/5.0")
    
    with col4:
        st.metric("🤖 Modèles utilisés", len(set(m for r in st.session_state.report_history 
                                                for m in r['metadata'].get('ai_models_used', []))))
    
    # Filtres et recherche
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search = st.text_input("🔍 Rechercher", placeholder="Titre, référence...")
    
    with col2:
        filter_type = st.selectbox(
            "Type",
            ["Tous"] + list(set(r['config']['type'] for r in st.session_state.report_history))
        )
    
    with col3:
        sort_by = st.selectbox(
            "Trier par",
            ["Date (récent)", "Date (ancien)", "Titre", "Taille", "Qualité"]
        )
    
    # Appliquer les filtres
    filtered_reports = st.session_state.report_history.copy()
    
    if search:
        filtered_reports = [
            r for r in filtered_reports 
            if search.lower() in r['config']['title'].lower() or 
               search.lower() in r['config'].get('case_ref', '').lower()
        ]
    
    if filter_type != "Tous":
        filtered_reports = [r for r in filtered_reports if r['config']['type'] == filter_type]
    
    # Trier
    if sort_by == "Date (récent)":
        filtered_reports.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Date (ancien)":
        filtered_reports.sort(key=lambda x: x['created_at'])
    elif sort_by == "Titre":
        filtered_reports.sort(key=lambda x: x['config']['title'])
    elif sort_by == "Taille":
        filtered_reports.sort(key=lambda x: x['metadata']['word_count'], reverse=True)
    else:  # Qualité
        filtered_reports.sort(key=lambda x: x['metadata'].get('quality_score', 0), reverse=True)
    
    # Affichage des rapports
    for report in filtered_reports:
        with st.expander(
            f"{REPORT_TEMPLATES.get(report['config']['type'], {}).get('icon', '📄')} "
            f"{report['config']['title']} - {report['created_at'].strftime('%d/%m/%Y %H:%M')}",
            expanded=False
        ):
            # Informations du rapport
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Type :** {REPORT_TEMPLATES.get(report['config']['type'], {}).get('name', report['config']['type'])}")
                st.write(f"**Référence :** {report['config'].get('case_ref', 'N/A')}")
                st.write(f"**Client :** {report['config'].get('client', 'N/A')}")
                st.write(f"**Sections :** {len(report['content'])}")
                
                # Tags des modèles IA utilisés
                if report['metadata'].get('ai_models_used'):
                    models_tags = " ".join([
                        f"`{AI_MODELS.get(m, {}).get('icon', '')} {m}`" 
                        for m in report['metadata']['ai_models_used']
                    ])
                    st.markdown(f"**IA :** {models_tags}")
            
            with col2:
                st.metric("Mots", f"{report['metadata']['word_count']:,}")
                st.metric("Pages", report['metadata']['page_estimate'])
                st.metric("Qualité", f"{report['metadata'].get('quality_score', 0):.1f}/5.0")
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("👁️ Voir", key=f"view_hist_{report['id']}"):
                    st.session_state.current_report = report
                    display_generated_report(report)
            
            with col2:
                if st.button("📑 Dupliquer", key=f"dup_hist_{report['id']}"):
                    duplicate_report(report)
            
            with col3:
                if st.button("✏️ Éditer", key=f"edit_hist_{report['id']}"):
                    st.session_state.current_report = report
                    st.session_state.edit_mode = True
            
            with col4:
                if st.button("🗑️ Supprimer", key=f"del_hist_{report['id']}"):
                    if st.checkbox(f"Confirmer", key=f"confirm_del_hist_{report['id']}"):
                        st.session_state.report_history.remove(report)
                        st.success("Rapport supprimé")
                        st.rerun()

def duplicate_report(report):
    """Duplique un rapport"""
    new_report = report.copy()
    new_report['id'] = f"duplicate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    new_report['created_at'] = datetime.now()
    new_report['config']['title'] = f"{report['config']['title']} (Copie)"
    
    st.session_state.report_history.append(new_report)
    st.success("✅ Rapport dupliqué avec succès")

def render_settings():
    """Paramètres du module"""
    st.markdown("### ⚙️ Paramètres")
    
    # Préférences générales
    with st.expander("🎨 Apparence et interface", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "Thème",
                ["Clair", "Sombre", "Auto"],
                index=0 if st.session_state.get('theme', 'light') == 'light' else 1
            )
            
            animations = st.checkbox(
                "Animations activées",
                value=True,
                help="Désactiver pour de meilleures performances"
            )
        
        with col2:
            compact_mode = st.checkbox(
                "Mode compact",
                value=False,
                help="Réduit l'espacement pour afficher plus de contenu"
            )
            
            preview_length = st.slider(
                "Longueur des aperçus (mots)",
                50, 500, 200
            )
    
    # Paramètres IA
    with st.expander("🤖 Configuration IA", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            default_model = st.selectbox(
                "Modèle par défaut",
                list(AI_MODELS.keys()),
                help="Modèle utilisé par défaut pour les nouvelles générations"
            )
            
            max_retries = st.number_input(
                "Tentatives max en cas d'erreur",
                min_value=1,
                max_value=5,
                value=3
            )
        
        with col2:
            timeout = st.slider(
                "Timeout par requête (secondes)",
                10, 120, 30
            )
            
            cache_responses = st.checkbox(
                "Mettre en cache les réponses",
                value=True,
                help="Améliore les performances pour les requêtes similaires"
            )
    
    # Paramètres d'export
    with st.expander("📤 Options d'export", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            default_format = st.selectbox(
                "Format d'export par défaut",
                ["PDF", "Word", "HTML", "Markdown"]
            )
            
            include_metadata = st.checkbox(
                "Inclure les métadonnées",
                value=True
            )
        
        with col2:
            watermark_text = st.text_input(
                "Texte du filigrane",
                placeholder="Confidentiel",
                help="Laissez vide pour désactiver"
            )
            
            auto_backup = st.checkbox(
                "Sauvegarde automatique",
                value=True,
                help="Sauvegarde les rapports localement"
            )
    
    # Sauvegarde et réinitialisation
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder les paramètres", type="primary", use_container_width=True):
            save_settings({
                'theme': theme,
                'animations': animations,
                'compact_mode': compact_mode,
                'preview_length': preview_length,
                'default_model': default_model,
                'max_retries': max_retries,
                'timeout': timeout,
                'cache_responses': cache_responses,
                'default_format': default_format,
                'include_metadata': include_metadata,
                'watermark_text': watermark_text,
                'auto_backup': auto_backup
            })
    
    with col2:
        if st.button("🔄 Paramètres par défaut", use_container_width=True):
            if st.checkbox("Confirmer la réinitialisation"):
                reset_settings()
    
    with col3:
        if st.button("🗑️ Effacer tout l'historique", use_container_width=True):
            if st.checkbox("⚠️ Confirmer la suppression définitive"):
                st.session_state.report_history = []
                st.session_state.custom_templates = {}
                st.success("Historique effacé")
                st.rerun()

def save_settings(settings):
    """Sauvegarde les paramètres"""
    st.session_state.settings = settings
    st.success("✅ Paramètres sauvegardés")
    
    # Appliquer certains paramètres immédiatement
    st.session_state.theme = 'light' if settings['theme'] == 'Clair' else 'dark'

def reset_settings():
    """Réinitialise les paramètres"""
    if 'settings' in st.session_state:
        del st.session_state.settings
    st.success("✅ Paramètres réinitialisés")
    st.rerun()

def save_report(report):
    """Sauvegarde un rapport"""
    # Simulation de sauvegarde
    st.success(f"✅ Rapport '{report['config']['title']}' sauvegardé")

def send_report(report):
    """Envoie un rapport par email"""
    with st.form("send_report_form"):
        st.markdown("### 📧 Envoyer le rapport")
        
        recipient = st.text_input("Destinataire", placeholder="email@example.com")
        cc = st.text_input("CC (optionnel)", placeholder="cc@example.com")
        
        subject = st.text_input(
            "Objet",
            value=f"{report['config']['title']} - {datetime.now().strftime('%d/%m/%Y')}"
        )
        
        message = st.text_area(
            "Message",
            value="Bonjour,\n\nVeuillez trouver ci-joint le rapport demandé.\n\nCordialement,",
            height=150
        )
        
        format_choice = st.selectbox("Format", ["PDF", "Word", "HTML"])
        
        if st.form_submit_button("📤 Envoyer", type="primary"):
            if recipient:
                # Simulation d'envoi
                with st.spinner("Envoi en cours..."):
                    time.sleep(2)
                st.success(f"✅ Rapport envoyé à {recipient}")
            else:
                st.error("Veuillez saisir une adresse email")

def export_report(report, format_type):
    """Exporte un rapport dans le format spécifié"""
    with st.spinner(f"Génération du fichier {format_type}..."):
        time.sleep(1)  # Simulation
        
        if format_type == "Markdown":
            content = export_to_markdown(report)
            st.download_button(
                f"⬇️ Télécharger {format_type}",
                data=content,
                file_name=f"{report['id']}.md",
                mime="text/markdown"
            )
        else:
            st.info(f"Export {format_type} en cours de développement")

def export_to_markdown(report):
    """Exporte le rapport en Markdown"""
    lines = [
        f"# {report['config']['title']}",
        "",
        f"**Date :** {report['config']['date'].strftime('%d %B %Y')}  ",
        f"**Auteur :** {report['config'].get('author', 'N/A')}  ",
        f"**Référence :** {report['config'].get('case_ref', 'N/A')}  ",
        "",
        "---",
        ""
    ]
    
    # Table des matières
    if report['config']['options'].get('toc', False):
        lines.extend([
            "## Table des matières",
            ""
        ])
        
        for i, section in enumerate(report['config']['sections'], 1):
            lines.append(f"{i}. [{section}](#{section.lower().replace(' ', '-')})")
        
        lines.extend(["", "---", ""])
    
    # Contenu
    for section, content in report['content'].items():
        lines.extend([
            f"## {section}",
            "",
            content,
            "",
            "---",
            ""
        ])
    
    # Métadonnées
    lines.extend([
        "",
        "## Métadonnées",
        "",
        f"- **Mots :** {report['metadata']['word_count']:,}",
        f"- **Pages estimées :** {report['metadata']['page_estimate']}",
        f"- **Temps de lecture :** {report['metadata']['reading_time']} minutes",
        f"- **Modèles IA :** {', '.join(report['metadata'].get('ai_models_used', []))}",
        f"- **Généré le :** {report['metadata']['generation_time'].strftime('%d/%m/%Y à %H:%M')}"
    ])
    
    return "\n".join(lines)

def use_custom_template(template):
    """Utilise un template personnalisé"""
    st.session_state.selected_custom_template = template
    st.info(f"Template '{template['name']}' sélectionné")
    st.rerun()

def edit_custom_template(template_id, template):
    """Édite un template personnalisé"""
    st.session_state.editing_template = template_id
    st.info("Mode édition activé pour ce template")
    # L'interface d'édition serait implémentée ici

# Point d'entrée principal
if __name__ == "__main__":
    run()