import streamlit as st

# PREMIÈRE commande Streamlit OBLIGATOIREMENT
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration de l'encodage pour les emojis
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ================== IMPORTS ET CONFIGURATION ==================

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Vérifier la disponibilité d'Azure
try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    st.warning("⚠️ Modules Azure non disponibles - Fonctionnalités limitées")

import os
import io
from typing import Dict, List, Set, Tuple, Optional, Any
import json
from datetime import datetime, timedelta
import re
import pandas as pd
import base64
import hashlib
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import lru_cache, wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor
import difflib
import plotly.graph_objects as go
import plotly.express as px

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports conditionnels pour les IA
try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ================== CONFIGURATION CENTRALISÉE ==================

class AppConfig:
    """Configuration centralisée de l'application"""
    
    # UI
    PAGE_SIZE = 10
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Prescription
    PRESCRIPTION_CONTRAVENTION = 1  # an
    PRESCRIPTION_DELIT = 6  # ans
    PRESCRIPTION_CRIME = 20  # ans
    
    # Délais spécifiques pénal des affaires
    PRESCRIPTION_FRAUDE_FISCALE = 6  # ans (sauf dissimulation)
    PRESCRIPTION_TRAVAIL_DISSIMULE = 6  # ans
    
    # Export
    EXPORT_FORMAT = "%Y%m%d_%H%M%S"
    
    # Formats de citation
    CITATION_FORMATS = {
        'jurisprudence': "{juridiction}, {date}, n° {numero}",
        'article_code': "Art. {numero} {code}",
        'doctrine': "{auteur}, « {titre} », {revue} {annee}, n° {numero}, p. {page}",
        'circulaire': "Circ. {reference} du {date}",
        'reponse_ministerielle': "Rép. min. n° {numero}, {date}"
    }

# ================== INITIALISATION SESSION STATE ==================

def initialize_session_state():
    """Initialise toutes les variables de session"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.dossier_actif = None
        st.session_state.dossiers = {}
        st.session_state.pieces_selectionnees = {}  # Remplace dossiers
        st.session_state.current_page = 1
        st.session_state.search_query = ""
        st.session_state.docs_for_analysis = []
        st.session_state.document_content = ""
        st.session_state.custom_templates = {}
        st.session_state.letterhead = None
        st.session_state.citation_manager = None
        st.session_state.victimes_adapter = []
        st.session_state.plainte_originale = None
        st.session_state.plaintes_adaptees = {}
        st.session_state.azure_documents = {}
        st.session_state.selected_container = None
        st.session_state.current_folder_path = ""

# ================== ENUMERATIONS ==================

class InfractionAffaires(Enum):
    """Types d'infractions en droit pénal des affaires - Liste non exhaustive"""
    ABS = "Abus de biens sociaux"
    ABUS_CONFIANCE = "Abus de confiance"
    CORRUPTION = "Corruption"
    TRAFIC_INFLUENCE = "Trafic d'influence"
    PRISE_ILLEGALE = "Prise illégale d'intérêts"
    FAVORITISME = "Favoritisme"
    BLANCHIMENT = "Blanchiment"
    FRAUDE_FISCALE = "Fraude fiscale"
    ESCROQUERIE = "Escroquerie"
    FAUX_USAGE_FAUX = "Faux et usage de faux"
    BANQUEROUTE = "Banqueroute"
    DELIT_INITIE = "Délit d'initié"
    MANIPULATION_COURS = "Manipulation de cours"
    ENTRAVE = "Entrave"
    TRAVAIL_DISSIMULE = "Travail dissimulé"
    HARCELEMENT = "Harcèlement moral/sexuel"
    MISE_DANGER = "Mise en danger d'autrui"
    BLESSURES_INVOLONTAIRES = "Blessures involontaires"
    POLLUTION = "Atteinte à l'environnement"
    AUTRE = "Autre infraction"

class SearchMode(Enum):
    """Modes de recherche disponibles"""
    HYBRID = "Recherche hybride (textuelle + sémantique)"
    TEXT_ONLY = "Recherche textuelle uniquement"
    VECTOR_ONLY = "Recherche vectorielle uniquement"
    LOCAL = "Recherche locale uniquement"

class LLMProvider(Enum):
    """Providers LLM disponibles"""
    AZURE_OPENAI = "Azure OpenAI (GPT-4)"
    CLAUDE_OPUS = "Claude Opus 4"
    CHATGPT_4O = "ChatGPT 4o"
    GEMINI = "Google Gemini"
    PERPLEXITY = "Perplexity AI"

# ================== DATACLASSES ==================

@dataclass
class Document:
    """Représente un document juridique"""
    id: str
    title: str
    content: str
    source: str = 'local'
    page_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    folder_path: Optional[str] = None
    selected: bool = False  # Pour la sélection de pièces

@dataclass
class PieceSelectionnee:
    """Pièce sélectionnée pour un dossier"""
    document_id: str
    titre: str
    categorie: str
    date_selection: datetime = field(default_factory=datetime.now)
    notes: str = ""
    pertinence: int = 5  # Score de 1 à 10

# ================== CSS PERSONNALISÉ ==================

