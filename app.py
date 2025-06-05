import streamlit as st

# Configuration de la page EN PREMIER
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal IMMÉDIATEMENT après
st.title("IA Juridique")

# ENSUITE seulement, les autres imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
import io
from typing import Dict, List, Set, Tuple, Optional, Any
import json
from datetime import datetime, timedelta
# ... reste des imports
st.title("IA Juridique")

# Assistant Pénal des Affaires IA - Version Complète
# Intégrant Multi-LLM, Multi-Victimes et Adaptation IA

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
    print("🟢 AZURE DISPONIBLE")
except ImportError:
    AZURE_AVAILABLE = False
  
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

# Configuration Streamlit
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports conditionnels pour les IA
try:
    from openai import OpenAI
    from azure.ai.openai import AzureOpenAI
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
    import requests
except ImportError:
    requests = None

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

# ================== ENUMERATIONS ==================

class InfractionAffaires(Enum):
    """Types d'infractions en droit pénal des affaires"""
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

class ProcedureAffaires(Enum):
    """Types de procédures adaptées au pénal des affaires"""
    AUDITION_LIBRE = "Audition libre"
    ENQUETE_PRELIMINAIRE = "Enquête préliminaire"
    INSTRUCTION = "Information judiciaire"
    CITATION_DIRECTE = "Citation directe"
    CRPC = "CRPC"
    CJIP = "Convention judiciaire d'intérêt public"

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

@dataclass
class DossierAffaires:
    """Dossier pénal des affaires"""
    numero_parquet: str
    numero_instruction: Optional[str]
    
    # Client (personne physique ou morale)
    client_nom: str
    client_type: str  # "PP" ou "PM"
    client_info: Dict[str, Any]  # SIREN, forme juridique, CA, etc.
    
    # Procédure
    qualification_faits: List[str]
    date_faits: datetime
    procedure_type: ProcedureAffaires
    magistrat: Optional[str]
    
    # Éléments spécifiques affaires
    montant_prejudice: Optional[float] = None
    delegation_pouvoirs: Optional[Dict[str, Any]] = None
    programme_conformite: Optional[Dict[str, Any]] = None
    
    # Procédure
    auditions: List[Dict[str, Any]] = field(default_factory=list)
    perquisitions: List[Dict[str, Any]] = field(default_factory=list)
    expertises: List[Dict[str, Any]] = field(default_factory=list)
    audiences: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Multi-victimes
    victimes: List['VictimeInfo'] = field(default_factory=list)
    
    def calculer_prescription(self) -> Dict[str, Any]:
        """Calcule la prescription adaptée au pénal des affaires"""
        delais = {
            "contravention": AppConfig.PRESCRIPTION_CONTRAVENTION,
            "delit": AppConfig.PRESCRIPTION_DELIT,
            "crime": AppConfig.PRESCRIPTION_CRIME
        }
        
        # Cas spéciaux pénal des affaires
        if "Fraude fiscale" in self.qualification_faits:
            delai_prescription = AppConfig.PRESCRIPTION_FRAUDE_FISCALE
            nature = "delit_fiscal"
        elif "Travail dissimulé" in self.qualification_faits:
            delai_prescription = AppConfig.PRESCRIPTION_TRAVAIL_DISSIMULE
            nature = "delit_social"
        else:
            nature = "delit"  # La plupart des infractions affaires sont des délits
            delai_prescription = delais[nature]
        
        date_prescription = self.date_faits + timedelta(days=365 * delai_prescription)
        
        return {
            "nature_infraction": nature,
            "delai_annees": delai_prescription,
            "date_prescription": date_prescription,
            "prescrit": datetime.now() > date_prescription,
            "jours_restants": (date_prescription - datetime.now()).days
        }

@dataclass
class VictimeInfo:
    """Information sur une victime/plaignant"""
    nom: str
    prenom: str
    prejudice_subi: str
    montant_prejudice: float
    elements_specifiques: List[str]
    documents_support: List[str]  # Références aux documents

@dataclass
class DelegationPouvoir:
    """Représente une délégation de pouvoirs"""
    delegant: str
    delegataire: str
    date_delegation: datetime
    domaines: List[str]
    competence: bool = False
    autorite: bool = False
    moyens: bool = False
    subdelegation_autorisee: bool = False
    document_reference: Optional[str] = None
    
    def est_valide(self) -> bool:
        """Vérifie si la délégation remplit les conditions"""
        return all([self.competence, self.autorite, self.moyens])

