"""
Module unifié de gestion des pièces juridiques et de procédure
Fusion des fonctionnalités de sélection et de gestion complète
"""

import streamlit as st
from datetime import datetime
import json
from typing import Dict, List, Optional, Any, Tuple, Set
import uuid
import hashlib
import mimetypes
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import io
import re
from dataclasses import dataclass, field
from enum import Enum

# ========================= MODÈLES DE DONNÉES =========================

class DocumentType(Enum):
    PIECE_PROCEDURE = "piece_procedure"
    PIECE_JURIDIQUE = "piece_juridique"
    AUTRE = "autre"

class StatutPiece(Enum):
    ACTIF = "actif"
    ARCHIVE = "archivé"
    EN_REVISION = "en_revision"
    CONFIDENTIEL = "confidentiel"
    SUPPRIME = "supprimé"
    SELECTIONNE = "sélectionné"

@dataclass
class PieceJuridique:
    """Modèle unifié pour une pièce juridique/procédure"""
    # Identifiants
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: Optional[str] = None  # ID du document source
    
    # Informations principales
    nom: str = ""
    titre: str = ""  # Alias pour compatibilité
    type_piece: str = "Document"
    categorie: str = "Autre"
    numero_ordre: int = 1
    
    # Description et contenu
    description: Optional[str] = None
    contenu_extrait: Optional[str] = None
    
    # Dates
    date_ajout: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None
    date_document: Optional[datetime] = None
    date_selection: Optional[datetime] = None
    
    # Fichier
    chemin_fichier: Optional[str] = None
    taille: Optional[int] = None
    hash_fichier: Optional[str] = None
    mime_type: Optional[str] = None
    
    # Métadonnées
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # État et importance
    statut: str = "actif"
    importance: int = 5  # 1-10
    pertinence: float = 0.5  # 0-1
    pertinence_manuelle: Optional[int] = None  # 1-10
    
    # Gestion et suivi
    notes: str = ""
    modifie_par: Optional[str] = None
    version: int = 1
    versions_precedentes: List[Dict] = field(default_factory=list)
    
    # Relations
    pieces_liees: List[str] = field(default_factory=list)
    dossier_id: Optional[str] = None
    
    @property
    def numero(self):
        """Alias pour compatibilité"""
        return self.numero_ordre
    
    @property
    def date(self):
        """Date principale du document"""
        return self.date_document or self.date_ajout

# ========================= GESTIONNAIRE PRINCIPAL =========================

