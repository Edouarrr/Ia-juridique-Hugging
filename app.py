"""Application principale avec Azure Blob Storage, Search et OpenAI - Version complète intégrée"""

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

# ========== TYPES DE DOCUMENTS JURIDIQUES ==========

DOCUMENT_TYPES = {
    'pv': {
        'name': 'Procès-verbaux',
        'icon': '📝',
        'patterns': ['pv', 'proces-verbal', 'audition', 'interrogatoire', 'garde-a-vue'],
        'extensions': ['.pdf', '.docx'],
        'color': '#e74c3c'
    },
    'expertise': {
        'name': 'Expertises',
        'icon': '🔬',
        'patterns': ['expertise', 'expert', 'rapport', 'analyse', 'exp-'],
        'extensions': ['.pdf', '.docx'],
        'color': '#3498db'
    },
    'contrat': {
        'name': 'Contrats',
        'icon': '📄',
        'patterns': ['contrat', 'convention', 'accord', 'avenant'],
        'extensions': ['.pdf', '.docx'],
        'color': '#2ecc71'
    },
    'facture': {
        'name': 'Factures',
        'icon': '🧾',
        'patterns': ['facture', 'devis', 'bon-commande', 'bc', 'fact-'],
        'extensions': ['.pdf', '.xlsx', '.xls'],
        'color': '#f39c12'
    },
    'courrier': {
        'name': 'Correspondances',
        'icon': '✉️',
        'patterns': ['lettre', 'courrier', 'mail', 'email', 'correspondance'],
        'extensions': ['.pdf', '.docx', '.msg', '.eml'],
        'color': '#9b59b6'
    },
    'piece_saisie': {
        'name': 'Pièces saisies',
        'icon': '🔍',
        'patterns': ['scel', 'scelle', 'saisie', 'perquisition'],
        'extensions': ['.pdf', '.jpg', '.png'],
        'color': '#e67e22'
    },
    'procedure': {
        'name': 'Procédures',
        'icon': '⚖️',
        'patterns': ['proc-', 'procedure', 'ordonnance', 'requisitoire', 'jugement', 'arret'],
        'extensions': ['.pdf'],
        'color': '#34495e'
    },
    'autre': {
        'name': 'Autres',
        'icon': '📁',
        'patterns': [],
        'extensions': [],
        'color': '#7f8c8d'
    }
}

def detect_document_type(filename: str) -> str:
    """Détecte le type de document basé sur le nom et l'extension"""
    filename_lower = filename.lower()
    
    # Vérifier chaque type de document
    for doc_type, config in DOCUMENT_TYPES.items():
        if doc_type == 'autre':
            continue
            
        # Vérifier les patterns dans le nom
        for pattern in config['patterns']:
            if pattern in filename_lower:
                return doc_type
        
        # Vérifier l'extension si aucun pattern trouvé
        for ext in config['extensions']:
            if filename_lower.endswith(ext):
                # Vérification secondaire sur le contenu du nom
                for pattern in config['patterns']:
                    if pattern in filename_lower:
                        return doc_type
    
    return 'autre'

def get_documents_by_type(documents: List[Dict]) -> Dict[str, List[Dict]]:
    """Groupe les documents par type"""
    documents_by_type = {doc_type: [] for doc_type in DOCUMENT_TYPES.keys()}
    
    for doc in documents:
        # Déterminer le type basé sur le nom ou la catégorie existante
        if isinstance(doc, dict):
            if 'ref' in doc:  # Document fictif existant
                # Mapper les catégories existantes
                if any(cat in str(doc.get('ref', '')).upper() for cat in ['PV']):
                    doc_type = 'pv'
                elif any(cat in str(doc.get('ref', '')).upper() for cat in ['EXP']):
                    doc_type = 'expertise'
                elif any(cat in str(doc.get('ref', '')).upper() for cat in ['SCEL']):
                    doc_type = 'piece_saisie'
                elif any(cat in str(doc.get('ref', '')).upper() for cat in ['PROC']):
                    doc_type = 'procedure'
                else:
                    doc_type = detect_document_type(doc.get('titre', ''))
            else:  # Document Azure réel
                doc_type = detect_document_type(doc.get('name', ''))
            
            doc['document_type'] = doc_type
            documents_by_type[doc_type].append(doc)
    
    return documents_by_type

# ========== GESTIONNAIRE AZURE BLOB STORAGE (CORRIGÉ) ==========

class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage avec correction de l'erreur max_results"""
    
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
            # Test de connexion sans max_results
            try:
                # Tenter de lister un conteneur pour vérifier la connexion
                containers = list(self.blob_service_client.list_containers())
                self.connected = True
                logger.info(f"✅ Azure Blob connecté - {len(containers)} conteneurs trouvés")
            except StopIteration:
                # Pas de conteneurs mais connexion OK
                self.connected = True
                logger.info("✅ Azure Blob connecté - Aucun conteneur")
        except Exception as e:
            self.connection_error = str(e)
            logger.error(f"❌ Erreur connexion Azure Blob: {e}")
    
    def is_connected(self):
        return self.connected
    
    def list_containers(self):
        """Liste tous les conteneurs sans utiliser max_results"""
        if not self.connected:
            return []
        try:
            containers = []
            # Utiliser list() pour convertir l'itérateur en liste
            for container in self.blob_service_client.list_containers():
                containers.append(container.name)
            return containers
        except Exception as e:
            logger.error(f"Erreur liste conteneurs: {e}")
            return []
    
    def list_blobs(self, container_name: str, prefix: str = ""):
        """Liste les blobs dans un conteneur"""
        if not self.connected:
            return []
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = []
            
            # Utiliser name_starts_with au lieu de prefix
            blob_list = container_client.list_blobs(name_starts_with=prefix) if prefix else container_client.list_blobs()
            
            for blob in blob_list:
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
        """Télécharge un blob"""
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
        """Upload un blob"""
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
        """Recherche de documents avec support du type"""
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
                    'document_type': result.get('document_type', 'autre'),
                    'score': result.get('@search.score'),
                    'highlights': result.get('@search.highlights', {})
                })
            
            return results
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    def _build_filter(self, filters: Dict) -> str:
        """Construit un filtre OData avec support du type de document"""
        filter_parts = []
        
        if 'container' in filters:
            filter_parts.append(f"container eq '{filters['container']}'")
        
        if 'document_type' in filters:
            filter_parts.append(f"document_type eq '{filters['document_type']}'")
        
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
            # Test simple sans appeler models.list()
            self.connected = True
            logger.info("✅ Azure OpenAI configuré")
        except Exception as e:
            self.connection_error = str(e)
            logger.error(f"❌ Erreur configuration Azure OpenAI: {e}")
    
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

