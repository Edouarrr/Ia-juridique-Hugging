# modules/import_export.py
"""Module d'import des documents (l'export est géré par export_manager.py)"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
import json
import io
import re
from pathlib import Path
from collections import defaultdict

# Imports des dépendances
from modules.dataclasses import Document
from utils.helpers import clean_key
from modules.export_manager import export_manager, ExportConfig

# [Garder toutes les fonctions d'import existantes du document 5]
# [Supprimer toutes les fonctions d'export qui sont maintenant dans export_manager.py]

# Remplacer la fonction show_import_export_interface par :

def show_import_interface():
    """Interface principale d'import de documents"""
    
    st.markdown("### 📥 Import de documents")
    
    # Utiliser la fonction process_import_request existante
    process_import_request("", {})

def show_import_export_tabs():
    """Interface avec onglets pour import et export"""
    
    tab1, tab2, tab3 = st.tabs(["📥 Import", "📤 Export", "📊 Historique"])
    
    with tab1:
        show_import_interface()
    
    with tab2:
        show_export_interface()
    
    with tab3:
        show_import_export_history()

def show_export_interface():
    """Interface d'export utilisant le gestionnaire unifié"""
    
    st.markdown("### 📤 Export de documents")
    
    # Déterminer le contenu à exporter
    export_options = []
    
    # Vérifier les différents contenus disponibles
    if st.session_state.get('current_bordereau'):
        export_options.append(("Bordereau actuel", 'bordereau'))
    
    if st.session_state.get('redaction_result'):
        export_options.append(("Document rédigé", 'redaction'))
    
    if st.session_state.get('timeline_result'):
        export_options.append(("Chronologie", 'timeline'))
    
    if st.session_state.get('ai_analysis_results'):
        export_options.append(("Analyse IA", 'analysis'))
    
    if st.session_state.get('selected_pieces'):
        export_options.append(("Pièces sélectionnées", 'pieces'))
    
    if not export_options:
        st.warning("⚠️ Aucun contenu disponible pour l'export")
        st.info("💡 Générez d'abord du contenu : bordereau, analyse, rédaction...")
        return
    
    # Sélection du contenu
    content_name = st.selectbox(
        "Contenu à exporter",
        [opt[0] for opt in export_options],
        key="export_content_select"
    )
    
    # Trouver le type correspondant
    content_type = next(opt[1] for opt in export_options if opt[0] == content_name)
    
    # Préparer le contenu
    if content_type == 'bordereau':
        bordereau = st.session_state['current_bordereau']
        content = prepare_bordereau_for_export(bordereau)
        export_content = content['text']
        title = f"Bordereau_{bordereau['metadata'].get('reference', 'pieces')}"
        
    elif content_type == 'redaction':
        data = st.session_state['redaction_result']
        export_content = data.get('document', '')
        title = f"Document_{data.get('type', 'juridique')}"
        
    elif content_type == 'timeline':
        data = st.session_state['timeline_result']
        export_content = format_timeline_for_export(data)
        title = f"Chronologie_{data.get('type', '')}"
        
    elif content_type == 'analysis':
        data = st.session_state['ai_analysis_results']
        export_content = data.get('content', '')
        title = "Analyse_IA"
        
    elif content_type == 'pieces':
        pieces = st.session_state['selected_pieces']
        export_content = format_pieces_for_export(pieces)
        title = "Liste_pieces"
    
    # Utiliser l'interface unifiée d'export
    export_manager.show_export_interface(
        content=export_content,
        title=title,
        content_type=content_type,
        key_prefix="main_export"
    )

# Fonctions helper pour formater le contenu

def format_timeline_for_export(data: dict) -> pd.DataFrame:
    """Formate une chronologie pour l'export"""
    
    if 'events' in data:
        df = pd.DataFrame(data['events'])
        
        # Formater les colonnes
        if 'actors' in df.columns:
            df['actors'] = df['actors'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        
        return df
    
    return pd.DataFrame()

def format_pieces_for_export(pieces: List) -> pd.DataFrame:
    """Formate une liste de pièces pour l'export"""
    
    return pd.DataFrame([{
        'N°': p.numero,
        'Titre': p.titre,
        'Description': p.description or '',
        'Catégorie': p.categorie,
        'Date': p.date.strftime('%d/%m/%Y') if hasattr(p, 'date') and p.date else 'N/A'
    } for p in pieces])