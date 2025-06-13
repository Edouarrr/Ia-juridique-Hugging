"""
Module de gestion des pièces de procédure - Version améliorée
Avec tags, catégories, statuts et interface optimisée
"""

import streamlit as st
from datetime import datetime
import json
from typing import Dict, List, Optional, Any, Tuple
import uuid
import hashlib
import mimetypes
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import io

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
        tags: List[str] = field(default_factory=list)
        statut: str = "actif"  # actif, archivé, supprimé
        importance: int = 5  # 1-10
        date_modification: Optional[datetime] = None
        modifie_par: Optional[str] = None
        version: int = 1
        versions_precedentes: List[Dict] = field(default_factory=list)

class PiecesManager:
    """Gestionnaire avancé des pièces de procédure"""
    
    # Types de pièces avec catégories
    CATEGORIES_PIECES = {
        "Procédure": {
            "types": ["Assignation", "Citation directe", "Conclusions", "Requête", "Mémoire"],
            "icon": "📋",
            "color": "#3498db"
        },
        "Décision": {
            "types": ["Jugement", "Arrêt", "Ordonnance"],
            "icon": "⚖️",
            "color": "#e74c3c"
        },
        "Preuve": {
            "types": ["Pièce justificative", "Attestation", "Expertise", "Procès-verbal", "Constat"],
            "icon": "🔍",
            "color": "#2ecc71"
        },
        "Contrat": {
            "types": ["Contrat", "Avenant", "Convention", "Protocole"],
            "icon": "📄",
            "color": "#f39c12"
        },
        "Correspondance": {
            "types": ["Courrier", "Email", "Notification", "Mise en demeure"],
            "icon": "📧",
            "color": "#9b59b6"
        },
        "Financier": {
            "types": ["Facture", "Devis", "Relevé bancaire", "Bilan"],
            "icon": "💰",
            "color": "#1abc9c"
        },
        "Média": {
            "types": ["Photo", "Vidéo", "Audio", "Plan", "Schéma"],
            "icon": "📸",
            "color": "#34495e"
        },
        "Autre": {
            "types": ["Document", "Note", "Rapport", "Autre"],
            "icon": "📎",
            "color": "#95a5a6"
        }
    }
    
    # Statuts possibles
    STATUTS = {
        "actif": {"label": "Actif", "icon": "✅", "color": "#2ecc71"},
        "archivé": {"label": "Archivé", "icon": "📦", "color": "#95a5a6"},
        "en_revision": {"label": "En révision", "icon": "🔄", "color": "#f39c12"},
        "confidentiel": {"label": "Confidentiel", "icon": "🔒", "color": "#e74c3c"},
        "supprimé": {"label": "Supprimé", "icon": "🗑️", "color": "#c0392b"}
    }
    
    def __init__(self):
        """Initialise le gestionnaire avec des fonctionnalités avancées"""
        if 'pieces' not in st.session_state:
            st.session_state.pieces = {}
        if 'pieces_par_dossier' not in st.session_state:
            st.session_state.pieces_par_dossier = {}
        if 'pieces_metadata' not in st.session_state:
            st.session_state.pieces_metadata = {
                'total_size': 0,
                'last_modified': datetime.now(),
                'tags': set(),
                'categories_count': defaultdict(int),
                'types_count': defaultdict(int)
            }
        if 'pieces_history' not in st.session_state:
            st.session_state.pieces_history = []
        if 'pieces_favoris' not in st.session_state:
            st.session_state.pieces_favoris = set()
    
    def add_piece(self, piece: PieceProcedure, dossier_id: Optional[str] = None) -> str:
        """Ajoute une pièce avec validation et historique"""
        # Validation
        if not piece.nom:
            raise ValueError("Le nom de la pièce est obligatoire")
        
        # Vérifier l'unicité du hash si fichier
        if piece.hash_fichier:
            for existing_piece in st.session_state.pieces.values():
                if existing_piece.hash_fichier == piece.hash_fichier:
                    raise ValueError(f"Ce fichier existe déjà sous le nom : {existing_piece.nom}")
        
        # Ajouter la pièce
        st.session_state.pieces[piece.id] = piece
        
        # Associer au dossier si spécifié
        if dossier_id:
            if dossier_id not in st.session_state.pieces_par_dossier:
                st.session_state.pieces_par_dossier[dossier_id] = []
            st.session_state.pieces_par_dossier[dossier_id].append(piece.id)
        
        # Mettre à jour les métadonnées
        self._update_global_metadata(piece, 'add')
        
        # Ajouter à l'historique
        self._add_to_history('add', piece.id, {'nom': piece.nom, 'type': piece.type_piece})
        
        return piece.id
    
    def update_piece(self, piece_id: str, create_version: bool = True, **kwargs):
        """Met à jour une pièce avec gestion des versions"""
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
        
        # Mettre à jour les métadonnées globales
        st.session_state.pieces_metadata['last_modified'] = datetime.now()
        
        # Ajouter à l'historique
        self._add_to_history('update', piece_id, kwargs)
    
    def delete_piece(self, piece_id: str, permanent: bool = False):
        """Supprime ou archive une pièce avec traçabilité"""
        if piece_id not in st.session_state.pieces:
            return
        
        piece = st.session_state.pieces[piece_id]
        
        if permanent:
            # Suppression définitive
            # Retirer des dossiers
            for dossier_id, pieces in st.session_state.pieces_par_dossier.items():
                if piece_id in pieces:
                    pieces.remove(piece_id)
            
            # Retirer des favoris
            st.session_state.pieces_favoris.discard(piece_id)
            
            # Mettre à jour les métadonnées
            self._update_global_metadata(piece, 'remove')
            
            # Supprimer la pièce
            del st.session_state.pieces[piece_id]
            
            # Historique
            self._add_to_history('delete_permanent', piece_id, {'nom': piece.nom})
        else:
            # Archivage
            piece.statut = "archivé"
            piece.date_modification = datetime.now()
            
            # Historique
            self._add_to_history('archive', piece_id, {'nom': piece.nom})
    
    def search_pieces(self, query: str = "", filters: Dict[str, Any] = None) -> List[PieceProcedure]:
        """Recherche avancée avec scoring et filtres multiples"""
        results = []
        query_lower = query.lower() if query else ""
        
        for piece in st.session_state.pieces.values():
            # Filtrer par statut (sauf si explicitement demandé)
            if not filters or not filters.get('include_archived'):
                if piece.statut in ['supprimé', 'archivé']:
                    continue
            
            score = 0
            
            # Scoring basé sur la recherche textuelle
            if query:
                # Recherche dans le nom (poids élevé)
                if query_lower in piece.nom.lower():
                    score += 5
                    if piece.nom.lower().startswith(query_lower):
                        score += 2
                
                # Recherche dans la description
                if piece.description and query_lower in piece.description.lower():
                    score += 3
                
                # Recherche dans le type
                if query_lower in piece.type_piece.lower():
                    score += 2
                
                # Recherche dans les tags
                for tag in piece.tags:
                    if query_lower in tag.lower():
                        score += 3
                        break
                
                # Recherche dans les métadonnées
                metadata_str = json.dumps(piece.metadata).lower()
                if query_lower in metadata_str:
                    score += 1
            else:
                score = 1  # Si pas de query, inclure tous
            
            # Appliquer les filtres
            if filters:
                # Filtre par catégorie
                if filters.get('categorie'):
                    categorie = self._get_categorie(piece.type_piece)
                    if categorie != filters['categorie']:
                        continue
                
                # Filtre par type
                if filters.get('type_piece') and piece.type_piece != filters['type_piece']:
                    continue
                
                # Filtre par statut
                if filters.get('statut') and piece.statut != filters['statut']:
                    continue
                
                # Filtre par importance
                if filters.get('importance_min') and piece.importance < filters['importance_min']:
                    continue
                
                # Filtre par dates
                if filters.get('date_debut') and piece.date_ajout < filters['date_debut']:
                    continue
                if filters.get('date_fin') and piece.date_ajout > filters['date_fin']:
                    continue
                
                # Filtre par dossier
                if filters.get('dossier_id'):
                    pieces_dossier = st.session_state.pieces_par_dossier.get(filters['dossier_id'], [])
                    if piece.id not in pieces_dossier:
                        continue
                
                # Filtre par tags (au moins un tag doit matcher)
                if filters.get('tags'):
                    if not any(tag in piece.tags for tag in filters['tags']):
                        continue
                
                # Filtre par taille
                if piece.taille:
                    if filters.get('taille_min') and piece.taille < filters['taille_min']:
                        continue
                    if filters.get('taille_max') and piece.taille > filters['taille_max']:
                        continue
                
                # Filtre par favoris
                if filters.get('favoris_only') and piece.id not in st.session_state.pieces_favoris:
                    continue
            
            if score > 0:
                results.append((score, piece))
        
        # Trier par score décroissant puis par date
        results.sort(key=lambda x: (x[0], x[1].date_ajout), reverse=True)
        return [piece for _, piece in results]
    
    def get_piece(self, piece_id: str) -> Optional[PieceProcedure]:
        """Récupère une pièce par son ID"""
        return st.session_state.pieces.get(piece_id)
    
    def get_pieces_dossier(self, dossier_id: str, include_archived: bool = False) -> List[PieceProcedure]:
        """Récupère toutes les pièces d'un dossier"""
        piece_ids = st.session_state.pieces_par_dossier.get(dossier_id, [])
        pieces = []
        
        for pid in piece_ids:
            piece = self.get_piece(pid)
            if piece:
                if include_archived or piece.statut == "actif":
                    pieces.append(piece)
        
        return sorted(pieces, key=lambda p: p.numero_ordre)
    
    def toggle_favori(self, piece_id: str):
        """Ajoute ou retire une pièce des favoris"""
        if piece_id in st.session_state.pieces_favoris:
            st.session_state.pieces_favoris.remove(piece_id)
            return False
        else:
            st.session_state.pieces_favoris.add(piece_id)
            return True
    
    def get_favoris(self) -> List[PieceProcedure]:
        """Récupère toutes les pièces favorites"""
        return [self.get_piece(pid) for pid in st.session_state.pieces_favoris if self.get_piece(pid)]
    
    def bulk_operations(self, piece_ids: List[str], operation: str, **params) -> Dict[str, Any]:
        """Opérations en masse sur plusieurs pièces"""
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for piece_id in piece_ids:
            try:
                if operation == 'delete':
                    self.delete_piece(piece_id, params.get('permanent', False))
                elif operation == 'archive':
                    self.update_piece(piece_id, statut='archivé', create_version=False)
                elif operation == 'restore':
                    self.update_piece(piece_id, statut='actif', create_version=False)
                elif operation == 'move':
                    self.move_to_dossier(piece_id, params.get('dossier_id'))
                elif operation == 'tag':
                    self.add_tags(piece_id, params.get('tags', []))
                elif operation == 'remove_tag':
                    self.remove_tags(piece_id, params.get('tags', []))
                elif operation == 'update_type':
                    self.update_piece(piece_id, type_piece=params.get('type_piece'))
                elif operation == 'update_importance':
                    self.update_piece(piece_id, importance=params.get('importance'))
                elif operation == 'export':
                    # Géré séparément
                    pass
                
                results['success'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{piece_id}: {str(e)}")
        
        return results
    
    def move_to_dossier(self, piece_id: str, new_dossier_id: str):
        """Déplace une pièce vers un autre dossier"""
        piece = self.get_piece(piece_id)
        if not piece:
            return
        
        # Retirer de l'ancien dossier
        for dossier_id, pieces in st.session_state.pieces_par_dossier.items():
            if piece_id in pieces:
                pieces.remove(piece_id)
        
        # Ajouter au nouveau dossier
        if new_dossier_id:
            if new_dossier_id not in st.session_state.pieces_par_dossier:
                st.session_state.pieces_par_dossier[new_dossier_id] = []
            st.session_state.pieces_par_dossier[new_dossier_id].append(piece_id)
        
        # Historique
        self._add_to_history('move', piece_id, {'to_dossier': new_dossier_id})
    
    def add_tags(self, piece_id: str, tags: List[str]):
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
            
            # Historique
            self._add_to_history('add_tags', piece_id, {'tags': normalized_tags})
    
    def remove_tags(self, piece_id: str, tags: List[str]):
        """Retire des tags d'une pièce"""
        piece = self.get_piece(piece_id)
        if piece:
            normalized_tags = [tag.strip().lower() for tag in tags]
            piece.tags = [t for t in piece.tags if t not in normalized_tags]
    
    def get_all_tags(self) -> List[Tuple[str, int]]:
        """Retourne tous les tags avec leur fréquence"""
        tag_counter = Counter()
        for piece in st.session_state.pieces.values():
            tag_counter.update(piece.tags)
        return tag_counter.most_common()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques détaillées sur les pièces"""
        pieces = [p for p in st.session_state.pieces.values() if p.statut != 'supprimé']
        total = len(pieces)
        
        if total == 0:
            return {
                'total': 0,
                'par_type': {},
                'par_categorie': {},
                'par_statut': {},
                'taille_totale': 0,
                'pieces_recentes': [],
                'tags_populaires': [],
                'evolution': {},
                'importance_moyenne': 0
            }
        
        # Statistiques de base
        par_type = Counter(p.type_piece for p in pieces)
        par_statut = Counter(p.statut for p in pieces)
        par_categorie = Counter(self._get_categorie(p.type_piece) for p in pieces)
        
        # Taille totale
        taille_totale = sum(p.taille for p in pieces if p.taille)
        
        # Importance moyenne
        importance_moyenne = sum(p.importance for p in pieces) / total
        
        # Pièces récentes
        pieces_recentes = sorted(pieces, key=lambda p: p.date_ajout, reverse=True)[:10]
        
        # Tags populaires
        tags_populaires = self.get_all_tags()[:10]
        
        # Évolution mensuelle
        evolution = defaultdict(int)
        for piece in pieces:
            mois = piece.date_ajout.strftime('%Y-%m')
            evolution[mois] += 1
        
        # Statistiques par dossier
        pieces_par_dossier = Counter()
        for dossier_id, piece_ids in st.session_state.pieces_par_dossier.items():
            pieces_par_dossier[dossier_id] = len([pid for pid in piece_ids if pid in [p.id for p in pieces]])
        
        return {
            'total': total,
            'par_type': dict(par_type),
            'par_categorie': dict(par_categorie),
            'par_statut': dict(par_statut),
            'taille_totale': taille_totale,
            'taille_moyenne': taille_totale // total if total > 0 else 0,
            'pieces_recentes': pieces_recentes,
            'tags_populaires': tags_populaires,
            'evolution': dict(evolution),
            'importance_moyenne': importance_moyenne,
            'pieces_par_dossier': dict(pieces_par_dossier),
            'total_favoris': len(st.session_state.pieces_favoris)
        }
    
    def export_pieces(self, piece_ids: List[str] = None, format: str = 'json') -> Any:
        """Exporte les pièces dans différents formats"""
        if piece_ids:
            pieces_to_export = [self.get_piece(pid) for pid in piece_ids if self.get_piece(pid)]
        else:
            pieces_to_export = [p for p in st.session_state.pieces.values() if p.statut != 'supprimé']
        
        if format == 'json':
            data = []
            for piece in pieces_to_export:
                piece_dict = {
                    'id': piece.id,
                    'nom': piece.nom,
                    'type_piece': piece.type_piece,
                    'numero_ordre': piece.numero_ordre,
                    'description': piece.description,
                    'date_ajout': piece.date_ajout.isoformat(),
                    'tags': piece.tags,
                    'statut': piece.statut,
                    'importance': piece.importance,
                    'taille': piece.taille,
                    'hash_fichier': piece.hash_fichier,
                    'metadata': piece.metadata
                }
                data.append(piece_dict)
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            # Créer un DataFrame pour l'export CSV
            data = []
            for piece in pieces_to_export:
                data.append({
                    'Nom': piece.nom,
                    'Type': piece.type_piece,
                    'Numéro': piece.numero_ordre,
                    'Date ajout': piece.date_ajout.strftime('%Y-%m-%d %H:%M'),
                    'Statut': piece.statut,
                    'Importance': piece.importance,
                    'Tags': ', '.join(piece.tags),
                    'Description': piece.description or '',
                    'Taille': self.format_file_size(piece.taille) if piece.taille else ''
                })
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False).encode('utf-8-sig')
        
        elif format == 'excel':
            # Export Excel avec plusieurs feuilles
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Feuille principale
                data = []
                for piece in pieces_to_export:
                    data.append({
                        'ID': piece.id,
                        'Nom': piece.nom,
                        'Type': piece.type_piece,
                        'Catégorie': self._get_categorie(piece.type_piece),
                        'Numéro': piece.numero_ordre,
                        'Date ajout': piece.date_ajout,
                        'Statut': piece.statut,
                        'Importance': piece.importance,
                        'Tags': ', '.join(piece.tags),
                        'Description': piece.description or '',
                        'Taille (octets)': piece.taille or 0,
                        'Hash': piece.hash_fichier or ''
                    })
                
                df_pieces = pd.DataFrame(data)
                df_pieces.to_excel(writer, sheet_name='Pièces', index=False)
                
                # Feuille des statistiques
                stats = self.get_statistics()
                stats_data = {
                    'Métrique': ['Total pièces', 'Taille totale', 'Importance moyenne', 'Nombre de tags uniques'],
                    'Valeur': [stats['total'], self.format_file_size(stats['taille_totale']), 
                             f"{stats['importance_moyenne']:.1f}", len(stats['tags_populaires'])]
                }
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Statistiques', index=False)
                
                # Formater les colonnes
                workbook = writer.book
                worksheet = writer.sheets['Pièces']
                
                # Ajuster la largeur des colonnes
                for i, col in enumerate(df_pieces.columns):
                    column_len = max(df_pieces[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, min(column_len, 50))
            
            output.seek(0)
            return output.getvalue()
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère l'historique des actions"""
        return st.session_state.pieces_history[-limit:]
    
    def _get_categorie(self, type_piece: str) -> str:
        """Détermine la catégorie d'un type de pièce"""
        for categorie, info in self.CATEGORIES_PIECES.items():
            if type_piece in info['types']:
                return categorie
        return "Autre"
    
    def _update_global_metadata(self, piece: PieceProcedure, action: str):
        """Met à jour les métadonnées globales"""
        metadata = st.session_state.pieces_metadata
        
        if action == 'add':
            if piece.taille:
                metadata['total_size'] += piece.taille
            metadata['categories_count'][self._get_categorie(piece.type_piece)] += 1
            metadata['types_count'][piece.type_piece] += 1
            if piece.tags:
                metadata['tags'].update(piece.tags)
        
        elif action == 'remove':
            if piece.taille:
                metadata['total_size'] -= piece.taille
            metadata['categories_count'][self._get_categorie(piece.type_piece)] -= 1
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
        
        # Limiter la taille de l'historique
        if len(st.session_state.pieces_history) > 1000:
            st.session_state.pieces_history = st.session_state.pieces_history[-500:]
    
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """Calcule le hash SHA-256 d'un fichier"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formate la taille d'un fichier"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

# ========================= INTERFACE UTILISATEUR AMÉLIORÉE =========================

def display_pieces_interface():
    """Interface principale de gestion des pièces avec design moderne"""
    
    # Styles CSS personnalisés
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
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📎 Gestion des Pièces de Procédure")
    
    manager = PiecesManager()
    
    # Barre d'outils principale
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    
    with col1:
        if st.button("➕ Nouvelle pièce", key="new_piece_btn", type="primary", use_container_width=True):
            st.session_state.show_add_piece = True
    
    with col2:
        if st.button("📤 Import multiple", key="bulk_import_btn", use_container_width=True):
            st.session_state.show_bulk_import = True
    
    with col3:
        if st.button("⚡ Actions groupées", key="bulk_actions_btn", use_container_width=True):
            st.session_state.show_bulk_actions = True
    
    with col4:
        # Compteur de sélection
        selected_count = len(st.session_state.get('selected_pieces', []))
        if selected_count > 0:
            st.metric("Sélection", selected_count)
    
    with col5:
        if st.button("🔄", key="refresh_pieces", help="Actualiser"):
            st.rerun()
    
    # Zone d'ajout de pièce (modal)
    if st.session_state.get('show_add_piece'):
        display_add_piece_modal(manager)
    
    # Zone d'import multiple (modal)
    if st.session_state.get('show_bulk_import'):
        display_bulk_import_modal(manager)
    
    # Zone d'actions groupées (modal)
    if st.session_state.get('show_bulk_actions'):
        display_bulk_actions_modal(manager)
    
    # Onglets principaux avec icônes
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Vue d'ensemble",
        "🔍 Recherche avancée",
        "⭐ Favoris",
        "📊 Statistiques",
        "📜 Historique",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        display_pieces_overview(manager)
    
    with tab2:
        display_advanced_search(manager)
    
    with tab3:
        display_favoris(manager)
    
    with tab4:
        display_statistics_dashboard(manager)
    
    with tab5:
        display_history(manager)
    
    with tab6:
        display_settings(manager)

def display_pieces_overview(manager: PiecesManager):
    """Vue d'ensemble des pièces avec filtres rapides"""
    
    # Filtres rapides en ligne
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Recherche rapide",
            placeholder="Nom, type, tag...",
            key="quick_search"
        )
    
    with col2:
        selected_categorie = st.selectbox(
            "📁 Catégorie",
            ["Toutes"] + list(manager.CATEGORIES_PIECES.keys()),
            key="filter_category"
        )
    
    with col3:
        selected_statut = st.selectbox(
            "📌 Statut",
            ["Tous"] + [s['label'] for s in manager.STATUTS.values()],
            key="filter_status"
        )
    
    with col4:
        sort_by = st.selectbox(
            "🔀 Trier par",
            ["Date récente", "Nom A-Z", "Importance", "Taille"],
            key="sort_by"
        )
    
    with col5:
        view_mode = st.radio(
            "Vue",
            ["📋", "🎴", "📊"],
            horizontal=True,
            label_visibility="collapsed",
            key="view_mode"
        )
    
    # Préparer les filtres
    filters = {}
    if selected_categorie != "Toutes":
        filters['categorie'] = selected_categorie
    if selected_statut != "Tous":
        statut_key = [k for k, v in manager.STATUTS.items() if v['label'] == selected_statut][0]
        filters['statut'] = statut_key
    
    # Rechercher les pièces
    pieces = manager.search_pieces(search_query, filters)
    
    # Trier selon le critère
    if sort_by == "Date récente":
        pieces.sort(key=lambda p: p.date_ajout, reverse=True)
    elif sort_by == "Nom A-Z":
        pieces.sort(key=lambda p: p.nom.lower())
    elif sort_by == "Importance":
        pieces.sort(key=lambda p: p.importance, reverse=True)
    elif sort_by == "Taille":
        pieces.sort(key=lambda p: p.taille or 0, reverse=True)
    
    # Statistiques rapides
    if pieces:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(pieces))
        with col2:
            total_size = sum(p.taille or 0 for p in pieces)
            st.metric("Taille totale", manager.format_file_size(total_size))
        with col3:
            avg_importance = sum(p.importance for p in pieces) / len(pieces)
            st.metric("Importance moy.", f"{avg_importance:.1f}/10")
        with col4:
            favoris_count = len([p for p in pieces if p.id in st.session_state.pieces_favoris])
            st.metric("Favoris", favoris_count)
    
    # Affichage selon le mode
    if view_mode == "📋":  # Liste
        display_pieces_list_view(pieces, manager)
    elif view_mode == "🎴":  # Cartes
        display_pieces_cards_view(pieces, manager)
    else:  # Tableau
        display_pieces_table_view(pieces, manager)
    
    # Barre d'actions flottante si sélection
    if st.session_state.get('selected_pieces'):
        display_selection_actions(manager)

