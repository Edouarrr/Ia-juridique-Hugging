# modules/analyse_ia.py
"""Page d'analyse par IA avec vérification des jurisprudences"""

import streamlit as st
import asyncio

from config.app_config import InfractionAffaires, ANALYSIS_PROMPTS_AFFAIRES, LLMProvider
from managers.multi_llm_manager import MultiLLMManager
from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
from models.dataclasses import AnalyseJuridique, InfractionIdentifiee

def show_page():
    """Affiche la page d'analyse IA"""
    st.header("🤖 Analyse IA des documents")
    
    # Vérifier qu'il y a des pièces sélectionnées
    if not st.session_state.pieces_selectionnees:
        st.warning("⚠️ Veuillez d'abord sélectionner des pièces dans l'onglet 'Sélection de pièces'")
        return
    
    # Configuration de l'analyse
    show_analysis_config()
    
    # Type d'analyse
    analyse_types = show_analysis_types()
    
    # Bouton d'analyse
    if st.button("🚀 Lancer l'analyse", type="primary", key="lancer_analyse"):
        run_analysis(analyse_types)

def show_analysis_config():
    """Affiche la configuration de l'analyse"""
    st.markdown("### ⚙️ Configuration de l'analyse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type d'infraction
        infractions_list = [inf.value for inf in InfractionAffaires]
        
        st.session_state.infraction = st.text_input(
            "Type d'infraction",
            placeholder="Ex: Abus de biens sociaux, corruption, fraude fiscale...",
            key="infraction_input",
            help="Saisissez librement l'infraction"
        )
        
        if not st.session_state.infraction:
            st.info("💡 Suggestions : " + ", ".join(infractions_list[:5]) + "...")
        
        st.session_state.client_nom = st.text_input(
            "Nom du client",
            placeholder="Personne physique ou morale",
            key="client_nom_analyse"
        )
        
        st.session_state.client_type = st.radio(
            "Type de client",
            ["Personne physique", "Personne morale"],
            key="client_type_analyse"
        )
    
    with col2:
        # Providers IA à utiliser
        llm_manager = MultiLLMManager()
        available_providers = list(llm_manager.clients.keys())
        
        if available_providers:
            st.session_state.selected_providers = st.multiselect(
                "IA à utiliser",
                [p.value for p in available_providers],
                default=[available_providers[0].value] if available_providers else [],
                key="selected_providers_analyse"
            )
            
            st.session_state.fusion_mode = st.radio(
                "Mode de fusion des réponses",
                ["Synthèse IA", "Concatenation simple"],
                key="fusion_mode_analyse"
            )
        else:
            st.error("❌ Aucune IA configurée")

def show_analysis_types():
    """Affiche et sélectionne les types d'analyse"""
    st.markdown("### 📄 Pièces à analyser")
    
    st.session_state.pieces_a_analyser = []
    for piece_id, piece in st.session_state.pieces_selectionnees.items():
        if st.checkbox(
            f"{piece.titre} ({piece.categorie})",
            value=True,
            key=f"analyse_piece_{piece_id}"
        ):
            st.session_state.pieces_a_analyser.append(piece_id)
    
    st.markdown("### 🎯 Type d'analyse")
    
    return st.multiselect(
        "Sélectionner les analyses à effectuer",
        list(ANALYSIS_PROMPTS_AFFAIRES.keys()),
        default=list(ANALYSIS_PROMPTS_AFFAIRES.keys())[:2],
        key="analyse_types_select"
    )

def run_analysis(analyse_types):
    """Lance l'analyse avec les paramètres sélectionnés"""
    if not st.session_state.infraction or not st.session_state.client_nom or not st.session_state.pieces_a_analyser:
        st.error("❌ Veuillez remplir tous les champs")
        return
    
    # Préparer le contenu
    contenu_pieces = prepare_content_for_analysis()
    
    # Construire le prompt
    prompt_base = f"""Tu es un avocat expert en droit pénal des affaires.
Client: {st.session_state.client_nom} ({st.session_state.client_type})
Infraction reprochée: {st.session_state.infraction}
Documents analysés:
{chr(10).join(contenu_pieces)}
Analyses demandées:
"""
    
    # Lancer les analyses
    with st.spinner("🔄 Analyse en cours..."):
        resultats = {}
        llm_manager = MultiLLMManager()
        
        for analyse_type in analyse_types:
            prompts = ANALYSIS_PROMPTS_AFFAIRES[analyse_type]
            
            # Construire le prompt complet
            prompt_complet = prompt_base + f"\n{analyse_type}:\n"
            for p in prompts:
                prompt_complet += f"- {p}\n"
            
            # Convertir les providers
            providers_enum = [
                p for p in LLMProvider 
                if p.value in st.session_state.selected_providers
            ]
            
            # Interroger les IA
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            responses = loop.run_until_complete(
                llm_manager.query_multiple_llms(
                    providers_enum,
                    prompt_complet
                )
            )
            
            # Fusionner les réponses
            if st.session_state.fusion_mode == "Synthèse IA" and len(responses) > 1:
                fusion = llm_manager.fusion_responses(responses)
            else:
                fusion = "\n\n".join([
                    f"### {r['provider']}\n{r['response']}"
                    for r in responses
                    if r['success']
                ])
            
            resultats[analyse_type] = fusion
        
        # Afficher les résultats
        show_analysis_results(resultats)
        
        # Créer un objet AnalyseJuridique pour l'export
        if resultats:
            analyse = create_analyse_from_results(resultats)
            st.session_state.last_analysis = analyse
            
            # Bouton d'export rapide
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("💾 Exporter cette analyse", key="export_rapide", type="primary"):
                    st.switch_page("pages/import_export.py")

def prepare_content_for_analysis():
    """Prépare le contenu des pièces pour l'analyse"""
    contenu_pieces = []
    for piece_id in st.session_state.pieces_a_analyser:
        if piece_id in st.session_state.azure_documents:
            doc = st.session_state.azure_documents[piece_id]
            piece = st.session_state.pieces_selectionnees[piece_id]
            
            contenu_pieces.append(f"""
=== {doc.title} ({piece.categorie}) ===
Pertinence: {piece.pertinence}/10
Notes: {piece.notes}
Contenu:
{doc.content[:3000]}...
""")
    return contenu_pieces

def show_analysis_results(resultats):
    """Affiche les résultats de l'analyse"""
    st.markdown("## 📊 Résultats de l'analyse")
    
    # Stockage des résultats
    st.session_state.resultats_analyse = resultats
    
    for analyse_type, resultat in resultats.items():
        with st.expander(analyse_type, expanded=True):
            st.markdown(resultat)
            
            # Options d'export
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "💾 Télécharger",
                    resultat,
                    f"analyse_{analyse_type.replace(' ', '_')}.txt",
                    "text/plain",
                    key=f"download_analyse_{analyse_type}"
                )
            
            with col2:
                if st.button("📋 Copier", key=f"copy_analyse_{analyse_type}"):
                    st.write("Contenu copié!")
    
    # NOUVEAU : Vérification des jurisprudences
    if st.checkbox("🔍 Vérifier les jurisprudences citées", key="verify_juris_check"):
        verify_jurisprudences_in_analysis(resultats)

