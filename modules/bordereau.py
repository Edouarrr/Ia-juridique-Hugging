# modules/bordereau.py
"""Module de création et gestion des bordereaux de communication de pièces"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from models.dataclasses import PieceSelectionnee
try:
    from modules.export_manager import ExportManager, ExportConfig
except ImportError:
    # Fallback si le module n'est pas disponible
    ExportManager = None
    ExportConfig = None

def process_bordereau_request(query: str, analysis: dict):
    """Traite une demande de création de bordereau"""
    
    pieces = st.session_state.get('selected_pieces', [])
    
    if not pieces:
        st.warning("⚠️ Aucune pièce sélectionnée pour le bordereau")
        return
    
    # Créer le bordereau
    bordereau = create_bordereau(pieces, analysis)
    
    # Afficher le bordereau
    display_bordereau_interface(bordereau, pieces)

def create_bordereau(pieces: List[PieceSelectionnee], analysis: dict) -> dict:
    """Crée un bordereau structuré"""
    
    # Déterminer les parties si disponibles
    pour = analysis.get('client', '[À compléter]')
    contre = analysis.get('adversaire', '[À compléter]')
    juridiction = analysis.get('juridiction', '[Tribunal]')
    
    bordereau = {
        'header': f"""BORDEREAU DE COMMUNICATION DE PIÈCES
AFFAIRE : {analysis.get('reference', 'N/A').upper()}
DATE : {datetime.now().strftime('%d/%m/%Y')}
NOMBRE DE PIÈCES : {len(pieces)}
POUR : {pour}
CONTRE : {contre}
DEVANT : {juridiction}
PIÈCES COMMUNIQUÉES :""",
        'pieces': pieces,
        'footer': f"""
Je certifie que les pièces communiquées sont conformes aux originaux en ma possession.
Fait à [Ville], le {datetime.now().strftime('%d/%m/%Y')}
[Signature]""",
        'metadata': {
            'created_at': datetime.now(),
            'piece_count': len(pieces),
            'categories': list(set(p.categorie for p in pieces)),
            'reference': analysis.get('reference'),
            'pour': pour,
            'contre': contre,
            'juridiction': juridiction
        }
    }
    
    return bordereau

def display_bordereau_interface(bordereau: dict, pieces: List[PieceSelectionnee]):
    """Affiche l'interface du bordereau avec le nouveau système d'export"""
    
    st.markdown("### 📊 Bordereau de communication de pièces")
    
    # Options d'édition
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"📋 {bordereau['metadata']['piece_count']} pièces - {len(bordereau['metadata']['categories'])} catégories")
    
    with col2:
        edit_mode = st.checkbox("✏️ Mode édition", key="edit_bordereau")
    
    # En-tête
    if edit_mode:
        bordereau['header'] = st.text_area(
            "En-tête du bordereau",
            value=bordereau['header'],
            height=200,
            key="bordereau_header_edit"
        )
    else:
        st.text(bordereau['header'])
    
    st.divider()
    
    # Table des pièces
    display_pieces_table(pieces, edit_mode)
    
    st.divider()
    
    # Pied de page
    if edit_mode:
        bordereau['footer'] = st.text_area(
            "Pied de page",
            value=bordereau['footer'],
            height=100,
            key="bordereau_footer_edit"
        )
    else:
        st.text(bordereau['footer'])
    
    # Export avec le nouveau système unifié
    st.markdown("### 💾 Export du bordereau")
    
    # Préparer le contenu pour l'export
    bordereau_content = prepare_bordereau_for_export(bordereau)
    
    # Utiliser l'interface unifiée d'export
    export_manager.show_export_interface(
        content=bordereau_content,
        title=f"Bordereau_{bordereau['metadata'].get('reference', 'pieces')}",
        content_type='document',
        key_prefix="bordereau"
    )
    
    # Actions supplémentaires
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Préparer pour envoi", key="prepare_email_bordereau"):
            st.session_state.pending_email = {
                'type': 'bordereau',
                'content': bordereau,
                'subject': f"Bordereau de pièces - {bordereau['metadata']['reference']}"
            }
            st.success("📧 Bordereau prêt pour envoi")
    
    with col2:
        if st.button("📋 Copier le texte", key="copy_bordereau"):
            # Créer une version texte pour le presse-papier
            text_content = bordereau_content['text']
            st.code(text_content, language=None)
            st.info("💡 Sélectionnez et copiez le texte ci-dessus")
    
    # Stocker le bordereau
    st.session_state.current_bordereau = bordereau

def display_pieces_table(pieces: List[PieceSelectionnee], edit_mode: bool):
    """Affiche le tableau des pièces"""
    
    # Créer un DataFrame
    df_data = []
    for piece in pieces:
        df_data.append({
            'N°': piece.numero,
            'Cote': piece.cote or f"P-{piece.numero:03d}",
            'Titre': piece.titre,
            'Description': piece.description,
            'Catégorie': piece.categorie,
            'Date': piece.date.strftime('%d/%m/%Y') if piece.date else 'N/A',
            'Pages': piece.pages or '-',
            'Format': piece.format or '-'
        })
    
    df = pd.DataFrame(df_data)
    
    if edit_mode:
        # Mode édition
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="fixed",
            key="bordereau_pieces_editor"
        )
        # Mettre à jour les pièces si modifiées
        # ... (logique de mise à jour)
    else:
        # Affichage simple
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    
    # Statistiques par catégorie
    with st.expander("📊 Statistiques par catégorie"):
        category_stats = df.groupby('Catégorie').agg({
            'N°': 'count',
            'Pages': lambda x: sum(p for p in x if isinstance(p, int))
        }).rename(columns={'N°': 'Nombre'})
        
        st.dataframe(category_stats)

def prepare_bordereau_for_export(bordereau: dict) -> dict:
    """Prépare le bordereau pour l'export unifié"""
    
    # Version texte complète
    text_lines = [bordereau['header'], '']
    
    # Table des pièces en format texte
    col_widths = {
        'numero': 5,
        'cote': 10,
        'titre': 40,
        'categorie': 20,
        'date': 12
    }
    
    # En-tête du tableau
    header = (
        f"{'N°'.ljust(col_widths['numero'])}"
        f"{'COTE'.ljust(col_widths['cote'])}"
        f"{'TITRE'.ljust(col_widths['titre'])}"
        f"{'CATÉGORIE'.ljust(col_widths['categorie'])}"
        f"{'DATE'.ljust(col_widths['date'])}"
    )
    
    text_lines.append(header)
    text_lines.append('-' * len(header))
    
    # Lignes du tableau
    for piece in bordereau['pieces']:
        cote = piece.cote or f"P-{piece.numero:03d}"
        titre = piece.titre[:col_widths['titre']-3] + '...' if len(piece.titre) > col_widths['titre'] else piece.titre
        categorie = piece.categorie[:col_widths['categorie']-3] + '...' if len(piece.categorie) > col_widths['categorie'] else piece.categorie
        date_str = piece.date.strftime('%d/%m/%Y') if piece.date else 'N/A'
        
        line = (
            f"{str(piece.numero).ljust(col_widths['numero'])}"
            f"{cote.ljust(col_widths['cote'])}"
            f"{titre.ljust(col_widths['titre'])}"
            f"{categorie.ljust(col_widths['categorie'])}"
            f"{date_str.ljust(col_widths['date'])}"
        )
        
        text_lines.append(line)
        
        if piece.description:
            text_lines.append(f"     → {piece.description}")
    
    text_lines.extend(['', bordereau['footer']])
    
    # DataFrame pour export Excel
    df_pieces = pd.DataFrame([{
        'N°': p.numero,
        'Cote': p.cote or f"P-{p.numero:03d}",
        'Titre': p.titre,
        'Description': p.description or '',
        'Catégorie': p.categorie,
        'Date': p.date.strftime('%d/%m/%Y') if p.date else 'N/A',
        'Pages': p.pages or '',
        'Format': p.format or ''
    } for p in bordereau['pieces']])
    
    return {
        'text': '\n'.join(text_lines),
        'dataframe': df_pieces,
        'metadata': bordereau['metadata'],
        'structured': bordereau
    }

