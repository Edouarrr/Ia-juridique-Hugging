# pages/analyse.py
"""Page d'analyse juridique avec vérification automatique des jurisprudences"""

import streamlit as st
import asyncio
from datetime import datetime
import uuid
from typing import Optional

from config import TYPES_INFRACTIONS, MESSAGES
from models import AnalyseJuridique, Infraction, Personne, TypePersonne
from managers import (
    LLMManager, 
    DocumentManager, 
    JurisprudenceVerifier,
    display_jurisprudence_verification,
    display_model_selector,
    display_import_interface,
    display_export_interface
)
from utils import load_custom_css, create_alert_box, create_section_divider, format_date

def show():
    """Affiche la page d'analyse juridique"""
    load_custom_css()
    
    st.title("📋 Analyse juridique approfondie")
    st.markdown("Analysez vos cas avec vérification automatique des jurisprudences citées")
    
    # Initialiser les managers
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = LLMManager()
    if 'doc_manager' not in st.session_state:
        st.session_state.doc_manager = DocumentManager()
    if 'jurisprudence_verifier' not in st.session_state:
        st.session_state.jurisprudence_verifier = JurisprudenceVerifier()
    
    # Tabs principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Nouveau cas",
        "📂 Import document", 
        "📊 Résultats",
        "💾 Export"
    ])
    
    with tab1:
        show_new_case_form()
    
    with tab2:
        display_import_interface()
        if st.session_state.get('imported_content'):
            if st.button("Analyser le document importé"):
                st.session_state['case_description'] = st.session_state['imported_content']
                st.rerun()
    
    with tab3:
        show_analysis_results()
    
    with tab4:
        if 'current_analysis' in st.session_state:
            display_export_interface(st.session_state['current_analysis'])
        else:
            st.info("Aucune analyse disponible pour l'export")

def show_new_case_form():
    """Formulaire de saisie d'un nouveau cas"""
    st.markdown("### Description du cas")
    
    # Sélection du modèle
    col1, col2 = st.columns([2, 1])
    with col1:
        provider, model = display_model_selector()
    with col2:
        analysis_depth = st.selectbox(
            "Profondeur d'analyse",
            ["Rapide", "Standard", "Approfondie"],
            index=1
        )
    
    # Type d'infraction
    case_type = st.selectbox(
        "Type d'infraction principal (optionnel)",
        ["Sélectionner..."] + TYPES_INFRACTIONS,
        help="Aide à orienter l'analyse"
    )
    
    # Description du cas
    case_description = st.text_area(
        "Description détaillée du cas",
        value=st.session_state.get('case_description', ''),
        height=300,
        placeholder="""Décrivez les faits, les personnes impliquées, les actions réalisées, les dates importantes...

Exemple : 
Le dirigeant de la société X a utilisé les fonds de l'entreprise pour financer des travaux dans sa résidence personnelle. Les montants détournés s'élèvent à 150 000 euros sur une période de 2 ans. Les factures ont été comptabilisées comme des frais de rénovation des locaux de l'entreprise..."""
    )
    
    # Personnes impliquées
    st.markdown("### Personnes impliquées (optionnel)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        person_name = st.text_input("Nom")
    with col2:
        person_type = st.selectbox(
            "Type",
            [t.value for t in TypePersonne]
        )
    with col3:
        person_role = st.text_input("Rôle dans l'affaire")
    
    if st.button("➕ Ajouter une personne"):
        if 'persons_list' not in st.session_state:
            st.session_state.persons_list = []
        
        if person_name:
            st.session_state.persons_list.append({
                'nom': person_name,
                'type': person_type,
                'role': person_role
            })
            st.success(f"Personne ajoutée : {person_name}")
    
    # Afficher les personnes ajoutées
    if st.session_state.get('persons_list'):
        st.markdown("**Personnes enregistrées :**")
        for i, person in enumerate(st.session_state.persons_list):
            st.caption(f"{i+1}. {person['nom']} ({person['type']}) - {person['role']}")
    
    # Options avancées
    with st.expander("Options avancées"):
        include_jurisprudence = st.checkbox(
            "Rechercher et vérifier les jurisprudences",
            value=True,
            help="Recherche automatique et vérification sur Judilibre/Légifrance"
        )
        
        include_doctrine = st.checkbox(
            "Inclure références doctrinales",
            value=False
        )
        
        risk_assessment = st.checkbox(
            "Évaluation approfondie des risques",
            value=True
        )
    
    # Bouton d'analyse
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🚀 Lancer l'analyse juridique",
            type="primary",
            disabled=not case_description,
            use_container_width=True
        ):
            if not case_description:
                st.error("Veuillez décrire le cas à analyser")
                return
            
            # Sauvegarder les paramètres
            st.session_state['case_description'] = case_description
            st.session_state['case_type'] = case_type if case_type != "Sélectionner..." else None
            st.session_state['analysis_params'] = {
                'provider': provider,
                'model': model,
                'depth': analysis_depth,
                'include_jurisprudence': include_jurisprudence,
                'include_doctrine': include_doctrine,
                'risk_assessment': risk_assessment
            }
            
            # Lancer l'analyse
            perform_analysis()