class GestionnairePiecesUnifie:
    """Gestionnaire unifié pour toutes les pièces"""
    
    # Catégories avec patterns de détection et style
    CATEGORIES_CONFIG = {
        'Procédure': {
            'patterns': ['plainte', 'procès-verbal', 'audition', 'perquisition', 'garde à vue', 
                        'réquisitoire', 'assignation', 'citation', 'conclusions', 'requête', 'mémoire'],
            'types': ['Assignation', 'Citation directe', 'Conclusions', 'Requête', 'Mémoire', 
                     'Plainte', 'Procès-verbal', 'Audition'],
            'icon': '📋',
            'color': '#3498db'
        },
        'Décision': {
            'patterns': ['jugement', 'arrêt', 'ordonnance', 'décision', 'verdict'],
            'types': ['Jugement', 'Arrêt', 'Ordonnance', 'Décision'],
            'icon': '⚖️',
            'color': '#e74c3c'
        },
        'Expertise': {
            'patterns': ['expertise', 'expert', 'rapport technique', 'analyse', 'évaluation technique'],
            'types': ['Expertise', 'Rapport d\'expert', 'Analyse technique'],
            'icon': '🔬',
            'color': '#2ecc71'
        },
        'Contrat': {
            'patterns': ['contrat', 'convention', 'accord', 'avenant', 'protocole', 'engagement'],
            'types': ['Contrat', 'Avenant', 'Convention', 'Protocole', 'Accord'],
            'icon': '📄',
            'color': '#f39c12'
        },
        'Correspondance': {
            'patterns': ['courrier', 'email', 'lettre', 'mail', 'courriel', 'message', 'notification'],
            'types': ['Courrier', 'Email', 'Notification', 'Mise en demeure'],
            'icon': '📧',
            'color': '#9b59b6'
        },
        'Preuve': {
            'patterns': ['attestation', 'procès-verbal', 'constat', 'témoignage', 'preuve'],
            'types': ['Pièce justificative', 'Attestation', 'Procès-verbal', 'Constat', 'Témoignage'],
            'icon': '🔍',
            'color': '#e67e22'
        },
        'Financier': {
            'patterns': ['bilan', 'compte', 'comptable', 'facture', 'devis', 'relevé', 'virement'],
            'types': ['Facture', 'Devis', 'Relevé bancaire', 'Bilan', 'Grand livre'],
            'icon': '💰',
            'color': '#1abc9c'
        },
        'Identité': {
            'patterns': ['carte identité', 'passeport', 'kbis', 'statuts', 'extrait', 'immatriculation'],
            'types': ['Carte d\'identité', 'Passeport', 'KBIS', 'Statuts', 'RIB'],
            'icon': '🆔',
            'color': '#34495e'
        },
        'Média': {
            'patterns': ['photo', 'vidéo', 'audio', 'enregistrement', 'image'],
            'types': ['Photo', 'Vidéo', 'Audio', 'Plan', 'Schéma'],
            'icon': '📸',
            'color': '#95a5a6'
        },
        'Autre': {
            'patterns': [],
            'types': ['Document', 'Note', 'Rapport', 'Autre'],
            'icon': '📎',
            'color': '#7f8c8d'
        }
    }
    
    # Statuts avec configuration visuelle
    STATUTS_CONFIG = {
        'actif': {'label': 'Actif', 'icon': '✅', 'color': '#2ecc71'},
        'sélectionné': {'label': 'Sélectionné', 'icon': '☑️', 'color': '#3498db'},
        'archivé': {'label': 'Archivé', 'icon': '📦', 'color': '#95a5a6'},
        'en_revision': {'label': 'En révision', 'icon': '🔄', 'color': '#f39c12'},
        'confidentiel': {'label': 'Confidentiel', 'icon': '🔒', 'color': '#e74c3c'},
        'supprimé': {'label': 'Supprimé', 'icon': '🗑️', 'color': '#c0392b'}
    }
    
    def __init__(self):
        """Initialise le gestionnaire unifié"""
        # Collections principales
        if 'pieces' not in st.session_state:
            st.session_state.pieces = {}
        if 'pieces_selectionnees' not in st.session_state:
            st.session_state.pieces_selectionnees = {}
        if 'pieces_par_dossier' not in st.session_state:
            st.session_state.pieces_par_dossier = defaultdict(list)
        
        # Métadonnées globales
        if 'pieces_metadata' not in st.session_state:
            st.session_state.pieces_metadata = {
                'total_size': 0,
                'last_modified': datetime.now(),
                'tags': set(),
                'categories_count': defaultdict(int),
                'types_count': defaultdict(int)
            }
        
        # Historique et favoris
        if 'pieces_history' not in st.session_state:
            st.session_state.pieces_history = []
        if 'pieces_favoris' not in st.session_state:
            st.session_state.pieces_favoris = set()
        
        # État UI
        if 'selected_pieces' not in st.session_state:
            st.session_state.selected_pieces = []
    
    # ==================== GESTION DES PIÈCES ====================
    
    def ajouter_piece(self, piece: PieceJuridique, dossier_id: Optional[str] = None, 
                     auto_select: bool = False) -> str:
        """Ajoute une pièce au système"""
        # Validation
        if not piece.nom and not piece.titre:
            raise ValueError("Le nom de la pièce est obligatoire")
        
        # Normaliser le nom
        if not piece.nom:
            piece.nom = piece.titre
        if not piece.titre:
            piece.titre = piece.nom
        
        # Déterminer la catégorie si non définie
        if piece.categorie == "Autre" or not piece.categorie:
            piece.categorie = self._determiner_categorie(piece)
        
        # Vérifier l'unicité du hash si fichier
        if piece.hash_fichier:
            for existing_piece in st.session_state.pieces.values():
                if existing_piece.hash_fichier == piece.hash_fichier:
                    if not st.checkbox(f"Le fichier '{piece.nom}' existe déjà. Continuer ?"):
                        return existing_piece.id
        
        # Calculer la pertinence initiale
        if hasattr(st.session_state, 'current_analysis'):
            piece.pertinence = self._calculer_pertinence(piece, st.session_state.current_analysis)
        
        # Ajouter la pièce
        st.session_state.pieces[piece.id] = piece
        
        # Associer au dossier
        if dossier_id:
            piece.dossier_id = dossier_id
            st.session_state.pieces_par_dossier[dossier_id].append(piece.id)
        
        # Sélectionner automatiquement si demandé
        if auto_select:
            self.selectionner_piece(piece.id)
        
        # Mettre à jour les métadonnées
        self._update_global_metadata(piece, 'add')
        
        # Historique
        self._add_to_history('add', piece.id, {
            'nom': piece.nom,
            'type': piece.type_piece,
            'categorie': piece.categorie
        })
        
        return piece.id
    
    def selectionner_piece(self, piece_id: str, notes: str = ""):
        """Sélectionne une pièce pour la communication"""
        if piece_id not in st.session_state.pieces:
            return
        
        piece = st.session_state.pieces[piece_id]
        
        # Marquer comme sélectionnée
        piece.statut = 'sélectionné'
        piece.date_selection = datetime.now()
        if notes:
            piece.notes = notes
        
        # Ajouter aux pièces sélectionnées
        st.session_state.pieces_selectionnees[piece_id] = piece
        
        # Renumeroter
        self._renumeroter_pieces_selectionnees()
        
        # Historique
        self._add_to_history('select', piece_id, {'nom': piece.nom})
    
    def deselectionner_piece(self, piece_id: str):
        """Retire une pièce de la sélection"""
        if piece_id in st.session_state.pieces_selectionnees:
            del st.session_state.pieces_selectionnees[piece_id]
            
            # Remettre en statut actif
            if piece_id in st.session_state.pieces:
                st.session_state.pieces[piece_id].statut = 'actif'
            
            self._renumeroter_pieces_selectionnees()
            self._add_to_history('deselect', piece_id, {})
    
    def modifier_piece(self, piece_id: str, create_version: bool = True, **kwargs):
        """Modifie une pièce avec gestion des versions"""
        if piece_id not in st.session_state.pieces:
            raise ValueError(f"Pièce {piece_id} introuvable")
        
        piece = st.session_state.pieces[piece_id]
        
        # Créer une version si demandé
        if create_version and any(k in ['nom', 'description', 'type_piece'] for k in kwargs):
            version_data = {
                'version': piece.version,
                'date': datetime.now().isoformat(),
                'nom': piece.nom,
                'description': piece.description,
                'type_piece': piece.type_piece,
                'modifie_par': kwargs.get('modifie_par', 'Utilisateur')
            }
            piece.versions_precedentes.append(version_data)
            piece.version += 1
        
        # Appliquer les modifications
        for key, value in kwargs.items():
            if hasattr(piece, key):
                setattr(piece, key, value)
        
        piece.date_modification = datetime.now()
        
        # Propager aux pièces sélectionnées
        if piece_id in st.session_state.pieces_selectionnees:
            st.session_state.pieces_selectionnees[piece_id] = piece
        
        # Mettre à jour les métadonnées
        st.session_state.pieces_metadata['last_modified'] = datetime.now()
        
        # Historique
        self._add_to_history('update', piece_id, kwargs)
    
    def supprimer_piece(self, piece_id: str, permanent: bool = False):
        """Supprime ou archive une pièce"""
        if piece_id not in st.session_state.pieces:
            return
        
        piece = st.session_state.pieces[piece_id]
        
        if permanent:
            # Suppression définitive
            # Retirer de toutes les collections
            st.session_state.pieces_selectionnees.pop(piece_id, None)
            st.session_state.pieces_favoris.discard(piece_id)
            
            for dossier_pieces in st.session_state.pieces_par_dossier.values():
                if piece_id in dossier_pieces:
                    dossier_pieces.remove(piece_id)
            
            # Supprimer
            del st.session_state.pieces[piece_id]
            
            self._update_global_metadata(piece, 'remove')
            self._add_to_history('delete_permanent', piece_id, {'nom': piece.nom})
        else:
            # Archivage
            piece.statut = 'archivé'
            piece.date_modification = datetime.now()
            self._add_to_history('archive', piece_id, {'nom': piece.nom})
    
    # ==================== RECHERCHE ET FILTRAGE ====================
    
    def rechercher_pieces(self, query: str = "", filters: Dict[str, Any] = None, 
                         limit: Optional[int] = None) -> List[PieceJuridique]:
        """Recherche avancée avec scoring et filtres"""
        results = []
        query_lower = query.lower() if query else ""
        
        for piece in st.session_state.pieces.values():
            # Filtrer par statut
            if not filters or not filters.get('include_archived'):
                if piece.statut in ['supprimé', 'archivé']:
                    continue
            
            score = 0
            
            # Scoring textuel
            if query:
                # Nom/titre (poids élevé)
                if query_lower in piece.nom.lower():
                    score += 5
                    if piece.nom.lower().startswith(query_lower):
                        score += 2
                
                # Description
                if piece.description and query_lower in piece.description.lower():
                    score += 3
                
                # Type et catégorie
                if query_lower in piece.type_piece.lower():
                    score += 2
                if query_lower in piece.categorie.lower():
                    score += 2
                
                # Tags
                for tag in piece.tags:
                    if query_lower in tag.lower():
                        score += 3
                        break
                
                # Contenu extrait
                if piece.contenu_extrait and query_lower in piece.contenu_extrait.lower():
                    score += 1
                
                # Notes
                if piece.notes and query_lower in piece.notes.lower():
                    score += 2
            else:
                score = 1
            
            # Appliquer les filtres
            if filters and not self._piece_matches_filters(piece, filters):
                continue
            
            if score > 0:
                results.append((score, piece))
        
        # Trier par score et pertinence
        results.sort(key=lambda x: (x[0], x[1].pertinence, x[1].date_ajout), reverse=True)
        
        pieces = [piece for _, piece in results]
        
        if limit:
            pieces = pieces[:limit]
        
        return pieces
    
    def _piece_matches_filters(self, piece: PieceJuridique, filters: Dict[str, Any]) -> bool:
        """Vérifie si une pièce correspond aux filtres"""
        # Catégorie
        if filters.get('categorie') and piece.categorie != filters['categorie']:
            return False
        
        # Type
        if filters.get('type_piece') and piece.type_piece != filters['type_piece']:
            return False
        
        # Statut
        if filters.get('statut') and piece.statut != filters['statut']:
            return False
        
        # Importance
        if filters.get('importance_min') and piece.importance < filters['importance_min']:
            return False
        if filters.get('importance_max') and piece.importance > filters['importance_max']:
            return False
        
        # Pertinence
        if filters.get('pertinence_min') and piece.pertinence < filters['pertinence_min']:
            return False
        
        # Dates
        if filters.get('date_debut') and piece.date_ajout < filters['date_debut']:
            return False
        if filters.get('date_fin') and piece.date_ajout > filters['date_fin']:
            return False
        
        # Dossier
        if filters.get('dossier_id') and piece.dossier_id != filters['dossier_id']:
            return False
        
        # Tags (au moins un doit matcher)
        if filters.get('tags'):
            if not any(tag in piece.tags for tag in filters['tags']):
                return False
        
        # Favoris
        if filters.get('favoris_only') and piece.id not in st.session_state.pieces_favoris:
            return False
        
        # Sélection
        if filters.get('selected_only') and piece.id not in st.session_state.pieces_selectionnees:
            return False
        
        return True
    
    # ==================== GESTION DE LA SÉLECTION ====================
    
    def get_pieces_selectionnees(self) -> List[PieceJuridique]:
        """Retourne les pièces sélectionnées triées par numéro"""
        pieces = list(st.session_state.pieces_selectionnees.values())
        return sorted(pieces, key=lambda p: p.numero_ordre)
    
    def get_pieces_par_categorie(self, selected_only: bool = False) -> Dict[str, List[PieceJuridique]]:
        """Retourne les pièces groupées par catégorie"""
        result = defaultdict(list)
        
        if selected_only:
            pieces = st.session_state.pieces_selectionnees.values()
        else:
            pieces = [p for p in st.session_state.pieces.values() if p.statut != 'supprimé']
        
        for piece in pieces:
            result[piece.categorie].append(piece)
        
        # Trier les pièces dans chaque catégorie
        for cat_pieces in result.values():
            cat_pieces.sort(key=lambda p: p.numero_ordre)
        
        return dict(result)
    
    def generer_bordereau(self, format_type: str = "detaille", 
                         pieces_ids: Optional[List[str]] = None) -> str:
        """Génère un bordereau de communication"""
        if pieces_ids:
            pieces = [self.get_piece(pid) for pid in pieces_ids if self.get_piece(pid)]
        else:
            pieces = self.get_pieces_selectionnees()
        
        if not pieces:
            return "Aucune pièce sélectionnée"
        
        lines = [
            "BORDEREAU DE COMMUNICATION DE PIÈCES",
            "=" * 60,
            f"Date : {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            f"Nombre de pièces : {len(pieces)}",
            "",
        ]
        
        # Grouper par catégorie
        pieces_par_cat = defaultdict(list)
        for piece in pieces:
            pieces_par_cat[piece.categorie].append(piece)
        
        # Afficher par catégorie
        for categorie in sorted(pieces_par_cat.keys()):
            cat_pieces = sorted(pieces_par_cat[categorie], key=lambda p: p.numero_ordre)
            cat_config = self.CATEGORIES_CONFIG.get(categorie, self.CATEGORIES_CONFIG['Autre'])
            
            lines.extend([
                "",
                f"{cat_config['icon']} {categorie.upper()} ({len(cat_pieces)} pièces)",
                "-" * 50,
            ])
            
            for piece in cat_pieces:
                if format_type == "detaille":
                    lines.extend([
                        f"Pièce n°{piece.numero_ordre} : {piece.nom}",
                        f"   Type : {piece.type_piece}",
                        f"   Source : {piece.source}" if piece.source else "",
                    ])
                    
                    if piece.description:
                        desc = piece.description[:150] + "..." if len(piece.description) > 150 else piece.description
                        lines.append(f"   Description : {desc}")
                    
                    if piece.pertinence >= 0.7:
                        lines.append(f"   Pertinence : Très élevée ({piece.pertinence:.0%})")
                    elif piece.pertinence >= 0.4:
                        lines.append(f"   Pertinence : Moyenne ({piece.pertinence:.0%})")
                    
                    if piece.notes:
                        lines.append(f"   Notes : {piece.notes}")
                    
                    if piece.tags:
                        lines.append(f"   Tags : {', '.join(piece.tags)}")
                    
                    if piece.date_document:
                        lines.append(f"   Date du document : {piece.date_document.strftime('%d/%m/%Y')}")
                    
                    lines.append("")
                    
                elif format_type == "simple":
                    lines.append(f"  {piece.numero_ordre}. {piece.nom} ({piece.type_piece})")
                
                elif format_type == "compact":
                    tags_str = f" [{', '.join(piece.tags[:3])}]" if piece.tags else ""
                    lines.append(f"  • {piece.nom}{tags_str}")
        
        # Résumé
        lines.extend([
            "",
            "RÉSUMÉ",
            "-" * 50,
        ])
        
        for categorie, pieces in pieces_par_cat.items():
            lines.append(f"  • {categorie} : {len(pieces)} pièces")
        
        return "\n".join(lines)
    
    # ==================== IMPORT/EXPORT ====================
    
    def exporter_pieces(self, piece_ids: Optional[List[str]] = None, 
                       format_export: str = 'json') -> Tuple[Any, str, str]:
        """Exporte les pièces dans différents formats"""
        # Sélectionner les pièces à exporter
        if piece_ids:
            pieces = [self.get_piece(pid) for pid in piece_ids if self.get_piece(pid)]
        else:
            pieces = self.get_pieces_selectionnees()
        
        if not pieces:
            pieces = [p for p in st.session_state.pieces.values() if p.statut != 'supprimé']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_export == 'json':
            # Export JSON complet
            data = {
                'export_date': datetime.now().isoformat(),
                'total_pieces': len(pieces),
                'pieces': []
            }
            
            for piece in pieces:
                piece_data = {
                    'id': piece.id,
                    'nom': piece.nom,
                    'type_piece': piece.type_piece,
                    'categorie': piece.categorie,
                    'numero_ordre': piece.numero_ordre,
                    'description': piece.description,
                    'source': piece.source,
                    'date_ajout': piece.date_ajout.isoformat(),
                    'date_document': piece.date_document.isoformat() if piece.date_document else None,
                    'tags': piece.tags,
                    'statut': piece.statut,
                    'importance': piece.importance,
                    'pertinence': piece.pertinence,
                    'notes': piece.notes,
                    'metadata': piece.metadata
                }
                data['pieces'].append(piece_data)
            
            content = json.dumps(data, ensure_ascii=False, indent=2)
            filename = f"pieces_export_{timestamp}.json"
            mime_type = "application/json"
        
        elif format_export == 'csv':
            # Export CSV
            rows = []
            for piece in pieces:
                rows.append({
                    'Numéro': piece.numero_ordre,
                    'Nom': piece.nom,
                    'Type': piece.type_piece,
                    'Catégorie': piece.categorie,
                    'Date': piece.date_document.strftime('%d/%m/%Y') if piece.date_document else '',
                    'Source': piece.source,
                    'Importance': piece.importance,
                    'Pertinence': f"{piece.pertinence:.0%}",
                    'Statut': self.STATUTS_CONFIG[piece.statut]['label'],
                    'Tags': ', '.join(piece.tags),
                    'Notes': piece.notes
                })
            
            df = pd.DataFrame(rows)
            content = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            filename = f"pieces_export_{timestamp}.csv"
            mime_type = "text/csv"
        
        elif format_export == 'excel':
            # Export Excel multi-feuilles
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Feuille principale des pièces
                pieces_data = []
                for piece in pieces:
                    pieces_data.append({
                        'N°': piece.numero_ordre,
                        'Nom': piece.nom,
                        'Type': piece.type_piece,
                        'Catégorie': piece.categorie,
                        'Date document': piece.date_document,
                        'Date ajout': piece.date_ajout,
                        'Source': piece.source,
                        'Importance': piece.importance,
                        'Pertinence': piece.pertinence,
                        'Statut': self.STATUTS_CONFIG[piece.statut]['label'],
                        'Tags': ', '.join(piece.tags),
                        'Notes': piece.notes,
                        'Description': piece.description or ''
                    })
                
                df_pieces = pd.DataFrame(pieces_data)
                df_pieces.to_excel(writer, sheet_name='Pièces', index=False)
                
                # Feuille de synthèse par catégorie
                synthese_data = []
                for cat, cat_pieces in self.get_pieces_par_categorie().items():
                    synthese_data.append({
                        'Catégorie': cat,
                        'Nombre': len(cat_pieces),
                        'Importance moyenne': sum(p.importance for p in cat_pieces) / len(cat_pieces) if cat_pieces else 0,
                        'Types': ', '.join(set(p.type_piece for p in cat_pieces))
                    })
                
                df_synthese = pd.DataFrame(synthese_data)
                df_synthese.to_excel(writer, sheet_name='Synthèse', index=False)
                
                # Feuille des tags
                tags_data = []
                for tag, count in self.get_all_tags():
                    tags_data.append({'Tag': tag, 'Occurrences': count})
                
                if tags_data:
                    df_tags = pd.DataFrame(tags_data)
                    df_tags.to_excel(writer, sheet_name='Tags', index=False)
                
                # Mise en forme
                workbook = writer.book
                for worksheet in writer.sheets.values():
                    worksheet.set_column('A:Z', 15)
            
            output.seek(0)
            content = output.getvalue()
            filename = f"pieces_export_{timestamp}.xlsx"
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        elif format_export == 'txt':
            # Export texte (bordereau détaillé)
            content = self.generer_bordereau("detaille", piece_ids)
            filename = f"bordereau_pieces_{timestamp}.txt"
            mime_type = "text/plain"
        
        else:
            raise ValueError(f"Format d'export non supporté : {format_export}")
        
        return content, filename, mime_type
    
    def importer_pieces_json(self, json_data: str) -> Dict[str, Any]:
        """Importe des pièces depuis un JSON"""
        try:
            data = json.loads(json_data)
            results = {'success': 0, 'failed': 0, 'errors': []}
            
            for piece_data in data.get('pieces', []):
                try:
                    # Recréer la pièce
                    piece = PieceJuridique(
                        nom=piece_data.get('nom', ''),
                        type_piece=piece_data.get('type_piece', 'Document'),
                        categorie=piece_data.get('categorie', 'Autre'),
                        numero_ordre=piece_data.get('numero_ordre', 1),
                        description=piece_data.get('description'),
                        source=piece_data.get('source', ''),
                        tags=piece_data.get('tags', []),
                        statut=piece_data.get('statut', 'actif'),
                        importance=piece_data.get('importance', 5),
                        pertinence=piece_data.get('pertinence', 0.5),
                        notes=piece_data.get('notes', ''),
                        metadata=piece_data.get('metadata', {})
                    )
                    
                    # Dates
                    if piece_data.get('date_document'):
                        piece.date_document = datetime.fromisoformat(piece_data['date_document'])
                    
                    self.ajouter_piece(piece)
                    results['success'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{piece_data.get('nom', 'Sans nom')}: {str(e)}")
            
            return results
            
        except json.JSONDecodeError as e:
            return {'success': 0, 'failed': 1, 'errors': [f"Erreur JSON : {str(e)}"]}
    
    # ==================== OPÉRATIONS GROUPÉES ====================
    
    def operations_groupees(self, piece_ids: List[str], operation: str, **params) -> Dict[str, Any]:
        """Effectue des opérations sur plusieurs pièces"""
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for piece_id in piece_ids:
            try:
                if operation == 'select':
                    self.selectionner_piece(piece_id, params.get('notes', ''))
                elif operation == 'deselect':
                    self.deselectionner_piece(piece_id)
                elif operation == 'delete':
                    self.supprimer_piece(piece_id, params.get('permanent', False))
                elif operation == 'archive':
                    self.modifier_piece(piece_id, statut='archivé', create_version=False)
                elif operation == 'restore':
                    self.modifier_piece(piece_id, statut='actif', create_version=False)
                elif operation == 'move':
                    self.deplacer_vers_dossier(piece_id, params.get('dossier_id'))
                elif operation == 'tag':
                    self.ajouter_tags(piece_id, params.get('tags', []))
                elif operation == 'untag':
                    self.retirer_tags(piece_id, params.get('tags', []))
                elif operation == 'importance':
                    self.modifier_piece(piece_id, importance=params.get('importance', 5))
                elif operation == 'categorie':
                    self.modifier_piece(piece_id, categorie=params.get('categorie'))
                
                results['success'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{piece_id}: {str(e)}")
        
        return results
    
    # ==================== TAGS ET FAVORIS ====================
    
    def ajouter_tags(self, piece_id: str, tags: List[str]):
        """Ajoute des tags à une pièce"""
        piece = self.get_piece(piece_id)
        if piece:
            # Normaliser les tags
            normalized_tags = [tag.strip().lower() for tag in tags if tag.strip()]
            
            # Ajouter les nouveaux tags
            piece.tags.extend(normalized_tags)
            piece.tags = list(set(piece.tags))  # Dédupliquer
            
            # Mettre à jour les tags globaux
            st.session_state.pieces_metadata['tags'].update(normalized_tags)
            
            self._add_to_history('add_tags', piece_id, {'tags': normalized_tags})
    
    def retirer_tags(self, piece_id: str, tags: List[str]):
        """Retire des tags d'une pièce"""
        piece = self.get_piece(piece_id)
        if piece:
            normalized_tags = [tag.strip().lower() for tag in tags]
            piece.tags = [t for t in piece.tags if t not in normalized_tags]
            self._add_to_history('remove_tags', piece_id, {'tags': normalized_tags})
    
    def get_all_tags(self) -> List[Tuple[str, int]]:
        """Retourne tous les tags avec leur fréquence"""
        tag_counter = Counter()
        for piece in st.session_state.pieces.values():
            if piece.statut != 'supprimé':
                tag_counter.update(piece.tags)
        return tag_counter.most_common()
    
    def toggle_favori(self, piece_id: str) -> bool:
        """Ajoute/retire une pièce des favoris"""
        if piece_id in st.session_state.pieces_favoris:
            st.session_state.pieces_favoris.remove(piece_id)
            self._add_to_history('unfavorite', piece_id, {})
            return False
        else:
            st.session_state.pieces_favoris.add(piece_id)
            self._add_to_history('favorite', piece_id, {})
            return True
    
    def get_favoris(self) -> List[PieceJuridique]:
        """Récupère toutes les pièces favorites"""
        return [self.get_piece(pid) for pid in st.session_state.pieces_favoris 
                if self.get_piece(pid) and self.get_piece(pid).statut != 'supprimé']
    
    # ==================== STATISTIQUES ====================
    
    def get_statistiques(self) -> Dict[str, Any]:
        """Calcule des statistiques détaillées"""
        pieces = [p for p in st.session_state.pieces.values() if p.statut != 'supprimé']
        pieces_selectionnees = list(st.session_state.pieces_selectionnees.values())
        
        if not pieces:
            return self._get_empty_stats()
        
        # Stats de base
        total = len(pieces)
        total_selectionne = len(pieces_selectionnees)
        
        # Par catégorie et type
        par_categorie = Counter(p.categorie for p in pieces)
        par_type = Counter(p.type_piece for p in pieces)
        par_statut = Counter(p.statut for p in pieces)
        
        # Sélection par catégorie
        selection_par_categorie = Counter(p.categorie for p in pieces_selectionnees)
        
        # Calculs moyens
        importance_moyenne = sum(p.importance for p in pieces) / total
        pertinence_moyenne = sum(p.pertinence for p in pieces) / total
        
        # Tailles
        taille_totale = sum(p.taille or 0 for p in pieces)
        pieces_avec_fichier = sum(1 for p in pieces if p.chemin_fichier)
        
        # Tags
        tags_populaires = self.get_all_tags()[:10]
        
        # Évolution temporelle
        evolution_mensuelle = defaultdict(int)
        for piece in pieces:
            mois = piece.date_ajout.strftime('%Y-%m')
            evolution_mensuelle[mois] += 1
        
        # Pièces récentes et importantes
        pieces_recentes = sorted(pieces, key=lambda p: p.date_ajout, reverse=True)[:10]
        pieces_importantes = sorted(pieces, key=lambda p: (p.importance, p.pertinence), reverse=True)[:10]
        
        return {
            'total': total,
            'total_selectionne': total_selectionne,
            'par_categorie': dict(par_categorie),
            'par_type': dict(par_type),
            'par_statut': dict(par_statut),
            'selection_par_categorie': dict(selection_par_categorie),
            'importance_moyenne': importance_moyenne,
            'pertinence_moyenne': pertinence_moyenne,
            'taille_totale': taille_totale,
            'taille_moyenne': taille_totale // total if total > 0 else 0,
            'pieces_avec_fichier': pieces_avec_fichier,
            'pieces_avec_notes': sum(1 for p in pieces if p.notes),
            'total_favoris': len(st.session_state.pieces_favoris),
            'tags_populaires': tags_populaires,
            'evolution_mensuelle': dict(evolution_mensuelle),
            'pieces_recentes': pieces_recentes,
            'pieces_importantes': pieces_importantes,
            'derniere_modification': st.session_state.pieces_metadata.get('last_modified')
        }
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques vides"""
        return {
            'total': 0, 'total_selectionne': 0, 'par_categorie': {}, 'par_type': {},
            'par_statut': {}, 'selection_par_categorie': {}, 'importance_moyenne': 0,
            'pertinence_moyenne': 0, 'taille_totale': 0, 'taille_moyenne': 0,
            'pieces_avec_fichier': 0, 'pieces_avec_notes': 0, 'total_favoris': 0,
            'tags_populaires': [], 'evolution_mensuelle': {}, 'pieces_recentes': [],
            'pieces_importantes': [], 'derniere_modification': None
        }
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def get_piece(self, piece_id: str) -> Optional[PieceJuridique]:
        """Récupère une pièce par son ID"""
        return st.session_state.pieces.get(piece_id)
    
    def get_pieces_dossier(self, dossier_id: str, include_archived: bool = False) -> List[PieceJuridique]:
        """Récupère les pièces d'un dossier"""
        piece_ids = st.session_state.pieces_par_dossier.get(dossier_id, [])
        pieces = []
        
        for pid in piece_ids:
            piece = self.get_piece(pid)
            if piece:
                if include_archived or piece.statut not in ['archivé', 'supprimé']:
                    pieces.append(piece)
        
        return sorted(pieces, key=lambda p: p.numero_ordre)
    
    def deplacer_vers_dossier(self, piece_id: str, nouveau_dossier_id: str):
        """Déplace une pièce vers un autre dossier"""
        piece = self.get_piece(piece_id)
        if not piece:
            return
        
        # Retirer de l'ancien dossier
        if piece.dossier_id:
            old_pieces = st.session_state.pieces_par_dossier.get(piece.dossier_id, [])
            if piece_id in old_pieces:
                old_pieces.remove(piece_id)
        
        # Ajouter au nouveau
        if nouveau_dossier_id:
            piece.dossier_id = nouveau_dossier_id
            if nouveau_dossier_id not in st.session_state.pieces_par_dossier:
                st.session_state.pieces_par_dossier[nouveau_dossier_id] = []
            st.session_state.pieces_par_dossier[nouveau_dossier_id].append(piece_id)
        else:
            piece.dossier_id = None
        
        self._add_to_history('move', piece_id, {'to_dossier': nouveau_dossier_id})
    
    def get_historique(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère l'historique des actions"""
        return st.session_state.pieces_history[-limit:]
    
    @staticmethod
    def calculer_hash_fichier(content: bytes) -> str:
        """Calcule le hash SHA-256 d'un fichier"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def formater_taille_fichier(size_bytes: Optional[int]) -> str:
        """Formate la taille d'un fichier"""
        if not size_bytes:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # ==================== MÉTHODES PRIVÉES ====================
    
    def _determiner_categorie(self, piece: PieceJuridique) -> str:
        """Détermine automatiquement la catégorie d'une pièce"""
        text_lower = (piece.nom + ' ' + piece.type_piece + ' ' + 
                     (piece.description or '') + ' ' + (piece.contenu_extrait or '')).lower()
        
        for categorie, config in self.CATEGORIES_CONFIG.items():
            if config['patterns']:
                for pattern in config['patterns']:
                    if pattern in text_lower:
                        return categorie
        
        return 'Autre'
    
    def _calculer_pertinence(self, piece: PieceJuridique, analysis: Dict[str, Any]) -> float:
        """Calcule la pertinence d'une pièce par rapport à une analyse"""
        score = 0.5  # Score de base
        
        # Analyse du contenu
        if analysis.get('subject_matter'):
            subject_words = set(analysis['subject_matter'].lower().split())
            piece_text = (piece.nom + ' ' + (piece.description or '') + ' ' + 
                         (piece.contenu_extrait or '')).lower()
            piece_words = set(piece_text.split())
            
            common_words = subject_words.intersection(piece_words)
            if subject_words:
                score += (len(common_words) / len(subject_words)) * 0.3
        
        # Référence exacte
        if analysis.get('reference'):
            ref_lower = analysis['reference'].lower()
            if ref_lower in piece.nom.lower():
                score += 0.25
            elif piece.description and ref_lower in piece.description.lower():
                score += 0.15
        
        # Fraîcheur
        if piece.date_document:
            age_days = (datetime.now() - piece.date_document).days
            if age_days < 30:
                score += 0.1
            elif age_days < 90:
                score += 0.05
        
        # Importance
        score += (piece.importance / 10) * 0.1
        
        return min(score, 1.0)
    
    def _renumeroter_pieces_selectionnees(self):
        """Renumérotation des pièces sélectionnées"""
        pieces = sorted(st.session_state.pieces_selectionnees.values(), 
                       key=lambda p: (p.categorie, p.date_ajout))
        
        for i, piece in enumerate(pieces, 1):
            piece.numero_ordre = i
    
    def _update_global_metadata(self, piece: PieceJuridique, action: str):
        """Met à jour les métadonnées globales"""
        metadata = st.session_state.pieces_metadata
        
        if action == 'add':
            if piece.taille:
                metadata['total_size'] += piece.taille
            metadata['categories_count'][piece.categorie] += 1
            metadata['types_count'][piece.type_piece] += 1
            if piece.tags:
                metadata['tags'].update(piece.tags)
        
        elif action == 'remove':
            if piece.taille:
                metadata['total_size'] = max(0, metadata['total_size'] - piece.taille)
            metadata['categories_count'][piece.categorie] -= 1
            metadata['types_count'][piece.type_piece] -= 1
        
        metadata['last_modified'] = datetime.now()
    
    def _add_to_history(self, action: str, piece_id: str, details: Dict[str, Any]):
        """Ajoute une action à l'historique"""
        entry = {
            'timestamp': datetime.now(),
            'action': action,
            'piece_id': piece_id,
            'details': details,
            'user': st.session_state.get('current_user', 'Utilisateur')
        }
        
        st.session_state.pieces_history.append(entry)
        
        # Limiter la taille
        if len(st.session_state.pieces_history) > 1000:
            st.session_state.pieces_history = st.session_state.pieces_history[-500:]

# ========================= INTERFACE UTILISATEUR =========================

def display_pieces_interface():
    """Interface principale de gestion des pièces"""
    
    # CSS personnalisé
    st.markdown("""
    <style>
    .piece-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .piece-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    .tag-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 15px;
        font-size: 0.85rem;
        background: #e3f2fd;
        color: #1976d2;
    }
    .importance-bar {
        height: 4px;
        border-radius: 2px;
        margin-top: 0.5rem;
    }
    .category-header {
        font-weight: bold;
        margin: 1rem 0 0.5rem 0;
        padding: 0.5rem;
        background: #f5f5f5;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📎 Gestion Unifiée des Pièces")
    
    gestionnaire = GestionnairePiecesUnifie()
    
    # Barre d'outils principale
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 1, 1])
    
    with col1:
        if st.button("➕ Nouvelle pièce", key="new_piece_btn", type="primary", use_container_width=True):
            st.session_state.show_add_piece_modal = True
    
    with col2:
        if st.button("📤 Import", key="import_btn", use_container_width=True):
            st.session_state.show_import_modal = True
    
    with col3:
        if st.button("⚡ Actions groupées", key="bulk_actions_btn", use_container_width=True):
            st.session_state.show_bulk_actions = True
    
    with col4:
        # Compteur de sélection UI
        selected_count = len(st.session_state.get('selected_pieces', []))
        if selected_count > 0:
            st.metric("UI", selected_count)
    
    with col5:
        # Compteur de sélection pour communication
        comm_count = len(st.session_state.pieces_selectionnees)
        if comm_count > 0:
            st.metric("Comm", comm_count)
    
    with col6:
        if st.button("🔄", key="refresh_pieces", help="Actualiser"):
            st.rerun()
    
    # Modales
    if st.session_state.get('show_add_piece_modal'):
        display_add_piece_modal(gestionnaire)
    
    if st.session_state.get('show_import_modal'):
        display_import_modal(gestionnaire)
    
    if st.session_state.get('show_bulk_actions'):
        display_bulk_actions_modal(gestionnaire)
    
    # Onglets principaux
    tabs = st.tabs([
        "📋 Vue d'ensemble",
        "✅ Sélection communication",
        "🔍 Recherche avancée",
        "⭐ Favoris",
        "📊 Statistiques",
        "📜 Historique",
        "⚙️ Configuration"
    ])
    
    with tabs[0]:
        display_pieces_overview(gestionnaire)
    
    with tabs[1]:
        display_selection_communication(gestionnaire)
    
    with tabs[2]:
        display_advanced_search(gestionnaire)
    
    with tabs[3]:
        display_favoris(gestionnaire)
    
    with tabs[4]:
        display_statistics_dashboard(gestionnaire)
    
    with tabs[5]:
        display_history(gestionnaire)
    
    with tabs[6]:
        display_settings(gestionnaire)

def display_pieces_overview(gestionnaire: GestionnairePiecesUnifie):
    """Vue d'ensemble avec filtres rapides"""
    
    # Filtres en ligne
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Recherche",
            placeholder="Nom, type, tag, description...",
            key="quick_search"
        )
    
    with col2:
        categories = ["Toutes"] + list(gestionnaire.CATEGORIES_CONFIG.keys())
        selected_categorie = st.selectbox("📁 Catégorie", categories, key="filter_cat")
    
    with col3:
        statuts = ["Tous"] + [s['label'] for s in gestionnaire.STATUTS_CONFIG.values()]
        selected_statut = st.selectbox("📌 Statut", statuts, key="filter_statut")
    
    with col4:
        sort_options = ["Date récente", "Nom A-Z", "Importance", "Pertinence", "Numéro"]
        sort_by = st.selectbox("🔀 Tri", sort_options, key="sort_by")
    
    with col5:
        view_mode = st.radio("Vue", ["📋", "🎴", "📊"], horizontal=True, label_visibility="collapsed")
    
    # Préparer les filtres
    filters = {}
    if selected_categorie != "Toutes":
        filters['categorie'] = selected_categorie
    if selected_statut != "Tous":
        statut_key = [k for k, v in gestionnaire.STATUTS_CONFIG.items() if v['label'] == selected_statut][0]
        filters['statut'] = statut_key
    
    # Rechercher
    pieces = gestionnaire.rechercher_pieces(search_query, filters)
    
    # Trier
    if sort_by == "Date récente":
        pieces.sort(key=lambda p: p.date_ajout, reverse=True)
    elif sort_by == "Nom A-Z":
        pieces.sort(key=lambda p: p.nom.lower())
    elif sort_by == "Importance":
        pieces.sort(key=lambda p: p.importance, reverse=True)
    elif sort_by == "Pertinence":
        pieces.sort(key=lambda p: p.pertinence, reverse=True)
    elif sort_by == "Numéro":
        pieces.sort(key=lambda p: p.numero_ordre)
    
    # Stats rapides
    if pieces:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(pieces))
        with col2:
            selectionnees = len([p for p in pieces if p.statut == 'sélectionné'])
            st.metric("Sélectionnées", selectionnees)
        with col3:
            avg_importance = sum(p.importance for p in pieces) / len(pieces)
            st.metric("Importance moy.", f"{avg_importance:.1f}/10")
        with col4:
            favoris = len([p for p in pieces if p.id in st.session_state.pieces_favoris])
            st.metric("Favoris", favoris)
    
    # Affichage selon le mode
    if view_mode == "📋":
        display_pieces_list_view(pieces, gestionnaire)
    elif view_mode == "🎴":
        display_pieces_cards_view(pieces, gestionnaire)
    else:
        display_pieces_table_view(pieces, gestionnaire)
    
    # Actions flottantes si sélection
    if st.session_state.get('selected_pieces'):
        display_floating_actions(gestionnaire)

def display_selection_communication(gestionnaire: GestionnairePiecesUnifie):
    """Interface de sélection pour communication de pièces"""
    
    st.markdown("### 📋 Sélection de pièces pour communication")
    
    # Colonnes principales
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("#### 📄 Pièces disponibles")
        
        # Recherche et filtres
        search = st.text_input("🔍 Filtrer", placeholder="Rechercher...", key="search_available")
        
        col1, col2 = st.columns(2)
        with col1:
            cat_filter = st.selectbox(
                "Catégorie",
                ["Toutes"] + list(gestionnaire.CATEGORIES_CONFIG.keys()),
                key="cat_filter_available"
            )
        with col2:
            importance_min = st.slider("Importance min", 1, 10, 1, key="imp_filter_available")
        
        # Préparer les filtres
        filters = {'statut': 'actif'}
        if cat_filter != "Toutes":
            filters['categorie'] = cat_filter
        filters['importance_min'] = importance_min
        
        # Rechercher les pièces
        available_pieces = gestionnaire.rechercher_pieces(search, filters)
        
        # Exclure les déjà sélectionnées
        available_pieces = [p for p in available_pieces if p.id not in st.session_state.pieces_selectionnees]
        
        # Afficher les pièces disponibles
        for piece in available_pieces[:20]:  # Limiter l'affichage
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
                    st.markdown(f"**{cat_config['icon']} {piece.nom}**")
                    
                    if piece.description:
                        st.caption(piece.description[:100] + "..." if len(piece.description) > 100 else piece.description)
                    
                    # Badges
                    badges = []
                    if piece.pertinence >= 0.7:
                        badges.append("🟢 Très pertinent")
                    elif piece.pertinence >= 0.4:
                        badges.append("🟡 Pertinent")
                    
                    if piece.importance >= 7:
                        badges.append("⭐ Important")
                    
                    if badges:
                        st.caption(" | ".join(badges))
                
                with col2:
                    if st.button("➕", key=f"add_comm_{piece.id}", help="Ajouter à la sélection"):
                        gestionnaire.selectionner_piece(piece.id)
                        st.rerun()
                
                st.divider()
        
        if len(available_pieces) > 20:
            st.info(f"... et {len(available_pieces) - 20} autres pièces")
    
    with col_right:
        st.markdown("#### ✅ Pièces sélectionnées")
        
        pieces_selectionnees = gestionnaire.get_pieces_selectionnees()
        
        if not pieces_selectionnees:
            st.info("Aucune pièce sélectionnée. Ajoutez des pièces depuis la colonne de gauche.")
        else:
            # Actions globales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Bordereau", key="gen_bordereau", use_container_width=True):
                    st.session_state.show_bordereau = True
            
            with col2:
                if st.button("📤 Exporter", key="export_selection", use_container_width=True):
                    st.session_state.show_export_selection = True
            
            with col3:
                if st.button("🗑️ Tout retirer", key="clear_selection", use_container_width=True):
                    for piece_id in list(st.session_state.pieces_selectionnees.keys()):
                        gestionnaire.deselectionner_piece(piece_id)
                    st.rerun()
            
            st.divider()
            
            # Grouper par catégorie
            pieces_par_cat = gestionnaire.get_pieces_par_categorie(selected_only=True)
            
            for categorie, pieces in pieces_par_cat.items():
                cat_config = gestionnaire.CATEGORIES_CONFIG[categorie]
                
                with st.expander(f"{cat_config['icon']} {categorie} ({len(pieces)} pièces)", expanded=True):
                    for piece in pieces:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"**#{piece.numero_ordre} - {piece.nom}**")
                                if piece.notes:
                                    st.caption(f"📝 {piece.notes}")
                            
                            with col2:
                                # Note rapide
                                note = st.text_input(
                                    "Note",
                                    value=piece.notes,
                                    key=f"note_{piece.id}",
                                    label_visibility="collapsed",
                                    placeholder="Note..."
                                )
                                if note != piece.notes:
                                    gestionnaire.modifier_piece(piece.id, notes=note)
                            
                            with col3:
                                if st.button("❌", key=f"remove_comm_{piece.id}", help="Retirer"):
                                    gestionnaire.deselectionner_piece(piece.id)
                                    st.rerun()
    
    # Modales
    if st.session_state.get('show_bordereau'):
        display_bordereau_modal(gestionnaire)
    
    if st.session_state.get('show_export_selection'):
        display_export_modal(gestionnaire, selection_only=True)

def display_pieces_list_view(pieces: List[PieceJuridique], gestionnaire: GestionnairePiecesUnifie):
    """Affichage en liste détaillée"""
    
    if not pieces:
        st.info("🔍 Aucune pièce trouvée")
        return
    
    for piece in pieces:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1.5, 1])
            
            with col1:
                # Checkbox pour sélection UI
                selected = st.checkbox(
                    "",
                    key=f"select_{piece.id}",
                    label_visibility="collapsed"
                )
                
                if selected:
                    if piece.id not in st.session_state.get('selected_pieces', []):
                        st.session_state.selected_pieces = st.session_state.get('selected_pieces', []) + [piece.id]
                else:
                    if piece.id in st.session_state.get('selected_pieces', []):
                        st.session_state.selected_pieces.remove(piece.id)
                
                st.caption(f"#{piece.numero_ordre}")
            
            with col2:
                # Infos principales
                cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
                statut_config = gestionnaire.STATUTS_CONFIG[piece.statut]
                
                col_title, col_icons = st.columns([10, 2])
                
                with col_title:
                    st.markdown(f"### {cat_config['icon']} {piece.nom}")
                
                with col_icons:
                    # Favoris
                    is_favori = piece.id in st.session_state.pieces_favoris
                    if st.button(
                        "⭐" if is_favori else "☆",
                        key=f"fav_{piece.id}",
                        help="Retirer des favoris" if is_favori else "Ajouter aux favoris"
                    ):
                        gestionnaire.toggle_favori(piece.id)
                        st.rerun()
                    
                    # Statut
                    st.caption(f"{statut_config['icon']} {statut_config['label']}")
                
                # Description et tags
                if piece.description:
                    st.caption(piece.description[:200] + "..." if len(piece.description) > 200 else piece.description)
                
                if piece.tags:
                    tags_html = "".join(f'<span class="tag-badge">{tag}</span>' for tag in piece.tags[:5])
                    if len(piece.tags) > 5:
                        tags_html += f'<span class="tag-badge">+{len(piece.tags)-5}</span>'
                    st.markdown(tags_html, unsafe_allow_html=True)
                
                # Barres de progression
                col_imp, col_pert = st.columns(2)
                
                with col_imp:
                    imp_color = "#4caf50" if piece.importance >= 7 else "#ff9800" if piece.importance >= 4 else "#f44336"
                    st.markdown(
                        f'<div style="font-size: 0.8em; color: #666;">Importance: {piece.importance}/10</div>'
                        f'<div class="importance-bar" style="background: linear-gradient(to right, {imp_color} {piece.importance*10}%, #e0e0e0 {piece.importance*10}%);"></div>',
                        unsafe_allow_html=True
                    )
                
                with col_pert:
                    pert_color = "#4caf50" if piece.pertinence >= 0.7 else "#ff9800" if piece.pertinence >= 0.4 else "#f44336"
                    st.markdown(
                        f'<div style="font-size: 0.8em; color: #666;">Pertinence: {piece.pertinence:.0%}</div>'
                        f'<div class="importance-bar" style="background: linear-gradient(to right, {pert_color} {piece.pertinence*100}%, #e0e0e0 {piece.pertinence*100}%);"></div>',
                        unsafe_allow_html=True
                    )
            
            with col3:
                # Métadonnées
                st.write(f"**{piece.type_piece}**")
                st.caption(f"📅 {piece.date_ajout.strftime('%d/%m/%Y à %H:%M')}")
                
                if piece.date_document:
                    st.caption(f"📄 Document du {piece.date_document.strftime('%d/%m/%Y')}")
                
                if piece.taille:
                    st.caption(f"📦 {gestionnaire.formater_taille_fichier(piece.taille)}")
                
                if piece.source:
                    st.caption(f"📍 {piece.source}")
                
                if piece.version > 1:
                    st.caption(f"📝 Version {piece.version}")
            
            with col4:
                # États et notes
                if piece.date_modification:
                    st.caption(f"Modifié le {piece.date_modification.strftime('%d/%m')}")
                
                if piece.notes:
                    with st.expander("📝 Notes"):
                        st.caption(piece.notes)
                
                if piece.pieces_liees:
                    st.caption(f"🔗 {len(piece.pieces_liees)} pièces liées")
                
                if piece.metadata.get('confidentiel'):
                    st.caption("🔒 Confidentiel")
            
            with col5:
                # Actions
                col_view, col_menu = st.columns(2)
                
                with col_view:
                    if st.button("👁️", key=f"view_{piece.id}", help="Détails"):
                        st.session_state.current_piece_id = piece.id
                        st.session_state.show_piece_detail = True
                
                with col_menu:
                    if st.button("⋮", key=f"menu_{piece.id}", help="Actions"):
                        st.session_state.show_piece_menu = piece.id
            
            # Menu contextuel
            if st.session_state.get('show_piece_menu') == piece.id:
                display_piece_context_menu(piece, gestionnaire)
            
            st.divider()
    
    # Modal de détail
    if st.session_state.get('show_piece_detail'):
        display_piece_detail_modal(gestionnaire)

