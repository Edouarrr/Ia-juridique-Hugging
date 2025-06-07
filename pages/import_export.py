# pages/import_export.py
"""Page d'import/export de documents"""

import streamlit as st
from datetime import datetime

from managers.document_manager import DocumentManager, display_import_interface, display_export_interface
from models.dataclasses import AnalyseJuridique, InfractionIdentifiee

def show_page():
    """Affiche la page d'import/export"""
    st.header("📥 Import/Export de documents")
    
    # Initialiser le gestionnaire de documents
    if 'doc_manager' not in st.session_state:
        st.session_state.doc_manager = DocumentManager()
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["📤 Import", "💾 Export", "📊 Historique"])
    
    with tab1:
        show_import_tab()
    
    with tab2:
        show_export_tab()
    
    with tab3:
        show_history_tab()

def show_import_tab():
    """Onglet d'import"""
    display_import_interface()
    
    # Si du contenu a été importé, proposer de l'analyser
    if 'imported_content' in st.session_state and st.session_state.imported_content:
        st.markdown("### 🔍 Analyse du contenu importé")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"📄 Contenu importé : {len(st.session_state.imported_content)} caractères")
        
        with col2:
            if st.button("🤖 Analyser", type="primary"):
                # Créer un document temporaire
                from models.dataclasses import Document
                temp_doc = Document(
                    id=f"import_{datetime.now().timestamp()}",
                    title="Document importé",
                    content=st.session_state.imported_content,
                    source="import"
                )
                
                # Ajouter aux documents
                st.session_state.azure_documents[temp_doc.id] = temp_doc
                st.success("✅ Document ajouté à la sélection. Allez dans 'Analyse IA' pour l'analyser.")

def show_export_tab():
    """Onglet d'export"""
    # Vérifier s'il y a une analyse à exporter
    if 'last_analysis' in st.session_state:
        display_export_interface(st.session_state.last_analysis)
    else:
        # Créer une analyse de démonstration
        st.info("💡 Effectuez d'abord une analyse dans l'onglet 'Analyse IA' pour pouvoir l'exporter.")
        
        if st.checkbox("Voir un exemple d'export"):
            # Créer une analyse exemple
            exemple_analyse = create_exemple_analyse()
            display_export_interface(exemple_analyse)

def show_history_tab():
    """Onglet historique"""
    st.markdown("### 📊 Historique des imports/exports")
    
    doc_manager = st.session_state.doc_manager
    stats = doc_manager.get_import_stats()
    
    if stats['count'] == 0:
        st.info("Aucun document importé pour le moment")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Documents importés", stats['count'])
        
        with col2:
            total_size_mb = stats['total_size'] / (1024 * 1024)
            st.metric("Taille totale", f"{total_size_mb:.2f} MB")
        
        with col3:
            st.metric("Dernier import", stats['latest'])
        
        # Types de fichiers
        if 'types' in stats and stats['types']:
            st.markdown("#### Types de fichiers")
            for ext, count in stats['types'].items():
                st.write(f"- {ext}: {count} fichiers")
        
        # Liste des documents
        if doc_manager.imported_documents:
            st.markdown("#### Documents importés")
            for doc in doc_manager.imported_documents[-10:]:  # Derniers 10
                with st.expander(f"📄 {doc['filename']}"):
                    st.write(f"Date: {doc['import_date'].strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"Taille: {doc['size'] / 1024:.2f} KB")
                    st.text_area(
                        "Aperçu",
                        value=doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'],
                        height=200,
                        disabled=True
                    )

def create_exemple_analyse() -> AnalyseJuridique:
    """Crée une analyse exemple pour la démonstration"""
    return AnalyseJuridique(
        description_cas="Exemple de cas d'abus de biens sociaux",
        qualification_juridique="Abus de biens sociaux caractérisé",
        infractions_identifiees=[
            InfractionIdentifiee(
                nom="Abus de biens sociaux",
                qualification="Délit",
                articles=["L241-3", "L242-6 Code de commerce"],
                elements_constitutifs=[
                    "Usage des biens contraire à l'intérêt social",
                    "Mauvaise foi caractérisée",
                    "Intérêt personnel direct ou indirect"
                ],
                sanctions={
                    "Emprisonnement": "5 ans",
                    "Amende": "375 000 euros"
                },
                prescription="6 ans"
            )
        ],
        regime_responsabilite="Responsabilité pénale du dirigeant",
        sanctions_encourues={
            "Peines principales": "5 ans d'emprisonnement et 375 000 € d'amende",
            "Peines complémentaires": "Interdiction de gérer, confiscation"
        },
        jurisprudences_citees=[
            "Cass. crim., 27 oct. 2021, n° 20-81.570",
            "Cass. crim., 15 sept. 2021, n° 20-83.098"
        ],
        recommandations=[
            "Régulariser la situation comptable",
            "Préparer une défense sur la bonne foi",
            "Documenter l'intérêt social des opérations"
        ],
        niveau_risque="Élevé",
        model_used="GPT-4"
    )