def verify_jurisprudences_in_analysis(resultats: dict):
    """Vérifie les jurisprudences citées dans l'analyse"""
    st.markdown("### 🔍 Vérification des jurisprudences citées")
    
    # Extraire tout le texte des résultats
    full_text = "\n".join(resultats.values())
    
    # Créer le vérificateur
    verifier = JurisprudenceVerifier()
    
    # Afficher l'interface de vérification
    verification_results = display_jurisprudence_verification(full_text, verifier)
    
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

def create_analyse_from_results(resultats: dict) -> AnalyseJuridique:
    """Convertit les résultats en objet AnalyseJuridique"""
    # Parser les résultats pour extraire les informations
    
    analyse = AnalyseJuridique(
        description_cas=st.session_state.get('resume_faits', ''),
        qualification_juridique=resultats.get("🎯 Analyse infractions économiques", ""),
        niveau_risque="À déterminer",
        model_used=st.session_state.selected_providers[0] if st.session_state.selected_providers else "Non spécifié"
    )
    
    # Extraire les infractions si possible
    if st.session_state.get('infraction'):
        analyse.infractions_identifiees.append(
            InfractionIdentifiee(
                nom=st.session_state.infraction,
                qualification="Délit",  # À déterminer selon l'analyse
                articles=[],  # À extraire de l'analyse
                elements_constitutifs=[],  # À extraire
                sanctions={},  # À extraire
                prescription="6 ans"  # Par défaut pour les délits
            )
        )
    
    # Ajouter les recommandations depuis l'analyse
    for key, value in resultats.items():
        if "défense" in key.lower():
            # Extraire les recommandations
            lines = value.split('\n')
            for line in lines:
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    analyse.recommandations.append(line.strip('- •'))
    
    # Extraire d'autres informations si présentes
    if "💰 Enjeux financiers" in resultats:
        analyse.regime_responsabilite = "Voir analyse des enjeux financiers"
    
    if "🏢 Responsabilité personne morale" in resultats:
        if "personne morale" not in analyse.regime_responsabilite:
            analyse.regime_responsabilite += " - Responsabilité personne morale possible"
    
    # Ajouter les jurisprudences vérifiées si disponibles
    if 'jurisprudence_verification' in st.session_state:
        for verif_result in st.session_state.jurisprudence_verification:
            if verif_result.status == 'verified':
                ref = verif_result.reference
                analyse.jurisprudences_citees.append(ref.to_citation())
    
    return analyse
          