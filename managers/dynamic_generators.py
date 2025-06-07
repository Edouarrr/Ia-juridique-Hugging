# managers/dynamic_generators.py
"""Générateurs dynamiques pour prompts et templates"""

import json
import re
import logging
import asyncio
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

from managers.multi_llm_manager import MultiLLMManager
from config.app_config import LLMProvider

async def generate_dynamic_search_prompts(search_query: str, context: str = "") -> Dict[str, Dict[str, List[str]]]:
    """Génère dynamiquement des prompts de recherche basés sur la requête"""
    llm_manager = MultiLLMManager()
    
    # Utiliser Claude Opus 4 et ChatGPT 4o si disponibles
    preferred_providers = []
    if LLMProvider.CLAUDE_OPUS in llm_manager.clients:
        preferred_providers.append(LLMProvider.CLAUDE_OPUS)
    if LLMProvider.CHATGPT_4O in llm_manager.clients:
        preferred_providers.append(LLMProvider.CHATGPT_4O)
    
    if not preferred_providers and llm_manager.clients:
        preferred_providers = [list(llm_manager.clients.keys())[0]]
    
    if not preferred_providers:
        # Retour aux prompts statiques si aucun LLM disponible
        return {
            "🔍 Recherches suggérées": {
                "Générique": [
                    f"{search_query} jurisprudence récente",
                    f"{search_query} éléments constitutifs",
                    f"{search_query} moyens de défense",
                    f"{search_query} sanctions encourues"
                ]
            }
        }
    
    prompt = f"""En tant qu'expert en droit pénal des affaires, génère des prompts de recherche juridique pertinents basés sur cette requête : "{search_query}"
{f"Contexte supplémentaire : {context}" if context else ""}
Crée une structure JSON avec des catégories et sous-catégories de prompts de recherche.
Chaque prompt doit être concis (max 80 caractères) et cibler un aspect juridique précis.
Format attendu :
{{
    "🔍 Éléments constitutifs": {{
        "Élément matériel": ["prompt1", "prompt2", ...],
        "Élément intentionnel": ["prompt1", "prompt2", ...]
    }},
    "⚖️ Jurisprudence": {{
        "Décisions récentes": ["prompt1", "prompt2", ...],
        "Arrêts de principe": ["prompt1", "prompt2", ...]
    }},
    "🛡️ Moyens de défense": {{
        "Exceptions": ["prompt1", "prompt2", ...],
        "Stratégies": ["prompt1", "prompt2", ...]
    }}
}}
Génère au moins 3 catégories avec 2 sous-catégories chacune, et 4 prompts par sous-catégorie."""
    
    system_prompt = """Tu es un avocat spécialisé en droit pénal des affaires avec 20 ans d'expérience.
Tu maîtrises parfaitement la recherche juridique et sais formuler des requêtes précises pour trouver
la jurisprudence, la doctrine et les textes pertinents. Tes prompts sont toujours en français,
techniquement précis et adaptés au contexte du droit pénal économique français."""
    
    try:
        response = await llm_manager.query_single_llm(
            preferred_providers[0],
            prompt,
            system_prompt
        )
        
        if response['success']:
            # Extraire le JSON de la réponse
            json_match = re.search(r'\{[\s\S]*\}', response['response'])
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
        
    except Exception as e:
        logger.error(f"Erreur génération prompts dynamiques: {e}")
    
    # Fallback
    return {
        "🔍 Recherches suggérées": {
            "Générique": [
                f"{search_query} jurisprudence",
                f"{search_query} éléments constitutifs",
                f"{search_query} défense",
                f"{search_query} sanctions"
            ]
        }
    }

async def generate_dynamic_templates(type_acte: str, context: Dict[str, Any] = None) -> Dict[str, str]:
    """Génère dynamiquement des modèles d'actes juridiques"""
    llm_manager = MultiLLMManager()
    
    # Utiliser Claude Opus 4 et ChatGPT 4o si disponibles
    preferred_providers = []
    if LLMProvider.CLAUDE_OPUS in llm_manager.clients:
        preferred_providers.append(LLMProvider.CLAUDE_OPUS)
    if LLMProvider.CHATGPT_4O in llm_manager.clients:
        preferred_providers.append(LLMProvider.CHATGPT_4O)
    
    if not preferred_providers and llm_manager.clients:
        preferred_providers = [list(llm_manager.clients.keys())[0]]
    
    if not preferred_providers:
        return {}
    
    context_str = ""
    if context:
        context_str = f"""
Contexte spécifique :
- Client : {context.get('client', 'Non spécifié')}
- Infraction : {context.get('infraction', 'Non spécifiée')}
- Juridiction : {context.get('juridiction', 'Non spécifiée')}
"""
    
    prompt = f"""Génère 3 modèles d'actes juridiques pour : "{type_acte}"
{context_str}
Pour chaque modèle, fournis :
1. Un titre descriptif avec emoji (ex: "📨 Demande d'audition libre")
2. Le contenu complet du modèle avec les balises [CHAMP] pour les éléments à personnaliser
Utilise un style juridique professionnel, formel et conforme aux usages du barreau français.
Les modèles doivent être immédiatement utilisables par un avocat.
Format de réponse attendu (JSON) :
{{
    "📄 Modèle standard de {type_acte}": "Contenu du modèle...",
    "⚖️ Modèle approfondi de {type_acte}": "Contenu du modèle...",
    "🔍 Modèle détaillé de {type_acte}": "Contenu du modèle..."
}}"""
    
    system_prompt = """Tu es un avocat au barreau de Paris, spécialisé en droit pénal des affaires.
Tu rédiges des actes juridiques depuis 20 ans et maîtrises parfaitement les formules consacrées,
la structure des actes et les mentions obligatoires. Tes modèles sont toujours conformes
aux exigences procédurales et aux usages de la profession."""
    
    try:
        # Interroger les LLMs
        responses = await llm_manager.query_multiple_llms(
            preferred_providers,
            prompt,
            system_prompt
        )
        
        # Fusionner les réponses si plusieurs LLMs
        if len(responses) > 1:
            fusion_prompt = f"""Voici plusieurs propositions de modèles pour "{type_acte}".
Fusionne-les intelligemment pour créer les 3 meilleurs modèles en gardant le meilleur de chaque proposition.
{chr(10).join([f"Proposition {i+1}: {r['response']}" for i, r in enumerate(responses) if r['success']])}
Retourne un JSON avec 3 modèles fusionnés."""
            
            fusion_response = await llm_manager.query_single_llm(
                preferred_providers[0],
                fusion_prompt,
                "Tu es un expert en fusion de contenus juridiques."
            )
            
            if fusion_response['success']:
                response_text = fusion_response['response']
            else:
                response_text = responses[0]['response'] if responses[0]['success'] else ""
        else:
            response_text = responses[0]['response'] if responses and responses[0]['success'] else ""
        
        # Extraire le JSON
        if response_text:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
        
    except Exception as e:
        logger.error(f"Erreur génération modèles dynamiques: {e}")
    
    # Fallback avec un modèle basique
    return {
        f"📄 Modèle standard de {type_acte}": f"""[EN-TÊTE AVOCAT]
À l'attention de [DESTINATAIRE]
Objet : {type_acte}
Référence : [RÉFÉRENCE]
[FORMULE D'APPEL],
J'ai l'honneur de [OBJET DE LA DEMANDE].
[DÉVELOPPEMENT]
[CONCLUSION]
Je vous prie d'agréer, [FORMULE DE POLITESSE].
[SIGNATURE]"""
    }