@dataclass
class PieceVersee:
    """Pièce versée aux débats"""
    numero: int
    titre: str
    contenu: str
    type: str
    date_ajout: datetime = field(default_factory=datetime.now)
    cote_dossier: Optional[str] = None
    dossier_id: Optional[str] = None
    citation_complete: Optional[str] = None

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
    
    .dossier-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-color);
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .procedure-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .badge-instruction { 
        background-color: #3f51b5; 
        color: white; 
    }
    
    .badge-crpc { 
        background-color: #009688; 
        color: white; 
    }
    
    .badge-cjip { 
        background-color: #4caf50; 
        color: white; 
    }
    
    .piece-versee {
        background: #f8f9fa;
        border-left: 3px solid var(--success-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .llm-response {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

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
                from azure.ai.openai import AzureOpenAI
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
                import anthropic
                clients[LLMProvider.CLAUDE_OPUS] = anthropic.Anthropic(
                    api_key=self.configs[LLMProvider.CLAUDE_OPUS]['api_key']
                )
            except Exception as e:
                logger.warning(f"Claude non disponible: {e}")
        
        # ChatGPT
        if self.configs[LLMProvider.CHATGPT_4O]['api_key']:
            try:
                from openai import OpenAI
                clients[LLMProvider.CHATGPT_4O] = OpenAI(
                    api_key=self.configs[LLMProvider.CHATGPT_4O]['api_key']
                )
            except Exception as e:
                logger.warning(f"ChatGPT non disponible: {e}")
        
        # Gemini
        if self.configs[LLMProvider.GEMINI]['api_key']:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.configs[LLMProvider.GEMINI]['api_key'])
                clients[LLMProvider.GEMINI] = genai.GenerativeModel(
                    self.configs[LLMProvider.GEMINI]['model']
                )
            except Exception as e:
                logger.warning(f"Gemini non disponible: {e}")
        
        # Perplexity
        if self.configs[LLMProvider.PERPLEXITY]['api_key']:
            try:
                from openai import OpenAI
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
                    'usage': response.usage.dict() if response.usage else None
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
                    'usage': response.usage.dict() if response.usage else None
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
                    'usage': response.usage.dict() if response.usage else None,
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
    
    async def query_multiple_llms(self,
                                 providers: List[LLMProvider],
                                 prompt: str,
                                 system_prompt: str = None) -> List[Dict[str, Any]]:
        """Interroge plusieurs LLMs en parallèle"""
        
        tasks = [
            self.query_single_llm(provider, prompt, system_prompt)
            for provider in providers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Gérer les exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    'provider': providers[i].value,
                    'success': False,
                    'error': str(result),
                    'response': None
                })
            else:
                final_results.append(result)
        
        return final_results
    
    def fusion_responses(self, 
                        responses: List[Dict[str, Any]],
                        fusion_llm: LLMProvider = LLMProvider.AZURE_OPENAI) -> str:
        """Fusionne plusieurs réponses en utilisant un LLM"""
        
        # Filtrer les réponses réussies
        valid_responses = [
            r for r in responses 
            if r['success'] and r['response']
        ]
        
        if not valid_responses:
            return "Aucune réponse valide à fusionner."
        
        if len(valid_responses) == 1:
            return valid_responses[0]['response']
        
        # Construire le prompt de fusion
        fusion_prompt = """Tu es un expert juridique en droit pénal des affaires.
Voici plusieurs analyses juridiques provenant de différentes IA sur la même question :
"""
        
        for i, resp in enumerate(valid_responses, 1):
            fusion_prompt += f"=== Analyse {i} ({resp['provider']}) ===\n"
            fusion_prompt += f"{resp['response']}\n\n"
        
        fusion_prompt += """
=== INSTRUCTIONS DE FUSION ===
Fusionne ces analyses en :
1. Conservant TOUS les arguments juridiques uniques de chaque réponse
2. Gardant TOUTES les références légales (articles, jurisprudence)
3. Structurant de manière claire et hiérarchisée
4. Éliminant les redondances tout en préservant les nuances
5. Signalant les points de divergence s'il y en a
6. Enrichissant avec les détails complémentaires de chaque analyse
Produis une synthèse complète et détaillée qui combine le meilleur de chaque analyse.
"""
        
        # Utiliser le LLM de fusion
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        fusion_result = loop.run_until_complete(
            self.query_single_llm(
                fusion_llm,
                fusion_prompt,
                "Tu es un expert en synthèse juridique."
            )
        )
        
        if fusion_result['success']:
            return fusion_result['response']
        else:
            # Fallback : concatenation simple
            return self._simple_fusion(valid_responses)
    
    def _simple_fusion(self, responses: List[Dict[str, Any]]) -> str:
        """Fusion simple sans LLM"""
        
        fusion = "SYNTHÈSE DES ANALYSES\n" + "="*50 + "\n\n"
        
        for resp in responses:
            fusion += f"### Analyse {resp['provider']}\n"
            fusion += f"{resp['response']}\n\n"
            fusion += "-"*30 + "\n\n"
        
        return fusion

# ================== GESTIONNAIRE MULTI-VICTIMES ==================

class GestionnaireMultiVictimes:
    """Gère plusieurs victimes dans une même affaire"""
    
    def __init__(self):
        self.victimes: Dict[str, VictimeInfo] = {}
        self.affaire_commune: Dict[str, Any] = {}
    
    def ajouter_victime(self, victime: VictimeInfo) -> str:
        """Ajoute une victime à l'affaire"""
        victime_id = f"{victime.nom}_{victime.prenom}"
        self.victimes[victime_id] = victime
        return victime_id
    
    def extraire_prejudices(self, doc_content: str, victime_id: str) -> Dict[str, Any]:
        """Extrait les éléments de préjudice spécifiques d'un document"""
        victime = self.victimes.get(victime_id)
        if not victime:
            return {}
        
        # Extraction des éléments pertinents
        prejudice_elements = {
            'montant': victime.montant_prejudice,
            'nature': victime.prejudice_subi,
            'elements_specifiques': victime.elements_specifiques,
            'preuves': victime.documents_support
        }
        
        return prejudice_elements

# ================== ADAPTATEUR PLAINTE IA ==================

class AdaptateurPlainteIA:
    """Adapte des plaintes existantes pour de nouvelles victimes"""
    
    def __init__(self, llm_manager: MultiLLMManager = None):
        self.llm_manager = llm_manager
        self.template_cache = {}
    
    async def adapter_plainte(self, 
                            plainte_originale: str,
                            victime_originale: VictimeInfo,
                            nouvelles_victimes: List[VictimeInfo],
                            contexte_commun: Dict[str, Any]) -> Dict[str, str]:
        """Adapte une plainte pour plusieurs nouvelles victimes"""
        
        plaintes_adaptees = {}
        
        for victime in nouvelles_victimes:
            prompt = self._construire_prompt_adaptation(
                plainte_originale,
                victime_originale,
                victime,
                contexte_commun
            )
            
            # Appel à l'IA
            if self.llm_manager:
                response = await self.llm_manager.query_single_llm(
                    LLMProvider.AZURE_OPENAI,
                    prompt,
                    "Tu es un avocat expert en droit pénal des affaires."
                )
                if response['success']:
                    plaintes_adaptees[f"{victime.nom}_{victime.prenom}"] = response['response']
                else:
                    # Fallback
                    plaintes_adaptees[f"{victime.nom}_{victime.prenom}"] = \
                        self._adaptation_basique(plainte_originale, victime)
            else:
                # Fallback sans IA
                plaintes_adaptees[f"{victime.nom}_{victime.prenom}"] = \
                    self._adaptation_basique(plainte_originale, victime)
        
        return plaintes_adaptees
    
    def _construire_prompt_adaptation(self, plainte_originale: str,
                                    victime_orig: VictimeInfo,
                                    nouvelle_victime: VictimeInfo,
                                    contexte: Dict[str, Any]) -> str:
        """Construit le prompt pour l'IA"""
        
        return f"""Tu es un avocat spécialisé en droit pénal des affaires.
        
Voici une plainte rédigée pour {victime_orig.nom} {victime_orig.prenom}:
{plainte_originale}
Adapte cette plainte pour {nouvelle_victime.nom} {nouvelle_victime.prenom} en:
1. Conservant la structure et les arguments juridiques
2. Remplaçant les informations personnelles
3. Adaptant le préjudice spécifique:
   - Nature du préjudice: {nouvelle_victime.prejudice_subi}
   - Montant: {nouvelle_victime.montant_prejudice}€
   - Éléments spécifiques: {', '.join(nouvelle_victime.elements_specifiques)}
4. Insistant particulièrement sur le préjudice subi par cette victime
Contexte de l'affaire: {contexte}
Génère la plainte adaptée en gardant le même niveau de qualité juridique."""
    
    def _adaptation_basique(self, plainte_originale: str, 
                          nouvelle_victime: VictimeInfo) -> str:
        """Adaptation basique sans IA"""
        
        # Remplacements simples
        plainte = plainte_originale
        
        # Patterns à remplacer
        replacements = {
            r'\[NOM\]': nouvelle_victime.nom,
            r'\[PRENOM\]': nouvelle_victime.prenom,
            r'\[PREJUDICE\]': nouvelle_victime.prejudice_subi,
            r'\[MONTANT\]': f"{nouvelle_victime.montant_prejudice:,.2f}",
        }
        
        for pattern, replacement in replacements.items():
            plainte = re.sub(pattern, replacement, plainte)
        
        # Ajouter section préjudice spécifique
        section_prejudice = f"""
III. PRÉJUDICE SPÉCIFIQUE DE {nouvelle_victime.nom} {nouvelle_victime.prenom}
Le préjudice subi se caractérise par :
- Nature : {nouvelle_victime.prejudice_subi}
- Montant : {nouvelle_victime.montant_prejudice:,.2f} euros
- Éléments particuliers : {', '.join(nouvelle_victime.elements_specifiques)}
Ce préjudice est établi par les pièces suivantes :
{chr(10).join([f"- {doc}" for doc in nouvelle_victime.documents_support])}
"""
        
        # Insérer avant "PAR CES MOTIFS"
        if "PAR CES MOTIFS" in plainte:
            plainte = plainte.replace("PAR CES MOTIFS", section_prejudice + "\nPAR CES MOTIFS")
        else:
            plainte += "\n" + section_prejudice
        
        return plainte

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

# ================== GESTION DES CITATIONS ==================

class CitationManager:
    """Gestionnaire des citations juridiques"""
    
    def __init__(self):
        self.citations = {}
        self.citation_formats = AppConfig.CITATION_FORMATS
    
    def format_citation(self, source_type: str, metadata: Dict[str, Any]) -> str:
        """Formate une citation selon les normes juridiques"""
        format_template = self.citation_formats.get(source_type, "{reference}")
        
        try:
            return format_template.format(**metadata)
        except KeyError as e:
            logger.warning(f"Métadonnées manquantes pour citation : {e}")
            return metadata.get('reference', 'Source non spécifiée')

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
    
    def extract_folder_documents(self, container_name: str, folder_path: str, 
                               recursive: bool = True) -> List[Document]:
        """Extrait tous les documents d'un dossier (et sous-dossiers si recursive)"""
        documents = []
        
        if not self.blob_service_client:
            return documents
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Lister tous les blobs dans le dossier
            blobs = container_client.list_blobs(name_starts_with=folder_path)
            
            supported_extensions = ['.pdf', '.txt', '.docx', '.doc', '.rtf']
            
            for blob in blobs:
                # Vérifier l'extension
                file_ext = os.path.splitext(blob.name)[1].lower()
                
                if file_ext in supported_extensions:
                    # Télécharger et extraire le contenu
                    try:
                        content_bytes = self.download_file(container_name, blob.name)
                        
                        if content_bytes:
                            # Extraire le texte selon le type
                            if file_ext == '.txt':
                                content = content_bytes.decode('utf-8', errors='ignore')
                            elif file_ext in ['.docx', '.doc']:
                                content = self._extract_docx_text(content_bytes)
                            elif file_ext == '.pdf':
                                content = self._extract_pdf_text(content_bytes)
                            else:
                                content = content_bytes.decode('utf-8', errors='ignore')
                            
                            # Créer le document
                            doc = Document(
                                id=f"azure_{blob.name.replace('/', '_')}",
                                title=os.path.basename(blob.name),
                                content=content,
                                source='azure_blob',
                                metadata={
                                    'container': container_name,
                                    'blob_path': blob.name,
                                    'folder': folder_path,
                                    'size': blob.size,
                                    'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
                                },
                                folder_path=folder_path
                            )
                            
                            documents.append(doc)
                            
                    except Exception as e:
                        logger.warning(f"Erreur extraction {blob.name} : {e}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Erreur extraction documents : {e}")
            return documents
    
    def _extract_docx_text(self, content_bytes: bytes) -> str:
        """Extrait le texte d'un fichier DOCX"""
        try:
            if DOCX_AVAILABLE:
                doc = DocxDocument(io.BytesIO(content_bytes))
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                return "[Contenu DOCX - module python-docx requis]"
        except Exception as e:
            logger.error(f"Erreur extraction DOCX : {e}")
            return "[Erreur extraction DOCX]"
    
    def _extract_pdf_text(self, content_bytes: bytes) -> str:
        """Extrait le texte d'un fichier PDF"""
        try:
            # Ici vous pourriez utiliser PyPDF2 ou pdfplumber
            # Pour l'instant, retour basique
            return "[Contenu PDF - extraction non implémentée]"
        except Exception as e:
            logger.error(f"Erreur extraction PDF : {e}")
            return "[Erreur extraction PDF]"

# ================== DOCUMENT MANAGER ==================

class DocumentManager:
    """Gestionnaire de documents avec recherche locale et Azure"""
    
    def __init__(self):
        self.local_documents: Dict[str, Document] = {}
        self.citation_manager = CitationManager()
        self.azure_blob_manager = AzureBlobManager()
        
        # Initialiser Azure si disponible
        if AZURE_AVAILABLE and os.getenv('AZURE_SEARCH_ENDPOINT'):
            self._init_azure_clients()
        else:
            self.search_client = None
    
    def _init_azure_clients(self):
        """Initialise les clients Azure"""
        try:
            self.search_client = SearchClient(
                endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
                index_name="penal-affaires-index",
                credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_KEY'))
            )
            logger.info("Client Azure Search initialisé")
        except Exception as e:
            logger.error(f"Erreur initialisation Azure : {e}")
            self.search_client = None
    
    def search(self, query: str, mode: SearchMode = SearchMode.HYBRID, 
               page: int = 1) -> Tuple[List[Document], int]:
        """Recherche dans les documents"""
        results = []
        
        # Recherche Azure si disponible
        if self.search_client and mode != SearchMode.LOCAL:
            try:
                azure_results = self._search_azure(query, mode, page)
                results.extend(azure_results)
            except Exception as e:
                logger.warning(f"Recherche Azure échouée : {e}")
        
        # Recherche locale
        local_results = self._search_local(query)
        results.extend(local_results)
        
        # Pagination
        start = (page - 1) * AppConfig.PAGE_SIZE
        end = start + AppConfig.PAGE_SIZE
        
        return results[start:end], len(results)
    
    def _search_local(self, query: str) -> List[Document]:
        """Recherche locale simple"""
        results = []
        query_lower = query.lower()
        
        for doc in self.local_documents.values():
            if query_lower in doc.content.lower() or query_lower in doc.title.lower():
                results.append(doc)
        
        return results
    
    def _search_azure(self, query: str, mode: SearchMode, page: int) -> List[Document]:
        """Recherche Azure"""
        if not self.search_client:
            return []
        
        search_params = {
            "search_text": query,
            "select": ["id", "title", "content", "metadata"],
            "top": AppConfig.PAGE_SIZE,
            "skip": (page - 1) * AppConfig.PAGE_SIZE
        }
        
        results = self.search_client.search(**search_params)
        
        documents = []
        for result in results:
            doc = Document(
                id=result["id"],
                title=result["title"],
                content=result["content"],
                source="azure",
                metadata=result.get("metadata", {})
            )
            documents.append(doc)
        
        return documents
    
    def add_document(self, title: str, content: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Ajoute un document"""
        doc_id = f"doc_{datetime.now().timestamp()}"
        
        doc = Document(
            id=doc_id,
            title=title,
            content=content,
            metadata=metadata or {}
        )
        
        self.local_documents[doc_id] = doc
        st.session_state.docs_for_analysis.append(doc)
        return doc_id

# ================== ANALYSEUR DE RISQUES AFFAIRES ==================

class RiskAnalyzerAffaires:
    """Analyse des risques spécifique au pénal des affaires"""
    
    def __init__(self):
        self.risk_patterns = {
            'absence_element_intentionnel': {
                'check': lambda d: 'Abus de biens sociaux' in d.qualification_faits,
                'level': 'opportunity',
                'description': 'Élément intentionnel difficile à prouver',
                'strategy': 'Démontrer la poursuite de l\'intérêt social'
            },
            'delegation_valide': {
                'check': lambda d: d.delegation_pouvoirs and d.delegation_pouvoirs.get('valide'),
                'level': 'opportunity',
                'description': 'Délégation de pouvoirs valide',
                'strategy': 'Exonération de responsabilité du dirigeant'
            },
            'programme_conformite': {
                'check': lambda d: d.programme_conformite and d.programme_conformite.get('score', 0) > 4,
                'level': 'opportunity',
                'description': 'Programme de conformité robuste',
                'strategy': 'Négocier CJIP ou atténuation de peine'
            },
            'regularisation_fiscale': {
                'check': lambda d: 'Fraude fiscale' in d.qualification_faits,
                'level': 'opportunity',
                'description': 'Régularisation fiscale possible',
                'strategy': 'Négocier avec l\'administration fiscale'
            }
        }
    
    def analyze(self, dossier: DossierAffaires) -> Dict[str, Any]:
        """Analyse complète des risques"""
        risks = {'critical': [], 'high': [], 'medium': [], 'opportunities': []}
        
        for risk_name, risk_config in self.risk_patterns.items():
            try:
                if risk_config['check'](dossier):
                    risk_entry = {
                        'type': risk_name,
                        'description': risk_config['description'],
                        'level': risk_config['level']
                    }
                    
                    if 'strategy' in risk_config:
                        risk_entry['strategy'] = risk_config['strategy']
                    
                    level = risk_config['level']
                    if level == 'opportunity':
                        risks['opportunities'].append(risk_entry)
                    else:
                        risks[level].append(risk_entry)
                        
            except Exception as e:
                logger.warning(f"Erreur analyse risque {risk_name}: {e}")
        
        return {
            'risks': risks,
            'summary': self._generate_summary(risks),
            'recommendations': self._generate_recommendations(risks)
        }
    
    def _generate_summary(self, risks: Dict[str, List]) -> str:
        """Génère un résumé des risques"""
        opp_count = len(risks.get('opportunities', []))
        
        if opp_count >= 3:
            return f"✅ {opp_count} opportunités de défense identifiées"
        elif opp_count > 0:
            return f"📊 Situation équilibrée avec {opp_count} points favorables"
        else:
            return "⚠️ Peu d'éléments favorables identifiés"
    
    def _generate_recommendations(self, risks: Dict[str, List]) -> List[str]:
        """Génère des recommandations"""
        recommendations = []
        
        for opp in risks.get('opportunities', []):
            if opp.get('strategy'):
                recommendations.append(opp['strategy'])
        
        return recommendations[:3]  # Top 3

# ================== CALCULATEUR D'AMENDES ==================

class CalculateurAmendesAffaires:
    """Calcule les amendes en droit pénal des affaires"""
    
    def __init__(self):
        self.amendes_base = {
            'Abus de biens sociaux': 375000,
            'Corruption': 1000000,
            'Trafic d\'influence': 500000,
            'Fraude fiscale': 500000,
            'Blanchiment': 375000,
            'Faux et usage de faux': 375000,
            'Escroquerie': 375000,
            'Abus de confiance': 375000,
            'Favoritisme': 200000,
            'Prise illégale d\'intérêts': 500000,
            'Travail dissimulé': 45000,
            'Banqueroute': 75000
        }
    
    def calculer_amende(self, infraction: str, is_pm: bool = False, 
                       chiffre_affaires: float = None) -> Dict[str, Any]:
        """Calcule l'amende encourue"""
        
        amende_base = self.amendes_base.get(infraction, 375000)
        amende_pm = amende_base * 5 if is_pm else amende_base
        
        calcul_special = {}
        
        # Calculs spéciaux selon l'infraction
        if infraction == 'Fraude fiscale':
            calcul_special['mode'] = 'Jusqu\'au double du produit de la fraude'
        elif infraction == 'Blanchiment':
            calcul_special['mode'] = 'Jusqu\'à 50% des sommes blanchies'
        elif infraction == 'Corruption' and chiffre_affaires and is_pm:
            calcul_special['mode'] = 'Jusqu\'à 10% du CA moyen'
            calcul_special['montant'] = chiffre_affaires * 0.1
        
        peines_comp = []
        if is_pm:
            peines_comp = [
                "Exclusion des marchés publics (5 ans max)",
                "Interdiction de faire appel public à l'épargne",
                "Confiscation",
                "Affichage de la décision"
            ]
        
        return {
            'amende_base': amende_base if not is_pm else amende_pm,
            'calcul_special': calcul_special,
            'peines_complementaires': peines_comp
        }

# ================== GESTIONNAIRE DE PIÈCES ==================

class GestionnairePieces:
    """Gestionnaire des pièces versées aux débats"""
    
    def __init__(self, citation_manager: CitationManager):
        self.pieces: Dict[int, PieceVersee] = {}
        self.numero_actuel = 0
        self.citation_manager = citation_manager
    
    def verser_piece(self, titre: str, contenu: str, type_piece: str,
                    dossier_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> int:
        """Verse une nouvelle pièce"""
        self.numero_actuel += 1
        
        citation = self.citation_manager.format_citation(type_piece, metadata or {})
        
        piece = PieceVersee(
            numero=self.numero_actuel,
            titre=titre,
            contenu=contenu,
            type=type_piece,
            dossier_id=dossier_id,
            citation_complete=citation
        )
        
        self.pieces[self.numero_actuel] = piece
        return self.numero_actuel
    
    def generer_bordereau(self) -> str:
        """Génère le bordereau de communication"""
        bordereau = "BORDEREAU DE COMMUNICATION DE PIÈCES\n"
        bordereau += "=" * 50 + "\n\n"
        bordereau += f"Date : {datetime.now().strftime('%d/%m/%Y')}\n\n"
        
        for piece in sorted(self.pieces.values(), key=lambda x: x.numero):
            bordereau += f"{piece.numero}. {piece.titre}\n"
            if piece.citation_complete:
                bordereau += f"   {piece.citation_complete}\n"
        
        bordereau += f"\n\nTOTAL : {len(self.pieces)} pièces\n"
        
        return bordereau

# ================== ASSISTANT RÉDACTION AFFAIRES ==================

class AssistantRedactionAffaires:
    """Assistant pour la rédaction d'actes en pénal des affaires"""
    
    def __init__(self):
        self.templates = {
            'demande_audition_libre': {
                'titre': 'Demande d\'audition libre',
                'contenu': """Maître [NOM]
Avocat au Barreau de [VILLE]
À l'attention de [DESTINATAIRE]
[SERVICE]
Objet : Demande d'audition libre
Procédure n° [NUMERO]
Monsieur/Madame,
J'ai l'honneur de vous informer que M./Mme [CLIENT], dirigeant(e) de la société [SOCIETE], 
souhaite être entendu(e) dans le cadre de l'enquête référencée ci-dessus.
Mon client(e) se tient à votre disposition pour une audition libre et sollicite 
communication préalable des pièces de la procédure (art. 61-1 CPP).
Disponibilités proposées :
- [DATE 1]
- [DATE 2]
- [DATE 3]
Je vous prie d'agréer, Monsieur/Madame, l'expression de ma considération distinguée.
Maître [NOM]"""
            },
            
            'conclusions_relaxe_abs': {
                'titre': 'Conclusions aux fins de relaxe - ABS',
                'contenu': """CONCLUSIONS AUX FINS DE RELAXE
POUR : [CLIENT]
       [SOCIETE]
CONTRE : LE MINISTÈRE PUBLIC
I. SUR L'ABSENCE D'ÉLÉMENT MATÉRIEL
L'abus de biens sociaux suppose un usage contraire à l'intérêt social.
En l'espèce, les actes ont été réalisés dans l'intérêt exclusif de la société.
II. SUR L'ABSENCE D'ÉLÉMENT INTENTIONNEL
Mon client a agi en toute transparence et bonne foi.
Aucun enrichissement personnel n'est démontré.
III. SUR LA PRESCRIPTION (subsidiairement)
Les faits se prescrivent par 6 ans à compter de leur révélation.
PAR CES MOTIFS
- PRONONCER la relaxe"""
            },
            
            'memoire_cjip': {
                'titre': 'Mémoire CJIP',
                'contenu': """MÉMOIRE EN VUE D'UNE CJIP
POUR : [SOCIETE]
I. ÉLIGIBILITÉ
- Personne morale
- Infractions éligibles
- Absence de condamnation préalable
II. INTÉRÊT PUBLIC
- Réparation rapide
- Économie judiciaire
III. ENGAGEMENTS
- Amende : [MONTANT]
- Programme de conformité renforcé
- Audit externe
IV. GARANTIES
- Validation CA
- Budget dédié"""
            }
        }

# ================== EXPORT PROFESSIONNEL ==================

class ProfessionalExporter:
    """Export en format professionnel"""
    
    def __init__(self, letterhead: Dict[str, Any] = None):
        self.letterhead = letterhead or {}
    
    def export_to_word(self, content: str, title: str = None) -> Optional[bytes]:
        """Exporte en format Word"""
        
        if not DOCX_AVAILABLE:
            st.warning("Module python-docx non installé")
            return None
        
        try:
            doc = DocxDocument()
            
            # En-tête si configuré
            if self.letterhead:
                header = doc.sections[0].header
                header_para = header.paragraphs[0]
                header_para.text = self.letterhead.get('nom', '')
                header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Titre
            if title:
                doc.add_heading(title, 0)
            
            # Contenu
            for line in content.split('\n'):
                if line.strip():
                    doc.add_paragraph(line)
            
            # Export
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur export Word : {e}")
            return None

# ================== GESTIONNAIRE PRINCIPAL ==================

class GestionnaireAffaires:
    """Gestionnaire principal des dossiers pénaux des affaires"""
    
    def __init__(self):
        self.dossiers: Dict[str, DossierAffaires] = {}
        self.citation_manager = CitationManager()
        self.gestionnaire_pieces = GestionnairePieces(self.citation_manager)
        self.risk_analyzer = RiskAnalyzerAffaires()
        self.calculateur_amendes = CalculateurAmendesAffaires()
        self.assistant_redaction = AssistantRedactionAffaires()
        self.gestionnaire_multi_victimes = GestionnaireMultiVictimes()
        self.llm_manager = None  # Sera initialisé si configuré
        self.adaptateur_plainte = None
    
    def init_llm_manager(self):
        """Initialise le gestionnaire LLM"""
        if not self.llm_manager:
            self.llm_manager = MultiLLMManager()
            self.adaptateur_plainte = AdaptateurPlainteIA(self.llm_manager)
    
    def creer_dossier(self, dossier: DossierAffaires) -> str:
        """Crée un nouveau dossier"""
        dossier_id = f"{dossier.numero_parquet}_{datetime.now().timestamp()}"
        self.dossiers[dossier_id] = dossier
        return dossier_id
    
    def analyser_dossier(self, dossier_id: str) -> Dict[str, Any]:
        """Analyse complète d'un dossier"""
        
        if dossier_id not in self.dossiers:
            return {}
        
        dossier = self.dossiers[dossier_id]
        
        # Analyse des risques
        risk_analysis = self.risk_analyzer.analyze(dossier)
        
        # Calcul des amendes
        amendes = {}
        for infraction in dossier.qualification_faits:
            is_pm = dossier.client_type == "PM"
            ca = dossier.client_info.get('chiffre_affaires') if is_pm else None
            amendes[infraction] = self.calculateur_amendes.calculer_amende(
                infraction, is_pm, ca
            )
        
        return {
            'risk_analysis': risk_analysis,
            'amendes': amendes,
            'prescription': dossier.calculer_prescription()
        }

# ================== GESTIONNAIRES SINGLETON ==================

@st.cache_resource
def get_managers():
    """Crée et retourne les gestionnaires singleton"""
    return {
        'gestionnaire': GestionnaireAffaires(),
        'doc_manager': DocumentManager(),
        'exporter': ProfessionalExporter()
    }

# ================== INITIALISATION ==================

initialize_session_state()
managers = get_managers()
gestionnaire = managers['gestionnaire']
doc_manager = managers['doc_manager']
exporter = managers['exporter']

# Initialiser le gestionnaire LLM si configuré
gestionnaire.init_llm_manager()

# ================== INTERFACE PRINCIPALE ==================

# Créer les tabs principaux
tabs = st.tabs([
    "📂 Dossiers",
    "🔍 Recherche",
    "🤖 IA Multi-LLM",
    "✍️ Rédaction", 
    "📎 Pièces",
    "☁️ Azure Blob",
    "⚙️ Configuration"
])

# ================== TAB 1: GESTION DES DOSSIERS ==================

with tabs[0]:
    st.header("📂 Gestion des dossiers")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("➕ Nouveau dossier")
        
        with st.form("nouveau_dossier"):
            numero_parquet = st.text_input("N° Parquet", placeholder="2024/12345")
            
            # Type de client
            client_type = st.radio("Type de client", ["Personne physique", "Personne morale"])
            
            if client_type == "Personne physique":
                client_nom = st.text_input("Nom et prénom")
                client_info = {}
            else:
                client_nom = st.text_input("Dénomination sociale")
                col_pm1, col_pm2 = st.columns(2)
                with col_pm1:
                    forme_juridique = st.selectbox("Forme", ["SAS", "SARL", "SA", "SNC"])
                    siren = st.text_input("SIREN")
                with col_pm2:
                    ca = st.number_input("CA annuel (€)", min_value=0, step=100000)
                    effectif = st.number_input("Effectif", min_value=0)
                
                client_info = {
                    'forme_juridique': forme_juridique,
                    'siren': siren,
                    'chiffre_affaires': ca,
                    'effectif': effectif
                }
            
            procedure_type = st.selectbox(
                "Type de procédure",
                [p.value for p in ProcedureAffaires]
            )
            
            qualifications = st.multiselect(
                "Infractions",
                [inf.value for inf in InfractionAffaires]
            )
            
            date_faits = st.date_input("Date des faits")
            montant_prejudice = st.number_input("Préjudice allégué (€)", min_value=0)
            
            if st.form_submit_button("Créer le dossier", type="primary"):
                if numero_parquet and client_nom:
                    dossier = DossierAffaires(
                        numero_parquet=numero_parquet,
                        numero_instruction=None,
                        client_nom=client_nom,
                        client_type="PM" if client_type == "Personne morale" else "PP",
                        client_info=client_info,
                        qualification_faits=qualifications,
                        date_faits=datetime.combine(date_faits, datetime.min.time()),
                        procedure_type=ProcedureAffaires(procedure_type),
                        magistrat=None,
                        montant_prejudice=montant_prejudice
                    )
                    
                    dossier_id = gestionnaire.creer_dossier(dossier)
                    st.session_state.dossier_actif = dossier_id
                    st.session_state.dossiers[dossier_id] = dossier
                    st.success(f"✅ Dossier {numero_parquet} créé")
                    st.rerun()
    
    with col2:
        st.subheader("📁 Dossiers actifs")
        
        if st.session_state.dossiers:
            for dossier_id, dossier in st.session_state.dossiers.items():
                with st.container():
                    st.markdown('<div class="dossier-card">', unsafe_allow_html=True)
                    
                    col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
                    
                    with col_d1:
                        st.markdown(f"**{dossier.numero_parquet}**")
                        st.write(f"**Client :** {dossier.client_nom}")
                        if dossier.client_type == "PM":
                            st.caption(f"{dossier.client_info.get('forme_juridique', 'PM')}")
                        
                        # Infractions
                        infractions_str = ", ".join(dossier.qualification_faits[:2])
                        if len(dossier.qualification_faits) > 2:
                            infractions_str += f" (+{len(dossier.qualification_faits)-2})"
                        st.write(f"**Infractions :** {infractions_str}")
                        
                        # Victimes
                        if dossier.victimes:
                            st.caption(f"👥 {len(dossier.victimes)} victime(s)")
                        
                        # Badge procédure
                        badge_class = f"badge-{dossier.procedure_type.name.lower()}"
                        st.markdown(
                            f'<span class="procedure-badge {badge_class}">'
                            f'{dossier.procedure_type.value}</span>',
                            unsafe_allow_html=True
                        )
                    
                    with col_d2:
                        # Prescription
                        prescription = dossier.calculer_prescription()
                        if prescription['prescrit']:
                            st.error("⚠️ PRESCRIT")
                        else:
                            jours = prescription['jours_restants']
                            if jours < 180:
                                st.warning(f"⏰ Prescription: {jours}j")
                            else:
                                st.info(f"📅 Prescription: {jours}j")
                        
                        # Enjeux
                        if dossier.montant_prejudice:
                            st.metric("Enjeux", f"{dossier.montant_prejudice:,.0f}€")
                    
                    with col_d3:
                        if st.button("📂 Ouvrir", key=f"open_{dossier_id}"):
                            st.session_state.dossier_actif = dossier_id
                            st.rerun()
                        
                        if st.button("🤖 Analyser", key=f"analyze_{dossier_id}"):
                            with st.spinner("Analyse..."):
                                analysis = gestionnaire.analyser_dossier(dossier_id)
                                st.session_state[f"analysis_{dossier_id}"] = analysis
                                st.success("✅ Analyse terminée")
                    
                    # Afficher l'analyse si disponible
                    if f"analysis_{dossier_id}" in st.session_state:
                        with st.expander("📊 Résultats de l'analyse"):
                            analysis = st.session_state[f"analysis_{dossier_id}"]
                            
                            st.write(f"**Synthèse :** {analysis['risk_analysis']['summary']}")
                            
                            # Recommandations
                            if analysis['risk_analysis']['recommendations']:
                                st.write("**Stratégies recommandées :**")
                                for rec in analysis['risk_analysis']['recommendations']:
                                    st.write(f"• {rec}")
                            
                            # Amendes
                            if analysis['amendes']:
                                st.write("**Amendes encourues :**")
                                for inf, amende in analysis['amendes'].items():
                                    st.write(f"• {inf}: {amende['amende_base']:,.0f}€")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Aucun dossier créé")

# ================== TAB 2: RECHERCHE ==================

with tabs[1]:
    st.header("🔍 Recherche et analyse")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Recherche jurisprudence")
        
        query = st.text_input(
            "Rechercher", 
            placeholder="Ex: abus biens sociaux élément intentionnel..."
        )
        
        search_mode = st.selectbox(
            "Mode",
            [mode.value for mode in SearchMode]
        )
        
        if st.button("🔍 Rechercher", type="primary"):
            if query:
                with st.spinner("Recherche..."):
                    results, total = doc_manager.search(
                        query=query,
                        mode=SearchMode(search_mode),
                        page=st.session_state.current_page
                    )
                    
                    if results:
                        st.success(f"✅ {total} résultats")
                        
                        for result in results:
                            with st.expander(f"📄 {result.title}"):
                                st.write(result.content[:500] + "...")
                                
                                if st.button("📎 Verser aux débats", key=f"verser_{result.id}"):
                                    num = gestionnaire.gestionnaire_pieces.verser_piece(
                                        titre=result.title,
                                        contenu=result.content,
                                        type_piece='jurisprudence',
                                        dossier_id=st.session_state.dossier_actif
                                    )
                                    st.success(f"✅ Pièce n°{num}")
                    else:
                        st.warning("Aucun résultat")
    
    with col2:
        st.subheader("🎯 Recherches suggérées")
        
        for categorie, recherches in SEARCH_PROMPTS_AFFAIRES.items():
            with st.expander(categorie):
                for type_recherche, prompts in recherches.items():
                    st.markdown(f"**{type_recherche}**")
                    for prompt in prompts[:2]:  # Limiter à 2
                        if st.button(f"🔍 {prompt[:30]}...", key=f"prompt_{prompt[:20]}"):
                            st.session_state.search_query = prompt

# ================== TAB 3: IA MULTI-LLM ==================

with tabs[2]:
    st.header("🤖 Assistant IA Multi-LLM")
    
    # Initialiser le manager
    if 'llm_manager' not in st.session_state:
        if gestionnaire.llm_manager:
            st.session_state.llm_manager = gestionnaire.llm_manager
        else:
            st.session_state.llm_manager = None
    
    llm_manager = st.session_state.llm_manager
    
    if not llm_manager:
        st.warning("⚠️ Aucun LLM configuré. Vérifiez vos clés API dans le fichier .env")
    else:
        # Sélection des LLMs
        col1_llm, col2_llm = st.columns([1, 2])
        
        with col1_llm:
            st.subheader("🎯 Configuration")
            
            # LLMs disponibles
            available_llms = list(llm_manager.clients.keys())
            
            if not available_llms:
                st.error("Aucun LLM configuré. Vérifiez vos clés API.")
            else:
                st.success(f"✅ {len(available_llms)} LLMs disponibles")
                
                # Mode de requête
                query_mode = st.radio(
                    "Mode d'interrogation",
                    ["Un seul LLM", "Plusieurs LLMs", "Tous les LLMs"]
                )
                
                selected_llms = []
                
                if query_mode == "Un seul LLM":
                    selected_llm = st.selectbox(
                        "Choisir le LLM",
                        available_llms,
                        format_func=lambda x: x.value
                    )
                    selected_llms = [selected_llm]
                
                elif query_mode == "Plusieurs LLMs":
                    selected_llms = st.multiselect(
                        "Choisir les LLMs",
                        available_llms,
                        format_func=lambda x: x.value
                    )
                
                else:  # Tous les LLMs
                    selected_llms = available_llms
                
                # Options de fusion
                enable_fusion = False
                fusion_llm = None
                
                if len(selected_llms) > 1:
                    st.divider()
                    
                    enable_fusion = st.checkbox("🔀 Activer la fusion des réponses", value=True)
                    
                    if enable_fusion:
                        fusion_llm = st.selectbox(
                            "LLM pour la fusion",
                            available_llms,
                            format_func=lambda x: x.value,
                            help="Le LLM qui fusionnera toutes les réponses"
                        )
            
            # Contexte du dossier
            st.divider()
            
            use_dossier_context = st.checkbox("📂 Utiliser le contexte du dossier actif")
            
            if use_dossier_context and st.session_state.dossier_actif:
                dossier = st.session_state.dossiers.get(st.session_state.dossier_actif)
                if dossier:
                    st.info(f"Dossier : {dossier.numero_parquet}")
                    st.caption(f"Client : {dossier.client_nom}")
                    st.caption(f"Infractions : {', '.join(dossier.qualification_faits[:2])}")
        
        with col2_llm:
            st.subheader("💬 Requête")
            
            # Templates de prompts
            prompt_templates = {
                "Analyse juridique": """Analyse juridique approfondie :
                
Contexte : {context}
Question : {question}
Fournis une analyse détaillée incluant :
1. Les éléments constitutifs de l'infraction
2. Les moyens de défense possibles
3. La jurisprudence pertinente
4. Les risques et opportunités
5. Une stratégie recommandée""",
                
                "Adaptation de plainte": """Adapte cette plainte pour un nouveau plaignant :
Plainte originale :
{original}
Nouveau plaignant : {nouveau_plaignant}
Préjudice spécifique : {prejudice}
Adapte en conservant la structure juridique mais en personnalisant pour ce plaignant.""",
                
                "Recherche de jurisprudence": """Recherche la jurisprudence pertinente pour :
                
Infraction : {infraction}
Point de droit : {point_droit}
Cite les arrêts les plus récents et pertinents avec leurs apports.""",
                
                "Stratégie de défense": """Élabore une stratégie de défense pour :
Client : {client}
Infractions reprochées : {infractions}
Éléments favorables : {elements_favorables}
Éléments défavorables : {elements_defavorables}
Propose une stratégie complète et argumentée."""
            }
            
            # Sélection du template
            use_template = st.checkbox("📋 Utiliser un template")
            
            if use_template:
                template_name = st.selectbox(
                    "Template",
                    list(prompt_templates.keys())
                )
                
                # Variables du template
                template = prompt_templates[template_name]
                variables = re.findall(r'\{(\w+)\}', template)
                
                variable_values = {}
                for var in variables:
                    if var == 'context' and use_dossier_context and 'dossier' in locals():
                        # Auto-remplir le contexte
                        context = f"Dossier {dossier.numero_parquet}, "
                        context += f"Client: {dossier.client_nom}, "
                        context += f"Infractions: {', '.join(dossier.qualification_faits)}"
                        variable_values[var] = context
                    else:
                        variable_values[var] = st.text_area(
                            f"{var.replace('_', ' ').title()}",
                            height=100 if var in ['original', 'prejudice'] else 50
                        )
                
                # Construire le prompt final
                try:
                    prompt = template.format(**variable_values)
                except KeyError:
                    prompt = template
                    st.warning("Remplissez toutes les variables du template")
            else:
                # Prompt libre
                prompt = st.text_area(
                    "Votre question",
                    height=200,
                    placeholder="Posez votre question juridique..."
                )
            
            # System prompt optionnel
            with st.expander("⚙️ Instructions système (optionnel)"):
                system_prompt = st.text_area(
                    "Instructions pour l'IA",
                    value="Tu es un avocat expert en droit pénal des affaires français. "
                          "Fournis des analyses précises avec références légales.",
                    height=100
                )
            
            # Bouton pour lancer la requête
            if st.button("🚀 Interroger les LLMs", type="primary", disabled=not selected_llms):
                if prompt:
                    with st.spinner(f"Interrogation de {len(selected_llms)} LLM(s)..."):
                        
                        # Mesurer le temps
                        start_time = datetime.now()
                        
                        # Interroger les LLMs
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        results = loop.run_until_complete(
                            llm_manager.query_multiple_llms(
                                selected_llms,
                                prompt,
                                system_prompt
                            )
                        )
                        
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        # Stocker les résultats
                        st.session_state.llm_results = results
                        st.session_state.llm_duration = duration
                        st.session_state.llm_prompt = prompt
                        
                        st.success(f"✅ Terminé en {duration:.1f} secondes")
                else:
                    st.error("Entrez une question")
            
            # Affichage des résultats
            if st.session_state.get('llm_results'):
                st.divider()
                st.subheader("📊 Résultats")
                
                results = st.session_state.llm_results
                successful_results = [r for r in results if r['success']]
                
                # Métriques
                col_m1, col_m2, col_m3 = st.columns(3)
                
                with col_m1:
                    st.metric("Réponses reçues", f"{len(successful_results)}/{len(results)}")
                
                with col_m2:
                    st.metric("Temps total", f"{st.session_state.llm_duration:.1f}s")
                
                with col_m3:
                    total_tokens = sum(
                        r.get('usage', {}).get('total_tokens', 0) 
                        for r in successful_results 
                        if r.get('usage')
                    )
                    if total_tokens:
                        st.metric("Tokens utilisés", f"{total_tokens:,}")
                
                # Tabs pour les réponses
                tab_names = [r['provider'] for r in successful_results]
                if len(successful_results) > 1 and enable_fusion:
                    tab_names.append("🔀 Fusion")
                
                response_tabs = st.tabs(tab_names)
                
                # Afficher chaque réponse
                for i, (tab, result) in enumerate(zip(response_tabs, successful_results)):
                    with tab:
                        if result['success']:
                            # Options d'action
                            col_a1, col_a2, col_a3 = st.columns(3)
                            
                            with col_a1:
                                if st.button("📋 Copier", key=f"copy_{i}"):
                                    st.code(result['response'])
                            
                            with col_a2:
                                if st.button("📎 Verser aux débats", key=f"verser_llm_{i}"):
                                    num = gestionnaire.gestionnaire_pieces.verser_piece(
                                        titre=f"Analyse IA - {result['provider']}",
                                        contenu=result['response'],
                                        type_piece='rapport',
                                        dossier_id=st.session_state.dossier_actif
                                    )
                                    st.success(f"✅ Pièce n°{num}")
                            
                            with col_a3:
                                if st.button("✏️ Éditer", key=f"edit_{i}"):
                                    st.session_state.document_content = result['response']
                                    st.info("📝 Chargé dans l'éditeur")
                            
                            # Afficher la réponse
                            st.markdown('<div class="llm-response">', unsafe_allow_html=True)
                            st.markdown(result['response'])
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Métadonnées
                            with st.expander("📊 Détails"):
                                if result.get('usage'):
                                    st.json(result['usage'])
                                if result.get('citations'):
                                    st.write("**Sources :**")
                                    for citation in result['citations']:
                                        st.write(f"- {citation}")
                        else:
                            st.error(f"❌ Erreur : {result.get('error', 'Inconnue')}")
                
                # Tab fusion si activée
                if len(successful_results) > 1 and enable_fusion:
                    with response_tabs[-1]:
                        if st.button("🔀 Générer la fusion", type="primary"):
                            with st.spinner("Fusion en cours..."):
                                fusion_result = llm_manager.fusion_responses(
                                    successful_results,
                                    fusion_llm
                                )
                                
                                st.session_state.fusion_result = fusion_result
                                st.success("✅ Fusion terminée")
                        
                        if st.session_state.get('fusion_result'):
                            # Options pour la fusion
                            col_f1, col_f2, col_f3 = st.columns(3)
                            
                            with col_f1:
                                if st.button("📋 Copier fusion"):
                                    st.code(st.session_state.fusion_result)
                            
                            with col_f2:
                                if st.button("📎 Verser fusion"):
                                    num = gestionnaire.gestionnaire_pieces.verser_piece(
                                        titre="Analyse IA - Synthèse multi-LLM",
                                        contenu=st.session_state.fusion_result,
                                        type_piece='rapport',
                                        dossier_id=st.session_state.dossier_actif
                                    )
                                    st.success(f"✅ Pièce n°{num}")
                            
                            with col_f3:
                                if st.button("✏️ Éditer fusion"):
                                    st.session_state.document_content = st.session_state.fusion_result
                                    st.info("📝 Chargé dans l'éditeur")
                            
                            # Afficher la fusion
                            st.markdown("### 🔀 Synthèse fusionnée")
                            st.markdown('<div class="llm-response">', unsafe_allow_html=True)
                            st.markdown(st.session_state.fusion_result)
                            st.markdown('</div>', unsafe_allow_html=True)
                
                # Comparaison côte à côte
                if len(successful_results) > 1:
                    with st.expander("🔄 Comparaison côte à côte"):
                        cols = st.columns(len(successful_results[:3]))  # Max 3 colonnes
                        
                        for col, result in zip(cols, successful_results[:3]):
                            with col:
                                st.markdown(f"**{result['provider']}**")
                                st.markdown(result['response'][:500] + "...")

# ================== TAB 4: RÉDACTION ==================

with tabs[3]:
    st.header("✍️ Rédaction d'actes")
    
    # Nouveau : Section adaptation multi-victimes
    adaptation_enabled = st.checkbox("🔄 Adapter une plainte pour plusieurs victimes")
    
    if adaptation_enabled:
        st.subheader("Adaptation multi-victimes")
        
        col1_adapt, col2_adapt = st.columns([1, 1])
        
        with col1_adapt:
            st.markdown("### 1️⃣ Document source")
            
            # Sélection de la plainte originale
            if st.session_state.docs_for_analysis:
                plainte_source = st.selectbox(
                    "Plainte à adapter",
                    st.session_state.docs_for_analysis,
                    format_func=lambda x: x.title
                )
                
                if st.button("📄 Charger cette plainte"):
                    st.session_state.plainte_originale = plainte_source.content
                    st.success("✅ Plainte chargée")
            
            # Option de charger depuis un fichier
            uploaded_file = st.file_uploader(
                "Ou télécharger une plainte",
                type=['txt', 'docx'],
                key="plainte_upload"
            )
            
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                st.session_state.plainte_originale = content
                st.success("✅ Fichier chargé")
        
        with col2_adapt:
            st.markdown("### 2️⃣ Nouvelles victimes")
            
            # Formulaire pour ajouter des victimes
            with st.form("nouvelle_victime"):
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                prejudice = st.text_area("Description du préjudice")
                montant = st.number_input("Montant du préjudice (€)", min_value=0.0)
                
                elements_spec = st.text_area(
                    "Éléments spécifiques (un par ligne)",
                    help="Ex: Perte de chance, atteinte à l'image, etc."
                )
                
                if st.form_submit_button("➕ Ajouter cette victime"):
                    victime = VictimeInfo(
                        nom=nom,
                        prenom=prenom,
                        prejudice_subi=prejudice,
                        montant_prejudice=montant,
                        elements_specifiques=elements_spec.split('\n') if elements_spec else [],
                        documents_support=[]
                    )
                    
                    if 'victimes_adapter' not in st.session_state:
                        st.session_state.victimes_adapter = []
                    
                    st.session_state.victimes_adapter.append(victime)
                    st.success(f"✅ {nom} {prenom} ajouté(e)")
                    st.rerun()
        
        # Liste des victimes à traiter
        if st.session_state.get('victimes_adapter'):
            st.markdown("### 👥 Victimes à traiter")
            
            for i, victime in enumerate(st.session_state.victimes_adapter):
                col1_v, col2_v, col3_v = st.columns([2, 2, 1])
                
                with col1_v:
                    st.write(f"**{victime.nom} {victime.prenom}**")
                
                with col2_v:
                    st.write(f"Préjudice: {victime.montant_prejudice:,.0f}€")
                
                with col3_v:
                    if st.button("🗑️", key=f"del_victime_{i}"):
                        st.session_state.victimes_adapter.pop(i)
                        st.rerun()
            
            # Choix du mode d'adaptation
            adaptation_mode = st.radio(
                "Mode d'adaptation",
                ["🤖 Avec IA (recommandé)", "📝 Sans IA (basique)"]
            )
            
            # Bouton pour générer toutes les plaintes
            if st.button("🚀 Générer toutes les plaintes adaptées", type="primary"):
                if st.session_state.get('plainte_originale'):
                    with st.spinner("Adaptation en cours..."):
                        
                        # Créer l'adaptateur
                        if not gestionnaire.adaptateur_plainte:
                            gestionnaire.adaptateur_plainte = AdaptateurPlainteIA()
                        
                        adaptateur = gestionnaire.adaptateur_plainte
                        
                        # Adapter pour chaque victime
                        plaintes_adaptees = {}
                        
                        if adaptation_mode.startswith("🤖") and gestionnaire.llm_manager:
                            # Adaptation avec IA
                            victime_orig = VictimeInfo(
                                nom="[NOM]",
                                prenom="[PRENOM]",
                                prejudice_subi="[PREJUDICE]",
                                montant_prejudice=0,
                                elements_specifiques=[],
                                documents_support=[]
                            )
                            
                            contexte = {}
                            if st.session_state.dossier_actif:
                                dossier = st.session_state.dossiers.get(st.session_state.dossier_actif)
                                if dossier:
                                    contexte = {
                                        'numero_parquet': dossier.numero_parquet,
                                        'infractions': dossier.qualification_faits,
                                        'date_faits': dossier.date_faits.strftime('%d/%m/%Y')
                                    }
                            
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            plaintes_adaptees = loop.run_until_complete(
                                adaptateur.adapter_plainte(
                                    st.session_state.plainte_originale,
                                    victime_orig,
                                    st.session_state.victimes_adapter,
                                    contexte
                                )
                            )
                        else:
                            # Adaptation basique
                            for victime in st.session_state.victimes_adapter:
                                plainte_adaptee = adaptateur._adaptation_basique(
                                    st.session_state.plainte_originale,
                                    victime
                                )
                                
                                plaintes_adaptees[f"{victime.nom}_{victime.prenom}"] = plainte_adaptee
                        
                        st.session_state.plaintes_adaptees = plaintes_adaptees
                        st.success(f"✅ {len(plaintes_adaptees)} plaintes générées")
                else:
                    st.error("Chargez d'abord une plainte source")
        
        # Affichage et export des plaintes adaptées
        if st.session_state.get('plaintes_adaptees'):
            st.markdown("### 📄 Plaintes générées")
            
            for victime_id, plainte in st.session_state.plaintes_adaptees.items():
                with st.expander(f"Plainte pour {victime_id}"):
                    st.text_area(
                        "Contenu",
                        value=plainte[:1000] + "...",
                        height=300,
                        key=f"preview_{victime_id}"
                    )
                    
                    col_exp1, col_exp2, col_exp3 = st.columns(3)
                    
                    with col_exp1:
                        st.download_button(
                            "💾 Télécharger TXT",
                            plainte,
                            f"plainte_{victime_id}.txt",
                            key=f"dl_txt_{victime_id}"
                        )
                    
                    with col_exp2:
                        if st.button("📄 Export Word", key=f"word_{victime_id}"):
                            doc_bytes = exporter.export_to_word(
                                plainte,
                                f"Plainte - {victime_id}"
                            )
                            if doc_bytes:
                                st.download_button(
                                    "💾 DOCX",
                                    doc_bytes,
                                    f"plainte_{victime_id}.docx",
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_docx_{victime_id}"
                                )
                    
                    with col_exp3:
                        if st.button("📎 Verser aux débats", key=f"verser_plainte_{victime_id}"):
                            num = gestionnaire.gestionnaire_pieces.verser_piece(
                                titre=f"Plainte {victime_id}",
                                contenu=plainte,
                                type_piece='plainte',
                                dossier_id=st.session_state.dossier_actif
                            )
                            st.success(f"✅ Pièce n°{num}")
            
            # Export groupé
            if st.button("📦 Exporter toutes les plaintes"):
                import zipfile
                import io
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for victime_id, plainte in st.session_state.plaintes_adaptees.items():
                        zip_file.writestr(f"plainte_{victime_id}.txt", plainte)
                
                zip_buffer.seek(0)
                
                st.download_button(
                    "💾 Télécharger ZIP",
                    zip_buffer.getvalue(),
                    f"plaintes_adaptees_{datetime.now().strftime(AppConfig.EXPORT_FORMAT)}.zip",
                    "application/zip"
                )
    
    # Section rédaction classique
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 Modèles")
        
        template_key = st.selectbox(
            "Type de document",
            list(gestionnaire.assistant_redaction.templates.keys()),
            format_func=lambda x: gestionnaire.assistant_redaction.templates[x]['titre']
        )
        
        if st.button("📋 Utiliser ce modèle", type="primary"):
            template = gestionnaire.assistant_redaction.templates[template_key]
            st.session_state.document_content = template['contenu']
            st.success("✅ Modèle chargé")
    
    with col2:
        st.subheader("✏️ Éditeur")
        
        # Éditeur
        st.session_state.document_content = st.text_area(
            "Document",
            value=st.session_state.document_content,
            height=600
        )
        
        # Export
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if st.button("💾 Export TXT"):
                st.download_button(
                    "Télécharger",
                    st.session_state.document_content,
                    f"document_{datetime.now().strftime(AppConfig.EXPORT_FORMAT)}.txt"
                )
        
        with col_exp2:
            if st.button("📄 Export Word"):
                if st.session_state.letterhead:
                    doc_bytes = exporter.export_to_word(
                        st.session_state.document_content,
                        "Document juridique"
                    )
                    if doc_bytes:
                        st.download_button(
                            "Télécharger DOCX",
                            doc_bytes,
                            f"document_{datetime.now().strftime(AppConfig.EXPORT_FORMAT)}.docx",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.warning("Configurez votre en-tête")

# ================== TAB 5: PIÈCES ==================

with tabs[4]:
    st.header("📎 Gestion des pièces")
    
    pieces = gestionnaire.gestionnaire_pieces.pieces
    
    if pieces:
        # Liste des pièces
        for piece in pieces.values():
            with st.expander(f"📄 Pièce n°{piece.numero} - {piece.titre}"):
                if piece.citation_complete:
                    st.code(piece.citation_complete)
                
                st.write(piece.contenu[:300] + "..." if len(piece.contenu) > 300 else piece.contenu)
                
                if st.button(f"🗑️ Retirer", key=f"remove_{piece.numero}"):
                    del gestionnaire.gestionnaire_pieces.pieces[piece.numero]
                    st.rerun()
        
        # Bordereau
        if st.button("📋 Générer le bordereau", type="primary"):
            bordereau = gestionnaire.gestionnaire_pieces.generer_bordereau()
            st.text_area("Bordereau", value=bordereau, height=400)
            
            st.download_button(
                "💾 Télécharger",
                bordereau,
                f"bordereau_{datetime.now().strftime(AppConfig.EXPORT_FORMAT)}.txt"
            )
    else:
        st.info("Aucune pièce versée")

# ================== TAB 6: AZURE BLOB ==================

with tabs[5]:
    st.header("☁️ Azure Blob Storage")
    
    if not doc_manager.azure_blob_manager.blob_service_client:
        st.warning("⚠️ Azure Blob Storage non configuré. Ajoutez AZURE_STORAGE_CONNECTION_STRING dans le fichier .env")
    else:
        col1_blob, col2_blob = st.columns([1, 2])
        
        with col1_blob:
            st.subheader("📁 Navigation")
            
            # Sélection du container
            containers = doc_manager.azure_blob_manager.list_containers()
            
            if containers:
                selected_container = st.selectbox(
                    "Container",
                    containers,
                    key="azure_container"
                )
                
                # Navigation dans les dossiers
                if 'azure_current_path' not in st.session_state:
                    st.session_state.azure_current_path = ""
                
                # Afficher le chemin actuel
                if st.session_state.azure_current_path:
                    st.caption(f"📍 {st.session_state.azure_current_path}")
                    
                    # Bouton retour
                    if st.button("⬆️ Dossier parent"):
                        parts = st.session_state.azure_current_path.rstrip('/').split('/')
                        if len(parts) > 1:
                            st.session_state.azure_current_path = '/'.join(parts[:-1]) + '/'
                        else:
                            st.session_state.azure_current_path = ""
                        st.rerun()
                
                # Lister le contenu
                items = doc_manager.azure_blob_manager.list_folders(
                    selected_container,
                    st.session_state.azure_current_path
                )
                
                if items:
                    st.write("**Contenu :**")
                    
                    # Afficher les dossiers et fichiers
                    for item in items:
                        if item['type'] == 'folder':
                            if st.button(f"📁 {item['name']}", key=f"folder_{item['path']}"):
                                st.session_state.azure_current_path = item['path']
                                st.rerun()
                        else:
                            # Afficher les fichiers
                            file_size = item['size'] / 1024  # Ko
                            if file_size > 1024:
                                file_size = f"{file_size/1024:.1f} Mo"
                            else:
                                file_size = f"{file_size:.1f} Ko"
                            
                            st.caption(f"📄 {item['name']} ({file_size})")
                
                # Options d'extraction
                st.divider()
                
                recursive = st.checkbox("🔄 Inclure les sous-dossiers", value=True)
                
                if st.button("📥 Extraire les documents", type="primary"):
                    if st.session_state.azure_current_path:
                        with st.spinner("Extraction en cours..."):
                            documents = doc_manager.azure_blob_manager.extract_folder_documents(
                                selected_container,
                                st.session_state.azure_current_path,
                                recursive=recursive
                            )
                            
                            if documents:
                                # Ajouter aux documents locaux
                                for doc in documents:
                                    doc_manager.local_documents[doc.id] = doc
                                    st.session_state.docs_for_analysis.append(doc)
                                
                                st.session_state.azure_documents = documents
                                st.success(f"✅ {len(documents)} documents extraits")
                            else:
                                st.warning("Aucun document trouvé")
                    else:
                        st.error("Sélectionnez un dossier")
            else:
                st.error("Aucun container Azure trouvé")
        
        with col2_blob:
            st.subheader("📄 Documents extraits")
            
            if st.session_state.get('azure_documents'):
                documents = st.session_state.azure_documents
                
                # Statistiques
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Documents", len(documents))
                
                with col_stat2:
                    total_size = sum(doc.metadata.get('size', 0) for doc in documents)
                    st.metric("Taille totale", f"{total_size/1024/1024:.1f} Mo")
                
                with col_stat3:
                    folders = set(doc.folder_path for doc in documents)
                    st.metric("Dossiers", len(folders))
                
                # Options d'action
                st.divider()
                
                action = st.radio(
                    "Action sur les documents",
                    ["📋 Afficher", "🤖 Analyser avec IA", "📎 Verser aux débats"]
                )
                
                if action == "📋 Afficher":
                    # Liste des documents
                    for doc in documents[:10]:  # Limiter l'affichage
                        with st.expander(f"📄 {doc.title}"):
                            st.write(f"**Chemin :** {doc.metadata.get('blob_path', '')}")
                            st.write(f"**Taille :** {doc.metadata.get('size', 0)/1024:.1f} Ko")
                            st.write("**Extrait :**")
                            st.text(doc.content[:500] + "...")
                
                elif action == "🤖 Analyser avec IA":
                    # Analyse groupée avec IA
                    st.write("**Analyse par IA**")
                    
                    # Contexte des documents
                    doc_context = f"J'ai {len(documents)} documents du dossier Azure '{st.session_state.azure_current_path}'"
                    doc_list = "\n".join([f"- {doc.title}" for doc in documents[:10]])
                    if len(documents) > 10:
                        doc_list += f"\n... et {len(documents)-10} autres documents"
                    
                    st.info(doc_context)
                    st.caption("Documents :")
                    st.text(doc_list)
                    
                    # Question pour l'IA
                    question = st.text_area(
                        "Question pour l'IA sur ces documents",
                        placeholder="Ex: Quelle est la stratégie de défense principale qui ressort de ces documents ?",
                        height=100
                    )
                    
                    if st.button("🤖 Analyser", type="primary"):
                        if question and gestionnaire.llm_manager:
                            # Construire le contexte complet
                            full_context = f"{doc_context}\n\nContenu des documents principaux :\n"
                            
                            # Ajouter le contenu des documents (limité)
                            for i, doc in enumerate(documents[:5]):  # Max 5 documents
                                full_context += f"\n--- Document {i+1}: {doc.title} ---\n"
                                full_context += doc.content[:2000] + "...\n"
                            
                            full_prompt = f"Contexte : {full_context}\n\nQuestion : {question}"
                            
                            with st.spinner("Analyse en cours..."):
                                # Utiliser le premier LLM disponible
                                available_llms = list(gestionnaire.llm_manager.clients.keys())
                                if available_llms:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    
                                    result = loop.run_until_complete(
                                        gestionnaire.llm_manager.query_single_llm(
                                            available_llms[0],
                                            full_prompt,
                                            "Tu es un avocat expert analysant des documents juridiques."
                                        )
                                    )
                                    
                                    if result['success']:
                                        st.success("✅ Analyse terminée")
                                        st.markdown("**Réponse de l'IA :**")
                                        st.markdown(result['response'])
                                        
                                        # Option de sauvegarder
                                        if st.button("📎 Verser cette analyse aux débats"):
                                            num = gestionnaire.gestionnaire_pieces.verser_piece(
                                                titre=f"Analyse IA - Dossier Azure {st.session_state.azure_current_path}",
                                                contenu=result['response'],
                                                type_piece='rapport',
                                                dossier_id=st.session_state.dossier_actif
                                            )
                                            st.success(f"✅ Pièce n°{num}")
                                    else:
                                        st.error(f"Erreur : {result.get('error')}")
                        else:
                            st.error("Entrez une question et vérifiez la configuration des LLMs")
                
                elif action == "📎 Verser aux débats":
                    # Verser tous les documents
                    if st.button("📎 Verser tous les documents", type="primary"):
                        versed_count = 0
                        
                        with st.spinner("Versement en cours..."):
                            for doc in documents:
                                num = gestionnaire.gestionnaire_pieces.verser_piece(
                                    titre=doc.title,
                                    contenu=doc.content,
                                    type_piece='document',
                                    dossier_id=st.session_state.dossier_actif,
                                    metadata={
                                        'source': 'azure_blob',
                                        'container': doc.metadata.get('container'),
                                        'path': doc.metadata.get('blob_path')
                                    }
                                )
                                versed_count += 1
                        
                        st.success(f"✅ {versed_count} documents versés aux débats")
                
                # Export des documents
                st.divider()
                
                if st.button("💾 Exporter en ZIP"):
                    import zipfile
                    import io
                    
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for doc in documents:
                            # Créer l'arborescence dans le ZIP
                            file_path = doc.metadata.get('blob_path', doc.title)
                            zip_file.writestr(file_path, doc.content)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        "💾 Télécharger ZIP",
                        zip_buffer.getvalue(),
                        f"azure_documents_{datetime.now().strftime(AppConfig.EXPORT_FORMAT)}.zip",
                        "application/zip"
                    )
            else:
                st.info("Sélectionnez un dossier Azure pour extraire les documents")
                
                # Guide d'utilisation
                with st.expander("📖 Guide d'utilisation"):
                    st.markdown("""
                    ### Comment utiliser Azure Blob Storage
                    
                    1. **Configuration** : Ajoutez votre chaîne de connexion Azure dans le fichier `.env` :
                       ```
                       AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
                       ```
                    
                    2. **Navigation** : 
                       - Sélectionnez un container
                       - Cliquez sur les dossiers pour naviguer
                       - Utilisez "Dossier parent" pour remonter
                    
                    3. **Extraction** :
                       - Sélectionnez un dossier
                       - Choisissez d'inclure ou non les sous-dossiers
                       - Cliquez sur "Extraire les documents"
                    
                    4. **Analyse IA** :
                       - Les documents extraits peuvent être analysés par l'IA
                       - Posez des questions sur l'ensemble des documents
                       - L'IA synthétisera les informations pertinentes
                    
                    5. **Formats supportés** :
                       - `.txt` : Texte brut
                       - `.docx` / `.doc` : Documents Word
                       - `.pdf` : Documents PDF (nécessite PyPDF2)
                       - `.rtf` : Rich Text Format
                    """)

# ================== TAB 7: CONFIGURATION ==================

with tabs[6]:
    st.header("⚙️ Configuration")
    
    st.subheader("🎨 En-tête personnalisé")
    
    with st.form("config_letterhead"):
        nom = st.text_input("Nom du cabinet")
        adresse = st.text_area("Adresse", height=100)
        telephone = st.text_input("Téléphone")
        email = st.text_input("Email")
        barreau = st.text_input("Barreau")
        
        if st.form_submit_button("💾 Sauvegarder"):
            st.session_state.letterhead = {
                'nom': nom,
                'adresse': adresse,
                'telephone': telephone,
                'email': email,
                'barreau': barreau
            }
            exporter.letterhead = st.session_state.letterhead
            st.success("✅ Configuration sauvegardée")

# ================== SIDEBAR ==================

with st.sidebar:
    st.markdown("## 💼 Assistant Pénal des Affaires")
    st.caption("Version complète avec Multi-LLM v3.0")
    
    st.divider()
    
    # Dossier actif
    if st.session_state.dossier_actif:
        dossier = st.session_state.dossiers.get(st.session_state.dossier_actif)
        if dossier:
            st.success(f"📂 {dossier.numero_parquet}")
            st.caption(f"{dossier.client_nom}")
            
            if dossier.client_type == "PM":
                st.caption(f"{dossier.client_info.get('forme_juridique', 'PM')}")
            
            # Métriques
            if dossier.montant_prejudice:
                st.metric("Enjeux", f"{dossier.montant_prejudice:,.0f}€")
            
            # Prescription
            prescription = dossier.calculer_prescription()
            if not prescription['prescrit']:
                st.metric("Prescription", f"{prescription['jours_restants']}j")
            
            # Victimes
            if dossier.victimes:
                st.metric("Victimes", len(dossier.victimes))
    else:
        st.info("Aucun dossier sélectionné")
    
    st.divider()
    
    # Actions rapides
    st.subheader("⚡ Actions rapides")
    
    if st.button("📋 Bordereau", use_container_width=True):
        if gestionnaire.gestionnaire_pieces.pieces:
            st.text_area(
                "Bordereau",
                gestionnaire.gestionnaire_pieces.generer_bordereau()[:200] + "...",
                height=150
            )
    
    if st.button("🔍 Recherche ABS", use_container_width=True):
        st.session_state.search_query = "abus biens sociaux élément intentionnel"
    
    if st.button("📄 Modèle CJIP", use_container_width=True):
        st.session_state.document_content = gestionnaire.assistant_redaction.templates['memoire_cjip']['contenu']
    
    if st.button("🤖 Test Multi-LLM", use_container_width=True):
        st.session_state.selected_tab = 2  # Tab IA
    
    if doc_manager.azure_blob_manager.blob_service_client:
        if st.button("☁️ Azure Blob", use_container_width=True):
            st.session_state.selected_tab = 5  # Tab Azure
    
    # Footer
    st.divider()
    st.caption("💼 Assistant Pénal Affaires v3.0")
    st.caption("✨ Multi-LLM & Multi-Victimes")
    st.caption("☁️ Azure Blob Storage")
    st.caption(f"© {datetime.now().year}")

# ================== MAIN ==================

if __name__ == "__main__":
    logger.info("Application Assistant Pénal des Affaires démarrée")