st.markdown("""
<style>
    :root {
        --primary-color: #1a237e;
        --secondary-color: #283593;
        --success-color: #2e7d32;
        --warning-color: #f57c00;
        --error-color: #c62828;
    }
    
    .main { 
        background-color: #f5f5f5; 
    }
    
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--secondary-color);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 35, 126, 0.3);
    }
    
    .document-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .document-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .folder-nav {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .search-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .piece-selectionnee {
        background: #e8f5e9;
        border-left: 3px solid var(--success-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .azure-browser {
        background: #f0f7ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ================== UTILITAIRES ==================

def clean_key(text: str) -> str:
    """Nettoie une chaîne pour en faire une clé Streamlit valide"""
    # Remplace les caractères spéciaux
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ô': 'o', 'ö': 'o',
        'î': 'i', 'ï': 'i',
        'ç': 'c',
        ' ': '_',
        '-': '_',
        "'": '_',
        '"': '_',
        '.': '_',
        ',': '_',
        '(': '_',
        ')': '_',
        '[': '_',
        ']': '_',
        '/': '_',
        '\\': '_'
    }
    
    cleaned = text.lower()
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    # Garde uniquement les caractères alphanumériques et underscore
    cleaned = ''.join(c if c.isalnum() or c == '_' else '_' for c in cleaned)
    
    # Supprime les underscores multiples
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Supprime les underscores au début et à la fin
    cleaned = cleaned.strip('_')
    
    return cleaned

# ================== GESTIONNAIRE AZURE BLOB ==================

class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage avec navigation dans les dossiers"""
    
    def __init__(self):
        self.blob_service_client = None
        self.container_client = None
        self._init_blob_client()
    
    def _init_blob_client(self):
        """Initialise le client Azure Blob"""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connection_string and AZURE_AVAILABLE:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                logger.info("Client Azure Blob Storage initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Azure Blob : {e}")
    
    def list_containers(self) -> List[str]:
        """Liste tous les containers disponibles"""
        if not self.blob_service_client:
            return []
        
        try:
            containers = self.blob_service_client.list_containers()
            return [container.name for container in containers]
        except Exception as e:
            logger.error(f"Erreur listing containers : {e}")
            return []
    
    def list_folders(self, container_name: str, prefix: str = "") -> List[Dict[str, Any]]:
        """Liste les dossiers et fichiers dans un chemin donné"""
        if not self.blob_service_client:
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Structure pour stocker l'arborescence
            folders = set()
            files = []
            
            # Lister tous les blobs avec le préfixe
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                # Extraire le chemin relatif
                relative_path = blob.name[len(prefix):] if prefix else blob.name
                parts = relative_path.split('/')
                
                # Si c'est un dossier (a des sous-éléments)
                if len(parts) > 1 and parts[0]:
                    folders.add(parts[0])
                # Si c'est un fichier direct
                elif len(parts) == 1 and parts[0]:
                    files.append({
                        'name': parts[0],
                        'size': blob.size,
                        'last_modified': blob.last_modified,
                        'content_type': blob.content_settings.content_type if blob.content_settings else None,
                        'full_path': blob.name
                    })
            
            # Combiner dossiers et fichiers
            result = []
            
            # Ajouter les dossiers
            for folder in sorted(folders):
                result.append({
                    'name': folder,
                    'type': 'folder',
                    'path': f"{prefix}{folder}/" if prefix else f"{folder}/"
                })
            
            # Ajouter les fichiers
            for file in sorted(files, key=lambda x: x['name']):
                result.append({
                    'name': file['name'],
                    'type': 'file',
                    'size': file['size'],
                    'last_modified': file['last_modified'],
                    'content_type': file['content_type'],
                    'full_path': file['full_path']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur listing dossiers : {e}")
            return []
    
    def download_file(self, container_name: str, blob_name: str) -> Optional[bytes]:
        """Télécharge un fichier depuis Azure Blob"""
        if not self.blob_service_client:
            return None
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            return blob_client.download_blob().readall()
            
        except Exception as e:
            logger.error(f"Erreur téléchargement blob : {e}")
            return None
    
    def extract_text_from_blob(self, container_name: str, blob_name: str) -> Optional[str]:
        """Extrait le texte d'un blob"""
        content_bytes = self.download_file(container_name, blob_name)
        
        if not content_bytes:
            return None
        
        file_ext = os.path.splitext(blob_name)[1].lower()
        
        try:
            if file_ext == '.txt':
                return content_bytes.decode('utf-8', errors='ignore')
            elif file_ext in ['.docx', '.doc'] and DOCX_AVAILABLE:
                doc = DocxDocument(io.BytesIO(content_bytes))
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                return f"[Format {file_ext} non supporté pour l'extraction de texte]"
        except Exception as e:
            logger.error(f"Erreur extraction texte : {e}")
            return None

# ================== GESTIONNAIRE DE SÉLECTION DE PIÈCES ==================

class GestionnairePiecesSelectionnees:
    """Gère la sélection et l'organisation des pièces pour un dossier"""
    
    def __init__(self):
        self.pieces: Dict[str, PieceSelectionnee] = {}
        self.categories = [
            "📄 Procédure",
            "💰 Comptabilité",
            "📊 Expertise",
            "📧 Correspondances",
            "📋 Contrats",
            "🏢 Documents sociaux",
            "🔍 Preuves",
            "📑 Autres"
        ]
    
    def ajouter_piece(self, document: Document, categorie: str, notes: str = "", pertinence: int = 5):
        """Ajoute une pièce à la sélection"""
        piece = PieceSelectionnee(
            document_id=document.id,
            titre=document.title,
            categorie=categorie,
            notes=notes,
            pertinence=pertinence
        )
        
        self.pieces[document.id] = piece
        
        # Sauvegarder dans session state
        if 'pieces_selectionnees' not in st.session_state:
            st.session_state.pieces_selectionnees = {}
        st.session_state.pieces_selectionnees[document.id] = piece
    
    def retirer_piece(self, document_id: str):
        """Retire une pièce de la sélection"""
        if document_id in self.pieces:
            del self.pieces[document_id]
        
        if document_id in st.session_state.pieces_selectionnees:
            del st.session_state.pieces_selectionnees[document_id]
    
    def get_pieces_par_categorie(self) -> Dict[str, List[PieceSelectionnee]]:
        """Retourne les pièces organisées par catégorie"""
        pieces_par_cat = {cat: [] for cat in self.categories}
        
        for piece in self.pieces.values():
            if piece.categorie in pieces_par_cat:
                pieces_par_cat[piece.categorie].append(piece)
        
        return pieces_par_cat
    
    def generer_bordereau(self) -> str:
        """Génère un bordereau des pièces sélectionnées"""
        bordereau = "BORDEREAU DES PIÈCES SÉLECTIONNÉES\n"
        bordereau += "=" * 50 + "\n\n"
        bordereau += f"Date : {datetime.now().strftime('%d/%m/%Y')}\n\n"
        
        pieces_par_cat = self.get_pieces_par_categorie()
        numero = 1
        
        for categorie, pieces in pieces_par_cat.items():
            if pieces:
                bordereau += f"\n{categorie}\n{'-' * len(categorie)}\n"
                for piece in sorted(pieces, key=lambda x: x.pertinence, reverse=True):
                    bordereau += f"{numero}. {piece.titre}"
                    if piece.notes:
                        bordereau += f" - {piece.notes}"
                    bordereau += f" (Pertinence: {piece.pertinence}/10)\n"
                    numero += 1
        
        bordereau += f"\n\nTOTAL : {len(self.pieces)} pièces\n"
        
        return bordereau

# ================== CONFIGURATION LLM ==================

class LLMConfig:
    """Configuration des LLMs"""
    
    @staticmethod
    def get_configs() -> Dict[LLMProvider, Dict[str, Any]]:
        return {
            LLMProvider.AZURE_OPENAI: {
                'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
                'key': os.getenv('AZURE_OPENAI_KEY'),
                'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
                'api_version': '2024-02-01'
            },
            LLMProvider.CLAUDE_OPUS: {
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'model': 'claude-3-opus-20240229'
            },
            LLMProvider.CHATGPT_4O: {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': 'gpt-4-turbo-preview'
            },
            LLMProvider.GEMINI: {
                'api_key': os.getenv('GOOGLE_API_KEY'),
                'model': 'gemini-pro'
            },
            LLMProvider.PERPLEXITY: {
                'api_key': os.getenv('PERPLEXITY_API_KEY'),
                'model': 'pplx-70b-online'
            }
        }

# ================== GESTIONNAIRE MULTI-LLM ==================

class MultiLLMManager:
    """Gestionnaire pour interroger plusieurs LLMs"""
    
    def __init__(self):
        self.configs = LLMConfig.get_configs()
        self.clients = self._initialize_clients()
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _initialize_clients(self) -> Dict[LLMProvider, Any]:
        """Initialise les clients LLM"""
        clients = {}
        
        # Azure OpenAI
        if self.configs[LLMProvider.AZURE_OPENAI]['key']:
            try:
                if AzureOpenAI:
                    clients[LLMProvider.AZURE_OPENAI] = AzureOpenAI(
                        azure_endpoint=self.configs[LLMProvider.AZURE_OPENAI]['endpoint'],
                        api_key=self.configs[LLMProvider.AZURE_OPENAI]['key'],
                        api_version=self.configs[LLMProvider.AZURE_OPENAI]['api_version']
                    )
            except Exception as e:
                logger.warning(f"Azure OpenAI non disponible: {e}")
        
        # Claude
        if self.configs[LLMProvider.CLAUDE_OPUS]['api_key']:
            try:
                if anthropic:
                    clients[LLMProvider.CLAUDE_OPUS] = anthropic.Anthropic(
                        api_key=self.configs[LLMProvider.CLAUDE_OPUS]['api_key']
                    )
            except Exception as e:
                logger.warning(f"Claude non disponible: {e}")
        
        # ChatGPT
        if self.configs[LLMProvider.CHATGPT_4O]['api_key']:
            try:
                if OpenAI:
                    clients[LLMProvider.CHATGPT_4O] = OpenAI(
                        api_key=self.configs[LLMProvider.CHATGPT_4O]['api_key']
                    )
            except Exception as e:
                logger.warning(f"ChatGPT non disponible: {e}")
        
        # Gemini
        if self.configs[LLMProvider.GEMINI]['api_key']:
            try:
                if genai:
                    genai.configure(api_key=self.configs[LLMProvider.GEMINI]['api_key'])
                    clients[LLMProvider.GEMINI] = genai.GenerativeModel(
                        self.configs[LLMProvider.GEMINI]['model']
                    )
            except Exception as e:
                logger.warning(f"Gemini non disponible: {e}")
        
        # Perplexity
        if self.configs[LLMProvider.PERPLEXITY]['api_key']:
            try:
                if OpenAI:
                    clients[LLMProvider.PERPLEXITY] = OpenAI(
                        api_key=self.configs[LLMProvider.PERPLEXITY]['api_key'],
                        base_url="https://api.perplexity.ai"
                    )
            except Exception as e:
                logger.warning(f"Perplexity non disponible: {e}")
        
        return clients
    
    async def query_single_llm(self, 
                              provider: LLMProvider, 
                              prompt: str,
                              system_prompt: str = None) -> Dict[str, Any]:
        """Interroge un seul LLM"""
        
        if provider not in self.clients:
            return {
                'provider': provider.value,
                'success': False,
                'error': 'Provider non configuré',
                'response': None
            }
        
        try:
            client = self.clients[provider]
            
            # Azure OpenAI
            if provider == LLMProvider.AZURE_OPENAI:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model=self.configs[provider]['deployment'],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None
                }
            
            # Claude
            elif provider == LLMProvider.CLAUDE_OPUS:
                messages = []
                messages.append({"role": "user", "content": prompt})
                
                response = client.messages.create(
                    model=self.configs[provider]['model'],
                    messages=messages,
                    system=system_prompt if system_prompt else "Tu es un assistant juridique expert en droit pénal des affaires.",
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.content[0].text,
                    'usage': {'total_tokens': response.usage.input_tokens + response.usage.output_tokens}
                }
            
            # ChatGPT 4o
            elif provider == LLMProvider.CHATGPT_4O:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model=self.configs[provider]['model'],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None
                }
            
            # Gemini
            elif provider == LLMProvider.GEMINI:
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = client.generate_content(full_prompt)
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.text,
                    'usage': None
                }
            
            # Perplexity
            elif provider == LLMProvider.PERPLEXITY:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model=self.configs[provider]['model'],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None,
                    'citations': getattr(response, 'citations', [])  # Perplexity inclut des citations
                }
            
        except Exception as e:
            logger.error(f"Erreur {provider.value}: {str(e)}")
            return {
                'provider': provider.value,
                'success': False,
                'error': str(e),
                'response': None
            }

