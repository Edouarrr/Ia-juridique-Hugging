"""
Page de diagnostic pour l'application juridique
Créez un dossier 'pages' et mettez ce fichier dedans
"""

import importlib
import os
import sys
import traceback
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Diagnostic Import",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Diagnostic des Imports")
st.caption(f"Diagnostic réalisé le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")

# Section 1: État général
st.header("1️⃣ État général du système")

col1, col2, col3, col4 = st.columns(4)

# Test modules
with col1:
    try:
        import modules
        loaded = len(modules.get_loaded_modules()) if hasattr(modules, 'get_loaded_modules') else 0
        st.metric("Modules", f"{loaded} chargés", "✅")
    except:
        st.metric("Modules", "Non chargé", "❌")

# Test Azure
with col2:
    try:
        import azure.search.documents
        import azure.storage.blob
        st.metric("Azure SDK", "Disponible", "✅")
    except:
        st.metric("Azure SDK", "Manquant", "❌")

# Test utils
with col3:
    try:
        from utils.session import initialize_session_state
        st.metric("Utils", "OK", "✅")
    except:
        st.metric("Utils", "Erreur", "❌")

# Test models
with col4:
    try:
        from models.dataclasses import Document
        st.metric("Models", "OK", "✅")
    except:
        st.metric("Models", "Erreur", "❌")

# Section 2: Détail des erreurs
st.header("2️⃣ Analyse détaillée des problèmes")

# Fonctions manquantes
st.subheader("🔍 Vérification des fonctions critiques")

critical_checks = [
    ("utils.helpers", "truncate_text", "Fonction requise par synthesis"),
    ("utils.helpers", "clean_key", "Fonction requise par plusieurs modules"),
    ("models.dataclasses", "EmailConfig", "Classe requise par email"),
    ("models.dataclasses", "Relationship", "Classe requise par mapping"),
    ("models.dataclasses", "PlaidoirieResult", "Classe requise par plaidoirie"),
    ("models.dataclasses", "PreparationClientResult", "Classe requise par preparation_client")
]

for module_path, item_name, description in critical_checks:
    col1, col2, col3 = st.columns([2, 1, 3])
    
    with col1:
        st.write(f"**{module_path}.{item_name}**")
    
    with col2:
        try:
            parts = module_path.split('.')
            if len(parts) == 2:
                module = __import__(parts[0], fromlist=[parts[1]])
                submodule = getattr(module, parts[1])
                if hasattr(submodule, item_name):
                    st.success("✅ Trouvé")
                else:
                    st.error("❌ Manquant")
            else:
                module = __import__(module_path)
                if hasattr(module, item_name):
                    st.success("✅ Trouvé")
                else:
                    st.error("❌ Manquant")
        except Exception as e:
            st.error("❌ Erreur")
    
    with col3:
        st.caption(description)

# Section 3: Modules problématiques
st.header("3️⃣ État des modules")

if 'modules' in sys.modules:
    try:
        import modules

        # Utiliser tabs pour organiser
        tab1, tab2, tab3 = st.tabs(["✅ Modules OK", "⚠️ Modules Stub", "❌ Modules en erreur"])
        
        all_modules = modules.MODULES_LIST if hasattr(modules, 'MODULES_LIST') else []
        
        with tab1:
            ok_modules = []
            for mod_name in all_modules:
                status = modules.get_module_status(mod_name) if hasattr(modules, 'get_module_status') else {}
                if status.get('loaded') and not status.get('is_stub'):
                    ok_modules.append((mod_name, status))
            
            if ok_modules:
                for mod_name, status in ok_modules:
                    with st.expander(f"✅ {mod_name} ({status.get('functions_count', 0)} fonctions)"):
                        for func_name, desc in status.get('functions', {}).items():
                            st.write(f"• `{func_name}`: {desc}")
            else:
                st.info("Aucun module chargé correctement")
        
        with tab2:
            stub_modules = []
            for mod_name in all_modules:
                status = modules.get_module_status(mod_name) if hasattr(modules, 'get_module_status') else {}
                if status.get('is_stub'):
                    stub_modules.append((mod_name, status))
            
            if stub_modules:
                for mod_name, status in stub_modules:
                    st.warning(f"⚠️ **{mod_name}**: Module stub (fichier manquant)")
                    if status.get('error'):
                        st.caption(f"Erreur: {status['error']}")
            else:
                st.success("Aucun module stub")
        
        with tab3:
            error_modules = []
            for mod_name in all_modules:
                status = modules.get_module_status(mod_name) if hasattr(modules, 'get_module_status') else {}
                if not status.get('loaded'):
                    error_modules.append((mod_name, status))
            
            if error_modules:
                for mod_name, status in error_modules:
                    with st.expander(f"❌ {mod_name}"):
                        st.error(status.get('error', 'Erreur inconnue'))
            else:
                st.success("Aucune erreur de chargement")
        
    except Exception as e:
        st.error(f"Erreur lors de l'analyse des modules: {e}")
