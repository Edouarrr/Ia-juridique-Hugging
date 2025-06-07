# pages/recherche.py
"""Page de recherche de jurisprudence avec vérification multi-sources"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict

from config.app_config import TYPES_INFRACTIONS, LEGAL_APIS
from models.jurisprudence_models import JurisprudenceSearch, JurisprudenceReference, TypeJuridiction, SourceJurisprudence
from managers.legal_search import LegalSearchManager
from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
from utils.styles import load_custom_css, create_alert_box, create_badge, create_progress_bar

def show():
    """Affiche la page de recherche de jurisprudence"""
    load_custom_css()
    
    st.title("🔍 Recherche de jurisprudence")
    st.markdown("Recherchez et vérifiez des jurisprudences sur Judilibre, Légifrance et via l'IA")
    
    # Initialiser les managers
    if 'legal_search_manager' not in st.session_state:
        llm_manager = st.session_state.get('llm_manager')
        st.session_state.legal_search_manager = LegalSearchManager(llm_manager)
    
    if 'jurisprudence_verifier' not in st.session_state:
        st.session_state.jurisprudence_verifier = JurisprudenceVerifier()
    
    # Vérifier la configuration des APIs
    check_api_configuration()
    
    # Tabs de recherche
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔎 Recherche simple",
        "🎯 Recherche avancée",
        "✅ Vérification",
        "📊 Résultats"
    ])
    
    with tab1:
        show_simple_search()
    
    with tab2:
        show_advanced_search()
    
    with tab3:
        show_verification_tab()
    
    with tab4:
        show_results_tab()

def check_api_configuration():
    """Vérifie la configuration des APIs juridiques"""
    col1, col2 = st.columns(2)
    
    with col1:
        if LEGAL_APIS['judilibre']['api_key'] == 'votre_cle_api_judilibre':
            st.warning("⚠️ API Judilibre non configurée")
        else:
            st.success("✅ API Judilibre configurée")
    
    with col2:
        if LEGAL_APIS['legifrance']['client_id'] == 'votre_client_id_legifrance':
            st.warning("⚠️ API Légifrance non configurée")
        else:
            st.success("✅ API Légifrance configurée")
    
    if not all([
        LEGAL_APIS['judilibre']['api_key'] != 'votre_cle_api_judilibre',
        LEGAL_APIS['legifrance']['client_id'] != 'votre_client_id_legifrance'
    ]):
        st.info("💡 Configurez vos APIs dans la page Configuration pour activer toutes les sources")

def show_simple_search():
    """Interface de recherche simple"""
    st.markdown("### Recherche rapide")
    
    # Champ de recherche principal
    search_query = st.text_input(
        "Entrez vos mots-clés ou une référence de jurisprudence",
        placeholder="Ex: abus biens sociaux dirigeant, Cass. crim. 22-81.234",
        help="Recherche dans toutes les sources disponibles"
    )
    
    # Options rapides
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_infractions = st.multiselect(
            "Infractions",
            TYPES_INFRACTIONS[:10],
            max_selections=3
        )
    
    with col2:
        date_range = st.select_slider(
            "Période",
            options=["1 an", "3 ans", "5 ans", "10 ans", "Toutes"],
            value="5 ans"
        )
    
    with col3:
        sources = st.multiselect(
            "Sources",
            ["Judilibre", "Légifrance", "IA"],
            default=["Judilibre", "Légifrance"]
        )
    
    # Bouton de recherche
    if st.button("🔎 Rechercher", type="primary", use_container_width=True):
        if not search_query and not selected_infractions:
            st.error("Veuillez saisir des mots-clés ou sélectionner au moins une infraction")
            return
        
        # Préparer les paramètres
        keywords = search_query.split() if search_query else []
        
        # Calculer la date de début selon la période
        date_debut = None
        if date_range != "Toutes":
            years = int(date_range.split()[0])
            date_debut = datetime.now() - timedelta(days=years*365)
        
        # Créer la recherche
        search_params = JurisprudenceSearch(
            keywords=keywords,
            infractions=selected_infractions,
            date_debut=date_debut,
            sources=[SourceJurisprudence[s.upper()] for s in sources if s != "IA"],
            max_results=30
        )
        
        # Lancer la recherche
        perform_search(search_params, include_ai="IA" in sources)

def show_advanced_search():
    """Interface de recherche avancée"""
    st.markdown("### Recherche avancée")
    
    # Critères de recherche en colonnes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Mots-clés et termes")
        keywords = st.text_area(
            "Mots-clés (un par ligne)",
            height=100,
            help="Entrez un mot-clé par ligne"
        )
        
        must_include = st.text_input(
            "Doit contenir",
            help="Termes obligatoires séparés par des virgules"
        )
        
        exclude = st.text_input(
            "Exclure",
            help="Termes à exclure séparés par des virgules"
        )
    
    with col2:
        st.markdown("#### Juridictions et dates")
        juridictions = st.multiselect(
            "Juridictions",
            ["Cass. crim.", "Cass. civ.", "Cass. com.", "Cass. soc.", "CE", "CA", "Cons. const."],
            help="Sélectionnez les juridictions"
        )
        
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            date_debut = st.date_input(
                "Date début",
                value=None,
                help="Laisser vide pour pas de limite"
            )
        with col_date2:
            date_fin = st.date_input(
                "Date fin",
                value=None,
                help="Laisser vide pour aujourd'hui"
            )
    
    # Infractions et articles
    st.markdown("#### Domaine juridique")
    
    infractions = st.multiselect(
        "Types d'infractions",
        TYPES_INFRACTIONS,
        help="Sélectionnez les infractions concernées"
    )
    
    articles = st.text_input(
        "Articles de loi",
        placeholder="Ex: L242-6, 432-11, 313-1",
        help="Articles du Code pénal, Code de commerce, etc."
    )
    
    # Options de tri et filtrage
    with st.expander("Options de tri et filtrage"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sort_by = st.selectbox(
                "Trier par",
                ["Pertinence", "Date (récent)", "Date (ancien)", "Juridiction"]
            )
        
        with col2:
            max_results = st.number_input(
                "Nombre max de résultats",
                min_value=10,
                max_value=200,
                value=50,
                step=10
            )
        
        with col3:
            only_verified = st.checkbox(
                "Uniquement jurisprudences vérifiées",
                value=False
            )
    
    # Sources à interroger
    st.markdown("#### Sources de recherche")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        use_judilibre = st.checkbox("Judilibre", value=True)
    with col2:
        use_legifrance = st.checkbox("Légifrance", value=True)
    with col3:
        use_ai = st.checkbox("Suggestions IA", value=False)
    
    # Bouton de recherche
    if st.button("🔎 Lancer la recherche avancée", type="primary", use_container_width=True):
        # Préparer les paramètres
        keywords_list = [k.strip() for k in keywords.split('\n') if k.strip()]
        if must_include:
            keywords_list.extend(must_include.split(','))
        
        articles_list = [a.strip() for a in articles.split(',') if a.strip()] if articles else []
        
        sources = []
        if use_judilibre:
            sources.append(SourceJurisprudence.JUDILIBRE)
        if use_legifrance:
            sources.append(SourceJurisprudence.LEGIFRANCE)
        
        # Mapper le tri
        sort_map = {
            "Pertinence": "pertinence",
            "Date (récent)": "date_desc",
            "Date (ancien)": "date_asc",
            "Juridiction": "juridiction"
        }
        
        search_params = JurisprudenceSearch(
            keywords=keywords_list,
            juridictions=[],  # À implémenter
            date_debut=date_debut,
            date_fin=date_fin,
            infractions=infractions,
            articles=articles_list,
            sources=sources,
            max_results=max_results,
            sort_by=sort_map.get(sort_by, "pertinence")
        )
        
        # Lancer la recherche
        perform_search(search_params, include_ai=use_ai)

def show_verification_tab():
    """Onglet de vérification de jurisprudences"""
    st.markdown("### Vérification de jurisprudences")
    st.markdown("Collez un texte contenant des références de jurisprudence pour les vérifier")
    
    # Zone de texte pour vérification
    text_to_verify = st.text_area(
        "Texte à vérifier",
        height=200,
        placeholder="""Exemple :