# ================== PROMPTS PÉNAL DES AFFAIRES ==================

SEARCH_PROMPTS_AFFAIRES = {
    "🔍 Infractions économiques": {
        "Abus de biens sociaux": [
            "abus biens sociaux élément intentionnel dirigeant",
            "ABS intérêt personnel indirect jurisprudence",
            "ABS contrariété intérêt social caractérisée",
            "ABS groupe sociétés justification flux"
        ],
        "Corruption": [
            "corruption élément matériel pacte preuve",
            "corruption passive dirigeant public privé",
            "corruption agent public étranger FCPA",
            "corruption privée 445-1 code pénal"
        ],
        "Blanchiment": [
            "blanchiment présomption origine frauduleuse",
            "blanchiment auto-blanchiment dirigeant",
            "blanchiment élément moral connaissance",
            "blanchiment justification origine fonds"
        ],
        "Fraude fiscale": [
            "fraude fiscale élément intentionnel preuve",
            "fraude fiscale soustraction frauduleuse",
            "fraude fiscale régularisation spontanée",
            "fraude fiscale responsabilité dirigeant de fait"
        ]
    },
    "⚖️ Responsabilité PM": {
        "Imputation": [
            "responsabilité pénale personne morale organe représentant",
            "responsabilité PM pour compte critères jurisprudence",
            "responsabilité PM défaut organisation prévention",
            "responsabilité PM fusion absorption transmission"
        ],
        "Défenses": [
            "délégation pouvoirs conditions cumulatives validité",
            "délégation pouvoirs compétence autorité moyens",
            "programme conformité atténuation responsabilité",
            "CJIP conditions éligibilité négociation"
        ]
    }
}

