# modules/recherche.py
"""Module de recherche unifié - Interface principale avec toutes les fonctionnalités"""

import streamlit as st
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict
import pandas as pd

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

# ========================= IMPORTS =========================

# modules/recherche.py
"""Module de recherche unifié - Interface principale avec toutes les fonctionnalités"""

import streamlit as st
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict
import pandas as pd

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

# ========================= IMPORTS =========================

try:
    # Import des managers
    from managers.azure_blob_manager import AzureBlobManager
    from managers.azure_search_manager import AzureSearchManager
    from managers.multi_llm_manager import MultiLLMManager
    from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
    
    # Import des modèles
    from models.dataclasses import (
        Document, 
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
    
except ImportError as e:
    st.error(f"⚠️ Import manquant : {e}")
    
# ========================= PAGE PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "Entrez votre commande ou recherche",
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
    
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
            st.session_state.universal_query = "rédiger "
            st.session_state.process_query = True
    
    with col2:
        if st.button("🤖 Analyser dossier", key="quick_analysis"):
            st.session_state.universal_query = "analyser "
            st.session_state.process_query = True
    
    with col3:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.universal_query = "importer documents"
            st.session_state.process_query = True
    
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
            show_work_statistics()
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            share_current_work()

# ========================= ROUTING ET TRAITEMENT =========================

def process_universal_query(query: str):
    """Traite une requête universelle et route vers la bonne fonction"""
    
    # Sauvegarder la requête
    st.session_state.last_universal_query = query
    
    # Analyser la requête pour détecter le type
    query_lower = query.lower()
    
    # DÉTECTION POUR RÉDACTION (incluant votre cas de plainte)
    if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer', 'plainte', 'conclusions', 'courrier', 'assignation']):
        st.info("📝 Détection d'une demande de rédaction...")
        
        # Cas spécifique : plainte avec parties multiples
        if 'plainte' in query_lower:
            # Extraire les parties de la requête
            parties = []
            parties_keywords = [
                'interconstruction', 'vinci', 'sogeprom', 'demathieu bard',
                'bouygues', 'eiffage', 'spie', 'leon grosse'
            ]
            
            for partie in parties_keywords:
                if partie in query_lower:
                    # Formatage correct du nom
                    if partie == 'sogeprom':
                        parties.append('SOGEPROM Réalisations')
                    elif partie == 'demathieu bard':
                        parties.append('Demathieu Bard')
                    else:
                        parties.append(partie.title())
            
            # Extraire la référence
            reference = None
            if '@' in query:
                ref_match = re.search(r'@(\w+)', query)
                if ref_match:
                    reference = ref_match.group(1)
            
            # Créer la demande de rédaction
            st.session_state.redaction_request = {
                'type': 'plainte',
                'parties': parties,
                'reference': reference,
                'query': query
            }
            
            # Générer la plainte
            generate_plainte(query, parties)
        else:
            # Autres types de rédaction
            process_redaction_request(query, analyze_query(query))
    
    # PLAIDOIRIE
    elif any(word in query_lower for word in ['plaidoirie', 'plaider', 'audience']):
        st.info("🎤 Détection d'une demande de plaidoirie...")
        process_plaidoirie_request(query, analyze_query(query))
    
    # PRÉPARATION CLIENT
    elif any(word in query_lower for word in ['préparer client', 'préparation', 'coaching']):
        st.info("👥 Détection d'une demande de préparation client...")
        process_preparation_client_request(query, analyze_query(query))
    
    # IMPORT
    elif any(word in query_lower for word in ['import', 'importer', 'charger', 'upload']):
        st.info("📥 Détection d'une demande d'import...")
        process_import_request(query, analyze_query(query))
    
    # EXPORT
    elif any(word in query_lower for word in ['export', 'exporter', 'télécharger', 'download']):
        st.info("💾 Détection d'une demande d'export...")
        process_export_request(query, analyze_query(query))
    
    # EMAIL
    elif any(word in query_lower for word in ['email', 'envoyer', 'mail', 'courrier électronique']):
        st.info("📧 Détection d'une demande d'email...")
        process_email_request(query, analyze_query(query))
    
    # ANALYSE
    elif any(word in query_lower for word in ['analyser', 'analyse', 'étudier', 'examiner']):
        st.info("🤖 Détection d'une demande d'analyse...")
        process_analysis_request(query, analyze_query(query))
    
    # PIÈCES
    elif any(word in query_lower for word in ['sélectionner pièces', 'pièces', 'sélection']):
        st.info("📋 Détection d'une demande de sélection de pièces...")
        process_piece_selection_request(query, analyze_query(query))
    
    # BORDEREAU
    elif 'bordereau' in query_lower:
        st.info("📊 Détection d'une demande de bordereau...")
        process_bordereau_request(query, analyze_query(query))
    
    # SYNTHÈSE
    elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
        st.info("📝 Détection d'une demande de synthèse...")
        process_synthesis_request(query, analyze_query(query))
    
    # TEMPLATES
    elif any(word in query_lower for word in ['template', 'modèle', 'gabarit']):
        st.info("📄 Détection d'une demande de template...")
        process_template_request(query, analyze_query(query))
    
    # JURISPRUDENCE
    elif any(word in query_lower for word in ['jurisprudence', 'juris', 'décision', 'arrêt']):
        st.info("⚖️ Détection d'une demande de jurisprudence...")
        process_jurisprudence_request(query, analyze_query(query))
    
    # CHRONOLOGIE
    elif any(word in query_lower for word in ['chronologie', 'timeline', 'frise']):
        st.info("⏱️ Détection d'une demande de chronologie...")
        process_timeline_request(query, analyze_query(query))
    
    # CARTOGRAPHIE
    elif any(word in query_lower for word in ['cartographie', 'mapping', 'carte', 'réseau']):
        st.info("🗺️ Détection d'une demande de cartographie...")
        process_mapping_request(query, analyze_query(query))
    
    # COMPARAISON
    elif any(word in query_lower for word in ['comparer', 'comparaison', 'différences']):
        st.info("🔄 Détection d'une demande de comparaison...")
        process_comparison_request(query, analyze_query(query))
    
    else:
        # Recherche simple par défaut
        st.info("🔍 Recherche simple...")
        process_search_request(query, analyze_query(query))

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
    
    st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
    
    if not results:
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
    for i, result in enumerate(results[:20], 1):  # Limiter à 20
        with st.container():
            if view_mode == "Compact":
                st.markdown(f"**{i}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
            else:
                st.markdown(f"**{i}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
                
                # Extrait
                content = result.get('content', '')
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

# ========================= GESTION DES PIÈCES =========================

def process_piece_selection_request(query: str, analysis: dict):
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

def process_bordereau_request(query: str, analysis: dict):
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

def process_analysis_request(query: str, analysis: dict):
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

def process_redaction_request(query: str, analysis: dict):
    """Traite une demande de rédaction"""
    # Import depuis le module de rédaction
    st.info("📝 Traitement de la demande de rédaction...")
    # TODO: Implémenter ou importer depuis recherche_redaction

def generate_plainte(query: str, parties: list):
    """Génère une plainte avec les parties spécifiées"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        st.error("❌ Aucune IA disponible")
        return
    
    # Construire le prompt
    plainte_prompt = f"""Rédige une plainte pénale professionnelle.
DEMANDEUR: {st.session_state.get('client_nom', 'Le plaignant')}
PARTIES MISES EN CAUSE: {', '.join(parties)}
CONTEXTE: {query}
Structure la plainte avec:
1. En-tête (Tribunal compétent, identité du plaignant)
2. EXPOSÉ DES FAITS (chronologique et détaillé)
3. QUALIFICATION JURIDIQUE (infractions caractérisées)
4. PRÉJUDICES SUBIS (moral, matériel, financier)
5. DEMANDES (poursuites pénales, dommages-intérêts)
6. PIÈCES JOINTES
Style: Formel, juridique, factuel."""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            plainte_prompt,
            "Tu es un avocat expert en rédaction de plaintes pénales."
        )
        
        if response['success']:
            st.session_state.redaction_result = {
                'type': 'plainte',
                'document': response['response'],
                'provider': provider.value,
                'timestamp': datetime.now(),
                'parties': parties
            }
            st.rerun()
    except Exception as e:
        st.error(f"❌ Erreur génération: {str(e)}")

def process_plaidoirie_request(query: str, analysis: dict):
    """Traite une demande de plaidoirie"""
    st.info("🎤 Préparation de plaidoirie...")
    # TODO: Implémenter

def process_preparation_client_request(query: str, analysis: dict):
    """Traite une demande de préparation client"""
    st.info("👥 Préparation du client...")
    # TODO: Implémenter

def process_import_request(query: str, analysis: dict):
    """Traite une demande d'import"""
    st.info("📥 Import de documents...")
    # TODO: Implémenter

def process_export_request(query: str, analysis: dict):
    """Traite une demande d'export"""
    st.info("💾 Export en cours...")
    # TODO: Implémenter

def process_email_request(query: str, analysis: dict):
    """Traite une demande d'email"""
    st.info("📧 Préparation de l'email...")
    # TODO: Implémenter

def process_synthesis_request(query: str, analysis: dict):
    """Traite une demande de synthèse"""
    
    # Déterminer la source
    if st.session_state.get('selected_pieces'):
        content_to_synthesize = synthesize_selected_pieces(st.session_state.selected_pieces)
    elif analysis.get('reference'):
        docs = search_by_reference(f"@{analysis['reference']}")
        pieces = []
        for i, doc in enumerate(docs):
            pieces.append(PieceSelectionnee(
                numero=i + 1,
                titre=doc.get('title', 'Sans titre'),
                description=doc.get('content', '')[:200] + '...' if doc.get('content') else '',
                categorie=determine_document_category(doc),
                source=doc.get('source', '')
            ))
        content_to_synthesize = synthesize_selected_pieces(pieces)
    else:
        st.warning("⚠️ Aucun contenu à synthétiser")
        return

def process_template_request(query: str, analysis: dict):
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

def process_jurisprudence_request(query: str, analysis: dict):
    """Traite une demande de jurisprudence"""
    st.info("⚖️ Recherche de jurisprudence...")
    # TODO: Implémenter

def process_timeline_request(query: str, analysis: dict):
    """Traite une demande de chronologie"""
    st.info("⏱️ Création de la chronologie...")
    # TODO: Implémenter

def process_mapping_request(query: str, analysis: dict):
    """Traite une demande de cartographie"""
    st.info("🗺️ Création de la cartographie...")
    # TODO: Implémenter

def process_comparison_request(query: str, analysis: dict):
    """Traite une demande de comparaison"""
    st.info("🔄 Comparaison en cours...")
    # TODO: Implémenter

def process_search_request(query: str, analysis: dict):
    """Traite une demande de recherche simple"""
    
    results = []
    
    # Recherche selon le contexte
    if analysis.get('reference'):
        results = search_by_reference(f"@{analysis['reference']}")
    else:
        results = perform_search(query)
    
    # Stocker les résultats
    st.session_state.search_results = results
    
    if not results:
        st.warning("⚠️ Aucun résultat trouvé")
    else:
        st.success(f"✅ {len(results)} résultats trouvés")

# ========================= FONCTIONS HELPER =========================

def analyze_query(query: str) -> dict:
    """Analyse une requête pour extraire les informations clés"""
    
    analysis = {
        'original_query': query,
        'reference': None,
        'subject_matter': None,
        'document_type': None,
        'action': None
    }
    
    # Extraire la référence @
    ref_match = re.search(r'@(\w+)', query)
    if ref_match:
        analysis['reference'] = ref_match.group(1)
    
    # Détecter le type de document
    query_lower = query.lower()
    for doc_type in ['conclusions', 'plainte', 'courrier', 'assignation', 'mise en demeure']:
        if doc_type in query_lower:
            analysis['document_type'] = doc_type
            break
    
    # Détecter l'action principale
    actions = {
        'rédiger': 'redaction',
        'analyser': 'analysis',
        'rechercher': 'search',
        'comparer': 'comparison',
        'créer': 'creation'
    }
    
    for keyword, action in actions.items():
        if keyword in query_lower:
            analysis['action'] = action
            break
    
    # Extraire le sujet
    # Simplification - en production, utiliser NLP
    if 'abus' in query_lower and 'biens' in query_lower:
        analysis['subject_matter'] = 'abus de biens sociaux'
    elif 'corruption' in query_lower:
        analysis['subject_matter'] = 'corruption'
    elif 'fraude' in query_lower:
        analysis['subject_matter'] = 'fraude'
    
    return analysis

def collect_relevant_documents(analysis: dict) -> List[Dict[str, Any]]:
    """Collecte les documents pertinents selon l'analyse"""
    
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        documents.append({
            'id': doc_id,
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'metadata': doc.metadata
        })
    
    # Filtrer par référence si présente
    if analysis.get('reference'):
        ref_lower = analysis['reference'].lower()
        documents = [d for d in documents if ref_lower in d['title'].lower() or ref_lower in d.get('source', '').lower()]
    
    return documents

def collect_available_documents(analysis: dict) -> list:
    """Collecte tous les documents disponibles"""
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        documents.append({
            'id': doc_id,
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'metadata': doc.metadata
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

def calculate_piece_relevance(doc: dict, analysis: dict) -> float:
    """Calcule la pertinence d'une pièce"""
    score = 0.5
    
    if analysis.get('subject_matter'):
        if analysis['subject_matter'] in doc.get('content', '').lower():
            score += 0.3
    
    if analysis.get('reference'):
        if analysis['reference'] in doc.get('title', '').lower():
            score += 0.2
    
    return min(score, 1.0)

def create_bordereau(pieces: list, analysis: dict) -> dict:
    """Crée un bordereau structuré"""
    
    bordereau = {
        'header': f"""BORDEREAU DE COMMUNICATION DE PIÈCES
AFFAIRE : {analysis.get('reference', 'N/A').upper()}
DATE : {datetime.now().strftime('%d/%m/%Y')}
NOMBRE DE PIÈCES : {len(pieces)}""",
        'pieces': pieces,
        'footer': f"""Je certifie que les pièces communiquées sont conformes aux originaux.
Fait le {datetime.now().strftime('%d/%m/%Y')}""",
        'metadata': {
            'created_at': datetime.now(),
            'piece_count': len(pieces),
            'reference': analysis.get('reference')
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
        if piece.date:
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
        if ref_clean in doc.title.lower() or ref_clean in doc.source.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source
            })
    
    return results

def perform_search(query: str) -> List[Dict[str, Any]]:
    """Effectue une recherche générale"""
    
    results = []
    query_lower = query.lower()
    query_words = query_lower.split()
    
    # Recherche locale
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        score = 0
        content_lower = doc.content.lower()
        title_lower = doc.title.lower()
        
        for word in query_words:
            if word in title_lower:
                score += 2
            if word in content_lower:
                score += 1
        
        if score > 0:
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'score': score / len(query_words)
            })
    
    # Recherche Azure si disponible
    try:
        search_manager = st.session_state.get('azure_search_manager')
        if search_manager and hasattr(search_manager, 'search'):
            azure_results = search_manager.search(query)
            results.extend(azure_results)
    except:
        pass
    
    return sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:50]

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
        'analysis': st.session_state.get('current_analysis', {}),
        'results': {}
    }
    
    # Collecter tous les résultats
    result_keys = [
        'redaction_result', 'timeline_result', 'mapping_result',
        'comparison_result', 'synthesis_result', 'ai_analysis_results',
        'search_results', 'plaidoirie_result', 'preparation_client_result'
    ]
    
    for key in result_keys:
        if key in st.session_state:
            work_data['results'][key] = st.session_state[key]
    
    # Sauvegarder
    import json
    
    json_str = json.dumps(work_data, indent=2, ensure_ascii=False, default=str)
    
    st.download_button(
        "💾 Télécharger la sauvegarde",
        json_str,
        f"sauvegarde_travail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="download_work_save"
    )

def show_work_statistics():
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

# ========================= FIN DU MODULE =========================

# ========================= PAGE PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "Entrez votre commande ou recherche",
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
    
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
            st.session_state.universal_query = "rédiger "
            st.session_state.process_query = True
    
    with col2:
        if st.button("🤖 Analyser dossier", key="quick_analysis"):
            st.session_state.universal_query = "analyser "
            st.session_state.process_query = True
    
    with col3:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.universal_query = "importer documents"
            st.session_state.process_query = True
    
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
            show_work_statistics()
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            share_current_work()

# ========================= ROUTING ET TRAITEMENT =========================

def process_universal_query(query: str):
    """Traite une requête universelle et route vers la bonne fonction"""
    
    # Sauvegarder la requête
    st.session_state.last_universal_query = query
    
    # Analyser la requête pour détecter le type
    query_lower = query.lower()
    
    # DÉTECTION POUR RÉDACTION (incluant votre cas de plainte)
    if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer', 'plainte', 'conclusions', 'courrier', 'assignation']):
        st.info("📝 Détection d'une demande de rédaction...")
        
        # Cas spécifique : plainte avec parties multiples
        if 'plainte' in query_lower:
            # Extraire les parties de la requête
            parties = []
            parties_keywords = [
                'interconstruction', 'vinci', 'sogeprom', 'demathieu bard',
                'bouygues', 'eiffage', 'spie', 'leon grosse'
            ]
            
            for partie in parties_keywords:
                if partie in query_lower:
                    # Formatage correct du nom
                    if partie == 'sogeprom':
                        parties.append('SOGEPROM Réalisations')
                    elif partie == 'demathieu bard':
                        parties.append('Demathieu Bard')
                    else:
                        parties.append(partie.title())
            
            # Extraire la référence
            reference = None
            if '@' in query:
                ref_match = re.search(r'@(\w+)', query)
                if ref_match:
                    reference = ref_match.group(1)
            
            # Créer la demande de rédaction
            st.session_state.redaction_request = {
                'type': 'plainte',
                'parties': parties,
                'reference': reference,
                'query': query
            }
            
            # Générer la plainte
            generate_plainte(query, parties)
        else:
            # Autres types de rédaction
            process_redaction_request(query, analyze_query(query))
    
    # PLAIDOIRIE
    elif any(word in query_lower for word in ['plaidoirie', 'plaider', 'audience']):
        st.info("🎤 Détection d'une demande de plaidoirie...")
        process_plaidoirie_request(query, analyze_query(query))
    
    # PRÉPARATION CLIENT
    elif any(word in query_lower for word in ['préparer client', 'préparation', 'coaching']):
        st.info("👥 Détection d'une demande de préparation client...")
        process_preparation_client_request(query, analyze_query(query))
    
    # IMPORT
    elif any(word in query_lower for word in ['import', 'importer', 'charger', 'upload']):
        st.info("📥 Détection d'une demande d'import...")
        process_import_request(query, analyze_query(query))
    
    # EXPORT
    elif any(word in query_lower for word in ['export', 'exporter', 'télécharger', 'download']):
        st.info("💾 Détection d'une demande d'export...")
        process_export_request(query, analyze_query(query))
    
    # EMAIL
    elif any(word in query_lower for word in ['email', 'envoyer', 'mail', 'courrier électronique']):
        st.info("📧 Détection d'une demande d'email...")
        process_email_request(query, analyze_query(query))
    
    # ANALYSE
    elif any(word in query_lower for word in ['analyser', 'analyse', 'étudier', 'examiner']):
        st.info("🤖 Détection d'une demande d'analyse...")
        process_analysis_request(query, analyze_query(query))
    
    # PIÈCES
    elif any(word in query_lower for word in ['sélectionner pièces', 'pièces', 'sélection']):
        st.info("📋 Détection d'une demande de sélection de pièces...")
        process_piece_selection_request(query, analyze_query(query))
    
    # BORDEREAU
    elif 'bordereau' in query_lower:
        st.info("📊 Détection d'une demande de bordereau...")
        process_bordereau_request(query, analyze_query(query))
    
    # SYNTHÈSE
    elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
        st.info("📝 Détection d'une demande de synthèse...")
        process_synthesis_request(query, analyze_query(query))
    
    # TEMPLATES
    elif any(word in query_lower for word in ['template', 'modèle', 'gabarit']):
        st.info("📄 Détection d'une demande de template...")
        process_template_request(query, analyze_query(query))
    
    # JURISPRUDENCE
    elif any(word in query_lower for word in ['jurisprudence', 'juris', 'décision', 'arrêt']):
        st.info("⚖️ Détection d'une demande de jurisprudence...")
        process_jurisprudence_request(query, analyze_query(query))
    
    # CHRONOLOGIE
    elif any(word in query_lower for word in ['chronologie', 'timeline', 'frise']):
        st.info("⏱️ Détection d'une demande de chronologie...")
        process_timeline_request(query, analyze_query(query))
    
    # CARTOGRAPHIE
    elif any(word in query_lower for word in ['cartographie', 'mapping', 'carte', 'réseau']):
        st.info("🗺️ Détection d'une demande de cartographie...")
        process_mapping_request(query, analyze_query(query))
    
    # COMPARAISON
    elif any(word in query_lower for word in ['comparer', 'comparaison', 'différences']):
        st.info("🔄 Détection d'une demande de comparaison...")
        process_comparison_request(query, analyze_query(query))
    
    else:
        # Recherche simple par défaut
        st.info("🔍 Recherche simple...")
        process_search_request(query, analyze_query(query))

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
    
    st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
    
    if not results:
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
    for i, result in enumerate(results[:20], 1):  # Limiter à 20
        with st.container():
            if view_mode == "Compact":
                st.markdown(f"**{i}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
            else:
                st.markdown(f"**{i}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
                
                # Extrait
                content = result.get('content', '')
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

# ========================= GESTION DES PIÈCES =========================

def process_piece_selection_request(query: str, analysis: dict):
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

def process_bordereau_request(query: str, analysis: dict):
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

def process_analysis_request(query: str, analysis: dict):
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

def process_redaction_request(query: str, analysis: dict):
    """Traite une demande de rédaction"""
    # Import depuis le module de rédaction
    st.info("📝 Traitement de la demande de rédaction...")
    # TODO: Implémenter ou importer depuis recherche_redaction

def generate_plainte(query: str, parties: list):
    """Génère une plainte avec les parties spécifiées"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        st.error("❌ Aucune IA disponible")
        return
    
    # Construire le prompt
    plainte_prompt = f"""Rédige une plainte pénale professionnelle.

DEMANDEUR: {st.session_state.get('client_nom', 'Le plaignant')}
PARTIES MISES EN CAUSE: {', '.join(parties)}
CONTEXTE: {query}

Structure la plainte avec:
1. En-tête (Tribunal compétent, identité du plaignant)
2. EXPOSÉ DES FAITS (chronologique et détaillé)
3. QUALIFICATION JURIDIQUE (infractions caractérisées)
4. PRÉJUDICES SUBIS (moral, matériel, financier)
5. DEMANDES (poursuites pénales, dommages-intérêts)
6. PIÈCES JOINTES

Style: Formel, juridique, factuel."""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            plainte_prompt,
            "Tu es un avocat expert en rédaction de plaintes pénales."
        )
        
        if response['success']:
            st.session_state.redaction_result = {
                'type': 'plainte',
                'document': response['response'],
                'provider': provider.value,
                'timestamp': datetime.now(),
                'parties': parties
            }
            st.rerun()
    except Exception as e:
        st.error(f"❌ Erreur génération: {str(e)}")

def process_plaidoirie_request(query: str, analysis: dict):
    """Traite une demande de plaidoirie"""
    st.info("🎤 Préparation de plaidoirie...")
    # TODO: Implémenter

def process_preparation_client_request(query: str, analysis: dict):
    """Traite une demande de préparation client"""
    st.info("👥 Préparation du client...")
    # TODO: Implémenter

def process_import_request(query: str, analysis: dict):
    """Traite une demande d'import"""
    st.info("📥 Import de documents...")
    # TODO: Implémenter

def process_export_request(query: str, analysis: dict):
    """Traite une demande d'export"""
    st.info("💾 Export en cours...")
    # TODO: Implémenter

def process_email_request(query: str, analysis: dict):
    """Traite une demande d'email"""
    st.info("📧 Préparation de l'email...")
    # TODO: Implémenter

def process_synthesis_request(query: str, analysis: dict):
    """Traite une demande de synthèse"""
    
    # Déterminer la source
    if st.session_state.get('selected_pieces'):
        content_to_synthesize = synthesize_selected_pieces(st.session_state.selected_pieces)
    elif analysis.get('reference'):
        docs = search_by_reference(f"@{analysis['reference']}")
        pieces = []
        for i, doc in enumerate(docs):
            pieces.append(PieceSelectionnee(
                numero=i + 1,
                titre=doc.get('title', 'Sans titre'),
                description=doc.get('content', '')[:200] + '...' if doc.get('content') else '',
                categorie=determine_document_category(doc),
                source=doc.get('source', '')
            ))
        content_to_synthesize = synthesize_selected_pieces(pieces)
    else:
        st.warning("⚠️ Aucun contenu à synthétiser")
        return

def process_template_request(query: str, analysis: dict):
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

def process_jurisprudence_request(query: str, analysis: dict):
    """Traite une demande de jurisprudence"""
    st.info("⚖️ Recherche de jurisprudence...")
    # TODO: Implémenter

def process_timeline_request(query: str, analysis: dict):
    """Traite une demande de chronologie"""
    st.info("⏱️ Création de la chronologie...")
    # TODO: Implémenter

def process_mapping_request(query: str, analysis: dict):
    """Traite une demande de cartographie"""
    st.info("🗺️ Création de la cartographie...")
    # TODO: Implémenter

def process_comparison_request(query: str, analysis: dict):
    """Traite une demande de comparaison"""
    st.info("🔄 Comparaison en cours...")
    # TODO: Implémenter

def process_search_request(query: str, analysis: dict):
    """Traite une demande de recherche simple"""
    
    results = []
    
    # Recherche selon le contexte
    if analysis.get('reference'):
        results = search_by_reference(f"@{analysis['reference']}")
    else:
        results = perform_search(query)
    
    # Stocker les résultats
    st.session_state.search_results = results
    
    if not results:
        st.warning("⚠️ Aucun résultat trouvé")
    else:
        st.success(f"✅ {len(results)} résultats trouvés")

# ========================= FONCTIONS HELPER =========================

def analyze_query(query: str) -> dict:
    """Analyse une requête pour extraire les informations clés"""
    
    analysis = {
        'original_query': query,
        'reference': None,
        'subject_matter': None,
        'document_type': None,
        'action': None
    }
    
    # Extraire la référence @
    ref_match = re.search(r'@(\w+)', query)
    if ref_match:
        analysis['reference'] = ref_match.group(1)
    
    # Détecter le type de document
    query_lower = query.lower()
    for doc_type in ['conclusions', 'plainte', 'courrier', 'assignation', 'mise en demeure']:
        if doc_type in query_lower:
            analysis['document_type'] = doc_type
            break
    
    # Détecter l'action principale
    actions = {
        'rédiger': 'redaction',
        'analyser': 'analysis',
        'rechercher': 'search',
        'comparer': 'comparison',
        'créer': 'creation'
    }
    
    for keyword, action in actions.items():
        if keyword in query_lower:
            analysis['action'] = action
            break
    
    # Extraire le sujet
    # Simplification - en production, utiliser NLP
    if 'abus' in query_lower and 'biens' in query_lower:
        analysis['subject_matter'] = 'abus de biens sociaux'
    elif 'corruption' in query_lower:
        analysis['subject_matter'] = 'corruption'
    elif 'fraude' in query_lower:
        analysis['subject_matter'] = 'fraude'
    
    return analysis

def collect_relevant_documents(analysis: dict) -> List[Dict[str, Any]]:
    """Collecte les documents pertinents selon l'analyse"""
    
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        documents.append({
            'id': doc_id,
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'metadata': doc.metadata
        })
    
    # Filtrer par référence si présente
    if analysis.get('reference'):
        ref_lower = analysis['reference'].lower()
        documents = [d for d in documents if ref_lower in d['title'].lower() or ref_lower in d.get('source', '').lower()]
    
    return documents

def collect_available_documents(analysis: dict) -> list:
    """Collecte tous les documents disponibles"""
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        documents.append({
            'id': doc_id,
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'metadata': doc.metadata
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

def calculate_piece_relevance(doc: dict, analysis: dict) -> float:
    """Calcule la pertinence d'une pièce"""
    score = 0.5
    
    if analysis.get('subject_matter'):
        if analysis['subject_matter'] in doc.get('content', '').lower():
            score += 0.3
    
    if analysis.get('reference'):
        if analysis['reference'] in doc.get('title', '').lower():
            score += 0.2
    
    return min(score, 1.0)

def create_bordereau(pieces: list, analysis: dict) -> dict:
    """Crée un bordereau structuré"""
    
    bordereau = {
        'header': f"""BORDEREAU DE COMMUNICATION DE PIÈCES
AFFAIRE : {analysis.get('reference', 'N/A').upper()}
DATE : {datetime.now().strftime('%d/%m/%Y')}
NOMBRE DE PIÈCES : {len(pieces)}""",
        'pieces': pieces,
        'footer': f"""Je certifie que les pièces communiquées sont conformes aux originaux.
Fait le {datetime.now().strftime('%d/%m/%Y')}""",
        'metadata': {
            'created_at': datetime.now(),
            'piece_count': len(pieces),
            'reference': analysis.get('reference')
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
        if piece.date:
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
        if ref_clean in doc.title.lower() or ref_clean in doc.source.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source
            })
    
    return results

def perform_search(query: str) -> List[Dict[str, Any]]:
    """Effectue une recherche générale"""
    
    results = []
    query_lower = query.lower()
    query_words = query_lower.split()
    
    # Recherche locale
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        score = 0
        content_lower = doc.content.lower()
        title_lower = doc.title.lower()
        
        for word in query_words:
            if word in title_lower:
                score += 2
            if word in content_lower:
                score += 1
        
        if score > 0:
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'score': score / len(query_words)
            })
    
    # Recherche Azure si disponible
    try:
        search_manager = st.session_state.get('azure_search_manager')
        if search_manager and search_manager.is_connected():
            azure_results = search_manager.search(query)
            results.extend(azure_results)
    except:
        pass
    
    return sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:50]

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
        'analysis': st.session_state.get('current_analysis', {}),
        'results': {}
    }
    
    # Collecter tous les résultats
    result_keys = [
        'redaction_result', 'timeline_result', 'mapping_result',
        'comparison_result', 'synthesis_result', 'ai_analysis_results',
        'search_results', 'plaidoirie_result', 'preparation_client_result'
    ]
    
    for key in result_keys:
        if key in st.session_state:
            work_data['results'][key] = st.session_state[key]
    
    # Sauvegarder
    import json
    
    json_str = json.dumps(work_data, indent=2, ensure_ascii=False, default=str)
    
    st.download_button(
        "💾 Télécharger la sauvegarde",
        json_str,
        f"sauvegarde_travail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="download_work_save"
    )

def show_work_statistics():
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

# ========================= FIN DU MODULE =========================