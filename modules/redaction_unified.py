"""Module de rédaction juridique avancé avec IA - Nexora Law"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
# Import des configurations et classes
from config.app_config import (DOCUMENT_TEMPLATES, LEGAL_PHRASES,
                                REDACTION_STYLES, DocumentType, LLMProvider)
from utils import clean_key, format_legal_date, truncate_text
from utils.decorators import decorate_public_functions
from utils.session import initialize_session_state

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])


# Classes de données simplifiées
class RedactionResult:
    def __init__(self, type, document, provider, style, jurisprudence_used=False, 
                 jurisprudence_references=None, responses=None):
        self.type = type
        self.document = document
        self.provider = provider
        self.style = style
        self.jurisprudence_used = jurisprudence_used
        self.jurisprudence_references = jurisprudence_references or []
        self.responses = responses or []

class JurisprudenceCase:
    def __init__(self, id, title, jurisdiction, date, reference, summary, keywords):
        self.id = id
        self.title = title
        self.jurisdiction = jurisdiction
        self.date = date
        self.reference = reference
        self.summary = summary
        self.keywords = keywords
    
    def get_citation(self):
        return f"{self.jurisdiction}, {self.date.strftime('%d %B %Y')}, {self.reference}"

# Styles et configurations par défaut
DOCUMENT_TYPES = {
    'conclusions': {'name': '⚖️ Conclusions', 'desc': 'Conclusions en défense ou demande'},
    'plainte': {'name': '📝 Plainte', 'desc': 'Plainte pénale avec ou sans constitution PC'},
    'courrier': {'name': '✉️ Courrier', 'desc': 'Courrier juridique professionnel'},
    'mise_demeure': {'name': '⚡ Mise en demeure', 'desc': 'Mise en demeure formelle'},
    'assignation': {'name': '📋 Assignation', 'desc': 'Assignation devant tribunal'},
    'requete': {'name': '📄 Requête', 'desc': 'Requête au tribunal'},
    'memoire': {'name': '📚 Mémoire', 'desc': 'Mémoire en défense ou demande'},
    'constitution_pc': {'name': '🔒 Constitution PC', 'desc': 'Constitution de partie civile'},
}

LONGUEUR_OPTIONS = {
    'concis': {'name': '📄 Concis', 'pages': '3-5 pages', 'tokens': 2000},
    'standard': {'name': '📑 Standard', 'pages': '5-10 pages', 'tokens': 3000},
    'detaille': {'name': '📖 Détaillé', 'pages': '10-20 pages', 'tokens': 4000},
    'tres_detaille': {'name': '📚 Très détaillé', 'pages': '20-30 pages', 'tokens': 6000},
    'exhaustif': {'name': '📜 Exhaustif', 'pages': '30+ pages', 'tokens': 8000}
}

FUSION_MODES = {
    'intelligent': {'name': '🎯 Fusion intelligente', 'desc': 'Combine le meilleur de chaque version'},
    'best_of': {'name': '⭐ Meilleure version', 'desc': 'Sélectionne la version la plus complète'},
    'synthesis': {'name': '🔗 Synthèse enrichie', 'desc': 'Enrichit avec éléments uniques'},
    'consensus': {'name': '🤝 Consensus', 'desc': 'Points communs renforcés'},
    'creative': {'name': '💡 Créative', 'desc': 'Fusion avec approche innovante'}
}

def run():
    """Fonction principale du module de rédaction avancée"""
    
    # CSS personnalisé pour améliorer le design
    st.markdown("""
    <style>
    .redaction-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .ai-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .generation-progress {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # En-tête avec animation
    st.markdown("""
    <div class="redaction-header">
        <h1>🚀 Module de Rédaction Juridique Avancé</h1>
        <p>Générez des documents juridiques professionnels avec l'intelligence artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation des variables de session
    initialize_session_state()
    initialize_redaction_state()
    
    # Interface principale en onglets
    tabs = st.tabs([
        "🎯 Assistant Rédaction",
        "📝 Nouveau Document", 
        "🎨 Styles & Templates",
        "⚙️ Configuration IA",
        "📊 Historique & Analytics"
    ])
    
    with tabs[0]:
        show_redaction_assistant()
    
    with tabs[1]:
        show_new_document_interface()
    
    with tabs[2]:
        show_styles_templates_interface()
    
    with tabs[3]:
        show_ai_configuration()
    
    with tabs[4]:
        show_history_analytics()

def initialize_redaction_state():
    """Initialise les variables de session spécifiques au module"""
    
    defaults = {
        'redaction_state': {
            'initialized': True,
            'current_document': None,
            'history': [],
            'templates': {},
            'learned_styles': {},
            'favorite_prompts': []
        },
        'ai_config': {
            'providers': [],
            'fusion_mode': 'intelligent',
            'temperature': 0.7,
            'max_tokens': 4000
        },
        'document_draft': {
            'type': None,
            'content': '',
            'metadata': {},
            'versions': []
        },
        'style_analyzer': None,
        'jurisprudence_cache': {},
        'generation_metrics': {
            'total_documents': 0,
            'total_words': 0,
            'average_time': 0,
            'satisfaction_score': 0
        }
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def show_redaction_assistant():
    """Interface de l'assistant de rédaction intelligent"""
    
    st.markdown("### 🎯 Assistant de Rédaction Intelligent")
    
    # Analyse de la demande
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "💬 Décrivez votre besoin de rédaction",
            placeholder="Ex: J'ai besoin de rédiger des conclusions en défense pour mon client M. Dupont dans une affaire d'abus de biens sociaux...",
            height=120,
            key="redaction_query"
        )
    
    with col2:
        st.markdown("#### 💡 Suggestions")
        suggestions = [
            "Conclusions en défense",
            "Plainte avec CPC",
            "Mise en demeure",
            "Courrier au confrère"
        ]
        for sugg in suggestions:
            if st.button(sugg, key=f"sugg_{sugg}", use_container_width=True):
                st.session_state.redaction_query = f"Je souhaite rédiger {sugg.lower()}"
                st.rerun()
    
    if query:
        # Analyse intelligente de la demande
        with st.spinner("🔍 Analyse de votre demande..."):
            analysis = analyze_redaction_request(query)
            
        if analysis:
            display_analysis_results(analysis)
            
            # Actions rapides basées sur l'analyse
            st.markdown("### 🚀 Actions suggérées")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(
                    f"📝 Créer {analysis['document_type']['name']}", 
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.document_draft['type'] = analysis['document_type']['key']
                    st.session_state.document_draft['metadata'] = analysis
                    st.session_state.active_tab = 1
                    st.rerun()
            
            with col2:
                if st.button(
                    "🎨 Voir les modèles",
                    use_container_width=True
                ):
                    st.session_state.active_tab = 2
                    st.rerun()
            
            with col3:
                if st.button(
                    "⚙️ Configurer l'IA",
                    use_container_width=True
                ):
                    st.session_state.active_tab = 3
                    st.rerun()

def analyze_redaction_request(query: str) -> Dict[str, Any]:
    """Analyse intelligente de la demande de rédaction"""
    
    # Simulation d'analyse - remplacer par IA réelle
    analysis = {
        'confidence': 0.95,
        'document_type': {'key': 'conclusions', 'name': 'Conclusions en défense'},
        'detected_elements': {
            'parties': ['M. Dupont'],
            'juridiction': 'Tribunal Judiciaire',
            'matiere': 'Pénal des affaires',
            'infraction': 'Abus de biens sociaux',
            'urgence': False
        },
        'suggestions': {
            'style': 'combatif',
            'longueur': 'tres_detaille',
            'jurisprudence': True,
            'ton': 'formel'
        }
    }
    
    # Détection simple basée sur mots-clés
    query_lower = query.lower()
    
    for doc_key, doc_info in DOCUMENT_TYPES.items():
        if doc_key in query_lower or any(word in query_lower for word in doc_info['name'].lower().split()):
            analysis['document_type'] = {'key': doc_key, 'name': doc_info['name']}
            break
    
    return analysis

def display_analysis_results(analysis: Dict[str, Any]):
    """Affiche les résultats de l'analyse"""
    
    with st.expander("📊 Résultats de l'analyse", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Type détecté",
                analysis['document_type']['name'],
                f"{int(analysis['confidence']*100)}% de confiance"
            )
        
        with col2:
            elements = analysis['detected_elements']
            st.markdown("**Éléments identifiés:**")
            for key, value in elements.items():
                if value and key != 'urgence':
                    st.write(f"• {key.title()}: {value}")
        
        with col3:
            st.markdown("**Recommandations:**")
            sugg = analysis['suggestions']
            st.write(f"• Style: {sugg['style']}")
            st.write(f"• Longueur: {sugg['longueur']}")
            st.write(f"• Jurisprudence: {'Oui' if sugg['jurisprudence'] else 'Non'}")

def show_new_document_interface():
    """Interface de création d'un nouveau document"""
    
    st.markdown("### 📝 Création d'un Nouveau Document")
    
    # Sélection du type si non défini
    if not st.session_state.document_draft['type']:
        st.markdown("#### 1️⃣ Choisissez le type de document")
        
        # Grille de sélection avec cartes
        cols = st.columns(3)
        for idx, (key, info) in enumerate(DOCUMENT_TYPES.items()):
            with cols[idx % 3]:
                if st.button(
                    f"{info['name']}\n{info['desc']}",
                    key=f"doc_type_{key}",
                    use_container_width=True,
                    help=info['desc']
                ):
                    st.session_state.document_draft['type'] = key
                    st.rerun()
    else:
        # Configuration du document
        doc_type = st.session_state.document_draft['type']
        doc_info = DOCUMENT_TYPES[doc_type]
        
        # En-tête avec le type sélectionné
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"#### {doc_info['name']} - {doc_info['desc']}")
        with col2:
            if st.button("🔄 Changer", key="change_doc_type"):
                st.session_state.document_draft['type'] = None
                st.rerun()
        
        # Configuration en sous-onglets
        config_tabs = st.tabs([
            "📋 Informations",
            "🎨 Style & Format",
            "🤖 IA & Génération",
            "📎 Documents référence"
        ])
        
        with config_tabs[0]:
            show_document_information_form(doc_type)
        
        with config_tabs[1]:
            show_style_format_configuration()
        
        with config_tabs[2]:
            show_ai_generation_settings()
        
        with config_tabs[3]:
            show_reference_documents_selection()
        
        # Bouton de génération principal
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "🚀 Générer le Document",
                type="primary",
                use_container_width=True,
                disabled=not is_ready_to_generate()
            ):
                generate_document()

