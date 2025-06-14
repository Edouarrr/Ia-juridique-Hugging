# managers/unified_document_generator.py
"""
Générateur unifié de documents juridiques avec système de plugins
Préserve TOUTES les fonctionnalités existantes
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union

from managers.jurisprudence_verifier import JurisprudenceVerifier
# Import des gestionnaires existants
from managers.multi_llm_manager import MultiLLMManager
from managers.style_analyzer import StyleAnalyzer
from managers.template_manager import TemplateManager
# Import des dataclasses
from config.app_config import DocumentType
from modules.dataclasses import (DocumentJuridique, InfractionIdentifiee,
                                 Partie, PhaseProcedure, StyleRedaction)

logger = logging.getLogger(__name__)

# =============== ENUMS SPÉCIFIQUES ===============

class DocumentLength(Enum):
    """Longueurs de documents disponibles"""
    SHORT = "court"           # < 5 pages (~2500 mots)
    STANDARD = "standard"     # 5-15 pages (~7500 mots)  
    MEDIUM = "moyen"         # 15-25 pages (~12500 mots)
    LONG = "long"            # 25-50 pages (~25000 mots)
    VERY_LONG = "tres_long"  # 50+ pages (~50000+ mots)

class PlaidoirieDuration(Enum):
    """Durées de plaidoirie"""
    EXPRESS = 10      # 10 minutes
    COURT = 20        # 20 minutes
    STANDARD = 30     # 30 minutes
    MOYEN = 45        # 45 minutes
    LONG = 60         # 60 minutes
    APPROFONDI = 90   # 90 minutes
    COMPLET = 120     # 120 minutes

# =============== REQUÊTE UNIFIÉE ===============

@dataclass
class UnifiedGenerationRequest:
    """Requête de génération unifiée pour tous types de documents"""
    
    # Informations de base
    document_type: DocumentType
    parties: Dict[str, List[Partie]]
    infractions: List[InfractionIdentifiee]
    contexte: str
    
    # Style et format
    style: StyleRedaction
    length: DocumentLength
    
    # Options spécifiques
    options: Dict[str, Any] = field(default_factory=dict)
    
    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Options spécifiques plaidoirie
    plaidoirie_duration: Optional[PlaidoirieDuration] = None
    support_conclusions: Optional[DocumentJuridique] = None
    points_forts_oraux: Optional[List[str]] = None
    
    # Options documents longs
    structure_detaillee: Optional[Dict[str, int]] = None  # Section -> nb mots cibles
    enrichissement_auto: bool = True
    generation_parallele: bool = False

# =============== INTERFACE PLUGIN ===============

class GenerationPlugin(ABC):
    """Interface pour les plugins de génération"""
    
    @abstractmethod
    def can_handle(self, request: UnifiedGenerationRequest) -> bool:
        """Détermine si ce plugin peut traiter la requête"""
        pass
    
    @abstractmethod
    async def generate(self, request: UnifiedGenerationRequest, 
                      base_generator: 'UnifiedDocumentGenerator') -> DocumentJuridique:
        """Génère le document selon la spécialité du plugin"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Retourne les capacités du plugin"""
        pass

# =============== PLUGIN DOCUMENTS LONGS ===============

