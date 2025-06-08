# modules/recherche.py
"""Module de recherche unifié - Version allégée qui coordonne les autres modules"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List
import re

# Import des managers
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from managers.multi_llm_manager import MultiLLMManager
from managers.dynamic_generators import generate_dynamic_search_prompts

# Import des modules spécialisés
from modules.import_export import process_import_request, process_export_request
from modules.mapping import process_mapping_request
from modules.comparison import process_comparison_request
from modules.timeline import process_timeline_request
from modules.redaction import process_redaction_request
from modules.plaidoirie import process_plaidoirie_request
from modules.preparation_client import process_preparation_client_request
from modules.synthesis import process_synthesis_request
from modules.bordereau import process_bordereau_request, process_piece_selection_request
from modules.email import process_email_request

# Import des modèles et helpers
from models.dataclasses import Document, QueryAnalysis
from utils.helpers import analyze_query_intent, clean_key

# Configuration
from config.app_config import SearchMode

def show_page():
    """Affiche la page principale de recherche unifiée"""
    
    st.markdown("### 🔍 Interface de Recherche Unifiée")
    
    # Barre de recherche universelle
    query = st.text_input(
        "Que souhaitez-vous faire ?",
        placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, créer chronologie...",
        key="universal_query",
        help="Utilisez @ pour référencer un dossier spécifique"
    )
    
    # Boutons d'action rapide
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📝 Rédiger", key="quick_redact"):
            st.session_state.universal_query = "rédiger document juridique"
    
    with col2:
        if st.button("🔍 Analyser", key="quick_analyze"):
            st.session_state.universal_query = "analyser les risques"
    
    with col3:
        if st.button("⏱️ Chronologie", key="quick_timeline"):
            st.session_state.universal_query = "créer chronologie"
    
    with col4:
        if st.button("📊 Comparer", key="quick_compare"):
            st.session_state.universal_query = "comparer documents"
    
    with col5:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.universal_query = "importer documents"
    
    # Traiter la requête
    if query or st.session_state.get('universal_query'):
        process_universal_query(query or st.session_state.universal_query)
    
    # Afficher les résultats dans des tabs
    show_results_tabs()

def process_universal_query(query: str):
    """Traite une requête universelle et route vers la bonne fonction"""
    
    if not query.strip():
        return
    
    # Sauvegarder la requête
    st.session_state.last_universal_query = query
    
    # Analyser l'intention
    with st.spinner("🤔 Analyse de votre demande..."):
        analysis = analyze_query_intent(query)
        st.session_state.current_analysis = analysis
    
    # Router selon l'intention détectée
    intent_handlers = {
        'redaction': process_redaction_request,
        'plaidoirie': process_plaidoirie_request,
        'preparation_client': process_preparation_client_request,
        'timeline': process_timeline_request,
        'mapping': process_mapping_request,
        'comparison': process_comparison_request,
        'import': process_import_request,
        'export': process_export_request,
        'email': process_email_request,
        'synthesis': process_synthesis_request,
        'piece_selection': process_piece_selection_request,
        'bordereau': process_bordereau_request,
        'analysis': process_analysis_request,
        'search': process_search_request,
        'jurisprudence': process_jurisprudence_request,
        'template': process_template_request
    }
    
    handler = intent_handlers.get(analysis.intent, process_search_request)
    
    try:
        handler(query, analysis.to_dict())
    except Exception as e:
        st.error(f"❌ Erreur lors du traitement : {str(e)}")
        if st.checkbox("Voir les détails de l'erreur"):
            st.exception(e)

def show_results_tabs():
    """Affiche les résultats dans des onglets organisés"""
    
    # Déterminer quels onglets afficher
    tabs_to_show = []
    
    if any(st.session_state.get(key) for key in [
        'search_results', 'redaction_result', 'timeline_result', 
        'mapping_result', 'ai_analysis_results'
    ]):
        tabs_to_show.append("📊 Résultats")
    
    if st.session_state.get('selected_pieces') or st.session_state.get('current_bordereau'):
        tabs_to_show.append("📋 Pièces")
    
    if st.session_state.get('jurisprudence_search_active'):
        tabs_to_show.append("⚖️ Jurisprudence")
    
    tabs_to_show.extend(["📁 Explorateur", "⚙️ Configuration"])
    
    # Créer les onglets
    tabs = st.tabs(tabs_to_show)
    
    # Contenu des onglets
    tab_index = 0
    
    if "📊 Résultats" in tabs_to_show:
        with tabs[tab_index]:
            show_unified_results_tab()
        tab_index += 1
    
    if "📋 Pièces" in tabs_to_show:
        with tabs[tab_index]:
            show_pieces_management_tab()
        tab_index += 1
    
    if "⚖️ Jurisprudence" in tabs_to_show:
        with tabs[tab_index]:
            show_jurisprudence_tab()
        tab_index += 1
    
    with tabs[tab_index]:  # Explorateur
        show_explorer_tab()
    tab_index += 1
    
    with tabs[tab_index]:  # Configuration
        show_configuration_tab()

def show_unified_results_tab():
    """Affiche tous les types de résultats dans un onglet unifié"""
    
    # Import des fonctions d'affichage depuis les modules
    from modules.redaction import show_redaction_results
    from modules.plaidoirie import show_plaidoirie_results
    from modules.preparation_client import show_preparation_client_results
    from modules.timeline import show_timeline_results
    from modules.mapping import show_mapping_results
    from modules.comparison import show_comparison_results
    from modules.synthesis import show_synthesis_results
    
    # Vérifier quel type de résultat afficher
    has_results = False
    
    # Affichage selon la priorité
    if st.session_state.get('redaction_result'):
        show_redaction_results()
        has_results = True
    
    elif st.session_state.get('plaidoirie_result'):
        show_plaidoirie_results()
        has_results = True
    
    elif st.session_state.get('preparation_client_result'):
        show_preparation_client_results()
        has_results = True
    
    elif st.session_state.get('timeline_result'):
        show_timeline_results()
        has_results = True
    
    elif st.session_state.get('mapping_result'):
        show_mapping_results()
        has_results = True
    
    elif st.session_state.get('comparison_result'):
        show_comparison_results()
        has_results = True
    
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        has_results = True
    
    elif st.session_state.get('ai_analysis_results'):
        show_ai_analysis_results()
        has_results = True
    
    elif st.session_state.get('search_results'):
        show_search_results()
        has_results = True
    
    if not has_results:
        show_welcome_message()

def show_welcome_message():
    """Affiche le message de bienvenue avec exemples"""
    
    st.info("💡 Utilisez la barre de recherche universelle pour commencer")
    
    st.markdown("""
    ### 🚀 Exemples de commandes
    
    **Recherche :**
    - `contrats société XYZ`
    - `@affaire_martin documents comptables`
    
    **Analyse :**
    - `analyser les risques @dossier_pénal`
    - `identifier les infractions @affaire_corruption`
    
    **Rédaction :**
    - `rédiger conclusions défense @affaire_martin abus biens sociaux`
    - `créer plainte avec constitution partie civile escroquerie`
    
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
    - `exporter analyse format word`
    """)

def process_analysis_request(query: str, analysis: dict):
    """Traite une demande d'analyse IA"""
    
    # Collecter les documents pertinents
    documents = collect_relevant_documents(analysis)
    
    if not documents:
        st.warning("⚠️ Aucun document trouvé pour l'analyse")
        return
    
    # Déterminer le type d'analyse
    analysis_type = detect_analysis_type(query)
    
    # Lancer l'analyse appropriée
    with st.spinner("🤖 Analyse en cours..."):
        if analysis_type == 'risks':
            results = analyze_legal_risks(documents, query)
        elif analysis_type == 'compliance':
            results = analyze_compliance(documents, query)
        elif analysis_type == 'strategy':
            results = analyze_strategy(documents, query)
        else:
            results = perform_general_analysis(documents, query)
    
    # Stocker les résultats
    st.session_state.ai_analysis_results = results

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

