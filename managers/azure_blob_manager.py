# managers/multi_llm_manager.py
"""Gestionnaire pour interroger plusieurs LLMs en parallèle"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

logger = logging.getLogger(__name__)

# Imports conditionnels pour les IA
try:
    from openai import OpenAI, AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI non disponible")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic non disponible")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini non disponible")

from config import LLM_CONFIGS


class LLMProvider(Enum):
    """Providers LLM disponibles"""
    AZURE_OPENAI = "Azure OpenAI (GPT-4)"
    CLAUDE_OPUS = "Claude Opus 4"
    CHATGPT_4O = "ChatGPT 4o"
    GEMINI = "Google Gemini"
    PERPLEXITY = "Perplexity AI"


class MultiLLMManager:
    """Gestionnaire pour interroger plusieurs LLMs"""
    
    def __init__(self):
        self.configs = LLM_CONFIGS
        self.clients = self._initialize_clients()
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _initialize_clients(self) -> Dict[LLMProvider, Any]:
        """Initialise les clients LLM"""
        clients = {}
        
        # Azure OpenAI
        if self.configs[LLMProvider.AZURE_OPENAI]['key'] and OPENAI_AVAILABLE:
            try:
                clients[LLMProvider.AZURE_OPENAI] = AzureOpenAI(
                    azure_endpoint=self.configs[LLMProvider.AZURE_OPENAI]['endpoint'],
                    api_key=self.configs[LLMProvider.AZURE_OPENAI]['key'],
                    api_version=self.configs[LLMProvider.AZURE_OPENAI]['api_version']
                )
            except Exception as e:
                logger.warning(f"Azure OpenAI non disponible: {e}")
        
        # Claude
        if self.configs[LLMProvider.CLAUDE_OPUS]['api_key'] and ANTHROPIC_AVAILABLE:
            try:
                clients[LLMProvider.CLAUDE_OPUS] = anthropic.Anthropic(
                    api_key=self.configs[LLMProvider.CLAUDE_OPUS]['api_key']
                )
            except Exception as e:
                logger.warning(f"Claude non disponible: {e}")
        
        # ChatGPT
        if self.configs[LLMProvider.CHATGPT_4O]['api_key'] and OPENAI_AVAILABLE:
            try:
                clients[LLMProvider.CHATGPT_4O] = OpenAI(
                    api_key=self.configs[LLMProvider.CHATGPT_4O]['api_key']
                )
            except Exception as e:
                logger.warning(f"ChatGPT non disponible: {e}")
        
        # Gemini
        if self.configs[LLMProvider.GEMINI]['api_key'] and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.configs[LLMProvider.GEMINI]['api_key'])
                clients[LLMProvider.GEMINI] = genai.GenerativeModel(
                    self.configs[LLMProvider.GEMINI]['model']
                )
            except Exception as e:
                logger.warning(f"Gemini non disponible: {e}")
        
        # Perplexity
        if self.configs[LLMProvider.PERPLEXITY]['api_key'] and OPENAI_AVAILABLE:
            try:
                clients[LLMProvider.PERPLEXITY] = OpenAI(
                    api_key=self.configs[LLMProvider.PERPLEXITY]['api_key'],
                    base_url="https://api.perplexity.ai"
                )
            except Exception as e:
                logger.warning(f"Perplexity non disponible: {e}")
        
        return clients
    
    async def query_single_llm(self, 
                              provider: LLMProvider, 
                              prompt: str,
                              system_prompt: str = None) -> Dict[str, Any]:
        """Interroge un seul LLM"""
        
        if provider not in self.clients:
            return {
                'provider': provider.value,
                'success': False,
                'error': 'Provider non configuré',
                'response': None
            }
        
        try:
            client = self.clients[provider]
            
            # Azure OpenAI
            if provider == LLMProvider.AZURE_OPENAI:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model=self.configs[provider]['deployment'],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None
                }
            
            # Claude
            elif provider == LLMProvider.CLAUDE_OPUS:
                messages = []
                messages.append({"role": "user", "content": prompt})
                
                response = client.messages.create(
                    model=self.configs[provider]['model'],
                    messages=messages,
                    system=system_prompt if system_prompt else "Tu es un assistant juridique expert en droit pénal des affaires.",
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.content[0].text,
                    'usage': {'total_tokens': response.usage.input_tokens + response.usage.output_tokens}
                }
            
            # ChatGPT 4o
            elif provider == LLMProvider.CHATGPT_4O:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model=self.configs[provider]['model'],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None
                }
            
            # Gemini
            elif provider == LLMProvider.GEMINI:
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = client.generate_content(full_prompt)
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.text,
                    'usage': None
                }
            
            # Perplexity
            elif provider == LLMProvider.PERPLEXITY:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model=self.configs[provider]['model'],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                return {
                    'provider': provider.value,
                    'success': True,
                    'response': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None,
                    'citations': getattr(response, 'citations', [])
                }
            
        except Exception as e:
            logger.error(f"Erreur {provider.value}: {str(e)}")
            return {
                'provider': provider.value,
                'success': False,
                'error': str(e),
                'response': None
            }
    
    async def query_multiple_llms(self, providers: List[LLMProvider], prompt: str, 
                                 system_prompt: str = None) -> List[Dict[str, Any]]:
        """Interroge plusieurs LLMs en parallèle"""
        tasks = []
        
        for provider in providers:
            task = self.query_single_llm(provider, prompt, system_prompt)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    def fusion_responses(self, responses: List[Dict[str, Any]]) -> str:
        """Fusionne intelligemment plusieurs réponses"""
        valid_responses = [r for r in responses if r['success']]
        
        if not valid_responses:
            return "Aucune réponse valide obtenue."
        
        if len(valid_responses) == 1:
            return valid_responses[0]['response']
        
        # Construire un prompt de fusion
        fusion_prompt = "Voici plusieurs analyses d'experts. Synthétise-les en gardant les points essentiels:\n\n"
        
        for resp in valid_responses:
            fusion_prompt += f"### {resp['provider']}\n{resp['response']}\n\n"
        
        # Utiliser le premier LLM disponible pour la fusion
        if self.clients:
            provider = list(self.clients.keys())[0]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            fusion_result = loop.run_until_complete(
                self.query_single_llm(
                    provider,
                    fusion_prompt,
                    "Tu es un expert en synthèse. Fusionne ces analyses en gardant le meilleur de chaque."
                )
            )
            
            if fusion_result['success']:
                return fusion_result['response']
        
        # Fallback: concatenation simple
        return "\n\n".join([f"### {r['provider']}\n{r['response']}" for r in valid_responses])