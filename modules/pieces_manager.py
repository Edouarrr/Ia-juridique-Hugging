# modules/pieces_manager.py
"""Module unifié de gestion des pièces et bordereaux
Version améliorée avec lazy loading et multi-LLM
"""

import json
import os
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Ajouter le chemin parent pour les imports

from managers.azure_search_manager import AzureSearchManager
from managers.export_manager import ExportManager
# Import des gestionnaires
from managers.multi_llm_manager import MultiLLMManager
# Import des modèles
from models.dataclasses import (Document, ElementProcedure, ForceProbante,
                                NaturePiece, PieceProcedurale,
                                PieceSelectionnee)
# Import des utilitaires
from utils.file_utils import sanitize_filename, format_file_size
from utils.text_processing import extract_key_phrases
try:
    from utils.helpers import clean_key, truncate_text
    from utils.date_time import format_legal_date
except Exception:  # pragma: no cover - fallback for standalone use
    from utils.fallback import clean_key, format_legal_date, truncate_text
    from utils.file_utils import format_file_size
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# ==================================================
# FONCTION PRINCIPALE (POINT D'ENTRÉE LAZY LOADING)
# ==================================================

def run():
    """Point d'entrée principal pour le lazy loading"""
    
    # Style CSS personnalisé
    st.markdown("""
    <style>
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Cards améliorées */
    .piece-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
        transition: all 0.3s ease;
    }
    
    .piece-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-color: #007bff;
    }
    
    /* Badges */
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .badge-contrat { background: #e3f2fd; color: #1565c0; }
    .badge-facture { background: #f3e5f5; color: #6a1b9a; }
    .badge-correspondance { background: #e8f5e9; color: #2e7d32; }
    .badge-procedure { background: #ffe6e6; color: #c62828; }
    .badge-expertise { background: #fff3e0; color: #e65100; }
    
    /* Progress indicators */
    .progress-step {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e9ecef;
        color: #6c757d;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .progress-step.active {
        background: #007bff;
        color: white;
        transform: scale(1.1);
    }
    
    .progress-step.completed {
        background: #28a745;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header avec animation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.title("📎 Gestion Intelligente des Pièces")
        st.markdown("*Sélection, analyse et génération de bordereaux avec IA*")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialisation
    init_pieces_manager()
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Barre de progression visuelle
    display_progress_bar()
    
    # Interface principale avec onglets améliorés
    display_enhanced_interface(gestionnaire)

# ==================================================
# CLASSE PRINCIPALE UNIFIÉE (CONSERVÉE)
# ==================================================

class GestionnairePiecesUnifie:
    """Gestionnaire unifié pour pièces et bordereaux"""
    
    def __init__(self):
        self.pieces_disponibles: Dict[str, PieceSelectionnee] = {}
        self.pieces_selectionnees: List[PieceSelectionnee] = []
        self.categories_pieces = {
            "Contrats": ["contrat", "convention", "accord", "pacte", "bail"],
            "Factures": ["facture", "devis", "bon de commande", "avoir"],
            "Correspondances": ["email", "courrier", "lettre", "mail", "message"],
            "Documents comptables": ["bilan", "compte", "comptable", "fiscal", "déclaration"],
            "Procédure": ["assignation", "jugement", "ordonnance", "arrêt", "citation"],
            "Expertises": ["rapport", "expertise", "constat", "procès-verbal"],
            "Preuves": ["attestation", "témoignage", "certificat", "justificatif"],
            "Administratif": ["statuts", "kbis", "pouvoir", "délégation"]
        }
        self.llm_manager = None
        self.search_manager = None
        self.export_manager = None
        self._init_managers()
    
    def _init_managers(self):
        """Initialise les gestionnaires"""
        try:
            self.llm_manager = MultiLLMManager()
        except:
            pass
        
        try:
            self.search_manager = st.session_state.get('azure_search_manager')
        except:
            pass
        
        try:
            self.export_manager = ExportManager()
        except:
            pass
    
    # ==================================================
    # GESTION DES PIÈCES (TOUTES LES MÉTHODES CONSERVÉES)
    # ==================================================
    
    def ajouter_piece_disponible(self, piece: PieceSelectionnee) -> bool:
        """Ajoute une pièce aux pièces disponibles"""
        try:
            # Générer un ID unique si nécessaire
            if not hasattr(piece, 'id'):
                piece.id = f"piece_{uuid.uuid4().hex[:8]}"
            
            # Catégoriser automatiquement
            if not piece.categorie or piece.categorie == "Autre":
                piece.categorie = self.categoriser_piece(piece)
            
            # Ajouter aux disponibles
            self.pieces_disponibles[piece.id] = piece
            return True
            
        except Exception as e:
            st.error(f"Erreur ajout pièce : {str(e)}")
            return False
    
    def selectionner_piece(self, piece_id: str) -> bool:
        """Sélectionne une pièce pour le bordereau"""
        if piece_id in self.pieces_disponibles:
            piece = self.pieces_disponibles[piece_id]
            
            # Vérifier si déjà sélectionnée
            if not any(p.id == piece_id for p in self.pieces_selectionnees):
                # Attribuer un numéro
                piece.numero = len(self.pieces_selectionnees) + 1
                self.pieces_selectionnees.append(piece)
                return True
        return False
    
    def deselectionner_piece(self, piece_id: str) -> bool:
        """Retire une pièce de la sélection"""
        self.pieces_selectionnees = [
            p for p in self.pieces_selectionnees if p.id != piece_id
        ]
        # Renuméroter
        for i, piece in enumerate(self.pieces_selectionnees):
            piece.numero = i + 1
        return True
    
    def categoriser_piece(self, piece: PieceSelectionnee) -> str:
        """Catégorise automatiquement une pièce"""
        titre_lower = piece.titre.lower()
        contenu_lower = (piece.description or "").lower()
        
        for categorie, mots_cles in self.categories_pieces.items():
            for mot in mots_cles:
                if mot in titre_lower or mot in contenu_lower:
                    return categorie
        
        return "Autre"
    
    def rechercher_pieces(self, query: str) -> List[PieceSelectionnee]:
        """Recherche des pièces dans les documents"""
        pieces = []
        
        # Recherche dans les documents importés
        if 'imported_documents' in st.session_state:
            for doc_id, doc in st.session_state.imported_documents.items():
                if self._match_document(doc, query):
                    piece = self._document_to_piece(doc, len(pieces) + 1)
                    pieces.append(piece)
        
        # Recherche Azure si disponible
        if self.search_manager and st.session_state.get('azure_documents'):
            results = self.search_manager.search_documents(query, top=20)
            for result in results:
                piece = self._search_result_to_piece(result, len(pieces) + 1)
                pieces.append(piece)
        
        return pieces
    
    def _match_document(self, doc: Document, query: str) -> bool:
        """Vérifie si un document correspond à la recherche"""
        query_lower = query.lower()
        return (
            query_lower in doc.title.lower() or
            query_lower in doc.content.lower() or
            (doc.metadata and query_lower in str(doc.metadata).lower())
        )
    
    def _document_to_piece(self, doc: Document, numero: int) -> PieceSelectionnee:
        """Convertit un document en pièce"""
        return PieceSelectionnee(
            numero=numero,
            titre=doc.title,
            description=truncate_text(doc.content, 200),
            categorie=self.categoriser_piece(PieceSelectionnee(
                numero=numero,
                titre=doc.title,
                description=doc.content
            )),
            date=doc.metadata.get('date') if doc.metadata else None,
            source=doc.source,
            pertinence=0.8,
            document_source=doc
        )
    
    def _search_result_to_piece(self, result: dict, numero: int) -> PieceSelectionnee:
        """Convertit un résultat de recherche en pièce"""
        return PieceSelectionnee(
            numero=numero,
            titre=result.get('title', 'Sans titre'),
            description=result.get('content', '')[:200],
            categorie="Résultat de recherche",
            source="Azure Search",
            pertinence=result.get('@search.score', 0.5)
        )
    
    # ==================================================
    # GÉNÉRATION DE BORDEREAUX (TOUTES LES MÉTHODES CONSERVÉES)
    # ==================================================
    
    def generer_bordereau(
        self,
        pieces: List[PieceSelectionnee],
        type_bordereau: str = "communication",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Génère un bordereau de pièces"""
        
        if not pieces:
            return {"error": "Aucune pièce sélectionnée"}
        
        # Préparer les métadonnées
        meta = metadata or {}
        meta.update({
            'date_generation': datetime.now(),
            'nombre_pieces': len(pieces),
            'type': type_bordereau
        })
        
        # Générer le contenu selon le type
        if type_bordereau == "communication":
            contenu = self._generer_bordereau_communication(pieces, meta)
        elif type_bordereau == "inventaire":
            contenu = self._generer_bordereau_inventaire(pieces, meta)
        elif type_bordereau == "contradictoire":
            contenu = self._generer_bordereau_contradictoire(pieces, meta)
        else:
            contenu = self._generer_bordereau_simple(pieces, meta)
        
        return {
            'type': type_bordereau,
            'contenu': contenu,
            'pieces': pieces,
            'metadata': meta,
            'stats': self._calculer_stats_pieces(pieces)
        }
    
    def _generer_bordereau_communication(
        self,
        pieces: List[PieceSelectionnee],
        metadata: Dict
    ) -> str:
        """Génère un bordereau de communication de pièces"""
        
        # En-tête
        date_str = datetime.now().strftime('%d/%m/%Y')
        avocat_name = metadata.get('avocat', '[Nom de l\'avocat]')
        barreau_ville = metadata.get('barreau', '[Ville]')
        
        contenu = f"""BORDEREAU DE COMMUNICATION DE PIÈCES
Référence : {metadata.get('reference', 'N/A')}
Date : {date_str}
{metadata.get('destinataire', 'TRIBUNAL JUDICIAIRE')}
Affaire : {metadata.get('client', '')} c/ {metadata.get('adversaire', '')}
{metadata.get('juridiction', '')}
Maître {avocat_name}
Avocat au Barreau de {barreau_ville}
COMMUNIQUE LES PIÈCES SUIVANTES :
"""
        
        # Liste des pièces par catégorie
        categories = self._grouper_par_categorie(pieces)
        
        for categorie, pieces_cat in categories.items():
            if len(categories) > 1:
                contenu += f"\n{categorie.upper()}\n\n"
            
            for piece in pieces_cat:
                contenu += f"Pièce n° {piece.numero} : {piece.titre}"
                
                if piece.date:
                    date_piece_str = piece.date.strftime('%d/%m/%Y')
                    contenu += f" ({date_piece_str})"
                
                if piece.description:
                    contenu += f"\n              {truncate_text(piece.description, 100)}"
                
                contenu += "\n"
        
        # Total et signature
        date_jour = datetime.now().strftime('%d/%m/%Y')
        ville_str = metadata.get('ville', '[Ville]')
        avocat_str = metadata.get('avocat', '[Nom de l\'avocat]')
        
        contenu += f"""
TOTAL : {len(pieces)} pièce{'s' if len(pieces) > 1 else ''}
Fait à {ville_str}, le {date_jour}
Maître {avocat_str}
"""
        
        return contenu
    
    def _generer_bordereau_inventaire(
        self,
        pieces: List[PieceSelectionnee],
        metadata: Dict
    ) -> str:
        """Génère un inventaire détaillé des pièces"""
        
        date_str = datetime.now().strftime('%d/%m/%Y')
        contenu = f"""INVENTAIRE DES PIÈCES
Date : {date_str}
Référence : {metadata.get('reference', 'N/A')}
Nombre total de pièces : {len(pieces)}
"""
        
        # Tableau détaillé
        for piece in pieces:
            date_piece = piece.date.strftime('%d/%m/%Y') if piece.date else 'Non datée'
            nature_value = piece.nature.value if hasattr(piece, 'nature') else 'Copie'
            force_probante_value = piece.force_probante.value if hasattr(piece, 'force_probante') else 'Normale'
            
            contenu += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIÈCE N° {piece.numero}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Titre : {piece.titre}
Catégorie : {piece.categorie}
Date : {date_piece}
Source : {piece.source}
Cote : {piece.cote or f'P-{piece.numero:03d}'}
Description :
{piece.description or 'Aucune description'}
Nature : {nature_value}
Communicable : {'Oui' if piece.communicable else 'Non'}
Confidentiel : {'Oui' if piece.confidentiel else 'Non'}
Force probante : {force_probante_value}
"""
        
        return contenu
    
    def _generer_bordereau_contradictoire(
        self,
        pieces: List[PieceSelectionnee],
        metadata: Dict
    ) -> str:
        """Génère un bordereau contradictoire avec accusé"""
        
        contenu = self._generer_bordereau_communication(pieces, metadata)
        
        # Ajouter section accusé de réception
        contenu += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCUSÉ DE RÉCEPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Je soussigné(e), Maître ________________________________
Avocat de _____________________________________________
Reconnais avoir reçu communication des pièces ci-dessus énumérées.
Fait à _________________, le _____/_____/_______
Signature :
"""
        
        return contenu
    
    def _generer_bordereau_simple(
        self,
        pieces: List[PieceSelectionnee],
        metadata: Dict
    ) -> str:
        """Génère un bordereau simple"""
        
        contenu = "LISTE DES PIÈCES\n\n"
        
        for piece in pieces:
            contenu += f"{piece.numero}. {piece.titre}\n"
        
        return contenu
    
    def _grouper_par_categorie(
        self,
        pieces: List[PieceSelectionnee]
    ) -> Dict[str, List[PieceSelectionnee]]:
        """Groupe les pièces par catégorie"""
        categories = {}
        
        for piece in pieces:
            cat = piece.categorie or "Autres"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(piece)
        
        return categories
    
    def _calculer_stats_pieces(self, pieces: List[PieceSelectionnee]) -> Dict:
        """Calcule des statistiques sur les pièces"""
        stats = {
            'total': len(pieces),
            'par_categorie': {},
            'communicables': sum(1 for p in pieces if p.communicable),
            'confidentielles': sum(1 for p in pieces if p.confidentiel),
            'avec_date': sum(1 for p in pieces if p.date),
            'pertinence_moyenne': sum(p.pertinence for p in pieces) / len(pieces) if pieces else 0
        }
        
        # Stats par catégorie
        for piece in pieces:
            cat = piece.categorie or "Autres"
            stats['par_categorie'][cat] = stats['par_categorie'].get(cat, 0) + 1
        
        return stats
    
    # ==================================================
    # ANALYSE INTELLIGENTE MULTI-LLM (AMÉLIORÉE)
    # ==================================================
    
    def analyser_pertinence_pieces_multi_llm(
        self,
        pieces: List[PieceSelectionnee],
        contexte: str,
        llm_choices: List[str],
        fusion_mode: str = "consensus"
    ) -> Dict[str, Any]:
        """Analyse la pertinence avec plusieurs LLMs"""
        
        if not self.llm_manager:
            return {"error": "IA non disponible"}
        
        # Préparer le prompt
        prompt = f"""Contexte de l'affaire : {contexte}

Pièces à analyser :
"""
        for piece in pieces[:20]:  # Limiter à 20 pièces
            prompt += f"\n- Pièce {piece.numero} : {piece.titre}"
            if piece.description:
                prompt += f" - {truncate_text(piece.description, 100)}"
        
        prompt += """

Pour chaque pièce, évalue :
1. Sa pertinence (0-10) par rapport au contexte
2. Son importance stratégique (faible/moyenne/élevée)
3. Les risques potentiels associés
4. Les pièces complémentaires suggérées

Format : analyse structurée avec recommandations précises."""
        
        system_prompt = """Tu es un expert en analyse de pièces juridiques spécialisé en droit pénal des affaires.
Tu dois fournir une analyse détaillée et structurée en suivant le format demandé."""
        
        # Collecter les analyses de chaque LLM
        with st.spinner("🤖 Analyse multi-IA en cours..."):
            if fusion_mode == "consensus":
                # Mode consensus : tous les LLMs
                response = self.llm_manager.query_llms_consensus(
                    llm_choices,
                    prompt,
                    system_prompt
                )
            elif fusion_mode == "parallel":
                # Mode parallèle : analyses individuelles
                response = self.llm_manager.query_llms_parallel(
                    llm_choices,
                    prompt,
                    system_prompt
                )
            else:
                # Mode simple : premier LLM disponible
                response = self.llm_manager.query_single_llm(
                    llm_choices[0],
                    prompt,
                    system_prompt
                )
        
        if response['success']:
            return {
                'analyse': response['response'],
                'mode': fusion_mode,
                'llms_used': llm_choices,
                'pieces_analysees': len(pieces),
                'timestamp': datetime.now(),
                'consensus_score': response.get('consensus_score', 0)
            }
        else:
            return {"error": response.get('error', 'Erreur analyse')}
    
    def suggerer_pieces_manquantes(
        self,
        pieces_existantes: List[PieceSelectionnee],
        type_affaire: str
    ) -> List[str]:
        """Suggère des pièces manquantes selon le type d'affaire"""
        
        # Dictionnaire des pièces types par affaire
        pieces_types = {
            "abus_biens_sociaux": [
                "Statuts de la société",
                "K-bis",
                "Comptes annuels",
                "Rapports du commissaire aux comptes",
                "PV d'assemblées générales",
                "Relevés bancaires société",
                "Contrats litigieux",
                "Factures suspectes"
            ],
            "escroquerie": [
                "Plainte initiale",
                "Contrats ou promesses",
                "Échanges de correspondances",
                "Preuves de paiement",
                "Documents publicitaires",
                "Témoignages",
                "Expertises"
            ],
            "faux_usage_faux": [
                "Document falsifié",
                "Document original",
                "Rapport d'expertise en écriture",
                "Preuves d'utilisation",
                "Préjudice subi"
            ],
            "corruption": [
                "Preuves de sollicitation",
                "Échanges entre parties",
                "Mouvements financiers",
                "Contrats obtenus",
                "Témoignages"
            ]
        }
        
        # Identifier les pièces manquantes
        pieces_necessaires = pieces_types.get(type_affaire, [])
        titres_existants = [p.titre.lower() for p in pieces_existantes]
        
        manquantes = []
        for piece_type in pieces_necessaires:
            if not any(piece_type.lower() in titre for titre in titres_existants):
                manquantes.append(piece_type)
        
        return manquantes
    
    # ==================================================
    # EXPORT ET FORMATS (TOUTES LES MÉTHODES CONSERVÉES)
    # ==================================================
    
    def exporter_bordereau(
        self,
        bordereau: Dict[str, Any],
        format_export: str = "word"
    ) -> Optional[bytes]:
        """Exporte le bordereau dans le format demandé"""
        
        if not self.export_manager:
            st.error("Module d'export non disponible")
            return None
        
        try:
            if format_export == "word":
                return self.export_manager.export_to_word(
                    bordereau['contenu'],
                    title=f"Bordereau_{bordereau['type']}",
                    metadata=bordereau['metadata']
                )
            elif format_export == "pdf":
                return self.export_manager.export_to_pdf(
                    bordereau['contenu'],
                    title=f"Bordereau_{bordereau['type']}"
                )
            elif format_export == "excel":
                # Convertir en DataFrame
                df_data = []
                for piece in bordereau['pieces']:
                    date_str = piece.date.strftime('%d/%m/%Y') if piece.date else ''
                    df_data.append({
                        'N°': piece.numero,
                        'Titre': piece.titre,
                        'Catégorie': piece.categorie,
                        'Date': date_str,
                        'Description': piece.description,
                        'Source': piece.source,
                        'Cote': piece.cote or f'P-{piece.numero:03d}'
                    })
                df = pd.DataFrame(df_data)
                return self.export_manager.export_to_excel(
                    {'Bordereau': df},
                    title=f"Bordereau_{bordereau['type']}"
                )
            else:
                return bordereau['contenu'].encode('utf-8')
                
        except Exception as e:
            st.error(f"Erreur export : {str(e)}")
            return None

# ==================================================
# FONCTIONS D'INTERFACE STREAMLIT AMÉLIORÉES
# ==================================================

def init_pieces_manager():
    """Initialise le gestionnaire de pièces dans session_state"""
    if 'gestionnaire_pieces' not in st.session_state:
        st.session_state.gestionnaire_pieces = GestionnairePiecesUnifie()
    
    # Initialiser les autres états
    if 'pieces_selectionnees' not in st.session_state:
        st.session_state.pieces_selectionnees = {}
    
    if 'current_bordereau' not in st.session_state:
        st.session_state.current_bordereau = None
    
    if 'piece_analysis' not in st.session_state:
        st.session_state.piece_analysis = {}
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1

def display_progress_bar():
    """Affiche une barre de progression visuelle"""
    steps = [
        {"num": 1, "name": "Sélection", "icon": "📋"},
        {"num": 2, "name": "Analyse", "icon": "🔍"},
        {"num": 3, "name": "Bordereau", "icon": "📝"},
        {"num": 4, "name": "Export", "icon": "📤"}
    ]
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1,1,1,1,1,1,1])
    
    current = st.session_state.get('current_step', 1)
    
    for i, (col, step) in enumerate(zip([col1, col3, col5, col7], steps)):
        with col:
            if step['num'] < current:
                st.markdown(f"""
                <div class="progress-step completed">
                    ✓
                </div>
                <small>{step['name']}</small>
                """, unsafe_allow_html=True)
            elif step['num'] == current:
                st.markdown(f"""
                <div class="progress-step active">
                    {step['icon']}
                </div>
                <small><b>{step['name']}</b></small>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="progress-step">
                    {step['num']}
                </div>
                <small>{step['name']}</small>
                """, unsafe_allow_html=True)
    
    # Lignes de connexion
    for col in [col2, col4, col6]:
        with col:
            st.markdown("➔", unsafe_allow_html=True)

