# modules/explorer.py
"""Module explorateur de fichiers et documents"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os
from pathlib import Path

from models.dataclasses import Document
from managers.azure_blob_manager import AzureBlobManager
from utils.helpers import (
    clean_key,
    get_file_icon,
    format_file_size,
    sanitize_filename,
    calculate_read_time
)

# Configuration de l'explorateur
EXPLORER_CONFIG = {
    'files_per_page': 20,
    'preview_chars': 500,
    'supported_extensions': ['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.json', '.xml'],
    'image_extensions': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    'max_file_size_mb': 100
}

def show_explorer_interface():
    """Interface principale de l'explorateur"""
    
    st.markdown("### 📁 Explorateur de documents")
    
    # Sources disponibles
    sources = get_available_sources()
    
    if not sources:
        st.info("Aucune source de documents disponible")
        show_connection_help()
        return
    
    # Sélection de la source
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_source = st.selectbox(
            "Source",
            sources,
            key="explorer_source_select"
        )
    
    with col2:
        # Actions globales
        if st.button("🔄 Actualiser", key="refresh_explorer"):
            clear_explorer_cache()
            st.rerun()
    
    # Interface selon la source
    if selected_source == "Documents locaux":
        show_local_documents_explorer()
    
    elif selected_source == "Azure Blob Storage":
        show_azure_blob_explorer()
    
    elif selected_source == "Google Drive":
        show_google_drive_explorer()
    
    elif selected_source == "OneDrive":
        show_onedrive_explorer()

def get_available_sources() -> List[str]:
    """Récupère les sources disponibles"""
    
    sources = []
    
    # Documents locaux
    if st.session_state.get('azure_documents'):
        sources.append("Documents locaux")
    
    # Azure Blob
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and blob_manager.is_connected():
        sources.append("Azure Blob Storage")
    
    # Google Drive (si configuré)
    if st.session_state.get('google_drive_connected'):
        sources.append("Google Drive")
    
    # OneDrive (si configuré)
    if st.session_state.get('onedrive_connected'):
        sources.append("OneDrive")
    
    # Toujours proposer les documents locaux
    if "Documents locaux" not in sources:
        sources.insert(0, "Documents locaux")
    
    return sources

def show_local_documents_explorer():
    """Explorateur de documents locaux"""
    
    documents = st.session_state.get('azure_documents', {})
    
    # Barre de recherche et filtres
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Rechercher",
            placeholder="Titre, contenu, source...",
            key="local_explorer_search"
        )
    
    with col2:
        # Filtre par type
        doc_types = ["Tous"] + get_document_types(documents)
        selected_type = st.selectbox(
            "Type",
            doc_types,
            key="local_explorer_type_filter"
        )
    
    with col3:
        # Tri
        sort_options = ["Date ↓", "Date ↑", "Titre A-Z", "Titre Z-A", "Taille ↓", "Taille ↑"]
        sort_by = st.selectbox(
            "Trier par",
            sort_options,
            key="local_explorer_sort"
        )
    
    # Appliquer les filtres
    filtered_docs = filter_documents(documents, search_query, selected_type)
    sorted_docs = sort_documents(filtered_docs, sort_by)
    
    # Statistiques
    show_explorer_stats(filtered_docs, len(documents))
    
    # Vue (grille ou liste)
    view_mode = st.radio(
        "Vue",
        ["📋 Liste", "📊 Grille", "📈 Analyse"],
        key="local_explorer_view",
        horizontal=True
    )
    
    if view_mode == "📋 Liste":
        show_documents_list_view(sorted_docs)
    
    elif view_mode == "📊 Grille":
        show_documents_grid_view(sorted_docs)
    
    else:  # Analyse
        show_documents_analysis_view(sorted_docs)
    
    # Actions groupées
    show_bulk_actions(sorted_docs)

def filter_documents(documents: Dict[str, Document], search_query: str, doc_type: str) -> Dict[str, Document]:
    """Filtre les documents"""
    
    filtered = {}
    search_lower = search_query.lower()
    
    for doc_id, doc in documents.items():
        # Filtre par recherche
        if search_query:
            searchable = f"{doc.title} {doc.content[:500]} {doc.source}".lower()
            if search_lower not in searchable:
                continue
        
        # Filtre par type
        if doc_type != "Tous":
            if get_document_type(doc) != doc_type:
                continue
        
        filtered[doc_id] = doc
    
    return filtered