def display_piece_context_menu(piece: PieceJuridique, gestionnaire: GestionnairePiecesUnifie):
    """Menu contextuel pour une pièce"""
    
    with st.container():
        cols = st.columns(6)
        
        # Ligne 1
        with cols[0]:
            if st.button("✏️ Éditer", key=f"edit_{piece.id}", use_container_width=True):
                st.session_state.edit_piece_id = piece.id
                st.session_state.show_edit_modal = True
                st.session_state.show_piece_menu = None
        
        with cols[1]:
            if piece.statut != 'sélectionné':
                if st.button("✅ Sélectionner", key=f"sel_{piece.id}", use_container_width=True):
                    gestionnaire.selectionner_piece(piece.id)
                    st.rerun()
            else:
                if st.button("❌ Désélectionner", key=f"desel_{piece.id}", use_container_width=True):
                    gestionnaire.deselectionner_piece(piece.id)
                    st.rerun()
        
        with cols[2]:
            if st.button("📋 Dupliquer", key=f"dup_{piece.id}", use_container_width=True):
                duplicate_piece(gestionnaire, piece)
                st.session_state.show_piece_menu = None
        
        with cols[3]:
            if st.button("🏷️ Tags", key=f"tags_{piece.id}", use_container_width=True):
                st.session_state.manage_tags_piece = piece.id
                st.session_state.show_piece_menu = None
        
        with cols[4]:
            if piece.statut == 'actif':
                if st.button("📦 Archiver", key=f"arch_{piece.id}", use_container_width=True):
                    gestionnaire.modifier_piece(piece.id, statut='archivé')
                    st.rerun()
            else:
                if st.button("♻️ Restaurer", key=f"rest_{piece.id}", use_container_width=True):
                    gestionnaire.modifier_piece(piece.id, statut='actif')
                    st.rerun()
        
        with cols[5]:
            if st.button("🗑️ Supprimer", key=f"del_{piece.id}", use_container_width=True):
                if st.checkbox("Confirmer", key=f"confirm_del_{piece.id}"):
                    gestionnaire.supprimer_piece(piece.id, permanent=True)
                    st.rerun()