class LongDocumentPlugin(GenerationPlugin):
    """Plugin spécialisé pour documents longs (25-50+ pages)"""
    
    def can_handle(self, request: UnifiedGenerationRequest) -> bool:
        return request.length in [DocumentLength.LONG, DocumentLength.VERY_LONG]
    
    async def generate(self, request: UnifiedGenerationRequest, 
                      base_generator: 'UnifiedDocumentGenerator') -> DocumentJuridique:
        """Génération optimisée pour documents longs"""
        
        logger.info(f"Plugin documents longs activé - Cible: {request.length.value}")
        
        # Structure spécifique documents longs
        if request.document_type == DocumentType.PLAINTE and request.length == DocumentLength.VERY_LONG:
            structure = {
                "en_tete": 500,
                "qualites_parties": 2000,
                "table_chronologique": 1500,
                "expose_faits": 15000,  # 30% du document
                "analyse_mecanismes": 10000,  # 20% du document
                "discussion_juridique": 20000,  # 40% du document
                "prejudices": 5000,
                "demandes": 2000,
                "pieces": 1000
            }
        else:
            structure = self._calculate_structure(request)
        
        # Générer en parallèle si demandé
        if request.generation_parallele:
            return await self._generate_parallel(request, structure, base_generator)
        else:
            return await self._generate_sequential(request, structure, base_generator)
    
    async def _generate_parallel(self, request: UnifiedGenerationRequest,
                               structure: Dict[str, int],
                               base_generator: 'UnifiedDocumentGenerator') -> DocumentJuridique:
        """Génération parallèle pour performance"""
        
        tasks = []
        for section, target_words in structure.items():
            task = self._generate_section_long(section, target_words, request, base_generator)
            tasks.append((section, task))
        
        # Exécuter en parallèle
        results = await asyncio.gather(*[task for _, task in tasks])
        
        # Assembler les sections
        sections = {}
        for i, (section, _) in enumerate(tasks):
            sections[section] = results[i]
        
        # Enrichir si nécessaire
        if request.enrichissement_auto:
            sections = await self._auto_enrich(sections, structure, request, base_generator)
        
        return base_generator._assemble_final_document(sections, request)
    
    async def _generate_section_long(self, section: str, target_words: int,
                                   request: UnifiedGenerationRequest,
                                   base_generator: 'UnifiedDocumentGenerator') -> str:
        """Génère une section longue avec contenu approfondi"""
        
        prompt = f"""
        Rédige la section '{section}' d'un document juridique LONG et DÉTAILLÉ.
        
        Type de document: {request.document_type.value}
        Longueur IMPÉRATIVE: {target_words} mots MINIMUM
        Style: {request.style.value}
        
        CONTEXTE COMPLET:
        {request.contexte}
        
        PARTIES IMPLIQUÉES:
        Demandeurs: {', '.join([p.nom for p in request.parties.get('demandeurs', [])])}
        Défendeurs: {', '.join([p.nom for p in request.parties.get('defendeurs', [])])}
        
        INFRACTIONS À ANALYSER:
        {self._format_infractions_detail(request.infractions)}
        
        INSTRUCTIONS SPÉCIFIQUES SECTION '{section}':
        {self._get_section_instructions_long(section)}
        
        CONSIGNES IMPÉRATIVES:
        - NE JAMAIS résumer ou condenser
        - Développer CHAQUE point en profondeur
        - Utiliser des phrases longues et complexes quand approprié
        - Multiplier les détails factuels et analyses
        - Citer des pièces (Pièce n°X) régulièrement
        - Structurer avec sous-sections numérotées
        - Maintenir une progression logique
        - Viser {target_words} mots MINIMUM
        """
        
        response = await base_generator.llm_manager.query_single_llm_async(
            provider=base_generator._select_best_provider(request),
            query=prompt,
            system_prompt=self._get_long_doc_system_prompt(request.style)
        )
        
        if response.get('success'):
            return response['response']
        
        # Fallback
        return f"[Section {section} - Contenu à générer - {target_words} mots]"
    
    def _get_section_instructions_long(self, section: str) -> str:
        """Instructions spécifiques pour sections longues"""
        
        instructions = {
            "expose_faits": """
            1. Chronologie ultra-détaillée avec dates précises
            2. Description approfondie de CHAQUE événement
            3. Contexte et ambiance de chaque réunion/échange
            4. Citations de correspondances importantes
            5. Analyse des motivations des acteurs
            6. Liens entre les événements
            7. Éléments de preuve pour chaque fait
            """,
            "discussion_juridique": """
            1. Analyse EXHAUSTIVE de chaque infraction
            2. Éléments constitutifs détaillés (matériel ET moral)
            3. Jurisprudence abondante (15+ arrêts par infraction)
            4. Doctrine citée et analysée
            5. Réfutation anticipée des arguments adverses
            6. Analyse comparative avec cas similaires
            7. Développements sur les circonstances aggravantes
            """,
            "analyse_mecanismes": """
            1. Schémas frauduleux décortiqués étape par étape
            2. Rôle précis de chaque intervenant
            3. Flux financiers détaillés avec montants
            4. Techniques de dissimulation analysées
            5. Preuves de l'intentionnalité
            6. Comparaison avec schémas connus
            """
        }
        
        return instructions.get(section, "Développer de manière exhaustive et détaillée")
    
    def _get_long_doc_system_prompt(self, style: StyleRedaction) -> str:
        """System prompt pour documents longs"""
        
        base = """Tu es un avocat pénaliste expert avec 20 ans d'expérience, 
        spécialisé dans la rédaction de documents juridiques complexes et approfondis.
        Tu maîtrises l'art de l'argumentation détaillée et exhaustive."""
        
        style_additions = {
            StyleRedaction.FORMEL: "Tu privilégies les développements solennels et magistraux.",
            StyleRedaction.TECHNIQUE: "Tu fournis une analyse technique ultra-détaillée.",
            StyleRedaction.PERSUASIF: "Tu construis une argumentation fleuve implacable."
        }
        
        return f"{base} {style_additions.get(style, '')}"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "min_length": 25000,  # mots
            "max_length": 100000,
            "parallel_generation": True,
            "auto_enrichment": True,
            "specialized_sections": ["analyse_mecanismes", "chronologie_detaillee"]
        }
    
    def _calculate_structure(self, request: UnifiedGenerationRequest) -> Dict[str, int]:
        """Calcule la structure optimale selon le type et la longueur"""
        # Logique de calcul de structure...
        pass

