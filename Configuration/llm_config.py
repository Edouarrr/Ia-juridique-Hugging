# config/llm_config.py
"""Configuration des modèles de langage"""

import streamlit as st
from typing import Optional, Dict, Any
import openai
import anthropic
import google.generativeai as genai
from mistralai.client import MistralClient
from groq import Groq

# Configuration des modèles disponibles
LLM_CONFIGS = {
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default": "gpt-4o-mini",
        "requires_api_key": True,
        "api_key_name": "OPENAI_API_KEY",
        "client_class": "openai"
    },
    "Anthropic": {
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "default": "claude-3-5-sonnet-20241022",
        "requires_api_key": True,
        "api_key_name": "ANTHROPIC_API_KEY",
        "client_class": "anthropic"
    },
    "Google": {
        "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
        "default": "gemini-1.5-flash",
        "requires_api_key": True,
        "api_key_name": "GOOGLE_API_KEY",
        "client_class": "google"
    },
    "Mistral": {
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "open-mistral-7b"],
        "default": "mistral-large-latest",
        "requires_api_key": True,
        "api_key_name": "MISTRAL_API_KEY",
        "client_class": "mistral"
    },
    "Groq": {
        "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "default": "llama-3.1-70b-versatile",
        "requires_api_key": True,
        "api_key_name": "GROQ_API_KEY",
        "client_class": "groq"
    }
}

def get_llm_client(provider: str, api_key: Optional[str] = None):
    """Retourne le client configuré pour le provider spécifié"""
    if not api_key:
        # Essayer de récupérer depuis session_state
        api_key = st.session_state.get(f"{provider.lower()}_api_key")
        
    if not api_key and LLM_CONFIGS[provider]["requires_api_key"]:
        st.error(f"Clé API {provider} non configurée")
        return None
        
    client_type = LLM_CONFIGS[provider]["client_class"]
    
    if client_type == "openai":
        return openai.OpenAI(api_key=api_key)
    elif client_type == "anthropic":
        return anthropic.Anthropic(api_key=api_key)
    elif client_type == "google":
        genai.configure(api_key=api_key)
        return genai
    elif client_type == "mistral":
        return MistralClient(api_key=api_key)
    elif client_type == "groq":
        return Groq(api_key=api_key)
    else:
        raise ValueError(f"Provider non supporté: {provider}")

def get_default_params(provider: str) -> Dict[str, Any]:
    """Retourne les paramètres par défaut pour un provider"""
    base_params = {
        "temperature": 0.7,
        "max_tokens": 4000,
    }
    
    # Paramètres spécifiques par provider
    if provider == "OpenAI":
        base_params.update({
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        })
    elif provider == "Anthropic":
        base_params["max_tokens"] = 4096
    elif provider == "Google":
        base_params.update({
            "top_p": 0.95,
            "top_k": 40
        })
    
    return base_params

def validate_api_key(provider: str, api_key: str) -> bool:
    """Valide une clé API en essayant une requête simple"""
    try:
        client = get_llm_client(provider, api_key)
        if not client:
            return False
            
        # Test simple selon le provider
        if provider == "OpenAI":
            client.models.list()
        elif provider == "Anthropic":
            # Anthropic n'a pas de méthode list, on teste avec un appel minimal
            client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
        elif provider == "Google":
            list(genai.list_models())
        elif provider == "Mistral":
            client.list_models()
        elif provider == "Groq":
            client.models.list()
            
        return True
    except Exception as e:
        st.error(f"Erreur de validation: {str(e)}")
        return False