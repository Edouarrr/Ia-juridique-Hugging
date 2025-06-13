"""Module de recherche unifié avec compréhension du langage naturel et routage intelligent vers les modules"""

import streamlit as st
import asyncio
import re
import html
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from difflib import SequenceMatcher

# ========================= IMPORTS CENTRALISÉS =========================

# Import du service de recherche depuis les managers
try:
    from managers.universal_search_service import UniversalSearchService, get_universal_search_service
    SEARCH_SERVICE_AVAILABLE = True
except ImportError:
    SEARCH_SERVICE_AVAILABLE = False
    # Définir une classe de fallback pour UniversalSearchService
    class UniversalSearchService:
        def __init__(self):
            self.cache = {}
        
        def analyze_query_advanced(self, query: str):
            return self._simple_query_analysis(query)
        
        def _simple_query_analysis(self, query: str):
            class SimpleQueryAnalysis:
                def __init__(self, query):
                    self.original_query = query
                    self.query_lower = query.lower()
                    self.timestamp = datetime.now()
                    self.command_type = 'search'
                    self.reference = None
                    self.parties = {'demandeurs': [], 'defendeurs': []}
                    self.infractions = []
            
            return SimpleQueryAnalysis(query)
        
        async def search(self, query: str):
            class SearchResult:
                def __init__(self):
                    self.documents = []
                    self.facets = {}
                    self.suggestions = []
            return SearchResult()
        
        def generate_reference_suggestions(self, partial: str):
            return []
        
        def collect_all_references(self):
            return []
        
        def clear_cache(self):
            self.cache.clear()
        
        async def get_search_statistics(self):
            return {
                'total_searches': 0,
                'average_results': 0,
                'cache_size': 0,
                'popular_keywords': {}
            }
    
    def get_universal_search_service():
        return UniversalSearchService()

# Import des dataclasses et configurations
try:
    from modules.dataclasses import (
        Document, DocumentJuridique, Partie, TypePartie, PhaseProcedure,
        TypeDocument, TypeAnalyse, QueryAnalysis, InfractionAffaires,
        PieceSelectionnee, BordereauPieces, collect_available_documents,
        group_documents_by_category,
        InfractionIdentifiee, FactWithSource, SourceReference, ArgumentStructure,
        StyleLearningResult, StyleConfig, learn_document_style
    )
    DATACLASSES_AVAILABLE = True
except ImportError:
    DATACLASSES_AVAILABLE = False
    # Classes de fallback minimales
    class Document:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class QueryAnalysis:
        def __init__(self, original_query, **kwargs):
            self.original_query = original_query
            self.query_lower = original_query.lower()
            self.timestamp = datetime.now()
            self.command_type = 'search'
            self.reference = None
            self.parties = {'demandeurs': [], 'defendeurs': []}
            self.infractions = []
            for k, v in kwargs.items():
                setattr(self, k, v)

# Import des configurations
try:
    from models.configurations import (
        DEFAULT_STYLE_CONFIGS, BUILTIN_DOCUMENT_TEMPLATES,
        DEFAULT_LETTERHEADS, FORMULES_JURIDIQUES,
        ARGUMENTATION_PATTERNS, ANALYSIS_CONFIGS
    )
    CONFIGURATIONS_AVAILABLE = True
except ImportError:
    CONFIGURATIONS_AVAILABLE = False
    DEFAULT_STYLE_CONFIGS = {}
    BUILTIN_DOCUMENT_TEMPLATES = {}
    DEFAULT_LETTERHEADS = {}
    FORMULES_JURIDIQUES = {}
    ARGUMENTATION_PATTERNS = {}
    ANALYSIS_CONFIGS = {}

# ========================= IMPORTS POUR IA ET LANGAGE NATUREL =========================

# Import des APIs LLM pour analyse en langage naturel
try:
    from utils.api_utils import get_available_models, call_llm_api
    HAS_API_UTILS = True
except ImportError:
    HAS_API_UTILS = False
    def get_available_models():
        return ["claude-3-sonnet", "gpt-4", "gpt-3.5-turbo"]
    
    async def call_llm_api(prompt, model="claude-3-sonnet", temperature=0.3, max_tokens=2000):
        return "API non disponible - Génération de contenu désactivée"

# Import du LLM Manager
try:
    from managers.llm_manager import LLMManager, get_llm_manager
    LLM_MANAGER_AVAILABLE = True
except ImportError:
    LLM_MANAGER_AVAILABLE = False

# Import du Multi-LLM Manager
try:
    from managers.multi_llm_manager import MultiLLMManager
    MULTI_LLM_AVAILABLE = True
except ImportError:
    MULTI_LLM_AVAILABLE = False

# ========================= IMPORTS MODULES JURIDIQUES =========================

# Import du module d'intégration juridique
try:
    from modules.integration_juridique import (
        enhance_search_with_generation,
        AnalyseurRequeteJuridique,
        process_juridical_generation
    )
    JURIDIQUE_AVAILABLE = True
except ImportError:
    JURIDIQUE_AVAILABLE = False
    print("⚠️ Module integration_juridique non disponible")

# Import du module de génération
try:
    from modules.generation_juridique import show_page as show_generation_page
    GENERATION_MODULE_AVAILABLE = True
except ImportError:
    GENERATION_MODULE_AVAILABLE = False
    print("⚠️ Module generation_juridique non disponible")

# Import du module de génération longue
try:
    from modules.generation_longue import (
        GenerateurDocumentsLongs,
        show_generation_longue_interface
    )
    GENERATION_LONGUE_AVAILABLE = True
except ImportError:
    GENERATION_LONGUE_AVAILABLE = False
    print("⚠️ Module generation_longue non disponible")

# Import du cahier des charges
try:
    from config.cahier_des_charges import (
        STRUCTURES_ACTES,
        PROMPTS_GENERATION,
        validate_acte
    )
    CAHIER_CHARGES_AVAILABLE = True
except ImportError:
    CAHIER_CHARGES_AVAILABLE = False
    print("⚠️ Cahier des charges non disponible")

# ========================= CLASSE NaturalLanguageAnalyzer AMÉLIORÉE =========================

