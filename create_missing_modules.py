# create_missing_modules.py
"""
Script pour créer les modules manquants et corriger les noms
À exécuter à la racine du projet
"""

import os
import shutil

def create_module_if_missing(module_path: str, content: str):
    """Crée un module s'il n'existe pas"""
    if not os.path.exists(module_path):
        print(f"✅ Création de {module_path}")
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"⚠️  {module_path} existe déjà")

def main():
    """Crée les modules manquants et corrige les noms"""
    
    modules_dir = "modules"
    
    # 1. Créer le module documents_longs.py
    documents_longs_content = '''"""Module de gestion des documents longs"""

import streamlit as st
from typing import List, Dict, Any

MODULE_FUNCTIONS = {
    "display_long_documents": "Afficher les documents longs",
    "split_document": "Diviser un document en sections",
    "merge_documents": "Fusionner plusieurs documents",
    "analyze_long_text": "Analyser un texte long"
}

def display_long_documents():
    """Affiche l'interface de gestion des documents longs"""
    st.header("📄 Documents longs")
    st.info("Module de gestion des documents longs en cours de développement")
    
def split_document(content: str, max_length: int = 1000) -> List[str]:
    """Divise un document en sections"""
    sections = []
    words = content.split()
    current_section = []
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
    """Fusionne plusieurs documents"""
    return "\\n\\n---\\n\\n".join(documents)

def analyze_long_text(text: str) -> Dict[str, Any]:
    """Analyse un texte long"""
    return {
        "length": len(text),
        "words": len(text.split()),
        "paragraphs": len(text.split("\\n\\n")),
        "sections": len(split_document(text))
    }
'''
    
    create_module_if_missing(
        os.path.join(modules_dir, "documents_longs.py"),
        documents_longs_content
    )
    
    # 2. Renommer template.py en templates.py si nécessaire
    template_path = os.path.join(modules_dir, "template.py")
    templates_path = os.path.join(modules_dir, "templates.py")
    
    if os.path.exists(template_path) and not os.path.exists(templates_path):
        print(f"📝 Copie de template.py vers templates.py")
        shutil.copy2(template_path, templates_path)
    elif os.path.exists(templates_path):
        print(f"✅ templates.py existe déjà")
    else:
        print(f"⚠️  Ni template.py ni templates.py n'existent")
        
        # Créer templates.py
        templates_content = '''"""Module de gestion des templates"""

import streamlit as st
from typing import Dict, List

MODULE_FUNCTIONS = {
    "show_templates": "Afficher les templates",
    "create_template": "Créer un template",
    "load_template": "Charger un template",
    "save_template": "Sauvegarder un template"
}

# Templates prédéfinis
TEMPLATES = {
    "plainte": """PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE

POUR : [NOM DU PLAIGNANT]

CONTRE : [NOM DU MIS EN CAUSE]

FAITS :
[Description des faits]

QUALIFICATION JURIDIQUE :
[Articles du code pénal]

PREJUDICE :
[Description du préjudice]

PAR CES MOTIFS :
[Demandes]
""",
    "conclusions": """CONCLUSIONS

POUR : [CLIENT]

RAPPEL DES FAITS :
[Résumé des faits]

DISCUSSION :
[Arguments juridiques]

PAR CES MOTIFS :
[Demandes au tribunal]
"""
}

def show_templates():
    """Affiche l'interface des templates"""
    st.header("📑 Templates de documents")
    
    template_type = st.selectbox(
        "Type de template",
        list(TEMPLATES.keys())
    )
    
    if template_type:
        st.text_area(
            "Contenu du template",
            value=TEMPLATES[template_type],
            height=400
        )

def create_template(name: str, content: str) -> bool:
    """Crée un nouveau template"""
    if name not in TEMPLATES:
        TEMPLATES[name] = content
        return True
    return False

def load_template(name: str) -> str:
    """Charge un template"""
    return TEMPLATES.get(name, "")

def save_template(name: str, content: str) -> bool:
    """Sauvegarde un template"""
    TEMPLATES[name] = content
    return True
'''
        
        create_module_if_missing(templates_path, templates_content)
    
    # 3. Vérifier generation-longue.py vs generation_longue.py
    gen_longue_dash = os.path.join(modules_dir, "generation-longue.py")
    gen_longue_under = os.path.join(modules_dir, "generation_longue.py")
    
    if os.path.exists(gen_longue_dash):
        print(f"✅ generation-longue.py existe (avec tiret)")
        # Note: Le nouveau __init__.py gère déjà ce cas
    elif os.path.exists(gen_longue_under):
        print(f"📝 generation_longue.py existe (avec underscore)")
        # Optionnel: créer un lien ou copie avec tiret
        print(f"   → Copie vers generation-longue.py pour compatibilité")
        shutil.copy2(gen_longue_under, gen_longue_dash)
    else:
        print(f"⚠️  Aucun module generation-longue trouvé")
    
    print("\n✅ Vérification terminée !")
    print("\n📝 N'oubliez pas d'ajouter les classes manquantes dans:")
    print("   - models/dataclasses.py (voir dataclasses_additions)")
    print("   - utils/helpers.py (voir helpers_additions)")

if __name__ == "__main__":
    main()