else:
    st.error("Le système de modules n'est pas importé")

# Section 4: Corrections automatiques
st.header("4️⃣ Corrections automatiques")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔧 Corriger utils/helpers.py", use_container_width=True):
        try:
            # Ajouter truncate_text
            with open('utils/helpers.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'def truncate_text' not in content:
                truncate_code = '''

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Tronque un texte à une longueur maximale."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    available_length = max_length - len(suffix)
    if available_length <= 0:
        return suffix
    return text[:available_length] + suffix'''
                
                with open('utils/helpers.py', 'a', encoding='utf-8') as f:
                    f.write(truncate_code)
                
                st.success("✅ Ajouté truncate_text à utils/helpers.py")
            else:
                st.info("truncate_text existe déjà")
                
        except Exception as e:
            st.error(f"Erreur: {e}")

with col2:
    if st.button("🔧 Corriger models/dataclasses.py", use_container_width=True):
        try:
            # Ajouter les classes manquantes
            with open('models/dataclasses.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            classes_to_add = []
            
            if 'class Relationship' not in content:
                classes_to_add.append("""
@dataclass
class Relationship:
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0""")
            
            if 'class PlaidoirieResult' not in content:
                classes_to_add.append("""
@dataclass
class PlaidoirieResult:
    content: str
    success: bool
    structure: Dict[str, str] = field(default_factory=dict)
    arguments_principaux: List[str] = field(default_factory=list)
    duree_estimee: int = 30
    tone: str = "professionnel"
    metadata: Dict[str, Any] = field(default_factory=dict)""")
            
            if 'class PreparationClientResult' not in content:
                classes_to_add.append("""
@dataclass
class PreparationClientResult:
    documents: List[Any] = field(default_factory=list)
    notes: str = ""
    questions_cles: List[str] = field(default_factory=list)
    points_attention: List[str] = field(default_factory=list)
    recommandations: List[str] = field(default_factory=list)
    duree_estimee: int = 60
    agenda: Dict[str, str] = field(default_factory=dict)""")
            
            if classes_to_add:
                with open('models/dataclasses.py', 'a', encoding='utf-8') as f:
                    f.write("\n\n# Classes ajoutées automatiquement")
                    for class_def in classes_to_add:
                        f.write("\n" + class_def)
                
                st.success(f"✅ Ajouté {len(classes_to_add)} classes à models/dataclasses.py")
            else:
                st.info("Toutes les classes existent déjà")
                
        except Exception as e:
            st.error(f"Erreur: {e}")

# Section 5: Rapport
st.header("5️⃣ Rapport de diagnostic")

if st.button("📄 Générer rapport complet"):
    report = f"""RAPPORT DE DIAGNOSTIC - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*60}

1. ÉTAT GÉNÉRAL:
"""
    
    # Test modules
    try:
        import modules
        loaded = modules.get_loaded_modules() if hasattr(modules, 'get_loaded_modules') else {}
        report += f"- Modules: {len(loaded)} chargés sur {len(modules.MODULES_LIST if hasattr(modules, 'MODULES_LIST') else [])}\\n"
    except:
        report += "- Modules: NON CHARGÉ\\n"
    
    # Test des imports critiques
    report += "\\n2. IMPORTS CRITIQUES:\\n"
    for module_path, item_name, _ in critical_checks:
        try:
            parts = module_path.split('.')
            if len(parts) == 2:
                module = __import__(parts[0], fromlist=[parts[1]])
                submodule = getattr(module, parts[1])
                exists = hasattr(submodule, item_name)
            else:
                module = __import__(module_path)
                exists = hasattr(module, item_name)
            
            report += f"- {module_path}.{item_name}: {'OK' if exists else 'MANQUANT'}\\n"
        except:
            report += f"- {module_path}.{item_name}: ERREUR\\n"
    
    # Recommandations
    report += """
3. RECOMMANDATIONS:
- Remplacer modules/__init__.py par la version corrigée
- Ajouter les fonctions manquantes dans utils/helpers.py
- Ajouter les classes manquantes dans models/dataclasses.py
- Redémarrer l'application après les corrections
"""
    
    st.text_area("Rapport", report, height=400)
    
    st.download_button(
        label="💾 Télécharger le rapport",
        data=report,
        file_name=f"diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

# Footer
st.markdown("---")
st.caption("💡 Après avoir appliqué les corrections, redémarrez l'application pour que les changements prennent effet.")