class NaturalLanguageAnalyzer:
    """Analyseur de langage naturel pour comprendre les requêtes utilisateur"""
    
    def __init__(self):
        self.llm_manager = None
        if LLM_MANAGER_AVAILABLE:
            try:
                self.llm_manager = get_llm_manager()
            except:
                pass
        
        if not self.llm_manager and MULTI_LLM_AVAILABLE:
            try:
                self.multi_llm = MultiLLMManager()
            except:
                self.multi_llm = None
        else:
            self.multi_llm = None
    
    async def analyze_natural_query(self, query: str) -> Dict[str, Any]:
        """
        Analyse une requête en langage naturel et extrait les éléments structurés
        """
        # Prompt amélioré pour détecter les documents longs
        analysis_prompt = f"""Tu es un assistant juridique expert. Analyse cette requête et extrais les informations structurées.

Requête : "{query}"

Extrais et structure les informations suivantes au format JSON :
{{
    "intention": "search|prepare|create|analyze|synthesize|other",
    "action_principale": "description de l'action demandée",
    "reference_dossier": "référence du dossier si mentionnée (ex: Lesueur)",
    "type_document": "type de document recherché ou à créer",
    "document_complexite": "simple|standard|long|exhaustif",
    "longueur_estimee": "courte|moyenne|longue|tres_longue",
    "parties": {{
        "demandeurs": ["liste des demandeurs"],
        "defendeurs": ["liste des défendeurs"]
    }},
    "contexte": "audience|procédure|urgence|normal",
    "elements_juridiques": ["infractions ou éléments juridiques mentionnés"],
    "contraintes_temporelles": "date ou délai mentionné",
    "mots_cles_importants": ["mots-clés pertinents pour la recherche"],
    "indicateurs_complexite": ["exhaustif", "complet", "détaillé", "approfondi", "long"],
    "requete_reformulee": "reformulation claire de la requête pour recherche"
}}

IMPORTANT : 
- Si la requête contient des mots comme "exhaustif", "complet", "détaillé", "approfondi", "long", "50 pages", mettre document_complexite = "exhaustif" et longueur_estimee = "tres_longue"
- Pour "plainte", "conclusions", "mémoire" sans autre indication : document_complexite = "standard"
- Pour "note", "courrier", "email" : document_complexite = "simple"

Exemples :
- "Rédige une plainte exhaustive contre Vinci" → document_complexite: "exhaustif", longueur_estimee: "tres_longue"
- "Prépare des conclusions complètes" → document_complexite: "long", longueur_estimee: "longue"
- "Écris un courrier au client" → document_complexite: "simple", longueur_estimee: "courte"

Réponds UNIQUEMENT avec le JSON, sans autre texte."""

        try:
            # Essayer avec le LLM manager principal
            if self.llm_manager and HAS_API_UTILS:
                response = await call_llm_api(
                    prompt=analysis_prompt,
                    model="claude-3-sonnet",
                    temperature=0.2,
                    max_tokens=1000
                )
            elif self.multi_llm:
                provider = list(self.multi_llm.clients.keys())[0] if self.multi_llm.clients else None
                if provider:
                    result = self.multi_llm.query_single_llm(
                        provider,
                        analysis_prompt,
                        "Tu es un assistant expert en analyse sémantique."
                    )
                    response = result['response'] if result['success'] else None
                else:
                    response = None
            else:
                response = None
            
            if response:
                import json
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
            
        except Exception as e:
            st.warning(f"Analyse IA temporairement indisponible : {str(e)}")
        
        # Fallback : analyse basique par règles
        return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> Dict[str, Any]:
        """Analyse de fallback basée sur des règles si l'IA n'est pas disponible"""
        query_lower = query.lower()
        
        # Détection de l'intention
        intention = "search"
        action_principale = "rechercher des documents"
        
        if any(word in query_lower for word in ['prépare', 'préparer', 'préparation']):
            intention = "prepare"
            action_principale = "préparer le client"
        elif any(word in query_lower for word in ['rédige', 'rédiger', 'créer', 'écrire', 'génère', 'générer']):
            intention = "create"
            action_principale = "rédiger un document"
        elif any(word in query_lower for word in ['analyse', 'analyser']):
            intention = "analyze"
            action_principale = "analyser les documents"
        elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
            intention = "synthesize"
            action_principale = "faire une synthèse"
        
        # Détection du type de document
        type_document = None
        if 'plainte' in query_lower:
            type_document = 'plainte'
        elif 'conclusions' in query_lower:
            type_document = 'conclusions'
        elif 'mémoire' in query_lower:
            type_document = 'mémoire'
        elif 'courrier' in query_lower or 'lettre' in query_lower:
            type_document = 'courrier'
        elif 'citation' in query_lower:
            type_document = 'citation'
        
        # Détection de la complexité
        document_complexite = "standard"
        longueur_estimee = "moyenne"
        
        # Mots indiquant un document long/exhaustif
        if any(word in query_lower for word in ['exhaustif', 'exhaustive', 'complet', 'complète', 
                                                 'détaillé', 'détaillée', 'approfondi', 'approfondie',
                                                 'long', 'longue', '50 pages', '40 pages', '30 pages']):
            document_complexite = "exhaustif"
            longueur_estimee = "tres_longue"
        elif any(word in query_lower for word in ['simple', 'court', 'bref', 'succinct']):
            document_complexite = "simple"
            longueur_estimee = "courte"
        
        # Extraction de la référence
        reference = None
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            reference = ref_match.group(1)
        
        # Détection du contexte
        contexte = "normal"
        if 'audience' in query_lower:
            contexte = "audience"
        elif 'urgent' in query_lower or 'urgence' in query_lower:
            contexte = "urgence"
        elif 'procédure' in query_lower:
            contexte = "procédure"
        
        # Extraction des parties
        parties = {"demandeurs": [], "defendeurs": []}
        
        # Pattern pour "contre X"
        contre_match = re.findall(r'contre\s+([A-Z][A-Za-z\s,&]+?)(?:\s+pour|\s+et|\s*,|\s*$)', query, re.IGNORECASE)
        if contre_match:
            parties['defendeurs'] = [p.strip() for p in contre_match]
        
        # Extraction des mots-clés importants
        mots_vides = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'pour', 'avec', 'dans', 'sur'}
        mots_cles = [mot for mot in query.split() if mot.lower() not in mots_vides and len(mot) > 2]
        
        return {
            "intention": intention,
            "action_principale": action_principale,
            "reference_dossier": reference,
            "type_document": type_document,
            "document_complexite": document_complexite,
            "longueur_estimee": longueur_estimee,
            "parties": parties,
            "contexte": contexte,
            "elements_juridiques": [],
            "contraintes_temporelles": None,
            "mots_cles_importants": mots_cles,
            "indicateurs_complexite": [],
            "requete_reformulee": query
        }

# ========================= CLASSE UniversalSearchInterface =========================

class UniversalSearchInterface:
    """Interface de recherche universelle"""
    
    def __init__(self):
        self.search_service = get_universal_search_service() if SEARCH_SERVICE_AVAILABLE else None
        self.nl_analyzer = NaturalLanguageAnalyzer()
    
    def show_interface(self):
        """Affiche l'interface de recherche universelle"""
        show_page()

# ========================= CLASSE SearchInterface MODIFIÉE =========================

