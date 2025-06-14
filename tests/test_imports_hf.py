import pytest
pytest.importorskip("aiohttp")

def test_jurisprudence_reference_same_class():
    from models.jurisprudence_models import JurisprudenceReference
    from modules.dataclasses import JurisprudenceReference as JR2

    assert JurisprudenceReference is JR2


def test_managers_importable():
    from managers.jurisprudence_verifier import JurisprudenceVerifier  # noqa: F401
    from managers.legal_search import LegalSearchManager  # noqa: F401
