# modules/recherche.py
"""Module de recherche unifié - Interface principale avec toutes les fonctionnalités"""

import streamlit as st
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict
import pandas as pd

# Import des managers depuis le package managers
try:
    # Import du service de recherche principal
    from managers.universal_search_service import UniversalSearchService, Document, QueryAnalysis, SearchResult
    
    # Import des autres managers disponibles
    from managers.azure_blob_manager import AzureBlobManager
    from managers.azure_search_manager import AzureSearchManager
    from managers.multi_llm_manager import MultiLLMManager
    from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
    from managers.document_manager import DocumentManager
    from managers.company_info_manager import CompanyInfoManager
    from managers.legal_search import LegalSearchManager
    from managers.style_analyzer import StyleAnalyzer
    from managers.dynamic_generators import DynamicGenerators
    
    MANAGERS_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Erreur d'import des managers : {e}")
    MANAGERS_AVAILABLE = False

# ========================= CONFIGURATION =========================

# Styles de rédaction
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

# Templates de documents prédéfinis
DOCUMENT_TEMPLATES = {
    'conclusions_defense': {
        'name': 'Conclusions en défense',
        'structure': [
            'I. FAITS ET PROCÉDURE',
            'II. DISCUSSION',
            ' A. Sur la recevabilité',
            ' B. Sur le fond',
            ' 1. Sur l\'élément matériel',
            ' 2. Sur l\'élément intentionnel',
            ' 3. Sur le préjudice',
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

# ========================= IMPORTS DES MODÈLES =========================

try:
    # Import des modèles
    from models.dataclasses import (
        PieceSelectionnee, 
        AnalyseJuridique,
        InfractionIdentifiee
    )
    
    # Import de la configuration
    from config.app_config import (
        InfractionAffaires,
        ANALYSIS_PROMPTS_AFFAIRES,
        ANALYSIS_PROMPTS_INFRACTIONS,
        LLMProvider,
        SearchMode,
        app_config,
        api_config
    )
    
    MODELS_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Import manquant : {e}")
    MODELS_AVAILABLE = False

# ========================= INITIALISATION =========================

def init_search_service():
    """Initialise le service de recherche universel"""
    if 'search_service' not in st.session_state:
        st.session_state.search_service = UniversalSearchService()
    return st.session_state.search_service

# ========================= PAGE PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    # Initialiser le service de recherche
    search_service = init_search_service()
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        default_value = ""
        if 'pending_query' in st.session_state:
            default_value = st.session_state.pending_query
            del st.session_state.pending_query
        elif 'universal_query' in st.session_state:
            default_value = st.session_state.universal_query

        query = st.text_input(
            "Entrez votre commande ou recherche",
            value=default_value,
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique")
    
    with col2:
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Suggestions de commandes
    with st.expander("💡 Exemples de commandes", expanded=False):
        st.markdown("""
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        
        **Analyse :**
        - `analyser les risques @dossier_pénal`
        - `identifier les infractions @affaire_corruption`
        
        **Rédaction :**
        - `rédiger conclusions défense @affaire_martin abus biens sociaux`
        - `créer plainte avec constitution partie civile escroquerie`
        - `rédiger plainte contre Vinci, SOGEPROM @projet_26_05_2025`
        
        **Plaidoirie & Préparation :**
        - `préparer plaidoirie @affaire_martin audience correctionnelle`
        - `préparer client interrogatoire @dossier_fraude`
        
        **Visualisations :**
        - `chronologie des faits @affaire_martin`
        - `cartographie des sociétés @groupe_abc`
        - `comparer les auditions @témoins`
        
        **Gestion :**
        - `sélectionner pièces @dossier catégorie procédure`
        - `créer bordereau @pièces_sélectionnées`
        - `importer documents PDF`
        - `exporter analyse format word`
        - `envoyer par email @destinataire`
        """)
    
    # Menu d'actions rapides
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Nouvelle rédaction", key="quick_redaction"):
            st.session_state.pending_query = "rédiger "
            st.session_state.process_query = True
            st.rerun()

    with col2:
        if st.button("🤖 Analyser dossier", key="quick_analysis"):
            st.session_state.pending_query = "analyser "
            st.session_state.process_query = True
            st.rerun()

    with col3:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.pending_query = "importer documents"
            st.session_state.process_query = True
            st.rerun()
    
    with col4:
        if st.button("🔄 Réinitialiser", key="quick_reset"):
            clear_universal_state()
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            process_universal_query(query)
    
    # Afficher les résultats
    show_unified_results_tab()
    
    # Réinitialiser le flag de traitement
    if 'process_query' in st.session_state:
        st.session_state.process_query = False
    
    # Footer avec actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder le travail", key="save_work"):
            save_current_work()
    
    with col2:
        if st.button("📊 Afficher les statistiques", key="show_stats"):
            asyncio.run(show_work_statistics())
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            share_current_work()

# ========================= ROUTING ET TRAITEMENT =========================

def process_universal_query(query: str):
    """Traite une requête universelle et route vers la bonne fonction"""
    
    # Sauvegarder la requête
    st.session_state.last_universal_query = query
    
    # Utiliser le service de recherche pour analyser la requête
    search_service = init_search_service()
    query_analysis = search_service.analyze_query_advanced(query)
    
    # Router selon le type de commande détecté
    if query_analysis.command_type == 'plainte':
        st.info("📝 Détection d'une demande de plainte...")
        process_plainte_request(query, query_analysis)
    
    elif query_analysis.command_type == 'redaction':
        st.info("📝 Détection d'une demande de rédaction...")
        process_redaction_request(query, query_analysis)
    
    elif query_analysis.command_type == 'plaidoirie':
        st.info("🎤 Détection d'une demande de plaidoirie...")
        process_plaidoirie_request(query, query_analysis)
    
    elif query_analysis.command_type == 'preparation_client':
        st.info("👥 Détection d'une demande de préparation client...")
        process_preparation_client_request(query, query_analysis)
    
    elif query_analysis.command_type == 'import':
        st.info("📥 Détection d'une demande d'import...")
        process_import_request(query, query_analysis)
    
    elif query_analysis.command_type == 'export':
        st.info("💾 Détection d'une demande d'export...")
        process_export_request(query, query_analysis)
    
    elif query_analysis.command_type == 'email':
        st.info("📧 Détection d'une demande d'email...")
        process_email_request(query, query_analysis)
    
    elif query_analysis.command_type == 'analysis':
        st.info("🤖 Détection d'une demande d'analyse...")
        process_analysis_request(query, query_analysis)
    
    elif query_analysis.command_type == 'piece_selection':
        st.info("📋 Détection d'une demande de sélection de pièces...")
        process_piece_selection_request(query, query_analysis)
    
    elif query_analysis.command_type == 'bordereau':
        st.info("📊 Détection d'une demande de bordereau...")
        process_bordereau_request(query, query_analysis)
    
    elif query_analysis.command_type == 'synthesis':
        st.info("📝 Détection d'une demande de synthèse...")
        process_synthesis_request(query, query_analysis)
    
    elif query_analysis.command_type == 'template':
        st.info("📄 Détection d'une demande de template...")
        process_template_request(query, query_analysis)
    
    elif query_analysis.command_type == 'jurisprudence':
        st.info("⚖️ Détection d'une demande de jurisprudence...")
        process_jurisprudence_request(query, query_analysis)
    
    elif query_analysis.command_type == 'timeline':
        st.info("⏱️ Détection d'une demande de chronologie...")
        process_timeline_request(query, query_analysis)
    
    elif query_analysis.command_type == 'mapping':
        st.info("🗺️ Détection d'une demande de cartographie...")
        process_mapping_request(query, query_analysis)
    
    elif query_analysis.command_type == 'comparison':
        st.info("🔄 Détection d'une demande de comparaison...")
        process_comparison_request(query, query_analysis)
    
    else:
        # Recherche simple par défaut
        st.info("🔍 Recherche simple...")
        process_search_request(query, query_analysis)

# ========================= TRAITEMENT DE LA PLAINTE =========================

def process_plainte_request(query: str, query_analysis: QueryAnalysis):
    """Traite spécifiquement une demande de plainte"""
    
    query_lower = query.lower()
    
    # Déterminer le type de plainte
    is_partie_civile = any(term in query_lower for term in [
        'partie civile', 'constitution de partie civile', 'cpc', 
        'doyen', 'juge d\'instruction', 'instruction'
    ])
    
    # Débogage
    st.write("🔍 Analyse de la demande de plainte...")
    if is_partie_civile:
        st.info("📋 Type : Plainte avec constitution de partie civile (au Doyen des Juges d'Instruction)")
    else:
        st.info("📋 Type : Plainte simple (au Procureur de la République)")
    
    # Utiliser les données extraites par le service
    parties_demanderesses = query_analysis.parties['demandeurs']
    parties_defenderesses = query_analysis.parties['defendeurs']
    infractions_detectees = query_analysis.infractions
    reference = query_analysis.reference
    
    # Enrichir les informations des parties avec CompanyInfoManager
    company_manager = None
    if MANAGERS_AVAILABLE:
        try:
            company_manager = CompanyInfoManager()
        except:
            pass
    
    # Afficher les parties extraites
    st.write("✅ Demandeurs identifiés :", parties_demanderesses)
    st.write("⚖️ Défendeurs identifiés :", parties_defenderesses)
    st.write("🎯 Infractions détectées :", infractions_detectees)
    if reference:
        st.write(f"📁 Référence : @{reference}")
    
    # Enrichir les informations des parties avec CompanyInfoManager
    if company_manager and (parties_demanderesses or parties_defenderesses):
        with st.expander("🏢 Informations détaillées des parties", expanded=False):
            for partie in parties_demanderesses:
                info = company_manager.get_company_info(partie)
                if info:
                    st.markdown(f"**{partie}**")
                    st.json(info)
    
    # Recherche de modèle de date
    modele = None
    date_patterns = [
        r'(\d{1,2}[\s\-/]\d{1,2}[\s\-/]\d{2,4})',
        r'(\d{1,2}\s+\w+\s+\d{2,4})'
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, query)
        if date_match:
            modele = f"Modèle du {date_match.group(1)}"
            st.write(f"📅 {modele}")
            break
    
    # Validation et suggestions
    st.markdown("### 📋 Résumé de l'analyse")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🏢 Demandeurs (victimes) :**")
        if parties_demanderesses:
            for p in parties_demanderesses:
                st.write(f"• {p}")
        else:
            st.warning("❌ Aucun demandeur identifié")
            st.info("💡 Précisez : 'pour [société X]'")
    
    with col2:
        st.markdown("**⚖️ Défendeurs (mis en cause) :**")
        if parties_defenderesses:
            for p in parties_defenderesses:
                st.write(f"• {p}")
        else:
            st.warning("❌ Aucun défendeur identifié")
            st.info("💡 Précisez : 'contre [M. X]'")
    
    with col3:
        st.markdown("**🎯 Infractions :**")
        if infractions_detectees:
            for inf in infractions_detectees[:3]:  # Limiter l'affichage
                st.write(f"• {inf}")
            if len(infractions_detectees) > 3:
                st.write(f"• + {len(infractions_detectees) - 3} autres")
        else:
            st.info("📌 Infractions standards")
    
    # Options supplémentaires
    with st.expander("⚙️ Options de la plainte", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Forcer le type de plainte
            type_force = st.radio(
                "Type de plainte",
                ["Auto-détection", "Plainte simple", "Plainte avec CPC"],
                index=0 if not is_partie_civile else 2,
                key="type_plainte_force"
            )
            
            if type_force == "Plainte simple":
                is_partie_civile = False
            elif type_force == "Plainte avec CPC":
                is_partie_civile = True
        
        with col2:
            # Options de contenu
            st.markdown("**Options de contenu :**")
            include_chronologie = st.checkbox("Inclure chronologie détaillée", value=True)
            include_prejudices = st.checkbox("Détailler les préjudices", value=True)
            include_jurisprudence = st.checkbox("Citer jurisprudences", value=is_partie_civile)
            
            # Utiliser StyleAnalyzer si disponible
            if MANAGERS_AVAILABLE and StyleAnalyzer:
                use_style_analysis = st.checkbox("Analyser le style optimal", value=False)
            else:
                use_style_analysis = False
    
    # Créer la demande de rédaction enrichie
    st.session_state.redaction_request = {
        'type': 'plainte_avec_cpc' if is_partie_civile else 'plainte_simple',
        'demandeurs': parties_demanderesses,
        'defendeurs': parties_defenderesses,
        'infractions': infractions_detectees,
        'reference': reference,
        'modele': modele,
        'query': query,
        'options': {
            'chronologie': include_chronologie if 'include_chronologie' in locals() else True,
            'prejudices': include_prejudices if 'include_prejudices' in locals() else True,
            'jurisprudence': include_jurisprudence if 'include_jurisprudence' in locals() else is_partie_civile,
            'style_analysis': use_style_analysis if 'use_style_analysis' in locals() else False
        }
    }
    
    # Bouton de génération manuel
    if st.button("🚀 Générer la plainte", type="primary", key="generate_plainte_btn"):
        # Générer la plainte avec toutes les parties
        toutes_parties = parties_demanderesses + parties_defenderesses
        generate_plainte(query, toutes_parties, query_analysis)
    
    # Ou génération automatique si parties identifiées
    elif parties_demanderesses or parties_defenderesses:
        toutes_parties = parties_demanderesses + parties_defenderesses
        generate_plainte(query, toutes_parties, query_analysis)
    else:
        st.error("❌ Impossible d'identifier les parties dans la requête")
        
        # Formulaire pour saisir manuellement
        with st.form("saisie_parties"):
            st.markdown("### 📝 Saisie manuelle des parties")
            
            demandeurs_manuel = st.text_area(
                "Demandeurs (un par ligne)",
                placeholder="INTERCONSTRUCTION\nVINCI\nSOGEPROM RÉALISATIONS",
                height=100
            )
            
            defendeurs_manuel = st.text_area(
                "Défendeurs (un par ligne)",
                placeholder="M. PERINET\nVP INVEST",
                height=100
            )
            
            if st.form_submit_button("Générer avec ces parties"):
                if demandeurs_manuel or defendeurs_manuel:
                    parties_demanderesses = [p.strip() for p in demandeurs_manuel.split('\n') if p.strip()]
                    parties_defenderesses = [p.strip() for p in defendeurs_manuel.split('\n') if p.strip()]
                    toutes_parties = parties_demanderesses + parties_defenderesses
                    # Mettre à jour l'analyse
                    query_analysis.parties['demandeurs'] = parties_demanderesses
                    query_analysis.parties['defendeurs'] = parties_defenderesses
                    generate_plainte(query, toutes_parties, query_analysis)
                else:
                    st.error("Veuillez saisir au moins une partie")

# ========================= AFFICHAGE DES RÉSULTATS =========================

def show_unified_results_tab():
    """Affiche tous les types de résultats dans un onglet unifié"""
    
    has_results = False
    
    # RÉSULTATS DE RÉDACTION (Priorité 1)
    if st.session_state.get('redaction_result'):
        show_redaction_results()
        has_results = True
    
    # RÉSULTATS D'ANALYSE IA (Priorité 2)
    elif st.session_state.get('ai_analysis_results'):
        show_ai_analysis_results()
        has_results = True
    
    # RÉSULTATS DE RECHERCHE (Priorité 3)
    elif st.session_state.get('search_results'):
        show_search_results()
        has_results = True
    
    # RÉSULTATS DE SYNTHÈSE (Priorité 4)
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        has_results = True
    
    # RÉSULTATS DE TIMELINE (Priorité 5)
    elif st.session_state.get('timeline_result'):
        show_timeline_results()
        has_results = True
    
    # Message si aucun résultat
    if not has_results:
        st.info("💡 Utilisez la barre de recherche universelle pour commencer")
        
        # Suggestions d'utilisation
        st.markdown("""
        ### 🚀 Exemples de commandes
        
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        
        **Analyse :**
        - `analyser les risques @dossier_pénal`
        - `identifier les infractions @affaire_corruption`
        
        **Rédaction :**
        - `rédiger conclusions défense @affaire_martin`
        - `créer plainte contre Vinci, SOGEPROM`
        
        **Gestion :**
        - `importer documents PDF`
        - `exporter analyse format word`
        """)

def show_redaction_results():
    """Affiche les résultats de rédaction"""
    result = st.session_state.redaction_result
    
    st.markdown("### 📝 Document juridique généré")
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        doc_icons = {
            'conclusions': '⚖️ Conclusions',
            'plainte': '📋 Plainte',
            'plainte_simple': '📋 Plainte simple',
            'plainte_avec_cpc': '📋 Plainte avec CPC',
            'courrier': '✉️ Courrier',
            'assignation': '📜 Assignation'
        }
        st.metric("Type", doc_icons.get(result['type'], '📄 Document'))
    
    with col2:
        st.metric("Généré par", result.get('provider', 'IA'))
    
    with col3:
        word_count = len(result['document'].split())
        st.metric("Mots", f"{word_count:,}")
    
    with col4:
        char_count = len(result['document'])
        st.metric("Caractères", f"{char_count:,}")
    
    # Zone d'édition principale
    st.markdown("#### 📄 Contenu du document")
    
    edited_content = st.text_area(
        "Vous pouvez éditer le document",
        value=result['document'],
        height=600,
        key="edit_redaction_main"
    )
    
    # Barre d'outils
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🔄 Régénérer", key="regenerate_main"):
            st.session_state.process_query = True
            st.rerun()
    
    with col2:
        if st.button("📊 Statistiques", key="document_stats"):
            show_document_statistics(edited_content)
    
    with col3:
        # Export Word
        st.download_button(
            "📄 Word",
            edited_content.encode('utf-8'),
            f"{result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    with col4:
        # Export texte
        st.download_button(
            "📝 Texte",
            edited_content.encode('utf-8'),
            f"{result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col5:
        if st.button("📧 Envoyer", key="prepare_email_main"):
            st.session_state.pending_email = {
                'content': edited_content,
                'type': result['type']
            }

def show_ai_analysis_results():
    """Affiche les résultats d'analyse IA avec vérification des jurisprudences"""
    results = st.session_state.ai_analysis_results
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    analysis_titles = {
        'risk_analysis': '⚠️ Analyse des risques',
        'compliance': '✅ Analyse de conformité',
        'strategy': '🎯 Analyse stratégique',
        'general_analysis': '🤖 Analyse générale',
        'infractions': '🎯 Analyse infractions économiques'
    }
    
    st.markdown(f"### {analysis_titles.get(results.get('type'), '🤖 Analyse IA')}")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents analysés", results.get('document_count', 0))
    with col2:
        st.metric("Type", results.get('type', 'general').replace('_', ' ').title())
    with col3:
        st.metric("Généré le", results.get('timestamp', datetime.now()).strftime('%H:%M'))
    
    # Contenu de l'analyse
    st.markdown("#### 📊 Résultats de l'analyse")
    
    analysis_content = st.text_area(
        "Analyse détaillée",
        value=results.get('content', ''),
        height=600,
        key="ai_analysis_content"
    )
    
    # Vérification des jurisprudences
    if st.checkbox("🔍 Vérifier les jurisprudences citées", key="verify_juris_check"):
        verify_jurisprudences_in_analysis(analysis_content)
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "💾 Télécharger",
            analysis_content.encode('utf-8'),
            f"analyse_{results.get('type', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("🔄 Approfondir", key="deepen_analysis"):
            st.session_state.pending_deepen_analysis = True

def show_search_results():
    """Affiche les résultats de recherche"""
    results = st.session_state.search_results
    
    # Si results est un objet SearchResult
    if hasattr(results, 'documents'):
        documents = results.documents
        total_count = results.total_count
    else:
        # Si c'est une liste simple
        documents = results
        total_count = len(results)
    
    st.markdown(f"### 🔍 Résultats de recherche ({total_count} documents)")
    
    if not documents:
        st.info("Aucun résultat trouvé")
        return
    
    # Options d'affichage
    col1, col2 = st.columns(2)
    
    with col1:
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Titre", "Date", "Source"],
            key="sort_search_results"
        )
    
    with col2:
        view_mode = st.radio(
            "Affichage",
            ["Compact", "Détaillé"],
            key="view_mode_search",
            horizontal=True
        )
    
    # Afficher les résultats
    for i, doc in enumerate(documents[:20], 1):  # Limiter à 20
        with st.container():
            # Gestion selon le type de doc (Document object ou dict)
            if hasattr(doc, 'title'):
                # C'est un objet Document
                title = doc.title
                source = doc.source
                content = doc.content
                score = doc.metadata.get('score', 0) if hasattr(doc, 'metadata') else 0
            else:
                # C'est un dictionnaire
                title = doc.get('title', 'Sans titre')
                source = doc.get('source', 'N/A')
                content = doc.get('content', '')
                score = doc.get('score', 0)
            
            if view_mode == "Compact":
                st.markdown(f"**{i}. {title}**")
                st.caption(f"Source: {source} | Score: {score:.0%}")
            else:
                st.markdown(f"**{i}. {title}**")
                st.caption(f"Source: {source} | Score: {score:.0%}")
                
                # Extrait
                if content:
                    st.text_area(
                        "Extrait",
                        value=content[:500] + '...' if len(content) > 500 else content,
                        height=150,
                        key=f"extract_{i}",
                        disabled=True
                    )
            
            st.divider()

def show_synthesis_results():
    """Affiche les résultats de synthèse"""
    result = st.session_state.synthesis_result
    
    if 'error' in result:
        st.error(f"❌ {result['error']}")
        return
    
    st.markdown("### 📝 Synthèse des documents")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pièces analysées", result.get('piece_count', 0))
    with col2:
        st.metric("Catégories", len(result.get('categories', [])))
    with col3:
        st.metric("Généré le", result.get('timestamp', datetime.now()).strftime('%H:%M'))
    
    # Contenu
    synthesis_content = st.text_area(
        "Contenu de la synthèse",
        value=result.get('content', ''),
        height=600,
        key="synthesis_content_display"
    )
    
    # Actions
    if st.download_button(
        "💾 Télécharger",
        synthesis_content.encode('utf-8'),
        f"synthese_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain"
    ):
        st.success("✅ Synthèse téléchargée")

def show_timeline_results():
    """Affiche les résultats de chronologie"""
    result = st.session_state.timeline_result
    
    st.markdown(f"### ⏱️ Chronologie")
    
    # Affichage simple
    for event in result.get('events', []):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(f"**{event.get('date', 'N/A')}**")
        with col2:
            st.write(event.get('description', ''))
            if event.get('actors'):
                st.caption(f"👥 {', '.join(event['actors'])}")

# ========================= GÉNÉRATION DE PLAINTE =========================

def generate_plainte(query: str, parties: list, query_analysis: QueryAnalysis):
    """Génère une plainte simple ou avec constitution de partie civile"""
    
    try:
        # Débogage
        st.write("🔍 Génération de la plainte en cours...")
        st.write(f"Requête originale : {query}")
        
        # Initialiser le manager
        llm_manager = MultiLLMManager()
        
        # Debug pour voir les clients disponibles
        llm_manager.debug_status()
        
        if not llm_manager.clients:
            st.error("❌ Aucune IA n'est configurée")
            st.info("💡 Veuillez configurer au moins une clé API dans les variables d'environnement")
            
            # Afficher les instructions détaillées
            with st.expander("📋 Instructions de configuration"):
                st.markdown("""
                **Sur Hugging Face Spaces :**
                1. Allez dans Settings → Variables and secrets
                2. Ajoutez une ou plusieurs de ces clés :
                   - `OPENAI_API_KEY` - Pour GPT-4
                   - `ANTHROPIC_API_KEY` - Pour Claude 3
                   - `GOOGLE_API_KEY` - Pour Gemini
                   - `MISTRAL_API_KEY` - Pour Mistral
                   - `GROQ_API_KEY` - Pour Groq (Mixtral)
                
                **Recommandé :** Au moins une clé parmi OpenAI, Anthropic ou Google
                """)
            return
        
        # Afficher les providers disponibles
        providers = llm_manager.get_available_providers()
        st.success(f"✅ {len(providers)} IA(s) disponible(s) : {', '.join(providers)}")
        
        # DÉTERMINER LE TYPE DE PLAINTE
        query_lower = query.lower()
        is_partie_civile = any(term in query_lower for term in [
            'partie civile', 'constitution de partie civile', 'cpc', 
            'doyen', 'juge d\'instruction', 'instruction'
        ])
        
        type_plainte = 'plainte_avec_cpc' if is_partie_civile else 'plainte_simple'
        destinataire = "Monsieur le Doyen des Juges d'Instruction" if is_partie_civile else "Monsieur le Procureur de la République"
        
        st.info(f"📋 Type détecté : {'Plainte avec constitution de partie civile' if is_partie_civile else 'Plainte simple au Procureur'}")
        
        # Utiliser les données de l'analyse
        parties_demanderesses = query_analysis.parties['demandeurs']
        parties_defenderesses = query_analysis.parties['defendeurs']
        infractions_mentionnees = query_analysis.infractions
        reference = query_analysis.reference
        
        # Si pas d'infractions détectées, ajouter les infractions complètes avec articles
        if not infractions_mentionnees:
            infractions_mentionnees = [
                'Escroquerie (art. 313-1 Code pénal)',
                'Abus de confiance (art. 314-1 Code pénal)',
                'Faux et usage de faux (art. 441-1 Code pénal)'
            ]
        else:
            # Enrichir avec les articles de loi
            infractions_articles = {
                'Escroquerie': 'Escroquerie (art. 313-1 Code pénal)',
                'Abus de confiance': 'Abus de confiance (art. 314-1 Code pénal)',
                'Abus de biens sociaux': 'Abus de biens sociaux (art. L241-3 et L242-6 Code de commerce)',
                'Faux et usage de faux': 'Faux et usage de faux (art. 441-1 Code pénal)',
                'Corruption': 'Corruption (art. 432-11 et 433-1 Code pénal)',
                'Trafic d\'influence': 'Trafic d\'influence (art. 432-11 et 433-2 Code pénal)',
                'Favoritisme': 'Favoritisme (art. 432-14 Code pénal)',
                'Prise illégale d\'intérêts': 'Prise illégale d\'intérêts (art. 432-12 Code pénal)',
                'Blanchiment': 'Blanchiment (art. 324-1 Code pénal)',
                'Fraude fiscale': 'Fraude fiscale (art. 1741 Code général des impôts)',
                'Travail dissimulé': 'Travail dissimulé (art. L8221-3 Code du travail)',
                'Marchandage': 'Marchandage (art. L8231-1 Code du travail)',
                'Entrave': 'Entrave (art. L2328-1 Code du travail)',
                'Banqueroute': 'Banqueroute (art. L654-2 Code de commerce)',
                'Recel': 'Recel (art. 321-1 Code pénal)'
            }
            infractions_mentionnees = [infractions_articles.get(inf, inf) for inf in infractions_mentionnees]
        
        # Référence au modèle
        if '26 05 2025' in query or '26/05/2025' in query or '26-05-2025' in query:
            reference = "projet de complément de plainte du 26/05/2025"
        
        # Afficher les informations extraites
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏢 Demandeurs (victimes) :**")
            for partie in parties_demanderesses:
                st.write(f"• {partie}")
            
            st.markdown("**📋 Infractions visées :**")
            for infraction in infractions_mentionnees[:5]:  # Limiter l'affichage
                st.write(f"• {infraction}")
        
        with col2:
            st.markdown("**⚖️ Défendeurs (mis en cause) :**")
            for partie in parties_defenderesses:
                st.write(f"• {partie}")
            
            if reference:
                st.info(f"📄 Modèle : {reference}")
        
        # CONSTRUIRE LE PROMPT SELON LE TYPE DE PLAINTE
        if is_partie_civile:
            # Prompt pour plainte avec constitution de partie civile
            plainte_prompt = f"""Tu es un avocat pénaliste expert en droit pénal des affaires avec 25 ans d'expérience. Tu maîtrises particulièrement les affaires complexes de criminalité économique et financière.

MISSION : Rédiger une plainte avec constitution de partie civile EXHAUSTIVE et PERCUTANTE pour un dossier complexe.

CONTEXTE DE LA REQUÊTE :
{query}

PARTIES IDENTIFIÉES :
- Demandeurs (victimes) : {', '.join(parties_demanderesses) if parties_demanderesses else '[À COMPLÉTER]'}
- Défendeurs (mis en cause) : {', '.join(parties_defenderesses) if parties_defenderesses else '[À IDENTIFIER dans les faits]'}
- Référence : {reference if reference else 'Dossier complexe de criminalité économique'}

INFRACTIONS À EXAMINER :
{chr(10).join(f'- {inf}' for inf in infractions_mentionnees)}

INSTRUCTIONS POUR UNE PLAINTE EXHAUSTIVE :

1. **EN-TÊTE FORMEL**
   {destinataire}
   Tribunal judiciaire de [DÉTERMINER selon le siège social]
   [Adresse complète]
   
   Date : [Date du jour]
   
   OBJET : PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE
   
   Références : {reference if reference else 'Votre réf. : / Notre réf. : '}

2. **IDENTIFICATION COMPLÈTE DES PARTIES**
   
   POUR :
   {chr(10).join(f'   - {p}, société [FORME JURIDIQUE À PRÉCISER - SA/SARL/SAS], au capital de [MONTANT] euros, immatriculée au RCS de [VILLE] sous le numéro [NUMÉRO], dont le siège social est situé [ADRESSE COMPLÈTE], représentée par [PRÉSIDENT/GÉRANT], dûment habilité' for p in parties_demanderesses)}
   
   Ayant pour conseil :
   Maître [NOM], Avocat au Barreau de [VILLE]
   [Adresse complète du cabinet]
   Tél : [NUMÉRO] - Email : [EMAIL]
   
   CONTRE :
   {chr(10).join(f'   - {p}, [COMPLÉTER : né le XX/XX/XXXX à VILLE si personne physique OU forme juridique si société], demeurant/siège social [ADRESSE]' for p in parties_defenderesses)}
   
   ET CONTRE :
   - Toute autre personne que l'instruction révélerait comme auteur, coauteur ou complice des faits dénoncés

3. **EXPOSÉ EXHAUSTIF DES FAITS** (PARTIE CRUCIALE - MINIMUM 3000 MOTS)
   
   A. CONTEXTE GÉNÉRAL ET HISTORIQUE DES RELATIONS
      - Genèse du projet/de la relation d'affaires
      - Chronologie détaillée des événements
      - Acteurs impliqués et leurs rôles respectifs
      - Documents contractuels de référence
   
   B. MÉCANISME FRAUDULEUX DÉTAILLÉ
      - Description précise du montage frauduleux
      - Modus operandi des mis en cause
      - Flux financiers suspects (avec montants)
      - Documents falsifiés ou manipulés
      - Témoignages et preuves matérielles
   
   C. DÉCOUVERTE DE LA FRAUDE
      - Circonstances de la découverte
      - Premiers indices et soupçons
      - Investigations menées
      - Confrontations éventuelles
   
   D. AGGRAVATION DU PRÉJUDICE
      - Manœuvres dilatoires
      - Dissimulation d'actifs
      - Tentatives d'intimidation
      - Destruction de preuves

4. **QUALIFICATION JURIDIQUE APPROFONDIE**
   
   Pour CHAQUE infraction, développer :
   
   A. L'ÉLÉMENT MATÉRIEL
      - Actes précis constituant l'infraction
      - Preuves matérielles (documents, emails, enregistrements)
      - Témoignages corroborants
      - Expertises éventuelles
   
   B. L'ÉLÉMENT INTENTIONNEL
      - Conscience de l'illégalité
      - Volonté de nuire
      - Préméditation
      - Mobile (enrichissement, vengeance, etc.)
   
   C. LE LIEN DE CAUSALITÉ
      - Lien direct entre les actes et le préjudice
      - Absence de cause étrangère
   
   D. CIRCONSTANCES AGGRAVANTES
      - Bande organisée
      - Abus de fonction
      - Vulnérabilité de la victime
      - Montant du préjudice

5. **ÉVALUATION DÉTAILLÉE DES PRÉJUDICES**
   
   Pour CHAQUE société demanderesse :
   
   A. PRÉJUDICE FINANCIER DIRECT
      - Détournements : [MONTANT] €
      - Surfacturations : [MONTANT] €
      - Manque à gagner : [MONTANT] €
      - Frais supplémentaires : [MONTANT] €
      SOUS-TOTAL : [MONTANT] € HT
   
   B. PRÉJUDICE FINANCIER INDIRECT
      - Perte de marchés : [MONTANT] €
      - Coûts de restructuration : [MONTANT] €
      - Frais d'expertise : [MONTANT] €
      - Frais de justice : [MONTANT] €
      SOUS-TOTAL : [MONTANT] € HT
   
   C. PRÉJUDICE MORAL ET COMMERCIAL
      - Atteinte à la réputation
      - Perte de confiance des partenaires
      - Désorganisation de l'entreprise
      - Souffrance morale des dirigeants
      ÉVALUATION : [MONTANT] € (provisoire)
   
   TOTAL GÉNÉRAL : [MONTANT] € (sous réserve d'augmentation)

6. **CONSTITUTION DE PARTIE CIVILE**
   
   Les sociétés demanderesses déclarent expressément se constituer partie civile dans la présente procédure et :
   
   - Consignent la somme de [3000 à 15000] euros à titre de consignation
   - Se réservent le droit de solliciter tous dommages-intérêts complémentaires
   - Demandent la condamnation solidaire des mis en cause
   - Sollicitent l'exécution provisoire de la décision à intervenir

7. **DEMANDES D'ACTES D'INSTRUCTION**
   
   Les parties civiles sollicitent :
   - Auditions des mis en cause et témoins
   - Perquisitions aux sièges sociaux et domiciles
   - Saisies conservatoires sur les biens
   - Expertises comptables et financières
   - Exploitation des données informatiques
   - Commissions rogatoires internationales si nécessaire
   - Interceptions téléphoniques si justifiées

8. **PAR CES MOTIFS**
   
   Les sociétés demanderesses demandent qu'il plaise à Monsieur le Doyen des Juges d'Instruction de :
   
   - RECEVOIR leur plainte avec constitution de partie civile
   - ORDONNER l'ouverture d'une information judiciaire
   - PROCÉDER à tous actes utiles à la manifestation de la vérité
   - TRANSMETTRE le dossier au Parquet pour réquisitions
   - DÉLIVRER récépissé de la présente plainte

9. **BORDEREAU DE PIÈCES DÉTAILLÉ**
   
   [Liste numérotée de 1 à XX avec description précise de chaque pièce]

10. **SOUS TOUTES RÉSERVES**
    
    Notamment de :
    - Compléter et préciser les présentes
    - Produire toutes pièces nouvelles
    - Se constituer partie civile contre toute autre personne
    - Modifier la qualification des faits
    - Majorer l'évaluation des préjudices

SIGNATURE
[Nom et qualité du signataire]

IMPORTANT : Cette plainte doit être EXHAUSTIVE (minimum 8000 mots), PRÉCISE (dates, montants, références), PERCUTANTE (démonstration implacable) et IRRÉFUTABLE (preuves solides)."""
        
        else:
            # Prompt pour plainte simple au Procureur
            plainte_prompt = f"""Tu es un avocat pénaliste expert en droit pénal des affaires. Tu dois rédiger une plainte simple mais complète et professionnelle.

CONTEXTE : {query}

PARTIES :
- Plaignants : {', '.join(parties_demanderesses) if parties_demanderesses else '[À IDENTIFIER]'}
- Mis en cause : {', '.join(parties_defenderesses) if parties_defenderesses else '[À IDENTIFIER]'}

STRUCTURE DE LA PLAINTE SIMPLE :

1. **EN-TÊTE**
   Monsieur le Procureur de la République
   Tribunal judiciaire de [VILLE]
   [Adresse]
   
   [Lieu], le [Date]
   
   OBJET : Plainte
   
   Lettre recommandée avec AR

2. **IDENTITÉ DU PLAIGNANT**
   Je soussigné(e) / Nous soussignons :
   [Identité complète avec adresse]

3. **EXPOSÉ DES FAITS**
   Développer de manière claire et chronologique :
   - Contexte
   - Faits reprochés
   - Préjudice subi
   - Preuves disponibles

4. **QUALIFICATION JURIDIQUE**
   Les faits exposés sont susceptibles de recevoir les qualifications suivantes :
   {chr(10).join(f'- {inf}' for inf in infractions_mentionnees)}

5. **PRÉJUDICE**
   Description et évaluation du préjudice subi

6. **DEMANDES**
   Je demande/Nous demandons :
   - L'ouverture d'une enquête
   - L'audition des personnes mises en cause
   - Toutes investigations utiles
   - L'engagement de poursuites

7. **PIÈCES JOINTES**
   Liste des pièces

8. **FORMULE FINALE**
   Je me tiens/Nous nous tenons à votre disposition...
   
   Signature

Rédige une plainte COMPLÈTE (minimum 3000 mots) et PROFESSIONNELLE."""
        
        # Sélectionner le meilleur provider disponible
        preferred_providers = ['anthropic', 'openai', 'google', 'mistral', 'groq']
        selected_provider = None
        
        for pref in preferred_providers:
            if pref in providers:
                selected_provider = pref
                break
        
        if not selected_provider:
            selected_provider = providers[0]
        
        st.info(f"🤖 Utilisation de : {selected_provider}")
        
        # Options de génération avancées
        with st.expander("⚙️ Options avancées", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                temperature = st.slider(
                    "Créativité",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="Plus bas = plus factuel, plus haut = plus créatif"
                )
            with col2:
                max_tokens = st.number_input(
                    "Longueur maximale",
                    min_value=2000,
                    max_value=10000,
                    value=8000,
                    step=1000,
                    help="Nombre de tokens maximum pour la réponse"
                )
        
        # Générer la plainte
        with st.spinner(f"⚖️ Génération de la {'plainte avec constitution de partie civile' if is_partie_civile else 'plainte simple'} via {selected_provider}..."):
            response = llm_manager.query_single_llm(
                selected_provider,
                plainte_prompt,
                "Tu es Maître Jean-Michel Durand, avocat au Barreau de Paris depuis 25 ans, spécialisé en droit pénal des affaires et criminalité en col blanc. Tu as plaidé dans les plus grandes affaires de corruption et d'escroquerie. Tu rédiges des plaintes qui ont mené à de nombreuses condamnations.",
                temperature=temperature if 'temperature' in locals() else 0.3,
                max_tokens=max_tokens if 'max_tokens' in locals() else 8000
            )
        
        if response['success']:
            # Enrichir la réponse si nécessaire
            document_final = response['response']
            
            # Vérifier que le document contient les éléments essentiels
            if is_partie_civile:
                elements_requis = [
                    "POUR :", "CONTRE :", "EXPOSÉ", "FAITS", 
                    "QUALIFICATION JURIDIQUE", "PRÉJUDICES", 
                    "CONSTITUTION DE PARTIE CIVILE", "DEMANDES"
                ]
            else:
                elements_requis = [
                    "Monsieur le Procureur", "EXPOSÉ DES FAITS", 
                    "QUALIFICATION", "DEMANDES"
                ]
            
            missing_elements = [elem for elem in elements_requis if elem.upper() not in document_final.upper()]
            
            if missing_elements:
                st.warning(f"⚠️ Éléments manquants détectés : {', '.join(missing_elements)}")
                st.info("💡 Vous pouvez éditer le document pour ajouter les sections manquantes")
            
            # Analyse de la qualité
            word_count = len(document_final.split())
            char_count = len(document_final)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mots", f"{word_count:,}")
                if word_count < 3000:
                    st.warning("⚠️ Document un peu court pour un dossier complexe")
            with col2:
                st.metric("Caractères", f"{char_count:,}")
            with col3:
                st.metric("Pages estimées", f"~{word_count // 250}")
            
            # Sauvegarder le résultat
            st.session_state.redaction_result = {
                'type': type_plainte,
                'document': document_final,
                'provider': selected_provider,
                'timestamp': datetime.now(),
                'metadata': {
                    'demandeurs': parties_demanderesses,
                    'defendeurs': parties_defenderesses,
                    'reference': reference,
                    'infractions': infractions_mentionnees,
                    'requete_originale': query,
                    'generation_time': response.get('elapsed_time', 0),
                    'word_count': word_count,
                    'destinataire': destinataire
                }
            }
            
            st.success(f"✅ {'Plainte avec constitution de partie civile' if is_partie_civile else 'Plainte simple'} générée avec succès !")
            
            # Proposer des actions supplémentaires
            st.markdown("### 🎯 Actions disponibles")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 Régénérer", key="regen_same"):
                    st.session_state.force_regenerate = True
                    st.rerun()
            
            with col2:
                if st.button("📈 Version plus détaillée", key="more_detailed"):
                    st.session_state.request_detailed = True
                    st.rerun()
            
            with col3:
                if st.button("🔀 Autre IA", key="try_other_ai"):
                    other_providers = [p for p in providers if p != selected_provider]
                    if other_providers:
                        st.session_state.next_provider = other_providers[0]
                        st.rerun()
            
            with col4:
                if st.button("📊 Comparer les IA", key="compare_all"):
                    st.session_state.compare_all_providers = True
                    st.rerun()
            
            # Suggestions d'amélioration
            with st.expander("💡 Suggestions d'amélioration", expanded=False):
                st.markdown("""
                **Pour enrichir votre plainte :**
                
                1. **Ajoutez des détails factuels** :
                   - Dates précises des faits
                   - Montants exacts des préjudices
                   - Noms complets et fonctions des personnes
                   - Références des contrats ou factures
                
                2. **Renforcez les preuves** :
                   - Emails et correspondances
                   - Rapports d'expertise
                   - Témoignages écrits
                   - Documents comptables
                
                3. **Précisez les infractions** :
                   - Articles de loi exacts
                   - Jurisprudences applicables
                   - Circonstances aggravantes
                
                4. **Complétez les demandes** :
                   - Mesures conservatoires
                   - Expertises judiciaires
                   - Auditions spécifiques
                """)
            
        else:
            st.error(f"❌ Erreur lors de la génération : {response.get('error', 'Erreur inconnue')}")
            
            # Proposer des alternatives
            if len(providers) > 1:
                st.info("💡 Essayez avec un autre provider disponible")
                for provider in providers:
                    if st.button(f"Essayer avec {provider}", key=f"try_{provider}"):
                        st.session_state.next_provider = provider
                        st.rerun()
            
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {str(e)}")
        with st.expander("🔍 Détails techniques"):
            import traceback
            st.code(traceback.format_exc())

# ========================= GESTION DES PIÈCES =========================

def process_piece_selection_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de sélection de pièces"""
    
    st.markdown("### 📋 Sélection de pièces")
    
    # Collecter les documents disponibles
    available_docs = collect_available_documents(analysis)
    
    if not available_docs:
        st.warning("⚠️ Aucun document disponible")
        return
    
    # Grouper par catégorie
    categories = group_documents_by_category(available_docs)
    
    # Interface de sélection
    selected_pieces = []
    
    for category, docs in categories.items():
        with st.expander(f"📁 {category} ({len(docs)} documents)", expanded=True):
            select_all = st.checkbox(f"Tout sélectionner - {category}", key=f"select_all_{category}")
            
            for doc in docs:
                is_selected = st.checkbox(
                    f"📄 {doc['title']}",
                    value=select_all,
                    key=f"select_doc_{doc['id']}",
                    help=f"Source: {doc.get('source', 'N/A')}"
                )
                
                if is_selected:
                    selected_pieces.append(PieceSelectionnee(
                        numero=len(selected_pieces) + 1,
                        titre=doc['title'],
                        description=doc.get('description', ''),
                        categorie=category,
                        date=doc.get('date'),
                        source=doc.get('source', ''),
                        pertinence=calculate_piece_relevance(doc, analysis)
                    ))
    
    # Sauvegarder la sélection
    st.session_state.selected_pieces = selected_pieces
    
    # Actions
    if selected_pieces:
        st.success(f"✅ {len(selected_pieces)} pièces sélectionnées")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Créer bordereau", key="create_bordereau_from_selection"):
                process_bordereau_request(query, analysis)
        
        with col2:
            if st.button("📄 Synthétiser", key="synthesize_selection"):
                synthesize_selected_pieces(selected_pieces)
        
        with col3:
            if st.button("📤 Exporter liste", key="export_piece_list"):
                export_piece_list(selected_pieces)

def process_bordereau_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de création de bordereau"""
    
    pieces = st.session_state.get('selected_pieces', [])
    
    if not pieces:
        st.warning("⚠️ Aucune pièce sélectionnée pour le bordereau")
        return
    
    # Créer le bordereau
    bordereau = create_bordereau(pieces, analysis)
    
    # Afficher
    st.markdown("### 📊 Bordereau de communication de pièces")
    
    # En-tête
    st.text_area(
        "En-tête du bordereau",
        value=bordereau['header'],
        height=150,
        key="bordereau_header"
    )
    
    # Table des pièces
    try:
        df = pd.DataFrame([
            {
                'N°': p.numero,
                'Titre': p.titre,
                'Description': p.description,
                'Catégorie': p.categorie,
                'Date': p.date.strftime('%d/%m/%Y') if p.date else 'N/A'
            }
            for p in pieces
        ])
        
        st.dataframe(df, use_container_width=True)
    except:
        # Affichage sans pandas
        for piece in pieces:
            st.write(f"**{piece.numero}.** {piece.titre}")
            if piece.description:
                st.caption(piece.description)
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "💾 Télécharger bordereau",
            create_bordereau_document(bordereau),
            f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    with col2:
        if st.button("📧 Envoyer bordereau", key="send_bordereau"):
            st.session_state.pending_email = {
                'content': create_bordereau_document(bordereau),
                'type': 'bordereau'
            }

def synthesize_selected_pieces(pieces: list):
    """Synthétise les pièces sélectionnées"""
    
    try:
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            return {'error': 'Aucune IA disponible'}
        
        # Construire le contexte
        context = "PIÈCES À SYNTHÉTISER:\n\n"
        
        for piece in pieces[:20]:  # Limiter
            context += f"Pièce {piece.numero}: {piece.titre}\n"
            context += f"Catégorie: {piece.categorie}\n"
            if piece.description:
                context += f"Description: {piece.description}\n"
            context += "\n"
        
        # Prompt
        synthesis_prompt = f"""{context}

Crée une synthèse structurée de ces pièces.
La synthèse doit inclure:
1. Vue d'ensemble des pièces
2. Points clés par catégorie
3. Chronologie si applicable
4. Points d'attention juridiques
5. Recommandations"""
        
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            synthesis_prompt,
            "Tu es un expert en analyse de documents juridiques."
        )
        
        if response['success']:
            synthesis_result = {
                'content': response['response'],
                'piece_count': len(pieces),
                'categories': list(set(p.categorie for p in pieces)),
                'timestamp': datetime.now()
            }
            st.session_state.synthesis_result = synthesis_result
            return synthesis_result
        else:
            return {'error': 'Échec de la synthèse'}
            
    except Exception as e:
        return {'error': f'Erreur synthèse: {str(e)}'}

# ========================= ANALYSE IA =========================

def process_analysis_request(query: str, analysis: QueryAnalysis):
    """Traite une demande d'analyse IA avec support des infractions"""
    
    # Collecter les documents pertinents
    documents = collect_relevant_documents(analysis)
    
    if not documents:
        st.warning("⚠️ Aucun document trouvé pour l'analyse")
        return
    
    # Configuration de l'analyse
    st.markdown("### ⚙️ Configuration de l'analyse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type d'infraction si pertinent
        if any(word in query.lower() for word in ['infraction', 'délit', 'crime']):
            infractions_list = [inf.value for inf in InfractionAffaires]
            
            st.session_state.infraction = st.text_input(
                "Type d'infraction",
                placeholder="Ex: Abus de biens sociaux, corruption, fraude fiscale...",
                key="infraction_input",
                help="Saisissez librement l'infraction"
            )
            
            if not st.session_state.infraction:
                st.info("💡 Suggestions : " + ", ".join(infractions_list[:5]) + "...")
        
        # Client
        st.session_state.client_nom = st.text_input(
            "Nom du client",
            placeholder="Personne physique ou morale",
            key="client_nom_analyse"
        )
    
    with col2:
        # Type d'analyse
        analysis_type = st.selectbox(
            "Type d'analyse",
            ["Analyse générale", "Risques juridiques", "Conformité", "Stratégie", "Infractions"],
            key="analysis_type_select"
        )
    
    # Lancer l'analyse
    if st.button("🚀 Lancer l'analyse", type="primary", key="launch_analysis"):
        with st.spinner("🤖 Analyse en cours..."):
            if analysis_type == "Risques juridiques":
                results = analyze_legal_risks(documents, query)
            elif analysis_type == "Conformité":
                results = analyze_compliance(documents, query)
            elif analysis_type == "Stratégie":
                results = analyze_strategy(documents, query)
            elif analysis_type == "Infractions":
                results = analyze_infractions(documents, query)
            else:
                results = perform_general_analysis(documents, query)
        
        # Stocker les résultats
        st.session_state.ai_analysis_results = results
        st.rerun()

def analyze_infractions(documents: List[Dict[str, Any]], query: str) -> dict:
    """Analyse spécifique des infractions économiques"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    # Construire le prompt spécialisé
    infraction_prompt = f"""Analyse ces documents pour identifier des infractions économiques.

Client: {st.session_state.get('client_nom', 'Non spécifié')}
Infraction suspectée: {st.session_state.get('infraction', 'À déterminer')}

DOCUMENTS:
{chr(10).join([f"- {doc.get('title', 'Sans titre')}: {doc.get('content', '')[:500]}..." for doc in documents[:10]])}

Identifie:
1. INFRACTIONS CARACTÉRISÉES
   - Qualification juridique précise
   - Articles du Code pénal applicables
   - Éléments constitutifs présents/absents
   
2. RESPONSABILITÉS
   - Personnes physiques impliquées
   - Responsabilité des personnes morales
   
3. SANCTIONS ENCOURUES
   - Peines principales
   - Peines complémentaires
   - Prescription

4. ÉLÉMENTS DE PREUVE
   - Preuves matérielles identifiées
   - Témoignages pertinents
   - Documents clés

5. STRATÉGIE DE DÉFENSE
   - Points faibles de l'accusation
   - Arguments de défense possibles
   - Jurisprudences favorables"""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            infraction_prompt,
            "Tu es un avocat expert en droit pénal des affaires."
        )
        
        if response['success']:
            return {
                'type': 'infractions',
                'content': response['response'],
                'document_count': len(documents),
                'timestamp': datetime.now(),
                'query': query,
                'infraction': st.session_state.get('infraction', 'Non spécifiée')
            }
    except Exception as e:
        return {'error': f'Erreur analyse infractions: {str(e)}'}

def analyze_legal_risks(documents: List[Dict[str, Any]], query: str) -> dict:
    """Analyse les risques juridiques"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    # Construire le prompt
    risk_prompt = f"""Analyse les risques juridiques dans ces documents.

DOCUMENTS:
{chr(10).join([f"- {doc.get('title', 'Sans titre')}: {doc.get('content', '')[:500]}..." for doc in documents[:10]])}

QUESTION: {query}

Identifie et évalue:
1. RISQUES PÉNAUX
2. RISQUES CIVILS
3. RISQUES RÉPUTATIONNELS
4. RECOMMANDATIONS

Format structuré avec évaluation précise."""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            risk_prompt,
            "Tu es un expert en analyse de risques juridiques."
        )
        
        if response['success']:
            return {
                'type': 'risk_analysis',
                'content': response['response'],
                'document_count': len(documents),
                'timestamp': datetime.now(),
                'query': query
            }
    except Exception as e:
        return {'error': f'Erreur analyse: {str(e)}'}

def analyze_compliance(documents: List[Dict[str, Any]], query: str) -> dict:
    """Analyse de conformité"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    compliance_prompt = f"""Analyse la conformité légale et réglementaire.

DOCUMENTS:
{chr(10).join([f"- {doc.get('title', 'Sans titre')}: {doc.get('content', '')[:500]}..." for doc in documents[:10]])}

QUESTION: {query}

Vérifie:
1. CONFORMITÉ LÉGALE
2. CONFORMITÉ RÉGLEMENTAIRE
3. MANQUEMENTS IDENTIFIÉS
4. ACTIONS CORRECTIVES
5. RECOMMANDATIONS"""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            compliance_prompt,
            "Tu es un expert en conformité juridique."
        )
        
        if response['success']:
            return {
                'type': 'compliance',
                'content': response['response'],
                'document_count': len(documents),
                'timestamp': datetime.now(),
                'query': query
            }
    except Exception as e:
        return {'error': f'Erreur analyse conformité: {str(e)}'}

def analyze_strategy(documents: List[Dict[str, Any]], query: str) -> dict:
    """Analyse stratégique"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    strategy_prompt = f"""Développe une stratégie juridique basée sur ces documents.

DOCUMENTS:
{chr(10).join([f"- {doc.get('title', 'Sans titre')}: {doc.get('content', '')[:500]}..." for doc in documents[:10]])}

QUESTION: {query}

Élabore:
1. ANALYSE DE LA SITUATION
2. OPTIONS STRATÉGIQUES
3. AVANTAGES/INCONVÉNIENTS
4. STRATÉGIE RECOMMANDÉE
5. PLAN D'ACTION"""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            strategy_prompt,
            "Tu es un stratège juridique expérimenté."
        )
        
        if response['success']:
            return {
                'type': 'strategy',
                'content': response['response'],
                'document_count': len(documents),
                'timestamp': datetime.now(),
                'query': query
            }
    except Exception as e:
        return {'error': f'Erreur analyse stratégique: {str(e)}'}

def perform_general_analysis(documents: List[Dict[str, Any]], query: str) -> dict:
    """Analyse générale des documents"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    general_prompt = f"""Analyse ces documents pour répondre à la question.

DOCUMENTS:
{chr(10).join([f"- {doc.get('title', 'Sans titre')}: {doc.get('content', '')[:500]}..." for doc in documents[:10]])}

QUESTION: {query}

Fournis une analyse complète et structurée."""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            general_prompt,
            "Tu es un expert en analyse juridique."
        )
        
        if response['success']:
            return {
                'type': 'general_analysis',
                'content': response['response'],
                'document_count': len(documents),
                'timestamp': datetime.now(),
                'query': query
            }
    except Exception as e:
        return {'error': f'Erreur analyse: {str(e)}'}

def verify_jurisprudences_in_analysis(content: str):
    """Vérifie les jurisprudences citées dans l'analyse"""
    st.markdown("### 🔍 Vérification des jurisprudences citées")
    
    try:
        # Créer le vérificateur
        verifier = JurisprudenceVerifier()
        
        # Afficher l'interface de vérification
        verification_results = display_jurisprudence_verification(content, verifier)
        
        # Stocker les résultats de vérification
        if verification_results:
            st.session_state.jurisprudence_verification = verification_results
            
            # Résumé
            verified_count = sum(1 for r in verification_results if r.status == 'verified')
            total_count = len(verification_results)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Jurisprudences vérifiées", f"{verified_count}/{total_count}")
            
            with col2:
                confidence = (verified_count / total_count * 100) if total_count > 0 else 0
                st.metric("Fiabilité des sources", f"{confidence:.0f}%")
        
        return verification_results
    except:
        st.warning("⚠️ Vérificateur de jurisprudences non disponible")
        return []

# ========================= FONCTIONS DE TRAITEMENT =========================

def process_redaction_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de rédaction générale"""
    st.info("📝 Traitement de la demande de rédaction...")
    
    # Déterminer le type de document
    doc_type = analysis.document_type or 'document'
    
    # Afficher l'interface de configuration
    st.markdown("### ⚙️ Configuration du document")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type de document
        doc_type = st.selectbox(
            "Type de document",
            list(DOCUMENT_TEMPLATES.keys()),
            format_func=lambda x: DOCUMENT_TEMPLATES[x]['name'],
            key="doc_type_select"
        )
        
        # Style de rédaction
        style = st.selectbox(
            "Style de rédaction",
            list(REDACTION_STYLES.keys()),
            format_func=lambda x: REDACTION_STYLES[x]['name'],
            key="style_select",
            index=list(REDACTION_STYLES.keys()).index(DOCUMENT_TEMPLATES[doc_type]['style'])
        )
    
    with col2:
        # Parties si applicable
        if doc_type in ['conclusions_defense', 'plainte_simple', 'assignation']:
            demandeur = st.text_input("Demandeur/Plaignant", key="demandeur_input")
            defendeur = st.text_input("Défendeur/Mis en cause", key="defendeur_input")
        
        # Référence
        reference = st.text_input(
            "Référence dossier",
            value=analysis.reference or '',
            placeholder="Ex: @VINCI2024",
            key="reference_input"
        )
    
    # Bouton de génération
    if st.button("🚀 Générer le document", type="primary", key="generate_doc_btn"):
        generate_document(doc_type, style, query, analysis)

def process_plaidoirie_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de plaidoirie"""
    st.info("🎤 Préparation de plaidoirie...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_preparation_client_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de préparation client"""
    st.info("👥 Préparation du client...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_import_request(query: str, analysis: QueryAnalysis):
    """Traite une demande d'import"""
    st.info("📥 Import de documents...")
    
    # Interface d'upload
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers",
        type=['pdf', 'docx', 'txt', 'csv', 'xlsx'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        st.info(f"📄 {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        if st.button("📥 Importer", key="import_btn"):
            with st.spinner("Import en cours..."):
                import_documents(uploaded_files)

def process_export_request(query: str, analysis: QueryAnalysis):
    """Traite une demande d'export"""
    st.info("💾 Export en cours...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_email_request(query: str, analysis: QueryAnalysis):
    """Traite une demande d'email"""
    st.info("📧 Préparation de l'email...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_synthesis_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de synthèse"""
    
    # Déterminer la source
    if st.session_state.get('selected_pieces'):
        synthesize_selected_pieces(st.session_state.selected_pieces)
    elif analysis.reference:
        docs = search_by_reference(f"@{analysis.reference}")
        pieces = []
        for i, doc in enumerate(docs):
            pieces.append(PieceSelectionnee(
                numero=i + 1,
                titre=doc.get('title', 'Sans titre'),
                description=doc.get('content', '')[:200] + '...' if doc.get('content') else '',
                categorie=determine_document_category(doc),
                source=doc.get('source', '')
            ))
        synthesize_selected_pieces(pieces)
    else:
        st.warning("⚠️ Aucun contenu à synthétiser")
        return

def process_template_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de template"""
    st.info("📄 Gestion des templates...")
    
    # Afficher les templates disponibles
    st.markdown("### 📄 Templates disponibles")
    
    for template_id, template in DOCUMENT_TEMPLATES.items():
        with st.expander(f"📄 {template['name']}", expanded=False):
            st.markdown("**Structure:**")
            for element in template['structure']:
                st.write(f"- {element}")
            st.markdown(f"**Style:** {REDACTION_STYLES[template['style']]['description']}")
            
            if st.button(f"Utiliser ce template", key=f"use_template_{template_id}"):
                st.session_state.selected_template = template_id
                st.info(f"✅ Template '{template['name']}' sélectionné")

def process_jurisprudence_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de jurisprudence"""
    st.info("⚖️ Recherche de jurisprudence...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_timeline_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de chronologie"""
    st.info("⏱️ Création de la chronologie...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_mapping_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de cartographie"""
    st.info("🗺️ Création de la cartographie...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_comparison_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de comparaison"""
    st.info("🔄 Comparaison en cours...")
    st.warning("⚠️ Fonctionnalité en cours de développement")
    # TODO: Implémenter

def process_search_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de recherche simple"""
    
    # Utiliser le service de recherche universel
    search_service = init_search_service()
    
    # Utiliser LegalSearchManager si disponible pour enrichir
    legal_search = None
    if MANAGERS_AVAILABLE:
        try:
            legal_search = LegalSearchManager()
        except:
            pass
    
    with st.spinner("🔍 Recherche en cours..."):
        # Recherche principale via UniversalSearchService
        results = asyncio.run(search_service.search(query))
        
        # Enrichir avec LegalSearchManager si disponible
        if legal_search and 'jurisprudence' in query.lower():
            try:
                legal_results = legal_search.search_jurisprudence(query)
                # Ajouter les résultats juridiques aux résultats principaux
                if legal_results:
                    st.info(f"📚 {len(legal_results)} jurisprudences trouvées via LegalSearch")
            except:
                pass
    
    # Stocker les résultats
    st.session_state.search_results = results
    
    if results.documents:
        st.success(f"✅ {results.total_count} résultats trouvés")
    else:
        st.warning("⚠️ Aucun résultat trouvé")

# ========================= FONCTIONS HELPER =========================

def collect_relevant_documents(analysis: QueryAnalysis) -> List[Dict[str, Any]]:
    """Collecte les documents pertinents selon l'analyse"""
    
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        # Convertir en dictionnaire si c'est un objet
        if hasattr(doc, 'title'):
            documents.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'metadata': getattr(doc, 'metadata', {})
            })
        else:
            documents.append({
                'id': doc_id,
                'title': doc.get('title', 'Sans titre'),
                'content': doc.get('content', ''),
                'source': doc.get('source', 'Local'),
                'metadata': doc.get('metadata', {})
            })
    
    # Filtrer par référence si présente
    if analysis.reference:
        ref_lower = analysis.reference.lower()
        documents = [d for d in documents if ref_lower in d['title'].lower() or ref_lower in d.get('source', '').lower()]
    
    return documents

def collect_available_documents(analysis: QueryAnalysis) -> list:
    """Collecte tous les documents disponibles"""
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if hasattr(doc, 'title'):
            documents.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'metadata': getattr(doc, 'metadata', {})
            })
        else:
            documents.append({
                'id': doc_id,
                'title': doc.get('title', 'Sans titre'),
                'content': doc.get('content', ''),
                'source': doc.get('source', 'Local'),
                'metadata': doc.get('metadata', {})
            })
    
    return documents

def group_documents_by_category(documents: list) -> dict:
    """Groupe les documents par catégorie"""
    categories = defaultdict(list)
    
    for doc in documents:
        category = determine_document_category(doc)
        categories[category].append(doc)
    
    return dict(categories)

def determine_document_category(doc: dict) -> str:
    """Détermine la catégorie d'un document"""
    title_lower = doc.get('title', '').lower()
    content_lower = doc.get('content', '')[:500].lower()
    
    category_patterns = {
        'Procédure': ['plainte', 'procès-verbal', 'audition'],
        'Expertise': ['expertise', 'expert', 'rapport technique'],
        'Comptabilité': ['bilan', 'compte', 'facture'],
        'Contrats': ['contrat', 'convention', 'accord'],
        'Correspondance': ['courrier', 'email', 'lettre']
    }
    
    for category, keywords in category_patterns.items():
        if any(kw in title_lower or kw in content_lower for kw in keywords):
            return category
    
    return 'Autres'

def calculate_piece_relevance(doc: dict, analysis: QueryAnalysis) -> float:
    """Calcule la pertinence d'une pièce"""
    score = 0.5
    
    if analysis.subject_matter:
        if analysis.subject_matter in doc.get('content', '').lower():
            score += 0.3
    
    if analysis.reference:
        if analysis.reference in doc.get('title', '').lower():
            score += 0.2
    
    return min(score, 1.0)

def create_bordereau(pieces: list, analysis: QueryAnalysis) -> dict:
    """Crée un bordereau structuré"""
    
    bordereau = {
        'header': f"""BORDEREAU DE COMMUNICATION DE PIÈCES

AFFAIRE : {analysis.reference.upper() if analysis.reference else 'N/A'}
DATE : {datetime.now().strftime('%d/%m/%Y')}
NOMBRE DE PIÈCES : {len(pieces)}""",
        'pieces': pieces,
        'footer': f"""Je certifie que les pièces communiquées sont conformes aux originaux.

Fait le {datetime.now().strftime('%d/%m/%Y')}""",
        'metadata': {
            'created_at': datetime.now(),
            'piece_count': len(pieces),
            'reference': analysis.reference
        }
    }
    
    return bordereau

def create_bordereau_document(bordereau: dict) -> bytes:
    """Crée le document du bordereau"""
    content = bordereau['header'] + '\n\n'
    
    for piece in bordereau['pieces']:
        content += f"{piece.numero}. {piece.titre}\n"
        if piece.description:
            content += f"   {piece.description}\n"
        content += f"   Catégorie: {piece.categorie}\n"
        if hasattr(piece, 'date') and piece.date:
            content += f"   Date: {piece.date.strftime('%d/%m/%Y')}\n"
        content += "\n"
    
    content += bordereau['footer']
    
    return content.encode('utf-8')

def export_piece_list(pieces: list):
    """Exporte la liste des pièces"""
    content = "LISTE DES PIÈCES SÉLECTIONNÉES\n"
    content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    content += f"Nombre de pièces : {len(pieces)}\n\n"
    
    # Grouper par catégorie
    by_category = defaultdict(list)
    for piece in pieces:
        by_category[piece.categorie].append(piece)
    
    for category, cat_pieces in by_category.items():
        content += f"\n{category.upper()} ({len(cat_pieces)} pièces)\n"
        content += "-" * 50 + "\n"
        
        for piece in cat_pieces:
            content += f"{piece.numero}. {piece.titre}\n"
            if piece.description:
                content += f"   {piece.description}\n"
            content += "\n"
    
    # Télécharger
    st.download_button(
        "💾 Télécharger la liste",
        content.encode('utf-8'),
        f"liste_pieces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain"
    )

def search_by_reference(reference: str) -> list:
    """Recherche par référence @"""
    results = []
    ref_clean = reference.replace('@', '').strip().lower()
    
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if hasattr(doc, 'title'):
            if ref_clean in doc.title.lower() or ref_clean in doc.source.lower():
                results.append({
                    'id': doc_id,
                    'title': doc.title,
                    'content': doc.content,
                    'source': doc.source
                })
        else:
            if ref_clean in doc.get('title', '').lower() or ref_clean in doc.get('source', '').lower():
                results.append({
                    'id': doc_id,
                    'title': doc.get('title', 'Sans titre'),
                    'content': doc.get('content', ''),
                    'source': doc.get('source', 'N/A')
                })
    
    return results

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'current_analysis',
        'redaction_result', 'timeline_result', 'mapping_result',
        'comparison_result', 'synthesis_result', 'ai_analysis_results',
        'search_results', 'selected_pieces', 'import_files',
        'plaidoirie_result', 'preparation_client_result'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

def save_current_work():
    """Sauvegarde le travail actuel"""
    work_data = {
        'timestamp': datetime.now().isoformat(),
        'query': st.session_state.get('universal_query', ''),
        'analysis': {},
        'results': {}
    }
    
    # Collecter tous les résultats
    result_keys = [
        'redaction_result', 'timeline_result', 'mapping_result',
        'comparison_result', 'synthesis_result', 'ai_analysis_results',
        'search_results', 'plaidoirie_result', 'preparation_client_result'
    ]
    
    for key in result_keys:
        if key in st.session_state and st.session_state[key]:
            # Convertir les objets complexes en dictionnaires
            if hasattr(st.session_state[key], '__dict__'):
                work_data['results'][key] = st.session_state[key].__dict__
            else:
                work_data['results'][key] = st.session_state[key]
    
    # Sauvegarder
    import json
    
    # Fonction pour sérialiser les objets non-sérialisables
    def default_serializer(obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
    
    json_str = json.dumps(work_data, indent=2, ensure_ascii=False, default=default_serializer)
    
    st.download_button(
        "💾 Télécharger la sauvegarde",
        json_str,
        f"sauvegarde_travail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="download_work_save"
    )

async def show_work_statistics():
    """Affiche les statistiques du travail en cours"""
    st.info("📊 Statistiques du travail en cours")
    
    # Compter les résultats
    stats = {
        'Documents': len(st.session_state.get('azure_documents', {})),
        'Pièces sélectionnées': len(st.session_state.get('selected_pieces', [])),
        'Analyses': 1 if st.session_state.get('ai_analysis_results') else 0,
        'Rédactions': 1 if st.session_state.get('redaction_result') else 0
    }
    
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label, value)
    
    # Statistiques de recherche si disponibles
    if 'search_service' in st.session_state:
        search_stats = await st.session_state.search_service.get_search_statistics()
        
        st.markdown("### 📊 Statistiques de recherche")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Recherches totales", search_stats['total_searches'])
            st.metric("Taille du cache", search_stats['cache_size'])
        
        with col2:
            st.metric("Résultats moyens", f"{search_stats['average_results']:.1f}")
            
            if search_stats['popular_keywords']:
                st.markdown("**Mots-clés populaires:**")
                for keyword, count in list(search_stats['popular_keywords'].items())[:5]:
                    st.write(f"• {keyword}: {count} fois")

def share_current_work():
    """Partage le travail actuel"""
    st.info("🔗 Fonctionnalité de partage")
    
    # Pour l'instant, proposer l'export
    save_current_work()

def show_document_statistics(content: str):
    """Affiche les statistiques d'un document"""
    
    # Calculs
    words = content.split()
    sentences = content.split('.')
    paragraphs = content.split('\n\n')
    
    # Références
    law_refs = len(re.findall(r'article\s+[LR]?\s*\d+', content, re.IGNORECASE))
    
    # Affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mots", f"{len(words):,}")
        st.metric("Phrases", f"{len(sentences):,}")
    
    with col2:
        st.metric("Paragraphes", len(paragraphs))
        st.metric("Mots/phrase", f"{len(words) / max(len(sentences), 1):.1f}")
    
    with col3:
        st.metric("Articles cités", law_refs)
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        st.metric("Longueur moy.", f"{avg_word_length:.1f} car/mot")

def generate_document(doc_type: str, style: str, query: str, analysis: QueryAnalysis):
    """Génère un document selon le type et le style"""
    try:
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            st.error("❌ Aucune IA disponible")
            return
        
        # Utiliser DynamicGenerators si disponible pour enrichir la génération
        dynamic_gen = None
        if MANAGERS_AVAILABLE:
            try:
                dynamic_gen = DynamicGenerators()
            except:
                pass
        
        # Construire le prompt selon le template
        template = DOCUMENT_TEMPLATES[doc_type]
        style_info = REDACTION_STYLES[style]
        
        # Si DynamicGenerators est disponible, l'utiliser pour améliorer le prompt
        if dynamic_gen and hasattr(dynamic_gen, 'enhance_prompt'):
            try:
                enhanced_prompt = dynamic_gen.enhance_prompt(
                    doc_type=doc_type,
                    style=style,
                    context=query,
                    reference=analysis.reference
                )
                prompt = enhanced_prompt
            except:
                # Fallback au prompt standard
                prompt = f"""Rédige un document juridique de type {template['name']}.

STRUCTURE À SUIVRE :
{chr(10).join(template['structure'])}

STYLE : {style_info['name']}
- Ton : {style_info['tone']}
- Vocabulaire : {style_info['vocabulary']}

CONTEXTE : {query}
RÉFÉRENCE : {analysis.reference or 'N/A'}

Rédige un document complet et professionnel."""
        else:
            # Prompt standard
            prompt = f"""Rédige un document juridique de type {template['name']}.

STRUCTURE À SUIVRE :
{chr(10).join(template['structure'])}

STYLE : {style_info['name']}
- Ton : {style_info['tone']}
- Vocabulaire : {style_info['vocabulary']}

CONTEXTE : {query}
RÉFÉRENCE : {analysis.reference or 'N/A'}

Rédige un document complet et professionnel."""
        
        # Sélectionner un provider
        provider = list(llm_manager.clients.keys())[0]
        
        with st.spinner(f"📝 Génération du {template['name']}..."):
            response = llm_manager.query_single_llm(
                provider,
                prompt,
                f"Tu es un expert en rédaction juridique spécialisé en {template['name']}."
            )
        
        if response['success']:
            # Post-traitement avec StyleAnalyzer si disponible
            final_document = response['response']
            
            if MANAGERS_AVAILABLE and StyleAnalyzer:
                try:
                    analyzer = StyleAnalyzer()
                    if hasattr(analyzer, 'analyze_and_improve'):
                        improved = analyzer.analyze_and_improve(
                            final_document,
                            target_style=style,
                            document_type=doc_type
                        )
                        if improved:
                            final_document = improved
                            st.info("✨ Document amélioré avec l'analyseur de style")
                except:
                    pass
            
            st.session_state.redaction_result = {
                'type': doc_type,
                'document': final_document,
                'provider': provider,
                'timestamp': datetime.now(),
                'metadata': {
                    'style': style,
                    'query': query,
                    'reference': analysis.reference,
                    'enhanced': dynamic_gen is not None
                }
            }
            st.success(f"✅ {template['name']} généré avec succès !")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")

def import_documents(files):
    """Importe les documents uploadés"""
    
    imported_count = 0
    doc_manager = None
    
    # Utiliser DocumentManager si disponible
    if MANAGERS_AVAILABLE:
        try:
            doc_manager = DocumentManager()
        except:
            pass
    
    for file in files:
        try:
            # Si DocumentManager est disponible, l'utiliser
            if doc_manager and hasattr(doc_manager, 'import_document'):
                try:
                    result = doc_manager.import_document(file)
                    if result and result.get('success'):
                        imported_count += 1
                        st.success(f"✅ {file.name} importé via DocumentManager")
                        continue
                except:
                    # Fallback à la méthode standard
                    pass
            
            # Méthode standard de lecture
            if file.name.endswith('.txt'):
                content = file.read().decode('utf-8')
            elif file.name.endswith('.pdf'):
                # Si DocumentManager a un extracteur PDF, l'utiliser
                if doc_manager and hasattr(doc_manager, 'extract_pdf_content'):
                    try:
                        content = doc_manager.extract_pdf_content(file)
                    except:
                        st.warning(f"⚠️ Import PDF non implémenté pour {file.name}")
                        continue
                else:
                    st.warning(f"⚠️ Import PDF non implémenté pour {file.name}")
                    continue
            elif file.name.endswith(('.docx', '.doc')):
                # Si DocumentManager a un extracteur Word, l'utiliser
                if doc_manager and hasattr(doc_manager, 'extract_word_content'):
                    try:
                        content = doc_manager.extract_word_content(file)
                    except:
                        st.warning(f"⚠️ Import Word non implémenté pour {file.name}")
                        continue
                else:
                    st.warning(f"⚠️ Import Word non implémenté pour {file.name}")
                    continue
            else:
                st.warning(f"⚠️ Type de fichier non supporté : {file.name}")
                continue
            
            # Créer le document
            doc_id = f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imported_count}"
            
            if 'imported_documents' not in st.session_state:
                st.session_state.imported_documents = {}
            
            # Enrichir les métadonnées si possible
            metadata = {
                'import_date': datetime.now().isoformat(),
                'file_size': len(content) if isinstance(content, str) else 0,
                'file_type': file.name.split('.')[-1].lower()
            }
            
            # Si DocumentManager peut extraire des métadonnées supplémentaires
            if doc_manager and hasattr(doc_manager, 'extract_metadata'):
                try:
                    extra_metadata = doc_manager.extract_metadata(file, content)
                    metadata.update(extra_metadata)
                except:
                    pass
            
            st.session_state.imported_documents[doc_id] = {
                'title': file.name,
                'content': content,
                'source': 'Import manuel',
                'metadata': metadata
            }
            
            imported_count += 1
            
        except Exception as e:
            st.error(f"❌ Erreur import {file.name}: {str(e)}")
    
    if imported_count > 0:
        st.success(f"✅ {imported_count} document(s) importé(s) avec succès")
        
        # Si DocumentManager peut indexer les documents
        if doc_manager and hasattr(doc_manager, 'index_documents'):
            with st.spinner("Indexation des documents..."):
                try:
                    doc_manager.index_documents(st.session_state.imported_documents)
                    st.info("📚 Documents indexés pour la recherche")
                except:
                    pass
        
        st.rerun()

# ========================= FIN DU MODULE =========================