class SearchInterface:
    """Interface utilisateur pour le module de recherche avec compréhension du langage naturel"""
    
    def __init__(self):
        """Initialisation avec le service de recherche universelle"""
        if SEARCH_SERVICE_AVAILABLE:
            self.search_service = get_universal_search_service()
        else:
            self.search_service = None
        
        # Phase par défaut
        if DATACLASSES_AVAILABLE:
            try:
                self.current_phase = PhaseProcedure.ENQUETE_PRELIMINAIRE
            except:
                self.current_phase = None
        else:
            self.current_phase = None
        
        # Ajouter l'analyseur juridique
        if JURIDIQUE_AVAILABLE:
            self.analyseur_juridique = AnalyseurRequeteJuridique()
        else:
            self.analyseur_juridique = None
        
        # Ajouter l'analyseur de langage naturel
        self.nl_analyzer = NaturalLanguageAnalyzer()
    
    async def process_universal_query(self, query: str):
        """Traite une requête en utilisant d'abord l'analyse en langage naturel"""
        
        # Sauvegarder la requête
        st.session_state.last_universal_query = query
        
        # Analyse en langage naturel d'abord
        with st.spinner("🧠 Analyse de votre demande en cours..."):
            nl_analysis = await self.nl_analyzer.analyze_natural_query(query)
            st.session_state.nl_analysis = nl_analysis
        
        # Afficher l'analyse si demandé
        if st.session_state.get('show_nl_analysis', False):
            with st.expander("🤖 Analyse IA de votre requête", expanded=True):
                st.json(nl_analysis)
        
        # NOUVEAU : Logique de routage améliorée
        # 1. Si c'est une création de document
        if nl_analysis['intention'] == 'create' and nl_analysis.get('type_document'):
            
            # Vérifier d'abord si c'est un document long/exhaustif
            if nl_analysis.get('document_complexite') in ['exhaustif', 'long'] or \
               nl_analysis.get('longueur_estimee') in ['longue', 'tres_longue']:
                
                # Rediriger vers le module de génération longue
                if GENERATION_LONGUE_AVAILABLE:
                    st.info("📜 Redirection vers le module de génération de documents longs...")
                    st.session_state.show_generation_longue = True
                    st.session_state.juridique_context = {
                        'type_acte': self._map_type_document_to_acte(nl_analysis['type_document']),
                        'parties': nl_analysis.get('parties', {}),
                        'infractions': nl_analysis.get('elements_juridiques', []),
                        'contexte': nl_analysis.get('contexte', ''),
                        'from_nl': True
                    }
                    st.rerun()
                    return
                else:
                    st.warning("Module de génération longue non disponible, utilisation du module standard")
            
            # Sinon, utiliser le module de génération standard
            if GENERATION_MODULE_AVAILABLE:
                st.info("⚖️ Redirection vers le module de génération juridique...")
                st.session_state.show_juridique_module = True
                st.session_state.juridique_context = nl_analysis
                st.rerun()
                return
            else:
                st.error("Aucun module de génération disponible")
                return
        
        # 2. Si c'est une préparation
        elif nl_analysis['intention'] == 'prepare':
            return await self._process_preparation_from_nl(query, nl_analysis)
        
        # 3. Si c'est une analyse
        elif nl_analysis['intention'] == 'analyze':
            return await self._process_analysis_from_nl(query, nl_analysis)
        
        # 4. Si c'est une synthèse
        elif nl_analysis['intention'] == 'synthesize':
            return await self._process_synthesis_from_nl(query, nl_analysis)
        
        # 5. Sinon, recherche améliorée
        else:
            # Enrichir la requête avec l'analyse NL
            enhanced_query = self._enhance_query_from_nl(query, nl_analysis)
            
            # Continuer avec la recherche standard
            if self.search_service:
                query_analysis = self.search_service.analyze_query_advanced(enhanced_query)
            else:
                query_analysis = self._simple_query_analysis(enhanced_query)
            
            # Enrichir l'analyse avec les données du NL
            if nl_analysis.get('parties'):
                query_analysis.parties = nl_analysis['parties']
            if nl_analysis.get('elements_juridiques'):
                query_analysis.infractions = nl_analysis['elements_juridiques']
            
            return await self._process_search_request(enhanced_query, query_analysis)
    
    def _map_type_document_to_acte(self, type_document: str) -> str:
        """Convertit le type de document détecté en type d'acte pour le module de génération"""
        mapping = {
            'plainte': 'plainte_cpc',
            'conclusions': 'conclusions_fond',
            'mémoire': 'conclusions_appel',
            'citation': 'citation_directe',
            'requête': 'requete',
            'courrier': 'courrier',
            'observations': 'observations_175'
        }
        
        # Si le type exact n'est pas trouvé, essayer de deviner
        type_lower = (type_document or '').lower()
        for key, value in mapping.items():
            if key in type_lower:
                return value
        
        # Par défaut
        return 'plainte_cpc'
    
    def _enhance_query_from_nl(self, original_query: str, nl_analysis: Dict) -> str:
        """Enrichit la requête originale avec les éléments extraits par l'analyse NL"""
        
        enhanced_query = nl_analysis.get('requete_reformulee', original_query)
        
        # Ajouter la référence si détectée et pas déjà présente
        if nl_analysis.get('reference_dossier') and '@' not in enhanced_query:
            enhanced_query = f"@{nl_analysis['reference_dossier']} {enhanced_query}"
        
        # Ajouter les mots-clés importants s'ils ne sont pas déjà présents
        if nl_analysis.get('mots_cles_importants'):
            for mot_cle in nl_analysis['mots_cles_importants']:
                if mot_cle.lower() not in enhanced_query.lower():
                    enhanced_query += f" {mot_cle}"
        
        # Ajouter le contexte si pertinent
        if nl_analysis.get('contexte') and nl_analysis['contexte'] != 'normal':
            if nl_analysis['contexte'] not in enhanced_query.lower():
                enhanced_query += f" {nl_analysis['contexte']}"
        
        return enhanced_query
    
    async def _process_preparation_from_nl(self, query: str, nl_analysis: Dict):
        """Traite une demande de préparation client basée sur l'analyse NL"""
        st.info("📋 Préparation client détectée")
        
        # Enrichir le contexte avec l'analyse
        preparation_context = {
            'reference': nl_analysis.get('reference_dossier'),
            'contexte': nl_analysis.get('contexte', 'audience'),
            'action': nl_analysis.get('action_principale'),
            'contraintes': nl_analysis.get('contraintes_temporelles'),
            'parties': nl_analysis.get('parties', {}),
            'elements_juridiques': nl_analysis.get('elements_juridiques', [])
        }
        
        # Stocker le contexte
        st.session_state.preparation_context = preparation_context
        
        # Rediriger vers le module approprié
        if 'preparation_client_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['preparation_client_page']()
        else:
            # Si pas de module, faire une recherche contextuelle
            search_query = f"@{nl_analysis.get('reference_dossier', '')} preparation {nl_analysis.get('contexte', '')} checklist guide"
            return await self._process_search_request(search_query, None)
    
    async def _process_analysis_from_nl(self, query: str, nl_analysis: Dict):
        """Traite une demande d'analyse basée sur l'analyse NL"""
        st.info("🔍 Analyse détectée")
        
        # Préparer le contexte d'analyse
        analysis_context = {
            'reference': nl_analysis.get('reference_dossier'),
            'focus': nl_analysis.get('action_principale'),
            'elements': nl_analysis.get('elements_juridiques', []),
            'type_analyse': self._determine_analysis_type(nl_analysis)
        }
        
        st.session_state.analysis_context = analysis_context
        
        if 'analyse_ia_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['analyse_ia_page']()
        else:
            st.warning("Module d'analyse non disponible")
    
    async def _process_synthesis_from_nl(self, query: str, nl_analysis: Dict):
        """Traite une demande de synthèse basée sur l'analyse NL"""
        st.info("📑 Synthèse détectée")
        
        synthesis_context = {
            'reference': nl_analysis.get('reference_dossier'),
            'focus': nl_analysis.get('mots_cles_importants', []),
            'type_synthese': 'complete' if 'complet' in query.lower() else 'resumee'
        }
        
        st.session_state.synthesis_context = synthesis_context
        
        if 'synthesis_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['synthesis_page']()
        else:
            # Rechercher et synthétiser directement
            if nl_analysis.get('reference_dossier'):
                search_query = f"@{nl_analysis['reference_dossier']}"
                results = await self._process_search_request(search_query, None)
                if results and hasattr(results, 'documents') and results.documents:
                    await synthesize_selected_pieces(results.documents[:10])
    
    def _determine_analysis_type(self, nl_analysis: Dict) -> str:
        """Détermine le type d'analyse à effectuer"""
        query_lower = nl_analysis.get('original_query', '').lower()
        
        if 'risque' in query_lower:
            return 'risques'
        elif 'infraction' in query_lower:
            return 'infractions'
        elif 'chronolog' in query_lower:
            return 'chronologique'
        elif 'partie' in query_lower:
            return 'parties'
        elif 'preuve' in query_lower:
            return 'preuves'
        else:
            return 'complete'
    
    def _simple_query_analysis(self, query: str):
        """Analyse simple de la requête si le service n'est pas disponible"""
        if DATACLASSES_AVAILABLE:
            analysis = QueryAnalysis(
                original_query=query,
                query_lower=query.lower(),
                timestamp=datetime.now()
            )
        else:
            class SimpleQueryAnalysis:
                def __init__(self, query):
                    self.original_query = query
                    self.query_lower = query.lower()
                    self.timestamp = datetime.now()
                    self.command_type = 'search'
                    self.reference = None
                    self.parties = {'demandeurs': [], 'defendeurs': []}
                    self.infractions = []
            
            analysis = SimpleQueryAnalysis(query)
        
        # Détection basique du type de commande
        query_lower = analysis.query_lower
        if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer']):
            analysis.command_type = 'redaction'
        elif any(word in query_lower for word in ['plainte', 'cpc']):
            analysis.command_type = 'plainte'
        elif any(word in query_lower for word in ['analyse', 'analyser']):
            analysis.command_type = 'analysis'
        
        # Extraction basique de la référence
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            analysis.reference = ref_match.group(1)
        
        return analysis
    
    async def _process_search_request(self, query: str, query_analysis):
        """Traite une demande de recherche par défaut"""
        st.info("🔍 Recherche en cours...")
        
        if self.search_service:
            # Utiliser le service de recherche
            search_result = await self.search_service.search(query)
            
            # Stocker les résultats
            st.session_state.search_results = search_result.documents
            
            if not search_result.documents:
                st.warning("⚠️ Aucun résultat trouvé")
                # Proposer des alternatives basées sur l'analyse NL
                if 'nl_analysis' in st.session_state and st.session_state.nl_analysis.get('mots_cles_importants'):
                    st.info("💡 Essayez avec ces mots-clés : " + ', '.join(st.session_state.nl_analysis['mots_cles_importants']))
            else:
                st.success(f"✅ {len(search_result.documents)} résultats trouvés")
                
                # Afficher les facettes si disponibles
                if search_result.facets:
                    with st.expander("🔍 Filtres disponibles"):
                        for facet_name, facet_values in search_result.facets.items():
                            st.write(f"**{facet_name}**")
                            for value, count in facet_values.items():
                                st.write(f"- {value}: {count}")
                
                # Afficher les suggestions si disponibles
                if search_result.suggestions:
                    st.info("💡 Suggestions de recherche:")
                    cols = st.columns(min(len(search_result.suggestions), 3))
                    for i, suggestion in enumerate(search_result.suggestions):
                        with cols[i]:
                            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                                st.session_state.pending_query = suggestion
                                st.rerun()
            
            return search_result
        else:
            # Fallback simple
            st.warning("Service de recherche non disponible")
            return []

