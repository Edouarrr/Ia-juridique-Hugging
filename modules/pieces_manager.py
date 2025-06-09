"""
Module de gestion des pièces de procédure
"""

import streamlit as st
from datetime import datetime
import json
from typing import Dict, List, Optional, Any
import uuid
import hashlib
import mimetypes
from pathlib import Path

# Import des modèles avec gestion d'erreur
try:
    from models.dataclasses import PieceProcedure, Document, DocumentType
except ImportError:
    # Définitions de secours si l'import échoue
    from dataclasses import dataclass, field
    from typing import Dict, List, Optional, Any
    from datetime import datetime
    from enum import Enum
    
    class DocumentType(Enum):
        PIECE_PROCEDURE = "piece_procedure"
        AUTRE = "autre"
    
    @dataclass
    class PieceProcedure:
        id: str
        nom: str
        type_piece: str
        numero_ordre: int
        description: Optional[str] = None
        date_ajout: datetime = field(default_factory=datetime.now)
        chemin_fichier: Optional[str] = None
        taille: Optional[int] = None
        hash_fichier: Optional[str] = None
        metadata: Dict[str, Any] = field(default_factory=dict)

class PiecesManager:
    """Gestionnaire des pièces de procédure"""
    
    # Types de pièces prédéfinis
    TYPES_PIECES = [
        "Assignation",
        "Conclusions",
        "Pièce justificative",
        "Expertise",
        "Procès-verbal",
        "Jugement",
        "Arrêt",
        "Ordonnance",
        "Requête",
        "Mémoire",
        "Attestation",
        "Contrat",
        "Facture",
        "Correspondance",
        "Photo",
        "Vidéo",
        "Audio",
        "Plan",
        "Autre"
    ]
    
    def __init__(self):
        """Initialise le gestionnaire"""
        if 'pieces' not in st.session_state:
            st.session_state.pieces = {}
        if 'pieces_par_dossier' not in st.session_state:
            st.session_state.pieces_par_dossier = {}
        if 'pieces_metadata' not in st.session_state:
            st.session_state.pieces_metadata = {}
    
    def add_piece(self, piece: PieceProcedure, dossier_id: Optional[str] = None) -> str:
        """Ajoute une pièce"""
        st.session_state.pieces[piece.id] = piece
        
        # Associer au dossier si spécifié
        if dossier_id:
            if dossier_id not in st.session_state.pieces_par_dossier:
                st.session_state.pieces_par_dossier[dossier_id] = []
            st.session_state.pieces_par_dossier[dossier_id].append(piece.id)
        
        return piece.id
    
    def get_piece(self, piece_id: str) -> Optional[PieceProcedure]:
        """Récupère une pièce par son ID"""
        return st.session_state.pieces.get(piece_id)
    
    def get_pieces_dossier(self, dossier_id: str) -> List[PieceProcedure]:
        """Récupère toutes les pièces d'un dossier"""
        piece_ids = st.session_state.pieces_par_dossier.get(dossier_id, [])
        return [self.get_piece(pid) for pid in piece_ids if self.get_piece(pid)]
    
    def update_piece(self, piece_id: str, **kwargs):
        """Met à jour une pièce"""
        if piece_id in st.session_state.pieces:
            piece = st.session_state.pieces[piece_id]
            for key, value in kwargs.items():
                if hasattr(piece, key):
                    setattr(piece, key, value)
    
    def delete_piece(self, piece_id: str):
        """Supprime une pièce"""
        if piece_id in st.session_state.pieces:
            # Retirer des dossiers
            for dossier_id, pieces in st.session_state.pieces_par_dossier.items():
                if piece_id in pieces:
                    pieces.remove(piece_id)
            
            # Supprimer la pièce
            del st.session_state.pieces[piece_id]
    
    def reorder_pieces(self, dossier_id: str, new_order: List[str]):
        """Réorganise l'ordre des pièces d'un dossier"""
        if dossier_id in st.session_state.pieces_par_dossier:
            # Mettre à jour l'ordre
            st.session_state.pieces_par_dossier[dossier_id] = new_order
            
            # Mettre à jour les numéros d'ordre
            for i, piece_id in enumerate(new_order):
                if piece_id in st.session_state.pieces:
                    st.session_state.pieces[piece_id].numero_ordre = i + 1
    
    def search_pieces(self, query: str, filters: Dict[str, Any] = None) -> List[PieceProcedure]:
        """Recherche des pièces"""
        results = []
        query_lower = query.lower()
        
        for piece in st.session_state.pieces.values():
            score = 0
            
            # Recherche dans le nom
            if query_lower in piece.nom.lower():
                score += 3
            
            # Recherche dans la description
            if piece.description and query_lower in piece.description.lower():
                score += 2
            
            # Recherche dans le type
            if query_lower in piece.type_piece.lower():
                score += 1
            
            # Appliquer les filtres
            if filters:
                if filters.get('type_piece') and piece.type_piece != filters['type_piece']:
                    continue
                if filters.get('date_debut') and piece.date_ajout < filters['date_debut']:
                    continue
                if filters.get('date_fin') and piece.date_ajout > filters['date_fin']:
                    continue
                if filters.get('dossier_id'):
                    pieces_dossier = st.session_state.pieces_par_dossier.get(filters['dossier_id'], [])
                    if piece.id not in pieces_dossier:
                        continue
            
            if score > 0:
                results.append((score, piece))
        
        # Trier par score décroissant
        results.sort(key=lambda x: x[0], reverse=True)
        return [piece for _, piece in results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les pièces"""
        total = len(st.session_state.pieces)
        
        if total == 0:
            return {
                'total': 0,
                'par_type': {},
                'taille_totale': 0,
                'pieces_recentes': []
            }
        
        par_type = {}
        taille_totale = 0
        
        for piece in st.session_state.pieces.values():
            # Par type
            par_type[piece.type_piece] = par_type.get(piece.type_piece, 0) + 1
            
            # Taille totale
            if piece.taille:
                taille_totale += piece.taille
        
        # Pièces récentes
        pieces_recentes = sorted(
            st.session_state.pieces.values(),
            key=lambda p: p.date_ajout,
            reverse=True
        )[:10]
        
        return {
            'total': total,
            'par_type': par_type,
            'taille_totale': taille_totale,
            'pieces_recentes': pieces_recentes
        }
    
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """Calcule le hash SHA-256 d'un fichier"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formate la taille d'un fichier"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

def display_pieces_interface():
    """Interface principale de gestion des pièces"""
    st.title("📎 Gestion des Pièces")
    
    manager = PiecesManager()
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Liste des pièces",
        "➕ Ajouter une pièce",
        "🔍 Recherche",
        "📊 Statistiques"
    ])
    
    with tab1:
        display_pieces_list(manager)
    
    with tab2:
        display_add_piece(manager)
    
    with tab3:
        display_search_pieces(manager)
    
    with tab4:
        display_pieces_statistics(manager)

