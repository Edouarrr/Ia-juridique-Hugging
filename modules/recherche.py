# modules/recherche.py
"""Module de recherche unifié optimisé - Interface principale avec toutes les fonctionnalités"""

import streamlit as st
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
import pandas as pd

# ========================= CONFIGURATION =========================

# Styles de rédaction
REDACTION_STYLES = {
    'formel': {
        'name': 'Formel',
        'description': 'Style juridique classique et solennel',
        'tone': 'respectueux et distant',
        'vocabulary': 'technique et précis'
    },
    'persuasif': {
        'name': 'Persuasif',
        'description': 'Style argumentatif et convaincant',
        'tone': 'assertif et engagé',
        'vocabulary': 'percutant et imagé'
    },
    'technique': {
        'name': 'Technique',
        'description': 'Style factuel et détaillé',
        'tone': 'neutre et objectif',
        'vocabulary': 'spécialisé et exhaustif'
    },
    'synthétique': {
        'name': 'Synthétique',
        'description': 'Style concis et efficace',
        'tone': 'direct et clair',
        'vocabulary': 'simple et précis'
    },
    'pédagogique': {
        'name': 'Pédagogique',
        'description': 'Style explicatif et accessible',
        'tone': 'bienveillant et didactique',
        'vocabulary': 'vulgarisé et illustré'
    }
}

# Templates de documents prédéfinis
DOCUMENT_TEMPLATES = {
    'conclusions_defense': {
        'name': 'Conclusions en défense',
        'structure': [
            'I. FAITS ET PROCÉDURE',
            'II. DISCUSSION',
            ' A. Sur la recevabilité',
            ' B. Sur le fond',
            ' 1. Sur l\'élément matériel',
            ' 2. Sur l\'élément intentionnel',
            ' 3. Sur le préjudice',
            'III. PAR CES MOTIFS'
        ],
        'style': 'formel'
    },
    'plainte_simple': {
        'name': 'Plainte simple',
        'structure': [
            'Objet : Plainte',
            'EXPOSÉ DES FAITS',
            'QUALIFICATION JURIDIQUE',
            'PRÉJUDICES SUBIS',
            'DEMANDES',
            'PIÈCES JOINTES'
        ],
        'style': 'formel'
    },
    'plainte_avec_cpc': {
        'name': 'Plainte avec constitution de partie civile',
        'structure': [
            'Objet : Plainte avec constitution de partie civile',
            'EXPOSÉ DES FAITS',
            'QUALIFICATION JURIDIQUE',
            'PRÉJUDICES SUBIS',
            'CONSTITUTION DE PARTIE CIVILE',
            'ÉVALUATION DU PRÉJUDICE',
            'DEMANDES',
            'PIÈCES JOINTES'
        ],
        'style': 'formel'
    },
    'mise_en_demeure': {
        'name': 'Mise en demeure',
        'structure': [
            'MISE EN DEMEURE',
            'Rappel des faits',
            'Obligations non respectées',
            'Délai accordé',
            'Conséquences du défaut',
            'Réserves'
        ],
        'style': 'persuasif'
    },
    'note_synthese': {
        'name': 'Note de synthèse',
        'structure': [
            'SYNTHÈSE EXÉCUTIVE',
            'I. CONTEXTE',
            'II. ANALYSE',
            'III. RECOMMANDATIONS',
            'IV. PLAN D\'ACTION'
        ],
        'style': 'synthétique'
    }
}

# ========================= IMPORTS =========================

try:
    # Import des managers
    from managers.azure_blob_manager import AzureBlobManager
    from managers.azure_search_manager import AzureSearchManager
    from managers.multi_llm_manager import MultiLLMManager
    from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
    from managers.company_info_manager import get_company_info_manager
    from managers.style_analyzer import StyleAnalyzer
    
    # Import des modèles
    from models.dataclasses import (
        Document, 
        PieceSelectionnee, 
        AnalyseJuridique,
        InfractionIdentifiee,
        PhaseProcedure,
        StatutProcedural,
        create_partie_from_name_with_lookup,
        format_partie_designation_by_phase,
        format_piece_with_source_and_footnote,
        InformationEntreprise,
        SourceEntreprise,
        StylePattern,
        StyleLearningResult,
        Partie,
        TypePartie
    )
    
    # Import de la configuration
    from config.app_config import (
        InfractionAffaires,
        ANALYSIS_PROMPTS_AFFAIRES,
        ANALYSIS_PROMPTS_INFRACTIONS,
        LLMProvider,
        SearchMode,
        app_config,
        api_config
    )
    
    # Import des services
    from services.universal_search_service import UniversalSearchService
    
except ImportError as e:
    st.error(f"⚠️ Import manquant : {e}")

# ========================= CLASSE PRINCIPALE =========================

