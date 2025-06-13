"""Application IA Juridique - Version complète optimisée avec toutes les fonctionnalités"""

import streamlit as st
import streamlit.components.v1 as components
import os
import time
import logging
from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple
import uuid
import re
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="IA Juridique - Analyse Intelligente",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS PROFESSIONNEL TONS BLEUS ==========
st.markdown("""
<style>
    /* Variables de couleur - tons bleus professionnels */
    :root {
        --primary-blue: #1e3a5f;
        --secondary-blue: #2c5282;
        --light-blue: #e6f2ff;
        --accent-blue: #4299e1;
        --success-green: #48bb78;
        --warning-amber: #ed8936;
        --danger-soft: #fc8181;
        --text-primary: #2d3748;
        --text-secondary: #718096;
        --border-color: #cbd5e0;
        --bg-light: #f7fafc;
        --hover-blue: #2b6cb0;
    }
    
    /* Typography - polices plus petites */
    * { font-size: 0.875rem; }
    h1 { font-size: 1.5rem !important; color: var(--primary-blue); }
    h2 { font-size: 1.25rem !important; color: var(--primary-blue); }
    h3 { font-size: 1.1rem !important; color: var(--secondary-blue); }
    h4 { font-size: 1rem !important; color: var(--secondary-blue); }
    .stButton button { font-size: 0.875rem; }
    
    /* Layout compact */
    .block-container { 
        padding-top: 2rem; 
        max-width: 1400px;
    }
    
    /* Azure Status Cards */
    .azure-status {
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        border-left: 4px solid;
        background: var(--light-blue);
    }
    .azure-connected { 
        border-left-color: var(--success-green);
        background: #e6fffa;
    }
    .azure-optional {
        border-left-color: var(--warning-amber);
        background: #fffaf0;
    }
    .azure-error {
        border-left-color: var(--danger-soft);
        background: #fff5f5;
    }
    
    /* Search area avec détection @client */
    .search-container {
        background: var(--bg-light);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
        margin: 1rem 0;
    }
    .search-container.client-active {
        border-color: var(--accent-blue);
        background: var(--light-blue);
        box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
    }
    
    /* Document cards */
    .doc-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        transition: all 0.2s;
        cursor: pointer;
    }
    .doc-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .doc-type-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    
    /* Prompt suggestions */
    .prompt-suggestion {
        background: var(--light-blue);
        border: 1px solid var(--accent-blue);
        border-radius: 0.375rem;
        padding: 0.5rem 0.75rem;
        margin: 0.25rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .prompt-suggestion:hover {
        background: var(--accent-blue);
        color: white;
    }
    
    /* Boutons personnalisés */
    .stButton > button {
        background: white;
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: var(--light-blue);
        border-color: var(--accent-blue);
        color: var(--primary-blue);
    }
    .stButton > button[kind="primary"] {
        background: var(--accent-blue);
        border-color: var(--accent-blue);
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--hover-blue);
        border-color: var(--hover-blue);
    }
    
    /* Diagnostics */
    .diagnostic-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .diagnostic-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        padding: 1rem;
        font-size: 0.8rem;
    }
    .diagnostic-card.success {
        border-left: 4px solid var(--success-green);
    }
    .diagnostic-card.warning {
        border-left: 4px solid var(--warning-amber);
    }
    .diagnostic-card.error {
        border-left: 4px solid var(--danger-soft);
    }
    
    /* Sidebar optimisée */
    section[data-testid="stSidebar"] {
        background: var(--bg-light);
    }
    
    /* Réduction espaces */
    .stTextArea > div > div > textarea {
        font-size: 0.875rem;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== GESTIONNAIRES AZURE OPTIMISÉS ==========

class AzureBlobManager:
    """Gestionnaire Azure Blob Storage avec cache et gestion versions"""
    def __init__(self):
        self.connected = False
        self.error = None
        self.client = None
        self._containers_cache = []
        self._blobs_cache = {}
        
        try:
            conn_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if conn_string:
                from azure.storage.blob import BlobServiceClient
                self.client = BlobServiceClient.from_connection_string(conn_string)
                # Test connexion avec timeout
                try:
                    containers = list(self.client.list_containers(max_results=1))
                    self.connected = True
                    self._load_containers_cache()
                    logger.info("✅ Azure Blob connecté")
                except Exception as e:
                    self.error = f"Erreur connexion: {str(e)[:100]}"
            else:
                self.error = "AZURE_STORAGE_CONNECTION_STRING non configurée"
        except ImportError:
            self.error = "Module azure-storage-blob non installé"
        except Exception as e:
            self.error = str(e)[:100]
    
    def _load_containers_cache(self):
        """Charge la liste des conteneurs en cache"""
        if self.connected:
            try:
                self._containers_cache = [c.name for c in self.client.list_containers()]
            except:
                self._containers_cache = []
    
    def list_containers(self):
        return self._containers_cache
    
    def list_blobs_with_versions(self, container_name: str, show_all_versions: bool = False):
        """Liste les blobs avec gestion des versions Word"""
        if not self.connected:
            return []
        
        cache_key = f"{container_name}_{show_all_versions}"
        if cache_key in self._blobs_cache:
            return self._blobs_cache[cache_key]
        
        try:
            container = self.client.get_container_client(container_name)
            all_blobs = []
            
            for blob in container.list_blobs():
                all_blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None
                })
            
            # Grouper les documents Word par nom de base
            if not show_all_versions:
                word_docs = {}
                other_docs = []
                
                for blob in all_blobs:
                    if blob['name'].endswith(('.docx', '.doc')):
                        # Extraire le nom de base (sans date/version)
                        base_name = re.sub(r'[-_]\d{8}[-_]\d{6}', '', blob['name'])
                        base_name = re.sub(r'[-_]v\d+', '', base_name)
                        base_name = re.sub(r'[-_](final|draft|version\d+)', '', base_name, re.I)
                        
                        if base_name not in word_docs:
                            word_docs[base_name] = []
                        word_docs[base_name].append(blob)
                    else:
                        other_docs.append(blob)
                
                # Garder seulement la version la plus récente
                filtered_blobs = other_docs
                for base_name, versions in word_docs.items():
                    latest = max(versions, key=lambda x: x['last_modified'])
                    latest['versions_count'] = len(versions)
                    filtered_blobs.append(latest)
                
                self._blobs_cache[cache_key] = filtered_blobs
                return filtered_blobs
            else:
                self._blobs_cache[cache_key] = all_blobs
                return all_blobs
        except Exception as e:
            logger.error(f"Erreur liste blobs: {e}")
            return []
    
    def download_blob(self, container_name: str, blob_name: str):
        """Télécharge un blob"""
        if not self.connected:
            return None
        try:
            blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
            return blob_client.download_blob().readall()
        except Exception as e:
            logger.error(f"Erreur téléchargement: {e}")
            return None

class AzureSearchManager:
    """Gestionnaire Azure Cognitive Search"""
    def __init__(self):
        self.connected = False
        self.error = None
        self.search_client = None
        
        try:
            endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'documents')
            
            if endpoint and key:
                from azure.search.documents import SearchClient
                from azure.core.credentials import AzureKeyCredential
                
                self.search_client = SearchClient(
                    endpoint=endpoint,
                    index_name=index_name,
                    credential=AzureKeyCredential(key)
                )
                # Test connexion
                try:
                    self.search_client.get_document_count()
                    self.connected = True
                    logger.info("✅ Azure Search connecté")
                except:
                    self.error = "Erreur de connexion à l'index"
            else:
                self.error = "Configuration manquante (ENDPOINT/KEY)"
        except ImportError:
            self.error = "Module azure-search-documents non installé"
        except Exception as e:
            self.error = str(e)[:100]
    
    def search(self, query: str, filter_type: str = None, top: int = 10):
        """Recherche avec filtre optionnel par type"""
        if not self.connected:
            return []
        
        try:
            search_filter = None
            if filter_type:
                search_filter = f"document_type eq '{filter_type}'"
            
            results = self.search_client.search(
                search_text=query,
                filter=search_filter,
                top=top,
                include_total_count=True
            )
            
            return [
                {
                    'title': r.get('title', r.get('name', 'Sans titre')),
                    'content': r.get('content', '')[:200],
                    'type': r.get('document_type', 'autre'),
                    'score': r.get('@search.score', 0),
                    'path': r.get('path', '')
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []

class AzureOpenAIManager:
    """Gestionnaire Azure OpenAI"""
    def __init__(self):
        self.connected = False
        self.error = None
        self.client = None
        self.deployment_name = None
        
        try:
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            key = os.getenv('AZURE_OPENAI_KEY')
            self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
            
            if endpoint and key:
                from openai import AzureOpenAI
                
                self.client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=key,
                    api_version="2024-02-01"
                )
                self.connected = True
                logger.info("✅ Azure OpenAI configuré")
            else:
                self.error = "Configuration manquante (ENDPOINT/KEY)"
        except ImportError:
            self.error = "Module openai non installé"
        except Exception as e:
            self.error = str(e)[:100]
    
    def generate_prompts(self, documents: List[Dict], context: str = "") -> List[str]:
        """Génère des prompts basés sur les documents"""
        if not self.connected:
            return self._generate_default_prompts(documents)
        
        try:
            docs_summary = "\n".join([f"- {d.get('name', 'Document')}" for d in documents[:10]])
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Vous êtes un expert juridique. Générez 5 questions pertinentes pour analyser ces documents."},
                    {"role": "user", "content": f"Documents:\n{docs_summary}\n\nContexte: {context}"}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            prompts = response.choices[0].message.content.split('\n')
            return [p.strip() for p in prompts if p.strip()][:5]
        except:
            return self._generate_default_prompts(documents)
    
    def _generate_default_prompts(self, documents: List[Dict]) -> List[str]:
        """Prompts par défaut si IA non disponible"""
        prompts = [
            "Analyser les contradictions entre les documents",
            "Identifier les éléments favorables à la défense",
            "Créer une timeline des événements",
            "Synthétiser les points clés",
            "Proposer une stratégie juridique"
        ]
        
        # Ajouter des prompts spécifiques aux types de documents
        doc_types = set(d.get('type', '') for d in documents if d.get('type'))
        if 'pv' in doc_types:
            prompts.append("Analyser les incohérences dans les procès-verbaux")
        if 'expertise' in doc_types:
            prompts.append("Contester les conclusions des expertises")
        if 'contrat' in doc_types:
            prompts.append("Vérifier la validité des contrats")
        
        return prompts[:8]
    
    def categorize_document(self, filename: str, content_preview: str = "") -> str:
        """Catégorise un document avec l'IA"""
        if not self.connected:
            return self._categorize_by_rules(filename)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Catégorisez ce document juridique. Répondez uniquement par: pv, expertise, contrat, facture, courrier, procedure, ou autre."},
                    {"role": "user", "content": f"Nom: {filename}\nAperçu: {content_preview[:100]}"}
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            category = response.choices[0].message.content.strip().lower()
            valid_categories = ['pv', 'expertise', 'contrat', 'facture', 'courrier', 'procedure', 'autre']
            
            return category if category in valid_categories else 'autre'
        except:
            return self._categorize_by_rules(filename)
    
    def _categorize_by_rules(self, filename: str) -> str:
        """Catégorisation par règles si IA non disponible"""
        filename_lower = filename.lower()
        
        if any(term in filename_lower for term in ['pv', 'proces-verbal', 'audition']):
            return 'pv'
        elif any(term in filename_lower for term in ['expertise', 'expert', 'rapport']):
            return 'expertise'
        elif any(term in filename_lower for term in ['contrat', 'convention', 'accord']):
            return 'contrat'
        elif any(term in filename_lower for term in ['facture', 'devis', 'bon']):
            return 'facture'
        elif any(term in filename_lower for term in ['lettre', 'courrier', 'mail']):
            return 'courrier'
        elif any(term in filename_lower for term in ['procedure', 'jugement', 'ordonnance']):
            return 'procedure'
        else:
            return 'autre'

# ========== TYPES DE DOCUMENTS ==========

DOCUMENT_TYPES = {
    'pv': {'name': 'Procès-verbaux', 'icon': '📝', 'color': '#2c5282'},
    'expertise': {'name': 'Expertises', 'icon': '🔬', 'color': '#2d3748'},
    'contrat': {'name': 'Contrats', 'icon': '📄', 'color': '#38a169'},
    'facture': {'name': 'Factures', 'icon': '🧾', 'color': '#d69e2e'},
    'courrier': {'name': 'Correspondances', 'icon': '✉️', 'color': '#805ad5'},
    'procedure': {'name': 'Procédures', 'icon': '⚖️', 'color': '#e53e3e'},
    'autre': {'name': 'Autres', 'icon': '📁', 'color': '#718096'}
}

# ========== JAVASCRIPT POUR RECHERCHE NATURELLE ==========

SEARCH_JAVASCRIPT = """
<script>
(function() {
    // Fonction pour gérer la recherche avec @client et Entrée simple
    function setupEnhancedSearch() {
        const searchInterval = setInterval(() => {
            const textarea = document.querySelector('textarea[aria-label="search_area"]');
            if (!textarea) return;
            
            clearInterval(searchInterval);
            
            // Détection du @ et mise en évidence
            textarea.addEventListener('input', function(e) {
                const value = e.target.value;
                
                if (value.startsWith('@')) {
                    textarea.style.borderColor = '#4299e1';
                    textarea.style.borderWidth = '2px';
                    textarea.style.backgroundColor = '#e6f2ff';
                } else {
                    textarea.style.borderColor = '';
                    textarea.style.borderWidth = '';
                    textarea.style.backgroundColor = '';
                }
            });
            
            // Validation avec Entrée simple (pas Cmd+Entrée)
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    
                    // Trouver et cliquer le bouton Analyser
                    const buttons = document.querySelectorAll('button');
                    for (const button of buttons) {
                        if (button.textContent.includes('Analyser')) {
                            button.click();
                            break;
                        }
                    }
                }
            });
            
            // Focus automatique
            if (document.activeElement !== textarea) {
                textarea.focus();
            }
        }, 100);
    }
    
    // Lancer au chargement et à chaque mutation
    setupEnhancedSearch();
    
    const observer = new MutationObserver(() => {
        setupEnhancedSearch();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
</script>
"""

# ========== ÉTAT GLOBAL ==========

def init_session_state():
    """Initialisation de l'état global"""
    defaults = {
        'initialized': False,
        'selected_ais': [],
        'current_view': 'dashboard',
        'search_query': '',
        'selected_client': None,
        'selected_documents': [],
        'show_all_versions': False,
        'document_type_filter': 'tous',
        'azure_blob_manager': None,
        'azure_search_manager': None,
        'azure_openai_manager': None,
        'clients_cache': {},
        'prompts_cache': [],
        'folder_aliases': {}  # Cache des alias
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialisation des services Azure une seule fois
    if not st.session_state.initialized:
        with st.spinner("Initialisation des services..."):
            st.session_state.azure_blob_manager = AzureBlobManager()
            st.session_state.azure_search_manager = AzureSearchManager()
            st.session_state.azure_openai_manager = AzureOpenAIManager()
            # Réinitialiser les alias après connexion
            st.session_state.folder_aliases = {}
            st.session_state.initialized = True

# ========== COMPOSANTS UI ==========

def show_diagnostics():
    """Affiche les diagnostics des services"""
    st.markdown("### 🔧 Diagnostics des services")
    
    services = [
        {
            'name': 'Azure Blob Storage',
            'manager': st.session_state.azure_blob_manager,
            'required': True,
            'icon': '💾'
        },
        {
            'name': 'Azure Search',
            'manager': st.session_state.azure_search_manager,
            'required': False,
            'icon': '🔍'
        },
        {
            'name': 'Azure OpenAI',
            'manager': st.session_state.azure_openai_manager,
            'required': False,
            'icon': '🤖'
        }
    ]
    
    st.markdown('<div class="diagnostic-grid">', unsafe_allow_html=True)
    
    cols = st.columns(3)
    for idx, service in enumerate(services):
        with cols[idx]:
            manager = service['manager']
            is_connected = manager and hasattr(manager, 'connected') and manager.connected
            
            if is_connected:
                status_class = 'success'
                status_text = '✅ Connecté'
                status_color = '#48bb78'
            elif service['required']:
                status_class = 'error'
                status_text = '❌ Erreur'
                status_color = '#fc8181'
            else:
                status_class = 'warning'
                status_text = '⚠️ Optionnel'
                status_color = '#ed8936'
            
            st.markdown(f"""
            <div class="diagnostic-card {status_class}">
                <h4 style="margin: 0; color: {status_color};">{service['icon']} {service['name']}</h4>
                <p style="margin: 0.5rem 0; font-weight: 500;">{status_text}</p>
                <p style="margin: 0; font-size: 0.75rem; color: var(--text-secondary);">
                    {manager.error if manager and hasattr(manager, 'error') and manager.error else 'Fonctionnel'}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ai_selector():
    """Sélecteur d'IA avec design professionnel"""
    st.markdown("### 🤖 Sélection des IA")
    
    available_ais = {
        'GPT-3.5': {'icon': '🚀', 'desc': 'Analyse rapide', 'color': '#4299e1'},
        'GPT-4': {'icon': '🧠', 'desc': 'Analyse approfondie', 'color': '#2c5282'},
        'ChatGPT o1': {'icon': '💬', 'desc': 'Raisonnement avancé', 'color': '#10a37f'},
        'Claude': {'icon': '🎭', 'desc': 'Argumentation', 'color': '#805ad5'},
        'Gemini': {'icon': '✨', 'desc': 'Recherche exhaustive', 'color': '#38a169'},
        'Perplexity': {'icon': '🔮', 'desc': 'Recherche web temps réel', 'color': '#6366f1'},
        'Mistral': {'icon': '🌟', 'desc': 'Spécialiste français', 'color': '#d69e2e'}
    }
    
    # Ajouter Azure OpenAI si disponible
    if st.session_state.azure_openai_manager and st.session_state.azure_openai_manager.connected:
        available_ais['Azure OpenAI'] = {'icon': '☁️', 'desc': 'IA Microsoft', 'color': '#0078d4'}
    
    # Adapter le nombre de colonnes
    num_ais = len(available_ais)
    cols_per_row = 4
    rows = (num_ais + cols_per_row - 1) // cols_per_row
    
    ai_list = list(available_ais.items())
    
    for row in range(rows):
        cols = st.columns(min(cols_per_row, num_ais - row * cols_per_row))
        
        for col_idx in range(len(cols)):
            ai_idx = row * cols_per_row + col_idx
            if ai_idx < num_ais:
                ai_name, ai_info = ai_list[ai_idx]
                
                with cols[col_idx]:
                    selected = ai_name in st.session_state.selected_ais
                    
                    if st.checkbox(
                        f"{ai_info['icon']} {ai_name}",
                        key=f"ai_{ai_name}",
                        value=selected,
                        help=ai_info['desc']
                    ):
                        if ai_name not in st.session_state.selected_ais:
                            st.session_state.selected_ais.append(ai_name)
                    else:
                        if ai_name in st.session_state.selected_ais:
                            st.session_state.selected_ais.remove(ai_name)

def generate_folder_alias(folder_name: str) -> str:
    """Génère un alias court pour un dossier"""
    # Supprimer les caractères spéciaux
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', folder_name.lower())
    
    # Stratégies pour créer l'alias
    if len(clean_name) <= 3:
        return clean_name
    elif len(clean_name) <= 6:
        return clean_name[:3]
    else:
        # Prendre les premières lettres des mots principaux
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|\d+', folder_name)
        if len(words) > 1:
            return ''.join(w[0].lower() for w in words[:3])
        else:
            return clean_name[:3]

def get_folder_aliases() -> Dict[str, str]:
    """Retourne un mapping alias -> nom réel du dossier"""
    if 'folder_aliases' not in st.session_state:
        st.session_state.folder_aliases = {}
        
        if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected:
            containers = st.session_state.azure_blob_manager.list_containers()
            
            # Générer des alias uniques
            used_aliases = set()
            for container in containers:
                base_alias = generate_folder_alias(container)
                alias = base_alias
                counter = 1
                
                # S'assurer que l'alias est unique
                while alias in used_aliases:
                    alias = f"{base_alias}{counter}"
                    counter += 1
                
                used_aliases.add(alias)
                st.session_state.folder_aliases[alias] = container
    
    return st.session_state.folder_aliases

def extract_client_and_query(query: str) -> Tuple[Optional[str], str]:
    """Extrait le client et la requête depuis la recherche en utilisant les alias"""
    if query.startswith('@'):
        match = re.match(r'@(\w+)\s*,?\s*(.*)', query)
        if match:
            alias = match.group(1).lower()
            rest = match.group(2)
            
            # Chercher dans les alias
            aliases = get_folder_aliases()
            if alias in aliases:
                return aliases[alias], rest
            
            # Chercher correspondance partielle
            for a, folder in aliases.items():
                if a.startswith(alias) or alias in a:
                    return folder, rest
            
            # Si pas trouvé dans les alias, chercher dans les noms réels
            if st.session_state.azure_blob_manager:
                containers = st.session_state.azure_blob_manager.list_containers()
                for container in containers:
                    if container.lower().startswith(alias) or alias in container.lower():
                        return container, rest
    
    return None, query

def show_search_interface():
    """Interface de recherche avec support @client et prompts IA"""
    st.markdown("### 🔍 Recherche intelligente")
    
    # Détection du client actuel
    query = st.session_state.get('search_query', '')
    client, clean_query = extract_client_and_query(query)
    
    # Container avec style adaptatif
    container_class = "search-container client-active" if client else "search-container"
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    # Si client détecté, afficher ses infos
    if client and st.session_state.azure_blob_manager and client in st.session_state.azure_blob_manager.list_containers():
        st.info(f"📁 Analyse du dossier : **{client}**")
        
        # Toggle versions
        col1, col2 = st.columns([3, 1])
        with col2:
            st.session_state.show_all_versions = st.checkbox(
                "Toutes versions",
                key="version_toggle",
                help="Afficher toutes les versions des documents Word"
            )
        
        # Afficher les documents du client
        with st.expander("📄 Documents disponibles", expanded=True):
            display_client_documents(client)
    
    # Afficher les alias disponibles
    aliases = get_folder_aliases()
    if aliases and not client:
        alias_examples = []
        for alias, folder in list(aliases.items())[:5]:
            alias_examples.append(f"@{alias} ({folder})")
        alias_text = " • ".join(alias_examples)
        st.caption(f"💡 Dossiers disponibles : {alias_text}...")
    
    # Zone de recherche - 3 lignes
    search_text = st.text_area(
        "search_area",
        value=query,
        placeholder=(
            "Tapez @ suivi de l'indicateur du dossier, puis votre demande\n"
            "Exemple : @mar, analyser les contradictions dans les PV\n"
            "Appuyez sur Entrée pour lancer l'analyse"
        ),
        height=100,  # 3 lignes
        key="search_query",
        label_visibility="hidden"
    )
    
    # Boutons d'action
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.session_state.azure_search_manager and st.session_state.azure_search_manager.connected:
            if st.button("🔍 Rechercher", use_container_width=True):
                perform_azure_search(clean_query if client else search_text)
    
    with col3:
        if st.button("🤖 Analyser", type="primary", use_container_width=True):
            if search_text and st.session_state.selected_ais:
                process_analysis(search_text)
            else:
                st.warning("Sélectionnez des IA et entrez une requête")
    
    # Prompts suggérés basés sur les documents
    if client and st.session_state.azure_openai_manager:
        show_ai_prompts(client)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_client_documents(client: str):
    """Affiche les documents d'un client avec tri par type"""
    blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(
        client, 
        st.session_state.show_all_versions
    )
    
    if not blobs:
        st.warning("Aucun document trouvé")
        return
    
    # Catégoriser les documents
    categorized = {}
    openai_manager = st.session_state.azure_openai_manager
    
    for blob in blobs:
        # Utiliser l'IA pour catégoriser si disponible
        doc_type = openai_manager.categorize_document(blob['name']) if openai_manager else 'autre'
        
        if doc_type not in categorized:
            categorized[doc_type] = []
        categorized[doc_type].append(blob)
    
    # Filtre par type
    st.markdown("**Filtrer par type :**")
    type_options = ['tous'] + list(categorized.keys())
    selected_type = st.selectbox(
        "Type de document",
        options=type_options,
        format_func=lambda x: DOCUMENT_TYPES.get(x, {'name': 'Tous'})['name'],
        key="doc_type_filter",
        label_visibility="collapsed"
    )
    
    # Affichage des documents filtrés
    total_shown = 0
    for doc_type, docs in categorized.items():
        if selected_type != 'tous' and doc_type != selected_type:
            continue
        
        if docs:
            type_info = DOCUMENT_TYPES.get(doc_type, {'name': 'Autres', 'icon': '📁', 'color': '#718096'})
            st.markdown(f"**{type_info['icon']} {type_info['name']} ({len(docs)})**")
            
            for doc in docs[:10]:  # Limiter l'affichage
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Badge de version si applicable
                    version_badge = ""
                    if doc.get('versions_count', 0) > 1:
                        version_badge = f"<span style='color: var(--warning-amber); font-size: 0.7rem;'> ({doc['versions_count']} versions)</span>"
                    
                    st.markdown(f"""
                    <div class="doc-card">
                        <span class="doc-type-badge" style="background: {type_info['color']}20; color: {type_info['color']};">
                            {type_info['icon']}
                        </span>
                        {doc['name']}{version_badge}
                        <span style="float: right; color: var(--text-secondary); font-size: 0.7rem;">
                            {doc['size'] // 1024} KB
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.checkbox("Sélectionner", key=f"sel_{doc['name']}", label_visibility="hidden"):
                        if doc['name'] not in st.session_state.selected_documents:
                            st.session_state.selected_documents.append(doc['name'])
                    else:
                        if doc['name'] in st.session_state.selected_documents:
                            st.session_state.selected_documents.remove(doc['name'])
                
                total_shown += 1
    
    if total_shown == 0:
        st.info("Aucun document ne correspond au filtre")

def show_ai_prompts(client: str):
    """Affiche les prompts générés par l'IA"""
    st.markdown("**💡 Suggestions d'analyse (générées par IA) :**")
    
    # Récupérer les documents du client
    blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(client, False)
    
    # Trouver l'alias du client
    aliases = get_folder_aliases()
    client_alias = None
    for alias, folder in aliases.items():
        if folder == client:
            client_alias = alias
            break
    
    # Générer ou récupérer les prompts
    cache_key = f"prompts_{client}_{len(blobs)}"
    if cache_key not in st.session_state.prompts_cache:
        prompts = st.session_state.azure_openai_manager.generate_prompts(blobs, client)
        st.session_state.prompts_cache = prompts
    else:
        prompts = st.session_state.prompts_cache
    
    # Afficher les prompts
    cols = st.columns(2)
    for idx, prompt in enumerate(prompts[:6]):
        with cols[idx % 2]:
            if st.button(
                f"→ {prompt}",
                key=f"prompt_{idx}",
                use_container_width=True,
                help="Cliquez pour utiliser ce prompt"
            ):
                # Utiliser l'alias si disponible
                prefix = f"@{client_alias}" if client_alias else f"@{client}"
                st.session_state.search_query = f"{prefix}, {prompt}"
                st.rerun()

def perform_azure_search(query: str):
    """Effectue une recherche Azure Search"""
    with st.spinner("Recherche en cours..."):
        results = st.session_state.azure_search_manager.search(
            query,
            filter_type=st.session_state.get('doc_type_filter') if st.session_state.get('doc_type_filter') != 'tous' else None
        )
        
        if results:
            st.success(f"✅ {len(results)} résultats trouvés")
            
            for result in results[:5]:
                st.markdown(f"""
                <div class="doc-card">
                    <strong>{result['title']}</strong> (Score: {result['score']:.2f})<br>
                    <span style="color: var(--text-secondary); font-size: 0.8rem;">
                        {result['content']}...
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Aucun résultat trouvé")

def process_analysis(query: str):
    """Traite l'analyse avec les IA sélectionnées"""
    with st.spinner(f"Analyse par {len(st.session_state.selected_ais)} IA..."):
        # Simulation de traitement
        progress = st.progress(0)
        for i in range(100):
            progress.progress(i + 1)
            time.sleep(0.01)
    
    st.success("✅ Analyse terminée")
    
    # Résultats
    client, clean_query = extract_client_and_query(query)
    
    # Trouver l'alias utilisé
    alias_used = None
    if client and query.startswith('@'):
        match = re.match(r'@(\w+)', query)
        if match:
            alias_used = match.group(1)
    
    if 'Azure OpenAI' in st.session_state.selected_ais and st.session_state.azure_openai_manager.connected:
        st.info("🤖 Analyse réelle avec Azure OpenAI disponible")
    else:
        st.markdown(f"""
        <div class="diagnostic-card success">
            <h4>📊 Résultats de l'analyse</h4>
            <p><strong>Dossier :</strong> {f'@{alias_used} ({client})' if alias_used else client or 'Général'}</p>
            <p><strong>Requête :</strong> {clean_query}</p>
            <p><strong>IA utilisées :</strong> {', '.join(st.session_state.selected_ais)}</p>
            <hr>
            <p style="font-size: 0.8rem;">
                Pour une analyse réelle, configurez les API des IA sélectionnées.
            </p>
        </div>
        """, unsafe_allow_html=True)

def show_sidebar():
    """Sidebar avec navigation et infos"""
    with st.sidebar:
        st.markdown("## ⚖️ IA Juridique")
        
        # Statut rapide
        blob_ok = st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected
        search_ok = st.session_state.azure_search_manager and st.session_state.azure_search_manager.connected
        ai_ok = st.session_state.azure_openai_manager and st.session_state.azure_openai_manager.connected
        
        status_icons = []
        if blob_ok:
            status_icons.append("💾✅")
        if search_ok:
            status_icons.append("🔍✅")
        if ai_ok:
            status_icons.append("🤖✅")
        
        if status_icons:
            st.success(" ".join(status_icons))
        
        # Navigation
        st.markdown("### Navigation")
        
        menu = [
            ("🏠 Tableau de bord", "dashboard"),
            ("🔍 Recherche avancée", "search"),
            ("📊 Analyses", "analyses"),
            ("⚙️ Configuration", "config"),
            ("❓ Aide", "help")
        ]
        
        for label, view in menu:
            if st.button(
                label,
                key=f"nav_{view}",
                use_container_width=True,
                type="primary" if st.session_state.current_view == view else "secondary"
            ):
                st.session_state.current_view = view
                st.rerun()
        
        # Dossiers disponibles avec alias
        if blob_ok:
            st.markdown("---")
            st.markdown("### 📁 Dossiers")
            
            aliases = get_folder_aliases()
            containers = st.session_state.azure_blob_manager.list_containers()
            
            # Afficher avec alias
            for container in containers[:10]:
                # Trouver l'alias correspondant
                alias = None
                for a, c in aliases.items():
                    if c == container:
                        alias = a
                        break
                
                display_name = f"@{alias} - {container}" if alias else f"📂 {container}"
                
                if st.button(
                    display_name,
                    key=f"folder_{container}",
                    use_container_width=True
                ):
                    st.session_state.search_query = f"@{alias}, " if alias else f"@{container}, "
                    st.session_state.current_view = "dashboard"
                    st.rerun()
        
        # IA actives
        if st.session_state.selected_ais:
            st.markdown("---")
            st.markdown("### 🤖 IA actives")
            for ai in st.session_state.selected_ais:
                st.markdown(f"• {ai}")

# ========== VUES PRINCIPALES ==========

def show_dashboard():
    """Tableau de bord principal"""
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# ⚖️ IA Juridique")
        st.markdown("*Analyse intelligente multi-IA de documents juridiques*")
    
    # Diagnostics
    show_diagnostics()
    
    # Sélection IA
    st.markdown("---")
    show_ai_selector()
    
    # Interface de recherche
    st.markdown("---")
    show_search_interface()
    
    # Actions rapides si des documents sont sélectionnés
    if st.session_state.selected_documents:
        st.markdown("### ⚡ Actions sur documents sélectionnés")
        
        cols = st.columns(4)
        actions = [
            ("🔍 Contradictions", "analyser les contradictions"),
            ("📊 Timeline", "créer une timeline"),
            ("✅ Points favorables", "identifier les points favorables"),
            ("📑 Synthèse", "synthétiser les documents")
        ]
        
        for idx, (label, action) in enumerate(actions):
            with cols[idx]:
                if st.button(label, key=f"quick_{idx}", use_container_width=True):
                    docs = ", ".join(st.session_state.selected_documents[:3])
                    st.session_state.search_query = f"{action} dans {docs}"
                    process_analysis(st.session_state.search_query)

def show_config():
    """Page de configuration détaillée"""
    st.markdown("# ⚙️ Configuration")
    
    # Diagnostics détaillés
    show_diagnostics()
    
    st.markdown("---")
    
    # Instructions par service
    tabs = st.tabs(["💾 Blob Storage", "🔍 Search", "🤖 OpenAI"])
    
    with tabs[0]:
        st.markdown("""
        ### Configuration Azure Blob Storage (Obligatoire)
        
        1. Créez un compte de stockage Azure
        2. Récupérez la chaîne de connexion
        3. Ajoutez dans les secrets Hugging Face :
        
        ```
        AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=votrecompte;AccountKey=votrecle;EndpointSuffix=core.windows.net
        ```
        """)
        
        if st.button("🔄 Tester la connexion Blob"):
            st.session_state.azure_blob_manager = AzureBlobManager()
            st.rerun()
    
    with tabs[1]:
        st.markdown("""
        ### Configuration Azure Search (Optionnel)
        
        1. Créez un service Azure Cognitive Search
        2. Créez un index pour vos documents
        3. Ajoutez dans les secrets :
        
        ```
        AZURE_SEARCH_ENDPOINT=https://votre-search.search.windows.net
        AZURE_SEARCH_KEY=votre-cle-api
        AZURE_SEARCH_INDEX=nom-de-votre-index
        ```
        """)
    
    with tabs[2]:
        st.markdown("""
        ### Configuration Azure OpenAI (Optionnel)
        
        1. Déployez un modèle dans Azure OpenAI
        2. Récupérez l'endpoint et la clé
        3. Ajoutez dans les secrets :
        
        ```
        AZURE_OPENAI_ENDPOINT=https://votre-openai.openai.azure.com/
        AZURE_OPENAI_KEY=votre-cle-api
        AZURE_OPENAI_DEPLOYMENT=nom-du-deploiement
        ```
        """)

def show_help():
    """Page d'aide"""
    st.markdown("# ❓ Aide")
    
    st.markdown("""
    ### 🚀 Utilisation de la recherche @indicateur
    
    1. **Tapez @** suivi de l'indicateur du dossier (3-4 lettres)
    2. **Ajoutez une virgule** puis votre requête
    3. **Appuyez sur Entrée** pour lancer l'analyse
    
    **Exemple :** `@mar, analyser les contradictions dans les PV`
    
    Les indicateurs sont générés automatiquement :
    - Noms courts : les 3 premières lettres
    - Noms longs : initiales des mots principaux
    - Les indicateurs sont affichés dans la sidebar
    
    ### 🤖 IA disponibles
    
    - **GPT-3.5** : Analyse rapide et efficace
    - **GPT-4** : Analyse approfondie et nuancée
    - **ChatGPT o1** : Raisonnement complexe et structuré
    - **Claude** : Argumentation juridique détaillée
    - **Gemini** : Recherche exhaustive multi-sources
    - **Perplexity** : Recherche web en temps réel
    - **Mistral** : Expertise en droit français
    - **Azure OpenAI** : IA sécurisée Microsoft (si configurée)
    
    ### 🤖 Génération de prompts par IA
    
    - L'IA analyse vos documents et suggère des analyses pertinentes
    - Cliquez sur une suggestion pour l'utiliser
    - Les prompts s'adaptent aux types de documents présents
    
    ### 📄 Gestion des versions
    
    - Par défaut, seule la dernière version des documents Word est affichée
    - Activez "Toutes versions" pour voir l'historique complet
    - Les documents sont groupés intelligemment par nom de base
    
    ### 🎨 Interface optimisée
    
    - Design professionnel en tons bleus
    - Polices réduites pour plus d'information
    - Validation rapide avec Entrée (pas Cmd+Entrée)
    - Zone de recherche sur 3 lignes pour plus de confort
    """)
    
    # Afficher la table des alias si connecté
    if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected:
        aliases = get_folder_aliases()
        if aliases:
            st.markdown("### 📁 Table des indicateurs de dossiers")
            
            # Créer un tableau des alias
            alias_data = []
            for alias, folder in sorted(aliases.items()):
                alias_data.append({
                    "Indicateur": f"@{alias}",
                    "Dossier": folder
                })
            
            # Afficher en colonnes pour économiser l'espace
            cols = st.columns(2)
            half = len(alias_data) // 2
            
            with cols[0]:
                for item in alias_data[:half]:
                    st.markdown(f"**{item['Indicateur']}** → {item['Dossier']}")
            
            with cols[1]:
                for item in alias_data[half:]:
                    st.markdown(f"**{item['Indicateur']}** → {item['Dossier']}")

# ========== FONCTION PRINCIPALE ==========

def main():
    """Point d'entrée principal"""
    # Initialisation
    init_session_state()
    
    # Injection du JavaScript pour la recherche
    components.html(SEARCH_JAVASCRIPT, height=0)
    
    # Sidebar
    show_sidebar()
    
    # Router
    views = {
        'dashboard': show_dashboard,
        'search': show_dashboard,  # Même vue pour l'instant
        'analyses': lambda: st.info("📊 Module d'analyses en développement"),
        'config': show_config,
        'help': show_help
    }
    
    current_view = st.session_state.get('current_view', 'dashboard')
    if current_view in views:
        views[current_view]()
    else:
        show_dashboard()
    
    # Footer discret
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: var(--text-secondary); font-size: 0.7rem;'>
        IA Juridique v3.0 • Analyse intelligente avec IA • Azure Integration
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()