"""Application principale avec Azure Blob Storage, Search et OpenAI intégrés"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import time
import json
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import uuid
import asyncio

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="IA Juridique - Droit Pénal des Affaires",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SECTION AZURE - IMPORTS ET VÉRIFICATIONS ==========

# Azure Blob Storage
AZURE_BLOB_AVAILABLE = False
AZURE_BLOB_ERROR = None

try:
    from azure.storage.blob import BlobServiceClient, ContainerClient
    from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
    AZURE_BLOB_AVAILABLE = True
    logger.info("✅ Azure Blob Storage disponible")
except ImportError as e:
    AZURE_BLOB_ERROR = str(e)
    logger.error(f"❌ Azure Blob Storage non disponible: {AZURE_BLOB_ERROR}")

# Azure Search
AZURE_SEARCH_AVAILABLE = False
AZURE_SEARCH_ERROR = None

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.models import VectorizedQuery
    from azure.core.credentials import AzureKeyCredential
    AZURE_SEARCH_AVAILABLE = True
    logger.info("✅ Azure Search disponible")
except ImportError as e:
    AZURE_SEARCH_ERROR = str(e)
    logger.warning(f"⚠️ Azure Search non disponible: {AZURE_SEARCH_ERROR}")

# Azure OpenAI
AZURE_OPENAI_AVAILABLE = False
AZURE_OPENAI_ERROR = None

try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
    logger.info("✅ Azure OpenAI disponible")
except ImportError as e:
    AZURE_OPENAI_ERROR = str(e)
    logger.warning(f"⚠️ Azure OpenAI non disponible: {AZURE_OPENAI_ERROR}")

# ========== GESTIONNAIRE AZURE BLOB STORAGE ==========

class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage"""
    
    def __init__(self):
        self.connected = False
        self.blob_service_client = None
        self.connection_error = None
        
        if not AZURE_BLOB_AVAILABLE:
            self.connection_error = "Modules Azure Blob non disponibles"
            return
        
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        if not connection_string:
            self.connection_error = "AZURE_STORAGE_CONNECTION_STRING non définie"
            return
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            # Test de connexion
            list(self.blob_service_client.list_containers(max_results=1))
            self.connected = True
            logger.info("✅ Azure Blob connecté")
        except Exception as e:
            self.connection_error = str(e)
            logger.error(f"❌ Erreur connexion Azure Blob: {e}")
    
    def is_connected(self):
        return self.connected
    
    def list_containers(self):
        if not self.connected:
            return []
        try:
            return [container.name for container in self.blob_service_client.list_containers()]
        except Exception as e:
            logger.error(f"Erreur liste conteneurs: {e}")
            return []
    
    def list_blobs(self, container_name: str, prefix: str = ""):
        if not self.connected:
            return []
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = []
            for blob in container_client.list_blobs(prefix=prefix):
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None
                })
            return blobs
        except Exception as e:
            logger.error(f"Erreur liste blobs: {e}")
            return []
    
    def download_blob(self, container_name: str, blob_name: str):
        if not self.connected:
            return None
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            return blob_client.download_blob().readall()
        except Exception as e:
            logger.error(f"Erreur téléchargement blob: {e}")
            return None
    
    def upload_blob(self, container_name: str, blob_name: str, data: bytes):
        if not self.connected:
            return False
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            blob_client.upload_blob(data, overwrite=True)
            return True
        except Exception as e:
            logger.error(f"Erreur upload blob: {e}")
            return False