def display_pieces_list_view(pieces: List[PieceProcedure], manager: PiecesManager):
    """Affichage en liste avec design moderne"""
    
    if not pieces:
        st.info("🔍 Aucune pièce trouvée avec ces critères")
        return
    
    # Container pour la liste
    for piece in pieces:
        # Déterminer la catégorie et ses propriétés
        categorie = manager._get_categorie(piece.type_piece)
        cat_info = manager.CATEGORIES_PIECES[categorie]
        statut_info = manager.STATUTS[piece.statut]
        
        # Créer la carte de la pièce
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1.5, 1])
            
            with col1:
                # Checkbox et numéro
                selected = st.checkbox(
                    "",
                    key=f"select_{piece.id}",
                    label_visibility="collapsed"
                )
                if selected:
                    if 'selected_pieces' not in st.session_state:
                        st.session_state.selected_pieces = []
                    if piece.id not in st.session_state.selected_pieces:
                        st.session_state.selected_pieces.append(piece.id)
                else:
                    if 'selected_pieces' in st.session_state and piece.id in st.session_state.selected_pieces:
                        st.session_state.selected_pieces.remove(piece.id)
                
                st.caption(f"#{piece.numero_ordre}")
            
            with col2:
                # Titre et description
                col_title, col_fav = st.columns([10, 1])
                with col_title:
                    st.markdown(f"### {cat_info['icon']} {piece.nom}")
                with col_fav:
                    is_favori = piece.id in st.session_state.pieces_favoris
                    if st.button(
                        "⭐" if is_favori else "☆",
                        key=f"fav_{piece.id}",
                        help="Retirer des favoris" if is_favori else "Ajouter aux favoris"
                    ):
                        manager.toggle_favori(piece.id)
                        st.rerun()
                
                if piece.description:
                    st.caption(piece.description[:150] + "..." if len(piece.description) > 150 else piece.description)
                
                # Tags
                if piece.tags:
                    tags_html = ""
                    for tag in piece.tags[:5]:  # Limiter l'affichage
                        tags_html += f'<span class="tag-badge">{tag}</span>'
                    if len(piece.tags) > 5:
                        tags_html += f'<span class="tag-badge">+{len(piece.tags)-5}</span>'
                    st.markdown(tags_html, unsafe_allow_html=True)
                
                # Barre d'importance
                importance_color = (
                    "#4caf50" if piece.importance >= 7
                    else "#ff9800" if piece.importance >= 4
                    else "#f44336"
                )
                st.markdown(
                    f'<div class="importance-bar" style="background: linear-gradient(to right, {importance_color} {piece.importance*10}%, #e0e0e0 {piece.importance*10}%);"></div>',
                    unsafe_allow_html=True
                )
            
            with col3:
                # Informations
                st.write(f"**{piece.type_piece}**")
                st.caption(f"{statut_info['icon']} {statut_info['label']}")
                st.caption(f"📅 {piece.date_ajout.strftime('%d/%m/%Y à %H:%M')}")
                if piece.taille:
                    st.caption(f"📦 {manager.format_file_size(piece.taille)}")
                if piece.version > 1:
                    st.caption(f"📝 Version {piece.version}")
            
            with col4:
                # Métadonnées rapides
                if piece.date_modification:
                    st.caption(f"Modifié le {piece.date_modification.strftime('%d/%m')}")
                if piece.chemin_fichier:
                    st.caption("📎 Fichier attaché")
                if piece.metadata.get('confidentiel'):
                    st.caption("🔒 Confidentiel")
            
            with col5:
                # Actions
                col_view, col_menu = st.columns(2)
                
                with col_view:
                    if st.button("👁️", key=f"view_{piece.id}", help="Voir les détails"):
                        st.session_state.current_piece_id = piece.id
                        st.session_state.show_piece_detail = True
                
                with col_menu:
                    if st.button("⋮", key=f"menu_{piece.id}", help="Plus d'actions"):
                        st.session_state.show_piece_menu = piece.id
            
            # Menu contextuel
            if st.session_state.get('show_piece_menu') == piece.id:
                display_piece_context_menu(piece, manager)
            
            st.divider()
    
    # Modal de détail
    if st.session_state.get('show_piece_detail'):
        display_piece_detail_modal(manager, st.session_state.current_piece_id)

