#!/usr/bin/env python3
"""
Script de correction des imports pour Hugging Face
À exécuter dans votre espace Hugging Face
"""

import os


def add_truncate_text_to_helpers():
    """Ajoute la fonction truncate_text à utils/helpers.py"""
    
    helpers_path = 'utils/helpers.py'
    
    # Vérifier si truncate_text existe déjà
    try:
        with open(helpers_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'def truncate_text' in content:
            print("✅ truncate_text existe déjà dans utils/helpers.py")
            return
        
        # Ajouter la fonction à la fin
        truncate_function = '''

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.
    
    Args:
        text: Le texte à tronquer
        max_length: La longueur maximale (par défaut 100)
        suffix: Le suffixe à ajouter (par défaut "...")
        
    Returns:
        Le texte tronqué
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Calculer la longueur disponible pour le texte
    available_length = max_length - len(suffix)
    
    if available_length <= 0:
        return suffix
    
    # Tronquer et ajouter le suffixe
    return text[:available_length] + suffix
'''
        
        with open(helpers_path, 'a', encoding='utf-8') as f:
            f.write(truncate_function)
        
        print("✅ Ajouté truncate_text à utils/helpers.py")
        
    except Exception as e:
        print(f"❌ Erreur avec utils/helpers.py: {e}")

def add_classes_to_dataclasses():
    """Ajoute les classes manquantes à models/dataclasses.py"""
    
    dataclasses_path = 'models/dataclasses.py'
    
    try:
        with open(dataclasses_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les classes existent déjà
        if 'class EmailConfig' in content:
            print("✅ Les classes supplémentaires existent déjà dans models/dataclasses.py")
            return
        
        # Classes à ajouter
        additional_classes = '''

# ========== CLASSES AJOUTÉES POUR COMPATIBILITÉ ==========

@dataclass
class EmailConfig:
    """Configuration pour l'envoi d'emails"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender: str = ""
    password: str = ""
    use_tls: bool = True

@dataclass
class Relationship:
    """Relation entre deux entités"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0

@dataclass
class PlaidoirieResult:
    """Résultat de génération de plaidoirie"""
    content: str
    success: bool
    structure: Dict[str, str] = field(default_factory=dict)
    arguments_principaux: List[str] = field(default_factory=list)
    duree_estimee: int = 30
    tone: str = "professionnel"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreparationClientResult:
    """Résultat de préparation client"""
    documents: List[Any] = field(default_factory=list)
    notes: str = ""
    questions_cles: List[str] = field(default_factory=list)
    points_attention: List[str] = field(default_factory=list)
    recommandations: List[str] = field(default_factory=list)
    duree_estimee: int = 60
    agenda: Dict[str, str] = field(default_factory=dict)

# Mettre à jour __all__ si nécessaire
try:
    __all__.extend([
        'EmailConfig',
        'Relationship',
        'PlaidoirieResult',
        'PreparationClientResult'
    ])
except:
    pass
'''
        
        with open(dataclasses_path, 'a', encoding='utf-8') as f:
            f.write(additional_classes)
        
        print("✅ Ajouté les classes manquantes à models/dataclasses.py")
        
    except Exception as e:
        print(f"❌ Erreur avec models/dataclasses.py: {e}")

def create_documents_longs_module():
    """Crée le module documents_longs.py s'il n'existe pas"""
    
    module_path = 'modules/documents_longs.py'
    
    if os.path.exists(module_path):
        print("✅ modules/documents_longs.py existe déjà")
        return
    
    content = '''"""Module de gestion des documents longs"""

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
    
    try:
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Créé modules/documents_longs.py")
    except Exception as e:
        print(f"❌ Erreur lors de la création de documents_longs.py: {e}")

def check_templates_alias():
    """Vérifie et crée l'alias templates si nécessaire"""
    
    template_path = 'modules/template.py'
    templates_path = 'modules/templates.py'
    
    if os.path.exists(templates_path):
        print("✅ modules/templates.py existe déjà")
    elif os.path.exists(template_path):
        # Créer une copie ou un lien
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(templates_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Créé modules/templates.py depuis template.py")
        except Exception as e:
            print(f"⚠️ Impossible de créer templates.py: {e}")
    else:
        print("⚠️ Ni template.py ni templates.py n'existent")

def main():
    """Applique toutes les corrections"""
    
    print("🔧 Application des corrections pour les imports...")
    print("=" * 60)
    
    # 1. Ajouter truncate_text à helpers
    print("\n1️⃣ Correction de utils/helpers.py...")
    add_truncate_text_to_helpers()
    
    # 2. Ajouter les classes manquantes
    print("\n2️⃣ Correction de models/dataclasses.py...")
    add_classes_to_dataclasses()
    
    # 3. Créer documents_longs si nécessaire
    print("\n3️⃣ Vérification de modules/documents_longs.py...")
    create_documents_longs_module()
    
    # 4. Vérifier templates
    print("\n4️⃣ Vérification de modules/templates.py...")
    check_templates_alias()
    
    print("\n" + "=" * 60)
    print("✅ Corrections appliquées !")
    print("\n⚠️ IMPORTANT: Vous devez encore remplacer modules/__init__.py")
    print("   avec la version corrigée fournie précédemment.")
    
    # Test rapide
    print("\n🧪 Test rapide des imports...")
    try:
        import modules
        loaded = len(modules.get_loaded_modules()) if hasattr(modules, 'get_loaded_modules') else 0
        print(f"✅ {loaded} modules chargés")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()