# ========================= FONCTIONS UTILITAIRES LOCALES =========================

def determine_document_category(doc: Dict[str, Any]) -> str:
    """Détermine la catégorie d'un document"""
    if doc.get('category'):
        return doc['category']
    
    title = doc.get('title', '').lower()
    content = doc.get('content', '').lower()[:1000]
    
    category_keywords = {
        'Procédure': ['assignation', 'citation', 'conclusions', 'jugement', 'arrêt', 'ordonnance', 
                      'requête', 'pourvoi', 'appel', 'mémoire', 'audience'],
        'Expertise': ['expertise', 'expert', 'rapport d\'expertise', 'évaluation', 'diagnostic',
                      'constat', 'analyse technique', 'étude'],
        'Contrat': ['contrat', 'convention', 'accord', 'bail', 'cession', 'pacte', 'protocole',
                    'engagement', 'marché', 'commande'],
        'Correspondance': ['courrier', 'lettre', 'email', 'courriel', 'notification', 'mise en demeure',
                          'réponse', 'demande', 'réclamation'],
        'Comptabilité': ['facture', 'devis', 'comptable', 'bilan', 'compte', 'relevé', 'paiement',
                        'avoir', 'note de frais', 'budget'],
        'Administratif': ['statuts', 'kbis', 'pv', 'procès-verbal', 'assemblée', 'délibération',
                         'décision', 'arrêté', 'décret', 'règlement'],
        'Preuve': ['attestation', 'témoignage', 'déclaration', 'certificat', 'justificatif',
                   'preuve', 'pièce', 'élément'],
        'Pénal': ['plainte', 'garde à vue', 'audition', 'procès-verbal', 'enquête', 'instruction',
                  'commission rogatoire', 'réquisitoire']
    }
    
    best_category = 'Autre'
    max_score = 0
    
    for category, keywords in category_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in title:
                score += 2
            if keyword in content:
                score += 1
        
        if score > max_score:
            max_score = score
            best_category = category
    
    return best_category

def calculate_piece_relevance(doc: Dict[str, Any], analysis: Any) -> float:
    """Calcule la pertinence d'une pièce par rapport à l'analyse"""
    score = 0.5
    
    if not analysis:
        return score
    
    title = doc.get('title', '').lower()
    content = doc.get('content', '').lower()[:2000]
    metadata = doc.get('metadata', {})
    
    if hasattr(analysis, 'keywords'):
        for keyword in analysis.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title:
                score += 0.2
            elif keyword_lower in content:
                score += 0.1
    
    if hasattr(analysis, 'reference') and analysis.reference:
        ref_lower = analysis.reference.lower()
        if ref_lower in title:
            score += 0.3
        elif ref_lower in content:
            score += 0.15
    
    if hasattr(analysis, 'parties'):
        all_parties = []
        all_parties.extend(analysis.parties.get('demandeurs', []))
        all_parties.extend(analysis.parties.get('defendeurs', []))
        
        for partie in all_parties:
            partie_lower = partie.lower()
            if partie_lower in title:
                score += 0.15
            elif partie_lower in content:
                score += 0.08
    
    if hasattr(analysis, 'infractions'):
        for infraction in analysis.infractions:
            infraction_lower = infraction.lower()
            if infraction_lower in title or infraction_lower in content:
                score += 0.1
    
    if metadata.get('date'):
        try:
            doc_date = datetime.fromisoformat(str(metadata['date']))
            days_old = (datetime.now() - doc_date).days
            if days_old < 30:
                score += 0.1
            elif days_old < 90:
                score += 0.05
        except:
            pass
    
    if hasattr(analysis, 'document_type'):
        doc_type = determine_document_category(doc)
        if analysis.document_type == 'plainte' and doc_type in ['Pénal', 'Preuve']:
            score += 0.15
        elif analysis.document_type == 'conclusions' and doc_type == 'Procédure':
            score += 0.15
    
    return min(max(score, 0.0), 1.0)

