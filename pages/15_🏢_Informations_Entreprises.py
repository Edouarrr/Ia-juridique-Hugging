# pages/15_🏢_Informations_Entreprises.py
"""Page Streamlit pour la recherche d'informations d'entreprises"""

import streamlit as st
import asyncio
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

from services.company_info_service import get_company_info_service
from models.dataclasses import (
    InformationEntreprise, SourceEntreprise, Partie, 
    TypePartie, CasJuridique, PhaseProcedure
)

st.set_page_config(
    page_title="Informations Entreprises",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Recherche d'Informations d'Entreprises")
st.markdown("""
Recherchez automatiquement les informations légales des entreprises (capital social, RCS, siège social, etc.)
depuis Pappers et Societe.com pour enrichir vos documents juridiques.
""")

# Initialiser le service
company_service = get_company_info_service()

# Vérifier la configuration
has_pappers = bool(st.secrets.get("PAPPERS_API_KEY", ""))

if not has_pappers:
    st.warning("""
    ⚠️ **Configuration requise**
    
    Pour utiliser toutes les fonctionnalités, configurez votre clé API Pappers dans les secrets Streamlit.
    Sans clé API, seule la recherche sur Societe.com (limitée) sera disponible.
    
    Ajoutez dans `.streamlit/secrets.toml`:
    ```
    PAPPERS_API_KEY = "votre_clé_api"
    ```
    """)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Recherche simple", 
    "📋 Recherche multiple", 
    "🔄 Enrichir une affaire",
    "📊 Entreprises sauvegardées"
])

with tab1:
    st.header("Recherche d'une entreprise")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        company_name = st.text_input(
            "Nom de l'entreprise",
            placeholder="Ex: VINCI, INTERCONSTRUCTION, etc.",
            help="Entrez le nom complet ou partiel de l'entreprise"
        )
    
    with col2:
        source_pref = st.selectbox(
            "Source préférée",
            [SourceEntreprise.PAPPERS.value, SourceEntreprise.SOCIETE_COM.value],
            index=0 if has_pappers else 1
        )
    
    if st.button("🔍 Rechercher", type="primary", disabled=not company_name):
        with st.spinner(f"Recherche en cours sur {source_pref}..."):
            try:
                info = asyncio.run(
                    company_service.get_company_info(
                        company_name,
                        SourceEntreprise(source_pref)
                    )
                )
                
                if info:
                    st.success(f"✅ Entreprise trouvée sur {info.source.value}")
                    
                    # Afficher les informations
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Informations générales")
                        st.write(f"**Dénomination :** {info.denomination}")
                        if info.forme_juridique:
                            st.write(f"**Forme juridique :** {info.forme_juridique}")
                        if info.capital_social:
                            st.write(f"**Capital social :** {info.format_capital()}")
                        if info.date_creation:
                            st.write(f"**Date de création :** {info.date_creation.strftime('%d/%m/%Y')}")
                        if info.effectif:
                            st.write(f"**Effectif :** {info.effectif}")
                    
                    with col2:
                        st.subheader("Immatriculation")
                        if info.siren:
                            st.write(f"**SIREN :** {info.siren}")
                        if info.siret:
                            st.write(f"**SIRET :** {info.siret}")
                        if info.get_immatriculation_complete():
                            st.write(f"**RCS :** {info.get_immatriculation_complete()}")
                        if info.code_ape:
                            st.write(f"**Code APE :** {info.code_ape}")
                    
                    # Adresse
                    st.subheader("Siège social")
                    if info.siege_social:
                        st.write(info.siege_social)
                    elif info.code_postal and info.ville:
                        st.write(f"{info.code_postal} {info.ville}")
                    
                    # Dirigeants
                    if info.representants_legaux:
                        st.subheader("Représentants légaux")
                        for rep in info.representants_legaux:
                            st.write(f"- {rep['nom']}")
                            if rep.get('qualite'):
                                st.write(f"  *{rep['qualite']}*")
                    
                    # Formatage juridique
                    with st.expander("📄 Désignation juridique complète"):
                        designation = company_service.format_for_legal_document(info)
                        st.code(designation, language=None)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Télécharger",
                                designation,
                                file_name=f"{info.denomination.replace(' ', '_')}_designation.txt",
                                mime="text/plain"
                            )
                        with col2:
                            if st.button("📋 Copier"):
                                st.write("Copié! (fonctionnalité à implémenter)")
                    
                    # Sauvegarder
                    if 'saved_companies' not in st.session_state:
                        st.session_state.saved_companies = {}
                    
                    if st.button("💾 Sauvegarder cette entreprise"):
                        st.session_state.saved_companies[info.denomination] = info
                        st.success(f"Entreprise '{info.denomination}' sauvegardée")
                
                else:
                    st.error(f"Aucune information trouvée pour '{company_name}'")
                    
                    # Suggestions
                    st.info("""
                    **Suggestions :**
                    - Vérifiez l'orthographe du nom
                    - Essayez avec le nom commercial ou la raison sociale
                    - Utilisez le numéro SIREN si vous le connaissez
                    """)
                    
            except Exception as e:
                st.error(f"Erreur lors de la recherche : {e}")

