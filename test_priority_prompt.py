import pytest
pytest.importorskip("streamlit")
import streamlit as st
from managers.multi_llm_manager import MultiLLMManager


def test_prepend_prioritized_pieces():
    st.session_state.pieces_prioritaires = ["PV de perquisition", "plainte pénale"]
    original = "Analyse la situation."
    result = MultiLLMManager._prepend_prioritized_pieces(original)
    assert "PV de perquisition" in result
    assert result.endswith(original)


def test_prepend_no_pieces():
    st.session_state.pieces_prioritaires = []
    original = "Analyse la situation."
    result = MultiLLMManager._prepend_prioritized_pieces(original)
    assert result == original

