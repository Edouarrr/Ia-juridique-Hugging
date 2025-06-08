# modules/piece_selection_optimized.py
"""Module optimisé de gestion de la sélection des pièces juridiques"""

import streamlit as st
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
import re
from dataclasses import dataclass, field

from models.dataclasses import PieceSelectionnee, Document
from utils.helpers import clean_key

@dataclass
class PieceSelectionneeAvancee(PieceSelectionnee):
    """Version étendue de PieceSelectionnee avec fonctionnalités supplémentaires"""
    notes: str = ""
    pertinence_manuelle: Optional[int] = None  # 1-10
    tags: List[str] = field(default_factory=list)
    date_selection: datetime = field(default_factory=datetime.now)
    modifie_le: Optional[datetime] = None

class GestionnairePiecesSelectionnees:
    """Gestionnaire centralisé pour les pièces sélectionnées"""
    
    # Catégories par défaut avec leurs patterns de détection
    CATEGORIES_PATTERNS = {
        'Procédure': ['plainte', 'procès-verbal', 'audition', 'perquisition', 'garde à vue', 'réquisitoire'],
        'Expertise': ['expertise', 'expert', 'rapport technique', 'analyse', 'évaluation technique'],
        'Comptabilité': ['bilan', 'compte', 'comptable', 'facture', 'devis', 'grand livre', 'journal'],
        'Contrats': ['contrat', 'convention', 'accord', 'avenant', 'protocole', 'engagement'],
        'Correspondance': ['courrier', 'email', 'lettre', 'mail', 'courriel', 'message'],
        'Pièces d\'identité': ['carte identité', 'passeport', 'kbis', 'statuts', 'extrait', 'immatriculation'],
        'Bancaire': ['relevé', 'virement', 'compte bancaire', 'rib', 'iban', 'swift'],
        'Juridique': ['jugement', 'arrêt', 'ordonnance', 'décision', 'verdict', 'citation'],
        'Administratif': ['autorisation', 'déclaration', 'certificat', 'attestation', 'permis', 'licence'],
        'Autres': []
    }
    
    def __init__(self):
        self.pieces: Dict[str, PieceSelectionneeAvancee] = {}
        self.categories_custom = list(self.CATEGORIES_PATTERNS.keys())
        
    def ajouter_piece(self, doc: Dict[str, Any], categorie: Optional[str] = None, 
                     notes: str = "", pertinence_auto: float = 0.5) -> str:
        """Ajoute une pièce à la sélection"""
        doc_id = doc.get('id', str(datetime.now().timestamp()))
        
        if doc_id in self.pieces:
            return doc_id
        
        # Déterminer la catégorie si non fournie
        if not categorie:
            categorie = self._determiner_categorie(doc)
        
        # Créer la pièce
        piece = PieceSelectionneeAvancee(
            numero=len(self.pieces) + 1,
            titre=doc.get('title', 'Sans titre'),
            description=self._extraire_description(doc),
            categorie=categorie,
            date=self._extraire_date(doc),
            source=doc.get('source', ''),
            pertinence=pertinence_auto,
            notes=notes,
            document_id=doc_id
        )
        
        self.pieces[doc_id] = piece
        self._sauvegarder_session()
        return doc_id
    
    def retirer_piece(self, doc_id: str):
        """Retire une pièce de la sélection"""
        if doc_id in self.pieces:
            del self.pieces[doc_id]
            self._renumeroter()
            self._sauvegarder_session()
    
    def modifier_piece(self, doc_id: str, **kwargs):
        """Modifie les propriétés d'une pièce"""
        if doc_id in self.pieces:
            piece = self.pieces[doc_id]
            for key, value in kwargs.items():
                if hasattr(piece, key):
                    setattr(piece, key, value)
            piece.modifie_le = datetime.now()
            self._sauvegarder_session()
    
    def get_pieces_par_categorie(self) -> Dict[str, List[PieceSelectionneeAvancee]]:
        """Retourne les pièces groupées par catégorie"""
        result = defaultdict(list)
        for piece in self.pieces.values():
            result[piece.categorie].append(piece)
        return dict(result)
    
    def rechercher_pieces(self, query: str) -> List[PieceSelectionneeAvancee]:
        """Recherche des pièces selon un critère"""
        query_lower = query.lower()
        results = []
        
        for piece in self.pieces.values():
            if (query_lower in piece.titre.lower() or 
                query_lower in piece.description.lower() or
                query_lower in piece.notes.lower() or
                any(query_lower in tag.lower() for tag in piece.tags)):
                results.append(piece)
        
        return results
    
    def calculer_statistiques(self) -> Dict[str, Any]:
        """Calcule les statistiques de la sélection"""
        if not self.pieces:
            return {'total': 0}
        
        pieces_list = list(self.pieces.values())
        categories_count = defaultdict(int)
        for piece in pieces_list:
            categories_count[piece.categorie] += 1
        
        return {
            'total': len(pieces_list),
            'categories': dict(categories_count),
            'pertinence_moyenne': sum(p.pertinence for p in pieces_list) / len(pieces_list),
            'pertinence_manuelle_moyenne': self._calculer_moyenne_pertinence_manuelle(),
            'pieces_avec_notes': sum(1 for p in pieces_list if p.notes),
            'derniere_modification': max((p.modifie_le or p.date_selection for p in pieces_list), default=None)
        }
    
    def generer_bordereau(self, format_type: str = "detaille") -> str:
        """Génère un bordereau de communication"""
        if not self.pieces:
            return "Aucune pièce sélectionnée"
        
        lines = [
            "BORDEREAU DE COMMUNICATION DE PIÈCES",
            "=" * 50,
            f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"Nombre de pièces : {len(self.pieces)}",
            "",
        ]
        
        pieces_par_cat = self.get_pieces_par_categorie()
        
        for categorie, pieces in sorted(pieces_par_cat.items()):
            lines.extend([
                "",
                f"{categorie.upper()} ({len(pieces)} pièces)",
                "-" * 40,
            ])
            
            for piece in sorted(pieces, key=lambda x: x.numero):
                if format_type == "detaille":
                    lines.extend([
                        f"Pièce n°{piece.numero} : {piece.titre}",
                        f"   Description : {piece.description[:100]}..." if len(piece.description) > 100 else f"   Description : {piece.description}",
                        f"   Source : {piece.source}",
                        f"   Pertinence : {piece.pertinence:.0%}",
                    ])
                    if piece.notes:
                        lines.append(f"   Notes : {piece.notes}")
                    if piece.date:
                        date_str = piece.date.strftime('%d/%m/%Y') if isinstance(piece.date, datetime) else str(piece.date)
                        lines.append(f"   Date : {date_str}")
                    lines.append("")
                else:  # format simple
                    lines.append(f"{piece.numero}. {piece.titre}")
        
        return "\n".join(lines)
    
    def exporter_selection(self, format_export: str = "txt") -> Tuple[str, str, str]:
        """Exporte la sélection dans différents formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_export == "txt":
            content = self.generer_bordereau("detaille")
            filename = f"selection_pieces_{timestamp}.txt"
            mime_type = "text/plain"
        
        elif format_export == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';')
            
            # En-têtes
            writer.writerow(['Numéro', 'Titre', 'Catégorie', 'Description', 
                           'Source', 'Pertinence', 'Notes', 'Date'])
            
            # Données
            for piece in sorted(self.pieces.values(), key=lambda x: x.numero):
                date_str = piece.date.strftime('%d/%m/%Y') if piece.date and isinstance(piece.date, datetime) else str(piece.date or '')
                writer.writerow([
                    piece.numero,
                    piece.titre,
                    piece.categorie,
                    piece.description,
                    piece.source,
                    f"{piece.pertinence:.0%}",
                    piece.notes,
                    date_str
                ])
            
            content = output.getvalue()
            filename = f"selection_pieces_{timestamp}.csv"
            mime_type = "text/csv"
        
        elif format_export == "json":
            import json
            
            data = {
                'export_date': datetime.now().isoformat(),
                'total_pieces': len(self.pieces),
                'pieces': []
            }
            
            for piece in sorted(self.pieces.values(), key=lambda x: x.numero):
                piece_data = {
                    'numero': piece.numero,
                    'titre': piece.titre,
                    'categorie': piece.categorie,
                    'description': piece.description,
                    'source': piece.source,
                    'pertinence': piece.pertinence,
                    'notes': piece.notes,
                    'tags': piece.tags,
                    'date': piece.date.isoformat() if piece.date and isinstance(piece.date, datetime) else str(piece.date or ''),
                    'date_selection': piece.date_selection.isoformat()
                }
                data['pieces'].append(piece_data)
            
            content = json.dumps(data, ensure_ascii=False, indent=2)
            filename = f"selection_pieces_{timestamp}.json"
            mime_type = "application/json"
        
        else:
            raise ValueError(f"Format non supporté : {format_export}")
        
        return content, filename, mime_type
    
    # Méthodes privées
    def _determiner_categorie(self, doc: Dict[str, Any]) -> str:
        """Détermine automatiquement la catégorie d'un document"""
        title_lower = doc.get('title', '').lower()
        content_lower = doc.get('content', '')[:1000].lower()
        
        for category, keywords in self.CATEGORIES_PATTERNS.items():
            if keywords and any(kw in title_lower or kw in content_lower for kw in keywords):
                return category
        
        return 'Autres'
    
    def _extraire_description(self, doc: Dict[str, Any]) -> str:
        """Extrait une description du document"""
        content = doc.get('content', '')
        if len(content) > 200:
            return content[:197] + '...'
        return content
    
    def _extraire_date(self, doc: Dict[str, Any]) -> Optional[datetime]:
        """Extrait la date du document"""
        if doc.get('date'):
            if isinstance(doc['date'], datetime):
                return doc['date']
            try:
                return datetime.fromisoformat(str(doc['date']))
            except:
                pass
        
        # Essayer dans les métadonnées
        if doc.get('metadata', {}).get('date'):
            try:
                return datetime.fromisoformat(str(doc['metadata']['date']))
            except:
                pass
        
        return None
    
    def _renumeroter(self):
        """Renumérotation des pièces après suppression"""
        for i, piece in enumerate(sorted(self.pieces.values(), key=lambda x: x.numero), 1):
            piece.numero = i
    
    def _calculer_moyenne_pertinence_manuelle(self) -> Optional[float]:
        """Calcule la moyenne des pertinences manuelles"""
        pertinences = [p.pertinence_manuelle for p in self.pieces.values() if p.pertinence_manuelle]
        return sum(pertinences) / len(pertinences) if pertinences else None
    
    def _sauvegarder_session(self):
        """Sauvegarde dans la session Streamlit"""
        st.session_state.pieces_selectionnees = self.pieces
        st.session_state.gestionnaire_pieces = self


