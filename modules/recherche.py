# modules/recherche.py
"""Module de recherche unifiée avec 100% des fonctionnalités intégrées"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
import re
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Any, Tuple
import io
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Imports des modules internes
from config.app_config import SearchMode, ANALYSIS_PROMPTS_AFFAIRES, LLMProvider
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from managers.multi_llm_manager import MultiLLMManager
from managers.document_manager import display_import_interface
from managers.dynamic_generators import generate_dynamic_search_prompts
from managers.legal_search import LegalSearchManager, display_legal_search_interface
from managers.jurisprudence_verifier import JurisprudenceVerifier
from models.dataclasses import Document, PieceSelectionnee
from utils.helpers import clean_key

# Configuration des styles de rédaction
REDACTION_STYLES = {
    'formel': {
        'name': 'Formel',
        'description': 'Style juridique classique et solennel',
        'tone': 'respectueux et distant',
        'vocabulary': 'technique et précis'
    },
    'persuasif': {
        'name': 'Persuasif',
        'description': 'Style argumentatif et convaincant',
        'tone': 'assertif et engagé',
        'vocabulary': 'percutant et imagé'
    },
    'technique': {
        'name': 'Technique',
        'description': 'Style factuel et détaillé',
        'tone': 'neutre et objectif',
        'vocabulary': 'spécialisé et exhaustif'
    },
    'synthétique': {
        'name': 'Synthétique',
        'description': 'Style concis et efficace',
        'tone': 'direct et clair',
        'vocabulary': 'simple et précis'
    },
    'pédagogique': {
        'name': 'Pédagogique',
        'description': 'Style explicatif et accessible',
        'tone': 'bienveillant et didactique',
        'vocabulary': 'vulgarisé et illustré'
    }
}

# Templates prédéfinis
DOCUMENT_TEMPLATES = {
    'conclusions_defense': {
        'name': 'Conclusions en défense',
        'structure': [
            'I. FAITS ET PROCÉDURE',
            'II. DISCUSSION',
            '   A. Sur la recevabilité',
            '   B. Sur le fond',
            '      1. Sur l\'élément matériel',
            '      2. Sur l\'élément intentionnel',
            '      3. Sur le préjudice',
            'III. PAR CES MOTIFS'
        ],
        'style': 'formel'
    },
    'plainte_simple': {
        'name': 'Plainte simple',
        'structure': [
            'Objet : Plainte',
            'EXPOSÉ DES FAITS',
            'QUALIFICATION JURIDIQUE',
            'PRÉJUDICES SUBIS',
            'DEMANDES',
            'PIÈCES JOINTES'
        ],
        'style': 'formel'
    },
    'plainte_avec_cpc': {
        'name': 'Plainte avec constitution de partie civile',
        'structure': [
            'Objet : Plainte avec constitution de partie civile',
            'EXPOSÉ DES FAITS',
            'QUALIFICATION JURIDIQUE',
            'PRÉJUDICES SUBIS',
            'CONSTITUTION DE PARTIE CIVILE',
            'ÉVALUATION DU PRÉJUDICE',
            'DEMANDES',
            'PIÈCES JOINTES'
        ],
        'style': 'formel'
    },
    'mise_en_demeure': {
        'name': 'Mise en demeure',
        'structure': [
            'MISE EN DEMEURE',
            'Rappel des faits',
            'Obligations non respectées',
            'Délai accordé',
            'Conséquences du défaut',
            'Réserves'
        ],
        'style': 'persuasif'
    },
    'note_synthese': {
        'name': 'Note de synthèse',
        'structure': [
            'SYNTHÈSE EXÉCUTIVE',
            'I. CONTEXTE',
            'II. ANALYSE',
            'III. RECOMMANDATIONS',
            'IV. PLAN D\'ACTION'
        ],
        'style': 'synthétique'
    }
}

def show_page():
    """Affiche la page de recherche unifiée complète"""
    
    # Initialiser l'historique si nécessaire
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'saved_templates' not in st.session_state:
        st.session_state.saved_templates = {}
    
    st.header("🔍 Centre de Commande Juridique IA")
    
    # BARRE DE RECHERCHE UNIVERSELLE
    show_universal_interface()
    
    # Quick actions si aucune requête
    if not st.session_state.get('universal_query'):
        show_quick_actions()
    
    # Onglets pour fonctionnalités spécialisées
    tabs = st.tabs([
        "📊 Résultats", 
        "📋 Pièces",
        "⚖️ Jurisprudence", 
        "📁 Explorateur",
        "⚙️ Configuration"
    ])
    
    with tabs[0]:
        show_unified_results_tab()
    
    with tabs[1]:
        show_pieces_management_tab()
    
    with tabs[2]:
        show_jurisprudence_tab()
    
    with tabs[3]:
        show_explorer_tab()
    
    with tabs[4]:
        show_configuration_tab()

def show_universal_interface():
    """Interface universelle de recherche et commande complète"""
    
    # Afficher l'historique si demandé
    if st.session_state.get('show_history', False):
        show_query_history_panel()
    
    st.markdown("""
    ### 🎯 Barre de Commande Universelle
    
    <style>
    .command-examples {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Exemples contextuels
    with st.expander("💡 Exemples de commandes", expanded=False):
        show_contextual_examples()
    
    # BARRE UNIVERSELLE avec autocomplétion
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "🎯 Que voulez-vous faire ?",
            value=st.session_state.get('universal_query', ''),
            placeholder="Ex: rédiger conclusions défense @affaire_martin abus de biens sociaux",
            key="universal_input",
            help="Recherche, analyse, rédaction, import, export, synthèse... Tout est possible !",
            on_change=on_query_change
        )
    
    with col2:
        # Bouton historique
        if st.button("📜", key="toggle_history", help="Historique des commandes"):
            st.session_state.show_history = not st.session_state.get('show_history', False)
            st.rerun()
    
    # Suggestions intelligentes
    if query and len(query) > 2:
        suggestions = get_smart_suggestions(query)
        if suggestions:
            st.markdown("**Suggestions :**")
            cols = st.columns(min(len(suggestions), 3))
            for i, (col, suggestion) in enumerate(zip(cols, suggestions[:3])):
                with col:
                    if st.button(f"→ {suggestion}", key=f"sugg_{i}"):
                        st.session_state.universal_query = suggestion
                        st.rerun()
    
    # ANALYSE EN TEMPS RÉEL
    if query:
        analysis = analyze_universal_query(query)
        display_universal_analysis(analysis)
        
        # Configuration contextuelle selon l'intention
        show_contextual_config(analysis)
    
    # DÉCLENCHEMENT AUTOMATIQUE
    if query and query != st.session_state.get('last_universal_query', ''):
        st.session_state.last_universal_query = query
        # Ajouter à l'historique
        add_to_history(query)
        process_universal_query(query)
    
    # BOUTONS D'ACTION
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🚀 Exécuter", type="primary", key="execute_universal", disabled=not query):
            if query:
                process_universal_query(query)
    
    with col2:
        if st.button("🗑️ Effacer", key="clear_universal"):
            clear_universal_state()
    
    with col3:
        if st.button("💾 Sauvegarder", key="save_universal"):
            save_current_work()
    
    with col4:
        if st.button("📤 Partager", key="share_universal"):
            share_current_work()
    
    with col5:
        if st.button("⚡ Actions", key="quick_actions"):
            st.session_state.show_quick_actions = not st.session_state.get('show_quick_actions', False)

def on_query_change():
    """Callback lors du changement de requête"""
    # Réinitialiser certains états si la requête change significativement
    new_query = st.session_state.get('universal_input', '')
    old_query = st.session_state.get('universal_query', '')
    
    if new_query != old_query:
        st.session_state.universal_query = new_query

def get_smart_suggestions(query: str) -> List[str]:
    """Génère des suggestions intelligentes basées sur la requête"""
    suggestions = []
    query_lower = query.lower()
    
    # Suggestions basées sur les mots-clés
    if 'rédiger' in query_lower and 'conclusions' not in query_lower:
        suggestions.append(f"{query} conclusions en défense")
    
    if '@' in query and ' ' not in query.split('@')[1]:
        # Suggérer des actions pour la référence
        ref = query.split('@')[1]
        suggestions.extend([
            f"{query} analyser les risques",
            f"{query} chronologie des faits",
            f"{query} cartographie des relations"
        ])
    
    if any(word in query_lower for word in ['comparer', 'différence']):
        suggestions.append(f"{query} entre les auditions")
    
    # Suggestions basées sur l'historique
    if 'query_history' in st.session_state:
        for hist_query in st.session_state.query_history[-5:]:
            if query_lower in hist_query.lower() and hist_query != query:
                suggestions.append(hist_query)
    
    return list(set(suggestions))[:5]  # Max 5 suggestions uniques

def show_contextual_examples():
    """Affiche des exemples contextuels de commandes"""
    examples = {
        "🔍 Recherche": [
            "contrats société XYZ",
            "@affaire_martin",
            "@dossier_2024 documents comptables"
        ],
        "🤖 Analyse": [
            "@affaire_martin analyser les risques pénaux",
            "@contrats identifier les clauses abusives",
            "analyser prescription @dossier_ancien"
        ],
        "📝 Rédaction": [
            "rédiger conclusions défense @affaire_martin abus de biens sociaux",
            "plainte avec constitution partie civile escroquerie @victime_x",
            "courrier mise en demeure @impayés_2024",
            "créer template conclusions"
        ],
        "📊 Visualisations": [
            "chronologie des faits @affaire_corruption",
            "cartographie des sociétés @groupe_abc",
            "comparer les auditions @témoins_affaire_x"
        ],
        "📋 Gestion": [
            "sélectionner pièces @dossier_pénal catégorie procédure",
            "créer bordereau @pièces_sélectionnées",
            "synthèse @documents_expertise"
        ],
        "📤 Communication": [
            "envoyer conclusions à avocat@example.com",
            "exporter @analyse_risques format word",
            "importer documents pdf @nouveau_dossier"
        ]
    }
    
    for category, cmds in examples.items():
        st.markdown(f"**{category}**")
        for cmd in cmds:
            st.code(cmd, language=None)

def analyze_universal_query(query: str) -> dict:
    """Analyse complète de la requête pour déterminer l'intention et les paramètres"""
    analysis = {
        'intent': 'search',
        'confidence': 0.0,
        'has_reference': False,
        'reference': None,
        'action': None,
        'document_type': None,
        'subject_matter': None,
        'parameters': {},
        'entities': [],
        'modifiers': [],
        'output_format': None,
        'style': None,
        'recipients': [],
        'details': {}
    }
    
    query_lower = query.lower()
    
    # 1. DÉTECTER LES RÉFÉRENCES
    if '@' in query:
        analysis['has_reference'] = True
        ref_matches = re.findall(r'@(\w+)', query)
        analysis['reference'] = ref_matches[0] if ref_matches else None
        analysis['entities'].extend(ref_matches)
    
    # 2. DÉTECTER L'INTENTION PRINCIPALE
    
    # Rédaction
    redaction_keywords = {
        'conclusions': ['conclusions', 'conclusion', 'défense', 'demande'],
        'plainte': ['plainte', 'porter plainte', 'dépôt plainte'],
        'constitution_pc': ['constitution partie civile', 'partie civile', 'constitution pc'],
        'courrier': ['courrier', 'lettre', 'correspondance', 'mise en demeure'],
        'assignation': ['assignation', 'assigner', 'citation'],
        'mémoire': ['mémoire', 'duplique', 'triplique', 'réplique'],
        'requête': ['requête', 'demande au juge', 'solliciter'],
        'transaction': ['transaction', 'protocole', 'accord'],
        'note': ['note', 'mémo', 'memorandum']
    }
    
    for doc_type, keywords in redaction_keywords.items():
        if any(kw in query_lower for kw in keywords):
            analysis['intent'] = 'redaction'
            analysis['document_type'] = doc_type
            analysis['confidence'] = 0.9
            break
    
    # Verbes d'action pour la rédaction
    if analysis['intent'] != 'redaction':
        redaction_verbs = ['rédiger', 'écrire', 'préparer', 'créer', 'composer', 'établir', 'formuler']
        if any(verb in query_lower for verb in redaction_verbs):
            analysis['intent'] = 'redaction'
            analysis['confidence'] = max(analysis['confidence'], 0.8)
    
    # Chronologie/Timeline
    if any(kw in query_lower for kw in ['chronologie', 'timeline', 'calendrier', 'historique', 'séquence']):
        analysis['intent'] = 'timeline'
        analysis['confidence'] = 0.9
        
        if any(kw in query_lower for kw in ['fait', 'événement']):
            analysis['details']['timeline_type'] = 'facts'
        elif any(kw in query_lower for kw in ['procédure', 'procédural', 'juridique']):
            analysis['details']['timeline_type'] = 'procedure'
        else:
            analysis['details']['timeline_type'] = 'general'
    
    # Cartographie/Mapping
    if any(kw in query_lower for kw in ['cartographie', 'mapping', 'carte', 'réseau', 'liens', 'relations']):
        analysis['intent'] = 'mapping'
        analysis['confidence'] = 0.9
        
        if any(kw in query_lower for kw in ['personne', 'individu']):
            analysis['details']['entity_type'] = 'persons'
        elif any(kw in query_lower for kw in ['société', 'entreprise', 'entité']):
            analysis['details']['entity_type'] = 'companies'
        else:
            analysis['details']['entity_type'] = 'all'
    
    # Comparaison
    if any(kw in query_lower for kw in ['comparer', 'comparaison', 'différence', 'convergence', 'contradiction']):
        analysis['intent'] = 'comparison'
        analysis['confidence'] = 0.9
        
        if any(kw in query_lower for kw in ['audition', 'déclaration', 'témoignage']):
            analysis['details']['comparison_type'] = 'auditions'
        else:
            analysis['details']['comparison_type'] = 'general'
    
    # Import/Export
    if any(kw in query_lower for kw in ['importer', 'import', 'télécharger', 'upload', 'charger']):
        analysis['intent'] = 'import'
        analysis['confidence'] = 0.9
        analysis['details']['file_types'] = detect_file_types(query_lower)
    
    if any(kw in query_lower for kw in ['exporter', 'export', 'téléchargement', 'download', 'extraire']):
        analysis['intent'] = 'export'
        analysis['confidence'] = 0.9
        analysis['details']['format'] = detect_export_format(query_lower)
    
    # Email/Envoi
    if any(kw in query_lower for kw in ['envoyer', 'email', 'mail', 'transmettre', 'adresser']):
        analysis['intent'] = 'send_email'
        analysis['confidence'] = 0.9
        # Extraire les emails
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, query)
        analysis['recipients'] = emails
    
    # Sélection de pièces
    if any(kw in query_lower for kw in ['sélectionner pièces', 'choisir pièces', 'organiser pièces', 'trier']):
        analysis['intent'] = 'piece_selection'
        analysis['confidence'] = 0.9
    
    # Bordereau
    if 'bordereau' in query_lower:
        analysis['intent'] = 'bordereau'
        analysis['confidence'] = 0.9
    
    # Synthèse
    if any(kw in query_lower for kw in ['synthèse', 'résumé', 'résumer', 'synthétiser', 'summary']):
        analysis['intent'] = 'synthesis'
        analysis['confidence'] = 0.9
    
    # Template
    if any(kw in query_lower for kw in ['template', 'modèle', 'gabarit', 'canevas']):
        analysis['intent'] = 'template'
        analysis['confidence'] = 0.8
        
        if 'créer' in query_lower or 'nouveau' in query_lower:
            analysis['details']['action'] = 'create'
        elif 'modifier' in query_lower or 'éditer' in query_lower:
            analysis['details']['action'] = 'edit'
        else:
            analysis['details']['action'] = 'apply'
    
    # Analyse IA
    if analysis['intent'] == 'search' and analysis['confidence'] < 0.7:
        analysis_keywords = ['analyser', 'analyse', 'évaluer', 'examiner', 'identifier', 'détecter']
        if any(kw in query_lower for kw in analysis_keywords):
            analysis['intent'] = 'analysis'
            analysis['confidence'] = 0.8
    
    # Jurisprudence
    if any(kw in query_lower for kw in ['jurisprudence', 'arrêt', 'décision', 'précédent']):
        if analysis['intent'] == 'search':
            analysis['intent'] = 'jurisprudence'
            analysis['confidence'] = 0.9
        else:
            analysis['modifiers'].append('with_jurisprudence')
    
    # 3. DÉTECTER LES PARAMÈTRES ADDITIONNELS
    
    # Style de rédaction
    for style_key, style_info in REDACTION_STYLES.items():
        if style_key in query_lower or style_info['name'].lower() in query_lower:
            analysis['style'] = style_key
    
    # Format de sortie
    formats = {
        'word': ['word', 'docx', 'doc'],
        'pdf': ['pdf'],
        'html': ['html', 'web'],
        'markdown': ['markdown', 'md'],
        'txt': ['txt', 'texte', 'text']
    }
    
    for format_name, keywords in formats.items():
        if any(kw in query_lower for kw in keywords):
            analysis['output_format'] = format_name
    
    # Infractions/sujets juridiques
    infractions = {
        'abus_biens_sociaux': ['abus de biens sociaux', 'abs', 'détournement actifs'],
        'escroquerie': ['escroquerie', 'tromperie', 'manœuvres frauduleuses'],
        'abus_confiance': ['abus de confiance', 'détournement fonds'],
        'faux': ['faux', 'usage de faux', 'falsification'],
        'corruption': ['corruption', 'trafic influence', 'prise illégale'],
        'blanchiment': ['blanchiment', 'dissimulation', 'recel'],
        'favoritisme': ['favoritisme', 'délit favoritisme', 'marchés publics'],
        'prise_illegale': ['prise illégale intérêts', 'conflit intérêts'],
        'harcelement': ['harcèlement', 'harcèlement moral', 'harcèlement sexuel'],
        'travail_dissimule': ['travail dissimulé', 'travail noir', 'dissimulation emploi']
    }
    
    for infraction, keywords in infractions.items():
        if any(kw in query_lower for kw in keywords):
            analysis['subject_matter'] = infraction
            analysis['details']['infraction'] = infraction
    
    # Urgence
    if any(kw in query_lower for kw in ['urgent', 'urgence', 'immédiat', 'rapidement', 'vite']):
        analysis['modifiers'].append('urgent')
    
    # Mode édition
    if any(kw in query_lower for kw in ['éditer', 'modifier', 'corriger', 'améliorer']):
        analysis['modifiers'].append('edit_mode')
    
    # Nombre d'IA pour traitement
    ia_count_match = re.search(r'(\d+)\s*ia', query_lower)
    if ia_count_match:
        analysis['parameters']['ai_count'] = int(ia_count_match.group(1))
    
    return analysis