# ========================= FONCTION ANALYSE_IA_PAGE =========================

def analyse_ia_page():
    """Page d'analyse IA"""
    st.markdown("## 🤖 Analyse IA")
    
    # Vérifier si on a un contexte d'analyse depuis la recherche NL
    if 'analysis_context' in st.session_state:
        context = st.session_state.analysis_context
        st.info(f"📋 Contexte détecté : {context.get('focus', 'Analyse')} pour {context.get('reference', 'le dossier')}")
    
    # Vérifier si des documents sont disponibles
    documents = []
    if 'azure_documents' in st.session_state:
        documents.extend(st.session_state.azure_documents.values())
    if 'imported_documents' in st.session_state:
        documents.extend(st.session_state.imported_documents.values())
    
    if not documents:
        st.warning("Aucun document disponible pour l'analyse. Importez d'abord des documents.")
        return
    
    # Options d'analyse
    col1, col2 = st.columns(2)
    
    with col1:
        # Type d'analyse avec pré-sélection si contexte
        default_type = "Analyse complète"
        if 'analysis_context' in st.session_state:
            type_map = {
                'risques': "Analyse des risques",
                'infractions': "Analyse des infractions",
                'chronologique': "Analyse chronologique",
                'parties': "Analyse des parties",
                'preuves': "Analyse des preuves"
            }
            default_type = type_map.get(st.session_state.analysis_context.get('type_analyse'), "Analyse complète")
        
        analysis_type = st.selectbox(
            "Type d'analyse",
            [
                "Analyse complète",
                "Analyse des risques",
                "Analyse des infractions",
                "Analyse chronologique",
                "Analyse des parties",
                "Analyse des preuves"
            ],
            index=[
                "Analyse complète",
                "Analyse des risques",
                "Analyse des infractions",
                "Analyse chronologique",
                "Analyse des parties",
                "Analyse des preuves"
            ].index(default_type)
        )
    
    with col2:
        # Pré-sélectionner les documents si contexte
        default_selection = []
        if 'analysis_context' in st.session_state and st.session_state.analysis_context.get('reference'):
            ref = st.session_state.analysis_context['reference'].lower()
            default_selection = [
                doc.get('title', f'Document {i}') 
                for i, doc in enumerate(documents) 
                if ref in doc.get('title', '').lower()
            ][:10]
        
        if not default_selection:
            default_selection = [doc.get('title', f'Document {i}') for i, doc in enumerate(documents[:5])]
        
        doc_selection = st.multiselect(
            "Documents à analyser",
            options=[doc.get('title', f'Document {i}') for i, doc in enumerate(documents)],
            default=default_selection
        )
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        include_citations = st.checkbox("Inclure les citations", value=True)
        include_recommendations = st.checkbox("Inclure des recommandations", value=True)
        output_format = st.selectbox(
            "Format de sortie",
            ["Rapport structuré", "Points clés", "Synthèse narrative"]
        )
    
    # Bouton d'analyse
    if st.button("🚀 Lancer l'analyse", type="primary"):
        with st.spinner(f"⏳ {analysis_type} en cours..."):
            # Ici vous appelleriez votre service d'analyse
            st.session_state.ai_analysis_results = {
                'type': analysis_type,
                'document_count': len(doc_selection),
                'timestamp': datetime.now(),
                'content': f"[Résultats de l'analyse {analysis_type} sur {len(doc_selection)} documents]"
            }
            st.success("✅ Analyse terminée !")
            st.rerun()
    
    # Afficher les résultats s'ils existent
    if 'ai_analysis_results' in st.session_state:
        show_analysis_results()

# ========================= MANAGERS AVANCÉS - IMPORT CONDITIONNEL =========================

MANAGERS = {
    'azure_blob': False,
    'azure_search': False,
    'company_info': False,
    'document_manager': False,
    'dynamic_generators': False,
    'export_manager': False,
    'jurisprudence_verifier': False,
    'legal_search': False,
    'llm_manager': False,
    'multi_llm': False,
    'style_analyzer': False,
    'template_manager': False,
    'universal_search': False
}

# Import des managers (gardé minimal pour la lisibilité)
managers_to_import = [
    ('azure_blob_manager', 'AzureBlobManager', 'azure_blob'),
    ('azure_search_manager', 'AzureSearchManager', 'azure_search'),
    ('company_info_manager', 'CompanyInfoManager', 'company_info'),
    ('document_manager', 'DocumentManager', 'document_manager'),
    ('export_manager', 'ExportManager', 'export_manager'),
    ('jurisprudence_verifier', 'JurisprudenceVerifier', 'jurisprudence_verifier'),
    ('legal_search', 'LegalSearchManager', 'legal_search'),
    ('multi_llm_manager', 'MultiLLMManager', 'multi_llm'),
    ('style_analyzer', 'StyleAnalyzer', 'style_analyzer'),
    ('template_manager', 'TemplateManager', 'template_manager')
]

for module_name, class_name, key in managers_to_import:
    try:
        exec(f"from managers.{module_name} import {class_name}")
        MANAGERS[key] = True
    except ImportError as e:
        print(f"Import {class_name} failed: {e}")

# Import des fonctions spéciales
try:
    from managers.dynamic_generators import generate_dynamic_search_prompts, generate_dynamic_templates
    MANAGERS['dynamic_generators'] = True
except ImportError as e:
    print(f"Import dynamic_generators functions failed: {e}")

# ========================= IMPORTS DES MODULES SPÉCIFIQUES =========================

MODULES_AVAILABLE = {}
MODULE_FUNCTIONS = {}

# Import conditionnel de tous les modules
modules_to_import = [
    ('bordereau', ['show_page']),
    ('comparison', ['show_page']),
    ('configuration', ['show_page']),
    ('email', ['show_page']),
    ('explorer', ['show_page']),
    ('import_export', ['show_page']),
    ('jurisprudence', ['show_page']),
    ('mapping', ['show_page']),
    ('plaidoirie', ['show_page']),
    ('preparation_client', ['show_page']),
    ('redaction_unified', ['show_page']),
    ('selection_piece', ['show_page']),
    ('synthesis', ['show_page']),
    ('templates', ['show_page']),
    ('timeline', ['show_page'])
]

for module_name, functions in modules_to_import:
    try:
        module = __import__(f'modules.{module_name}', fromlist=functions)
        MODULES_AVAILABLE[module_name] = True
        
        for func_name in functions:
            if hasattr(module, func_name):
                MODULE_FUNCTIONS[f'{module_name}_page'] = getattr(module, func_name)
    except ImportError:
        MODULES_AVAILABLE[module_name] = False

# Ajouter la fonction analyse_ia_page directement
MODULE_FUNCTIONS['analyse_ia_page'] = analyse_ia_page
MODULES_AVAILABLE['analyse_ia'] = True

