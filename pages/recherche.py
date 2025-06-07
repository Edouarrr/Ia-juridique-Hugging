# pages/recherche.py
"""Page de recherche de documents avec recherche juridique intégrée"""

import streamlit as st
import asyncio
from datetime import datetime

from config.app_config import SearchMode
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from managers.document_manager import display_import_interface
from managers.dynamic_generators import generate_dynamic_search_prompts
from managers.legal_search import LegalSearchManager, display_legal_search_interface
from models.dataclasses import Document
from utils.helpers import clean_key

def show_page():
    """Affiche la page de recherche"""
    st.header("🔍 Recherche de documents")
    
    # Onglets
    tabs = st.tabs([
        "🔎 Recherche", 
        "⚖️ Jurisprudence", 
        "🌐 Navigation Azure", 
        "📤 Import direct", 
        "🤖 Recherche intelligente"
    ])
    
    with tabs[0]:
        show_search_tab()
    
    with tabs[1]:
        show_jurisprudence_tab()
    
    with tabs[2]:
        show_azure_browser_tab()
    
    with tabs[3]:
        show_import_tab()
    
    with tabs[4]:
        show_intelligent_search_tab()

def show_search_tab():
    """Onglet de recherche principale"""
    # Champ de recherche
    search_query = st.text_input(
        "Rechercher dans les documents",
        value=st.session_state.get('search_query', ''),
        placeholder="Ex: abus de biens sociaux, fraude fiscale...",
        key="search_input"
    )
    
    # Options de recherche
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_mode = st.selectbox(
            "Mode de recherche",
            [mode.value for mode in SearchMode],
            key="search_mode"
        )
    
    with col2:
        nb_results = st.number_input(
            "Nombre de résultats",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            key="nb_results"
        )
    
    with col3:
        if st.button("🔍 Rechercher", type="primary", key="search_button"):
            if search_query:
                perform_search(search_query, search_mode, nb_results)
    
    # Afficher les résultats
    if 'search_results' in st.session_state:
        show_search_results(st.session_state.search_results)

def show_jurisprudence_tab():
    """Onglet de recherche juridique multi-sources"""
    display_legal_search_interface()

def show_azure_browser_tab():
    """Onglet de navigation Azure Blob"""
    if not st.session_state.get('azure_blob_manager'):
        st.warning("⚠️ Azure Blob Storage non configuré")
        return
    
    blob_manager = st.session_state.azure_blob_manager
    
    # Sélection du container
    containers = blob_manager.list_containers()
    
    if containers:
        selected_container = st.selectbox(
            "Sélectionner un container",
            containers,
            key="container_select"
        )
        
        if st.button("📂 Explorer", key="explore_container"):
            st.session_state.selected_container = selected_container
            st.session_state.current_folder_path = ""
    
    # Navigation dans les dossiers
    if st.session_state.get('selected_container'):
        show_folder_navigation()

def show_import_tab():
    """Onglet d'import direct"""
    st.markdown("### 📤 Import direct de documents")
    display_import_interface()

def show_intelligent_search_tab():
    """Onglet de recherche intelligente avec prompts dynamiques"""
    st.markdown("### 🤖 Recherche juridique intelligente")
    
    st.info("""
    Cette fonctionnalité génère automatiquement des requêtes de recherche optimisées
    pour couvrir tous les aspects juridiques de votre recherche.
    """)
    
    # Champ de recherche
    topic = st.text_input(
        "Sujet de recherche",
        placeholder="Ex: Abus de biens sociaux, corruption, fraude fiscale...",
        key="intelligent_search_topic"
    )
    
    # Contexte optionnel
    with st.expander("➕ Ajouter du contexte (optionnel)"):
        context_client = st.text_input("Client concerné", key="context_client_search")
        context_juridiction = st.text_input("Juridiction", key="context_juridiction_search")
        context_date = st.text_input("Période concernée", key="context_date_search")
    
    if st.button("🎯 Générer les recherches", type="primary", key="generate_searches"):
        if topic:
            generate_intelligent_searches(topic, {
                'client': context_client,
                'juridiction': context_juridiction,
                'date': context_date
            })