def detect_file_types(query: str) -> List[str]:
    """Détecte les types de fichiers mentionnés"""
    file_types = []
    
    type_keywords = {
        'pdf': ['pdf'],
        'docx': ['word', 'docx', 'doc'],
        'txt': ['txt', 'texte', 'text'],
        'xlsx': ['excel', 'xlsx', 'xls'],
        'pptx': ['powerpoint', 'pptx', 'ppt'],
        'msg': ['email', 'msg', 'eml']
    }
    
    for file_type, keywords in type_keywords.items():
        if any(kw in query for kw in keywords):
            file_types.append(file_type)
    
    return file_types if file_types else ['pdf', 'docx', 'txt']

def detect_export_format(query: str) -> str:
    """Détecte le format d'export demandé"""
    if 'word' in query or 'docx' in query:
        return 'docx'
    elif 'pdf' in query:
        return 'pdf'
    elif 'excel' in query or 'xlsx' in query:
        return 'xlsx'
    elif 'html' in query:
        return 'html'
    else:
        return 'docx'  # Par défaut

def display_universal_analysis(analysis: dict):
    """Affiche l'analyse de la requête avec tous les détails"""
    
    # Icônes par intention
    intent_icons = {
        'search': '🔍 Recherche',
        'analysis': '🤖 Analyse',
        'redaction': '📝 Rédaction',
        'timeline': '⏱️ Chronologie',
        'mapping': '🗺️ Cartographie',
        'comparison': '🔄 Comparaison',
        'import': '📥 Import',
        'export': '📤 Export',
        'send_email': '📧 Email',
        'piece_selection': '📋 Sélection',
        'bordereau': '📊 Bordereau',
        'synthesis': '📝 Synthèse',
        'template': '📄 Template',
        'jurisprudence': '⚖️ Jurisprudence'
    }
    
    # Affichage principal
    cols = st.columns([2, 2, 1, 1])
    
    with cols[0]:
        st.info(intent_icons.get(analysis['intent'], '❓ Inconnu'))
    
    with cols[1]:
        if analysis['document_type']:
            doc_types = {
                'conclusions': '⚖️ Conclusions',
                'plainte': '📋 Plainte',
                'constitution_pc': '🛡️ Constitution PC',
                'courrier': '✉️ Courrier',
                'assignation': '📜 Assignation',
                'mémoire': '📚 Mémoire',
                'requête': '📄 Requête'
            }
            st.success(doc_types.get(analysis['document_type'], '📄 Document'))
    
    with cols[2]:
        if analysis['reference']:
            st.warning(f"🔗 @{analysis['reference']}")
    
    with cols[3]:
        # Indicateur de confiance
        confidence = analysis['confidence']
        color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
        st.caption(f"{color} {confidence:.0%}")
    
    # Détails supplémentaires
    if analysis['modifiers'] or analysis['parameters']:
        with st.expander("🔧 Paramètres détectés", expanded=False):
            if analysis['modifiers']:
                st.write(f"**Modificateurs :** {', '.join(analysis['modifiers'])}")
            if analysis['style']:
                st.write(f"**Style :** {REDACTION_STYLES[analysis['style']]['name']}")
            if analysis['output_format']:
                st.write(f"**Format :** {analysis['output_format'].upper()}")
            if analysis['recipients']:
                st.write(f"**Destinataires :** {', '.join(analysis['recipients'])}")
            if analysis['subject_matter']:
                st.write(f"**Sujet :** {analysis['subject_matter'].replace('_', ' ').title()}")

def show_contextual_config(analysis: dict):
    """Affiche la configuration contextuelle selon l'intention détectée"""
    
    if analysis['intent'] == 'redaction':
        show_redaction_config(analysis)
    
    elif analysis['intent'] == 'import':
        show_import_config(analysis)
    
    elif analysis['intent'] == 'export':
        show_export_config(analysis)
    
    elif analysis['intent'] == 'send_email':
        show_email_config(analysis)
    
    elif analysis['intent'] == 'template':
        show_template_config(analysis)
    
    elif analysis['intent'] in ['timeline', 'mapping', 'comparison']:
        show_visualization_config(analysis)

def show_redaction_config(analysis: dict = None):
    """Configuration pour la rédaction"""
    
    with st.expander("⚙️ Configuration de la rédaction", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Sélection des IA
            llm_manager = MultiLLMManager()
            available_llms = list(llm_manager.clients.keys()) if hasattr(llm_manager, 'clients') else []
            
            if available_llms:
                default_selection = min(2, len(available_llms))
                selected_llms = st.multiselect(
                    "🤖 IA pour la rédaction",
                    [llm.value if hasattr(llm, 'value') else str(llm) for llm in available_llms],
                    default=[llm.value if hasattr(llm, 'value') else str(llm) for llm in available_llms[:default_selection]],
                    key="redaction_llms",
                    help="Sélectionnez 1 à 4 IA"
                )
            else:
                st.warning("Aucune IA disponible")
                selected_llms = []
            
            # Style de rédaction
            current_style = analysis.get('style') if analysis else None
            style = st.selectbox(
                "✍️ Style de rédaction",
                list(REDACTION_STYLES.keys()),
                index=list(REDACTION_STYLES.keys()).index(current_style) if current_style else 0,
                format_func=lambda x: REDACTION_STYLES[x]['name'],
                key="redaction_style",
                help=REDACTION_STYLES[current_style]['description'] if current_style else None
            )
        
        with col2:
            # Mode de fusion
            fusion_mode = st.radio(
                "🔄 Mode de fusion IA",
                ["Maximum d'arguments", "Consensus", "Meilleur score"],
                key="fusion_mode",
                help="Comment combiner les réponses des différentes IA"
            )
            
            # Template
            use_template = st.checkbox("📄 Utiliser un template", value=True, key="use_template")
            if use_template:
                template_name = st.selectbox(
                    "Template",
                    list(DOCUMENT_TEMPLATES.keys()),
                    format_func=lambda x: DOCUMENT_TEMPLATES[x]['name'],
                    key="template_choice"
                )
        
        with col3:
            # Options avancées
            st.checkbox("⚖️ Recherche auto jurisprudence", value=True, key="auto_juris")
            st.checkbox("🔗 Ajouter hyperliens", value=True, key="add_hyperlinks")
            st.checkbox("📚 Citer les sources", value=True, key="cite_sources")
            st.checkbox("📊 Structurer en sections", value=True, key="structure_sections")
            st.checkbox("✏️ Mode édition après", value=False, key="edit_after")
            
            # Urgence
            if analysis and 'urgent' in analysis.get('modifiers', []):
                st.warning("⚡ Mode urgent activé")

def show_import_config(analysis: dict):
    """Configuration pour l'import"""
    
    with st.expander("📥 Configuration de l'import", expanded=True):
        file_types = analysis['details'].get('file_types', ['pdf', 'docx', 'txt'])
        
        uploaded_files = st.file_uploader(
            "Glissez vos fichiers ici",
            type=file_types,
            accept_multiple_files=True,
            key="import_files",
            help=f"Types acceptés : {', '.join(file_types)}"
        )
        
        if uploaded_files:
            col1, col2 = st.columns(2)
            
            with col1:
                destination = st.selectbox(
                    "Destination",
                    ["Documents locaux", "Azure Blob", "Nouveau dossier"],
                    key="import_destination"
                )
            
            with col2:
                if destination == "Nouveau dossier":
                    folder_name = st.text_input(
                        "Nom du dossier",
                        value=f"import_{datetime.now().strftime('%Y%m%d')}",
                        key="import_folder_name"
                    )
            
            auto_analyze = st.checkbox(
                "🤖 Analyser automatiquement après import",
                value=True,
                key="auto_analyze_import"
            )

def show_export_config(analysis: dict):
    """Configuration pour l'export"""
    
    with st.expander("📤 Configuration de l'export", expanded=True):
        format = analysis['details'].get('format', 'docx')
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Format d'export",
                ['docx', 'pdf', 'txt', 'html', 'xlsx'],
                index=['docx', 'pdf', 'txt', 'html', 'xlsx'].index(format),
                key="export_format"
            )
            
            include_metadata = st.checkbox(
                "Inclure métadonnées",
                value=True,
                key="export_metadata"
            )
        
        with col2:
            if export_format == 'pdf':
                st.checkbox("En-tête personnalisé", key="pdf_header")
                st.checkbox("Numérotation pages", value=True, key="pdf_page_numbers")
            
            elif export_format == 'docx':
                st.checkbox("Table des matières", value=True, key="docx_toc")
                st.checkbox("Styles personnalisés", key="docx_custom_styles")

