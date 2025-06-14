"""Tests pour la recherche multi-dossier"""

import asyncio
import pytest
pytest.importorskip("streamlit")
import streamlit as st

from utils.session import initialize_session_state
from services.universal_search_service import UniversalSearchService


class MockState:
    def __init__(self):
        self.data = {}
    def __getattr__(self, key):
        return self.data.get(key)
    def __setattr__(self, key, value):
        if key == 'data':
            super().__setattr__(key, value)
        else:
            self.data[key] = value
    def __contains__(self, key):
        return key in self.data


def setup_state():
    st.session_state = MockState()
    initialize_session_state()


def test_search_all_dossiers_basic():
    setup_state()

    st.session_state.imported_documents = {
        "D1_doc1": {
            "title": "Contrat A",
            "content": "contrat de vente pour Vinci",
            "source": "local",
            "type": "contrat",
            "metadata": {"dossier": "D1"},
        },
        "D2_doc1": {
            "title": "Facture",
            "content": "facture simple",
            "source": "local",
            "type": "facture",
            "metadata": {"dossier": "D2"},
        },
    }

    service = UniversalSearchService()
    results = asyncio.run(service.search_all_dossiers("contrat"))

    assert "D1" in results
    assert results["D1"].total_count == 1
    assert "D2" not in results


def test_search_triggers_all_dossiers():
    setup_state()

    st.session_state.imported_documents = {
        "D1_doc1": {
            "title": "Contrat A",
            "content": "contrat A",
            "source": "local",
            "type": "contrat",
            "metadata": {"dossier": "D1"},
        },
        "D2_doc1": {
            "title": "Contrat B",
            "content": "autre contrat",
            "source": "local",
            "type": "contrat",
            "metadata": {"dossier": "D2"},
        },
    }

    service = UniversalSearchService()
    result = asyncio.run(service.search("tous les contrats"))
    assert isinstance(result, dict)
    assert set(result.keys()) == {"D1", "D2"}
