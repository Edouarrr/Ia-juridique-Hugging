# config/ai_models.py
"""Central registry of available AI models."""

AI_MODELS = {
    "gpt4": {
        "name": "GPT-4 Turbo",
        "display_name": "GPT-4 Turbo",
        "provider": "OpenAI",
        "description": "Modèle le plus avancé pour l'analyse complexe",
        "icon": "🧠",
        "strengths": [
            "Raisonnement complexe",
            "Analyse juridique",
            "Créativité"
        ],
        "capabilities": ["text", "analysis", "reasoning", "code"],
        "color": "#10a37f",
        "performance_score": 0.95,
        "speed": "Modéré",
        "quality": 5,
        "cost": 3,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "claude3": {
        "name": "Claude 3 Opus",
        "display_name": "Claude 3 Opus",
        "provider": "Anthropic",
        "description": "IA Anthropic spécialisée en analyse détaillée",
        "icon": "🎭",
        "strengths": [
            "Analyse approfondie",
            "Éthique",
            "Nuance"
        ],
        "capabilities": ["text", "analysis", "ethics", "long_context"],
        "color": "#6b46c1",
        "performance_score": 0.93,
        "speed": "Rapide",
        "quality": 5,
        "cost": 3,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "gemini": {
        "name": "Gemini Pro",
        "display_name": "Gemini Pro",
        "provider": "Google",
        "description": "Modèle Google multimodal performant",
        "icon": "✨",
        "strengths": [
            "Multimodal",
            "Rapidité",
            "Précision"
        ],
        "capabilities": ["text", "analysis", "multimodal", "speed"],
        "color": "#ea4335",
        "performance_score": 0.91,
        "speed": "Rapide",
        "quality": 4,
        "cost": 2,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "mistral": {
        "name": "Mistral Large",
        "display_name": "Mistral Large",
        "provider": "Mistral AI",
        "description": "IA française optimisée pour le juridique",
        "icon": "🇫🇷",
        "strengths": [
            "Droit français",
            "Efficacité",
            "Open Source"
        ],
        "capabilities": ["text", "legal_fr", "efficiency"],
        "color": "#ff6b6b",
        "performance_score": 0.88,
        "speed": "Très rapide",
        "quality": 4,
        "cost": 2,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "llama": {
        "name": "Llama 3",
        "display_name": "Llama 3",
        "provider": "Meta",
        "description": "Modèle Meta open source performant",
        "icon": "🦙",
        "strengths": [
            "Open Source",
            "Personnalisation",
            "Performance"
        ],
        "capabilities": ["text", "customization", "local"],
        "color": "#4285f4",
        "performance_score": 0.85,
        "speed": "Rapide",
        "quality": 3,
        "cost": 1,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "gpt-3.5": {
        "name": "GPT-3.5 Turbo",
        "display_name": "GPT-3.5 Turbo",
        "provider": "OpenAI",
        "description": "Modèle rapide et efficace",
        "icon": "⚡",
        "strengths": [
            "Rapidité",
            "Efficacité",
            "Coût réduit"
        ],
        "speed": "Ultra rapide",
        "quality": 3,
    },
    "mixtral-8x7b": {
        "name": "Mixtral 8x7B",
        "display_name": "Mixtral 8x7B",
        "provider": "mistral",
        "description": "Open source performant",
        "icon": "🔀",
        "strengths": [
            "Open source",
            "Multilangue",
            "Customisable"
        ],
    },
    "llama-2": {
        "name": "Llama 2 70B",
        "display_name": "Llama 2 70B",
        "provider": "Meta",
        "description": "Modèle open source performant",
        "icon": "🦙",
        "strengths": [
            "Open source",
            "Personnalisable",
            "Confidentialité"
        ],
    },
    "llama-3-70b": {
        "name": "Llama 3 70B",
        "display_name": "Llama 3 70B",
        "provider": "Meta",
        "description": "Modèle open-source performant",
        "icon": "🦙",
        "strengths": [
            "Rapidité",
            "Fiabilité",
            "Coût réduit"
        ],
    },
}

# aliases
AI_MODELS["gpt-4"] = AI_MODELS["gpt4"]
AI_MODELS["gpt-4-turbo"] = AI_MODELS["gpt4"]
AI_MODELS["GPT-4"] = AI_MODELS["gpt4"]
AI_MODELS["claude"] = AI_MODELS["claude3"]
AI_MODELS["claude-3"] = AI_MODELS["claude3"]
AI_MODELS["claude-3-opus"] = AI_MODELS["claude3"]
AI_MODELS["claude-3-sonnet"] = AI_MODELS["claude3"]
AI_MODELS["Claude"] = AI_MODELS["claude3"]
AI_MODELS["gemini-pro"] = AI_MODELS["gemini"]
AI_MODELS["Gemini"] = AI_MODELS["gemini"]
AI_MODELS["mistral-large"] = AI_MODELS["mistral"]
AI_MODELS["Mistral"] = AI_MODELS["mistral"]
AI_MODELS["llama-3"] = AI_MODELS["llama"]
AI_MODELS["Llama"] = AI_MODELS["llama"]
AI_MODELS["GPT-3.5"] = AI_MODELS["gpt-3.5"]
AI_MODELS["gpt-3.5-turbo"] = AI_MODELS["gpt-3.5"]