def display_pieces_list(manager: PiecesManager):
    """Affiche la liste des pièces"""
    st.subheader("📋 Liste des pièces")
    
    # Options d'affichage
    col1, col2, col3 = st.columns(3)
    with col1:
        view_mode = st.selectbox(
            "Mode d'affichage",
            ["Liste", "Cartes", "Tableau"]
        )
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Date d'ajout", "Nom", "Type", "Numéro d'ordre"]
        )
    with col3:
        filter_type = st.selectbox(
            "Filtrer par type",
            ["Tous"] + manager.TYPES_PIECES
        )
    
    # Récupérer et filtrer les pièces
    pieces = list(st.session_state.pieces.values())
    
    if filter_type != "Tous":
        pieces = [p for p in pieces if p.type_piece == filter_type]
    
    # Trier les pièces
    if sort_by == "Date d'ajout":
        pieces.sort(key=lambda p: p.date_ajout, reverse=True)
    elif sort_by == "Nom":
        pieces.sort(key=lambda p: p.nom.lower())
    elif sort_by == "Type":
        pieces.sort(key=lambda p: p.type_piece)
    elif sort_by == "Numéro d'ordre":
        pieces.sort(key=lambda p: p.numero_ordre)
    
    if not pieces:
        st.info("Aucune pièce trouvée")
        return
    
    # Affichage selon le mode choisi
    if view_mode == "Liste":
        for piece in pieces:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                
                with col1:
                    st.write(f"#{piece.numero_ordre}")
                
                with col2:
                    st.markdown(f"**{piece.nom}**")
                    if piece.description:
                        st.caption(piece.description[:100] + "..." if len(piece.description) > 100 else piece.description)
                
                with col3:
                    st.write(f"📁 {piece.type_piece}")
                    st.caption(f"Ajouté le {piece.date_ajout.strftime('%d/%m/%Y')}")
                
                with col4:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("👁️", key=f"view_{piece.id}", help="Voir"):
                            st.session_state.current_piece_id = piece.id
                            st.session_state.show_piece_detail = True
                    with col_b:
                        if st.button("🗑️", key=f"del_{piece.id}", help="Supprimer"):
                            manager.delete_piece(piece.id)
                            st.rerun()
                
                st.divider()
    
    elif view_mode == "Cartes":
        # Affichage en cartes
        cols = st.columns(3)
        for i, piece in enumerate(pieces):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {piece.nom}")
                    st.caption(f"Pièce n°{piece.numero_ordre}")
                    st.write(f"**Type :** {piece.type_piece}")
                    st.write(f"**Date :** {piece.date_ajout.strftime('%d/%m/%Y')}")
                    if piece.taille:
                        st.write(f"**Taille :** {manager.format_file_size(piece.taille)}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Détails", key=f"card_view_{piece.id}", use_container_width=True):
                            st.session_state.current_piece_id = piece.id
                            st.session_state.show_piece_detail = True
                    with col2:
                        if st.button("Suppr.", key=f"card_del_{piece.id}", use_container_width=True):
                            manager.delete_piece(piece.id)
                            st.rerun()
    
    elif view_mode == "Tableau":
        # Affichage en tableau
        data = []
        for piece in pieces:
            data.append({
                "N°": piece.numero_ordre,
                "Nom": piece.nom,
                "Type": piece.type_piece,
                "Date": piece.date_ajout.strftime('%d/%m/%Y'),
                "Taille": manager.format_file_size(piece.taille) if piece.taille else "N/A",
                "ID": piece.id
            })
        
        df = st.dataframe(data, use_container_width=True, hide_index=True)
    
    # Modal de détail
    if getattr(st.session_state, 'show_piece_detail', False):
        display_piece_detail(manager, st.session_state.current_piece_id)