# ========== CONFIGURATION DES IA DISPONIBLES ==========

def get_available_ais():
    """Retourne les IA disponibles selon la configuration"""
    ais = {
        "GPT-3.5": {"icon": "🤖", "description": "Analyse rapide des pièces procédurales"},
        "GPT-4": {"icon": "🧠", "description": "Analyse approfondie et contradictions dans les pièces"},
        "Claude Opus 4": {"icon": "🎭", "description": "Argumentation basée sur les pièces du dossier"},
        "Gemini": {"icon": "✨", "description": "Recherche exhaustive dans toutes les pièces"},
        "Mistral": {"icon": "🌟", "description": "Analyse juridique des pièces françaises"}
    }
    
    # Ajouter Azure OpenAI si disponible et activé
    if AZURE_OPENAI_AVAILABLE and st.session_state.get('azure_openai_enabled', False):
        azure_openai_manager = st.session_state.get('azure_openai_manager')
        if azure_openai_manager and azure_openai_manager.is_connected():
            ais["Azure OpenAI"] = {
                "icon": "☁️", 
                "description": "IA sécurisée Microsoft", 
            }
    
    return ais

# Base de données enrichie avec les pièces du dossier (conservée)
DOSSIERS_CLIENTS = {
    "lesueur": {
        "info": {
            "nom": "M. Lesueur",
            "affaire": "ABS SAS TechFinance", 
            "qualification": "Abus de biens sociaux - Art. 314-1",
            "statut": "Mis en examen",
            "audience": "15/02/2024 - Tribunal correctionnel",
            "montant": "450 000 €"
        },
        "pieces": {
            "PV": [
                {"ref": "PV-001", "titre": "PV audition garde à vue Lesueur", "date": "10/01/2024", "pages": 45},
                {"ref": "PV-002", "titre": "PV perquisition siège social", "date": "08/01/2024", "pages": 23},
                {"ref": "PV-003", "titre": "PV audition comptable société", "date": "12/01/2024", "pages": 18}
            ],
            "Expertises": [
                {"ref": "EXP-001", "titre": "Rapport expertise comptable", "date": "20/01/2024", "pages": 156},
                {"ref": "EXP-002", "titre": "Analyse flux financiers 2022-2023", "date": "22/01/2024", "pages": 89}
            ],
            "Documents_saisis": [
                {"ref": "SCEL-001", "titre": "Relevés bancaires SAS TechFinance", "periode": "2022-2023", "pages": 234},
                {"ref": "SCEL-002", "titre": "Factures litigieuses", "nombre": 47, "pages": 94},
                {"ref": "SCEL-003", "titre": "Contrats prestations fictives", "nombre": 12, "pages": 156},
                {"ref": "SCEL-004", "titre": "Emails direction", "nombre": 1247, "pages": 890}
            ],
            "Procedures": [
                {"ref": "PROC-001", "titre": "Ordonnance de mise en examen", "date": "15/01/2024", "pages": 8},
                {"ref": "PROC-002", "titre": "Réquisitoire supplétif", "date": "25/01/2024", "pages": 12}
            ]
        }
    },
    "martin": {
        "info": {
            "nom": "Mme Martin",
            "affaire": "Blanchiment réseau crypto",
            "qualification": "Blanchiment aggravé - Art. 324-1",
            "statut": "Témoin assisté", 
            "audience": "20/02/2024 - Juge d'instruction",
            "montant": "2.3 M€"
        },
        "pieces": {
            "PV": [
                {"ref": "PV-101", "titre": "PV audition libre Martin", "date": "05/01/2024", "pages": 28},
                {"ref": "PV-102", "titre": "PV exploitation données blockchain", "date": "15/01/2024", "pages": 167}
            ],
            "Expertises": [
                {"ref": "EXP-101", "titre": "Rapport TRACFIN", "date": "01/12/2023", "pages": 43},
                {"ref": "EXP-102", "titre": "Expertise crypto-actifs", "date": "18/01/2024", "pages": 78}
            ],
            "Documents_saisis": [
                {"ref": "SCEL-101", "titre": "Wallets crypto identifiés", "nombre": 23, "pages": 145},
                {"ref": "SCEL-102", "titre": "Virements SEPA suspects", "nombre": 156, "pages": 312}
            ],
            "Procedures": [
                {"ref": "PROC-101", "titre": "Convocation témoin assisté", "date": "10/01/2024", "pages": 3}
            ]
        }
    },
    "dupont": {
        "info": {
            "nom": "M. Dupont", 
            "affaire": "Corruption marché public BTP",
            "qualification": "Corruption active agent public",
            "statut": "Mis en examen",
            "audience": "25/02/2024 - Chambre de l'instruction",
            "montant": "1.8 M€"
        },
        "pieces": {
            "PV": [
                {"ref": "PV-201", "titre": "PV interpellation Dupont", "date": "03/01/2024", "pages": 15},
                {"ref": "PV-202", "titre": "PV écoutes téléphoniques", "date": "Déc 2023", "pages": 456}
            ],
            "Expertises": [
                {"ref": "EXP-201", "titre": "Analyse marchés publics truqués", "date": "20/01/2024", "pages": 234}
            ],
            "Documents_saisis": [
                {"ref": "SCEL-201", "titre": "Cahiers des charges modifiés", "nombre": 8, "pages": 89},
                {"ref": "SCEL-202", "titre": "Versements occultes", "nombre": 34, "pages": 67}
            ],
            "Procedures": [
                {"ref": "PROC-201", "titre": "Commission rogatoire internationale", "date": "15/01/2024", "pages": 23}
            ]
        }
    }
}