def sort_documents(documents: Dict[str, Document], sort_by: str) -> List[Tuple[str, Document]]:
    """Trie les documents"""
    
    docs_list = list(documents.items())
    
    if sort_by == "Date ↓":
        docs_list.sort(key=lambda x: x[1].created_at, reverse=True)
    elif sort_by == "Date ↑":
        docs_list.sort(key=lambda x: x[1].created_at)
    elif sort_by == "Titre A-Z":
        docs_list.sort(key=lambda x: x[1].title.lower())
    elif sort_by == "Titre Z-A":
        docs_list.sort(key=lambda x: x[1].title.lower(), reverse=True)
    elif sort_by == "Taille ↓":
        docs_list.sort(key=lambda x: len(x[1].content), reverse=True)
    elif sort_by == "Taille ↑":
        docs_list.sort(key=lambda x: len(x[1].content))
    
    return docs_list

def get_document_types(documents: Dict[str, Document]) -> List[str]:
    """Récupère les types de documents uniques"""
    
    types = set()
    
    for doc in documents.values():
        doc_type = get_document_type(doc)
        types.add(doc_type)
    
    return sorted(list(types))

def get_document_type(doc: Document) -> str:
    """Détermine le type d'un document"""
    
    if doc.mime_type:
        if 'pdf' in doc.mime_type:
            return "PDF"
        elif 'word' in doc.mime_type or 'document' in doc.mime_type:
            return "Word"
        elif 'sheet' in doc.mime_type or 'excel' in doc.mime_type:
            return "Excel"
        elif 'text' in doc.mime_type:
            return "Texte"
    
    # Déduction depuis le titre
    title_lower = doc.title.lower()
    if title_lower.endswith('.pdf'):
        return "PDF"
    elif title_lower.endswith(('.doc', '.docx')):
        return "Word"
    elif title_lower.endswith(('.xls', '.xlsx')):
        return "Excel"
    elif title_lower.endswith('.txt'):
        return "Texte"
    
    return "Autre"