def display_piece_context_menu(piece: PieceProcedure, manager: PiecesManager):
    """Menu contextuel pour une pièce"""
    
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Éditer", key=f"edit_ctx_{piece.id}", use_container_width=True):
                st.session_state.edit_piece_id = piece.id
                st.session_state.show_edit_piece = True
                st.session_state.show_piece_menu = None
        
        with col2:
            if st.button("📋 Dupliquer", key=f"dup_ctx_{piece.id}", use_container_width=True):
                duplicate_piece(manager, piece)
                st.session_state.show_piece_menu = None
        
        with col3:
            if st.button("📤 Exporter", key=f"exp_ctx_{piece.id}", use_container_width=True):
                export_single_piece(manager, piece)
                st.session_state.show_piece_menu = None
        
        with col4:
            if piece.statut == "actif":
                if st.button("📦 Archiver", key=f"arch_ctx_{piece.id}", use_container_width=True):
                    manager.update_piece(piece.id, statut="archivé")
                    st.rerun()
            else:
                if st.button("♻️ Restaurer", key=f"rest_ctx_{piece.id}", use_container_width=True):
                    manager.update_piece(piece.id, statut="actif")
                    st.rerun()
        
        # Seconde ligne d'actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🏷️ Gérer tags", key=f"tags_ctx_{piece.id}", use_container_width=True):
                st.session_state.manage_tags_piece = piece.id
                st.session_state.show_piece_menu = None
        
        with col2:
            if st.button("📁 Déplacer", key=f"move_ctx_{piece.id}", use_container_width=True):
                st.session_state.move_piece = piece.id
                st.session_state.show_piece_menu = None
        
        with col3:
            importance = st.slider(
                "Importance",
                1, 10, piece.importance,
                key=f"imp_ctx_{piece.id}"
            )
            if importance != piece.importance:
                manager.update_piece(piece.id, importance=importance)
                st.rerun()
        
        with col4:
            if st.button("🗑️ Supprimer", key=f"del_ctx_{piece.id}", use_container_width=True):
                if st.checkbox("Confirmer", key=f"confirm_del_{piece.id}"):
                    manager.delete_piece(piece.id, permanent=True)
                    st.rerun()

