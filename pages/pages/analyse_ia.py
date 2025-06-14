# pages/analyse_ia.py
"""Page d'analyse par IA"""

import asyncio

import streamlit as st

from config.app_config import (ANALYSIS_PROMPTS_AFFAIRES, InfractionAffaires,
                               LLMProvider)
from managers.multi_llm_manager import MultiLLMManager


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