def show_explorer_stats(filtered_docs: Dict[str, Document], total_docs: int):
    """Affiche les statistiques de l'explorateur"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Documents affichés",
            len(filtered_docs),
            f"sur {total_docs}"
        )
    
    with col2:
        total_size = sum(len(doc.content) for doc in filtered_docs.values())
        st.metric("Taille totale", format_file_size(total_size))
    
    with col3:
        if filtered_docs:
            avg_size = total_size / len(filtered_docs)
            st.metric("Taille moyenne", format_file_size(int(avg_size)))
    
    with col4:
        # Documents récents (< 7 jours)
        recent_count = sum(
            1 for doc in filtered_docs.values()
            if (datetime.now() - doc.created_at).days < 7
        )
        st.metric("Récents (< 7j)", recent_count)

def show_documents_list_view(sorted_docs: List[Tuple[str, Document]]):
    """Vue liste des documents"""
    
    # Pagination
    page = st.session_state.get('explorer_page', 1)
    per_page = EXPLORER_CONFIG['files_per_page']
    total_pages = (len(sorted_docs) - 1) // per_page + 1 if sorted_docs else 1
    
    # Navigation
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if page > 1:
                if st.button("⬅️ Précédent"):
                    st.session_state.explorer_page = page - 1
                    st.rerun()
        
        with col2:
            st.write(f"Page {page} / {total_pages}")
        
        with col3:
            if page < total_pages:
                if st.button("Suivant ➡️"):
                    st.session_state.explorer_page = page + 1
                    st.rerun()
    
    # Documents de la page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_docs = sorted_docs[start_idx:end_idx]
    
    # Affichage
    for doc_id, doc in page_docs:
        show_document_list_item(doc_id, doc)

def show_document_list_item(doc_id: str, doc: Document):
    """Affiche un document dans la vue liste"""
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            # Icône et titre
            icon = get_file_icon(doc.title)
            st.markdown(f"### {icon} {doc.title}")
            
            # Métadonnées
            meta_parts = []
            
            if doc.source:
                meta_parts.append(f"📂 {doc.source}")
            
            if doc.author:
                meta_parts.append(f"👤 {doc.author}")
            
            meta_parts.append(f"📅 {doc.created_at.strftime('%d/%m/%Y')}")
            
            st.caption(" • ".join(meta_parts))
            
            # Aperçu du contenu
            if doc.content:
                preview = doc.content[:EXPLORER_CONFIG['preview_chars']]
                if len(doc.content) > EXPLORER_CONFIG['preview_chars']:
                    preview += "..."
                
                with st.expander("Aperçu", expanded=False):
                    st.text(preview)
        
        with col2:
            # Taille et stats
            st.metric("Taille", format_file_size(len(doc.content)))
            
            if doc.content:
                words = len(doc.content.split())
                st.caption(f"{words:,} mots")
                
                read_time = calculate_read_time(doc.content)
                st.caption(f"⏱️ {read_time} min")
        
        with col3:
            # Tags
            if doc.tags:
                for tag in doc.tags[:3]:
                    st.caption(f"🏷️ {tag}")
                
                if len(doc.tags) > 3:
                    st.caption(f"... +{len(doc.tags) - 3}")
        
        with col4:
            # Actions
            if st.button("👁️", key=f"view_{doc_id}", help="Voir"):
                show_document_detail(doc_id, doc)
            
            if st.button("📝", key=f"edit_{doc_id}", help="Éditer"):
                edit_document(doc_id, doc)
            
            if st.button("🤖", key=f"analyze_{doc_id}", help="Analyser"):
                analyze_document(doc_id, doc)
            
            if st.button("🗑️", key=f"delete_{doc_id}", help="Supprimer"):
                if confirm_delete_document(doc_id):
                    delete_document(doc_id)
        
        st.divider()

def show_documents_grid_view(sorted_docs: List[Tuple[str, Document]]):
    """Vue grille des documents"""
    
    # Nombre de colonnes
    num_cols = 3
    
    # Pagination
    page = st.session_state.get('explorer_grid_page', 1)
    per_page = num_cols * 4  # 4 lignes
    total_pages = (len(sorted_docs) - 1) // per_page + 1 if sorted_docs else 1
    
    # Navigation
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if page > 1:
                if st.button("⬅️"):
                    st.session_state.explorer_grid_page = page - 1
                    st.rerun()
        
        with col2:
            st.write(f"Page {page} / {total_pages}")
        
        with col3:
            if page < total_pages:
                if st.button("➡️"):
                    st.session_state.explorer_grid_page = page + 1
                    st.rerun()
    
    # Documents de la page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_docs = sorted_docs[start_idx:end_idx]
    
    # Affichage en grille
    for i in range(0, len(page_docs), num_cols):
        cols = st.columns(num_cols)
        
        for j in range(num_cols):
            if i + j < len(page_docs):
                doc_id, doc = page_docs[i + j]
                
                with cols[j]:
                    show_document_grid_card(doc_id, doc)

def show_document_grid_card(doc_id: str, doc: Document):
    """Affiche une carte de document dans la grille"""
    
    with st.container():
        # Icône et type
        icon = get_file_icon(doc.title)
        doc_type = get_document_type(doc)
        
        st.markdown(f"### {icon}")
        
        # Titre (tronqué si nécessaire)
        title = doc.title
        if len(title) > 30:
            title = title[:27] + "..."
        
        st.markdown(f"**{title}**")
        
        # Métadonnées
        st.caption(f"{doc_type} • {format_file_size(len(doc.content))}")
        st.caption(f"📅 {doc.created_at.strftime('%d/%m/%Y')}")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️", key=f"grid_view_{doc_id}"):
                show_document_detail(doc_id, doc)
        
        with col2:
            if st.button("📝", key=f"grid_edit_{doc_id}"):
                edit_document(doc_id, doc)
        
        with col3:
            if st.button("🤖", key=f"grid_analyze_{doc_id}"):
                analyze_document(doc_id, doc)
        
        # Séparateur visuel
        st.markdown("---")

def show_documents_analysis_view(sorted_docs: List[Tuple[str, Document]]):
    """Vue analyse des documents"""
    
    if not sorted_docs:
        st.info("Aucun document à analyser")
        return
    
    # Statistiques globales
    st.markdown("#### 📊 Analyse de la collection")
    
    # Calculs
    total_size = sum(len(doc.content) for _, doc in sorted_docs)
    total_words = sum(len(doc.content.split()) for _, doc in sorted_docs)
    
    # Types de documents
    type_counts = {}
    for _, doc in sorted_docs:
        doc_type = get_document_type(doc)
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    
    # Sources
    source_counts = {}
    for _, doc in sorted_docs:
        source = doc.source or "Non spécifié"
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Affichage des métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", len(sorted_docs))
        st.metric("Taille totale", format_file_size(total_size))
    
    with col2:
        st.metric("Mots totaux", f"{total_words:,}")
        avg_words = total_words // len(sorted_docs) if sorted_docs else 0
        st.metric("Mots/document", f"{avg_words:,}")
    
    with col3:
        st.metric("Types différents", len(type_counts))
        most_common_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "N/A"
        st.metric("Type principal", most_common_type)
    
    with col4:
        st.metric("Sources", len(source_counts))
        # Tags uniques
        all_tags = set()
        for _, doc in sorted_docs:
            all_tags.update(doc.tags)
        st.metric("Tags uniques", len(all_tags))
    
    # Graphiques si disponibles
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Répartition par type
        if type_counts:
            fig1 = go.Figure([go.Pie(
                labels=list(type_counts.keys()),
                values=list(type_counts.values()),
                hole=0.3
            )])
            
            fig1.update_layout(
                title="Répartition par type",
                height=300
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        # Timeline de création
        dates = [doc.created_at.date() for _, doc in sorted_docs]
        date_counts = {}
        for date in dates:
            date_counts[date] = date_counts.get(date, 0) + 1
        
        if date_counts:
            fig2 = go.Figure([go.Bar(
                x=list(date_counts.keys()),
                y=list(date_counts.values()),
                name='Documents créés'
            )])
            
            fig2.update_layout(
                title="Timeline de création",
                xaxis_title="Date",
                yaxis_title="Nombre de documents",
                height=300
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
    except ImportError:
        st.info("Installez plotly pour voir les graphiques")
    
    # Top documents par taille
    st.markdown("#### 📈 Documents les plus volumineux")
    
    top_by_size = sorted(sorted_docs, key=lambda x: len(x[1].content), reverse=True)[:5]
    
    for i, (doc_id, doc) in enumerate(top_by_size, 1):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"{i}. {doc.title}")
        
        with col2:
            st.write(format_file_size(len(doc.content)))
        
        with col3:
            st.write(f"{len(doc.content.split()):,} mots")

def show_bulk_actions(documents: List[Tuple[str, Document]]):
    """Actions groupées sur les documents"""
    
    if not documents:
        return
    
    st.markdown("#### 🔧 Actions groupées")
    
    # Sélection
    selected_docs = st.multiselect(
        "Sélectionner des documents",
        options=[doc_id for doc_id, _ in documents],
        format_func=lambda x: next(doc.title for doc_id, doc in documents if doc_id == x),
        key="bulk_select_docs"
    )
    
    if selected_docs:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 Exporter sélection", key="bulk_export"):
                export_selected_documents(selected_docs)
        
        with col2:
            if st.button("🏷️ Ajouter tags", key="bulk_tag"):
                add_tags_to_documents(selected_docs)
        
        with col3:
            if st.button("📁 Déplacer", key="bulk_move"):
                move_documents(selected_docs)
        
        with col4:
            if st.button("🗑️ Supprimer", key="bulk_delete"):
                if st.checkbox("Confirmer suppression", key="confirm_bulk_delete"):
                    delete_documents(selected_docs)

def show_document_detail(doc_id: str, doc: Document):
    """Affiche le détail d'un document"""
    
    st.session_state.current_document = {
        'id': doc_id,
        'document': doc
    }
    st.session_state.show_document_detail = True