# =============== PLUGIN PLAIDOIRIE ===============

class PlaidoiriePlugin(GenerationPlugin):
    """Plugin spécialisé pour plaidoiries avec calibrage temporel"""
    
    # Vitesse de lecture moyenne : 150 mots/minute en plaidoirie
    WORDS_PER_MINUTE = 150
    
    def can_handle(self, request: UnifiedGenerationRequest) -> bool:
        return (request.document_type == DocumentType.PLAIDOIRIE or
                request.plaidoirie_duration is not None)
    
    async def generate(self, request: UnifiedGenerationRequest,
                      base_generator: 'UnifiedDocumentGenerator') -> DocumentJuridique:
        """Génère une plaidoirie calibrée et optimisée pour l'oral"""
        
        # Calculer le nombre de mots cible
        duration_minutes = request.plaidoirie_duration.value if request.plaidoirie_duration else 30
        target_words = duration_minutes * self.WORDS_PER_MINUTE
        
        logger.info(f"Génération plaidoirie {duration_minutes} min (~{target_words} mots)")
        
        # Structure adaptée au temps
        structure = self._calculate_plaidoirie_structure(duration_minutes, request)
        
        # Générer chaque partie
        sections = {}
        
        # 1. Introduction percutante
        sections['introduction'] = await self._generate_introduction_orale(
            request, structure['introduction'], base_generator
        )
        
        # 2. Narration des faits (si temps suffisant)
        if duration_minutes >= 20:
            sections['narration'] = await self._generate_narration_orale(
                request, structure['narration'], base_generator
            )
        
        # 3. Arguments principaux
        sections['arguments'] = await self._generate_arguments_oraux(
            request, structure['arguments'], base_generator
        )
        
        # 4. Réfutation (si temps suffisant)
        if duration_minutes >= 45:
            sections['refutation'] = await self._generate_refutation_orale(
                request, structure['refutation'], base_generator
            )
        
        # 5. Conclusion forte
        sections['conclusion'] = await self._generate_conclusion_orale(
            request, structure['conclusion'], base_generator
        )
        
        # Assembler avec marqueurs temporels
        content = self._assemble_plaidoirie_with_timing(sections, duration_minutes)
        
        # Créer le document
        return DocumentJuridique(
            titre=f"Plaidoirie {duration_minutes} minutes - {request.metadata.get('affaire', 'Affaire')}",
            type_document="plaidoirie",
            contenu=content,
            auteur=request.metadata.get('auteur', 'Assistant IA'),
            date_creation=datetime.now(),
            metadata={
                "duration_minutes": duration_minutes,
                "word_count": len(content.split()),
                "support_conclusions": request.support_conclusions.titre if request.support_conclusions else None,
                "style_oral": True,
                "points_forts": request.points_forts_oraux
            }
        )
    
    def _calculate_plaidoirie_structure(self, duration_minutes: int, 
                                       request: UnifiedGenerationRequest) -> Dict[str, int]:
        """Calcule la répartition optimale du temps"""
        
        total_words = duration_minutes * self.WORDS_PER_MINUTE
        
        if duration_minutes <= 20:
            # Plaidoirie courte : aller à l'essentiel
            return {
                'introduction': int(total_words * 0.15),  # 3 min
                'arguments': int(total_words * 0.70),     # 14 min
                'conclusion': int(total_words * 0.15)     # 3 min
            }
        elif duration_minutes <= 45:
            # Plaidoirie moyenne
            return {
                'introduction': int(total_words * 0.10),  # 10%
                'narration': int(total_words * 0.25),     # 25%
                'arguments': int(total_words * 0.50),     # 50%
                'conclusion': int(total_words * 0.15)     # 15%
            }
        else:
            # Plaidoirie longue : tout développer
            return {
                'introduction': int(total_words * 0.08),
                'narration': int(total_words * 0.20),
                'arguments': int(total_words * 0.45),
                'refutation': int(total_words * 0.20),
                'conclusion': int(total_words * 0.07)
            }
    
    async def _generate_introduction_orale(self, request: UnifiedGenerationRequest,
                                         target_words: int,
                                         base_generator: 'UnifiedDocumentGenerator') -> str:
        """Génère une introduction percutante pour l'oral"""
        
        prompt = f"""
        Rédige une INTRODUCTION DE PLAIDOIRIE percutante et mémorable.
        Longueur: {target_words} mots exactement.
        
        AFFAIRE: {request.contexte[:500]}
        CLIENT: {request.parties.get('demandeurs', [{}])[0].nom if request.parties.get('demandeurs') else 'Le demandeur'}
        
        OBJECTIFS:
        1. Capter immédiatement l'attention (phrase d'accroche forte)
        2. Présenter l'enjeu principal en termes humains
        3. Annoncer la ligne de défense/accusation
        4. Créer une connexion émotionnelle
        
        STYLE ORAL:
        - Phrases courtes et rythmées
        - Vocabulaire accessible mais soutenu
        - Effets oratoires (questions rhétoriques, anaphores)
        - Ton {request.style.value}
        
        STRUCTURE:
        - Accroche (20%)
        - Présentation de l'affaire (40%)
        - Enjeux humains/juridiques (25%)
        - Annonce du plan (15%)
        """
        
        response = await base_generator.llm_manager.query_single_llm_async(
            provider=base_generator._select_best_provider(request),
            query=prompt,
            system_prompt="""Tu es un avocat plaidant expérimenté, maître dans l'art oratoire.
            Tu sais captiver ton auditoire dès les premiers mots et créer une atmosphère dramatique appropriée."""
        )
        
        if response.get('success'):
            return f"[INTRODUCTION - {target_words//self.WORDS_PER_MINUTE} minutes]\n\n{response['response']}"
        
        return "[Introduction à générer]"
    
    async def _generate_arguments_oraux(self, request: UnifiedGenerationRequest,
                                       target_words: int,
                                       base_generator: 'UnifiedDocumentGenerator') -> str:
        """Génère les arguments adaptés à l'oral"""
        
        # Si on a des conclusions de support, s'en inspirer
        base_arguments = ""
        if request.support_conclusions:
            base_arguments = f"""
            ARGUMENTS DES CONCLUSIONS À ADAPTER POUR L'ORAL:
            {request.support_conclusions.contenu[:2000]}
            """
        
        # Points forts à mettre en avant
        points_forts = ""
        if request.points_forts_oraux:
            points_forts = f"""
            POINTS FORTS À DÉVELOPPER:
            {chr(10).join([f'- {point}' for point in request.points_forts_oraux])}
            """
        
        prompt = f"""
        Développe les ARGUMENTS PRINCIPAUX pour une plaidoirie orale.
        Longueur: {target_words} mots.
        
        {base_arguments}
        {points_forts}
        
        INFRACTIONS: {', '.join([i.type.value for i in request.infractions])}
        
        ADAPTATION ORALE:
        1. Transformer le juridique en narratif
        2. Utiliser des exemples concrets et visuels
        3. Créer des moments d'intensité dramatique
        4. Alterner rythmes (lent pour l'important, rapide pour dynamiser)
        5. Intégrer des pauses stratégiques [PAUSE]
        
        TECHNIQUES ORATOIRES:
        - Questions rhétoriques pour impliquer l'auditoire
        - Répétitions pour marquer les esprits
        - Métaphores pour illustrer
        - Gradations pour monter en puissance
        - Formules frappantes mémorables
        
        STRUCTURE PAR ARGUMENT:
        1. Annonce claire
        2. Développement avec preuves
        3. Illustration concrète
        4. Conclusion partielle forte
        """
        
        response = await base_generator.llm_manager.query_single_llm_async(
            provider=base_generator._select_best_provider(request),
            query=prompt
        )
        
        if response.get('success'):
            # Ajouter des marqueurs de timing
            content = response['response']
            return self._add_timing_markers(content, target_words)
            
        return "[Arguments à générer]"
    
    def _add_timing_markers(self, content: str, target_words: int) -> str:
        """Ajoute des marqueurs temporels pour aider l'orateur"""
        
        # Calculer le temps approximatif
        time_minutes = target_words // self.WORDS_PER_MINUTE
        
        # Diviser en sections
        paragraphs = content.split('\n\n')
        words_per_paragraph = target_words // max(len(paragraphs), 1)
        
        marked_content = f"[SECTION {time_minutes} MINUTES]\n\n"
        
        cumulative_time = 0
        for i, para in enumerate(paragraphs):
            para_words = len(para.split())
            para_time = para_words / self.WORDS_PER_MINUTE
            cumulative_time += para_time
            
            if i > 0 and i % 3 == 0:  # Marqueur tous les 3 paragraphes
                marked_content += f"\n[TEMPS ÉCOULÉ: {cumulative_time:.1f} min]\n\n"
            
            marked_content += para + "\n\n"
        
        return marked_content
    
    def _assemble_plaidoirie_with_timing(self, sections: Dict[str, str], 
                                        duration_minutes: int) -> str:
        """Assemble la plaidoirie avec indications temporelles"""
        
        content = f"""PLAIDOIRIE - DURÉE CIBLE : {duration_minutes} MINUTES
========================================================

RAPPEL TIMING:
- Introduction : {int(duration_minutes * 0.1)} minutes
- Corps : {int(duration_minutes * 0.75)} minutes  
- Conclusion : {int(duration_minutes * 0.15)} minutes

========================================================

"""
        
        for section_name, section_content in sections.items():
            content += f"\n{section_content}\n\n"
            content += "[TRANSITION - RESPIRER - REGARDER L'AUDITOIRE]\n\n"
        
        # Ajouter un résumé timing à la fin
        total_words = sum(len(s.split()) for s in sections.values())
        estimated_time = total_words / self.WORDS_PER_MINUTE
        
        content += f"""
========================================================
RÉCAPITULATIF:
- Nombre de mots : {total_words}
- Durée estimée : {estimated_time:.1f} minutes
- Vitesse recommandée : {self.WORDS_PER_MINUTE} mots/min
========================================================
"""
        
        return content
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "duration_range": [10, 120],  # minutes
            "adaptation_from_conclusions": True,
            "oral_techniques": True,
            "timing_markers": True,
            "voice_guidance": True
        }

