import pytest
pytest.importorskip("aiohttp")

from managers.unified_document_generator import (
    DocumentLength,
    UnifiedDocumentGenerator,
    UnifiedGenerationRequest,
)
from config.app_config import DocumentType
from modules.dataclasses import Partie, StyleRedaction


def test_generation_request_creation():
    request = UnifiedGenerationRequest(
        document_type=DocumentType.CONCLUSIONS,
        parties={"demandeur": [Partie(nom="A", type="pm", role="demandeur")]},
        infractions=[],
        contexte="test",
        style=StyleRedaction.PROFESSIONNEL,
        length=DocumentLength.SHORT,
    )

    assert request.document_type == DocumentType.CONCLUSIONS


def test_generator_can_instantiate():
    generator = UnifiedDocumentGenerator()
    assert hasattr(generator, "plugins")