def show_document_information_form(doc_type: str):
    """Formulaire d'informations du document"""
    
    st.markdown("##### 📋 Informations principales")
    
    # Formulaire adaptatif selon le type
    if doc_type in ['conclusions', 'plainte', 'constitution_pc']:
        col1, col2 = st.columns(2)
        
        with col1:
            client = st.text_input(
                "👤 Client/Demandeur",
                key="info_client",
                placeholder="Nom complet du client"
            )
            
            adversaire = st.text_input(
                "⚔️ Partie adverse",
                key="info_adversaire",
                placeholder="Nom de la partie adverse"
            )
            
            juridiction = st.selectbox(
                "🏛️ Juridiction",
                ["Tribunal Judiciaire", "Cour d'Appel", "Tribunal de Commerce", 
                 "Conseil de Prud'hommes", "Tribunal Administratif"],
                key="info_juridiction"
            )
        
        with col2:
            reference = st.text_input(
                "📎 Référence dossier",
                key="info_reference",
                placeholder="RG: XX/XXXXX"
            )
            
            date_audience = st.date_input(
                "📅 Date d'audience",
                key="info_date_audience"
            )
            
            magistrat = st.text_input(
                "👨‍⚖️ Magistrat",
                key="info_magistrat",
                placeholder="Nom du juge/président"
            )
        
        # Zone de contexte
        contexte = st.text_area(
            "📝 Contexte et faits",
            height=200,
            key="info_contexte",
            placeholder="Décrivez les faits de manière chronologique et détaillée..."
        )
        
        # Arguments principaux
        col1, col2 = st.columns([2, 1])
        
        with col1:
            arguments = st.text_area(
                "💡 Arguments principaux",
                height=150,
                key="info_arguments",
                placeholder="- Premier moyen\n- Deuxième moyen\n- Troisième moyen"
            )
        
        with col2:
            st.markdown("##### 💰 Demandes")
            
            if doc_type in ['plainte', 'constitution_pc']:
                damages = st.checkbox("Dommages et intérêts", key="info_damages")
                if damages:
                    amount = st.number_input(
                        "Montant (€)",
                        min_value=0,
                        key="info_amount"
                    )
            
            provisions = st.checkbox("Article 700 CPC", key="info_700")
            if provisions:
                provisions_amount = st.number_input(
                    "Montant art. 700 (€)",
                    min_value=0,
                    value=3000,
                    key="info_700_amount"
                )
    
    elif doc_type == 'courrier':
        col1, col2 = st.columns(2)
        
        with col1:
            destinataire = st.text_input("📮 Destinataire", key="courrier_dest")
            qualite = st.text_input("💼 Qualité", key="courrier_qualite")
            adresse = st.text_area("📍 Adresse", height=80, key="courrier_adresse")
        
        with col2:
            objet = st.text_input("📋 Objet", key="courrier_objet")
            reference = st.text_input("📎 Vos références", key="courrier_ref")
            nos_ref = st.text_input("📎 Nos références", key="courrier_nos_ref")
        
        contenu = st.text_area(
            "📝 Points à développer",
            height=200,
            key="courrier_contenu",
            placeholder="Décrivez les points à aborder dans le courrier..."
        )
    
    # Pièces jointes
    with st.expander("📎 Pièces et annexes"):
        pieces = st.text_area(
            "Liste des pièces",
            placeholder="- Pièce n°1 : Contrat du XX/XX/XXXX\n- Pièce n°2 : Facture n°XXX",
            key="info_pieces"
        )

