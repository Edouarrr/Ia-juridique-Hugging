# managers/multi_llm_manager.py
"""Gestionnaire unifié pour plusieurs LLMs"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    from openai import OpenAI, AzureOpenAI
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
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    logger.warning("Mistral SDK non installé")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK non installé")

# Import de la configuration
from config.app_config import LLMProvider

class MultiLLMManager:
    """Gestionnaire pour interroger plusieurs LLMs"""
    
    def __init__(self):
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialise les clients pour chaque LLM disponible"""
        
        # OpenAI
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.clients[LLMProvider.OPENAI] = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("OpenAI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation OpenAI: {e}")
        
        # Azure OpenAI
        if OPENAI_AVAILABLE and os.getenv("AZURE_OPENAI_ENDPOINT"):
            try:
                self.clients["AZURE_OPENAI"] = AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_KEY"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
                )
                logger.info("Azure OpenAI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Azure OpenAI: {e}")
        
        # Anthropic Claude
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.clients[LLMProvider.ANTHROPIC] = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                logger.info("Anthropic Claude initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Anthropic: {e}")
        
        # Google Gemini
        if GOOGLE_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            try:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.clients[LLMProvider.GOOGLE] = genai.GenerativeModel('gemini-pro')
                logger.info("Google Gemini initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Google Gemini: {e}")
        
        # Mistral
        if MISTRAL_AVAILABLE and os.getenv("MISTRAL_API_KEY"):
            try:
                self.clients[LLMProvider.MISTRAL] = MistralClient(
                    api_key=os.getenv("MISTRAL_API_KEY")
                )
                logger.info("Mistral initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Mistral: {e}")
        
        # Groq
        if GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
            try:
                self.clients[LLMProvider.GROQ] = Groq(
                    api_key=os.getenv("GROQ_API_KEY")
                )
                logger.info("Groq initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Groq: {e}")
    
    def query_single_llm(
        self, 
        provider: LLMProvider, 
        prompt: str, 
        system_prompt: str = "Tu es un assistant juridique expert en droit pénal des affaires français.",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Interroge un LLM spécifique de manière synchrone"""
        
        # Vérifier si le provider est une string (pour Azure)
        if isinstance(provider, str):
            provider_key = provider
            provider_name = provider
        else:
            provider_key = provider
            provider_name = provider.value
        
        if provider_key not in self.clients:
            return {
                'success': False,
                'provider': provider_name,
                'error': f"Provider {provider_name} non disponible"
            }
        
        try:
            start_time = time.time()
            
            if provider_key == LLMProvider.OPENAI or provider_key == "AZURE_OPENAI":
                response = self._query_openai(provider_key, prompt, system_prompt, temperature, max_tokens)
            elif provider_key == LLMProvider.ANTHROPIC:
                response = self._query_claude(prompt, system_prompt, temperature, max_tokens)
            elif provider_key == LLMProvider.GOOGLE:
                response = self._query_gemini(prompt, system_prompt, temperature, max_tokens)
            elif provider_key == LLMProvider.MISTRAL:
                response = self._query_mistral(prompt, system_prompt, temperature, max_tokens)
            elif provider_key == LLMProvider.GROQ:
                response = self._query_groq(prompt, system_prompt, temperature, max_tokens)
            else:
                return {
                    'success': False,
                    'provider': provider_name,
                    'error': f"Provider {provider_name} non implémenté"
                }
            
            elapsed_time = time.time() - start_time
            
            return {
                'success': True,
                'provider': provider_name,
                'response': response,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            logger.error(f"Erreur requête {provider_name}: {str(e)}")
            return {
                'success': False,
                'provider': provider_name,
                'error': str(e)
            }
    
    def _query_openai(self, provider_key, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge OpenAI ou Azure OpenAI"""
        client = self.clients[provider_key]
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4") if provider_key == "AZURE_OPENAI" else "gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def _query_claude(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Claude"""
        client = self.clients[LLMProvider.ANTHROPIC]
        
        response = client.messages.create(
            model="claude-3-opus-20240229",
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.content[0].text
    
    def _query_gemini(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Google Gemini"""
        model = self.clients[LLMProvider.GOOGLE]
        
        # Gemini n'a pas de system prompt séparé, on le combine
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens
            }
        )
        
        return response.text
    
    def _query_mistral(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Mistral"""
        client = self.clients[LLMProvider.MISTRAL]
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = client.chat(
            model="mistral-large-latest",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def _query_groq(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Interroge Groq"""
        client = self.clients[LLMProvider.GROQ]
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def query_multiple_llms(
        self,
        providers: List[LLMProvider],
        prompt: str,
        system_prompt: str = "Tu es un assistant juridique expert en droit pénal des affaires français.",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Interroge plusieurs LLMs"""
        
        # Filtrer les providers disponibles
        available_providers = [p for p in providers if p in self.clients]
        
        if not available_providers:
            return [{
                'success': False,
                'error': 'Aucun provider disponible'
            }]
        
        if parallel:
            return self._query_parallel(available_providers, prompt, system_prompt, temperature, max_tokens)
        else:
            return self._query_sequential(available_providers, prompt, system_prompt, temperature, max_tokens)
    
    def _query_parallel(self, providers, prompt, system_prompt, temperature, max_tokens):
        """Interroge les LLMs en parallèle"""
        results = []
        
        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            future_to_provider = {
                executor.submit(
                    self.query_single_llm,
                    provider,
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens
                ): provider for provider in providers
            }
            
            for future in as_completed(future_to_provider):
                result = future.result()
                results.append(result)
        
        return results
    
    def _query_sequential(self, providers, prompt, system_prompt, temperature, max_tokens):
        """Interroge les LLMs en séquence"""
        results = []
        
        for provider in providers:
            result = self.query_single_llm(provider, prompt, system_prompt, temperature, max_tokens)
            results.append(result)
            time.sleep(0.5)  # Petit délai pour éviter le rate limiting
        
        return results
    
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
            
            result = self.query_single_llm(
                provider,
                fusion_prompt,
                "Tu es un expert en synthèse juridique. Fusionne les analyses en gardant le meilleur de chaque."
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
        return [provider.value if hasattr(provider, 'value') else str(provider) for provider in self.clients.keys()]
    
    def test_connections(self) -> Dict[str, bool]:
        """Teste la connexion à chaque LLM"""
        results = {}
        
        test_prompt = "Réponds simplement 'OK' si tu reçois ce message."
        
        for provider in self.clients.keys():
            try:
                result = self.query_single_llm(provider, test_prompt, "Réponds uniquement 'OK'.", 0.1, 10)
                results[provider.value if hasattr(provider, 'value') else str(provider)] = result['success']
            except:
                results[provider.value if hasattr(provider, 'value') else str(provider)] = False
        
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