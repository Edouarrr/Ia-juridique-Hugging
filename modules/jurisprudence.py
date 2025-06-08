# modules/jurisprudence.py
"""Module de recherche et gestion de la jurisprudence"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import re

from models.dataclasses import (
    JurisprudenceReference,
    VerificationResult,
    SourceJurisprudence,
    TypeJuridiction,
    get_all_juridictions
)
from managers.jurisprudence_verifier import JurisprudenceVerifier
from managers.legal_search import LegalSearchManager
from utils.helpers import clean_key, highlight_text

# Configuration des sources
SOURCE_CONFIGS = {
    SourceJurisprudence.LEGIFRANCE: {
        'name': 'Légifrance',
        'icon': '🏛️',
        'url': 'https://www.legifrance.gouv.fr',
        'api_available': True
    },
    SourceJurisprudence.DOCTRINE: {
        'name': 'Doctrine.fr',
        'icon': '📚',
        'url': 'https://www.doctrine.fr',
        'api_available': False
    },
    SourceJurisprudence.DALLOZ: {
        'name': 'Dalloz',
        'icon': '📖',
        'url': 'https://www.dalloz.fr',
        'api_available': False
    },
    SourceJurisprudence.COURDECASSATION: {
        'name': 'Cour de cassation',
        'icon': '⚖️',
        'url': 'https://www.courdecassation.fr',
        'api_available': True
    }
}

def process_jurisprudence_request(query: str, analysis: dict):
    """Traite une demande de recherche de jurisprudence"""
    
    st.markdown("### ⚖️ Recherche de jurisprudence")
    
    # Activer le mode jurisprudence
    st.session_state.jurisprudence_search_active = True
    
    # Extraire les critères de recherche
    search_criteria = extract_jurisprudence_criteria(query, analysis)
    
    # Interface de recherche
    show_jurisprudence_search_interface(search_criteria)

def extract_jurisprudence_criteria(query: str, analysis: dict) -> Dict[str, Any]:
    """Extrait les critères de recherche jurisprudentielle"""
    
    criteria = {
        'keywords': [],
        'juridictions': [],
        'date_range': None,
        'numero': None,
        'articles': [],
        'parties': []
    }
    
    query_lower = query.lower()
    
    # Mots-clés juridiques
    legal_keywords = [
        'responsabilité', 'préjudice', 'dommages', 'faute', 'causalité',
        'contrat', 'obligation', 'résiliation', 'nullité', 'prescription',
        'procédure', 'compétence', 'recevabilité', 'appel', 'cassation'
    ]
    
    criteria['keywords'] = [kw for kw in legal_keywords if kw in query_lower]
    
    # Ajouter les termes de l'analyse
    if analysis.get('legal_terms'):
        criteria['keywords'].extend(analysis['legal_terms'])
    
    # Juridictions
    for juridiction in get_all_juridictions():
        if juridiction.lower() in query_lower:
            criteria['juridictions'].append(juridiction)
    
    # Numéro de décision
    numero_pattern = r'\b(\d{2}-\d{2}\.\d{3}|\d{2}-\d{5})\b'
    numero_match = re.search(numero_pattern, query)
    if numero_match:
        criteria['numero'] = numero_match.group(1)
    
    # Articles de loi
    article_pattern = r'article\s+([LR]?\s*\d+(?:-\d+)?)'
    articles = re.findall(article_pattern, query, re.IGNORECASE)
    criteria['articles'] = articles
    
    return criteria

def show_jurisprudence_search_interface(initial_criteria: Dict[str, Any] = None):
    """Interface principale de recherche jurisprudentielle"""
    
    # Gestionnaires
    verifier = st.session_state.get('jurisprudence_verifier', JurisprudenceVerifier())
    search_manager = st.session_state.get('legal_search_manager', LegalSearchManager())
    
    # Onglets
    tabs = st.tabs([
        "🔍 Recherche",
        "✅ Vérification",
        "📚 Base locale",
        "📊 Statistiques",
        "⚙️ Configuration"
    ])
    
    with tabs[0]:
        show_search_tab(search_manager, initial_criteria)
    
    with tabs[1]:
        show_verification_tab(verifier)
    
    with tabs[2]:
        show_local_database_tab()
    
    with tabs[3]:
        show_statistics_tab()
    
    with tabs[4]:
        show_configuration_tab()

def show_search_tab(search_manager: LegalSearchManager, initial_criteria: Dict[str, Any] = None):
    """Onglet de recherche"""
    
    st.markdown("#### 🔍 Recherche de jurisprudence")
    
    # Formulaire de recherche
    with st.form("jurisprudence_search_form"):
        # Recherche textuelle
        query = st.text_input(
            "Recherche libre",
            value=" ".join(initial_criteria.get('keywords', [])) if initial_criteria else "",
            placeholder="Ex: responsabilité contractuelle dommages-intérêts",
            key="juris_free_search"
        )
        
        # Critères avancés
        col1, col2 = st.columns(2)
        
        with col1:
            # Juridictions
            selected_juridictions = st.multiselect(
                "Juridictions",
                options=get_all_juridictions(),
                default=initial_criteria.get('juridictions', []) if initial_criteria else [],
                key="juris_juridictions"
            )
            
            # Période
            date_range = st.selectbox(
                "Période",
                ["Toutes", "1 mois", "6 mois", "1 an", "5 ans", "10 ans", "Personnalisée"],
                key="juris_date_range"
            )
            
            if date_range == "Personnalisée":
                date_start = st.date_input("Date début", key="juris_date_start")
                date_end = st.date_input("Date fin", key="juris_date_end")
        
        with col2:
            # Sources
            selected_sources = st.multiselect(
                "Sources",
                options=[s.value for s in SourceJurisprudence],
                default=[SourceJurisprudence.LEGIFRANCE.value],
                format_func=lambda x: SOURCE_CONFIGS[SourceJurisprudence(x)]['name'],
                key="juris_sources"
            )
            
            # Importance
            min_importance = st.slider(
                "Importance minimale",
                min_value=1,
                max_value=10,
                value=5,
                key="juris_importance"
            )
        
        # Articles visés
        articles = st.text_input(
            "Articles visés (séparés par des virgules)",
            value=", ".join(initial_criteria.get('articles', [])) if initial_criteria else "",
            placeholder="Ex: L.1142-1, L.1142-2",
            key="juris_articles"
        )
        
        # Options de recherche
        with st.expander("Options avancées", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                search_in_summary = st.checkbox("Rechercher dans les résumés", value=True)
                search_in_full_text = st.checkbox("Rechercher dans le texte intégral", value=False)
                
            with col2:
                only_principle = st.checkbox("Décisions de principe uniquement", value=False)
                with_commentary = st.checkbox("Avec commentaires uniquement", value=False)
        
        # Bouton de recherche
        search_submitted = st.form_submit_button("🔍 Rechercher", type="primary")
    
    # Lancer la recherche
    if search_submitted:
        perform_jurisprudence_search(
            query,
            selected_juridictions,
            selected_sources,
            articles,
            date_range,
            min_importance,
            search_in_summary,
            search_in_full_text,
            only_principle,
            with_commentary
        )
    
    # Afficher les résultats
    show_search_results()

def perform_jurisprudence_search(
    query: str,
    juridictions: List[str],
    sources: List[str],
    articles: str,
    date_range: str,
    min_importance: int,
    search_in_summary: bool,
    search_in_full_text: bool,
    only_principle: bool,
    with_commentary: bool
):
    """Effectue la recherche de jurisprudence"""
    
    with st.spinner("🔍 Recherche en cours..."):
        # Construire les critères
        search_criteria = {
            'query': query,
            'juridictions': juridictions,
            'sources': [SourceJurisprudence(s) for s in sources],
            'articles': [a.strip() for a in articles.split(',') if a.strip()],
            'date_range': parse_date_range(date_range),
            'min_importance': min_importance,
            'search_in_summary': search_in_summary,
            'search_in_full_text': search_in_full_text,
            'only_principle': only_principle,
            'with_commentary': with_commentary
        }
        
        # Rechercher
        results = search_jurisprudence(search_criteria)
        
        # Stocker les résultats
        st.session_state.jurisprudence_results = results
        st.session_state.jurisprudence_search_criteria = search_criteria
        
        if results:
            st.success(f"✅ {len(results)} décision(s) trouvée(s)")
        else:
            st.warning("⚠️ Aucune décision trouvée")

def search_jurisprudence(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche la jurisprudence selon les critères"""
    
    results = []
    
    # Recherche dans les sources
    for source in criteria['sources']:
        if source == SourceJurisprudence.LEGIFRANCE:
            results.extend(search_legifrance(criteria))
        
        elif source == SourceJurisprudence.COURDECASSATION:
            results.extend(search_cour_cassation(criteria))
        
        elif source == SourceJurisprudence.INTERNAL:
            results.extend(search_internal_database(criteria))
    
    # Filtrer par importance
    results = [r for r in results if r.importance >= criteria['min_importance']]
    
    # Trier par pertinence et date
    results.sort(key=lambda x: (x.importance, x.date), reverse=True)
    
    return results