def edit_document(doc_id: str, doc: Document):
    """Édite un document"""
    
    st.session_state.editing_document = {
        'id': doc_id,
        'document': doc
    }

def analyze_document(doc_id: str, doc: Document):
    """Lance l'analyse d'un document"""
    
    st.session_state.universal_query = f"analyser @{doc_id}"
    st.session_state.current_page = 'recherche'
    st.rerun()

def confirm_delete_document(doc_id: str) -> bool:
    """Demande confirmation pour supprimer un document"""
    
    return st.checkbox(f"Confirmer suppression de {doc_id}", key=f"confirm_delete_{doc_id}")

def delete_document(doc_id: str):
    """Supprime un document"""
    
    if doc_id in st.session_state.azure_documents:
        del st.session_state.azure_documents[doc_id]
        st.success("✅ Document supprimé")
        st.rerun()

def delete_documents(doc_ids: List[str]):
    """Supprime plusieurs documents"""
    
    count = 0
    for doc_id in doc_ids:
        if doc_id in st.session_state.azure_documents:
            del st.session_state.azure_documents[doc_id]
            count += 1
    
    st.success(f"✅ {count} documents supprimés")
    st.rerun()

def export_selected_documents(doc_ids: List[str]):
    """Exporte les documents sélectionnés"""
    
    import json
    
    export_data = {}
    
    for doc_id in doc_ids:
        if doc_id in st.session_state.azure_documents:
            doc = st.session_state.azure_documents[doc_id]
            export_data[doc_id] = doc.to_dict()
    
    # JSON
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Télécharger JSON",
        json_str,
        f"documents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="download_selected_docs"
    )