# ========================= SYNTHÈSE DES PIÈCES =========================

async def synthesize_selected_pieces(pieces: List[Any]) -> Dict:
    """Synthétise les pièces sélectionnées"""
    
    if not MANAGERS['multi_llm']:
        st.error('Module Multi-LLM non disponible')
        return {'error': 'Module Multi-LLM non disponible'}
    
    try:
        from managers.multi_llm_manager import MultiLLMManager
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            st.error('Aucune IA disponible')
            return {'error': 'Aucune IA disponible'}
        
        # Construire le contexte
        context = "PIÈCES À SYNTHÉTISER:\n\n"
        
        for i, piece in enumerate(pieces[:20], 1):
            context += f"Pièce {i}: {piece.get('title', 'Sans titre')}\n"
            if piece.get('category'):
                context += f"Catégorie: {piece['category']}\n"
            if piece.get('content'):
                context += f"Extrait: {piece['content'][:200]}...\n"
            context += "\n"
        
        # Prompt de synthèse
        synthesis_prompt = f"""{context}
Crée une synthèse structurée de ces pièces.
La synthèse doit inclure:
1. Vue d'ensemble des pièces
2. Points clés par catégorie
3. Chronologie si applicable
4. Points d'attention juridiques
5. Recommandations"""
        
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            synthesis_prompt,
            "Tu es un expert en analyse de documents juridiques."
        )
        
        if response['success']:
            synthesis_result = {
                'content': response['response'],
                'piece_count': len(pieces),
                'categories': list(set(p.get('category', 'Autre') for p in pieces)),
                'timestamp': datetime.now()
            }
            st.session_state.synthesis_result = synthesis_result
            
            # Afficher directement le résultat
            with st.expander("📝 Synthèse générée", expanded=True):
                st.write(response['response'])
                
                # Actions
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Télécharger",
                        response['response'].encode('utf-8'),
                        f"synthese_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        "text/plain"
                    )
                with col2:
                    if st.button("🔄 Regénérer"):
                        st.rerun()
            
            return synthesis_result
        else:
            st.error(f"Échec de la synthèse : {response.get('error', 'Erreur inconnue')}")
            return {'error': 'Échec de la synthèse'}
            
    except Exception as e:
        st.error(f'Erreur synthèse: {str(e)}')
        return {'error': f'Erreur synthèse: {str(e)}'}

# ========================= FONCTION PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle avec compréhension du langage naturel"""
    
    # Initialiser l'interface
    if 'search_interface' not in st.session_state:
        st.session_state.search_interface = SearchInterface()
    
    interface = st.session_state.search_interface
    
    st.markdown("## 🔍 Recherche Universelle avec IA")
    
    # Toggle pour afficher l'analyse IA
    col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
    with col_header2:
        st.session_state.show_nl_analysis = st.checkbox("🧠 Voir analyse IA", value=False)
    
    with col_header3:
        if st.checkbox("🔧 État des modules"):
            show_modules_status()
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        default_value = ""
        if 'pending_query' in st.session_state:
            default_value = st.session_state.pending_query
            del st.session_state.pending_query
        elif 'universal_query' in st.session_state:
            default_value = st.session_state.universal_query
        
        query = st.text_area(
            "Entrez votre demande en langage naturel",
            value=default_value,
            placeholder="""Écrivez naturellement ce que vous souhaitez faire. L'IA comprendra votre intention.

Exemples en langage naturel :
- "J'ai besoin de préparer mon client Lesueur pour l'audience de demain"
- "Trouve-moi tous les documents sur l'affaire Vinci concernant la corruption"
- "Rédige une plainte exhaustive contre SOGEPROM pour abus de biens sociaux"
- "Fais-moi une synthèse des derniers échanges avec l'avocat adverse"
- "Analyse les risques juridiques dans le dossier Martin"
- "Crée des conclusions complètes pour l'affaire Dupont" (→ génération longue)
- "Écris un courrier simple au client" (→ génération standard)

Vous pouvez toujours utiliser @ pour référencer un dossier spécifique.""",
            key="universal_query",
            height=150,
            help="💡 Écrivez naturellement. Pour des documents longs, utilisez des mots comme 'exhaustif', 'complet', 'détaillé'."
        )
        
        # Auto-complétion des références
        if query and '@' in query:
            suggestions = get_reference_suggestions(query)
            if suggestions:
                st.markdown("**Suggestions :**")
                cols = st.columns(min(len(suggestions), 5))
                for i, suggestion in enumerate(suggestions[:5]):
                    with cols[i]:
                        if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                            parts = query.split('@')
                            if len(parts) > 1:
                                new_query = parts[0] + suggestion
                                st.session_state.pending_query = new_query
                                st.rerun()
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Prévisualisation en temps réel
    if query and '@' in query:
        parts = query.split('@')
        if len(parts) > 1:
            ref_part = parts[-1].split()[0] if parts[-1].strip() else ''
            
            if ref_part and len(ref_part) >= 2:
                show_live_preview(ref_part, query)
    
    # Afficher les références disponibles
    if st.checkbox("📁 Voir toutes les références disponibles"):
        show_available_references()
    
    # Suggestions de commandes enrichies
    with st.expander("💡 Exemples de demandes", expanded=False):
        st.markdown("""
        **🗣️ Langage naturel :**
        - `J'ai besoin de préparer mon client pour l'audience de demain`
        - `Trouve-moi les conclusions de l'avocat adverse dans l'affaire Martin`
        - `Quels sont les risques juridiques si on poursuit Vinci ?`
        - `Aide-moi à rédiger une réponse aux conclusions adverses`
        - `Fais un résumé des pièces comptables du dossier SOGEPROM`
        
        **📝 Rédaction (automatiquement routée vers le bon module) :**
        - `Rédige une plainte exhaustive contre Vinci` → Module génération longue (50+ pages)
        - `Crée des conclusions complètes pour l'appel` → Module génération longue (40+ pages)
        - `Écris une plainte simple contre Martin` → Module génération standard
        - `Prépare un courrier au client` → Module génération standard
        
        **📊 Analyse et synthèse :**
        - `Analyse les échanges de mails dans l'affaire SOGEPROM`
        - `Fais-moi un résumé chronologique des événements`
        - `Identifie les contradictions dans les témoignages`
        
        **🔍 Recherche classique :**
        - `@affaire_martin documents comptables`
        - `contrats société XYZ`
        """)
    
    # Menu d'actions rapides
    show_quick_actions()
    
    # Afficher le module juridique si demandé
    if st.session_state.get('show_juridique_module', False):
        if GENERATION_MODULE_AVAILABLE:
            show_generation_page()
            if st.button("← Retour à la recherche", key="back_to_search"):
                st.session_state.show_juridique_module = False
                st.rerun()
            return
        else:
            st.error("Module de génération juridique non disponible")
            st.session_state.show_juridique_module = False
    
    # Afficher le module de génération longue si demandé
    if st.session_state.get('show_generation_longue', False):
        if GENERATION_LONGUE_AVAILABLE:
            show_generation_longue_interface()
            if st.button("← Retour à la recherche", key="back_to_search_longue"):
                st.session_state.show_generation_longue = False
                st.rerun()
            return
        else:
            st.error("Module de génération longue non disponible")
            st.session_state.show_generation_longue = False
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(interface.process_universal_query(query))
            finally:
                loop.close()
    
    # Afficher les résultats
    show_unified_results()
    
    # Réinitialiser le flag de traitement
    if 'process_query' in st.session_state:
        st.session_state.process_query = False
    
    # Footer avec actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder le travail", key="save_work"):
            save_current_work()
    
    with col2:
        if st.button("📊 Afficher les statistiques", key="show_stats"):
            asyncio.run(show_work_statistics())
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            st.info("Fonctionnalité de partage à implémenter")

