import pytest

pytest.importorskip("streamlit")


def test_basic_imports():
    from config.app_config import DocumentType  # noqa: F401
    from modules.dataclasses import Document, Partie  # noqa: F401
    from managers.multi_llm_manager import MultiLLMManager  # noqa: F401
    from managers.unified_document_generator import UnifiedDocumentGenerator  # noqa: F401
    from utils.helpers import initialize_session_state  # noqa: F401


def test_session_state_initialization(monkeypatch):
    import streamlit as st

    class MockSessionState:
        def __init__(self):
            self.data = {}

        def __getattr__(self, key):
            return self.data.get(key)

        def __setattr__(self, key, value):
            if key == "data":
                super().__setattr__(key, value)
            else:
                self.data[key] = value

        def __contains__(self, key):
            return key in self.data

    monkeypatch.setattr(st, "session_state", MockSessionState())
    from utils.helpers import initialize_session_state

    initialize_session_state()
    assert "initialized" in st.session_state.data


def test_unified_generator_instantiation():
    from managers.unified_document_generator import UnifiedDocumentGenerator

    generator = UnifiedDocumentGenerator()
    assert hasattr(generator, "plugins")
