from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class AIModel(Enum):
    """Models of AI used in the timeline module."""
    CHAT_GPT_4 = "ChatGPT 4"
    CLAUDE_OPUS_4 = "Claude Opus 4"
    PERPLEXITY = "Perplexity"
    GEMINI = "Gemini"
    MISTRAL = "Mistral"
    FUSION = "🔥 Mode Fusion"


@dataclass
class TimelineEvent:
    """Structure d'un événement de la timeline"""
    date: datetime
    description: str
    importance: int = 5
    category: str = "autre"
    actors: List[str] = None
    source: str = ""
    confidence: float = 0.8
    ai_extracted: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.actors is None:
            self.actors = []
        if self.metadata is None:
            self.metadata = {}