# ========================= FONCTIONS D'AFFICHAGE =========================

def show_modules_status():
    """Affiche l'état détaillé des modules et des managers"""
    with st.expander("🔧 État des modules et managers", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Modules disponibles", sum(1 for v in MODULES_AVAILABLE.values() if v))
            st.metric("Fonctions importées", len(MODULE_FUNCTIONS))
        
        with col2:
            st.metric("Managers disponibles", sum(1 for v in MANAGERS.values() if v))
            st.metric("Service de recherche", "✅" if SEARCH_SERVICE_AVAILABLE else "❌")
        
        with col3:
            if CONFIGURATIONS_AVAILABLE:
                st.metric("Templates", len(BUILTIN_DOCUMENT_TEMPLATES))
                st.metric("Styles", len(DEFAULT_STYLE_CONFIGS))
            else:
                st.metric("Templates", "❌")
                st.metric("Styles", "❌")
        
        # État du module juridique
        st.markdown("### ⚖️ Modules de génération")
        
        if GENERATION_LONGUE_AVAILABLE:
            st.success("✅ Module documents longs disponible (25-50+ pages)")
        else:
            st.error("❌ Module documents longs non disponible")
            
        if GENERATION_MODULE_AVAILABLE:
            st.success("✅ Module génération standard disponible")
        else:
            st.error("❌ Module génération standard non disponible")
        
        if JURIDIQUE_AVAILABLE:
            st.success("✅ Module d'intégration juridique disponible")
        else:
            st.error("❌ Module d'intégration juridique non disponible")

        if CAHIER_CHARGES_AVAILABLE:
            st.success("✅ Cahier des charges juridique chargé")
        else:
            st.error("❌ Cahier des charges non disponible")
        
        # État du module IA
        if HAS_API_UTILS:
            st.success("✅ APIs IA disponibles")
        else:
            st.error("❌ APIs IA non disponibles")
        
        if LLM_MANAGER_AVAILABLE:
            st.success("✅ LLM Manager disponible")
        else:
            st.error("❌ LLM Manager non disponible")

def show_quick_actions():
    """Affiche les actions rapides"""
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if st.button("📝 Nouvelle rédaction", key="quick_redaction"):
            st.session_state.pending_query = "rédiger "
            st.session_state.process_query = True
            st.rerun()
    
    with col2:
        if st.button("🤖 Analyser dossier", key="quick_analysis"):
            st.session_state.pending_query = "analyser "
            st.session_state.process_query = True
            st.rerun()
    
    with col3:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.pending_query = "importer documents"
            st.session_state.process_query = True
            st.rerun()
    
    with col4:
        if st.button("🔄 Réinitialiser", key="quick_reset"):
            clear_universal_state()
    
    with col5:
        if st.button("⚖️ Actes juridiques", key="quick_juridique"):
            if GENERATION_MODULE_AVAILABLE:
                st.session_state.show_juridique_module = True
            else:
                st.session_state.pending_query = "rédiger plainte"
                st.session_state.process_query = True
            st.rerun()
    
    with col6:
        if st.button("📜 Doc. longs", key="quick_long_docs"):
            if GENERATION_LONGUE_AVAILABLE:
                st.session_state.show_generation_longue = True
            else:
                st.session_state.pending_query = "plainte exhaustive 50 pages"
                st.session_state.process_query = True
            st.rerun()

def show_unified_results():
    """Affiche tous les types de résultats de manière unifiée"""
    
    results_found = False
    
    # Résultats de recherche
    if st.session_state.get('search_results'):
        show_search_results()
        results_found = True
    
    # Résultats d'analyse
    elif st.session_state.get('ai_analysis_results'):
        show_analysis_results()
        results_found = True
    
    # Résultats de synthèse
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        results_found = True
    
    if not results_found:
        st.info("💡 Utilisez la barre de recherche pour commencer. Écrivez naturellement ce que vous souhaitez faire.")

def show_search_results():
    """Affiche les résultats de recherche"""
    results = st.session_state.search_results
    
    if isinstance(results, list) and results:
        st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
        
        # Options de tri
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_option = st.selectbox(
                "Trier par",
                ["Pertinence", "Date", "Type"],
                key="sort_results"
            )
        
        # Afficher les résultats
        for i, result in enumerate(results[:10], 1):
            if hasattr(result, 'highlights'):
                with st.expander(f"{i}. {result.title}"):
                    if result.highlights:
                        st.markdown("**📌 Extraits pertinents:**")
                        for highlight in result.highlights:
                            st.info(f"...{highlight}...")
                    else:
                        st.write(result.content[:500] + '...')
                    
                    if hasattr(result, 'metadata') and result.metadata:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"📊 Score: {result.metadata.get('score', 0):.0f}")
                        with col2:
                            st.caption(f"📁 Source: {result.source}")
                        with col3:
                            match_type = result.metadata.get('match_type', 'standard')
                            if match_type == 'exact':
                                st.caption("✅ Correspondance exacte")
                            elif match_type == 'partial':
                                st.caption("📍 Correspondance partielle")
            else:
                with st.expander(f"{i}. {result.get('title', 'Sans titre')}"):
                    st.write(result.get('content', '')[:500] + '...')
                    st.caption(f"Score: {result.get('score', 0):.0%}")
        
        if len(results) > 10:
            st.info(f"📄 Affichage des 10 premiers résultats sur {len(results)}.")

def show_analysis_results():
    """Affiche les résultats d'analyse"""
    results = st.session_state.ai_analysis_results
    
    st.markdown("### 🤖 Résultats de l'analyse")
    
    st.text_area(
        "Analyse",
        value=results.get('content', ''),
        height=400,
        key="analysis_content"
    )
    
    if results.get('document_count'):
        st.info(f"📄 Documents analysés : {results['document_count']}")

def show_synthesis_results():
    """Affiche les résultats de synthèse"""
    result = st.session_state.synthesis_result
    
    st.markdown("### 📝 Synthèse des documents")
    
    st.text_area(
        "Contenu de la synthèse",
        value=result.get('content', ''),
        height=400,
        key="synthesis_content"
    )
    
    if result.get('piece_count'):
        st.info(f"📄 Pièces analysées : {result['piece_count']}")

# ========================= FONCTIONS UTILITAIRES =========================

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'current_analysis',
        'search_results', 'synthesis_result', 'ai_analysis_results',
        'show_juridique_module', 'show_generation_longue', 'juridique_context',
        'nl_analysis', 'analysis_context', 'preparation_context', 'synthesis_context'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    if hasattr(st.session_state, 'search_interface') and st.session_state.search_interface.search_service:
        st.session_state.search_interface.search_service.clear_cache()
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