def display_add_piece_modal(manager: PiecesManager):
    """Modal d'ajout de pièce améliorée"""
    
    with st.container():
        st.markdown("---")
        
        # En-tête de la modal
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("## ➕ Ajouter une nouvelle pièce")
        with col2:
            if st.button("❌ Fermer", key="close_add_modal"):
                st.session_state.show_add_piece = False
                st.rerun()
        
        # Tabs pour différents modes d'ajout
        tab1, tab2, tab3 = st.tabs(["📝 Saisie manuelle", "📎 Import fichier", "📚 Import multiple"])
        
        with tab1:
            display_manual_add_form(manager)
        
        with tab2:
            display_file_import_form(manager)
        
        with tab3:
            display_bulk_import_form(manager)

def display_manual_add_form(manager: PiecesManager):
    """Formulaire de saisie manuelle amélioré"""
    
    with st.form("add_piece_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input(
                "Nom de la pièce *",
                placeholder="Ex: Contrat de vente du 15/03/2024",
                help="Nom descriptif de la pièce"
            )
            
            # Sélection de catégorie puis type
            categorie = st.selectbox(
                "Catégorie *",
                list(manager.CATEGORIES_PIECES.keys()),
                help="Catégorie générale de la pièce"
            )
            
            type_piece = st.selectbox(
                "Type de pièce *",
                manager.CATEGORIES_PIECES[categorie]['types'],
                help="Type spécifique dans la catégorie"
            )
            
            importance = st.slider(
                "Importance",
                1, 10, 5,
                help="1: Peu important, 10: Critique"
            )
        
        with col2:
            numero_ordre = st.number_input(
                "Numéro d'ordre",
                min_value=1,
                value=len([p for p in st.session_state.pieces.values() if p.statut != 'supprimé']) + 1,
                help="Position dans la liste"
            )
            
            statut = st.selectbox(
                "Statut",
                [(k, v['label']) for k, v in manager.STATUTS.items() if k != 'supprimé'],
                format_func=lambda x: x[1],
                help="Statut initial de la pièce"
            )[0]
            
            dossier_id = st.selectbox(
                "Dossier",
                ["Aucun"] + list(st.session_state.get('dossiers', {}).keys()),
                help="Dossier de rattachement"
            )
            
            if dossier_id == "Aucun":
                dossier_id = None
            
            date_ajout = st.date_input(
                "Date d'ajout",
                value=datetime.now(),
                help="Date de création de la pièce"
            )
        
        # Description
        description = st.text_area(
            "Description",
            placeholder="Description détaillée de la pièce, contexte, contenu principal...",
            height=100,
            help="Description complète pour faciliter la recherche"
        )
        
        # Tags
        col1, col2 = st.columns(2)
        
        with col1:
            # Tags existants
            existing_tags = [tag for tag, _ in manager.get_all_tags()]
            selected_tags = st.multiselect(
                "Tags existants",
                existing_tags,
                help="Sélectionnez des tags existants"
            )
        
        with col2:
            # Nouveaux tags
            new_tags = st.text_input(
                "Nouveaux tags",
                placeholder="tag1, tag2, tag3",
                help="Séparez par des virgules"
            )
        
        # Métadonnées avancées
        with st.expander("⚙️ Métadonnées avancées"):
            col1, col2 = st.columns(2)
            
            with col1:
                is_confidentiel = st.checkbox("🔒 Confidentiel")
                requires_signature = st.checkbox("✍️ Nécessite signature")
            
            with col2:
                validity_date = st.date_input(
                    "Date de validité",
                    value=None,
                    help="Date jusqu'à laquelle la pièce est valide"
                )
                
                related_pieces = st.multiselect(
                    "Pièces liées",
                    [(p.id, p.nom) for p in st.session_state.pieces.values() if p.statut == 'actif'],
                    format_func=lambda x: x[1],
                    help="Sélectionnez des pièces en relation"
                )
            
            # JSON personnalisé
            custom_metadata = st.text_area(
                "Métadonnées personnalisées (JSON)",
                placeholder='{"avocat": "Me Dupont", "juridiction": "TGI Paris"}',
                height=100
            )
        
        # Boutons d'action
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submitted = st.form_submit_button(
                "✅ Ajouter la pièce",
                use_container_width=True,
                type="primary"
            )
        
        if submitted and nom:
            try:
                # Préparer les tags
                all_tags = selected_tags + [t.strip() for t in new_tags.split(',') if t.strip()]
                
                # Préparer les métadonnées
                metadata = {}
                if is_confidentiel:
                    metadata['confidentiel'] = True
                if requires_signature:
                    metadata['signature_requise'] = True
                if validity_date:
                    metadata['date_validite'] = validity_date.isoformat()
                if related_pieces:
                    metadata['pieces_liees'] = [p[0] for p in related_pieces]
                
                # Parser les métadonnées personnalisées
                if custom_metadata:
                    try:
                        custom = json.loads(custom_metadata)
                        metadata.update(custom)
                    except json.JSONDecodeError:
                        st.error("❌ Format JSON invalide pour les métadonnées")
                        return
                
                # Créer la pièce
                piece = PieceProcedure(
                    id=str(uuid.uuid4()),
                    nom=nom,
                    type_piece=type_piece,
                    numero_ordre=numero_ordre,
                    description=description if description else None,
                    date_ajout=datetime.combine(date_ajout, datetime.min.time()),
                    tags=all_tags,
                    statut=statut,
                    importance=importance,
                    metadata=metadata
                )
                
                # Ajouter la pièce
                piece_id = manager.add_piece(piece, dossier_id)
                
                st.success(f"✅ Pièce '{nom}' ajoutée avec succès!")
                st.balloons()
                
                # Proposer d'ajouter un fichier
                if st.button("📎 Ajouter un fichier à cette pièce"):
                    st.session_state.add_file_to_piece = piece_id
                    st.session_state.show_add_piece = False
                    st.rerun()
                
                # Fermer après délai
                import time
                time.sleep(2)
                st.session_state.show_add_piece = False
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