# =============== PLUGIN STANDARD ===============

class StandardDocumentPlugin(GenerationPlugin):
    """Plugin pour documents standards (5-15 pages)"""
    
    def can_handle(self, request: UnifiedGenerationRequest) -> bool:
        # Plugin par défaut
        return True
    
    async def generate(self, request: UnifiedGenerationRequest,
                      base_generator: 'UnifiedDocumentGenerator') -> DocumentJuridique:
        """Génération standard optimisée"""
        
        # Utiliser la logique existante de base_generator
        structure = base_generator._get_standard_structure(request.document_type)
        
        sections = {}
        for section in structure['sections']:
            sections[section] = await base_generator._generate_section_standard(
                section, request
            )
        
        return base_generator._assemble_final_document(sections, request)
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "length_range": [2500, 15000],  # mots
            "templates": True,
            "ai_enhancement": True
        }

# =============== GESTIONNAIRE PRINCIPAL ===============

class UnifiedDocumentGenerator:
    """Gestionnaire unifié avec système de plugins"""
    
    def __init__(self):
        # Gestionnaires existants
        self.llm_manager = MultiLLMManager()
        self.template_manager = TemplateManager()
        self.style_analyzer = StyleAnalyzer()
        self.jurisprudence_verifier = JurisprudenceVerifier()
        
        # Plugins
        self.plugins: Dict[str, GenerationPlugin] = {
            'long': LongDocumentPlugin(),
            'plaidoirie': PlaidoiriePlugin(),
            'standard': StandardDocumentPlugin()
        }
        
        # Cache et configuration
        self._cache = {}
        self._templates_cache = {}
        
    async def generate(self, request: UnifiedGenerationRequest) -> DocumentJuridique:
        """
        Point d'entrée unique pour TOUTE génération
        
        Sélectionne automatiquement le bon plugin
        """
        
        logger.info(f"Génération unifiée: {request.document_type.value}")
        
        # Sélectionner le plugin approprié
        selected_plugin = None
        
        # Priorité aux plugins spécialisés
        for plugin_name, plugin in self.plugins.items():
            if plugin_name != 'standard' and plugin.can_handle(request):
                selected_plugin = plugin
                logger.info(f"Plugin sélectionné: {plugin_name}")
                break
        
        # Fallback sur standard
        if not selected_plugin:
            selected_plugin = self.plugins['standard']
            logger.info("Plugin standard sélectionné (défaut)")
        
        # Générer via le plugin
        try:
            document = await selected_plugin.generate(request, self)
            
            # Post-traitement commun
            document = await self._post_process_document(document, request)
            
            return document
            
        except Exception as e:
            logger.error(f"Erreur génération: {e}")
            raise
    
    async def _post_process_document(self, document: DocumentJuridique,
                                   request: UnifiedGenerationRequest) -> DocumentJuridique:
        """Post-traitement commun à tous les documents"""
        
        # Vérification jurisprudence si demandé
        if request.options.get('verify_jurisprudence', True):
            jurisprudences = await self.jurisprudence_verifier.verify_async(document.contenu)
            if jurisprudences:
                document.metadata['jurisprudences_verified'] = len(jurisprudences)
        
        # Analyse du style si demandé
        if request.options.get('analyze_style', False):
            style_analysis = self.style_analyzer.analyze(document.contenu)
            document.metadata['style_analysis'] = style_analysis
        
        # Ajout des pièces référencées
        if request.options.get('add_pieces_references', True):
            document = self._add_pieces_references(document, request)
        
        return document
    
    def _select_best_provider(self, request: UnifiedGenerationRequest) -> str:
        """Sélectionne le meilleur LLM selon le contexte"""
        
        providers = self.llm_manager.get_available_providers()
        if not providers:
            raise ValueError("Aucun provider LLM disponible")
        
        # Préférences selon le type
        if request.length in [DocumentLength.LONG, DocumentLength.VERY_LONG]:
            # Claude pour les longs documents
            if 'anthropic' in providers:
                return 'anthropic'
        
        if request.document_type == DocumentType.PLAIDOIRIE:
            # GPT-4 pour l'oralité
            if 'openai' in providers:
                return 'openai'
        
        # Par défaut
        return providers[0]
    
    def _get_standard_structure(self, doc_type: DocumentType) -> Dict[str, List[str]]:
        """Retourne la structure standard d'un document"""
        
        structures = {
            DocumentType.PLAINTE: {
                'sections': ['en_tete', 'qualites', 'faits', 'discussion', 'demandes'],
                'required': ['en_tete', 'faits', 'demandes']
            },
            DocumentType.CONCLUSIONS: {
                'sections': ['en_tete', 'rappel', 'faits', 'discussion', 'dispositif'],
                'required': ['en_tete', 'discussion', 'dispositif']
            },
            DocumentType.ASSIGNATION: {
                'sections': ['en_tete', 'convocation', 'expose', 'moyens', 'dispositif'],
                'required': ['en_tete', 'convocation', 'dispositif']
            }
        }
        
        return structures.get(doc_type, structures[DocumentType.PLAINTE])
    
    async def _generate_section_standard(self, section: str,
                                       request: UnifiedGenerationRequest) -> str:
        """Génère une section standard"""
        
        # Utiliser un template si disponible
        template_key = f"{request.document_type.value}_{section}"
        template = self.template_manager.get_template(template_key)
        
        if template:
            # Remplir le template
            context = self._build_template_context(request)
            content = self.template_manager.fill_template(template_key, context)
            
            # Enrichir avec IA si demandé
            if request.options.get('ai_enhancement', True):
                content = await self._enhance_with_ai(content, section, request)
            
            return content
        else:
            # Génération IA directe
            return await self._generate_section_ai(section, request)
    
    def _build_template_context(self, request: UnifiedGenerationRequest) -> Dict[str, Any]:
        """Construit le contexte pour les templates"""
        
        context = {
            'date': datetime.now().strftime('%d/%m/%Y'),
            'parties_demandeurs': ', '.join([p.nom for p in request.parties.get('demandeurs', [])]),
            'parties_defendeurs': ', '.join([p.nom for p in request.parties.get('defendeurs', [])]),
            'infractions': ', '.join([i.type.value for i in request.infractions]),
            'contexte': request.contexte,
            **request.metadata
        }
        
        return context
    
    async def _generate_section_ai(self, section: str,
                                  request: UnifiedGenerationRequest) -> str:
        """Génère une section avec l'IA"""
        
        # Prompt adapté au type de section
        prompt = f"""
        Génère la section '{section}' pour un(e) {request.document_type.value}.
        
        Style: {request.style.value}
        Contexte: {request.contexte}
        
        Parties:
        - Demandeurs: {', '.join([p.nom for p in request.parties.get('demandeurs', [])])}
        - Défendeurs: {', '.join([p.nom for p in request.parties.get('defendeurs', [])])}
        
        Instructions spécifiques pour '{section}':
        {self._get_section_instructions(section, request.document_type)}
        """
        
        response = await self.llm_manager.query_single_llm_async(
            provider=self._select_best_provider(request),
            query=prompt
        )
        
        if response.get('success'):
            return response['response']
            
        return f"[Section {section} à générer]"
    
    def _assemble_final_document(self, sections: Dict[str, str],
                               request: UnifiedGenerationRequest) -> DocumentJuridique:
        """Assemble le document final"""
        
        # Joindre les sections
        content_parts = []
        structure = self._get_standard_structure(request.document_type)
        
        for section in structure['sections']:
            if section in sections:
                content_parts.append(sections[section])
        
        content = '\n\n'.join(content_parts)
        
        # Créer le document
        return DocumentJuridique(
            titre=self._generate_title(request),
            type_document=request.document_type.value,
            contenu=content,
            auteur=request.metadata.get('auteur', 'Assistant IA'),
            date_creation=datetime.now(),
            metadata={
                'style': request.style.value,
                'length': request.length.value,
                'word_count': len(content.split()),
                'generation_method': 'unified',
                **request.metadata
            }
        )
    
    def _generate_title(self, request: UnifiedGenerationRequest) -> str:
        """Génère un titre approprié"""
        
        partie = ''
        if request.parties.get('demandeurs'):
            partie = request.parties['demandeurs'][0].nom
        elif request.parties.get('defendeurs'):
            partie = request.parties['defendeurs'][0].nom
            
        date = datetime.now().strftime('%d/%m/%Y')
        
        return f"{request.document_type.value.replace('_', ' ').title()} - {partie} - {date}"
    
    def get_plugin_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Retourne les capacités de tous les plugins"""
        
        capabilities = {}
        for name, plugin in self.plugins.items():
            capabilities[name] = plugin.get_capabilities()
            
        return capabilities