La Cour de cassation a jugé dans l'arrêt Cass. crim., 27 octobre 2021, n° 20-86.531 que...
Voir également CE, 15 mars 2023, n° 456789 sur la question de...
"""
    )
    
    # Options de vérification
    col1, col2 = st.columns(2)
    with col1:
        verify_judilibre = st.checkbox("Vérifier sur Judilibre", value=True)
    with col2:
        verify_legifrance = st.checkbox("Vérifier sur Légifrance", value=True)
    
    # Bouton de vérification
    if st.button("✅ Vérifier les références", type="primary"):
        if not text_to_verify:
            st.error("Veuillez coller un texte contenant des références")
            return
        
        # Lancer la vérification
        verifier = st.session_state.jurisprudence_verifier
        display_jurisprudence_verification(text_to_verify, verifier)
        
        # Incrémenter le compteur
        st.session_state['verifications_count'] = st.session_state.get('verifications_count', 0) + 1

def show_results_tab():
    """Affiche les résultats de recherche"""
    if 'search_results' not in st.session_state:
        st.info("Aucun résultat de recherche. Effectuez d'abord une recherche.")
        return
    
    results = st.session_state['search_results']
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    total_results = sum(len(r) for r in results.values())
    
    with col1:
        st.metric("Total résultats", total_results)
    with col2:
        st.metric("Judilibre", len(results.get('judilibre', [])))
    with col3:
        st.metric("Légifrance", len(results.get('legifrance', [])))
    with col4:
        st.metric("IA", len(results.get('ai', [])))
    
    # Filtres de résultats
    st.markdown("### Filtres")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_source = st.selectbox(
            "Source",
            ["Toutes"] + list(results.keys())
        )
    
    with col2:
        filter_verified = st.selectbox(
            "Statut",
            ["Tous", "Vérifiés", "Non vérifiés"]
        )
    
    with col3:
        results_per_page = st.selectbox(
            "Résultats par page",
            [10, 20, 50, 100],
            index=1
        )
    
    # Affichage des résultats
    st.markdown("### Résultats de recherche")
    
    # Fusionner et filtrer les résultats
    all_results = []
    for source, docs in results.items():
        if filter_source == "Toutes" or filter_source == source:
            for doc in docs:
                doc.source_type = source
                all_results.append(doc)
    
    # Filtrer par statut de vérification
    if filter_verified == "Vérifiés":
        all_results = [d for d in all_results if hasattr(d, 'reference') and d.reference.verified]
    elif filter_verified == "Non vérifiés":
        all_results = [d for d in all_results if hasattr(d, 'reference') and not d.reference.verified]
    
    # Pagination
    total_pages = (len(all_results) + results_per_page - 1) // results_per_page
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=max(1, total_pages),
        value=1
    )
    
    start_idx = (page - 1) * results_per_page
    end_idx = start_idx + results_per_page
    page_results = all_results[start_idx:end_idx]
    
    # Afficher les résultats
    for i, doc in enumerate(page_results, start=start_idx + 1):
        display_search_result(doc, i)
    
    # Navigation
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"Page {page} sur {total_pages}")

def perform_search(search_params: JurisprudenceSearch, include_ai: bool = False):
    """Lance la recherche avec les paramètres donnés"""
    with st.spinner("Recherche en cours sur les bases juridiques..."):
        try:
            search_manager = st.session_state.legal_search_manager
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Recherche async
            async def search():
                async with search_manager:
                    return await search_manager.search_all_sources(
                        search_params,
                        include_ai=include_ai
                    )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            status_text.text("Interrogation des bases de données...")
            progress_bar.progress(30)
            
            results = loop.run_until_complete(search())
            
            progress_bar.progress(70)
            status_text.text("Traitement des résultats...")
            
            # Fusionner et dédupliquer
            all_docs = search_manager.merge_and_deduplicate_results(results)
            
            # Sauvegarder les résultats
            st.session_state['search_results'] = results
            st.session_state['all_search_results'] = all_docs
            st.session_state['last_search_params'] = search_params
            
            progress_bar.progress(100)
            
            # Afficher le résumé
            total = sum(len(r) for r in results.values())
            st.success(f"✅ {total} résultats trouvés !")
            
            # Résumé par source
            for source, docs in results.items():
                if docs:
                    st.info(f"{source.capitalize()} : {len(docs)} résultats")
            
            status_text.empty()
            progress_bar.empty()
            
        except Exception as e:
            st.error(f"Erreur lors de la recherche : {str(e)}")
            st.exception(e)

def display_search_result(doc, index: int):
    """Affiche un résultat de recherche"""
    with st.container():
        # En-tête avec numéro et source
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Titre avec statut de vérification
            if hasattr(doc, 'reference') and doc.reference:
                if doc.reference.verified:
                    st.markdown(f"**{index}. ✅ {doc.titre}**")
                else:
                    st.markdown(f"**{index}. ❓ {doc.titre}**")
            else:
                st.markdown(f"**{index}. {doc.titre}**")
        
        with col2:
            # Badge de source
            source_colors = {
                'judilibre': 'primary',
                'legifrance': 'success',
                'ai': 'warning'
            }
            color = source_colors.get(doc.source_type, 'secondary')
            st.markdown(
                create_badge(doc.source_type.upper(), color),
                unsafe_allow_html=True
            )
        
        # Métadonnées
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if hasattr(doc, 'reference') and doc.reference:
                st.caption(f"📅 {doc.reference.date}")
        
        with col2:
            st.caption(f"📊 Pertinence: {doc.pertinence*100:.0f}%")
        
        with col3:
            if doc.url:
                st.caption(f"[🔗 Voir la décision]({doc.url})")
        
        # Contenu
        with st.expander("Voir le détail"):
            if doc.contenu:
                # Limiter la longueur affichée
                content = doc.contenu[:500] + "..." if len(doc.contenu) > 500 else doc.contenu
                st.write(content)
            
            if hasattr(doc, 'reference') and doc.reference and doc.reference.sommaire:
                st.markdown("**Sommaire :**")
                st.write(doc.reference.sommaire)
            
            # Mots-clés
            if doc.mots_cles:
                st.markdown("**Mots-clés :** " + ", ".join(doc.mots_cles))
        
        st.markdown("---")

# Point d'entrée
if __name__ == "__main__":
    show()