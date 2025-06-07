# managers/llm_manager.py
"""Gestionnaire unifié pour tous les modèles de langage"""

import streamlit as st
from typing import Optional, Dict, Any, List
import asyncio
import json
from datetime import datetime
import logging

import openai
import anthropic
import google.generativeai as genai
from mistralai.client import MistralClient
from groq import Groq

from config.llm_config import get_llm_client, get_default_params, LLM_CONFIGS
from config.prompts import get_prompt

logger = logging.getLogger(__name__)

class LLMManager:
    """Gestionnaire centralisé pour tous les LLMs"""
    
    def __init__(self):
        self.clients = {}
        self.current_provider = None
        self.current_model = None
        self.conversation_history = []
        
    def initialize_client(self, provider: str, api_key: Optional[str] = None) -> bool:
        """Initialise le client pour un provider donné"""
        try:
            client = get_llm_client(provider, api_key)
            if client:
                self.clients[provider] = client
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur initialisation {provider}: {e}")
            return False
    
    def set_current_model(self, provider: str, model: str):
        """Définit le modèle actuel"""
        if provider not in self.clients:
            if not self.initialize_client(provider):
                raise ValueError(f"Impossible d'initialiser {provider}")
        
        self.current_provider = provider
        self.current_model = model
        
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Génère une réponse avec le modèle actuel"""
        if not self.current_provider or not self.current_model:
            raise ValueError("Aucun modèle sélectionné")
            
        # Paramètres par défaut
        params = get_default_params(self.current_provider)
        params.update(kwargs)
        
        # Appel selon le provider
        if self.current_provider == "OpenAI":
            return await self._generate_openai(prompt, system_prompt, params)
        elif self.current_provider == "Anthropic":
            return await self._generate_anthropic(prompt, system_prompt, params)
        elif self.current_provider == "Google":
            return await self._generate_google(prompt, system_prompt, params)
        elif self.current_provider == "Mistral":
            return await self._generate_mistral(prompt, system_prompt, params)
        elif self.current_provider == "Groq":
            return await self._generate_groq(prompt, system_prompt, params)
        else:
            raise ValueError(f"Provider non supporté: {self.current_provider}")
    
    async def _generate_openai(self, prompt: str, system_prompt: Optional[str], params: Dict) -> str:
        """Génération avec OpenAI"""
        client = self.clients["OpenAI"]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.current_model,
                messages=messages,
                **params
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur OpenAI: {e}")
            raise
    
    async def _generate_anthropic(self, prompt: str, system_prompt: Optional[str], params: Dict) -> str:
        """Génération avec Anthropic"""
        client = self.clients["Anthropic"]
        
        # Anthropic utilise un format différent
        anthropic_params = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": params.get("max_tokens", 4096)
        }
        
        if system_prompt:
            anthropic_params["system"] = system_prompt
            
        if "temperature" in params:
            anthropic_params["temperature"] = params["temperature"]
        
        try:
            response = await asyncio.to_thread(
                client.messages.create,
                **anthropic_params
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Erreur Anthropic: {e}")
            raise
    
    async def _generate_google(self, prompt: str, system_prompt: Optional[str], params: Dict) -> str:
        """Génération avec Google Gemini"""
        model = genai.GenerativeModel(self.current_model)
        
        # Combiner system et user prompt pour Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        generation_config = {
            "temperature": params.get("temperature", 0.7),
            "max_output_tokens": params.get("max_tokens", 4000),
            "top_p": params.get("top_p", 0.95),
            "top_k": params.get("top_k", 40)
        }
        
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Erreur Google: {e}")
            raise
    
    async def _generate_mistral(self, prompt: str, system_prompt: Optional[str], params: Dict) -> str:
        """Génération avec Mistral"""
        client = self.clients["Mistral"]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await asyncio.to_thread(
                client.chat,
                model=self.current_model,
                messages=messages,
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("max_tokens", 4000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur Mistral: {e}")
            raise
    
    async def _generate_groq(self, prompt: str, system_prompt: Optional[str], params: Dict) -> str:
        """Génération avec Groq"""
        client = self.clients["Groq"]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.current_model,
                messages=messages,
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("max_tokens", 4000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur Groq: {e}")
            raise
    
    async def analyze_legal_case(
        self,
        case_description: str,
        case_type: str,
        analysis_depth: str = "approfondie"
    ) -> Dict[str, Any]:
        """Analyse un cas juridique avec le modèle actuel"""
        
        # Obtenir le prompt approprié
        prompt = get_prompt("analyse_generale", description_cas=case_description)
        
        # System prompt juridique
        system_prompt = """Tu es un expert en droit pénal des affaires français avec 20 ans d'expérience. 