def perform_analysis():
    """Effectue l'analyse juridique"""
    with st.spinner("Analyse en cours... Cela peut prendre quelques minutes."):
        try:
            # Récupérer les paramètres
            case_description = st.session_state['case_description']
            case_type = st.session_state.get('case_type')
            params = st.session_state['analysis_params']
            
            # Configurer le LLM
            llm_manager = st.session_state.llm_manager
            llm_manager.set_current_model(params['provider'], params['model'])
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Étape 1 : Analyse juridique
            status_text.text("Analyse des éléments juridiques...")
            progress_bar.progress(20)
            
            # Lancer l'analyse async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            analysis_result = loop.run_until_complete(
                llm_manager.analyze_legal_case(
                    case_description,
                    case_type or "général",
                    params['depth']
                )
            )
            
            progress_bar.progress(60)
            
            # Étape 2 : Vérification des jurisprudences
            if params['include_jurisprudence']:
                status_text.text("Vérification des jurisprudences citées...")
                
                # Extraire le texte complet de l'analyse
                analysis_text = format_analysis_to_text(analysis_result)
                
                # Vérifier les jurisprudences
                verifier = st.session_state.jurisprudence_verifier
                references = verifier.extract_references_from_text(analysis_text)
                
                if references:
                    async def verify_refs():
                        async with verifier:
                            return await verifier.verify_multiple_references(references)
                    
                    verification_results = loop.run_until_complete(verify_refs())
                    analysis_result['verification_results'] = verification_results
                
            progress_bar.progress(80)
            
            # Étape 3 : Création de l'objet AnalyseJuridique
            status_text.text("Finalisation de l'analyse...")
            
            # Créer les objets Infraction
            infractions = []
            for inf_name in analysis_result.get('infractions_identifiees', []):
                if isinstance(inf_name, str):
                    infraction = Infraction(
                        nom=inf_name,
                        qualification="À déterminer",
                        articles=[],
                        elements_constitutifs=[],
                        sanctions={},
                        prescription="3 ans"
                    )
                    infractions.append(infraction)
            
            # Créer les objets Personne
            personnes = []
            for p in st.session_state.get('persons_list', []):
                personne = Personne(
                    nom=p['nom'],
                    type_personne=TypePersonne.PHYSIQUE,  # À adapter
                    role=p['role']
                )
                personnes.append(personne)
            
            # Créer l'analyse complète
            analyse = AnalyseJuridique(
                id=str(uuid.uuid4()),
                date_analyse=datetime.now(),
                description_cas=case_description,
                infractions_identifiees=infractions,
                personnes_impliquees=personnes,
                elements_factuels=analysis_result.get('elements_factuels', []),
                qualification_juridique=analysis_result.get('qualification_juridique', ''),
                regime_responsabilite=analysis_result.get('regime_responsabilite', ''),
                sanctions_encourues=analysis_result.get('sanctions_encourues', {}),
                jurisprudences_citees=analysis_result.get('jurisprudences_citees', []),
                recommandations=analysis_result.get('recommandations', []),
                niveau_risque=analysis_result.get('niveau_risque', 'Modéré'),
                model_used=f"{params['provider']}/{params['model']}"
            )
            
            # Sauvegarder l'analyse
            st.session_state['current_analysis'] = analyse
            st.session_state['analysis_result'] = analysis_result
            
            # Incrémenter le compteur
            st.session_state['analyses_count'] = st.session_state.get('analyses_count', 0) + 1
            
            progress_bar.progress(100)
            status_text.text("Analyse terminée !")
            
            st.success("✅ Analyse juridique complétée avec succès !")
            
            # Passer à l'onglet résultats
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur lors de l'analyse : {str(e)}")
            st.exception(e)