def display_piece_detail(manager: PiecesManager, piece_id: str):
    """Affiche le détail d'une pièce"""
    piece = manager.get_piece(piece_id)
    
    if not piece:
        st.error("Pièce introuvable")
        return
    
    # Modal simulée
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"## 📄 {piece.nom}")
        with col2:
            if st.button("❌ Fermer"):
                st.session_state.show_piece_detail = False
                st.rerun()
        
        # Informations principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Type", piece.type_piece)
        with col2:
            st.metric("N° d'ordre", piece.numero_ordre)
        with col3:
            st.metric("Date d'ajout", piece.date_ajout.strftime('%d/%m/%Y'))
        
        # Description
        if piece.description:
            st.markdown("### 📝 Description")
            st.info(piece.description)
        
        # Informations techniques
        st.markdown("### 🔧 Informations techniques")
        col1, col2 = st.columns(2)
        with col1:
            if piece.taille:
                st.write(f"**Taille :** {manager.format_file_size(piece.taille)}")
            if piece.hash_fichier:
                st.write(f"**Hash SHA-256 :** `{piece.hash_fichier[:16]}...`")
        with col2:
            if piece.chemin_fichier:
                st.write(f"**Chemin :** `{piece.chemin_fichier}`")
        
        # Métadonnées
        if piece.metadata:
            st.markdown("### 📊 Métadonnées")
            st.json(piece.metadata)
        
        # Actions
        st.markdown("### Actions")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✏️ Modifier", use_container_width=True):
                st.session_state.edit_piece_id = piece_id
                st.session_state.show_edit_piece = True
        with col2:
            if st.button("📋 Dupliquer", use_container_width=True):
                # Créer une copie
                new_piece = PieceProcedure(
                    id=str(uuid.uuid4()),
                    nom=f"{piece.nom} (copie)",
                    type_piece=piece.type_piece,
                    numero_ordre=piece.numero_ordre,
                    description=piece.description,
                    date_ajout=datetime.now(),
                    chemin_fichier=piece.chemin_fichier,
                    taille=piece.taille,
                    hash_fichier=piece.hash_fichier,
                    metadata=piece.metadata.copy()
                )
                manager.add_piece(new_piece)
                st.success("Pièce dupliquée!")
                st.rerun()
        with col3:
            if st.button("📤 Exporter", use_container_width=True):
                st.info("Export à implémenter")
        with col4:
            if st.button("🗑️ Supprimer", use_container_width=True):
                manager.delete_piece(piece_id)
                st.success("Pièce supprimée")
                st.session_state.show_piece_detail = False
                st.rerun()