def search_legifrance(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche sur Légifrance (simulation)"""
    
    # Pour l'instant, retourner des exemples
    sample_results = []
    
    if 'responsabilité' in criteria['query'].lower():
        sample_results.append(
            JurisprudenceReference(
                numero="19-21.524",
                date=datetime(2021, 3, 17),
                juridiction="Cour de cassation, chambre civile 1",
                type_juridiction=TypeJuridiction.COUR_DE_CASSATION,
                formation="Première chambre civile",
                titre="Responsabilité contractuelle - Obligation de résultat",
                resume="La responsabilité du transporteur est engagée de plein droit en cas de retard dans la livraison.",
                url="https://www.legifrance.gouv.fr/juri/id/JURITEXT000043268591",
                source=SourceJurisprudence.LEGIFRANCE,
                mots_cles=["responsabilité", "transport", "retard", "obligation de résultat"],
                articles_vises=["Article 1231-1 du Code civil"],
                importance=8,
                solution="Cassation",
                portee="Principe"
            )
        )
    
    return sample_results

def search_cour_cassation(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche sur le site de la Cour de cassation"""
    # Implémentation similaire
    return []

def search_internal_database(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche dans la base locale"""
    
    results = []
    
    # Récupérer la base locale
    local_db = st.session_state.get('jurisprudence_database', {})
    
    for ref_id, ref in local_db.items():
        # Vérifier les critères
        score = 0
        
        # Mots-clés
        if criteria['query']:
            query_words = criteria['query'].lower().split()
            ref_text = f"{ref.titre} {ref.resume}".lower()
            
            for word in query_words:
                if word in ref_text:
                    score += 1
        
        # Juridiction
        if criteria['juridictions']:
            if ref.juridiction in criteria['juridictions']:
                score += 2
        
        # Articles
        if criteria['articles']:
            for article in criteria['articles']:
                if article in ref.articles_vises:
                    score += 3
        
        # Date
        if criteria['date_range']:
            start, end = criteria['date_range']
            if start <= ref.date <= end:
                score += 1
            else:
                continue
        
        if score > 0:
            results.append(ref)
    
    return results

def parse_date_range(date_range: str) -> Optional[Tuple[datetime, datetime]]:
    """Parse la période de recherche"""
    
    if date_range == "Toutes":
        return None
    
    end_date = datetime.now()
    
    if date_range == "1 mois":
        start_date = end_date - timedelta(days=30)
    elif date_range == "6 mois":
        start_date = end_date - timedelta(days=180)
    elif date_range == "1 an":
        start_date = end_date - timedelta(days=365)
    elif date_range == "5 ans":
        start_date = end_date - timedelta(days=365*5)
    elif date_range == "10 ans":
        start_date = end_date - timedelta(days=365*10)
    else:
        return None
    
    return (start_date, end_date)

def show_search_results():
    """Affiche les résultats de recherche"""
    
    results = st.session_state.get('jurisprudence_results', [])
    
    if not results:
        return
    
    st.markdown(f"#### 📊 Résultats ({len(results)} décisions)")
    
    # Options d'affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Date", "Juridiction", "Importance"],
            key="juris_sort"
        )
    
    with col2:
        view_mode = st.radio(
            "Affichage",
            ["Résumé", "Détaillé"],
            key="juris_view_mode",
            horizontal=True
        )
    
    with col3:
        group_by = st.selectbox(
            "Grouper par",
            ["Aucun", "Juridiction", "Année", "Matière"],
            key="juris_group"
        )
    
    # Trier les résultats
    sorted_results = sort_jurisprudence_results(results, sort_by)
    
    # Grouper si demandé
    if group_by != "Aucun":
        grouped_results = group_jurisprudence_results(sorted_results, group_by)
        
        for group_name, group_results in grouped_results.items():
            with st.expander(f"{group_name} ({len(group_results)} décisions)", expanded=True):
                for ref in group_results:
                    show_jurisprudence_item(ref, view_mode)
    else:
        # Affichage simple
        for ref in sorted_results:
            show_jurisprudence_item(ref, view_mode)

def sort_jurisprudence_results(results: List[JurisprudenceReference], sort_by: str) -> List[JurisprudenceReference]:
    """Trie les résultats de jurisprudence"""
    
    if sort_by == "Date":
        return sorted(results, key=lambda x: x.date, reverse=True)
    elif sort_by == "Juridiction":
        return sorted(results, key=lambda x: x.juridiction)
    elif sort_by == "Importance":
        return sorted(results, key=lambda x: x.importance, reverse=True)
    else:  # Pertinence
        return results  # Déjà trié par pertinence

def group_jurisprudence_results(results: List[JurisprudenceReference], group_by: str) -> Dict[str, List[JurisprudenceReference]]:
    """Groupe les résultats de jurisprudence"""
    
    grouped = {}
    
    for ref in results:
        if group_by == "Juridiction":
            key = ref.juridiction
        elif group_by == "Année":
            key = str(ref.date.year)
        elif group_by == "Matière":
            # Déterminer la matière depuis les mots-clés
            if any(kw in ['contrat', 'obligation', 'responsabilité contractuelle'] for kw in ref.mots_cles):
                key = "Droit des contrats"
            elif any(kw in ['responsabilité', 'préjudice', 'dommages'] for kw in ref.mots_cles):
                key = "Responsabilité civile"
            elif any(kw in ['procédure', 'compétence', 'appel'] for kw in ref.mots_cles):
                key = "Procédure civile"
            else:
                key = "Autres"
        else:
            key = "Tous"
        
        if key not in grouped:
            grouped[key] = []
        
        grouped[key].append(ref)
    
    return grouped

def show_jurisprudence_item(ref: JurisprudenceReference, view_mode: str):
    """Affiche un élément de jurisprudence"""
    
    with st.container():
        if view_mode == "Résumé":
            # Vue compacte
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Titre avec lien
                if ref.url:
                    st.markdown(f"**[{ref.get_citation()}]({ref.url})**")
                else:
                    st.markdown(f"**{ref.get_citation()}**")
                
                if ref.titre:
                    st.caption(ref.titre)
            
            with col2:
                # Importance
                importance_color = "🟢" if ref.importance >= 8 else "🟡" if ref.importance >= 5 else "🔴"
                st.write(f"{importance_color} {ref.importance}/10")
            
            with col3:
                # Actions
                if st.button("📖", key=f"view_juris_{ref.numero}"):
                    show_jurisprudence_detail(ref)
                
                if st.button("📌", key=f"save_juris_{ref.numero}"):
                    save_to_favorites(ref)
        
        else:  # Vue détaillée
            # En-tête
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if ref.url:
                    st.markdown(f"### [{ref.get_citation()}]({ref.url})")
                else:
                    st.markdown(f"### {ref.get_citation()}")
            
            with col2:
                importance_color = "🟢" if ref.importance >= 8 else "🟡" if ref.importance >= 5 else "🔴"
                st.metric("Importance", f"{importance_color} {ref.importance}/10")
            
            # Métadonnées
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Formation :** {ref.formation or 'N/A'}")
                st.write(f"**Solution :** {ref.solution or 'N/A'}")
            
            with col2:
                st.write(f"**Portée :** {ref.portee or 'N/A'}")
                st.write(f"**Source :** {SOURCE_CONFIGS[ref.source]['name']}")
            
            with col3:
                if ref.articles_vises:
                    st.write(f"**Articles :** {', '.join(ref.articles_vises[:3])}")
                    if len(ref.articles_vises) > 3:
                        st.caption(f"... et {len(ref.articles_vises) - 3} autres")
            
            # Résumé
            if ref.resume:
                st.markdown("**Résumé :**")
                st.info(ref.resume)
            
            # Mots-clés
            if ref.mots_cles:
                st.write("**Mots-clés :** " + " • ".join([f"`{kw}`" for kw in ref.mots_cles]))
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📖 Texte intégral", key=f"full_text_{ref.numero}"):
                    show_full_text(ref)
            
            with col2:
                if st.button("🔗 Décisions liées", key=f"related_{ref.numero}"):
                    show_related_decisions(ref)
            
            with col3:
                if st.button("💬 Commentaires", key=f"comments_{ref.numero}"):
                    show_commentaries(ref)
            
            with col4:
                if st.button("📌 Sauvegarder", key=f"save_detail_{ref.numero}"):
                    save_to_favorites(ref)
        
        st.divider()

def show_jurisprudence_detail(ref: JurisprudenceReference):
    """Affiche le détail d'une décision"""
    
    st.session_state.current_jurisprudence = ref
    st.session_state.show_jurisprudence_detail = True

def save_to_favorites(ref: JurisprudenceReference):
    """Sauvegarde une décision dans les favoris"""
    
    if 'jurisprudence_favorites' not in st.session_state:
        st.session_state.jurisprudence_favorites = {}
    
    ref_id = f"{ref.numero}_{ref.date.strftime('%Y%m%d')}"
    st.session_state.jurisprudence_favorites[ref_id] = ref
    
    st.success("📌 Décision sauvegardée dans les favoris")

def show_full_text(ref: JurisprudenceReference):
    """Affiche le texte intégral"""
    
    if ref.texte_integral:
        with st.expander("📄 Texte intégral", expanded=True):
            st.text_area(
                "Texte de la décision",
                value=ref.texte_integral,
                height=600,
                key=f"full_text_display_{ref.numero}"
            )
    else:
        st.info("Texte intégral non disponible. Consultez le lien source.")
        if ref.url:
            st.markdown(f"[Voir sur {SOURCE_CONFIGS[ref.source]['name']}]({ref.url})")

def show_related_decisions(ref: JurisprudenceReference):
    """Affiche les décisions liées"""
    
    with st.spinner("Recherche des décisions liées..."):
        # Rechercher les décisions citées
        related = []
        
        if ref.decisions_citees:
            for decision_ref in ref.decisions_citees:
                # Essayer de trouver la décision
                # Pour l'instant, juste afficher la référence
                related.append(decision_ref)
        
        # Rechercher les décisions similaires
        similar_criteria = {
            'query': ' '.join(ref.mots_cles[:3]),
            'juridictions': [ref.juridiction],
            'sources': [ref.source],
            'articles': ref.articles_vises[:2],
            'date_range': None,
            'min_importance': ref.importance - 2
        }
        
        similar_results = search_jurisprudence(similar_criteria)
        
        # Filtrer la décision actuelle
        similar_results = [r for r in similar_results if r.numero != ref.numero]
        
        # Afficher
        if related or similar_results:
            st.markdown("#### 🔗 Décisions liées")
            
            if related:
                st.write("**Décisions citées :**")
                for dec_ref in related:
                    st.write(f"• {dec_ref}")
            
            if similar_results:
                st.write(f"**Décisions similaires ({len(similar_results)}) :**")
                for similar in similar_results[:5]:
                    st.write(f"• {similar.get_citation()}")
                    if similar.titre:
                        st.caption(similar.titre)
        else:
            st.info("Aucune décision liée trouvée")

def show_commentaries(ref: JurisprudenceReference):
    """Affiche les commentaires"""
    
    if ref.commentaires:
        st.markdown("#### 💬 Commentaires")
        
        for i, commentaire in enumerate(ref.commentaires, 1):
            with st.expander(f"Commentaire {i}"):
                st.write(commentaire)
    else:
        st.info("Aucun commentaire disponible pour cette décision")

def show_verification_tab(verifier: JurisprudenceVerifier):
    """Onglet de vérification"""
    
    st.markdown("#### ✅ Vérification de jurisprudence")
    
    st.info("""
    Vérifiez l'authenticité et la validité d'une référence de jurisprudence.
    Entrez la référence complète ou partielle.
    """)
    
    # Formulaire de vérification
    with st.form("verification_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            reference = st.text_input(
                "Référence à vérifier",
                placeholder="Ex: Cass. civ. 1, 17 mars 2021, n° 19-21.524",
                key="verify_reference"
            )
        
        with col2:
            verify_button = st.form_submit_button("🔍 Vérifier", type="primary")
    
    if verify_button and reference:
        with st.spinner("Vérification en cours..."):
            result = verifier.verify_reference(reference)
            show_verification_result(result)
    
    # Historique des vérifications
    show_verification_history()

def show_verification_result(result: VerificationResult):
    """Affiche le résultat de vérification"""
    
    if result.is_valid:
        st.success(f"✅ Référence valide (confiance : {result.confidence:.0%})")
        
        if result.reference:
            # Afficher les détails
            ref = result.reference
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Juridiction :** {ref.juridiction}")
                st.write(f"**Date :** {ref.date.strftime('%d/%m/%Y')}")
                st.write(f"**Numéro :** {ref.numero}")
            
            with col2:
                st.write(f"**Source vérifiée :** {SOURCE_CONFIGS[result.source_verified]['name']}")
                if ref.url:
                    st.write(f"**Lien :** [Voir la décision]({ref.url})")
            
            if ref.titre:
                st.write(f"**Titre :** {ref.titre}")
            
            if ref.resume:
                st.info(ref.resume)
            
            # Proposer de sauvegarder
            if st.button("📌 Sauvegarder cette décision"):
                save_to_database(ref)
    
    else:
        st.error(f"❌ Référence non trouvée ou invalide")
        
        if result.message:
            st.write(result.message)
        
        # Suggestions
        if result.suggestions:
            st.write("**Suggestions :**")
            for suggestion in result.suggestions[:3]:
                st.write(f"• {suggestion.get_citation()}")

def show_verification_history():
    """Affiche l'historique des vérifications"""
    
    history = st.session_state.get('verification_history', [])
    
    if history:
        with st.expander("📜 Historique des vérifications", expanded=False):
            for entry in reversed(history[-10:]):  # Dernières 10
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(entry['reference'])
                
                with col2:
                    if entry['valid']:
                        st.success("✅ Valide")
                    else:
                        st.error("❌ Invalide")
                
                with col3:
                    st.caption(entry['date'].strftime('%d/%m %H:%M'))

def show_local_database_tab():
    """Onglet base de données locale"""
    
    st.markdown("#### 📚 Base de jurisprudence locale")
    
    # Statistiques
    local_db = st.session_state.get('jurisprudence_database', {})
    favorites = st.session_state.get('jurisprudence_favorites', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Décisions enregistrées", len(local_db))
    
    with col2:
        st.metric("Favoris", len(favorites))
    
    with col3:
        if local_db:
            juridictions = set(ref.juridiction for ref in local_db.values())
            st.metric("Juridictions", len(juridictions))
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Ajouter manuellement"):
            st.session_state.show_add_jurisprudence = True
    
    with col2:
        if st.button("📥 Importer CSV/JSON"):
            st.session_state.show_import_jurisprudence = True
    
    with col3:
        if st.button("📤 Exporter la base"):
            export_jurisprudence_database()
    
    # Interface d'ajout manuel
    if st.session_state.get('show_add_jurisprudence'):
        show_add_jurisprudence_form()
    
    # Interface d'import
    if st.session_state.get('show_import_jurisprudence'):
        show_import_jurisprudence_interface()
    
    # Liste des décisions
    show_local_jurisprudence_list(local_db, favorites)

def show_add_jurisprudence_form():
    """Formulaire d'ajout manuel de jurisprudence"""
    
    with st.form("add_jurisprudence_form"):
        st.markdown("##### ➕ Ajouter une décision")
        
        col1, col2 = st.columns(2)
        
        with col1:
            juridiction = st.selectbox(
                "Juridiction *",
                options=get_all_juridictions(),
                key="add_juris_juridiction"
            )
            
            numero = st.text_input(
                "Numéro *",
                placeholder="Ex: 19-21.524",
                key="add_juris_numero"
            )
            
            date = st.date_input(
                "Date *",
                key="add_juris_date"
            )
            
            formation = st.text_input(
                "Formation",
                placeholder="Ex: Première chambre civile",
                key="add_juris_formation"
            )
        
        with col2:
            titre = st.text_input(
                "Titre",
                placeholder="Ex: Responsabilité contractuelle",
                key="add_juris_titre"
            )
            
            solution = st.selectbox(
                "Solution",
                ["", "Cassation", "Rejet", "Irrecevabilité", "Non-lieu"],
                key="add_juris_solution"
            )
            
            portee = st.selectbox(
                "Portée",
                ["", "Principe", "Espèce", "Revirement"],
                key="add_juris_portee"
            )
            
            importance = st.slider(
                "Importance",
                min_value=1,
                max_value=10,
                value=5,
                key="add_juris_importance"
            )
        
        # Résumé
        resume = st.text_area(
            "Résumé",
            placeholder="Résumé de la décision...",
            height=100,
            key="add_juris_resume"
        )
        
        # Articles et mots-clés
        col1, col2 = st.columns(2)
        
        with col1:
            articles = st.text_input(
                "Articles visés (séparés par des virgules)",
                placeholder="Ex: L.1142-1, L.1142-2",
                key="add_juris_articles"
            )
        
        with col2:
            mots_cles = st.text_input(
                "Mots-clés (séparés par des virgules)",
                placeholder="Ex: responsabilité, préjudice, causalité",
                key="add_juris_mots_cles"
            )
        
        # URL
        url = st.text_input(
            "URL source",
            placeholder="https://...",
            key="add_juris_url"
        )
        
        # Boutons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Enregistrer", type="primary"):
                # Créer la référence
                new_ref = JurisprudenceReference(
                    numero=numero,
                    date=datetime.combine(date, datetime.min.time()),
                    juridiction=juridiction,
                    formation=formation,
                    titre=titre,
                    resume=resume,
                    url=url,
                    source=SourceJurisprudence.MANUAL,
                    mots_cles=[kw.strip() for kw in mots_cles.split(',') if kw.strip()],
                    articles_vises=[art.strip() for art in articles.split(',') if art.strip()],
                    importance=importance,
                    solution=solution,
                    portee=portee
                )
                
                # Sauvegarder
                save_to_database(new_ref)
                st.success("✅ Décision ajoutée à la base")
                st.session_state.show_add_jurisprudence = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Annuler"):
                st.session_state.show_add_jurisprudence = False
                st.rerun()

def save_to_database(ref: JurisprudenceReference):
    """Sauvegarde une référence dans la base locale"""
    
    if 'jurisprudence_database' not in st.session_state:
        st.session_state.jurisprudence_database = {}
    
    ref_id = f"{ref.numero}_{ref.date.strftime('%Y%m%d')}"
    st.session_state.jurisprudence_database[ref_id] = ref

def show_local_jurisprudence_list(database: Dict[str, JurisprudenceReference], favorites: Dict[str, JurisprudenceReference]):
    """Affiche la liste des décisions locales"""
    
    if not database:
        st.info("Aucune décision dans la base locale")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_juridiction = st.selectbox(
            "Filtrer par juridiction",
            ["Toutes"] + list(set(ref.juridiction for ref in database.values())),
            key="filter_local_juridiction"
        )
    
    with col2:
        filter_importance = st.slider(
            "Importance min",
            min_value=1,
            max_value=10,
            value=1,
            key="filter_local_importance"
        )
    
    with col3:
        show_favorites_only = st.checkbox(
            "Favoris uniquement",
            key="show_favorites_only"
        )
    
    # Appliquer les filtres
    filtered_refs = database.values()
    
    if filter_juridiction != "Toutes":
        filtered_refs = [ref for ref in filtered_refs if ref.juridiction == filter_juridiction]
    
    filtered_refs = [ref for ref in filtered_refs if ref.importance >= filter_importance]
    
    if show_favorites_only:
        filtered_refs = [ref for ref in filtered_refs if f"{ref.numero}_{ref.date.strftime('%Y%m%d')}" in favorites]
    
    # Afficher
    st.write(f"**{len(filtered_refs)} décision(s)**")
    
    for ref in sorted(filtered_refs, key=lambda x: x.date, reverse=True):
        ref_id = f"{ref.numero}_{ref.date.strftime('%Y%m%d')}"
        is_favorite = ref_id in favorites
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{ref.get_citation()}**")
                if ref.titre:
                    st.caption(ref.titre)
            
            with col2:
                importance_color = "🟢" if ref.importance >= 8 else "🟡" if ref.importance >= 5 else "🔴"
                st.write(f"{importance_color} {ref.importance}/10")
            
            with col3:
                if st.button("📝", key=f"edit_local_{ref_id}"):
                    st.session_state.editing_jurisprudence = ref_id
            
            with col4:
                if is_favorite:
                    if st.button("⭐", key=f"unfav_local_{ref_id}"):
                        del st.session_state.jurisprudence_favorites[ref_id]
                        st.rerun()
                else:
                    if st.button("☆", key=f"fav_local_{ref_id}"):
                        st.session_state.jurisprudence_favorites[ref_id] = ref
                        st.rerun()
        
        st.divider()

def export_jurisprudence_database():
    """Exporte la base de jurisprudence"""
    
    database = st.session_state.get('jurisprudence_database', {})
    
    if not database:
        st.warning("Aucune décision à exporter")
        return
    
    # Préparer les données
    export_data = []
    
    for ref_id, ref in database.items():
        export_data.append({
            'numero': ref.numero,
            'date': ref.date.strftime('%Y-%m-%d'),
            'juridiction': ref.juridiction,
            'formation': ref.formation,
            'titre': ref.titre,
            'resume': ref.resume,
            'url': ref.url,
            'source': ref.source.value,
            'mots_cles': ', '.join(ref.mots_cles),
            'articles_vises': ', '.join(ref.articles_vises),
            'importance': ref.importance,
            'solution': ref.solution,
            'portee': ref.portee
        })
    
    # Export JSON
    import json
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Télécharger JSON",
        json_str,
        f"jurisprudence_export_{datetime.now().strftime('%Y%m%d')}.json",
        "application/json",
        key="download_juris_json"
    )
    
    # Export CSV si pandas disponible
    try:
        import pandas as pd
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            "💾 Télécharger CSV",
            csv,
            f"jurisprudence_export_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            key="download_juris_csv"
        )
    except ImportError:
        pass

def show_statistics_tab():
    """Onglet statistiques"""
    
    st.markdown("#### 📊 Statistiques jurisprudentielles")
    
    database = st.session_state.get('jurisprudence_database', {})
    
    if not database:
        st.info("Aucune donnée pour les statistiques")
        return
    
    # Conversion en données pour analyse
    refs = list(database.values())
    
    # Statistiques générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total décisions", len(refs))
    
    with col2:
        avg_importance = sum(ref.importance for ref in refs) / len(refs)
        st.metric("Importance moyenne", f"{avg_importance:.1f}/10")
    
    with col3:
        principe_count = sum(1 for ref in refs if ref.portee == "Principe")
        st.metric("Décisions de principe", principe_count)
    
    with col4:
        recent_count = sum(1 for ref in refs if (datetime.now() - ref.date).days < 365)
        st.metric("Décisions < 1 an", recent_count)
    
    # Graphiques si plotly disponible
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Répartition par juridiction
        juridiction_counts = {}
        for ref in refs:
            juridiction_counts[ref.juridiction] = juridiction_counts.get(ref.juridiction, 0) + 1
        
        fig1 = go.Figure([go.Bar(
            x=list(juridiction_counts.keys()),
            y=list(juridiction_counts.values()),
            text=list(juridiction_counts.values()),
            textposition='auto'
        )])
        
        fig1.update_layout(
            title="Répartition par juridiction",
            xaxis_title="Juridiction",
            yaxis_title="Nombre de décisions",
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Évolution temporelle
        years = [ref.date.year for ref in refs]
        year_counts = Counter(years)
        
        fig2 = go.Figure([go.Scatter(
            x=sorted(year_counts.keys()),
            y=[year_counts[year] for year in sorted(year_counts.keys())],
            mode='lines+markers',
            name='Décisions'
        )])
        
        fig2.update_layout(
            title="Évolution temporelle",
            xaxis_title="Année",
            yaxis_title="Nombre de décisions",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Nuage de mots-clés
        all_keywords = []
        for ref in refs:
            all_keywords.extend(ref.mots_cles)
        
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(20)
        
        st.markdown("##### 🏷️ Mots-clés les plus fréquents")
        
        cols = st.columns(4)
        for i, (keyword, count) in enumerate(top_keywords):
            with cols[i % 4]:
                st.metric(keyword, count)
        
    except ImportError:
        st.info("Installez plotly pour voir les graphiques")

def show_configuration_tab():
    """Onglet configuration"""
    
    st.markdown("#### ⚙️ Configuration de la recherche jurisprudentielle")
    
    # Sources activées
    st.markdown("##### 🔌 Sources de recherche")
    
    enabled_sources = st.session_state.get('enabled_jurisprudence_sources', [SourceJurisprudence.LEGIFRANCE, SourceJurisprudence.INTERNAL])
    
    for source in SourceJurisprudence:
        config = SOURCE_CONFIGS[source]
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            is_enabled = st.checkbox(
                "",
                value=source in enabled_sources,
                key=f"enable_source_{source.value}"
            )
            
            if is_enabled and source not in enabled_sources:
                enabled_sources.append(source)
            elif not is_enabled and source in enabled_sources:
                enabled_sources.remove(source)
        
        with col2:
            st.write(f"{config['icon']} **{config['name']}**")
            st.caption(config['url'])
        
        with col3:
            if config['api_available']:
                st.success("API ✅")
            else:
                st.warning("Web 🌐")
    
    st.session_state.enabled_jurisprudence_sources = enabled_sources
    
    # Préférences de recherche
    st.markdown("##### 🎯 Préférences de recherche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_importance = st.slider(
            "Importance minimale par défaut",
            min_value=1,
            max_value=10,
            value=st.session_state.get('default_juris_importance', 5),
            key="config_default_importance"
        )
        st.session_state.default_juris_importance = default_importance
        
        auto_verify = st.checkbox(
            "Vérification automatique des références",
            value=st.session_state.get('auto_verify_juris', True),
            key="config_auto_verify"
        )
        st.session_state.auto_verify_juris = auto_verify
    
    with col2:
        max_results = st.number_input(
            "Nombre max de résultats",
            min_value=10,
            max_value=500,
            value=st.session_state.get('max_juris_results', 100),
            step=10,
            key="config_max_results"
        )
        st.session_state.max_juris_results = max_results
        
        highlight_search = st.checkbox(
            "Surligner les termes recherchés",
            value=st.session_state.get('highlight_juris_search', True),
            key="config_highlight"
        )
        st.session_state.highlight_juris_search = highlight_search
    
    # API Keys (si nécessaire)
    st.markdown("##### 🔑 Clés API")
    
    st.info("""
    Certaines sources nécessitent des clés API pour un accès complet.
    Configurez-les dans les variables d'environnement ou les secrets Streamlit.
    """)
    
    # Test de connexion
    if st.button("🔌 Tester les connexions"):
        test_jurisprudence_sources()

def test_jurisprudence_sources():
    """Teste la connexion aux sources de jurisprudence"""
    
    with st.spinner("Test en cours..."):
        results = {}
        
        for source in st.session_state.get('enabled_jurisprudence_sources', []):
            try:
                # Test basique de recherche
                test_criteria = {
                    'query': 'test',
                    'juridictions': [],
                    'sources': [source],
                    'articles': [],
                    'date_range': None,
                    'min_importance': 1
                }
                
                # Timeout court pour le test
                test_results = search_jurisprudence(test_criteria)
                results[source] = True
                
            except Exception as e:
                results[source] = False
        
        # Afficher les résultats
        for source, success in results.items():
            config = SOURCE_CONFIGS[source]
            
            if success:
                st.success(f"✅ {config['name']} - Connexion OK")
            else:
                st.error(f"❌ {config['name']} - Connexion échouée")

# Fonctions utilitaires pour intégration avec d'autres modules

def get_jurisprudence_for_document(document_type: str, keywords: List[str], limit: int = 5) -> List[JurisprudenceReference]:
    """Récupère la jurisprudence pertinente pour un type de document"""
    
    # Critères de recherche adaptés au type
    search_criteria = {
        'query': ' '.join(keywords),
        'juridictions': [],
        'sources': st.session_state.get('enabled_jurisprudence_sources', [SourceJurisprudence.LEGIFRANCE]),
        'articles': [],
        'date_range': None,
        'min_importance': 7  # Jurisprudence importante pour les documents
    }
    
    # Adapter selon le type
    if document_type == 'conclusions':
        search_criteria['min_importance'] = 8
    elif document_type == 'plainte':
        search_criteria['min_importance'] = 6
    
    # Rechercher
    results = search_jurisprudence(search_criteria)
    
    return results[:limit]

def format_jurisprudence_citation(ref: JurisprudenceReference) -> str:
    """Formate une citation de jurisprudence pour insertion dans un document"""
    
    citation = ref.get_citation()
    
    if ref.url:
        # Format avec lien
        return f"[{citation}]({ref.url})"
    else:
        # Format simple
        return citation

def verify_and_update_citations(content: str) -> Tuple[str, List[VerificationResult]]:
    """Vérifie et met à jour les citations de jurisprudence dans un texte"""
    
    verifier = JurisprudenceVerifier()
    verification_results = []
    
    # Pattern pour détecter les citations
    citation_pattern = r'((?:Cass\.|CA|CE|CC)\s+[^,]+,\s+\d{1,2}\s+\w+\s+\d{4}(?:,\s+n°\s*[\d\-\.]+)?)'
    
    citations = re.findall(citation_pattern, content)
    
    for citation in citations:
        # Vérifier
        result = verifier.verify_reference(citation)
        verification_results.append(result)
        
        # Mettre à jour si trouvé
        if result.is_valid and result.reference:
            # Remplacer par la citation formatée
            formatted = format_jurisprudence_citation(result.reference)
            content = content.replace(citation, formatted)
    
    return content, verification_results

# Pour l'intégration dans le module recherche
def show_jurisprudence_interface(query: str = "", analysis: dict = None):
    """Interface principale appelée par le module recherche"""
    
    if query and analysis:
        process_jurisprudence_request(query, analysis)
    else:
        # Afficher l'interface par défaut
        initial_criteria = extract_jurisprudence_criteria(query or "", analysis or {})
        show_jurisprudence_search_interface(initial_criteria)