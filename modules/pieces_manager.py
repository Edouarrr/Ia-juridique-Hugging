# modules/pieces_manager.py
"""Module unifié de gestion des pièces et bordereaux
REMPLACE pieces_manager.py ET bordereau.py
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import uuid
import json
import pandas as pd
from dataclasses import dataclass, field
import traceback

# Import des modèles
from models.dataclasses import (
    PieceSelectionnee, Document, PieceProcedurale,
    NaturePiece, ForceProbante, ElementProcedure
)

# Import des gestionnaires
from managers.multi_llm_manager import MultiLLMManager
from managers.azure_search_manager import AzureSearchManager
from managers.export_manager import ExportManager

# Import des utilitaires
from utils.helpers import (
    truncate_text, clean_filename, format_file_size,
    extract_key_phrases, clean_key
)

# ==================================================
# CLASSE PRINCIPALE UNIFIÉE
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
    # GESTION DES PIÈCES
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
    # GÉNÉRATION DE BORDEREAUX
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
        contenu = f"""BORDEREAU DE COMMUNICATION DE PIÈCES

Référence : {metadata.get('reference', 'N/A')}
Date : {datetime.now().strftime('%d/%m/%Y')}

{metadata.get('destinataire', 'TRIBUNAL JUDICIAIRE')}

Affaire : {metadata.get('client', '')} c/ {metadata.get('adversaire', '')}
{metadata.get('juridiction', '')}

Maître {metadata.get('avocat', '[Nom de l\'avocat]')}
Avocat au Barreau de {metadata.get('barreau', '[Ville]')}

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
                    contenu += f" ({piece.date.strftime('%d/%m/%Y')})"
                
                if piece.description:
                    contenu += f"\n              {truncate_text(piece.description, 100)}"
                
                contenu += "\n"
        
        # Total et signature
        contenu += f"""
TOTAL : {len(pieces)} pièce{'s' if len(pieces) > 1 else ''}

Fait à {metadata.get('ville', '[Ville]')}, le {datetime.now().strftime('%d/%m/%Y')}

Maître {metadata.get('avocat', '[Nom de l\'avocat]')}
"""
        
        return contenu
    
    def _generer_bordereau_inventaire(
        self,
        pieces: List[PieceSelectionnee],
        metadata: Dict
    ) -> str:
        """Génère un inventaire détaillé des pièces"""
        
        contenu = f"""INVENTAIRE DES PIÈCES

Date : {datetime.now().strftime('%d/%m/%Y')}
Référence : {metadata.get('reference', 'N/A')}
Nombre total de pièces : {len(pieces)}

"""
        
        # Tableau détaillé
        for piece in pieces:
            contenu += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIÈCE N° {piece.numero}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Titre : {piece.titre}
Catégorie : {piece.categorie}
Date : {piece.date.strftime('%d/%m/%Y') if piece.date else 'Non datée'}
Source : {piece.source}
Cote : {piece.cote or f'P-{piece.numero:03d}'}

Description :
{piece.description or 'Aucune description'}

Nature : {piece.nature.value if hasattr(piece, 'nature') else 'Copie'}
Communicable : {'Oui' if piece.communicable else 'Non'}
Confidentiel : {'Oui' if piece.confidentiel else 'Non'}
Force probante : {piece.force_probante.value if hasattr(piece, 'force_probante') else 'Normale'}
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
    # ANALYSE INTELLIGENTE
    # ==================================================
    
    def analyser_pertinence_pieces(
        self,
        pieces: List[PieceSelectionnee],
        contexte: str
    ) -> Dict[str, Any]:
        """Analyse la pertinence des pièces par rapport au contexte"""
        
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
2. Son importance stratégique
3. Les risques potentiels
4. Les pièces manquantes suggérées