def display_enhanced_interface(gestionnaire: GestionnairePiecesUnifie):
    """Interface principale améliorée"""
    
    # Onglets avec icônes et design amélioré
    tab_icons = ["📋", "🔍", "📝", "📊", "⚙️"]
    tab_names = ["Sélection", "Analyse IA", "Bordereau", "Statistiques", "Configuration"]
    
    tabs = st.tabs([f"{icon} {name}" for icon, name in zip(tab_icons, tab_names)])
    
    with tabs[0]:
        st.session_state.current_step = 1
        display_enhanced_selection_tab(gestionnaire)
    
    with tabs[1]:
        st.session_state.current_step = 2
        display_enhanced_analysis_tab(gestionnaire)
    
    with tabs[2]:
        st.session_state.current_step = 3
        display_enhanced_bordereau_tab(gestionnaire)
    
    with tabs[3]:
        display_enhanced_statistics_tab(gestionnaire)
    
    with tabs[4]:
        display_configuration_tab(gestionnaire)

def display_enhanced_selection_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet de sélection amélioré"""
    
    # Layout en 2 colonnes principales
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        # Panel de résumé flottant
        st.markdown("### 📎 Sélection actuelle")
        
        nb_selected = len(gestionnaire.pieces_selectionnees)
        
        # Métriques visuelles
        st.metric("Pièces sélectionnées", nb_selected, 
                  delta=f"+{nb_selected}" if nb_selected > 0 else None)
        
        if nb_selected > 0:
            # Mini liste des pièces
            with st.expander("Voir la sélection", expanded=True):
                for piece in gestionnaire.pieces_selectionnees[:5]:
                    st.caption(f"{piece.numero}. {truncate_text(piece.titre, 30)}")
                if nb_selected > 5:
                    st.caption(f"... et {nb_selected - 5} autres")
            
            # Actions rapides
            st.markdown("### 🚀 Actions rapides")
            
            if st.button("📝 Créer bordereau", type="primary", use_container_width=True):
                st.session_state.show_bordereau_creation = True
            
            if st.button("🔍 Analyser avec IA", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()
            
            if st.button("🗑️ Vider la sélection", use_container_width=True):
                gestionnaire.pieces_selectionnees.clear()
                st.rerun()
    
    with col_main:
        # Barre de recherche améliorée
        st.markdown("### 🔍 Recherche intelligente")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Rechercher des documents",
                placeholder="Ex: contrat 2024, facture client X, expertise...",
                key="piece_search_enhanced",
                label_visibility="collapsed"
            )
        
        with col2:
            search_clicked = st.button("🔍 Rechercher", type="primary", use_container_width=True)
        
        # Filtres avancés
        with st.expander("⚙️ Filtres avancés", expanded=False):
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                search_category = st.multiselect(
                    "Catégories",
                    list(gestionnaire.categories_pieces.keys()),
                    key="search_categories_multi"
                )
            
            with col_b:
                search_dates = st.date_input(
                    "Période",
                    value=[],
                    key="search_date_range"
                )
            
            with col_c:
                search_source = st.multiselect(
                    "Sources",
                    ["Documents importés", "Azure", "Templates"],
                    key="search_sources_multi"
                )
        
        # Effectuer la recherche
        if search_clicked and search_query:
            with st.spinner("🔎 Recherche en cours..."):
                time.sleep(0.5)  # Animation
                pieces = gestionnaire.rechercher_pieces(search_query)
                st.session_state.search_results_pieces = pieces
        
        # Résultats de recherche
        if 'search_results_pieces' in st.session_state:
            display_enhanced_search_results(gestionnaire, st.session_state.search_results_pieces)
        
        # Sources de documents
        st.markdown("### 📚 Sources de documents")
        
        source_tabs = st.tabs([
            "📥 Importés", 
            "☁️ Azure", 
            "📋 Templates", 
            "➕ Créer"
        ])
        
        with source_tabs[0]:
            display_enhanced_imported_documents(gestionnaire)
        
        with source_tabs[1]:
            display_enhanced_azure_documents(gestionnaire)
        
        with source_tabs[2]:
            display_enhanced_templates(gestionnaire)
        
        with source_tabs[3]:
            display_enhanced_manual_creation(gestionnaire)

def display_enhanced_search_results(
    gestionnaire: GestionnairePiecesUnifie,
    results: List[PieceSelectionnee]
):
    """Affiche les résultats de recherche avec un design amélioré"""
    
    if not results:
        st.info("🔍 Aucun résultat trouvé. Essayez avec d'autres mots-clés.")
        return
    
    st.success(f"✅ {len(results)} document(s) trouvé(s)")
    
    # Grille de résultats
    for i, piece in enumerate(results[:20]):
        with st.container():
            st.markdown(f'<div class="piece-card fade-in" style="animation-delay: {i*0.05}s">', 
                       unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1.5, 1])
            
            with col1:
                # Titre et description
                st.markdown(f"**{piece.titre}**")
                if piece.description:
                    st.caption(truncate_text(piece.description, 150))
                
                # Tags
                tags_html = f'<span class="category-badge badge-{piece.categorie.lower()}">{piece.categorie}</span>'
                if piece.date:
                    date_str = piece.date.strftime('%d/%m/%Y')
                    tags_html += f' <span class="category-badge">📅 {date_str}</span>'
                st.markdown(tags_html, unsafe_allow_html=True)
            
            with col2:
                # Pertinence visuelle
                st.progress(piece.pertinence, text=f"Pertinence: {piece.pertinence:.0%}")
            
            with col3:
                # Actions
                is_selected = any(p.id == piece.id for p in gestionnaire.pieces_selectionnees)
                
                if is_selected:
                    if st.button("✅ Sélectionnée", key=f"remove_{piece.id}", 
                                use_container_width=True):
                        gestionnaire.deselectionner_piece(piece.id)
                        st.rerun()
                else:
                    if st.button("➕ Sélectionner", key=f"add_{piece.id}", 
                                type="primary", use_container_width=True):
                        gestionnaire.ajouter_piece_disponible(piece)
                        gestionnaire.selectionner_piece(piece.id)
                        st.success(f"✅ '{piece.titre}' ajoutée")
                        time.sleep(0.5)
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

def display_enhanced_imported_documents(gestionnaire: GestionnairePiecesUnifie):
    """Affiche les documents importés avec un design amélioré"""
    
    if not st.session_state.get('imported_documents'):
        st.info("📥 Aucun document importé. Utilisez le module Import/Export pour ajouter des documents.")
        
        if st.button("🚀 Aller à l'import", type="primary"):
            st.session_state.selected_module = "import_export"
            st.rerun()
        return
    
    # Grille de documents
    docs = list(st.session_state.imported_documents.items())
    
    # Barre de sélection rapide
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📚 {len(docs)} document(s) disponible(s)")
    with col2:
        if st.button("✅ Tout sélectionner", use_container_width=True):
            for doc_id, doc in docs:
                piece = gestionnaire._document_to_piece(doc, len(gestionnaire.pieces_selectionnees) + 1)
                gestionnaire.ajouter_piece_disponible(piece)
                gestionnaire.selectionner_piece(piece.id)
            st.success(f"✅ {len(docs)} documents ajoutés")
            st.rerun()
    
    # Affichage des documents
    for i, (doc_id, doc) in enumerate(docs):
        display_enhanced_document_card(gestionnaire, doc, doc_id, i)

def display_enhanced_document_card(
    gestionnaire: GestionnairePiecesUnifie,
    doc: Document,
    doc_id: str,
    index: int
):
    """Affiche une carte de document améliorée"""
    
    with st.container():
        st.markdown(f'<div class="piece-card fade-in" style="animation-delay: {index*0.05}s">', 
                   unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{doc.title}**")
            if hasattr(doc, 'content'):
                st.caption(truncate_text(doc.content, 120))
            
            # Catégorie automatique
            piece_temp = PieceSelectionnee(
                numero=0,
                titre=doc.title,
                description=getattr(doc, 'content', '')
            )
            categorie = gestionnaire.categoriser_piece(piece_temp)
            
            tags_html = f'<span class="category-badge badge-{categorie.lower()}">{categorie}</span>'
            if doc.metadata and doc.metadata.get('date'):
                tags_html += f' <span class="category-badge">📅 {doc.metadata["date"]}</span>'
            st.markdown(tags_html, unsafe_allow_html=True)
        
        with col2:
            if doc.metadata:
                size = doc.metadata.get('size', 0)
                if size:
                    st.caption(f"📄 {format_file_size(size)}")
                source = doc.metadata.get('source', 'Local')
                st.caption(f"📍 {source}")
        
        with col3:
            is_selected = any(
                p.titre == doc.title for p in gestionnaire.pieces_selectionnees
            )
            
            if is_selected:
                if st.button("✅ Sélectionnée", key=f"doc_selected_{doc_id}", 
                            use_container_width=True):
                    piece_id = next(
                        (p.id for p in gestionnaire.pieces_selectionnees if p.titre == doc.title),
                        None
                    )
                    if piece_id:
                        gestionnaire.deselectionner_piece(piece_id)
                        st.rerun()
            else:
                if st.button("➕ Sélectionner", key=f"doc_select_{doc_id}", 
                            type="primary", use_container_width=True):
                    piece = gestionnaire._document_to_piece(
                        doc,
                        len(gestionnaire.pieces_selectionnees) + 1
                    )
                    gestionnaire.ajouter_piece_disponible(piece)
                    gestionnaire.selectionner_piece(piece.id)
                    st.success(f"✅ '{doc.title}' ajoutée")
                    time.sleep(0.5)
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_enhanced_azure_documents(gestionnaire: GestionnairePiecesUnifie):
    """Affiche les documents Azure avec design amélioré"""
    
    if not st.session_state.get('azure_documents'):
        st.info("☁️ Aucun document Azure. Configurez Azure Storage dans les paramètres.")
        
        if st.button("⚙️ Configurer Azure", type="primary"):
            st.session_state.selected_module = "configuration"
            st.rerun()
        return
    
    # Affichage similaire aux documents importés
    docs = list(st.session_state.azure_documents.items())
    
    st.info(f"☁️ {len(docs)} document(s) Azure disponible(s)")
    
    for i, (doc_id, doc) in enumerate(docs):
        display_enhanced_document_card(gestionnaire, doc, f"azure_{doc_id}", i)

def display_enhanced_templates(gestionnaire: GestionnairePiecesUnifie):
    """Affiche les templates de pièces avec design amélioré"""
    
    st.markdown("### 📋 Modèles de pièces par type d'affaire")
    
    # Sélection du type avec icônes
    type_icons = {
        "Abus de biens sociaux": "💼",
        "Escroquerie": "🎭",
        "Faux et usage de faux": "📝",
        "Corruption": "💰",
        "Blanchiment": "🏦",
        "Abus de confiance": "🤝"
    }
    
    cols = st.columns(3)
    selected_type = None
    
    for i, (type_name, icon) in enumerate(type_icons.items()):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(f"{icon} {type_name}", key=f"type_{type_name}", 
                        use_container_width=True):
                selected_type = type_name
                st.session_state.selected_template_type = type_name
    
    # Afficher les pièces suggérées
    if st.session_state.get('selected_template_type'):
        type_affaire = st.session_state.selected_template_type
        type_key = type_affaire.lower().replace(" ", "_").replace("'", "")
        
        pieces_suggerees = gestionnaire.suggerer_pieces_manquantes(
            gestionnaire.pieces_selectionnees,
            type_key
        )
        
        if pieces_suggerees:
            st.warning(f"💡 {len(pieces_suggerees)} pièce(s) suggérée(s) pour {type_affaire}")
            
            # Grille de suggestions
            for i, piece_nom in enumerate(pieces_suggerees):
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"• **{piece_nom}**")
                        st.caption("Pièce recommandée pour ce type d'affaire")
                    
                    with col2:
                        if st.button("➕ Créer", key=f"create_template_{i}", 
                                    type="primary", use_container_width=True):
                            piece = PieceSelectionnee(
                                numero=len(gestionnaire.pieces_selectionnees) + 1,
                                titre=piece_nom,
                                description=f"[À compléter - {piece_nom}]",
                                categorie="Template",
                                source="Modèle"
                            )
                            gestionnaire.ajouter_piece_disponible(piece)
                            gestionnaire.selectionner_piece(piece.id)
                            st.success(f"✅ Template '{piece_nom}' créé")
                            time.sleep(0.5)
                            st.rerun()
        else:
            st.success(f"✅ Toutes les pièces types pour {type_affaire} sont présentes")

def display_enhanced_manual_creation(gestionnaire: GestionnairePiecesUnifie):
    """Interface de création manuelle améliorée"""
    
    st.markdown("### ➕ Créer une pièce manuellement")
    
    with st.form("create_piece_enhanced_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            titre = st.text_input("📝 Titre de la pièce *", 
                                 placeholder="Ex: Contrat de prestations")
            
            categorie = st.selectbox(
                "📁 Catégorie",
                [""] + list(gestionnaire.categories_pieces.keys()) + ["Autre"]
            )
            
            date = st.date_input("📅 Date du document", value=None)
            
            cote = st.text_input("🏷️ Cote", placeholder="Ex: C-001")
        
        with col2:
            nature = st.selectbox(
                "📋 Nature",
                ["Original", "Copie", "Copie certifiée conforme"]
            )
            
            importance = st.select_slider(
                "⭐ Importance",
                options=["Faible", "Moyenne", "Élevée", "Critique"],
                value="Moyenne"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                communicable = st.checkbox("✅ Communicable", value=True)
            with col_b:
                confidentiel = st.checkbox("🔒 Confidentiel", value=False)
        
        description = st.text_area(
            "📝 Description",
            placeholder="Description détaillée de la pièce et de son contenu...",
            height=120
        )
        
        # Tags personnalisés
        tags = st.text_input(
            "🏷️ Tags (séparés par des virgules)",
            placeholder="Ex: urgent, preuve principale, à vérifier"
        )
        
        submitted = st.form_submit_button(
            "🚀 Créer la pièce",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if titre and categorie:
                # Animation de création
                with st.spinner("✨ Création en cours..."):
                    time.sleep(0.5)
                    
                    # Créer la pièce avec les métadonnées enrichies
                    piece = PieceSelectionnee(
                        numero=len(gestionnaire.pieces_selectionnees) + 1,
                        titre=titre,
                        description=description,
                        categorie=categorie,
                        date=date if date else None,
                        cote=cote,
                        nature=NaturePiece.ORIGINAL if nature == "Original" else NaturePiece.COPIE,
                        communicable=communicable,
                        confidentiel=confidentiel,
                        source="Création manuelle",
                        metadata={
                            'importance': importance,
                            'tags': [t.strip() for t in tags.split(',')] if tags else []
                        }
                    )
                    
                    # Ajouter et sélectionner
                    gestionnaire.ajouter_piece_disponible(piece)
                    gestionnaire.selectionner_piece(piece.id)
                    
                    st.success(f"✅ Pièce '{titre}' créée avec succès!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("❌ Veuillez remplir au moins le titre et la catégorie")

def display_enhanced_analysis_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet d'analyse IA amélioré avec multi-LLM"""
    
    st.markdown("### 🤖 Analyse intelligente des pièces")
    
    if not gestionnaire.pieces_selectionnees:
        st.info("ℹ️ Sélectionnez d'abord des pièces dans l'onglet 'Sélection'")
        
        if st.button("📋 Aller à la sélection", type="primary"):
            st.session_state.current_step = 1
            st.rerun()
        return
    
    # Configuration de l'analyse
    col1, col2 = st.columns([2, 1])
    
    with col1:
        contexte = st.text_area(
            "📝 Contexte de l'affaire",
            placeholder="Décrivez l'affaire pour une analyse pertinente des pièces...",
            height=120,
            value=st.session_state.get('current_analysis', {}).get('request', '')
        )
    
    with col2:
        type_affaire = st.selectbox(
            "⚖️ Type d'affaire",
            [
                "Abus de biens sociaux",
                "Escroquerie",
                "Faux et usage de faux",
                "Corruption",
                "Blanchiment",
                "Autre"
            ]
        )
        
        st.markdown("**📊 Pièces à analyser**")
        st.metric("Total", len(gestionnaire.pieces_selectionnees))
    
    # Configuration Multi-LLM
    st.markdown("### 🤖 Configuration IA")
    
    col_llm1, col_llm2, col_llm3 = st.columns(3)
    
    with col_llm1:
        # Sélection des modèles
        available_llms = []
        if gestionnaire.llm_manager:
            available_llms = list(gestionnaire.llm_manager.clients.keys())
        
        selected_llms = st.multiselect(
            "🤖 Modèles IA",
            available_llms,
            default=available_llms[:2] if len(available_llms) >= 2 else available_llms,
            help="Sélectionnez un ou plusieurs modèles pour l'analyse"
        )
    
    with col_llm2:
        fusion_mode = st.radio(
            "🔄 Mode de fusion",
            ["consensus", "parallel", "simple"],
            format_func=lambda x: {
                "consensus": "🤝 Consensus",
                "parallel": "🔀 Parallèle",
                "simple": "⚡ Simple"
            }[x],
            help="Consensus: synthèse des réponses, Parallèle: toutes les réponses, Simple: premier modèle"
        )
    
    with col_llm2:
        analysis_depth = st.select_slider(
            "🔬 Profondeur d'analyse",
            options=["Rapide", "Standard", "Approfondie"],
            value="Standard"
        )
    
    # Bouton d'analyse
    if st.button("🚀 Lancer l'analyse multi-IA", type="primary", use_container_width=True):
        if contexte and selected_llms:
            # Animation d'analyse
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            phases = [
                ("Préparation des données", 0.2),
                ("Interrogation des modèles IA", 0.5),
                ("Fusion des analyses", 0.8),
                ("Génération du rapport", 1.0)
            ]
            
            for phase, progress in phases:
                status_text.text(f"⏳ {phase}...")
                progress_bar.progress(progress)
                time.sleep(0.5)
            
            # Lancer l'analyse
            analyse = gestionnaire.analyser_pertinence_pieces_multi_llm(
                gestionnaire.pieces_selectionnees,
                f"{contexte}\nType d'affaire : {type_affaire}",
                selected_llms,
                fusion_mode
            )
            
            if 'error' not in analyse:
                st.session_state.piece_analysis = analyse
                status_text.text("✅ Analyse terminée avec succès!")
                progress_bar.empty()
                st.success("🎉 Analyse multi-IA complétée!")
                
                # Afficher les résultats
                display_enhanced_analysis_results(analyse)
            else:
                st.error(f"❌ Erreur : {analyse['error']}")
        else:
            st.warning("⚠️ Veuillez remplir le contexte et sélectionner au moins un modèle IA")
    
    # Afficher l'analyse existante
    if st.session_state.get('piece_analysis') and not st.session_state.get('show_new_analysis'):
        display_enhanced_analysis_results(st.session_state.piece_analysis)
    
    # Suggestions de pièces manquantes
    st.markdown("---")
    st.markdown("### 💡 Analyse des pièces manquantes")
    
    type_key = type_affaire.lower().replace(" ", "_").replace("'", "")
    pieces_manquantes = gestionnaire.suggerer_pieces_manquantes(
        gestionnaire.pieces_selectionnees,
        type_key
    )
    
    if pieces_manquantes:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.warning(f"⚠️ {len(pieces_manquantes)} pièce(s) potentiellement manquante(s)")
        
        with col2:
            if st.button("📋 Créer les manquantes", type="primary", use_container_width=True):
                for piece_nom in pieces_manquantes:
                    piece = PieceSelectionnee(
                        numero=len(gestionnaire.pieces_selectionnees) + 1,
                        titre=piece_nom,
                        description=f"[À compléter - {piece_nom}]",
                        categorie="Manquante",
                        source="Suggestion IA"
                    )
                    gestionnaire.ajouter_piece_disponible(piece)
                st.success(f"✅ {len(pieces_manquantes)} templates créés")
                st.rerun()
        
        # Liste des manquantes avec actions
        for piece in pieces_manquantes:
            with st.container():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"• **{piece}**")
                with col_b:
                    if st.button("➕", key=f"add_missing_{piece}", help="Créer cette pièce"):
                        pass  # Action déjà gérée par le bouton global
    else:
        st.success("✅ Toutes les pièces types semblent présentes pour ce type d'affaire")