def duplicate_piece(manager: PiecesManager, piece: PieceProcedure):
    """Duplique une pièce"""
    try:
        new_piece = PieceProcedure(
            id=str(uuid.uuid4()),
            nom=f"{piece.nom} (copie)",
            type_piece=piece.type_piece,
            numero_ordre=len([p for p in st.session_state.pieces.values() if p.statut != 'supprimé']) + 1,
            description=piece.description,
            date_ajout=datetime.now(),
            chemin_fichier=piece.chemin_fichier,
            taille=piece.taille,
            hash_fichier=None,  # Nouveau hash pour éviter la duplication
            metadata=piece.metadata.copy(),
            tags=piece.tags.copy(),
            statut="actif",
            importance=piece.importance
        )
        
        manager.add_piece(new_piece)
        st.success(f"✅ Pièce '{piece.nom}' dupliquée avec succès!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la duplication : {str(e)}")

def export_single_piece(manager: PiecesManager, piece: PieceProcedure):
    """Exporte une seule pièce"""
    try:
        # Exporter en JSON
        export_data = manager.export_pieces([piece.id], format='json')
        
        st.download_button(
            "💾 Télécharger JSON",
            export_data,
            f"piece_{piece.nom.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
            "application/json",
            key=f"download_single_{piece.id}"
        )
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'export : {str(e)}")

# Ajout des autres fonctions d'affichage...
# (Les autres fonctions continueraient ici avec le même niveau de détail et d'amélioration)

# Point d'entrée principal
if __name__ == "__main__":
    display_pieces_interface()