# pages/selection_pieces.py
"""Page de sélection et organisation des pièces"""

import streamlit as st
from datetime import datetime

from models.dataclasses import PieceSelectionnee
from utils.helpers import GestionnairePiecesSelectionnees

def show_page():
    """Affiche la page de sélection des pièces"""
    st.header("📁 Sélection et organisation des pièces")
    
    # Gestionnaire de pièces
    gestionnaire = GestionnairePiecesSelectionnees()
    
    # Charger les pièces depuis la session
    if 'pieces_selectionnees' in st.session_state:
        gestionnaire.pieces = st.session_state.pieces_selectionnees
    
    # Vue d'ensemble
    show_overview(gestionnaire)
    
    # Deux colonnes : documents disponibles et pièces sélectionnées
    col_docs, col_pieces = st.columns([1, 1])
    
    with col_docs:
        show_available_documents(gestionnaire)
    
    with col_pieces:
        show_selected_pieces(gestionnaire)

def show_overview(gestionnaire):
    """Affiche la vue d'ensemble"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents disponibles", len(st.session_state.azure_documents))
    
    with col2:
        st.metric("Pièces sélectionnées", len(gestionnaire.pieces))
    
    with col3:
        if st.button("📋 Générer bordereau", key="generer_bordereau"):
            bordereau = gestionnaire.generer_bordereau()
            st.text_area("Bordereau", bordereau, height=400, key="bordereau_display")
            
            st.download_button(
                "💾 Télécharger le bordereau",
                bordereau,
                "bordereau_pieces.txt",
                "text/plain",
                key="download_bordereau"
            )

def show_available_documents(gestionnaire):
    """Affiche les documents disponibles"""
    st.markdown("### 📄 Documents disponibles")
    
    # Filtre
    filtre = st.text_input(
        "Filtrer les documents",
        placeholder="Rechercher par nom...",
        key="filtre_docs_pieces"
    )
    
    # Liste des documents
    for doc_id, doc in st.session_state.azure_documents.items():
        if filtre.lower() in doc.title.lower():
            with st.container():
                st.markdown('<div class="document-card">', unsafe_allow_html=True)
                
                st.markdown(f"**{doc.title}**")
                
                if doc.metadata.get('last_modified'):
                    st.caption(f"Modifié: {doc.metadata['last_modified']}")
                
                # Si déjà sélectionné
                if doc_id in gestionnaire.pieces:
                    st.success("✅ Déjà sélectionné")
                    
                    if st.button(f"❌ Retirer", key=f"remove_{doc_id}"):
                        gestionnaire.retirer_piece(doc_id)
                        st.rerun()
                else:
                    # Sélection avec catégorie
                    col_cat, col_btn = st.columns([3, 1])
                    
                    with col_cat:
                        categorie = st.selectbox(
                            "Catégorie",
                            gestionnaire.categories,
                            key=f"cat_select_{doc_id}"
                        )
                    
                    with col_btn:
                        if st.button("➕", key=f"add_piece_{doc_id}"):
                            gestionnaire.ajouter_piece(doc, categorie)
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

def show_selected_pieces(gestionnaire):
    """Affiche les pièces sélectionnées"""
    st.markdown("### ✅ Pièces sélectionnées")
    
    pieces_par_cat = gestionnaire.get_pieces_par_categorie()
    
    for categorie, pieces in pieces_par_cat.items():
        if pieces:
            with st.expander(f"{categorie} ({len(pieces)})", expanded=True):
                for piece in sorted(pieces, key=lambda x: x.pertinence, reverse=True):
                    show_piece_detail(piece, gestionnaire)

def show_piece_detail(piece, gestionnaire):
    """Affiche le détail d'une pièce"""
    st.markdown('<div class="piece-selectionnee">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**{piece.titre}**")
        
        # Notes
        notes = st.text_input(
            "Notes",
            value=piece.notes,
            key=f"notes_{piece.document_id}",
            placeholder="Ajouter des notes..."
        )
        
        # Pertinence
        pertinence = st.slider(
            "Pertinence",
            1, 10,
            value=piece.pertinence,
            key=f"pertinence_{piece.document_id}"
        )
        
        # Mettre à jour la pièce
        if notes != piece.notes or pertinence != piece.pertinence:
            piece.notes = notes
            piece.pertinence = pertinence
            st.session_state.pieces_selectionnees[piece.document_id] = piece
    
    with col2:
        if st.button("🗑️", key=f"delete_piece_{piece.document_id}"):
            gestionnaire.retirer_piece(piece.document_id)
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)