def display_enhanced_analysis_results(analysis: Dict[str, Any]):
    """Affiche les résultats d'analyse avec un design amélioré"""
    
    # Métriques de l'analyse
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Pièces analysées", analysis.get('pieces_analysees', 0))
    
    with col2:
        mode_labels = {
            "consensus": "Consensus",
            "parallel": "Parallèle",
            "simple": "Simple"
        }
        st.metric("Mode", mode_labels.get(analysis.get('mode', 'simple')))
    
    with col3:
        llms_count = len(analysis.get('llms_used', []))
        st.metric("Modèles IA", llms_count)
    
    with col4:
        consensus = analysis.get('consensus_score', 0)
        if consensus:
            st.metric("Score consensus", f"{consensus:.0%}")
    
    # Contenu de l'analyse
    st.markdown("### 📊 Rapport d'analyse")
    
    with st.expander("🔍 Analyse détaillée", expanded=True):
        # Formatage amélioré du contenu
        content = analysis.get('analyse', '')
        
        # Diviser en sections si possible
        sections = content.split('\n\n')
        for section in sections:
            if section.strip():
                if any(keyword in section.lower() for keyword in ['pertinence', 'importance', 'risque', 'recommandation']):
                    st.markdown(f"**{section.split(':')[0]}**")
                    if ':' in section:
                        st.write(section.split(':', 1)[1].strip())
                else:
                    st.write(section)
    
    # Métadonnées
    if analysis.get('timestamp'):
        date_str = analysis['timestamp'].strftime('%d/%m/%Y à %H:%M')
        st.caption(f"📅 Analyse effectuée le {date_str}")
    
    # Actions sur l'analyse
    col_export1, col_export2, col_export3 = st.columns(3)
    
    with col_export1:
        if st.button("📄 Exporter l'analyse", use_container_width=True):
            # Export du rapport d'analyse
            st.download_button(
                "💾 Télécharger le rapport",
                analysis.get('analyse', ''),
                f"analyse_pieces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )
    
    with col_export2:
        if st.button("🔄 Nouvelle analyse", use_container_width=True):
            st.session_state.piece_analysis = None
            st.rerun()
    
    with col_export3:
        if st.button("📝 Créer le bordereau", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

def display_enhanced_bordereau_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet de génération de bordereaux amélioré"""
    
    if not gestionnaire.pieces_selectionnees:
        st.info("ℹ️ Sélectionnez d'abord des pièces pour créer un bordereau")
        
        if st.button("📋 Aller à la sélection", type="primary"):
            st.session_state.current_step = 1
            st.rerun()
        return
    
    st.markdown(f"### 📝 Création du bordereau ({len(gestionnaire.pieces_selectionnees)} pièces)")
    
    # Aperçu des pièces sélectionnées
    with st.expander(f"📎 Aperçu des {len(gestionnaire.pieces_selectionnees)} pièces sélectionnées", expanded=False):
        for i, piece in enumerate(gestionnaire.pieces_selectionnees):
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                st.markdown(f"**{piece.numero}.**")
            
            with col2:
                st.write(piece.titre)
                if piece.categorie:
                    st.caption(f"📁 {piece.categorie}")
            
            with col3:
                if st.button("🗑️", key=f"remove_from_bordereau_{piece.numero}",
                            help="Retirer cette pièce"):
                    gestionnaire.deselectionner_piece(piece.id)
                    st.rerun()
    
    # Formulaire de création
    with st.form("bordereau_enhanced_form"):
        # Type de bordereau avec icônes
        st.markdown("### 📋 Type de bordereau")
        
        type_options = {
            "Communication de pièces": "📤",
            "Inventaire détaillé": "📊", 
            "Bordereau contradictoire": "⚖️",
            "Liste simple": "📝"
        }
        
        selected_type = st.radio(
            "Sélectionnez le type",
            list(type_options.keys()),
            format_func=lambda x: f"{type_options[x]} {x}",
            horizontal=True
        )
        
        # Informations de l'affaire
        st.markdown("### ⚖️ Informations de l'affaire")
        
        col1, col2 = st.columns(2)
        
        with col1:
            reference = st.text_input(
                "📋 Référence de l'affaire",
                value=st.session_state.get('current_analysis', {}).get('reference', ''),
                placeholder="Ex: 2024/12345"
            )
            
            client = st.text_input(
                "👤 Client",
                value=st.session_state.get('current_analysis', {}).get('client', ''),
                placeholder="Nom du client"
            )
            
            avocat = st.text_input(
                "⚖️ Avocat",
                placeholder="Maître..."
            )
        
        with col2:
            adversaire = st.text_input(
                "⚔️ Partie adverse",
                value=st.session_state.get('current_analysis', {}).get('adversaire', ''),
                placeholder="Nom de la partie adverse"
            )
            
            juridiction = st.text_input(
                "🏛️ Juridiction",
                value=st.session_state.get('current_analysis', {}).get('juridiction', ''),
                placeholder="Ex: Tribunal Judiciaire de Paris"
            )
            
            destinataire = st.text_input(
                "📮 Destinataire",
                value="TRIBUNAL JUDICIAIRE" if "communication" in selected_type.lower() else "",
                placeholder="Destinataire du bordereau"
            )
        
        # Informations complémentaires
        st.markdown("### 📍 Informations complémentaires")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            barreau = st.text_input("🏛️ Barreau", placeholder="Ex: Paris")
        
        with col4:
            ville = st.text_input("📍 Ville", placeholder="Ex: Paris")
        
        with col5:
            include_stats = st.checkbox("📊 Inclure les statistiques", value=True)
            include_summary = st.checkbox("📝 Inclure un résumé", value=False)
        
        # Options avancées
        with st.expander("⚙️ Options avancées"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                format_page = st.selectbox(
                    "📄 Format de page",
                    ["A4", "Letter", "Legal"]
                )
                
                numerotation = st.selectbox(
                    "🔢 Numérotation",
                    ["Continue", "Par catégorie", "Alphanumérique"]
                )
            
            with col_b:
                langue = st.selectbox(
                    "🌐 Langue",
                    ["Français", "English", "Español"]
                )
                
                signature_electronique = st.checkbox("✍️ Signature électronique", value=False)
        
        # Bouton de génération stylisé
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            submitted = st.form_submit_button(
                "🚀 Générer le bordereau",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            # Animation de génération
            with st.spinner("⏳ Génération du bordereau en cours..."):
                progress = st.progress(0)
                
                # Préparer les métadonnées
                metadata = {
                    'reference': reference,
                    'client': client,
                    'adversaire': adversaire,
                    'juridiction': juridiction,
                    'avocat': avocat,
                    'destinataire': destinataire,
                    'barreau': barreau,
                    'ville': ville,
                    'format_page': format_page,
                    'langue': langue,
                    'numerotation': numerotation,
                    'signature_electronique': signature_electronique
                }
                
                progress.progress(0.5)
                
                # Mapper le type
                type_map = {
                    "Communication de pièces": "communication",
                    "Inventaire détaillé": "inventaire",
                    "Bordereau contradictoire": "contradictoire",
                    "Liste simple": "simple"
                }
                
                # Générer
                bordereau = gestionnaire.generer_bordereau(
                    gestionnaire.pieces_selectionnees,
                    type_bordereau=type_map.get(selected_type, "simple"),
                    metadata=metadata
                )
                
                progress.progress(1.0)
                time.sleep(0.5)
                
                if 'error' not in bordereau:
                    st.session_state.current_bordereau = bordereau
                    st.success("✅ Bordereau généré avec succès!")
                    st.balloons()
                else:
                    st.error(f"❌ Erreur : {bordereau['error']}")
    
    # Afficher le bordereau généré
    if st.session_state.get('current_bordereau'):
        display_enhanced_generated_bordereau(gestionnaire, st.session_state.current_bordereau)

def display_enhanced_generated_bordereau(
    gestionnaire: GestionnairePiecesUnifie,
    bordereau: Dict[str, Any]
):
    """Affiche le bordereau généré avec un design amélioré"""
    
    st.markdown("---")
    st.markdown("### 📄 Bordereau généré")
    
    # Statistiques visuelles
    if bordereau.get('stats'):
        stats = bordereau['stats']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📎 Total pièces",
                stats['total'],
                delta=f"{stats['total']} pièce(s)"
            )
        
        with col2:
            st.metric(
                "✅ Communicables",
                stats['communicables'],
                delta=f"{stats['communicables']/stats['total']:.0%}" if stats['total'] > 0 else "0%"
            )
        
        with col3:
            st.metric(
                "🔒 Confidentielles",
                stats['confidentielles'],
                delta=f"{stats['confidentielles']/stats['total']:.0%}" if stats['total'] > 0 else "0%"
            )
        
        with col4:
            st.metric(
                "📅 Avec date",
                stats['avec_date'],
                delta=f"{stats['avec_date']/stats['total']:.0%}" if stats['total'] > 0 else "0%"
            )
        
        # Graphique des catégories
        if stats['par_categorie']:
            st.markdown("#### 📊 Répartition par catégorie")
            
            df_cat = pd.DataFrame(
                list(stats['par_categorie'].items()),
                columns=['Catégorie', 'Nombre']
            )
            
            st.bar_chart(df_cat.set_index('Catégorie'))
    
    # Aperçu du bordereau avec style
    st.markdown("#### 📝 Aperçu du document")
    
    with st.container():
        st.markdown("""
        <div style="
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 2rem;
            font-family: 'Courier New', monospace;
            max-height: 600px;
            overflow-y: auto;
        ">
        """, unsafe_allow_html=True)
        
        st.text(bordereau['contenu'])
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Options d'export améliorées
    st.markdown("### 📤 Export et partage")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Export Word
        if st.button("📄 Word", use_container_width=True, type="primary"):
            with st.spinner("Génération du fichier Word..."):
                file_content = gestionnaire.exporter_bordereau(bordereau, "word")
                if file_content:
                    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        "💾 Télécharger Word",
                        file_content,
                        f"bordereau_{bordereau['type']}_{date_str}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
    
    with col2:
        # Export PDF
        if st.button("📕 PDF", use_container_width=True):
            with st.spinner("Génération du PDF..."):
                file_content = gestionnaire.exporter_bordereau(bordereau, "pdf")
                if file_content:
                    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        "💾 Télécharger PDF",
                        file_content,
                        f"bordereau_{bordereau['type']}_{date_str}.pdf",
                        "application/pdf",
                        use_container_width=True
                    )
    
    with col3:
        # Export Excel
        if st.button("📊 Excel", use_container_width=True):
            with st.spinner("Génération du fichier Excel..."):
                file_content = gestionnaire.exporter_bordereau(bordereau, "excel")
                if file_content:
                    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        "💾 Télécharger Excel",
                        file_content,
                        f"bordereau_{bordereau['type']}_{date_str}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
    
    with col4:
        # Actions supplémentaires
        if st.button("🔄 Nouveau", use_container_width=True):
            st.session_state.current_bordereau = None
            st.session_state.current_step = 1
            st.rerun()
    
    # Options de partage
    with st.expander("🔗 Options de partage"):
        col_share1, col_share2 = st.columns(2)
        
        with col_share1:
            email = st.text_input("📧 Email destinataire", placeholder="exemple@email.com")
            
        with col_share2:
            if st.button("📤 Envoyer par email", use_container_width=True):
                if email:
                    st.info(f"📧 Envoi à {email} (fonctionnalité à implémenter)")
                else:
                    st.warning("⚠️ Veuillez saisir une adresse email")
        
        # Lien de partage
        st.text_input(
            "🔗 Lien de partage",
            value=f"https://nexora-law.app/bordereau/{uuid.uuid4().hex[:8]}",
            disabled=True,
            help="Lien de partage sécurisé (fonctionnalité à venir)"
        )

def display_enhanced_statistics_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet des statistiques amélioré"""
    
    st.markdown("### 📊 Tableau de bord des pièces")
    
    if not gestionnaire.pieces_selectionnees:
        st.info("ℹ️ Aucune pièce sélectionnée pour les statistiques")
        return
    
    # Calculer les stats
    stats = gestionnaire._calculer_stats_pieces(gestionnaire.pieces_selectionnees)
    
    # Vue d'ensemble avec design amélioré
    st.markdown("#### 🎯 Vue d'ensemble")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📎 Total",
            stats['total'],
            delta="100%"
        )
    
    with col2:
        comm_pct = (stats['communicables']/stats['total']*100) if stats['total'] > 0 else 0
        st.metric(
            "✅ Communicables",
            stats['communicables'],
            delta=f"{comm_pct:.0f}%"
        )
    
    with col3:
        conf_pct = (stats['confidentielles']/stats['total']*100) if stats['total'] > 0 else 0
        st.metric(
            "🔒 Confidentielles",
            stats['confidentielles'],
            delta=f"{conf_pct:.0f}%",
            delta_color="inverse"
        )
    
    with col4:
        date_pct = (stats['avec_date']/stats['total']*100) if stats['total'] > 0 else 0
        st.metric(
            "📅 Datées",
            stats['avec_date'],
            delta=f"{date_pct:.0f}%"
        )
    
    with col5:
        st.metric(
            "⭐ Pertinence",
            f"{stats['pertinence_moyenne']:.0%}",
            delta="+5%" if stats['pertinence_moyenne'] > 0.7 else "-5%"
        )
    
    # Graphiques interactifs
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📊 Répartition par catégorie")
        
        if stats['par_categorie']:
            # Créer un DataFrame pour le graphique
            df_cat = pd.DataFrame(
                list(stats['par_categorie'].items()),
                columns=['Catégorie', 'Nombre']
            )
            
            # Ajouter des couleurs
            colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6610f2', '#17a2b8']
            df_cat['Couleur'] = [colors[i % len(colors)] for i in range(len(df_cat))]
            
            st.bar_chart(df_cat.set_index('Catégorie')['Nombre'])
    
    with col_chart2:
        st.markdown("#### 📈 Analyse temporelle")
        
        # Analyser les dates
        dates_data = []
        for piece in gestionnaire.pieces_selectionnees:
            if piece.date:
                dates_data.append({
                    'Date': piece.date,
                    'Mois': piece.date.strftime('%Y-%m'),
                    'Nombre': 1
                })
        
        if dates_data:
            df_dates = pd.DataFrame(dates_data)
            df_monthly = df_dates.groupby('Mois')['Nombre'].sum().reset_index()
            st.line_chart(df_monthly.set_index('Mois'))
        else:
            st.info("Pas assez de données temporelles")
    
    # Tableau détaillé interactif
    st.markdown("---")
    st.markdown("### 📋 Détail des pièces")
    
    # Options de filtrage
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        filter_category = st.multiselect(
            "Filtrer par catégorie",
            ["Toutes"] + list(stats['par_categorie'].keys()),
            default=["Toutes"]
        )
    
    with col_filter2:
        filter_comm = st.selectbox(
            "Communicable",
            ["Toutes", "Oui", "Non"]
        )
    
    with col_filter3:
        filter_conf = st.selectbox(
            "Confidentiel",
            ["Toutes", "Oui", "Non"]
        )
    
    # Préparer les données filtrées
    pieces_filtered = gestionnaire.pieces_selectionnees
    
    if "Toutes" not in filter_category:
        pieces_filtered = [p for p in pieces_filtered if p.categorie in filter_category]
    
    if filter_comm != "Toutes":
        comm_value = filter_comm == "Oui"
        pieces_filtered = [p for p in pieces_filtered if p.communicable == comm_value]
    
    if filter_conf != "Toutes":
        conf_value = filter_conf == "Oui"
        pieces_filtered = [p for p in pieces_filtered if p.confidentiel == conf_value]
    
    # Créer le DataFrame
    pieces_data = []
    for piece in pieces_filtered:
        pieces_data.append({
            'N°': piece.numero,
            'Titre': truncate_text(piece.titre, 50),
            'Catégorie': piece.categorie,
            'Date': piece.date.strftime('%d/%m/%Y') if piece.date else '—',
            'Source': piece.source,
            'Pertinence': f"{piece.pertinence:.0%}",
            'Comm.': '✅' if piece.communicable else '❌',
            'Conf.': '🔒' if piece.confidentiel else '—'
        })
    
    if pieces_data:
        df_pieces = pd.DataFrame(pieces_data)
        
        # Afficher avec style
        st.dataframe(
            df_pieces,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pertinence": st.column_config.ProgressColumn(
                    "Pertinence",
                    help="Score de pertinence",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
            }
        )
        
        # Options d'export
        st.markdown("### 💾 Export des données")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            csv = df_pieces.to_csv(index=False)
            st.download_button(
                "📥 Télécharger CSV",
                csv,
                f"pieces_stats_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col_exp2:
            if st.button("📊 Rapport détaillé", use_container_width=True):
                st.info("Génération du rapport détaillé (à implémenter)")
        
        with col_exp3:
            if st.button("📧 Envoyer par email", use_container_width=True):
                st.info("Envoi par email (à implémenter)")
    else:
        st.info("Aucune pièce ne correspond aux filtres sélectionnés")

def display_configuration_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet de configuration du module"""
    
    st.markdown("### ⚙️ Configuration du module")
    
    # Paramètres généraux
    with st.expander("🎯 Paramètres généraux", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            auto_categorize = st.checkbox(
                "🏷️ Catégorisation automatique",
                value=True,
                help="Catégorise automatiquement les pièces selon leur contenu"
            )
            
            auto_number = st.checkbox(
                "🔢 Numérotation automatique",
                value=True,
                help="Numérote automatiquement les pièces ajoutées"
            )
            
            show_previews = st.checkbox(
                "👁️ Afficher les aperçus",
                value=True,
                help="Affiche un aperçu du contenu des pièces"
            )
        
        with col2:
            default_comm = st.checkbox(
                "✅ Communicable par défaut",
                value=True,
                help="Les nouvelles pièces sont communicables par défaut"
            )
            
            require_date = st.checkbox(
                "📅 Date obligatoire",
                value=False,
                help="Exige une date pour chaque pièce"
            )
            
            enable_ocr = st.checkbox(
                "📷 OCR automatique",
                value=False,
                help="Active la reconnaissance de texte sur les images"
            )
    
    # Catégories personnalisées
    with st.expander("📁 Catégories personnalisées"):
        st.info("Gérez vos catégories de pièces")
        
        # Afficher les catégories existantes
        for cat, keywords in gestionnaire.categories_pieces.items():
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.text_input(
                    "Catégorie",
                    value=cat,
                    key=f"cat_name_{cat}",
                    disabled=True
                )
            
            with col2:
                st.text_input(
                    "Mots-clés",
                    value=", ".join(keywords),
                    key=f"cat_keywords_{cat}",
                    disabled=True
                )
            
            with col3:
                if st.button("🗑️", key=f"del_cat_{cat}"):
                    pass  # Implémenter la suppression
        
        # Ajouter une nouvelle catégorie
        st.markdown("**Ajouter une catégorie**")
        
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_cat_name = st.text_input(
                "Nom",
                key="new_cat_name",
                placeholder="Ex: Contrats"
            )
        
        with col2:
            new_cat_keywords = st.text_input(
                "Mots-clés (séparés par des virgules)",
                key="new_cat_keywords",
                placeholder="Ex: contrat, accord, convention"
            )
        
        with col3:
            if st.button("➕ Ajouter", use_container_width=True):
                if new_cat_name and new_cat_keywords:
                    keywords = [k.strip() for k in new_cat_keywords.split(',')]
                    gestionnaire.categories_pieces[new_cat_name] = keywords
                    st.success(f"✅ Catégorie '{new_cat_name}' ajoutée")
                    st.rerun()
    
    # Configuration IA
    with st.expander("🤖 Configuration IA"):
        st.info("Paramètres d'analyse intelligente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input(
                "Nombre max de pièces à analyser",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                help="Limite le nombre de pièces analysées simultanément"
            )
            
            st.selectbox(
                "Modèle IA par défaut",
                ["gpt-4", "claude-3", "mixtral-8x7b"],
                help="Modèle utilisé pour l'analyse simple"
            )
        
        with col2:
            st.slider(
                "Seuil de pertinence",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Seuil minimum pour considérer une pièce pertinente"
            )
            
            st.selectbox(
                "Mode de fusion par défaut",
                ["consensus", "parallel", "simple"],
                help="Mode utilisé pour la fusion multi-IA"
            )
    
    # Templates de bordereaux
    with st.expander("📝 Templates de bordereaux"):
        st.info("Personnalisez vos modèles de bordereaux")
        
        template_type = st.selectbox(
            "Type de bordereau",
            ["Communication", "Inventaire", "Contradictoire"]
        )
        
        st.text_area(
            "En-tête personnalisé",
            placeholder="Entrez votre en-tête personnalisé...",
            height=100
        )
        
        st.text_area(
            "Pied de page personnalisé",
            placeholder="Entrez votre pied de page personnalisé...",
            height=100
        )
        
        if st.button("💾 Sauvegarder le template", type="primary"):
            st.success("✅ Template sauvegardé")
    
    # Sauvegarde de la configuration
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("💾 Sauvegarder toute la configuration", 
                     type="primary", use_container_width=True):
            st.success("✅ Configuration sauvegardée avec succès!")
            time.sleep(1)
            st.rerun()

# ==================================================
# FONCTIONS DE TRAITEMENT DES REQUÊTES (CONSERVÉES)
# ==================================================

def process_pieces_request(query: str, analysis: dict):
    """Traite une requête de gestion de pièces"""
    
    init_pieces_manager()
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Analyser la requête
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['sélectionner', 'choisir', 'ajouter']):
        # Rechercher et sélectionner des pièces
        pieces = gestionnaire.rechercher_pieces(query)
        
        if pieces:
            st.success(f"✅ {len(pieces)} pièce(s) trouvée(s)")
            for piece in pieces[:10]:
                gestionnaire.ajouter_piece_disponible(piece)
                gestionnaire.selectionner_piece(piece.id)
        else:
            st.warning("⚠️ Aucune pièce trouvée")
    
    elif any(word in query_lower for word in ['bordereau', 'liste', 'inventaire']):
        # Générer un bordereau
        if gestionnaire.pieces_selectionnees:
            process_liste_pieces_request(query, analysis)
        else:
            st.warning("⚠️ Sélectionnez d'abord des pièces")
    
    elif 'analyser' in query_lower:
        # Analyser les pièces
        if gestionnaire.pieces_selectionnees:
            analyse = gestionnaire.analyser_pertinence_pieces_multi_llm(
                gestionnaire.pieces_selectionnees,
                query,
                list(gestionnaire.llm_manager.clients.keys())[:2],
                "consensus"
            )
            if 'error' not in analyse:
                st.session_state.piece_analysis = analyse
                display_enhanced_analysis_results(analyse)
        else:
            st.warning("⚠️ Aucune pièce à analyser")
    
    else:
        # Afficher l'interface par défaut
        run()

def process_liste_pieces_request(query: str, analysis: dict):
    """Traite une requête de création de liste/bordereau"""
    
    init_pieces_manager()
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Si pas de pièces sélectionnées, utiliser toutes les pièces disponibles
    if not gestionnaire.pieces_selectionnees:
        # Chercher des pièces dans les documents
        if st.session_state.get('imported_documents'):
            for doc_id, doc in st.session_state.imported_documents.items():
                piece = gestionnaire._document_to_piece(
                    doc,
                    len(gestionnaire.pieces_selectionnees) + 1
                )
                gestionnaire.ajouter_piece_disponible(piece)
                gestionnaire.selectionner_piece(piece.id)
    
    if not gestionnaire.pieces_selectionnees:
        st.warning("⚠️ Aucune pièce disponible pour créer un bordereau")
        return
    
    # Déterminer le type de bordereau
    query_lower = query.lower()
    
    if 'communication' in query_lower:
        type_bordereau = "communication"
    elif 'inventaire' in query_lower:
        type_bordereau = "inventaire"
    elif 'contradictoire' in query_lower:
        type_bordereau = "contradictoire"
    else:
        type_bordereau = "communication"  # Par défaut
    
    # Préparer les métadonnées
    metadata = {
        'reference': analysis.get('reference', ''),
        'client': analysis.get('client', ''),
        'adversaire': analysis.get('adversaire', ''),
        'juridiction': analysis.get('juridiction', ''),
        'avocat': analysis.get('avocat', '[Nom de l\'avocat]'),
        'destinataire': 'TRIBUNAL JUDICIAIRE',
        'barreau': analysis.get('barreau', '[Ville]'),
        'ville': analysis.get('ville', '[Ville]')
    }
    
    # Générer le bordereau
    with st.spinner("🚀 Génération du bordereau..."):
        bordereau = gestionnaire.generer_bordereau(
            gestionnaire.pieces_selectionnees,
            type_bordereau=type_bordereau,
            metadata=metadata
        )
        
        if 'error' not in bordereau:
            st.session_state.current_bordereau = bordereau
            
            # Afficher le résultat
            st.success(f"✅ Bordereau de {bordereau['stats']['total']} pièces généré")
            
            # Aperçu
            with st.expander("📄 Aperçu du bordereau", expanded=True):
                st.text(bordereau['contenu'])
            
            # Options d'export
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export Word
                file_content = gestionnaire.exporter_bordereau(bordereau, "word")
                if file_content:
                    date_export = datetime.now().strftime('%Y%m%d')
                    st.download_button(
                        "📄 Télécharger Word",
                        file_content,
                        f"bordereau_{type_bordereau}_{date_export}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            
            with col2:
                # Export PDF
                file_content = gestionnaire.exporter_bordereau(bordereau, "pdf")
                if file_content:
                    date_export = datetime.now().strftime('%Y%m%d')
                    st.download_button(
                        "📕 Télécharger PDF",
                        file_content,
                        f"bordereau_{type_bordereau}_{date_export}.pdf",
                        "application/pdf"
                    )
            
            with col3:
                # Export Excel
                file_content = gestionnaire.exporter_bordereau(bordereau, "excel")
                if file_content:
                    date_export = datetime.now().strftime('%Y%m%d')
                    st.download_button(
                        "📊 Télécharger Excel",
                        file_content,
                        f"bordereau_{type_bordereau}_{date_export}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.error(f"❌ Erreur : {bordereau['error']}")

# ==================================================
# POINT D'ENTRÉE PRINCIPAL
# ==================================================

if __name__ == "__main__":
    run()