def process_jurisprudence_request(query: str, analysis: dict):
    """Traite une demande de recherche de jurisprudence"""
    
    from modules.jurisprudence import show_jurisprudence_interface
    st.session_state.jurisprudence_search_active = True
    show_jurisprudence_interface(query, analysis)

def process_template_request(query: str, analysis: dict):
    """Traite une demande liée aux templates"""
    
    from modules.templates import process_template_action
    process_template_action(query, analysis)

# Fonctions helper

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

def detect_analysis_type(query: str) -> str:
    """Détecte le type d'analyse demandé"""
    
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['risque', 'danger', 'exposition']):
        return 'risks'
    elif any(word in query_lower for word in ['conformité', 'compliance']):
        return 'compliance'
    elif any(word in query_lower for word in ['stratégie', 'défense']):
        return 'strategy'
    else:
        return 'general'

def search_by_reference(reference: str) -> List[Dict[str, Any]]:
    """Recherche par référence @"""
    
    results = []
    ref_clean = reference.replace('@', '').strip().lower()
    
    # Recherche dans les documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if ref_clean in doc.title.lower() or ref_clean in doc.source.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'score': 1.0 if ref_clean == doc.title.lower() else 0.8
            })
    
    # Recherche Azure si disponible
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and search_manager.is_connected():
        try:
            azure_results = search_manager.search(reference)
            results.extend(azure_results)
        except:
            pass
    
    return sorted(results, key=lambda x: x.get('score', 0), reverse=True)

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
    
    # Recherche Azure
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and search_manager.is_connected():
        try:
            azure_results = search_manager.search(query)
            results.extend(azure_results)
        except:
            pass
    
    return sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:50]