# ========== GESTIONNAIRE AZURE SEARCH ==========

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search"""
    
    def __init__(self):
        self.connected = False
        self.search_client = None
        self.index_client = None
        self.connection_error = None
        self.index_name = "juridique-documents"
        
        if not AZURE_SEARCH_AVAILABLE:
            self.connection_error = "Modules Azure Search non disponibles"
            return
        
        endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        key = os.getenv('AZURE_SEARCH_KEY')
        
        if not endpoint or not key:
            self.connection_error = "Configuration Azure Search manquante"
            return
        
        try:
            credential = AzureKeyCredential(key)
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=self.index_name,
                credential=credential
            )
            self.index_client = SearchIndexClient(
                endpoint=endpoint,
                credential=credential
            )
            self.connected = True
            logger.info("✅ Azure Search connecté")
        except Exception as e:
            self.connection_error = str(e)
            logger.error(f"❌ Erreur connexion Azure Search: {e}")
    
    def is_connected(self):
        return self.connected
    
    def search_documents(self, query: str, filters: Dict = None, top: int = 10):
        """Recherche de documents"""
        if not self.connected:
            return []
        
        try:
            search_results = self.search_client.search(
                search_text=query,
                filter=self._build_filter(filters) if filters else None,
                top=top,
                include_total_count=True
            )
            
            results = []
            for result in search_results:
                results.append({
                    'id': result.get('id'),
                    'title': result.get('title'),
                    'content': result.get('content'),
                    'container': result.get('container'),
                    'blob_name': result.get('blob_name'),
                    'score': result.get('@search.score'),
                    'highlights': result.get('@search.highlights', {})
                })
            
            return results
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    def index_document(self, document: Dict):
        """Indexe un document"""
        if not self.connected:
            return False
        
        try:
            self.search_client.upload_documents([document])
            return True
        except Exception as e:
            logger.error(f"Erreur indexation: {e}")
            return False
    
    def _build_filter(self, filters: Dict) -> str:
        """Construit un filtre OData"""
        filter_parts = []
        
        if 'container' in filters:
            filter_parts.append(f"container eq '{filters['container']}'")
        
        if 'date_from' in filters:
            filter_parts.append(f"last_modified ge {filters['date_from'].isoformat()}")
        
        if 'date_to' in filters:
            filter_parts.append(f"last_modified le {filters['date_to'].isoformat()}")
        
        return " and ".join(filter_parts) if filter_parts else None

# ========== GESTIONNAIRE AZURE OPENAI ==========

class AzureOpenAIManager:
    """Gestionnaire pour Azure OpenAI"""
    
    def __init__(self):
        self.connected = False
        self.client = None
        self.connection_error = None
        self.deployment_name = None
        
        if not AZURE_OPENAI_AVAILABLE:
            self.connection_error = "Module OpenAI non disponible"
            return
        
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        key = os.getenv('AZURE_OPENAI_KEY')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
        
        if not endpoint or not key:
            self.connection_error = "Configuration Azure OpenAI manquante"
            return
        
        try:
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=key,
                api_version="2024-02-01"
            )
            # Test de connexion
            self.client.models.list()
            self.connected = True
            logger.info("✅ Azure OpenAI connecté")
        except Exception as e:
            self.connection_error = str(e)
            logger.error(f"❌ Erreur connexion Azure OpenAI: {e}")
    
    def is_connected(self):
        return self.connected
    
    async def analyze_document(self, content: str, prompt: str):
        """Analyse un document avec Azure OpenAI"""
        if not self.connected:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en droit pénal des affaires français."},
                    {"role": "user", "content": f"{prompt}\n\nDocument:\n{content[:4000]}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur analyse Azure OpenAI: {e}")
            return None

# ========== CONFIGURATION DES IA ==========

def get_available_ais():
    """Retourne les IA disponibles selon la configuration"""
    ais = {
        "GPT-3.5": {"icon": "🤖", "description": "Analyse rapide", "available": True, "type": "standard"},
        "GPT-4": {"icon": "🧠", "description": "Analyse approfondie", "available": True, "type": "standard"},
        "Claude Opus 4": {"icon": "🎭", "description": "Argumentation avancée", "available": True, "type": "standard"},
        "Gemini": {"icon": "✨", "description": "Recherche exhaustive", "available": True, "type": "standard"},
        "Mistral": {"icon": "🌟", "description": "IA française", "available": True, "type": "standard"}
    }
    
    # Ajouter Azure OpenAI si disponible et activé
    if AZURE_OPENAI_AVAILABLE and st.session_state.get('azure_openai_enabled', False):
        azure_openai_manager = st.session_state.get('azure_openai_manager')
        if azure_openai_manager and azure_openai_manager.is_connected():
            ais["Azure OpenAI"] = {
                "icon": "☁️", 
                "description": "IA sécurisée Microsoft", 
                "available": True,
                "type": "azure"
            }
    
    return ais

# ========== FONCTIONS CSS ==========

def load_custom_css():
    st.markdown("""
    <style>
    /* Variables CSS */
    :root {
        --primary-color: #1a1a2e;
        --secondary-color: #16213e;
        --accent-color: #e94560;
        --success-color: #0f3460;
        --azure-color: #0078d4;
        --text-primary: #2c3e50;
        --text-secondary: #7f8c8d;
        --border-color: #bdc3c7;
        --background-light: #f8f9fa;
    }
    
    /* Layout compact */
    .block-container {
        padding-top: 0.5rem !important;
        max-width: 1600px !important;
    }
    
    /* Services Azure */
    .azure-service {
        background: #f0f8ff;
        border: 1px solid var(--azure-color);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    .azure-service.connected {
        border-left: 4px solid #28a745;
    }
    
    .azure-service.disconnected {
        border-left: 4px solid #dc3545;
    }
    
    .azure-service.optional {
        border-left: 4px solid #ffc107;
    }
    
    /* Toggle Azure */
    .azure-toggle {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: #e3f2fd;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Search results */
    .search-result {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 15px;
        margin: 10px 0;
        transition: all 0.2s ease;
    }
    
    .search-result:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .search-highlight {
        background: #ffeb3b;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-badge.connected {
        background: #d4edda;
        color: #155724;
    }
    
    .status-badge.disconnected {
        background: #f8d7da;
        color: #721c24;
    }
    
    .status-badge.optional {
        background: #fff3cd;
        color: #856404;
    }
    
    /* Document cards */
    .document-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .document-card:hover {
        background: var(--background-light);
        transform: translateX(3px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Typography */
    h1 { font-size: 1.4rem !important; margin-bottom: 0.3rem !important; }
    h2 { font-size: 1.2rem !important; margin-bottom: 0.3rem !important; }
    h3 { font-size: 1.05rem !important; margin-bottom: 0.3rem !important; }
    </style>
    """, unsafe_allow_html=True)

# ========== ÉTAT GLOBAL ==========

def init_session_state():
    """Initialise les variables de session"""
    defaults = {
        'selected_ais': [],
        'response_mode': 'fusion',
        'current_view': 'dashboard',
        'search_query': "",
        'current_container': None,
        'selected_documents': [],
        'azure_blob_manager': None,
        'azure_search_manager': None,
        'azure_openai_manager': None,
        'azure_initialized': False,
        'azure_openai_enabled': False,
        'azure_search_enabled': True,
        'search_results': [],
        'analysis_results': {}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialiser les services Azure
    if not st.session_state.azure_initialized:
        init_azure_services()

def init_azure_services():
    """Initialise tous les services Azure"""
    # Blob Storage (obligatoire)
    try:
        st.session_state.azure_blob_manager = AzureBlobManager()
        logger.info("Azure Blob Manager initialisé")
    except Exception as e:
        logger.error(f"Erreur init Azure Blob: {e}")
    
    # Search (optionnel)
    if AZURE_SEARCH_AVAILABLE and st.session_state.azure_search_enabled:
        try:
            st.session_state.azure_search_manager = AzureSearchManager()
            logger.info("Azure Search Manager initialisé")
        except Exception as e:
            logger.error(f"Erreur init Azure Search: {e}")
    
    # OpenAI (optionnel)
    if AZURE_OPENAI_AVAILABLE and st.session_state.azure_openai_enabled:
        try:
            st.session_state.azure_openai_manager = AzureOpenAIManager()
            logger.info("Azure OpenAI Manager initialisé")
        except Exception as e:
            logger.error(f"Erreur init Azure OpenAI: {e}")
    
    st.session_state.azure_initialized = True

# ========== AFFICHAGE STATUS AZURE ==========

def display_azure_services_status():
    """Affiche le statut de tous les services Azure"""
    st.markdown("### 🔌 Services Azure")
    
    # Blob Storage (obligatoire)
    blob_manager = st.session_state.get('azure_blob_manager')
    blob_status = blob_manager and blob_manager.is_connected()
    
    st.markdown(f"""
    <div class="azure-service {'connected' if blob_status else 'disconnected'}">
        <strong>{'✅' if blob_status else '❌'} Azure Blob Storage</strong> (Obligatoire)<br>
        <small>{blob_manager.connection_error if blob_manager and not blob_status else 'Connecté'}</small>
    </div>
    """, unsafe_allow_html=True)
    
    if not blob_status:
        st.error("""
        **Configuration requise :**
        1. Définir `AZURE_STORAGE_CONNECTION_STRING` dans les secrets
        2. Format : `DefaultEndpointsProtocol=https;AccountName=...`
        """)
        return False
    
    # Azure Search (optionnel)
    col1, col2 = st.columns([3, 1])
    with col1:
        search_manager = st.session_state.get('azure_search_manager')
        search_status = search_manager and search_manager.is_connected() if st.session_state.azure_search_enabled else False
        
        st.markdown(f"""
        <div class="azure-service {'connected' if search_status else 'optional'}">
            <strong>{'✅' if search_status else '⚠️'} Azure Search</strong> (Optionnel)<br>
            <small>{'Connecté' if search_status else 'Non configuré ou désactivé'}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        new_search_state = st.checkbox(
            "Activer",
            value=st.session_state.azure_search_enabled,
            key="toggle_search"
        )
        if new_search_state != st.session_state.azure_search_enabled:
            st.session_state.azure_search_enabled = new_search_state
            st.session_state.azure_initialized = False
            st.rerun()
    
    # Azure OpenAI (optionnel)
    col3, col4 = st.columns([3, 1])
    with col3:
        openai_manager = st.session_state.get('azure_openai_manager')
        openai_status = openai_manager and openai_manager.is_connected() if st.session_state.azure_openai_enabled else False
        
        st.markdown(f"""
        <div class="azure-service {'connected' if openai_status else 'optional'}">
            <strong>{'✅' if openai_status else '⚠️'} Azure OpenAI</strong> (Optionnel)<br>
            <small>{'Connecté' if openai_status else 'Non configuré ou désactivé'}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        new_openai_state = st.checkbox(
            "Activer",
            value=st.session_state.azure_openai_enabled,
            key="toggle_openai"
        )
        if new_openai_state != st.session_state.azure_openai_enabled:
            st.session_state.azure_openai_enabled = new_openai_state
            st.session_state.azure_initialized = False
            st.rerun()
    
    return blob_status

# ========== RECHERCHE AVEC AZURE SEARCH ==========

def search_with_azure_search():
    """Interface de recherche avec Azure Search"""
    search_manager = st.session_state.get('azure_search_manager')
    
    if not search_manager or not search_manager.is_connected():
        st.info("Azure Search non disponible - Recherche basique activée")
        return basic_search()
    
    st.markdown("### 🔍 Recherche avancée avec Azure Search")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Rechercher dans tous les documents",
            placeholder="Ex: contrat de vente, procès-verbal, expertise...",
            key="azure_search_query"
        )
    
    with col2:
        search_button = st.button("🔍 Rechercher", type="primary", use_container_width=True)
    
    # Filtres avancés
    with st.expander("⚙️ Filtres avancés"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            container_filter = st.selectbox(
                "Conteneur",
                ["Tous"] + (st.session_state.azure_blob_manager.list_containers() if st.session_state.azure_blob_manager else []),
                key="search_container_filter"
            )
        
        with col2:
            date_from = st.date_input("Date début", key="search_date_from")
        
        with col3:
            date_to = st.date_input("Date fin", key="search_date_to")
    
    if search_button and query:
        with st.spinner("Recherche en cours..."):
            # Construire les filtres
            filters = {}
            if container_filter != "Tous":
                filters['container'] = container_filter
            if date_from:
                filters['date_from'] = datetime.combine(date_from, datetime.min.time())
            if date_to:
                filters['date_to'] = datetime.combine(date_to, datetime.max.time())
            
            # Recherche
            results = search_manager.search_documents(query, filters=filters, top=20)
            st.session_state.search_results = results
            
            # Affichage des résultats
            if results:
                st.success(f"✅ {len(results)} résultats trouvés")
                
                for idx, result in enumerate(results):
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        
                        with col1:
                            st.markdown(f"""
                            <div class="search-result">
                                <h4>📄 {result['title']}</h4>
                                <p><small>📁 {result['container']} | Score: {result['score']:.2f}</small></p>
                                <p>{result['content'][:200]}...</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("Analyser", key=f"analyze_{idx}"):
                                st.session_state.selected_documents = [f"{result['container']}/{result['blob_name']}"]
                                st.session_state.current_view = "analyze_real_documents"
                                st.rerun()
            else:
                st.warning("Aucun résultat trouvé")

def basic_search():
    """Recherche basique sans Azure Search"""
    st.markdown("### 🔍 Recherche dans les documents")
    
    query = st.text_input(
        "Rechercher",
        placeholder="Entrez votre recherche...",
        key="basic_search_query"
    )
    
    if query and st.button("Rechercher", type="primary"):
        st.info("Recherche basique - Activez Azure Search pour une recherche avancée")

# ========== ANALYSE AVEC AZURE OPENAI ==========

async def analyze_with_azure_openai(documents: List[str], prompt: str):
    """Analyse des documents avec Azure OpenAI"""
    openai_manager = st.session_state.get('azure_openai_manager')
    
    if not openai_manager or not openai_manager.is_connected():
        return None
    
    blob_manager = st.session_state.azure_blob_manager
    results = []
    
    for doc_path in documents[:3]:  # Limiter à 3 documents
        try:
            container, blob_name = doc_path.split('/', 1)
            content = blob_manager.download_blob(container, blob_name)
            
            if content:
                # Convertir en texte selon le type
                text_content = content.decode('utf-8', errors='ignore')[:4000]
                
                # Analyser avec Azure OpenAI
                analysis = await openai_manager.analyze_document(text_content, prompt)
                
                if analysis:
                    results.append({
                        'document': doc_path,
                        'analysis': analysis
                    })
        except Exception as e:
            logger.error(f"Erreur analyse document {doc_path}: {e}")
    
    return results

# ========== AFFICHAGE DES DOCUMENTS ==========

def display_documents_with_search():
    """Affiche les documents avec option de recherche"""
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if not blob_manager or not blob_manager.is_connected():
        st.warning("⚠️ Connexion Azure Blob requise")
        return
    
    # Recherche si Azure Search activé
    if st.session_state.azure_search_enabled:
        search_with_azure_search()
        st.markdown("---")
    
    # Liste des documents
    st.markdown("### 📁 Documents disponibles")
    
    containers = blob_manager.list_containers()
    if not containers:
        st.info("Aucun conteneur disponible")
        return
    
    selected_container = st.selectbox(
        "Sélectionner un dossier",
        containers,
        key="container_select"
    )
    
    if selected_container:
        with st.spinner(f"Chargement de {selected_container}..."):
            blobs = blob_manager.list_blobs(selected_container)
        
        if blobs:
            # Stats
            total_size = sum(b.get('size', 0) for b in blobs) / (1024 * 1024)
            st.info(f"📄 {len(blobs)} documents • 💾 {total_size:.1f} MB")
            
            # Affichage avec sélection
            for blob in blobs:
                doc_path = f"{selected_container}/{blob['name']}"
                unique_key = f"doc_{hashlib.md5(doc_path.encode()).hexdigest()[:8]}"
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    size_kb = blob.get('size', 0) / 1024
                    st.markdown(f"""
                    <div class="document-card">
                        📄 {blob['name']}
                        <span style="float: right; color: #7f8c8d; font-size: 0.8rem;">{size_kb:.1f} KB</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.checkbox("", key=unique_key, value=doc_path in st.session_state.selected_documents):
                        if doc_path not in st.session_state.selected_documents:
                            st.session_state.selected_documents.append(doc_path)
                    else:
                        if doc_path in st.session_state.selected_documents:
                            st.session_state.selected_documents.remove(doc_path)

# ========== ANALYSE DES DOCUMENTS ==========

def analyze_real_documents():
    """Analyse les documents avec les IA sélectionnées"""
    if not st.session_state.selected_documents:
        st.warning("Sélectionnez des documents à analyser")
        return
    
    if not st.session_state.selected_ais:
        st.warning("Sélectionnez au moins une IA")
        return
    
    st.markdown(f"### 🤖 Analyse de {len(st.session_state.selected_documents)} document(s)")
    
    # Prompt d'analyse
    prompt = st.text_area(
        "Instructions d'analyse",
        value=st.session_state.get('search_query', ''),
        placeholder="Décrivez ce que vous recherchez...",
        height=100
    )
    
    if st.button("🚀 Lancer l'analyse", type="primary"):
        # Vérifier si Azure OpenAI est sélectionné
        use_azure_openai = "Azure OpenAI" in st.session_state.selected_ais
        
        if use_azure_openai and st.session_state.azure_openai_enabled:
            # Analyse avec Azure OpenAI
            with st.spinner("Analyse avec Azure OpenAI..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(
                    analyze_with_azure_openai(st.session_state.selected_documents, prompt)
                )
                
                if results:
                    st.success("✅ Analyse terminée")
                    
                    for result in results:
                        with st.expander(f"📄 {result['document']}"):
                            st.markdown(result['analysis'])
                else:
                    st.error("Aucun résultat d'analyse")
        else:
            # Analyse simulée pour les autres IA
            with st.spinner(f"Analyse par {len(st.session_state.selected_ais)} IA..."):
                progress = st.progress(0)
                for i in range(100):
                    progress.progress(i + 1)
                    time.sleep(0.01)
            
            st.success("✅ Analyse terminée")
            st.info("Configuration des APIs LLM requise pour une analyse réelle")

# ========== SÉLECTEUR IA ==========

def create_ai_selector():
    """Sélecteur d'IA avec Azure OpenAI conditionnel"""
    st.markdown("#### 🤖 Sélection des IA")
    
    available_ais = get_available_ais()
    
    cols = st.columns(3)
    for idx, (ai_name, ai_info) in enumerate(available_ais.items()):
        if ai_info['available']:
            with cols[idx % 3]:
                selected = ai_name in st.session_state.selected_ais
                unique_key = f"ai_{ai_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
                
                if st.checkbox(
                    f"{ai_info['icon']} {ai_name}",
                    value=selected,
                    key=unique_key,
                    help=ai_info['description']
                ):
                    if ai_name not in st.session_state.selected_ais:
                        st.session_state.selected_ais.append(ai_name)
                else:
                    if ai_name in st.session_state.selected_ais:
                        st.session_state.selected_ais.remove(ai_name)

# ========== SIDEBAR ==========

def create_sidebar():
    """Sidebar avec statut des services"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #1a1a2e, #0078d4); 
                    margin: -35px -35px 15px -35px; border-radius: 0 0 10px 10px;">
            <h3 style="color: white; margin: 0; font-size: 1.1rem;">⚖️ IA Juridique Azure</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Statut des services
        st.markdown("#### 🔌 Services Azure")
        
        # Blob Storage
        blob_status = st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.is_connected()
        st.markdown(f"{'✅' if blob_status else '❌'} Blob Storage")
        
        # Search
        if st.session_state.azure_search_enabled:
            search_status = st.session_state.azure_search_manager and st.session_state.azure_search_manager.is_connected()
            st.markdown(f"{'✅' if search_status else '⚠️'} Search")
        
        # OpenAI
        if st.session_state.azure_openai_enabled:
            openai_status = st.session_state.azure_openai_manager and st.session_state.azure_openai_manager.is_connected()
            st.markdown(f"{'✅' if openai_status else '⚠️'} OpenAI")
        
        # Documents sélectionnés
        if st.session_state.selected_documents:
            st.markdown("---")
            st.markdown(f"#### 📄 {len(st.session_state.selected_documents)} documents")
            
            if st.button("🗑️ Tout déselectionner"):
                st.session_state.selected_documents = []
                st.rerun()
        
        # Navigation
        st.markdown("---")
        st.markdown("#### 📊 Navigation")
        
        nav_items = [
            ("🏠 Accueil", "dashboard"),
            ("📁 Documents", "documents"),
            ("🔍 Recherche", "search"),
            ("⚙️ Configuration", "config")
        ]
        
        for label, view in nav_items:
            if st.button(label, use_container_width=True):
                st.session_state.current_view = view
                st.rerun()

# ========== DASHBOARD ==========

def show_dashboard():
    """Dashboard principal"""
    st.markdown("""
    <h1 style="text-align: center;">⚖️ IA Juridique - Azure Integration</h1>
    <p style="text-align: center; color: #7f8c8d;">
        Analyse intelligente avec Azure Blob Storage, Search et OpenAI
    </p>
    """, unsafe_allow_html=True)
    
    # Statut des services
    if display_azure_services_status():
        st.markdown("---")
        
        # Sélecteur IA
        create_ai_selector()
        
        st.markdown("---")
        
        # Documents et recherche
        display_documents_with_search()
        
        # Actions sur documents sélectionnés
        if st.session_state.selected_documents:
            st.markdown("---")
            st.markdown(f"### ⚡ Actions sur {len(st.session_state.selected_documents)} document(s)")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Analyser", type="primary", use_container_width=True):
                    st.session_state.current_view = "analyze_real_documents"
                    st.rerun()
            
            with col2:
                if st.button("📊 Comparer", use_container_width=True):
                    st.info("Comparaison en développement")
            
            with col3:
                if st.button("📋 Synthétiser", use_container_width=True):
                    st.info("Synthèse en développement")

# ========== CONFIGURATION ==========

def show_config():
    """Page de configuration des services Azure"""
    st.markdown("## ⚙️ Configuration Azure")
    
    # Instructions
    with st.expander("📋 Instructions de configuration"):
        st.markdown("""
        ### Azure Blob Storage (Obligatoire)
        ```
        AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
        ```
        
        ### Azure Search (Optionnel)
        ```
        AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
        AZURE_SEARCH_KEY=your-api-key
        ```
        
        ### Azure OpenAI (Optionnel)
        ```
        AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
        AZURE_OPENAI_KEY=your-api-key
        AZURE_OPENAI_DEPLOYMENT=gpt-4
        ```
        """)
    
    # Test des connexions
    st.markdown("### 🔧 Test des connexions")
    
    if st.button("🔄 Réinitialiser toutes les connexions"):
        st.session_state.azure_initialized = False
        init_azure_services()
        st.success("✅ Services réinitialisés")
        time.sleep(1)
        st.rerun()
    
    # Détails des connexions
    st.markdown("### 📊 Détails des services")
    
    # Blob Storage
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager:
        with st.expander("Azure Blob Storage"):
            if blob_manager.is_connected():
                containers = blob_manager.list_containers()
                st.success(f"✅ Connecté - {len(containers)} conteneurs")
                for container in containers[:5]:
                    st.write(f"📁 {container}")
            else:
                st.error(f"❌ Erreur: {blob_manager.connection_error}")
    
    # Search
    if st.session_state.azure_search_enabled:
        search_manager = st.session_state.get('azure_search_manager')
        if search_manager:
            with st.expander("Azure Search"):
                if search_manager.is_connected():
                    st.success(f"✅ Connecté - Index: {search_manager.index_name}")
                else:
                    st.error(f"❌ Erreur: {search_manager.connection_error}")
    
    # OpenAI
    if st.session_state.azure_openai_enabled:
        openai_manager = st.session_state.get('azure_openai_manager')
        if openai_manager:
            with st.expander("Azure OpenAI"):
                if openai_manager.is_connected():
                    st.success(f"✅ Connecté - Déploiement: {openai_manager.deployment_name}")
                else:
                    st.error(f"❌ Erreur: {openai_manager.connection_error}")

# ========== ROUTER PRINCIPAL ==========

def main():
    """Point d'entrée principal"""
    init_session_state()
    load_custom_css()
    
    create_sidebar()
    
    # Router
    views = {
        "dashboard": show_dashboard,
        "documents": lambda: display_documents_with_search(),
        "search": lambda: search_with_azure_search() if st.session_state.azure_search_enabled else basic_search(),
        "analyze_real_documents": analyze_real_documents,
        "config": show_config
    }
    
    current_view = st.session_state.current_view
    if current_view in views:
        views[current_view]()
    else:
        show_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: #95a5a6; font-size: 0.7rem;'>
        ⚖️ IA Juridique Azure • Blob Storage + Search + OpenAI • RGPD Compliant
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()