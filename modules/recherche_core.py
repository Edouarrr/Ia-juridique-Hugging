"""Core du module de recherche - Interface principale et routing"""

import streamlit as st
import re
from datetime import datetime

# Imports des sous-modules
from .recherche_config import REDACTION_STYLES, DOCUMENT_TEMPLATES
from .recherche_import import process_import_request
from .recherche_export import process_export_request
from .recherche_email import process_email_request
from .recherche_redaction import process_redaction_request, generate_plainte
from .recherche_analysis import process_analysis_request
from .recherche_pieces import (
    process_piece_selection_request,
    process_bordereau_request,
    process_synthesis_request
)
from .recherche_templates import process_template_request
from .recherche_jurisprudence import process_jurisprudence_request
from .recherche_visualizations import (
    process_timeline_request,
    process_mapping_request,
    process_comparison_request
)
from .recherche_search import process_search_request
from .recherche_display import show_unified_results_tab
from .recherche_utils import analyze_query

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
        from .recherche_plaidoirie import process_plaidoirie_request
        process_plaidoirie_request(query, analyze_query(query))
    
    # PRÉPARATION CLIENT
    elif any(word in query_lower for word in ['préparer client', 'préparation', 'coaching']):
        st.info("👥 Détection d'une demande de préparation client...")
        from .recherche_preparation import process_preparation_client_request
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