# Suite de modules/explorer.py

def add_tags_to_documents(doc_ids: List[str]):
    """Ajoute des tags aux documents"""
    
    new_tags = st.text_input(
        "Tags à ajouter (séparés par des virgules)",
        key="bulk_tags_input"
    )
    
    if new_tags and st.button("➕ Ajouter les tags", key="apply_bulk_tags"):
        tags_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]
        
        count = 0
        for doc_id in doc_ids:
            if doc_id in st.session_state.azure_documents:
                doc = st.session_state.azure_documents[doc_id]
                doc.tags.extend(tags_list)
                doc.tags = list(set(doc.tags))  # Dédupliquer
                count += 1
        
        st.success(f"✅ Tags ajoutés à {count} documents")
        st.rerun()

def move_documents(doc_ids: List[str]):
    """Déplace des documents vers une autre source/dossier"""
    
    new_source = st.text_input(
        "Nouvelle source/dossier",
        placeholder="Ex: Dossier_2024",
        key="bulk_move_destination"
    )
    
    if new_source and st.button("📁 Déplacer", key="apply_bulk_move"):
        count = 0
        for doc_id in doc_ids:
            if doc_id in st.session_state.azure_documents:
                doc = st.session_state.azure_documents[doc_id]
                doc.source = new_source
                doc.updated_at = datetime.now()
                count += 1
        
        st.success(f"✅ {count} documents déplacés vers '{new_source}'")
        st.rerun()

