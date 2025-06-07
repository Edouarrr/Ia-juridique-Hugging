# managers/multi_llm_manager.py
"""Gestionnaire unifié pour plusieurs LLMs"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import streamlit as st

from config.app_config import LLMProvider, get_llm_configs

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports conditionnels pour chaque provider
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK non installé")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI SDK non installé")

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Generative AI SDK non installé")

try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False
    logger.warning("Azure OpenAI SDK non installé")

class MultiLLMManager:
    """Gestionnaire pour interroger plusieurs LLMs"""
    
    def __init__(self):
        self.clients = {}
        self.configs = get_llm_configs()
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialise les clients pour chaque LLM disponible"""
        
        # Azure OpenAI
        if AZURE_OPENAI_AVAILABLE and self.configs[LLMProvider.AZURE_OPENAI]['endpoint']:
            try:
                self.clients[LLMProvider.AZURE_OPENAI] = AzureOpenAI(
                    api_key=self.configs[LLMProvider.AZURE_OPENAI]['key'],
                    api_version=self.configs[LLMProvider.AZURE_OPENAI]['api_version'],
                    azure_endpoint=self.configs[LLMProvider.AZURE_OPENAI]['endpoint']
                )
                logger.info("Azure OpenAI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Azure OpenAI: {e}")
        
        # Anthropic Claude
        if ANTHROPIC_AVAILABLE and self.configs[LLMProvider.CLAUDE_OPUS]['api_key']:
            try:
                self.clients[LLMProvider.CLAUDE_OPUS] = anthropic.Anthropic(
                    api_key=self.configs[LLMProvider.CLAUDE_OPUS]['api_key']
                )
                logger.info("Anthropic Claude initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Anthropic: {e}")
        
        # OpenAI ChatGPT
        if OPENAI_AVAILABLE and self.configs[LLMProvider.CHATGPT_4O]['api_key']:
            try:
                openai.api_key = self.configs[LLMProvider.CHATGPT_4O]['api_key']
                self.clients[LLMProvider.CHATGPT_4O] = openai
                logger.info("OpenAI ChatGPT initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation OpenAI: {e}")
        
        # Google Gemini
        if GOOGLE_AVAILABLE and self.configs[LLMProvider.GEMINI]['api_key']:
            try:
                genai.configure(api_key=self.configs[LLMProvider.GEMINI]['api_key'])
                self.clients[LLMProvider.GEMINI] = genai.GenerativeModel(
                    self.configs[LLMProvider.GEMINI]['model']
                )
                logger.info("Google Gemini initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Google Gemini: {e}")
        
        # Perplexity (utilise l'API OpenAI)
        if OPENAI_AVAILABLE and self.configs[LLMProvider.PERPLEXITY]['api_key']:
            try:
                # Perplexity utilise une API compatible OpenAI
                self.clients[LLMProvider.PERPLEXITY] = openai.OpenAI(
                    api_key=self.configs[LLMProvider.PERPLEXITY]['api_key'],
                    base_url="https://api.perplexity.ai"
                )
                logger.info("Perplexity AI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Perplexity: {e}")
    
    async def query_single_llm(
        self, 
        provider: LLMProvider, 
        prompt: str, 
        system_prompt: str = "Tu es un assistant juridique expert en droit pénal des affaires français.",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Interroge un LLM spécifique"""
        
        if provider not in self.clients:
            return {
                'success': False,
                'provider': provider.value,
                'error': f"Provider {provider.value} non disponible"
            }
        
        try:
            if provider == LLMProvider.AZURE_OPENAI:
                response = await self._query_azure_openai(prompt, system_prompt, temperature, max_tokens)
            elif provider == LLMProvider.CLAUDE_OPUS:
                response = await self._query_claude(prompt, system_prompt, temperature, max_tokens)
            elif provider == LLMProvider.CHATGPT_4O:
                response = await self._query_openai(prompt, system_prompt, temperature, max_tokens)
            elif provider == LLMProvider.GEMINI:
                response = await self._query_gemini(prompt, system_prompt, temperature, max_tokens)
            elif provider == LLMProvider.PERPLEXITY:
                response = await self._query_perplexity(prompt, system_prompt, temperature, max_tokens)
            else:
                return {
                    'success': False,
                    'provider': provider.value,
                    'error': f"Provider {provider.value} non implémenté"
                }
            
            return {
                'success': True,
                'provider': provider.value,
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Erreur requête {provider.value}: {str(e)}")
            return {
                'success': False,
                'provider': provider.value,
                'error': str(e)
            }
    
    async def _query_azure_openai(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Azure OpenAI"""
        client = self.clients[LLMProvider.AZURE_OPENAI]
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.configs[LLMProvider.AZURE_OPENAI]['deployment'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _query_claude(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Claude"""
        client = self.clients[LLMProvider.CLAUDE_OPUS]
        
        response = await asyncio.to_thread(
            client.messages.create,
            model=self.configs[LLMProvider.CLAUDE_OPUS]['model'],
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.content[0].text
    
    async def _query_openai(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge OpenAI ChatGPT"""
        client = self.clients[LLMProvider.CHATGPT_4O]
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.configs[LLMProvider.CHATGPT_4O]['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _query_gemini(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Google Gemini"""
        model = self.clients[LLMProvider.GEMINI]
        
        # Gemini n'a pas de system prompt séparé, on le combine
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = await asyncio.to_thread(
            model.generate_content,
            full_prompt,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens
            }
        )
        
        return response.text
    
    async def _query_perplexity(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Perplexity"""
        client = self.clients[LLMProvider.PERPLEXITY]
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.configs[LLMProvider.PERPLEXITY]['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def query_multiple_llms(
        self,
        providers: List[LLMProvider],
        prompt: str,
        system_prompt: str = "Tu es un assistant juridique expert en droit pénal des affaires français.",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> List[Dict[str, Any]]:
        """Interroge plusieurs LLMs en parallèle"""
        
        tasks = []
        for provider in providers:
            if provider in self.clients:
                task = self.query_single_llm(provider, prompt, system_prompt, temperature, max_tokens)
                tasks.append(task)
        
        if not tasks:
            return [{
                'success': False,
                'error': 'Aucun provider disponible'
            }]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les exceptions
        clean_results = []
        for result in results:
            if isinstance(result, Exception):
                clean_results.append({
                    'success': False,
                    'error': str(result)
                })
            else:
                clean_results.append(result)
        
        return clean_results
    
    def fusion_responses(self, responses: List[Dict[str, Any]], fusion_prompt: Optional[str] = None) -> str:
        """Fusionne intelligemment plusieurs réponses de LLMs"""
        
        # Filtrer les réponses valides
        valid_responses = [r for r in responses if r.get('success') and r.get('response')]
        
        if not valid_responses:
            return "Aucune réponse valide à fusionner."
        
        if len(valid_responses) == 1:
            return valid_responses[0]['response']
        
        # Construire le prompt de fusion
        if not fusion_prompt:
            fusion_prompt = """Voici plusieurs analyses juridiques du même sujet par différents experts.
Fusionne-les en gardant les meilleurs éléments de chaque analyse.
Présente une synthèse structurée et complète.

"""
        
        for i, response in enumerate(valid_responses):
            fusion_prompt += f"\n### Analyse {i+1} ({response['provider']}):\n{response['response']}\n"
        
        fusion_prompt += "\n### Synthèse fusionnée:\n"
        
        # Utiliser le premier LLM disponible pour la fusion
        if self.clients:
            provider = list(self.clients.keys())[0]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.query_single_llm(
                    provider,
                    fusion_prompt,
                    "Tu es un expert en synthèse juridique. Fusionne les analyses en gardant le meilleur de chaque."
                )
            )
            
            if result['success']:
                return result['response']
        
        # Fallback : concaténation simple
        combined = "## Synthèse des analyses\n\n"
        for response in valid_responses:
            combined += f"### {response['provider']}\n{response['response']}\n\n"
        
        return combined
    
    def get_available_providers(self) -> List[str]:
        """Retourne la liste des providers disponibles"""
        return [provider.value for provider in self.clients.keys()]
    
    def test_connections(self) -> Dict[str, bool]:
        """Teste la connexion à chaque LLM"""
        results = {}
        
        test_prompt = "Réponds simplement 'OK' si tu reçois ce message."
        
        for provider in LLMProvider:
            if provider in self.clients:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(
                        self.query_single_llm(provider, test_prompt, "Réponds uniquement 'OK'.", 0.1, 10)
                    )
                    
                    results[provider.value] = result['success']
                except:
                    results[provider.value] = False
            else:
                results[provider.value] = False
        
        return results

# Fonction helper pour Streamlit
def display_llm_status():
    """Affiche le statut des LLMs dans Streamlit"""
    llm_manager = MultiLLMManager()
    
    st.markdown("### 🤖 État des IA")
    
    status = llm_manager.test_connections()
    
    cols = st.columns(len(status))
    for i, (provider, is_connected) in enumerate(status.items()):
        with cols[i]:
            if is_connected:
                st.success(f"✅ {provider}")
            else:
                st.error(f"❌ {provider}")