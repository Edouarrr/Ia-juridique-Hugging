"""Gestion simplifiée de plusieurs modèles LLM."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class LLMModel:
    """Représente un client de modèle de langage."""
    name: str
    client: Any


class MultiLLMManager:
    """Manager minimaliste pour orchestrer plusieurs LLM."""

    def __init__(self) -> None:
        self.clients: Dict[str, Any] = {}

    def register_model(self, name: str, client: Any) -> None:
        """Enregistre un nouveau client LLM."""
        self.clients[name] = client

    def chat(self, model: str, messages: List[str]) -> str:
        """Envoie une conversation au modèle spécifié."""
        if model not in self.clients:
            raise ValueError(f"Model {model} not registered")
        client = self.clients[model]
        if hasattr(client, "chat"):
            return client.chat(messages)
        raise AttributeError("Client does not support chat")