ANALYSIS_PROMPTS_AFFAIRES = {
    "🎯 Analyse infractions économiques": [
        "Analysez précisément les éléments constitutifs de l'infraction reprochée",
        "Identifiez l'élément intentionnel et les moyens de le contester",
        "Recherchez les causes d'exonération ou d'atténuation",
        "Proposez une stratégie axée sur la bonne foi et l'intérêt social"
    ],
    "🏢 Responsabilité personne morale": [
        "Vérifiez les conditions d'imputation à la personne morale",
        "Analysez si les faits ont été commis pour le compte de la PM",
        "Examinez le rôle des organes et représentants",
        "Évaluez l'impact d'une éventuelle délégation de pouvoirs"
    ],
    "🛡️ Moyens de défense affaires": [
        "Valorisez le programme de conformité existant",
        "Démontrez les mesures correctives prises",
        "Argumentez sur l'absence d'enrichissement personnel",
        "Mettez en avant la transparence et la bonne gouvernance"
    ],
    "💰 Enjeux financiers": [
        "Calculez précisément le préjudice allégué",
        "Contestez les méthodes de calcul du préjudice",
        "Évaluez l'impact financier des sanctions encourues",
        "Proposez des modalités de réparation adaptées"
    ]
}

# ================== INTERFACE PRINCIPALE ==================

def main():
    """Interface principale de l'application"""
    
    # Initialisation
    initialize_session_state()
    
    # Titre principal avec style
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # Menu principal
        page = st.selectbox(
            "Choisir une fonctionnalité",
            [
                "🔍 Recherche de documents",
                "📁 Sélection de pièces",
                "🤖 Analyse IA",
                "📝 Rédaction assistée",
                "⚙️ Configuration"
            ],
            key="main_navigation"
        )
        
        st.markdown("---")
        
        # Infos système
        st.markdown("### 📊 État du système")
        
        # État Azure
        if AZURE_AVAILABLE:
            st.success("✅ Azure connecté")
        else:
            st.warning("⚠️ Azure non disponible")
        
        # Documents chargés
        nb_docs = len(st.session_state.azure_documents)
        nb_pieces = len(st.session_state.pieces_selectionnees)
        
        st.metric("Documents disponibles", nb_docs)
        st.metric("Pièces sélectionnées", nb_pieces)
    
    # Pages
    if page == "🔍 Recherche de documents":
        page_recherche_documents()
    elif page == "📁 Sélection de pièces":
        page_selection_pieces()
    elif page == "🤖 Analyse IA":
        page_analyse_ia()
    elif page == "📝 Rédaction assistée":
        page_redaction_assistee()
    elif page == "⚙️ Configuration":
        page_configuration()