def display_add_piece_modal(gestionnaire: GestionnairePiecesUnifie):
    """Modal d'ajout de pièce"""
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("## ➕ Ajouter une nouvelle pièce")
        with col2:
            if st.button("❌ Fermer", key="close_add_modal"):
                st.session_state.show_add_piece_modal = False
                st.rerun()
        
        # Formulaire
        with st.form("add_piece_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input(
                    "Nom de la pièce *",
                    placeholder="Ex: Contrat de vente du 15/03/2024"
                )
                
                categorie = st.selectbox(
                    "Catégorie *",
                    list(gestionnaire.CATEGORIES_CONFIG.keys())
                )
                
                type_piece = st.selectbox(
                    "Type de pièce *",
                    gestionnaire.CATEGORIES_CONFIG[categorie]['types']
                )
                
                importance = st.slider("Importance", 1, 10, 5)
            
            with col2:
                source = st.text_input(
                    "Source",
                    placeholder="Ex: Dossier client, Email du 15/03..."
                )
                
                date_document = st.date_input(
                    "Date du document",
                    value=None
                )
                
                dossier = st.selectbox(
                    "Dossier",
                    ["Aucun"] + list(st.session_state.get('dossiers', {}).keys())
                )
                
                auto_select = st.checkbox(
                    "Sélectionner automatiquement pour communication"
                )
            
            # Description
            description = st.text_area(
                "Description",
                placeholder="Description détaillée...",
                height=100
            )
            
            # Tags
            tags_input = st.text_input(
                "Tags (séparés par des virgules)",
                placeholder="contrat, important, urgent"
            )
            
            # Métadonnées avancées
            with st.expander("⚙️ Options avancées"):
                col1, col2 = st.columns(2)
                
                with col1:
                    is_confidentiel = st.checkbox("🔒 Confidentiel")
                    pertinence = st.slider("Pertinence initiale", 0.0, 1.0, 0.5)
                
                with col2:
                    notes = st.text_area(
                        "Notes internes",
                        placeholder="Notes pour la communication..."
                    )
            
            # Bouton de soumission
            submitted = st.form_submit_button(
                "✅ Créer la pièce",
                use_container_width=True,
                type="primary"
            )
            
            if submitted and nom:
                try:
                    # Créer la pièce
                    piece = PieceJuridique(
                        nom=nom,
                        type_piece=type_piece,
                        categorie=categorie,
                        description=description,
                        source=source,
                        importance=importance,
                        pertinence=pertinence,
                        notes=notes,
                        tags=[t.strip() for t in tags_input.split(',') if t.strip()]
                    )
                    
                    if date_document:
                        piece.date_document = datetime.combine(date_document, datetime.min.time())
                    
                    if is_confidentiel:
                        piece.metadata['confidentiel'] = True
                    
                    # Ajouter la pièce
                    dossier_id = None if dossier == "Aucun" else dossier
                    piece_id = gestionnaire.ajouter_piece(piece, dossier_id, auto_select)
                    
                    st.success(f"✅ Pièce '{nom}' créée avec succès!")
                    st.balloons()
                    
                    # Fermer après délai
                    import time
                    time.sleep(1.5)
                    st.session_state.show_add_piece_modal = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

def display_bordereau_modal(gestionnaire: GestionnairePiecesUnifie):
    """Modal de génération de bordereau"""
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("## 📊 Générer un bordereau")
        with col2:
            if st.button("❌ Fermer", key="close_bordereau"):
                st.session_state.show_bordereau = False
                st.rerun()
        
        # Options
        col1, col2 = st.columns(2)
        
        with col1:
            format_type = st.radio(
                "Format",
                ["detaille", "simple", "compact"],
                format_func=lambda x: {
                    "detaille": "Détaillé (avec descriptions)",
                    "simple": "Simple (liste numérotée)",
                    "compact": "Compact (titres uniquement)"
                }[x]
            )
        
        with col2:
            pieces_selectionnees = gestionnaire.get_pieces_selectionnees()
            st.metric("Pièces sélectionnées", len(pieces_selectionnees))
        
        # Aperçu
        st.markdown("### 📄 Aperçu")
        
        bordereau = gestionnaire.generer_bordereau(format_type)
        st.text_area("", bordereau, height=400, disabled=True)
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "💾 Télécharger TXT",
                bordereau,
                f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                use_container_width=True
            )
        
        with col2:
            # Copier dans le presse-papier
            if st.button("📋 Copier", use_container_width=True):
                st.write("Contenu copié! (utilisez Ctrl+C)")
                st.code(bordereau)
        
        with col3:
            if st.button("📧 Envoyer", use_container_width=True):
                st.info("Fonction d'envoi à implémenter")