def show_azure_blob_explorer():
    """Explorateur Azure Blob Storage"""
    
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if not blob_manager or not blob_manager.is_connected():
        st.warning("⚠️ Azure Blob Storage non connecté")
        show_azure_connection_help()
        return
    
    try:
        # Liste des conteneurs
        containers = blob_manager.list_containers()
        
        if not containers:
            st.info("Aucun conteneur disponible")
            
            if st.button("➕ Créer un conteneur"):
                create_new_container(blob_manager)
            return
        
        # Sélection du conteneur
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_container = st.selectbox(
                "Conteneur",
                containers,
                key="blob_container_select"
            )
        
        with col2:
            if st.button("🔄 Actualiser", key="refresh_containers"):
                st.rerun()
        
        # Navigation dans le conteneur
        current_path = st.session_state.get('blob_current_path', '')
        
        # Breadcrumb
        show_blob_breadcrumb(current_path)
        
        # Actions sur le chemin actuel
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📁 Nouveau dossier", key="new_blob_folder"):
                create_blob_folder(blob_manager, selected_container, current_path)
        
        with col2:
            if st.button("⬆️ Upload fichiers", key="upload_to_blob"):
                upload_files_to_blob(blob_manager, selected_container, current_path)
        
        with col3:
            if current_path:
                if st.button("⬆️ Dossier parent", key="blob_parent"):
                    parent_path = '/'.join(current_path.split('/')[:-1])
                    st.session_state.blob_current_path = parent_path
                    st.rerun()
        
        # Lister le contenu
        with st.spinner("Chargement..."):
            items = blob_manager.list_folder_contents(selected_container, current_path)
        
        if not items:
            st.info("Dossier vide")
        else:
            # Séparer dossiers et fichiers
            folders = [item for item in items if item['type'] == 'folder']
            files = [item for item in items if item['type'] == 'file']
            
            # Afficher les dossiers
            if folders:
                st.markdown("#### 📁 Dossiers")
                show_blob_folders(folders, selected_container)
            
            # Afficher les fichiers
            if files:
                st.markdown("#### 📄 Fichiers")
                show_blob_files(files, blob_manager, selected_container)
        
    except Exception as e:
        st.error(f"❌ Erreur Azure : {str(e)}")
        
        if st.button("🔧 Reconfigurer la connexion"):
            st.session_state.show_azure_config = True

def show_blob_breadcrumb(current_path: str):
    """Affiche le fil d'Ariane pour la navigation"""
    
    if not current_path:
        st.caption("📁 Racine")
    else:
        parts = current_path.split('/')
        breadcrumb_parts = ["📁 Racine"]
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                breadcrumb_parts.append(f"**{part}**")
            else:
                breadcrumb_parts.append(part)
        
        st.caption(" > ".join(breadcrumb_parts))

def show_blob_folders(folders: List[Dict[str, Any]], container: str):
    """Affiche les dossiers blob"""
    
    for folder in folders:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"📁 **{folder['name']}**")
            if folder.get('last_modified'):
                st.caption(f"Modifié le {folder['last_modified'].strftime('%d/%m/%Y')}")
        
        with col2:
            if folder.get('item_count'):
                st.caption(f"{folder['item_count']} éléments")
        
        with col3:
            if st.button("Ouvrir", key=f"open_folder_{folder['name']}"):
                st.session_state.blob_current_path = folder['path']
                st.rerun()

def show_blob_files(files: List[Dict[str, Any]], blob_manager: AzureBlobManager, container: str):
    """Affiche les fichiers blob"""
    
    for file in files:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                icon = get_file_icon(file['name'])
                st.write(f"{icon} **{file['name']}**")
                
                if file.get('last_modified'):
                    st.caption(f"Modifié le {file['last_modified'].strftime('%d/%m/%Y à %H:%M')}")
            
            with col2:
                if file.get('size'):
                    st.write(format_file_size(file['size']))
            
            with col3:
                # Télécharger
                if st.button("⬇️", key=f"download_blob_{file['name']}", help="Télécharger"):
                    download_blob_file(blob_manager, container, file['path'], file['name'])
            
            with col4:
                # Plus d'actions
                action = st.selectbox(
                    "",
                    ["Actions", "Analyser", "Importer", "Supprimer"],
                    key=f"blob_action_{file['name']}"
                )
                
                if action == "Analyser":
                    analyze_blob_file(blob_manager, container, file)
                elif action == "Importer":
                    import_blob_file(blob_manager, container, file)
                elif action == "Supprimer":
                    if st.checkbox(f"Confirmer suppression", key=f"confirm_del_blob_{file['name']}"):
                        delete_blob_file(blob_manager, container, file['path'])
            
            st.divider()

def download_blob_file(blob_manager: AzureBlobManager, container: str, blob_path: str, filename: str):
    """Télécharge un fichier depuis blob"""
    
    try:
        with st.spinner(f"Téléchargement de {filename}..."):
            content = blob_manager.download_blob(container, blob_path)
            
            st.download_button(
                f"💾 Enregistrer {filename}",
                content,
                filename,
                key=f"save_downloaded_{filename}"
            )
            
    except Exception as e:
        st.error(f"Erreur téléchargement : {str(e)}")

