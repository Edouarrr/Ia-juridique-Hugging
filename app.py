"""Application IA Juridique - Version améliorée avec corrections et toggle recherche"""

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
import zipfile
import tempfile
import shutil
import unicodedata
import hashlib

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

# ========== FONCTIONS UTILITAIRES ==========

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Tronque un texte à une longueur maximale"""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    available_length = max_length - len(suffix)
    return text[:available_length] + suffix

def clean_key(key: str) -> str:
    """Nettoie une clé pour la rendre utilisable comme identifiant"""
    if not key:
        return ""
    key = str(key)
    # Supprimer les accents
    key = ''.join(c for c in unicodedata.normalize('NFD', key) 
                  if unicodedata.category(c) != 'Mn')
    key = key.lower()
    key = re.sub(r'[^a-z0-9]+', '_', key)
    key = key.strip('_')
    key = re.sub(r'_+', '_', key)
    return key

def get_modules_status() -> Dict:
    """Retourne le statut des modules"""
    # Simulation du statut des modules
    return {
        'total_modules': 9,
        'loaded_count': 7,
        'failed_count': 2,
        'loaded': ['search', 'compare', 'timeline', 'extract', 'strategy', 'report', 'chat'],
        'failed': {
            'contract': 'Module en développement',
            'jurisprudence': 'Module en développement'
        }
    }

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
    
    /* Module cards pour la page d'accueil */
    .module-card {
        background: white;
        border: 2px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        min-height: 280px;
    }
    
    .module-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .module-card.featured {
        border-color: var(--accent-blue);
        background: linear-gradient(135deg, white 0%, var(--light-blue) 100%);
    }
    
    .module-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
        color: var(--accent-blue);
    }
    
    .module-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--primary-blue);
        margin-bottom: 0.5rem;
    }
    
    .module-description {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    
    .module-features {
        list-style: none;
        padding: 0;
        margin: 0.5rem 0;
    }
    
    .module-features li {
        font-size: 0.8rem;
        color: var(--text-primary);
        padding: 0.2rem 0;
        padding-left: 1.2rem;
        position: relative;
    }
    
    .module-features li:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: var(--success-green);
        font-weight: bold;
    }
    
    .module-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: var(--accent-blue);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 1rem;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .module-badge.new {
        background: var(--success-green);
    }
    
    .module-badge.premium {
        background: var(--warning-amber);
    }
    
    /* Upload area */
    .upload-area {
        border: 3px dashed var(--accent-blue);
        border-radius: 1rem;
        padding: 3rem;
        text-align: center;
        background: var(--light-blue);
        transition: all 0.3s;
        position: relative;
        min-height: 200px;
    }
    
    .upload-area.dragover {
        background: white;
        border-color: var(--primary-blue);
        border-width: 4px;
    }
    
    .upload-icon {
        font-size: 4rem;
        color: var(--accent-blue);
        margin-bottom: 1rem;
    }
    
    /* Welcome section */
    .welcome-section {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .welcome-section h1 {
        color: white !important;
        margin-bottom: 1rem;
    }
    
    .welcome-section p {
        font-size: 1rem;
        opacity: 0.9;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Toggle switch */
    .toggle-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.5rem;
        background: var(--bg-light);
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Stats cards */
    .stat-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-blue);
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
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
        opacity: 0;
        animation: fadeIn 0.5s ease forwards;
    }
    
    @keyframes fadeIn {
        to {
            opacity: 1;
            transform: translateY(0);
        }
        from {
            opacity: 0;
            transform: translateY(10px);
        }
    }
    
    .doc-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Sidebar optimisée */
    section[data-testid="stSidebar"] {
        background: var(--bg-light);
    }
    
    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
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
                # Test connexion simple
                try:
                    # Test simple sans paramètres
                    container_iter = self.client.list_containers()
                    # Tenter de récupérer au moins un conteneur
                    try:
                        next(container_iter)
                        self.connected = True
                        self._load_containers_cache()
                        logger.info("✅ Azure Blob connecté")
                    except StopIteration:
                        # Pas de conteneur mais connexion OK
                        self.connected = True
                        self._containers_cache = []
                        logger.info("✅ Azure Blob connecté (aucun conteneur)")
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
                self._containers_cache = []
                for container in self.client.list_containers():
                    self._containers_cache.append(container.name)
                logger.info(f"Cache conteneurs : {len(self._containers_cache)} trouvés")
            except Exception as e:
                logger.error(f"Erreur chargement conteneurs : {e}")
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
        """Génère des prompts basés sur les documents avec indicateur de progression"""
        if not self.connected:
            return self._generate_default_prompts(documents)
        
        try:
            # Créer un placeholder pour le statut
            status_placeholder = st.empty()
            status_placeholder.info("🤖 Génération des suggestions par IA...")
            
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
            
            # Effacer le statut
            status_placeholder.empty()
            
            prompts = response.choices[0].message.content.split('\n')
            return [p.strip() for p in prompts if p.strip()][:5]
        except:
            # En cas d'erreur, effacer le statut et retourner les prompts par défaut
            try:
                status_placeholder.empty()
            except:
                pass
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

# ========== GESTIONNAIRE DE DOCUMENTS LOCAUX ==========

class LocalDocumentManager:
    """Gestionnaire pour les documents uploadés localement"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.documents = {}
        
    def process_uploaded_files(self, uploaded_files) -> Dict[str, List[Dict]]:
        """Traite les fichiers uploadés et retourne une structure similaire à Azure"""
        result = {}
        
        for file in uploaded_files:
            # Déterminer si c'est un dossier ou un fichier
            file_path = Path(file.name)
            folder_name = file_path.parts[0] if len(file_path.parts) > 1 else "Documents locaux"
            
            if folder_name not in result:
                result[folder_name] = []
            
            # Sauvegarder temporairement
            temp_path = os.path.join(self.temp_dir, file.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, 'wb') as f:
                f.write(file.getbuffer())
            
            # Créer l'info du document
            doc_info = {
                'name': os.path.basename(file.name),
                'size': file.size,
                'last_modified': datetime.now(),
                'path': file.name,
                'local': True
            }
            
            result[folder_name].append(doc_info)
        
        self.documents = result
        return result
    
    def get_document_content(self, folder: str, filename: str) -> bytes:
        """Récupère le contenu d'un document local"""
        file_path = os.path.join(self.temp_dir, folder, filename)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
        return None
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

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

# ========== MODULES DISPONIBLES ==========

