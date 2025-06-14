"""Application IA Juridique - Droit Pénal des Affaires - Version complète avec Multi-LLM"""

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
import importlib
import sys
import traceback

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

# ========== IMPORT DU MANAGER MULTI-LLM ==========
try:
    from multi_llm_manager import MultiLLMManager
    MULTI_LLM_AVAILABLE = True
    logger.info("✅ Manager Multi-LLM importé avec succès")
except ImportError as e:
    MULTI_LLM_AVAILABLE = False
    logger.error(f"❌ Impossible d'importer le manager Multi-LLM : {e}")

# ========== IMPORT DES MODULES EXISTANTS ==========
def get_modules_status():
    """Retourne le statut de tous les modules"""
    modules_to_import = [
        'search_module',
        'compare_documents',
        'timeline_juridique',
        'extract_information',
        'strategy_juridique',
        'plaidoirie',
        'preparation_client',
        'negotiation',
        'report_generation',
        'courrier_juridique',
        'conclusions',
        'jurisprudence',
        'calcul_prejudice',
        'procedure_verification',
        'contradiction_analysis',
        'risk_assessment',
        'evidence_chain',
        'witness_preparation'
    ]
    
    status = {
        'total_modules': len(modules_to_import),
        'loaded': [],
        'failed': {},
        'loaded_count': 0,
        'failed_count': 0
    }
    
    # Tenter d'importer chaque module
    for module_name in modules_to_import:
        try:
            # Essayer d'importer depuis le dossier modules
            module = importlib.import_module(f'modules.{module_name}')
            status['loaded'].append(module_name)
            status['loaded_count'] += 1
            logger.info(f"✅ Module {module_name} chargé")
        except ImportError as e:
            status['failed'][module_name] = f"Module non trouvé : {str(e)}"
            status['failed_count'] += 1
            logger.warning(f"⚠️ Module {module_name} non trouvé")
        except Exception as e:
            status['failed'][module_name] = f"Erreur : {str(e)}"
            status['failed_count'] += 1
            logger.error(f"❌ Erreur lors du chargement de {module_name}: {e}")
    
    return status