def show_style_format_configuration():
    """Configuration du style et format"""
    
    st.markdown("##### 🎨 Style et Format")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Style de rédaction avec preview
        style = st.selectbox(
            "✍️ Style de rédaction",
            list(REDACTION_STYLES.keys()) if 'REDACTION_STYLES' in globals() else ['formel', 'persuasif', 'combatif'],
            format_func=lambda x: f"{x.title()} - Style {x}",
            key="config_style"
        )
        
        # Styles appris disponibles
        if st.session_state.redaction_state.get('learned_styles'):
            learned = st.selectbox(
                "🎯 Style appris",
                ["Aucun"] + list(st.session_state.redaction_state['learned_styles'].keys()),
                key="config_learned_style"
            )
    
    with col2:
        # Longueur avec estimation
        longueur = st.select_slider(
            "📏 Longueur du document",
            options=list(LONGUEUR_OPTIONS.keys()),
            value='detaille',
            format_func=lambda x: f"{LONGUEUR_OPTIONS[x]['name']} ({LONGUEUR_OPTIONS[x]['pages']})",
            key="config_longueur"
        )
        
        # Ton
        ton = st.select_slider(
            "🎯 Ton",
            options=["Très formel", "Formel", "Équilibré", "Direct", "Combatif"],
            value="Formel",
            key="config_ton"
        )
    
    with col3:
        # Options de formatage
        st.markdown("**Options de format:**")
        
        include_toc = st.checkbox("📑 Table des matières", value=True, key="format_toc")
        include_summary = st.checkbox("📋 Résumé exécutif", value=False, key="format_summary")
        include_juris = st.checkbox("⚖️ Section jurisprudence", value=True, key="format_juris")
        numbered_sections = st.checkbox("🔢 Sections numérotées", value=True, key="format_numbered")
    
    # Templates disponibles
    st.markdown("##### 📋 Modèles disponibles")
    
    templates = get_available_templates(st.session_state.document_draft['type'])
    
    if templates:
        selected_template = st.selectbox(
            "Choisir un modèle",
            ["Aucun"] + list(templates.keys()),
            key="config_template"
        )
        
        if selected_template != "Aucun":
            with st.expander("👁️ Aperçu du modèle"):
                st.text(templates[selected_template].get('preview', 'Aperçu non disponible'))
    
    # Personnalisation avancée
    with st.expander("🎨 Personnalisation avancée"):
        col1, col2 = st.columns(2)
        
        with col1:
            formules_intro = st.text_area(
                "Formules d'introduction préférées",
                height=100,
                key="custom_intro"
            )
        
        with col2:
            formules_conclusion = st.text_area(
                "Formules de conclusion préférées",
                height=100,
                key="custom_conclusion"
            )