def display_add_piece(manager: PiecesManager):
    """Interface d'ajout de pièce"""
    st.subheader("➕ Ajouter une pièce")
    
    # Choix du mode d'ajout
    mode = st.radio(
        "Mode d'ajout",
        ["Saisie manuelle", "Import de fichier", "Import multiple"],
        horizontal=True
    )
    
    if mode == "Saisie manuelle":
        with st.form("add_piece_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom de la pièce*", placeholder="Contrat de vente")
                type_piece = st.selectbox("Type de pièce*", manager.TYPES_PIECES)
                numero_ordre = st.number_input(
                    "Numéro d'ordre",
                    min_value=1,
                    value=len(st.session_state.pieces) + 1
                )
            
            with col2:
                dossier_id = st.text_input("ID du dossier (optionnel)", placeholder="Laisser vide si non lié")
                date_ajout = st.date_input("Date d'ajout", value=datetime.now())
            
            description = st.text_area(
                "Description",
                placeholder="Description détaillée de la pièce...",
                height=100
            )
            
            # Métadonnées personnalisées
            st.markdown("### Métadonnées (optionnel)")
            metadata_json = st.text_area(
                "Format JSON",
                placeholder='{"auteur": "Me Dupont", "version": "1.0"}',
                height=100
            )
            
            submitted = st.form_submit_button("✅ Ajouter la pièce", use_container_width=True)
            
            if submitted and nom:
                try:
                    metadata = {}
                    if metadata_json:
                        metadata = json.loads(metadata_json)
                    
                    piece = PieceProcedure(
                        id=str(uuid.uuid4()),
                        nom=nom,
                        type_piece=type_piece,
                        numero_ordre=numero_ordre,
                        description=description if description else None,
                        date_ajout=datetime.combine(date_ajout, datetime.min.time()),
                        metadata=metadata
                    )
                    
                    manager.add_piece(piece, dossier_id if dossier_id else None)
                    st.success(f"✅ Pièce '{nom}' ajoutée avec succès!")
                    st.balloons()
                except json.JSONDecodeError:
                    st.error("❌ Erreur dans le format JSON des métadonnées")
    
    elif mode == "Import de fichier":
        st.info("📁 Glissez-déposez un fichier ou cliquez pour parcourir")
        
        uploaded_file = st.file_uploader(
            "Choisir un fichier",
            accept_multiple_files=False
        )
        
        if uploaded_file:
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input(
                    "Nom de la pièce",
                    value=uploaded_file.name,
                    placeholder="Nom personnalisé"
                )
                type_piece = st.selectbox("Type de pièce", manager.TYPES_PIECES)
            
            with col2:
                numero_ordre = st.number_input(
                    "Numéro d'ordre",
                    min_value=1,
                    value=len(st.session_state.pieces) + 1
                )
                dossier_id = st.text_input("ID du dossier (optionnel)")
            
            description = st.text_area("Description", height=100)
            
            if st.button("📥 Importer le fichier", use_container_width=True):
                # Lire le contenu du fichier
                content = uploaded_file.read()
                
                # Créer la pièce
                piece = PieceProcedure(
                    id=str(uuid.uuid4()),
                    nom=nom,
                    type_piece=type_piece,
                    numero_ordre=numero_ordre,
                    description=description if description else None,
                    date_ajout=datetime.now(),
                    chemin_fichier=uploaded_file.name,
                    taille=len(content),
                    hash_fichier=manager.calculate_file_hash(content),
                    metadata={
                        "mime_type": uploaded_file.type,
                        "original_name": uploaded_file.name
                    }
                )
                
                manager.add_piece(piece, dossier_id if dossier_id else None)
                st.success(f"✅ Fichier '{nom}' importé avec succès!")
    
    else:  # Import multiple
        st.info("📁 Glissez-déposez plusieurs fichiers ou cliquez pour parcourir")
        
        uploaded_files = st.file_uploader(
            "Choisir des fichiers",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} fichiers sélectionnés**")
            
            # Options communes
            col1, col2 = st.columns(2)
            with col1:
                type_piece = st.selectbox("Type de pièce pour tous", manager.TYPES_PIECES)
            with col2:
                dossier_id = st.text_input("ID du dossier (optionnel)")
            
            if st.button(f"📥 Importer {len(uploaded_files)} fichiers", use_container_width=True):
                progress = st.progress(0)
                
                for i, file in enumerate(uploaded_files):
                    # Lire le contenu
                    content = file.read()
                    
                    # Créer la pièce
                    piece = PieceProcedure(
                        id=str(uuid.uuid4()),
                        nom=file.name,
                        type_piece=type_piece,
                        numero_ordre=len(st.session_state.pieces) + i + 1,
                        date_ajout=datetime.now(),
                        chemin_fichier=file.name,
                        taille=len(content),
                        hash_fichier=manager.calculate_file_hash(content),
                        metadata={
                            "mime_type": file.type,
                            "original_name": file.name
                        }
                    )
                    
                    manager.add_piece(piece, dossier_id if dossier_id else None)
                    progress.progress((i + 1) / len(uploaded_files))
                
                st.success(f"✅ {len(uploaded_files)} fichiers importés avec succès!")
                st.balloons()

