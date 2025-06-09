# modules/recherche.py
"""Module de recherche unifié optimisé - Combine toutes les fonctionnalités"""

import streamlit as st
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
import pandas as pd
from enum import Enum
from dataclasses import dataclass, field

# ========================= IMPORTS DEPUIS ADVANCED_FEATURES =========================

try:
    from modules.advanced_features import (
        # Fonctions principales
        generate_advanced_plainte,
        verify_jurisprudences_in_plainte,
        compare_ai_generations,
        show_plainte_statistics,
        show_improvement_suggestions,
        perform_legal_search,
        manage_documents_advanced,
        enhanced_multi_llm_comparison,
        use_dynamic_generators,
        
        # Gestion des pièces
        collect_available_documents,
        group_documents_by_category,
        determine_document_category,
        calculate_piece_relevance,
        create_bordereau,
        create_bordereau_document,
        export_piece_list,
        synthesize_selected_pieces,
        show_piece_selection_advanced,
        show_bordereau_interface_advanced,
        
        # Utils
        show_document_statistics,
        save_current_work,
        show_work_statistics,
        process_plainte_request,
        
        # Configuration
        REDACTION_STYLES,
        DOCUMENT_TEMPLATES,
        MANAGERS
    )
    HAS_ADVANCED_FEATURES = True
except ImportError:
    HAS_ADVANCED_FEATURES = False
    REDACTION_STYLES = {}
    DOCUMENT_TEMPLATES = {}
    MANAGERS = {}

# ========================= IMPORTS DES MODULES SPÉCIFIQUES =========================

MODULES_AVAILABLE = {}
MODULE_FUNCTIONS = {}

# Import conditionnel de tous les modules
modules_to_import = [
    ('analyse_ia', ['show_page']),
    ('bordereau', ['process_bordereau_request', 'create_bordereau']),
    ('comparison', ['process_comparison_request']),
    ('configuration', ['show_page']),
    ('email', ['process_email_request']),
    ('explorer', ['show_explorer_interface']),
    ('import_export', ['process_import_request', 'process_export_request']),
    ('jurisprudence', ['process_jurisprudence_request', 'show_jurisprudence_interface']),
    ('mapping', ['process_mapping_request']),
    ('plaidoirie', ['process_plaidoirie_request']),
    ('preparation_client', ['process_preparation_client_request']),
    ('redaction_unified', ['process_redaction_request']),
    ('selection_piece', ['show_page']),
    ('synthesis', ['process_synthesis_request']),
    ('templates', ['process_template_request']),
    ('timeline', ['process_timeline_request'])
]

for module_name, functions in modules_to_import:
    try:
        module = __import__(f'modules.{module_name}', fromlist=functions)
        MODULES_AVAILABLE[module_name] = True
        
        for func_name in functions:
            if hasattr(module, func_name):
                if func_name == 'show_page':
                    # Renommer pour éviter les conflits
                    MODULE_FUNCTIONS[f'{module_name}_page'] = getattr(module, func_name)
                else:
                    MODULE_FUNCTIONS[func_name] = getattr(module, func_name)
    except ImportError:
        MODULES_AVAILABLE[module_name] = False

# ========================= IMPORTS DES MANAGERS ET MODELS =========================

try:
    from managers.azure_blob_manager import AzureBlobManager
    from managers.azure_search_manager import AzureSearchManager
    from managers.multi_llm_manager import MultiLLMManager
    from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
    from managers.company_info_manager import get_company_info_manager
    from managers.style_analyzer import StyleAnalyzer
    
    MANAGERS_AVAILABLE = True
except ImportError:
    MANAGERS_AVAILABLE = False