# ========== GESTIONNAIRE DE MODULES AMÉLIORÉ ==========
class ModuleManager:
    """Gestionnaire de modules avec support complet"""
    
    def __init__(self):
        self.modules_path = Path(__file__).parent / "modules"
        self.loaded_modules = {}
        self.module_configs = self._get_module_configs()
        self.modules_status = get_modules_status()
    
    def _get_module_configs(self) -> Dict:
        """Configuration complète de tous les modules pour droit pénal des affaires"""
        return {
            # Modules d'analyse
            "search_module": {
                "name": "🔍 Recherche & Analyse",
                "desc": "Recherche IA multi-documents dans les dossiers pénaux",
                "category": "analyse",
                "active": True
            },
            "compare_documents": {
                "name": "📊 Comparaison documents",
                "desc": "Analyse comparative pour détecter les contradictions",
                "category": "analyse",
                "active": True
            },
            "timeline_juridique": {
                "name": "📅 Timeline juridique",
                "desc": "Chronologie des infractions et procédures",
                "category": "analyse",
                "active": True
            },
            "extract_information": {
                "name": "📑 Extraction d'informations",
                "desc": "Extraction des éléments constitutifs des infractions",
                "category": "analyse",
                "active": True
            },
            "contradiction_analysis": {
                "name": "⚡ Analyse contradictions",
                "desc": "Détection automatique des incohérences",
                "category": "analyse",
                "active": True
            },
            
            # Modules de stratégie pénale
            "strategy_juridique": {
                "name": "⚖️ Stratégie de défense",
                "desc": "Élaboration de la stratégie en droit pénal des affaires",
                "category": "strategie",
                "active": True
            },
            "plaidoirie": {
                "name": "🎯 Plaidoirie pénale",
                "desc": "Préparation des plaidoiries devant le tribunal correctionnel",
                "category": "strategie",
                "active": True
            },
            "preparation_client": {
                "name": "👤 Préparation interrogatoire",
                "desc": "Préparer le client aux interrogatoires et audiences",
                "category": "strategie",
                "active": True
            },
            "negotiation": {
                "name": "🤝 CRPC & Transaction",
                "desc": "Négociation CRPC et transactions pénales",
                "category": "strategie",
                "active": True
            },
            "risk_assessment": {
                "name": "⚠️ Évaluation des risques",
                "desc": "Analyse des risques pénaux et quantum des peines",
                "category": "strategie",
                "active": True
            },
            
            # Modules de génération
            "report_generation": {
                "name": "📄 Rapports d'analyse",
                "desc": "Génération de rapports sur les infractions économiques",
                "category": "generation",
                "active": True
            },
            "courrier_juridique": {
                "name": "✉️ Courriers pénaux",
                "desc": "Courriers au procureur, juge d'instruction",
                "category": "generation",
                "active": True
            },
            "conclusions": {
                "name": "📝 Conclusions pénales",
                "desc": "Rédaction de conclusions en défense",
                "category": "generation",
                "active": True
            },
            
            # Modules d'expertise pénale
            "jurisprudence": {
                "name": "⚖️ Jurisprudence pénale",
                "desc": "Recherche jurisprudence Cass. Crim. et CJUE",
                "category": "expertise",
                "active": True
            },
            "calcul_prejudice": {
                "name": "💰 Préjudice & Amendes",
                "desc": "Calcul du préjudice et quantum des amendes",
                "category": "expertise",
                "active": True
            },
            "procedure_verification": {
                "name": "📋 Nullités procédure",
                "desc": "Vérification des nullités de procédure pénale",
                "category": "expertise",
                "active": True
            },
            "evidence_chain": {
                "name": "🔗 Chaîne de preuves",
                "desc": "Analyse de la recevabilité des preuves",
                "category": "expertise",
                "active": True
            },
            "witness_preparation": {
                "name": "👥 Préparation témoins",
                "desc": "Préparation des témoins de la défense",
                "category": "expertise",
                "active": True
            }
        }
    
    def load_module(self, module_id: str):
        """Charge un module avec gestion d'erreur complète"""
        if module_id in self.loaded_modules:
            return self.loaded_modules[module_id]
        
        try:
            # Import depuis modules.nom_module
            module_path = f"modules.{module_id}"
            module = importlib.import_module(module_path)
            self.loaded_modules[module_id] = module
            logger.info(f"✅ Module {module_id} chargé avec succès")
            return module
        except ImportError as e:
            logger.warning(f"⚠️ Module {module_id} non trouvé : {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur chargement {module_id} : {e}")
            return None
    
    def run_module(self, module_id: str):
        """Exécute un module avec fallback"""
        module = self.load_module(module_id)
        
        if module and hasattr(module, 'run'):
            try:
                module.run()
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du module : {e}")
                self._show_default_module_interface(module_id)
        else:
            self._show_default_module_interface(module_id)
    
    def _show_default_module_interface(self, module_id: str):
        """Interface par défaut avec fonctionnalités spécifiques au droit pénal des affaires"""
        config = self.module_configs.get(module_id, {})
        st.title(f"{config.get('name', module_id)}")
        st.info(f"🚧 Module en cours de configuration\n\n{config.get('desc', '')}")
        
        # Interfaces spécifiques selon le module
        if module_id == "plaidoirie":
            self._show_plaidoirie_penale_interface()
        elif module_id == "preparation_client":
            self._show_preparation_interrogatoire_interface()
        elif module_id == "jurisprudence":
            self._show_jurisprudence_penale_interface()
        elif module_id == "negotiation":
            self._show_crpc_interface()
        elif module_id == "risk_assessment":
            self._show_risk_assessment_interface()
        else:
            st.warning("Module en développement - Fonctionnalité bientôt disponible")
    
    def _show_plaidoirie_penale_interface(self):
        """Interface pour la plaidoirie pénale"""
        tabs = st.tabs(["📝 Infractions", "🎯 Arguments", "🗣️ Simulation", "📊 Quantum"])
        
        with tabs[0]:
            st.markdown("### Analyse des infractions reprochées")
            infractions = st.multiselect(
                "Infractions",
                ["Abus de biens sociaux", "Escroquerie", "Abus de confiance", 
                 "Faux et usage de faux", "Blanchiment", "Corruption", 
                 "Prise illégale d'intérêts", "Favoritisme", "Recel"]
            )
            
        with tabs[1]:
            st.markdown("### Arguments de défense")
            defenses = st.multiselect(
                "Moyens de défense",
                ["Absence d'élément intentionnel", "Prescription", "Nullité procédure",
                 "Irrecevabilité des preuves", "Bonne foi", "Autorisation des organes sociaux"]
            )
            
        with tabs[2]:
            st.markdown("### Simulation d'audience correctionnelle")
            st.info("Préparez-vous aux questions du président et du ministère public")
            
        with tabs[3]:
            st.markdown("### Évaluation du quantum de peine")
            st.slider("Risque emprisonnement (mois)", 0, 60, 12)
            st.slider("Risque amende (k€)", 0, 1000, 100)
    
    def _show_preparation_interrogatoire_interface(self):
        """Interface pour la préparation aux interrogatoires"""
        st.markdown("### Préparation aux interrogatoires et auditions")
        
        type_procedure = st.selectbox(
            "Type de procédure",
            ["Garde à vue", "Audition libre", "Interrogatoire première comparution",
             "Interrogatoire juge d'instruction", "Audience correctionnelle"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Exercice du droit au silence")
            st.checkbox("Demande de confrontation")
        with col2:
            st.checkbox("Communication du dossier")
            st.checkbox("Présence de l'avocat")
    
    def _show_jurisprudence_penale_interface(self):
        """Interface pour la recherche de jurisprudence pénale"""
        st.markdown("### Recherche jurisprudence pénale des affaires")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            juridiction = st.selectbox(
                "Juridiction",
                ["Cass. Crim.", "Cour d'appel", "CJUE", "CEDH", "Cons. Const."]
            )
        with col2:
            infraction = st.selectbox(
                "Infraction",
                ["Toutes", "ABS", "Escroquerie", "Corruption", "Blanchiment", "Favoritisme"]
            )
        with col3:
            st.date_input("Depuis", value=datetime(2020, 1, 1))
    
    def _show_crpc_interface(self):
        """Interface pour la négociation CRPC"""
        st.markdown("### Négociation CRPC - Comparution sur Reconnaissance Préalable de Culpabilité")
        
        col1, col2 = st.columns(2)
        with col1:
            peine_proposee = st.selectbox(
                "Peine proposée",
                ["Amende", "Emprisonnement avec sursis", "TIG", "Jours-amende"]
            )
        with col2:
            quantum = st.number_input("Quantum", min_value=0)
        
        st.text_area("Points de négociation", placeholder="Éléments à négocier avec le parquet...")
    
    def _show_risk_assessment_interface(self):
        """Interface pour l'évaluation des risques pénaux"""
        st.markdown("### Évaluation des risques pénaux")
        
        # Facteurs aggravants/atténuants
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Facteurs aggravants")
            st.checkbox("Réitération/Récidive")
            st.checkbox("Préjudice important")
            st.checkbox("Abus de position")
            st.checkbox("Organisation/Bande organisée")
        
        with col2:
            st.markdown("#### Facteurs atténuants")
            st.checkbox("Primo-délinquant")
            st.checkbox("Collaboration avec la justice")
            st.checkbox("Réparation du préjudice")
            st.checkbox("Circonstances particulières")

# Instance globale
module_manager = ModuleManager()

# ========== CSS PROFESSIONNEL DROIT PÉNAL ==========
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
        --danger-red: #e53e3e;
        --text-primary: #2d3748;
        --text-secondary: #718096;
        --border-color: #cbd5e0;
        --bg-light: #f7fafc;
        --hover-blue: #2b6cb0;
    }
    
    /* Typography - police réduite */
    * { font-size: 0.875rem; }
    h1 { font-size: 1.5rem !important; color: var(--primary-blue); }
    h2 { font-size: 1.25rem !important; color: var(--primary-blue); }
    h3 { font-size: 1.1rem !important; color: var(--secondary-blue); }
    h4 { font-size: 1rem !important; color: var(--secondary-blue); }
    
    /* Barre de recherche centrale 4 lignes */
    .main-search-container {
        background: linear-gradient(135deg, #f0f7ff 0%, #e6f2ff 100%);
        border: 2px solid var(--accent-blue);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-search-container:hover {
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
    }
    
    .main-search-container textarea {
        font-size: 1rem !important;
        line-height: 1.6 !important;
        min-height: 120px !important;
    }
    
    /* Module cards */
    .module-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
        height: 100%;
    }
    
    .module-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .module-card.error {
        border-left: 4px solid var(--danger-red);
    }
    
    .module-card.success {
        border-left: 4px solid var(--success-green);
    }
    
    /* Diagnostic cards */
    .diagnostic-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .diagnostic-card.success {
        border-left: 4px solid var(--success-green);
    }
    
    .diagnostic-card.error {
        border-left: 4px solid var(--danger-red);
    }
    
    /* Stats */
    .stat-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-blue);
    }
    
    /* Document cards avec détection @ */
    .search-container.client-active textarea {
        border-color: var(--accent-blue);
        background: var(--light-blue);
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.3);
    }
    
    /* Azure status */
    .azure-status {
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .azure-connected { 
        border-left-color: var(--success-green);
        background: #e6fffa;
    }
    
    .azure-error {
        border-left-color: var(--danger-red);
        background: #fff5f5;
    }
</style>
""", unsafe_allow_html=True)

# ========== GESTIONNAIRES AZURE (conservés de l'original) ==========
class AzureBlobManager:
    """Gestionnaire Azure Blob Storage avec cache et gestion versions"""
    def __init__(self):
        self.connected = False
        self.error = None
        self.client = None
        self._containers_cache = []
        self._blobs_cache = {}
        self._documents_count = 0
        
        try:
            conn_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if conn_string:
                from azure.storage.blob import BlobServiceClient
                self.client = BlobServiceClient.from_connection_string(conn_string)
                try:
                    container_iter = self.client.list_containers()
                    try:
                        next(container_iter)
                        self.connected = True
                        self._load_containers_cache()
                        self._count_all_documents()
                        logger.info("✅ Azure Blob connecté")
                    except StopIteration:
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
    
    def _count_all_documents(self):
        """Compte le nombre total de documents"""
        if self.connected:
            try:
                total = 0
                for container in self._containers_cache:
                    try:
                        container_client = self.client.get_container_client(container)
                        blobs = list(container_client.list_blobs())
                        total += len(blobs)
                    except:
                        pass
                self._documents_count = total
            except:
                self._documents_count = 0
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques des documents"""
        stats = {
            'total_documents': self._documents_count,
            'containers': len(self._containers_cache),
            'documents_by_type': {
                'juridique': 156,
                'expertises': 89,
                'procedures': 234,
                'correspondances': 412,
                'factures': 98
            }
        }
        return stats
    
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
    
    def search_containers_by_infraction(self, infraction: str) -> List[str]:
        """Recherche les conteneurs mentionnant une infraction"""
        matching_containers = []
        infraction_lower = infraction.lower()
        
        # Mots-clés par type d'infraction
        infraction_keywords = {
            'abs': ['abus', 'biens', 'sociaux', 'abs'],
            'escroquerie': ['escroquerie', 'tromperie', 'manoeuvre'],
            'blanchiment': ['blanchiment', 'dissimulation', 'capitaux'],
            'corruption': ['corruption', 'trafic', 'influence'],
            'faux': ['faux', 'usage', 'falsification'],
            'favoritisme': ['favoritisme', 'marché', 'public']
        }
        
        # Recherche élargie
        keywords = infraction_keywords.get(infraction_lower, [infraction_lower])
        
        for container in self._containers_cache:
            container_lower = container.lower()
            if any(keyword in container_lower for keyword in keywords):
                matching_containers.append(container)
        
        return matching_containers
    
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
            
            if not show_all_versions:
                word_docs = {}
                other_docs = []
                
                for blob in all_blobs:
                    if blob['name'].endswith(('.docx', '.doc')):
                        base_name = re.sub(r'[-_]\d{8}[-_]\d{6}', '', blob['name'])
                        base_name = re.sub(r'[-_]v\d+', '', base_name)
                        base_name = re.sub(r'[-_](final|draft|version\d+)', '', base_name, re.I)
                        
                        if base_name not in word_docs:
                            word_docs[base_name] = []
                        word_docs[base_name].append(blob)
                    else:
                        other_docs.append(blob)
                
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
    
    def analyze_query_intent(self, query: str) -> Dict:
        """Analyse l'intention pour le droit pénal des affaires"""
        query_lower = query.lower()
        
        # Détection de module explicite
        for module_id, config in module_manager.module_configs.items():
            if module_id in query_lower or any(word in query_lower for word in config['name'].lower().split()):
                return {'module': module_id, 'query': query}
        
        # Détection par mots-clés juridiques
        if any(word in query_lower for word in ['contradiction', 'incohérence', 'divergence']):
            return {'module': 'contradiction_analysis', 'query': query}
        elif any(word in query_lower for word in ['plaidoirie', 'plaider', 'audience']):
            return {'module': 'plaidoirie', 'query': query}
        elif any(word in query_lower for word in ['crpc', 'transaction', 'négocier']):
            return {'module': 'negotiation', 'query': query}
        elif any(word in query_lower for word in ['risque', 'peine', 'quantum']):
            return {'module': 'risk_assessment', 'query': query}
        elif any(word in query_lower for word in ['nullité', 'procédure', 'vice']):
            return {'module': 'procedure_verification', 'query': query}
        
        return {'module': 'search_module', 'query': query}
    
    def generate_prompts(self, documents: List[Dict], context: str = "") -> List[str]:
        """Génère des prompts pour le droit pénal des affaires"""
        if not self.connected:
            return self._generate_default_prompts_penal(documents)
        
        try:
            status_placeholder = st.empty()
            status_placeholder.info("🤖 Génération des suggestions par IA...")
            
            docs_summary = "\n".join([f"- {d.get('name', 'Document')}" for d in documents[:10]])
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en droit pénal des affaires. Générez 5 questions pertinentes pour analyser un dossier pénal économique."},
                    {"role": "user", "content": f"Documents:\n{docs_summary}\n\nContexte: dossier pénal des affaires"}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            status_placeholder.empty()
            
            prompts = response.choices[0].message.content.split('\n')
            return [p.strip() for p in prompts if p.strip()][:5]
        except:
            try:
                status_placeholder.empty()
            except:
                pass
            return self._generate_default_prompts_penal(documents)
    
    def _generate_default_prompts_penal(self, documents: List[Dict]) -> List[str]:
        """Prompts par défaut pour le droit pénal des affaires"""
        return [
            "Analyser les éléments constitutifs des infractions",
            "Identifier les nullités de procédure exploitables",
            "Évaluer le quantum de peine encouru",
            "Rechercher les contradictions dans les PV",
            "Proposer une stratégie de défense",
            "Vérifier la prescription des faits",
            "Analyser la recevabilité des preuves",
            "Préparer les arguments pour la plaidoirie"
        ]
    
    def categorize_document(self, filename: str, content_preview: str = "") -> str:
        """Catégorise un document juridique pénal"""
        if not self.connected:
            return self._categorize_by_rules(filename)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Catégorisez ce document pénal. Répondez uniquement par: pv, expertise, requisitoire, ordonnance, jugement, appel, constitution, plainte, ou autre."},
                    {"role": "user", "content": f"Nom: {filename}\nAperçu: {content_preview[:100]}"}
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            category = response.choices[0].message.content.strip().lower()
            valid_categories = ['pv', 'expertise', 'requisitoire', 'ordonnance', 'jugement', 'appel', 'constitution', 'plainte', 'autre']
            
            return category if category in valid_categories else 'autre'
        except:
            return self._categorize_by_rules(filename)
    
    def _categorize_by_rules(self, filename: str) -> str:
        """Catégorisation par règles pour documents pénaux"""
        filename_lower = filename.lower()
        
        if any(term in filename_lower for term in ['pv', 'proces-verbal', 'audition', 'garde-vue']):
            return 'pv'
        elif any(term in filename_lower for term in ['expertise', 'expert', 'rapport']):
            return 'expertise'
        elif any(term in filename_lower for term in ['requisitoire', 'ministere-public', 'parquet']):
            return 'requisitoire'
        elif any(term in filename_lower for term in ['ordonnance', 'juge-instruction', 'instruction']):
            return 'ordonnance'
        elif any(term in filename_lower for term in ['jugement', 'arret', 'decision']):
            return 'jugement'
        elif any(term in filename_lower for term in ['appel', 'pourvoi', 'cassation']):
            return 'appel'
        elif any(term in filename_lower for term in ['constitution', 'partie-civile']):
            return 'constitution'
        elif any(term in filename_lower for term in ['plainte', 'denonciation']):
            return 'plainte'
        else:
            return 'autre'

# ========== TYPES DE DOCUMENTS PÉNAUX ==========
DOCUMENT_TYPES = {
    'pv': {'name': 'Procès-verbaux', 'icon': '📝', 'color': '#2c5282'},
    'expertise': {'name': 'Expertises', 'icon': '🔬', 'color': '#2d3748'},
    'requisitoire': {'name': 'Réquisitoires', 'icon': '⚖️', 'color': '#e53e3e'},
    'ordonnance': {'name': 'Ordonnances', 'icon': '🔨', 'color': '#38a169'},
    'jugement': {'name': 'Jugements', 'icon': '⚖️', 'color': '#805ad5'},
    'appel': {'name': 'Appels', 'icon': '📤', 'color': '#d69e2e'},
    'constitution': {'name': 'Constitutions PC', 'icon': '👥', 'color': '#3182ce'},
    'plainte': {'name': 'Plaintes', 'icon': '📨', 'color': '#e53e3e'},
    'autre': {'name': 'Autres', 'icon': '📁', 'color': '#718096'}
}

# ========== JAVASCRIPT POUR RECHERCHE ==========
SEARCH_JAVASCRIPT = """
<script>
(function() {
    function setupEnhancedSearch() {
        const searchInterval = setInterval(() => {
            const textarea = document.querySelector('textarea[aria-label="Zone de recherche principale"]');
            if (!textarea) return;
            
            clearInterval(searchInterval);
            
            // Détection du @ et mise en évidence
            textarea.addEventListener('input', function(e) {
                const value = e.target.value;
                
                if (value.startsWith('@')) {
                    textarea.style.borderColor = '#4299e1';
                    textarea.style.borderWidth = '3px';
                    textarea.style.backgroundColor = '#e6f2ff';
                    textarea.style.boxShadow = '0 0 0 3px rgba(66, 153, 225, 0.3)';
                } else {
                    textarea.style.borderColor = '';
                    textarea.style.borderWidth = '';
                    textarea.style.backgroundColor = '';
                    textarea.style.boxShadow = '';
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
        'selected_folders': [],  # Ajout pour la sélection de dossiers
        'show_all_versions': False,
        'show_documents': False,
        'document_type_filter': 'tous',
        'azure_blob_manager': None,
        'azure_search_manager': None,
        'azure_openai_manager': None,
        'multi_llm_manager': None,
        'clients_cache': {},
        'prompts_cache': [],
        'folder_aliases': {},
        'search_mode': 'multi_ia',
        'target_module': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialisation des services une seule fois
    if not st.session_state.initialized:
        init_container = st.container()
        
        with init_container:
            st.markdown("### 🚀 Initialisation de l'application - Droit Pénal des Affaires")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Étape 1 : Azure Blob Storage
            status_text.text("💾 Connexion à Azure Blob Storage...")
            progress_bar.progress(0.2)
            st.session_state.azure_blob_manager = AzureBlobManager()
            time.sleep(0.3)
            
            # Étape 2 : Azure Search
            status_text.text("🔍 Configuration d'Azure Search...")
            progress_bar.progress(0.4)
            st.session_state.azure_search_manager = AzureSearchManager()
            time.sleep(0.3)
            
            # Étape 3 : Azure OpenAI
            status_text.text("🤖 Initialisation d'Azure OpenAI...")
            progress_bar.progress(0.6)
            st.session_state.azure_openai_manager = AzureOpenAIManager()
            time.sleep(0.3)
            
            # Étape 4 : Multi-LLM Manager
            status_text.text("🎭 Configuration du Manager Multi-LLM...")
            progress_bar.progress(0.8)
            if MULTI_LLM_AVAILABLE:
                try:
                    st.session_state.multi_llm_manager = MultiLLMManager()
                    logger.info("✅ Manager Multi-LLM initialisé")
                except Exception as e:
                    logger.error(f"❌ Erreur initialisation Multi-LLM : {e}")
                    st.session_state.multi_llm_manager = None
            time.sleep(0.3)
            
            # Étape 5 : Finalisation
            status_text.text("✅ Finalisation...")
            progress_bar.progress(1.0)
            st.session_state.folder_aliases = {}
            st.session_state.initialized = True
            time.sleep(0.2)
        
        init_container.empty()

# ========== FONCTIONS UTILITAIRES ==========
def generate_folder_alias(folder_name: str) -> str:
    """Génère un alias court pour un dossier"""
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', folder_name.lower())
    
    if len(clean_name) <= 3:
        return clean_name
    elif len(clean_name) <= 6:
        return clean_name[:3]
    else:
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
            
            used_aliases = set()
            for container in containers:
                base_alias = generate_folder_alias(container)
                alias = base_alias
                counter = 1
                
                while alias in used_aliases:
                    alias = f"{base_alias}{counter}"
                    counter += 1
                
                used_aliases.add(alias)
                st.session_state.folder_aliases[alias] = container
    
    return st.session_state.folder_aliases

def extract_client_and_query(query: str) -> Tuple[Optional[str], str, Optional[str]]:
    """Extrait le client/infraction/fichier et la requête depuis la recherche"""
    if query.startswith('@'):
        # Recherche de fichier spécifique
        if '.' in query.split(',')[0]:  # Probablement un fichier
            match = re.match(r'@([^\s,]+)\s*,?\s*(.*)', query)
            if match:
                filename = match.group(1)
                rest = match.group(2)
                
                # Rechercher le fichier dans tous les conteneurs
                if st.session_state.azure_blob_manager:
                    containers = st.session_state.azure_blob_manager.list_containers()
                    for container in containers:
                        blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(container, True)
                        for blob in blobs:
                            if filename.lower() in blob['name'].lower():
                                # Fichier trouvé
                                st.session_state.selected_documents = [blob['name']]
                                return container, rest, 'file'
                
                return filename, rest, 'file_not_found'
        
        # Recherche de dossier ou infraction
        match = re.match(r'@(\w+)\s*,?\s*(.*)', query)
        if match:
            identifier = match.group(1).lower()
            rest = match.group(2)
            
            # Chercher dans les alias de dossiers
            aliases = get_folder_aliases()
            if identifier in aliases:
                return aliases[identifier], rest, 'folder'
            
            # Chercher correspondance partielle dans les alias
            for a, folder in aliases.items():
                if a.startswith(identifier) or identifier in a:
                    return folder, rest, 'folder'
            
            # Si pas trouvé dans les alias, chercher dans les noms réels
            if st.session_state.azure_blob_manager:
                containers = st.session_state.azure_blob_manager.list_containers()
                for container in containers:
                    if container.lower().startswith(identifier) or identifier in container.lower():
                        return container, rest, 'folder'
            
            # Sinon, considérer comme une infraction
            return identifier, rest, 'infraction'
    
    return None, query, None

# ========== COMPOSANTS UI ==========
def show_modules_diagnostic():
    """Affiche le diagnostic détaillé des modules"""
    st.markdown("### 📊 Diagnostic des Modules")
    
    status = module_manager.modules_status
    
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
                config = module_manager.module_configs.get(module, {})
                st.success(f"• **{module}** - {config.get('name', 'Sans nom')}")
    
    if status['failed_count'] > 0:
        with st.expander(f"❌ Modules en erreur ({status['failed_count']})", expanded=True):
            for module, error in status['failed'].items():
                config = module_manager.module_configs.get(module, {})
                st.error(f"**{module}** ({config.get('name', 'Sans nom')})")
                st.caption(f"Erreur : {error}")
                
                # Suggestions de résolution
                if "No module named" in error:
                    st.info(f"💡 Créez le fichier `modules/{module}.py` avec une fonction `run()`")
                elif "has no attribute 'run'" in error:
                    st.info(f"💡 Ajoutez une fonction `run()` dans `modules/{module}.py`")

def show_main_search_bar():
    """Barre de recherche principale mise en avant - 4 lignes"""
    st.markdown('<div class="main-search-container">', unsafe_allow_html=True)
    
    # Titre et aide
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 🔍 Recherche Intelligente Multi-IA - Droit Pénal des Affaires")
    with col2:
        mode = st.radio(
            "Mode",
            ["🤖 Multi-IA", "📋 Module"],
            horizontal=True,
            key="search_mode_toggle",
            label_visibility="collapsed"
        )
        st.session_state.search_mode = "multi_ia" if "Multi-IA" in mode else "module"
    
    # Détection du contexte actuel
    query = st.session_state.get('search_query', '')
    client, clean_query, query_type = extract_client_and_query(query)
    
    # Affichage du contexte et navigation
    if client:
        if query_type == 'folder':
            # Afficher le dossier avec navigation hiérarchique
            display_folder_navigation(client, clean_query)
        elif query_type == 'file':
            # Fichier spécifique trouvé
            st.success(f"📄 **Fichier trouvé dans le dossier :** {client}")
            st.info(f"Document sélectionné : {st.session_state.selected_documents[0] if st.session_state.selected_documents else 'Aucun'}")
        elif query_type == 'file_not_found':
            st.warning(f"❌ **Fichier non trouvé :** {client}")
            st.info("Vérifiez le nom du fichier ou utilisez la recherche globale")
        else:
            # Recherche par infraction
            matching_folders = st.session_state.azure_blob_manager.search_containers_by_infraction(client)
            if matching_folders:
                st.info(f"🔍 **Infraction :** {client} - {len(matching_folders)} dossier(s) trouvé(s)")
                with st.expander("Sélectionner des dossiers", expanded=True):
                    for folder in matching_folders[:10]:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📁 {folder}")
                        with col2:
                            if st.button("Ouvrir", key=f"open_inf_{folder}"):
                                st.session_state.search_query = f"@{folder}, {clean_query}"
                                st.rerun()
                        with col3:
                            if st.checkbox("Sélectionner", key=f"sel_folder_{folder}"):
                                if 'selected_folders' not in st.session_state:
                                    st.session_state.selected_folders = []
                                if folder not in st.session_state.selected_folders:
                                    st.session_state.selected_folders.append(folder)
    
    # Zone de recherche principale - 4 lignes
    search_text = st.text_area(
        "Zone de recherche principale",
        placeholder=(
            "💡 Recherche en langage naturel ou commandes spécifiques :\n"
            "• @indice → Sélectionner un dossier pénal (ex: @mar pour Martel)\n"
            "• @infraction → Tous les dossiers avec cette infraction (ex: @abs, @escroquerie, @blanchiment)\n"
            "• @fichier.pdf → Rechercher un fichier spécifique\n"
            "• Appuyez sur Entrée pour lancer l'analyse"
        ),
        height=120,  # 4 lignes
        key="search_query",
        label_visibility="collapsed"
    )
    
    # Suggestions contextuelles
    if not query:
        st.caption("**Exemples :** @abs, analyser les éléments constitutifs | @escroquerie, stratégie de défense | nullité: vérifier la procédure")
    
    # Boutons d'action
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        if st.session_state.search_mode == "module":
            selected_module = st.selectbox(
                "Module cible",
                options=list(module_manager.module_configs.keys()),
                format_func=lambda x: module_manager.module_configs[x]['name'],
                key="target_module_select",
                label_visibility="collapsed"
            )
            st.session_state.target_module = selected_module
    
    with col2:
        if st.button(
            "🔍 Rechercher",
            use_container_width=True,
            disabled=not search_text
        ):
            if st.session_state.azure_search_manager and st.session_state.azure_search_manager.connected:
                perform_azure_search(clean_query if client else search_text)
    
    with col3:
        if st.button(
            "🤖 Analyser",
            type="primary",
            use_container_width=True,
            disabled=not search_text or (st.session_state.search_mode == "multi_ia" and not st.session_state.selected_ais)
        ):
            if st.session_state.search_mode == "multi_ia":
                if st.session_state.selected_ais:
                    process_multi_ia_analysis(search_text)
                else:
                    st.warning("Sélectionnez au moins une IA")
            else:
                process_module_query(search_text)
    
    # Prompts suggérés si contexte actif
    if client and st.session_state.azure_openai_manager and query_type == 'folder':
        show_ai_prompts(client)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ai_selector():
    """Sélecteur d'IA pour droit pénal des affaires"""
    st.markdown("### 🤖 Intelligence Artificielle - Sélection Multi-IA")
    
    # IA disponibles selon les specs
    available_ais = {
        'ChatGPT 4': {'icon': '🧠', 'desc': 'Analyse approfondie', 'speciality': 'Stratégie juridique'},
        'Claude Opus 4': {'icon': '🎭', 'desc': 'Argumentation juridique', 'speciality': 'Plaidoirie'},
        'Perplexity': {'icon': '🔮', 'desc': 'Recherche jurisprudence', 'speciality': 'Sources actualisées'},
        'Gemini': {'icon': '✨', 'desc': 'Analyse exhaustive', 'speciality': 'Synthèse complexe'},
        'Mistral': {'icon': '🌟', 'desc': 'Droit français', 'speciality': 'Code pénal'}
    }
    
    # Ajouter Azure OpenAI si disponible
    if st.session_state.azure_openai_manager and st.session_state.azure_openai_manager.connected:
        available_ais['Azure OpenAI'] = {'icon': '☁️', 'desc': 'IA Microsoft', 'speciality': 'Analyse sécurisée'}
    
    # Affichage en ligne avec spécialités
    cols = st.columns(len(available_ais))
    
    for idx, (ai_name, ai_info) in enumerate(available_ais.items()):
        with cols[idx]:
            selected = ai_name in st.session_state.selected_ais
            
            if st.checkbox(
                f"{ai_info['icon']} {ai_name}",
                key=f"ai_{ai_name}",
                value=selected,
                help=f"{ai_info['desc']} - {ai_info['speciality']}"
            ):
                if ai_name not in st.session_state.selected_ais:
                    st.session_state.selected_ais.append(ai_name)
            else:
                if ai_name in st.session_state.selected_ais:
                    st.session_state.selected_ais.remove(ai_name)
            
            st.caption(ai_info['speciality'])

def show_ai_prompts(client: str):
    """Affiche les prompts générés par l'IA pour le dossier pénal"""
    st.markdown("**💡 Suggestions d'analyse pénale :**")
    
    blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(client, False)
    
    aliases = get_folder_aliases()
    client_alias = None
    for alias, folder in aliases.items():
        if folder == client:
            client_alias = alias
            break
    
    # Générer des prompts spécifiques au pénal
    prompts = st.session_state.azure_openai_manager.generate_prompts(blobs, "dossier pénal")
    
    cols = st.columns(2)
    for idx, prompt in enumerate(prompts[:6]):
        with cols[idx % 2]:
            if st.button(
                f"→ {prompt}",
                key=f"prompt_{idx}",
                use_container_width=True
            ):
                prefix = f"@{client_alias}" if client_alias else f"@{client}"
                st.session_state.search_query = f"{prefix}, {prompt}"
                st.rerun()

def display_folder_navigation(client: str, clean_query: str):
    """Affiche la navigation hiérarchique du dossier avec sélection"""
    # En-tête du dossier principal
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.success(f"📁 **Dossier pénal actif :** {client}")
    with col2:
        if st.button("📂 Tout sélectionner", key="select_all_folder"):
            if 'selected_folders' not in st.session_state:
                st.session_state.selected_folders = []
            if client not in st.session_state.selected_folders:
                st.session_state.selected_folders.append(client)
            # Sélectionner aussi tous les documents
            blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(client, False)
            for blob in blobs:
                if blob['name'] not in st.session_state.selected_documents:
                    st.session_state.selected_documents.append(blob['name'])
    with col3:
        if st.checkbox("Sélectionner dossier", key=f"sel_main_folder_{client}"):
            if 'selected_folders' not in st.session_state:
                st.session_state.selected_folders = []
            if client not in st.session_state.selected_folders:
                st.session_state.selected_folders.append(client)
        else:
            if 'selected_folders' in st.session_state and client in st.session_state.selected_folders:
                st.session_state.selected_folders.remove(client)
    
    # Options d'affichage
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        view_mode = st.radio(
            "Affichage",
            ["📋 Liste", "🌳 Arborescence", "📊 Par type"],
            horizontal=True,
            key="view_mode"
        )
    with col2:
        st.session_state.show_all_versions = st.checkbox(
            "Toutes versions",
            key="version_toggle",
            help="Afficher toutes les versions des documents Word"
        )
    with col3:
        sort_order = st.selectbox(
            "Tri",
            ["Plus récent", "Nom", "Type", "Taille"],
            key="sort_order",
            label_visibility="collapsed"
        )
    
    # Afficher les documents selon le mode choisi
    with st.expander("📄 Contenu du dossier", expanded=True):
        if view_mode == "📋 Liste":
            display_documents_list(client, sort_order)
        elif view_mode == "🌳 Arborescence":
            display_documents_tree(client)
        else:  # Par type
            display_documents_by_type(client)
    
    # Résumé des sélections
    display_selection_summary()

def display_documents_list(client: str, sort_order: str):
    """Affiche les documents en liste avec tri"""
    with st.spinner(f"Chargement des documents..."):
        blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(
            client, 
            st.session_state.show_all_versions
        )
    
    if not blobs:
        st.warning("Aucun document trouvé dans ce dossier")
        return
    
    # Tri des documents
    if sort_order == "Plus récent":
        blobs.sort(key=lambda x: x['last_modified'], reverse=True)
    elif sort_order == "Nom":
        blobs.sort(key=lambda x: x['name'])
    elif sort_order == "Type":
        blobs.sort(key=lambda x: x['name'].split('.')[-1] if '.' in x['name'] else '')
    elif sort_order == "Taille":
        blobs.sort(key=lambda x: x['size'], reverse=True)
    
    # Grouper les versions Word
    word_versions = {}
    other_docs = []
    
    for blob in blobs:
        if blob['name'].endswith(('.docx', '.doc')):
            # Extraire le nom de base
            base_name = re.sub(r'[-_]\d{8}[-_]\d{6}', '', blob['name'])
            base_name = re.sub(r'[-_]v\d+', '', base_name)
            base_name = re.sub(r'[-_](final|draft|version\d+)', '', base_name, re.I)
            
            if base_name not in word_versions:
                word_versions[base_name] = []
            word_versions[base_name].append(blob)
        else:
            other_docs.append(blob)
    
    # Afficher les documents Word (dernière version en premier)
    for base_name, versions in word_versions.items():
        versions.sort(key=lambda x: x['last_modified'], reverse=True)
        
        if st.session_state.show_all_versions:
            # Afficher toutes les versions
            with st.expander(f"📄 {base_name} ({len(versions)} versions)", expanded=False):
                for idx, version in enumerate(versions):
                    display_document_item(version, is_latest=(idx == 0), version_info=f"v{len(versions)-idx}")
        else:
            # Afficher seulement la dernière version
            latest = versions[0]
            latest['versions_count'] = len(versions)
            display_document_item(latest, is_latest=True)
    
    # Afficher les autres documents
    for doc in other_docs:
        display_document_item(doc)

def display_document_item(doc: Dict, is_latest: bool = False, version_info: str = ""):
    """Affiche un élément document avec options de sélection"""
    # Déterminer le type de document
    doc_type = 'autre'
    if st.session_state.azure_openai_manager:
        doc_type = st.session_state.azure_openai_manager.categorize_document(doc['name'])
    
    type_info = DOCUMENT_TYPES.get(doc_type, {'name': 'Autre', 'icon': '📄', 'color': '#718096'})
    
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    
    with col1:
        # Badge de version si applicable
        version_badge = ""
        if doc.get('versions_count', 0) > 1:
            version_badge = f" 📚 {doc['versions_count']} versions"
        elif version_info:
            version_badge = f" ({version_info})"
        
        latest_badge = " 🔥 Dernière" if is_latest else ""
        
        st.markdown(f"""
        <div style="padding: 0.5rem 0;">
            <span style="background: {type_info['color']}20; color: {type_info['color']}; 
                  padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                {type_info['icon']} {type_info['name']}
            </span>
            <strong>{doc['name']}</strong>{version_badge}{latest_badge}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.caption(f"{doc['size'] // 1024} KB")
    
    with col3:
        if doc['last_modified']:
            st.caption(doc['last_modified'].strftime("%d/%m/%Y"))
    
    with col4:
        if st.checkbox("Sélectionner", key=f"sel_doc_{doc['name']}", label_visibility="collapsed"):
            if doc['name'] not in st.session_state.selected_documents:
                st.session_state.selected_documents.append(doc['name'])
        else:
            if doc['name'] in st.session_state.selected_documents:
                st.session_state.selected_documents.remove(doc['name'])

def display_documents_tree(client: str):
    """Affiche les documents en arborescence"""
    with st.spinner(f"Construction de l'arborescence..."):
        blobs = st.session_state.azure_blob_manager.list_blobs_with_versions(
            client, 
            st.session_state.show_all_versions
        )
    
    if not blobs:
        st.warning("Aucun document trouvé")
        return
    
    # Construire l'arbre
    tree = {}
    for blob in blobs:
        parts = blob['name'].split('/')
        current = tree
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # Fichier
                if 'files' not in current:
                    current['files'] = []
                current['files'].append(blob)
            else:  # Répertoire
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    # Afficher l'arbre
    display_tree_recursive(tree, client)

def display_tree_recursive(tree: Dict, path: str, level: int = 0):
    """Affiche récursivement l'arborescence"""
    indent = "　" * level * 2
    
    # Afficher les dossiers
    for folder_name, folder_content in tree.items():
        if folder_name != 'files':
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{indent}📁 **{folder_name}**")
            with col2:
                folder_path = f"{path}/{folder_name}"
                if st.checkbox("Sél.", key=f"sel_folder_{folder_path}", label_visibility="collapsed"):
                    if 'selected_folders' not in st.session_state:
                        st.session_state.selected_folders = []
                    if folder_path not in st.session_state.selected_folders:
                        st.session_state.selected_folders.append(folder_path)
            
            display_tree_recursive(folder_content, folder_path, level + 1)
    
    # Afficher les fichiers
    if 'files' in tree:
        for file_blob in tree['files']:
            col1, col2 = st.columns([4, 1])
            with col1:
                doc_type = st.session_state.azure_openai_manager.categorize_document(file_blob['name']) if st.session_state.azure_openai_manager else 'autre'
                type_info = DOCUMENT_TYPES.get(doc_type, {'icon': '📄'})
                st.markdown(f"{indent}　{type_info['icon']} {file_blob['name'].split('/')[-1]}")
            with col2:
                if st.checkbox("Sél.", key=f"sel_file_{file_blob['name']}", label_visibility="collapsed"):
                    if file_blob['name'] not in st.session_state.selected_documents:
                        st.session_state.selected_documents.append(file_blob['name'])

def display_documents_by_type(client: str):
    """Affiche les documents groupés par type"""
    # Utiliser la fonction existante mais modifiée
    display_client_documents(client)

def display_selection_summary():
    """Affiche un résumé des sélections"""
    selected_folders = st.session_state.get('selected_folders', [])
    selected_docs = st.session_state.get('selected_documents', [])
    
    if selected_folders or selected_docs:
        st.markdown("---")
        st.markdown("### 📌 Sélection actuelle")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Dossiers sélectionnés", len(selected_folders))
            if selected_folders:
                with st.expander("Voir les dossiers"):
                    for folder in selected_folders:
                        st.write(f"📁 {folder}")
        
        with col2:
            st.metric("Documents sélectionnés", len(selected_docs))
            if selected_docs and len(selected_docs) <= 10:
                with st.expander("Voir les documents"):
                    for doc in selected_docs:
                        st.write(f"📄 {doc.split('/')[-1]}")
        
        with col3:
            if st.button("❌ Effacer la sélection", use_container_width=True):
                st.session_state.selected_folders = []
                st.session_state.selected_documents = []
                st.rerun()

def perform_azure_search(query: str):
    """Effectue une recherche Azure Search dans le contexte pénal"""
    with st.spinner("Recherche dans la base documentaire pénale..."):
        results = st.session_state.azure_search_manager.search(query)
    
    if results:
        st.success(f"✅ {len(results)} résultats trouvés")
        
        for result in results[:5]:
            score_percent = min(result['score'] * 20, 100)
            score_color = '#48bb78' if score_percent > 70 else '#ed8936' if score_percent > 40 else '#e53e3e'
            
            st.markdown(f"""
            <div class="module-card" style="border-left: 4px solid {score_color};">
                <div style="display: flex; justify-content: space-between;">
                    <strong>{result['title']}</strong>
                    <span style="background: {score_color}20; color: {score_color}; padding: 0.2rem 0.5rem; 
                          border-radius: 0.25rem; font-size: 0.75rem;">
                        {score_percent:.0f}% pertinent
                    </span>
                </div>
                <p style="color: var(--text-secondary); font-size: 0.8rem; margin: 0.5rem 0;">
                    {result['content']}...
                </p>
                <p style="font-size: 0.7rem; color: var(--text-secondary);">
                    📁 Type: {DOCUMENT_TYPES.get(result.get('type', 'autre'), {'name': 'Autre'})['name']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Aucun résultat trouvé pour cette recherche")

def process_multi_ia_analysis(query: str):
    """Traite l'analyse avec plusieurs IA via le Multi-LLM Manager"""
    client, clean_query, query_type = extract_client_and_query(query)
    
    if MULTI_LLM_AVAILABLE and st.session_state.multi_llm_manager:
        # Utiliser le Multi-LLM Manager
        with st.spinner("Analyse multi-IA en cours via le Manager Multi-LLM..."):
            try:
                # Préparer le contexte pour le manager
                context = {
                    'domain': 'droit_penal_affaires',
                    'client': client,
                    'query_type': query_type,
                    'documents': st.session_state.selected_documents if st.session_state.selected_documents else []
                }
                
                # Appeler le manager pour chaque IA sélectionnée
                results = {}
                progress = st.progress(0)
                
                for idx, ai_name in enumerate(st.session_state.selected_ais):
                    progress.progress((idx + 1) / len(st.session_state.selected_ais))
                    
                    # Mapper les noms d'IA vers les identifiants du manager
                    ai_mapping = {
                        'ChatGPT 4': 'gpt4',
                        'Claude Opus 4': 'claude',
                        'Perplexity': 'perplexity',
                        'Gemini': 'gemini',
                        'Mistral': 'mistral'
                    }
                    
                    ai_id = ai_mapping.get(ai_name, ai_name.lower())
                    
                    try:
                        # Appeler le manager
                        result = st.session_state.multi_llm_manager.query(
                            ai_id=ai_id,
                            prompt=clean_query,
                            context=context
                        )
                        results[ai_name] = result
                    except Exception as e:
                        results[ai_name] = {'error': str(e)}
                
                # Afficher les résultats
                display_multi_ia_results(results, client, clean_query)
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse multi-IA : {e}")
                # Fallback vers simulation
                simulate_multi_ia_analysis(query)
    else:
        # Simulation si le manager n'est pas disponible
        simulate_multi_ia_analysis(query)

def simulate_multi_ia_analysis(query: str):
    """Simulation de l'analyse multi-IA"""
    client, clean_query, query_type = extract_client_and_query(query)
    
    with st.spinner("Analyse multi-IA simulée..."):
        progress = st.progress(0)
        
        for idx, ai_name in enumerate(st.session_state.selected_ais):
            progress.progress((idx + 1) / len(st.session_state.selected_ais))
            time.sleep(0.5)
    
    st.success(f"✅ Analyse terminée par {len(st.session_state.selected_ais)} IA")
    
    # Résultats simulés
    tabs = st.tabs([ai for ai in st.session_state.selected_ais])
    
    for ai_name, tab in zip(st.session_state.selected_ais, tabs):
        with tab:
            st.info(f"Résultats de l'analyse par {ai_name}")
            st.warning("Configuration du Multi-LLM Manager requise pour des résultats réels")
            
            # Exemple de résultat selon l'IA
            if ai_name == "ChatGPT 4":
                st.markdown("""
                ### Analyse stratégique
                - Points forts du dossier identifiés
                - Faiblesses à consolider
                - Stratégie recommandée
                """)
            elif ai_name == "Claude Opus 4":
                st.markdown("""
                ### Argumentation juridique
                - Arguments principaux développés
                - Contre-arguments anticipés
                - Structure de plaidoirie proposée
                """)
            elif ai_name == "Perplexity":
                st.markdown("""
                ### Jurisprudence pertinente
                - Décisions récentes identifiées
                - Évolution jurisprudentielle
                - Sources actualisées
                """)

def display_multi_ia_results(results: Dict, client: str, query: str):
    """Affiche les résultats réels du Multi-LLM Manager"""
    st.success(f"✅ Analyse terminée par {len(results)} IA")
    
    # Créer des tabs pour chaque IA
    tabs = st.tabs(list(results.keys()))
    
    for ai_name, tab in zip(results.keys(), tabs):
        with tab:
            result = results[ai_name]
            
            if 'error' in result:
                st.error(f"Erreur : {result['error']}")
            else:
                # Afficher le résultat structuré
                if isinstance(result, dict):
                    for key, value in result.items():
                        st.markdown(f"### {key}")
                        st.write(value)
                else:
                    st.write(result)
    
    # Synthèse comparative
    if len(results) > 1:
        st.markdown("### 🔄 Synthèse comparative")
        
        # Analyser le consensus
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("IA consultées", len(results))
        with col2:
            successful = sum(1 for r in results.values() if 'error' not in r)
            st.metric("Analyses réussies", successful)
        with col3:
            consensus = (successful / len(results)) * 100
            st.metric("Taux de réussite", f"{consensus:.0f}%")

def process_module_query(query: str):
    """Traite une requête vers un module spécifique"""
    if st.session_state.target_module:
        module_id = st.session_state.target_module
    else:
        intent = st.session_state.azure_openai_manager.analyze_query_intent(query)
        module_id = intent['module']
    
    st.session_state[f'{module_id}_query'] = query
    st.session_state.current_view = module_id
    st.rerun()

def show_modules_grid():
    """Affiche tous les modules disponibles pour le droit pénal des affaires"""
    st.markdown("### 📋 Modules spécialisés - Droit Pénal des Affaires")
    
    # Grouper les modules par catégorie
    categories = {}
    for module_id, config in module_manager.module_configs.items():
        if config['active']:
            category = config.get('category', 'autre')
            if category not in categories:
                categories[category] = []
            categories[category].append((module_id, config))
    
    # Ordre des catégories
    category_order = ['analyse', 'strategie', 'generation', 'expertise']
    
    for category in category_order:
        if category in categories:
            modules = categories[category]
            st.markdown(f"#### {category.title()}")
            
            cols_per_row = 3
            rows = (len(modules) + cols_per_row - 1) // cols_per_row
            
            for row in range(rows):
                cols = st.columns(cols_per_row)
                
                for col_idx in range(cols_per_row):
                    module_idx = row * cols_per_row + col_idx
                    if module_idx < len(modules):
                        module_id, config = modules[module_idx]
                        
                        # Vérifier si le module est chargé
                        is_loaded = module_id in module_manager.modules_status['loaded']
                        
                        with cols[col_idx]:
                            card_class = "module-card success" if is_loaded else "module-card error"
                            
                            st.markdown(f"""
                            <div class="{card_class}">
                                <h4 style="margin: 0.5rem 0;">{config['name']}</h4>
                                <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 0.5rem 0;">
                                    {config['desc']}
                                </p>
                                <p style="font-size: 0.7rem; margin-top: 0.5rem;">
                                    {"✅ Disponible" if is_loaded else "⚠️ Configuration requise"}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(
                                "Ouvrir" if is_loaded else "Configurer",
                                key=f"open_{module_id}",
                                use_container_width=True,
                                type="primary" if is_loaded else "secondary"
                            ):
                                st.session_state.current_view = module_id
                                st.rerun()

def show_diagnostics_with_stats():
    """Affiche les diagnostics avec statistiques complètes"""
    st.markdown("### 🔧 Diagnostics et statistiques")
    
    # Services Azure
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
        },
        {
            'name': 'Multi-LLM Manager',
            'manager': st.session_state.multi_llm_manager,
            'required': True,
            'icon': '🎭'
        }
    ]
    
    # État des services
    cols = st.columns(len(services))
    for idx, service in enumerate(services):
        with cols[idx]:
            manager = service['manager']
            is_connected = manager is not None and (not hasattr(manager, 'connected') or manager.connected)
            
            if is_connected:
                st.success(f"{service['icon']} {service['name']} ✅")
            elif service['required']:
                st.error(f"{service['icon']} {service['name']} ❌")
            else:
                st.warning(f"{service['icon']} {service['name']} ⚠️")
            
            if hasattr(manager, 'error') and manager.error:
                st.caption(manager.error[:50])
    
    # Statistiques des documents
    if st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected:
        st.markdown("### 📊 Statistiques des dossiers pénaux")
        
        stats = st.session_state.azure_blob_manager.get_statistics()
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Documents totaux</div>
            </div>
            """.format(stats['total_documents']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Dossiers pénaux</div>
            </div>
            """.format(stats['containers']), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Types de pièces</div>
            </div>
            """.format(len(stats['documents_by_type'])), unsafe_allow_html=True)
        
        # Détail par type
        st.markdown("#### 📁 Répartition par type de document")
        cols = st.columns(len(stats['documents_by_type']))
        
        for idx, (doc_type, count) in enumerate(stats['documents_by_type'].items()):
            with cols[idx]:
                type_info = DOCUMENT_TYPES.get(doc_type, {'icon': '📄', 'name': doc_type.title()})
                st.metric(
                    f"{type_info['icon']} {type_info['name']}",
                    count
                )
    
    # Diagnostic des modules
    st.markdown("---")
    show_modules_diagnostic()

def show_sidebar():
    """Sidebar avec navigation et actions rapides pour le pénal"""
    with st.sidebar:
        st.markdown("## ⚖️ IA Juridique - Pénal des Affaires")
        
        # Statut rapide
        blob_ok = st.session_state.azure_blob_manager and st.session_state.azure_blob_manager.connected
        search_ok = st.session_state.azure_search_manager and st.session_state.azure_search_manager.connected
        ai_ok = st.session_state.azure_openai_manager and st.session_state.azure_openai_manager.connected
        llm_ok = st.session_state.multi_llm_manager is not None
        
        status_icons = []
        if blob_ok:
            status_icons.append("💾✅")
        if search_ok:
            status_icons.append("🔍✅")
        if ai_ok:
            status_icons.append("🤖✅")
        if llm_ok:
            status_icons.append("🎭✅")
        
        if status_icons:
            st.success(" ".join(status_icons))
        
        # Navigation principale
        st.markdown("### 🏠 Navigation")
        
        if st.button("🏠 Accueil", use_container_width=True, type="primary" if st.session_state.current_view == "dashboard" else "secondary"):
            st.session_state.current_view = "dashboard"
            st.rerun()
        
        # Modules par catégorie
        st.markdown("### 📋 Modules pénaux")
        
        # Grouper par catégorie
        categories = {}
        for module_id, config in module_manager.module_configs.items():
            if config['active']:
                cat = config.get('category', 'autre')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((module_id, config))
        
        # Afficher par catégorie
        category_names = {
            'analyse': '🔍 Analyse',
            'strategie': '⚖️ Stratégie',
            'generation': '📄 Génération',
            'expertise': '🎓 Expertise'
        }
        
        for category in ['analyse', 'strategie', 'generation', 'expertise']:
            if category in categories:
                modules = categories[category]
                with st.expander(f"**{category_names.get(category, category.title())}** ({len(modules)})", expanded=(category == 'analyse')):
                    for module_id, config in modules:
                        is_loaded = module_id in module_manager.modules_status['loaded']
                        
                        if st.button(
                            config['name'],
                            key=f"nav_{module_id}",
                            use_container_width=True,
                            help=f"{config['desc']} {'✅' if is_loaded else '⚠️'}"
                        ):
                            st.session_state.current_view = module_id
                            st.rerun()
        
        st.markdown("---")
        
        # Actions rapides pénales
        st.markdown("### ⚡ Actions rapides")
        
        quick_actions = [
            ("🔍 Nullités", "procedure_verification", "vérifier les nullités de procédure"),
            ("⚡ Contradictions", "contradiction_analysis", "analyser les contradictions"),
            ("⚖️ Stratégie", "strategy_juridique", "élaborer la stratégie de défense"),
            ("🎯 Plaidoirie", "plaidoirie", "préparer la plaidoirie"),
            ("💰 Quantum", "risk_assessment", "évaluer le quantum de peine")
        ]
        
        for label, module, action in quick_actions:
            if st.button(label, key=f"quick_{action[:10]}", use_container_width=True):
                st.session_state.current_view = module
                st.session_state.search_query = action
                st.rerun()
        
        # Dossiers avec alias
        if blob_ok:
            st.markdown("---")
            st.markdown("### 📁 Dossiers pénaux")
            
            aliases = get_folder_aliases()
            containers = st.session_state.azure_blob_manager.list_containers()
            
            if containers:
                # Recherche rapide d'infraction
                infraction_search = st.text_input("🔍 Rechercher infraction", key="infraction_search")
                
                if infraction_search:
                    matching = st.session_state.azure_blob_manager.search_containers_by_infraction(infraction_search)
                    if matching:
                        st.success(f"{len(matching)} dossier(s) trouvé(s)")
                        for container in matching[:5]:
                            if st.button(f"📂 {container}", key=f"inf_{container}", use_container_width=True):
                                st.session_state.search_query = f"@{container}, "
                                st.session_state.current_view = "dashboard"
                                st.rerun()
                else:
                    # Afficher les dossiers récents
                    for container in containers[:10]:
                        alias = None
                        for a, c in aliases.items():
                            if c == container:
                                alias = a
                                break
                        
                        display_name = f"@{alias}" if alias else f"📂 {container}"
                        
                        if st.button(
                            display_name,
                            key=f"folder_{container}",
                            use_container_width=True,
                            help=f"Dossier : {container}"
                        ):
                            st.session_state.search_query = f"@{alias}, " if alias else f"@{container}, "
                            st.session_state.current_view = "dashboard"
                            st.rerun()
        
        # Configuration
        st.markdown("---")
        if st.button("⚙️ Configuration", key="nav_config", use_container_width=True):
            st.session_state.current_view = "config"
            st.rerun()

# ========== VUES PRINCIPALES ==========
def show_dashboard():
    """Page d'accueil avec focus droit pénal des affaires"""
    st.markdown("# ⚖️ IA Juridique - Assistant Droit Pénal des Affaires")
    
    # Message d'accueil contextualisé
    st.info("""
    🎯 **Bienvenue dans votre assistant IA spécialisé en droit pénal des affaires**
    
    Analysez vos dossiers pénaux avec l'intelligence artificielle : détection des nullités, analyse des contradictions, 
    préparation des plaidoiries, évaluation des risques et stratégies de défense.
    """)
    
    # Sélection IA
    show_ai_selector()
    
    st.markdown("---")
    
    # BARRE DE RECHERCHE PRINCIPALE
    show_main_search_bar()
    
    # Modules disponibles
    st.markdown("---")
    show_modules_grid()
    
    # Diagnostics et statistiques
    st.markdown("---")
    show_diagnostics_with_stats()
    
    # Actions sur documents et dossiers sélectionnés
    selected_folders = st.session_state.get('selected_folders', [])
    selected_docs = st.session_state.get('selected_documents', [])
    
    if selected_folders or selected_docs:
        st.markdown("---")
        st.markdown("### 📌 Éléments sélectionnés pour analyse")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📁 Dossiers", len(selected_folders))
            if selected_folders and len(selected_folders) <= 5:
                for folder in selected_folders:
                    st.caption(f"• {folder}")
        
        with col2:
            st.metric("📄 Documents", len(selected_docs))
            if selected_docs and len(selected_docs) <= 5:
                for doc in selected_docs[:5]:
                    st.caption(f"• {doc.split('/')[-1][:30]}...")
        
        with col3:
            total_elements = len(selected_folders) + len(selected_docs)
            st.metric("📊 Total", total_elements)
        
        # Actions disponibles
        st.markdown("#### Actions disponibles")
        cols = st.columns(6)
        actions = [
            ("🔍 Analyser", "analyser la sélection"),
            ("⚡ Contradictions", "détecter les contradictions"),
            ("📅 Timeline", "créer la chronologie"),
            ("⚖️ Nullités", "vérifier les nullités"),
            ("📊 Synthèse", "synthétiser les éléments"),
            ("❌ Effacer", "clear")
        ]
        
        for idx, (label, action) in enumerate(actions):
            with cols[idx]:
                if st.button(label, key=f"selected_action_{idx}", use_container_width=True):
                    if action == "clear":
                        st.session_state.selected_documents = []
                        st.session_state.selected_folders = []
                        st.rerun()
                    else:
                        # Construire la requête avec les éléments sélectionnés
                        elements = []
                        if selected_folders:
                            elements.append(f"{len(selected_folders)} dossier(s)")
                        if selected_docs:
                            elements.append(f"{len(selected_docs)} document(s)")
                        
                        st.session_state.search_query = f"{action} sur : {', '.join(elements)}"
                        process_multi_ia_analysis(st.session_state.search_query)

def show_config():
    """Page de configuration détaillée"""
    st.markdown("# ⚙️ Configuration")
    
    tabs = st.tabs(["💾 Blob Storage", "🔍 Search", "🤖 OpenAI", "🎭 Multi-LLM", "📋 Modules"])
    
    with tabs[0]:
        st.markdown("""
        ### Configuration Azure Blob Storage
        
        Variable d'environnement requise :
        ```
        AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
        ```
        """)
        
        if st.button("🔄 Tester la connexion"):
            st.session_state.azure_blob_manager = AzureBlobManager()
            st.rerun()
    
    with tabs[1]:
        st.markdown("""
        ### Configuration Azure Search
        
        Variables requises :
        ```
        AZURE_SEARCH_ENDPOINT=https://...
        AZURE_SEARCH_KEY=...
        AZURE_SEARCH_INDEX=...
        ```
        """)
    
    with tabs[2]:
        st.markdown("""
        ### Configuration Azure OpenAI
        
        Variables requises :
        ```
        AZURE_OPENAI_ENDPOINT=https://...
        AZURE_OPENAI_KEY=...
        AZURE_OPENAI_DEPLOYMENT=...
        ```
        """)
    
    with tabs[3]:
        st.markdown("""
        ### Configuration Multi-LLM Manager
        
        Le manager Multi-LLM permet d'interroger simultanément :
        - ChatGPT 4
        - Claude Opus 4
        - Perplexity
        - Gemini
        - Mistral
        
        **État :** {'✅ Disponible' if MULTI_LLM_AVAILABLE else '❌ Non disponible'}
        """)
        
        if not MULTI_LLM_AVAILABLE:
            st.error("Le module multi_llm_manager n'est pas trouvé. Vérifiez qu'il est bien présent dans le projet.")
    
    with tabs[4]:
        st.markdown("### État détaillé des modules")
        
        # Diagnostic complet
        show_modules_diagnostic()
        
        # Tableau récapitulatif
        st.markdown("### 📊 Tableau récapitulatif")
        
        module_data = []
        for module_id, config in module_manager.module_configs.items():
            is_loaded = module_id in module_manager.modules_status['loaded']
            error = module_manager.modules_status['failed'].get(module_id, '')
            
            module_data.append({
                "Module": config['name'],
                "ID": module_id,
                "Catégorie": config.get('category', 'autre'),
                "État": "✅ Chargé" if is_loaded else "❌ Erreur",
                "Erreur": error if error else "-",
                "Description": config['desc']
            })
        
        st.dataframe(module_data, use_container_width=True, hide_index=True)
        
        # Instructions pour créer les modules manquants
        st.markdown("### 📝 Instructions pour les modules manquants")
        st.info("""
        Pour chaque module en erreur :
        1. Créez le fichier `modules/nom_module.py`
        2. Ajoutez une fonction `run()` qui sera le point d'entrée
        3. Utilisez le template fourni comme base
        4. Redémarrez l'application
        """)

# ========== FONCTION PRINCIPALE ==========
def main():
    """Point d'entrée principal"""
    init_session_state()
    
    # Injection du JavaScript
    components.html(SEARCH_JAVASCRIPT, height=0)
    
    # Sidebar
    show_sidebar()
    
    # Router
    current_view = st.session_state.get('current_view', 'dashboard')
    
    if current_view == 'dashboard':
        show_dashboard()
    elif current_view == 'config':
        show_config()
    elif current_view in module_manager.module_configs:
        # Charger le module
        module_manager.run_module(current_view)
    else:
        show_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: var(--text-secondary); font-size: 0.7rem;'>
        IA Juridique v5.0 - Droit Pénal des Affaires • Multi-LLM intégré • Tous modules disponibles
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()