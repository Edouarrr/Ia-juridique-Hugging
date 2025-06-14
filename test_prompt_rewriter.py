import pytest
pytest.importorskip("streamlit")

from utils.prompt_rewriter import rewrite_prompt
from managers.multi_llm_manager import MultiLLMManager


def test_rewrite_prompt_simple():
    text = "donne-moi le contrat de la société"
    rewritten = rewrite_prompt(text)
    assert "fournis-moi" in rewritten
    assert "convention" in rewritten
    assert "entreprise" in rewritten


def test_integration_query_single_llm(monkeypatch):
    monkeypatch.setattr(MultiLLMManager, "_initialize_clients", lambda self: None)
    manager = MultiLLMManager()
    manager.clients = {"openai": True}

    def fake_query_openai(self, provider_key, prompt, system_prompt, temperature, max_tokens):
        return prompt

    monkeypatch.setattr(MultiLLMManager, "_query_openai", fake_query_openai)

    result = manager.query_single_llm("openai", "donne-moi le contrat", "sys")
    assert result["response"] == rewrite_prompt("donne-moi le contrat")