def save_current_work() -> Dict:
    """Sauvegarde complète du travail actuel"""
    work_data = {
        'timestamp': datetime.now().isoformat(),
        'version': '2.1',
        'session_data': {},
        'results': {},
        'documents': {},
        'analysis': {}
    }
    
    session_keys = [
        'universal_query', 'last_universal_query',
        'search_results', 'synthesis_result', 'ai_analysis_results',
        'nl_analysis', 'analysis_context', 'preparation_context'
    ]
    
    for key in session_keys:
        if key in st.session_state:
            value = st.session_state[key]
            if hasattr(value, '__dict__'):
                work_data['session_data'][key] = value.__dict__
            else:
                work_data['session_data'][key] = value
    
    if 'azure_documents' in st.session_state:
        for doc_id, doc in st.session_state.azure_documents.items():
            if hasattr(doc, '__dict__'):
                work_data['documents'][doc_id] = doc.__dict__
            else:
                work_data['documents'][doc_id] = doc
    
    import json
    
    def default_serializer(obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
    
    json_str = json.dumps(work_data, indent=2, ensure_ascii=False, default=default_serializer)
    
    st.download_button(
        "💾 Sauvegarder le travail",
        json_str,
        f"sauvegarde_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="save_work_btn"
    )
    
    return work_data

async def show_work_statistics():
    """Affiche des statistiques détaillées du travail"""
    st.markdown("### 📊 Statistiques du travail")
    
    stats = {
        'Documents Azure': len(st.session_state.get('azure_documents', {})),
        'Documents importés': len(st.session_state.get('imported_documents', {})),
        'Analyses effectuées': 1 if st.session_state.get('ai_analysis_results') else 0,
        'Recherches': 1 if st.session_state.get('search_results') else 0
    }
    
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label, value)

def get_reference_suggestions(query: str) -> List[str]:
    """Obtient des suggestions de références basées sur la requête"""
    
    suggestions = []
    
    if SEARCH_SERVICE_AVAILABLE:
        service = get_universal_search_service()
        
        if '@' in query:
            parts = query.split('@')
            partial_ref = parts[-1].strip().split()[0] if parts[-1].strip() else ''
            
            if partial_ref:
                suggestions = service.generate_reference_suggestions(partial_ref)
    
    return suggestions[:5]

def collect_all_references() -> List[str]:
    """Collecte toutes les références de dossiers disponibles"""
    
    if SEARCH_SERVICE_AVAILABLE:
        service = get_universal_search_service()
        return service.collect_all_references()
    
    references = set()
    
    all_docs = {}
    all_docs.update(st.session_state.get('azure_documents', {}))
    all_docs.update(st.session_state.get('imported_documents', {}))
    
    for doc in all_docs.values():
        title = doc.get('title', '')
        
        patterns = [
            r'affaire[_\s]+(\w+)',
            r'dossier[_\s]+(\w+)',
            r'projet[_\s]+(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, title, re.IGNORECASE)
            references.update(matches)
    
    return sorted(list(references))

def find_matching_documents(reference: str) -> List[Dict]:
    """Trouve les documents correspondant à une référence partielle"""
    
    matches = []
    ref_lower = reference.lower()
    
    all_docs = {}
    all_docs.update(st.session_state.get('azure_documents', {}))
    all_docs.update(st.session_state.get('imported_documents', {}))
    
    for doc_id, doc in all_docs.items():
        title = doc.get('title', '')
        content = doc.get('content', '')[:200]
        
        if ref_lower in title.lower() or ref_lower in content.lower():
            clean_ref = extract_clean_reference(title)
            
            matches.append({
                'id': doc_id,
                'title': title,
                'type': doc.get('type', 'Document'),
                'date': doc.get('date', doc.get('metadata', {}).get('date', 'Non daté')),
                'preview': content,
                'clean_ref': clean_ref or reference,
                'score': calculate_match_score(title, content, reference)
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def extract_clean_reference(title: str) -> str:
    """Extrait une référence propre du titre"""
    
    patterns = [
        r'affaire[_\s]+(\w+)',
        r'dossier[_\s]+(\w+)',
        r'projet[_\s]+(\w+)',
        r'^(\w+_\d{4})',
        r'^(\w+)[\s_]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    words = title.split()
    for word in words:
        if len(word) > 3 and word.isalnum():
            return word
    
    return None

def calculate_match_score(title: str, content: str, reference: str) -> float:
    """Calcule un score de pertinence pour le tri"""
    
    score = 0
    ref_lower = reference.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    if ref_lower == title_lower:
        score += 100
    elif title_lower.startswith(ref_lower):
        score += 50
    elif ref_lower in title_lower:
        score += 30
    elif ref_lower in content_lower:
        score += 10
    
    if len(reference) >= 5:
        score += 5
    
    return score

def highlight_match(text: str, match: str) -> str:
    """Surligne les correspondances dans le texte"""
    
    text = html.escape(text)
    match = html.escape(match)
    
    pattern = re.compile(re.escape(match), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark style="background-color: #ffeb3b; padding: 2px;">{m.group()}</mark>',
        text
    )
    
    return highlighted

def show_live_preview(reference: str, full_query: str):
    """Affiche une prévisualisation des dossiers correspondants"""
    
    with st.container():
        matches = find_matching_documents(reference)
        
        if matches:
            st.markdown(f"### 📁 Aperçu des résultats pour **@{reference}**")
            
            for i, match in enumerate(matches[:5]):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    highlighted_title = highlight_match(match['title'], reference)
                    st.markdown(f"**{i+1}.** {highlighted_title}", unsafe_allow_html=True)
                
                with col2:
                    doc_type = match.get('type', 'Document')
                    date = match.get('date', 'Non daté')
                    st.caption(f"{doc_type} • {date}")
                
                with col3:
                    if st.button("Utiliser", key=f"use_{match['id']}", use_container_width=True):
                        new_query = full_query.replace(f"@{reference}", f"@{match['clean_ref']}")
                        st.session_state.pending_query = new_query
                        st.rerun()
            
            if len(matches) > 5:
                st.info(f"📊 {len(matches) - 5} autres résultats disponibles.")
        else:
            st.info(f"🔍 Aucun dossier trouvé pour '@{reference}'.")

def show_available_references():
    """Affiche toutes les références disponibles de manière organisée"""
    
    references = collect_all_references()
    
    if references:
        st.markdown("### 📚 Références disponibles")
        
        grouped = {}
        for ref in references:
            first_letter = ref[0].upper()
            if first_letter not in grouped:
                grouped[first_letter] = []
            grouped[first_letter].append(ref)
        
        cols = st.columns(4)
        col_idx = 0
        
        for letter in sorted(grouped.keys()):
            with cols[col_idx % 4]:
                st.markdown(f"**{letter}**")
                for ref in grouped[letter]:
                    if st.button(f"@{ref}", key=f"ref_{ref}", use_container_width=True):
                        st.session_state.pending_query = f"@{ref} "
                        st.rerun()
            col_idx += 1
    else:
        st.info("Aucune référence trouvée. Importez des documents pour commencer.")

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()