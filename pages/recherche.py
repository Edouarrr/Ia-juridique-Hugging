# pages/recherche.py
"""Page de recherche de documents"""

import streamlit as st
import os
import asyncio

from config.app_config import APP_CONFIG, SearchMode
from models.dataclasses import Document
from managers.dynamic_generators import generate_dynamic_search_prompts
from utils.helpers import clean_key

def show_page():
    """Affiche la page de recherche"""
    st.header("🔍 Recherche de documents")
    
    # Récupérer les gestionnaires depuis session state
    azure_manager = st.session_state.get('azure_blob_manager')
    search_manager = st.session_state.get('azure_search_manager')
    
    if not azure_manager or not azure_manager.is_connected():
        st.error("❌ Connexion Azure Blob non configurée. Veuillez vérifier vos variables d'environnement.")
        return
    
    # Section de recherche principale
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        
        # Barre de recherche
        with st.form(key="search_form"):
            col1, col2 = st.columns([4, 1])
            with col1:
                search_query = st.text_input(
                    "Rechercher dans tous les documents",
                    value=st.session_state.get('search_query', ''),
                    placeholder="Ex: abus de biens sociaux, délégation de pouvoirs...",
                    key="search_input_main"
                )
            
            with col2:
                search_clicked = st.form_submit_button("🔍 Rechercher", type="primary")
        
        # Options avancées
        with st.expander("Options avancées"):
            search_mode = st.selectbox(
                "Mode de recherche",
                ["Recherche dans mes documents", "Recherche jurisprudence (Légifrance)", "Recherche complète"],
                key="search_mode_select"
            )
            
            # Option pour la génération dynamique
            use_dynamic_prompts = st.checkbox(
                "🤖 Utiliser l'IA pour enrichir ma recherche",
                value=True,
                help="Génère automatiquement des recherches pertinentes basées sur votre requête"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Effectuer la recherche
        if search_clicked and search_query:
            st.session_state.search_query = search_query
            
            with st.spinner("Recherche en cours..."):
                if search_mode == "Recherche jurisprudence (Légifrance)":
                    show_legifrance_search(search_query)
                elif search_manager and search_manager.search_client:
                    show_azure_search_results(search_query, search_manager)
                else:
                    show_local_search_results(search_query)
    
    # Navigation Azure Blob
    st.markdown("### 📂 Explorer les documents SharePoint")
    show_azure_navigation(azure_manager)
    
    # Suggestions de recherche (avec génération dynamique)
    if st.session_state.get('search_query'):
        if st.session_state.get('search_mode_select') == "Recherche dans mes documents" and use_dynamic_prompts:
            show_dynamic_search_suggestions(st.session_state.search_query)
        else:
            show_search_suggestions(st.session_state.search_query)

def show_legifrance_search(search_query: str):
    """Affiche les liens de recherche Légifrance"""
    st.info("🏛️ Recherche sur Légifrance...")
    
    legifrance_url = f"https://www.legifrance.gouv.fr/search/all?tab=all&query={search_query}"
    
    st.markdown(f"""
    📎 **Liens utiles pour votre recherche :**
    - [Rechercher sur Légifrance]({legifrance_url})
    - [Jurisprudence judiciaire](https://www.courdecassation.fr/recherche-judilibre?search_api_fulltext={search_query})
    - [Jurisprudence administrative](https://www.conseil-etat.fr/arianeweb/)
    """)

def show_azure_search_results(search_query: str, search_manager):
    """Affiche les résultats de recherche Azure"""
    results = search_manager.search_hybrid(search_query, mode=SearchMode.HYBRID)
    
    if results:
        st.success(f"✅ {len(results)} résultats trouvés")
        
        for result in results[:20]:
            with st.container():
                st.markdown('<div class="document-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{result['title']}**")
                    st.caption(f"Score: {result['score']:.2f}")
                    
                    excerpt = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                    st.text(excerpt)
                
                with col2:
                    if result['id'] in st.session_state.azure_documents:
                        st.success("✅ Déjà ajouté")
                    else:
                        if st.button("➕ Ajouter", key=f"add_search_{result['id']}"):
                            doc = Document(
                                id=result['id'],
                                title=result['title'],
                                content=result['content'],
                                source=result['source']
                            )
                            st.session_state.azure_documents[doc.id] = doc
                            st.success("✅ Ajouté")
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Aucun résultat trouvé")

def show_local_search_results(search_query: str):
    """Affiche les résultats de recherche locale"""
    st.info("🔍 Recherche dans les documents locaux...")
    results = []
    
    for doc_id, doc in st.session_state.azure_documents.items():
        if search_query.lower() in doc.title.lower() or search_query.lower() in doc.content.lower():
            results.append(doc)
    
    if results:
        st.success(f"✅ {len(results)} résultats trouvés")
        
        for doc in results[:20]:
            with st.container():
                st.markdown('<div class="document-card">', unsafe_allow_html=True)
                st.markdown(f"**{doc.title}**")
                
                # Extrait avec le terme recherché
                content_lower = doc.content.lower()
                query_lower = search_query.lower()
                
                if query_lower in content_lower:
                    idx = content_lower.find(query_lower)
                    start = max(0, idx - 150)
                    end = min(len(doc.content), idx + 150)
                    excerpt = "..." + doc.content[start:end] + "..."
                    st.text(excerpt)
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Aucun résultat trouvé")

def show_azure_navigation(azure_manager):
    """Affiche la navigation dans Azure Blob"""
    selected_container = APP_CONFIG['DEFAULT_CONTAINER']
    
    # Vérifier que le container existe
    containers = azure_manager.list_containers()
    
    if selected_container not in containers:
        st.error(f"❌ Le container '{selected_container}' n'existe pas.")
        return
    
    st.info(f"📁 Container actif : **{selected_container}**")
    
    # Navigation dans les dossiers
    st.markdown('<div class="folder-nav">', unsafe_allow_html=True)
    
    # Fil d'Ariane
    current_path = st.session_state.get('current_folder_path', '')
    if current_path:
        show_breadcrumb(current_path)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lister le contenu
    with st.spinner("Chargement des documents..."):
        items = azure_manager.list_folders(selected_container, current_path)
    
    if items:
        show_folder_items(items, azure_manager, selected_container, current_path)
    else:
        st.info("📭 Aucun document dans ce dossier")

def show_breadcrumb(current_path: str):
    """Affiche le fil d'Ariane"""
    path_parts = current_path.split('/')
    path_parts = [p for p in path_parts if p]
    
    breadcrumb = "📁 "
    if st.button("Racine", key="breadcrumb_root"):
        st.session_state.current_folder_path = ""
        st.rerun()
    
    for i, part in enumerate(path_parts):
        breadcrumb += f" > "
        partial_path = '/'.join(path_parts[:i+1]) + '/'
        if st.button(part, key=f"breadcrumb_{clean_key(part)}_{i}"):
            st.session_state.current_folder_path = partial_path
            st.rerun()

def show_folder_items(items, azure_manager, selected_container, current_path):
    """Affiche les éléments d'un dossier"""
    folders = [item for item in items if item['type'] == 'folder']
    files = [item for item in items if item['type'] == 'file']
    
    st.caption(f"📁 {len(folders)} dossiers, 📄 {len(files)} fichiers")
    
    # Afficher les dossiers
    if folders:
        st.markdown("#### 📁 Dossiers")
        for item in folders:
            show_folder_item(item, azure_manager, selected_container)
    
    # Afficher les fichiers
    if files:
        st.markdown("#### 📄 Fichiers")
        for item in files:
            show_file_item(item, azure_manager, selected_container, current_path)

def show_folder_item(item, azure_manager, selected_container):
    """Affiche un élément dossier"""
    with st.container():
        st.markdown('<div class="folder-card">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"📁 **{item['name']}**")
        
        with col2:
            sub_items = azure_manager.list_folders(selected_container, item['path'])
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
                    add_entire_folder(azure_manager, selected_container, item)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_file_item(item, azure_manager, selected_container, current_path):
    """Affiche un élément fichier"""
    with st.container():
        st.markdown('<div class="document-card">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            file_ext = os.path.splitext(item['name'])[1].lower()
            icon = {
                '.pdf': '📄',
                '.docx': '📝',
                '.doc': '📝',
                '.txt': '📃',
                '.xlsx': '📊',
                '.xls': '📊'
            }.get(file_ext, '📎')
            
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
                if st.button("👁️", key=f"view_file_{clean_key(item['full_path'])}"):
                    view_file_content(azure_manager, selected_container, item)
            
            with col_select:
                doc_id = f"azure_{clean_key(item['full_path'])}"
                
                if doc_id in st.session_state.azure_documents:
                    st.success("✅")
                else:
                    if st.button("➕", key=f"add_doc_{doc_id}", help="Ajouter"):
                        add_file_to_documents(azure_manager, selected_container, item, current_path, doc_id)
        
        st.markdown('</div>', unsafe_allow_html=True)

def view_file_content(azure_manager, selected_container, item):
    """Affiche le contenu d'un fichier"""
    with st.spinner("Chargement..."):
        content = azure_manager.extract_text_from_blob(selected_container, item['full_path'])
        
        if content:
            st.text_area(
                f"Contenu de {item['name']}",
                content[:2000] + "..." if len(content) > 2000 else content,
                height=300,
                key=f"content_view_{clean_key(item['full_path'])}"
            )

def add_file_to_documents(azure_manager, selected_container, item, current_path, doc_id):
    """Ajoute un fichier aux documents"""
    with st.spinner("Ajout..."):
        content = azure_manager.extract_text_from_blob(selected_container, item['full_path'])
        
        if content:
            doc = Document(
                id=doc_id,
                title=item['name'],
                content=content,
                source='azure',
                metadata={
                    'container': selected_container,
                    'path': item['full_path'],
                    'size': item.get('size'),
                    'last_modified': item.get('last_modified')
                },
                folder_path=current_path
            )
            
            st.session_state.azure_documents[doc_id] = doc
            
            # Indexer dans Azure Search si disponible
            if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
                st.session_state.azure_search_manager.index_document(doc)
            
            st.success(f"✅ {item['name']} ajouté")
            st.rerun()

def add_entire_folder(azure_manager, selected_container, item):
    """Ajoute tous les fichiers d'un dossier"""
    with st.spinner(f"Ajout du dossier {item['name']}..."):
        all_files = azure_manager.get_all_files_in_folder(selected_container, item['path'])
        
        added_count = 0
        for file_info in all_files:
            content = azure_manager.extract_text_from_blob(selected_container, file_info['full_path'])
            
            if content:
                doc_id = f"azure_{clean_key(file_info['full_path'])}"
                doc = Document(
                    id=doc_id,
                    title=file_info['name'],
                    content=content,
                    source='azure',
                    metadata={
                        'container': selected_container,
                        'path': file_info['full_path'],
                        'size': file_info.get('size'),
                        'last_modified': file_info.get('last_modified')
                    },
                    folder_path=file_info['folder']
                )
                
                st.session_state.azure_documents[doc_id] = doc
                
                # Indexer dans Azure Search
                if st.session_state.get('azure_search_manager') and st.session_state.azure_search_manager.search_client:
                    st.session_state.azure_search_manager.index_document(doc)
                
                added_count += 1
        
        if added_count > 0:
            st.success(f"✅ {added_count} documents ajoutés")

def show_search_suggestions(search_query: str):
    """Affiche des suggestions de recherche statiques"""
    st.markdown("### 💡 Affiner votre recherche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📚 Recherches complémentaires")
        suggestions = [
            f"{search_query} jurisprudence récente",
            f"{search_query} Cour de cassation",
            f"{search_query} éléments constitutifs",
            f"{search_query} moyens de défense"
        ]
        
        for suggestion in suggestions:
            if st.button(suggestion, key=f"sugg_{clean_key(suggestion)}", use_container_width=True):
                st.session_state.search_query = suggestion
                st.rerun()
    
    with col2:
        st.markdown("#### 🏛️ Sources juridiques")
        st.markdown(f"""
        **Rechercher "{search_query}" sur :**
        - [📖 Légifrance](https://www.legifrance.gouv.fr/search/all?tab=all&query={search_query})
        - [⚖️ Cour de cassation](https://www.courdecassation.fr/recherche-judilibre?search_api_fulltext={search_query})
        - [🏛️ Conseil d'État](https://www.conseil-etat.fr/arianeweb/)
        """)

def show_dynamic_search_suggestions(search_query: str):
    """Affiche des suggestions de recherche générées dynamiquement par l'IA"""
    st.markdown("### 💡 Recherches suggérées par l'IA")
    
    # Vérifier si on a déjà généré des suggestions pour cette requête
    cache_key = f"prompts_{clean_key(search_query)}"
    
    if cache_key not in st.session_state:
        with st.spinner("🤖 Génération de suggestions intelligentes..."):
            # Contexte additionnel
            context = ""
            if st.session_state.get('infraction'):
                context += f"Infraction: {st.session_state.infraction}. "
            if st.session_state.get('client_type'):
                context += f"Type de client: {st.session_state.client_type}. "
            
            # Générer les prompts
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            suggestions_dynamiques = loop.run_until_complete(
                generate_dynamic_search_prompts(search_query, context)
            )
            
            st.session_state[cache_key] = suggestions_dynamiques
    else:
        suggestions_dynamiques = st.session_state[cache_key]
    
    # Afficher les suggestions par catégorie
    for categorie, sous_categories in suggestions_dynamiques.items():
        with st.expander(categorie, expanded=True):
            for sous_cat, prompts in sous_categories.items():
                st.markdown(f"**{sous_cat}**")
                
                # Créer une grille de boutons
                cols = st.columns(2)
                for i, prompt in enumerate(prompts[:4]):  # Limiter à 4 prompts par sous-catégorie
                    with cols[i % 2]:
                        if st.button(
                            prompt, 
                            key=f"dyn_sugg_{clean_key(categorie)}_{clean_key(sous_cat)}_{i}",
                            use_container_width=True,
                            help=f"Rechercher: {prompt}"
                        ):
                            st.session_state.search_query = prompt
                            st.rerun()
    
    # Option pour régénérer
    if st.button("🔄 Générer d'autres suggestions", key="regenerate_suggestions"):
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        st.rerun()