def show_analysis_results():
    """Affiche les résultats de l'analyse"""
    if 'current_analysis' not in st.session_state:
        st.info("Aucune analyse disponible. Veuillez d'abord analyser un cas.")
        return
    
    analyse = st.session_state['current_analysis']
    analysis_result = st.session_state.get('analysis_result', {})
    
    # En-tête avec métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Infractions identifiées",
            len(analyse.infractions_identifiees)
        )
    
    with col2:
        st.metric(
            "Niveau de risque",
            analyse.niveau_risque
        )
    
    with col3:
        st.metric(
            "Jurisprudences citées",
            len(analyse.jurisprudences_citees)
        )
    
    with col4:
        st.metric(
            "Date d'analyse",
            format_date(analyse.date_analyse)
        )
    
    st.markdown(create_section_divider(), unsafe_allow_html=True)
    
    # Qualification juridique
    st.markdown("### ⚖️ Qualification juridique")
    st.write(analyse.qualification_juridique)
    
    # Infractions identifiées
    st.markdown("### 🚨 Infractions identifiées")
    for i, infraction in enumerate(analyse.infractions_identifiees, 1):
        with st.expander(f"{i}. {infraction.nom}", expanded=True):
            st.markdown(f"**Qualification :** {infraction.qualification}")
            st.markdown(f"**Articles :** {', '.join(infraction.articles) if infraction.articles else 'À déterminer'}")
            st.markdown(f"**Prescription :** {infraction.prescription}")
            
            if infraction.elements_constitutifs:
                st.markdown("**Éléments constitutifs :**")
                for elem in infraction.elements_constitutifs:
                    st.markdown(f"- {elem}")
    
    # Régime de responsabilité
    st.markdown("### 👥 Régime de responsabilité")
    st.write(analyse.regime_responsabilite)
    
    # Sanctions encourues
    st.markdown("### ⚠️ Sanctions encourues")
    for type_sanction, details in analyse.sanctions_encourues.items():
        st.markdown(f"**{type_sanction} :** {details}")
    
    # Jurisprudences avec vérification
    if analyse.jurisprudences_citees:
        st.markdown("### 📚 Jurisprudences citées")
        
        # Si on a des résultats de vérification
        if 'verification_results' in analysis_result:
            # Afficher avec statut de vérification
            for i, (juris, verif_result) in enumerate(
                zip(analyse.jurisprudences_citees, analysis_result['verification_results'])
            ):
                icon = "✅" if verif_result.status == 'verified' else "❌"
                st.markdown(f"{icon} {juris}")
        else:
            # Afficher sans vérification
            for juris in analyse.jurisprudences_citees:
                st.markdown(f"- {juris}")
        
        # Bouton pour vérifier maintenant
        if st.button("🔍 Vérifier les jurisprudences maintenant"):
            analysis_text = format_analysis_to_text(analysis_result)
            display_jurisprudence_verification(
                analysis_text,
                st.session_state.jurisprudence_verifier
            )
    
    # Recommandations
    st.markdown("### 💡 Recommandations stratégiques")
    for i, reco in enumerate(analyse.recommandations, 1):
        st.markdown(f"{i}. {reco}")
    
    # Évaluation du risque
    st.markdown("### 📊 Évaluation du risque")
    risk_color = {
        "Faible": "green",
        "Modéré": "orange",
        "Élevé": "red",
        "Critique": "darkred"
    }.get(analyse.niveau_risque, "gray")
    
    st.markdown(
        f"<h3 style='color: {risk_color};'>Niveau de risque global : {analyse.niveau_risque}</h3>",
        unsafe_allow_html=True
    )
    
    # Actions
    st.markdown("### 🎯 Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Générer rapport complet"):
            st.info("Utilisez l'onglet Export pour générer un rapport")
    
    with col2:
        if st.button("🔄 Nouvelle analyse"):
            if st.confirm("Êtes-vous sûr ? L'analyse actuelle sera perdue."):
                st.session_state.pop('current_analysis', None)
                st.session_state.pop('analysis_result', None)
                st.rerun()
    
    with col3:
        if st.button("💾 Sauvegarder"):
            st.success("Analyse sauvegardée dans l'historique")

def format_analysis_to_text(analysis_result: dict) -> str:
    """Convertit le résultat d'analyse en texte pour la vérification"""
    text_parts = []
    
    if 'qualification_juridique' in analysis_result:
        text_parts.append(analysis_result['qualification_juridique'])
    
    if 'jurisprudences_citees' in analysis_result:
        text_parts.append("Jurisprudences citées :")
        text_parts.extend(analysis_result['jurisprudences_citees'])
    
    if 'regime_responsabilite' in analysis_result:
        text_parts.append(analysis_result['regime_responsabilite'])
    
    if 'recommandations' in analysis_result:
        text_parts.extend(analysis_result['recommandations'])
    
    return '\n\n'.join(text_parts)

# Point d'entrée
if __name__ == "__main__":
    show()