Tu fournis des analyses juridiques précises, complètes et structurées. 
Tu cites toujours les sources légales et jurisprudentielles exactes.
Tu utilises un langage professionnel mais accessible."""
        
        # Générer l'analyse
        response = await self.generate_response(
            prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Plus faible pour plus de précision
        )
        
        # Parser et structurer la réponse
        analysis = self._parse_legal_analysis(response, case_type)
        
        # Ajouter des métadonnées
        analysis["metadata"] = {
            "model": f"{self.current_provider}/{self.current_model}",
            "timestamp": datetime.now().isoformat(),
            "analysis_depth": analysis_depth,
            "case_type": case_type
        }
        
        return analysis
    
    def _parse_legal_analysis(self, response: str, case_type: str) -> Dict[str, Any]:
        """Parse et structure une analyse juridique"""
        analysis = {
            "qualification_juridique": "",
            "infractions_identifiees": [],
            "elements_constitutifs": {},
            "regime_responsabilite": "",
            "sanctions_encourues": {},
            "jurisprudences_citees": [],
            "recommandations": [],
            "niveau_risque": ""
        }
        
        # Extraction basique - à améliorer avec des patterns plus sophistiqués
        sections = response.split('\n\n')
        current_section = None
        
        for section in sections:
            section_lower = section.lower()
            
            if "qualification" in section_lower:
                current_section = "qualification_juridique"
            elif "infraction" in section_lower:
                current_section = "infractions_identifiees"
            elif "élément" in section_lower and "constitutif" in section_lower:
                current_section = "elements_constitutifs"
            elif "responsabilité" in section_lower:
                current_section = "regime_responsabilite"
            elif "sanction" in section_lower:
                current_section = "sanctions_encourues"
            elif "jurisprudence" in section_lower:
                current_section = "jurisprudences_citees"
            elif "recommandation" in section_lower:
                current_section = "recommandations"
            elif "risque" in section_lower:
                current_section = "niveau_risque"
            
            # Ajouter le contenu à la section appropriée
            if current_section:
                if isinstance(analysis[current_section], list):
                    # Pour les listes, extraire les items
                    items = [line.strip() for line in section.split('\n') if line.strip() and not line.startswith('#')]
                    analysis[current_section].extend(items)
                elif isinstance(analysis[current_section], dict):
                    # Pour les dicts, parser plus finement
                    analysis[current_section][case_type] = section
                else:
                    # Pour les strings
                    analysis[current_section] = section.strip()
        
        return analysis
    
    async def generate_legal_document(
        self,
        document_type: str,
        context: Dict[str, Any],
        format: str = "markdown"
    ) -> str:
        """Génère un document juridique"""
        
        # Prompts spécialisés par type de document
        document_prompts = {
            "note_juridique": "Rédige une note juridique professionnelle sur : {context}",
            "conclusions": "Rédige des conclusions d'avocat pour : {context}",
            "rapport_expertise": "Rédige un rapport d'expertise juridique sur : {context}",
            "memo_defense": "Rédige un mémorandum de défense pour : {context}"
        }
        
        prompt = document_prompts.get(
            document_type,
            "Rédige un document juridique sur : {context}"
        ).format(context=json.dumps(context, ensure_ascii=False))
        
        response = await self.generate_response(
            prompt,
            temperature=0.3
        )
        
        # Formater selon le type demandé
        if format == "markdown":
            return response
        elif format == "html":
            # Convertir markdown en HTML (utiliser markdown2 ou similar)
            return response  # À implémenter
        else:
            return response
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique de conversation"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Efface l'historique"""
        self.conversation_history = []
    
    def add_to_history(self, role: str, content: str):
        """Ajoute un message à l'historique"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "model": f"{self.current_provider}/{self.current_model}"
        })
    
    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Génère une réponse en streaming (pour les providers qui le supportent)"""
        if self.current_provider in ["OpenAI", "Anthropic"]:
            # Implémenter le streaming
            # Pour l'instant, on simule avec yield
            response = await self.generate_response(prompt, system_prompt, **kwargs)
            words = response.split()
            for i in range(0, len(words), 5):
                yield ' '.join(words[i:i+5]) + ' '
                await asyncio.sleep(0.1)
        else:
            # Pas de streaming, retourner tout d'un coup
            response = await self.generate_response(prompt, system_prompt, **kwargs)
            yield response


# Fonctions utilitaires pour Streamlit
def display_model_selector():
    """Widget de sélection du modèle"""
    col1, col2 = st.columns(2)
    
    with col1:
        provider = st.selectbox(
            "Provider",
            options=list(LLM_CONFIGS.keys()),
            help="Sélectionnez le fournisseur d'IA"
        )
    
    with col2:
        model = st.selectbox(
            "Modèle",
            options=LLM_CONFIGS[provider]["models"],
            index=LLM_CONFIGS[provider]["models"].index(LLM_CONFIGS[provider]["default"])
        )
    
    return provider, model

def display_model_params():
    """Widget pour les paramètres du modèle"""
    with st.expander("Paramètres avancés"):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Contrôle la créativité (0=précis, 1=créatif)"
            )
            
            max_tokens = st.slider(
                "Tokens max",
                min_value=100,
                max_value=8000,
                value=4000,
                step=100
            )
        
        with col2:
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=0.9,
                step=0.1
            )
            
            frequency_penalty = st.slider(
                "Pénalité de fréquence",
                min_value=0.0,
                max_value=2.0,
                value=0.0,
                step=0.1
            )
    
    return {
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty
    }

# Export
__all__ = [
    'LLMManager',
    'display_model_selector',
    'display_model_params'
]