def analyze_blob_file(blob_manager: AzureBlobManager, container: str, file: Dict[str, Any]):
    """Analyse un fichier blob"""
    
    try:
        # Télécharger et stocker temporairement
        content = blob_manager.download_blob(container, file['path'])
        
        # Créer un document temporaire
        doc_id = f"blob_{clean_key(file['name'])}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extraire le texte selon le type
        if file['name'].endswith('.pdf'):
            text_content = "PDF - Extraction nécessite PyPDF2"
        else:
            text_content = content.decode('utf-8', errors='ignore')
        
        doc = Document(
            id=doc_id,
            title=file['name'],
            content=text_content,
            source=f"Azure Blob: {container}/{file['path']}",
            metadata={
                'blob_container': container,
                'blob_path': file['path'],
                'blob_size': file.get('size', 0),
                'blob_modified': file.get('last_modified')
            }
        )
        
        # Stocker temporairement
        if 'azure_documents' not in st.session_state:
            st.session_state.azure_documents = {}
        
        st.session_state.azure_documents[doc_id] = doc
        
        # Lancer l'analyse
        st.session_state.universal_query = f"analyser @{doc_id}"
        st.session_state.current_page = 'recherche'
        st.rerun()
        
    except Exception as e:
        st.error(f"Erreur analyse : {str(e)}")

def import_blob_file(blob_manager: AzureBlobManager, container: str, file: Dict[str, Any]):
    """Importe un fichier blob dans les documents locaux"""
    
    try:
        with st.spinner(f"Import de {file['name']}..."):
            # Télécharger
            content = blob_manager.download_blob(container, file['path'])
            
            # Créer le document
            doc_id = f"imported_{clean_key(file['name'])}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extraire le texte selon le type
            if file['name'].endswith('.pdf'):
                text_content = "PDF - Extraction nécessite PyPDF2"
            else:
                text_content = content.decode('utf-8', errors='ignore')
            
            doc = Document(
                id=doc_id,
                title=file['name'],
                content=text_content,
                source=f"Import depuis Azure Blob",
                metadata={
                    'original_container': container,
                    'original_path': file['path'],
                    'import_date': datetime.now().isoformat()
                },
                file_size=file.get('size', 0)
            )
            
            # Stocker
            if 'azure_documents' not in st.session_state:
                st.session_state.azure_documents = {}
            
            st.session_state.azure_documents[doc_id] = doc
            
            st.success(f"✅ {file['name']} importé avec succès")
            
    except Exception as e:
        st.error(f"Erreur import : {str(e)}")

def delete_blob_file(blob_manager: AzureBlobManager, container: str, blob_path: str):
    """Supprime un fichier blob"""
    
    try:
        blob_manager.delete_blob(container, blob_path)
        st.success("✅ Fichier supprimé")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur suppression : {str(e)}")

def upload_files_to_blob(blob_manager: AzureBlobManager, container: str, current_path: str):
    """Upload des fichiers vers blob"""
    
    uploaded_files = st.file_uploader(
        "Sélectionner les fichiers",
        accept_multiple_files=True,
        key="blob_upload_files"
    )
    
    if uploaded_files:
        if st.button("⬆️ Uploader", key="confirm_blob_upload"):
            progress_bar = st.progress(0)
            
            for i, file in enumerate(uploaded_files):
                try:
                    # Construire le chemin blob
                    blob_name = f"{current_path}/{file.name}" if current_path else file.name
                    
                    # Uploader
                    blob_manager.upload_blob(container, blob_name, file.read())
                    
                    # Progresser
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                except Exception as e:
                    st.error(f"Erreur upload {file.name} : {str(e)}")
            
            st.success(f"✅ {len(uploaded_files)} fichiers uploadés")
            progress_bar.empty()
            st.rerun()