# ========== FUSION DES DOCUMENTS AZURE ET FICTIFS ==========

def get_merged_clients_data():
    """Fusionne les dossiers clients fictifs avec les vrais dossiers Azure"""
    merged_data = dict(DOSSIERS_CLIENTS)  # Copie des données fictives
    
    # Si Azure est connecté, ajouter les vrais dossiers
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        
        for container in containers:
            # Éviter les doublons
            container_key = container.lower().replace('-', '_').replace(' ', '_')
            if container_key not in merged_data:
                # Récupérer les blobs
                blobs = blob_manager.list_blobs(container)
                
                # Organiser par type
                pieces_by_category = {}
                for blob in blobs:
                    doc_type = detect_document_type(blob['name'])
                    category = DOCUMENT_TYPES[doc_type]['name']
                    
                    if category not in pieces_by_category:
                        pieces_by_category[category] = []
                    
                    pieces_by_category[category].append({
                        "ref": f"AZ-{len(pieces_by_category[category])+1:03d}",
                        "titre": blob['name'],
                        "date": blob['last_modified'].strftime("%d/%m/%Y") if blob['last_modified'] else "N/A",
                        "pages": "N/A",
                        "azure_path": f"{container}/{blob['name']}",
                        "size": blob['size']
                    })
                
                # Créer l'entrée du client
                merged_data[container_key] = {
                    "info": {
                        "nom": container.title(),
                        "affaire": f"Dossier Azure - {container}",
                        "qualification": "À déterminer",
                        "statut": "En cours",
                        "audience": "Non définie",
                        "montant": "N/A",
                        "source": "azure"
                    },
                    "pieces": pieces_by_category
                }
    
    return merged_data

# Suggestions de prompts basées sur les pièces (conservée)
def generate_piece_based_prompts(client_key, pieces):
    """Génère des prompts basés sur les pièces du dossier"""
    prompts = []
    
    # Adaptation pour gérer les deux formats (fictif et Azure)
    for category, items in pieces.items():
        if items and len(items) > 0:
            # Prompts génériques basés sur la catégorie
            if 'PV' in category or 'Procès' in category:
                prompts.append(f"Analyser contradictions dans les procès-verbaux")
                prompts.append(f"Identifier points faibles des PV")
            elif 'Expert' in category:
                prompts.append(f"Contester conclusions des expertises")
                prompts.append(f"Extraire éléments favorables des rapports")
            elif 'saisi' in category.lower():
                prompts.append(f"Analyser pièces saisies pour éléments à décharge")
                prompts.append(f"Vérifier authenticité des documents saisis")
    
    # Prompts spécifiques si pièces identifiées
    for category, items in pieces.items():
        if items:
            for item in items[:2]:  # Limiter à 2 par catégorie
                titre = item.get('titre', 'Document')
                ref = item.get('ref', 'REF')
                prompts.append(f"Analyser {titre} ({ref})")
    
    return prompts[:8]  # Limiter le nombre total

# Questions basées sur les pièces pour la préparation (conservée et adaptée)
def generate_piece_based_questions(module_theme, pieces, client_info):
    """Génère des questions basées sur les pièces spécifiques du dossier"""
    questions = []
    
    # Questions génériques adaptables
    for category, items in pieces.items():
        if items:
            if 'PV' in category or 'procès' in category.lower():
                for item in items[:2]:
                    questions.append(f"❓ Dans {item.get('titre', 'le document')} ({item.get('ref', 'REF')}), comment expliquez-vous les faits mentionnés ?")
            
            elif 'expert' in category.lower():
                for item in items[:1]:
                    questions.append(f"❓ Le rapport {item.get('titre', 'expertise')} soulève des questions. Quelle est votre position ?")
            
            elif 'saisi' in category.lower():
                for item in items[:1]:
                    questions.append(f"❓ Les documents saisis ({item.get('ref', 'REF')}) nécessitent des explications. Qu'en dites-vous ?")
    
    return questions[:6]  # Limiter le nombre