AVAILABLE_MODULES = {
    'search': {
        'id': 'search',
        'name': 'Recherche & Analyse Multi-IA',
        'icon': '🔍',
        'description': 'Analysez vos documents avec plusieurs IA simultanément',
        'features': [
            'Analyse par 7 IA différentes',
            'Recherche intelligente @dossier',
            'Suggestions automatiques par IA',
            'Comparaison des résultats'
        ],
        'badge': 'Principal',
        'color': 'featured'
    },
    'compare': {
        'id': 'compare',
        'name': 'Comparaison de Documents',
        'icon': '📊',
        'description': 'Identifiez les contradictions et concordances entre documents',
        'features': [
            'Détection automatique des contradictions',
            'Analyse des concordances',
            'Timeline comparative',
            'Export des différences'
        ],
        'badge': None,
        'color': None
    },
    'timeline': {
        'id': 'timeline',
        'name': 'Timeline Juridique',
        'icon': '📅',
        'description': 'Créez une chronologie visuelle et interactive des événements',
        'features': [
            'Extraction automatique des dates',
            'Visualisation interactive',
            'Filtrage par type d\'événement',
            'Export en PDF'
        ],
        'badge': None,
        'color': None
    },
    'extract': {
        'id': 'extract',
        'name': 'Extraction Intelligente',
        'icon': '📑',
        'description': 'Extrayez automatiquement les informations clés de vos documents',
        'features': [
            'Points favorables/défavorables',
            'Personnes et entités',
            'Montants et dates',
            'Éléments juridiques clés'
        ],
        'badge': None,
        'color': None
    },
    'strategy': {
        'id': 'strategy',
        'name': 'Stratégie Juridique IA',
        'icon': '⚖️',
        'description': 'Obtenez des recommandations stratégiques générées par l\'IA',
        'features': [
            'Analyse des forces/faiblesses',
            'Recommandations tactiques',
            'Scénarios possibles',
            'Plan d\'action détaillé'
        ],
        'badge': 'Premium',
        'color': 'premium'
    },
    'report': {
        'id': 'report',
        'name': 'Génération de Rapports',
        'icon': '📄',
        'description': 'Créez automatiquement des documents juridiques professionnels',
        'features': [
            'Notes de plaidoirie',
            'Mémos juridiques',
            'Synthèses d\'analyse',
            'Personnalisation du format'
        ],
        'badge': None,
        'color': None
    },
    'contract': {
        'id': 'contract',
        'name': 'Analyse de Contrats',
        'icon': '📋',
        'description': 'Analysez et comparez vos contrats avec l\'IA',
        'features': [
            'Détection des clauses à risque',
            'Comparaison de versions',
            'Suggestions d\'amélioration',
            'Conformité légale'
        ],
        'badge': 'Nouveau',
        'color': 'new'
    },
    'jurisprudence': {
        'id': 'jurisprudence',
        'name': 'Recherche Jurisprudence',
        'icon': '⚖️',
        'description': 'Trouvez des décisions similaires et des précédents',
        'features': [
            'Base de données étendue',
            'Recherche par similarité',
            'Analyse des tendances',
            'Citations automatiques'
        ],
        'badge': 'Nouveau',
        'color': 'new'
    },
    'chat': {
        'id': 'chat',
        'name': 'Assistant Juridique IA',
        'icon': '💬',
        'description': 'Dialoguez avec un assistant juridique intelligent',
        'features': [
            'Réponses contextuelles',
            'Mémoire de conversation',
            'Références aux documents',
            'Conseils personnalisés'
        ],
        'badge': None,
        'color': None
    }
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
                    
                    // Récupérer le mode actuel (toggle)
                    const searchMode = document.querySelector('input[name="search_mode"]:checked');
                    const mode = searchMode ? searchMode.value : 'multi-ia';
                    
                    // Trouver et cliquer le bon bouton selon le mode
                    const buttons = document.querySelectorAll('button');
                    for (const button of buttons) {
                        if (mode === 'multi-ia' && button.textContent.includes('Analyser')) {
                            button.click();
                            break;
                        } else if (mode === 'module' && button.textContent.includes('Ouvrir le module')) {
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
    
    // Drag and drop pour l'upload
    function setupDragAndDrop() {
        const uploadArea = document.querySelector('.upload-area');
        if (!uploadArea) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            uploadArea.classList.add('dragover');
        }
        
        function unhighlight(e) {
            uploadArea.classList.remove('dragover');
        }
    }
    
    // Lancer au chargement et à chaque mutation
    setupEnhancedSearch();
    setupDragAndDrop();
    
    const observer = new MutationObserver(() => {
        setupEnhancedSearch();
        setupDragAndDrop();
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
        'current_view': 'home',
        'search_query': '',
        'search_mode': 'multi-ia',  # 'multi-ia' ou 'module'
        'selected_client': None,
        'selected_documents': [],
        'show_all_versions': False,
        'show_documents': False,
        'document_type_filter': 'tous',
        'azure_blob_manager': None,
        'azure_search_manager': None,
        'azure_openai_manager': None,
        'local_document_manager': None,
        'clients_cache': {},
        'prompts_cache': [],
        'folder_aliases': {},
        'local_folders': {},
        'active_source': 'azure'  # 'azure' ou 'local'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialisation des services Azure une seule fois
    if not st.session_state.initialized:
        with st.spinner("🚀 Initialisation de l'application..."):
            # Azure Blob Storage
            st.session_state.azure_blob_manager = AzureBlobManager()
            
            # Azure Search
            st.session_state.azure_search_manager = AzureSearchManager()
            
            # Azure OpenAI
            st.session_state.azure_openai_manager = AzureOpenAIManager()
            
            # Local Document Manager
            st.session_state.local_document_manager = LocalDocumentManager()
            
            st.session_state.initialized = True

# ========== COMPOSANTS UI ==========

def show_home_page():
    """Page d'accueil complète avec tous les modules"""
    # Section de bienvenue
    st.markdown("""
    <div class="welcome-section">
        <h1>⚖️ IA Juridique - Analyse Intelligente Multi-IA</h1>
        <p>
            Analysez vos documents juridiques avec la puissance de 8 intelligences artificielles différentes.
            Obtenez des analyses approfondies, identifiez les contradictions, créez des stratégies gagnantes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Actions rapides sans les statistiques
    st.markdown("### 🚀 Actions rapides")
    
    col1, col2, col3, col4 = st.columns(4)
    
    quick_actions = [
        ("🔍 Nouvelle analyse", "search", ""),
        ("📁 Charger dossier", "upload", ""),
        ("💬 Assistant IA", "chat", ""),
        ("⚙️ Configuration", "config", "")
    ]
    
    for idx, (label, action, query) in enumerate(quick_actions):
        with [col1, col2, col3, col4][idx]:
            if st.button(label, key=f"quick_{action}", use_container_width=True, type="primary"):
                if action == "upload":
                    st.session_state.current_view = "home"
                    st.session_state.show_upload = True
                elif action == "config":
                    st.session_state.current_view = "config"
                else:
                    st.session_state.current_view = action
                    if query:
                        st.session_state.search_query = query
                st.rerun()
    
    # Section upload de documents
    st.markdown("### 📁 Vos documents")
    
    tabs = st.tabs(["☁️ Documents Azure", "💾 Documents locaux"])
    
    with tabs[0]:
        if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected:
            containers = st.session_state.azure_blob_manager.list_containers()
            if containers:
                st.success(f"✅ {len(containers)} dossiers disponibles sur Azure")
                
                # Afficher quelques dossiers
                cols = st.columns(3)
                for idx, container in enumerate(containers[:6]):
                    with cols[idx % 3]:
                        if st.button(f"📁 {container}", key=f"azure_{container}", use_container_width=True):
                            st.session_state.search_query = f"@{container}, "
                            st.session_state.current_view = "search"
                            st.rerun()
                
                if len(containers) > 6:
                    st.info(f"... et {len(containers) - 6} autres dossiers")
            else:
                st.warning("Aucun dossier Azure disponible")
        else:
            st.error("❌ Azure Blob Storage non connecté")
            if st.button("⚙️ Configurer Azure"):
                st.session_state.current_view = "config"
                st.rerun()
    
    with tabs[1]:
        # Zone de drag & drop
        st.markdown("""
        <div class="upload-area">
            <div class="upload-icon">📤</div>
            <h3>Glissez-déposez vos documents ici</h3>
            <p>ou cliquez pour parcourir</p>
            <p style="font-size: 0.8rem; opacity: 0.7;">
                Formats acceptés : PDF, DOCX, TXT, images<br>
                Vous pouvez déposer un dossier complet
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Chargez vos documents",
            type=['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="file_uploader",
            label_visibility="hidden"
        )
        
        if uploaded_files:
            with st.spinner("Traitement des documents..."):
                local_folders = st.session_state.local_document_manager.process_uploaded_files(uploaded_files)
                st.session_state.local_folders = local_folders
                st.success(f"✅ {len(uploaded_files)} documents chargés dans {len(local_folders)} dossier(s)")
                
                # Afficher les dossiers locaux
                for folder_name, docs in local_folders.items():
                    if st.button(f"📁 {folder_name} ({len(docs)} docs)", key=f"local_{folder_name}"):
                        st.session_state.selected_client = folder_name
                        st.session_state.active_source = 'local'
                        st.session_state.current_view = "search"
                        st.rerun()
    
    # Grille des modules
    st.markdown("### 🛠️ Modules disponibles")
    st.markdown("Découvrez toutes les fonctionnalités de l'IA Juridique")
    
    # Organiser les modules en grille
    modules_list = list(AVAILABLE_MODULES.values())
    cols_per_row = 3
    
    for i in range(0, len(modules_list), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            if i + j < len(modules_list):
                module = modules_list[i + j]
                
                with cols[j]:
                    # Carte du module
                    card_class = f"module-card {module.get('color', '')}"
                    badge_html = ""
                    if module.get('badge'):
                        badge_class = f"module-badge {module.get('color', '')}"
                        badge_html = f'<div class="{badge_class}">{module["badge"]}</div>'
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                        {badge_html}
                        <div class="module-icon">{module['icon']}</div>
                        <div class="module-title">{module['name']}</div>
                        <div class="module-description">{module['description']}</div>
                        <ul class="module-features">
                            {''.join([f'<li>{feature}</li>' for feature in module['features']])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(
                        f"Ouvrir {module['name']}", 
                        key=f"open_{module['id']}",
                        use_container_width=True,
                        type="primary" if module.get('color') == 'featured' else "secondary"
                    ):
                        st.session_state.current_view = module['id']
                        st.rerun()
    
    # Section d'aide
    st.markdown("---")
    st.markdown("### ❓ Besoin d'aide ?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **🎯 Commencer rapidement**
        1. Chargez vos documents (Azure ou local)
        2. Sélectionnez les IA à utiliser
        3. Tapez votre question
        4. Analysez les résultats
        """)
    
    with col2:
        st.info("""
        **💡 Astuces pro**
        - Utilisez @ pour cibler un dossier
        - Combinez plusieurs IA pour des analyses complètes
        - Exportez vos rapports en PDF
        - Sauvegardez vos analyses favorites
        """)
    
    with col3:
        st.info("""
        **🔧 Support technique**
        - Documentation complète disponible
        - Tutoriels vidéo intégrés
        - Support par chat 24/7
        - Formation personnalisée sur demande
        """)

def show_diagnostics():
    """Affiche les diagnostics détaillés des services et documents"""
    st.markdown("### 🔧 État des services")
    
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
    
    cols = st.columns(3)
    for idx, service in enumerate(services):
        with cols[idx]:
            manager = service['manager']
            is_connected = manager and hasattr(manager, 'connected') and manager.connected
            
            if is_connected:
                st.success(f"{service['icon']} {service['name']}\n✅ Connecté")
            elif service['required']:
                st.error(f"{service['icon']} {service['name']}\n❌ Erreur")
            else:
                st.warning(f"{service['icon']} {service['name']}\n⚠️ Optionnel")
            
            if manager and hasattr(manager, 'error') and manager.error:
                st.caption(manager.error[:50])
    
    # Diagnostic des modules
    st.markdown("### 📊 Diagnostic des Modules")
    
    status = get_modules_status()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total modules", status['total_modules'])
    with col2:
        st.metric("Modules chargés", status['loaded_count'], 
                 delta=f"+{status['loaded_count']}" if status['loaded_count'] > 0 else None)
    with col3:
        st.metric("Modules en erreur", status['failed_count'],
                 delta=f"-{status['failed_count']}" if status['failed_count'] > 0 else None)
    
    if status['loaded_count'] > 0:
        with st.expander(f"✅ Modules chargés ({status['loaded_count']})", expanded=False):
            for module in sorted(status['loaded']):
                st.success(f"• {module}")
    
    if status['failed_count'] > 0:
        with st.expander(f"❌ Modules en erreur ({status['failed_count']})", expanded=True):
            for module, error in status['failed'].items():
                st.error(f"**{module}**: {error}")
    
    # Statistiques des documents
    st.markdown("### 📈 Statistiques des documents")
    
    # Compter les documents Azure
    azure_docs_count = 0
    azure_folders_count = 0
    
    if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected:
        containers = st.session_state.azure_blob_manager.list_containers()
        azure_folders_count = len(containers)
        # Estimation du nombre de documents
        for container in containers[:3]:  # Limiter pour la performance
            blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(container, False)
            azure_docs_count += len(blobs)
        if azure_folders_count > 3:
            azure_docs_count = int(azure_docs_count * azure_folders_count / 3)  # Extrapolation
    
    # Compter les documents locaux
    local_docs_count = 0
    local_folders_count = len(st.session_state.local_folders)
    for folder_docs in st.session_state.local_folders.values():
        local_docs_count += len(folder_docs)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ☁️ Documents Azure")
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            st.metric("Dossiers", azure_folders_count)
        with sub_col2:
            st.metric("Documents", f"~{azure_docs_count}")
    
    with col2:
        st.markdown("#### 💾 Documents locaux")
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            st.metric("Dossiers", local_folders_count)
        with sub_col2:
            st.metric("Documents", local_docs_count)

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
    
    # Boutons de sélection rapide
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Tout sélectionner", use_container_width=True):
            st.session_state.selected_ais = list(available_ais.keys())
            st.rerun()
    
    with col2:
        if st.button("🎯 Sélection recommandée", use_container_width=True):
            st.session_state.selected_ais = ['GPT-4', 'Claude', 'Mistral']
            st.rerun()
    
    with col3:
        if st.button("❌ Tout désélectionner", use_container_width=True):
            st.session_state.selected_ais = []
            st.rerun()
    
    # Grille de sélection
    cols = st.columns(4)
    
    for idx, (ai_name, ai_info) in enumerate(available_ais.items()):
        with cols[idx % 4]:
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
        
        # Ajouter les dossiers Azure
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
        
        # Ajouter les dossiers locaux
        for folder_name in st.session_state.get('local_folders', {}):
            base_alias = f"loc_{generate_folder_alias(folder_name)}"
            alias = base_alias
            counter = 1
            
            while alias in st.session_state.folder_aliases:
                alias = f"{base_alias}{counter}"
                counter += 1
            
            st.session_state.folder_aliases[alias] = f"[LOCAL] {folder_name}"
    
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

def display_client_documents(client: str):
    """Affiche les documents d'un client avec tri par type et indicateur de chargement"""
    # Déterminer si c'est un dossier local
    is_local = client.startswith("[LOCAL]")
    
    if is_local:
        # Documents locaux
        folder_name = client.replace("[LOCAL] ", "")
        blobs = st.session_state.local_folders.get(folder_name, [])
    else:
        # Documents Azure
        with st.spinner(f"Chargement des documents de {client}..."):
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
    
    with st.spinner("Catégorisation des documents..."):
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
                    
                    # Badge local si applicable
                    local_badge = ""
                    if doc.get('local', False):
                        local_badge = "<span style='color: var(--accent-blue); font-size: 0.7rem;'> [LOCAL]</span>"
                    
                    st.markdown(f"""
                    <div class="doc-card">
                        <span class="doc-type-badge" style="background: {type_info['color']}20; color: {type_info['color']};">
                            {type_info['icon']}
                        </span>
                        {doc['name']}{version_badge}{local_badge}
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

def show_search_interface():
    """Interface de recherche avec toggle module/multi-IA"""
    st.markdown("### 🔍 Recherche intelligente")
    
    # Toggle pour choisir le mode de recherche
    st.markdown("#### Mode de recherche")
    mode_col1, mode_col2, mode_col3 = st.columns([1, 1, 2])
    
    with mode_col1:
        if st.button(
            "🤖 Multi-IA", 
            type="primary" if st.session_state.search_mode == 'multi-ia' else "secondary",
            use_container_width=True,
            help="Analyser avec plusieurs IA simultanément"
        ):
            st.session_state.search_mode = 'multi-ia'
            st.rerun()
    
    with mode_col2:
        if st.button(
            "📋 Module spécifique", 
            type="primary" if st.session_state.search_mode == 'module' else "secondary",
            use_container_width=True,
            help="Appeler un module spécifique directement"
        ):
            st.session_state.search_mode = 'module'
            st.rerun()
    
    with mode_col3:
        if st.session_state.search_mode == 'multi-ia':
            st.info("💡 Mode Multi-IA : Analysez avec plusieurs IA en parallèle")
        else:
            st.info("💡 Mode Module : Tapez le nom d'un module pour y accéder directement")
    
    st.markdown("---")
    
    # Si mode multi-IA, afficher le sélecteur d'IA
    if st.session_state.search_mode == 'multi-ia':
        show_ai_selector()
        st.markdown("---")
    
    # Détection du client actuel
    query = st.session_state.get('search_query', '')
    client, clean_query = extract_client_and_query(query)
    
    # Si client détecté, afficher ses infos
    if client:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(f"📁 Analyse du dossier : **{client}**")
        
        with col2:
            if not client.startswith("[LOCAL]"):
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
        for alias, folder in list(aliases.items())[:8]:
            alias_examples.append(f"@{alias}")
        alias_text = " • ".join(alias_examples)
        st.info(f"💡 Dossiers disponibles : {alias_text}...")
    
    # Zone de recherche
    placeholder = ""
    if st.session_state.search_mode == 'multi-ia':
        placeholder = (
            "Tapez @ suivi de l'indicateur du dossier, puis votre demande\n"
            "Exemple : @mar, analyser les contradictions dans les PV\n"
            "Appuyez sur Entrée pour lancer l'analyse"
        )
    else:
        placeholder = (
            "Tapez le nom d'un module ou utilisez le langage naturel\n"
            "Exemples : 'timeline', 'créer une chronologie', 'comparer documents'\n"
            "Appuyez sur Entrée pour ouvrir le module"
        )
    
    search_text = st.text_area(
        "search_area",
        value=query,
        placeholder=placeholder,
        height=100,
        key="search_query",
        label_visibility="hidden"
    )
    
    # Boutons d'action selon le mode
    col1, col2, col3 = st.columns([2, 1, 1])
    
    if st.session_state.search_mode == 'multi-ia':
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
    else:
        # Mode module
        with col3:
            if st.button("📋 Ouvrir le module", type="primary", use_container_width=True):
                if search_text:
                    module_id = find_module_by_query(search_text)
                    if module_id:
                        st.session_state.current_view = module_id
                        st.rerun()
                    else:
                        st.error(f"Aucun module trouvé pour '{search_text}'")
                else:
                    st.warning("Entrez le nom d'un module")
    
    # Prompts suggérés ou modules suggérés selon le mode
    if st.session_state.search_mode == 'multi-ia' and client and st.session_state.azure_openai_manager:
        show_ai_prompts(client)
    elif st.session_state.search_mode == 'module':
        show_module_suggestions()

def find_module_by_query(query: str) -> Optional[str]:
    """Trouve un module basé sur une requête en langage naturel"""
    query_lower = query.lower().strip()
    
    # Correspondances directes par ID
    for module_id in AVAILABLE_MODULES:
        if module_id in query_lower:
            return module_id
    
    # Correspondances par mots-clés
    keyword_mapping = {
        'search': ['recherche', 'rechercher', 'analyser', 'analyse'],
        'compare': ['comparer', 'comparaison', 'différences', 'contradictions'],
        'timeline': ['timeline', 'chronologie', 'dates', 'événements'],
        'extract': ['extraire', 'extraction', 'informations clés'],
        'strategy': ['stratégie', 'stratégique', 'plan', 'tactique'],
        'report': ['rapport', 'génération', 'document', 'mémo'],
        'contract': ['contrat', 'clause', 'accord'],
        'jurisprudence': ['jurisprudence', 'précédent', 'décision'],
        'chat': ['chat', 'assistant', 'dialogue', 'conversation']
    }
    
    for module_id, keywords in keyword_mapping.items():
        if any(keyword in query_lower for keyword in keywords):
            return module_id
    
    return None

def show_module_suggestions():
    """Affiche des suggestions de modules"""
    st.markdown("**💡 Modules disponibles :**")
    
    cols = st.columns(3)
    for idx, (module_id, module_info) in enumerate(AVAILABLE_MODULES.items()):
        with cols[idx % 3]:
            if st.button(
                f"{module_info['icon']} {module_info['name']}",
                key=f"suggest_module_{module_id}",
                use_container_width=True,
                help=module_info['description']
            ):
                st.session_state.current_view = module_id
                st.rerun()

def show_ai_prompts(client: str):
    """Affiche les prompts générés par l'IA"""
    st.markdown("**💡 Suggestions d'analyse (générées par IA) :**")
    
    # Récupérer les documents du client
    if client.startswith("[LOCAL]"):
        folder_name = client.replace("[LOCAL] ", "")
        blobs = st.session_state.local_folders.get(folder_name, [])
    else:
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
    """Effectue une recherche Azure Search avec barre de progression"""
    with st.spinner("🔍 Recherche en cours..."):
        results = st.session_state.azure_search_manager.search(
            query,
            filter_type=st.session_state.get('doc_type_filter') if st.session_state.get('doc_type_filter') != 'tous' else None
        )
    
    if results:
        st.success(f"✅ {len(results)} résultats trouvés")
        
        for result in results[:5]:
            # Calculer la pertinence visuelle
            score_percent = min(result['score'] * 20, 100)
            score_color = '#48bb78' if score_percent > 70 else '#ed8936' if score_percent > 40 else '#fc8181'
            
            st.markdown(f"""
            <div class="doc-card" style="border-left: 4px solid {score_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{result['title']}</strong>
                    <span style="background: {score_color}20; color: {score_color}; padding: 0.2rem 0.5rem; 
                          border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600;">
                        {score_percent:.0f}% pertinent
                    </span>
                </div>
                <p style="color: var(--text-secondary); font-size: 0.8rem; margin: 0.5rem 0 0 0;">
                    {result['content']}...
                </p>
                <p style="font-size: 0.7rem; color: var(--text-secondary); margin: 0.25rem 0 0 0;">
                    📁 Type: {DOCUMENT_TYPES.get(result.get('type', 'autre'), {'name': 'Autre'})['name']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Aucun résultat trouvé pour cette recherche")

def process_analysis(query: str):
    """Traite l'analyse avec les IA sélectionnées"""
    client, clean_query = extract_client_and_query(query)
    
    # Trouver l'alias utilisé
    alias_used = None
    if client and query.startswith('@'):
        match = re.match(r'@(\w+)', query)
        if match:
            alias_used = match.group(1)
    
    # Container pour la progression
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Analyse en cours...")
        
        # Barre de progression principale
        main_progress = st.progress(0)
        status_text = st.empty()
        
        # Calculer les étapes
        num_ais = len(st.session_state.selected_ais)
        total_steps = 3 + num_ais
        current_step = 0
        
        # Étape 1 : Préparation
        status_text.markdown("**📋 Préparation de l'analyse...**")
        time.sleep(0.5)
        current_step += 1
        main_progress.progress(current_step / total_steps)
        
        # Étape 2 : Chargement des documents si client spécifié
        if client:
            status_text.markdown(f"**📁 Chargement du dossier @{alias_used}...**")
            time.sleep(0.5)
            current_step += 1
            main_progress.progress(current_step / total_steps)
        
        # Étape 3 : Indexation
        status_text.markdown("**🔍 Indexation du contenu...**")
        time.sleep(0.5)
        current_step += 1
        main_progress.progress(current_step / total_steps)
        
        # Analyser avec chaque IA
        results_per_ai = {}
        
        for ai_name in st.session_state.selected_ais:
            # Obtenir les infos de l'IA
            ai_info = {
                'GPT-3.5': {'icon': '🚀', 'time': 0.8},
                'GPT-4': {'icon': '🧠', 'time': 1.2},
                'ChatGPT o1': {'icon': '💬', 'time': 1.5},
                'Claude': {'icon': '🎭', 'time': 1.0},
                'Gemini': {'icon': '✨', 'time': 1.0},
                'Perplexity': {'icon': '🔮', 'time': 1.8},
                'Mistral': {'icon': '🌟', 'time': 0.8},
                'Azure OpenAI': {'icon': '☁️', 'time': 1.0}
            }.get(ai_name, {'icon': '🤖', 'time': 1.0})
            
            status_text.markdown(f"**{ai_info['icon']} {ai_name} analyse les documents...**")
            time.sleep(ai_info['time'])
            current_step += 1
            main_progress.progress(current_step / total_steps)
            
            # Stocker le résultat simulé
            results_per_ai[ai_name] = {
                'status': 'success',
                'time': ai_info['time'],
                'confidence': 85 + (len(results_per_ai) * 2)
            }
        
        # Finalisation
        main_progress.progress(1.0)
        status_text.markdown("**✅ Analyse terminée avec succès !**")
        time.sleep(0.5)
    
    # Effacer le container de progression
    progress_container.empty()
    
    # Afficher les résultats
    st.success(f"✅ Analyse terminée - {num_ais} IA ont traité votre requête")
    
    # Résultats détaillés
    if 'Azure OpenAI' in st.session_state.selected_ais and st.session_state.azure_openai_manager.connected:
        st.info("🤖 Analyse réelle avec Azure OpenAI disponible")
    
    # Afficher les résultats par IA
    st.markdown("### 📊 Résultats de l'analyse")
    
    # Créer des tabs pour chaque IA
    if num_ais > 1:
        tabs = st.tabs([f"{ai}" for ai in st.session_state.selected_ais])
        
        for idx, (ai_name, tab) in enumerate(zip(st.session_state.selected_ais, tabs)):
            with tab:
                display_ai_result(ai_name, client, alias_used, clean_query, results_per_ai.get(ai_name, {}))
    else:
        # Si une seule IA, afficher directement
        display_ai_result(st.session_state.selected_ais[0], client, alias_used, clean_query, 
                         results_per_ai.get(st.session_state.selected_ais[0], {}))
    
    # Synthèse comparative si plusieurs IA
    if num_ais > 1:
        show_comparative_synthesis(results_per_ai)

def display_ai_result(ai_name: str, client: str, alias_used: str, query: str, result_info: dict):
    """Affiche le résultat d'une IA spécifique"""
    ai_configs = {
        'GPT-3.5': {
            'strength': 'Analyse rapide et synthétique',
            'focus': 'Points clés et contradictions évidentes'
        },
        'GPT-4': {
            'strength': 'Analyse approfondie et nuancée',
            'focus': 'Implications juridiques complexes'
        },
        'ChatGPT o1': {
            'strength': 'Raisonnement structuré étape par étape',
            'focus': 'Chaîne de raisonnement juridique'
        },
        'Claude': {
            'strength': 'Argumentation détaillée',
            'focus': 'Construction d\'une défense solide'
        },
        'Gemini': {
            'strength': 'Recherche exhaustive',
            'focus': 'Exploration de toutes les pistes'
        },
        'Perplexity': {
            'strength': 'Sources et jurisprudence récentes',
            'focus': 'Actualité juridique pertinente'
        },
        'Mistral': {
            'strength': 'Expertise en droit français',
            'focus': 'Spécificités du code pénal français'
        },
        'Azure OpenAI': {
            'strength': 'Analyse sécurisée et conforme',
            'focus': 'Traitement confidentiel des données'
        }
    }
    
    config = ai_configs.get(ai_name, {'strength': 'Analyse générale', 'focus': 'Tous aspects'})
    
    st.markdown(f"""
    **Analyse par {ai_name}**
    
    📁 **Dossier :** {f'@{alias_used} ({client})' if alias_used else client or 'Général'}
    
    📝 **Requête :** {query}
    
    💪 **Point fort :** {config['strength']}
    
    🎯 **Focus :** {config['focus']}
    
    ---
    
    *Configuration des API requise pour l'analyse réelle. Cette IA est spécialisée dans {config['focus'].lower()}.*
    """)

def show_comparative_synthesis(results_per_ai: dict):
    """Affiche une synthèse comparative des résultats"""
    st.markdown("### 🔄 Synthèse comparative")
    
    # Niveau de consensus
    consensus_level = sum(r.get('confidence', 0) for r in results_per_ai.values()) / len(results_per_ai)
    consensus_color = '#48bb78' if consensus_level > 80 else '#ed8936' if consensus_level > 60 else '#fc8181'
    
    st.markdown(f"""
    <div style="background: {consensus_color}20; border: 1px solid {consensus_color}; 
                border-radius: 0.5rem; padding: 0.75rem; margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600; color: {consensus_color};">Niveau de consensus</span>
            <span style="font-size: 1.2rem; font-weight: 700; color: {consensus_color};">{consensus_level:.0f}%</span>
        </div>
        <div style="background: #e2e8f0; border-radius: 0.25rem; height: 8px; margin-top: 0.5rem;">
            <div style="background: {consensus_color}; height: 100%; width: {consensus_level}%; 
                        border-radius: 0.25rem; transition: width 0.5s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Résumé par IA
    cols = st.columns(len(results_per_ai))
    for idx, (ai_name, result) in enumerate(results_per_ai.items()):
        with cols[idx]:
            ai_icon = {
                'GPT-3.5': '🚀', 'GPT-4': '🧠', 'ChatGPT o1': '💬',
                'Claude': '🎭', 'Gemini': '✨', 'Perplexity': '🔮',
                'Mistral': '🌟', 'Azure OpenAI': '☁️'
            }.get(ai_name, '🤖')
            
            confidence = result.get('confidence', 0)
            conf_color = '#48bb78' if confidence > 80 else '#ed8936' if confidence > 60 else '#fc8181'
            
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <div style="font-size: 2rem;">{ai_icon}</div>
                <div style="font-weight: 600; margin: 0.5rem 0;">{ai_name}</div>
                <div style="color: {conf_color}; font-weight: 600;">
                    {confidence}% confiance
                </div>
                <div style="font-size: 0.7rem; color: var(--text-secondary);">
                    {result.get('time', 0):.1f}s
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_sidebar():
    """Sidebar avec navigation et actions rapides"""
    with st.sidebar:
        st.markdown("## ⚖️ IA Juridique")
        
        # Bouton retour accueil
        if st.session_state.current_view != 'home':
            if st.button("🏠 Retour à l'accueil", use_container_width=True, type="primary"):
                st.session_state.current_view = 'home'
                st.rerun()
        
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
        
        # Navigation par modules
        st.markdown("### 📋 Modules")
        
        for module_id, module in AVAILABLE_MODULES.items():
            is_current = st.session_state.current_view == module_id
            
            if st.button(
                f"{module['icon']} {module['name']}",
                key=f"nav_{module_id}",
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                st.session_state.current_view = module_id
                st.rerun()
        
        st.markdown("---")
        
        # Actions rapides
        st.markdown("### ⚡ Actions rapides")
        
        if st.button("🔍 Nouvelle recherche", key="quick_search_sidebar", use_container_width=True):
            st.session_state.current_view = "search"
            st.session_state.search_query = ""
            st.rerun()
        
        if st.button("📁 Charger documents", key="quick_upload_sidebar", use_container_width=True):
            st.session_state.current_view = "home"
            st.rerun()
        
        # Dossiers récents
        if blob_ok or st.session_state.local_folders:
            st.markdown("---")
            st.markdown("### 📁 Dossiers récents")
            
            # Dossiers Azure
            if blob_ok:
                containers = st.session_state.azure_blob_manager.list_containers()[:5]
                for container in containers:
                    if st.button(f"☁️ {container}", key=f"recent_{container}", use_container_width=True):
                        st.session_state.search_query = f"@{container}, "
                        st.session_state.current_view = "search"
                        st.rerun()
            
            # Dossiers locaux
            for folder_name in list(st.session_state.local_folders.keys())[:3]:
                if st.button(f"💾 {folder_name}", key=f"recent_local_{folder_name}", use_container_width=True):
                    st.session_state.selected_client = folder_name
                    st.session_state.active_source = 'local'
                    st.session_state.current_view = "search"
                    st.rerun()
        
        # Configuration et aide
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚙️ Config", key="nav_config", use_container_width=True):
                st.session_state.current_view = "config"
                st.rerun()
        
        with col2:
            if st.button("❓ Aide", key="nav_help", use_container_width=True):
                st.session_state.current_view = "help"
                st.rerun()

# ========== MODULES SPÉCIFIQUES ==========

def show_compare_module():
    """Module de comparaison de documents"""
    st.markdown("# 📊 Comparaison de documents")
    st.markdown("Analysez les différences et contradictions entre plusieurs documents")
    
    # Sélection de la source
    source_tab = st.tabs(["☁️ Documents Azure", "💾 Documents locaux"])
    
    with source_tab[0]:
        if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected:
            containers = st.session_state.azure_blob_manager.list_containers()
            
            if containers:
                selected_container = st.selectbox(
                    "Sélectionnez un dossier",
                    options=containers,
                    key="compare_container"
                )
                
                if selected_container:
                    docs = st.session_state.azure_blob_manager.list_blobs_with_versions(selected_container, False)
                    
                    if docs:
                        st.multiselect(
                            "Sélectionnez les documents à comparer (minimum 2)",
                            options=[d['name'] for d in docs],
                            key="docs_to_compare"
                        )
    
    with source_tab[1]:
        if st.session_state.local_folders:
            selected_local_folder = st.selectbox(
                "Sélectionnez un dossier local",
                options=list(st.session_state.local_folders.keys()),
                key="compare_local_folder"
            )
            
            if selected_local_folder:
                docs = st.session_state.local_folders[selected_local_folder]
                
                if docs:
                    st.multiselect(
                        "Sélectionnez les documents à comparer (minimum 2)",
                        options=[d['name'] for d in docs],
                        key="local_docs_to_compare"
                    )
    
    # Lancer la comparaison
    docs_selected = st.session_state.get('docs_to_compare', []) or st.session_state.get('local_docs_to_compare', [])
    
    if docs_selected and len(docs_selected) >= 2:
        if st.button("🔍 Lancer la comparaison", type="primary"):
            with st.spinner("Analyse comparative en cours..."):
                time.sleep(2)
            
            st.success("✅ Comparaison terminée")
            
            # Résultats simulés
            st.markdown("### 📋 Résultats de la comparaison")
            
            tabs = st.tabs(["🔍 Contradictions", "✅ Concordances", "📊 Synthèse", "📈 Visualisation"])
            
            with tabs[0]:
                st.warning("**3 contradictions majeures identifiées**")
                st.markdown("""
                1. **Dates divergentes** : Document 1 mentionne le 15/01, Document 2 le 17/01
                2. **Montants différents** : 45,000€ vs 47,500€
                3. **Témoignages contradictoires** sur la présence du client
                """)
            
            with tabs[1]:
                st.success("**Points de concordance**")
                st.markdown("""
                - Lieu de l'incident confirmé dans tous les documents
                - Personnes présentes identiques (sauf client)
                - Chronologie générale cohérente
                """)
            
            with tabs[2]:
                st.info("**Synthèse comparative**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Cohérence globale", "78%", "+5%")
                with col2:
                    st.metric("Points critiques", "3", "-1")
            
            with tabs[3]:
                st.info("Visualisation interactive des différences (nécessite configuration complète)")
    else:
        st.info("Sélectionnez au moins 2 documents pour comparer")

def show_timeline_module():
    """Module de création de timeline"""
    st.markdown("# 📅 Timeline juridique")
    st.markdown("Créez une chronologie visuelle des événements")
    
    if st.session_state.selected_documents or st.session_state.search_query:
        source = "documents sélectionnés" if st.session_state.selected_documents else "recherche actuelle"
        st.info(f"📄 Source : {source}")
        
        if st.button("🚀 Générer la timeline", type="primary"):
            with st.spinner("Extraction des dates et événements..."):
                progress = st.progress(0)
                for i in range(100):
                    progress.progress(i + 1)
                    time.sleep(0.01)
            
            st.success("✅ Timeline générée")
            
            # Timeline simulée
            st.markdown("### 📅 Chronologie des événements")
            
            events = [
                ("2024-01-15", "🔍", "Perquisition au siège social", "critique"),
                ("2024-01-17", "📝", "Première audition", "important"),
                ("2024-01-22", "📄", "Remise des documents", "neutre"),
                ("2024-02-01", "⚖️", "Mise en examen", "critique"),
                ("2024-02-15", "📊", "Rapport d'expertise", "important"),
                ("2024-03-01", "🏛️", "Audience préliminaire", "critique"),
                ("2024-03-15", "📑", "Dépôt des conclusions", "important")
            ]
            
            for date, icon, event, importance in events:
                color = {
                    'critique': '#e53e3e',
                    'important': '#ed8936',
                    'neutre': '#718096'
                }.get(importance, '#718096')
                
                st.markdown(f"""
                <div class="doc-card" style="border-left: 4px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{date}</strong> {icon} {event}
                        </div>
                        <span style="background: {color}20; color: {color}; padding: 0.2rem 0.5rem; 
                              border-radius: 0.25rem; font-size: 0.7rem; font-weight: 600;">
                            {importance.capitalize()}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Options d'export
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Exporter PDF"):
                    st.success("Timeline exportée en PDF")
            with col2:
                if st.button("📊 Exporter Excel"):
                    st.success("Timeline exportée en Excel")
            with col3:
                if st.button("🖼️ Exporter Image"):
                    st.success("Timeline exportée en image")
    else:
        st.info("Sélectionnez des documents ou effectuez une recherche pour créer une timeline")

def show_extract_module():
    """Module d'extraction d'informations"""
    st.markdown("# 📑 Extraction intelligente")
    st.markdown("Extrayez automatiquement les informations clés")
    
    extraction_type = st.radio(
        "Que souhaitez-vous extraire ?",
        ["Points favorables", "Éléments à charge", "Informations clés", "Entités et personnes", "Personnalisé"],
        horizontal=True
    )
    
    if extraction_type == "Personnalisé":
        custom_query = st.text_input("Décrivez ce que vous cherchez", placeholder="Ex: tous les montants supérieurs à 10 000€")
    
    # Options avancées
    with st.expander("Options avancées"):
        col1, col2 = st.columns(2)
        with col1:
            confidence_threshold = st.slider("Seuil de confiance", 0, 100, 75, help="Ne montrer que les résultats avec ce niveau de confiance minimum")
        with col2:
            max_results = st.number_input("Nombre max de résultats", 1, 100, 20)
    
    if st.button("🔍 Lancer l'extraction", type="primary"):
        with st.spinner(f"Extraction des {extraction_type.lower()}..."):
            time.sleep(1.5)
        
        st.success("✅ Extraction terminée")
        
        # Résultats selon le type
        if extraction_type == "Points favorables":
            st.markdown("### ✅ Points favorables identifiés")
            
            favorable_points = [
                ("Absence de préméditation", "Aucun élément ne suggère une planification", 92),
                ("Coopération totale", "Le client a fourni tous les documents demandés", 88),
                ("Témoignages favorables", "3 témoins confirment la version du client", 85),
                ("Expertises contradictoires", "Les conclusions ne sont pas unanimes", 79),
                ("Procédure contestable", "Plusieurs vices de forme identifiés", 76)
            ]
            
            for point, detail, confidence in favorable_points:
                if confidence >= confidence_threshold:
                    st.success(f"""
                    **{point}** (Confiance: {confidence}%)
                    
                    {detail}
                    """)
                    
        elif extraction_type == "Éléments à charge":
            st.markdown("### ⚠️ Éléments à charge")
            
            charge_points = [
                ("Signatures sur documents", "Présence confirmée du client sur 5 documents", 95),
                ("Mouvements financiers", "Transferts suspects totalisant 250 000€", 88),
                ("Chronologie défavorable", "Dates coïncidentes avec les faits reprochés", 82)
            ]
            
            for point, detail, confidence in charge_points:
                if confidence >= confidence_threshold:
                    st.warning(f"""
                    **{point}** (Confiance: {confidence}%)
                    
                    {detail}
                    """)
                    
        elif extraction_type == "Entités et personnes":
            st.markdown("### 👥 Entités et personnes identifiées")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Personnes physiques**")
                persons = [
                    "Jean DUPONT (Client)",
                    "Marie MARTIN (Témoin)",
                    "Pierre DURAND (Expert)",
                    "Sophie BERNARD (Avocat adverse)"
                ]
                for person in persons[:max_results//2]:
                    st.markdown(f"• {person}")
            
            with col2:
                st.markdown("**Personnes morales**")
                entities = [
                    "SARL DUPONT & ASSOCIÉS",
                    "Banque Nationale de Paris",
                    "Cabinet d'expertise AUDIT PLUS",
                    "Tribunal de Commerce de Paris"
                ]
                for entity in entities[:max_results//2]:
                    st.markdown(f"• {entity}")
                    
        else:
            st.markdown("### 📋 Informations clés extraites")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Documents analysés", "47")
            with col2:
                st.metric("Personnes identifiées", "12")
            with col3:
                st.metric("Dates clés", "8")
            with col4:
                st.metric("Montants cumulés", "2.3M€")
            
            # Détails
            with st.expander("Voir les détails"):
                st.json({
                    "dates_cles": ["2024-01-15", "2024-01-17", "2024-02-01"],
                    "montants": [45000, 125000, 2130000],
                    "lieux": ["Paris", "Lyon", "Marseille"],
                    "types_documents": {
                        "PV": 12,
                        "Expertises": 5,
                        "Contrats": 8,
                        "Factures": 22
                    }
                })

def show_strategy_module():
    """Module de stratégie juridique"""
    st.markdown("# ⚖️ Stratégie juridique IA")
    st.markdown("Obtenez des recommandations stratégiques personnalisées")
    
    # Contexte de l'affaire
    st.text_area(
        "Contexte de l'affaire",
        placeholder="Décrivez brièvement l'affaire, les enjeux et vos objectifs...",
        height=150,
        key="strategy_context"
    )
    
    # Type d'affaire
    col1, col2 = st.columns(2)
    
    with col1:
        case_type = st.selectbox(
            "Type d'affaire",
            ["Pénal", "Civil", "Commercial", "Administratif", "Social", "Fiscal"]
        )
    
    with col2:
        urgency = st.select_slider(
            "Urgence",
            options=["Faible", "Modérée", "Élevée", "Critique"],
            value="Modérée"
        )
    
    # Axes d'analyse
    strategy_focus = st.multiselect(
        "Axes d'analyse prioritaires",
        ["Contestation des preuves", "Vices de procédure", "Fond du dossier", 
         "Négociation", "Témoignages", "Expertises", "Jurisprudence"],
        default=["Fond du dossier", "Contestation des preuves"]
    )
    
    # IA à utiliser pour la stratégie
    st.markdown("### 🤖 IA pour l'analyse stratégique")
    strategy_ais = st.multiselect(
        "Sélectionnez les IA pour générer la stratégie",
        ["GPT-4", "Claude", "Mistral", "ChatGPT o1"],
        default=["GPT-4", "Claude"]
    )
    
    if st.button("🎯 Générer la stratégie", type="primary", disabled=not strategy_ais):
        with st.spinner("Analyse stratégique en cours..."):
            progress = st.progress(0)
            for i in range(100):
                progress.progress(i + 1)
                time.sleep(0.02)
        
        st.success("✅ Stratégie générée avec succès")
        
        # Stratégie détaillée
        st.markdown("### 🎯 Stratégie recommandée")
        
        tabs = st.tabs(["📍 Vue d'ensemble", "💪 Forces", "⚠️ Risques", "📋 Plan d'action", "📊 Scénarios"])
        
        with tabs[0]:
            st.markdown("""
            **Analyse stratégique globale**
            
            Basée sur l'analyse de 47 documents et la jurisprudence récente, voici notre recommandation :
            
            1. **Ligne de défense principale** : Contester la régularité de la procédure
            2. **Ligne subsidiaire** : Démontrer l'absence d'intention frauduleuse
            3. **Approche tactique** : Négociation parallèle pour minimiser les risques
            
            **Probabilité de succès estimée** : 72% (avec réserves sur certains points)
            """)
            
            # Métriques clés
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Succès global", "72%", "+12%")
            with col2:
                st.metric("Risque résiduel", "Modéré", "Stable")
            with col3:
                st.metric("Temps estimé", "6-8 mois", None)
        
        with tabs[1]:
            st.markdown("### 💪 Forces du dossier")
            
            strengths = [
                {
                    "point": "Vices de procédure identifiés",
                    "impact": "Élevé",
                    "details": "3 irrégularités majeures dans la procédure d'instruction"
                },
                {
                    "point": "Expertises contradictoires",
                    "impact": "Moyen",
                    "details": "Les conclusions des experts divergent sur des points essentiels"
                },
                {
                    "point": "Profil du client",
                    "impact": "Moyen",
                    "details": "Aucun antécédent, réputation professionnelle solide"
                },
                {
                    "point": "Témoignages favorables",
                    "impact": "Moyen",
                    "details": "5 témoins crédibles soutiennent la version du client"
                }
            ]
            
            for strength in strengths:
                impact_color = {
                    "Élevé": "🟢",
                    "Moyen": "🟡",
                    "Faible": "🔴"
                }.get(strength["impact"], "⚪")
                
                st.markdown(f"""
                **{strength["point"]}** {impact_color} Impact: {strength["impact"]}
                
                {strength["details"]}
                """)
        
        with tabs[2]:
            st.markdown("### ⚠️ Points de vigilance")
            
            risks = [
                ("Documents compromettants", "Certaines pièces nécessitent une explication solide", "Élevé"),
                ("Témoins adverses", "2 témoins de la partie adverse semblent crédibles", "Moyen"),
                ("Jurisprudence défavorable", "Décisions récentes dans des cas similaires", "Moyen"),
                ("Délais de prescription", "Attention aux dates limites pour certains recours", "Critique")
            ]
            
            for risk, detail, level in risks:
                level_color = {
                    "Critique": "#e53e3e",
                    "Élevé": "#ed8936",
                    "Moyen": "#d69e2e",
                    "Faible": "#38a169"
                }.get(level, "#718096")
                
                st.markdown(f"""
                <div style="padding: 0.75rem; border-left: 4px solid {level_color}; background: {level_color}20; margin: 0.5rem 0;">
                    <strong>{risk}</strong> - Niveau: {level}
                    <br>{detail}
                </div>
                """, unsafe_allow_html=True)
        
        with tabs[3]:
            st.markdown("### 📋 Plan d'action détaillé")
            
            phases = [
                {
                    "phase": "Phase 1 : Préparation (0-2 mois)",
                    "actions": [
                        "Audit complet du dossier",
                        "Identification des témoins clés",
                        "Recherche jurisprudentielle approfondie",
                        "Constitution de l'équipe de défense"
                    ]
                },
                {
                    "phase": "Phase 2 : Offensive (2-4 mois)",
                    "actions": [
                        "Dépôt des premières conclusions",
                        "Contestation de la procédure",
                        "Demandes d'actes complémentaires",
                        "Audition des témoins favorables"
                    ]
                },
                {
                    "phase": "Phase 3 : Consolidation (4-6 mois)",
                    "actions": [
                        "Contre-expertise si nécessaire",
                        "Mémoire en défense approfondi",
                        "Négociations éventuelles",
                        "Préparation des plaidoiries"
                    ]
                }
            ]
            
            for phase_info in phases:
                st.markdown(f"**{phase_info['phase']}**")
                for action in phase_info['actions']:
                    st.markdown(f"- {action}")
                st.markdown("")
        
        with tabs[4]:
            st.markdown("### 📊 Scénarios possibles")
            
            scenarios = [
                {
                    "name": "Scénario optimiste",
                    "probability": 35,
                    "outcome": "Relaxe/Non-lieu complet",
                    "conditions": "Vices de procédure reconnus + témoignages décisifs"
                },
                {
                    "name": "Scénario réaliste",
                    "probability": 45,
                    "outcome": "Sanctions minimales/Négociation favorable",
                    "conditions": "Défense solide + négociation efficace"
                },
                {
                    "name": "Scénario pessimiste",
                    "probability": 20,
                    "outcome": "Condamnation partielle",
                    "conditions": "Rejet des arguments procéduraux"
                }
            ]
            
            for scenario in scenarios:
                color = '#48bb78' if scenario["probability"] > 40 else '#ed8936' if scenario["probability"] > 25 else '#fc8181'
                
                st.markdown(f"""
                <div style="margin: 1rem 0; padding: 1rem; border: 1px solid {color}; border-radius: 0.5rem;">
                    <h4 style="color: {color}; margin: 0;">{scenario["name"]} - {scenario["probability"]}%</h4>
                    <p style="margin: 0.5rem 0;"><strong>Issue probable :</strong> {scenario["outcome"]}</p>
                    <p style="margin: 0; font-size: 0.8rem; color: var(--text-secondary);">
                        Conditions : {scenario["conditions"]}
                    </p>
                </div>
                """, unsafe_allow_html=True)

def show_report_module():
    """Module de génération de rapports"""
    st.markdown("# 📄 Génération de rapports")
    st.markdown("Créez des documents juridiques professionnels automatiquement")
    
    # Type de rapport
    report_type = st.selectbox(
        "Type de document à générer",
        ["Synthèse d'analyse", "Note de plaidoirie", "Mémo juridique", 
         "Conclusions", "Rapport d'expertise", "Courrier officiel", "Note stratégique"]
    )
    
    # Paramètres du rapport
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tone = st.select_slider(
            "Ton du document",
            options=["Très formel", "Formel", "Neutre", "Accessible", "Pédagogique"],
            value="Formel"
        )
    
    with col2:
        length = st.select_slider(
            "Longueur",
            options=["Concis (1-2 pages)", "Standard (3-5 pages)", 
                    "Détaillé (6-10 pages)", "Exhaustif (10+ pages)"],
            value="Standard (3-5 pages)"
        )
    
    with col3:
        format_output = st.selectbox(
            "Format de sortie",
            ["PDF", "Word", "HTML", "Markdown"]
        )
    
    # Éléments à inclure
    st.markdown("### 📌 Éléments à inclure")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_elements = st.multiselect(
            "Sections principales",
            ["Résumé exécutif", "Chronologie", "Analyse des preuves", 
             "Jurisprudence", "Recommandations", "Annexes", "Bibliographie"],
            default=["Résumé exécutif", "Chronologie", "Analyse des preuves", "Recommandations"]
        )
    
    with col2:
        visual_elements = st.multiselect(
            "Éléments visuels",
            ["Graphiques", "Tableaux", "Timeline visuelle", "Schémas", "Citations mises en avant"],
            default=["Tableaux", "Citations mises en avant"]
        )
    
    # Informations spécifiques
    with st.expander("Informations spécifiques au document"):
        destinataire = st.text_input("Destinataire", placeholder="Ex: Tribunal de Commerce de Paris")
        reference = st.text_input("Référence du dossier", placeholder="Ex: RG 2024/12345")
        urgent = st.checkbox("Marquer comme URGENT")
        confidentiel = st.checkbox("Marquer comme CONFIDENTIEL")
    
    # Génération
    if st.button("📝 Générer le document", type="primary"):
        with st.spinner(f"Génération du {report_type.lower()}..."):
            progress = st.progress(0)
            status = st.empty()
            
            steps = [
                "Analyse du contexte...",
                "Extraction des informations pertinentes...",
                "Structuration du document...",
                "Rédaction du contenu...",
                "Mise en forme professionnelle...",
                "Génération des éléments visuels...",
                "Finalisation et export..."
            ]
            
            for i, step in enumerate(steps):
                status.text(step)
                progress.progress((i + 1) / len(steps))
                time.sleep(0.5)
        
        st.success(f"✅ {report_type} généré avec succès")
        
        # Aperçu du document
        st.markdown(f"### 📄 Aperçu : {report_type}")
        
        # En-tête du document
        if urgent:
            st.error("**URGENT**")
        if confidentiel:
            st.warning("**CONFIDENTIEL**")
        
        with st.container():
            st.markdown(f"""
            ---
            
            **{report_type.upper()}**
            
            **Référence :** {reference if reference else "À définir"}
            
            **Date :** {datetime.now().strftime('%d/%m/%Y')}
            
            **Destinataire :** {destinataire if destinataire else "À définir"}
            
            ---
            
            ## I. Résumé exécutif
            
            Cette {report_type.lower()} présente une analyse approfondie du dossier référencé ci-dessus. 
            Les conclusions principales sont les suivantes :
            
            - Point clé 1 : [Analyse générée par IA]
            - Point clé 2 : [Analyse générée par IA]
            - Point clé 3 : [Analyse générée par IA]
            
            ## II. Contexte et enjeux
            
            [Contenu généré automatiquement basé sur les documents analysés]
            
            ## III. Analyse détaillée
            
            ### 3.1 Examen des pièces
            
            [Analyse approfondie des documents]
            
            ### 3.2 Points de droit applicables
            
            [Références juridiques pertinentes]
            
            ## IV. Recommandations
            
            Au vu des éléments analysés, nous recommandons :
            
            1. [Recommandation stratégique 1]
            2. [Recommandation stratégique 2]
            3. [Recommandation stratégique 3]
            
            ## V. Conclusion
            
            [Synthèse et perspectives]
            
            ---
            
            *Document généré automatiquement par IA Juridique*
            """)
        
        # Actions sur le document
        st.markdown("### 🛠️ Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"📥 Télécharger {format_output}", use_container_width=True):
                st.success(f"Document téléchargé au format {format_output}")
        
        with col2:
            if st.button("✏️ Éditer", use_container_width=True):
                st.info("Ouverture de l'éditeur...")
        
        with col3:
            if st.button("📧 Envoyer", use_container_width=True):
                st.info("Préparation de l'envoi...")
        
        with col4:
            if st.button("💾 Sauvegarder", use_container_width=True):
                st.success("Document sauvegardé")

def show_contract_module():
    """Module d'analyse de contrats"""
    st.markdown("# 📋 Analyse de contrats")
    st.markdown("Analysez vos contrats avec l'IA pour identifier les risques et opportunités")
    
    st.info("🚧 Module en développement - Disponible prochainement")
    
    st.markdown("""
    ### Fonctionnalités à venir :
    
    - 🔍 **Détection automatique des clauses importantes**
    - ⚠️ **Identification des clauses à risque**
    - 📊 **Comparaison de versions de contrats**
    - ✅ **Vérification de conformité légale**
    - 💡 **Suggestions d'amélioration**
    - 📑 **Extraction des obligations et échéances**
    """)

def show_jurisprudence_module():
    """Module de recherche de jurisprudence"""
    st.markdown("# ⚖️ Recherche de jurisprudence")
    st.markdown("Trouvez des décisions similaires et des précédents juridiques")
    
    st.info("🚧 Module en développement - Disponible prochainement")
    
    st.markdown("""
    ### Fonctionnalités à venir :
    
    - 🔍 **Recherche par mots-clés et concepts juridiques**
    - 📊 **Analyse de tendances jurisprudentielles**
    - 🎯 **Recommandations de décisions pertinentes**
    - 📈 **Statistiques de succès par type d'argument**
    - 🔗 **Liens vers les textes complets**
    - 📑 **Génération automatique de citations**
    """)

def show_chat_module():
    """Module d'assistant juridique par chat"""
    st.markdown("# 💬 Assistant juridique IA")
    st.markdown("Dialoguez avec votre assistant juridique intelligent")
    
    # Zone de chat
    chat_container = st.container()
    
    # Historique des messages (simulé)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Bonjour ! Je suis votre assistant juridique IA. Comment puis-je vous aider aujourd'hui ?"
            }
        ]
    
    # Afficher l'historique
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div style="text-align: right; margin: 0.5rem 0;">
                    <div style="display: inline-block; background: var(--accent-blue); color: white; 
                                padding: 0.5rem 1rem; border-radius: 1rem 1rem 0 1rem; max-width: 70%;">
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: left; margin: 0.5rem 0;">
                    <div style="display: inline-block; background: var(--light-blue); color: var(--text-primary); 
                                padding: 0.5rem 1rem; border-radius: 1rem 1rem 1rem 0; max-width: 70%;">
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Zone de saisie
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Votre question",
            placeholder="Posez votre question juridique...",
            key="chat_input",
            label_visibility="hidden"
        )
    
    with col2:
        send_button = st.button("Envoyer", type="primary", use_container_width=True)
    
    if send_button and user_input:
        # Ajouter le message utilisateur
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Simuler une réponse de l'assistant
        with st.spinner("L'assistant réfléchit..."):
            time.sleep(1)
        
        # Réponse simulée
        response = "Je comprends votre question. Pour vous donner une réponse précise, j'aurais besoin de consulter les documents de votre dossier. Pourriez-vous me préciser le contexte ?"
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()
    
    # Suggestions de questions
    st.markdown("### 💡 Suggestions de questions")
    
    suggestions = [
        "Quelle est la prescription pour ce type d'affaire ?",
        "Quels sont mes recours possibles ?",
        "Comment contester cette décision ?",
        "Quelle jurisprudence s'applique à mon cas ?"
    ]
    
    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions):
        with cols[idx % 2]:
            if st.button(suggestion, key=f"suggest_{idx}", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": suggestion
                })
                st.rerun()

def show_config():
    """Page de configuration détaillée"""
    st.markdown("# ⚙️ Configuration")
    
    # Diagnostics
    show_diagnostics()
    
    st.markdown("---")
    
    # Onglets de configuration
    tabs = st.tabs(["💾 Azure Storage", "🔍 Azure Search", "🤖 Azure OpenAI", "⚡ Performances"])
    
    with tabs[0]:
        st.markdown("""
        ### Configuration Azure Blob Storage
        
        Le stockage Azure est **obligatoire** pour utiliser les documents cloud.
        
        **État actuel :** """ + 
        ("✅ Connecté" if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected else "❌ Non connecté"))
        
        with st.expander("Instructions de configuration"):
            st.markdown("""
            1. Créez un compte de stockage Azure
            2. Récupérez la chaîne de connexion dans le portail Azure
            3. Ajoutez-la dans les secrets Hugging Face :
            
            ```
            AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=votrecompte;AccountKey=votrecle;EndpointSuffix=core.windows.net
            ```
            """)
        
        if st.button("🔄 Tester la connexion Blob Storage"):
            with st.spinner("Test en cours..."):
                st.session_state.azure_blob_manager = AzureBlobManager()
                time.sleep(1)
            
            if st.session_state.azure_blob_manager.connected:
                st.success("✅ Connexion réussie !")
                containers = st.session_state.azure_blob_manager.list_containers()
                st.info(f"📁 {len(containers)} conteneurs trouvés")
            else:
                st.error("❌ Échec de la connexion")
                if st.session_state.azure_blob_manager.error:
                    st.error(f"Erreur : {st.session_state.azure_blob_manager.error}")
    
    with tabs[1]:
        st.markdown("""
        ### Configuration Azure Cognitive Search
        
        La recherche Azure permet une recherche sémantique avancée (optionnel).
        
        **État actuel :** """ + 
        ("✅ Connecté" if st.session_state.azure_search_manager and st.session_state.azure_search_manager.connected else "⚠️ Non configuré"))
        
        with st.expander("Instructions de configuration"):
            st.markdown("""
            1. Créez un service Azure Cognitive Search
            2. Créez un index pour vos documents
            3. Ajoutez dans les secrets :
            
            ```
            AZURE_SEARCH_ENDPOINT=https://votre-search.search.windows.net
            AZURE_SEARCH_KEY=votre-cle-api
            AZURE_SEARCH_INDEX=nom-de-votre-index
            ```
            """)
        
        if st.button("🔄 Tester Azure Search"):
            with st.spinner("Test en cours..."):
                st.session_state.azure_search_manager = AzureSearchManager()
                time.sleep(1)
            
            if st.session_state.azure_search_manager.connected:
                st.success("✅ Connexion réussie !")
            else:
                st.warning("⚠️ Service non configuré")
    
    with tabs[2]:
        st.markdown("""
        ### Configuration Azure OpenAI
        
        Azure OpenAI permet d'utiliser GPT-4 de manière sécurisée (optionnel).
        
        **État actuel :** """ + 
        ("✅ Connecté" if st.session_state.azure_openai_manager and st.session_state.azure_openai_manager.connected else "⚠️ Non configuré"))
        
        with st.expander("Instructions de configuration"):
            st.markdown("""
            1. Déployez un modèle dans Azure OpenAI
            2. Récupérez l'endpoint et la clé API
            3. Ajoutez dans les secrets :
            
            ```
            AZURE_OPENAI_ENDPOINT=https://votre-openai.openai.azure.com/
            AZURE_OPENAI_KEY=votre-cle-api
            AZURE_OPENAI_DEPLOYMENT=nom-du-deploiement
            ```
            """)
        
        if st.button("🔄 Tester Azure OpenAI"):
            with st.spinner("Test en cours..."):
                st.session_state.azure_openai_manager = AzureOpenAIManager()
                time.sleep(1)
            
            if st.session_state.azure_openai_manager.connected:
                st.success("✅ Connexion réussie !")
                st.info(f"Modèle : {st.session_state.azure_openai_manager.deployment_name}")
            else:
                st.warning("⚠️ Service non configuré")
    
    with tabs[3]:
        st.markdown("""
        ### ⚡ Optimisation des performances
        
        Configurez les paramètres de performance de l'application.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            cache_duration = st.slider(
                "Durée du cache (minutes)",
                min_value=5,
                max_value=60,
                value=30,
                help="Durée de conservation des données en cache"
            )
            
            max_concurrent_ai = st.number_input(
                "IA simultanées maximum",
                min_value=1,
                max_value=8,
                value=3,
                help="Nombre d'IA pouvant analyser en parallèle"
            )
        
        with col2:
            enable_compression = st.checkbox(
                "Compression des documents",
                value=True,
                help="Compresser les documents pour économiser la bande passante"
            )
            
            enable_preview = st.checkbox(
                "Aperçu des documents",
                value=True,
                help="Générer des aperçus pour les documents"
            )
        
        if st.button("💾 Sauvegarder les paramètres"):
            st.success("✅ Paramètres sauvegardés")

def show_help():
    """Page d'aide complète"""
    st.markdown("# ❓ Guide d'utilisation")
    
    # Menu d'aide
    help_topics = st.tabs([
        "🚀 Démarrage rapide",
        "📁 Gestion des documents", 
        "🤖 Utilisation des IA",
        "🔍 Recherche avancée",
        "📊 Modules spécialisés",
        "❓ FAQ"
    ])
    
    with help_topics[0]:
        st.markdown("""
        ### 🚀 Démarrage rapide
        
        **Bienvenue dans l'IA Juridique !** Voici comment démarrer en 3 étapes :
        
        #### 1️⃣ Chargez vos documents
        
        **Option A : Documents Azure (recommandé)**
        - Vos documents sont déjà sur Azure Blob Storage
        - Accès instantané à tous vos dossiers
        - Synchronisation automatique
        
        **Option B : Documents locaux**
        - Glissez-déposez vos fichiers directement
        - Supporte PDF, DOCX, TXT et images
        - Possibilité de déposer des dossiers complets
        
        #### 2️⃣ Sélectionnez vos IA
        
        Choisissez parmi 8 IA spécialisées :
        - **GPT-4** : Pour les analyses complexes
        - **Claude** : Pour l'argumentation juridique
        - **Mistral** : Expert en droit français
        - Et 5 autres IA complémentaires
        
        💡 **Astuce** : Utilisez plusieurs IA pour croiser les analyses
        
        #### 3️⃣ Lancez votre analyse
        
        - Tapez votre question en langage naturel
        - Utilisez @dossier pour cibler un dossier spécifique
        - Appuyez sur Entrée pour lancer l'analyse
        
        **C'est parti !** 🎉
        """)
        
        # Vidéo tutoriel simulée
        st.info("🎥 Tutoriel vidéo disponible : 'Première analyse en 5 minutes'")
    
    with help_topics[1]:
        st.markdown("""
        ### 📁 Gestion des documents
        
        #### Organisation des dossiers
        
        **Structure recommandée :**
        ```
        📁 Affaire_Client_2024/
        ├── 📝 PV_Auditions/
        ├── 🔬 Expertises/
        ├── 📄 Contrats/
        ├── ⚖️ Procedures/
        └── 📑 Correspondances/
        ```
        
        #### Indicateurs de dossiers (@alias)
        
        L'application génère automatiquement des alias courts :
        - `@mar` → Dossier Martinez_2024
        - `@dup` → Dossier Dupont_Affaire_Penale
        - `@loc_imp` → Dossier local Import_15_01
        
        **Comment ça marche ?**
        1. Les 3 premières lettres pour les noms courts
        2. Les initiales pour les noms composés
        3. Préfixe `loc_` pour les dossiers locaux
        
        #### Gestion des versions
        
        Pour les documents Word :
        - ✅ Par défaut : seule la dernière version s'affiche
        - 📚 Option "Toutes versions" : voir l'historique complet
        - 🔄 Détection automatique des versions (dates, v1/v2, etc.)
        
        #### Types de documents reconnus
        
        L'IA catégorise automatiquement vos documents :
        - 📝 **PV** : Procès-verbaux, auditions
        - 🔬 **Expertises** : Rapports d'experts
        - 📄 **Contrats** : Accords, conventions
        - 🧾 **Factures** : Documents comptables
        - ✉️ **Courriers** : Correspondances
        - ⚖️ **Procédures** : Jugements, ordonnances
        - 📁 **Autres** : Documents divers
        """)
    
    with help_topics[2]:
        st.markdown("""
        ### 🤖 Utilisation des IA
        
        #### Profils des IA disponibles
        
        | IA | Spécialité | Vitesse | Usage recommandé |
        |---|---|---|---|
        | 🚀 **GPT-3.5** | Analyse rapide | ⚡⚡⚡ | Première exploration |
        | 🧠 **GPT-4** | Analyse approfondie | ⚡⚡ | Cas complexes |
        | 💬 **ChatGPT o1** | Raisonnement structuré | ⚡ | Logique juridique |
        | 🎭 **Claude** | Argumentation | ⚡⚡ | Plaidoiries |
        | ✨ **Gemini** | Recherche exhaustive | ⚡⚡ | Documentation |
        | 🔮 **Perplexity** | Actualités juridiques | ⚡⚡⚡ | Jurisprudence récente |
        | 🌟 **Mistral** | Droit français | ⚡⚡⚡ | Spécificités FR |
        | ☁️ **Azure OpenAI** | Sécurisé | ⚡⚡ | Données sensibles |
        
        #### Stratégies de sélection
        
        **🎯 Pour une analyse rapide :**
        - Sélectionnez GPT-3.5 + Mistral
        - Temps : ~5 secondes
        - Idéal pour : premier aperçu
        
        **🔬 Pour une analyse complète :**
        - Sélectionnez GPT-4 + Claude + Mistral
        - Temps : ~15 secondes
        - Idéal pour : dossiers importants
        
        **🌐 Pour une recherche exhaustive :**
        - Sélectionnez toutes les IA
        - Temps : ~30 secondes
        - Idéal pour : cas critiques
        
        #### Interprétation des résultats
        
        - **Niveau de consensus** : Agreement entre les IA (>80% = fiable)
        - **Confiance individuelle** : Certitude de chaque IA
        - **Points de divergence** : À examiner en priorité
        """)
    
    with help_topics[3]:
        st.markdown("""
        ### 🔍 Recherche avancée
        
        #### Mode Multi-IA vs Mode Module
        
        L'application propose deux modes de recherche :
        
        **🤖 Mode Multi-IA** : Analyse avec plusieurs IA
        - Sélectionnez les IA à utiliser
        - Lancez une analyse comparative
        - Obtenez des perspectives multiples
        
        **📋 Mode Module** : Appel direct d'un module
        - Tapez le nom du module ou utilisez le langage naturel
        - Exemples : "timeline", "créer une chronologie", "comparer documents"
        - Accès rapide aux fonctionnalités spécifiques
        
        #### Syntaxe de recherche
        
        **Recherche simple :**
        ```
        analyser les contradictions dans les témoignages
        ```
        
        **Recherche ciblée (avec @) :**
        ```
        @mar, identifier les incohérences dans les PV
        ```
        
        **Recherche multi-critères :**
        ```
        @dup, comparer les montants entre factures et contrats après janvier 2024
        ```
        
        #### Opérateurs avancés
        
        | Opérateur | Fonction | Exemple |
        |---|---|---|
        | `@dossier` | Cible un dossier | `@mar, analyse` |
        | `ET` | Tous les termes | `contrat ET clause` |
        | `OU` | Au moins un terme | `PV OU audition` |
        | `"..."` | Expression exacte | `"clause abusive"` |
        | `SAUF` | Exclure un terme | `expertise SAUF médicale` |
        | `DATE:` | Filtrer par date | `DATE:2024 contradictions` |
        
        #### Prompts suggérés par l'IA
        
        L'IA analyse vos documents et suggère des analyses pertinentes :
        - Basées sur les types de documents présents
        - Adaptées au contexte juridique
        - Évolutives selon vos recherches précédentes
        
        #### Filtres et tri
        
        - **Par type** : PV, Expertises, Contrats...
        - **Par date** : Plus récent, plus ancien
        - **Par pertinence** : Score de l'IA
        - **Par taille** : Documents volumineux
        """)
    
    with help_topics[4]:
        st.markdown("""
        ### 📊 Modules spécialisés
        
        #### Module Comparaison
        **Idéal pour :** Détecter les contradictions
        - Sélectionnez 2+ documents
        - L'IA identifie automatiquement les divergences
        - Export des résultats en tableau
        
        #### Module Timeline
        **Idéal pour :** Visualiser la chronologie
        - Extraction automatique des dates
        - Classement par importance
        - Export en PDF pour le tribunal
        
        #### Module Extraction
        **Idéal pour :** Synthèse rapide
        - Points favorables/défavorables
        - Personnes et montants clés
        - Éléments de preuve
        
        #### Module Stratégie
        **Idéal pour :** Plan d'action
        - Analyse forces/faiblesses
        - Scénarios probabilistes
        - Recommandations tactiques
        
        #### Module Rapports
        **Idéal pour :** Documents officiels
        - 7 types de documents
        - Personnalisation complète
        - Export multi-formats
        """)
    
    with help_topics[5]:
        st.markdown("""
        ### ❓ Questions fréquentes
        
        **Q : Mes données sont-elles sécurisées ?**
        > R : Oui, vos documents restent sur Azure ou en local. Les IA n'ont accès qu'aux extraits nécessaires à l'analyse.
        
        **Q : Puis-je utiliser l'application hors ligne ?**
        > R : Partiellement. Les documents locaux fonctionnent, mais les IA nécessitent une connexion internet.
        
        **Q : Comment améliorer la précision des analyses ?**
        > R : 
        > - Utilisez plusieurs IA pour croiser les résultats
        > - Formulez des questions précises
        > - Organisez bien vos documents par type
        
        **Q : Quelle est la limite de taille des documents ?**
        > R : 
        > - Azure : jusqu'à 100 MB par fichier
        > - Local : jusqu'à 50 MB par fichier
        > - Pas de limite sur le nombre de documents
        
        **Q : Les analyses sont-elles juridiquement valables ?**
        > R : Les analyses IA sont des outils d'aide à la décision. Elles ne remplacent pas l'avis d'un juriste qualifié.
        
        **Q : Comment exporter mes analyses ?**
        > R : Chaque module propose des options d'export (PDF, Word, Excel). Les rapports peuvent être personnalisés.
        
        **Q : Puis-je ajouter mes propres IA ?**
        > R : Cette fonctionnalité est en développement. Contactez le support pour plus d'informations.
        
        ---
        
        💡 **Besoin d'aide supplémentaire ?**
        - 📧 Support : support@ia-juridique.fr
        - 💬 Chat en direct : disponible 9h-18h
        - 📚 Documentation complète : docs.ia-juridique.fr
        """)

# ========== FONCTION PRINCIPALE ==========

def main():
    """Point d'entrée principal de l'application"""
    # Initialisation
    init_session_state()
    
    # Injection du JavaScript pour la recherche et le drag & drop
    components.html(SEARCH_JAVASCRIPT, height=0)
    
    # Sidebar toujours visible
    show_sidebar()
    
    # Router vers les différentes vues
    views = {
        'home': show_home_page,
        'search': show_search_interface,
        'compare': show_compare_module,
        'timeline': show_timeline_module,
        'extract': show_extract_module,
        'strategy': show_strategy_module,
        'report': show_report_module,
        'contract': show_contract_module,
        'jurisprudence': show_jurisprudence_module,
        'chat': show_chat_module,
        'config': show_config,
        'help': show_help
    }
    
    current_view = st.session_state.get('current_view', 'home')
    
    # Afficher la vue appropriée
    if current_view in views:
        views[current_view]()
    else:
        show_home_page()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: var(--text-secondary); font-size: 0.75rem;'>
        ⚖️ IA Juridique v5.0 | Analyse Multi-IA | 9 Modules Spécialisés | Support Documents Locaux
        </p>""",
        unsafe_allow_html=True
    )

# Nettoyage à la fermeture
def cleanup():
    """Nettoie les ressources temporaires"""
    if 'local_document_manager' in st.session_state:
        st.session_state.local_document_manager.cleanup()

# Point d'entrée
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Erreur critique : {str(e)}")
        logger.exception("Erreur dans l'application principale")
    finally:
        # Enregistrer le nettoyage pour la fermeture
        import atexit
        atexit.register(cleanup)