def create_blob_folder(blob_manager: AzureBlobManager, container: str, current_path: str):
    """Crée un dossier dans blob"""
    
    folder_name = st.text_input(
        "Nom du dossier",
        key="new_blob_folder_name"
    )
    
    if folder_name and st.button("➕ Créer", key="create_blob_folder_confirm"):
        try:
            # Les dossiers dans blob sont virtuels, créés par convention
            # On crée un fichier placeholder
            folder_path = f"{current_path}/{folder_name}" if current_path else folder_name
            placeholder_path = f"{folder_path}/.placeholder"
            
            blob_manager.upload_blob(container, placeholder_path, b"")
            
            st.success(f"✅ Dossier '{folder_name}' créé")
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur création dossier : {str(e)}")

def show_google_drive_explorer():
    """Explorateur Google Drive (placeholder)"""
    
    st.info("🚧 Intégration Google Drive en cours de développement")
    
    st.markdown("""
    Pour activer Google Drive :
    1. Configurez l'API Google Drive
    2. Obtenez les credentials OAuth2
    3. Ajoutez-les dans la configuration
    """)

def show_onedrive_explorer():
    """Explorateur OneDrive (placeholder)"""
    
    st.info("🚧 Intégration OneDrive en cours de développement")
    
    st.markdown("""
    Pour activer OneDrive :
    1. Configurez l'API Microsoft Graph
    2. Obtenez les tokens d'accès
    3. Ajoutez-les dans la configuration
    """)

def show_connection_help():
    """Aide pour connecter des sources"""
    
    with st.expander("💡 Comment ajouter des sources de documents", expanded=True):
        st.markdown("""
        ### Documents locaux
        - Utilisez l'import de fichiers dans l'interface principale
        - Glissez-déposez ou sélectionnez vos fichiers
        
        ### Azure Blob Storage
        1. Créez un compte de stockage Azure
        2. Obtenez la chaîne de connexion
        3. Ajoutez-la dans les variables d'environnement :
           ```
           AZURE_STORAGE_CONNECTION_STRING=your_connection_string
           ```
        
        ### Google Drive
        1. Activez l'API Google Drive
        2. Créez des credentials OAuth2
        3. Configuration à venir...
        
        ### OneDrive
        1. Enregistrez votre app dans Azure AD
        2. Obtenez les tokens d'accès
        3. Configuration à venir...
        """)

def show_azure_connection_help():
    """Aide pour la connexion Azure"""
    
    st.markdown("""
    ### Configuration Azure Blob Storage
    
    1. **Créer un compte de stockage** dans le portail Azure
    2. **Récupérer la chaîne de connexion** :
       - Accédez à votre compte de stockage
       - Clés d'accès > Chaîne de connexion
    3. **Configurer l'application** :
       - Ajoutez dans `.env` ou les secrets Streamlit :
         ```
         AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
         ```
    """)

def clear_explorer_cache():
    """Efface le cache de l'explorateur"""
    
    cache_keys = [
        'explorer_page',
        'explorer_grid_page',
        'blob_current_path',
        'explorer_filter'
    ]
    
    for key in cache_keys:
        if key in st.session_state:
            del st.session_state[key]

# Fonctions helper pour intégration

def get_document_by_path(path: str) -> Optional[Document]:
    """Récupère un document par son chemin"""
    
    # Recherche dans les documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if doc.metadata.get('original_path') == path:
            return doc
    
    return None

def search_documents_in_explorer(query: str, source: str = None) -> List[Document]:
    """Recherche des documents dans l'explorateur"""
    
    results = []
    query_lower = query.lower()
    
    # Documents locaux
    if not source or source == "Documents locaux":
        for doc in st.session_state.get('azure_documents', {}).values():
            if query_lower in doc.title.lower() or query_lower in doc.content.lower():
                results.append(doc)
    
    # Autres sources à implémenter...
    
    return results

def get_folder_structure() -> Dict[str, List[Document]]:
    """Récupère la structure de dossiers"""
    
    structure = {}
    
    for doc in st.session_state.get('azure_documents', {}).values():
        folder = doc.source or "Sans dossier"
        
        if folder not in structure:
            structure[folder] = []
        
        structure[folder].append(doc)
    
    return structure