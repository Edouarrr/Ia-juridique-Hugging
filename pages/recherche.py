# pages/recherche.py
"""Page de recherche enrichie avec toutes les fonctionnalités d'Azure"""

import streamlit as st
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any

from config.app_config import (
    TYPES_INFRACTIONS, 
    LEGAL_APIS, 
    DEFAULT_CONTAINER,
    AZURE_SEARCH_CONFIG
)
from models.dataclasses import Document, SearchResult
from utils.styles import load_custom_css, create_alert_box, create_section_divider
from utils.helpers import clean_key


def show():
    """Affiche la page de recherche complète avec Azure Blob et Search"""
    load_custom_css()
    
    st.title("🔍 Recherche de documents")
    
    # Initialiser les gestionnaires Azure s'ils ne sont pas déjà présents
    initialize_azure_managers()
    
    # Vérifier la connexion Azure
    if not st.session_state.get('azure_blob_manager') or not st.session_state.azure_blob_manager.is_connected():
        st.error("❌ Connexion Azure Blob non configurée.")
        st.info("💡 Variable requise : AZURE_STORAGE_CONNECTION_STRING")
        return
    
    # Section de recherche principale
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        
        # Barre de recherche
        col1, col2 = st.columns([4, 1])
        with col1:
            search_query = st.text_input(
                "Rechercher dans tous les documents",
                value=st.session_state.get('search_query', ''),
                placeholder="Ex: abus de biens sociaux, délégation de pouvoirs, fraude fiscale...",
                key="search_input_main"
            )
        
        with col2:
            search_clicked = st.button("🔍 Rechercher", type="primary", key="search_button")
        
        # Options de recherche avancée
        with st.expander("⚙️ Options avancées"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_mode = st.selectbox(
                    "Mode de recherche",
                    ["Recherche dans mes documents", "Recherche jurisprudence (Légifrance)", "Recherche complète"],
                    key="search_mode_select"
                )
            
            with col2:
                # Mode de recherche Azure si disponible
                if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
                    from managers.azure_search_manager import SearchMode
                    azure_search_mode = st.selectbox(
                        "Type de recherche Azure",
                        [mode.value for mode in SearchMode],
                        key="azure_search_mode"
                    )
                else:
                    st.info("🔍 Recherche vectorielle non configurée")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Effectuer la recherche
        if search_clicked and search_query:
            st.session_state.search_query = search_query
            perform_search(search_query, search_mode)
    
    # Navigation Azure Blob
    st.markdown("### 📂 Explorer les documents SharePoint")
    
    display_azure_navigation()
    
    # Suggestions de recherche dynamiques
    if st.session_state.get('search_query'):
        display_search_suggestions()


def initialize_azure_managers():
    """Initialise les gestionnaires Azure s'ils ne sont pas déjà présents"""
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state:
        try:
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
        except Exception as e:
            st.error(f"Erreur initialisation Azure Blob: {e}")
            st.session_state.azure_blob_manager = None
    
    # Azure Search Manager
    if 'azure_search_manager' not in st.session_state:
        try:
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
        except Exception as e:
            st.error(f"Erreur initialisation Azure Search: {e}")
            st.session_state.azure_search_manager = None
    
    # Initialiser le stockage des documents
    if 'azure_documents' not in st.session_state:
        st.session_state.azure_documents = {}


def perform_search(search_query: str, search_mode: str):
    """Effectue la recherche selon le mode sélectionné"""
    with st.spinner("Recherche en cours..."):
        # Si recherche Légifrance
        if search_mode == "Recherche jurisprudence (Légifrance)":
            display_legifrance_search(search_query)
        
        # Si Azure Search disponible
        elif st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
            perform_azure_search(search_query)
        
        # Recherche locale
        else:
            perform_local_search(search_query)


def display_legifrance_search(search_query: str):
    """Affiche les liens de recherche Légifrance"""
    st.info("🏛️ Recherche sur les sources juridiques officielles")
    
    # Construire les URLs de recherche
    legifrance_url = f"https://www.legifrance.gouv.fr/search/all?tab=all&query={search_query}"
    judilibre_url = f"https://www.courdecassation.fr/recherche-judilibre?search_api_fulltext={search_query}"
    conseil_etat_url = "https://www.conseil-etat.fr/arianeweb/"
    
    st.markdown(f"""
    📎 **Liens utiles pour votre recherche :**
    - [🏛️ Rechercher sur Légifrance]({legifrance_url})
    - [⚖️ Jurisprudence judiciaire (Judilibre)]({judilibre_url})
    - [🏛️ Jurisprudence administrative (Conseil d'État)]({conseil_etat_url})
    - [📚 Doctrine.fr](https://www.doctrine.fr/search?q={search_query})
    
    💡 **Conseils pour une recherche efficace :**
    - Utilisez des références précises (articles de loi, numéros de pourvoi)
    - Employez les mots-clés juridiques exacts
    - Utilisez les opérateurs de recherche (ET, OU, SAUF)
    """)


def perform_azure_search(search_query: str):
    """Effectue une recherche avec Azure Search"""
    from managers.azure_search_manager import SearchMode
    
    # Mapper le mode sélectionné
    mode_str = st.session_state.get('azure_search_mode', SearchMode.HYBRID.value)
    mode_map = {
        "Recherche hybride (textuelle + sémantique)": SearchMode.HYBRID,
        "Recherche textuelle uniquement": SearchMode.TEXT_ONLY,
        "Recherche vectorielle uniquement": SearchMode.VECTOR_ONLY,
        "Recherche locale uniquement": SearchMode.LOCAL
    }
    
    selected_mode = mode_map.get(mode_str, SearchMode.HYBRID)
    
    # Effectuer la recherche
    results = st.session_state.azure_search_manager.search_hybrid(
        search_query,
        mode=selected_mode,
        top=20
    )
    
    # Afficher les résultats
    if results:
        st.success(f"✅ {len(results)} résultats trouvés")
        
        for result in results:
            display_search_result(result)
    else:
        st.info("Aucun résultat trouvé dans l'index Azure Search")
        
        # Proposer d'effectuer une recherche locale
        if st.button("🔍 Rechercher dans les documents locaux"):
            perform_local_search(search_query)


def perform_local_search(search_query: str):
    """Effectue une recherche dans les documents locaux"""
    st.info("🔍 Recherche dans les documents chargés...")
    
    results = []
    query_lower = search_query.lower()
    
    # Rechercher dans tous les documents
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if query_lower in doc.title.lower() or query_lower in doc.content.lower():
            # Calculer un score simple basé sur le nombre d'occurrences
            title_score = doc.title.lower().count(query_lower) * 2
            content_score = doc.content.lower().count(query_lower)
            total_score = title_score + content_score
            
            results.append({
                'document': doc,
                'score': total_score
            })
    
    # Trier par score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    if results:
        st.success(f"✅ {len(results)} résultats trouvés dans les documents locaux")
        
        for result in results[:20]:  # Limiter à 20 résultats
            doc = result['document']
            score = result['score']
            
            with st.container():
                st.markdown('<div class="document-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{doc.title}**")
                    st.caption(f"Score de pertinence: {score}")
                    
                    # Extraire un extrait pertinent
                    content_lower = doc.content.lower()
                    idx = content_lower.find(query_lower)
                    if idx != -1:
                        start = max(0, idx - 150)
                        end = min(len(doc.content), idx + 150)
                        excerpt = "..." + doc.content[start:end] + "..."
                        
                        # Surligner le terme recherché
                        excerpt = excerpt.replace(
                            search_query,
                            f"**{search_query}**"
                        )
                        st.markdown(excerpt)
                    else:
                        # Afficher le début du document
                        excerpt = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                        st.text(excerpt)
                
                with col2:
                    st.caption(f"Source: {doc.source}")
                    if doc.metadata.get('last_modified'):
                        st.caption(f"Modifié: {doc.metadata['last_modified']}")
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Aucun résultat trouvé dans les documents chargés")


def display_search_result(result: Dict[str, Any]):
    """Affiche un résultat de recherche"""
    with st.container():
        st.markdown('<div class="document-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"**{result['title']}**")
            st.caption(f"Score: {result['score']:.2f}")
            
            # Extrait du contenu
            excerpt = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
            st.text(excerpt)
        
        with col2:
            doc_id = result['id']
            
            if doc_id in st.session_state.get('azure_documents', {}):
                st.success("✅ Déjà ajouté")
            else:
                if st.button("➕ Ajouter", key=f"add_search_{doc_id}"):
                    # Créer un document à partir du résultat
                    doc = Document(
                        id=doc_id,
                        title=result['title'],
                        content=result['content'],
                        source=result.get('source', 'search'),
                        metadata=result.get('metadata', {})
                    )
                    st.session_state.azure_documents[doc.id] = doc
                    st.success("✅ Document ajouté")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_azure_navigation():
    """Affiche la navigation dans Azure Blob Storage"""
    azure_manager = st.session_state.get('azure_blob_manager')
    
    if not azure_manager:
        st.warning("⚠️ Gestionnaire Azure Blob non initialisé")
        return
    
    # Container par défaut
    selected_container = DEFAULT_CONTAINER
    
    # Vérifier que le container existe
    containers = azure_manager.list_containers()
    
    if not containers:
        st.warning("⚠️ Aucun container Azure trouvé")
        return
    
    if selected_container not in containers:
        st.error(f"❌ Le container '{selected_container}' n'existe pas.")
        
        # Proposer de sélectionner un autre container
        selected_container = st.selectbox(
            "Sélectionner un container",
            containers,
            key="select_container"
        )
    else:
        st.info(f"📁 Container actif : **{selected_container}**")
    
    # Navigation dans les dossiers
    if selected_container:
        display_folder_navigation(azure_manager, selected_container)


def display_folder_navigation(azure_manager, container_name: str):
    """Affiche la navigation dans les dossiers"""
    st.markdown('<div class="folder-nav">', unsafe_allow_html=True)
    
    # Fil d'Ariane
    current_path = st.session_state.get('current_folder_path', '')
    if current_path:
        display_breadcrumb(current_path)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lister le contenu
    with st.spinner("Chargement des documents..."):
        items = azure_manager.list_folders(container_name, current_path)
    
    if items:
        folders = [item for item in items if item['type'] == 'folder']
        files = [item for item in items if item['type'] == 'file']
        
        st.caption(f"📁 {len(folders)} dossiers, 📄 {len(files)} fichiers")
        
        # Afficher les dossiers
        if folders:
            display_folders(folders, azure_manager, container_name)
        
        # Afficher les fichiers
        if files:
            display_files(files, azure_manager, container_name, current_path)
    else:
        st.info("📭 Aucun document dans ce dossier")


def display_breadcrumb(current_path: str):
    """Affiche le fil d'Ariane"""
    path_parts = current_path.split('/')
    path_parts = [p for p in path_parts if p]
    
    cols = st.columns(len(path_parts) + 1)
    
    with cols[0]:
        if st.button("🏠 Racine", key="breadcrumb_root"):
            st.session_state.current_folder_path = ""
            st.rerun()
    
    for i, part in enumerate(path_parts):
        with cols[i + 1]:
            partial_path = '/'.join(path_parts[:i+1]) + '/'
            if st.button(f"📁 {part}", key=f"breadcrumb_{clean_key(part)}_{i}"):
                st.session_state.current_folder_path = partial_path
                st.rerun()


def display_folders(folders: List[Dict], azure_manager, container_name: str):
    """Affiche les dossiers"""
    st.markdown("#### 📁 Dossiers")
    
    for item in folders:
        with st.container():
            st.markdown('<div class="folder-card">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"📁 **{item['name']}**")
            
            with col2:
                # Compter les fichiers dans le dossier
                sub_items = azure_manager.list_folders(container_name, item['path'])
                sub_files = [i for i in sub_items if i['type'] == 'file']
                st.caption(f"{len(sub_files)} fichiers")
            
            with col3:
                col_open, col_add = st.columns(2)
                
                with col_open:
                    if st.button("📂", key=f"open_folder_{clean_key(item['name'])}", help="Ouvrir"):
                        st.session_state.current_folder_path = item['path']
                        st.rerun()
                
                with col_add:
                    if st.button("➕", key=f"add_folder_all_{clean_key(item['path'])}", help="Ajouter tout le dossier"):
                        add_entire_folder(azure_manager, container_name, item)
            
            st.markdown('</div>', unsafe_allow_html=True)


def display_files(files: List[Dict], azure_manager, container_name: str, current_path: str):
    """Affiche les fichiers"""
    st.markdown("#### 📄 Fichiers")
    
    for item in files:
        with st.container():
            st.markdown('<div class="document-card">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Icône selon le type de fichier
                file_ext = os.path.splitext(item['name'])[1].lower()
                icon = get_file_icon(file_ext)
                
                st.markdown(f"{icon} **{item['name']}**")
                
                if item.get('size'):
                    size_mb = item['size'] / (1024 * 1024)
                    st.caption(f"Taille: {size_mb:.2f} MB")
            
            with col2:
                if item.get('last_modified'):
                    st.caption(f"Modifié: {item['last_modified'].strftime('%d/%m/%Y')}")
            
            with col3:
                col_view, col_select = st.columns(2)
                
                with col_view:
                    if st.button("👁️", key=f"view_file_{clean_key(item['full_path'])}", help="Aperçu"):
                        display_file_preview(azure_manager, container_name, item)
                
                with col_select:
                    doc_id = f"azure_{clean_key(item['full_path'])}"
                    
                    if doc_id in st.session_state.get('azure_documents', {}):
                        st.success("✅")
                    else:
                        if st.button("➕", key=f"add_doc_{doc_id}", help="Ajouter"):
                            add_file_to_documents(azure_manager, container_name, item, current_path)
            
            st.markdown('</div>', unsafe_allow_html=True)


def get_file_icon(file_ext: str) -> str:
    """Retourne l'icône appropriée selon l'extension du fichier"""
    return {
        '.pdf': '📄',
        '.docx': '📝',
        '.doc': '📝',
        '.txt': '📃',
        '.xlsx': '📊',
        '.xls': '📊',
        '.pptx': '📽️',
        '.ppt': '📽️',
        '.csv': '📈',
        '.json': '🔧',
        '.xml': '🔧'
    }.get(file_ext, '📎')


def display_file_preview(azure_manager, container_name: str, file_info: Dict):
    """Affiche un aperçu du fichier"""
    with st.spinner("Chargement de l'aperçu..."):
        content = azure_manager.extract_text_from_blob(
            container_name,
            file_info['full_path']
        )
        
        if content:
            st.text_area(
                f"Aperçu de {file_info['name']}",
                content[:2000] + "..." if len(content) > 2000 else content,
                height=300,
                key=f"preview_{clean_key(file_info['full_path'])}"
            )
        else:
            st.warning("⚠️ Impossible d'extraire le contenu de ce fichier")


def add_file_to_documents(azure_manager, container_name: str, file_info: Dict, current_path: str):
    """Ajoute un fichier aux documents"""
    with st.spinner("Ajout du document..."):
        content = azure_manager.extract_text_from_blob(
            container_name,
            file_info['full_path']
        )
        
        if content:
            doc_id = f"azure_{clean_key(file_info['full_path'])}"
            doc = Document(
                id=doc_id,
                title=file_info['name'],
                content=content,
                source='azure',
                metadata={
                    'container': container_name,
                    'path': file_info['full_path'],
                    'size': file_info.get('size'),
                    'last_modified': file_info.get('last_modified')
                },
                folder_path=current_path
            )
            
            if 'azure_documents' not in st.session_state:
                st.session_state.azure_documents = {}
            
            st.session_state.azure_documents[doc_id] = doc
            
            # Indexer dans Azure Search si disponible
            if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
                success = st.session_state.azure_search_manager.index_doc