# ========== FONCTION CSS OPTIMISÉE ==========
def load_custom_css():
    st.markdown("""
    <style>
    /* Variables CSS adaptées au pénal des affaires */
    :root {
        --primary-color: #1a1a2e;
        --secondary-color: #16213e;
        --accent-color: #e94560;
        --success-color: #0f3460;
        --warning-color: #f39c12;
        --danger-color: #c0392b;
        --text-primary: #2c3e50;
        --text-secondary: #7f8c8d;
        --border-color: #bdc3c7;
        --hover-color: #ecf0f1;
        --background-light: #f8f9fa;
        --ai-selected: #e94560;
        --ai-hover: #c0392b;
        --penal-bg: #fef5f5;
        --client-bg: #e8f5e9;
        --piece-bg: #fff3cd;
        --azure-color: #0078d4;
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
    
    /* Pièces du dossier */
    .piece-card {
        background: var(--piece-bg);
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 10px;
        margin: 5px 0;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .piece-card:hover {
        background: #ffe69c;
        transform: translateX(3px);
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
    }
    
    .piece-card.azure {
        border-color: var(--azure-color);
        background: #f0f8ff;
    }
    
    .piece-card.azure:hover {
        background: #e0f0ff;
        box-shadow: 0 2px 8px rgba(0, 120, 212, 0.3);
    }
    
    .piece-ref {
        font-weight: 700;
        color: var(--danger-color);
        margin-right: 8px;
    }
    
    .piece-pages {
        float: right;
        color: var(--text-secondary);
        font-size: 0.8rem;
    }
    
    /* Container pièces */
    .pieces-container {
        background: white;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .pieces-category {
        font-weight: 600;
        color: var(--accent-color);
        margin: 10px 0 5px 0;
        font-size: 0.9rem;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 3px;
    }
    
    /* Type filters */
    .type-filter-card {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .type-header {
        margin: 20px 0 10px 0;
        padding: 10px;
        border-radius: 5px;
    }
    
    /* Layout ultra-compact */
    .block-container {
        padding-top: 0.5rem !important;
        max-width: 1600px !important;
    }
    
    /* Typography compacte */
    h1 { font-size: 1.4rem !important; margin-bottom: 0.3rem !important; }
    h2 { font-size: 1.2rem !important; margin-bottom: 0.3rem !important; }
    h3 { font-size: 1.05rem !important; margin-bottom: 0.3rem !important; }
    h4 { font-size: 0.95rem !important; margin-bottom: 0.3rem !important; }
    h5 { font-size: 0.85rem !important; margin-bottom: 0.3rem !important; }
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
        'current_client': None,
        'selected_pieces': [],
        'azure_blob_manager': None,
        'azure_search_manager': None,
        'azure_openai_manager': None,
        'azure_initialized': False,
        'azure_openai_enabled': False,
        'azure_search_enabled': True,
        'document_type_filters': list(DOCUMENT_TYPES.keys()),
        'merged_clients': {},
        'search_results': []
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
    
    # Mettre à jour les clients fusionnés
    st.session_state.merged_clients = get_merged_clients_data()
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

# ========== AFFICHAGE DES PIÈCES AVEC FILTRES ==========

def display_dossier_pieces_with_filters(client_key):
    """Affiche les pièces disponibles dans le dossier avec filtres par type"""
    clients_data = st.session_state.get('merged_clients', get_merged_clients_data())
    
    if client_key not in clients_data:
        return
    
    pieces = clients_data[client_key]["pieces"]
    client_info = clients_data[client_key]["info"]
    
    # Convertir les pièces en liste plate pour le filtrage
    all_pieces = []
    for category, items in pieces.items():
        for item in items:
            item['category'] = category
            all_pieces.append(item)
    
    # Grouper par type de document
    pieces_by_type = get_documents_by_type(all_pieces)
    
    # Stats des pièces
    total_pieces = len(all_pieces)
    total_pages = sum(p.get('pages', 0) if p.get('pages') != 'N/A' else 0 for p in all_pieces)
    
    # Stats par type
    st.markdown(f"""
    <div class="pieces-stats">
        <span class="piece-stat">📁 {total_pieces} pièces</span>
        <span class="piece-stat">📄 {total_pages} pages</span>
        <span class="piece-stat">💰 {client_info['montant']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtres par type
    st.markdown("#### 🔍 Filtrer par type")
    
    filter_cols = st.columns(len([t for t, docs in pieces_by_type.items() if docs]))
    active_types = []
    
    for idx, (doc_type, docs) in enumerate(pieces_by_type.items()):
        if docs:
            with filter_cols[idx % len(filter_cols)]:
                config = DOCUMENT_TYPES[doc_type]
                is_active = doc_type in st.session_state.document_type_filters
                
                if st.button(
                    f"{config['icon']} {config['name']} ({len(docs)})",
                    key=f"filter_{doc_type}_{client_key}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True
                ):
                    if doc_type in st.session_state.document_type_filters:
                        st.session_state.document_type_filters.remove(doc_type)
                    else:
                        st.session_state.document_type_filters.append(doc_type)
                    st.rerun()
            
            if is_active:
                active_types.append(doc_type)
    
    # Container des pièces filtrées
    st.markdown('<div class="pieces-container">', unsafe_allow_html=True)
    
    # Affichage par type actif
    displayed_count = 0
    for doc_type in active_types:
        if doc_type in pieces_by_type and pieces_by_type[doc_type]:
            config = DOCUMENT_TYPES[doc_type]
            
            st.markdown(f"""
            <div class="pieces-category" style="color: {config['color']};">
                {config['icon']} {config['name']}
            </div>
            """, unsafe_allow_html=True)
            
            for piece in pieces_by_type[doc_type]:
                piece_id = f"{client_key}_{piece.get('ref', 'REF')}"
                selected = piece_id in st.session_state.selected_pieces
                is_azure = 'azure_path' in piece
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    piece_class = "piece-card azure" if is_azure else "piece-card"
                    st.markdown(f"""
                    <div class="{piece_class}">
                        <span class="piece-ref">{piece.get('ref', 'REF')}</span>
                        {piece.get('titre', 'Document')}
                        <span class="piece-pages">{piece.get('pages', 'N/A')} pages</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    unique_key = f"select_{piece_id}_{uuid.uuid4().hex[:8]}"
                    if st.checkbox("", key=unique_key, value=selected):
                        if piece_id not in st.session_state.selected_pieces:
                            st.session_state.selected_pieces.append(piece_id)
                    else:
                        if piece_id in st.session_state.selected_pieces:
                            st.session_state.selected_pieces.remove(piece_id)
                
                displayed_count += 1
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if displayed_count == 0:
        st.info("Aucune pièce ne correspond aux filtres sélectionnés")

# ========== BARRE DE RECHERCHE AVEC AZURE SEARCH ==========

def create_smart_search_with_pieces():
    """Barre de recherche intégrant les pièces du dossier et Azure Search"""
    
    # JavaScript pour détection @client (conservé)
    search_js = """
    <script>
    function setupPieceAwareSearch() {
        const checkTextarea = setInterval(function() {
            const textarea = document.querySelector('textarea[aria-label="main_search_pieces"]');
            if (textarea) {
                clearInterval(checkTextarea);
                
                let debounceTimer;
                
                textarea.addEventListener('input', function(event) {
                    clearTimeout(debounceTimer);
                    const value = textarea.value;
                    
                    if (value.startsWith('@')) {
                        textarea.style.borderColor = '#ffc107';
                        textarea.style.backgroundColor = '#fff3cd';
                        textarea.style.borderWidth = '2px';
                    } else {
                        textarea.style.borderColor = '';
                        textarea.style.backgroundColor = '';
                        textarea.style.borderWidth = '';
                    }
                    
                    debounceTimer = setTimeout(() => {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(textarea, value);
                        const inputEvent = new Event('input', { bubbles: true });
                        textarea.dispatchEvent(inputEvent);
                    }, 300);
                });
                
                textarea.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        const buttons = document.querySelectorAll('button');
                        buttons.forEach(button => {
                            if (button.textContent.includes('Analyser')) {
                                button.click();
                            }
                        });
                    }
                });
                
                textarea.focus();
            }
        }, 100);
    }
    
    setupPieceAwareSearch();
    const observer = new MutationObserver(setupPieceAwareSearch);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    # Azure Search si activé
    search_manager = st.session_state.get('azure_search_manager')
    if st.session_state.azure_search_enabled and search_manager and search_manager.is_connected():
        st.markdown("### 🔍 Recherche avancée avec Azure Search")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Rechercher dans tous les documents",
                placeholder="Ex: contrat de vente, procès-verbal, expertise...",
                key="azure_search_query"
            )
        
        with col2:
            if st.button("🔍 Rechercher", type="primary", use_container_width=True):
                if search_query:
                    with st.spinner("Recherche en cours..."):
                        results = search_manager.search_documents(search_query)
                        st.session_state.search_results = results
                        
                        if results:
                            st.success(f"✅ {len(results)} résultats trouvés")
                            # Afficher les résultats
                            for result in results[:5]:
                                st.markdown(f"""
                                **📄 {result['title']}**  
                                📁 {result['container']} | Score: {result['score']:.2f}  
                                {result['content'][:200]}...
                                """)
                        else:
                            st.warning("Aucun résultat trouvé")
        
        st.markdown("---")
    
    # Détection du client
    query = st.session_state.get('search_query', '')
    client_detected = False
    client_key = None
    
    clients_data = st.session_state.get('merged_clients', get_merged_clients_data())
    
    if query.startswith("@"):
        parts = query[1:].split(",", 1)
        potential_client = parts[0].strip().lower()
        if potential_client in clients_data:
            client_detected = True
            client_key = potential_client
            st.session_state.current_client = client_key
    
    # Container avec style adaptatif
    container_class = "search-container client-mode" if client_detected else "search-container"
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    # Affichage selon le mode
    if client_detected:
        client_info = clients_data[client_key]["info"]
        st.markdown(f"### 📁 Dossier {client_info['nom']} - {client_info['affaire']}")
        
        # Affichage des pièces avec filtres
        with st.expander("📂 Pièces du dossier", expanded=True):
            display_dossier_pieces_with_filters(client_key)
    else:
        st.markdown("### 🔍 Recherche intelligente avec analyse des pièces")
    
    # Zone de recherche
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Liste des clients disponibles
        available_clients = ", ".join([f"@{k}" for k in clients_data.keys()][:5])
        
        query = st.text_area(
            "main_search_pieces",
            placeholder=(
                f"Clients disponibles : {available_clients}...\n\n"
                "Exemples :\n"
                "• @lesueur, analyser contradictions PV-001 vs EXP-001\n"
                "• @martin, préparer défense sur SCEL-101\n"
                "• Recherche générale dans tous les documents"
            ),
            height=80,
            key="search_query",
            label_visibility="hidden"
        )
    
    with col2:
        st.write("")
        if st.button("🤖 Analyser", type="primary", use_container_width=True):
            if query:
                st.session_state.current_view = "analyze_with_pieces"
                st.rerun()
    
    # Suggestions basées sur les pièces
    if client_detected and client_key:
        pieces = clients_data[client_key]["pieces"]
        
        st.markdown("#### 💡 Analyses suggérées basées sur les pièces")
        
        # Générer des prompts basés sur les pièces
        piece_prompts = generate_piece_based_prompts(client_key, pieces)
        
        prompt_key_counter = 0
        for prompt in piece_prompts[:5]:
            prompt_key_counter += 1
            unique_key = f"pp_{client_key}_{prompt_key_counter}_{uuid.uuid4().hex[:8]}"
            if st.button(f"→ {prompt}", key=unique_key, use_container_width=True):
                st.session_state.search_query = f"@{client_key}, {prompt}"
                st.rerun()
        
        # Actions rapides sur pièces sélectionnées
        if st.session_state.selected_pieces:
            st.markdown("#### ⚡ Actions sur pièces sélectionnées")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Analyser contradictions", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, analyser contradictions dans {', '.join(st.session_state.selected_pieces)}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()
            with col2:
                if st.button("📋 Synthétiser", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, synthétiser {', '.join(st.session_state.selected_pieces)}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()
            with col3:
                if st.button("⚖️ Stratégie défense", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, stratégie défense basée sur {', '.join(st.session_state.selected_pieces)}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Injecter JavaScript
    components.html(search_js, height=0)
    
    return query

# ========== MODULE DE PRÉPARATION (conservé et adapté) ==========

def show_preparation_with_pieces():
    """Préparation client basée sur les pièces du dossier"""
    if not st.session_state.current_client:
        st.warning("Aucun client sélectionné")
        return
    
    client_key = st.session_state.current_client
    clients_data = st.session_state.get('merged_clients', get_merged_clients_data())
    
    if client_key not in clients_data:
        st.error("Client non trouvé")
        return
    
    client = clients_data[client_key]["info"]
    pieces = clients_data[client_key]["pieces"]
    
    st.markdown(f"## 👔 Préparation de {client['nom']} - Basée sur les pièces")
    
    # Rappel du dossier
    st.markdown(f"""
    <div class="preparation-card">
        <strong>📁 Affaire :</strong> {client['affaire']}<br>
        <strong>⚖️ Qualification :</strong> {client['qualification']}<br>
        <strong>📅 Audience :</strong> {client['audience']}<br>
        <strong>💰 Enjeu :</strong> {client['montant']}
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection IA
    create_ai_selector_mini()
    
    st.markdown("---")
    
    # Modules de préparation
    modules = {
        "questions_pieces": "Questions sur les pièces du dossier",
        "contradictions": "Contradictions entre pièces", 
        "elements_defense": "Éléments favorables dans les pièces",
        "strategie_pieces": "Stratégie basée sur les pièces"
    }
    
    for module_key, module_title in modules.items():
        with st.expander(f"📋 {module_title}", expanded=module_key=="questions_pieces"):
            
            if st.button(f"🤖 Générer avec IA", key=f"gen_{module_key}"):
                if not st.session_state.selected_ais:
                    st.warning("Sélectionnez au moins une IA")
                else:
                    with st.spinner(f"Analyse des pièces par {len(st.session_state.selected_ais)} IA..."):
                        time.sleep(1.5)
                    
                    if module_key == "questions_pieces":
                        # Questions basées sur les vraies pièces
                        questions = generate_piece_based_questions("questions sur pièces", pieces, client)
                        
                        for q in questions[:6]:
                            st.markdown(f"""
                            <div class="question-with-piece">
                                {q}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Conseils spécifiques
                        st.success("""
                        💡 **Conseils pour répondre sur les pièces :**
                        • Relisez les passages cités avant l'audience
                        • Préparez des explications cohérentes avec l'ensemble du dossier
                        • N'hésitez pas à demander à consulter la pièce pendant l'audience
                        • Restez cohérent avec vos déclarations antérieures
                        """)
                    
                    elif module_key == "contradictions":
                        st.markdown("""
                        <div class="ai-response-container">
                            <h4>⚠️ Contradictions identifiées</h4>
                            <p>Analyse basée sur les documents du dossier...</p>
                            <p><strong>Stratégie :</strong> Préparer des explications cohérentes pour chaque contradiction</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif module_key == "elements_defense":
                        st.markdown(f"""
                        <div class="ai-response-container">
                            <h4>✅ Éléments favorables identifiés</h4>
                            <p>Analyse des pièces en cours...</p>
                            <p><strong>À exploiter :</strong> Insister sur ces éléments pendant l'audience</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Notes sur les pièces
            notes = st.text_area(
                f"Notes sur les pièces ({module_key})",
                key=f"notes_{module_key}",
                placeholder="Points clés des pièces à retenir...",
                height=80
            )
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Générer mémo pièces", type="primary", use_container_width=True):
            st.success("Mémo des pièces clés généré")
    
    with col2:
        if st.button("🎯 Simulation avec pièces", use_container_width=True):
            st.info("Simulation basée sur les pièces...")
    
    with col3:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.rerun()

# ========== ANALYSE AVEC AZURE OPENAI ==========

def analyze_query_with_pieces():
    """Analyse une requête en se basant sur les pièces du dossier"""
    query = st.session_state.search_query
    
    if not st.session_state.selected_ais:
        st.warning("Sélectionnez au moins une IA")
        return
    
    # Extraire le client et la commande
    client_key = st.session_state.current_client
    clients_data = st.session_state.get('merged_clients', get_merged_clients_data())
    
    if not client_key and query.startswith("@"):
        parts = query[1:].split(",", 1)
        potential_client = parts[0].strip().lower()
        if potential_client in clients_data:
            client_key = potential_client
    
    if not client_key:
        st.error("Client non identifié")
        return
    
    client = clients_data[client_key]["info"]
    pieces = clients_data[client_key]["pieces"]
    
    st.markdown(f"### 🤖 Analyse pour {client['nom']}")
    st.markdown(f"**Requête :** {query}")
    st.markdown(f"**IA actives :** {', '.join(st.session_state.selected_ais)}")
    
    # Vérifier si Azure OpenAI est sélectionné et actif
    use_azure_openai = "Azure OpenAI" in st.session_state.selected_ais and st.session_state.azure_openai_enabled
    openai_manager = st.session_state.get('azure_openai_manager')
    
    if use_azure_openai and openai_manager and openai_manager.is_connected():
        # Analyse réelle avec Azure OpenAI
        with st.spinner(f"Analyse par Azure OpenAI..."):
            # Préparer le contenu des pièces sélectionnées
            selected_content = []
            for piece_id in st.session_state.selected_pieces[:3]:  # Limiter à 3
                # Extraire le contenu si c'est un document Azure
                for cat, items in pieces.items():
                    for item in items:
                        if f"{client_key}_{item.get('ref', '')}" == piece_id:
                            if 'azure_path' in item:
                                # Document Azure réel
                                container, blob_name = item['azure_path'].split('/', 1)
                                content = st.session_state.azure_blob_manager.download_blob(container, blob_name)
                                if content:
                                    selected_content.append({
                                        'ref': item['ref'],
                                        'titre': item['titre'],
                                        'content': content.decode('utf-8', errors='ignore')[:2000]
                                    })
                            else:
                                # Document fictif
                                selected_content.append({
                                    'ref': item['ref'],
                                    'titre': item['titre'],
                                    'content': f"[Contenu fictif de {item['titre']}]"
                                })
            
            # Analyser avec Azure OpenAI
            if selected_content:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                for doc in selected_content:
                    result = loop.run_until_complete(
                        openai_manager.analyze_document(doc['content'], query)
                    )
                    
                    if result:
                        st.markdown(f"""
                        <div class="ai-response-container">
                            <h4>📄 Analyse de {doc['titre']} ({doc['ref']})</h4>
                            <p>{result}</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        # Analyse simulée
        with st.spinner(f"Analyse des pièces du dossier par {len(st.session_state.selected_ais)} IA..."):
            time.sleep(2)
        
        # Réponse basée sur les pièces
        st.markdown(f"""
        <div class="ai-response-container">
            <h4>🔄 Analyse multi-IA basée sur les pièces</h4>
            
            <h5>📁 Pièces analysées :</h5>
            <ul>
        """, unsafe_allow_html=True)
        
        # Lister les pièces analysées
        for piece_id in st.session_state.selected_pieces[:5]:
            st.markdown(f"<li>{piece_id}</li>", unsafe_allow_html=True)
        
        st.markdown("""
            </ul>
            
            <h5>🔍 Analyse :</h5>
            <p>Configuration des APIs LLM requise pour une analyse réelle.</p>
            
            <h5>⚖️ Stratégie recommandée :</h5>
            <ol>
                <li>Analyser les contradictions identifiées</li>
                <li>Exploiter les éléments favorables</li>
                <li>Préparer les réponses aux points faibles</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Actions post-analyse
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📑 Tableau contradictions", use_container_width=True):
            st.info("Génération tableau...")
    
    with col2:
        if st.button("📊 Graphique timeline", use_container_width=True):
            st.info("Création timeline...")
    
    with col3:
        if st.button("✍️ Rédiger conclusions", use_container_width=True):
            st.session_state.current_view = "redaction"
            st.rerun()
    
    with col4:
        if st.button("⬅️ Nouvelle analyse", use_container_width=True):
            st.session_state.current_view = "dashboard"
            st.rerun()

# ========== SÉLECTEUR IA ==========

def create_ai_selector_mini():
    """Sélecteur d'IA compact"""
    st.markdown("#### 🤖 Sélection des IA")
    
    available_ais = get_available_ais()
    
    cols = st.columns(3)
    for idx, (ai_name, ai_info) in enumerate(available_ais.items()):
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
    
    # Mode
    if st.session_state.selected_ais:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Fusion", key="mode_fusion", use_container_width=True,
                        type="primary" if st.session_state.response_mode == "fusion" else "secondary"):
                st.session_state.response_mode = "fusion"
        with col2:
            if st.button("📊 Comparaison", key="mode_comp", use_container_width=True,
                        type="primary" if st.session_state.response_mode == "comparaison" else "secondary"):
                st.session_state.response_mode = "comparaison"
        with col3:
            if st.button("📝 Synthèse", key="mode_synth", use_container_width=True,
                        type="primary" if st.session_state.response_mode == "synthèse" else "secondary"):
                st.session_state.response_mode = "synthèse"

# ========== SIDEBAR ==========

def create_sidebar():
    """Sidebar avec accès rapide aux dossiers"""
    with st.sidebar:
        # Header
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #1a1a2e, #e94560); 
                    margin: -35px -35px 15px -35px; border-radius: 0 0 10px 10px;">
            <h3 style="color: white; margin: 0; font-size: 1.1rem;">⚖️ IA Pénal - Pièces</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Statut Azure
        blob_status = st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.is_connected()
        if blob_status:
            st.success("✅ Azure connecté")
        else:
            st.warning("⚠️ Azure non connecté")
        
        # IA actives
        if st.session_state.selected_ais:
            st.markdown("#### 🤖 IA actives")
            available_ais = get_available_ais()
            ia_list = " • ".join([available_ais[ai]['icon'] for ai in st.session_state.selected_ais if ai in available_ais])
            st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>{ia_list}</div>", unsafe_allow_html=True)
        
        # Dossiers clients avec stats pièces
        st.markdown("---")
        st.markdown("#### 📁 Dossiers actifs")
        
        clients_data = st.session_state.get('merged_clients', get_merged_clients_data())
        
        for client_key, client_data in list(clients_data.items())[:10]:  # Limiter l'affichage
            client = client_data["info"]
            pieces = client_data["pieces"]
            total_pieces = sum(len(items) for items in pieces.values())
            
            # Indicateur Azure
            is_azure = client.get('source') == 'azure'
            icon = "☁️" if is_azure else "📁"
            
            unique_key = f"sidebar_{client_key}_{uuid.uuid4().hex[:8]}"
            
            if st.button(
                f"{icon} {client['nom']} ({total_pieces} pièces)",
                key=unique_key,
                use_container_width=True,
                type="primary" if st.session_state.current_client == client_key else "secondary"
            ):
                st.session_state.search_query = f"@{client_key}, analyser dossier"
                st.session_state.current_client = client_key
                st.session_state.current_view = "dashboard"
                st.rerun()
        
        # Navigation
        st.markdown("---")
        st.markdown("#### 📊 Modules")
        
        modules = [
            ("🏠 Accueil", "dashboard"),
            ("👔 Préparation", "preparation"),
            ("🔍 Analyse pièces", "analyze_pieces"),
            ("✍️ Rédaction", "redaction"),
            ("📊 Statistiques", "stats"),
            ("⚙️ Configuration", "config")
        ]
        
        for label, view in modules:
            if st.button(label, key=f"nav_{view}", use_container_width=True):
                st.session_state.current_view = view
                st.rerun()
        
        # Alertes
        st.markdown("---")
        st.markdown("#### ⚠️ Alertes")
        if blob_status:
            containers = st.session_state.azure_blob_manager.list_containers()
            st.info(f"☁️ {len(containers)} dossiers Azure")
        else:
            st.warning("📄 Mode local uniquement")

# ========== DASHBOARD PRINCIPAL ==========

def show_dashboard():
    """Dashboard avec focus sur les pièces et intégration Azure"""
    
    # Header
    st.markdown("""
    <h1 style="text-align: center; margin: 5px 0;">⚖️ IA Juridique - Analyse des Pièces</h1>
    <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem;">
        Analyse intelligente basée sur les pièces du dossier • 6 IA spécialisées
    </p>
    """, unsafe_allow_html=True)
    
    # Statut Azure si connecté
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        st.info(f"☁️ Azure Blob Storage connecté - {len(containers)} dossiers disponibles")
    
    # Sélecteur IA
    create_ai_selector_mini()
    
    st.markdown("---")
    
    # Barre de recherche avec pièces
    query = create_smart_search_with_pieces()
    
    # Stats globales des pièces
    if not st.session_state.current_client:
        st.markdown("### 📊 Vue d'ensemble des dossiers")
        
        clients_data = st.session_state.get('merged_clients', get_merged_clients_data())
        
        # Séparer dossiers locaux et Azure
        local_clients = {k: v for k, v in clients_data.items() if v['info'].get('source') != 'azure'}
        azure_clients = {k: v for k, v in clients_data.items() if v['info'].get('source') == 'azure'}
        
        # Afficher les dossiers locaux
        if local_clients:
            st.markdown("#### 📁 Dossiers locaux")
            cols = st.columns(min(len(local_clients), 3))
            for idx, (client_key, client_data) in enumerate(list(local_clients.items())[:6]):
                with cols[idx % 3]:
                    client = client_data["info"]
                    pieces = client_data["pieces"]
                    total_pieces = sum(len(items) for items in pieces.values())
                    total_pages = sum(p.get('pages', 0) if p.get('pages') != 'N/A' else 0 for cat in pieces.values() for p in cat)
                    
                    st.markdown(f"""
                    <div class="module-card">
                        <h4>{client['nom']}</h4>
                        <p style="font-size: 0.8rem; margin: 5px 0;">{client['affaire']}</p>
                        <div class="pieces-stats" style="justify-content: center;">
                            <span class="piece-stat" style="font-size: 0.7rem;">📁 {total_pieces}</span>
                            <span class="piece-stat" style="font-size: 0.7rem;">📄 {total_pages}p</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Analyser", key=f"analyze_{client_key}", use_container_width=True):
                        st.session_state.search_query = f"@{client_key}, vue d'ensemble"
                        st.session_state.current_client = client_key
                        st.rerun()
        
        # Afficher les dossiers Azure
        if azure_clients:
            st.markdown("#### ☁️ Dossiers Azure")
            cols = st.columns(min(len(azure_clients), 3))
            for idx, (client_key, client_data) in enumerate(list(azure_clients.items())[:6]):
                with cols[idx % 3]:
                    client = client_data["info"]
                    pieces = client_data["pieces"]
                    total_pieces = sum(len(items) for items in pieces.values())
                    
                    st.markdown(f"""
                    <div class="module-card" style="border: 2px solid #0078d4;">
                        <h4>☁️ {client['nom']}</h4>
                        <p style="font-size: 0.8rem; margin: 5px 0;">{client['affaire']}</p>
                        <div class="pieces-stats" style="justify-content: center;">
                            <span class="piece-stat" style="font-size: 0.7rem;">📁 {total_pieces}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Explorer", key=f"explore_{client_key}", use_container_width=True):
                        st.session_state.search_query = f"@{client_key}, explorer"
                        st.session_state.current_client = client_key
                        st.rerun()
    
    # Actions rapides basées sur les pièces
    if st.session_state.current_client:
        st.markdown("### ⚡ Actions rapides sur les pièces")
        
        quick_cols = st.columns(5)
        actions = [
            ("🔍 Contradictions", "identifier contradictions entre pièces"),
            ("📊 Timeline", "créer timeline avec pièces"),
            ("✅ Éléments favorables", "extraire éléments favorables"),
            ("⚠️ Points faibles", "identifier risques dans pièces"),
            ("📑 Synthèse", "synthétiser toutes les pièces")
        ]
        
        for idx, (label, action) in enumerate(actions):
            with quick_cols[idx]:
                unique_key = f"quick_{action[:10]}_{uuid.uuid4().hex[:8]}"
                if st.button(label, key=unique_key, use_container_width=True):
                    st.session_state.search_query = f"@{st.session_state.current_client}, {action}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()

# ========== PAGE DE CONFIGURATION ==========

def show_config():
    """Page de configuration des services Azure"""
    st.markdown("## ⚙️ Configuration")
    
    # Afficher le statut des services
    display_azure_services_status()
    
    st.markdown("---")
    
    # Instructions de configuration
    with st.expander("📋 Instructions de configuration Azure"):
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
    
    # Bouton de réinitialisation
    if st.button("🔄 Réinitialiser toutes les connexions", type="primary"):
        st.session_state.azure_initialized = False
        init_azure_services()
        st.success("✅ Services réinitialisés")
        time.sleep(1)
        st.rerun()

# ========== ROUTER PRINCIPAL ==========

def main():
    """Point d'entrée principal"""
    
    # Initialisation
    init_session_state()
    load_custom_css()
    
    # Sidebar
    create_sidebar()
    
    # Router
    views = {
        "dashboard": show_dashboard,
        "preparation": show_preparation_with_pieces,
        "analyze_with_pieces": analyze_query_with_pieces,
        "analyze_pieces": lambda: st.info("🔍 Module d'analyse approfondie des pièces en développement"),
        "redaction": lambda: st.info("✍️ Module de rédaction basée sur les pièces en développement"),
        "stats": lambda: st.info("📊 Module de statistiques des pièces en développement"),
        "config": show_config
    }
    
    # Affichage
    current_view = st.session_state.current_view
    if current_view in views:
        views[current_view]()
    else:
        show_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: #95a5a6; font-size: 0.7rem;'>
        ⚖️ IA Juridique Pénal • Analyse basée sur les pièces • Azure Integration • RGPD
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()