def show_email_config(analysis: dict):
    """Configuration pour l'envoi d'email"""
    
    with st.expander("📧 Configuration de l'email", expanded=True):
        recipients = analysis.get('recipients', [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            to_email = st.text_input(
                "Destinataire(s)",
                value=', '.join(recipients),
                key="email_to",
                help="Séparez les adresses par des virgules"
            )
            
            cc_email = st.text_input(
                "Cc",
                key="email_cc"
            )
            
            subject = st.text_input(
                "Objet",
                value=extract_email_subject(st.session_state.get('universal_query', '')),
                key="email_subject"
            )
        
        with col2:
            attach_current = st.checkbox(
                "Joindre le document actuel",
                value=True,
                key="email_attach_current"
            )
            
            if attach_current:
                attachment_format = st.selectbox(
                    "Format de la pièce jointe",
                    ['pdf', 'docx', 'txt'],
                    key="email_attachment_format"
                )
            
            signature = st.checkbox(
                "Ajouter signature",
                value=True,
                key="email_signature"
            )

def show_template_config(analysis: dict):
    """Configuration pour les templates"""
    
    action = analysis['details'].get('action', 'apply')
    
    with st.expander("📄 Configuration des templates", expanded=True):
        if action == 'create':
            col1, col2 = st.columns(2)
            
            with col1:
                template_name = st.text_input(
                    "Nom du template",
                    key="new_template_name"
                )
                
                base_template = st.selectbox(
                    "Basé sur",
                    ["Vide"] + list(DOCUMENT_TEMPLATES.keys()),
                    format_func=lambda x: x if x == "Vide" else DOCUMENT_TEMPLATES[x]['name'],
                    key="base_template"
                )
            
            with col2:
                template_category = st.selectbox(
                    "Catégorie",
                    ["Procédure", "Correspondance", "Analyse", "Autre"],
                    key="template_category"
                )
                
                is_public = st.checkbox(
                    "Template public",
                    value=False,
                    key="template_public",
                    help="Les templates publics sont visibles par tous les utilisateurs"
                )
        
        elif action == 'edit':
            template_to_edit = st.selectbox(
                "Template à modifier",
                list(st.session_state.get('saved_templates', {}).keys()) + list(DOCUMENT_TEMPLATES.keys()),
                key="template_to_edit"
            )
        
        else:  # apply
            available_templates = list(DOCUMENT_TEMPLATES.keys()) + list(st.session_state.get('saved_templates', {}).keys())
            selected_template = st.selectbox(
                "Sélectionner un template",
                available_templates,
                format_func=lambda x: DOCUMENT_TEMPLATES.get(x, {}).get('name', x),
                key="selected_template"
            )

def show_visualization_config(analysis: dict):
    """Configuration pour les visualisations"""
    
    with st.expander("📊 Configuration de la visualisation", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if analysis['intent'] == 'timeline':
                timeline_type = st.radio(
                    "Type de chronologie",
                    ["Faits", "Procédure", "Mixte"],
                    key="timeline_viz_type"
                )
                
                date_format = st.selectbox(
                    "Format des dates",
                    ["JJ/MM/AAAA", "MM/JJ/AAAA", "AAAA-MM-JJ"],
                    key="timeline_date_format"
                )
            
            elif analysis['intent'] == 'mapping':
                layout_type = st.selectbox(
                    "Type de disposition",
                    ["Force-directed", "Hiérarchique", "Circulaire", "Kamada-Kawai"],
                    key="mapping_layout"
                )
                
                show_labels = st.checkbox(
                    "Afficher les labels",
                    value=True,
                    key="mapping_labels"
                )
            
            elif analysis['intent'] == 'comparison':
                comparison_view = st.radio(
                    "Vue de comparaison",
                    ["Côte à côte", "Unifié", "Tableau"],
                    key="comparison_view"
                )
                
                highlight_differences = st.checkbox(
                    "Surligner les différences",
                    value=True,
                    key="comparison_highlight"
                )
        
        with col2:
            color_scheme = st.selectbox(
                "Palette de couleurs",
                ["Défaut", "Professionnel", "Contraste élevé", "Dégradé"],
                key="viz_color_scheme"
            )
            
            export_resolution = st.selectbox(
                "Résolution d'export",
                ["Standard", "HD", "4K"],
                key="viz_resolution"
            )
            
            interactive = st.checkbox(
                "Mode interactif",
                value=True,
                key="viz_interactive"
            )

def show_quick_actions():
    """Affiche les actions rapides"""
    st.markdown("### ⚡ Actions rapides")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**📝 Rédaction**")
        if st.button("Conclusions", key="qa_conclusions"):
            st.session_state.universal_query = "rédiger conclusions en défense"
            st.rerun()
        if st.button("Plainte", key="qa_plainte"):
            st.session_state.universal_query = "rédiger plainte avec constitution partie civile"
            st.rerun()
    
    with col2:
        st.markdown("**📊 Analyses**")
        if st.button("Chronologie", key="qa_timeline"):
            st.session_state.universal_query = "chronologie des faits"
            st.rerun()
        if st.button("Cartographie", key="qa_mapping"):
            st.session_state.universal_query = "cartographie des relations"
            st.rerun()
    
    with col3:
        st.markdown("**📋 Gestion**")
        if st.button("Import docs", key="qa_import"):
            st.session_state.universal_query = "importer documents pdf"
            st.rerun()
        if st.button("Bordereau", key="qa_bordereau"):
            st.session_state.universal_query = "créer bordereau"
            st.rerun()
    
    with col4:
        st.markdown("**🔍 Recherche**")
        if st.button("Jurisprudence", key="qa_juris"):
            st.session_state.universal_query = "rechercher jurisprudence"
            st.rerun()
        if st.button("Templates", key="qa_templates"):
            st.session_state.universal_query = "gérer templates"
            st.rerun()

def add_to_history(query: str):
    """Ajoute une requête à l'historique"""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # Éviter les doublons consécutifs
    if not st.session_state.query_history or st.session_state.query_history[-1] != query:
        st.session_state.query_history.append(query)
        
        # Limiter la taille de l'historique
        if len(st.session_state.query_history) > 100:
            st.session_state.query_history = st.session_state.query_history[-100:]

def show_query_history_panel():
    """Affiche le panneau d'historique des requêtes"""
    with st.sidebar:
        st.markdown("### 📜 Historique des commandes")
        
        if st.session_state.get('query_history'):
            # Recherche dans l'historique
            search_history = st.text_input(
                "Filtrer l'historique",
                key="history_search",
                placeholder="Rechercher..."
            )
            
            # Filtrer l'historique
            history = st.session_state.query_history[::-1]  # Plus récent en premier
            if search_history:
                history = [q for q in history if search_history.lower() in q.lower()]
            
            # Afficher l'historique
            for i, query in enumerate(history[:20]):  # Limiter à 20
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if st.button(
                        f"📝 {query[:50]}..." if len(query) > 50 else f"📝 {query}",
                        key=f"hist_{i}",
                        help=query
                    ):
                        st.session_state.universal_query = query
                        st.session_state.show_history = False
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_hist_{i}"):
                        st.session_state.query_history.remove(query)
                        st.rerun()
            
            # Actions sur l'historique
            if st.button("🗑️ Effacer tout l'historique", key="clear_all_history"):
                st.session_state.query_history = []
                st.rerun()
            
            if st.button("💾 Exporter l'historique", key="export_history"):
                export_history()
        else:
            st.info("Aucun historique disponible")

def export_history():
    """Exporte l'historique des requêtes"""
    history_text = "\n".join([
        f"{i+1}. {query}"
        for i, query in enumerate(st.session_state.query_history)
    ])
    
    st.download_button(
        "💾 Télécharger",
        history_text,
        f"historique_commandes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
        key="download_history"
    )

def extract_email_subject(query: str) -> str:
    """Extrait ou génère un objet d'email depuis la requête"""
    # Chercher un pattern "objet: ..."
    subject_match = re.search(r'objet\s*:\s*([^,\n]+)', query, re.IGNORECASE)
    if subject_match:
        return subject_match.group(1).strip()
    
    # Générer un objet basé sur le contenu
    if 'conclusions' in query.lower():
        return "Conclusions en défense"
    elif 'plainte' in query.lower():
        return "Dépôt de plainte"
    elif 'mise en demeure' in query.lower():
        return "Mise en demeure"
    elif '@' in query:
        ref = query.split('@')[1].split()[0]
        return f"Dossier {ref}"
    else:
        return "Document juridique"

def process_universal_query(query: str):
    """Traite la requête universelle avec toutes les fonctionnalités"""
    analysis = analyze_universal_query(query)
    st.session_state.query_analysis = analysis
    
    with st.spinner("🔄 Traitement de votre demande..."):
        try:
            # Router vers la bonne fonction selon l'intention
            if analysis['intent'] == 'redaction':
                process_redaction_request(query, analysis)
            
            elif analysis['intent'] == 'timeline':
                process_timeline_request(query, analysis)
            
            elif analysis['intent'] == 'mapping':
                process_mapping_request(query, analysis)
            
            elif analysis['intent'] == 'comparison':
                process_comparison_request(query, analysis)
            
            elif analysis['intent'] == 'import':
                process_import_request(query, analysis)
            
            elif analysis['intent'] == 'export':
                process_export_request(query, analysis)
            
            elif analysis['intent'] == 'send_email':
                process_email_request(query, analysis)
            
            elif analysis['intent'] == 'piece_selection':
                process_piece_selection_request(query, analysis)
            
            elif analysis['intent'] == 'bordereau':
                process_bordereau_request(query, analysis)
            
            elif analysis['intent'] == 'synthesis':
                process_synthesis_request(query, analysis)
            
            elif analysis['intent'] == 'template':
                process_template_request(query, analysis)
            
            elif analysis['intent'] == 'jurisprudence':
                process_jurisprudence_request(query, analysis)
            
            elif analysis['intent'] == 'analysis':
                process_analysis_request(query, analysis)
            
            else:  # search
                process_search_request(query, analysis)
                
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement : {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# === FONCTIONS DE TRAITEMENT COMPLÈTES ===

def process_import_request(query: str, analysis: dict):
    """Traite une demande d'import de fichiers"""
    
    # Si des fichiers sont déjà uploadés
    if st.session_state.get('import_files'):
        files = st.session_state.import_files
        destination = st.session_state.get('import_destination', 'Documents locaux')
        
        imported_count = 0
        imported_docs = []
        
        for file in files:
            try:
                # Lire le contenu
                content = file.read()
                
                # Créer un document
                doc = Document(
                    id=f"import_{file.name}_{datetime.now().timestamp()}",
                    title=file.name,
                    content=content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else str(content),
                    source=f"Import {datetime.now().strftime('%d/%m/%Y')}",
                    metadata={
                        'file_type': file.type,
                        'file_size': file.size,
                        'import_date': datetime.now().isoformat()
                    }
                )
                
                # Stocker selon la destination
                if destination == "Documents locaux":
                    if 'azure_documents' not in st.session_state:
                        st.session_state.azure_documents = {}
                    st.session_state.azure_documents[doc.id] = doc
                    imported_docs.append(doc)
                    imported_count += 1
                
                elif destination == "Azure Blob":
                    # Upload vers Azure
                    blob_manager = st.session_state.get('azure_blob_manager')
                    if blob_manager and blob_manager.is_connected():
                        container = st.session_state.get('import_folder_name', 'imports')
                        # TODO: Implémenter upload_blob dans AzureBlobManager
                        st.info(f"Upload vers Azure: {file.name}")
                
            except Exception as e:
                st.error(f"Erreur import {file.name}: {str(e)}")
        
        # Résultat
        st.session_state.import_result = {
            'count': imported_count,
            'documents': imported_docs,
            'timestamp': datetime.now()
        }
        
        st.success(f"✅ {imported_count} fichiers importés avec succès")
        
        # Analyse automatique si demandée
        if st.session_state.get('auto_analyze_import') and imported_docs:
            st.info("🤖 Analyse automatique en cours...")
            analyze_imported_documents(imported_docs)
    
    else:
        st.info("📥 Utilisez le widget d'upload ci-dessus pour importer vos fichiers")

def analyze_imported_documents(documents: List[Document]):
    """Analyse automatique des documents importés"""
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        return
    
    analysis_prompt = """Analyse ces documents importés et fournis :
1. Type de document
2. Parties impliquées
3. Sujet principal
4. Points juridiques importants
5. Actions recommandées

Format structuré attendu."""
    
    for doc in documents[:5]:  # Limiter à 5
        context = f"Document : {doc.title}\n\n{doc.content[:2000]}"
        
        try:
            provider = list(llm_manager.clients.keys())[0]
            response = llm_manager.query_single_llm(
                provider,
                f"{analysis_prompt}\n\n{context}",
                "Tu es un expert en analyse documentaire juridique."
            )
            
            if response['success']:
                doc.metadata['ai_analysis'] = response['response']
                
        except Exception as e:
            print(f"Erreur analyse auto : {e}")

def process_export_request(query: str, analysis: dict):
    """Traite une demande d'export"""
    
    # Déterminer quoi exporter
    if analysis['reference']:
        # Exporter les documents de la référence
        documents = search_by_reference(f"@{analysis['reference']}")
        content_to_export = compile_documents_for_export(documents)
        filename_base = f"export_{analysis['reference']}"
    
    elif 'redaction_result' in st.session_state:
        # Exporter le dernier document rédigé
        content_to_export = st.session_state.redaction_result['document']
        filename_base = f"{st.session_state.redaction_result['type']}"
    
    elif 'analysis_results' in st.session_state:
        # Exporter les résultats d'analyse
        content_to_export = format_analysis_for_export(st.session_state.analysis_results)
        filename_base = "analyse"
    
    else:
        st.warning("⚠️ Aucun document à exporter")
        return
    
    # Format d'export
    export_format = st.session_state.get('export_format', analysis['details'].get('format', 'docx'))
    
    # Générer l'export
    export_data = generate_export(content_to_export, export_format, analysis)
    
    if export_data:
        filename = f"{filename_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        
        st.download_button(
            f"💾 Télécharger ({export_format.upper()})",
            export_data['content'],
            filename,
            export_data['mime_type'],
            key=f"download_export_{datetime.now().timestamp()}"
        )
        
        st.session_state.export_result = {
            'filename': filename,
            'format': export_format,
            'size': len(export_data['content']),
            'timestamp': datetime.now()
        }

def compile_documents_for_export(documents: list) -> str:
    """Compile plusieurs documents pour l'export"""
    content = f"EXPORT DE DOCUMENTS\n{'=' * 50}\n\n"
    content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    content += f"Nombre de documents : {len(documents)}\n\n"
    
    for i, doc in enumerate(documents, 1):
        content += f"\n{'=' * 50}\n"
        content += f"DOCUMENT {i} : {doc.get('title', 'Sans titre')}\n"
        content += f"Source : {doc.get('source', 'N/A')}\n"
        content += f"{'=' * 50}\n\n"
        content += doc.get('content', 'Contenu non disponible')
        content += "\n\n"
    
    return content

def generate_export(content: str, format: str, analysis: dict) -> dict:
    """Génère l'export dans le format demandé"""
    
    if format == 'txt':
        return {
            'content': content.encode('utf-8'),
            'mime_type': 'text/plain'
        }
    
    elif format == 'docx':
        try:
            import docx
            from io import BytesIO
            
            doc = docx.Document()
            
            # Ajouter métadonnées si demandé
            if st.session_state.get('export_metadata'):
                doc.add_heading('Métadonnées', level=1)
                doc.add_paragraph(f"Date d'export : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                doc.add_paragraph(f"Requête : {st.session_state.get('universal_query', 'N/A')}")
                doc.add_page_break()
            
            # Ajouter le contenu
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    # Détecter les titres
                    if paragraph.startswith('===') or paragraph.endswith('==='):
                        doc.add_heading(paragraph.replace('=', '').strip(), level=2)
                    elif paragraph.isupper() and len(paragraph.split()) < 10:
                        doc.add_heading(paragraph, level=1)
                    else:
                        doc.add_paragraph(paragraph)
            
            # Table des matières si demandée
            if st.session_state.get('docx_toc'):
                # TODO: Implémenter la génération de table des matières
                pass
            
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            return {
                'content': buffer.getvalue(),
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            
        except Exception as e:
            st.error(f"Erreur génération DOCX : {str(e)}")
            # Fallback vers TXT
            return generate_export(content, 'txt', analysis)
    
    elif format == 'pdf':
        # TODO: Implémenter l'export PDF avec reportlab ou weasyprint
        st.info("Export PDF en cours de développement, export en TXT")
        return generate_export(content, 'txt', analysis)
    
    elif format == 'html':
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Export Juridique</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #1a237e; }}
                h2 {{ color: #283593; }}
                .metadata {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <div class="metadata">
                <p>Export du {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            <div class="content">
                {content.replace('\n', '<br>')}
            </div>
        </body>
        </html>
        """
        
        return {
            'content': html_content.encode('utf-8'),
            'mime_type': 'text/html'
        }
    
    else:
        # Format non supporté
        return generate_export(content, 'txt', analysis)

def process_email_request(query: str, analysis: dict):
    """Traite une demande d'envoi d'email"""
    
    # Récupérer les paramètres
    recipients = st.session_state.get('email_to', '').split(',')
    cc = st.session_state.get('email_cc', '').split(',') if st.session_state.get('email_cc') else []
    subject = st.session_state.get('email_subject', extract_email_subject(query))
    
    # Déterminer le contenu à envoyer
    if 'redaction_result' in st.session_state:
        content = st.session_state.redaction_result['document']
        attachment_name = f"{st.session_state.redaction_result['type']}.docx"
    elif analysis['reference']:
        docs = search_by_reference(f"@{analysis['reference']}")
        content = compile_documents_for_export(docs)
        attachment_name = f"{analysis['reference']}.docx"
    else:
        content = "Document joint"
        attachment_name = "document.docx"
    
    # Préparer l'email
    email_draft = {
        'to': [email.strip() for email in recipients if email.strip()],
        'cc': [email.strip() for email in cc if email.strip()],
        'subject': subject,
        'body': f"""Bonjour,

Veuillez trouver ci-joint le document demandé.

{content[:500]}...

Cordialement,
[Votre nom]""",
        'attachments': []
    }
    
    # Ajouter pièce jointe si demandé
    if st.session_state.get('email_attach_current'):
        format = st.session_state.get('email_attachment_format', 'pdf')
        export_data = generate_export(content, format, analysis)
        
        if export_data:
            email_draft['attachments'].append({
                'filename': attachment_name.replace('.docx', f'.{format}'),
                'content': export_data['content'],
                'mime_type': export_data['mime_type']
            })
    
    # Interface de prévisualisation
    with st.expander("📧 Prévisualisation de l'email", expanded=True):
        st.write(f"**À :** {', '.join(email_draft['to'])}")
        if email_draft['cc']:
            st.write(f"**Cc :** {', '.join(email_draft['cc'])}")
        st.write(f"**Objet :** {email_draft['subject']}")
        st.text_area("Corps du message", email_draft['body'], height=200, key="email_body_preview")
        
        if email_draft['attachments']:
            st.write(f"**Pièces jointes :** {len(email_draft['attachments'])} fichier(s)")
            for att in email_draft['attachments']:
                st.write(f"- {att['filename']} ({len(att['content'])} octets)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Envoyer", type="primary", key="send_email_now"):
                if send_email(email_draft):
                    st.success("✅ Email envoyé avec succès")
                    st.session_state.email_sent = True
                else:
                    st.error("❌ Erreur lors de l'envoi")
        
        with col2:
            if st.button("💾 Sauvegarder comme brouillon", key="save_email_draft"):
                st.session_state.email_drafts = st.session_state.get('email_drafts', [])
                st.session_state.email_drafts.append(email_draft)
                st.success("✅ Brouillon sauvegardé")

def send_email(email_draft: dict) -> bool:
    """Envoie réellement l'email"""
    # TODO: Implémenter l'envoi réel via SMTP
    # Pour l'instant, simulation
    st.info("📧 Fonction d'envoi d'email à configurer avec vos paramètres SMTP")
    return False

def process_piece_selection_request(query: str, analysis: dict):
    """Traite une demande de sélection de pièces"""
    
    # Collecter les documents disponibles
    if analysis['reference']:
        available_docs = search_by_reference(f"@{analysis['reference']}")
    else:
        # Tous les documents
        available_docs = []
        
        # Documents locaux
        for doc_id, doc in st.session_state.get('azure_documents', {}).items():
            available_docs.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content[:500],
                'source': doc.source,
                'type': 'document'
            })
        
        # Ajouter documents Azure si disponibles
        blob_manager = st.session_state.get('azure_blob_manager')
        if blob_manager and blob_manager.is_connected():
            # TODO: Lister documents Azure
            pass
    
    # Interface de sélection
    st.markdown("### 📋 Sélection et organisation des pièces")
    
    # Catégories
    categories = extract_categories_from_query(query)
    if not categories:
        categories = ["📁 Procédure", "💰 Comptabilité", "📄 Contrats", "📧 Correspondances", "🔍 Autres"]
    
    selected_category = st.selectbox(
        "Catégorie",
        categories,
        key="piece_category"
    )
    
    # Table de sélection
    if available_docs:
        # Créer un DataFrame pour l'affichage
        import pandas as pd
        
        df_data = []
        for doc in available_docs:
            df_data.append({
                'Sélectionner': False,
                'Titre': doc['title'],
                'Source': doc['source'],
                'ID': doc['id']
            })
        
        df = pd.DataFrame(df_data)
        
        # Afficher avec sélection
        edited_df = st.data_editor(
            df,
            column_config={
                "Sélectionner": st.column_config.CheckboxColumn(
                    "✓",
                    help="Cocher pour sélectionner",
                    default=False,
                ),
                "Titre": st.column_config.TextColumn(
                    "Titre",
                    help="Titre du document",
                    width="medium",
                ),
                "Source": st.column_config.TextColumn(
                    "Source",
                    help="Source du document",
                    width="small",
                ),
                "ID": st.column_config.TextColumn(
                    "ID",
                    help="Identifiant unique",
                    width="small",
                    disabled=True,
                ),
            },
            disabled=["Titre", "Source", "ID"],
            hide_index=True,
            key="piece_selection_table"
        )
        
        # Actions sur la sélection
        selected_rows = edited_df[edited_df['Sélectionner']]
        
        if not selected_rows.empty:
            st.info(f"✅ {len(selected_rows)} pièce(s) sélectionnée(s)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Enregistrer sélection", key="save_piece_selection"):
                    save_piece_selection(selected_rows, selected_category)
            
            with col2:
                if st.button("📊 Créer bordereau", key="create_bordereau_from_selection"):
                    create_bordereau_from_selection(selected_rows, selected_category)
            
            with col3:
                if st.button("📤 Exporter sélection", key="export_piece_selection"):
                    export_piece_selection(selected_rows)
    else:
        st.warning("⚠️ Aucun document disponible pour la sélection")

def extract_categories_from_query(query: str) -> List[str]:
    """Extrait les catégories depuis la requête"""
    categories = []
    
    category_keywords = {
        "procédure": ["procédure", "procédural", "actes"],
        "comptabilité": ["comptabilité", "comptable", "financier", "comptes"],
        "contrats": ["contrat", "contractuel", "convention"],
        "correspondances": ["courrier", "lettre", "email", "correspondance"],
        "expertise": ["expertise", "expert", "rapport"],
        "pièces d'identité": ["identité", "kbis", "statuts"]
    }
    
    query_lower = query.lower()
    
    for cat, keywords in category_keywords.items():
        if any(kw in query_lower for kw in keywords):
            categories.append(f"📁 {cat.title()}")
    
    return categories

def save_piece_selection(selected_df, category: str):
    """Sauvegarde la sélection de pièces"""
    if 'pieces_selectionnees' not in st.session_state:
        st.session_state.pieces_selectionnees = {}
    
    for _, row in selected_df.iterrows():
        piece = PieceSelectionnee(
            document_id=row['ID'],
            titre=row['Titre'],
            categorie=category,
            notes=f"Sélectionné le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            pertinence=5,
            cote_bordereau=f"P-{len(st.session_state.pieces_selectionnees) + 1}"
        )
        
        st.session_state.pieces_selectionnees[row['ID']] = piece
    
    st.success(f"✅ {len(selected_df)} pièces ajoutées à la catégorie {category}")

def process_bordereau_request(query: str, analysis: dict):
    """Traite une demande de création de bordereau"""
    
    # Déterminer les pièces à inclure
    pieces = {}
    
    if analysis['reference']:
        # Pièces de la référence
        docs = search_by_reference(f"@{analysis['reference']}")
        for i, doc in enumerate(docs):
            pieces[doc['id']] = PieceSelectionnee(
                document_id=doc['id'],
                titre=doc['title'],
                categorie="Document",
                cote_bordereau=f"P-{i+1}"
            )
    else:
        # Pièces déjà sélectionnées
        pieces = st.session_state.get('pieces_selectionnees', {})
    
    if not pieces:
        st.warning("⚠️ Aucune pièce disponible pour créer le bordereau")
        return
    
    # Options du bordereau
    with st.expander("⚙️ Options du bordereau", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            bordereau_type = st.selectbox(
                "Type de bordereau",
                ["Communication de pièces", "Inventaire", "Production aux débats"],
                key="bordereau_type"
            )
            
            include_summary = st.checkbox(
                "Inclure résumé des pièces",
                value=True,
                key="bordereau_summary"
            )
        
        with col2:
            sort_by = st.selectbox(
                "Trier par",
                ["Cote", "Date", "Catégorie", "Titre"],
                key="bordereau_sort"
            )
            
            format_output = st.selectbox(
                "Format",
                ["Tableau", "Liste", "Détaillé"],
                key="bordereau_format"
            )
    
    # Générer le bordereau
    bordereau = generate_bordereau(pieces, {
        'type': bordereau_type,
        'include_summary': include_summary,
        'sort_by': sort_by,
        'format': format_output
    })
    
    # Afficher le bordereau
    st.markdown("### 📊 Bordereau généré")
    
    if format_output == "Tableau":
        display_bordereau_table(pieces)
    else:
        st.text_area(
            "Bordereau",
            bordereau,
            height=400,
            key="bordereau_preview"
        )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "💾 Télécharger",
            bordereau,
            f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain",
            key="download_bordereau"
        )
    
    with col2:
        if st.button("📧 Envoyer", key="send_bordereau"):
            st.session_state.universal_query = f"envoyer bordereau"
            st.rerun()
    
    with col3:
        if st.button("✏️ Éditer", key="edit_bordereau"):
            st.session_state.edit_bordereau = True

def generate_bordereau(pieces: dict, options: dict) -> str:
    """Génère le contenu du bordereau"""
    bordereau = f"BORDEREAU DE {options['type'].upper()}\n"
    bordereau += "=" * 60 + "\n\n"
    
    bordereau += f"Affaire : {st.session_state.get('current_case', 'N/A')}\n"
    bordereau += f"Date : {datetime.now().strftime('%d/%m/%Y')}\n"
    bordereau += f"Nombre de pièces : {len(pieces)}\n\n"
    
    bordereau += "-" * 60 + "\n"
    
    # Trier les pièces
    sorted_pieces = sorted(
        pieces.items(),
        key=lambda x: x[1].cote_bordereau if options['sort_by'] == 'Cote' else x[1].titre
    )
    
    # Format détaillé
    if options['format'] == 'Détaillé':
        for piece_id, piece in sorted_pieces:
            bordereau += f"\n{piece.cote_bordereau} - {piece.titre}\n"
            bordereau += f"   Catégorie : {piece.categorie}\n"
            
            if options['include_summary'] and hasattr(piece, 'notes'):
                bordereau += f"   Description : {piece.notes}\n"
            
            bordereau += "\n"
    
    # Format liste
    elif options['format'] == 'Liste':
        for piece_id, piece in sorted_pieces:
            bordereau += f"{piece.cote_bordereau} - {piece.titre}\n"
    
    # Format tableau (retourner comme texte tabulé)
    else:
        bordereau += f"{'Cote':<10} {'Titre':<50} {'Catégorie':<20}\n"
        bordereau += "-" * 80 + "\n"
        
        for piece_id, piece in sorted_pieces:
            bordereau += f"{piece.cote_bordereau:<10} {piece.titre[:50]:<50} {piece.categorie:<20}\n"
    
    return bordereau

def display_bordereau_table(pieces: dict):
    """Affiche le bordereau sous forme de tableau"""
    import pandas as pd
    
    data = []
    for piece_id, piece in pieces.items():
        data.append({
            'Cote': piece.cote_bordereau,
            'Titre': piece.titre,
            'Catégorie': piece.categorie,
            'Pertinence': piece.pertinence if hasattr(piece, 'pertinence') else 5
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Cote')
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pertinence": st.column_config.NumberColumn(
                "Pertinence",
                min_value=1,
                max_value=5,
                format="⭐ %d",
            )
        }
    )

def process_synthesis_request(query: str, analysis: dict):
    """Traite une demande de synthèse"""
    
    # Collecter les documents
    documents = []
    
    if analysis['reference']:
        documents = search_by_reference(f"@{analysis['reference']}")
    else:
        # Derniers documents analysés ou sélectionnés
        if 'search_results' in st.session_state:
            documents = st.session_state.search_results[:10]
        elif 'azure_documents' in st.session_state:
            documents = list(st.session_state.azure_documents.values())[:10]
    
    if not documents:
        st.warning("⚠️ Aucun document disponible pour la synthèse")
        return
    
    # Options de synthèse
    with st.expander("⚙️ Options de synthèse", expanded=True):
        synthesis_type = st.selectbox(
            "Type de synthèse",
            ["Executive summary", "Points clés", "Analyse SWOT", "Recommandations", "Chronologique"],
            key="synthesis_type"
        )
        
        max_length = st.slider(
            "Longueur maximale (mots)",
            100, 2000, 500,
            key="synthesis_length"
        )
        
        include_citations = st.checkbox(
            "Inclure citations",
            value=True,
            key="synthesis_citations"
        )
    
    # Générer la synthèse avec l'IA
    with st.spinner("🤖 Génération de la synthèse..."):
        synthesis = generate_synthesis_with_ai(documents, {
            'type': synthesis_type,
            'max_length': max_length,
            'include_citations': include_citations
        })
    
    if synthesis:
        st.markdown("### 📝 Synthèse générée")
        
        # Métadonnées
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Documents analysés", len(documents))
        
        with col2:
            st.metric("Mots", len(synthesis.split()))
        
        with col3:
            if 'key_points' in synthesis:
                st.metric("Points clés", len(synthesis.get('key_points', [])))
        
        # Contenu de la synthèse
        st.markdown(synthesis if isinstance(synthesis, str) else synthesis.get('content', ''))
        
        # Points clés si disponibles
        if isinstance(synthesis, dict) and 'key_points' in synthesis:
            st.markdown("### 🎯 Points clés")
            for i, point in enumerate(synthesis['key_points'], 1):
                st.write(f"{i}. {point}")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder", key="save_synthesis"):
                st.session_state.saved_syntheses = st.session_state.get('saved_syntheses', [])
                st.session_state.saved_syntheses.append({
                    'content': synthesis,
                    'timestamp': datetime.now(),
                    'document_count': len(documents)
                })
                st.success("✅ Synthèse sauvegardée")
        
        with col2:
            if st.button("📝 Transformer en note", key="synthesis_to_note"):
                st.session_state.universal_query = "rédiger note juridique basée sur la synthèse"
                st.rerun()
        
        with col3:
            if st.button("🔄 Régénérer", key="regenerate_synthesis"):
                process_synthesis_request(query, analysis)

def generate_synthesis_with_ai(documents: list, options: dict) -> Union[str, dict]:
    """Génère une synthèse avec l'IA"""
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        return "Erreur : Aucune IA disponible"
    
    # Construire le prompt selon le type
    prompts = {
        'Executive summary': """Crée un executive summary professionnel de ces documents.
Structure : Contexte, Points clés, Conclusions, Recommandations.
Maximum {max_length} mots.""",
        
        'Points clés': """Extrais les points clés de ces documents.
Liste numérotée, chaque point en 1-2 phrases.
Maximum {max_length} mots au total.""",
        
        'Analyse SWOT': """Effectue une analyse SWOT basée sur ces documents.
Forces, Faiblesses, Opportunités, Menaces.
Maximum {max_length} mots.""",
        
        'Recommandations': """Formule des recommandations basées sur ces documents.
Priorisées et actionnables.
Maximum {max_length} mots.""",
        
        'Chronologique': """Crée une synthèse chronologique des événements.
Ordre temporel avec dates.
Maximum {max_length} mots."""
    }
    
    prompt_template = prompts.get(options['type'], prompts['Executive summary'])
    prompt = prompt_template.format(max_length=options['max_length'])
    
    # Ajouter le contexte des documents
    context = "\n\n".join([
        f"Document {i+1}: {doc.get('title', 'Sans titre')}\n{doc.get('content', '')[:1500]}"
        for i, doc in enumerate(documents[:10])
    ])
    
    full_prompt = f"{prompt}\n\nDocuments à synthétiser :\n{context}"
    
    try:
        # Utiliser l'IA principale
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            full_prompt,
            "Tu es un expert en synthèse juridique."
        )
        
        if response['success']:
            synthesis_content = response['response']
            
            # Extraire les points clés si demandé
            if options['type'] == 'Points clés':
                key_points = extract_key_points(synthesis_content)
                return {
                    'content': synthesis_content,
                    'key_points': key_points
                }
            
            return synthesis_content
            
    except Exception as e:
        st.error(f"Erreur génération synthèse : {str(e)}")
        return "Erreur lors de la génération"

def extract_key_points(text: str) -> List[str]:
    """Extrait les points clés d'un texte"""
    points = []
    
    # Rechercher les listes numérotées
    numbered_points = re.findall(r'\d+\.\s*([^\n]+)', text)
    points.extend(numbered_points)
    
    # Rechercher les listes à puces
    bullet_points = re.findall(r'[•\-\*]\s*([^\n]+)', text)
    points.extend(bullet_points)
    
    # Si pas de liste, prendre les premières phrases
    if not points:
        sentences = text.split('.')[:5]
        points = [s.strip() for s in sentences if s.strip()]
    
    return points

def process_template_request(query: str, analysis: dict):
    """Traite une demande liée aux templates"""
    
    action = analysis['details'].get('action', 'apply')
    
    if action == 'create':
        create_new_template_interface()
    
    elif action == 'edit':
        edit_template_interface()
    
    else:  # apply
        apply_template_interface()

def create_new_template_interface():
    """Interface de création de nouveau template"""
    st.markdown("### 📄 Créer un nouveau template")
    
    template_name = st.session_state.get('new_template_name', '')
    
    if template_name:
        col1, col2 = st.columns(2)
        
        with col1:
            # Structure du template
            st.markdown("**Structure du document**")
            
            base_template = st.session_state.get('base_template', 'Vide')
            
            if base_template != 'Vide' and base_template in DOCUMENT_TEMPLATES:
                structure = DOCUMENT_TEMPLATES[base_template]['structure']
            else:
                structure = []
            
            # Éditeur de structure
            new_structure = st.text_area(
                "Sections (une par ligne)",
                value='\n'.join(structure),
                height=300,
                key="template_structure_editor"
            )
        
        with col2:
            # Paramètres du template
            st.markdown("**Paramètres**")
            
            style = st.selectbox(
                "Style par défaut",
                list(REDACTION_STYLES.keys()),
                format_func=lambda x: REDACTION_STYLES[x]['name'],
                key="template_default_style"
            )
            
            variables = st.text_area(
                "Variables (format: {nom_variable})",
                placeholder="{client}\n{adversaire}\n{date}\n{montant}",
                key="template_variables",
                help="Ces variables pourront être remplacées lors de l'utilisation"
            )
            
            instructions = st.text_area(
                "Instructions spéciales pour l'IA",
                placeholder="Toujours commencer par un rappel des faits...",
                key="template_instructions"
            )
        
        # Actions
        if st.button("💾 Sauvegarder le template", key="save_new_template"):
            save_new_template({
                'name': template_name,
                'structure': new_structure.split('\n'),
                'style': style,
                'variables': extract_template_variables(variables),
                'instructions': instructions,
                'category': st.session_state.get('template_category', 'Autre'),
                'is_public': st.session_state.get('template_public', False),
                'created_date': datetime.now()
            })
    else:
        st.warning("⚠️ Veuillez donner un nom au template")

def extract_template_variables(variables_text: str) -> List[str]:
    """Extrait les variables d'un template"""
    # Rechercher les patterns {variable}
    variables = re.findall(r'\{([^}]+)\}', variables_text)
    return list(set(variables))

def save_new_template(template_data: dict):
    """Sauvegarde un nouveau template"""
    if 'saved_templates' not in st.session_state:
        st.session_state.saved_templates = {}
    
    template_id = template_data['name'].lower().replace(' ', '_')
    st.session_state.saved_templates[template_id] = template_data
    
    st.success(f"✅ Template '{template_data['name']}' créé avec succès")
    
    # Proposer de l'utiliser immédiatement
    if st.button("Utiliser ce template maintenant", key="use_new_template_now"):
        st.session_state.universal_query = f"rédiger avec template {template_id}"
        st.rerun()

def process_jurisprudence_request(query: str, analysis: dict):
    """Traite une demande de recherche jurisprudentielle"""
    
    # Parser la requête juridique
    legal_terms = extract_legal_terms_from_query(query)
    
    # Sources de recherche
    sources = ['legifrance', 'doctrine']  # Limité aux sources disponibles
    
    # Interface de recherche
    st.markdown("### ⚖️ Recherche jurisprudentielle")
    
    with st.expander("🔍 Paramètres de recherche", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_sources = st.multiselect(
                "Sources",
                sources,
                default=sources,
                key="juris_sources"
            )
            
            date_range = st.selectbox(
                "Période",
                ["Toutes", "5 dernières années", "2 dernières années", "Cette année"],
                key="juris_date_range"
            )
        
        with col2:
            jurisdictions = st.multiselect(
                "Juridictions",
                ["Cour de cassation", "Conseil d'État", "Cours d'appel", "Toutes"],
                default=["Toutes"],
                key="juris_jurisdictions"
            )
            
            max_results = st.number_input(
                "Nombre max de résultats",
                5, 50, 20,
                key="juris_max_results"
            )
    
    # Recherche
    with st.spinner("🔍 Recherche en cours..."):
        jurisprudence_results = search_jurisprudence_unified(
            legal_terms,
            selected_sources,
            {
                'date_range': date_range,
                'jurisdictions': jurisdictions,
                'max_results': max_results
            }
        )
    
    # Affichage des résultats
    if jurisprudence_results:
        st.success(f"✅ {len(jurisprudence_results)} décisions trouvées")
        
        # Trier par pertinence
        jurisprudence_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Afficher les résultats
        for i, result in enumerate(jurisprudence_results):
            with st.expander(f"{i+1}. {result.get('title', 'Sans titre')}", expanded=(i < 3)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Juridiction :** {result.get('jurisdiction', 'N/A')}")
                    st.write(f"**Date :** {result.get('date', 'N/A')}")
                    st.write(f"**Référence :** {result.get('reference', 'N/A')}")
                    
                    if result.get('summary'):
                        st.markdown("**Résumé :**")
                        st.write(result['summary'])
                    
                    if result.get('key_points'):
                        st.markdown("**Points clés :**")
                        for point in result['key_points']:
                            st.write(f"• {point}")
                
                with col2:
                    relevance = result.get('relevance_score', 0)
                    st.metric("Pertinence", f"{relevance:.0%}")
                    
                    if result.get('url'):
                        st.markdown(f"[🔗 Voir la décision]({result['url']})")
                    
                    if st.button("📋 Citer", key=f"cite_juris_{i}"):
                        copy_jurisprudence_citation(result)
        
        # Actions globales
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Exporter résultats", key="export_juris"):
                export_jurisprudence_results(jurisprudence_results)
        
        with col2:
            if st.button("📊 Analyser tendances", key="analyze_juris_trends"):
                analyze_jurisprudence_trends(jurisprudence_results)
        
        with col3:
            if st.button("📝 Intégrer dans document", key="integrate_juris"):
                integrate_jurisprudence_in_document(jurisprudence_results)
    
    else:
        st.warning("⚠️ Aucune jurisprudence trouvée")

def extract_legal_terms_from_query(query: str) -> List[str]:
    """Extrait les termes juridiques pertinents de la requête"""
    # Termes juridiques courants
    legal_keywords = [
        'abus de biens sociaux', 'escroquerie', 'abus de confiance',
        'faux', 'corruption', 'blanchiment', 'prescription',
        'responsabilité', 'préjudice', 'dommages-intérêts',
        'nullité', 'résiliation', 'inexécution'
    ]
    
    terms = []
    query_lower = query.lower()
    
    # Ajouter les termes juridiques trouvés
    for keyword in legal_keywords:
        if keyword in query_lower:
            terms.append(keyword)
    
    # Ajouter les mots importants (plus de 4 lettres, pas des mots communs)
    stop_words = {'pour', 'dans', 'avec', 'sans', 'sous', 'vers', 'chez'}
    words = query_lower.split()
    
    for word in words:
        if len(word) > 4 and word not in stop_words and word not in terms:
            terms.append(word)
    
    return terms[:5]  # Limiter pour la recherche

def search_jurisprudence_unified(terms: List[str], sources: List[str], options: dict) -> List[dict]:
    """Recherche unifiée de jurisprudence"""
    results = []
    
    try:
        legal_search = LegalSearchManager()
        
        # Construire la requête
        query = ' '.join(terms)
        
        # Rechercher dans chaque source
        for source in sources:
            try:
                source_results = legal_search.search_source(
                    source=source,
                    query=query,
                    max_results=options['max_results'] // len(sources)  # Répartir
                )
                
                # Enrichir les résultats
                for result in source_results:
                    result['source'] = source
                    result['relevance_score'] = calculate_jurisprudence_relevance(result, terms)
                    
                    # Extraire les points clés avec l'IA si pas déjà fait
                    if not result.get('key_points') and result.get('content'):
                        result['key_points'] = extract_jurisprudence_key_points(result['content'])
                    
                    results.append(result)
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur recherche {source}: {str(e)}")
                
    except Exception as e:
        st.error(f"Erreur recherche jurisprudence : {str(e)}")
    
    return results

def calculate_jurisprudence_relevance(result: dict, terms: List[str]) -> float:
    """Calcule la pertinence d'une jurisprudence"""
    score = 0.0
    
    content_lower = (result.get('content', '') + result.get('summary', '')).lower()
    
    # Score basé sur la présence des termes
    for term in terms:
        if term.lower() in content_lower:
            score += 0.2
    
    # Bonus pour jurisprudence récente
    if result.get('date'):
        try:
            date = datetime.strptime(result['date'], '%Y-%m-%d')
            days_old = (datetime.now() - date).days
            if days_old < 365:  # Moins d'un an
                score += 0.3
            elif days_old < 730:  # Moins de 2 ans
                score += 0.2
        except:
            pass
    
    # Bonus pour les hautes juridictions
    if any(court in result.get('jurisdiction', '').lower() 
           for court in ['cassation', 'conseil d\'état']):
        score += 0.2
    
    return min(score, 1.0)

def extract_jurisprudence_key_points(content: str) -> List[str]:
    """Extrait les points clés d'une décision (version simplifiée)"""
    # TODO: Utiliser l'IA pour une extraction plus sophistiquée
    
    key_points = []
    
    # Rechercher les attendus importants
    attendus = re.findall(r'attendu que[^;]+;', content, re.IGNORECASE)
    key_points.extend(attendus[:3])
    
    # Rechercher les motifs
    motifs = re.findall(r'par ces motifs[^.]+\.', content, re.IGNORECASE)
    key_points.extend(motifs[:2])
    
    return key_points

def copy_jurisprudence_citation(result: dict):
    """Copie la citation d'une jurisprudence"""
    citation = f"{result.get('jurisdiction', 'N/A')}, {result.get('date', 'N/A')}, n°{result.get('reference', 'N/A')}"
    
    # Utiliser pyperclip si disponible, sinon afficher
    try:
        import pyperclip
        pyperclip.copy(citation)
        st.success("✅ Citation copiée dans le presse-papier")
    except:
        st.code(citation)
        st.info("📋 Citation à copier manuellement")

# === FONCTIONS D'AFFICHAGE DES RÉSULTATS ===

def show_unified_results_tab():
    """Affiche tous les types de résultats de manière unifiée"""
    
    # Déterminer quel type de résultat afficher
    result_types = []
    
    if 'redaction_result' in st.session_state:
        result_types.append(('📝 Rédaction', 'redaction'))
    
    if 'timeline_result' in st.session_state:
        result_types.append(('⏱️ Chronologie', 'timeline'))
    
    if 'mapping_result' in st.session_state:
        result_types.append(('🗺️ Cartographie', 'mapping'))
    
    if 'comparison_result' in st.session_state:
        result_types.append(('🔄 Comparaison', 'comparison'))
    
    if 'synthesis_result' in st.session_state:
        result_types.append(('📝 Synthèse', 'synthesis'))
    
    if 'import_result' in st.session_state:
        result_types.append(('📥 Import', 'import'))
    
    if 'export_result' in st.session_state:
        result_types.append(('📤 Export', 'export'))
    
    if 'bordereau_result' in st.session_state:
        result_types.append(('📊 Bordereau', 'bordereau'))
    
    if 'jurisprudence_result' in st.session_state:
        result_types.append(('⚖️ Jurisprudence', 'jurisprudence'))
    
    if 'ai_analysis_results' in st.session_state:
        result_types.append(('🤖 Analyse IA', 'analysis'))
    
    if 'search_results' in st.session_state:
        result_types.append(('🔍 Recherche', 'search'))
    
    if result_types:
        # S'il y a plusieurs types de résultats, créer des onglets
        if len(result_types) > 1:
            tab_names = [name for name, _ in result_types]
            tabs = st.tabs(tab_names)
            
            for i, (tab, (name, type_key)) in enumerate(zip(tabs, result_types)):
                with tab:
                    show_specific_result(type_key)
        else:
            # Un seul type de résultat
            show_specific_result(result_types[0][1])
    else:
        # Aucun résultat
        st.info("🔍 Utilisez la barre de commande universelle pour commencer")
        show_extended_examples()

def show_specific_result(result_type: str):
    """Affiche un type spécifique de résultat"""
    
    if result_type == 'redaction':
        show_redaction_results()
    
    elif result_type == 'timeline':
        show_timeline_results()
    
    elif result_type == 'mapping':
        show_mapping_results()
    
    elif result_type == 'comparison':
        show_comparison_results()
    
    elif result_type == 'synthesis':
        show_synthesis_results()
    
    elif result_type == 'import':
        show_import_results()
    
    elif result_type == 'export':
        show_export_results()
    
    elif result_type == 'bordereau':
        show_bordereau_results()
    
    elif result_type == 'jurisprudence':
        show_jurisprudence_results()
    
    elif result_type == 'analysis':
        show_ai_analysis_results()
    
    elif result_type == 'search':
        show_search_results_unified()

def show_synthesis_results():
    """Affiche les résultats de synthèse"""
    result = st.session_state.synthesis_result
    
    st.markdown("### 📝 Synthèse générée")
    
    # Affichage selon le type
    if isinstance(result, dict):
        if 'content' in result:
            st.markdown(result['content'])
        
        if 'key_points' in result:
            st.markdown("### 🎯 Points clés")
            for point in result['key_points']:
                st.write(f"• {point}")
    else:
        st.markdown(result)

def show_import_results():
    """Affiche les résultats d'import"""
    result = st.session_state.import_result
    
    st.success(f"✅ {result['count']} documents importés")
    
    if result.get('documents'):
        st.markdown("### 📄 Documents importés")
        for doc in result['documents'][:5]:  # Limiter l'affichage
            with st.expander(doc.title):
                st.write(f"**Source :** {doc.source}")
                st.write(f"**Taille :** {len(doc.content)} caractères")
                if hasattr(doc, 'metadata') and doc.metadata.get('ai_analysis'):
                    st.markdown("**Analyse IA :**")
                    st.write(doc.metadata['ai_analysis'])

def show_export_results():
    """Affiche les résultats d'export"""
    result = st.session_state.export_result
    
    st.success(f"✅ Export réussi : {result['filename']}")
    st.write(f"**Format :** {result['format'].upper()}")
    st.write(f"**Taille :** {result['size']} octets")

def show_bordereau_results():
    """Affiche les résultats de bordereau"""
    # Déjà géré dans process_bordereau_request
    pass

def show_jurisprudence_results():
    """Affiche les résultats de jurisprudence"""
    # Déjà géré dans process_jurisprudence_request
    pass

def show_pieces_management_tab():
    """Onglet de gestion des pièces"""
    st.markdown("### 📋 Gestion des pièces")
    
    pieces = st.session_state.get('pieces_selectionnees', {})
    
    if pieces:
        # Statistiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total pièces", len(pieces))
        
        with col2:
            categories = set(p.categorie for p in pieces.values())
            st.metric("Catégories", len(categories))
        
        with col3:
            avg_pertinence = sum(p.pertinence for p in pieces.values()) / len(pieces)
            st.metric("Pertinence moyenne", f"{avg_pertinence:.1f}/5")
        
        # Affichage par catégorie
        for category in sorted(categories):
            cat_pieces = [p for p in pieces.values() if p.categorie == category]
            
            with st.expander(f"{category} ({len(cat_pieces)} pièces)"):
                for piece in cat_pieces:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{piece.cote_bordereau}** - {piece.titre}")
                    
                    with col2:
                        st.write(f"⭐ {piece.pertinence}/5")
                    
                    with col3:
                        if st.button("🗑️", key=f"del_piece_{piece.document_id}"):
                            del pieces[piece.document_id]
                            st.rerun()
    else:
        st.info("Aucune pièce sélectionnée")
        
        if st.button("🔍 Sélectionner des pièces"):
            st.session_state.universal_query = "sélectionner pièces"
            st.rerun()

def show_extended_examples():
    """Affiche des exemples étendus de toutes les fonctionnalités"""
    
    st.markdown("### 💡 Exemples de commandes")
    
    # Grouper par catégorie
    example_categories = {
        "📝 Rédaction": [
            "rédiger conclusions défense @affaire_martin abus de biens sociaux",
            "plainte avec constitution partie civile escroquerie @victime_x",
            "courrier mise en demeure @impayés_2024 style persuasif",
            "créer template mémoire en réplique",
            "assignation en référé @urgent_locataire"
        ],
        "🔍 Recherche & Analyse": [
            "@affaire_martin analyser les risques pénaux",
            "chronologie des faits @corruption_2023",
            "cartographie des sociétés @groupe_abc",
            "comparer les auditions @témoins_affaire_x",
            "synthèse executive @documents_expertise"
        ],
        "📋 Gestion documentaire": [
            "sélectionner pièces @dossier_pénal catégorie procédure",
            "créer bordereau @pièces_sélectionnées",
            "importer documents pdf @nouveau_client",
            "exporter @analyse_risques format word avec métadonnées"
        ],
        "⚖️ Recherche juridique": [
            "jurisprudence abus de biens sociaux prescription",
            "rechercher arrêts récents corruption marchés publics",
            "tendances jurisprudentielles @blanchiment 2024"
        ],
        "📧 Communication": [
            "envoyer conclusions à avocat@cabinet.fr",
            "email avec bordereau @pièces_communication",
            "transmettre synthèse @client format pdf"
        ],
        "🤖 IA avancée": [
            "analyser avec 3 ia @contrats_complexes fusion consensus",
            "rédiger avec 4 ia plainte style technique",
            "comparer versions @document_évolutif highlight différences"
        ]
    }
    
    # Afficher en colonnes
    cols = st.columns(2)
    
    for i, (category, examples) in enumerate(example_categories.items()):
        with cols[i % 2]:
            st.markdown(f"**{category}**")
            for example in examples:
                if st.button(
                    f"→ {example[:40]}...",
                    key=f"ex_{example}",
                    help=example
                ):
                    st.session_state.universal_query = example
                    st.rerun()
            st.markdown("")

def show_explorer_tab():
    """Onglet explorateur de fichiers"""
    st.markdown("### 🗂️ Explorateur de documents")
    
    # Sources disponibles
    source = st.selectbox(
        "Source",
        ["Documents locaux", "Azure Blob Storage"],
        key="explorer_source"
    )
    
    if source == "Documents locaux":
        show_local_documents_explorer()
    else:
        show_azure_explorer()

def show_local_documents_explorer():
    """Explorateur de documents locaux"""
    documents = st.session_state.get('azure_documents', {})
    
    if documents:
        # Barre de recherche
        search = st.text_input("🔍 Filtrer", key="explorer_search")
        
        # Filtrer les documents
        filtered_docs = {
            id: doc for id, doc in documents.items()
            if not search or search.lower() in doc.title.lower()
        }
        
        # Afficher les documents
        for doc_id, doc in filtered_docs.items():
            with st.expander(f"📄 {doc.title}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Source :** {doc.source}")
                    st.write(f"**Taille :** {len(doc.content)} caractères")
                    st.text_area("Aperçu", doc.content[:500], height=100, disabled=True)
                
                with col2:
                    if st.button("🤖 Analyser", key=f"analyze_{doc_id}"):
                        st.session_state.universal_query = f"analyser @{doc_id}"
                        st.rerun()
                    
                    if st.button("📝 Utiliser", key=f"use_{doc_id}"):
                        st.session_state.universal_query = f"rédiger basé sur @{doc_id}"
                        st.rerun()
                    
                    if st.button("🗑️ Supprimer", key=f"delete_{doc_id}"):
                        del documents[doc_id]
                        st.rerun()
    else:
        st.info("Aucun document local")
        
        if st.button("📥 Importer des documents"):
            st.session_state.universal_query = "importer documents"
            st.rerun()

def show_azure_explorer():
    """Explorateur Azure Blob"""
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        
        if containers:
            selected_container = st.selectbox(
                "Container",
                containers,
                key="azure_container"
            )
            
            # Explorer le container
            if selected_container:
                current_path = st.session_state.get('azure_current_path', '')
                
                # Breadcrumb
                if current_path:
                    path_parts = current_path.split('/')
                    cols = st.columns(len(path_parts) + 1)
                    
                    with cols[0]:
                        if st.button("🏠", key="azure_home"):
                            st.session_state.azure_current_path = ''
                            st.rerun()
                    
                    for i, part in enumerate(path_parts):
                        with cols[i + 1]:
                            if st.button(part, key=f"path_{i}"):
                                st.session_state.azure_current_path = '/'.join(path_parts[:i+1])
                                st.rerun()
                
                # Lister le contenu
                items = blob_manager.list_folder_contents(selected_container, current_path)
                
                # Afficher les dossiers d'abord
                folders = [item for item in items if item['type'] == 'folder']
                files = [item for item in items if item['type'] == 'file']
                
                # Dossiers
                if folders:
                    st.markdown("**📁 Dossiers**")
                    cols = st.columns(4)
                    
                    for i, folder in enumerate(folders):
                        with cols[i % 4]:
                            if st.button(
                                f"📁 {folder['name']}",
                                key=f"folder_{folder['name']}",
                                use_container_width=True
                            ):
                                st.session_state.azure_current_path = folder['path']
                                st.rerun()
                
                # Fichiers
                if files:
                    st.markdown("**📄 Fichiers**")
                    
                    for file in files:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"📄 {file['name']}")
                            st.caption(f"{file['size'] / 1024:.1f} KB")
                        
                        with col2:
                            if st.button("📥", key=f"download_{file['name']}", help="Télécharger"):
                                download_azure_file(blob_manager, selected_container, file)
                        
                        with col3:
                            if st.button("➕", key=f"add_{file['name']}", help="Ajouter aux documents"):
                                add_azure_file_to_documents(blob_manager, selected_container, file)
        else:
            st.warning("Aucun container disponible")
    else:
        st.error("❌ Azure Blob non connecté")
        
        if st.button("🔄 Réessayer la connexion"):
            del st.session_state.azure_blob_manager
            st.rerun()

def download_azure_file(blob_manager, container: str, file: dict):
    """Télécharge un fichier depuis Azure"""
    try:
        content = blob_manager.download_blob(container, file['path'])
        
        st.download_button(
            "💾 Télécharger",
            content,
            file['name'],
            key=f"download_content_{file['name']}"
        )
    except Exception as e:
        st.error(f"Erreur téléchargement : {str(e)}")

def add_azure_file_to_documents(blob_manager, container: str, file: dict):
    """Ajoute un fichier Azure aux documents locaux"""
    try:
        content = blob_manager.download_blob(container, file['path'])
        
        doc = Document(
            id=f"azure_{container}_{file['name']}",
            title=file['name'],
            content=content.decode('utf-8', errors='ignore'),
            source=f"Azure: {container}",
            metadata={
                'container': container,
                'path': file['path'],
                'size': file['size']
            }
        )
        
        if 'azure_documents' not in st.session_state:
            st.session_state.azure_documents = {}
        
        st.session_state.azure_documents[doc.id] = doc
        st.success(f"✅ '{file['name']}' ajouté aux documents")
        
    except Exception as e:
        st.error(f"Erreur ajout : {str(e)}")

def show_configuration_tab():
    """Onglet de configuration avancée"""
    st.markdown("### ⚙️ Configuration")
    
    tabs = st.tabs(["🤖 IA", "📄 Templates", "🔧 Système", "👤 Préférences"])
    
    with tabs[0]:
        show_ai_configuration()
    
    with tabs[1]:
        show_templates_configuration()
    
    with tabs[2]:
        show_system_configuration()
    
    with tabs[3]:
        show_user_preferences()

def show_ai_configuration():
    """Configuration des IA"""
    st.markdown("### 🤖 Configuration des IA")
    
    llm_manager = MultiLLMManager()
    
    if hasattr(llm_manager, 'clients'):
        available_providers = list(llm_manager.clients.keys())
        
        st.write(f"**IA disponibles :** {len(available_providers)}")
        
        for provider in available_providers:
            with st.expander(f"{provider.value if hasattr(provider, 'value') else provider}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**État :** ✅ Connecté")
                    
                    # Paramètres spécifiques au provider
                    if hasattr(provider, 'value'):
                        if 'CLAUDE' in str(provider.value):
                            temp = st.slider(
                                "Température",
                                0.0, 1.0, 0.7,
                                key=f"temp_{provider.value}"
                            )
                        elif 'GPT' in str(provider.value):
                            model = st.selectbox(
                                "Modèle",
                                ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
                                key=f"model_{provider.value}"
                            )
                
                with col2:
                    if st.button("🧪 Tester", key=f"test_{provider}"):
                        test_llm_connection(llm_manager, provider)
    else:
        st.error("❌ Aucune IA configurée")

def test_llm_connection(llm_manager, provider):
    """Teste la connexion à une IA"""
    with st.spinner(f"Test de {provider}..."):
        try:
            response = llm_manager.query_single_llm(
                provider,
                "Réponds simplement 'OK' si tu me reçois.",
                "Test de connexion"
            )
            
            if response['success']:
                st.success(f"✅ {provider} répond : {response['response']}")
            else:
                st.error(f"❌ Erreur : {response.get('error', 'Inconnue')}")
                
        except Exception as e:
            st.error(f"❌ Erreur test : {str(e)}")

def show_templates_configuration():
    """Configuration des templates"""
    st.markdown("### 📄 Gestion des templates")
    
    # Templates système
    st.markdown("**Templates système**")
    
    for template_id, template in DOCUMENT_TEMPLATES.items():
        with st.expander(template['name']):
            st.write("**Structure :**")
            for section in template['structure']:
                st.write(f"• {section}")
            st.write(f"**Style par défaut :** {template['style']}")
    
    # Templates personnalisés
    st.markdown("**Templates personnalisés**")
    
    saved_templates = st.session_state.get('saved_templates', {})
    
    if saved_templates:
        for template_id, template in saved_templates.items():
            with st.expander(template['name']):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Structure :**")
                    for section in template.get('structure', []):
                        st.write(f"• {section}")
                    
                    if template.get('variables'):
                        st.write("**Variables :**")
                        st.write(', '.join(template['variables']))
                
                with col2:
                    if st.button("✏️", key=f"edit_template_{template_id}"):
                        st.session_state.universal_query = f"éditer template {template_id}"
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_template_{template_id}"):
                        del saved_templates[template_id]
                        st.success("✅ Template supprimé")
                        st.rerun()
    else:
        st.info("Aucun template personnalisé")
    
    if st.button("➕ Créer un nouveau template"):
        st.session_state.universal_query = "créer nouveau template"
        st.rerun()

def show_system_configuration():
    """Configuration système"""
    st.markdown("### 🔧 Configuration système")
    
    # Variables d'environnement
    st.markdown("**Variables d'environnement**")
    
    env_vars = [
        ("AZURE_STORAGE_CONNECTION_STRING", "Azure Blob Storage"),
        ("AZURE_SEARCH_ENDPOINT", "Azure Search Endpoint"),
        ("AZURE_SEARCH_KEY", "Azure Search Key"),
        ("ANTHROPIC_API_KEY", "Claude API"),
        ("OPENAI_API_KEY", "OpenAI API"),
        ("GOOGLE_API_KEY", "Google API"),
        ("MISTRAL_API_KEY", "Mistral API")
    ]
    
    for var, desc in env_vars:
        col1, col2, col3 = st.columns([3, 1, 2])
        
        with col1:
            st.text(desc)
        
        with col2:
            if os.getenv(var):
                st.success("✅")
            else:
                st.error("❌")
        
        with col3:
            if os.getenv(var):
                value = os.getenv(var)
                if 'KEY' in var or 'STRING' in var:
                    st.caption(f"{value[:10]}...")
                else:
                    st.caption(value[:30] + "..." if len(value) > 30 else value)
    
# Suite de show_system_configuration()
    
    # Statistiques système
    st.markdown("**Statistiques système**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents", len(st.session_state.get('azure_documents', {})))
        st.metric("Templates", len(st.session_state.get('saved_templates', {})))
    
    with col2:
        st.metric("Pièces sélectionnées", len(st.session_state.get('pieces_selectionnees', {})))
        st.metric("Historique", len(st.session_state.get('query_history', [])))
    
    with col3:
        # Calculer l'espace utilisé
        total_size = sum(
            len(doc.content) for doc in st.session_state.get('azure_documents', {}).values()
        )
        st.metric("Espace utilisé", f"{total_size / 1024 / 1024:.1f} MB")
        
        # Uptime
        if 'app_start_time' not in st.session_state:
            st.session_state.app_start_time = datetime.now()
        
        uptime = datetime.now() - st.session_state.app_start_time
        st.metric("Uptime", f"{uptime.total_seconds() / 60:.0f} min")
    
    # Actions de maintenance
    st.markdown("**Maintenance**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Nettoyer cache", key="clear_cache"):
            clear_application_cache()
    
    with col2:
        if st.button("💾 Sauvegarder état", key="save_state"):
            save_application_state()
    
    with col3:
        if st.button("🔄 Réinitialiser", key="reset_app"):
            if st.checkbox("Confirmer réinitialisation", key="confirm_reset"):
                reset_application()

def show_user_preferences():
    """Configuration des préférences utilisateur"""
    st.markdown("### 👤 Préférences utilisateur")
    
    # Préférences d'interface
    st.markdown("**Interface**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Thème",
            ["Automatique", "Clair", "Sombre"],
            key="pref_theme"
        )
        
        language = st.selectbox(
            "Langue",
            ["Français", "English"],
            key="pref_language"
        )
    
    with col2:
        compact_mode = st.checkbox(
            "Mode compact",
            value=st.session_state.get('compact_mode', False),
            key="pref_compact"
        )
        
        show_tips = st.checkbox(
            "Afficher les conseils",
            value=st.session_state.get('show_tips', True),
            key="pref_tips"
        )
    
    # Préférences de rédaction
    st.markdown("**Rédaction**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_style = st.selectbox(
            "Style par défaut",
            list(REDACTION_STYLES.keys()),
            format_func=lambda x: REDACTION_STYLES[x]['name'],
            key="pref_default_style"
        )
        
        default_ai_count = st.number_input(
            "Nombre d'IA par défaut",
            1, 4, 2,
            key="pref_ai_count"
        )
    
    with col2:
        auto_jurisprudence = st.checkbox(
            "Recherche auto de jurisprudence",
            value=True,
            key="pref_auto_juris"
        )
        
        auto_save = st.checkbox(
            "Sauvegarde automatique",
            value=True,
            key="pref_auto_save"
        )
    
    # Préférences de recherche
    st.markdown("**Recherche**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_results = st.number_input(
            "Résultats par défaut",
            5, 50, 20,
            key="pref_default_results"
        )
        
        search_mode = st.selectbox(
            "Mode de recherche par défaut",
            [mode.value for mode in SearchMode],
            key="pref_search_mode"
        )
    
    with col2:
        include_archives = st.checkbox(
            "Inclure archives",
            value=False,
            key="pref_include_archives"
        )
        
        fuzzy_search = st.checkbox(
            "Recherche floue",
            value=True,
            key="pref_fuzzy"
        )
    
    # Sauvegarder les préférences
    if st.button("💾 Sauvegarder les préférences", key="save_preferences"):
        save_user_preferences()

def save_user_preferences():
    """Sauvegarde les préférences utilisateur"""
    preferences = {
        'theme': st.session_state.get('pref_theme'),
        'language': st.session_state.get('pref_language'),
        'compact_mode': st.session_state.get('pref_compact'),
        'show_tips': st.session_state.get('pref_tips'),
        'default_style': st.session_state.get('pref_default_style'),
        'default_ai_count': st.session_state.get('pref_ai_count'),
        'auto_jurisprudence': st.session_state.get('pref_auto_juris'),
        'auto_save': st.session_state.get('pref_auto_save'),
        'default_results': st.session_state.get('pref_default_results'),
        'search_mode': st.session_state.get('pref_search_mode'),
        'include_archives': st.session_state.get('pref_include_archives'),
        'fuzzy_search': st.session_state.get('pref_fuzzy')
    }
    
    st.session_state.user_preferences = preferences
    
    # Sauvegarder dans un fichier ou base de données
    # TODO: Implémenter la persistance
    
    st.success("✅ Préférences sauvegardées")

# === FONCTIONS UTILITAIRES MANQUANTES ===

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'query_analysis',
        'search_results', 'ai_analysis_results', 'redaction_result',
        'timeline_result', 'mapping_result', 'comparison_result',
        'synthesis_result', 'import_result', 'export_result',
        'bordereau_result', 'jurisprudence_result'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def save_current_work():
    """Sauvegarde le travail en cours"""
    work_snapshot = {
        'timestamp': datetime.now(),
        'query': st.session_state.get('universal_query'),
        'results': {}
    }
    
    # Capturer tous les résultats actuels
    result_keys = [
        'redaction_result', 'timeline_result', 'mapping_result',
        'comparison_result', 'synthesis_result', 'search_results'
    ]
    
    for key in result_keys:
        if key in st.session_state:
            work_snapshot['results'][key] = st.session_state[key]
    
    # Sauvegarder
    if 'saved_work' not in st.session_state:
        st.session_state.saved_work = []
    
    st.session_state.saved_work.append(work_snapshot)
    
    st.success(f"✅ Travail sauvegardé à {datetime.now().strftime('%H:%M')}")

def share_current_work():
    """Partage le travail en cours"""
    # Créer un lien de partage ou exporter
    with st.expander("📤 Options de partage", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            share_format = st.selectbox(
                "Format de partage",
                ["Lien", "Export complet", "Résumé"],
                key="share_format"
            )
        
        with col2:
            share_with = st.text_input(
                "Partager avec",
                placeholder="email@example.com",
                key="share_with"
            )
        
        if st.button("📤 Partager", key="share_now"):
            if share_format == "Export complet":
                export_complete_work()
            else:
                st.info("🔄 Fonction de partage en développement")

def export_complete_work():
    """Exporte tout le travail en cours"""
    # Compiler tout le contenu
    export_content = "EXPORT COMPLET DU TRAVAIL\n" + "=" * 50 + "\n\n"
    export_content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    export_content += f"Requête : {st.session_state.get('universal_query', 'N/A')}\n\n"
    
    # Ajouter chaque type de résultat
    if 'redaction_result' in st.session_state:
        export_content += "\n=== RÉDACTION ===\n"
        export_content += st.session_state.redaction_result.get('document', '')
    
    if 'timeline_result' in st.session_state:
        export_content += "\n\n=== CHRONOLOGIE ===\n"
        for event in st.session_state.timeline_result.get('events', []):
            export_content += f"{event.get('date', 'N/A')} : {event.get('description', '')}\n"
    
    # Générer le fichier
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    st.download_button(
        "💾 Télécharger l'export complet",
        export_content,
        f"export_complet_{timestamp}.txt",
        "text/plain",
        key="download_complete_export"
    )

def clear_application_cache():
    """Nettoie le cache de l'application"""
    # Nettoyer les résultats temporaires
    temp_keys = [
        'search_results', 'ai_analysis_results',
        'temp_documents', 'cache_embeddings'
    ]
    
    cleared = 0
    for key in temp_keys:
        if key in st.session_state:
            del st.session_state[key]
            cleared += 1
    
    st.success(f"✅ Cache nettoyé ({cleared} éléments supprimés)")

def save_application_state():
    """Sauvegarde l'état complet de l'application"""
    # Créer un snapshot de l'état
    state_snapshot = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'documents': len(st.session_state.get('azure_documents', {})),
        'pieces': len(st.session_state.get('pieces_selectionnees', {})),
        'templates': len(st.session_state.get('saved_templates', {})),
        'history': st.session_state.get('query_history', [])[-10:],  # Dernières 10 requêtes
        'preferences': st.session_state.get('user_preferences', {})
    }
    
    # Sauvegarder dans un fichier JSON
    json_data = json.dumps(state_snapshot, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Télécharger l'état de l'application",
        json_data,
        f"etat_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="download_app_state"
    )

def reset_application():
    """Réinitialise complètement l'application"""
    # Sauvegarder d'abord l'historique
    history_backup = st.session_state.get('query_history', [])
    
    # Effacer tout sauf les connexions
    keys_to_preserve = ['azure_blob_manager', 'azure_search_manager']
    
    for key in list(st.session_state.keys()):
        if key not in keys_to_preserve:
            del st.session_state[key]
    
    # Restaurer un historique minimal
    st.session_state.query_history = history_backup[-10:]  # Garder les 10 dernières
    
    st.success("✅ Application réinitialisée")
    st.rerun()

# === FONCTIONS DE TRAITEMENT RESTANTES ===

def process_analysis_request(query: str, analysis: dict):
    """Traite une demande d'analyse IA simple"""
    # Collecter les documents pertinents
    if analysis['reference']:
        documents = search_by_reference(f"@{analysis['reference']}")
    else:
        documents = search_files(query)
    
    if not documents:
        st.warning("⚠️ Aucun document trouvé pour l'analyse")
        return
    
    # Construire le prompt d'analyse
    context = prepare_documents_context(documents)
    
    # Détecter le type d'analyse demandé
    analysis_type = detect_analysis_type(query)
    
    # Générer l'analyse avec l'IA
    ai_results = perform_ai_analysis(documents, query, analysis.get('reference'))
    
    if ai_results and ai_results.get('success'):
        st.session_state.ai_analysis_results = ai_results
    else:
        st.error("❌ Erreur lors de l'analyse")

def process_search_request(query: str, analysis: dict):
    """Traite une demande de recherche simple"""
    search_type = st.session_state.get('search_type_unified', '🔍 Auto')
    
    if analysis['reference']:
        results = search_by_reference(f"@{analysis['reference']}")
    elif '📁' in search_type:
        results = search_folders(query)
    elif '📄' in search_type:
        results = search_files(query)
    else:
        results = search_auto(query)
    
    st.session_state.search_results = results

def detect_analysis_type(query: str) -> str:
    """Détecte le type d'analyse demandé"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['risque', 'danger', 'exposition']):
        return 'risk_analysis'
    elif any(word in query_lower for word in ['clause', 'contrat', 'stipulation']):
        return 'contract_analysis'
    elif any(word in query_lower for word in ['responsabilité', 'faute', 'imputation']):
        return 'liability_analysis'
    elif any(word in query_lower for word in ['stratégie', 'défense', 'moyen']):
        return 'defense_strategy'
    else:
        return 'general_analysis'

def prepare_documents_context(documents: list) -> str:
    """Prépare le contexte des documents pour l'IA"""
    context_parts = []
    
    blob_manager = st.session_state.get('azure_blob_manager')
    
    for i, doc in enumerate(documents[:10]):  # Limiter à 10
        doc_content = ""
        
        # Récupérer le contenu selon le type
        if isinstance(doc, dict):
            if doc.get('type') == 'file' and 'container' in doc:
                # Fichier Azure
                try:
                    if blob_manager and blob_manager.is_connected():
                        content_bytes = blob_manager.download_blob(doc['container'], doc['path'])
                        doc_content = content_bytes.decode('utf-8', errors='ignore')[:2000]
                except:
                    doc_content = doc.get('content', '')
            else:
                doc_content = doc.get('content', '')
        else:
            # Document object
            doc_content = doc.content if hasattr(doc, 'content') else str(doc)
        
        if doc_content:
            title = doc.get('title', 'Sans titre') if isinstance(doc, dict) else getattr(doc, 'title', 'Sans titre')
            context_parts.append(f"""
=== DOCUMENT {i+1}: {title} ===
{doc_content[:1500]}...
""")
    
    return "\n".join(context_parts)

def perform_ai_analysis(search_results: list, question: str, reference: str = None) -> dict:
    """Effectue l'analyse IA sur les documents trouvés"""
    
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    # Préparer le contexte
    context = prepare_documents_context(search_results)
    
    if not context:
        return {'error': 'Aucun contenu analysable'}
    
    # Construire le prompt
    analysis_prompt = build_ai_analysis_prompt(question, context, reference)
    
    # Sélectionner les IA
    available_providers = list(llm_manager.clients.keys())
    selected_providers = available_providers[:2]  # 2 IA max
    
    # Exécuter l'analyse
    try:
        responses = asyncio.run(
            llm_manager.query_multiple_llms(
                selected_providers,
                analysis_prompt,
                "Tu es un avocat expert en droit pénal des affaires français."
            )
        )
        
        # Fusionner si plusieurs réponses
        if len(responses) > 1:
            fusion = llm_manager.fusion_responses(responses)
        else:
            fusion = responses[0]['response'] if responses and responses[0]['success'] else "Analyse non disponible"
        
        return {
            'success': True,
            'analysis': fusion,
            'providers_used': [r['provider'] for r in responses if r['success']],
            'document_count': len(search_results),
            'question': question,
            'reference': reference
        }
        
    except Exception as e:
        return {'error': f'Erreur analyse IA: {str(e)}'}

def build_ai_analysis_prompt(question: str, context: str, reference: str = None) -> str:
    """Construit le prompt d'analyse pour l'IA"""
    
    prompt = f"""ANALYSE JURIDIQUE DEMANDÉE

Question posée : {question}
"""
    
    if reference:
        prompt += f"Référence spécifique : @{reference}\n"
    
    prompt += f"""
Documents à analyser :
{context}

INSTRUCTIONS :
1. Analyse approfondie et structurée
2. Identification des points juridiques clés
3. Évaluation des risques et opportunités
4. Recommandations pratiques et actionnables
5. Citations précises des documents analysés

Structure ta réponse avec :
- 🎯 SYNTHÈSE EXÉCUTIVE (3-5 lignes max)
- 📋 ANALYSE DÉTAILLÉE
- ⚖️ POINTS JURIDIQUES CLÉS
- ⚠️ RISQUES IDENTIFIÉS
- 💡 OPPORTUNITÉS
- 🛡️ RECOMMANDATIONS
- 📚 RÉFÉRENCES ET SOURCES

Sois précis, professionnel et orienté solutions."""
    
    return prompt

def show_ai_analysis_results():
    """Affiche les résultats d'analyse IA"""
    results = st.session_state.ai_analysis_results
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    st.markdown("### 🤖 Analyse IA")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents analysés", results.get('document_count', 0))
    
    with col2:
        providers = results.get('providers_used', [])
        st.metric("IA utilisées", len(providers))
    
    with col3:
        if st.button("💾 Exporter", key="export_ai_analysis"):
            export_ai_analysis(results)
    
    # Résultat de l'analyse
    st.markdown("---")
    
    if 'analysis' in results:
        # Parser et afficher de manière structurée
        display_structured_analysis(results['analysis'])
    
    # Informations supplémentaires
    with st.expander("ℹ️ Détails de l'analyse", expanded=False):
        st.write(f"**Question analysée :** {results.get('question', 'N/A')}")
        if results.get('reference'):
            st.write(f"**Référence :** @{results['reference']}")
        st.write(f"**IA utilisées :** {', '.join(results.get('providers_used', []))}")
        st.write(f"**Timestamp :** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

def display_structured_analysis(analysis_text: str):
    """Affiche l'analyse de manière structurée"""
    # Essayer de parser les sections
    sections = {
        '🎯 SYNTHÈSE EXÉCUTIVE': '',
        '📋 ANALYSE DÉTAILLÉE': '',
        '⚖️ POINTS JURIDIQUES': '',
        '⚠️ RISQUES': '',
        '💡 OPPORTUNITÉS': '',
        '🛡️ RECOMMANDATIONS': '',
        '📚 RÉFÉRENCES': ''
    }
    
    current_section = None
    lines = analysis_text.split('\n')
    
    for line in lines:
        # Détecter les sections
        section_found = False
        for section in sections.keys():
            if any(marker in line for marker in section.split()):
                current_section = section
                section_found = True
                break
        
        if not section_found and current_section:
            sections[current_section] += line + '\n'
    
    # Afficher les sections non vides
    for section, content in sections.items():
        if content.strip():
            st.markdown(f"**{section}**")
            st.markdown(content)
            st.markdown("")

def export_ai_analysis(results: dict):
    """Exporte l'analyse IA"""
    content = f"""ANALYSE IA - {datetime.now().strftime('%d/%m/%Y %H:%M')}

Question : {results.get('question', 'N/A')}
Référence : @{results.get('reference', 'N/A')}
Documents analysés : {results.get('document_count', 0)}
IA utilisées : {', '.join(results.get('providers_used', []))}

{'=' * 50}

{results.get('analysis', 'Aucune analyse disponible')}
"""
    
    st.download_button(
        "💾 Télécharger l'analyse",
        content,
        f"analyse_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
        key="download_ai_analysis_txt"
    )

# === FONCTIONS DE RECHERCHE DE BASE ===

def search_by_reference(query: str) -> list:
    """Recherche par référence @"""
    if not query.startswith('@'):
        return []
    
    reference = query[1:].lower().strip()
    results = []
    
    # Recherche dans les documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if reference in doc_id.lower() or reference in doc.title.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content[:500] + "...",
                'score': 1.0,
                'source': doc.source,
                'type': 'document'
            })
    
    # Recherche dans Azure Blob
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        
        for container in containers:
            try:
                items = blob_manager.list_folder_contents(container, "")
                
                for item in items:
                    if reference in item['name'].lower():
                        results.append({
                            'id': f"ref_{container}_{item['name']}",
                            'title': f"{'📁' if item['type'] == 'folder' else '📄'} {item['name']}",
                            'content': f"Trouvé par référence @{reference}",
                            'score': 1.0,
                            'source': f"Azure: {container}",
                            'type': item['type'],
                            'path': item['path'],
                            'container': container
                        })
            except:
                continue
    
    return results

def search_folders(query: str) -> list:
    """Recherche de dossiers"""
    results = []
    query_lower = query.lower()
    
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        
        for container in containers:
            try:
                items = blob_manager.list_folder_contents(container, "")
                
                for item in items:
                    if item['type'] == 'folder' and query_lower in item['name'].lower():
                        # Compter le contenu
                        sub_items = blob_manager.list_folder_contents(container, item['path'])
                        file_count = len([i for i in sub_items if i['type'] == 'file'])
                        folder_count = len([i for i in sub_items if i['type'] == 'folder'])
                        
                        results.append({
                            'id': f"folder_{container}_{item['name']}",
                            'title': f"📁 {item['name']}",
                            'content': f"Dossier - {file_count} fichiers, {folder_count} sous-dossiers",
                            'score': 1.0,
                            'source': f"Azure: {container}",
                            'type': 'folder',
                            'path': item['path'],
                            'container': container,
                            'file_count': file_count,
                            'folder_count': folder_count
                        })
            except:
                continue
    
    return results

def search_files(query: str) -> list:
    """Recherche de fichiers"""
    results = []
    query_lower = query.lower()
    
    # Recherche locale
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if query_lower in doc.title.lower() or query_lower in doc.content.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content[:200] + "...",
                'score': 1.0,
                'source': doc.source,
                'type': 'document'
            })
    
    # Recherche Azure Search si disponible
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and hasattr(search_manager, 'search_text'):
        try:
            azure_results = search_manager.search_text(query, top=20)
            results.extend(azure_results)
        except:
            pass
    
    return results

def search_auto(query: str) -> list:
    """Recherche automatique tous types"""
    results = []
    
    # Combiner tous les types de recherche
    results.extend(search_files(query))
    results.extend(search_folders(query))
    
    # Si un seul mot, essayer aussi comme référence
    if len(query.split()) == 1:
        ref_results = search_by_reference(f"@{query}")
        results.extend(ref_results)
    
    # Dédupliquer et trier
    seen = set()
    unique_results = []
    
    for result in results:
        if result['id'] not in seen:
            seen.add(result['id'])
            unique_results.append(result)
    
    unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return unique_results

def show_search_results_unified():
    """Affiche les résultats de recherche"""
    results = st.session_state.get('search_results', [])
    
    if not results:
        st.info("Aucun résultat trouvé")
        return
    
    st.markdown(f"### 🔍 Résultats de recherche ({len(results)})")
    
    # Options d'affichage
    view_mode = st.radio(
        "Mode d'affichage",
        ["Liste", "Cartes", "Tableau"],
        horizontal=True,
        key="search_view_mode"
    )
    
    if view_mode == "Liste":
        for i, result in enumerate(results):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{result['title']}**")
                    st.caption(f"Score: {result.get('score', 0):.2f} | Source: {result['source']}")
                    st.text(result['content'][:200] + "...")
                
                with col2:
                    if st.button("👁️", key=f"view_{result['id']}"):
                        view_document_detail(result)
                    
                    if st.button("🤖", key=f"analyze_{result['id']}"):
                        st.session_state.universal_query = f"analyser @{result['id']}"
                        st.rerun()
    
    elif view_mode == "Cartes":
        cols = st.columns(3)
        for i, result in enumerate(results):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"**{result['title']}**")
                    st.caption(result['source'])
                    st.text(result['content'][:100] + "...")
                    
                    if st.button("Voir plus", key=f"more_{result['id']}"):
                        view_document_detail(result)
    
    else:  # Tableau
        import pandas as pd
        
        df_data = []
        for result in results:
            df_data.append({
                'Titre': result['title'],
                'Source': result['source'],
                'Score': result.get('score', 0),
                'Type': result.get('type', 'document')
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def view_document_detail(document: dict):
    """Affiche le détail d'un document"""
    with st.expander(f"📄 {document['title']}", expanded=True):
        st.write(f"**Source :** {document['source']}")
        st.write(f"**Type :** {document.get('type', 'document')}")
        
        if 'path' in document:
            st.write(f"**Chemin :** {document['path']}")
        
        st.text_area(
            "Contenu",
            document.get('content', 'Contenu non disponible'),
            height=300,
            key=f"content_{document['id']}"
        )

# === AUTRES FONCTIONS UTILITAIRES ===

def create_bordereau_from_selection(selected_df, category: str):
    """Crée un bordereau à partir de la sélection"""
    pieces = {}
    
    for i, (_, row) in enumerate(selected_df.iterrows()):
        pieces[row['ID']] = PieceSelectionnee(
            document_id=row['ID'],
            titre=row['Titre'],
            categorie=category,
            cote_bordereau=f"P-{i+1}"
        )
    
    # Générer le bordereau
    bordereau = generate_bordereau(pieces, {
        'type': 'Communication de pièces',
        'include_summary': True,
        'sort_by': 'Cote',
        'format': 'Tableau'
    })
    
    # Stocker le résultat
    st.session_state.bordereau_result = {
        'content': bordereau,
        'piece_count': len(pieces),
        'category': category,
        'timestamp': datetime.now()
    }
    
    st.success("✅ Bordereau créé")

def export_piece_selection(selected_df):
    """Exporte la sélection de pièces"""
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'piece_count': len(selected_df),
        'pieces': []
    }
    
    for _, row in selected_df.iterrows():
        export_data['pieces'].append({
            'id': row['ID'],
            'titre': row['Titre'],
            'source': row['Source']
        })
    
    json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Exporter la sélection",
        json_data,
        f"selection_pieces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="export_selection_json"
    )

def format_analysis_for_export(analysis_results: dict) -> str:
    """Formate les résultats d'analyse pour l'export"""
    if isinstance(analysis_results, dict):
        if 'analysis' in analysis_results:
            return analysis_results['analysis']
        else:
            return json.dumps(analysis_results, indent=2, ensure_ascii=False)
    else:
        return str(analysis_results)

def edit_template_interface():
    """Interface d'édition de template"""
    template_to_edit = st.session_state.get('template_to_edit')
    
    if template_to_edit:
        # Charger le template
        if template_to_edit in DOCUMENT_TEMPLATES:
            template = DOCUMENT_TEMPLATES[template_to_edit].copy()
            is_system = True
        else:
            template = st.session_state.saved_templates.get(template_to_edit, {})
            is_system = False
        
        if template:
            st.markdown(f"### ✏️ Édition du template : {template.get('name', template_to_edit)}")
            
            if is_system:
                st.warning("⚠️ Template système - Les modifications créeront une copie personnalisée")
            
            # Éditeur
            new_name = st.text_input(
                "Nom du template",
                value=template.get('name', ''),
                key="edit_template_name"
            )
            
            new_structure = st.text_area(
                "Structure (une section par ligne)",
                value='\n'.join(template.get('structure', [])),
                height=300,
                key="edit_template_structure"
            )
            
            new_style = st.selectbox(
                "Style par défaut",
                list(REDACTION_STYLES.keys()),
                index=list(REDACTION_STYLES.keys()).index(template.get('style', 'formel')),
                format_func=lambda x: REDACTION_STYLES[x]['name'],
                key="edit_template_style"
            )
            
            # Sauvegarder
            if st.button("💾 Sauvegarder les modifications", key="save_template_edits"):
                updated_template = {
                    'name': new_name,
                    'structure': new_structure.split('\n'),
                    'style': new_style,
                    'modified_date': datetime.now()
                }
                
                # Si c'est un template système, créer une copie
                if is_system:
                    new_id = f"custom_{template_to_edit}"
                    st.session_state.saved_templates[new_id] = updated_template
                    st.success(f"✅ Template personnalisé '{new_name}' créé")
                else:
                    st.session_state.saved_templates[template_to_edit] = updated_template
                    st.success(f"✅ Template '{new_name}' mis à jour")

def apply_template_interface():
    """Interface d'application de template"""
    selected_template = st.session_state.get('selected_template')
    
    if selected_template:
        # Charger le template
        if selected_template in DOCUMENT_TEMPLATES:
            template = DOCUMENT_TEMPLATES[selected_template]
        else:
            template = st.session_state.saved_templates.get(selected_template, {})
        
        if template:
            st.info(f"📄 Application du template : {template.get('name', selected_template)}")
            
            # Si le template a des variables, les demander
            if template.get('variables'):
                st.markdown("**Remplir les variables :**")
                
                variable_values = {}
                for var in template['variables']:
                    variable_values[var] = st.text_input(
                        var.replace('_', ' ').title(),
                        key=f"var_{var}"
                    )
                
                # Appliquer le template
                if st.button("✅ Appliquer le template", key="apply_template_now"):
                    st.session_state.universal_query = f"rédiger avec template {selected_template}"
                    st.session_state.template_variables = variable_values
                    st.rerun()

def search_relevant_jurisprudence(analysis: dict) -> list:
    """Recherche automatique de jurisprudence pertinente"""
    jurisprudence = []
    
    try:
        # Utiliser les termes de l'analyse
        keywords = []
        
        if analysis.get('subject_matter'):
            # Mapping infractions -> mots-clés
            juris_keywords = {
                'abus_biens_sociaux': ['abus biens sociaux', 'article L241-3'],
                'escroquerie': ['escroquerie', 'article 313-1'],
                'abus_confiance': ['abus confiance', 'article 314-1'],
                'faux': ['faux écritures', 'article 441-1'],
                'corruption': ['corruption', 'article 432-11'],
                'blanchiment': ['blanchiment', 'article 324-1']
            }
            
            keywords.extend(juris_keywords.get(analysis['subject_matter'], []))
        
        if keywords:
            # Recherche simplifiée
            jurisprudence = search_jurisprudence_unified(
                keywords,
                ['legifrance'],
                {'max_results': 10}
            )
    
    except Exception as e:
        print(f"Erreur recherche jurisprudence auto : {e}")
    
    return jurisprudence

def analyze_jurisprudence_trends(results: list):
    """Analyse les tendances jurisprudentielles"""
    st.info("📊 Analyse des tendances jurisprudentielles en développement")

def integrate_jurisprudence_in_document(results: list):
    """Intègre la jurisprudence dans un document"""
    if results:
        # Créer un prompt pour intégrer la jurisprudence
        juris_text = "\n\n".join([
            f"{r.get('title', 'Sans titre')} ({r.get('date', 'N/A')})\n{r.get('summary', '')}"
            for r in results[:5]
        ])
        
        st.session_state.universal_query = f"rédiger en intégrant cette jurisprudence : {juris_text[:200]}..."
        st.rerun()

def export_jurisprudence_results(results: list):
    """Exporte les résultats de jurisprudence"""
    export_content = "RECHERCHE JURISPRUDENTIELLE\n" + "=" * 50 + "\n\n"
    export_content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    export_content += f"Résultats : {len(results)}\n\n"
    
    for i, result in enumerate(results, 1):
        export_content += f"\n{i}. {result.get('title', 'Sans titre')}\n"
        export_content += f"   Juridiction : {result.get('jurisdiction', 'N/A')}\n"
        export_content += f"   Date : {result.get('date', 'N/A')}\n"
        export_content += f"   Référence : {result.get('reference', 'N/A')}\n"
        
        if result.get('summary'):
            export_content += f"   Résumé : {result['summary']}\n"
        
        if result.get('url'):
            export_content += f"   Lien : {result['url']}\n"
        
        export_content += "\n"
    
    st.download_button(
        "💾 Exporter la jurisprudence",
        export_content,
        f"jurisprudence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
        key="export_juris_txt"
    )

# === POINT D'ENTRÉE DU MODULE ===

if __name__ == "__main__":
    # Pour les tests
    show_page()