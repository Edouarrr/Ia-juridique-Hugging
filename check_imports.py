"""Vérification de tous les imports du projet"""

import sys
import traceback
import streamlit as st

def check_all_imports():
    """Vérifie tous les imports critiques du projet et retourne un rapport"""
    
    errors = []
    warnings = []
    success = []
    
    st.header("🔍 Vérification des imports")
    
    # 1. Vérifier les modèles
    with st.expander("📦 MODELS", expanded=True):
        try:
            from models.jurisprudence_models import (
                JurisprudenceReference, VerificationResult, SourceJurisprudence,
                JurisprudenceSearchCriteria, JurisprudenceAnalysis
            )
            st.success("✅ models.jurisprudence_models OK")
            success.append("models.jurisprudence_models")
        except ImportError as e:
            st.error(f"❌ models.jurisprudence_models ERREUR")
            errors.append(f"models.jurisprudence_models: {str(e)}")

        try:
            from models.dataclasses import (
                Document, PieceSelectionnee, DocumentJuridique,
                AnalyseJuridique, CasJuridique, StylePattern,
                SearchPattern, AnalysisResult, ExportConfig,
                SearchResult, UserPreferences, TaskResult
            )
            st.success("✅ models.dataclasses OK")
            success.append("models.dataclasses")
        except ImportError as e:
            st.error(f"❌ models.dataclasses ERREUR")
            errors.append(f"models.dataclasses: {str(e)}")

    # 2. Vérifier les managers
    with st.expander("📦 MANAGERS", expanded=True):
        managers_to_check = [
            ("managers.legal_search", ["LegalSearchManager", "display_legal_search_interface"]),
            ("managers.dynamic_generators", ["generate_dynamic_search_prompts"]),
            ("managers.jurisprudence_verifier", ["JurisprudenceVerifier"]),
            ("managers.azure_blob_manager", ["AzureBlobManager"]),
            ("managers.azure_search_manager", ["AzureSearchManager"]),
            ("managers.multi_llm_manager", ["MultiLLMManager"]),
            ("managers.document_manager", ["display_import_interface"]),
        ]

        for module_name, imports in managers_to_check:
            try:
                module = __import__(module_name, fromlist=imports)
                all_ok = True
                for item in imports:
                    if hasattr(module, item):
                        st.success(f"✅ {module_name}.{item} OK")
                    else:
                        st.warning(f"⚠️ {module_name}.{item} non trouvé")
                        warnings.append(f"{module_name}.{item} non trouvé dans le module")
                        all_ok = False
                if all_ok:
                    success.append(module_name)
            except ImportError as e:
                st.error(f"❌ {module_name} ERREUR")
                errors.append(f"{module_name}: {str(e)}")
            except Exception as e:
                st.error(f"❌ {module_name} ERREUR INATTENDUE")
                errors.append(f"{module_name}: {type(e).__name__}: {str(e)}")

    # 3. Vérifier la config
    with st.expander("📦 CONFIG", expanded=True):
        try:
            from config.app_config import app_config, api_config
            st.success("✅ config.app_config OK")
            success.append("config.app_config")
        except ImportError as e:
            st.error(f"❌ config.app_config ERREUR")
            errors.append(f"config.app_config: {str(e)}")

    # 4. Vérifier les utils
    with st.expander("📦 UTILS", expanded=True):
        try:
            from utils.helpers import initialize_session_state
            st.success("✅ utils.helpers OK")
            success.append("utils.helpers")
        except ImportError as e:
            st.error(f"❌ utils.helpers ERREUR")
            errors.append(f"utils.helpers: {str(e)}")

    # 5. Vérifier les modules
    with st.expander("📦 MODULES", expanded=True):
        modules_to_check = [
            "modules.recherche",
            "modules.advanced_features",
            "modules.analyse_ia",
            "modules.bordereau",
            "modules.dossier_penal",
            "modules.jurisprudence",
            "modules.pieces_manager",
            "modules.redaction",
            "modules.risques",
            "modules.timeline"
        ]
        
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                st.success(f"✅ {module_name} OK")
                success.append(module_name)
            except ImportError as e:
                st.error(f"❌ {module_name} ERREUR")
                errors.append(f"{module_name}: {str(e)}")
            except Exception as e:
                st.error(f"❌ {module_name} ERREUR")
                errors.append(f"{module_name}: {type(e).__name__}: {str(e)}")

    # 6. Vérifier les bibliothèques externes
    with st.expander("📦 BIBLIOTHÈQUES EXTERNES", expanded=False):
        external_libs = {
            "streamlit": "requis",
            "pandas": "optionnel",
            "plotly": "optionnel",
            "networkx": "optionnel",
            "docx": "optionnel",
            "PyPDF2": "optionnel",
            "openpyxl": "optionnel",
            "azure.storage.blob": "requis",
            "azure.search.documents": "requis",
        }

        for lib, status in external_libs.items():
            try:
                if '.' in lib:
                    parts = lib.split('.')
                    module = __import__(parts[0])
                    for part in parts[1:]:
                        module = getattr(module, part)
                else:
                    __import__(lib)
                st.success(f"✅ {lib} OK")
                success.append(f"lib:{lib}")
            except ImportError:
                if status == "requis":
                    st.error(f"❌ {lib} MANQUANT (REQUIS)")
                    errors.append(f"{lib}: bibliothèque requise non installée")
                else:
                    st.warning(f"⚠️ {lib} non installé ({status})")
                    warnings.append(f"{lib}: bibliothèque optionnelle non installée")

    # Résumé
    st.markdown("---")
    st.header("📊 RÉSUMÉ")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Succès", len(success))
    
    with col2:
        st.metric("❌ Erreurs", len(errors))
    
    with col3:
        st.metric("⚠️ Avertissements", len(warnings))

    if errors:
        with st.expander(f"❌ {len(errors)} ERREURS CRITIQUES", expanded=True):
            for i, error in enumerate(errors, 1):
                st.error(f"{i}. {error}")
    
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} AVERTISSEMENTS"):
            for i, warning in enumerate(warnings, 1):
                st.warning(f"{i}. {warning}")
    
    # Retourner le rapport
    return {
        'success': success,
        'errors': errors, 
        'warnings': warnings,
        'total_checked': len(success) + len(errors)
    }

# Fonction principale si exécuté directement
if __name__ == "__main__":
    st.set_page_config(
        page_title="Vérification des imports",
        page_icon="🔍",
        layout="wide"
    )
    
    report = check_all_imports()
    
    if not report['errors']:
        st.balloons()
        st.success("🎉 Tous les imports critiques fonctionnent!")
    else:
        st.error("⚠️ Des imports critiques sont manquants. Corrigez-les avant de déployer.")