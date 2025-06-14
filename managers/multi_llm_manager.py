# managers/multi_llm_manager.py
"""Gestionnaire unifié pour plusieurs LLMs"""

import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from typing import Any, Dict, List, Optional

import streamlit as st
from utils.prompt_rewriter import rewrite_prompt

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import anthropic
import openai
from openai import AzureOpenAI, OpenAI
import google.generativeai as genai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from groq import Groq

# Import de la configuration
try:
    from config.app_config import LLMProvider
except ImportError:
    # Fallback si l'import échoue
    class LLMProvider:
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        GOOGLE = "google"
        MISTRAL = "mistral"
        GROQ = "groq"

class MultiLLMManager:
    """Gestionnaire pour interroger plusieurs LLMs"""
    
    def __init__(self):
        self.clients = {}
        self._initialize_clients()

    def register_model(self, name: str, client: Any) -> None:
        """Enregistre dynamiquement un client LLM."""
        self.clients[name] = client

    def chat(self, model: str, messages: List[str]) -> str:
        """Envoie des messages au modèle spécifié et renvoie la réponse."""
        client = self.clients.get(model)
        if client is None:
            raise ValueError(f"Model {model} not registered")
        if hasattr(client, "chat"):
            return client.chat(messages)
        raise AttributeError("Client does not support chat")

    @staticmethod
    def _prepend_prioritized_pieces(prompt: str) -> str:
        """Ajoute les pièces prioritaires au début du prompt si présent."""
        pieces = st.session_state.get("pieces_prioritaires")
        if pieces:
            prefix = (
                "Les documents suivants doivent être considérés comme prioritaires : "
                + ", ".join(pieces)
                + ".\n\n"
            )
            return prefix + prompt
        return prompt
    
    def _initialize_clients(self):
        """Initialise les clients pour chaque LLM disponible"""
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.clients["openai"] = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("OpenAI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation OpenAI: {e}")
        
        # Azure OpenAI
        if os.getenv("AZURE_OPENAI_ENDPOINT"):
            try:
                self.clients["azure_openai"] = AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_KEY"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
                )
                logger.info("Azure OpenAI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Azure OpenAI: {e}")
        
        # Anthropic Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.clients["anthropic"] = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                logger.info("Anthropic Claude initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Anthropic: {e}")
        
        # Google Gemini
        if os.getenv("GOOGLE_API_KEY"):
            try:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.clients["google"] = genai.GenerativeModel('gemini-pro')
                logger.info("Google Gemini initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Google Gemini: {e}")
        
        # Mistral
        if os.getenv("MISTRAL_API_KEY"):
            try:
                self.clients["mistral"] = MistralClient(
                    api_key=os.getenv("MISTRAL_API_KEY")
                )
                logger.info("Mistral initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Mistral: {e}")
        
        # Groq
        if os.getenv("GROQ_API_KEY"):
            try:
                self.clients["groq"] = Groq(
                    api_key=os.getenv("GROQ_API_KEY")
                )
                logger.info("Groq initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Groq: {e}")
    
    def query_single_llm(
        self, 
        provider: Any,  # Peut être string ou enum
        prompt: str,
        system_prompt: str = "Tu es un assistant juridique expert en droit pénal des affaires français.",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Interroge un LLM spécifique de manière synchrone"""
        
        # Normaliser le provider en string
        if hasattr(provider, 'value'):
            provider_name = provider.value
            provider_key = provider.name.lower()
        else:
            provider_name = str(provider)
            provider_key = provider_name.lower().replace(' ', '_')
        
        # Mapping pour compatibilité
        provider_mapping = {
            'openai': 'openai',
            'anthropic': 'anthropic',
            'anthropic_claude': 'anthropic',
            'google': 'google',
            'google_gemini': 'google',
            'mistral': 'mistral',
            'mistral_ai': 'mistral',
            'groq': 'groq',
            'azure_openai': 'azure_openai'
        }
        
        provider_key = provider_mapping.get(provider_key, provider_key)

        if provider_key not in self.clients:
            return {
                'success': False,
                'provider': provider_name,
                'error': f"Provider {provider_name} non disponible. Providers disponibles: {list(self.clients.keys())}"
            }
        
        prompt = self._prepend_prioritized_pieces(prompt)

        try:
            start_time = time.time()

            # Rewrite prompt for clarity
            prompt = rewrite_prompt(prompt)

            if provider_key == "openai" or provider_key == "azure_openai":
                response = self._query_openai(provider_key, prompt, system_prompt, temperature, max_tokens)
            elif provider_key == "anthropic":
                response = self._query_claude(prompt, system_prompt, temperature, max_tokens)
            elif provider_key == "google":
                response = self._query_gemini(prompt, system_prompt, temperature, max_tokens)
            elif provider_key == "mistral":
                response = self._query_mistral(prompt, system_prompt, temperature, max_tokens)
            elif provider_key == "groq":
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
        
        model = "gpt-4-turbo-preview"
        if provider_key == "azure_openai":
            model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        
        response = client.chat.completions.create(
            model=model,
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
        client = self.clients["anthropic"]
        
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
        model = self.clients["google"]
        
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
        client = self.clients["mistral"]
        
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
        client = self.clients["groq"]
        
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
        providers: List[Any],
        prompt: str,
        system_prompt: str = "Tu es un assistant juridique expert en droit pénal des affaires français.",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Interroge plusieurs LLMs"""

        prompt = self._prepend_prioritized_pieces(prompt)
        
        # Normaliser les providers
        normalized_providers = []
        for p in providers:
            if hasattr(p, 'value'):
                key = p.name.lower()
            else:
                key = str(p).lower()
            
            # Vérifier si disponible
            if key in self.clients or key.replace('_', '') in self.clients:
                normalized_providers.append(p)
        
        if not normalized_providers:
            return [{
                'success': False,
                'error': 'Aucun provider disponible'
            }]
        
        if parallel:
            return self._query_parallel(normalized_providers, prompt, system_prompt, temperature, max_tokens)
        else:
            return self._query_sequential(normalized_providers, prompt, system_prompt, temperature, max_tokens)
    
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
        return list(self.clients.keys())
    
    def test_connections(self) -> Dict[str, bool]:
        """Teste la connexion à chaque LLM"""
        results = {}
        
        test_prompt = "Réponds simplement 'OK' si tu reçois ce message."
        
        for provider_key in self.clients.keys():
            try:
                result = self.query_single_llm(provider_key, test_prompt, "Réponds uniquement 'OK'.", 0.1, 10)
                results[provider_key] = result['success']
            except:
                results[provider_key] = False
        
        return results
    
    def debug_status(self):
        """Affiche le statut de debug des LLMs"""
        print("=== DEBUG MultiLLMManager ===")
        print(f"Clients initialisés: {list(self.clients.keys())}")
        print(f"Variables d'environnement:")
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY", "GROQ_API_KEY"]:
            value = os.getenv(key)
            print(f"  {key}: {'✅ Défini' if value else '❌ Non défini'}")
        print("="*30)

# Fonction helper pour Streamlit
def display_llm_status():
    """Affiche le statut des LLMs dans Streamlit"""
    llm_manager = MultiLLMManager()
    
    st.markdown("### 🤖 État des IA")
    
    status = llm_manager.test_connections()
    
    if not status:
        st.warning("Aucune IA configurée")
        return
    
    cols = st.columns(len(status))
    for i, (provider, is_connected) in enumerate(status.items()):
        with cols[i]:
            if is_connected:
                st.success(f"✅ {provider}")
            else:
                st.error(f"❌ {provider}")