"""Module de rédaction de documents juridiques"""

import streamlit as st
from datetime import datetime
from managers.multi_llm_manager import MultiLLMManager
from .recherche_export import create_formatted_docx

def process_redaction_request(query: str, analysis: dict):
    """Traite une demande de rédaction générale"""
    doc_type = analysis.get('document_type', 'general')
    
    if doc_type == 'plainte':
        parties = analysis.get('parties', [])
        generate_plainte(query, parties)
    elif doc_type == 'conclusions':
        generate_conclusions(query, analysis)
    else:
        st.warning("Type de document non reconnu")

def generate_plainte(query: str, parties: list):
    """Génère une plainte avec les IA disponibles"""
    
    st.markdown("### 📝 Génération de la plainte en cours...")
    
    # Vérifier si on a des IA disponibles
    try:
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            st.error("❌ Aucune IA n'est configurée. Veuillez configurer au moins une clé API dans les secrets.")
            st.info("Ajoutez une de ces clés dans les secrets Hugging Face : ANTHROPIC_API_KEY, OPENAI_API_KEY, ou GOOGLE_API_KEY")
            return
        
        # Construire le prompt pour la plainte
        prompt = f"""Tu es un avocat expert en droit pénal des affaires. 
        
Rédige une plainte pénale contre les sociétés suivantes : {', '.join(parties)}

Contexte : {query}

La plainte doit inclure :

1. EN-TÊTE
   - Identification du plaignant
   - Identification des mis en cause : {', '.join(parties)}
   - Objet de la plainte

2. EXPOSÉ DES FAITS
   - Chronologie détaillée
   - Description précise des manquements
   - Préjudices subis

3. QUALIFICATION JURIDIQUE
   - Infractions pénales caractérisées
   - Articles du Code pénal applicables
   - Éléments constitutifs

4. DEMANDES
   - Constitution de partie civile
   - Demandes d'actes d'enquête
   - Évaluation provisoire du préjudice

5. PIÈCES JOINTES
   - Liste des pièces justificatives

Format professionnel, ton formel, style juridique."""

        # Utiliser la première IA disponible
        provider = list(llm_manager.clients.keys())[0]
        
        with st.spinner(f"Génération avec {provider.value}..."):
            response = llm_manager.query_single_llm(
                provider,
                prompt,
                "Tu es un avocat pénaliste expert en droit des affaires."
            )
            
            if response['success']:
                # Stocker le résultat
                st.session_state.redaction_result = {
                    'type': 'plainte',
                    'document': response['response'],
                    'timestamp': datetime.now(),
                    'provider': provider.value,
                    'parties': parties
                }
                
                # Afficher le résultat
                st.success("✅ Plainte générée avec succès !")
                
                # Zone de texte pour éditer
                edited_content = st.text_area(
                    "📄 Contenu de la plainte (vous pouvez éditer)",
                    value=response['response'],
                    height=600,
                    key="edit_plainte"
                )
                
                # Boutons d'action
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Export Word
                    docx_data = create_formatted_docx(edited_content, 'plainte')
                    st.download_button(
                        "📄 Télécharger Word",
                        docx_data,
                        f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                with col2:
                    # Export PDF (si disponible)
                    st.download_button(
                        "📑 Télécharger PDF",
                        edited_content.encode('utf-8'),
                        f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        "text/plain"
                    )
                
                with col3:
                    if st.button("🔄 Régénérer"):
                        st.session_state.process_query = True
                        st.rerun()
                
            else:
                st.error(f"❌ Erreur : {response.get('error', 'Erreur inconnue')}")
                
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération : {str(e)}")
        st.info("Vérifiez que les clés API sont bien configurées dans les secrets")

def generate_conclusions(query: str, analysis: dict):
    """Génère des conclusions"""
    st.info("🚧 Génération de conclusions en cours d'implémentation")
    # TODO: Implémenter