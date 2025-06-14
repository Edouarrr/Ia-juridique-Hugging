import sys
import types
import importlib

import pytest


def load_enhanced_ui(monkeypatch):
    """Import enhanced_ui with a minimal streamlit stub."""
    dummy = types.ModuleType("streamlit")
    dummy.set_page_config = lambda *a, **k: None
    dummy.components = types.SimpleNamespace(v1=types.SimpleNamespace())
    dummy.markdown = lambda *a, **k: None
    dummy.text_area = lambda *a, **k: ""
    dummy.selectbox = lambda *a, **k: ""
    dummy.multiselect = lambda *a, **k: []
    dummy.radio = lambda *a, **k: ""
    dummy.button = lambda *a, **k: False
    dummy.columns = lambda n: [types.SimpleNamespace(__enter__=lambda self: self,
                                                    __exit__=lambda self, exc, val, tb: False) for _ in range(n)]
    dummy.session_state = {}
    dummy.error = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "streamlit", dummy)
    monkeypatch.setitem(sys.modules, "streamlit.components", types.ModuleType("components"))
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", types.ModuleType("v1"))
    # Stub external modules required by enhanced_ui
    dummy_app = types.ModuleType("app")
    dummy_app.ModuleManager = object
    monkeypatch.setitem(sys.modules, "app", dummy_app)

    mlm = types.ModuleType("managers.multi_llm_manager")
    mlm.MultiLLMManager = object
    monkeypatch.setitem(sys.modules, "managers.multi_llm_manager", mlm)
    return importlib.import_module("enhanced_ui")


def _patch_modules(monkeypatch, ui, export=None, index=None, timeline=None):
    if export is None:
        export = lambda folder: None
    if index is None:
        index = lambda folder: None
    if timeline is None:
        timeline = lambda folder: None
    monkeypatch.setattr(ui, "export_manager", types.SimpleNamespace(export=export))
    monkeypatch.setattr(ui, "azure_indexer", types.SimpleNamespace(index_folder=index))
    monkeypatch.setattr(ui, "timeline_generator", types.SimpleNamespace(generate=timeline))
    dummy_st = types.SimpleNamespace(error=lambda msg: errors.append(msg))
    errors.clear()
    monkeypatch.setattr(ui, "st", dummy_st)
    return dummy_st

errors = []


def test_export_command(monkeypatch):
    ui = load_enhanced_ui(monkeypatch)
    calls = {}
    def export(folder):
        calls["folder"] = folder
    _patch_modules(monkeypatch, ui, export=export)
    assert ui.handle_command("#export", "dir") is True
    assert calls["folder"] == "dir"
    assert errors == []


def test_index_command(monkeypatch):
    ui = load_enhanced_ui(monkeypatch)
    calls = {}
    def index_folder(folder):
        calls["folder"] = folder
    _patch_modules(monkeypatch, ui, index=index_folder)
    assert ui.handle_command("#index", "dir") is True
    assert calls["folder"] == "dir"
    assert errors == []


def test_timeline_command(monkeypatch):
    ui = load_enhanced_ui(monkeypatch)
    calls = {}
    def generate(folder):
        calls["folder"] = folder
    _patch_modules(monkeypatch, ui, timeline=generate)
    assert ui.handle_command("#timeline", "dir") is True
    assert calls["folder"] == "dir"
    assert errors == []


def test_unknown_command(monkeypatch):
    ui = load_enhanced_ui(monkeypatch)
    _patch_modules(monkeypatch, ui)
    assert ui.handle_command("#unknown", "dir") is False
    assert errors