def process_piece_selection_request(query: str, analysis: dict):
    """Traite une demande de sélection de pièces avec interface avancée"""
    
    st.markdown("### 📋 Sélection avancée de pièces")
    
    # Initialiser le gestionnaire
    if 'gestionnaire_pieces' not in st.session_state:
        st.session_state.gestionnaire_pieces = GestionnairePiecesSelectionnees()
    
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Interface en deux colonnes
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("#### 📄 Documents disponibles")
        _afficher_documents_disponibles(gestionnaire, analysis)
    
    with col_right:
        st.markdown("#### ✅ Pièces sélectionnées")
        _afficher_pieces_selectionnees(gestionnaire)
    
    # Barre d'actions
    _afficher_barre_actions(gestionnaire)


def _afficher_documents_disponibles(gestionnaire: GestionnairePiecesSelectionnees, analysis: dict):
    """Affiche les documents disponibles avec filtrage"""
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        filtre_texte = st.text_input(
            "🔍 Rechercher",
            placeholder="Titre, contenu...",
            key="filtre_docs_texte"
        )
    
    with col2:
        filtre_categorie = st.selectbox(
            "📁 Catégorie",
            ["Toutes"] + list(gestionnaire.CATEGORIES_PATTERNS.keys()),
            key="filtre_docs_categorie"
        )
    
    # Collecter et filtrer les documents
    documents = collect_available_documents(analysis)
    
    if filtre_texte:
        documents = [d for d in documents if filtre_texte.lower() in 
                    (d.get('title', '') + ' ' + d.get('content', '')).lower()]
    
    if filtre_categorie != "Toutes":
        documents = [d for d in documents if 
                    gestionnaire._determiner_categorie(d) == filtre_categorie]
    
    # Affichage avec pagination
    docs_par_page = 10
    total_pages = (len(documents) - 1) // docs_par_page + 1
    
    if total_pages > 1:
        page = st.number_input(
            f"Page ({total_pages} au total)",
            min_value=1,
            max_value=total_pages,
            value=1,
            key="page_docs"
        )
    else:
        page = 1
    
    debut = (page - 1) * docs_par_page
    fin = debut + docs_par_page
    
    # Afficher les documents
    for doc in documents[debut:fin]:
        _afficher_carte_document(doc, gestionnaire, analysis)