Format : analyse structurée avec recommandations."""
        
        try:
            response = self.llm_manager.query_single_llm(
                list(self.llm_manager.clients.keys())[0],
                prompt,
                "Tu es un expert en analyse de pièces juridiques."
            )
            
            if response['success']:
                return {
                    'analyse': response['response'],
                    'pieces_analysees': len(pieces),
                    'timestamp': datetime.now()
                }
            else:
                return {"error": response.get('error', 'Erreur analyse')}
                
        except Exception as e:
            return {"error": f"Erreur : {str(e)}"}
    
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
    # EXPORT ET FORMATS
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
                    df_data.append({
                        'N°': piece.numero,
                        'Titre': piece.titre,
                        'Catégorie': piece.categorie,
                        'Date': piece.date.strftime('%d/%m/%Y') if piece.date else '',
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
# FONCTIONS D'INTERFACE STREAMLIT
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

def display_pieces_interface():
    """Interface principale de gestion des pièces"""
    
    st.title("📎 Gestion des Pièces")
    
    # Initialiser si nécessaire
    init_pieces_manager()
    gestionnaire = st.session_state.gestionnaire_pieces
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Sélection",
        "📝 Bordereau",
        "🔍 Analyse",
        "📊 Statistiques"
    ])
    
    with tab1:
        display_piece_selection_tab(gestionnaire)
    
    with tab2:
        display_bordereau_tab(gestionnaire)
    
    with tab3:
        display_analysis_tab(gestionnaire)
    
    with tab4:
        display_statistics_tab(gestionnaire)

def display_piece_selection_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet de sélection des pièces"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Rechercher des pièces")
        
        # Barre de recherche
        search_query = st.text_input(
            "Rechercher dans les documents",
            placeholder="Ex: contrat, facture, email...",
            key="piece_search"
        )
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            search_category = st.selectbox(
                "Catégorie",
                ["Toutes"] + list(gestionnaire.categories_pieces.keys()),
                key="search_category"
            )
        
        with col_b:
            search_source = st.selectbox(
                "Source",
                ["Toutes", "Documents importés", "Azure", "Templates"],
                key="search_source"
            )
        
        with col_c:
            if st.button("🔍 Rechercher", type="primary", use_container_width=True):
                with st.spinner("Recherche en cours..."):
                    pieces = gestionnaire.rechercher_pieces(search_query)
                    st.session_state.search_results_pieces = pieces
    
    with col2:
        st.subheader("📎 Pièces sélectionnées")
        
        # Compteur
        nb_selected = len(gestionnaire.pieces_selectionnees)
        st.metric("Nombre de pièces", nb_selected)
        
        # Actions rapides
        if nb_selected > 0:
            col_x, col_y = st.columns(2)
            with col_x:
                if st.button("📝 Créer bordereau", use_container_width=True):
                    st.session_state.show_bordereau_creation = True
            
            with col_y:
                if st.button("🗑️ Tout retirer", use_container_width=True):
                    gestionnaire.pieces_selectionnees.clear()
                    st.rerun()
    
    # Afficher les résultats de recherche
    if 'search_results_pieces' in st.session_state:
        display_search_results(gestionnaire, st.session_state.search_results_pieces)
    
    # Afficher les pièces disponibles
    st.markdown("---")
    st.subheader("📚 Pièces disponibles")
    
    # Sources de pièces
    sources_tabs = st.tabs([
        "📥 Documents importés",
        "☁️ Azure",
        "📋 Templates",
        "➕ Ajouter manuellement"
    ])
    
    with sources_tabs[0]:
        display_imported_documents_as_pieces(gestionnaire)
    
    with sources_tabs[1]:
        display_azure_documents_as_pieces(gestionnaire)
    
    with sources_tabs[2]:
        display_template_pieces(gestionnaire)
    
    with sources_tabs[3]:
        display_manual_piece_creation(gestionnaire)

def display_search_results(
    gestionnaire: GestionnairePiecesUnifie,
    results: List[PieceSelectionnee]
):
    """Affiche les résultats de recherche"""
    
    if not results:
        st.info("Aucun résultat trouvé")
        return
    
    st.success(f"✅ {len(results)} pièce(s) trouvée(s)")
    
    # Afficher chaque résultat
    for piece in results[:20]:  # Limiter à 20
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{piece.titre}**")
            if piece.description:
                st.caption(truncate_text(piece.description, 100))
        
        with col2:
            st.caption(f"📁 {piece.categorie}")
            if piece.date:
                st.caption(f"📅 {piece.date.strftime('%d/%m/%Y')}")
        
        with col3:
            # Vérifier si déjà sélectionnée
            is_selected = any(p.titre == piece.titre for p in gestionnaire.pieces_selectionnees)
            
            if is_selected:
                if st.button("✅ Retirer", key=f"remove_{piece.titre}"):
                    gestionnaire.deselectionner_piece(piece.id)
                    st.rerun()
            else:
                if st.button("➕ Ajouter", key=f"add_{piece.titre}", type="primary"):
                    gestionnaire.ajouter_piece_disponible(piece)
                    gestionnaire.selectionner_piece(piece.id)
                    st.rerun()
        
        st.divider()

def display_imported_documents_as_pieces(gestionnaire: GestionnairePiecesUnifie):
    """Affiche les documents importés comme pièces"""
    
    if 'imported_documents' not in st.session_state or not st.session_state.imported_documents:
        st.info("Aucun document importé. Utilisez le module Import/Export.")
        return
    
    for doc_id, doc in st.session_state.imported_documents.items():
        display_document_as_piece(gestionnaire, doc, doc_id)

def display_azure_documents_as_pieces(gestionnaire: GestionnairePiecesUnifie):
    """Affiche les documents Azure comme pièces"""
    
    if not st.session_state.get('azure_documents'):
        st.info("Aucun document Azure. Configurez Azure Storage.")
        return
    
    for doc_id, doc in st.session_state.azure_documents.items():
        display_document_as_piece(gestionnaire, doc, doc_id, source="Azure")

def display_document_as_piece(
    gestionnaire: GestionnairePiecesUnifie,
    doc: Document,
    doc_id: str,
    source: str = "Local"
):
    """Affiche un document comme pièce sélectionnable"""
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.markdown(f"**{doc.title}**")
        if hasattr(doc, 'content'):
            st.caption(truncate_text(doc.content, 100))
    
    with col2:
        # Catégorie auto
        piece_temp = PieceSelectionnee(
            numero=0,
            titre=doc.title,
            description=getattr(doc, 'content', '')
        )
        categorie = gestionnaire.categoriser_piece(piece_temp)
        st.caption(f"📁 {categorie}")
    
    with col3:
        st.caption(f"📍 {source}")
        if doc.metadata and doc.metadata.get('date'):
            st.caption(f"📅 {doc.metadata['date']}")
    
    with col4:
        # Vérifier si déjà sélectionnée
        is_selected = any(
            p.titre == doc.title for p in gestionnaire.pieces_selectionnees
        )
        
        if is_selected:
            if st.button("✅", key=f"selected_{doc_id}", help="Déjà sélectionnée"):
                # Retirer
                piece_id = next(
                    (p.id for p in gestionnaire.pieces_selectionnees if p.titre == doc.title),
                    None
                )
                if piece_id:
                    gestionnaire.deselectionner_piece(piece_id)
                    st.rerun()
        else:
            if st.button("➕", key=f"select_{doc_id}", help="Ajouter aux pièces"):
                # Créer et ajouter la pièce
                piece = gestionnaire._document_to_piece(
                    doc,
                    len(gestionnaire.pieces_selectionnees) + 1
                )
                piece.source = source
                gestionnaire.ajouter_piece_disponible(piece)
                gestionnaire.selectionner_piece(piece.id)
                st.rerun()

def display_template_pieces(gestionnaire: GestionnairePiecesUnifie):
    """Affiche des modèles de pièces types"""
    
    st.info("📋 Modèles de pièces types pour différentes affaires")
    
    # Sélection du type d'affaire
    type_affaire = st.selectbox(
        "Type d'affaire",
        [
            "Abus de biens sociaux",
            "Escroquerie",
            "Faux et usage de faux",
            "Corruption",
            "Blanchiment",
            "Abus de confiance"
        ],
        key="template_type_affaire"
    )
    
    # Obtenir les pièces suggérées
    type_key = type_affaire.lower().replace(" ", "_").replace("'", "")
    pieces_suggerees = gestionnaire.suggerer_pieces_manquantes(
        gestionnaire.pieces_selectionnees,
        type_key
    )
    
    if pieces_suggerees:
        st.warning(f"💡 {len(pieces_suggerees)} pièce(s) suggérée(s) pour ce type d'affaire")
        
        for i, piece_nom in enumerate(pieces_suggerees):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"• {piece_nom}")
            
            with col2:
                if st.button("➕", key=f"add_template_{i}", help="Créer cette pièce"):
                    # Créer une pièce template
                    piece = PieceSelectionnee(
                        numero=len(gestionnaire.pieces_selectionnees) + 1,
                        titre=piece_nom,
                        description=f"[À compléter - {piece_nom}]",
                        categorie="Template",
                        source="Modèle"
                    )
                    gestionnaire.ajouter_piece_disponible(piece)
                    gestionnaire.selectionner_piece(piece.id)
                    st.success(f"✅ '{piece_nom}' ajoutée aux pièces")
                    st.rerun()

def display_manual_piece_creation(gestionnaire: GestionnairePiecesUnifie):
    """Interface de création manuelle de pièces"""
    
    with st.form("create_piece_form"):
        st.subheader("➕ Créer une pièce manuellement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            titre = st.text_input("Titre de la pièce *", placeholder="Ex: Contrat de prestations")
            categorie = st.selectbox(
                "Catégorie",
                list(gestionnaire.categories_pieces.keys()) + ["Autre"]
            )
            date = st.date_input("Date du document", value=None)
        
        with col2:
            cote = st.text_input("Cote", placeholder="Ex: C-001")
            nature = st.selectbox(
                "Nature",
                ["Original", "Copie", "Copie certifiée conforme"]
            )
            communicable = st.checkbox("Communicable", value=True)
            confidentiel = st.checkbox("Confidentiel", value=False)
        
        description = st.text_area(
            "Description",
            placeholder="Description détaillée de la pièce...",
            height=100
        )
        
        col_a, col_b, col_c = st.columns([1, 1, 1])
        
        with col_b:
            submitted = st.form_submit_button(
                "➕ Créer la pièce",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            if titre:
                # Créer la pièce
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
                    source="Création manuelle"
                )
                
                # Ajouter et sélectionner
                gestionnaire.ajouter_piece_disponible(piece)
                gestionnaire.selectionner_piece(piece.id)
                
                st.success(f"✅ Pièce '{titre}' créée et ajoutée")
                st.rerun()
            else:
                st.error("❌ Le titre est obligatoire")

def display_bordereau_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet de génération de bordereaux"""
    
    if not gestionnaire.pieces_selectionnees:
        st.info("ℹ️ Sélectionnez d'abord des pièces dans l'onglet 'Sélection'")
        return
    
    st.subheader(f"📝 Créer un bordereau ({len(gestionnaire.pieces_selectionnees)} pièces)")
    
    # Formulaire de création
    with st.form("bordereau_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            type_bordereau = st.selectbox(
                "Type de bordereau",
                [
                    "Communication de pièces",
                    "Inventaire détaillé",
                    "Bordereau contradictoire",
                    "Liste simple"
                ]
            )
            
            reference = st.text_input(
                "Référence de l'affaire",
                value=st.session_state.get('current_analysis', {}).get('reference', '')
            )
            
            client = st.text_input(
                "Client",
                value=st.session_state.get('current_analysis', {}).get('client', '')
            )
        
        with col2:
            adversaire = st.text_input(
                "Partie adverse",
                value=st.session_state.get('current_analysis', {}).get('adversaire', '')
            )
            
            juridiction = st.text_input(
                "Juridiction",
                value=st.session_state.get('current_analysis', {}).get('juridiction', '')
            )
            
            avocat = st.text_input("Nom de l'avocat")
        
        # Informations complémentaires
        col3, col4 = st.columns(2)
        
        with col3:
            destinataire = st.text_input(
                "Destinataire",
                value="TRIBUNAL JUDICIAIRE" if "communication" in type_bordereau.lower() else ""
            )
            barreau = st.text_input("Barreau", placeholder="Ex: Paris")
        
        with col4:
            ville = st.text_input("Ville", placeholder="Ex: Paris")
            include_stats = st.checkbox("Inclure les statistiques", value=True)
        
        # Aperçu des pièces
        with st.expander("📎 Pièces à inclure", expanded=False):
            for piece in gestionnaire.pieces_selectionnees:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"{piece.numero}. {piece.titre}")
                with col_b:
                    if st.button("🗑️", key=f"remove_bordereau_{piece.numero}"):
                        gestionnaire.deselectionner_piece(piece.id)
                        st.rerun()
        
        # Bouton de génération
        col_x, col_y, col_z = st.columns([1, 2, 1])
        with col_y:
            submitted = st.form_submit_button(
                "🚀 Générer le bordereau",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            # Préparer les métadonnées
            metadata = {
                'reference': reference,
                'client': client,
                'adversaire': adversaire,
                'juridiction': juridiction,
                'avocat': avocat,
                'destinataire': destinataire,
                'barreau': barreau,
                'ville': ville
            }
            
            # Mapper le type
            type_map = {
                "Communication de pièces": "communication",
                "Inventaire détaillé": "inventaire",
                "Bordereau contradictoire": "contradictoire",
                "Liste simple": "simple"
            }
            
            # Générer le bordereau
            with st.spinner("Génération en cours..."):
                bordereau = gestionnaire.generer_bordereau(
                    gestionnaire.pieces_selectionnees,
                    type_bordereau=type_map.get(type_bordereau, "simple"),
                    metadata=metadata
                )
                
                st.session_state.current_bordereau = bordereau
                st.success("✅ Bordereau généré avec succès !")
    
    # Afficher le bordereau généré
    if st.session_state.get('current_bordereau'):
        display_generated_bordereau(gestionnaire, st.session_state.current_bordereau)

def display_generated_bordereau(
    gestionnaire: GestionnairePiecesUnifie,
    bordereau: Dict[str, Any]
):
    """Affiche le bordereau généré"""
    
    st.markdown("---")
    st.subheader("📄 Bordereau généré")
    
    # Statistiques
    if bordereau.get('stats'):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total pièces", bordereau['stats']['total'])
        with col2:
            st.metric("Communicables", bordereau['stats']['communicables'])
        with col3:
            st.metric("Confidentielles", bordereau['stats']['confidentielles'])
        with col4:
            st.metric("Avec date", bordereau['stats']['avec_date'])
    
    # Contenu du bordereau
    with st.expander("📝 Aperçu du bordereau", expanded=True):
        st.text(bordereau['contenu'])
    
    # Options d'export
    st.subheader("📤 Export")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        format_export = st.selectbox(
            "Format",
            ["Word (.docx)", "PDF", "Excel (.xlsx)", "Texte (.txt)"]
        )
    
    with col2:
        if st.button("💾 Télécharger", type="primary"):
            # Mapper le format
            format_map = {
                "Word (.docx)": "word",
                "PDF": "pdf",
                "Excel (.xlsx)": "excel",
                "Texte (.txt)": "text"
            }
            
            # Exporter
            file_content = gestionnaire.exporter_bordereau(
                bordereau,
                format_map.get(format_export, "text")
            )
            
            if file_content:
                # Extensions
                ext_map = {
                    "word": "docx",
                    "pdf": "pdf",
                    "excel": "xlsx",
                    "text": "txt"
                }
                ext = ext_map.get(format_map.get(format_export, "text"), "txt")
                
                # Nom du fichier
                filename = f"bordereau_{bordereau['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                
                # Bouton de téléchargement
                st.download_button(
                    "💾 Enregistrer le fichier",
                    file_content,
                    filename,
                    mime=f"application/{ext}" if ext != "txt" else "text/plain"
                )
    
    with col3:
        if st.button("📧 Envoyer par email"):
            st.info("Fonctionnalité email à implémenter")
    
    with col4:
        if st.button("🔄 Nouveau bordereau"):
            st.session_state.current_bordereau = None
            st.rerun()

def display_analysis_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet d'analyse des pièces"""
    
    st.subheader("🔍 Analyse intelligente des pièces")
    
    if not gestionnaire.pieces_selectionnees:
        st.info("ℹ️ Sélectionnez des pièces pour les analyser")
        return
    
    # Contexte de l'analyse
    contexte = st.text_area(
        "Contexte de l'affaire",
        placeholder="Décrivez brièvement l'affaire pour une analyse pertinente...",
        height=100,
        value=st.session_state.get('current_analysis', {}).get('request', '')
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        type_affaire = st.selectbox(
            "Type d'affaire",
            [
                "Abus de biens sociaux",
                "Escroquerie",
                "Faux et usage de faux",
                "Corruption",
                "Blanchiment",
                "Autre"
            ]
        )
    
    with col2:
        if st.button("🤖 Analyser la pertinence", type="primary", use_container_width=True):
            if contexte:
                with st.spinner("Analyse en cours..."):
                    # Analyser
                    analyse = gestionnaire.analyser_pertinence_pieces(
                        gestionnaire.pieces_selectionnees,
                        f"{contexte}\nType d'affaire : {type_affaire}"
                    )
                    
                    if 'error' not in analyse:
                        st.session_state.piece_analysis = analyse
                        st.success("✅ Analyse terminée")
                    else:
                        st.error(f"❌ {analyse['error']}")
            else:
                st.warning("⚠️ Veuillez décrire le contexte")
    
    # Afficher l'analyse
    if st.session_state.get('piece_analysis'):
        display_piece_analysis_results(st.session_state.piece_analysis)
    
    # Suggestions de pièces manquantes
    st.markdown("---")
    st.subheader("💡 Pièces manquantes suggérées")
    
    type_key = type_affaire.lower().replace(" ", "_").replace("'", "")
    pieces_manquantes = gestionnaire.suggerer_pieces_manquantes(
        gestionnaire.pieces_selectionnees,
        type_key
    )
    
    if pieces_manquantes:
        st.warning(f"⚠️ {len(pieces_manquantes)} pièce(s) potentiellement manquante(s)")
        
        for piece in pieces_manquantes:
            st.write(f"• {piece}")
    else:
        st.success("✅ Toutes les pièces types semblent présentes")

def display_piece_analysis_results(analysis: Dict[str, Any]):
    """Affiche les résultats de l'analyse"""
    
    with st.expander("📊 Résultats de l'analyse", expanded=True):
        st.write(analysis.get('analyse', ''))
        
        if analysis.get('timestamp'):
            st.caption(f"Analyse effectuée le {analysis['timestamp'].strftime('%d/%m/%Y à %H:%M')}")

def display_statistics_tab(gestionnaire: GestionnairePiecesUnifie):
    """Onglet des statistiques sur les pièces"""
    
    st.subheader("📊 Statistiques des pièces")
    
    if not gestionnaire.pieces_selectionnees:
        st.info("ℹ️ Aucune pièce sélectionnée")
        return
    
    # Calculer les stats
    stats = gestionnaire._calculer_stats_pieces(gestionnaire.pieces_selectionnees)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total pièces", stats['total'])
    
    with col2:
        st.metric("Communicables", f"{stats['communicables']}/{stats['total']}")
    
    with col3:
        st.metric("Confidentielles", stats['confidentielles'])
    
    with col4:
        st.metric("Pertinence moy.", f"{stats['pertinence_moyenne']:.1%}")
    
    # Graphiques
    if stats['par_categorie']:
        st.markdown("### 📊 Répartition par catégorie")
        
        # Préparer les données pour le graphique
        categories = list(stats['par_categorie'].keys())
        counts = list(stats['par_categorie'].values())
        
        # Créer un DataFrame
        df_stats = pd.DataFrame({
            'Catégorie': categories,
            'Nombre': counts
        })
        
        # Afficher avec st.bar_chart
        st.bar_chart(df_stats.set_index('Catégorie'))
    
    # Liste détaillée
    st.markdown("### 📋 Liste détaillée")
    
    # Créer un DataFrame des pièces
    pieces_data = []
    for piece in gestionnaire.pieces_selectionnees:
        pieces_data.append({
            'N°': piece.numero,
            'Titre': piece.titre,
            'Catégorie': piece.categorie,
            'Date': piece.date.strftime('%d/%m/%Y') if piece.date else 'N/D',
            'Source': piece.source,
            'Pertinence': f"{piece.pertinence:.0%}",
            'Communicable': '✅' if piece.communicable else '❌',
            'Confidentiel': '🔒' if piece.confidentiel else ''
        })
    
    df_pieces = pd.DataFrame(pieces_data)
    st.dataframe(df_pieces, use_container_width=True, hide_index=True)
    
    # Export CSV
    if st.button("📥 Exporter en CSV"):
        csv = df_pieces.to_csv(index=False)
        st.download_button(
            "💾 Télécharger CSV",
            csv,
            "pieces_selectionnees.csv",
            "text/csv"
        )

# ==================================================
# FONCTIONS DE TRAITEMENT DES REQUÊTES
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
            analyse = gestionnaire.analyser_pertinence_pieces(
                gestionnaire.pieces_selectionnees,
                query
            )
            if 'error' not in analyse:
                st.session_state.piece_analysis = analyse
                display_piece_analysis_results(analyse)
        else:
            st.warning("⚠️ Aucune pièce à analyser")
    
    else:
        # Afficher l'interface par défaut
        display_pieces_interface()

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
    with st.spinner("Génération du bordereau..."):
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
                    st.download_button(
                        "📄 Télécharger Word",
                        file_content,
                        f"bordereau_{type_bordereau}_{datetime.now().strftime('%Y%m%d')}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            
            with col2:
                # Export PDF
                file_content = gestionnaire.exporter_bordereau(bordereau, "pdf")
                if file_content:
                    st.download_button(
                        "📕 Télécharger PDF",
                        file_content,
                        f"bordereau_{type_bordereau}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        "application/pdf"
                    )
            
            with col3:
                # Export Excel
                file_content = gestionnaire.exporter_bordereau(bordereau, "excel")
                if file_content:
                    st.download_button(
                        "📊 Télécharger Excel",
                        file_content,
                        f"bordereau_{type_bordereau}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.error(f"❌ Erreur : {bordereau['error']}")

# ==================================================
# EXPORT DES FONCTIONS PUBLIQUES
# ==================================================

__all__ = [
    'GestionnairePiecesUnifie',
    'init_pieces_manager',
    'display_pieces_interface',
    'process_pieces_request',
    'process_liste_pieces_request'
]