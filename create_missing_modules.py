# create_missing_modules.py
"""Utility to scaffold missing modules and register them.

This script ensures certain helper modules exist inside the ``modules``
package. When a module is created, its name is stored in
``modules/module_registry.py`` so the rest of the application can detect
its presence. A minimal pytest file is also generated for each module
to verify that the import succeeds.
"""

from __future__ import annotations

import os
import shutil
import json
from pathlib import Path


MODULES_DIR = Path("modules")
REGISTRY_FILE = MODULES_DIR / "module_registry.py"


def _load_registry() -> list[str]:
    """Return the list of registered modules."""
    if not REGISTRY_FILE.exists():
        return []
    namespace: dict[str, list[str]] = {}
    try:
        exec(REGISTRY_FILE.read_text(encoding="utf-8"), namespace)
    except Exception:
        return []
    return list(namespace.get("REGISTERED_MODULES", []))


def _save_registry(modules: list[str]) -> None:
    REGISTRY_FILE.write_text(
        "REGISTERED_MODULES = " + json.dumps(modules, indent=4) + "\n",
        encoding="utf-8",
    )


def register_module(module_name: str) -> None:
    """Add ``module_name`` to ``module_registry.py`` if not already present."""
    modules = _load_registry()
    if module_name not in modules:
        modules.append(module_name)
        _save_registry(modules)
        print(f"✅ Enregistrement de {module_name} dans module_registry")
    else:
        print(f"ℹ️  {module_name} déjà enregistré")


def create_test(module_name: str) -> None:
    """Create a basic pytest file for ``module_name`` if missing."""
    test_path = Path(f"test_{module_name}.py")
    if test_path.exists():
        print(f"ℹ️  {test_path} existe déjà")
        return

    content = (
        f"""# Auto-generated test for modules.{module_name}\n"
        "import importlib\n\n"
        f"def test_import_{module_name}():\n"
        f"    importlib.import_module('modules.{module_name}')\n"
        """
    )
    test_path.write_text(content, encoding="utf-8")
    print(f"✅ Création de {test_path}")


def create_module(module_path: Path, content: str, module_name: str) -> None:
    """Create the module if it doesn't exist and register it."""
    if not module_path.exists():
        module_path.write_text(content, encoding="utf-8")
        print(f"✅ Création de {module_path}")
    else:
        print(f"⚠️  {module_path} existe déjà")

    register_module(module_name)
    create_test(module_name)


def main() -> None:
    MODULES_DIR.mkdir(exist_ok=True)

    # documents_longs.py -------------------------------------------------
    documents_longs_content = """"""Module de gestion des documents longs"""

import streamlit as st
from typing import List, Dict, Any

MODULE_FUNCTIONS = {
    "display_long_documents": "Afficher les documents longs",
    "split_document": "Diviser un document en sections",
    "merge_documents": "Fusionner plusieurs documents",
    "analyze_long_text": "Analyser un texte long",
}


def display_long_documents() -> None:
    """Affiche l'interface de gestion des documents longs."""
    st.header("📄 Documents longs")
    st.info("Module de gestion des documents longs en cours de développement")


def split_document(content: str, max_length: int = 1000) -> List[str]:
    """Divise ``content`` en sections de ``max_length`` caractères."""
    sections: list[str] = []
    words = content.split()
    current_section: list[str] = []
    current_length = 0

    for word in words:
        current_section.append(word)
        current_length += len(word) + 1
        if current_length >= max_length:
            sections.append(" ".join(current_section))
            current_section = []
            current_length = 0

    if current_section:
        sections.append(" ".join(current_section))

    return sections


def merge_documents(documents: List[str]) -> str:
    """Fusionne plusieurs documents."""
    return "\n\n---\n\n".join(documents)


def analyze_long_text(text: str) -> Dict[str, Any]:
    """Analyse un texte long."""
    return {
        "length": len(text),
        "words": len(text.split()),
        "paragraphs": len(text.split("\n\n")),
        "sections": len(split_document(text)),
    }
"""

    create_module(MODULES_DIR / "documents_longs.py", documents_longs_content, "documents_longs")

    # templates.py -------------------------------------------------------
    template_module_content = """"""Module de gestion des templates"""

import streamlit as st
from typing import Dict, List

MODULE_FUNCTIONS = {
    "show_templates": "Afficher les templates",
    "create_template": "Créer un template",
    "load_template": "Charger un template",
    "save_template": "Sauvegarder un template",
}

TEMPLATES = {
    "plainte": "PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE",
    "conclusions": "CONCLUSIONS",
}


def show_templates() -> None:
    """Affiche l'interface des templates."""
    st.header("📑 Templates de documents")
    template_type = st.selectbox("Type de template", list(TEMPLATES.keys()))
    if template_type:
        st.text_area("Contenu du template", value=TEMPLATES[template_type], height=400)


def create_template(name: str, content: str) -> bool:
    """Crée un nouveau template."""
    if name not in TEMPLATES:
        TEMPLATES[name] = content
        return True
    return False


def load_template(name: str) -> str:
    """Charge un template."""
    return TEMPLATES.get(name, "")


def save_template(name: str, content: str) -> bool:
    """Sauvegarde un template."""
    TEMPLATES[name] = content
    return True
"""

    create_module(MODULES_DIR / "templates.py", template_module_content, "templates")

    # generation-longue.py alias -----------------------------------------
    gen_longue_dash = MODULES_DIR / "generation-longue.py"
    gen_longue_under = MODULES_DIR / "generation_longue.py"
    if gen_longue_under.exists() and not gen_longue_dash.exists():
        shutil.copy2(gen_longue_under, gen_longue_dash)
        print("✅ Copie de generation_longue.py vers generation-longue.py")

    print("\n✅ Vérification terminée !")


if __name__ == "__main__":
    main()