def generate_intelligent_searches(topic: str, context: dict):
    """Génère et affiche les recherches intelligentes"""
    with st.spinner("🔄 Génération des requêtes de recherche optimisées..."):
        # Générer les prompts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Convertir le contexte dict en string pour la fonction
        context_str = ""
        if context.get('client'):
            context_str += f"Client: {context['client']}. "
        if context.get('juridiction'):
            context_str += f"Juridiction: {context['juridiction']}. "
        if context.get('date'):
            context_str += f"Date: {context['date']}. "
        
        search_prompts = loop.run_until_complete(
            generate_dynamic_search_prompts(topic, context_str)
        )
        
        # Stocker dans session state
        cache_key = f"search_{clean_key(topic)}"
        st.session_state.dynamic_search_prompts[cache_key] = search_prompts
        
        # Afficher les résultats
        if search_prompts:
            st.success("✅ Requêtes de recherche générées avec succès!")
            
            # Pour chaque catégorie
            for category, subcategories in search_prompts.items():
                with st.expander(f"{category}", expanded=True):
                    # Si c'est un dictionnaire avec sous-catégories
                    if isinstance(subcategories, dict):
                        for subcat, queries in subcategories.items():
                            st.markdown(f"**{subcat}**")
                            for i, query in enumerate(queries):
                                col1, col2 = st.columns([4, 1])
                                
                                with col1:
                                    st.text(query)
                                
                                with col2:
                                    if st.button("🔍", key=f"search_query_{clean_key(category)}_{clean_key(subcat)}_{i}"):
                                        # Lancer la recherche
                                        perform_search(query, SearchMode.HYBRID.value, 10)
                    # Si c'est directement une liste de requêtes
                    elif isinstance(subcategories, list):
                        for i, query in enumerate(subcategories):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.text(query)
                            
                            with col2:
                                if st.button("🔍", key=f"search_query_{clean_key(category)}_{i}"):
                                    # Lancer la recherche
                                    perform_search(query, SearchMode.HYBRID.value, 10)
            
            # Bouton pour rechercher tout
            if st.button("🚀 Lancer toutes les recherches", type="primary", key="search_all"):
                all_queries = []
                for subcategories in search_prompts.values():
                    if isinstance(subcategories, dict):
                        for queries in subcategories.values():
                            all_queries.extend(queries)
                    elif isinstance(subcategories, list):
                        all_queries.extend(subcategories)
                
                # Limiter à 20 requêtes max
                for query in all_queries[:20]:
                    perform_search(query, SearchMode.HYBRID.value, 5)
                
                st.success(f"✅ {min(len(all_queries), 20)} recherches effectuées!")
        else:
            st.error("❌ Impossible de générer les requêtes. Vérifiez la configuration des IA.")

def perform_search(query: str, mode: str, limit: int):
    """Effectue une recherche"""
    st.session_state.search_query = query
    
    results = []
    
    # Recherche Azure Search si disponible
    if st.session_state.get('azure_search_manager') and mode != SearchMode.LOCAL.value:
        search_manager = st.session_state.azure_search_manager
        
        if mode == SearchMode.HYBRID.value:
            results = search_manager.search_hybrid(query, top=limit)
        elif mode == SearchMode.TEXT_ONLY.value:
            results = search_manager.search_text(query, top=limit)
        elif mode == SearchMode.VECTOR_ONLY.value:
            results = search_manager.search_vector(query, top=limit)
    
    # Recherche locale dans les documents chargés
    if mode == SearchMode.LOCAL.value or not results:
        results = search_local_documents(query, limit)
    
    st.session_state.search_results = results

def search_local_documents(query: str, limit: int):
    """Recherche dans les documents locaux"""
    results = []
    query_lower = query.lower()
    
    for doc_id, doc in st.session_state.azure_documents.items():
        if query_lower in doc.title.lower() or query_lower in doc.content.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content[:500] + "...",
                'score': 1.0,
                'source': doc.source
            })
    
    return results[:limit]