try:
    from models.dataclasses import (
        Document,
        Partie,
        TypePartie,
        PieceSelectionnee,
        PhaseProcedure,
        TypeDocument,
        TypeAnalyse,
        QueryAnalysis,
        InfractionAffaires
    )
    
    from config.app_config import (
        ANALYSIS_PROMPTS_AFFAIRES,
        ANALYSIS_PROMPTS_INFRACTIONS
    )
    
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    
    # Classes minimales de fallback
    class TypeAnalyse(Enum):
        GENERAL = "general"
        RISQUES_JURIDIQUES = "risques_juridiques"
        CONFORMITE = "conformite"
        STRATEGIE = "strategie"
        INFRACTIONS = "infractions"
    
    class PhaseProcedure(Enum):
        ENQUETE_PRELIMINAIRE = "enquete_preliminaire"
        INSTRUCTION = "instruction"
        JUGEMENT = "jugement"
        APPEL = "appel"
    
    class TypeDocument(Enum):
        DOCUMENT = "document"
        CONCLUSIONS = "conclusions"
        PLAINTE = "plainte"
        COURRIER = "courrier"
        ASSIGNATION = "assignation"
        MISE_EN_DEMEURE = "mise_en_demeure"
    
    @dataclass
    class QueryAnalysis:
        original_query: str
        query_lower: str
        timestamp: datetime
        reference: Optional[str] = None
        document_type: Optional[Any] = None
        action: Optional[str] = None
        subject_matter: Optional[str] = None
        phase_procedurale: Optional[Any] = None
        parties: Optional[Dict[str, List[str]]] = None
        infractions: Optional[List[str]] = None
        style_request: Optional[str] = None
        parties_enrichies: Optional[Dict[str, List[Any]]] = None

# ========================= CLASSE PRINCIPALE =========================