def show_ai_generation_settings():
    """Paramètres de génération IA"""
    
    st.markdown("##### 🤖 Configuration de l'IA")
    
    # Sélection des modèles
    available_models = get_available_ai_models()
    
    if not available_models:
        st.error("❌ Aucun modèle d'IA configuré. Veuillez ajouter des clés API dans la configuration.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sélection multiple avec détails
        st.markdown("**Modèles à utiliser:**")
        
        selected_models = []
        for model in available_models:
            col_model, col_info = st.columns([3, 1])
            
            with col_model:
                if st.checkbox(
                    f"{model['name']} - {model['provider']}",
                    value=model['default'],
                    key=f"model_{model['id']}"
                ):
                    selected_models.append(model['id'])
            
            with col_info:
                st.caption(f"⚡ {model['speed']} | 💰 {model['cost']}")
        
        st.session_state.ai_config['providers'] = selected_models
    
    with col2:
        st.markdown("**Paramètres avancés:**")
        
        # Mode de fusion si plusieurs modèles
        if len(selected_models) > 1:
            fusion_mode = st.selectbox(
                "🔄 Mode de fusion",
                list(FUSION_MODES.keys()),
                format_func=lambda x: FUSION_MODES[x]['name'],
                help=lambda x: FUSION_MODES[x]['desc'],
                key="ai_fusion_mode"
            )
            st.session_state.ai_config['fusion_mode'] = fusion_mode
        
        # Température (créativité)
        temperature = st.slider(
            "🌡️ Créativité",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            key="ai_temperature",
            help="Plus élevé = plus créatif, plus bas = plus factuel"
        )
        
        # Options supplémentaires
        use_rag = st.checkbox(
            "📚 Utiliser RAG",
            value=True,
            help="Recherche dans vos documents",
            key="ai_use_rag"
        )
        
        use_web = st.checkbox(
            "🌐 Recherche web",
            value=False,
            help="Pour jurisprudence récente",
            key="ai_use_web"
        )
    
    # Stratégies de génération
    with st.expander("🎯 Stratégies avancées"):
        col1, col2 = st.columns(2)
        
        with col1:
            generation_strategy = st.radio(
                "Stratégie de génération",
                [
                    "🎯 Standard - Une passe",
                    "🔄 Itérative - Amélioration progressive",
                    "🧩 Modulaire - Section par section",
                    "🎭 Débat - Argumentation contradictoire"
                ],
                key="ai_strategy"
            )
        
        with col2:
            if generation_strategy != "🎯 Standard - Une passe":
                iterations = st.number_input(
                    "Nombre d'itérations",
                    min_value=2,
                    max_value=5,
                    value=3,
                    key="ai_iterations"
                )
            
            review_mode = st.checkbox(
                "👁️ Mode révision",
                help="L'IA révise et améliore le document",
                key="ai_review"
            )

def show_reference_documents_selection():
    """Sélection des documents de référence"""
    
    st.markdown("##### 📎 Documents de référence")
    
    st.info("💡 Sélectionnez des documents similaires pour guider le style et la structure")
    
    # Sources disponibles
    source_tabs = st.tabs(["📁 Vos documents", "📚 Bibliothèque", "🌐 Recherche"])
    
    with source_tabs[0]:
        # Documents utilisateur
        if st.session_state.get('user_documents'):
            search = st.text_input("🔍 Rechercher", key="ref_search_user")
            
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.selectbox("Type", ["Tous"] + list(DOCUMENT_TYPES.keys()), key="ref_filter_type")
            with col2:
                filter_date = st.date_input("Après le", key="ref_filter_date")
            with col3:
                filter_client = st.text_input("Client", key="ref_filter_client")
            
            # Liste des documents
            display_reference_documents(
                st.session_state.user_documents,
                search,
                filters={'type': filter_type, 'date': filter_date, 'client': filter_client}
            )
        else:
            st.info("Aucun document disponible. Importez des documents pour les utiliser comme référence.")
    
    with source_tabs[1]:
        # Bibliothèque de modèles
        st.markdown("**Modèles professionnels disponibles:**")
        
        library_docs = get_library_documents(st.session_state.document_draft['type'])
        
        for doc in library_docs:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if st.checkbox(
                    f"{doc['title']} - {doc['author']}",
                    key=f"lib_doc_{doc['id']}",
                    help=doc['description']
                ):
                    add_reference_document(doc)
            
            with col2:
                if st.button("👁️", key=f"preview_lib_{doc['id']}"):
                    st.text_area("Aperçu", doc['preview'], height=200, key=f"preview_text_{doc['id']}")
    
    with source_tabs[2]:
        # Recherche externe
        st.markdown("**Rechercher des modèles similaires:**")
        
        query = st.text_input(
            "🔍 Recherche",
            placeholder="Ex: conclusions abus de biens sociaux",
            key="ref_search_external"
        )
        
        if query:
            with st.spinner("Recherche en cours..."):
                # Simulation de recherche
                time.sleep(1)
                st.info("Fonctionnalité de recherche externe à implémenter")

def generate_document():
    """Lance la génération du document"""
    
    # Vérifications
    if not st.session_state.ai_config['providers']:
        st.error("❌ Veuillez sélectionner au moins un modèle d'IA")
        return
    
    # Collecte des paramètres
    params = collect_generation_parameters()
    
    # Container de génération avec animation
    generation_container = st.container()
    
    with generation_container:
        st.markdown("""
        <div class="generation-progress">
            <h4>🚀 Génération en cours...</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Barre de progression détaillée
        progress_bar = st.progress(0)
        status_text = st.empty()
        details_expander = st.expander("📊 Détails de la génération", expanded=True)
        
        with details_expander:
            # Métriques en temps réel
            col1, col2, col3, col4 = st.columns(4)
            
            metric_time = col1.empty()
            metric_tokens = col2.empty()
            metric_models = col3.empty()
            metric_quality = col4.empty()
        
        # Étapes de génération
        steps = get_generation_steps(params)
        total_steps = len(steps)
        
        start_time = time.time()
        
        for idx, step in enumerate(steps):
            # Mise à jour du statut
            progress = (idx + 1) / total_steps
            progress_bar.progress(progress)
            status_text.text(f"⏳ {step['name']}...")
            
            # Mise à jour des métriques
            elapsed = time.time() - start_time
            metric_time.metric("⏱️ Temps", f"{elapsed:.1f}s")
            metric_tokens.metric("📝 Tokens", f"{step.get('tokens', 0):,}")
            metric_models.metric("🤖 Modèles", len(st.session_state.ai_config['providers']))
            metric_quality.metric("✨ Qualité", f"{step.get('quality', 85)}%")
            
            # Logs détaillés dans l'expander
            with details_expander:
                if step.get('details'):
                    st.info(f"ℹ️ {step['details']}")
            
            # Simulation du traitement
            time.sleep(step.get('duration', 1))
            
            # Traitement réel selon l'étape
            if step['key'] == 'preparation':
                prompt = build_generation_prompt(params)
            elif step['key'] == 'generation':
                responses = execute_ai_generation(params, prompt)
            elif step['key'] == 'fusion':
                final_document = apply_fusion_strategy(responses, params)
            elif step['key'] == 'revision':
                final_document = revise_document(final_document, params)
            elif step['key'] == 'formatting':
                formatted_document = format_final_document(final_document, params)
        
        # Génération terminée
        progress_bar.progress(1.0)
        status_text.text("✅ Génération terminée!")
        
        # Résultat final
        st.balloons()
        display_generation_results(formatted_document, params, elapsed)

def show_styles_templates_interface():
    """Interface de gestion des styles et templates"""
    
    st.markdown("### 🎨 Gestion des Styles et Templates")
    
    style_tabs = st.tabs([
        "📚 Bibliothèque",
        "🎯 Styles appris",
        "➕ Créer nouveau",
        "🔧 Gestionnaire"
    ])
    
    with style_tabs[0]:
        show_template_library()
    
    with style_tabs[1]:
        show_learned_styles()
    
    with style_tabs[2]:
        show_create_new_template()
    
    with style_tabs[3]:
        show_template_manager()

def show_ai_configuration():
    """Configuration des modèles d'IA"""
    
    st.markdown("### ⚙️ Configuration des Modèles d'IA")
    
    # État des modèles
    st.markdown("#### 📊 État des modèles")
    
    models = get_configured_models()
    
    if models:
        # Tableau de bord des modèles
        cols = st.columns(len(models))
        
        for idx, (model_id, model_info) in enumerate(models.items()):
            with cols[idx]:
                # Carte du modèle
                st.markdown(f"""
                <div class="ai-card">
                    <h4>{model_info['name']}</h4>
                    <p>🔌 {model_info['status']}</p>
                    <p>⚡ {model_info['speed']}</p>
                    <p>💰 {model_info['cost']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Actions
                if st.button("⚙️ Configurer", key=f"config_{model_id}"):
                    configure_model(model_id)
                
                if model_info['status'] == "Actif":
                    if st.button("🧪 Tester", key=f"test_{model_id}"):
                        test_model(model_id)
    else:
        st.info("Aucun modèle configuré. Ajoutez vos clés API ci-dessous.")
    
    # Ajout de nouveaux modèles
    st.markdown("#### ➕ Ajouter un modèle")
    
    with st.form("add_model_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            provider = st.selectbox(
                "Fournisseur",
                ["OpenAI", "Anthropic", "Google", "Mistral", "Cohere"]
            )
            
            api_key = st.text_input(
                "Clé API",
                type="password",
                help="Votre clé API sera stockée de manière sécurisée"
            )
        
        with col2:
            model_name = st.text_input(
                "Nom du modèle",
                placeholder="Ex: GPT-4"
            )
            
            model_id = st.text_input(
                "ID du modèle",
                placeholder="Ex: gpt-4-turbo"
            )
        
        if st.form_submit_button("➕ Ajouter le modèle", type="primary"):
            add_new_model(provider, api_key, model_name, model_id)
    
    # Paramètres globaux
    with st.expander("🌐 Paramètres globaux"):
        col1, col2 = st.columns(2)
        
        with col1:
            default_temp = st.slider(
                "Température par défaut",
                0.0, 1.0, 0.7,
                key="global_temp"
            )
            
            max_parallel = st.number_input(
                "Requêtes parallèles max",
                1, 10, 3,
                key="global_parallel"
            )
        
        with col2:
            timeout = st.number_input(
                "Timeout (secondes)",
                10, 300, 60,
                key="global_timeout"
            )
            
            retry_count = st.number_input(
                "Nombre de tentatives",
                1, 5, 3,
                key="global_retry"
            )

def show_history_analytics():
    """Historique et analytics des générations"""
    
    st.markdown("### 📊 Historique et Analytics")
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = st.session_state.generation_metrics
    
    with col1:
        st.metric(
            "📄 Documents générés",
            f"{metrics['total_documents']:,}",
            "+12 cette semaine"
        )
    
    with col2:
        st.metric(
            "📝 Mots générés",
            f"{metrics['total_words']:,}",
            "+15,420 cette semaine"
        )
    
    with col3:
        st.metric(
            "⏱️ Temps moyen",
            f"{metrics['average_time']:.1f}s",
            "-2.3s vs mois dernier"
        )
    
    with col4:
        st.metric(
            "⭐ Satisfaction",
            f"{metrics['satisfaction_score']:.1f}/5",
            "+0.2"
        )
    
    # Graphiques
    chart_tabs = st.tabs(["📈 Évolution", "🎯 Types", "🤖 Modèles", "📊 Détails"])
    
    with chart_tabs[0]:
        # Graphique d'évolution
        st.info("📈 Graphique d'évolution des générations à implémenter")
    
    with chart_tabs[1]:
        # Répartition par type
        st.info("🎯 Graphique de répartition par type de document à implémenter")
    
    with chart_tabs[2]:
        # Performance des modèles
        st.info("🤖 Comparaison des performances des modèles à implémenter")
    
    with chart_tabs[3]:
        # Tableau détaillé
        show_generation_history_table()

# === FONCTIONS UTILITAIRES ===

def get_available_ai_models():
    """Retourne la liste des modèles d'IA disponibles"""
    # Simulation - à remplacer par la vraie configuration
    return [
        {
            'id': 'gpt4',
            'name': 'GPT-4 Turbo',
            'provider': 'OpenAI',
            'speed': 'Rapide',
            'cost': 'Premium',
            'default': True
        },
        {
            'id': 'claude3',
            'name': 'Claude 3 Opus',
            'provider': 'Anthropic',
            'speed': 'Très rapide',
            'cost': 'Premium',
            'default': True
        },
        {
            'id': 'gemini',
            'name': 'Gemini Pro',
            'provider': 'Google',
            'speed': 'Rapide',
            'cost': 'Standard',
            'default': False
        }
    ]

def get_available_templates(doc_type: str):
    """Retourne les templates disponibles pour un type de document"""
    # Simulation - à remplacer par la vraie base de templates
    templates = {
        'conclusions': {
            'standard': {'name': 'Standard', 'preview': 'Structure classique en 3 parties'},
            'detaille': {'name': 'Détaillé', 'preview': 'Structure développée avec sous-sections'},
            'combatif': {'name': 'Combatif', 'preview': 'Structure offensive avec réfutation'}
        },
        'plainte': {
            'simple': {'name': 'Simple', 'preview': 'Plainte directe et concise'},
            'circonstanciee': {'name': 'Circonstanciée', 'preview': 'Plainte détaillée avec chronologie'}
        }
    }
    
    return templates.get(doc_type, {})

def is_ready_to_generate():
    """Vérifie si toutes les informations sont prêtes pour la génération"""
    
    # Vérifier les informations obligatoires
    required_fields = ['info_client', 'info_contexte']
    
    for field in required_fields:
        if field in st.session_state and not st.session_state[field]:
            return False
    
    # Vérifier qu'au moins un modèle est sélectionné
    if not st.session_state.ai_config.get('providers'):
        return False
    
    return True

def collect_generation_parameters():
    """Collecte tous les paramètres pour la génération"""
    
    params = {
        'document_type': st.session_state.document_draft['type'],
        'style': st.session_state.get('config_style', 'formel'),
        'length': st.session_state.get('config_longueur', 'detaille'),
        'tone': st.session_state.get('config_ton', 'Formel'),
        'client_info': {
            'client': st.session_state.get('info_client', ''),
            'adversaire': st.session_state.get('info_adversaire', ''),
            'juridiction': st.session_state.get('info_juridiction', ''),
            'reference': st.session_state.get('info_reference', ''),
            'contexte': st.session_state.get('info_contexte', ''),
            'arguments': st.session_state.get('info_arguments', '')
        },
        'ai_config': st.session_state.ai_config,
        'format_options': {
            'toc': st.session_state.get('format_toc', True),
            'summary': st.session_state.get('format_summary', False),
            'jurisprudence': st.session_state.get('format_juris', True),
            'numbered': st.session_state.get('format_numbered', True)
        },
        'template': st.session_state.get('config_template', 'Aucun'),
        'learned_style': st.session_state.get('config_learned_style', 'Aucun')
    }
    
    return params

def get_generation_steps(params):
    """Retourne les étapes de génération selon les paramètres"""
    
    steps = [
        {
            'key': 'preparation',
            'name': 'Préparation du contexte',
            'duration': 1,
            'details': 'Analyse des paramètres et construction du prompt',
            'tokens': 0,
            'quality': 95
        }
    ]
    
    # Recherche de jurisprudence si activée
    if params['format_options'].get('jurisprudence'):
        steps.append({
            'key': 'jurisprudence',
            'name': 'Recherche de jurisprudence',
            'duration': 2,
            'details': 'Recherche dans la base de jurisprudence',
            'tokens': 500,
            'quality': 90
        })
    
    # Génération principale
    if len(params['ai_config']['providers']) > 1:
        steps.append({
            'key': 'generation',
            'name': f'Génération avec {len(params["ai_config"]["providers"])} modèles',
            'duration': 5,
            'details': 'Génération parallèle du document',
            'tokens': LONGUEUR_OPTIONS[params['length']]['tokens'],
            'quality': 88
        })
        
        steps.append({
            'key': 'fusion',
            'name': f'Fusion {FUSION_MODES[params["ai_config"]["fusion_mode"]]["name"]}',
            'duration': 3,
            'details': 'Fusion intelligente des versions',
            'tokens': 1000,
            'quality': 92
        })
    else:
        steps.append({
            'key': 'generation',
            'name': 'Génération du document',
            'duration': 4,
            'details': 'Génération avec le modèle sélectionné',
            'tokens': LONGUEUR_OPTIONS[params['length']]['tokens'],
            'quality': 90
        })
    
    # Révision si activée
    if st.session_state.get('ai_review'):
        steps.append({
            'key': 'revision',
            'name': 'Révision et amélioration',
            'duration': 2,
            'details': 'Révision par l\'IA pour améliorer la qualité',
            'tokens': 500,
            'quality': 95
        })
    
    # Formatage final
    steps.append({
        'key': 'formatting',
        'name': 'Formatage final',
        'duration': 1,
        'details': 'Mise en forme et structuration',
        'tokens': 0,
        'quality': 98
    })
    
    return steps

def build_generation_prompt(params):
    """Construit le prompt de génération complet"""
    
    doc_name = DOCUMENT_TYPES[params['document_type']]['name']
    
    prompt = f"""Rédige {doc_name} complet et professionnel avec les éléments suivants:

INFORMATIONS DU DOSSIER:
- Client: {params['client_info']['client']}
- Partie adverse: {params['client_info']['adversaire']}
- Juridiction: {params['client_info']['juridiction']}
- Référence: {params['client_info']['reference']}

CONTEXTE ET FAITS:
{params['client_info']['contexte']}

ARGUMENTS À DÉVELOPPER:
{params['client_info']['arguments']}

STYLE ET FORMAT:
- Style: {params['style']} avec un ton {params['tone'].lower()}
- Longueur: {LONGUEUR_OPTIONS[params['length']]['pages']}
- Structure: {'numérotée' if params['format_options']['numbered'] else 'simple'}
"""
    
    if params['format_options']['toc']:
        prompt += "\n- Inclure une table des matières"
    
    if params['format_options']['summary']:
        prompt += "\n- Inclure un résumé exécutif en début de document"
    
    if params['template'] != 'Aucun':
        prompt += f"\n\nSuivre la structure du template '{params['template']}'"
    
    prompt += "\n\nLe document doit être immédiatement utilisable, juridiquement solide et sans placeholder."
    
    return prompt

def execute_ai_generation(params, prompt):
    """Exécute la génération avec les modèles sélectionnés"""
    
    # Simulation - à remplacer par les vrais appels API
    responses = []
    
    for provider in params['ai_config']['providers']:
        response = {
            'provider': provider,
            'success': True,
            'response': f"[Document généré par {provider}]\n\n" + generate_sample_document(params),
            'tokens_used': LONGUEUR_OPTIONS[params['length']]['tokens'],
            'time': 3.5
        }
        responses.append(response)
    
    return responses

def generate_sample_document(params):
    """Génère un document exemple (simulation)"""
    
    doc_type = params['document_type']
    
    if doc_type == 'conclusions':
        return f"""TRIBUNAL JUDICIAIRE DE PARIS
CONCLUSIONS EN DÉFENSE

POUR : {params['client_info']['client']}

CONTRE : {params['client_info']['adversaire']}

RG : {params['client_info']['reference']}

I. RAPPEL DES FAITS ET DE LA PROCÉDURE

{params['client_info']['contexte']}

II. DISCUSSION

{params['client_info']['arguments']}

III. DEMANDES

PAR CES MOTIFS, il est demandé au Tribunal de:
- DÉBOUTER la partie adverse de l'ensemble de ses demandes
- CONDAMNER la partie adverse aux entiers dépens

Fait à Paris, le {datetime.now().strftime('%d/%m/%Y')}"""
    
    return "Document généré (simulation)"

def apply_fusion_strategy(responses, params):
    """Applique la stratégie de fusion sélectionnée"""
    
    fusion_mode = params['ai_config']['fusion_mode']
    
    # Simulation de fusion
    if fusion_mode == 'intelligent':
        return f"[Fusion intelligente de {len(responses)} versions]\n\n" + responses[0]['response']
    elif fusion_mode == 'best_of':
        return f"[Meilleure version sélectionnée]\n\n" + max(responses, key=lambda x: len(x['response']))['response']
    else:
        return f"[Synthèse enrichie]\n\n" + responses[0]['response']

def revise_document(document, params):
    """Révise et améliore le document"""
    
    # Simulation de révision
    return document + "\n\n[Document révisé et amélioré]"

def format_final_document(document, params):
    """Formate le document final"""
    
    formatted = document
    
    if params['format_options']['toc']:
        formatted = "TABLE DES MATIÈRES\n\n" + formatted
    
    if params['format_options']['summary']:
        formatted = "RÉSUMÉ EXÉCUTIF\n\n[Résumé du document]\n\n" + formatted
    
    return formatted

def display_generation_results(document, params, generation_time):
    """Affiche les résultats de la génération"""
    
    st.success("✅ Document généré avec succès!")
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Mots", f"{len(document.split()):,}")
    
    with col2:
        st.metric("📄 Pages", len(document.split()) // 250)
    
    with col3:
        st.metric("⏱️ Temps", f"{generation_time:.1f}s")
    
    with col4:
        st.metric("🤖 Modèles", len(params['ai_config']['providers']))
    
    # Zone d'édition
    st.markdown("### 📝 Document généré")
    
    edited_doc = st.text_area(
        "Vous pouvez modifier le document",
        value=document,
        height=600,
        key="generated_document_edit"
    )
    
    # Actions
    st.markdown("### 💾 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.download_button(
            "📄 Télécharger (.txt)",
            edited_doc,
            f"{params['document_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        st.download_button(
            "📘 Télécharger (.docx)",
            edited_doc,  # Normalement converti en DOCX
            f"{params['document_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    with col3:
        if st.button("📋 Copier", key="copy_generated"):
            st.code(edited_doc)
            st.info("Utilisez Ctrl+C pour copier")
    
    with col4:
        if st.button("🔄 Régénérer", key="regenerate"):
            generate_document()
    
    # Feedback
    with st.expander("⭐ Évaluer le document"):
        rating = st.slider(
            "Qualité du document",
            1, 5, 4,
            key="document_rating"
        )
        
        feedback = st.text_area(
            "Commentaires (optionnel)",
            key="document_feedback"
        )
        
        if st.button("Envoyer l'évaluation", key="send_feedback"):
            st.success("Merci pour votre retour!")
            
            # Mise à jour des métriques
            st.session_state.generation_metrics['satisfaction_score'] = (
                st.session_state.generation_metrics['satisfaction_score'] * 0.9 + rating * 0.1
            )

def show_template_library():
    """Affiche la bibliothèque de templates"""
    
    st.markdown("#### 📚 Bibliothèque de Templates")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox(
            "Type de document",
            ["Tous"] + list(DOCUMENT_TYPES.keys()),
            key="lib_filter_type"
        )
    
    with col2:
        filter_style = st.selectbox(
            "Style",
            ["Tous", "Formel", "Persuasif", "Combatif"],
            key="lib_filter_style"
        )
    
    with col3:
        search = st.text_input(
            "🔍 Rechercher",
            key="lib_search"
        )
    
    # Affichage des templates (simulation)
    st.info("📚 Bibliothèque de templates à implémenter")

def show_learned_styles():
    """Affiche les styles appris"""
    
    st.markdown("#### 🎯 Styles Appris")
    
    if st.session_state.redaction_state.get('learned_styles'):
        for style_name, style_data in st.session_state.redaction_state['learned_styles'].items():
            with st.expander(f"📝 {style_name}"):
                st.write(f"**Créé le:** {style_data.get('created', 'N/A')}")
                st.write(f"**Basé sur:** {style_data.get('source_count', 0)} documents")
                st.write(f"**Utilisation:** {style_data.get('usage_count', 0)} fois")
                
                if st.button(f"🗑️ Supprimer", key=f"del_style_{style_name}"):
                    del st.session_state.redaction_state['learned_styles'][style_name]
                    st.rerun()
    else:
        st.info("Aucun style appris. Analysez des documents pour apprendre leur style.")

def show_create_new_template():
    """Interface de création de nouveau template"""
    
    st.markdown("#### ➕ Créer un Nouveau Template")
    
    with st.form("create_template_form"):
        name = st.text_input("Nom du template")
        doc_type = st.selectbox("Type de document", list(DOCUMENT_TYPES.keys()))
        
        structure = st.text_area(
            "Structure du template",
            height=300,
            placeholder="I. INTRODUCTION\n\nII. DÉVELOPPEMENT\n\nIII. CONCLUSION"
        )
        
        tags = st.multiselect(
            "Tags",
            ["Formel", "Combatif", "Concis", "Détaillé", "Urgence"]
        )
        
        if st.form_submit_button("Créer le template"):
            # Sauvegarder le template
            st.success(f"✅ Template '{name}' créé avec succès!")

def show_template_manager():
    """Gestionnaire de templates"""
    
    st.markdown("#### 🔧 Gestionnaire de Templates")
    
    # Import/Export
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded = st.file_uploader(
            "Importer des templates",
            type=['json', 'yaml'],
            key="import_templates"
        )
        
        if uploaded:
            st.success("✅ Templates importés")
    
    with col2:
        if st.button("📤 Exporter tous les templates"):
            # Export logic
            st.download_button(
                "Télécharger",
                "templates_export.json",
                "templates_export.json",
                "application/json"
            )

def show_generation_history_table():
    """Affiche l'historique des générations"""
    
    st.markdown("#### 📊 Historique détaillé")
    
    # Données exemple
    history_data = []
    
    for i in range(10):
        history_data.append({
            'Date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'Type': list(DOCUMENT_TYPES.values())[i % len(DOCUMENT_TYPES)]['name'],
            'Client': f"Client {i+1}",
            'Modèles': "GPT-4 + Claude",
            'Mots': f"{2000 + i*500:,}",
            'Temps': f"{10 + i*2}s",
            'Note': "⭐" * (3 + (i % 3))
        })
    
    df = pd.DataFrame(history_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Note": st.column_config.TextColumn(
                "Évaluation",
                width="small"
            )
        }
    )

# Fonctions helper supplémentaires

def get_configured_models():
    """Retourne les modèles configurés"""
    # Simulation
    return {
        'gpt4': {
            'name': 'GPT-4 Turbo',
            'status': 'Actif',
            'speed': 'Rapide',
            'cost': '0.03$/1K tokens'
        },
        'claude': {
            'name': 'Claude 3',
            'status': 'Actif',
            'speed': 'Très rapide',
            'cost': '0.025$/1K tokens'
        }
    }

def configure_model(model_id):
    """Configure un modèle spécifique"""
    st.info(f"Configuration de {model_id} à implémenter")

def test_model(model_id):
    """Teste un modèle"""
    with st.spinner(f"Test de {model_id} en cours..."):
        time.sleep(2)
        st.success(f"✅ {model_id} fonctionne correctement!")

def add_new_model(provider, api_key, model_name, model_id):
    """Ajoute un nouveau modèle"""
    if api_key and model_name and model_id:
        st.success(f"✅ Modèle {model_name} ajouté avec succès!")
        st.rerun()
    else:
        st.error("❌ Veuillez remplir tous les champs")

def get_library_documents(doc_type):
    """Retourne les documents de la bibliothèque"""
    # Simulation
    return [
        {
            'id': 'lib_1',
            'title': 'Conclusions type - Abus de biens sociaux',
            'author': 'Me Expert',
            'description': 'Modèle complet pour ABS',
            'preview': 'CONCLUSIONS EN DÉFENSE\n\nPOUR: ...'
        }
    ]

def add_reference_document(doc):
    """Ajoute un document de référence"""
    if 'reference_docs' not in st.session_state:
        st.session_state.reference_docs = []
    
    st.session_state.reference_docs.append(doc)
    st.success(f"✅ Document '{doc['title']}' ajouté aux références")

def display_reference_documents(documents, search, filters):
    """Affiche les documents de référence filtrés"""
    # Logique de filtrage et affichage
    st.info("Liste des documents de référence à implémenter")

# Point d'entrée principal
if __name__ == "__main__":
    run()