def show_search_results(results):
    """Affiche les résultats de recherche"""
    st.markdown(f"### 📊 Résultats ({len(results)} documents)")
    
    for result in results:
        with st.container():
            st.markdown('<div class="document-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**{result['title']}**")
                st.caption(f"Score: {result.get('score', 0):.2f} | Source: {result.get('source', 'Unknown')}")
                st.text(result['content'][:200] + "...")
            
            with col2:
                if st.button("👁️", key=f"view_{result['id']}"):
                    show_document_detail(result['id'])
                
                if st.button("➕", key=f"add_{result['id']}"):
                    add_to_selection(result['id'])
            
            st.markdown('</div>', unsafe_allow_html=True)

def show_folder_navigation():
    """Affiche la navigation dans les dossiers Azure"""
    blob_manager = st.session_state.azure_blob_manager
    container = st.session_state.selected_container
    current_path = st.session_state.get('current_folder_path', '')
    
    # Fil d'Ariane
    st.markdown(f"📁 **{container}** / {current_path}")
    
    # Lister le contenu
    try:
        items = blob_manager.list_folder_contents(container, current_path)
        
        # Séparer dossiers et fichiers
        folders = [item for item in items if item['type'] == 'folder']
        files = [item for item in items if item['type'] == 'file']
        
        # Afficher les dossiers
        if folders:
            st.markdown("#### 📂 Dossiers")
            for folder in folders:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.text(f"📁 {folder['name']}")
                
                with col2:
                    if st.button("Ouvrir", key=f"folder_{folder['name']}"):
                        st.session_state.current_folder_path = folder['path']
                        st.rerun()
        
        # Afficher les fichiers
        if files:
            st.markdown("#### 📄 Fichiers")
            for file in files:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.text(f"📄 {file['name']}")
                    st.caption(f"Taille: {file['size'] / 1024:.2f} KB")
                
                with col2:
                    if st.button("📥", key=f"download_{file['name']}"):
                        download_file(container, file['path'])
                
                with col3:
                    if st.button("➕", key=f"add_file_{file['name']}"):
                        add_file_to_documents(container, file)
        
        # Bouton retour
        if current_path:
            if st.button("⬅️ Retour"):
                parent_path = "/".join(current_path.split("/")[:-1])
                st.session_state.current_folder_path = parent_path
                st.rerun()
                
    except Exception as e:
        st.error(f"Erreur lors de la navigation : {str(e)}")

def show_document_detail(doc_id: str):
    """Affiche le détail d'un document"""
    if doc_id in st.session_state.azure_documents:
        doc = st.session_state.azure_documents[doc_id]
        
        with st.expander(f"📄 {doc.title}", expanded=True):
            st.text_area("Contenu", doc.content, height=400)
            
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Source: {doc.source}")
                st.caption(f"Créé le: {doc.created_at.strftime('%d/%m/%Y')}")
            
            with col2:
                if st.button("➕ Ajouter à la sélection", key=f"detail_add_{doc_id}"):
                    add_to_selection(doc_id)

def add_to_selection(doc_id: str):
    """Ajoute un document à la sélection"""
    from models.dataclasses import PieceSelectionnee
    
    if doc_id in st.session_state.azure_documents:
        doc = st.session_state.azure_documents[doc_id]
        
        piece = PieceSelectionnee(
            document_id=doc_id,
            titre=doc.title,
            categorie="📄 Documents",
            notes="Ajouté depuis la recherche"
        )
        
        st.session_state.pieces_selectionnees[doc_id] = piece
        st.success(f"✅ '{doc.title}' ajouté à la sélection")

def download_file(container: str, file_path: str):
    """Télécharge un fichier depuis Azure"""
    blob_manager = st.session_state.azure_blob_manager
    
    try:
        content = blob_manager.download_blob(container, file_path)
        
        st.download_button(
            "💾 Télécharger",
            content,
            file_path.split("/")[-1],
            key=f"download_content_{file_path}"
        )
    except Exception as e:
        st.error(f"Erreur téléchargement : {str(e)}")

def add_file_to_documents(container: str, file_info: dict):
    """Ajoute un fichier aux documents"""
    blob_manager = st.session_state.azure_blob_manager
    
    try:
        # Télécharger le contenu
        content = blob_manager.download_blob(container, file_info['path'])
        
        # Créer un document
        doc = Document(
            id=f"azure_{container}_{file_info['name']}",
            title=file_info['name'],
            content=content.decode('utf-8', errors='ignore'),
            source=f"Azure: {container}",
            folder_path=file_info['path']
        )
        
        st.session_state.azure_documents[doc.id] = doc
        st.success(f"✅ '{file_info['name']}' ajouté aux documents")
        
    except Exception as e:
        st.error(f"Erreur ajout document : {str(e)}")