def page_recherche_documents():
    """Page de recherche dans les documents Azure Blob"""
    
    st.header("🔍 Recherche de documents")
    
    # Section de recherche
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        
        # Barre de recherche principale
        col1, col2 = st.columns([4, 1])
        with col1:
            search_query = st.text_input(
                "Rechercher dans les documents",
                value=st.session_state.search_query,
                placeholder="Ex: abus de biens sociaux, délégation de pouvoirs, fraude fiscale...",
                key="search_input_main"
            )
        
        with col2:
            search_clicked = st.button("🔍 Rechercher", type="primary", key="search_button_main")
        
        # Options de recherche avancée
        with st.expander("Options avancées"):
            search_mode = st.selectbox(
                "Mode de recherche",
                [mode.value for mode in SearchMode],
                key="search_mode_select"
            )
            
            include_content = st.checkbox("Rechercher dans le contenu", value=True, key="search_content_check")
            include_metadata = st.checkbox("Rechercher dans les métadonnées", value=True, key="search_metadata_check")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation Azure Blob
    st.markdown("### 📂 Explorer les documents SharePoint")
    
    azure_manager = AzureBlobManager()
    
    if azure_manager.blob_service_client:
        # Sélection du container
        containers = azure_manager.list_containers()
        
        if containers:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_container = st.selectbox(
                    "Sélectionner un espace de stockage",
                    containers,
                    key="container_select"
                )
                
                st.session_state.selected_container = selected_container
            
            with col2:
                if st.button("🔄 Actualiser", key="refresh_containers"):
                    st.rerun()
            
            # Navigation dans les dossiers
            if selected_container:
                st.markdown('<div class="folder-nav">', unsafe_allow_html=True)
                
                # Fil d'Ariane
                current_path = st.session_state.get('current_folder_path', '')
                if current_path:
                    path_parts = current_path.split('/')
                    path_parts = [p for p in path_parts if p]  # Enlever les parties vides
                    
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
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Lister le contenu du dossier actuel
                items = azure_manager.list_folders(selected_container, current_path)
                
                if items:
                    # Organiser en colonnes
                    for item in items:
                        with st.container():
                            st.markdown('<div class="document-card">', unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                if item['type'] == 'folder':
                                    st.markdown(f"📁 **{item['name']}**")
                                else:
                                    # Icône selon le type de fichier
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
                                if item['type'] == 'folder':
                                    if st.button("📂 Ouvrir", key=f"open_folder_{clean_key(item['name'])}"):
                                        st.session_state.current_folder_path = item['path']
                                        st.rerun()
                                else:
                                    col_view, col_select = st.columns(2)
                                    
                                    with col_view:
                                        if st.button("👁️", key=f"view_file_{clean_key(item['full_path'])}"):
                                            # Extraire et afficher le contenu
                                            with st.spinner("Chargement..."):
                                                content = azure_manager.extract_text_from_blob(
                                                    selected_container,
                                                    item['full_path']
                                                )
                                                
                                                if content:
                                                    st.text_area(
                                                        f"Contenu de {item['name']}",
                                                        content[:2000] + "..." if len(content) > 2000 else content,
                                                        height=300,
                                                        key=f"content_view_{clean_key(item['full_path'])}"
                                                    )
                                    
                                    with col_select:
                                        # Créer un document et l'ajouter à la session
                                        doc_id = f"azure_{clean_key(item['full_path'])}"
                                        
                                        if st.button("➕", key=f"add_doc_{doc_id}", help="Ajouter à la sélection"):
                                            # Télécharger le contenu si pas déjà fait
                                            if doc_id not in st.session_state.azure_documents:
                                                with st.spinner("Ajout..."):
                                                    content = azure_manager.extract_text_from_blob(
                                                        selected_container,
                                                        item['full_path']
                                                    )
                                                    
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
                                                        st.success(f"✅ {item['name']} ajouté")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("📭 Aucun document dans ce dossier")
        else:
            st.warning("Aucun container disponible")
    else:
        st.error("❌ Connexion Azure Blob non configurée")
    
    # Prompts de recherche suggérés
    if search_query or search_clicked:
        st.markdown("### 💡 Recherches suggérées")
        
        for categorie, sous_categories in SEARCH_PROMPTS_AFFAIRES.items():
            with st.expander(categorie):
                for sous_cat, prompts in sous_categories.items():
                    st.markdown(f"**{sous_cat}**")
                    
                    # Créer une grille de boutons
                    cols = st.columns(2)
                    for idx, prompt in enumerate(prompts):
                        col = cols[idx % 2]
                        
                        with col:
                            # Clé unique pour chaque bouton
                            button_key = f"prompt_{clean_key(categorie)}_{clean_key(sous_cat)}_{idx}"
                            
                            if st.button(
                                prompt[:50] + "..." if len(prompt) > 50 else prompt,
                                key=button_key,
                                help=prompt
                            ):
                                st.session_state.search_query = prompt
                                st.rerun()

def page_selection_pieces():
    """Page de sélection et organisation des pièces"""
    
    st.header("📁 Sélection et organisation des pièces")
    
    # Gestionnaire de pièces
    gestionnaire = GestionnairePiecesSelectionnees()
    
    # Charger les pièces depuis la session
    if 'pieces_selectionnees' in st.session_state:
        gestionnaire.pieces = st.session_state.pieces_selectionnees
    
    # Vue d'ensemble
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents disponibles", len(st.session_state.azure_documents))
    
    with col2:
        st.metric("Pièces sélectionnées", len(gestionnaire.pieces))
    
    with col3:
        if st.button("📋 Générer bordereau", key="generer_bordereau"):
            bordereau = gestionnaire.generer_bordereau()
            st.text_area("Bordereau", bordereau, height=400, key="bordereau_display")
            
            # Option de téléchargement
            st.download_button(
                "💾 Télécharger le bordereau",
                bordereau,
                "bordereau_pieces.txt",
                "text/plain",
                key="download_bordereau"
            )
    
    # Deux colonnes : documents disponibles et pièces sélectionnées
    col_docs, col_pieces = st.columns([1, 1])
    
    # Colonne des documents disponibles
    with col_docs:
        st.markdown("### 📄 Documents disponibles")
        
        # Filtre
        filtre = st.text_input(
            "Filtrer les documents",
            placeholder="Rechercher par nom...",
            key="filtre_docs_pieces"
        )
        
        # Liste des documents
        for doc_id, doc in st.session_state.azure_documents.items():
            if filtre.lower() in doc.title.lower():
                with st.container():
                    st.markdown('<div class="document-card">', unsafe_allow_html=True)
                    
                    # Titre et métadonnées
                    st.markdown(f"**{doc.title}**")
                    
                    if doc.metadata.get('last_modified'):
                        st.caption(f"Modifié: {doc.metadata['last_modified']}")
                    
                    # Si déjà sélectionné, afficher différemment
                    if doc_id in gestionnaire.pieces:
                        st.success("✅ Déjà sélectionné")
                        
                        if st.button(f"❌ Retirer", key=f"remove_{doc_id}"):
                            gestionnaire.retirer_piece(doc_id)
                            st.rerun()
                    else:
                        # Sélection avec catégorie
                        col_cat, col_btn = st.columns([3, 1])
                        
                        with col_cat:
                            categorie = st.selectbox(
                                "Catégorie",
                                gestionnaire.categories,
                                key=f"cat_select_{doc_id}"
                            )
                        
                        with col_btn:
                            if st.button("➕", key=f"add_piece_{doc_id}"):
                                gestionnaire.ajouter_piece(doc, categorie)
                                st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Colonne des pièces sélectionnées
    with col_pieces:
        st.markdown("### ✅ Pièces sélectionnées")
        
        pieces_par_cat = gestionnaire.get_pieces_par_categorie()
        
        for categorie, pieces in pieces_par_cat.items():
            if pieces:
                with st.expander(f"{categorie} ({len(pieces)})", expanded=True):
                    for piece in sorted(pieces, key=lambda x: x.pertinence, reverse=True):
                        st.markdown('<div class="piece-selectionnee">', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**{piece.titre}**")
                            
                            # Notes
                            notes = st.text_input(
                                "Notes",
                                value=piece.notes,
                                key=f"notes_{piece.document_id}",
                                placeholder="Ajouter des notes..."
                            )
                            
                            # Pertinence
                            pertinence = st.slider(
                                "Pertinence",
                                1, 10,
                                value=piece.pertinence,
                                key=f"pertinence_{piece.document_id}"
                            )
                            
                            # Mettre à jour la pièce
                            if notes != piece.notes or pertinence != piece.pertinence:
                                piece.notes = notes
                                piece.pertinence = pertinence
                                st.session_state.pieces_selectionnees[piece.document_id] = piece
                        
                        with col2:
                            if st.button("🗑️", key=f"delete_piece_{piece.document_id}"):
                                gestionnaire.retirer_piece(piece.document_id)
                                st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

def page_analyse_ia():
    """Page d'analyse par IA"""
    
    st.header("🤖 Analyse IA des documents")
    
    # Vérifier qu'il y a des pièces sélectionnées
    if not st.session_state.pieces_selectionnees:
        st.warning("⚠️ Veuillez d'abord sélectionner des pièces dans l'onglet 'Sélection de pièces'")
        return
    
    # Configuration de l'analyse
    st.markdown("### ⚙️ Configuration de l'analyse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type d'infraction - Saisie libre avec suggestions
        infractions_list = [inf.value for inf in InfractionAffaires]
        
        infraction = st.text_input(
            "Type d'infraction",
            placeholder="Ex: Abus de biens sociaux, corruption, fraude fiscale...",
            key="infraction_input",
            help="Saisissez librement l'infraction ou choisissez dans les suggestions"
        )
        
        # Suggestions
        if not infraction:
            st.info("💡 Suggestions : " + ", ".join(infractions_list[:5]) + "...")
        
        # Client
        client_nom = st.text_input(
            "Nom du client",
            placeholder="Personne physique ou morale",
            key="client_nom_analyse"
        )
        
        client_type = st.radio(
            "Type de client",
            ["Personne physique", "Personne morale"],
            key="client_type_analyse"
        )
    
    with col2:
        # Providers IA à utiliser
        llm_manager = MultiLLMManager()
        available_providers = list(llm_manager.clients.keys())
        
        if available_providers:
            selected_providers = st.multiselect(
                "IA à utiliser",
                [p.value for p in available_providers],
                default=[available_providers[0].value] if available_providers else [],
                key="selected_providers_analyse"
            )
            
            # Mode de fusion
            fusion_mode = st.radio(
                "Mode de fusion des réponses",
                ["Synthèse IA", "Concatenation simple"],
                key="fusion_mode_analyse"
            )
        else:
            st.error("❌ Aucune IA configurée")
            return
    
    # Sélection des pièces à analyser
    st.markdown("### 📄 Pièces à analyser")
    
    pieces_a_analyser = []
    for piece_id, piece in st.session_state.pieces_selectionnees.items():
        if st.checkbox(
            f"{piece.titre} ({piece.categorie})",
            value=True,
            key=f"analyse_piece_{piece_id}"
        ):
            pieces_a_analyser.append(piece_id)
    
    # Type d'analyse
    st.markdown("### 🎯 Type d'analyse")
    
    analyse_types = st.multiselect(
        "Sélectionner les analyses à effectuer",
        list(ANALYSIS_PROMPTS_AFFAIRES.keys()),
        default=list(ANALYSIS_PROMPTS_AFFAIRES.keys())[:2],
        key="analyse_types_select"
    )
    
    # Bouton d'analyse
    if st.button("🚀 Lancer l'analyse", type="primary", key="lancer_analyse"):
        if not infraction or not client_nom or not pieces_a_analyser:
            st.error("❌ Veuillez remplir tous les champs")
            return
        
        # Préparer le contenu pour l'analyse
        contenu_pieces = []
        for piece_id in pieces_a_analyser:
            if piece_id in st.session_state.azure_documents:
                doc = st.session_state.azure_documents[piece_id]
                piece = st.session_state.pieces_selectionnees[piece_id]
                
                contenu_pieces.append(f"""
=== {doc.title} ({piece.categorie}) ===
Pertinence: {piece.pertinence}/10
Notes: {piece.notes}
Contenu:
{doc.content[:3000]}...
""")
        
        # Construire le prompt
        prompt_base = f"""Tu es un avocat expert en droit pénal des affaires.

Client: {client_nom} ({client_type})
Infraction reprochée: {infraction}

Documents analysés:
{chr(10).join(contenu_pieces)}

Analyses demandées:
"""
        
        # Lancer les analyses
        with st.spinner("🔄 Analyse en cours..."):
            resultats = {}
            
            # Pour chaque type d'analyse
            for analyse_type in analyse_types:
                prompts = ANALYSIS_PROMPTS_AFFAIRES[analyse_type]
                
                # Construire le prompt complet
                prompt_complet = prompt_base + f"\n{analyse_type}:\n"
                for p in prompts:
                    prompt_complet += f"- {p}\n"
                
                # Convertir les providers
                providers_enum = [
                    p for p in LLMProvider 
                    if p.value in selected_providers
                ]
                
                # Interroger les IA
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                responses = loop.run_until_complete(
                    llm_manager.query_multiple_llms(
                        providers_enum,
                        prompt_complet
                    )
                )
                
                # Fusionner les réponses
                if fusion_mode == "Synthèse IA" and len(responses) > 1:
                    fusion = llm_manager.fusion_responses(responses)
                else:
                    fusion = "\n\n".join([
                        f"### {r['provider']}\n{r['response']}"
                        for r in responses
                        if r['success']
                    ])
                
                resultats[analyse_type] = fusion
            
            # Afficher les résultats
            st.markdown("## 📊 Résultats de l'analyse")
            
            for analyse_type, resultat in resultats.items():
                with st.expander(analyse_type, expanded=True):
                    st.markdown(resultat)
                    
                    # Options d'export
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "💾 Télécharger",
                            resultat,
                            f"analyse_{clean_key(analyse_type)}.txt",
                            "text/plain",
                            key=f"download_analyse_{clean_key(analyse_type)}"
                        )
                    
                    with col2:
                        if st.button(
                            "📋 Copier",
                            key=f"copy_analyse_{clean_key(analyse_type)}"
                        ):
                            st.write("Contenu copié!")

def page_redaction_assistee():
    """Page de rédaction assistée"""
    
    st.header("📝 Rédaction assistée par IA")
    
    # Templates disponibles
    templates = {
        "📨 Demande d'audition libre": """Maître [NOM]
Avocat au Barreau de [VILLE]

À l'attention de [DESTINATAIRE]
[SERVICE]

Objet : Demande d'audition libre
Procédure n° [NUMERO]

Monsieur/Madame,

J'ai l'honneur de vous informer que [CLIENT], souhaite être entendu(e) dans le cadre de l'enquête référencée ci-dessus.

Mon client(e) se tient à votre disposition pour une audition libre et sollicite communication préalable des pièces de la procédure conformément à l'article 61-1 du Code de procédure pénale.

Je vous prie d'agréer, Monsieur/Madame, l'expression de ma considération distinguée.

Maître [NOM]""",
        
        "📄 Conclusions de relaxe": """CONCLUSIONS AUX FINS DE RELAXE

POUR : [CLIENT]

CONTRE : LE MINISTÈRE PUBLIC

I. SUR LES FAITS

[Exposé des faits]

II. SUR LE DROIT

[Arguments juridiques]

III. SUR L'ABSENCE D'ÉLÉMENTS CONSTITUTIFS

[Démonstration]

PAR CES MOTIFS

- CONSTATER l'absence d'éléments constitutifs
- PRONONCER la relaxe""",
        
        "🤝 Proposition CJIP": """PROPOSITION DE CONVENTION JUDICIAIRE D'INTÉRÊT PUBLIC

POUR : [SOCIÉTÉ]

I. ÉLIGIBILITÉ À LA CJIP

- Personne morale
- Infractions éligibles : [INFRACTIONS]
- Absence de condamnation préalable

II. INTÉRÊT DE LA CJIP

- Réparation rapide du préjudice
- Économie judiciaire
- Préservation de l'activité économique

III. ENGAGEMENTS PROPOSÉS

1. Amende d'intérêt public : [MONTANT]
2. Programme de conformité
3. Audit externe

IV. GARANTIES

- Validation par le conseil d'administration
- Budget dédié à la conformité
- Reporting régulier"""
    }
    
    # Sélection du template
    template_choisi = st.selectbox(
        "Choisir un modèle",
        list(templates.keys()),
        key="template_select_redaction"
    )
    
    # Afficher le template
    texte = st.text_area(
        "Contenu",
        value=templates[template_choisi],
        height=400,
        key="texte_redaction"
    )
    
    # Variables à remplacer
    st.markdown("### 📝 Variables à remplacer")
    
    # Extraire les variables du template
    variables = re.findall(r'\[([A-Z_]+)\]', texte)
    variables = list(set(variables))  # Supprimer les doublons
    
    if variables:
        replacements = {}
        
        # Créer des champs pour chaque variable
        cols = st.columns(2)
        for i, var in enumerate(sorted(variables)):
            col = cols[i % 2]
            
            with col:
                replacements[var] = st.text_input(
                    var,
                    key=f"var_{clean_key(var)}"
                )
        
        # Bouton pour appliquer les remplacements
        if st.button("✏️ Appliquer les variables", key="apply_variables"):
            texte_final = texte
            
            for var, value in replacements.items():
                if value:
                    texte_final = texte_final.replace(f"[{var}]", value)
            
            st.text_area(
                "Document finalisé",
                value=texte_final,
                height=400,
                key="texte_finalise"
            )
            
            # Option de téléchargement
            st.download_button(
                "💾 Télécharger le document",
                texte_final,
                f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                key="download_doc_redaction"
            )
    else:
        st.info("ℹ️ Aucune variable à remplacer dans ce modèle")
    
    # Section IA
    st.markdown("### 🤖 Amélioration par IA")
    
    if st.checkbox("Activer l'amélioration IA", key="enable_ia_redaction"):
        # Sélection du contexte
        col1, col2 = st.columns(2)
        
        with col1:
            contexte_infraction = st.text_input(
                "Infraction concernée",
                placeholder="Ex: Abus de biens sociaux",
                key="contexte_infraction_redaction"
            )
        
        with col2:
            ton = st.select_slider(
                "Ton du document",
                options=["Très formel", "Formel", "Neutre", "Direct", "Combatif"],
                value="Formel",
                key="ton_redaction"
            )
        
        # Instructions supplémentaires
        instructions = st.text_area(
            "Instructions supplémentaires pour l'IA",
            placeholder="Ex: Insister sur l'absence d'élément intentionnel, valoriser la bonne foi...",
            key="instructions_ia_redaction"
        )
        
        if st.button("🎯 Améliorer avec l'IA", key="ameliorer_ia"):
            if not texte.strip():
                st.error("❌ Le document est vide")
                return
            
            # Construire le prompt
            prompt = f"""Tu es un avocat expert en droit pénal des affaires.

Améliore ce document juridique en gardant sa structure mais en enrichissant le contenu.

Document original:
{texte}

Contexte:
- Infraction: {contexte_infraction or 'Non spécifié'}
- Ton souhaité: {ton}
- Instructions: {instructions or 'Aucune'}

Règles:
1. Conserve la structure du document
2. Enrichis les arguments juridiques
3. Ajoute des références légales pertinentes
4. Améliore la formulation
5. Garde le ton {ton.lower()}

Génère le document amélioré:"""
            
            # Appel à l'IA
            llm_manager = MultiLLMManager()
            
            with st.spinner("🔄 Amélioration en cours..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Utiliser le premier provider disponible
                if llm_manager.clients:
                    provider = list(llm_manager.clients.keys())[0]
                    
                    response = loop.run_until_complete(
                        llm_manager.query_single_llm(
                            provider,
                            prompt,
                            "Tu es un avocat spécialisé en rédaction d'actes juridiques."
                        )
                    )
                    
                    if response['success']:
                        st.markdown("### 📄 Document amélioré")
                        
                        st.text_area(
                            "Version améliorée",
                            value=response['response'],
                            height=500,
                            key="document_ameliore"
                        )
                        
                        # Comparaison
                        if st.checkbox("Voir les différences", key="voir_differences"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Original**")
                                st.text(texte)
                            
                            with col2:
                                st.markdown("**Amélioré**")
                                st.text(response['response'])
                        
                        # Téléchargement
                        st.download_button(
                            "💾 Télécharger la version améliorée",
                            response['response'],
                            f"document_ameliore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            "text/plain",
                            key="download_ameliore"
                        )
                    else:
                        st.error(f"❌ Erreur IA: {response['error']}")
                else:
                    st.error("❌ Aucune IA disponible")

def page_configuration():
    """Page de configuration"""
    
    st.header("⚙️ Configuration")
    
    tabs = st.tabs(["🔑 Clés API", "📊 État du système", "💾 Export/Import"])
    
    # Onglet Clés API
    with tabs[0]:
        st.markdown("### Configuration des clés API")
        
        st.info("""
        ℹ️ Les clés API doivent être configurées dans les variables d'environnement ou dans un fichier .env
        
        Variables nécessaires:
        - AZURE_OPENAI_KEY
        - AZURE_OPENAI_ENDPOINT
        - AZURE_SEARCH_KEY
        - AZURE_SEARCH_ENDPOINT
        - AZURE_STORAGE_CONNECTION_STRING
        - ANTHROPIC_API_KEY
        - OPENAI_API_KEY
        - GOOGLE_API_KEY
        - PERPLEXITY_API_KEY
        """)
        
        # Vérifier l'état des clés
        configs = LLMConfig.get_configs()
        
        for provider, config in configs.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.text(provider.value)
            
            with col2:
                if config.get('key') or config.get('api_key'):
                    st.success("✅")
                else:
                    st.error("❌")
    
    # Onglet État du système
    with tabs[1]:
        st.markdown("### État du système")
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Documents Azure", len(st.session_state.azure_documents))
        
        with col2:
            st.metric("Pièces sélectionnées", len(st.session_state.pieces_selectionnees))
        
        with col3:
            llm_manager = MultiLLMManager()
            st.metric("IA disponibles", len(llm_manager.clients))
        
        with col4:
            st.metric("Mémoire session", f"{len(str(st.session_state)) / 1024:.1f} KB")
        
        # État Azure
        st.markdown("### 🔷 Services Azure")
        
        services = {
            "Azure Blob Storage": AZURE_AVAILABLE and bool(os.getenv('AZURE_STORAGE_CONNECTION_STRING')),
            "Azure Search": AZURE_AVAILABLE and bool(os.getenv('AZURE_SEARCH_ENDPOINT')),
            "Azure OpenAI": bool(os.getenv('AZURE_OPENAI_ENDPOINT'))
        }
        
        for service, status in services.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.text(service)
            
            with col2:
                if status:
                    st.success("✅ Actif")
                else:
                    st.error("❌ Inactif")
    
    # Onglet Export/Import
    with tabs[2]:
        st.markdown("### 💾 Export/Import de configuration")
        
        # Export
        st.markdown("#### Export")
        
        export_data = {
            'pieces_selectionnees': {
                k: {
                    'document_id': v.document_id,
                    'titre': v.titre,
                    'categorie': v.categorie,
                    'notes': v.notes,
                    'pertinence': v.pertinence
                }
                for k, v in st.session_state.pieces_selectionnees.items()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            "📥 Exporter la configuration",
            export_json,
            f"config_penal_affaires_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            key="export_config"
        )
        
        # Import
        st.markdown("#### Import")
        
        uploaded_file = st.file_uploader(
            "Charger une configuration",
            type=['json'],
            key="import_config_file"
        )
        
        if uploaded_file:
            try:
                config_data = json.load(uploaded_file)
                
                # Prévisualisation
                st.json(config_data)
                
                if st.button("⬆️ Importer", key="import_config_button"):
                    # Importer les pièces sélectionnées
                    if 'pieces_selectionnees' in config_data:
                        for piece_id, piece_data in config_data['pieces_selectionnees'].items():
                            piece = PieceSelectionnee(
                                document_id=piece_data['document_id'],
                                titre=piece_data['titre'],
                                categorie=piece_data['categorie'],
                                notes=piece_data.get('notes', ''),
                                pertinence=piece_data.get('pertinence', 5)
                            )
                            st.session_state.pieces_selectionnees[piece_id] = piece
                    
                    st.success("✅ Configuration importée avec succès")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'import: {str(e)}")

# ================== LANCEMENT DE L'APPLICATION ==================

if __name__ == "__main__":
    main()