def validate_bordereau(bordereau: dict) -> List[str]:
    """Valide un bordereau et retourne les erreurs"""
    
    errors = []
    
    if not bordereau.get('pieces'):
        errors.append("Aucune pièce dans le bordereau")
    
    # Vérifier les numéros de pièces
    numeros = [p.numero for p in bordereau.get('pieces', [])]
    if len(numeros) != len(set(numeros)):
        errors.append("Numéros de pièces en double détectés")
    
    # Vérifier les cotes
    cotes = [p.cote for p in bordereau.get('pieces', []) if p.cote]
    if len(cotes) != len(set(cotes)):
        errors.append("Cotes en double détectées")
    
    # Vérifier les informations obligatoires
    if '[À compléter]' in bordereau.get('header', ''):
        errors.append("Informations manquantes dans l'en-tête")
    
    return errors

def generate_bordereau_summary(bordereau: dict) -> str:
    """Génère un résumé du bordereau"""
    
    pieces = bordereau.get('pieces', [])
    
    summary = f"""RÉSUMÉ DU BORDEREAU
    
Référence : {bordereau['metadata'].get('reference', 'N/A')}
Date : {bordereau['metadata']['created_at'].strftime('%d/%m/%Y')}
Nombre total de pièces : {len(pieces)}

PARTIES :
- Pour : {bordereau['metadata'].get('pour', 'N/A')}
- Contre : {bordereau['metadata'].get('contre', 'N/A')}
- Juridiction : {bordereau['metadata'].get('juridiction', 'N/A')}

RÉPARTITION PAR CATÉGORIE :
"""
    
    # Compter par catégorie
    from collections import Counter
    categories = Counter(p.categorie for p in pieces)
    
    for cat, count in categories.most_common():
        summary += f"- {cat} : {count} pièce(s)\n"
    
    # Ajouter des statistiques
    total_pages = sum(p.pages for p in pieces if p.pages and isinstance(p.pages, int))
    if total_pages:
        summary += f"\nNombre total de pages : {total_pages}"
    
    return summary

# Fonction pour l'export direct du bordereau (compatibilité)
def export_bordereau_to_format(bordereau: dict, format: str) -> bytes:
    """Export direct du bordereau dans un format spécifique"""
    
    content = prepare_bordereau_for_export(bordereau)
    
    # Déterminer le type de contenu selon le format
    if format in ['xlsx', 'csv']:
        export_content = content['dataframe']
    else:
        export_content = content['text']
    
    config = ExportConfig(
        format=format,
        title=f"Bordereau_{bordereau['metadata'].get('reference', 'pieces')}",
        content=export_content,
        metadata=bordereau['metadata']
    )
    
    data, _ = export_manager.export(config)
    return data