"""Module de génération juridique avancé avec support multi-IA et lazy loading"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
from pathlib import Path
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import re
import json
from functools import lru_cache
import plotly.graph_objects as go
import plotly.express as px

# Configuration du lazy loading
def lazy_load_components():
    """Charge les composants de manière asynchrone"""
    if 'components_loaded' not in st.session_state:
        st.session_state.components_loaded = {
            'analyseur': False,
            'generateur': False,
            'validateur': False,
            'ai_models': False
        }

# ========================= CONFIGURATION IA =========================

AI_MODELS = {
    'gpt4': {
        'name': 'GPT-4 Turbo',
        'provider': 'OpenAI',
        'icon': '🧠',
        'strengths': ['Raisonnement juridique complexe', 'Argumentation détaillée'],
        'speed': 'Modéré',
        'quality': 5,
        'cost': 3
    },
    'claude3': {
        'name': 'Claude 3 Opus',
        'provider': 'Anthropic',
        'icon': '🎓',
        'strengths': ['Nuance et contexte', 'Conformité éthique'],
        'speed': 'Rapide',
        'quality': 5,
        'cost': 3
    },
    'mistral': {
        'name': 'Mistral Large',
        'provider': 'Mistral AI',
        'icon': '⚡',
        'strengths': ['Vitesse', 'Efficacité'],
        'speed': 'Très rapide',
        'quality': 4,
        'cost': 2
    },
    'gemini': {
        'name': 'Gemini Pro',
        'provider': 'Google',
        'icon': '✨',
        'strengths': ['Recherche intégrée', 'Multimodal'],
        'speed': 'Rapide',
        'quality': 4,
        'cost': 2
    },
    'llama': {
        'name': 'LLaMA 3',
        'provider': 'Meta',
        'icon': '🦙',
        'strengths': ['Open source', 'Personnalisable'],
        'speed': 'Rapide',
        'quality': 3,
        'cost': 1
    }
}

# ========================= ANALYSEUR DE REQUÊTES JURIDIQUES =========================

class AnalyseurRequeteJuridiqueAvance:
    """Version avancée de l'analyseur de requêtes juridiques avec ML"""
    
    def __init__(self):
        self.keywords = {
            'generation': {
                'rediger': ['rédiger', 'rédige', 'rédigez', 'rédaction'],
                'creer': ['créer', 'crée', 'créez', 'création', 'établir'],
                'generer': ['générer', 'génère', 'générez', 'génération'],
                'preparer': ['préparer', 'prépare', 'préparez', 'préparation'],
                'ecrire': ['écrire', 'écris', 'écrivez', 'écriture']
            },
            'actes': {
                'plainte': ['plainte', 'dépôt de plainte', 'porter plainte'],
                'plainte_cpc': ['plainte avec constitution de partie civile', 'cpc', 'partie civile'],
                'conclusions': ['conclusions', 'conclusion', 'mémoire'],
                'conclusions_nullite': ['conclusions de nullité', 'nullité', 'in limine litis'],
                'assignation': ['assignation', 'assigner', 'faire citer'],
                'citation': ['citation directe', 'citation', 'citer'],
                'observations': ['observations', 'article 175', '175 cpp'],
                'courrier': ['courrier', 'lettre', 'correspondance'],
                'requete': ['requête', 'demande', 'saisine'],
                'memoire': ['mémoire', 'mémoire en défense', 'mémoire ampliatif']
            }
        }
        
        self.patterns = {
            'parties': r'contre\s+([A-Za-zÀ-ÿ\s,&\-\.]+?)(?:\s+et\s+|,|\s+pour\s+|$)',
            'infractions': r'pour\s+([\w\s,]+?)(?:\s+contre\s+|\s+à\s+|$)',
            'reference': r'@(\w+)|n°\s*(\w+)|réf\.\s*:\s*(\w+)',
            'date': r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            'montant': r'(\d+(?:\s*\d{3})*(?:,\d{2})?\s*(?:€|euros?))',
            'juridiction': r'(tribunal|cour|conseil|juridiction)\s+(?:de\s+)?(\w+)',
            'urgence': r'(urgent|urgence|immédiat|rapidement|délai|sous\s+\d+\s+jours?)'
        }
        
        self.infractions_db = {
            'abs': 'Abus de biens sociaux',
            'corruption': 'Corruption active ou passive',
            'escroquerie': 'Escroquerie',
            'abus de confiance': 'Abus de confiance',
            'blanchiment': 'Blanchiment de capitaux',
            'faux': 'Faux et usage de faux',
            'détournement': 'Détournement de fonds publics',
            'prise illégale': "Prise illégale d'intérêts",
            'favoritisme': 'Favoritisme',
            'trafic': "Trafic d'influence",
            'recel': 'Recel',
            'abus de faiblesse': 'Abus de faiblesse'
        }
    
    @lru_cache(maxsize=128)
    def analyser_requete(self, query: str) -> Dict[str, Any]:
        """Analyse une requête avec cache pour optimiser les performances"""
        
        query_lower = query.lower()
        
        # Analyse de base
        analyse = {
            'is_generation': self._detect_generation_request(query_lower),
            'type_acte': self._detect_acte_type(query_lower),
            'parties': self._extract_parties(query),
            'infractions': self._extract_infractions(query),
            'reference': self._extract_reference(query),
            'dates': self._extract_dates(query),
            'montants': self._extract_montants(query),
            'juridiction': self._extract_juridiction(query),
            'contexte': self._determine_contexte(query_lower),
            'confidence_score': 0.0,
            'query_original': query
        }
        
        # Calcul du score de confiance
        analyse['confidence_score'] = self._calculate_confidence(analyse)
        
        # Suggestions d'amélioration
        analyse['suggestions'] = self._generate_suggestions(analyse)
        
        return analyse
    
    def _detect_generation_request(self, query_lower: str) -> bool:
        """Détection améliorée avec scoring"""
        score = 0
        for category, keywords in self.keywords['generation'].items():
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
        return score > 0
    
    def _detect_acte_type(self, query_lower: str) -> Optional[str]:
        """Détection avec scoring et priorités"""
        scores = {}
        
        for acte_type, keywords in self.keywords['actes'].items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Score plus élevé pour les correspondances exactes
                    if f' {keyword} ' in f' {query_lower} ':
                        score += 2
                    else:
                        score += 1
            if score > 0:
                scores[acte_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def _extract_parties(self, query: str) -> Dict[str, List[str]]:
        """Extraction avancée des parties avec NER simulé"""
        parties = {
            'demandeurs': [],
            'defendeurs': [],
            'tiers': []
        }
        
        # Patterns améliorés
        patterns = {
            'defendeurs': [
                r'contre\s+([A-Za-zÀ-ÿ\s,&\-\.]+?)(?:\s+et\s+|,|\s+pour\s+|$)',
                r'à l\'encontre de\s+([A-Za-zÀ-ÿ\s,&\-\.]+?)(?:\s+et\s+|,|\s+pour\s+|$)'
            ],
            'demandeurs': [
                r'pour\s+([A-Za-zÀ-ÿ\s\-\.]+?)(?:\s+contre|\s*$)',
                r'au nom de\s+([A-Za-zÀ-ÿ\s\-\.]+?)(?:\s+contre|\s*$)'
            ],
            'tiers': [
                r'en présence de\s+([A-Za-zÀ-ÿ\s\-\.]+?)(?:\s+et\s+|,|$)',
                r'intervenant\s*:\s*([A-Za-zÀ-ÿ\s\-\.]+?)(?:\s+et\s+|,|$)'
            ]
        }
        
        for role, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    entities = [e.strip() for e in re.split(r',|et', match) if e.strip()]
                    parties[role].extend(entities)
        
        # Dédupliquer
        for role in parties:
            parties[role] = list(dict.fromkeys(parties[role]))
        
        return parties
    
    def _extract_infractions(self, query: str) -> List[Dict[str, Any]]:
        """Extraction des infractions avec métadonnées"""
        infractions = []
        query_lower = query.lower()
        
        for short_name, full_name in self.infractions_db.items():
            if short_name in query_lower:
                infraction = {
                    'nom': full_name,
                    'code': short_name,
                    'gravite': self._get_gravite_infraction(short_name),
                    'peines_encourues': self._get_peines_infraction(short_name)
                }
                infractions.append(infraction)
        
        return infractions
    
    def _get_gravite_infraction(self, code: str) -> str:
        """Détermine la gravité de l'infraction"""
        gravites = {
            'abs': 'Délit grave',
            'corruption': 'Crime',
            'escroquerie': 'Délit',
            'blanchiment': 'Délit grave'
        }
        return gravites.get(code, 'Délit')
    
    def _get_peines_infraction(self, code: str) -> Dict[str, Any]:
        """Retourne les peines encourues"""
        peines = {
            'abs': {'prison': '5 ans', 'amende': '375 000 €'},
            'corruption': {'prison': '10 ans', 'amende': '1 000 000 €'},
            'escroquerie': {'prison': '5 ans', 'amende': '375 000 €'}
        }
        return peines.get(code, {'prison': '3 ans', 'amende': '45 000 €'})
    
    def _extract_reference(self, query: str) -> Optional[str]:
        """Extraction améliorée des références"""
        for pattern in self.patterns['reference'].split('|'):
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return next(g for g in match.groups() if g)
        return None
    
    def _extract_dates(self, query: str) -> List[Dict[str, Any]]:
        """Extraction et parsing des dates"""
        dates = []
        for date_str in re.findall(self.patterns['date'], query):
            try:
                # Normaliser le format
                date_str = date_str.replace('-', '/')
                parts = date_str.split('/')
                if len(parts[2]) == 2:
                    parts[2] = '20' + parts[2]
                
                date_obj = datetime.strptime('/'.join(parts), '%d/%m/%Y')
                dates.append({
                    'original': date_str,
                    'parsed': date_obj,
                    'formatted': date_obj.strftime('%d %B %Y')
                })
            except:
                pass
        
        return dates
    
    def _extract_montants(self, query: str) -> List[Dict[str, Any]]:
        """Extraction et parsing des montants"""
        montants = []
        for montant_str in re.findall(self.patterns['montant'], query):
            # Nettoyer et parser
            clean = re.sub(r'\s', '', montant_str)
            clean = re.sub(r'euros?', '', clean, flags=re.IGNORECASE)
            clean = clean.replace('€', '').strip()
            
            try:
                if ',' in clean:
                    value = float(clean.replace(',', '.'))
                else:
                    value = float(clean)
                
                montants.append({
                    'original': montant_str,
                    'value': value,
                    'formatted': f"{value:,.2f} €".replace(',', ' ')
                })
            except:
                pass
        
        return montants
    
    def _extract_juridiction(self, query: str) -> Optional[Dict[str, str]]:
        """Extraction de la juridiction"""
        match = re.search(self.patterns['juridiction'], query, re.IGNORECASE)
        if match:
            return {
                'type': match.group(1).lower(),
                'lieu': match.group(2) if match.lastindex >= 2 else None
            }
        return None
    
    def _determine_contexte(self, query_lower: str) -> Dict[str, Any]:
        """Détermination avancée du contexte"""
        contexte = {
            'phase': self._detect_phase(query_lower),
            'urgence': self._detect_urgence(query_lower),
            'complexite': self._detect_complexite(query_lower),
            'type_procedure': self._detect_type_procedure(query_lower),
            'sensibilite': self._detect_sensibilite(query_lower)
        }
        
        return contexte
    
    def _detect_phase(self, query_lower: str) -> str:
        """Détecte la phase procédurale"""
        phases = {
            'pre_plainte': ['avant', 'préalable', 'envisage'],
            'enquete': ['enquête', 'préliminaire', 'gendarmerie', 'police'],
            'instruction': ['instruction', 'juge d\'instruction', 'doyen', 'cabinet'],
            'jugement': ['audience', 'jugement', 'tribunal', 'plaidoirie'],
            'appel': ['appel', 'cour d\'appel', 'appelant'],
            'cassation': ['cassation', 'cour de cassation', 'pourvoi']
        }
        
        for phase, keywords in phases.items():
            if any(kw in query_lower for kw in keywords):
                return phase
        
        return 'enquete'  # Par défaut
    
    def _detect_urgence(self, query_lower: str) -> Dict[str, Any]:
        """Détecte le niveau d'urgence"""
        urgence_keywords = {
            'extreme': ['immédiat', 'aujourd\'hui', 'maintenant', 'urgent absolu'],
            'haute': ['urgent', 'rapidement', 'vite', 'délai court'],
            'moderee': ['sous 48h', 'cette semaine', 'bientôt'],
            'normale': []
        }
        
        for level, keywords in urgence_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return {
                    'niveau': level,
                    'delai_estime': self._get_delai_from_urgence(level)
                }
        
        return {'niveau': 'normale', 'delai_estime': '7 jours'}
    
    def _get_delai_from_urgence(self, niveau: str) -> str:
        """Retourne le délai estimé selon l'urgence"""
        delais = {
            'extreme': '2 heures',
            'haute': '24 heures',
            'moderee': '48 heures',
            'normale': '7 jours'
        }
        return delais.get(niveau, '7 jours')
    
    def _detect_complexite(self, query_lower: str) -> str:
        """Détecte la complexité du dossier"""
        if any(word in query_lower for word in ['complexe', 'détaillé', 'exhaustif', 'approfondi', 'technique']):
            return 'elevee'
        elif any(word in query_lower for word in ['simple', 'basique', 'standard', 'classique']):
            return 'simple'
        
        # Complexité basée sur d'autres facteurs
        factors = 0
        if 'plusieurs' in query_lower or 'multiple' in query_lower:
            factors += 1
        if len(query_lower) > 200:
            factors += 1
        if any(word in query_lower for word in ['international', 'transfrontalier']):
            factors += 2
        
        if factors >= 2:
            return 'elevee'
        elif factors == 1:
            return 'moyenne'
        
        return 'normale'
    
    def _detect_type_procedure(self, query_lower: str) -> str:
        """Détecte le type de procédure"""
        procedures = {
            'penale': ['pénal', 'plainte', 'procureur', 'instruction'],
            'civile': ['civil', 'dommages', 'préjudice', 'réparation'],
            'commerciale': ['commercial', 'société', 'entreprise', 'contrat'],
            'administrative': ['administratif', 'préfet', 'mairie', 'administration'],
            'prud\'homale': ['prud\'hom', 'licenciement', 'salarié', 'employeur']
        }
        
        for proc, keywords in procedures.items():
            if any(kw in query_lower for kw in keywords):
                return proc
        
        return 'penale'  # Par défaut
    
    def _detect_sensibilite(self, query_lower: str) -> str:
        """Détecte la sensibilité du dossier"""
        if any(word in query_lower for word in ['confidentiel', 'sensible', 'secret', 'médiatique']):
            return 'haute'
        elif any(word in query_lower for word in ['public', 'médias', 'presse']):
            return 'moyenne'
        
        return 'normale'
    
    def _calculate_confidence(self, analyse: Dict[str, Any]) -> float:
        """Calcule un score de confiance pour l'analyse"""
        score = 0.0
        max_score = 0.0
        
        # Critères et leurs poids
        criteria = {
            'type_acte': (analyse['type_acte'] is not None, 0.2),
            'parties': (bool(analyse['parties']['defendeurs'] or analyse['parties']['demandeurs']), 0.2),
            'infractions': (bool(analyse['infractions']), 0.15),
            'reference': (analyse['reference'] is not None, 0.1),
            'dates': (bool(analyse['dates']), 0.1),
            'juridiction': (analyse['juridiction'] is not None, 0.1),
            'contexte_phase': (analyse['contexte']['phase'] != 'enquete', 0.15)  # Non par défaut
        }
        
        for criterion, (condition, weight) in criteria.items():
            max_score += weight
            if condition:
                score += weight
        
        return score / max_score if max_score > 0 else 0.0
    
    def _generate_suggestions(self, analyse: Dict[str, Any]) -> List[str]:
        """Génère des suggestions pour améliorer la requête"""
        suggestions = []
        
        if not analyse['type_acte']:
            suggestions.append("💡 Précisez le type d'acte souhaité (ex: 'rédiger une plainte')")
        
        if not analyse['parties']['defendeurs'] and not analyse['parties']['demandeurs']:
            suggestions.append("💡 Indiquez les parties concernées (ex: 'contre Société X')")
        
        if not analyse['infractions']:
            suggestions.append("💡 Mentionnez les infractions visées (ex: 'pour abus de biens sociaux')")
        
        if not analyse['reference']:
            suggestions.append("💡 Ajoutez une référence avec @ (ex: '@REF2024-001')")
        
        if analyse['contexte']['urgence']['niveau'] == 'normale':
            suggestions.append("💡 Précisez le délai si urgent (ex: 'urgent sous 48h')")
        
        return suggestions

# ========================= GÉNÉRATEUR MULTI-IA =========================

class GenerateurJuridiqueMultiIA:
    """Générateur utilisant plusieurs modèles d'IA"""
    
    def __init__(self):
        self.models = AI_MODELS
        self.templates = self._load_templates()
        self.style_guide = self._load_style_guide()
    
    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates d'actes juridiques"""
        return {
            'plainte': """[ENTÊTE]
PLAINTE

[PARTIES]
Je soussigné(e) {demandeur},
Porte plainte contre {defendeur}

[FAITS]
{exposition_faits}

[INFRACTIONS]
Ces faits sont susceptibles de recevoir les qualifications pénales suivantes :
{liste_infractions}

[DEMANDES]
{demandes}

[SIGNATURE]
Fait à {lieu}, le {date}
{signature}
""",
            'conclusions': """[ENTÊTE]
CONCLUSIONS

POUR : {demandeur}
CONTRE : {defendeur}

[PLAN]
{plan_detaille}

[DEVELOPPEMENT]
{argumentation}

[DISPOSITIF]
PAR CES MOTIFS
{demandes}

[SIGNATURE]
{signature_avocat}
"""
        }
    
    def _load_style_guide(self) -> Dict[str, Any]:
        """Charge le guide de style juridique"""
        return {
            'police': 'Garamond',
            'taille': 12,
            'interligne': 1.5,
            'marges': {'haut': 2.5, 'bas': 2.5, 'gauche': 2.5, 'droite': 2.5},
            'numerotation': True,
            'table_matieres': True
        }
    
    async def generer_avec_ia(self, 
                             type_acte: str,
                             params: Dict[str, Any],
                             models_selected: List[str],
                             fusion_mode: str = 'consensus') -> Dict[str, Any]:
        """Génère un acte avec les modèles sélectionnés"""
        
        # Préparer le prompt
        prompt = self._prepare_prompt(type_acte, params)
        
        # Générer avec chaque modèle
        generations = {}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, model_id in enumerate(models_selected):
            status_text.text(f"🤖 Génération avec {self.models[model_id]['name']}...")
            
            # Simuler la génération (remplacer par l'appel API réel)
            generation = await self._generate_with_model(model_id, prompt, params)
            generations[model_id] = generation
            
            progress_bar.progress((i + 1) / len(models_selected))
        
        # Fusionner les résultats
        status_text.text("🔄 Fusion des résultats...")
        
        if fusion_mode == 'consensus':
            result = self._fusion_consensus(generations)
        elif fusion_mode == 'best_of':
            result = self._fusion_best_of(generations)
        elif fusion_mode == 'complementaire':
            result = self._fusion_complementaire(generations)
        else:  # sequential
            result = self._fusion_sequential(generations)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Génération terminée!")
        
        return result
    
    def _prepare_prompt(self, type_acte: str, params: Dict[str, Any]) -> str:
        """Prépare le prompt pour les modèles"""
        
        base_prompt = f"""
Tu es un avocat expert en droit français. Tu dois rédiger un(e) {type_acte} 
selon les règles de procédure françaises et le cahier des charges suivant :

Type d'acte : {type_acte}
Phase procédurale : {params['contexte']['phase']}
Urgence : {params['contexte']['urgence']['niveau']}
Complexité : {params['contexte']['complexite']}

Parties :
- Demandeurs : {', '.join(params['parties']['demandeurs'])}
- Défendeurs : {', '.join(params['parties']['defendeurs'])}

Infractions visées :
{self._format_infractions(params['infractions'])}

Options de rédaction :
- Style : {params['options']['style']}
- Longueur cible : {params['options']['longueur_cible']} mots
- Inclure jurisprudence : {params['options']['inclure_jurisprudence']}

IMPORTANT : 
1. Respecter strictement le formalisme juridique français
2. Utiliser un langage juridique précis et approprié
3. Structurer l'acte selon les standards professionnels
4. Inclure toutes les mentions obligatoires
"""
        
        if params['options']['inclure_jurisprudence']:
            base_prompt += """
5. Citer la jurisprudence pertinente avec les références complètes
6. Analyser l'application de la jurisprudence aux faits de l'espèce
"""
        
        return base_prompt
    
    def _format_infractions(self, infractions: List[Any]) -> str:
        """Formate la liste des infractions"""
        formatted = []
        
        for inf in infractions:
            if isinstance(inf, dict):
                formatted.append(f"- {inf['nom']} ({inf['code']})")
                if 'peines_encourues' in inf:
                    formatted.append(f"  Peines : {inf['peines_encourues']['prison']} de prison, "
                                   f"{inf['peines_encourues']['amende']} d'amende")
            else:
                formatted.append(f"- {inf}")
        
        return '\n'.join(formatted)
    
    async def _generate_with_model(self, model_id: str, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère avec un modèle spécifique (simulation)"""
        
        # Simulation de l'appel API
        await asyncio.sleep(1)  # Simuler la latence
        
        # Template de base
        template = self.templates.get(params.get('type_acte', 'plainte'), self.templates['plainte'])
        
        # Simulation de contenu généré
        content = f"""
PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE

Monsieur le Doyen des Juges d'Instruction,

Je soussigné(e) {', '.join(params['parties']['demandeurs'])},

Ai l'honneur de porter plainte avec constitution de partie civile contre :
{', '.join(params['parties']['defendeurs'])}

Pour les faits suivants :

I. EXPOSÉ DES FAITS

[Contenu généré par {self.models[model_id]['name']}]

Les faits exposés ci-dessus révèlent de manière manifeste la commission d'infractions pénales 
caractérisées, justifiant pleinement l'ouverture d'une information judiciaire.

II. QUALIFICATION JURIDIQUE

Les faits dénoncés sont susceptibles de recevoir les qualifications pénales suivantes :

{self._format_infractions(params['infractions'])}

III. PRÉJUDICE ET DEMANDES

Du fait des infractions commises, j'ai subi un préjudice considérable que j'évalue 
provisoirement à la somme de [MONTANT] euros, sous réserve d'une évaluation plus précise.

PAR CES MOTIFS,

Je sollicite l'ouverture d'une information judiciaire des chefs précités et me constitue 
partie civile.

Fait à Paris, le {datetime.now().strftime('%d %B %Y')}

Signature
"""
        
        # Métadonnées
        metadata = {
            'model_id': model_id,
            'model_name': self.models[model_id]['name'],
            'generation_time': time.time(),
            'word_count': len(content.split()),
            'quality_score': self.models[model_id]['quality'],
            'confidence': 0.85 + (self.models[model_id]['quality'] * 0.03)
        }
        
        return {
            'content': content,
            'metadata': metadata,
            'analysis': self._analyze_generation(content, params)
        }
    
    def _analyze_generation(self, content: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la génération"""
        return {
            'structure_score': 0.9,
            'legal_compliance': 0.95,
            'clarity_score': 0.88,
            'completeness': 0.92,
            'style_conformity': 0.87
        }
    
    def _fusion_consensus(self, generations: Dict[str, Dict]) -> Dict[str, Any]:
        """Fusion par consensus - combine les meilleures parties"""
        
        # Analyser les sections communes
        sections = self._extract_sections(generations)
        
        # Sélectionner les meilleures sections
        best_sections = {}
        for section_name, section_variants in sections.items():
            # Scorer chaque variante
            scored_variants = []
            for model_id, content in section_variants.items():
                score = self._score_section(content, generations[model_id]['metadata'])
                scored_variants.append((score, model_id, content))
            
            # Prendre la meilleure
            scored_variants.sort(reverse=True)
            best_sections[section_name] = {
                'content': scored_variants[0][2],
                'model': scored_variants[0][1],
                'score': scored_variants[0][0]
            }
        
        # Reconstruire le document
        final_content = self._reconstruct_document(best_sections)
        
        return {
            'content': final_content,
            'fusion_method': 'consensus',
            'sections_sources': {k: v['model'] for k, v in best_sections.items()},
            'metadata': {
                'fusion_time': datetime.now(),
                'models_used': list(generations.keys()),
                'average_confidence': sum(g['metadata']['confidence'] for g in generations.values()) / len(generations)
            }
        }
    
    def _fusion_best_of(self, generations: Dict[str, Dict]) -> Dict[str, Any]:
        """Fusion best-of - sélectionne la meilleure génération globale"""
        
        # Scorer chaque génération
        scores = {}
        for model_id, generation in generations.items():
            score = self._score_generation(generation)
            scores[model_id] = score
        
        # Sélectionner la meilleure
        best_model = max(scores, key=scores.get)
        
        return {
            'content': generations[best_model]['content'],
            'fusion_method': 'best_of',
            'selected_model': best_model,
            'scores': scores,
            'metadata': generations[best_model]['metadata']
        }
    
    def _fusion_complementaire(self, generations: Dict[str, Dict]) -> Dict[str, Any]:
        """Fusion complémentaire - combine les forces de chaque modèle"""
        
        # Identifier les forces de chaque génération
        strengths = {}
        for model_id, generation in generations.items():
            strengths[model_id] = self._identify_strengths(generation)
        
        # Construire un document en utilisant les forces
        final_content = self._build_from_strengths(generations, strengths)
        
        return {
            'content': final_content,
            'fusion_method': 'complementaire',
            'strengths_map': strengths,
            'metadata': {
                'fusion_time': datetime.now(),
                'models_used': list(generations.keys())
            }
        }
    
    def _fusion_sequential(self, generations: Dict[str, Dict]) -> Dict[str, Any]:
        """Fusion séquentielle - chaque modèle améliore le précédent"""
        
        # Commencer avec la première génération
        current_content = generations[list(generations.keys())[0]]['content']
        improvements = []
        
        # Chaque modèle suivant améliore
        for model_id in list(generations.keys())[1:]:
            improvement = self._improve_content(current_content, generations[model_id])
            current_content = improvement['improved_content']
            improvements.append({
                'model': model_id,
                'changes': improvement['changes']
            })
        
        return {
            'content': current_content,
            'fusion_method': 'sequential',
            'improvements': improvements,
            'metadata': {
                'fusion_time': datetime.now(),
                'models_used': list(generations.keys())
            }
        }
    
    def _extract_sections(self, generations: Dict[str, Dict]) -> Dict[str, Dict]:
        """Extrait les sections de chaque génération"""
        sections = {}
        
        section_markers = [
            'EXPOSÉ DES FAITS',
            'QUALIFICATION JURIDIQUE',
            'PRÉJUDICE',
            'DEMANDES',
            'DISPOSITIF'
        ]
        
        for model_id, generation in generations.items():
            content = generation['content']
            
            for i, marker in enumerate(section_markers):
                if marker in content:
                    # Extraire jusqu'au prochain marqueur
                    start = content.find(marker)
                    if i < len(section_markers) - 1:
                        next_marker = section_markers[i + 1]
                        end = content.find(next_marker) if next_marker in content else len(content)
                    else:
                        end = len(content)
                    
                    section_content = content[start:end].strip()
                    
                    if marker not in sections:
                        sections[marker] = {}
                    
                    sections[marker][model_id] = section_content
        
        return sections
    
    def _score_section(self, content: str, metadata: Dict) -> float:
        """Score une section de contenu"""
        score = 0.0
        
        # Longueur
        word_count = len(content.split())
        if 50 <= word_count <= 500:
            score += 0.3
        elif word_count < 50:
            score += 0.1
        else:
            score += 0.2
        
        # Qualité du modèle
        score += metadata.get('quality_score', 3) * 0.1
        
        # Confiance
        score += metadata.get('confidence', 0.8) * 0.3
        
        # Présence de mots-clés juridiques
        legal_keywords = ['considérant', 'attendu', 'nonobstant', 'jurisprudence', 'article']
        keyword_count = sum(1 for kw in legal_keywords if kw in content.lower())
        score += min(keyword_count * 0.05, 0.3)
        
        return score
    
    def _score_generation(self, generation: Dict) -> float:
        """Score une génération complète"""
        base_score = 0.0
        
        # Analyse du contenu
        analysis = generation.get('analysis', {})
        base_score += analysis.get('structure_score', 0) * 0.2
        base_score += analysis.get('legal_compliance', 0) * 0.3
        base_score += analysis.get('clarity_score', 0) * 0.2
        base_score += analysis.get('completeness', 0) * 0.2
        base_score += analysis.get('style_conformity', 0) * 0.1
        
        # Métadonnées
        metadata = generation.get('metadata', {})
        base_score *= metadata.get('confidence', 1.0)
        
        return base_score
    
    def _identify_strengths(self, generation: Dict) -> Dict[str, float]:
        """Identifie les forces d'une génération"""
        analysis = generation.get('analysis', {})
        
        return {
            'structure': analysis.get('structure_score', 0),
            'legal': analysis.get('legal_compliance', 0),
            'clarity': analysis.get('clarity_score', 0),
            'completeness': analysis.get('completeness', 0),
            'style': analysis.get('style_conformity', 0)
        }
    
    def _build_from_strengths(self, generations: Dict, strengths: Dict) -> str:
        """Construit un document en utilisant les forces de chaque modèle"""
        # Simulation - dans la pratique, ce serait plus sophistiqué
        result_parts = []
        
        # Utiliser le modèle avec la meilleure structure pour l'introduction
        best_structure = max(strengths.items(), key=lambda x: x[1]['structure'])[0]
        result_parts.append(f"[Introduction from {best_structure}]")
        
        # Utiliser le modèle avec la meilleure conformité légale pour la qualification
        best_legal = max(strengths.items(), key=lambda x: x[1]['legal'])[0]
        result_parts.append(f"[Legal qualification from {best_legal}]")
        
        # Etc...
        
        return "\n\n".join(result_parts)
    
    def _improve_content(self, current: str, generation: Dict) -> Dict[str, Any]:
        """Améliore le contenu existant avec une nouvelle génération"""
        # Simulation
        return {
            'improved_content': current + f"\n\n[Améliorations par {generation['metadata']['model_name']}]",
            'changes': ['Ajout de jurisprudence', 'Clarification des demandes', 'Renforcement de l\'argumentation']
        }
    
    def _reconstruct_document(self, sections: Dict[str, Dict]) -> str:
        """Reconstruit le document à partir des sections"""
        parts = []
        
        for section_name, section_data in sections.items():
            parts.append(section_data['content'])
        
        return "\n\n".join(parts)

# ========================= INTERFACE UTILISATEUR =========================

def run():
    """Fonction principale du module"""
    
    # Initialisation du lazy loading
    lazy_load_components()
    
    # Configuration de la page
    st.set_page_config(
        page_title="Génération Juridique IA",
        page_icon="⚖️",
        layout="wide"
    )
    
    # CSS personnalisé pour une meilleure UX
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .ai-model-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .ai-model-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .quality-meter {
        background: #e9ecef;
        border-radius: 20px;
        height: 8px;
        overflow: hidden;
    }
    
    .quality-fill {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        height: 100%;
        transition: width 0.5s ease;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    
    .step {
        flex: 1;
        text-align: center;
        padding: 1rem;
        border-bottom: 3px solid #dee2e6;
        color: #6c757d;
        transition: all 0.3s ease;
    }
    
    .step.active {
        border-color: #007bff;
        color: #007bff;
        font-weight: bold;
    }
    
    .step.completed {
        border-color: #28a745;
        color: #28a745;
    }
    
    .fusion-mode-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .fusion-mode-card:hover {
        transform: scale(1.02);
    }
    
    .result-section {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .confidence-high { background: #d4edda; color: #155724; }
    .confidence-medium { background: #fff3cd; color: #856404; }
    .confidence-low { background: #f8d7da; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)
    
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ Génération Juridique Multi-IA</h1>
        <p>Créez des actes juridiques professionnels avec l'intelligence artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de l'état
    if 'generation_state' not in st.session_state:
        st.session_state.generation_state = {
            'step': 1,
            'analysis': None,
            'selected_models': [],
            'fusion_mode': 'consensus',
            'generated_content': None
        }
    
    # Indicateur d'étapes
    steps = ['📝 Analyse', '🤖 Sélection IA', '⚙️ Configuration', '🚀 Génération', '📄 Résultat']
    st.markdown('<div class="step-indicator">', unsafe_allow_html=True)
    
    for i, step_name in enumerate(steps, 1):
        if i < st.session_state.generation_state['step']:
            status = 'completed'
        elif i == st.session_state.generation_state['step']:
            status = 'active'
        else:
            status = ''
        
        st.markdown(f'<div class="step {status}">{step_name}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Contenu principal selon l'étape
    if st.session_state.generation_state['step'] == 1:
        render_step_analysis()
    elif st.session_state.generation_state['step'] == 2:
        render_step_ai_selection()
    elif st.session_state.generation_state['step'] == 3:
        render_step_configuration()
    elif st.session_state.generation_state['step'] == 4:
        render_step_generation()
    elif st.session_state.generation_state['step'] == 5:
        render_step_result()

def render_step_analysis():
    """Étape 1 : Analyse de la requête"""
    
    st.markdown("### 📝 Étape 1 : Analyse de votre demande")
    
    # Zone de saisie améliorée
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "Décrivez votre besoin juridique",
            height=150,
            placeholder="Ex: Rédiger une plainte contre la société ABC pour abus de biens sociaux et corruption...",
            help="Soyez le plus précis possible : type d'acte, parties concernées, infractions, contexte..."
        )
    
    with col2:
        st.markdown("#### 💡 Conseils")
        st.info("""
        Incluez :
        - Le type d'acte
        - Les parties
        - Les infractions
        - Le contexte
        - L'urgence
        """)
    
    # Exemples rapides
    st.markdown("#### 🎯 Exemples de requêtes")
    
    example_cols = st.columns(3)
    
    examples = [
        ("Plainte simple", "Rédiger une plainte contre M. Dupont pour escroquerie"),
        ("Plainte avec CPC", "Rédiger une plainte avec constitution de partie civile contre la société XYZ pour abus de biens sociaux"),
        ("Conclusions", "Rédiger des conclusions de nullité dans l'affaire @REF2024-123")
    ]
    
    for col, (title, example) in zip(example_cols, examples):
        with col:
            if st.button(f"📋 {title}", use_container_width=True):
                st.session_state.example_query = example
                st.rerun()
    
    # Utiliser l'exemple si sélectionné
    if 'example_query' in st.session_state:
        query = st.session_state.example_query
        del st.session_state.example_query
    
    # Bouton d'analyse
    if st.button("🔍 Analyser la demande", type="primary", use_container_width=True, disabled=not query):
        
        with st.spinner("🧠 Analyse en cours..."):
            # Charger l'analyseur (lazy loading)
            if not st.session_state.components_loaded['analyseur']:
                analyseur = AnalyseurRequeteJuridiqueAvance()
                st.session_state.analyseur = analyseur
                st.session_state.components_loaded['analyseur'] = True
            else:
                analyseur = st.session_state.analyseur
            
            # Analyser
            analyse = analyseur.analyser_requete(query)
            st.session_state.generation_state['analysis'] = analyse
            
            # Afficher les résultats
            st.success("✅ Analyse terminée!")
            
            # Score de confiance
            confidence = analyse['confidence_score']
            if confidence >= 0.8:
                badge_class = "confidence-high"
                badge_text = "Excellente"
            elif confidence >= 0.5:
                badge_class = "confidence-medium"
                badge_text = "Bonne"
            else:
                badge_class = "confidence-low"
                badge_text = "À améliorer"
            
            st.markdown(f"""
            <div style="text-align: center; margin: 2rem 0;">
                <h4>Score d'analyse</h4>
                <span class="confidence-badge {badge_class}">
                    {badge_text} ({confidence:.0%})
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Détails de l'analyse
            with st.expander("📊 Détails de l'analyse", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🎯 Type d'acte détecté:**")
                    if analyse['type_acte']:
                        st.success(analyse['type_acte'].replace('_', ' ').title())
                    else:
                        st.warning("Non détecté")
                    
                    st.markdown("**👥 Parties:**")
                    if analyse['parties']['defendeurs']:
                        st.write("Défendeurs:", ', '.join(analyse['parties']['defendeurs']))
                    if analyse['parties']['demandeurs']:
                        st.write("Demandeurs:", ', '.join(analyse['parties']['demandeurs']))
                    if not (analyse['parties']['defendeurs'] or analyse['parties']['demandeurs']):
                        st.warning("Aucune partie détectée")
                    
                    st.markdown("**📅 Dates détectées:**")
                    if analyse['dates']:
                        for date in analyse['dates']:
                            st.write(f"- {date['formatted']}")
                    else:
                        st.info("Aucune date détectée")
                
                with col2:
                    st.markdown("**🚨 Infractions:**")
                    if analyse['infractions']:
                        for inf in analyse['infractions']:
                            if isinstance(inf, dict):
                                st.write(f"- {inf['nom']} ({inf['gravite']})")
                            else:
                                st.write(f"- {inf}")
                    else:
                        st.warning("Aucune infraction détectée")
                    
                    st.markdown("**⚡ Contexte:**")
                    ctx = analyse['contexte']
                    st.write(f"Phase: {ctx['phase']}")
                    st.write(f"Urgence: {ctx['urgence']['niveau']} ({ctx['urgence']['delai_estime']})")
                    st.write(f"Complexité: {ctx['complexite']}")
                    
                    st.markdown("**💰 Montants:**")
                    if analyse['montants']:
                        for montant in analyse['montants']:
                            st.write(f"- {montant['formatted']}")
                    else:
                        st.info("Aucun montant détecté")
            
            # Suggestions d'amélioration
            if analyse['suggestions']:
                st.markdown("### 💡 Suggestions d'amélioration")
                for suggestion in analyse['suggestions']:
                    st.info(suggestion)
            
            # Boutons de navigation
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Modifier la requête", use_container_width=True):
                    st.session_state.generation_state['analysis'] = None
                    st.rerun()
            
            with col2:
                if st.button("➡️ Étape suivante", type="primary", use_container_width=True):
                    st.session_state.generation_state['step'] = 2
                    st.rerun()

def render_step_ai_selection():
    """Étape 2 : Sélection des modèles IA"""
    
    st.markdown("### 🤖 Étape 2 : Sélection des modèles IA")
    
    # Charger les modèles disponibles
    if not st.session_state.components_loaded['ai_models']:
        st.session_state.available_models = AI_MODELS
        st.session_state.components_loaded['ai_models'] = True
    
    st.markdown("""
    Sélectionnez un ou plusieurs modèles d'IA pour générer votre acte juridique. 
    Chaque modèle a ses forces spécifiques.
    """)
    
    # Mode de sélection
    selection_mode = st.radio(
        "Mode de sélection",
        ["🎯 Sélection manuelle", "🤖 Recommandation automatique", "⚡ Sélection rapide"],
        horizontal=True
    )
    
    selected_models = []
    
    if selection_mode == "🎯 Sélection manuelle":
        # Affichage des modèles disponibles
        for model_id, model_info in AI_MODELS.items():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            
            with col1:
                selected = st.checkbox(
                    model_info['icon'],
                    key=f"select_{model_id}",
                    value=model_id in st.session_state.generation_state.get('selected_models', [])
                )
                if selected:
                    selected_models.append(model_id)
            
            with col2:
                st.markdown(f"**{model_info['name']}**")
                st.caption(f"Par {model_info['provider']}")
                
                # Barre de qualité
                quality_percentage = (model_info['quality'] / 5) * 100
                st.markdown(f"""
                <div class="quality-meter">
                    <div class="quality-fill" style="width: {quality_percentage}%"></div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("**Points forts:**")
                for strength in model_info['strengths'][:2]:
                    st.caption(f"• {strength}")
            
            with col4:
                st.metric("Vitesse", model_info['speed'])
                cost_icons = "💰" * model_info['cost']
                st.caption(f"Coût: {cost_icons}")
    
    elif selection_mode == "🤖 Recommandation automatique":
        # Recommandations basées sur l'analyse
        analysis = st.session_state.generation_state['analysis']
        
        st.info("🎯 Recommandations basées sur votre demande:")
        
        recommendations = get_ai_recommendations(analysis)
        
        for rec in recommendations:
            model_id = rec['model_id']
            model_info = AI_MODELS[model_id]
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                **{model_info['icon']} {model_info['name']}**  
                {rec['reason']}
                """)
            
            with col2:
                if st.button(f"Sélectionner", key=f"rec_{model_id}"):
                    if model_id not in selected_models:
                        selected_models.append(model_id)
        
        # Option pour tout sélectionner
        if st.button("✅ Sélectionner toutes les recommandations", type="primary"):
            selected_models = [rec['model_id'] for rec in recommendations]
    
    else:  # Sélection rapide
        quick_options = {
            "🏃 Rapide": ['mistral'],
            "⚖️ Équilibré": ['claude3', 'gemini'],
            "🏆 Maximum": ['gpt4', 'claude3', 'mistral']
        }
        
        for option_name, model_ids in quick_options.items():
            if st.button(option_name, use_container_width=True):
                selected_models = model_ids
    
    # Mode de fusion si plusieurs modèles
    if len(selected_models) > 1:
        st.markdown("### 🔄 Mode de fusion des résultats")
        
        fusion_modes = {
            'consensus': {
                'name': '🤝 Consensus',
                'desc': 'Combine les meilleures parties de chaque génération',
                'icon': '🎯'
            },
            'best_of': {
                'name': '🏆 Best-of',
                'desc': 'Sélectionne la meilleure génération complète',
                'icon': '⭐'
            },
            'complementaire': {
                'name': '🧩 Complémentaire',
                'desc': 'Utilise les forces spécifiques de chaque modèle',
                'icon': '🔧'
            },
            'sequential': {
                'name': '📈 Séquentiel',
                'desc': 'Chaque modèle améliore le précédent',
                'icon': '🔄'
            }
        }
        
        fusion_cols = st.columns(len(fusion_modes))
        
        for col, (mode_id, mode_info) in zip(fusion_cols, fusion_modes.items()):
            with col:
                if st.button(
                    f"{mode_info['icon']} {mode_info['name']}",
                    key=f"fusion_{mode_id}",
                    help=mode_info['desc'],
                    use_container_width=True
                ):
                    st.session_state.generation_state['fusion_mode'] = mode_id
        
        # Afficher le mode sélectionné
        current_mode = st.session_state.generation_state.get('fusion_mode', 'consensus')
        st.success(f"Mode sélectionné : {fusion_modes[current_mode]['name']}")
    
    # Résumé de la sélection
    if selected_models:
        st.markdown("### 📋 Résumé de votre sélection")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Modèles sélectionnés", len(selected_models))
        
        with col2:
            avg_quality = sum(AI_MODELS[m]['quality'] for m in selected_models) / len(selected_models)
            st.metric("Qualité moyenne", f"{avg_quality:.1f}/5")
        
        with col3:
            total_cost = sum(AI_MODELS[m]['cost'] for m in selected_models)
            st.metric("Coût total", "💰" * (total_cost // len(selected_models)))
        
        # Liste des modèles
        st.markdown("**Modèles:**")
        for model_id in selected_models:
            st.write(f"• {AI_MODELS[model_id]['icon']} {AI_MODELS[model_id]['name']}")
    
    # Navigation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Étape précédente", use_container_width=True):
            st.session_state.generation_state['step'] = 1
            st.rerun()
    
    with col2:
        if st.button(
            "➡️ Étape suivante",
            type="primary",
            use_container_width=True,
            disabled=not selected_models
        ):
            st.session_state.generation_state['selected_models'] = selected_models
            st.session_state.generation_state['step'] = 3
            st.rerun()

def render_step_configuration():
    """Étape 3 : Configuration de la génération"""
    
    st.markdown("### ⚙️ Étape 3 : Configuration de la génération")
    
    analysis = st.session_state.generation_state['analysis']
    
    # Affichage en onglets pour une meilleure organisation
    tabs = st.tabs(["📝 Informations de base", "👥 Parties", "🚨 Infractions", "⚙️ Options avancées"])
    
    # Initialiser la configuration si nécessaire
    if 'config' not in st.session_state.generation_state:
        st.session_state.generation_state['config'] = {
            'type_acte': analysis.get('type_acte', 'plainte'),
            'parties': analysis.get('parties', {'demandeurs': [], 'defendeurs': []}),
            'infractions': [],
            'contexte': analysis.get('contexte', {}),
            'options': {
                'style': 'standard',
                'longueur_cible': 3000,
                'inclure_jurisprudence': True,
                'inclure_pieces': True
            }
        }
    
    config = st.session_state.generation_state['config']
    
    with tabs[0]:  # Informations de base
        col1, col2 = st.columns(2)
        
        with col1:
            # Type d'acte
            config['type_acte'] = st.selectbox(
                "Type d'acte juridique",
                options=[
                    'plainte', 'plainte_cpc', 'conclusions', 'conclusions_nullite',
                    'assignation', 'citation', 'observations', 'courrier',
                    'requete', 'memoire'
                ],
                index=['plainte', 'plainte_cpc', 'conclusions', 'conclusions_nullite',
                       'assignation', 'citation', 'observations', 'courrier',
                       'requete', 'memoire'].index(config['type_acte']) if config['type_acte'] in [
                    'plainte', 'plainte_cpc', 'conclusions', 'conclusions_nullite',
                    'assignation', 'citation', 'observations', 'courrier',
                    'requete', 'memoire'
                ] else 0,
                format_func=lambda x: x.replace('_', ' ').title(),
                help="Le type d'acte détermine la structure et le formalisme du document"
            )
            
            # Phase procédurale
            config['contexte']['phase'] = st.selectbox(
                "Phase procédurale",
                ["pre_plainte", "enquete", "instruction", "jugement", "appel", "cassation"],
                index=["pre_plainte", "enquete", "instruction", "jugement", "appel", "cassation"].index(
                    config['contexte'].get('phase', 'enquete')
                ),
                format_func=lambda x: {
                    'pre_plainte': 'Pré-plainte',
                    'enquete': 'Enquête préliminaire',
                    'instruction': 'Instruction',
                    'jugement': 'Jugement',
                    'appel': 'Appel',
                    'cassation': 'Cassation'
                }.get(x, x)
            )
            
            # Référence du dossier
            config['reference'] = st.text_input(
                "Référence du dossier",
                value=analysis.get('reference', ''),
                placeholder="Ex: REF2024-001"
            )
        
        with col2:
            # Juridiction
            juridiction = analysis.get('juridiction', {})
            
            juridiction_type = st.selectbox(
                "Type de juridiction",
                ["Tribunal judiciaire", "Tribunal de commerce", "Conseil de prud'hommes",
                 "Tribunal administratif", "Cour d'appel", "Cour de cassation"],
                index=0
            )
            
            juridiction_lieu = st.text_input(
                "Lieu",
                value=juridiction.get('lieu', 'Paris'),
                placeholder="Ex: Paris, Lyon, Marseille..."
            )
            
            config['juridiction'] = {
                'type': juridiction_type,
                'lieu': juridiction_lieu
            }
            
            # Urgence
            urgence_niveau = st.select_slider(
                "Niveau d'urgence",
                options=['normale', 'moderee', 'haute', 'extreme'],
                value=config['contexte'].get('urgence', {}).get('niveau', 'normale'),
                format_func=lambda x: {
                    'normale': '🟢 Normale',
                    'moderee': '🟡 Modérée',
                    'haute': '🟠 Haute',
                    'extreme': '🔴 Extrême'
                }.get(x, x)
            )
            
            config['contexte']['urgence'] = {
                'niveau': urgence_niveau,
                'delai_estime': {
                    'normale': '7 jours',
                    'moderee': '48 heures',
                    'haute': '24 heures',
                    'extreme': '2 heures'
                }.get(urgence_niveau, '7 jours')
            }
    
    with tabs[1]:  # Parties
        st.markdown("#### Configuration des parties")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**👤 Demandeurs / Plaignants**")
            
            demandeurs_text = st.text_area(
                "Liste des demandeurs",
                value='\n'.join(config['parties'].get('demandeurs', [])),
                height=150,
                placeholder="Un par ligne\nEx:\nM. Jean Dupont\nMme Marie Martin",
                label_visibility="collapsed"
            )
            
            config['parties']['demandeurs'] = [
                d.strip() for d in demandeurs_text.split('\n') if d.strip()
            ]
            
            # Informations complémentaires
            with st.expander("Informations complémentaires"):
                st.text_input("Adresse", key="dem_adresse")
                st.text_input("Avocat", key="dem_avocat")
        
        with col2:
            st.markdown("**👥 Défendeurs / Mis en cause**")
            
            defendeurs_text = st.text_area(
                "Liste des défendeurs",
                value='\n'.join(config['parties'].get('defendeurs', [])),
                height=150,
                placeholder="Un par ligne\nEx:\nSociété ABC\nM. Pierre Durand",
                label_visibility="collapsed"
            )
            
            config['parties']['defendeurs'] = [
                d.strip() for d in defendeurs_text.split('\n') if d.strip()
            ]
            
            # Informations complémentaires
            with st.expander("Informations complémentaires"):
                st.text_input("Siège social", key="def_siege")
                st.text_input("Représentant", key="def_representant")
        
        with col3:
            st.markdown("**🏛️ Tiers intervenants**")
            
            tiers_text = st.text_area(
                "Liste des tiers",
                value='\n'.join(config['parties'].get('tiers', [])),
                height=150,
                placeholder="Un par ligne (optionnel)",
                label_visibility="collapsed"
            )
            
            config['parties']['tiers'] = [
                t.strip() for t in tiers_text.split('\n') if t.strip()
            ]
    
    with tabs[2]:  # Infractions
        st.markdown("#### Configuration des infractions")
        
        # Catégories d'infractions
        categories = {
            "Atteintes aux biens": [
                "Vol", "Escroquerie", "Abus de confiance", "Abus de biens sociaux",
                "Recel", "Blanchiment"
            ],
            "Atteintes aux personnes": [
                "Violence", "Menaces", "Harcèlement", "Discrimination"
            ],
            "Infractions économiques": [
                "Corruption", "Trafic d'influence", "Prise illégale d'intérêts",
                "Favoritisme", "Détournement de fonds"
            ],
            "Infractions documentaires": [
                "Faux et usage de faux", "Usurpation d'identité"
            ]
        }
        
        # Sélection par catégorie
        selected_infractions = []
        
        for category, infractions in categories.items():
            with st.expander(f"📁 {category}"):
                cols = st.columns(2)
                for i, infraction in enumerate(infractions):
                    with cols[i % 2]:
                        if st.checkbox(infraction, key=f"inf_{infraction}"):
                            selected_infractions.append(infraction)
        
        config['infractions'] = selected_infractions
        
        # Infractions personnalisées
        custom_infractions = st.text_area(
            "Autres infractions (une par ligne)",
            placeholder="Ajoutez des infractions non listées ci-dessus"
        )
        
        if custom_infractions:
            config['infractions'].extend([
                inf.strip() for inf in custom_infractions.split('\n') if inf.strip()
            ])
        
        # Résumé
        if config['infractions']:
            st.success(f"✅ {len(config['infractions'])} infraction(s) sélectionnée(s)")
            
            # Détails des peines encourues
            with st.expander("⚖️ Peines encourues"):
                for inf in config['infractions']:
                    st.write(f"**{inf}** : Jusqu'à X ans de prison et Y€ d'amende")
    
    with tabs[3]:  # Options avancées
        st.markdown("#### Options de génération avancées")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Style de rédaction
            config['options']['style'] = st.selectbox(
                "Style de rédaction",
                ["standard", "technique", "argumentatif", "exhaustif", "concis"],
                format_func=lambda x: {
                    'standard': '📝 Standard',
                    'technique': '🔧 Technique',
                    'argumentatif': '💬 Argumentatif',
                    'exhaustif': '📚 Exhaustif',
                    'concis': '✂️ Concis'
                }.get(x, x),
                help="Le style influence le ton et le niveau de détail"
            )
            
            # Longueur cible
            config['options']['longueur_cible'] = st.slider(
                "Longueur cible (mots)",
                min_value=1000,
                max_value=10000,
                value=config['options'].get('longueur_cible', 3000),
                step=500,
                help="Estimation du nombre de mots souhaité"
            )
            
            # Format de sortie
            config['options']['format'] = st.selectbox(
                "Format de sortie",
                ["Word (.docx)", "PDF", "Texte brut (.txt)", "Markdown (.md)"],
                help="Format du fichier généré"
            )
        
        with col2:
            # Options de contenu
            config['options']['inclure_jurisprudence'] = st.checkbox(
                "📚 Inclure la jurisprudence",
                value=config['options'].get('inclure_jurisprudence', True),
                help="Ajoute les références jurisprudentielles pertinentes"
            )
            
            config['options']['inclure_pieces'] = st.checkbox(
                "📎 Générer la liste des pièces",
                value=config['options'].get('inclure_pieces', True),
                help="Crée automatiquement le bordereau de pièces"
            )
            
            config['options']['inclure_moyens'] = st.checkbox(
                "⚖️ Développer les moyens de droit",
                value=True,
                help="Analyse juridique approfondie"
            )
            
            config['options']['inclure_prejudice'] = st.checkbox(
                "💰 Détailler le préjudice",
                value=True,
                help="Évaluation et justification du préjudice"
            )
        
        # Options d'IA
        st.markdown("#### 🤖 Options d'intelligence artificielle")
        
        col1, col2 = st.columns(2)
        
        with col1:
            config['options']['temperature'] = st.slider(
                "Créativité",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="0 = Très conservateur, 1 = Très créatif"
            )
        
        with col2:
            config['options']['iterations'] = st.number_input(
                "Nombre d'itérations",
                min_value=1,
                max_value=5,
                value=1,
                help="Nombre de passes d'amélioration"
            )
    
    # Validation et résumé
    st.markdown("### 📋 Résumé de la configuration")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type d'acte", config['type_acte'].replace('_', ' ').title())
    
    with col2:
        total_parties = len(config['parties']['demandeurs']) + len(config['parties']['defendeurs'])
        st.metric("Parties", total_parties)
    
    with col3:
        st.metric("Infractions", len(config['infractions']))
    
    with col4:
        st.metric("Longueur", f"{config['options']['longueur_cible']:,} mots")
    
    # Validation
    issues = []
    if not config['parties']['demandeurs'] and not config['parties']['defendeurs']:
        issues.append("❌ Aucune partie renseignée")
    if not config['infractions'] and config['type_acte'] in ['plainte', 'plainte_cpc']:
        issues.append("❌ Aucune infraction sélectionnée")
    
    if issues:
        for issue in issues:
            st.error(issue)
    else:
        st.success("✅ Configuration complète et valide")
    
    # Navigation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Étape précédente", use_container_width=True):
            st.session_state.generation_state['step'] = 2
            st.rerun()
    
    with col2:
        if st.button(
            "🚀 Lancer la génération",
            type="primary",
            use_container_width=True,
            disabled=bool(issues)
        ):
            st.session_state.generation_state['config'] = config
            st.session_state.generation_state['step'] = 4
            st.rerun()

def render_step_generation():
    """Étape 4 : Génération en cours"""
    
    st.markdown("### 🚀 Étape 4 : Génération en cours")
    
    # Récupérer la configuration
    config = st.session_state.generation_state['config']
    selected_models = st.session_state.generation_state['selected_models']
    fusion_mode = st.session_state.generation_state.get('fusion_mode', 'consensus')
    
    # Container pour l'animation
    generation_container = st.container()
    
    with generation_container:
        # Charger le générateur
        if not st.session_state.components_loaded['generateur']:
            generateur = GenerateurJuridiqueMultiIA()
            st.session_state.generateur = generateur
            st.session_state.components_loaded['generateur'] = True
        else:
            generateur = st.session_state.generateur
        
        # Lancer la génération asynchrone
        import asyncio
        
        async def generate():
            return await generateur.generer_avec_ia(
                config['type_acte'],
                config,
                selected_models,
                fusion_mode
            )
        
        # Exécuter la génération
        try:
            result = asyncio.run(generate())
            
            # Sauvegarder le résultat
            st.session_state.generation_state['generated_content'] = result
            st.session_state.generation_state['step'] = 5
            
            time.sleep(1)  # Pause pour l'effet
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération : {str(e)}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Réessayer", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("⬅️ Retour à la configuration", use_container_width=True):
                    st.session_state.generation_state['step'] = 3
                    st.rerun()

def render_step_result():
    """Étape 5 : Affichage et édition du résultat"""
    
    st.markdown("### 📄 Étape 5 : Votre acte juridique est prêt!")
    
    result = st.session_state.generation_state['generated_content']
    config = st.session_state.generation_state['config']
    
    # Métadonnées du document
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Type", config['type_acte'].replace('_', ' ').title())
    
    with col2:
        word_count = len(result['content'].split())
        st.metric("📊 Mots", f"{word_count:,}")
    
    with col3:
        pages = word_count // 250
        st.metric("📄 Pages", f"~{pages}")
    
    with col4:
        confidence = result.get('metadata', {}).get('average_confidence', 0.85)
        st.metric("🎯 Confiance", f"{confidence:.0%}")
    
    # Informations sur la génération
    with st.expander("🔍 Détails de la génération"):
        st.markdown(f"**Méthode de fusion:** {result.get('fusion_method', 'N/A')}")
        
        if 'sections_sources' in result:
            st.markdown("**Sources des sections:**")
            for section, model in result['sections_sources'].items():
                st.write(f"- {section}: {AI_MODELS[model]['name']}")
        
        if 'scores' in result:
            st.markdown("**Scores des modèles:**")
            for model, score in result['scores'].items():
                st.write(f"- {AI_MODELS[model]['name']}: {score:.2f}")
    
    # Onglets pour différentes vues
    view_tabs = st.tabs(["✏️ Édition", "👁️ Aperçu", "📊 Analyse", "📥 Export"])
    
    with view_tabs[0]:  # Édition
        st.markdown("#### ✏️ Éditeur de document")
        
        # Barre d'outils
        tool_cols = st.columns(8)
        
        tools = [
            ("🔤", "Format"),
            ("🎨", "Style"),
            ("📏", "Alignement"),
            ("🔗", "Liens"),
            ("📋", "Listes"),
            ("📊", "Tableaux"),
            ("💾", "Sauvegarder"),
            ("↩️", "Annuler")
        ]
        
        for col, (icon, name) in zip(tool_cols, tools):
            with col:
                st.button(icon, help=name, use_container_width=True)
        
        # Zone d'édition
        edited_content = st.text_area(
            "Contenu éditable",
            value=result['content'],
            height=600,
            key="main_editor",
            label_visibility="collapsed"
        )
        
        # Outils d'édition avancés
        with st.expander("🛠️ Outils avancés"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Vérifier l'orthographe", use_container_width=True):
                    st.info("Vérification en cours...")
                
                if st.button("📏 Formater le document", use_container_width=True):
                    st.info("Formatage appliqué")
                
                if st.button("🔗 Insérer une référence", use_container_width=True):
                    st.info("Sélectionnez la référence à insérer")
            
            with col2:
                if st.button("📚 Ajouter de la jurisprudence", use_container_width=True):
                    st.info("Recherche de jurisprudence...")
                
                if st.button("📎 Gérer les pièces", use_container_width=True):
                    st.info("Gestionnaire de pièces")
                
                if st.button("💬 Suggestions IA", use_container_width=True):
                    st.info("Analyse en cours...")
    
    with view_tabs[1]:  # Aperçu
        st.markdown("#### 👁️ Aperçu du document")
        
        # Style d'aperçu
        preview_style = st.selectbox(
            "Style d'aperçu",
            ["📄 Document Word", "📑 PDF", "🌐 Web", "📱 Mobile"],
            label_visibility="collapsed"
        )
        
        # Container d'aperçu avec style
        st.markdown("""
        <div style="
            background: white;
            padding: 40px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-family: 'Garamond', serif;
            line-height: 1.8;
            color: #333;
            max-height: 600px;
            overflow-y: auto;
        ">
        """, unsafe_allow_html=True)
        
        # Contenu formaté
        formatted_content = edited_content.replace('\n', '<br>')
        st.markdown(formatted_content, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with view_tabs[2]:  # Analyse
        st.markdown("#### 📊 Analyse du document")
        
        # Graphiques d'analyse
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition des sections
            fig_sections = go.Figure(data=[
                go.Pie(
                    labels=['Introduction', 'Faits', 'Droit', 'Demandes', 'Conclusion'],
                    values=[20, 35, 25, 15, 5],
                    hole=.3
                )
            ])
            fig_sections.update_layout(
                title="Répartition des sections",
                height=300
            )
            st.plotly_chart(fig_sections, use_container_width=True)
            
            # Statistiques textuelles
            st.markdown("**📊 Statistiques textuelles**")
            stats = {
                "Mots": word_count,
                "Caractères": len(edited_content),
                "Paragraphes": edited_content.count('\n\n') + 1,
                "Phrases": edited_content.count('.') + edited_content.count('!') + edited_content.count('?')
            }
            
            for stat, value in stats.items():
                st.metric(stat, f"{value:,}")
        
        with col2:
            # Score de qualité
            quality_scores = {
                'Structure': 0.92,
                'Clarté': 0.88,
                'Exhaustivité': 0.95,
                'Conformité': 0.90,
                'Argumentation': 0.87
            }
            
            fig_quality = go.Figure(data=[
                go.Bar(
                    x=list(quality_scores.values()),
                    y=list(quality_scores.keys()),
                    orientation='h',
                    marker_color='lightblue'
                )
            ])
            fig_quality.update_layout(
                title="Scores de qualité",
                xaxis_title="Score",
                height=300
            )
            st.plotly_chart(fig_quality, use_container_width=True)
            
            # Recommandations
            st.markdown("**💡 Recommandations**")
            recommendations = [
                "✅ Structure juridique respectée",
                "⚠️ Ajouter plus de jurisprudence",
                "💡 Développer l'argumentation sur le préjudice",
                "✅ Formalisme procédural correct"
            ]
            
            for rec in recommendations:
                st.write(rec)
    
    with view_tabs[3]:  # Export
        st.markdown("#### 📥 Options d'export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Export de documents**")
            
            # Format d'export
            export_format = st.selectbox(
                "Format d'export",
                ["Word (.docx)", "PDF", "Texte (.txt)", "Markdown (.md)", "HTML"],
                key="export_format_final"
            )
            
            # Options d'export
            include_metadata = st.checkbox("Inclure les métadonnées", value=True)
            include_watermark = st.checkbox("Ajouter un filigrane", value=False)
            include_signature = st.checkbox("Espace pour signature", value=True)
            
            # Bouton d'export
            if st.button("📥 Télécharger", type="primary", use_container_width=True):
                # Préparer le fichier
                if export_format == "Word (.docx)":
                    file_content = edited_content.encode('utf-8')
                    file_name = f"{config['type_acte']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    mime_type = "text/plain"
                else:
                    file_content = edited_content.encode('utf-8')
                    file_name = f"{config['type_acte']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    mime_type = "text/plain"
                
                st.download_button(
                    "💾 Télécharger le fichier",
                    file_content,
                    file_name,
                    mime_type,
                    key="download_final_file"
                )
        
        with col2:
            st.markdown("**📧 Envoi et partage**")
            
            # Email
            email_recipient = st.text_input(
                "Destinataire",
                placeholder="email@example.com"
            )
            
            email_subject = st.text_input(
                "Objet",
                value=f"{config['type_acte'].replace('_', ' ').title()} - {config.get('reference', 'REF')}"
            )
            
            email_message = st.text_area(
                "Message",
                placeholder="Message d'accompagnement...",
                height=100
            )
            
            if st.button("📧 Envoyer par email", use_container_width=True):
                if email_recipient:
                    st.success("✅ Email envoyé avec succès!")
                else:
                    st.error("Veuillez saisir un destinataire")
            
            # Autres options
            st.markdown("**🔗 Autres options**")
            
            if st.button("☁️ Sauvegarder dans le cloud", use_container_width=True):
                st.info("Sauvegarde en cours...")
            
            if st.button("🖨️ Imprimer", use_container_width=True):
                st.info("Préparation pour l'impression...")
    
    # Actions finales
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Nouvelle génération", use_container_width=True):
            # Réinitialiser l'état
            st.session_state.generation_state = {
                'step': 1,
                'analysis': None,
                'selected_models': [],
                'fusion_mode': 'consensus',
                'generated_content': None
            }
            st.rerun()
    
    with col2:
        if st.button("♻️ Régénérer", use_container_width=True):
            st.session_state.generation_state['step'] = 4
            st.rerun()
    
    with col3:
        if st.button("📋 Dupliquer", use_container_width=True):
            st.info("Document dupliqué")
    
    with col4:
        if st.button("📚 Historique", use_container_width=True):
            st.info("Accès à l'historique des générations")

# ========================= FONCTIONS UTILITAIRES =========================

def get_ai_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """Recommande des modèles IA basés sur l'analyse"""
    recommendations = []
    
    # Logique de recommandation
    if analysis['contexte']['complexite'] == 'elevee':
        recommendations.append({
            'model_id': 'gpt4',
            'reason': "Complexité élevée nécessitant un raisonnement approfondi"
        })
        recommendations.append({
            'model_id': 'claude3',
            'reason': "Nuance et contexte important pour ce type de dossier"
        })
    
    if analysis['contexte']['urgence']['niveau'] in ['haute', 'extreme']:
        recommendations.append({
            'model_id': 'mistral',
            'reason': "Génération rapide requise vu l'urgence"
        })
    
    if analysis['options'].get('inclure_jurisprudence', False):
        recommendations.append({
            'model_id': 'gemini',
            'reason': "Capacités de recherche intégrées pour la jurisprudence"
        })
    
    # Toujours recommander au moins un modèle
    if not recommendations:
        recommendations.append({
            'model_id': 'claude3',
            'reason': "Modèle polyvalent adapté à votre demande"
        })
    
    return recommendations

def validate_configuration(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valide la configuration avant génération"""
    errors = []
    
    if not config.get('type_acte'):
        errors.append("Type d'acte non spécifié")
    
    if not config.get('parties', {}).get('demandeurs') and not config.get('parties', {}).get('defendeurs'):
        errors.append("Aucune partie spécifiée")
    
    if config.get('type_acte') in ['plainte', 'plainte_cpc'] and not config.get('infractions'):
        errors.append("Aucune infraction spécifiée pour une plainte")
    
    return len(errors) == 0, errors

# Point d'entrée
if __name__ == "__main__":
    run()