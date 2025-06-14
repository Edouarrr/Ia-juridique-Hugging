"""
Vérificateur d'intégration des fonctions
========================================
Ce module vérifie que toutes les fonctions sont correctement intégrées
"""

import importlib
import inspect
import os
import sys
import traceback
from typing import Dict, List, Tuple

import streamlit as st

# SUPPRIMÉ : st.set_page_config() car déjà appelé dans app.py

def verify_function_integration():
    """Vérifie l'intégration complète de toutes les fonctions"""
    
    st.header("🔍 Vérification de l'intégration des modules")
    
    # Définir les modules à vérifier
    modules_to_check = {
        'recherche': 'modules.recherche',
        'advanced_features': 'modules.advanced_features',
        'analyse_ia': 'modules.analyse_ia',
        'bordereau': 'modules.bordereau',
        'dossier_penal': 'modules.dossier_penal',
        'jurisprudence': 'modules.jurisprudence',
        'pieces_manager': 'modules.pieces_manager',
        'redaction': 'modules.redaction',
        'risques': 'modules.risques',
        'timeline': 'modules.timeline'
    }
    
    # Résultats de vérification
    results = {
        'modules_ok': [],
        'modules_error': [],
        'functions_found': {},
        'integration_status': {}
    }
    
    # Stocker les erreurs pour affichage ultérieur
    error_details = []
    
    # Vérifier chaque module
    for module_name, module_path in modules_to_check.items():
        st.markdown(f"### 📦 Module: {module_name}")
        
        try:
            # Importer le module
            module = importlib.import_module(module_path)
            st.success(f"✅ Module {module_name} importé avec succès")
            results['modules_ok'].append(module_name)
            
            # Vérifier MODULE_FUNCTIONS
            if hasattr(module, 'MODULE_FUNCTIONS'):
                functions = module.MODULE_FUNCTIONS
                st.info(f"📋 {len(functions)} fonctions déclarées dans MODULE_FUNCTIONS")
                results['functions_found'][module_name] = len(functions)
                
                # Vérifier chaque fonction
                missing_funcs = []
                present_funcs = []
                
                for func_name in functions:
                    if hasattr(module, func_name):
                        present_funcs.append(func_name)
                    else:
                        missing_funcs.append(func_name)
                
                # Afficher le résultat
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Fonctions présentes", len(present_funcs))
                    if present_funcs and st.checkbox(f"Voir les fonctions OK ({module_name})", key=f"ok_{module_name}"):
                        for func in present_funcs:
                            st.caption(f"✅ {func}")
                
                with col2:
                    st.metric("Fonctions manquantes", len(missing_funcs))
                    if missing_funcs:
                        st.error("Fonctions manquantes:")
                        for func in missing_funcs:
                            st.caption(f"❌ {func}")
                
                # Vérifier l'intégration dans recherche.py
                if module_name != 'recherche':
                    check_integration_in_recherche(module_name, functions, results)
                
            else:
                st.warning(f"⚠️ MODULE_FUNCTIONS non trouvé dans {module_name}")
                results['functions_found'][module_name] = 0
            
            # Lister toutes les fonctions du module
            all_functions = [name for name, obj in inspect.getmembers(module) 
                           if inspect.isfunction(obj) and not name.startswith('_')]
            
            # Utiliser un simple checkbox au lieu d'un expander
            if st.checkbox(f"Toutes les fonctions dans {module_name} ({len(all_functions)})", key=f"all_{module_name}"):
                for func_name in sorted(all_functions):
                    st.caption(f"• {func_name}")
                
        except ImportError as e:
            st.error(f"❌ Impossible d'importer {module_name}: {str(e)}")
            results['modules_error'].append(module_name)
            error_details.append({
                'module': module_name,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        except Exception as e:
            st.error(f"❌ Erreur lors de la vérification de {module_name}: {str(e)}")
            results['modules_error'].append(module_name)
            error_details.append({
                'module': module_name,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        
        st.divider()
    
    # Afficher les détails des erreurs à la fin
    if error_details:
        st.markdown("### ⚠️ Détails des erreurs")
        for error_info in error_details:
            with st.expander(f"Erreur dans {error_info['module']}"):
                st.error(error_info['error'])
                st.code(error_info['traceback'], language='python')
    
    # Résumé global
    st.markdown("---")
    st.header("📊 Résumé de la vérification")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Modules OK", 
            len(results['modules_ok']),
            delta=f"/{len(modules_to_check)}"
        )
    
    with col2:
        st.metric(
            "Modules en erreur",
            len(results['modules_error'])
        )
    
    with col3:
        total_functions = sum(results['functions_found'].values())
        st.metric(
            "Total fonctions",
            total_functions
        )
    
    # Vérification spéciale de recherche.py
    verify_recherche_integration(results)
    
    # Recommandations
    if results['modules_error']:
        st.markdown("---")
        st.header("🔧 Recommandations")
        st.error(f"**Modules à corriger:** {', '.join(results['modules_error'])}")
        st.info("💡 Assurez-vous que tous les fichiers sont présents dans le dossier `modules/`")
    else:
        st.success("✅ Tous les modules sont correctement importés!")
    
    return results

def check_integration_in_recherche(module_name: str, functions: List[str], results: Dict):
    """Vérifie si les fonctions d'un module sont intégrées dans recherche.py"""
    try:
        from modules import recherche
        
        if hasattr(recherche, 'MODULE_FUNCTIONS'):
            recherche_functions = recherche.MODULE_FUNCTIONS
            integrated = [f for f in functions if f in recherche_functions]
            not_integrated = [f for f in functions if f not in recherche_functions]
            
            if integrated:
                st.success(f"✅ {len(integrated)} fonctions intégrées dans recherche.py")
            if not_integrated:
                st.warning(f"⚠️ {len(not_integrated)} fonctions non intégrées dans recherche.py")
                if st.checkbox(f"Voir les fonctions non intégrées ({module_name})", key=f"not_int_{module_name}"):
                    for func in not_integrated:
                        st.caption(f"• {func}")
            
            results['integration_status'][module_name] = {
                'integrated': len(integrated),
                'not_integrated': len(not_integrated)
            }
    except Exception as e:
        st.error(f"Impossible de vérifier l'intégration: {str(e)}")

def verify_recherche_integration(results: Dict):
    """Vérifie spécifiquement l'intégration dans recherche.py"""
    st.markdown("---")
    st.header("🔍 Vérification du module de recherche unifié")
    
    try:
        from modules import recherche

        # Vérifier la classe UniversalSearchInterface
        if hasattr(recherche, 'UniversalSearchInterface'):
            st.success("✅ Classe UniversalSearchInterface trouvée")
            
            # Vérifier les méthodes importantes
            interface = recherche.UniversalSearchInterface()
            important_methods = [
                'analyze_query',
                'process_request',
                'execute_action',
                'route_to_module'
            ]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Méthodes principales:**")
                for method in important_methods:
                    if hasattr(interface, method):
                        st.caption(f"✅ {method}")
                    else:
                        st.caption(f"❌ {method}")
            
            with col2:
                # Vérifier MODULE_FUNCTIONS
                if hasattr(recherche, 'MODULE_FUNCTIONS'):
                    total_funcs = len(recherche.MODULE_FUNCTIONS)
                    st.metric("Fonctions totales", total_funcs)
                    
                    # Compter par catégorie
                    categories = {}
                    for func in recherche.MODULE_FUNCTIONS:
                        # Deviner la catégorie par le nom
                        if 'rediger' in func or 'creer' in func:
                            cat = 'Rédaction'
                        elif 'analyser' in func:
                            cat = 'Analyse'
                        elif 'rechercher' in func or 'jurisprudence' in func:
                            cat = 'Recherche'
                        elif 'bordereau' in func or 'piece' in func:
                            cat = 'Gestion'
                        else:
                            cat = 'Autre'
                        
                        categories[cat] = categories.get(cat, 0) + 1
                    
                    st.write("**Répartition par type:**")
                    for cat, count in sorted(categories.items()):
                        st.caption(f"• {cat}: {count}")
        else:
            st.error("❌ Classe UniversalSearchInterface non trouvée")
        
        # Vérifier l'intégration des modules
        st.markdown("### 📦 État de l'intégration des modules")
        
        if results.get('integration_status'):
            integrated_total = sum(s['integrated'] for s in results['integration_status'].values())
            not_integrated_total = sum(s['not_integrated'] for s in results['integration_status'].values())
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Fonctions intégrées", integrated_total)
            with col2:
                st.metric("Non intégrées", not_integrated_total)
            
            if not_integrated_total > 0:
                st.warning(f"⚠️ {not_integrated_total} fonctions ne sont pas encore intégrées dans la recherche unifiée")
                
                # Détails par module
                with st.expander("Voir les détails par module"):
                    for module, status in results['integration_status'].items():
                        if status['not_integrated'] > 0:
                            st.write(f"**{module}:** {status['not_integrated']} fonctions non intégrées")
        
    except ImportError:
        st.error("❌ Module recherche.py non trouvé!")
        st.info("Le fichier modules/recherche.py doit exister pour la version unifiée")
    except Exception as e:
        st.error(f"❌ Erreur lors de la vérification: {str(e)}")
        with st.expander("Détails"):
            st.code(traceback.format_exc())

def check_file_structure():
    """Vérifie la structure des fichiers du projet"""
    st.markdown("---")
    st.header("📁 Structure des fichiers")
    
    # Structure attendue
    expected_structure = {
        'modules/': [
            '__init__.py',
            'recherche.py',
            'advanced_features.py',
            'analyse_ia.py',
            'bordereau.py',
            'dossier_penal.py',
            'jurisprudence.py',
            'pieces_manager.py',
            'redaction.py',
            'risques.py',
            'timeline.py'
        ],
        'config/': [
            '__init__.py',
            'app_config.py'
        ],
        'managers/': [
            '__init__.py',
            'azure_blob_manager.py',
            'azure_search_manager.py',
            'universal_search_service.py'
        ],
        'utils/': [
            '__init__.py',
            'helpers.py',
            'styles.py'
        ]
    }
    
    # Vérifier chaque dossier
    for folder, files in expected_structure.items():
        with st.expander(f"📂 {folder}", expanded=False):
            folder_path = folder.rstrip('/')
            if os.path.exists(folder_path):
                st.success(f"✅ Dossier {folder} existe")
                
                # Vérifier chaque fichier
                missing_files = []
                present_files = []
                
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    if os.path.exists(file_path):
                        present_files.append(file)
                    else:
                        missing_files.append(file)
                
                col1, col2 = st.columns(2)
                with col1:
                    if present_files:
                        st.write("**Fichiers présents:**")
                        for f in present_files:
                            st.caption(f"✅ {f}")
                
                with col2:
                    if missing_files:
                        st.write("**Fichiers manquants:**")
                        for f in missing_files:
                            st.caption(f"❌ {f}")
            else:
                st.error(f"❌ Dossier {folder} manquant")

# Fonction principale appelée depuis app.py
def main():
    """Point d'entrée principal"""
    st.title("🔍 Vérification de l'intégration des modules")
    
    # Menu de navigation
    option = st.selectbox(
        "Choisir une vérification",
        ["Intégration complète", "Structure des fichiers", "Test rapide"]
    )
    
    if option == "Intégration complète":
        verify_function_integration()
    elif option == "Structure des fichiers":
        check_file_structure()
    elif option == "Test rapide":
        quick_test()

def quick_test():
    """Test rapide des imports critiques"""
    st.header("⚡ Test rapide")
    
    critical_imports = [
        "from modules import recherche",
        "from managers.azure_blob_manager import AzureBlobManager",
        "from managers.azure_search_manager import AzureSearchManager",
        "from config.app_config import app_config"
    ]
    
    for import_str in critical_imports:
        try:
            exec(import_str)
            st.success(f"✅ {import_str}")
        except Exception as e:
            st.error(f"❌ {import_str}")
            st.caption(str(e))

# Si exécuté directement (ne devrait pas arriver car appelé depuis app.py)
if __name__ == "__main__":
    main()