# Analyses spécialisées

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
    # Similaire à analyze_legal_risks mais avec focus conformité
    pass

def analyze_strategy(documents: List[Dict[str, Any]], query: str) -> dict:
    """Analyse stratégique"""
    # Similaire à analyze_legal_risks mais avec focus stratégie
    pass

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

# Affichage des résultats

def show_ai_analysis_results():
    """Affiche les résultats d'analyse IA"""
    
    results = st.session_state.ai_analysis_results
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    analysis_titles = {
        'risk_analysis': '⚠️ Analyse des risques',
        'compliance': '✅ Analyse de conformité',
        'strategy': '🎯 Analyse stratégique',
        'general_analysis': '🤖 Analyse générale'
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
    
    # Contenu
    st.markdown("#### 📊 Résultats de l'analyse")
    
    st.text_area(
        "Analyse détaillée",
        value=results.get('content', ''),
        height=600,
        key="ai_analysis_content"
    )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.download_button(
            "💾 Télécharger",
            results.get('content', '').encode('utf-8'),
            f"analyse_{results.get('type', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain",
            key="download_analysis"
        ):
            st.success("✅ Analyse téléchargée")

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
            ["Pertinence", "Titre", "Date"],
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
    for i, result in enumerate(results[:20]):
        with st.container():
            if view_mode == "Compact":
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{i+1}. {result.get('title', 'Sans titre')}**")
                    st.caption(f"Source: {result.get('source', 'N/A')}")
                
                with col2:
                    if result.get('score'):
                        st.metric("Score", f"{result['score']:.0%}")
            
            else:  # Détaillé
                st.markdown(f"**{i+1}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
                
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

# Autres onglets

def show_pieces_management_tab():
    """Affiche l'onglet de gestion des pièces"""
    from modules.bordereau import show_pieces_interface
    show_pieces_interface()

def show_jurisprudence_tab():
    """Affiche l'onglet jurisprudence"""
    from modules.jurisprudence import show_jurisprudence_interface
    show_jurisprudence_interface()

def show_explorer_tab():
    """Affiche l'explorateur de fichiers"""
    from modules.explorer import show_explorer_interface
    show_explorer_interface()

def show_configuration_tab():
    """Affiche l'onglet de configuration"""
    from modules.configuration import show_configuration_interface
    show_configuration_interface()