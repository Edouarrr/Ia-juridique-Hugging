# test_unified_generator.py
"""
Test simple du générateur unifié de documents
À placer dans le dossier racine de votre application Hugging Face
"""

import asyncio
from datetime import datetime

import pytest
pytest.importorskip("streamlit")
import streamlit as st

# Import du générateur unifié
from managers.unified_document_generator import (DocumentLength,
                                                 UnifiedDocumentGenerator,
                                                 UnifiedGenerationRequest)
# Import des dataclasses
from modules.dataclasses import (InfractionIdentifiee, Partie, StyleRedaction,
                                 TypeDocument)


def main():
    st.title("🧪 Test du Générateur Unifié")
    
    # Créer une instance du générateur
    generator = UnifiedDocumentGenerator()
    
    # Interface simple
    st.markdown("### Configuration rapide")
    
    # Type de document
    doc_type = st.selectbox(
        "Type de document",
        [TypeDocument.CONCLUSIONS, TypeDocument.ASSIGNATION, TypeDocument.PLAIDOIRIE]
    )
    
    # Contexte
    contexte = st.text_area(
        "Contexte de l'affaire",
        value="Litige commercial entre deux sociétés concernant un contrat de fourniture non respecté.",
        height=100
    )
    
    # Bouton de test
    if st.button("🎯 Tester la génération", type="primary"):
        
        # Créer des données de test
        parties = {
            "demandeur": [Partie(
                nom="Société TEST SA",
                type="personne_morale",
                role="demandeur",
                adresse="123 rue du Test, 75001 Paris"
            )],
            "defendeur": [Partie(
                nom="Entreprise DEMO SARL",
                type="personne_morale", 
                role="defendeur",
                adresse="456 avenue Demo, 69001 Lyon"
            )]
        }
        
        infractions = [
            InfractionIdentifiee(
                code="1147",
                libelle="Inexécution contractuelle",
                article="Article 1147 du Code civil",
                applicable=True
            )
        ]
        
        # Créer la requête
        request = UnifiedGenerationRequest(
            document_type=doc_type,
            parties=parties,
            infractions=infractions,
            contexte=contexte,
            style=StyleRedaction.PROFESSIONNEL,
            length=DocumentLength.STANDARD
        )
        
        # Générer
        with st.spinner("🔄 Génération en cours..."):
            try:
                # Appel asynchrone
                document = asyncio.run(generator.generate(request))
                
                # Afficher le résultat
                st.success("✅ Document généré avec succès!")
                
                # Métadonnées
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Type", document.type_document)
                with col2:
                    st.metric("Longueur", f"{len(document.contenu.split())} mots")
                with col3:
                    st.metric("Date", datetime.now().strftime("%d/%m/%Y"))
                
                # Contenu
                st.markdown("---")
                st.markdown(f"### {document.titre}")
                
                # Afficher avec une mise en forme basique
                with st.container():
                    st.markdown(document.contenu)
                
                # Options
                st.markdown("---")
                if st.button("💾 Sauvegarder dans la session"):
                    if 'test_documents' not in st.session_state:
                        st.session_state.test_documents = []
                    st.session_state.test_documents.append(document)
                    st.success("Document sauvegardé!")
                    
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")
                st.exception(e)  # Afficher la stack trace complète
    
    # Afficher les documents sauvegardés
    if 'test_documents' in st.session_state and st.session_state.test_documents:
        st.markdown("### 📚 Documents générés")
        for i, doc in enumerate(st.session_state.test_documents):
            with st.expander(f"{i+1}. {doc.titre}"):
                st.write(doc.contenu[:500] + "...")

if __name__ == "__main__":
    main()