with tab2:
    st.header("Recherche multiple d'entreprises")
    
    companies_input = st.text_area(
        "Liste des entreprises (une par ligne)",
        height=200,
        placeholder="VINCI\nINTERCONSTRUCTION\nSOGEPROM\netc.",
        help="Entrez un nom d'entreprise par ligne"
    )
    
    if st.button("🔍 Rechercher toutes", disabled=not companies_input):
        company_names = [name.strip() for name in companies_input.split('\n') if name.strip()]
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, name in enumerate(company_names):
            status_text.text(f"Recherche {i+1}/{len(company_names)}: {name}")
            progress_bar.progress((i + 1) / len(company_names))
            
            try:
                info = asyncio.run(
                    company_service.get_company_info(name)
                )
                
                if info:
                    results.append({
                        'Recherche': name,
                        'Trouvé': '✅',
                        'Dénomination': info.denomination,
                        'Forme juridique': info.forme_juridique,
                        'Capital': info.format_capital() if info.capital_social else 'N/A',
                        'RCS': info.get_immatriculation_complete() or 'N/A',
                        'Source': info.source.value,
                        'Info': info
                    })
                else:
                    results.append({
                        'Recherche': name,
                        'Trouvé': '❌',
                        'Dénomination': '-',
                        'Forme juridique': '-',
                        'Capital': '-',
                        'RCS': '-',
                        'Source': '-',
                        'Info': None
                    })
            except Exception as e:
                results.append({
                    'Recherche': name,
                    'Trouvé': '⚠️',
                    'Dénomination': f'Erreur: {str(e)}',
                    'Forme juridique': '-',
                    'Capital': '-',
                    'RCS': '-',
                    'Source': '-',
                    'Info': None
                })
        
        progress_bar.empty()
        status_text.empty()
        
        # Afficher les résultats
        if results:
            df = pd.DataFrame(results)
            df_display = df.drop('Info', axis=1)
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Statistiques
            found = len([r for r in results if r['Trouvé'] == '✅'])
            st.info(f"**Résultats :** {found}/{len(results)} entreprises trouvées")
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export CSV
                csv = df_display.to_csv(index=False)
                st.download_button(
                    "📥 Exporter en CSV",
                    csv,
                    file_name=f"recherche_entreprises_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Sauvegarder toutes
                if st.button("💾 Sauvegarder toutes les trouvées"):
                    if 'saved_companies' not in st.session_state:
                        st.session_state.saved_companies = {}
                    
                    saved_count = 0
                    for result in results:
                        if result['Info']:
                            st.session_state.saved_companies[result['Info'].denomination] = result['Info']
                            saved_count += 1
                    
                    st.success(f"{saved_count} entreprises sauvegardées")
            
            with col3:
                # Générer les désignations
                if st.button("📄 Générer toutes les désignations"):
                    designations = []
                    for result in results:
                        if result['Info']:
                            designation = company_service.format_for_legal_document(result['Info'])
                            designations.append(f"# {result['Info'].denomination}\n{designation}\n")
                    
                    if designations:
                        all_designations = "\n".join(designations)
                        st.download_button(
                            "📥 Télécharger les désignations",
                            all_designations,
                            file_name=f"designations_juridiques_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )

with tab3:
    st.header("Enrichir les parties d'une affaire")
    
    # Sélection de l'affaire
    if 'cases' in st.session_state and st.session_state.cases:
        case_names = list(st.session_state.cases.keys())
        selected_case_name = st.selectbox("Sélectionnez une affaire", case_names)
        
        if selected_case_name:
            case = st.session_state.cases[selected_case_name]
            
            st.subheader(f"Affaire : {case.titre}")
            
            # Afficher les parties actuelles
            all_parties = []
            for party_type, parties in case.parties.items():
                for partie in parties:
                    all_parties.append({
                        'Type': party_type,
                        'Nom': partie.nom,
                        'Type personne': partie.type_personne,
                        'Infos complètes': '✅' if partie.info_entreprise else '❌',
                        'Partie': partie
                    })
            
            if all_parties:
                df_parties = pd.DataFrame(all_parties)
                
                st.dataframe(
                    df_parties[['Type', 'Nom', 'Type personne', 'Infos complètes']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Bouton d'enrichissement
                entreprises_a_enrichir = [
                    p for p in all_parties 
                    if p['Partie'].type_personne == 'morale' and not p['Partie'].info_entreprise
                ]
                
                if entreprises_a_enrichir:
                    if st.button(f"🔄 Enrichir {len(entreprises_a_enrichir)} entreprise(s)", type="primary"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        enriched_count = 0
                        
                        for i, partie_data in enumerate(entreprises_a_enrichir):
                            partie = partie_data['Partie']
                            status_text.text(f"Recherche {i+1}/{len(entreprises_a_enrichir)}: {partie.nom}")
                            progress_bar.progress((i + 1) / len(entreprises_a_enrichir))
                            
                            try:
                                info = asyncio.run(
                                    company_service.get_company_info(partie.nom)
                                )
                                
                                if info:
                                    partie.update_from_entreprise_info(info)
                                    enriched_count += 1
                                    st.success(f"✅ {partie.nom} enrichie")
                                else:
                                    st.warning(f"⚠️ Aucune information trouvée pour {partie.nom}")
                                    
                            except Exception as e:
                                st.error(f"❌ Erreur pour {partie.nom}: {e}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        if enriched_count > 0:
                            st.success(f"🎉 {enriched_count} entreprise(s) enrichie(s)")
                            st.info("Les informations ont été ajoutées à l'affaire")
                            
                            # Proposer de régénérer les documents
                            if st.button("📄 Régénérer les documents avec les nouvelles informations"):
                                st.write("Fonctionnalité à implémenter")
                else:
                    st.info("✅ Toutes les entreprises ont déjà leurs informations complètes")
            else:
                st.warning("Aucune partie dans cette affaire")
    else:
        st.info("Aucune affaire disponible. Créez d'abord une affaire depuis la recherche universelle.")

with tab4:
    st.header("Entreprises sauvegardées")
    
    if 'saved_companies' in st.session_state and st.session_state.saved_companies:
        companies_data = []
        
        for name, info in st.session_state.saved_companies.items():
            companies_data.append({
                'Dénomination': info.denomination,
                'Forme juridique': info.forme_juridique or '-',
                'Capital': info.format_capital() if info.capital_social else '-',
                'RCS': info.get_immatriculation_complete() or '-',
                'Siège': info.ville or '-',
                'Source': info.source.value,
                'Date récup.': info.date_recuperation.strftime('%d/%m/%Y %H:%M')
            })
        
        df = pd.DataFrame(companies_data)
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Rechercher", placeholder="Nom, ville...")
        
        with col2:
            forme_filter = st.selectbox(
                "Forme juridique",
                ['Toutes'] + sorted(df['Forme juridique'].unique())
            )
        
        with col3:
            source_filter = st.selectbox(
                "Source",
                ['Toutes'] + sorted(df['Source'].unique())
            )
        
        # Appliquer les filtres
        df_filtered = df.copy()
        
        if search_term:
            mask = df_filtered.apply(
                lambda row: search_term.lower() in str(row).lower(), 
                axis=1
            )
            df_filtered = df_filtered[mask]
        
        if forme_filter != 'Toutes':
            df_filtered = df_filtered[df_filtered['Forme juridique'] == forme_filter]
        
        if source_filter != 'Toutes':
            df_filtered = df_filtered[df_filtered['Source'] == source_filter]
        
        # Afficher
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"**{len(df_filtered)} entreprise(s)** sur {len(df)} au total")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                "📥 Exporter la sélection",
                csv,
                file_name=f"entreprises_sauvegardees_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Actualiser
            if st.button("🔄 Actualiser toutes"):
                st.write("Actualisation en cours... (fonctionnalité à implémenter)")
        
        with col3:
            # Nettoyer
            if st.button("🗑️ Vider la liste", type="secondary"):
                st.session_state.saved_companies = {}
                st.success("Liste vidée")
                st.rerun()
    
    else:
        st.info("Aucune entreprise sauvegardée pour le moment")
        st.markdown("""
        **Comment sauvegarder des entreprises ?**
        1. Recherchez une entreprise dans l'onglet "Recherche simple"
        2. Cliquez sur "Sauvegarder cette entreprise"
        3. Ou faites une recherche multiple et sauvegardez toutes les trouvées
        """)

# Aide dans la sidebar
with st.sidebar:
    st.header("💡 Aide")
    
    st.markdown("""
    ### Sources de données
    
    **Pappers** (recommandé)
    - Base officielle complète
    - Données à jour
    - Nécessite une clé API
    - [Obtenir une clé](https://www.pappers.fr/api)
    
    **Societe.com**
    - Accès gratuit limité
    - Scraping web
    - Peut être plus lent
    
    ### Utilisation
    
    1. **Recherche simple**
       - Pour une entreprise spécifique
       - Affichage détaillé
       - Export de la désignation
    
    2. **Recherche multiple**
       - Traitement par lot
       - Export CSV
       - Idéal pour enrichir plusieurs parties
    
    3. **Enrichir une affaire**
       - Met à jour automatiquement les parties
       - Conserve la traçabilité
       - Prêt pour la rédaction
    
    ### Format de désignation
    
    La désignation juridique générée inclut :
    - Dénomination sociale
    - Forme juridique
    - Capital social
    - Immatriculation RCS
    - Siège social
    - Représentant légal
    """)
    
    if has_pappers:
        st.success("✅ API Pappers configurée")
    else:
        st.warning("⚠️ API Pappers non configurée")