def display_search_pieces(manager: PiecesManager):
    """Interface de recherche de pièces"""
    st.subheader("🔍 Recherche de pièces")
    
    # Barre de recherche
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Recherche",
            placeholder="Nom, description, type...",
            key="pieces_search"
        )
    with col2:
        search_button = st.button("🔍 Rechercher", use_container_width=True)
    
    # Filtres avancés
    with st.expander("🎯 Filtres avancés"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            type_filter = st.selectbox(
                "Type de pièce",
                ["Tous"] + manager.TYPES_PIECES
            )
        
        with col2:
            date_debut = st.date_input("Date début", value=None)
        
        with col3:
            date_fin = st.date_input("Date fin", value=None)
        
        dossier_filter = st.text_input("ID du dossier", placeholder="Filtrer par dossier")
    
    # Effectuer la recherche
    if search_button and query:
        filters = {}
        if type_filter != "Tous":
            filters['type_piece'] = type_filter
        if date_debut:
            filters['date_debut'] = datetime.combine(date_debut, datetime.min.time())
        if date_fin:
            filters['date_fin'] = datetime.combine(date_fin, datetime.max.time())
        if dossier_filter:
            filters['dossier_id'] = dossier_filter
        
        results = manager.search_pieces(query, filters)
        
        # Afficher les résultats
        if results:
            st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
            
            for piece in results:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{piece.nom}**")
                        if piece.description:
                            st.caption(piece.description[:150] + "..." if len(piece.description) > 150 else piece.description)
                    
                    with col2:
                        st.write(f"Type : {piece.type_piece}")
                        st.caption(f"Ajouté le {piece.date_ajout.strftime('%d/%m/%Y')}")
                    
                    with col3:
                        if st.button("Voir", key=f"search_view_{piece.id}"):
                            st.session_state.current_piece_id = piece.id
                            st.session_state.show_piece_detail = True
                    
                    st.divider()
        else:
            st.warning("❌ Aucun résultat trouvé")

def display_pieces_statistics(manager: PiecesManager):
    """Affiche les statistiques des pièces"""
    st.subheader("📊 Statistiques des pièces")
    
    stats = manager.get_statistics()
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total pièces", stats['total'])
    with col2:
        st.metric("Types différents", len(stats['par_type']))
    with col3:
        st.metric("Taille totale", manager.format_file_size(stats['taille_totale']))
    with col4:
        if stats['total'] > 0:
            taille_moyenne = stats['taille_totale'] / stats['total']
            st.metric("Taille moyenne", manager.format_file_size(int(taille_moyenne)))
        else:
            st.metric("Taille moyenne", "N/A")
    
    if stats['total'] > 0:
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📁 Répartition par type")
            for type_piece, count in sorted(stats['par_type'].items(), key=lambda x: x[1], reverse=True):
                st.write(f"**{type_piece}** : {count} pièces")
                if stats['total'] > 0:
                    st.progress(count / stats['total'])
        
        with col2:
            st.markdown("### 🕐 Pièces récentes")
            for piece in stats['pieces_recentes'][:5]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"• {piece.nom}")
                    st.caption(f"{piece.type_piece} - {piece.date_ajout.strftime('%d/%m/%Y')}")
                with col_b:
                    if st.button("👁️", key=f"stat_view_{piece.id}"):
                        st.session_state.current_piece_id = piece.id
                        st.session_state.show_piece_detail = True
    else:
        st.info("Aucune pièce dans la base. Commencez par en ajouter!")
    
    # Export des statistiques
    st.markdown("### 📤 Export")
    if st.button("📊 Exporter les statistiques en JSON"):
        export_data = {
            "date_export": datetime.now().isoformat(),
            "total_pieces": stats['total'],
            "repartition_types": stats['par_type'],
            "taille_totale_octets": stats['taille_totale'],
            "pieces_recentes": [
                {
                    "nom": p.nom,
                    "type": p.type_piece,
                    "date": p.date_ajout.isoformat()
                }
                for p in stats['pieces_recentes'][:10]
            ]
        }
        
        st.download_button(
            label="Télécharger",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"stats_pieces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Point d'entrée principal
if __name__ == "__main__":
    display_pieces_interface()