class UniversalSearchInterface:
    """Interface de recherche universelle optimisée - VERSION COMPLÈTE"""
    
    def __init__(self):
        """Initialisation de l'interface"""
        self.company_manager = get_company_info_manager() if MANAGERS_AVAILABLE else None
        self.style_analyzer = StyleAnalyzer() if MANAGERS_AVAILABLE else None
        self.current_phase = PhaseProcedure.ENQUETE_PRELIMINAIRE
        
        # Cache pour optimisation
        self._query_cache = {}
        self._document_cache = {}
    
    async def process_universal_query(self, query: str):
        """Traite une requête universelle de manière asynchrone"""
        
        # Vérifier le cache
        if query in self._query_cache:
            return self._query_cache[query]
        
        # Sauvegarder la requête
        st.session_state.last_universal_query = query
        
        # Analyser la requête avec la méthode complète
        query_analysis = self._analyze_query_enhanced(query)
        
        # Router vers le bon processeur
        processor = self._get_query_processor(query_analysis)
        
        if processor:
            result = await processor(query, query_analysis)
            # Mettre en cache
            self._query_cache[query] = result
            return result
        else:
            # Recherche simple par défaut
            return await self._process_search_request(query, query_analysis)
    
    def _analyze_query_enhanced(self, query: str) -> QueryAnalysis:
        """Analyse améliorée de la requête retournant un objet QueryAnalysis"""
        
        # Créer l'objet QueryAnalysis
        query_analysis = QueryAnalysis(
            original_query=query,
            query_lower=query.lower(),
            timestamp=datetime.now()
        )
        
        # Extraire la référence @
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            query_analysis.reference = ref_match.group(1)
        
        # Détecter le type de document
        doc_types = {
            'conclusions': TypeDocument.CONCLUSIONS,
            'plainte': TypeDocument.PLAINTE,
            'courrier': TypeDocument.COURRIER,
            'assignation': TypeDocument.ASSIGNATION,
            'mise en demeure': TypeDocument.MISE_EN_DEMEURE
        }
        
        for keyword, doc_type in doc_types.items():
            if keyword in query_analysis.query_lower:
                query_analysis.document_type = doc_type
                break
        
        # Détecter l'action principale
        actions = {
            'rédiger': 'redaction',
            'analyser': 'analysis',
            'rechercher': 'search',
            'comparer': 'comparison',
            'créer': 'creation',
            'synthétiser': 'synthesis',
            'importer': 'import',
            'exporter': 'export'
        }
        
        for keyword, action in actions.items():
            if keyword in query_analysis.query_lower:
                query_analysis.action = action
                break
        
        # Détecter le sujet
        subjects = {
            'abus de biens sociaux': ['abus', 'biens', 'sociaux'],
            'corruption': ['corruption'],
            'fraude': ['fraude'],
            'escroquerie': ['escroquerie'],
            'blanchiment': ['blanchiment']
        }
        
        for subject, keywords in subjects.items():
            if all(kw in query_analysis.query_lower for kw in keywords):
                query_analysis.subject_matter = subject
                break
        
        # Ajouter les analyses supplémentaires
        query_analysis.phase_procedurale = self._detect_procedural_phase(query)
        query_analysis.parties = self._extract_parties(query)
        query_analysis.infractions = self._extract_infractions(query)
        query_analysis.style_request = self._detect_style_request(query)
        
        return query_analysis
    
    def _detect_procedural_phase(self, query: str) -> PhaseProcedure:
        """Détecte la phase procédurale depuis la requête"""
        query_lower = query.lower()
        
        phase_keywords = {
            PhaseProcedure.ENQUETE_PRELIMINAIRE: [
                'enquête', 'plainte', 'signalement', 'dépôt de plainte',
                'procureur', 'parquet', 'officier de police judiciaire'
            ],
            PhaseProcedure.INSTRUCTION: [
                'instruction', 'juge d\'instruction', 'mis en examen',
                'témoin assisté', 'commission rogatoire', 'ordonnance'
            ],
            PhaseProcedure.JUGEMENT: [
                'audience', 'tribunal', 'jugement', 'plaidoirie',
                'prévenu', 'réquisitoire', 'correctionnel'
            ],
            PhaseProcedure.APPEL: [
                'appel', 'cour d\'appel', 'appelant', 'intimé'
            ]
        }
        
        for phase, keywords in phase_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return phase
        
        return PhaseProcedure.ENQUETE_PRELIMINAIRE
    
    def _extract_parties(self, query: str) -> Dict[str, List[str]]:
        """Extrait les parties de la requête"""
        
        query_lower = query.lower()
        parties = {'demandeurs': [], 'defendeurs': []}
        
        # Patterns de parties demanderesses
        demandeurs_patterns = [
            ('interconstruction', 'INTERCONSTRUCTION'),
            ('vinci', 'VINCI'),
            ('sogeprom', 'SOGEPROM RÉALISATIONS'),
            ('demathieu bard', 'DEMATHIEU BARD'),
            ('bouygues', 'BOUYGUES'),
            ('eiffage', 'EIFFAGE'),
            ('spie', 'SPIE BATIGNOLLES'),
            ('leon grosse', 'LEON GROSSE')
        ]
        
        # Patterns de parties défenderesses
        defendeurs_patterns = [
            ('perinet', 'M. PERINET'),
            ('périnet', 'M. PÉRINET'),
            ('vp invest', 'VP INVEST'),
            ('perraud', 'M. PERRAUD'),
            ('martin', 'M. MARTIN'),
            ('dupont', 'M. DUPONT')
        ]
        
        # Extraction intelligente
        if ' pour ' in query_lower and ' contre ' in query_lower:
            partie_pour = query_lower.split(' pour ')[1].split(' contre ')[0]
            partie_contre = query_lower.split(' contre ')[1]
            
            for pattern, nom in demandeurs_patterns:
                if pattern in partie_pour:
                    parties['demandeurs'].append(nom)
            
            for pattern, nom in defendeurs_patterns:
                if pattern in partie_contre:
                    parties['defendeurs'].append(nom)
        else:
            # Recherche globale
            for pattern, nom in demandeurs_patterns:
                if pattern in query_lower:
                    parties['demandeurs'].append(nom)
            
            for pattern, nom in defendeurs_patterns:
                if pattern in query_lower:
                    parties['defendeurs'].append(nom)
        
        return parties
    
    def _extract_infractions(self, query: str) -> List[str]:
        """Extrait les infractions mentionnées"""
        
        query_lower = query.lower()
        infractions = []
        
        # Utiliser les infractions de l'enum si disponible
        infractions_patterns = {
            'escroquerie': 'Escroquerie (art. 313-1 Code pénal)',
            'abus de confiance': 'Abus de confiance (art. 314-1 Code pénal)',
            'abus de biens sociaux': 'Abus de biens sociaux (art. L241-3 et L242-6 Code de commerce)',
            'faux': 'Faux et usage de faux (art. 441-1 Code pénal)',
            'corruption': 'Corruption (art. 432-11 et 433-1 Code pénal)',
            'trafic d\'influence': 'Trafic d\'influence (art. 432-11 et 433-2 Code pénal)',
            'favoritisme': 'Favoritisme (art. 432-14 Code pénal)',
            'prise illégale': 'Prise illégale d\'intérêts (art. 432-12 Code pénal)',
            'blanchiment': 'Blanchiment (art. 324-1 Code pénal)',
            'fraude fiscale': 'Fraude fiscale (art. 1741 Code général des impôts)',
            'travail dissimulé': 'Travail dissimulé (art. L8221-3 Code du travail)',
            'marchandage': 'Marchandage (art. L8231-1 Code du travail)',
            'entrave': 'Entrave (art. L2328-1 Code du travail)',
            'banqueroute': 'Banqueroute (art. L654-2 Code de commerce)',
            'recel': 'Recel (art. 321-1 Code pénal)'
        }
        
        for pattern, infraction in infractions_patterns.items():
            if pattern in query_lower:
                infractions.append(infraction)
        
        return infractions
    
    def _detect_style_request(self, query: str) -> Optional[str]:
        """Détecte une demande de style spécifique"""
        
        query_lower = query.lower()
        
        # Recherche de style explicite
        for style_id, style_info in REDACTION_STYLES.items():
            if style_info['name'].lower() in query_lower:
                return style_id
        
        # Recherche de style implicite
        if 'comme d\'habitude' in query_lower or 'style habituel' in query_lower:
            return 'learned'
        
        return None
    
    def _get_query_processor(self, query_analysis: QueryAnalysis):
        """Retourne le processeur approprié pour la requête"""
        
        query_lower = query_analysis.query_lower
        
        # RÉDACTION (incluant plaintes)
        if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer', 'plainte', 'conclusions', 'courrier', 'assignation']):
            return self._process_redaction_request
        
        # PLAIDOIRIE
        elif any(word in query_lower for word in ['plaidoirie', 'plaider', 'audience']):
            return self._process_plaidoirie_request
        
        # PRÉPARATION CLIENT
        elif any(word in query_lower for word in ['préparer client', 'préparation', 'coaching']):
            return self._process_preparation_client_request
        
        # IMPORT
        elif any(word in query_lower for word in ['import', 'importer', 'charger', 'upload']):
            return self._process_import_request
        
        # EXPORT
        elif any(word in query_lower for word in ['export', 'exporter', 'télécharger', 'download']):
            return self._process_export_request
        
        # EMAIL
        elif any(word in query_lower for word in ['email', 'envoyer', 'mail', 'courrier électronique']):
            return self._process_email_request
        
        # ANALYSE
        elif any(word in query_lower for word in ['analyser', 'analyse', 'étudier', 'examiner']):
            return self._process_analysis_request
        
        # PIÈCES
        elif any(word in query_lower for word in ['sélectionner pièces', 'pièces', 'sélection']):
            return self._process_piece_selection_request
        
        # BORDEREAU
        elif 'bordereau' in query_lower:
            return self._process_bordereau_request
        
        # SYNTHÈSE
        elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
            return self._process_synthesis_request
        
        # TEMPLATES
        elif any(word in query_lower for word in ['template', 'modèle', 'gabarit']):
            return self._process_template_request
        
        # JURISPRUDENCE
        elif any(word in query_lower for word in ['jurisprudence', 'juris', 'décision', 'arrêt']):
            return self._process_jurisprudence_request
        
        # CHRONOLOGIE
        elif any(word in query_lower for word in ['chronologie', 'timeline', 'frise']):
            return self._process_timeline_request
        
        # CARTOGRAPHIE
        elif any(word in query_lower for word in ['cartographie', 'mapping', 'carte', 'réseau']):
            return self._process_mapping_request
        
        # COMPARAISON
        elif any(word in query_lower for word in ['comparer', 'comparaison', 'différences']):
            return self._process_comparison_request
        
        return None
    
    # ===================== PROCESSEURS DE REQUÊTES =====================
    
    async def _process_redaction_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de rédaction"""
        
        st.info("📝 Détection d'une demande de rédaction...")
        
        # Cas spécifique : plainte
        if 'plainte' in query_analysis.query_lower:
            if HAS_ADVANCED_FEATURES:
                # Utiliser le module avancé
                return await process_plainte_request(query, query_analysis)
            else:
                # Fallback simple
                return await self._generate_simple_plainte(query, query_analysis)
        
        # Autres rédactions
        if 'process_redaction_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_redaction_request'](query, query_analysis)
        else:
            st.warning("Module de rédaction non disponible")
    
    async def _process_analysis_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'analyse"""
        
        if 'analyse_ia_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['analyse_ia_page']()
        else:
            st.warning("Module d'analyse non disponible")
    
    async def _process_plaidoirie_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de plaidoirie"""
        
        if 'process_plaidoirie_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_plaidoirie_request'](query, query_analysis)
        else:
            st.warning("Module plaidoirie non disponible")
    
    async def _process_preparation_client_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de préparation client"""
        
        if 'process_preparation_client_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_preparation_client_request'](query, query_analysis)
        else:
            st.warning("Module préparation client non disponible")
    
    async def _process_import_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'import"""
        
        if 'process_import_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_import_request'](query, query_analysis)
        else:
            st.warning("Module import non disponible")
    
    async def _process_export_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'export"""
        
        if 'process_export_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_export_request'](query, query_analysis)
        else:
            st.warning("Module export non disponible")
    
    async def _process_email_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'email"""
        
        if 'process_email_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_email_request'](query, query_analysis)
        else:
            st.warning("Module email non disponible")
    
    async def _process_piece_selection_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de sélection de pièces"""
        
        if 'selection_piece_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['selection_piece_page']()
        elif HAS_ADVANCED_FEATURES:
            show_piece_selection_advanced(query_analysis)
        else:
            st.warning("Module sélection de pièces non disponible")
    
    async def _process_bordereau_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de bordereau"""
        
        if 'process_bordereau_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_bordereau_request'](query, query_analysis)
        elif HAS_ADVANCED_FEATURES:
            docs = collect_available_documents(query_analysis)
            if docs:
                show_bordereau_interface_advanced(docs, query_analysis)
        else:
            st.warning("Module bordereau non disponible")
    
    async def _process_synthesis_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de synthèse"""
        
        if 'process_synthesis_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_synthesis_request'](query, query_analysis)
        elif HAS_ADVANCED_FEATURES and st.session_state.get('selected_pieces'):
            return await synthesize_selected_pieces(st.session_state.selected_pieces)
        else:
            st.warning("Module synthèse non disponible ou aucune pièce sélectionnée")
    
    async def _process_template_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de template"""
        
        if 'process_template_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_template_request'](query, query_analysis)
        else:
            st.warning("Module templates non disponible")
    
    async def _process_jurisprudence_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de jurisprudence"""
        
        if 'process_jurisprudence_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_jurisprudence_request'](query, query_analysis)
        elif 'show_jurisprudence_interface' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['show_jurisprudence_interface']()
        else:
            st.warning("Module jurisprudence non disponible")
    
    async def _process_timeline_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de timeline"""
        
        if 'process_timeline_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_timeline_request'](query, query_analysis)
        else:
            st.warning("Module timeline non disponible")
    
    async def _process_mapping_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de cartographie"""
        
        if 'process_mapping_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_mapping_request'](query, query_analysis)
        else:
            st.warning("Module cartographie non disponible")
    
    async def _process_comparison_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de comparaison"""
        
        if 'process_comparison_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_comparison_request'](query, query_analysis)
        else:
            st.warning("Module comparaison non disponible")
    
    async def _process_search_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de recherche par défaut"""
        
        st.info("🔍 Recherche en cours...")
        
        # Effectuer la recherche
        results = await self._perform_search(query, query_analysis)
        
        # Stocker les résultats
        st.session_state.search_results = results
        
        if not results:
            st.warning("⚠️ Aucun résultat trouvé")
        else:
            st.success(f"✅ {len(results)} résultats trouvés")
        
        return results
    
    async def _perform_search(self, query: str, query_analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """Effectue la recherche"""
        
        results = []
        
        # Recherche locale
        query_words = query.lower().split()
        
        for doc_id, doc in st.session_state.get('azure_documents', {}).items():
            score = 0
            
            # S'assurer que doc a les bons attributs
            if hasattr(doc, 'content'):
                content_lower = doc.content.lower()
                title_lower = doc.title.lower()
            else:
                content_lower = doc.get('content', '').lower()
                title_lower = doc.get('title', '').lower()
            
            for word in query_words:
                if word in title_lower:
                    score += 2
                if word in content_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    'id': doc_id,
                    'title': title_lower,
                    'content': content_lower,
                    'score': score / len(query_words)
                })
        
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:50]
    
    async def _generate_simple_plainte(self, query: str, query_analysis: QueryAnalysis):
        """Génère une plainte simple (fallback)"""
        
        parties = query_analysis.parties.get('defendeurs', [])
        infractions = query_analysis.infractions or ['Abus de biens sociaux']
        
        content = f"""PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE

Je soussigné(e) [NOM PRÉNOM]
Demeurant [ADRESSE]

Ai l'honneur de porter plainte avec constitution de partie civile contre :
{chr(10).join(['- ' + p for p in parties]) if parties else '- [PARTIES]'}

Pour les faits suivants :
[EXPOSÉ DES FAITS]

Ces faits sont susceptibles de recevoir la qualification de :
{chr(10).join(['- ' + i for i in infractions])}

Je me constitue partie civile et sollicite la désignation d'un juge d'instruction.

Fait à [VILLE], le {datetime.now().strftime('%d/%m/%Y')}
Signature
"""
        
        st.session_state.generated_plainte = content
        st.session_state.search_results = {
            'type': 'plainte',
            'content': content
        }
        
        return {'type': 'plainte', 'content': content}

# ========================= FONCTION PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    # Initialiser l'interface
    if 'search_interface' not in st.session_state:
        st.session_state.search_interface = UniversalSearchInterface()
    
    interface = st.session_state.search_interface
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # État des modules
    if st.checkbox("🔧 Voir l'état des modules"):
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
        
        query = st.text_input(
            "Entrez votre commande ou recherche",
            value=default_value,
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
    
    with col2:
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Suggestions de commandes
    with st.expander("💡 Exemples de commandes", expanded=False):
        st.markdown("""
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        
        **Analyse :**
        - `analyser les risques @dossier_pénal`
        - `identifier les infractions @affaire_corruption`
        
        **Rédaction :**
        - `rédiger conclusions défense @affaire_martin abus biens sociaux`
        - `créer plainte avec constitution partie civile escroquerie`
        - `rédiger plainte contre Vinci, SOGEPROM @projet_26_05_2025`
        
        **Synthèse :**
        - `synthétiser les pièces @dossier_fraude`
        - `résumer les auditions @affaire_martin`
        
        **Gestion :**
        - `sélectionner pièces @dossier catégorie procédure`
        - `créer bordereau @pièces_sélectionnées`
        - `importer documents PDF`
        - `exporter analyse format word`
        """)
    
    # Menu d'actions rapides
    show_quick_actions()
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            # Utiliser une nouvelle boucle d'événements
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
            if HAS_ADVANCED_FEATURES:
                save_current_work()
            else:
                st.warning("Fonction non disponible")
    
    with col2:
        if st.button("📊 Afficher les statistiques", key="show_stats"):
            if HAS_ADVANCED_FEATURES:
                asyncio.run(show_work_statistics())
            else:
                st.warning("Fonction non disponible")
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            st.info("Fonctionnalité de partage à implémenter")

def show_modules_status():
    """Affiche l'état détaillé des modules"""
    with st.expander("🔧 État des modules et fonctions", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Modules disponibles", sum(1 for v in MODULES_AVAILABLE.values() if v))
            st.metric("Fonctions importées", len(MODULE_FUNCTIONS))
        
        with col2:
            st.metric("Managers disponibles", sum(1 for v in MANAGERS.values() if v))
            st.metric("Advanced features", "✅" if HAS_ADVANCED_FEATURES else "❌")
        
        with col3:
            st.metric("Models disponibles", "✅" if MODELS_AVAILABLE else "❌")
            st.metric("Configuration", "✅" if MANAGERS_AVAILABLE else "❌")
        
        # Liste détaillée
        st.markdown("### 📋 Modules actifs")
        for module, available in MODULES_AVAILABLE.items():
            if available:
                st.success(f"✅ {module}")
            else:
                st.error(f"❌ {module}")

def show_quick_actions():
    """Affiche les actions rapides"""
    col1, col2, col3, col4 = st.columns(4)
    
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

def show_unified_results():
    """Affiche tous les types de résultats de manière unifiée"""
    
    # Vérifier tous les types de résultats possibles
    results_found = False
    
    # Résultats de rédaction
    if st.session_state.get('redaction_result'):
        show_redaction_results()
        results_found = True
    
    # Plainte générée
    elif st.session_state.get('generated_plainte'):
        show_plainte_results()
        results_found = True
    
    # Résultats d'analyse
    elif st.session_state.get('ai_analysis_results'):
        show_analysis_results()
        results_found = True
    
    # Résultats de recherche
    elif st.session_state.get('search_results'):
        show_search_results()
        results_found = True
    
    # Résultats de synthèse
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        results_found = True
    
    # Autres résultats...
    elif st.session_state.get('timeline_result'):
        show_timeline_results()
        results_found = True
    
    elif st.session_state.get('bordereau_result'):
        show_bordereau_results()
        results_found = True
    
    elif st.session_state.get('jurisprudence_results'):
        show_jurisprudence_results()
        results_found = True
    
    if not results_found:
        st.info("💡 Utilisez la barre de recherche universelle pour commencer")

def show_redaction_results():
    """Affiche les résultats de rédaction"""
    result = st.session_state.redaction_result
    
    st.markdown("### 📝 Document juridique généré")
    
    # Contenu éditable
    edited_content = st.text_area(
        "Contenu du document",
        value=result.get('document', result.get('content', '')),
        height=600,
        key="edit_redaction"
    )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📥 Télécharger",
            edited_content.encode('utf-8'),
            f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("📧 Envoyer"):
            st.session_state.pending_email = {'content': edited_content}
    
    with col3:
        if st.button("🔄 Régénérer"):
            st.session_state.process_query = True
            st.rerun()

def show_plainte_results():
    """Affiche les résultats de génération de plainte"""
    content = st.session_state.generated_plainte
    
    st.markdown("### 📋 Plainte générée")
    
    # Options avancées si disponibles
    if HAS_ADVANCED_FEATURES:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("✨ Version avancée", key="upgrade_plainte"):
                query = st.session_state.get('last_universal_query', '')
                asyncio.run(generate_advanced_plainte(query))
    
    # Contenu éditable
    edited_content = st.text_area(
        "Contenu de la plainte",
        value=content,
        height=600,
        key="edit_plainte"
    )
    
    # Actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.download_button(
            "📥 Télécharger",
            edited_content.encode('utf-8'),
            f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("📊 Statistiques", key="stats_plainte"):
            if HAS_ADVANCED_FEATURES:
                show_plainte_statistics(edited_content)
    
    with col3:
        if st.button("✅ Vérifier", key="verify_plainte"):
            if HAS_ADVANCED_FEATURES:
                verify_jurisprudences_in_plainte(edited_content)
    
    with col4:
        if st.button("🔄 Régénérer", key="regen_plainte"):
            st.session_state.process_query = True
            st.rerun()

def show_analysis_results():
    """Affiche les résultats d'analyse"""
    results = st.session_state.ai_analysis_results
    
    st.markdown("### 🤖 Résultats de l'analyse")
    
    # Contenu
    st.text_area(
        "Analyse",
        value=results.get('content', ''),
        height=400,
        key="analysis_content"
    )
    
    # Métadonnées
    if results.get('document_count'):
        st.info(f"📄 Documents analysés : {results['document_count']}")

def show_search_results():
    """Affiche les résultats de recherche"""
    results = st.session_state.search_results
    
    if isinstance(results, dict) and results.get('type') == 'plainte':
        show_plainte_results()
    elif isinstance(results, list):
        st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
        
        for i, result in enumerate(results[:10], 1):
            with st.expander(f"{i}. {result.get('title', 'Sans titre')}"):
                st.write(result.get('content', '')[:500] + '...')
                st.caption(f"Score: {result.get('score', 0):.0%}")

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

def show_timeline_results():
    """Affiche les résultats de timeline"""
    st.markdown("### ⏱️ Chronologie des événements")
    st.info("Timeline générée")

def show_bordereau_results():
    """Affiche les résultats de bordereau"""
    st.markdown("### 📊 Bordereau de communication")
    st.info("Bordereau généré")

def show_jurisprudence_results():
    """Affiche les résultats de jurisprudence"""
    st.markdown("### ⚖️ Jurisprudences trouvées")
    st.info("Résultats de jurisprudence")

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'current_analysis',
        'redaction_result', 'ai_analysis_results', 'search_results',
        'synthesis_result', 'selected_pieces', 'import_files',
        'generated_plainte', 'timeline_result', 'bordereau_result',
        'jurisprudence_results'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()
    