def _afficher_carte_document(doc: dict, gestionnaire: GestionnairePiecesSelectionnees, analysis: dict):
    """Affiche une carte de document"""
    doc_id = doc.get('id', str(hash(doc.get('title', ''))))
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Titre et badges
            titre = doc.get('title', 'Sans titre')
            if doc_id in gestionnaire.pieces:
                st.markdown(f"**✅ {titre}**")
            else:
                st.markdown(f"**{titre}**")
            
            # Métadonnées
            meta_parts = []
            if doc.get('source'):
                meta_parts.append(f"📍 {doc['source']}")
            if doc.get('date'):
                meta_parts.append(f"📅 {doc['date']}")
            
            pertinence = calculate_piece_relevance(doc, analysis)
            if pertinence >= 0.7:
                meta_parts.append("🟢 Très pertinent")
            elif pertinence >= 0.4:
                meta_parts.append("🟡 Pertinent")
            else:
                meta_parts.append("🔴 Peu pertinent")
            
            if meta_parts:
                st.caption(" | ".join(meta_parts))
            
            # Extrait du contenu
            if doc.get('content'):
                with st.expander("Aperçu", expanded=False):
                    st.text(doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content'])
        
        with col2:
            if doc_id not in gestionnaire.pieces:
                # Bouton d'ajout avec options
                if st.button("➕ Ajouter", key=f"add_{doc_id}"):
                    with st.popover("Options d'ajout"):
                        categorie = st.selectbox(
                            "Catégorie",
                            gestionnaire.categories_custom,
                            index=gestionnaire.categories_custom.index(
                                gestionnaire._determiner_categorie(doc)
                            ),
                            key=f"cat_{doc_id}"
                        )
                        
                        notes = st.text_area(
                            "Notes",
                            placeholder="Notes sur cette pièce...",
                            key=f"notes_add_{doc_id}"
                        )
                        
                        if st.button("Confirmer", key=f"confirm_add_{doc_id}"):
                            gestionnaire.ajouter_piece(
                                doc,
                                categorie=categorie,
                                notes=notes,
                                pertinence_auto=pertinence
                            )
                            st.rerun()
            else:
                if st.button("❌ Retirer", key=f"remove_{doc_id}"):
                    gestionnaire.retirer_piece(doc_id)
                    st.rerun()
        
        st.divider()


def _afficher_pieces_selectionnees(gestionnaire: GestionnairePiecesSelectionnees):
    """Affiche les pièces sélectionnées avec gestion avancée"""
    
    stats = gestionnaire.calculer_statistiques()
    
    # Statistiques
    if stats['total'] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", stats['total'])
        with col2:
            st.metric("Pertinence moy.", f"{stats['pertinence_moyenne']:.0%}")
        with col3:
            st.metric("Avec notes", stats['pieces_avec_notes'])
    
    # Filtres et tri
    col1, col2 = st.columns(2)
    with col1:
        filtre_cat_selected = st.selectbox(
            "Filtrer par catégorie",
            ["Toutes"] + list(stats['categories'].keys()),
            key="filtre_selected_cat"
        )
    
    with col2:
        tri_par = st.selectbox(
            "Trier par",
            ["Numéro", "Pertinence", "Titre", "Date"],
            key="tri_pieces"
        )
    
    # Affichage par catégorie
    pieces_par_cat = gestionnaire.get_pieces_par_categorie()
    
    for categorie, pieces in pieces_par_cat.items():
        if filtre_cat_selected != "Toutes" and categorie != filtre_cat_selected:
            continue
        
        if not pieces:
            continue
        
        with st.expander(f"📁 {categorie} ({len(pieces)} pièces)", expanded=True):
            # Trier les pièces
            if tri_par == "Numéro":
                pieces = sorted(pieces, key=lambda x: x.numero)
            elif tri_par == "Pertinence":
                pieces = sorted(pieces, key=lambda x: x.pertinence, reverse=True)
            elif tri_par == "Titre":
                pieces = sorted(pieces, key=lambda x: x.titre)
            elif tri_par == "Date":
                pieces = sorted(pieces, key=lambda x: x.date or datetime.min, reverse=True)
            
            for piece in pieces:
                _afficher_piece_detail(piece, gestionnaire)


def _afficher_piece_detail(piece: PieceSelectionneeAvancee, gestionnaire: GestionnairePiecesSelectionnees):
    """Affiche le détail d'une pièce avec édition"""
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**#{piece.numero} - {piece.titre}**")
            
            # Description
            if piece.description:
                st.caption(piece.description[:100] + "..." if len(piece.description) > 100 else piece.description)
        
        with col2:
            # Pertinence
            color = "🟢" if piece.pertinence >= 0.7 else "🟡" if piece.pertinence >= 0.4 else "🔴"
            st.caption(f"{color} {piece.pertinence:.0%}")
            
            # Pertinence manuelle
            if piece.pertinence_manuelle:
                st.caption(f"⭐ {piece.pertinence_manuelle}/10")
        
        with col3:
            # Actions
            col_edit, col_del = st.columns(2)
            
            with col_edit:
                if st.button("✏️", key=f"edit_{piece.document_id}"):
                    st.session_state[f"editing_{piece.document_id}"] = True
            
            with col_del:
                if st.button("🗑️", key=f"del_{piece.document_id}"):
                    gestionnaire.retirer_piece(piece.document_id)
                    st.rerun()
        
        # Mode édition
        if st.session_state.get(f"editing_{piece.document_id}"):
            with st.container():
                col1, col2 = st.columns(2)
                
                with col1:
                    # Notes
                    new_notes = st.text_area(
                        "Notes",
                        value=piece.notes,
                        key=f"edit_notes_{piece.document_id}"
                    )
                    
                    # Tags
                    tags_str = st.text_input(
                        "Tags (séparés par des virgules)",
                        value=", ".join(piece.tags),
                        key=f"edit_tags_{piece.document_id}"
                    )
                
                with col2:
                    # Pertinence manuelle
                    new_pertinence = st.slider(
                        "Pertinence manuelle",
                        1, 10,
                        value=piece.pertinence_manuelle or 5,
                        key=f"edit_pert_{piece.document_id}"
                    )
                    
                    # Catégorie
                    new_categorie = st.selectbox(
                        "Catégorie",
                        gestionnaire.categories_custom,
                        index=gestionnaire.categories_custom.index(piece.categorie),
                        key=f"edit_cat_{piece.document_id}"
                    )
                
                # Boutons de validation
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    if st.button("💾 Enregistrer", key=f"save_{piece.document_id}"):
                        gestionnaire.modifier_piece(
                            piece.document_id,
                            notes=new_notes,
                            tags=[t.strip() for t in tags_str.split(',') if t.strip()],
                            pertinence_manuelle=new_pertinence,
                            categorie=new_categorie
                        )
                        st.session_state[f"editing_{piece.document_id}"] = False
                        st.rerun()
                
                with col_cancel:
                    if st.button("❌ Annuler", key=f"cancel_{piece.document_id}"):
                        st.session_state[f"editing_{piece.document_id}"] = False
                        st.rerun()
        
        elif piece.notes or piece.tags:
            # Affichage des notes et tags
            if piece.notes:
                st.caption(f"📝 {piece.notes}")
            if piece.tags:
                st.caption(f"🏷️ {', '.join(piece.tags)}")
        
        st.divider()


def _afficher_barre_actions(gestionnaire: GestionnairePiecesSelectionnees):
    """Affiche la barre d'actions globales"""
    
    if not gestionnaire.pieces:
        st.info("Aucune pièce sélectionnée. Ajoutez des documents depuis la colonne de gauche.")
        return
    
    st.markdown("---")
    st.markdown("### 🎯 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Créer bordereau", key="create_bordereau_main"):
            with st.expander("Options du bordereau", expanded=True):
                format_bordereau = st.radio(
                    "Format",
                    ["detaille", "simple"],
                    key="format_bordereau"
                )
                
                bordereau = gestionnaire.generer_bordereau(format_bordereau)
                
                st.text_area("Aperçu", bordereau, height=300)
                
                st.download_button(
                    "💾 Télécharger",
                    bordereau.encode('utf-8'),
                    f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain",
                    key="download_bordereau_action"
                )
    
    with col2:
        if st.button("📤 Exporter", key="export_selection_main"):
            with st.expander("Options d'export", expanded=True):
                format_export = st.radio(
                    "Format",
                    ["txt", "csv", "json"],
                    key="format_export"
                )
                
                try:
                    content, filename, mime_type = gestionnaire.exporter_selection(format_export)
                    
                    st.download_button(
                        f"💾 Télécharger ({format_export.upper()})",
                        content.encode('utf-8'),
                        filename,
                        mime_type,
                        key=f"download_export_{format_export}"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'export : {str(e)}")
    
    with col3:
        if st.button("📝 Synthétiser", key="synthesize_main"):
            st.session_state.action_requested = "synthesis"
            st.session_state.synthesis_pieces = list(gestionnaire.pieces.values())
            st.rerun()
    
    with col4:
        if st.button("🗑️ Tout effacer", key="clear_all_main"):
            if st.button("⚠️ Confirmer suppression", key="confirm_clear_all"):
                gestionnaire.pieces.clear()
                gestionnaire._sauvegarder_session()
                st.rerun()


def collect_available_documents(analysis: dict) -> List[Dict[str, Any]]:
    """Collecte tous les documents disponibles avec enrichissement"""
    documents = []
    
    # Documents locaux depuis la session
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        doc_dict = {
            'id': doc_id,
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'metadata': doc.metadata if hasattr(doc, 'metadata') else {},
            'date': doc.metadata.get('date') if hasattr(doc, 'metadata') else None
        }
        documents.append(doc_dict)
    
    # Si référence spécifique dans l'analyse
    if analysis.get('reference'):
        ref_docs = search_by_reference(f"@{analysis['reference']}")
        documents.extend(ref_docs)
    
    # Dédupliquer par titre
    seen_titles = set()
    unique_docs = []
    for doc in documents:
        if doc['title'] not in seen_titles:
            seen_titles.add(doc['title'])
            unique_docs.append(doc)
    
    return unique_docs


def calculate_piece_relevance(doc: Dict[str, Any], analysis: Dict[str, Any]) -> float:
    """Calcule la pertinence d'une pièce de manière avancée"""
    score = 0.5  # Score de base
    
    # Analyse du contenu par rapport au sujet
    if analysis.get('subject_matter'):
        subject_words = set(analysis['subject_matter'].lower().split())
        doc_text = (doc.get('title', '') + ' ' + doc.get('content', '')).lower()
        
        # Calcul TF-IDF simplifié
        doc_words = set(doc_text.split())
        common_words = subject_words.intersection(doc_words)
        
        if subject_words:
            score += (len(common_words) / len(subject_words)) * 0.3
    
    # Bonus pour référence exacte
    if analysis.get('reference'):
        ref_lower = analysis['reference'].lower()
        if ref_lower in doc.get('title', '').lower():
            score += 0.2
        elif ref_lower in doc.get('content', '')[:500].lower():
            score += 0.1
    
    # Bonus pour fraîcheur
    if doc.get('date'):
        try:
            doc_date = doc['date'] if isinstance(doc['date'], datetime) else datetime.fromisoformat(str(doc['date']))
            age_days = (datetime.now() - doc_date).days
            
            if age_days < 7:
                score += 0.15
            elif age_days < 30:
                score += 0.10
            elif age_days < 90:
                score += 0.05
        except:
            pass
    
    # Bonus pour métadonnées complètes
    if doc.get('metadata'):
        metadata_keys = ['author', 'tags', 'category', 'importance']
        metadata_score = sum(0.025 for key in metadata_keys if doc['metadata'].get(key))
        score += metadata_score
    
    return min(score, 1.0)


def search_by_reference(reference: str) -> List[Dict[str, Any]]:
    """Recherche avancée par référence"""
    results = []
    ref_clean = reference.replace('@', '').strip().lower()
    
    # Patterns de recherche
    patterns = [
        ref_clean,  # Exact
        ref_clean.replace(' ', '_'),  # Underscores
        ref_clean.replace('_', ' '),  # Espaces
        ''.join(ref_clean.split()),  # Sans espaces
    ]
    
    # Recherche dans les documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        doc_text_lower = (doc.title + ' ' + doc.source + ' ' + doc.content[:2000]).lower()
        
        best_score = 0
        for pattern in patterns:
            if pattern in doc_text_lower:
                # Score basé sur la position
                position = doc_text_lower.find(pattern)
                if position < 100:  # Dans le titre ou début
                    score = 1.0
                elif position < 500:
                    score = 0.8
                else:
                    score = 0.6
                
                best_score = max(best_score, score)
        
        if best_score > 0:
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'metadata': doc.metadata if hasattr(doc, 'metadata') else {},
                'score': best_score
            })
    
    # Recherche Azure si disponible
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and search_manager.is_connected():
        try:
            azure_results = search_manager.search(reference, top=20)
            for result in azure_results:
                result['score'] = result.get('score', 0.5) * 0.8  # Légèrement pénaliser les résultats Azure
            results.extend(azure_results)
        except Exception as e:
            st.warning(f"Erreur lors de la recherche Azure : {str(e)}")
    
    # Trier par score et dédupliquer
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Dédupliquer par titre
    seen_titles = set()
    unique_results = []
    for result in results:
        if result['title'] not in seen_titles:
            seen_titles.add(result['title'])
            unique_results.append(result)
    
    return unique_results[:50]  # Limiter à 50 résultats


def show_pieces_management_tab():
    """Affiche l'onglet de gestion des pièces en mode page complète"""
    st.markdown("### 📋 Gestion avancée des pièces")
    
    # Initialiser le gestionnaire
    if 'gestionnaire_pieces' not in st.session_state:
        st.session_state.gestionnaire_pieces = GestionnairePiecesSelectionnees()
    
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Barre de recherche globale
    search_query = st.text_input(
        "🔍 Rechercher dans toutes les pièces",
        placeholder="Titre, description, notes, tags...",
        key="global_search_pieces"
    )
    
    if search_query:
        results = gestionnaire.rechercher_pieces(search_query)
        if results:
            st.success(f"Trouvé {len(results)} pièce(s)")
            for piece in results:
                _afficher_piece_detail(piece, gestionnaire)
        else:
            st.warning("Aucune pièce trouvée")
        return
    
    # Vue normale
    process_piece_selection_request("", {})