def display_statistics_dashboard(gestionnaire: GestionnairePiecesUnifie):
    """Tableau de bord des statistiques"""
    
    stats = gestionnaire.get_statistiques()
    
    if stats['total'] == 0:
        st.info("Aucune pièce enregistrée. Commencez par ajouter des pièces.")
        return
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total pièces",
            stats['total'],
            f"{stats['total_selectionne']} sélectionnées"
        )
    
    with col2:
        st.metric(
            "Importance moyenne",
            f"{stats['importance_moyenne']:.1f}/10",
            delta=None
        )
    
    with col3:
        st.metric(
            "Pertinence moyenne",
            f"{stats['pertinence_moyenne']:.0%}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Taille totale",
            gestionnaire.formater_taille_fichier(stats['taille_totale']),
            f"{stats['pieces_avec_fichier']} fichiers"
        )
    
    # Graphiques
    st.markdown("### 📊 Visualisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution par catégorie
        if stats['par_categorie']:
            st.markdown("#### Distribution par catégorie")
            
            # Créer un graphique simple avec Streamlit
            categories = list(stats['par_categorie'].keys())
            valeurs = list(stats['par_categorie'].values())
            
            # Barres horizontales
            for cat, val in zip(categories, valeurs):
                cat_config = gestionnaire.CATEGORIES_CONFIG.get(cat, gestionnaire.CATEGORIES_CONFIG['Autre'])
                col_icon, col_bar, col_val = st.columns([1, 8, 1])
                
                with col_icon:
                    st.write(cat_config['icon'])
                with col_bar:
                    st.progress(val / max(valeurs))
                with col_val:
                    st.write(str(val))
    
    with col2:
        # Top tags
        if stats['tags_populaires']:
            st.markdown("#### Tags populaires")
            
            for tag, count in stats['tags_populaires'][:10]:
                col_tag, col_count = st.columns([4, 1])
                with col_tag:
                    st.write(f"🏷️ {tag}")
                with col_count:
                    st.write(str(count))
    
    # Évolution temporelle
    if stats['evolution_mensuelle']:
        st.markdown("### 📈 Évolution mensuelle")
        
        mois = list(stats['evolution_mensuelle'].keys())
        valeurs = list(stats['evolution_mensuelle'].values())
        
        # Graphique simple
        st.bar_chart(dict(zip(mois[-12:], valeurs[-12:])))  # 12 derniers mois
    
    # Pièces importantes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌟 Pièces les plus importantes")
        for piece in stats['pieces_importantes'][:5]:
            cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
            st.write(f"{cat_config['icon']} **{piece.nom}**")
            st.caption(f"Importance: {piece.importance}/10 | Pertinence: {piece.pertinence:.0%}")
    
    with col2:
        st.markdown("### 🕐 Pièces récentes")
        for piece in stats['pieces_recentes'][:5]:
            cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
            st.write(f"{cat_config['icon']} **{piece.nom}**")
            st.caption(f"Ajoutée le {piece.date_ajout.strftime('%d/%m/%Y à %H:%M')}")

def duplicate_piece(gestionnaire: GestionnairePiecesUnifie, piece: PieceJuridique):
    """Duplique une pièce"""
    try:
        new_piece = PieceJuridique(
            nom=f"{piece.nom} (copie)",
            type_piece=piece.type_piece,
            categorie=piece.categorie,
            description=piece.description,
            source=piece.source,
            tags=piece.tags.copy(),
            importance=piece.importance,
            pertinence=piece.pertinence,
            notes="",
            metadata=piece.metadata.copy()
        )
        
        gestionnaire.ajouter_piece(new_piece, piece.dossier_id)
        st.success(f"✅ Pièce dupliquée avec succès!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")

# Fonctions additionnelles à implémenter :
# - display_pieces_cards_view
# - display_pieces_table_view
# - display_advanced_search
# - display_favoris
# - display_history
# - display_settings
# - display_import_modal
# - display_bulk_actions_modal
# - display_piece_detail_modal
# - display_floating_actions
# - display_export_modal

# Ces fonctions suivraient le même pattern que celles déjà implémentées

def display_pieces_cards_view(pieces: List[PieceJuridique], gestionnaire: GestionnairePiecesUnifie):
    """Affichage en cartes visuelles"""
    
    if not pieces:
        st.info("🔍 Aucune pièce trouvée")
        return
    
    # Grille de cartes
    cols_per_row = 3
    for i in range(0, len(pieces), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(pieces):
                piece = pieces[i + j]
                
                with col:
                    with st.container():
                        # Style de carte avec bordure colorée selon la catégorie
                        cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
                        statut_config = gestionnaire.STATUTS_CONFIG[piece.statut]
                        
                        st.markdown(
                            f"""
                            <div style="border: 2px solid {cat_config['color']}; 
                                        border-radius: 10px; padding: 15px; 
                                        background-color: white; height: 100%;">
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # En-tête
                        col_icon, col_title, col_fav = st.columns([1, 8, 1])
                        
                        with col_icon:
                            st.markdown(f"<h2>{cat_config['icon']}</h2>", unsafe_allow_html=True)
                        
                        with col_title:
                            st.markdown(f"**{piece.nom}**")
                            st.caption(f"{piece.type_piece} - #{piece.numero_ordre}")
                        
                        with col_fav:
                            is_favori = piece.id in st.session_state.pieces_favoris
                            if st.button(
                                "⭐" if is_favori else "☆",
                                key=f"fav_card_{piece.id}"
                            ):
                                gestionnaire.toggle_favori(piece.id)
                                st.rerun()
                        
                        # Corps
                        if piece.description:
                            st.caption(piece.description[:100] + "..." if len(piece.description) > 100 else piece.description)
                        
                        # Badges
                        badges = []
                        badges.append(f"{statut_config['icon']} {statut_config['label']}")
                        
                        if piece.importance >= 7:
                            badges.append("⭐ Important")
                        
                        if piece.pertinence >= 0.7:
                            badges.append("🎯 Très pertinent")
                        
                        st.caption(" | ".join(badges))
                        
                        # Tags (limités)
                        if piece.tags:
                            tags_str = ", ".join(piece.tags[:3])
                            if len(piece.tags) > 3:
                                tags_str += f" +{len(piece.tags)-3}"
                            st.caption(f"🏷️ {tags_str}")
                        
                        # Métadonnées
                        st.caption(f"📅 {piece.date_ajout.strftime('%d/%m/%Y')}")
                        
                        if piece.taille:
                            st.caption(f"📦 {gestionnaire.formater_taille_fichier(piece.taille)}")
                        
                        # Actions
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("👁️", key=f"view_card_{piece.id}", use_container_width=True):
                                st.session_state.current_piece_id = piece.id
                                st.session_state.show_piece_detail = True
                        
                        with col2:
                            if piece.statut != 'sélectionné':
                                if st.button("✅", key=f"sel_card_{piece.id}", use_container_width=True):
                                    gestionnaire.selectionner_piece(piece.id)
                                    st.rerun()
                            else:
                                if st.button("❌", key=f"desel_card_{piece.id}", use_container_width=True):
                                    gestionnaire.deselectionner_piece(piece.id)
                                    st.rerun()
                        
                        with col3:
                            if st.button("⋮", key=f"menu_card_{piece.id}", use_container_width=True):
                                st.session_state.show_piece_menu = piece.id
                        
                        # Menu contextuel dans la carte
                        if st.session_state.get('show_piece_menu') == piece.id:
                            display_piece_context_menu(piece, gestionnaire)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # Modal de détail
    if st.session_state.get('show_piece_detail'):
        display_piece_detail_modal(gestionnaire)

def display_pieces_table_view(pieces: List[PieceJuridique], gestionnaire: GestionnairePiecesUnifie):
    """Affichage en tableau"""
    
    if not pieces:
        st.info("🔍 Aucune pièce trouvée")
        return
    
    # Préparer les données pour le DataFrame
    data = []
    for piece in pieces:
        cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
        statut_config = gestionnaire.STATUTS_CONFIG[piece.statut]
        
        data.append({
            'Sél.': '☑️' if piece.id in st.session_state.get('selected_pieces', []) else '☐',
            'N°': piece.numero_ordre,
            'Cat.': cat_config['icon'],
            'Nom': piece.nom,
            'Type': piece.type_piece,
            'Statut': f"{statut_config['icon']} {statut_config['label']}",
            'Importance': f"{piece.importance}/10",
            'Pertinence': f"{piece.pertinence:.0%}",
            'Date': piece.date_ajout.strftime('%d/%m/%Y'),
            'Tags': ', '.join(piece.tags[:3]) + (f' +{len(piece.tags)-3}' if len(piece.tags) > 3 else ''),
            'Taille': gestionnaire.formater_taille_fichier(piece.taille) if piece.taille else '-',
            'Notes': '📝' if piece.notes else '',
            'Fav.': '⭐' if piece.id in st.session_state.pieces_favoris else '',
            'ID': piece.id
        })
    
    # Créer le DataFrame
    df = pd.DataFrame(data)
    
    # Configuration de l'affichage
    st.dataframe(
        df[['Sél.', 'N°', 'Cat.', 'Nom', 'Type', 'Statut', 'Importance', 
            'Pertinence', 'Date', 'Tags', 'Taille', 'Notes', 'Fav.']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'N°': st.column_config.NumberColumn(width='small'),
            'Cat.': st.column_config.TextColumn(width='small'),
            'Importance': st.column_config.TextColumn(width='small'),
            'Pertinence': st.column_config.TextColumn(width='small'),
            'Taille': st.column_config.TextColumn(width='small'),
            'Notes': st.column_config.TextColumn(width='small'),
            'Fav.': st.column_config.TextColumn(width='small')
        }
    )
    
    # Actions sur sélection
    st.markdown("### Actions rapides")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        piece_id = st.selectbox(
            "Pièce",
            options=[p['ID'] for p in data],
            format_func=lambda x: next(p['Nom'] for p in data if p['ID'] == x),
            key="quick_action_piece"
        )
    
    with col2:
        if st.button("👁️ Voir", key="quick_view", use_container_width=True):
            st.session_state.current_piece_id = piece_id
            st.session_state.show_piece_detail = True
    
    with col3:
        if st.button("✏️ Éditer", key="quick_edit", use_container_width=True):
            st.session_state.edit_piece_id = piece_id
            st.session_state.show_edit_modal = True
    
    with col4:
        piece = gestionnaire.get_piece(piece_id)
        if piece and piece.statut != 'sélectionné':
            if st.button("✅ Sélectionner", key="quick_select", use_container_width=True):
                gestionnaire.selectionner_piece(piece_id)
                st.rerun()
        else:
            if st.button("❌ Désélectionner", key="quick_deselect", use_container_width=True):
                gestionnaire.deselectionner_piece(piece_id)
                st.rerun()
    
    with col5:
        is_fav = piece_id in st.session_state.pieces_favoris
        if st.button("⭐" if is_fav else "☆ Favori", key="quick_fav", use_container_width=True):
            gestionnaire.toggle_favori(piece_id)
            st.rerun()
    
    # Modales
    if st.session_state.get('show_piece_detail'):
        display_piece_detail_modal(gestionnaire)
    
    if st.session_state.get('show_edit_modal'):
        display_edit_piece_modal(gestionnaire)

def display_advanced_search(gestionnaire: GestionnairePiecesUnifie):
    """Interface de recherche avancée"""
    
    st.markdown("### 🔍 Recherche avancée")
    
    # Formulaire de recherche
    with st.form("advanced_search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Recherche textuelle
            query = st.text_input(
                "Recherche textuelle",
                placeholder="Mots-clés dans nom, description, tags..."
            )
            
            # Catégories
            categories = st.multiselect(
                "Catégories",
                list(gestionnaire.CATEGORIES_CONFIG.keys())
            )
            
            # Types
            if categories:
                all_types = []
                for cat in categories:
                    all_types.extend(gestionnaire.CATEGORIES_CONFIG[cat]['types'])
                types = st.multiselect("Types de pièces", list(set(all_types)))
            else:
                types = []
        
        with col2:
            # Statuts
            statuts = st.multiselect(
                "Statuts",
                list(gestionnaire.STATUTS_CONFIG.keys()),
                format_func=lambda x: gestionnaire.STATUTS_CONFIG[x]['label']
            )
            
            # Importance
            importance_range = st.slider(
                "Importance",
                1, 10, (1, 10),
                help="Plage d'importance"
            )
            
            # Pertinence
            pertinence_min = st.slider(
                "Pertinence minimale",
                0.0, 1.0, 0.0,
                format="%.0%%"
            )
        
        with col3:
            # Dates
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                date_debut = st.date_input("Date début", value=None)
            with col_date2:
                date_fin = st.date_input("Date fin", value=None)
            
            # Tags
            all_tags = [tag for tag, _ in gestionnaire.get_all_tags()]
            selected_tags = st.multiselect("Tags", all_tags)
            
            # Options
            include_archived = st.checkbox("Inclure les pièces archivées")
            favoris_only = st.checkbox("Favoris uniquement")
            selected_only = st.checkbox("Pièces sélectionnées uniquement")
        
        # Bouton de recherche
        submitted = st.form_submit_button("🔍 Rechercher", use_container_width=True, type="primary")
    
    # Exécuter la recherche
    if submitted or query or categories or types or statuts or selected_tags:
        # Construire les filtres
        filters = {}
        
        if categories:
            filters['categorie'] = categories[0] if len(categories) == 1 else None
        
        if types:
            filters['type_piece'] = types[0] if len(types) == 1 else None
        
        if statuts:
            filters['statut'] = statuts[0] if len(statuts) == 1 else None
        
        filters['importance_min'] = importance_range[0]
        filters['importance_max'] = importance_range[1]
        filters['pertinence_min'] = pertinence_min
        
        if date_debut:
            filters['date_debut'] = datetime.combine(date_debut, datetime.min.time())
        if date_fin:
            filters['date_fin'] = datetime.combine(date_fin, datetime.max.time())
        
        if selected_tags:
            filters['tags'] = selected_tags
        
        filters['include_archived'] = include_archived
        filters['favoris_only'] = favoris_only
        filters['selected_only'] = selected_only
        
        # Rechercher
        results = gestionnaire.rechercher_pieces(query, filters)
        
        # Afficher les résultats
        st.markdown(f"### 📊 Résultats ({len(results)} pièces trouvées)")
        
        if results:
            # Options d'affichage
            col1, col2, col3 = st.columns([1, 1, 3])
            
            with col1:
                view_mode = st.radio(
                    "Affichage",
                    ["Liste", "Cartes", "Tableau"],
                    horizontal=True
                )
            
            with col2:
                if st.button("📤 Exporter résultats", key="export_search_results"):
                    st.session_state.export_pieces = [p.id for p in results]
                    st.session_state.show_export_modal = True
            
            with col3:
                if st.button("✅ Sélectionner tous les résultats", key="select_all_results"):
                    for piece in results:
                        if piece.statut != 'sélectionné':
                            gestionnaire.selectionner_piece(piece.id)
                    st.rerun()
            
            # Afficher selon le mode choisi
            if view_mode == "Liste":
                display_pieces_list_view(results, gestionnaire)
            elif view_mode == "Cartes":
                display_pieces_cards_view(results, gestionnaire)
            else:
                display_pieces_table_view(results, gestionnaire)
        else:
            st.info("Aucune pièce ne correspond aux critères de recherche.")
    
    # Modal d'export
    if st.session_state.get('show_export_modal'):
        display_export_modal(gestionnaire)

def display_favoris(gestionnaire: GestionnairePiecesUnifie):
    """Affichage des pièces favorites"""
    
    st.markdown("### ⭐ Pièces favorites")
    
    favoris = gestionnaire.get_favoris()
    
    if not favoris:
        st.info("Aucune pièce favorite. Ajoutez des pièces en favoris en cliquant sur l'étoile ⭐")
        return
    
    # Options d'affichage
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        sort_by = st.selectbox(
            "Trier par",
            ["Date d'ajout", "Nom", "Importance", "Catégorie"],
            key="sort_favoris"
        )
    
    with col2:
        filter_cat = st.selectbox(
            "Filtrer par catégorie",
            ["Toutes"] + list(set(p.categorie for p in favoris)),
            key="filter_cat_favoris"
        )
    
    with col3:
        if st.button("🗑️ Vider", key="clear_favoris"):
            if st.checkbox("Confirmer", key="confirm_clear_favoris"):
                st.session_state.pieces_favoris.clear()
                st.rerun()
    
    # Filtrer
    if filter_cat != "Toutes":
        favoris = [p for p in favoris if p.categorie == filter_cat]
    
    # Trier
    if sort_by == "Date d'ajout":
        favoris.sort(key=lambda p: p.date_ajout, reverse=True)
    elif sort_by == "Nom":
        favoris.sort(key=lambda p: p.nom.lower())
    elif sort_by == "Importance":
        favoris.sort(key=lambda p: p.importance, reverse=True)
    elif sort_by == "Catégorie":
        favoris.sort(key=lambda p: (p.categorie, p.nom))
    
    # Affichage en grille de cartes compactes
    cols_per_row = 2
    for i in range(0, len(favoris), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(favoris):
                piece = favoris[i + j]
                
                with col:
                    with st.container():
                        cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
                        
                        # Carte compacte
                        st.markdown(
                            f"""
                            <div style="background: #f8f9fa; padding: 15px; 
                                        border-radius: 10px; border-left: 4px solid {cat_config['color']};">
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # En-tête
                        col_icon, col_info, col_action = st.columns([1, 8, 1])
                        
                        with col_icon:
                            st.markdown(f"<h3>{cat_config['icon']}</h3>", unsafe_allow_html=True)
                        
                        with col_info:
                            st.markdown(f"**{piece.nom}**")
                            st.caption(f"{piece.type_piece} • Importance: {piece.importance}/10")
                            
                            if piece.tags:
                                st.caption(f"🏷️ {', '.join(piece.tags[:3])}")
                        
                        with col_action:
                            if st.button("⭐", key=f"unfav_{piece.id}", help="Retirer des favoris"):
                                gestionnaire.toggle_favori(piece.id)
                                st.rerun()
                        
                        # Actions rapides
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("👁️ Voir", key=f"view_fav_{piece.id}", use_container_width=True):
                                st.session_state.current_piece_id = piece.id
                                st.session_state.show_piece_detail = True
                        
                        with col2:
                            if piece.statut != 'sélectionné':
                                if st.button("✅ Sélect.", key=f"sel_fav_{piece.id}", use_container_width=True):
                                    gestionnaire.selectionner_piece(piece.id)
                                    st.rerun()
                            else:
                                st.button("☑️ Sélect.", key=f"selected_fav_{piece.id}", disabled=True, use_container_width=True)
                        
                        with col3:
                            if st.button("📋 Copier", key=f"dup_fav_{piece.id}", use_container_width=True):
                                duplicate_piece(gestionnaire, piece)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # Modal de détail
    if st.session_state.get('show_piece_detail'):
        display_piece_detail_modal(gestionnaire)

def display_history(gestionnaire: GestionnairePiecesUnifie):
    """Affichage de l'historique des actions"""
    
    st.markdown("### 📜 Historique des actions")
    
    # Options
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        limit = st.selectbox(
            "Nombre d'entrées",
            [50, 100, 200, 500],
            key="history_limit"
        )
    
    with col2:
        action_filter = st.selectbox(
            "Filtrer par action",
            ["Toutes", "add", "update", "delete", "select", "deselect", "archive", "favorite"],
            key="history_action_filter"
        )
    
    with col3:
        if st.button("🗑️ Effacer", key="clear_history"):
            if st.checkbox("Confirmer", key="confirm_clear_history"):
                st.session_state.pieces_history.clear()
                st.rerun()
    
    # Récupérer l'historique
    history = gestionnaire.get_historique(limit)
    
    # Filtrer si nécessaire
    if action_filter != "Toutes":
        history = [h for h in history if h['action'] == action_filter]
    
    if not history:
        st.info("Aucune action dans l'historique")
        return
    
    # Affichage
    for entry in reversed(history):  # Plus récent en premier
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 3])
            
            with col1:
                st.caption(entry['timestamp'].strftime('%d/%m/%Y %H:%M:%S'))
            
            with col2:
                # Icône selon l'action
                action_icons = {
                    'add': '➕',
                    'update': '✏️',
                    'delete': '🗑️',
                    'delete_permanent': '💀',
                    'select': '✅',
                    'deselect': '❌',
                    'archive': '📦',
                    'restore': '♻️',
                    'favorite': '⭐',
                    'unfavorite': '☆',
                    'move': '📁',
                    'add_tags': '🏷️',
                    'remove_tags': '🏷️❌'
                }
                
                icon = action_icons.get(entry['action'], '❓')
                st.write(f"{icon} **{entry['action']}**")
            
            with col3:
                # Détails de l'action
                details = entry.get('details', {})
                if details.get('nom'):
                    st.caption(f"Pièce: {details['nom']}")
                elif details.get('tags'):
                    st.caption(f"Tags: {', '.join(details['tags'])}")
                elif details.get('to_dossier'):
                    st.caption(f"Vers: {details['to_dossier']}")
                else:
                    st.caption(str(details))
            
            st.divider()

def display_settings(gestionnaire: GestionnairePiecesUnifie):
    """Paramètres et configuration"""
    
    st.markdown("### ⚙️ Paramètres")
    
    # Onglets de configuration
    tab1, tab2, tab3, tab4 = st.tabs(["Général", "Catégories", "Import/Export", "Maintenance"])
    
    with tab1:
        st.markdown("#### Paramètres généraux")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Préférences d'affichage
            st.markdown("##### Affichage")
            
            default_view = st.selectbox(
                "Vue par défaut",
                ["Liste", "Cartes", "Tableau"],
                key="settings_default_view"
            )
            
            items_per_page = st.number_input(
                "Éléments par page",
                min_value=10,
                max_value=100,
                value=20,
                step=10,
                key="settings_items_per_page"
            )
            
            show_archived = st.checkbox(
                "Afficher les pièces archivées par défaut",
                key="settings_show_archived"
            )
        
        with col2:
            # Paramètres de sélection
            st.markdown("##### Sélection")
            
            auto_select_important = st.checkbox(
                "Sélectionner automatiquement les pièces importantes (≥8/10)",
                key="settings_auto_select_important"
            )
            
            auto_select_pertinent = st.checkbox(
                "Sélectionner automatiquement les pièces très pertinentes (≥70%)",
                key="settings_auto_select_pertinent"
            )
            
            confirm_delete = st.checkbox(
                "Demander confirmation pour les suppressions",
                value=True,
                key="settings_confirm_delete"
            )
    
    with tab2:
        st.markdown("#### Gestion des catégories")
        
        # Afficher les catégories actuelles
        for cat_name, cat_config in gestionnaire.CATEGORIES_CONFIG.items():
            with st.expander(f"{cat_config['icon']} {cat_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Types de pièces:**")
                    for type_piece in cat_config['types']:
                        st.write(f"• {type_piece}")
                
                with col2:
                    st.write("**Mots-clés de détection:**")
                    for pattern in cat_config['patterns'][:5]:
                        st.write(f"• {pattern}")
                    if len(cat_config['patterns']) > 5:
                        st.caption(f"... et {len(cat_config['patterns'])-5} autres")
        
        # Ajouter une catégorie personnalisée
        st.markdown("##### Ajouter une catégorie")
        
        with st.form("add_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_cat_name = st.text_input("Nom de la catégorie")
                new_cat_icon = st.selectbox(
                    "Icône",
                    ["📁", "📎", "📌", "🗂️", "🗃️", "🗄️", "📂", "📑"]
                )
            
            with col2:
                new_cat_types = st.text_area(
                    "Types de pièces (un par ligne)",
                    height=100
                )
                new_cat_color = st.color_picker("Couleur", "#808080")
            
            if st.form_submit_button("Ajouter la catégorie"):
                st.info("Fonction à implémenter : ajout de catégorie personnalisée")
    
    with tab3:
        st.markdown("#### Import/Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Export des données")
            
            export_format = st.selectbox(
                "Format d'export",
                ["JSON", "CSV", "Excel", "TXT (Bordereau)"],
                key="settings_export_format"
            )
            
            include_in_export = st.multiselect(
                "Inclure dans l'export",
                ["Pièces actives", "Pièces archivées", "Pièces supprimées", "Historique", "Statistiques"],
                default=["Pièces actives"]
            )
            
            if st.button("📤 Exporter toutes les données", key="export_all_data"):
                try:
                    content, filename, mime_type = gestionnaire.exporter_pieces(
                        format_export=export_format.lower().replace(" (bordereau)", "")
                    )
                    
                    st.download_button(
                        f"💾 Télécharger {filename}",
                        content if isinstance(content, bytes) else content.encode('utf-8'),
                        filename,
                        mime_type
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'export : {str(e)}")
        
        with col2:
            st.markdown("##### Import de données")
            
            uploaded_file = st.file_uploader(
                "Importer un fichier",
                type=['json', 'csv', 'xlsx'],
                key="import_file"
            )
            
            if uploaded_file:
                if uploaded_file.name.endswith('.json'):
                    try:
                        json_data = uploaded_file.read().decode('utf-8')
                        if st.button("📥 Importer", key="import_json"):
                            results = gestionnaire.importer_pieces_json(json_data)
                            st.success(f"✅ Import terminé : {results['success']} réussies, {results['failed']} échouées")
                            if results['errors']:
                                with st.expander("Voir les erreurs"):
                                    for error in results['errors']:
                                        st.error(error)
                    except Exception as e:
                        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
    
    with tab4:
        st.markdown("#### Maintenance")
        
        stats = gestionnaire.get_statistiques()
        
        # Statistiques système
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total pièces", stats['total'])
            st.metric("Taille totale", gestionnaire.formater_taille_fichier(stats['taille_totale']))
        
        with col2:
            st.metric("Pièces archivées", len([p for p in st.session_state.pieces.values() if p.statut == 'archivé']))
            st.metric("Entrées historique", len(st.session_state.pieces_history))
        
        with col3:
            st.metric("Tags uniques", len(stats['tags_populaires']))
            st.metric("Favoris", stats['total_favoris'])
        
        st.markdown("##### Actions de maintenance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧹 Nettoyer les doublons", key="clean_duplicates"):
                st.info("Fonction à implémenter : détection et suppression des doublons")
            
            if st.button("🔧 Réindexer les pièces", key="reindex_pieces"):
                gestionnaire._renumeroter_pieces_selectionnees()
                st.success("✅ Pièces réindexées")
                st.rerun()
        
        with col2:
            if st.button("📊 Recalculer les statistiques", key="recalc_stats"):
                # Forcer le recalcul
                st.session_state.pieces_metadata['last_modified'] = datetime.now()
                st.success("✅ Statistiques recalculées")
                st.rerun()
            
            if st.button("🗑️ Vider la corbeille", key="empty_trash"):
                if st.checkbox("Confirmer la suppression définitive", key="confirm_empty_trash"):
                    # Supprimer définitivement les pièces marquées comme supprimées
                    to_delete = [p.id for p in st.session_state.pieces.values() if p.statut == 'supprimé']
                    for piece_id in to_delete:
                        del st.session_state.pieces[piece_id]
                    st.success(f"✅ {len(to_delete)} pièces supprimées définitivement")
                    st.rerun()

def display_import_modal(gestionnaire: GestionnairePiecesUnifie):
    """Modal d'import de fichiers"""
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("## 📤 Import de pièces")
        with col2:
            if st.button("❌ Fermer", key="close_import_modal"):
                st.session_state.show_import_modal = False
                st.rerun()
        
        # Options d'import
        tab1, tab2, tab3 = st.tabs(["📎 Fichiers locaux", "📄 Documents existants", "🌐 Import externe"])
        
        with tab1:
            st.markdown("#### Import de fichiers depuis votre ordinateur")
            
            uploaded_files = st.file_uploader(
                "Sélectionnez des fichiers",
                accept_multiple_files=True,
                key="import_local_files"
            )
            
            if uploaded_files:
                st.info(f"{len(uploaded_files)} fichiers sélectionnés")
                
                # Options d'import
                col1, col2 = st.columns(2)
                
                with col1:
                    default_category = st.selectbox(
                        "Catégorie par défaut",
                        list(gestionnaire.CATEGORIES_CONFIG.keys()),
                        key="import_default_category"
                    )
                    
                    default_importance = st.slider(
                        "Importance par défaut",
                        1, 10, 5,
                        key="import_default_importance"
                    )
                
                with col2:
                    auto_detect_type = st.checkbox(
                        "Détecter automatiquement le type",
                        value=True,
                        key="import_auto_detect"
                    )
                    
                    auto_select = st.checkbox(
                        "Sélectionner automatiquement pour communication",
                        key="import_auto_select"
                    )
                
                if st.button("📥 Importer les fichiers", key="do_import_files", type="primary"):
                    progress = st.progress(0)
                    success_count = 0
                    
                    for i, file in enumerate(uploaded_files):
                        try:
                            # Créer la pièce
                            piece = PieceJuridique(
                                nom=file.name,
                                type_piece=gestionnaire.CATEGORIES_CONFIG[default_category]['types'][0],
                                categorie=default_category,
                                importance=default_importance,
                                taille=file.size,
                                chemin_fichier=file.name,
                                mime_type=file.type
                            )
                            
                            # Calculer le hash
                            content = file.read()
                            piece.hash_fichier = gestionnaire.calculer_hash_fichier(content)
                            file.seek(0)  # Remettre au début
                            
                            # Extraction de texte si possible
                            if file.type and 'text' in file.type:
                                piece.contenu_extrait = content.decode('utf-8', errors='ignore')[:1000]
                            
                            # Détection automatique du type
                            if auto_detect_type:
                                piece.categorie = gestionnaire._determiner_categorie(piece)
                            
                            # Ajouter la pièce
                            gestionnaire.ajouter_piece(piece, auto_select=auto_select)
                            success_count += 1
                            
                        except Exception as e:
                            st.error(f"Erreur avec {file.name}: {str(e)}")
                        
                        progress.progress((i + 1) / len(uploaded_files))
                    
                    st.success(f"✅ {success_count}/{len(uploaded_files)} fichiers importés avec succès!")
                    
                    if success_count > 0:
                        st.balloons()
                        import time
                        time.sleep(2)
                        st.session_state.show_import_modal = False
                        st.rerun()
        
        with tab2:
            st.markdown("#### Import depuis les documents déjà chargés")
            
            # Vérifier s'il y a des documents dans la session
            azure_docs = st.session_state.get('azure_documents', {})
            
            if not azure_docs:
                st.info("Aucun document disponible dans la session. Chargez d'abord des documents.")
            else:
                st.info(f"{len(azure_docs)} documents disponibles")
                
                # Sélection des documents
                selected_docs = st.multiselect(
                    "Sélectionnez les documents à importer",
                    options=list(azure_docs.keys()),
                    format_func=lambda x: azure_docs[x].title if hasattr(azure_docs[x], 'title') else str(x),
                    key="import_select_docs"
                )
                
                if selected_docs:
                    if st.button("📥 Importer les documents sélectionnés", key="do_import_docs"):
                        success_count = 0
                        
                        for doc_id in selected_docs:
                            try:
                                doc = azure_docs[doc_id]
                                
                                # Créer la pièce depuis le document
                                piece = PieceJuridique(
                                    nom=doc.title if hasattr(doc, 'title') else f"Document {doc_id}",
                                    document_id=doc_id,
                                    description=doc.content[:500] if hasattr(doc, 'content') else "",
                                    contenu_extrait=doc.content[:1000] if hasattr(doc, 'content') else "",
                                    source=doc.source if hasattr(doc, 'source') else "Document importé",
                                    metadata=doc.metadata if hasattr(doc, 'metadata') else {}
                                )
                                
                                # Déterminer la catégorie
                                piece.categorie = gestionnaire._determiner_categorie(piece)
                                
                                # Calculer la pertinence si analyse disponible
                                if hasattr(st.session_state, 'current_analysis'):
                                    piece.pertinence = gestionnaire._calculer_pertinence(
                                        piece, 
                                        st.session_state.current_analysis
                                    )
                                
                                # Ajouter
                                gestionnaire.ajouter_piece(piece, auto_select=True)
                                success_count += 1
                                
                            except Exception as e:
                                st.error(f"Erreur avec le document {doc_id}: {str(e)}")
                        
                        st.success(f"✅ {success_count} documents importés avec succès!")
                        st.session_state.show_import_modal = False
                        st.rerun()
        
        with tab3:
            st.markdown("#### Import depuis une source externe")
            st.info("Fonctionnalité à venir : import depuis Azure, Google Drive, etc.")

def display_bulk_actions_modal(gestionnaire: GestionnairePiecesUnifie):
    """Modal d'actions groupées"""
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("## ⚡ Actions groupées")
        with col2:
            if st.button("❌ Fermer", key="close_bulk_modal"):
                st.session_state.show_bulk_actions = False
                st.rerun()
        
        # Sélection des pièces
        selected_pieces = st.session_state.get('selected_pieces', [])
        
        if not selected_pieces:
            st.warning("Aucune pièce sélectionnée. Sélectionnez des pièces depuis la vue principale.")
            return
        
        st.info(f"{len(selected_pieces)} pièces sélectionnées")
        
        # Actions disponibles
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Modification", "📁 Organisation", "🏷️ Tags", "🗑️ Suppression"])
        
        with tab1:
            st.markdown("#### Modification en masse")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Changement de statut
                new_status = st.selectbox(
                    "Nouveau statut",
                    ["Ne pas modifier"] + [v['label'] for k, v in gestionnaire.STATUTS_CONFIG.items()],
                    key="bulk_status"
                )
                
                if new_status != "Ne pas modifier":
                    status_key = [k for k, v in gestionnaire.STATUTS_CONFIG.items() if v['label'] == new_status][0]
                    if st.button("🔄 Appliquer le statut", key="apply_bulk_status"):
                        results = gestionnaire.operations_groupees(selected_pieces, 'archive' if status_key == 'archivé' else 'restore')
                        st.success(f"✅ Statut modifié pour {results['success']} pièces")
                        st.rerun()
            
            with col2:
                # Changement d'importance
                new_importance = st.slider(
                    "Nouvelle importance",
                    0, 10, 5,
                    help="0 = Ne pas modifier",
                    key="bulk_importance"
                )
                
                if new_importance > 0:
                    if st.button("⭐ Appliquer l'importance", key="apply_bulk_importance"):
                        results = gestionnaire.operations_groupees(
                            selected_pieces, 
                            'importance', 
                            importance=new_importance
                        )
                        st.success(f"✅ Importance modifiée pour {results['success']} pièces")
                        st.rerun()
        
        with tab2:
            st.markdown("#### Organisation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection pour communication
                if st.button("✅ Sélectionner pour communication", key="bulk_select_comm", use_container_width=True):
                    results = gestionnaire.operations_groupees(selected_pieces, 'select')
                    st.success(f"✅ {results['success']} pièces sélectionnées")
                    st.rerun()
                
                if st.button("❌ Retirer de la sélection", key="bulk_deselect_comm", use_container_width=True):
                    results = gestionnaire.operations_groupees(selected_pieces, 'deselect')
                    st.success(f"✅ {results['success']} pièces retirées")
                    st.rerun()
            
            with col2:
                # Déplacement vers dossier
                dossiers = ["Aucun"] + list(st.session_state.get('dossiers', {}).keys())
                new_dossier = st.selectbox("Déplacer vers", dossiers, key="bulk_dossier")
                
                if st.button("📁 Déplacer", key="bulk_move", use_container_width=True):
                    dossier_id = None if new_dossier == "Aucun" else new_dossier
                    results = gestionnaire.operations_groupees(
                        selected_pieces, 
                        'move', 
                        dossier_id=dossier_id
                    )
                    st.success(f"✅ {results['success']} pièces déplacées")
                    st.rerun()
        
        with tab3:
            st.markdown("#### Gestion des tags")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Ajouter des tags
                st.markdown("##### Ajouter des tags")
                
                # Tags existants
                existing_tags = [tag for tag, _ in gestionnaire.get_all_tags()]
                selected_existing_tags = st.multiselect(
                    "Tags existants",
                    existing_tags,
                    key="bulk_existing_tags"
                )
                
                # Nouveaux tags
                new_tags_input = st.text_input(
                    "Nouveaux tags (séparés par des virgules)",
                    key="bulk_new_tags"
                )
                
                if st.button("➕ Ajouter les tags", key="bulk_add_tags"):
                    all_tags = selected_existing_tags + [t.strip() for t in new_tags_input.split(',') if t.strip()]
                    if all_tags:
                        results = gestionnaire.operations_groupees(
                            selected_pieces,
                            'tag',
                            tags=all_tags
                        )
                        st.success(f"✅ Tags ajoutés à {results['success']} pièces")
                        st.rerun()
            
            with col2:
                # Retirer des tags
                st.markdown("##### Retirer des tags")
                
                # Collecter tous les tags des pièces sélectionnées
                all_piece_tags = set()
                for piece_id in selected_pieces:
                    piece = gestionnaire.get_piece(piece_id)
                    if piece:
                        all_piece_tags.update(piece.tags)
                
                if all_piece_tags:
                    tags_to_remove = st.multiselect(
                        "Tags à retirer",
                        list(all_piece_tags),
                        key="bulk_remove_tags"
                    )
                    
                    if tags_to_remove and st.button("➖ Retirer les tags", key="bulk_do_remove_tags"):
                        results = gestionnaire.operations_groupees(
                            selected_pieces,
                            'untag',
                            tags=tags_to_remove
                        )
                        st.success(f"✅ Tags retirés de {results['success']} pièces")
                        st.rerun()
                else:
                    st.info("Aucun tag commun dans la sélection")
        
        with tab4:
            st.markdown("#### Suppression")
            
            st.warning("⚠️ Attention : ces actions sont irréversibles!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📦 Archiver la sélection", key="bulk_archive", use_container_width=True):
                    results = gestionnaire.operations_groupees(selected_pieces, 'archive')
                    st.success(f"✅ {results['success']} pièces archivées")
                    st.session_state.selected_pieces = []
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Supprimer définitivement", key="bulk_delete", use_container_width=True):
                    if st.checkbox("Je confirme vouloir supprimer définitivement ces pièces", key="confirm_bulk_delete"):
                        results = gestionnaire.operations_groupees(
                            selected_pieces,
                            'delete',
                            permanent=True
                        )
                        st.success(f"✅ {results['success']} pièces supprimées")
                        st.session_state.selected_pieces = []
                        st.rerun()

def display_piece_detail_modal(gestionnaire: GestionnairePiecesUnifie):
    """Modal de détail d'une pièce"""
    
    piece_id = st.session_state.get('current_piece_id')
    if not piece_id:
        return
    
    piece = gestionnaire.get_piece(piece_id)
    if not piece:
        st.error("Pièce introuvable")
        return
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
            st.markdown(f"## {cat_config['icon']} {piece.nom}")
        with col2:
            if st.button("❌ Fermer", key="close_detail_modal"):
                st.session_state.show_piece_detail = False
                st.rerun()
        
        # Informations principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Type", piece.type_piece)
            st.metric("Catégorie", piece.categorie)
            statut_config = gestionnaire.STATUTS_CONFIG[piece.statut]
            st.metric("Statut", f"{statut_config['icon']} {statut_config['label']}")
        
        with col2:
            st.metric("Importance", f"{piece.importance}/10")
            st.metric("Pertinence", f"{piece.pertinence:.0%}")
            st.metric("Numéro d'ordre", piece.numero_ordre)
        
        with col3:
            st.metric("Date d'ajout", piece.date_ajout.strftime('%d/%m/%Y'))
            if piece.date_document:
                st.metric("Date document", piece.date_document.strftime('%d/%m/%Y'))
            if piece.taille:
                st.metric("Taille", gestionnaire.formater_taille_fichier(piece.taille))
        
        # Onglets détaillés
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Contenu", "🏷️ Tags & Notes", "📊 Métadonnées", "🔗 Relations", "📜 Historique"])
        
        with tab1:
            if piece.description:
                st.markdown("#### Description")
                st.write(piece.description)
            
            if piece.contenu_extrait:
                st.markdown("#### Extrait du contenu")
                st.text_area("", piece.contenu_extrait, height=200, disabled=True)
            
            if piece.source:
                st.markdown("#### Source")
                st.write(piece.source)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Tags")
                if piece.tags:
                    for tag in piece.tags:
                        st.write(f"🏷️ {tag}")
                else:
                    st.info("Aucun tag")
            
            with col2:
                st.markdown("#### Notes")
                if piece.notes:
                    st.write(piece.notes)
                else:
                    st.info("Aucune note")
        
        with tab3:
            st.markdown("#### Métadonnées système")
            
            metadata_df = pd.DataFrame([
                {"Propriété": "ID", "Valeur": piece.id},
                {"Propriété": "Document ID", "Valeur": piece.document_id or "N/A"},
                {"Propriété": "Version", "Valeur": piece.version},
                {"Propriété": "Hash fichier", "Valeur": piece.hash_fichier[:16] + "..." if piece.hash_fichier else "N/A"},
                {"Propriété": "Type MIME", "Valeur": piece.mime_type or "N/A"},
                {"Propriété": "Modifié par", "Valeur": piece.modifie_par or "N/A"},
                {"Propriété": "Date modification", "Valeur": piece.date_modification.strftime('%d/%m/%Y %H:%M') if piece.date_modification else "N/A"}
            ])
            
            st.dataframe(metadata_df, hide_index=True, use_container_width=True)
            
            if piece.metadata:
                st.markdown("#### Métadonnées personnalisées")
                st.json(piece.metadata)
        
        with tab4:
            st.markdown("#### Pièces liées")
            if piece.pieces_liees:
                for linked_id in piece.pieces_liees:
                    linked_piece = gestionnaire.get_piece(linked_id)
                    if linked_piece:
                        st.write(f"🔗 {linked_piece.nom}")
            else:
                st.info("Aucune pièce liée")
            
            if piece.dossier_id:
                st.markdown("#### Dossier")
                st.write(f"📁 {piece.dossier_id}")
        
        with tab5:
            if piece.versions_precedentes:
                st.markdown("#### Versions précédentes")
                for version in piece.versions_precedentes:
                    with st.expander(f"Version {version['version']} - {version['date']}"):
                        st.write(f"**Nom:** {version.get('nom', 'N/A')}")
                        st.write(f"**Type:** {version.get('type_piece', 'N/A')}")
                        st.write(f"**Modifié par:** {version.get('modifie_par', 'N/A')}")
                        if version.get('description'):
                            st.write(f"**Description:** {version['description']}")
            else:
                st.info("Aucune version précédente")
        
        # Actions
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("✏️ Éditer", key="edit_from_detail", use_container_width=True):
                st.session_state.edit_piece_id = piece_id
                st.session_state.show_edit_modal = True
                st.session_state.show_piece_detail = False
        
        with col2:
            if piece.statut != 'sélectionné':
                if st.button("✅ Sélectionner", key="select_from_detail", use_container_width=True):
                    gestionnaire.selectionner_piece(piece_id)
                    st.rerun()
            else:
                if st.button("❌ Désélectionner", key="deselect_from_detail", use_container_width=True):
                    gestionnaire.deselectionner_piece(piece_id)
                    st.rerun()
        
        with col3:
            is_fav = piece_id in st.session_state.pieces_favoris
            if st.button("⭐" if is_fav else "☆ Favori", key="fav_from_detail", use_container_width=True):
                gestionnaire.toggle_favori(piece_id)
                st.rerun()
        
        with col4:
            if st.button("📋 Dupliquer", key="dup_from_detail", use_container_width=True):
                duplicate_piece(gestionnaire, piece)
        
        with col5:
            if st.button("🗑️ Supprimer", key="del_from_detail", use_container_width=True):
                if st.checkbox("Confirmer", key="confirm_del_detail"):
                    gestionnaire.supprimer_piece(piece_id, permanent=True)
                    st.session_state.show_piece_detail = False
                    st.rerun()
    
    # Modal d'édition si demandée
    if st.session_state.get('show_edit_modal'):
        display_edit_piece_modal(gestionnaire)

def display_edit_piece_modal(gestionnaire: GestionnairePiecesUnifie):
    """Modal d'édition d'une pièce"""
    
    piece_id = st.session_state.get('edit_piece_id')
    if not piece_id:
        return
    
    piece = gestionnaire.get_piece(piece_id)
    if not piece:
        st.error("Pièce introuvable")
        return
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"## ✏️ Éditer : {piece.nom}")
        with col2:
            if st.button("❌ Fermer", key="close_edit_modal"):
                st.session_state.show_edit_modal = False
                st.rerun()
        
        # Formulaire d'édition
        with st.form("edit_piece_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom", value=piece.nom)
                
                categorie = st.selectbox(
                    "Catégorie",
                    list(gestionnaire.CATEGORIES_CONFIG.keys()),
                    index=list(gestionnaire.CATEGORIES_CONFIG.keys()).index(piece.categorie)
                )
                
                type_piece = st.selectbox(
                    "Type",
                    gestionnaire.CATEGORIES_CONFIG[categorie]['types'],
                    index=gestionnaire.CATEGORIES_CONFIG[categorie]['types'].index(piece.type_piece) 
                    if piece.type_piece in gestionnaire.CATEGORIES_CONFIG[categorie]['types'] else 0
                )
                
                importance = st.slider("Importance", 1, 10, piece.importance)
            
            with col2:
                source = st.text_input("Source", value=piece.source)
                
                statut = st.selectbox(
                    "Statut",
                    list(gestionnaire.STATUTS_CONFIG.keys()),
                    format_func=lambda x: gestionnaire.STATUTS_CONFIG[x]['label'],
                    index=list(gestionnaire.STATUTS_CONFIG.keys()).index(piece.statut)
                )
                
                pertinence = st.slider("Pertinence", 0.0, 1.0, piece.pertinence, format="%.0%%")
                
                create_version = st.checkbox(
                    "Créer une version",
                    value=True,
                    help="Enregistre l'état actuel avant modification"
                )
            
            # Description
            description = st.text_area(
                "Description",
                value=piece.description or "",
                height=100
            )
            
            # Notes
            notes = st.text_area(
                "Notes",
                value=piece.notes,
                height=100
            )
            
            # Tags
            current_tags = ", ".join(piece.tags)
            tags_input = st.text_input(
                "Tags (séparés par des virgules)",
                value=current_tags
            )
            
            # Bouton de soumission
            submitted = st.form_submit_button(
                "💾 Enregistrer les modifications",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                try:
                    # Préparer les modifications
                    modifications = {
                        'nom': nom,
                        'type_piece': type_piece,
                        'categorie': categorie,
                        'description': description,
                        'source': source,
                        'statut': statut,
                        'importance': importance,
                        'pertinence': pertinence,
                        'notes': notes,
                        'tags': [t.strip() for t in tags_input.split(',') if t.strip()],
                        'modifie_par': st.session_state.get('current_user', 'Utilisateur')
                    }
                    
                    # Appliquer les modifications
                    gestionnaire.modifier_piece(piece_id, create_version=create_version, **modifications)
                    
                    st.success("✅ Modifications enregistrées!")
                    import time
                    time.sleep(1)
                    
                    st.session_state.show_edit_modal = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

def display_floating_actions(gestionnaire: GestionnairePiecesUnifie):
    """Barre d'actions flottante pour la sélection"""
    
    selected_count = len(st.session_state.get('selected_pieces', []))
    
    if selected_count > 0:
        # Créer une barre flottante
        st.markdown(
            f"""
            <div style="position: fixed; bottom: 20px; right: 20px; 
                        background-color: #f0f2f6; padding: 15px; 
                        border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        z-index: 1000;">
                <h4>{selected_count} pièces sélectionnées</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Actions dans un expander
        with st.expander(f"🎯 Actions sur {selected_count} pièces", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Sélectionner pour comm.", key="float_select_comm"):
                    results = gestionnaire.operations_groupees(
                        st.session_state.selected_pieces,
                        'select'
                    )
                    st.success(f"{results['success']} pièces sélectionnées")
                    st.rerun()
            
            with col2:
                if st.button("📦 Archiver", key="float_archive"):
                    results = gestionnaire.operations_groupees(
                        st.session_state.selected_pieces,
                        'archive'
                    )
                    st.success(f"{results['success']} pièces archivées")
                    st.session_state.selected_pieces = []
                    st.rerun()
            
            with col3:
                if st.button("🏷️ Gérer tags", key="float_tags"):
                    st.session_state.show_bulk_actions = True
            
            with col4:
                if st.button("❌ Désélectionner tout", key="float_clear"):
                    st.session_state.selected_pieces = []
                    st.rerun()

def display_export_modal(gestionnaire: GestionnairePiecesUnifie, selection_only: bool = False):
    """Modal d'export"""
    
    with st.container():
        st.markdown("---")
        
        # En-tête
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("## 📤 Export de pièces")
        with col2:
            if st.button("❌ Fermer", key="close_export_modal"):
                st.session_state.show_export_modal = False
                st.session_state.show_export_selection = False
                st.rerun()
        
        # Options d'export
        col1, col2 = st.columns(2)
        
        with col1:
            format_export = st.selectbox(
                "Format d'export",
                ["json", "csv", "excel", "txt"],
                format_func=lambda x: {
                    "json": "JSON (complet)",
                    "csv": "CSV (tableur)",
                    "excel": "Excel (multi-feuilles)",
                    "txt": "TXT (bordereau)"
                }[x],
                key="export_format"
            )
        
        with col2:
            if selection_only:
                pieces_to_export = gestionnaire.get_pieces_selectionnees()
                st.metric("Pièces à exporter", len(pieces_to_export))
            else:
                export_scope = st.radio(
                    "Étendue",
                    ["Sélection communication", "Sélection UI", "Toutes les pièces"],
                    key="export_scope"
                )
                
                if export_scope == "Sélection communication":
                    pieces_to_export = gestionnaire.get_pieces_selectionnees()
                elif export_scope == "Sélection UI":
                    piece_ids = st.session_state.get('selected_pieces', [])
                    pieces_to_export = [gestionnaire.get_piece(pid) for pid in piece_ids if gestionnaire.get_piece(pid)]
                else:
                    pieces_to_export = None  # Toutes
        
        # Aperçu
        if format_export == "txt":
            st.markdown("### 📄 Aperçu du bordereau")
            format_bordereau = st.radio(
                "Style",
                ["detaille", "simple", "compact"],
                format_func=lambda x: {
                    "detaille": "Détaillé",
                    "simple": "Simple",
                    "compact": "Compact"
                }[x],
                horizontal=True,
                key="export_bordereau_style"
            )
            
            piece_ids = [p.id for p in pieces_to_export] if pieces_to_export else None
            preview = gestionnaire.generer_bordereau(format_bordereau, piece_ids)
            st.text_area("", preview[:1000] + "..." if len(preview) > 1000 else preview, height=300, disabled=True)
        
        # Export
        if st.button("💾 Générer l'export", key="do_export", type="primary", use_container_width=True):
            try:
                piece_ids = [p.id for p in pieces_to_export] if pieces_to_export else None
                
                content, filename, mime_type = gestionnaire.exporter_pieces(piece_ids, format_export)
                
                # Bouton de téléchargement
                st.download_button(
                    f"⬇️ Télécharger {filename}",
                    content if isinstance(content, bytes) else content.encode('utf-8'),
                    filename,
                    mime_type,
                    use_container_width=True,
                    key="download_export"
                )
                
                st.success("✅ Export généré avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'export : {str(e)}")

# ========================= FONCTIONS D'INTÉGRATION =========================

def process_piece_selection_request(query: str, analysis: dict):
    """Point d'entrée pour la sélection de pièces depuis l'analyse juridique"""
    
    st.markdown("### 📋 Sélection de pièces pour communication")
    
    # Initialiser le gestionnaire
    if 'gestionnaire_pieces' not in st.session_state:
        st.session_state.gestionnaire_pieces = GestionnairePiecesUnifie()
    
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Stocker l'analyse courante pour le calcul de pertinence
    st.session_state.current_analysis = analysis
    
    # Interface en deux colonnes
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("#### 📄 Documents disponibles")
        _afficher_documents_disponibles_analyse(gestionnaire, analysis)
    
    with col_right:
        st.markdown("#### ✅ Pièces sélectionnées")
        _afficher_pieces_selectionnees_analyse(gestionnaire)
    
    # Barre d'actions
    _afficher_barre_actions_analyse(gestionnaire)

def _afficher_documents_disponibles_analyse(gestionnaire: GestionnairePiecesUnifie, analysis: dict):
    """Affiche les documents disponibles pour l'analyse"""
    
    # Collecter les documents pertinents
    documents = collect_available_documents_for_analysis(analysis)
    
    # Filtres rapides
    col1, col2 = st.columns(2)
    with col1:
        filtre_texte = st.text_input(
            "🔍 Rechercher",
            placeholder="Titre, contenu...",
            key="filtre_docs_analyse"
        )
    
    with col2:
        pertinence_min = st.slider(
            "Pertinence min",
            0.0, 1.0, 0.3,
            format="%.0%%",
            key="pertinence_min_analyse"
        )
    
    # Convertir et filtrer les documents
    pieces_disponibles = []
    
    for doc in documents:
        # Créer une pièce temporaire pour l'affichage
        piece = PieceJuridique(
            nom=doc.get('title', 'Sans titre'),
            description=doc.get('content', '')[:500],
            source=doc.get('source', ''),
            document_id=doc.get('id'),
            metadata=doc.get('metadata', {})
        )
        
        # Calculer la pertinence
        piece.pertinence = gestionnaire._calculer_pertinence(piece, analysis)
        
        # Déterminer la catégorie
        piece.categorie = gestionnaire._determiner_categorie(piece)
        
        # Filtrer
        if piece.pertinence >= pertinence_min:
            if not filtre_texte or filtre_texte.lower() in (piece.nom + ' ' + piece.description).lower():
                pieces_disponibles.append((piece, doc))
    
    # Trier par pertinence
    pieces_disponibles.sort(key=lambda x: x[0].pertinence, reverse=True)
    
    # Afficher
    for piece, doc in pieces_disponibles[:20]:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                cat_config = gestionnaire.CATEGORIES_CONFIG[piece.categorie]
                
                # Vérifier si déjà sélectionné
                is_selected = any(p.document_id == piece.document_id for p in gestionnaire.get_pieces_selectionnees())
                
                if is_selected:
                    st.markdown(f"**✅ {cat_config['icon']} {piece.nom}**")
                else:
                    st.markdown(f"**{cat_config['icon']} {piece.nom}**")
                
                # Indicateur de pertinence
                if piece.pertinence >= 0.7:
                    st.caption(f"🟢 Très pertinent ({piece.pertinence:.0%})")
                elif piece.pertinence >= 0.4:
                    st.caption(f"🟡 Pertinent ({piece.pertinence:.0%})")
                else:
                    st.caption(f"🔴 Peu pertinent ({piece.pertinence:.0%})")
                
                # Aperçu
                if piece.description:
                    with st.expander("Aperçu", expanded=False):
                        st.text(piece.description)
            
            with col2:
                if not is_selected:
                    if st.button("➕", key=f"add_analyse_{piece.document_id}", help="Ajouter"):
                        # Créer la pièce complète
                        piece.type_piece = gestionnaire.CATEGORIES_CONFIG[piece.categorie]['types'][0]
                        piece_id = gestionnaire.ajouter_piece(piece, auto_select=True)
                        st.rerun()
                else:
                    st.caption("☑️ Sélectionné")
            
            st.divider()
    
    if len(pieces_disponibles) > 20:
        st.info(f"... et {len(pieces_disponibles) - 20} autres documents")

def _afficher_pieces_selectionnees_analyse(gestionnaire: GestionnairePiecesUnifie):
    """Affiche les pièces sélectionnées pour l'analyse"""
    
    pieces_selectionnees = gestionnaire.get_pieces_selectionnees()
    
    if not pieces_selectionnees:
        st.info("Aucune pièce sélectionnée")
        return
    
    # Stats rapides
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", len(pieces_selectionnees))
    with col2:
        pertinence_moy = sum(p.pertinence for p in pieces_selectionnees) / len(pieces_selectionnees)
        st.metric("Pertinence moy.", f"{pertinence_moy:.0%}")
    
    # Grouper par catégorie
    pieces_par_cat = gestionnaire.get_pieces_par_categorie(selected_only=True)
    
    for categorie, pieces in pieces_par_cat.items():
        cat_config = gestionnaire.CATEGORIES_CONFIG[categorie]
        
        st.markdown(f"**{cat_config['icon']} {categorie} ({len(pieces)})**")
        
        for piece in pieces:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"#{piece.numero_ordre} - {piece.nom}")
                    if piece.notes:
                        st.caption(f"📝 {piece.notes}")
                
                with col2:
                    if st.button("❌", key=f"remove_analyse_{piece.id}", help="Retirer"):
                        gestionnaire.deselectionner_piece(piece.id)
                        st.rerun()
                
                st.divider()

def _afficher_barre_actions_analyse(gestionnaire: GestionnairePiecesUnifie):
    """Barre d'actions pour l'analyse"""
    
    pieces_selectionnees = gestionnaire.get_pieces_selectionnees()
    
    if not pieces_selectionnees:
        return
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Créer bordereau", key="bordereau_analyse"):
            with st.expander("Options", expanded=True):
                format_type = st.radio(
                    "Format",
                    ["detaille", "simple"],
                    key="format_bordereau_analyse"
                )
                
                bordereau = gestionnaire.generer_bordereau(format_type)
                
                st.text_area("Aperçu", bordereau, height=300)
                
                st.download_button(
                    "💾 Télécharger",
                    bordereau,
                    f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
    
    with col2:
        if st.button("📤 Exporter", key="export_analyse"):
            st.session_state.show_export_selection = True
    
    with col3:
        if st.button("📝 Synthétiser", key="synthesize_analyse"):
            st.session_state.action_requested = "synthesis"
            st.session_state.synthesis_pieces = pieces_selectionnees
            st.rerun()
    
    with col4:
        if st.button("✅ Valider", key="validate_analyse"):
            st.success(f"✅ {len(pieces_selectionnees)} pièces validées pour communication")
            st.balloons()
    
    # Modal d'export
    if st.session_state.get('show_export_selection'):
        display_export_modal(gestionnaire, selection_only=True)

def collect_available_documents_for_analysis(analysis: dict) -> List[Dict[str, Any]]:
    """Collecte les documents disponibles pour une analyse"""
    documents = []
    
    # Documents depuis Azure
    azure_docs = st.session_state.get('azure_documents', {})
    for doc_id, doc in azure_docs.items():
        doc_dict = {
            'id': doc_id,
            'title': getattr(doc, 'title', f'Document {doc_id}'),
            'content': getattr(doc, 'content', ''),
            'source': getattr(doc, 'source', 'Azure'),
            'metadata': getattr(doc, 'metadata', {})
        }
        documents.append(doc_dict)
    
    # Documents depuis la recherche si référence
    if analysis.get('reference'):
        ref_docs = search_documents_by_reference(analysis['reference'])
        documents.extend(ref_docs)
    
    # Dédupliquer
    seen_ids = set()
    unique_docs = []
    for doc in documents:
        if doc['id'] not in seen_ids:
            seen_ids.add(doc['id'])
            unique_docs.append(doc)
    
    return unique_docs

def search_documents_by_reference(reference: str) -> List[Dict[str, Any]]:
    """Recherche des documents par référence"""
    results = []
    ref_clean = reference.replace('@', '').strip().lower()
    
    # Recherche dans Azure Search si disponible
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and hasattr(search_manager, 'is_connected') and search_manager.is_connected():
        try:
            azure_results = search_manager.search(reference, top=20)
            for result in azure_results:
                results.append({
                    'id': result.get('id', str(uuid.uuid4())),
                    'title': result.get('title', 'Sans titre'),
                    'content': result.get('content', ''),
                    'source': 'Azure Search',
                    'metadata': result.get('metadata', {})
                })
        except Exception as e:
            st.warning(f"Erreur lors de la recherche : {str(e)}")
    
    return results

def show_pieces_management_tab():
    """Affiche l'onglet de gestion des pièces"""
    display_pieces_interface()

def init_pieces_manager():
    """Initialise le gestionnaire de pièces au démarrage"""
    if 'gestionnaire_pieces' not in st.session_state:
        st.session_state.gestionnaire_pieces = GestionnairePiecesUnifie()
    
    # Migration des anciennes données si nécessaire
    if 'pieces_selectionnees' in st.session_state and isinstance(st.session_state.pieces_selectionnees, dict):
        # Si c'est l'ancien format, migrer
        gestionnaire = st.session_state.gestionnaire_pieces
        
        for piece_id, old_piece in st.session_state.pieces_selectionnees.items():
            if not isinstance(old_piece, PieceJuridique):
                # Convertir l'ancien format
                new_piece = PieceJuridique(
                    id=piece_id,
                    nom=getattr(old_piece, 'titre', getattr(old_piece, 'nom', 'Sans nom')),
                    type_piece=getattr(old_piece, 'type_piece', 'Document'),
                    categorie=getattr(old_piece, 'categorie', 'Autre'),
                    description=getattr(old_piece, 'description', ''),
                    source=getattr(old_piece, 'source', ''),
                    statut='sélectionné',
                    pertinence=getattr(old_piece, 'pertinence', 0.5),
                    notes=getattr(old_piece, 'notes', '')
                )
                
                # Ajouter au nouveau système
                gestionnaire.ajouter_piece(new_piece, auto_select=True)
    
    return st.session_state.gestionnaire_pieces

# ========================= DOCUMENTATION =========================

"""
MODULE UNIFIÉ DE GESTION DES PIÈCES JURIDIQUES
==============================================

Ce module fusionne les fonctionnalités de sélection de pièces pour communication
et de gestion complète des pièces de procédure.

UTILISATION PRINCIPALE
---------------------

1. Initialisation au démarrage de l'application :
   ```python
   from modules.pieces_manager import init_pieces_manager
   
   # Dans la fonction main() de l'application
   init_pieces_manager()
   ```

2. Intégration dans l'analyse juridique :
   ```python
   from modules.pieces_manager import process_piece_selection_request
   
   # Après une analyse juridique
   if analysis.get('action_type') == 'piece_selection':
       process_piece_selection_request(query, analysis)
   ```

3. Onglet de gestion complète :
   ```python
   from modules.pieces_manager import show_pieces_management_tab
   
   # Dans les tabs de l'interface principale
   with tab_pieces:
       show_pieces_management_tab()
   ```

FONCTIONNALITÉS PRINCIPALES
--------------------------

1. Gestion unifiée des pièces :
   - Création, modification, suppression
   - Catégorisation automatique
   - Calcul de pertinence
   - Gestion des versions

2. Sélection pour communication :
   - Interface dédiée pour sélectionner des pièces
   - Génération de bordereaux
   - Export dans plusieurs formats

3. Organisation avancée :
   - Tags et favoris
   - Dossiers et relations
   - Recherche multicritères
   - Actions groupées

4. Statistiques et historique :
   - Tableau de bord complet
   - Historique des actions
   - Export des données

STRUCTURE DES DONNÉES
--------------------

La pièce juridique (PieceJuridique) contient :
- Identifiants : id, document_id
- Informations : nom, type, catégorie, description
- Dates : ajout, modification, document, sélection
- État : statut, importance, pertinence
- Fichier : chemin, taille, hash, mime_type
- Relations : tags, notes, pièces liées, dossier
- Versioning : version, historique

PERSONNALISATION
---------------

Pour ajouter des catégories personnalisées, modifier CATEGORIES_CONFIG :
```python
gestionnaire.CATEGORIES_CONFIG['Ma Catégorie'] = {
    'patterns': ['mot1', 'mot2'],
    'types': ['Type 1', 'Type 2'],
    'icon': '📁',
    'color': '#123456'
}
```

INTÉGRATION AVEC AZURE
---------------------

Le module s'intègre automatiquement avec :
- Azure Documents (session)
- Azure Search Manager
- Système de fichiers local

"""

# Point d'entrée
if __name__ == "__main__":
    display_pieces_interface()