class UniversalSearchInterface:
    """Interface de recherche universelle optimisée"""
    
    def __init__(self):
        """Initialisation de l'interface"""
        self.service = UniversalSearchService()
        self.company_manager = get_company_info_manager()
        self.style_analyzer = StyleAnalyzer()
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
        
        # Analyser la requête
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
    
    def _analyze_query_enhanced(self, query: str) -> Dict[str, Any]:
        """Analyse améliorée de la requête"""
        
        analysis = {
            'original_query': query,
            'query_lower': query.lower(),
            'reference': None,
            'subject_matter': None,
            'document_type': None,
            'action': None,
            'phase_procedurale': self._detect_procedural_phase(query),
            'parties': self._extract_parties(query),
            'infractions': self._extract_infractions(query),
            'style_request': self._detect_style_request(query)
        }
        
        # Extraire la référence @
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            analysis['reference'] = ref_match.group(1)
        
        # Détecter le type de document
        doc_types = {
            'conclusions': 'conclusions',
            'plainte': 'plainte',
            'courrier': 'courrier',
            'assignation': 'assignation',
            'mise en demeure': 'mise_en_demeure'
        }
        
        for keyword, doc_type in doc_types.items():
            if keyword in analysis['query_lower']:
                analysis['document_type'] = doc_type
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
            if keyword in analysis['query_lower']:
                analysis['action'] = action
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
            if all(kw in analysis['query_lower'] for kw in keywords):
                analysis['subject_matter'] = subject
                break
        
        return analysis
    
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
    
    def _get_query_processor(self, analysis: Dict[str, Any]):
        """Retourne le processeur approprié pour la requête"""
        
        processors = {
            'redaction': self._process_redaction_request,
            'analysis': self._process_analysis_request,
            'synthesis': self._process_synthesis_request,
            'import': self._process_import_request,
            'export': self._process_export_request,
            'comparison': self._process_comparison_request
        }
        
        # Détection prioritaire par action
        if analysis.get('action'):
            return processors.get(analysis['action'])
        
        # Détection par mots-clés
        query_lower = analysis['query_lower']
        
        if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer', 'plainte']):
            return self._process_redaction_request
        elif any(word in query_lower for word in ['analyser', 'analyse', 'étudier']):
            return self._process_analysis_request
        elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
            return self._process_synthesis_request
        
        return None
    
    async def _process_redaction_request(self, query: str, analysis: Dict[str, Any]):
        """Traite une demande de rédaction avec enrichissement"""
        
        st.info("📝 Détection d'une demande de rédaction...")
        
        # Cas spécifique : plainte
        if 'plainte' in analysis['query_lower']:
            return await self._generate_plainte_enriched(query, analysis)
        
        # Autres types de rédaction
        doc_type = analysis.get('document_type', 'document')
        
        # Enrichir les parties si nécessaire
        if analysis['parties']['demandeurs'] or analysis['parties']['defendeurs']:
            enriched_parties = await self._enrich_parties(analysis['parties'], analysis['phase_procedurale'])
            analysis['parties_enrichies'] = enriched_parties
        
        # Générer le document
        result = await self._generate_document(doc_type, query, analysis)
        
        # Appliquer le style si demandé
        if analysis.get('style_request'):
            result['document'] = await self._apply_style(result['document'], analysis['style_request'])
        
        # Adapter la terminologie selon la phase
        result['document'] = self._adapt_terminology_by_phase(result['document'], analysis['phase_procedurale'])
        
        # Stocker le résultat
        st.session_state.redaction_result = result
        return result
    
    async def _enrich_parties(self, parties_dict: Dict[str, List[str]], phase: PhaseProcedure) -> Dict[str, List[Partie]]:
        """Enrichit les parties avec les informations d'entreprise"""
        
        enriched = {'demandeurs': [], 'defendeurs': []}
        
        with st.spinner("🔍 Recherche des informations légales des entreprises..."):
            # Enrichir les demandeurs
            for nom in parties_dict.get('demandeurs', []):
                partie = Partie(
                    id=f"partie_{nom.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    nom=nom,
                    type_partie=TypePartie.DEMANDEUR,
                    type_personne="morale",
                    phase_procedure=phase
                )
                
                # Enrichir avec les infos entreprise
                if self.company_manager:
                    info = await self.company_manager.get_company_info(nom)
                    if info:
                        partie.info_entreprise = info
                
                enriched['demandeurs'].append(partie)
            
            # Enrichir les défendeurs
            for nom in parties_dict.get('defendeurs', []):
                is_physique = nom.startswith(('M.', 'Mme', 'Monsieur', 'Madame'))
                
                if phase in [PhaseProcedure.ENQUETE_PRELIMINAIRE, PhaseProcedure.ENQUETE_FLAGRANCE]:
                    type_partie = TypePartie.MIS_EN_CAUSE
                else:
                    type_partie = TypePartie.DEFENDEUR
                
                partie = Partie(
                    id=f"partie_{nom.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    nom=nom,
                    type_partie=type_partie,
                    type_personne="physique" if is_physique else "morale",
                    phase_procedure=phase
                )
                
                # Enrichir si c'est une entreprise
                if not is_physique and self.company_manager:
                    info = await self.company_manager.get_company_info(nom)
                    if info:
                        partie.info_entreprise = info
                
                enriched['defendeurs'].append(partie)
        
        return enriched
    
    def _adapt_terminology_by_phase(self, text: str, phase: PhaseProcedure) -> str:
        """Adapte la terminologie selon la phase procédurale"""
        
        replacements = {
            PhaseProcedure.ENQUETE_PRELIMINAIRE: {
                'mis en examen': 'mis en cause',
                'prévenu': 'suspect',
                'témoin assisté': 'témoin',
                'le prévenu': 'le mis en cause',
                'les prévenus': 'les mis en cause',
                'l\'accusé': 'le suspect',
                'les accusés': 'les suspects'
            },
            PhaseProcedure.INSTRUCTION: {
                'prévenu': 'mis en examen',
                'suspect': 'mis en examen',
                'mis en cause': 'mis en examen',
                'le prévenu': 'le mis en examen',
                'les prévenus': 'les mis en examen',
                'l\'accusé': 'le mis en examen',
                'les accusés': 'les mis en examen'
            },
            PhaseProcedure.JUGEMENT: {
                'mis en examen': 'prévenu',
                'mis en cause': 'prévenu',
                'suspect': 'prévenu',
                'le mis en examen': 'le prévenu',
                'les mis en examen': 'les prévenus',
                'l\'accusé': 'le prévenu',
                'les accusés': 'les prévenus'
            }
        }
        
        if phase in replacements:
            for old_term, new_term in replacements[phase].items():
                # Remplacer avec sensibilité à la casse
                text = re.sub(rf'\b{old_term}\b', new_term, text, flags=re.IGNORECASE)
                # Gérer les majuscules en début de phrase
                text = re.sub(rf'\b{old_term.capitalize()}\b', new_term.capitalize(), text)
                text = re.sub(rf'\b{old_term.upper()}\b', new_term.upper(), text)
        
        return text
    
    async def _apply_style(self, document: str, style_request: str) -> str:
        """Applique un style au document"""
        
        if style_request == 'learned' and self.style_analyzer.learned_styles:
            # Prendre le style le plus récent
            style_name = list(self.style_analyzer.learned_styles.keys())[-1]
            return self.style_analyzer.apply_learned_style(document, self.style_analyzer.learned_styles[style_name])
        elif style_request in REDACTION_STYLES:
            # Appliquer un style prédéfini
            return self._apply_predefined_style(document, style_request)
        
        return document
    
    def _apply_predefined_style(self, document: str, style_id: str) -> str:
        """Applique un style prédéfini au document"""
        
        style = REDACTION_STYLES.get(style_id, {})
        
        # Application basique du style (à enrichir selon les besoins)
        if style_id == 'formel':
            # Rendre plus formel
            document = document.replace('vous', 'Vous')
            document = document.replace('je', 'Je')
        elif style_id == 'synthétique':
            # Rendre plus concis (exemple basique)
            document = re.sub(r'\s+', ' ', document)
        
        return document
    
    async def _generate_plainte_enriched(self, query: str, analysis: Dict[str, Any]):
        """Génère une plainte avec enrichissement complet"""
        
        # Déterminer le type de plainte
        is_partie_civile = any(term in analysis['query_lower'] for term in [
            'partie civile', 'constitution de partie civile', 'cpc', 
            'doyen', 'juge d\'instruction', 'instruction'
        ])
        
        type_plainte = 'plainte_avec_cpc' if is_partie_civile else 'plainte_simple'
        
        # Enrichir les parties
        enriched_parties = await self._enrich_parties(analysis['parties'], analysis['phase_procedurale'])
        
        # Afficher le résumé
        self._display_plainte_summary(enriched_parties, analysis['infractions'], type_plainte)
        
        # Options supplémentaires
        options = self._get_plainte_options()
        
        # Générer la plainte
        if st.button("🚀 Générer la plainte", type="primary", key="generate_plainte_btn"):
            return await self._generate_plainte_document(
                query, 
                enriched_parties, 
                analysis['infractions'],
                type_plainte,
                options
            )
        
        return None
    
    def _display_plainte_summary(self, parties: Dict[str, List[Partie]], infractions: List[str], type_plainte: str):
        """Affiche le résumé de la plainte à générer"""
        
        st.markdown("### 📋 Résumé de l'analyse")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏢 Demandeurs (victimes) :**")
            if parties['demandeurs']:
                for p in parties['demandeurs']:
                    designation = p.get_designation_complete()
                    st.write(f"• {designation}")
                    if p.info_entreprise:
                        st.caption(f"  SIREN: {p.info_entreprise.siren}")
            else:
                st.warning("❌ Aucun demandeur identifié")
        
        with col2:
            st.markdown("**⚖️ Défendeurs (mis en cause) :**")
            if parties['defendeurs']:
                for p in parties['defendeurs']:
                    designation = format_partie_designation_by_phase(p)
                    st.write(f"• {designation}")
                    if p.info_entreprise:
                        st.caption(f"  SIREN: {p.info_entreprise.siren}")
            else:
                st.warning("❌ Aucun défendeur identifié")
        
        with col3:
            st.markdown("**🎯 Infractions :**")
            if infractions:
                for inf in infractions[:3]:
                    st.write(f"• {inf}")
                if len(infractions) > 3:
                    st.write(f"• + {len(infractions) - 3} autres")
            else:
                st.info("📌 Infractions standards")
    
    def _get_plainte_options(self) -> Dict[str, Any]:
        """Récupère les options de génération de la plainte"""
        
        with st.expander("⚙️ Options de la plainte", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                include_chronologie = st.checkbox("Inclure chronologie détaillée", value=True)
                include_prejudices = st.checkbox("Détailler les préjudices", value=True)
                include_jurisprudence = st.checkbox("Citer jurisprudences", value=True)
            
            with col2:
                style = st.selectbox(
                    "Style de rédaction",
                    options=list(REDACTION_STYLES.keys()),
                    format_func=lambda x: REDACTION_STYLES[x]['name']
                )
                
                use_learned_style = st.checkbox("Utiliser mon style habituel", value=False)
        
        return {
            'chronologie': include_chronologie,
            'prejudices': include_prejudices,
            'jurisprudence': include_jurisprudence,
            'style': 'learned' if use_learned_style else style
        }
    
    async def _generate_plainte_document(self, query: str, parties: Dict[str, List[Partie]], 
                                       infractions: List[str], type_plainte: str, 
                                       options: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le document de plainte complet"""
        
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            st.error("❌ Aucune IA n'est configurée")
            return None
        
        # Construire les désignations juridiques complètes
        designations = {
            'demandeurs': [],
            'defendeurs': []
        }
        
        for role, parties_list in parties.items():
            for partie in parties_list:
                if partie.info_entreprise:
                    designation = self.company_manager.format_for_legal_document(
                        partie.info_entreprise,
                        style='complet'
                    )
                else:
                    designation = partie.get_designation_complete()
                
                designations[role].append(designation)
        
        # Construire le prompt enrichi
        prompt = self._build_plainte_prompt(
            query, designations, infractions, type_plainte, options
        )
        
        # Sélectionner le meilleur provider
        provider = self._select_best_provider(llm_manager.get_available_providers())
        
        # Générer la plainte
        with st.spinner(f"⚖️ Génération de la plainte via {provider}..."):
            response = llm_manager.query_single_llm(
                provider,
                prompt,
                "Tu es un avocat pénaliste expert avec 25 ans d'expérience.",
                temperature=0.3,
                max_tokens=8000
            )
        
        if response['success']:
            document = response['response']
            
            # Appliquer le style si demandé
            if options.get('style'):
                document = await self._apply_style(document, options['style'])
            
            # Adapter la terminologie
            phase = parties['demandeurs'][0].phase_procedure if parties['demandeurs'] else PhaseProcedure.ENQUETE_PRELIMINAIRE
            document = self._adapt_terminology_by_phase(document, phase)
            
            # Créer le résultat
            result = {
                'type': type_plainte,
                'document': document,
                'provider': provider,
                'timestamp': datetime.now(),
                'metadata': {
                    'parties': parties,
                    'designations': designations,
                    'infractions': infractions,
                    'options': options,
                    'phase_procedurale': phase.value,
                    'requete_originale': query,
                    'generation_time': response.get('elapsed_time', 0),
                    'word_count': len(document.split()),
                    'enriched_companies': sum(1 for p_list in parties.values() for p in p_list if p.info_entreprise)
                }
            }
            
            st.session_state.redaction_result = result
            st.success("✅ Plainte générée avec succès !")
            
            return result
        else:
            st.error(f"❌ Erreur : {response.get('error', 'Erreur inconnue')}")
            return None
    
    def _build_plainte_prompt(self, query: str, designations: Dict[str, List[str]], 
                            infractions: List[str], type_plainte: str, 
                            options: Dict[str, Any]) -> str:
        """Construit le prompt pour générer la plainte"""
        
        # Prompt de base selon le type
        if type_plainte == 'plainte_avec_cpc':
            base_prompt = self._get_cpc_prompt_template()
        else:
            base_prompt = self._get_simple_plainte_prompt_template()
        
        # Remplacer les variables
        prompt = base_prompt.format(
            query=query,
            demandeurs='\n'.join(f"   - {d}" for d in designations['demandeurs']),
            defendeurs='\n'.join(f"   - {d}" for d in designations['defendeurs']),
            infractions='\n'.join(f"- {i}" for i in infractions),
            include_chronologie="OUI" if options.get('chronologie') else "NON",
            include_prejudices="DÉTAILLÉ" if options.get('prejudices') else "SIMPLE",
            include_jurisprudence="OUI" if options.get('jurisprudence') else "NON"
        )
        
        return prompt
    
    def _get_cpc_prompt_template(self) -> str:
        """Template pour plainte avec constitution de partie civile"""
        return """Tu es un avocat pénaliste expert. Rédige une plainte avec constitution de partie civile EXHAUSTIVE.

CONTEXTE : {query}

PARTIES :
DEMANDEURS (avec désignations juridiques complètes) :
{demandeurs}

DÉFENDEURS :
{defendeurs}

INFRACTIONS À EXAMINER :
{infractions}

INSTRUCTIONS :
- Inclure chronologie : {include_chronologie}
- Détailler préjudices : {include_prejudices}
- Citer jurisprudences : {include_jurisprudence}

Rédige une plainte complète (minimum 5000 mots) avec :
1. EN-TÊTE FORMEL au Doyen des Juges d'Instruction
2. IDENTIFICATION COMPLÈTE DES PARTIES (utiliser les désignations fournies)
3. EXPOSÉ EXHAUSTIF DES FAITS (chronologique et détaillé)
4. QUALIFICATION JURIDIQUE APPROFONDIE
5. ÉVALUATION DÉTAILLÉE DES PRÉJUDICES
6. CONSTITUTION DE PARTIE CIVILE
7. DEMANDES D'ACTES D'INSTRUCTION
8. PAR CES MOTIFS
9. BORDEREAU DE PIÈCES"""
    
    def _get_simple_plainte_prompt_template(self) -> str:
        """Template pour plainte simple"""
        return """Tu es un avocat pénaliste expert. Rédige une plainte simple mais complète.

CONTEXTE : {query}

PARTIES :
PLAIGNANTS :
{demandeurs}

MIS EN CAUSE :
{defendeurs}

INFRACTIONS :
{infractions}

OPTIONS :
- Chronologie : {include_chronologie}
- Préjudices : {include_prejudices}
- Jurisprudences : {include_jurisprudence}

Rédige une plainte complète (minimum 3000 mots) avec :
1. EN-TÊTE au Procureur de la République
2. IDENTITÉ DU/DES PLAIGNANT(S) (utiliser les désignations fournies)
3. EXPOSÉ DES FAITS
4. QUALIFICATION JURIDIQUE
5. PRÉJUDICE
6. DEMANDES
7. PIÈCES JOINTES

Style : juridique, factuel et professionnel."""
    
    def _select_best_provider(self, available_providers: List[str]) -> str:
        """Sélectionne le meilleur provider disponible"""
        
        preferred_order = ['anthropic', 'openai', 'google', 'mistral', 'groq']
        
        for provider in preferred_order:
            if provider in available_providers:
                return provider
        
        return available_providers[0] if available_providers else None
    
    async def _process_analysis_request(self, query: str, analysis: Dict[str, Any]):
        """Traite une demande d'analyse"""
        
        st.info("🤖 Détection d'une demande d'analyse...")
        
        # Collecter les documents pertinents
        documents = await self._collect_relevant_documents(analysis)
        
        if not documents:
            st.warning("⚠️ Aucun document trouvé pour l'analyse")
            return None
        
        # Configuration de l'analyse
        config = self._get_analysis_config()
        
        # Lancer l'analyse
        if st.button("🚀 Lancer l'analyse", type="primary", key="launch_analysis"):
            with st.spinner("🤖 Analyse en cours..."):
                result = await self._perform_analysis(documents, query, config)
                
                # Stocker les résultats
                st.session_state.ai_analysis_results = result
                return result
        
        return None
    
    def _get_analysis_config(self) -> Dict[str, Any]:
        """Récupère la configuration d'analyse"""
        
        st.markdown("### ⚙️ Configuration de l'analyse")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_type = st.selectbox(
                "Type d'analyse",
                ["Analyse générale", "Risques juridiques", "Conformité", "Stratégie", "Infractions"],
                key="analysis_type_select"
            )
            
            client_nom = st.text_input(
                "Nom du client",
                placeholder="Personne physique ou morale",
                key="client_nom_analyse"
            )
        
        with col2:
            infraction = None
            if analysis_type == "Infractions":
                infraction = st.text_input(
                    "Type d'infraction",
                    placeholder="Ex: Abus de biens sociaux, corruption...",
                    key="infraction_input"
                )
        
        return {
            'type': analysis_type,
            'client': client_nom,
            'infraction': infraction
        }
    
    async def _perform_analysis(self, documents: List[Document], query: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Effectue l'analyse selon la configuration"""
        
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            return {'error': 'Aucune IA disponible'}
        
        # Construire le prompt selon le type
        prompt = self._build_analysis_prompt(documents, query, config)
        
        # Sélectionner le provider
        provider = self._select_best_provider(llm_manager.get_available_providers())
        
        # Effectuer l'analyse
        response = llm_manager.query_single_llm(
            provider,
            prompt,
            "Tu es un expert en analyse juridique.",
            temperature=0.2,
            max_tokens=4000
        )
        
        if response['success']:
            return {
                'type': config['type'].lower().replace(' ', '_'),
                'content': response['response'],
                'document_count': len(documents),
                'timestamp': datetime.now(),
                'query': query,
                'config': config
            }
        else:
            return {'error': response.get('error', 'Erreur inconnue')}
    
    def _build_analysis_prompt(self, documents: List[Document], query: str, config: Dict[str, Any]) -> str:
        """Construit le prompt d'analyse"""
        
        # Contexte des documents
        doc_context = "\n".join([
            f"- {doc.title}: {doc.content[:500]}..."
            for doc in documents[:10]
        ])
        
        base_prompt = f"""Analyse ces documents pour répondre à la question.
Client: {config.get('client', 'Non spécifié')}
DOCUMENTS:
{doc_context}
QUESTION: {query}
"""
        
        # Adapter selon le type
        if config['type'] == 'Risques juridiques':
            base_prompt += """
Identifie et évalue:
1. RISQUES PÉNAUX
2. RISQUES CIVILS
3. RISQUES RÉPUTATIONNELS
4. RECOMMANDATIONS"""
        elif config['type'] == 'Infractions':
            base_prompt += f"""
Infraction suspectée: {config.get('infraction', 'À déterminer')}
Identifie:
1. INFRACTIONS CARACTÉRISÉES
2. RESPONSABILITÉS
3. SANCTIONS ENCOURUES
4. ÉLÉMENTS DE PREUVE
5. STRATÉGIE DE DÉFENSE"""
        
        return base_prompt
    
    async def _collect_relevant_documents(self, analysis: Dict[str, Any]) -> List[Document]:
        """Collecte les documents pertinents"""
        
        documents = []
        
        # Documents locaux
        for doc_id, doc in st.session_state.get('azure_documents', {}).items():
            documents.append(doc)
        
        # Filtrer par référence si présente
        if analysis.get('reference'):
            ref_lower = analysis['reference'].lower()
            documents = [
                d for d in documents 
                if ref_lower in d.title.lower() or ref_lower in d.source.lower()
            ]
        
        return documents
    
    async def _process_search_request(self, query: str, analysis: Dict[str, Any]):
        """Traite une demande de recherche simple"""
        
        st.info("🔍 Recherche en cours...")
        
        # Effectuer la recherche
        results = await self._perform_search(query, analysis)
        
        # Stocker les résultats
        st.session_state.search_results = results
        
        if not results:
            st.warning("⚠️ Aucun résultat trouvé")
        else:
            st.success(f"✅ {len(results)} résultats trouvés")
        
        return results
    
    async def _perform_search(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Effectue la recherche"""
        
        results = []
        
        # Recherche locale
        query_words = query.lower().split()
        
        for doc_id, doc in st.session_state.get('azure_documents', {}).items():
            score = 0
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()
            
            for word in query_words:
                if word in title_lower:
                    score += 2
                if word in content_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    'id': doc_id,
                    'title': doc.title,
                    'content': doc.content,
                    'source': doc.source,
                    'score': score / len(query_words)
                })
        
        # Recherche Azure si disponible
        try:
            search_manager = st.session_state.get('azure_search_manager')
            if search_manager and hasattr(search_manager, 'search'):
                azure_results = await search_manager.search(query)
                results.extend(azure_results)
        except:
            pass
        
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:50]
    
    async def _process_synthesis_request(self, query: str, analysis: Dict[str, Any]):
        """Traite une demande de synthèse"""
        
        st.info("📝 Préparation de la synthèse...")
        
        # Déterminer la source
        pieces = st.session_state.get('selected_pieces', [])
        
        if not pieces:
            # Essayer de collecter depuis la référence
            if analysis.get('reference'):
                docs = await self._perform_search(f"@{analysis['reference']}", analysis)
                pieces = [
                    PieceSelectionnee(
                        numero=i + 1,
                        titre=doc.get('title', 'Sans titre'),
                        description=doc.get('content', '')[:200] + '...' if doc.get('content') else '',
                        categorie=self._determine_document_category(doc),
                        source=doc.get('source', '')
                    )
                    for i, doc in enumerate(docs[:20])
                ]
        
        if pieces:
            return await self._synthesize_pieces(pieces)
        else:
            st.warning("⚠️ Aucun contenu à synthétiser")
            return None
    
    async def _synthesize_pieces(self, pieces: List[PieceSelectionnee]) -> Dict[str, Any]:
        """Synthétise les pièces sélectionnées"""
        
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            return {'error': 'Aucune IA disponible'}
        
        # Construire le contexte
        context = "PIÈCES À SYNTHÉTISER:\n\n"
        for piece in pieces[:20]:
            context += f"Pièce {piece.numero}: {piece.titre}\n"
            context += f"Catégorie: {piece.categorie}\n"
            if piece.description:
                context += f"Description: {piece.description}\n"
            context += "\n"
        
        # Prompt
        synthesis_prompt = f"""{context}
Crée une synthèse structurée de ces pièces.
La synthèse doit inclure:
1. Vue d'ensemble des pièces
2. Points clés par catégorie
3. Chronologie si applicable
4. Points d'attention juridiques
5. Recommandations"""
        
        provider = self._select_best_provider(llm_manager.get_available_providers())
        response = llm_manager.query_single_llm(
            provider,
            synthesis_prompt,
            "Tu es un expert en analyse de documents juridiques."
        )
        
        if response['success']:
            result = {
                'content': response['response'],
                'piece_count': len(pieces),
                'categories': list(set(p.categorie for p in pieces)),
                'timestamp': datetime.now()
            }
            st.session_state.synthesis_result = result
            return result
        else:
            return {'error': 'Échec de la synthèse'}
    
    def _determine_document_category(self, doc: Dict[str, Any]) -> str:
        """Détermine la catégorie d'un document"""
        
        title_lower = doc.get('title', '').lower()
        content_lower = doc.get('content', '')[:500].lower()
        
        category_patterns = {
            'Procédure': ['plainte', 'procès-verbal', 'audition'],
            'Expertise': ['expertise', 'expert', 'rapport technique'],
            'Comptabilité': ['bilan', 'compte', 'facture'],
            'Contrats': ['contrat', 'convention', 'accord'],
            'Correspondance': ['courrier', 'email', 'lettre']
        }
        
        for category, keywords in category_patterns.items():
            if any(kw in title_lower or kw in content_lower for kw in keywords):
                return category
        
        return 'Autres'

# ========================= FONCTIONS PRINCIPALES =========================

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    # Initialiser l'interface
    if 'search_interface' not in st.session_state:
        st.session_state.search_interface = UniversalSearchInterface()
    
    interface = st.session_state.search_interface
    
    st.markdown("## 🔍 Recherche Universelle")
    
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
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Nouvelle rédaction", key="quick_redaction"):
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
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            # Utiliser asyncio pour exécuter la requête asynchrone
            asyncio.run(interface.process_universal_query(query))
    
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
            show_work_statistics()
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            share_current_work()

def show_unified_results():
    """Affiche tous les types de résultats"""
    
    has_results = False
    
    # RÉSULTATS DE RÉDACTION
    if st.session_state.get('redaction_result'):
        show_redaction_results()
        has_results = True
    
    # RÉSULTATS D'ANALYSE IA
    elif st.session_state.get('ai_analysis_results'):
        show_ai_analysis_results()
        has_results = True
    
    # RÉSULTATS DE RECHERCHE
    elif st.session_state.get('search_results'):
        show_search_results()
        has_results = True
    
    # RÉSULTATS DE SYNTHÈSE
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        has_results = True
    
    # Message si aucun résultat
    if not has_results:
        st.info("💡 Utilisez la barre de recherche universelle pour commencer")

def show_redaction_results():
    """Affiche les résultats de rédaction"""
    result = st.session_state.redaction_result
    
    st.markdown("### 📝 Document juridique généré")
    
    # Métadonnées enrichies
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        doc_icons = {
            'conclusions': '⚖️ Conclusions',
            'plainte_simple': '📋 Plainte simple',
            'plainte_avec_cpc': '⚖️ Plainte avec CPC',
            'courrier': '✉️ Courrier',
            'assignation': '📜 Assignation'
        }
        st.metric("Type", doc_icons.get(result['type'], '📄 Document'))
    
    with col2:
        st.metric("Généré par", result.get('provider', 'IA'))
        
    with col3:
        metadata = result.get('metadata', {})
        enriched = metadata.get('enriched_companies', 0)
        if enriched > 0:
            st.metric("Entreprises enrichies", enriched)
        else:
            word_count = len(result['document'].split())
            st.metric("Mots", f"{word_count:,}")
    
    with col4:
        phase = metadata.get('phase_procedurale', 'enquete_preliminaire')
        phase_display = {
            'enquete_preliminaire': 'Enquête',
            'instruction': 'Instruction',
            'jugement': 'Jugement',
            'appel': 'Appel'
        }
        st.metric("Phase", phase_display.get(phase, phase))
    
    # Zone d'édition principale
    st.markdown("#### 📄 Contenu du document")
    
    edited_content = st.text_area(
        "Vous pouvez éditer le document",
        value=result['document'],
        height=600,
        key="edit_redaction_main"
    )
    
    # Afficher les parties enrichies si disponibles
    if 'metadata' in result and 'designations' in result['metadata']:
        with st.expander("📋 Parties avec informations juridiques complètes", expanded=False):
            designations = result['metadata']['designations']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Demandeurs :**")
                for d in designations.get('demandeurs', []):
                    st.text(d)
            
            with col2:
                st.markdown("**Défendeurs :**")
                for d in designations.get('defendeurs', []):
                    st.text(d)
    
    # Barre d'outils enrichie
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🔄 Régénérer", key="regenerate_main"):
            st.session_state.process_query = True
            st.rerun()
    
    with col2:
        if st.button("📊 Statistiques", key="document_stats"):
            show_document_statistics(edited_content)
    
    with col3:
        # Export Word
        st.download_button(
            "📄 Word",
            edited_content.encode('utf-8'),
            f"{result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    with col4:
        # Export texte
        st.download_button(
            "📝 Texte",
            edited_content.encode('utf-8'),
            f"{result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col5:
        if st.button("📧 Envoyer", key="prepare_email_main"):
            st.session_state.pending_email = {
                'content': edited_content,
                'type': result['type']
            }

def show_ai_analysis_results():
    """Affiche les résultats d'analyse IA"""
    results = st.session_state.ai_analysis_results
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    analysis_titles = {
        'risk_analysis': '⚠️ Analyse des risques',
        'compliance': '✅ Analyse de conformité',
        'strategy': '🎯 Analyse stratégique',
        'general_analysis': '🤖 Analyse générale',
        'infractions': '🎯 Analyse infractions économiques'
    }
    
    st.markdown(f"### {analysis_titles.get(results.get('type'), '🤖 Analyse IA')}")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents analysés", results.get('document_count', 0))
    with col2:
        st.metric("Type", results.get('type', 'general').replace('_', ' ').title())
    with col3:
        st.metric("Généré le", results.get('timestamp', datetime.now()).strftime('%H:%M'))
    
    # Contenu de l'analyse
    st.markdown("#### 📊 Résultats de l'analyse")
    
    analysis_content = st.text_area(
        "Analyse détaillée",
        value=results.get('content', ''),
        height=600,
        key="ai_analysis_content"
    )
    
    # Vérification des jurisprudences
    if st.checkbox("🔍 Vérifier les jurisprudences citées", key="verify_juris_check"):
        verify_jurisprudences_in_analysis(analysis_content)
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "💾 Télécharger",
            analysis_content.encode('utf-8'),
            f"analyse_{results.get('type', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("🔄 Approfondir", key="deepen_analysis"):
            st.session_state.pending_deepen_analysis = True

def show_search_results():
    """Affiche les résultats de recherche"""
    results = st.session_state.search_results
    
    st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
    
    if not results:
        st.info("Aucun résultat trouvé")
        return
    
    # Options d'affichage
    col1, col2 = st.columns(2)
    
    with col1:
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Titre", "Date", "Source"],
            key="sort_search_results"
        )
    
    with col2:
        view_mode = st.radio(
            "Affichage",
            ["Compact", "Détaillé"],
            key="view_mode_search",
            horizontal=True
        )
    
    # Afficher les résultats
    for i, result in enumerate(results[:20], 1):
        with st.container():
            if view_mode == "Compact":
                st.markdown(f"**{i}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
            else:
                st.markdown(f"**{i}. {result.get('title', 'Sans titre')}**")
                st.caption(f"Source: {result.get('source', 'N/A')} | Score: {result.get('score', 0):.0%}")
                
                # Extrait
                content = result.get('content', '')
                if content:
                    st.text_area(
                        "Extrait",
                        value=content[:500] + '...' if len(content) > 500 else content,
                        height=150,
                        key=f"extract_{i}",
                        disabled=True
                    )
            
            st.divider()

def show_synthesis_results():
    """Affiche les résultats de synthèse"""
    result = st.session_state.synthesis_result
    
    if 'error' in result:
        st.error(f"❌ {result['error']}")
        return
    
    st.markdown("### 📝 Synthèse des documents")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pièces analysées", result.get('piece_count', 0))
    with col2:
        st.metric("Catégories", len(result.get('categories', [])))
    with col3:
        st.metric("Généré le", result.get('timestamp', datetime.now()).strftime('%H:%M'))
    
    # Contenu
    synthesis_content = st.text_area(
        "Contenu de la synthèse",
        value=result.get('content', ''),
        height=600,
        key="synthesis_content_display"
    )
    
    # Actions
    if st.download_button(
        "💾 Télécharger",
        synthesis_content.encode('utf-8'),
        f"synthese_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain"
    ):
        st.success("✅ Synthèse téléchargée")

def verify_jurisprudences_in_analysis(content: str):
    """Vérifie les jurisprudences citées dans l'analyse"""
    st.markdown("### 🔍 Vérification des jurisprudences citées")
    
    try:
        verifier = JurisprudenceVerifier()
        verification_results = display_jurisprudence_verification(content, verifier)
        
        if verification_results:
            st.session_state.jurisprudence_verification = verification_results
            
            verified_count = sum(1 for r in verification_results if r.status == 'verified')
            total_count = len(verification_results)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Jurisprudences vérifiées", f"{verified_count}/{total_count}")
            
            with col2:
                confidence = (verified_count / total_count * 100) if total_count > 0 else 0
                st.metric("Fiabilité des sources", f"{confidence:.0f}%")
        
        return verification_results
    except:
        st.warning("⚠️ Vérificateur de jurisprudences non disponible")
        return []

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'current_analysis',
        'redaction_result', 'ai_analysis_results', 'search_results',
        'synthesis_result', 'selected_pieces', 'import_files'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

def save_current_work():
    """Sauvegarde le travail actuel"""
    work_data = {
        'timestamp': datetime.now().isoformat(),
        'query': st.session_state.get('universal_query', ''),
        'results': {}
    }
    
    result_keys = [
        'redaction_result', 'ai_analysis_results',
        'search_results', 'synthesis_result'
    ]
    
    for key in result_keys:
        if key in st.session_state:
            work_data['results'][key] = st.session_state[key]
    
    import json
    json_str = json.dumps(work_data, indent=2, ensure_ascii=False, default=str)
    
    st.download_button(
        "💾 Télécharger la sauvegarde",
        json_str,
        f"sauvegarde_travail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="download_work_save"
    )

def show_work_statistics():
    """Affiche les statistiques du travail en cours"""
    st.info("📊 Statistiques du travail en cours")
    
    stats = {
        'Documents': len(st.session_state.get('azure_documents', {})),
        'Pièces sélectionnées': len(st.session_state.get('selected_pieces', [])),
        'Analyses': 1 if st.session_state.get('ai_analysis_results') else 0,
        'Rédactions': 1 if st.session_state.get('redaction_result') else 0
    }
    
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label, value)

def share_current_work():
    """Partage le travail actuel"""
    st.info("🔗 Fonctionnalité de partage")
    save_current_work()

def show_document_statistics(content: str):
    """Affiche les statistiques d'un document"""
    
    words = content.split()
    sentences = content.split('.')
    paragraphs = content.split('\n\n')
    law_refs = len(re.findall(r'article\s+[LR]?\s*\d+', content, re.IGNORECASE))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mots", f"{len(words):,}")
        st.metric("Phrases", f"{len(sentences):,}")
    
    with col2:
        st.metric("Paragraphes", len(paragraphs))
        st.metric("Mots/phrase", f"{len(words) / max(len(sentences), 1):.1f}")
    
    with col3:
        st.metric("Articles cités", law_refs)
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        st.metric("Longueur moy.", f"{avg_word_length:.1f} car/mot")

# ========================= FIN DU MODULE =========================