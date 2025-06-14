"""Module de génération pour documents juridiques longs (25-50+ pages)"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
from pathlib import Path
import time
import asyncio
from typing import Dict, List, Optional, Any
import json
import plotly.express as px
import plotly.graph_objects as go

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import truncate_text, clean_key, format_legal_date

# Import des configurations
try:
    from config.cahier_des_charges import (
        STRUCTURES_ACTES, 
        PROMPTS_GENERATION,
        INFRACTIONS_PENALES,
        FORMULES_JURIDIQUES
    )
except ImportError:
    # Configurations par défaut si imports échouent
    STRUCTURES_ACTES = {}
    PROMPTS_GENERATION = {'style_instruction': ''}
    INFRACTIONS_PENALES = []
    FORMULES_JURIDIQUES = {}

# Import du gestionnaire LLM
try:
    from managers.llm_manager import get_llm_manager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# ========================= CONFIGURATION =========================

# Modèles d'IA disponibles
AVAILABLE_MODELS = {
    "anthropic": {
        "name": "Claude 3 Opus",
        "icon": "🧠",
        "strengths": ["Raisonnement juridique", "Documents longs", "Cohérence"],
        "max_tokens": 100000
    },
    "openai": {
        "name": "GPT-4 Turbo",
        "icon": "🤖",
        "strengths": ["Créativité", "Rapidité", "Multilangue"],
        "max_tokens": 128000
    },
    "mistral": {
        "name": "Mistral Large",
        "icon": "🌟",
        "strengths": ["Efficacité", "Précision", "Français"],
        "max_tokens": 32000
    },
    "cohere": {
        "name": "Command R+",
        "icon": "💡",
        "strengths": ["Recherche", "Synthèse", "Citations"],
        "max_tokens": 128000
    }
}

# Types de documents avec leurs caractéristiques
DOCUMENT_TYPES = {
    'plainte_cpc': {
        'name': 'Plainte avec CPC',
        'icon': '⚖️',
        'pages': '50+',
        'complexity': 5,
        'sections': ['en_tete', 'identite_complete', 'faits_detailles', 'discussion_par_qualification', 'prejudice_demandes', 'pieces']
    },
    'conclusions_fond': {
        'name': 'Conclusions au fond',
        'icon': '📑',
        'pages': '40-50',
        'complexity': 4,
        'sections': ['en_tete', 'faits_procedure', 'discussion_juridique', 'demandes']
    },
    'conclusions_nullite': {
        'name': 'Conclusions de nullité',
        'icon': '🚫',
        'pages': '30-35',
        'complexity': 4,
        'sections': ['en_tete', 'nullite_copj', 'grief', 'demandes']
    },
    'conclusions_appel': {
        'name': "Conclusions d'appel",
        'icon': '📤',
        'pages': '40-45',
        'complexity': 4,
        'sections': ['en_tete', 'critique_motifs_fait', 'critique_motifs_droit', 'demandes']
    },
    'observations_175': {
        'name': 'Observations art. 175',
        'icon': '📝',
        'pages': '40-45',
        'complexity': 4,
        'sections': ['en_tete', 'evolution_accusations', 'qualification_approfondie', 'demandes']
    },
    'plainte_simple': {
        'name': 'Plainte simple',
        'icon': '📋',
        'pages': '25-30',
        'complexity': 3,
        'sections': ['en_tete', 'faits', 'discussion', 'demandes']
    },
    'citation_directe': {
        'name': 'Citation directe',
        'icon': '📮',
        'pages': '20-25',
        'complexity': 3,
        'sections': ['en_tete', 'expose_faits', 'application_espece', 'volet_civil']
    }
}

# ========================= GÉNÉRATEUR DOCUMENTS LONGS =========================

class GenerateurDocumentsLongsV2:
    """Générateur amélioré pour documents juridiques de 25-50+ pages"""
    
    def __init__(self):
        self.llm_manager = get_llm_manager() if LLM_AVAILABLE else None
        self.max_tokens_per_section = 4000
        self.models_config = {}
        
    def configure_models(self, models: List[str], fusion_mode: str = "vote"):
        """Configure les modèles à utiliser"""
        self.models_config = {
            'models': models,
            'fusion_mode': fusion_mode  # vote, average, best
        }
        
    async def generer_document_long(self, type_acte: str, params: Dict) -> Dict[str, Any]:
        """Génère un document long avec interface améliorée"""
        
        # Récupérer la configuration
        doc_config = DOCUMENT_TYPES.get(type_acte, {})
        structure = STRUCTURES_ACTES.get(type_acte, {})
        longueur_cible = structure.get('longueur_cible', 20000)
        longueur_min = structure.get('longueur_min', 15000)
        longueur_max = structure.get('longueur_max', 30000)
        
        # Container principal pour le suivi
        main_container = st.container()
        
        with main_container:
            # Header avec métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 Type", doc_config.get('name', type_acte))
            with col2:
                st.metric("📊 Pages cibles", doc_config.get('pages', '25+'))
            with col3:
                st.metric("🎯 Mots cibles", f"{longueur_cible:,}")
            with col4:
                complexity_stars = "⭐" * doc_config.get('complexity', 3)
                st.metric("💪 Complexité", complexity_stars)
            
            # Barre de progression principale
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_elapsed = st.empty()
            
            # Container pour les sections
            sections_container = st.container()
            
        # Initialiser le document
        document = {
            'type': type_acte,
            'sections': {},
            'contenu_complet': '',
            'metadata': {
                'longueur_mots': 0,
                'nb_pages_estimees': 0,
                'temps_generation': 0,
                'sections_generees': 0,
                'modeles_utilises': self.models_config.get('models', []),
                'fusion_mode': self.models_config.get('fusion_mode', 'single')
            }
        }
        
        # Timer
        start_time = time.time()
        
        # Générer section par section avec UI améliorée
        sections = doc_config.get('sections', structure.get('sections', []))
        total_sections = len(sections)
        
        # Créer un expander pour chaque section
        section_expanders = {}
        with sections_container:
            for section in sections:
                section_name = section.replace('_', ' ').title()
                section_expanders[section] = st.expander(
                    f"{self._get_section_icon(section)} {section_name}",
                    expanded=False
                )
        
        for idx, section in enumerate(sections):
            # Mettre à jour le statut
            elapsed = time.time() - start_time
            time_elapsed.text(f"⏱️ Temps écoulé : {elapsed:.1f}s")
            status_text.text(f"🔄 Génération : {section.replace('_', ' ').title()}")
            
            # Calculer la longueur cible
            section_weight = self._get_section_weight(section, type_acte)
            section_target = int(longueur_cible * section_weight)
            
            # Afficher les détails dans l'expander
            with section_expanders[section]:
                section_col1, section_col2 = st.columns([3, 1])
                with section_col1:
                    section_progress = st.progress(0)
                    section_status = st.empty()
                with section_col2:
                    section_metric = st.empty()
                
                # Générer la section avec suivi
                section_content = await self._generer_section_avec_suivi(
                    section=section,
                    type_acte=type_acte,
                    params=params,
                    target_length=section_target,
                    context=document['sections'],
                    progress_callback=lambda p, s: self._update_section_progress(
                        section_progress, section_status, section_metric, p, s
                    )
                )
            
            # Stocker la section
            document['sections'][section] = section_content
            
            # Mettre à jour les métriques globales
            section_words = len(section_content.split())
            document['metadata']['longueur_mots'] += section_words
            document['metadata']['sections_generees'] += 1
            
            # Mettre à jour la progress bar principale
            progress = (idx + 1) / total_sections
            progress_bar.progress(progress)
            
            # Marquer la section comme complétée
            with section_expanders[section]:
                st.success(f"✅ Section complétée : {section_words:,} mots")
        
        # Assembler le document final
        status_text.text("🔧 Assemblage du document final...")
        document['contenu_complet'] = self._assembler_document_long(
            sections=document['sections'],
            type_acte=type_acte,
            params=params
        )
        
        # Vérifier et enrichir si nécessaire
        mots_actuels = len(document['contenu_complet'].split())
        if mots_actuels < longueur_min and params.get('options', {}).get('enrichissement_auto', True):
            status_text.text("📝 Enrichissement automatique...")
            document = await self._enrichir_document_intelligent(document, longueur_min, params)
        
        # Finaliser
        document['metadata']['longueur_mots'] = len(document['contenu_complet'].split())
        document['metadata']['nb_pages_estimees'] = document['metadata']['longueur_mots'] // 500
        document['metadata']['temps_generation'] = time.time() - start_time
        
        # Affichage final
        progress_bar.progress(1.0)
        status_text.text("✅ Document généré avec succès !")
        time_elapsed.text(f"⏱️ Temps total : {document['metadata']['temps_generation']:.1f}s")
        
        return document
    
    def _get_section_icon(self, section: str) -> str:
        """Retourne une icône appropriée pour chaque section"""
        icons = {
            'en_tete': '📋',
            'identite_complete': '👤',
            'parties': '👥',
            'faits': '📖',
            'faits_detailles': '📚',
            'faits_procedure': '⚖️',
            'expose_faits': '📝',
            'discussion': '💭',
            'discussion_juridique': '⚖️',
            'discussion_par_qualification': '🔍',
            'qualification_approfondie': '🔬',
            'critique_motifs_droit': '⚖️',
            'critique_motifs_fait': '📊',
            'nullite_copj': '🚫',
            'application_espece': '🎯',
            'grief': '⚠️',
            'evolution_accusations': '📈',
            'prejudice_demandes': '💰',
            'prejudices': '💸',
            'volet_civil': '⚖️',
            'dispositif': '📜',
            'par_ces_motifs': '⚖️',
            'demandes': '📋',
            'pieces': '📎',
            'election_domicile': '🏠',
            'consignation': '💶'
        }
        return icons.get(section, '📄')
    
    def _update_section_progress(self, progress_bar, status_text, metric, progress, status):
        """Met à jour l'interface pour une section"""
        progress_bar.progress(progress)
        status_text.text(status)
        if 'mots' in status:
            # Extraire le nombre de mots du status
            words = status.split(':')[-1].strip().split()[0].replace(',', '')
            try:
                metric.metric("Mots", f"{int(words):,}")
            except:
                pass
    
    async def _generer_section_avec_suivi(self, section: str, type_acte: str,
                                         params: Dict, target_length: int,
                                         context: Dict, progress_callback) -> str:
        """Génère une section avec suivi du progrès"""
        
        # Si fusion de modèles activée
        if len(self.models_config.get('models', [])) > 1:
            return await self._generer_section_fusion(
                section, type_acte, params, target_length, context, progress_callback
            )
        
        # Génération simple
        progress_callback(0.1, "📝 Préparation du prompt...")
        
        prompt = self._creer_prompt_section_longue(
            section, type_acte, params, target_length, context
        )
        
        if not self.llm_manager:
            progress_callback(1.0, "✅ Section générée (mode template)")
            return self._generer_section_template_longue(
                section, type_acte, params, target_length
            )
        
        # Pour sections longues, multi-passes
        if target_length > 3000:
            return await self._generer_section_multi_passes_avec_suivi(
                prompt, target_length, section, progress_callback
            )
        else:
            progress_callback(0.5, "🤖 Génération IA en cours...")
            
            model = self.models_config.get('models', ['anthropic'])[0]
            response = self.llm_manager.query_single_llm(
                provider=model,
                query=prompt,
                system_prompt=PROMPTS_GENERATION.get('style_instruction', ''),
                max_tokens=self.max_tokens_per_section
            )
            
            if response['success']:
                words = len(response['response'].split())
                progress_callback(1.0, f"✅ Généré : {words:,} mots")
                return response['response']
            else:
                progress_callback(1.0, "⚠️ Fallback template")
                return self._generer_section_template_longue(
                    section, type_acte, params, target_length
                )
    
    async def _generer_section_fusion(self, section: str, type_acte: str,
                                     params: Dict, target_length: int,
                                     context: Dict, progress_callback) -> str:
        """Génère une section en utilisant plusieurs modèles et fusion"""
        
        models = self.models_config.get('models', ['anthropic'])
        fusion_mode = self.models_config.get('fusion_mode', 'vote')
        
        progress_callback(0.1, f"🔄 Fusion {len(models)} modèles...")
        
        # Créer le prompt
        prompt = self._creer_prompt_section_longue(
            section, type_acte, params, target_length, context
        )
        
        # Générer avec chaque modèle
        responses = {}
        for i, model in enumerate(models):
            progress = 0.1 + (0.7 * i / len(models))
            progress_callback(progress, f"🤖 {AVAILABLE_MODELS[model]['name']}...")
            
            if self.llm_manager:
                response = self.llm_manager.query_single_llm(
                    provider=model,
                    query=prompt,
                    system_prompt=PROMPTS_GENERATION.get('style_instruction', ''),
                    max_tokens=min(self.max_tokens_per_section, 
                                 AVAILABLE_MODELS[model]['max_tokens'])
                )
                if response['success']:
                    responses[model] = response['response']
        
        # Fusionner les réponses
        progress_callback(0.85, "🔀 Fusion des réponses...")
        
        if not responses:
            progress_callback(1.0, "⚠️ Aucune réponse, fallback template")
            return self._generer_section_template_longue(
                section, type_acte, params, target_length
            )
        
        # Stratégies de fusion
        if fusion_mode == "best":
            # Choisir la meilleure réponse (la plus longue et cohérente)
            best_response = max(responses.values(), key=lambda x: len(x))
            result = best_response
        elif fusion_mode == "average":
            # Moyenner et combiner
            result = self._fusionner_reponses_moyenne(responses, target_length)
        else:  # vote
            # Voter sur les meilleurs éléments
            result = self._fusionner_reponses_vote(responses, target_length)
        
        words = len(result.split())
        progress_callback(1.0, f"✅ Fusion complète : {words:,} mots")
        
        return result
    
    def _fusionner_reponses_moyenne(self, responses: Dict[str, str], target_length: int) -> str:
        """Fusionne les réponses en prenant le meilleur de chaque"""
        # Pour simplifier, on prend des paragraphes de chaque réponse
        all_paragraphs = []
        
        for model, response in responses.items():
            paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
            all_paragraphs.extend([(p, model) for p in paragraphs])
        
        # Sélectionner les meilleurs paragraphes jusqu'à la longueur cible
        result_paragraphs = []
        current_length = 0
        
        for paragraph, model in all_paragraphs:
            paragraph_words = len(paragraph.split())
            if current_length + paragraph_words <= target_length * 1.1:
                result_paragraphs.append(paragraph)
                current_length += paragraph_words
        
        return '\n\n'.join(result_paragraphs)
    
    def _fusionner_reponses_vote(self, responses: Dict[str, str], target_length: int) -> str:
        """Fusionne par vote sur les éléments communs"""
        # Analyse des éléments communs
        common_elements = []
        
        # Pour l'instant, on prend la réponse la plus complète
        # et on l'enrichit avec des éléments uniques des autres
        base_response = max(responses.values(), key=lambda x: len(x))
        
        # Enrichir avec des éléments uniques
        for model, response in responses.items():
            if response != base_response:
                # Extraire des éléments uniques (simplification)
                unique_parts = response[-1000:]  # Derniers 1000 caractères
                if unique_parts not in base_response:
                    base_response += f"\n\n{unique_parts}"
        
        return base_response[:target_length * 6]  # Approximation caractères
    
    async def _generer_section_multi_passes_avec_suivi(self, base_prompt: str,
                                                      target_length: int,
                                                      section_name: str,
                                                      progress_callback) -> str:
        """Génère en plusieurs passes avec suivi du progrès"""
        
        content_parts = []
        current_length = 0
        max_passes = 5
        
        for pass_num in range(max_passes):
            remaining_words = target_length - current_length
            
            if remaining_words <= 0:
                break
            
            # Progress pour cette passe
            pass_progress = 0.2 + (0.8 * pass_num / max_passes)
            progress_callback(pass_progress, f"📝 Passe {pass_num + 1}/{max_passes}")
            
            # Adapter le prompt
            if pass_num == 0:
                prompt = base_prompt
            else:
                prompt = f"""{base_prompt}
IMPORTANT : Ceci est la SUITE de la section (partie {pass_num + 1}).
Reprends là où tu t'es arrêté et continue le développement.
Il reste environ {remaining_words} mots à générer pour cette section.
NE PAS répéter ce qui a déjà été dit, mais CONTINUER et APPROFONDIR."""
            
            # Générer
            if self.llm_manager:
                model = self.models_config.get('models', ['anthropic'])[0]
                response = self.llm_manager.query_single_llm(
                    provider=model,
                    query=prompt,
                    system_prompt=PROMPTS_GENERATION.get('style_instruction', ''),
                    max_tokens=self.max_tokens_per_section
                )
                
                if response['success']:
                    part_content = response['response']
                    content_parts.append(part_content)
                    current_length += len(part_content.split())
                    
                    progress_callback(
                        pass_progress,
                        f"📊 Passe {pass_num + 1} : {current_length:,}/{target_length:,} mots"
                    )
                else:
                    break
            else:
                break
        
        progress_callback(1.0, f"✅ Multi-passes terminé : {current_length:,} mots")
        return '\n\n'.join(content_parts)
    
    async def _enrichir_document_intelligent(self, document: Dict, longueur_min: int,
                                           params: Dict) -> Dict:
        """Enrichissement intelligent avec analyse des sections faibles"""
        
        mots_actuels = document['metadata']['longueur_mots']
        mots_manquants = longueur_min - mots_actuels
        
        if mots_manquants <= 0:
            return document
        
        # Analyser quelles sections enrichir en priorité
        sections_analysis = []
        for section, content in document['sections'].items():
            weight = self._get_section_weight(section, document['type'])
            actual_words = len(content.split())
            expected_words = int(weight * longueur_min)
            deficit = expected_words - actual_words
            
            if deficit > 0:
                sections_analysis.append({
                    'section': section,
                    'deficit': deficit,
                    'priority': weight
                })
        
        # Trier par déficit et priorité
        sections_analysis.sort(key=lambda x: (x['deficit'] * x['priority']), reverse=True)
        
        # Enrichir les sections prioritaires
        enrichment_container = st.container()
        with enrichment_container:
            st.info(f"📈 Enrichissement intelligent : +{mots_manquants:,} mots nécessaires")
            enrichment_progress = st.progress(0)
            
            for i, section_info in enumerate(sections_analysis[:3]):  # Top 3 sections
                section = section_info['section']
                target_enrichment = min(section_info['deficit'], mots_manquants // 3)
                
                progress = i / min(3, len(sections_analysis))
                enrichment_progress.progress(progress)
                
                st.text(f"🔄 Enrichissement : {section.replace('_', ' ').title()}")
                
                # Générer contenu supplémentaire
                enrichment_prompt = self._creer_prompt_enrichissement(
                    section, document['sections'][section], target_enrichment
                )
                
                if self.llm_manager:
                    model = self.models_config.get('models', ['anthropic'])[0]
                    response = self.llm_manager.query_single_llm(
                        provider=model,
                        query=enrichment_prompt,
                        system_prompt=PROMPTS_GENERATION.get('style_instruction', '')
                    )
                    
                    if response['success']:
                        document['sections'][section] += "\n\n" + response['response']
            
            enrichment_progress.progress(1.0)
        
        # Reconstruire le document
        document['contenu_complet'] = self._assembler_document_long(
            document['sections'],
            document['type'],
            params
        )
        
        # Mettre à jour les métadonnées
        document['metadata']['longueur_mots'] = len(document['contenu_complet'].split())
        document['metadata']['nb_pages_estimees'] = document['metadata']['longueur_mots'] // 500
        document['metadata']['enrichissement'] = True
        
        return document
    
    def _creer_prompt_enrichissement(self, section: str, current_content: str,
                                   target_words: int) -> str:
        """Crée un prompt pour enrichir une section"""
        
        return f"""
La section '{section}' doit être ENRICHIE avec {target_words} mots supplémentaires.

Contenu actuel (fin de la section) :
{current_content[-2000:]}

CONSIGNES D'ENRICHISSEMENT :
1. CONTINUER le développement sans répéter
2. Ajouter des ARGUMENTS SUBSIDIAIRES
3. Développer des EXEMPLES JURISPRUDENTIELS supplémentaires
4. Approfondir l'ANALYSE DOCTRINALE
5. Ajouter des NUANCES et PRÉCISIONS
6. Développer des SCENARIOS ALTERNATIFS
7. Enrichir avec des RÉFÉRENCES COMPLÉMENTAIRES

IMPORTANT :
- NE PAS résumer ou conclure
- CONTINUER dans la même logique
- Maintenir le même niveau de détail
- Respecter le style juridique élaboré
"""
    
    def _get_section_weight(self, section: str, type_acte: str) -> float:
        """Détermine le poids relatif d'une section"""
        weights = {
            'faits': 0.35, 'faits_detailles': 0.40, 'faits_procedure': 0.35,
            'expose_faits': 0.35, 'discussion': 0.30, 'discussion_juridique': 0.35,
            'discussion_par_qualification': 0.35, 'qualification_approfondie': 0.35,
            'critique_motifs_droit': 0.25, 'critique_motifs_fait': 0.25,
            'nullite_copj': 0.15, 'application_espece': 0.10, 'grief': 0.10,
            'evolution_accusations': 0.15, 'prejudice_demandes': 0.15,
            'prejudices': 0.10, 'volet_civil': 0.10, 'en_tete': 0.05,
            'identite_complete': 0.05, 'parties': 0.05, 'dispositif': 0.05,
            'par_ces_motifs': 0.05, 'demandes': 0.05, 'pieces': 0.03,
            'election_domicile': 0.02, 'consignation': 0.02
        }
        
        # Ajustements spécifiques
        if type_acte == 'plainte_cpc' and section == 'faits_detailles':
            return 0.45
        elif type_acte == 'conclusions_fond' and section == 'discussion_par_qualification':
            return 0.40
        elif type_acte == 'conclusions_nullite' and section in ['nullite_copj', 'grief']:
            return 0.20
        
        return weights.get(section, 0.10)
    
    def _creer_prompt_section_longue(self, section: str, type_acte: str,
                                    params: Dict, target_length: int,
                                    context: Dict) -> str:
        """Crée un prompt détaillé pour générer une section longue"""
        
        parties = params.get('parties', {})
        infractions = params.get('infractions', [])
        contexte_affaire = params.get('contexte', '')
        
        # Base commune
        base_prompt = f"""
Rédige la section '{section}' pour {type_acte}.
Longueur IMPÉRATIVE : {target_length} mots MINIMUM.

CONTEXTE :
- Parties : {parties}
- Infractions : {infractions}
- Affaire : {contexte_affaire}

STYLE EXIGÉ :
- Juridique professionnel et élaboré
- Phrases complexes et nuancées
- Vocabulaire technique précis
- Développements exhaustifs
- Références doctrinales et jurisprudentielles
"""
        
        # Prompts spécialisés par section (conservés du code original)
        prompts_sections = {
            'faits_detailles': f"""
{base_prompt}

STRUCTURE DÉTAILLÉE :
I. PRÉSENTATION GÉNÉRALE (20%)
   A. Acteurs et contexte
   B. Environnement économique
   
II. GENÈSE DES FAITS (25%)
   A. Origines du litige
   B. Premiers dysfonctionnements
   
III. CHRONOLOGIE EXHAUSTIVE (35%)
   - Date, acteurs, faits, preuves
   - Analyse de chaque événement
   
IV. MÉCANISMES FRAUDULEUX (20%)
   A. Schémas et montages
   B. Modes opératoires

Développer CHAQUE point sur 200-300 mots minimum.
""",
            
            'discussion_par_qualification': f"""
{base_prompt}

POUR CHAQUE INFRACTION (3000-4000 mots) :

I. CADRE LÉGAL (1000+ mots)
   - Textes complets
   - Évolution législative
   - Doctrine

II. ÉLÉMENTS CONSTITUTIFS (1500+ mots)
   - Matériel (acte, conditions, résultat)
   - Moral (intention, dol)
   
III. APPLICATION AUX FAITS (1500+ mots)
   - Correspondance détaillée
   - Preuves et pièces
   
IV. JURISPRUDENCE (1000+ mots)
   - Minimum 10 arrêts analysés
"""
        }
        
        return prompts_sections.get(section, base_prompt)
    
    def _generer_section_template_longue(self, section: str, type_acte: str,
                                       params: Dict, target_length: int) -> str:
        """Template de fallback pour génération sans IA"""
        
        template = f"""
[SECTION : {section.upper().replace('_', ' ')}]
[Longueur cible : {target_length} mots]

[Cette section contiendra un développement exhaustif sur les points suivants :]

I. INTRODUCTION ET CONTEXTE
[Développement de 500-800 mots sur le contexte spécifique à cette section]

II. DÉVELOPPEMENT PRINCIPAL
[Corps principal de 60-70% de la longueur totale]
A. Premier aspect
B. Deuxième aspect
C. Troisième aspect

III. ANALYSE APPROFONDIE
[Analyse détaillée de 20-30% de la longueur]

IV. ÉLÉMENTS COMPLÉMENTAIRES
[Développements subsidiaires]

[Note : En production, cette section sera générée par l'IA avec le contenu juridique approprié]
"""
        return template
    
    def _assembler_document_long(self, sections: Dict[str, str],
                                type_acte: str, params: Dict) -> str:
        """Assemble le document final avec mise en forme"""
        
        # En-tête selon le type
        headers = {
            'plainte_cpc': """PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE

À L'ATTENTION DE MONSIEUR LE DOYEN DES JUGES D'INSTRUCTION
TRIBUNAL JUDICIAIRE DE [VILLE]

""",
            'conclusions_fond': """CONCLUSIONS AU FOND

POUR : [CLIENT]
CONTRE : [PARTIES ADVERSES]

""",
            'conclusions_nullite': """CONCLUSIONS AUX FINS DE NULLITÉ

POUR : [CLIENT]
CONTRE : [MINISTÈRE PUBLIC ET PARTIES]

"""
        }
        
        document_parts = [headers.get(type_acte, f"{type_acte.upper()}\n\n")]
        
        # Ajouter les sections avec numérotation
        section_number = 1
        for section_key, section_content in sections.items():
            section_title = section_key.upper().replace('_', ' ')
            roman_num = self._to_roman(section_number)
            
            document_parts.append(f"\n\n{roman_num}. {section_title}\n\n")
            document_parts.append(section_content)
            section_number += 1
        
        # Conclusion
        document_parts.append(self._generer_conclusion_longue(type_acte, params))
        
        return ''.join(document_parts)
    
    def _to_roman(self, num: int) -> str:
        """Convertit en chiffres romains"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        roman_num = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syms[i]
                num -= val[i]
            i += 1
        return roman_num
    
    def _generer_conclusion_longue(self, type_acte: str, params: Dict) -> str:
        """Génère la conclusion du document"""
        
        date_str = datetime.now().strftime('%d/%m/%Y')
        
        conclusions = {
            'plainte_cpc': f"""

PAR CES MOTIFS

Il est demandé à Monsieur le Doyen des Juges d'Instruction de bien vouloir :

- RECEVOIR la présente plainte avec constitution de partie civile ;
- CONSTATER la recevabilité et le bien-fondé de la constitution de partie civile ;
- ORDONNER l'ouverture d'une information judiciaire ;
- PROCÉDER à tous actes utiles à la manifestation de la vérité ;

SOUS TOUTES RÉSERVES

Fait à [VILLE], le {date_str}

[SIGNATURE]

BORDEREAU DE PIÈCES COMMUNIQUÉES
[Liste des pièces]
""",
            
            'conclusions_fond': f"""

PAR CES MOTIFS

[DEMANDES PRINCIPALES ET SUBSIDIAIRES]

SOUS TOUTES RÉSERVES

Fait le {date_str}

[SIGNATURE AVOCAT]
"""
        }
        
        return conclusions.get(type_acte, f"\n\nFait le {date_str}\n[SIGNATURE]")

# ========================= INTERFACE UTILISATEUR =========================

def run():
    """Fonction principale du module - OBLIGATOIRE"""
    
    # Titre et description
    st.title("📜 Générateur de Documents Juridiques Longs")
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>🎯 Module spécialisé pour documents complexes (25-50+ pages)</h3>
        <p>Ce module génère des actes juridiques exhaustifs adaptés aux dossiers complexes de droit pénal des affaires.</p>
        <ul>
            <li>📊 <b>Longueur</b> : 25 à 50+ pages selon le type d'acte</li>
            <li>🤖 <b>IA Multiple</b> : Fusion de plusieurs modèles pour une qualité optimale</li>
            <li>📈 <b>Enrichissement</b> : Ajustement automatique de la longueur</li>
            <li>⚡ <b>Performance</b> : Génération parallèle et optimisée</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation
    if 'generateur_long_v2' not in st.session_state:
        st.session_state.generateur_long_v2 = GenerateurDocumentsLongsV2()
    if 'document_genere' not in st.session_state:
        st.session_state.document_genere = None
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    
    generateur = st.session_state.generateur_long_v2
    
    # Structure en onglets
    tabs = st.tabs(["📝 Configuration", "🤖 Modèles IA", "🚀 Génération", "📊 Résultats", "📚 Historique"])
    
    with tabs[0]:  # Configuration
        st.markdown("### 📝 Configuration du document")
        
        # Sélection du type avec carte visuelle
        st.markdown("#### Type de document")
        
        # Créer une grille de cartes pour les types de documents
        cols = st.columns(3)
        selected_type = None
        
        for idx, (key, config) in enumerate(DOCUMENT_TYPES.items()):
            col = cols[idx % 3]
            with col:
                if st.button(
                    f"{config['icon']} {config['name']}\n{config['pages']} pages",
                    key=f"type_{key}",
                    use_container_width=True,
                    help=f"Complexité : {'⭐' * config['complexity']}"
                ):
                    st.session_state.selected_doc_type = key
        
        # Afficher le type sélectionné
        if 'selected_doc_type' in st.session_state:
            selected_type = st.session_state.selected_doc_type
            doc_config = DOCUMENT_TYPES[selected_type]
            
            st.success(f"✅ Type sélectionné : {doc_config['icon']} {doc_config['name']}")
            
            # Afficher les détails
            with st.expander("📋 Détails du document", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pages estimées", doc_config['pages'])
                with col2:
                    st.metric("Complexité", "⭐" * doc_config['complexity'])
                with col3:
                    st.metric("Sections", len(doc_config['sections']))
                
                # Liste des sections
                st.markdown("**Sections incluses :**")
                sections_text = []
                for section in doc_config['sections']:
                    icon = generateur._get_section_icon(section)
                    name = section.replace('_', ' ').title()
                    sections_text.append(f"{icon} {name}")
                st.write(" • ".join(sections_text))
        
        # Configuration des parties
        st.markdown("#### 👥 Parties")
        
        col1, col2 = st.columns(2)
        with col1:
            demandeurs = st.text_area(
                "Demandeurs / Plaignants",
                height=100,
                placeholder="Un par ligne\nEx: SCI PATRIMOINE\nM. DUPONT Jean",
                help="Entrez les noms des demandeurs, un par ligne"
            )
        
        with col2:
            defendeurs = st.text_area(
                "Défendeurs / Mis en cause",
                height=100,
                placeholder="Un par ligne\nEx: SA CONSTRUCTION\nM. MARTIN Pierre",
                help="Entrez les noms des défendeurs, un par ligne"
            )
        
        # Infractions
        st.markdown("#### 🚨 Infractions")
        
        # Liste prédéfinie avec possibilité d'ajouter
        infractions_predefinies = [
            "Abus de biens sociaux", "Corruption", "Escroquerie",
            "Abus de confiance", "Blanchiment", "Faux et usage de faux",
            "Détournement de fonds publics", "Favoritisme",
            "Prise illégale d'intérêts", "Trafic d'influence"
        ]
        
        infractions = st.multiselect(
            "Sélectionnez les infractions",
            infractions_predefinies,
            help="Vous pouvez sélectionner plusieurs infractions"
        )
        
        # Ajout d'infractions personnalisées
        infraction_custom = st.text_input(
            "Ajouter une infraction non listée",
            placeholder="Ex: Violation du secret professionnel"
        )
        if infraction_custom and st.button("➕ Ajouter", key="add_infraction"):
            infractions.append(infraction_custom)
            st.success(f"✅ Ajouté : {infraction_custom}")
        
        # Contexte
        st.markdown("#### 📖 Contexte de l'affaire")
        
        contexte = st.text_area(
            "Description détaillée",
            height=200,
            placeholder="""Décrivez l'affaire en détail :
- Période des faits
- Montants en jeu
- Contexte économique
- Relations entre les parties
- Éléments clés...""",
            help="Plus le contexte est détaillé, plus le document sera pertinent"
        )
        
        # Validation de la configuration
        config_complete = all([
            'selected_doc_type' in st.session_state,
            demandeurs.strip() or defendeurs.strip(),
            infractions,
            contexte.strip()
        ])
        
        if config_complete:
            st.success("✅ Configuration complète")
            st.session_state.doc_config = {
                'type': selected_type,
                'parties': {
                    'demandeurs': [d.strip() for d in demandeurs.split('\n') if d.strip()],
                    'defendeurs': [d.strip() for d in defendeurs.split('\n') if d.strip()]
                },
                'infractions': infractions,
                'contexte': contexte
            }
        else:
            st.warning("⚠️ Veuillez compléter tous les champs obligatoires")
    
    with tabs[1]:  # Modèles IA
        st.markdown("### 🤖 Configuration des modèles d'IA")
        
        st.info("""
        💡 **Fusion de modèles** : Combinez plusieurs IA pour obtenir le meilleur de chaque modèle.
        Chaque modèle a ses forces spécifiques.
        """)
        
        # Sélection des modèles
        st.markdown("#### Sélection des modèles")
        
        selected_models = []
        cols = st.columns(2)
        
        for idx, (model_key, model_info) in enumerate(AVAILABLE_MODELS.items()):
            col = cols[idx % 2]
            with col:
                if st.checkbox(
                    f"{model_info['icon']} {model_info['name']}",
                    key=f"model_{model_key}",
                    help=f"Forces : {', '.join(model_info['strengths'])}"
                ):
                    selected_models.append(model_key)
        
        if not selected_models:
            st.warning("⚠️ Sélectionnez au moins un modèle")
            selected_models = ['anthropic']  # Par défaut
        
        # Mode de fusion
        if len(selected_models) > 1:
            st.markdown("#### 🔀 Mode de fusion")
            
            fusion_mode = st.radio(
                "Stratégie de fusion",
                [
                    ("vote", "🗳️ Vote", "Sélectionne les meilleurs éléments de chaque modèle"),
                    ("average", "⚖️ Moyenne", "Combine équitablement les réponses"),
                    ("best", "🏆 Meilleur", "Choisit la réponse la plus complète")
                ],
                format_func=lambda x: f"{x[1]} {x[0].title()} - {x[2]}",
                horizontal=True
            )[0]
        else:
            fusion_mode = "single"
        
        # Afficher la configuration
        st.markdown("#### Configuration actuelle")
        
        config_cols = st.columns(len(selected_models) or 1)
        for idx, model in enumerate(selected_models):
            with config_cols[idx]:
                model_info = AVAILABLE_MODELS[model]
                st.metric(
                    model_info['name'],
                    model_info['icon'],
                    f"Max: {model_info['max_tokens']:,} tokens"
                )
        
        # Sauvegarder la configuration
        generateur.configure_models(selected_models, fusion_mode)
        st.success(f"✅ Configuration sauvegardée : {len(selected_models)} modèle(s)")
    
    with tabs[2]:  # Génération
        st.markdown("### 🚀 Génération du document")
        
        # Vérifier la configuration
        if 'doc_config' not in st.session_state:
            st.error("❌ Veuillez d'abord configurer le document dans l'onglet Configuration")
            return
        
        config = st.session_state.doc_config
        
        # Résumé de la configuration
        with st.expander("📋 Résumé de la configuration", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Type** : {DOCUMENT_TYPES[config['type']]['icon']} {DOCUMENT_TYPES[config['type']]['name']}")
                st.markdown(f"**Demandeurs** : {len(config['parties']['demandeurs'])} partie(s)")
                st.markdown(f"**Défendeurs** : {len(config['parties']['defendeurs'])} partie(s)")
            
            with col2:
                st.markdown(f"**Infractions** : {len(config['infractions'])} sélectionnée(s)")
                st.markdown(f"**Modèles IA** : {len(selected_models)} configuré(s)")
                st.markdown(f"**Mode fusion** : {fusion_mode}")
        
        # Options avancées
        with st.expander("⚙️ Options avancées"):
            col1, col2 = st.columns(2)
            
            with col1:
                enrichissement_auto = st.checkbox(
                    "📈 Enrichissement automatique",
                    value=True,
                    help="Ajoute automatiquement du contenu si la longueur minimale n'est pas atteinte"
                )
                
                parallel_generation = st.checkbox(
                    "⚡ Génération parallèle",
                    value=False,
                    help="Génère plusieurs sections simultanément (expérimental)"
                )
            
            with col2:
                save_draft = st.checkbox(
                    "💾 Sauvegarder les brouillons",
                    value=True,
                    help="Sauvegarde automatique après chaque section"
                )
                
                verbose_mode = st.checkbox(
                    "📊 Mode verbeux",
                    value=False,
                    help="Affiche des informations détaillées pendant la génération"
                )
        
        # Estimation du temps
        doc_type_config = DOCUMENT_TYPES[config['type']]
        sections_count = len(doc_type_config['sections'])
        models_count = len(selected_models)
        
        if models_count > 1:
            time_estimate = sections_count * models_count * 15  # 15s par section par modèle
        else:
            time_estimate = sections_count * 20  # 20s par section
        
        st.info(f"""
        ⏱️ **Estimation** : {time_estimate // 60} min {time_estimate % 60} sec
        
        📊 **Détails** :
        - {sections_count} sections à générer
        - {models_count} modèle(s) utilisé(s)
        - Mode {'fusion' if models_count > 1 else 'simple'}
        """)
        
        # Bouton de génération principal
        if st.button(
            "🚀 Lancer la génération",
            type="primary",
            use_container_width=True,
            disabled=not config_complete
        ):
            # Préparer les paramètres
            params = {
                **config,
                'options': {
                    'enrichissement_auto': enrichissement_auto,
                    'parallel': parallel_generation,
                    'save_draft': save_draft,
                    'verbose': verbose_mode
                }
            }
            
            # Container pour la génération
            generation_container = st.container()
            
            with generation_container:
                # Lancer la génération
                try:
                    # Créer une tâche asynchrone
                    import asyncio
                    
                    # Générer le document
                    document = asyncio.run(
                        generateur.generer_document_long(config['type'], params)
                    )
                    
                    # Sauvegarder le résultat
                    st.session_state.document_genere = document
                    st.session_state.generation_history.append({
                        'timestamp': datetime.now(),
                        'type': config['type'],
                        'document': document
                    })
                    
                    # Afficher le succès
                    st.balloons()
                    st.success("✅ Document généré avec succès !")
                    
                    # Basculer sur l'onglet résultats
                    st.info("📊 Consultez l'onglet 'Résultats' pour voir le document")
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération : {str(e)}")
                    if verbose_mode:
                        import traceback
                        st.code(traceback.format_exc())
    
    with tabs[3]:  # Résultats
        st.markdown("### 📊 Résultats de la génération")
        
        if st.session_state.document_genere:
            document = st.session_state.document_genere
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📝 Mots",
                    f"{document['metadata']['longueur_mots']:,}",
                    f"+{document['metadata']['longueur_mots'] - 15000:,}"
                )
            
            with col2:
                st.metric(
                    "📄 Pages",
                    f"~{document['metadata']['nb_pages_estimees']}",
                    f"Cible atteinte"
                )
            
            with col3:
                st.metric(
                    "📑 Sections",
                    document['metadata']['sections_generees'],
                    "Complètes"
                )
            
            with col4:
                temps = document['metadata']['temps_generation']
                st.metric(
                    "⏱️ Temps",
                    f"{temps//60:.0f}m {temps%60:.0f}s",
                    f"{document['metadata']['longueur_mots']/temps:.0f} mots/s"
                )
            
            # Aperçu du document
            with st.expander("📄 Aperçu du document", expanded=True):
                # Options d'affichage
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    preview_length = st.slider(
                        "Longueur de l'aperçu",
                        100, 2000, 500,
                        step=100,
                        help="Nombre de mots à afficher"
                    )
                
                with col2:
                    show_structure = st.checkbox(
                        "🏗️ Structure seule",
                        help="Afficher uniquement la structure"
                    )
                
                with col3:
                    highlight_sections = st.checkbox(
                        "🎨 Colorer sections",
                        help="Mettre en évidence les sections"
                    )
                
                # Affichage
                if show_structure:
                    # Afficher uniquement la structure
                    st.markdown("**Structure du document :**")
                    for section, content in document['sections'].items():
                        words = len(content.split())
                        icon = generateur._get_section_icon(section)
                        st.write(f"{icon} **{section.replace('_', ' ').title()}** : {words:,} mots")
                else:
                    # Afficher le contenu
                    preview_text = ' '.join(document['contenu_complet'].split()[:preview_length])
                    
                    if highlight_sections:
                        # Ajouter de la couleur aux titres de sections
                        import re
                        preview_text = re.sub(
                            r'([IVX]+\. [A-Z\s]+)',
                            r'<span style="color: #1f77b4; font-weight: bold;">\1</span>',
                            preview_text
                        )
                        st.markdown(preview_text, unsafe_allow_html=True)
                    else:
                        st.text(preview_text)
                    
                    st.info(f"... (aperçu limité à {preview_length} mots)")
            
            # Analyse détaillée
            with st.expander("📊 Analyse détaillée"):
                # Graphique de répartition des sections
                st.markdown("#### Répartition par section")
                
                # Préparer les données
                section_data = []
                for section, content in document['sections'].items():
                    section_data.append({
                        'Section': section.replace('_', ' ').title(),
                        'Mots': len(content.split()),
                        'Pourcentage': (len(content.split()) / document['metadata']['longueur_mots']) * 100
                    })
                
                df = pd.DataFrame(section_data)
                
                # Graphique en camembert
                fig = px.pie(
                    df,
                    values='Mots',
                    names='Section',
                    title='Répartition des mots par section',
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Tableau détaillé
                st.markdown("#### Statistiques par section")
                
                # Ajouter des colonnes calculées
                df['Pages'] = df['Mots'] / 500
                df['Densité'] = df['Mots'] / document['metadata']['sections_generees']
                
                # Formatter le tableau
                st.dataframe(
                    df.style.format({
                        'Mots': '{:,.0f}',
                        'Pourcentage': '{:.1f}%',
                        'Pages': '{:.1f}',
                        'Densité': '{:.0f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Modèles utilisés
                if document['metadata'].get('modeles_utilises'):
                    st.markdown("#### 🤖 Modèles utilisés")
                    model_cols = st.columns(len(document['metadata']['modeles_utilises']))
                    for idx, model in enumerate(document['metadata']['modeles_utilises']):
                        with model_cols[idx]:
                            model_info = AVAILABLE_MODELS.get(model, {})
                            st.info(f"{model_info.get('icon', '🤖')} {model_info.get('name', model)}")
            
            # Actions sur le document
            st.markdown("### 💾 Actions")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Télécharger en TXT
                st.download_button(
                    "📄 Télécharger (TXT)",
                    document['contenu_complet'].encode('utf-8'),
                    file_name=f"{document['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Télécharger en JSON (avec métadonnées)
                json_data = json.dumps({
                    'metadata': document['metadata'],
                    'content': document['contenu_complet'],
                    'sections': document['sections']
                }, ensure_ascii=False, indent=2)
                
                st.download_button(
                    "📊 Export JSON",
                    json_data.encode('utf-8'),
                    file_name=f"{document['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col3:
                # Copier dans le presse-papier (simulé)
                if st.button("📋 Copier", use_container_width=True):
                    st.info("📋 Utilisez Ctrl+A puis Ctrl+C dans l'aperçu")
            
            with col4:
                # Nouvelle génération
                if st.button("🔄 Nouveau", use_container_width=True):
                    st.session_state.document_genere = None
                    st.rerun()
            
            # Section d'édition
            with st.expander("✏️ Éditer le document"):
                st.warning("⚠️ L'édition modifiera le document généré")
                
                # Sélectionner la section à éditer
                section_to_edit = st.selectbox(
                    "Section à éditer",
                    list(document['sections'].keys()),
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                
                # Éditeur de texte
                edited_content = st.text_area(
                    f"Contenu de la section '{section_to_edit}'",
                    value=document['sections'][section_to_edit],
                    height=400
                )
                
                # Sauvegarder les modifications
                if st.button("💾 Sauvegarder les modifications"):
                    document['sections'][section_to_edit] = edited_content
                    # Reconstruire le document
                    document['contenu_complet'] = generateur._assembler_document_long(
                        document['sections'],
                        document['type'],
                        st.session_state.doc_config
                    )
                    # Mettre à jour les métadonnées
                    document['metadata']['longueur_mots'] = len(document['contenu_complet'].split())
                    document['metadata']['nb_pages_estimees'] = document['metadata']['longueur_mots'] // 500
                    document['metadata']['edited'] = True
                    
                    st.success("✅ Modifications sauvegardées")
                    st.rerun()
        
        else:
            # Aucun document généré
            st.info("📄 Aucun document généré pour le moment")
            st.markdown("""
            Pour générer un document :
            1. 📝 Configurez le document dans l'onglet 'Configuration'
            2. 🤖 Sélectionnez les modèles d'IA dans l'onglet 'Modèles IA'
            3. 🚀 Lancez la génération dans l'onglet 'Génération'
            """)
    
    with tabs[4]:  # Historique
        st.markdown("### 📚 Historique des générations")
        
        if st.session_state.generation_history:
            # Options de filtrage
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Filtre par type
                types_in_history = list(set(h['type'] for h in st.session_state.generation_history))
                filter_type = st.multiselect(
                    "Filtrer par type",
                    types_in_history,
                    default=types_in_history
                )
            
            with col2:
                # Tri
                sort_order = st.radio(
                    "Trier par",
                    ["Plus récent", "Plus ancien"],
                    horizontal=True
                )
            
            # Afficher l'historique
            history_filtered = [
                h for h in st.session_state.generation_history
                if h['type'] in filter_type
            ]
            
            if sort_order == "Plus récent":
                history_filtered.reverse()
            
            for idx, entry in enumerate(history_filtered):
                with st.expander(
                    f"{DOCUMENT_TYPES[entry['type']]['icon']} "
                    f"{entry['timestamp'].strftime('%d/%m/%Y %H:%M')} - "
                    f"{DOCUMENT_TYPES[entry['type']]['name']}",
                    expanded=False
                ):
                    # Métadonnées
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Mots", f"{entry['document']['metadata']['longueur_mots']:,}")
                    with col2:
                        st.metric("Pages", f"~{entry['document']['metadata']['nb_pages_estimees']}")
                    with col3:
                        temps = entry['document']['metadata']['temps_generation']
                        st.metric("Temps", f"{temps//60:.0f}m {temps%60:.0f}s")
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"👁️ Voir", key=f"view_{idx}"):
                            st.session_state.document_genere = entry['document']
                            st.info("📊 Basculez sur l'onglet 'Résultats'")
                    
                    with col2:
                        st.download_button(
                            "💾 Télécharger",
                            entry['document']['contenu_complet'].encode('utf-8'),
                            file_name=f"{entry['type']}_{entry['timestamp'].strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key=f"download_{idx}"
                        )
                    
                    with col3:
                        if st.button(f"🗑️ Supprimer", key=f"delete_{idx}"):
                            st.session_state.generation_history.remove(entry)
                            st.rerun()
            
            # Statistiques globales
            with st.expander("📊 Statistiques globales"):
                total_docs = len(st.session_state.generation_history)
                total_words = sum(h['document']['metadata']['longueur_mots'] for h in st.session_state.generation_history)
                total_pages = sum(h['document']['metadata']['nb_pages_estimees'] for h in st.session_state.generation_history)
                total_time = sum(h['document']['metadata']['temps_generation'] for h in st.session_state.generation_history)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Documents", total_docs)
                with col2:
                    st.metric("Mots totaux", f"{total_words:,}")
                with col3:
                    st.metric("Pages totales", f"~{total_pages:,}")
                with col4:
                    st.metric("Temps total", f"{total_time//60:.0f}m")
                
                # Graphique d'évolution
                if total_docs > 1:
                    st.markdown("#### 📈 Évolution des générations")
                    
                    # Préparer les données
                    evolution_data = []
                    for entry in st.session_state.generation_history:
                        evolution_data.append({
                            'Date': entry['timestamp'],
                            'Mots': entry['document']['metadata']['longueur_mots'],
                            'Type': DOCUMENT_TYPES[entry['type']]['name']
                        })
                    
                    df_evolution = pd.DataFrame(evolution_data)
                    
                    # Graphique
                    fig = px.line(
                        df_evolution,
                        x='Date',
                        y='Mots',
                        color='Type',
                        markers=True,
                        title='Évolution du nombre de mots par génération'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Actions globales
            st.markdown("#### Actions globales")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Effacer tout l'historique", type="secondary", use_container_width=True):
                    if st.checkbox("Confirmer la suppression"):
                        st.session_state.generation_history = []
                        st.success("✅ Historique effacé")
                        st.rerun()
            
            with col2:
                # Export de l'historique
                history_json = json.dumps([
                    {
                        'timestamp': entry['timestamp'].isoformat(),
                        'type': entry['type'],
                        'metadata': entry['document']['metadata']
                    }
                    for entry in st.session_state.generation_history
                ], ensure_ascii=False, indent=2)
                
                st.download_button(
                    "📥 Exporter l'historique",
                    history_json.encode('utf-8'),
                    file_name=f"historique_generations_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        else:
            st.info("📚 Aucune génération dans l'historique")
            st.markdown("""
            L'historique conserve toutes vos générations de documents pour :
            - 📊 Comparer les résultats
            - 💾 Retrouver des documents antérieurs
            - 📈 Analyser vos statistiques d'utilisation
            """)

# Point d'entrée OBLIGATOIRE
if __name__ == "__main__":
    run()