# verify_all_functions.py
"""Vérifie que TOUTES vos fonctions spécifiques sont bien intégrées"""

import streamlit as st

def verify_function_integration():
    """Vérifie l'intégration de toutes vos fonctions spécifiques"""
    
    st.title("✅ Vérification de l'intégration de VOS modules")
    
    # Liste de VOS fonctions spécifiques à vérifier
    your_functions = {
        'analyse_ia': {
            'module': 'modules.analyse_ia',
            'functions': ['show_page as analyse_ia_page'],
            'expected': 'analyse_ia_page'
        },
        'bordereau': {
            'module': 'modules.bordereau',
            'functions': ['process_bordereau_request', 'create_bordereau'],
            'expected': ['process_bordereau_request', 'create_bordereau']
        },
        'comparison': {
            'module': 'modules.comparison',
            'functions': ['process_comparison_request'],
            'expected': 'process_comparison_request'
        },
        'configuration': {
            'module': 'modules.configuration',
            'functions': ['show_page as config_page'],
            'expected': 'config_page'
        },
        'email': {
            'module': 'modules.email',
            'functions': ['process_email_request'],
            'expected': 'process_email_request'
        },
        'explorer': {
            'module': 'modules.explorer',
            'functions': ['show_explorer_interface'],
            'expected': 'show_explorer_interface'
        },
        'import_export': {
            'module': 'modules.import_export',
            'functions': ['process_import_request', 'process_export_request'],
            'expected': ['process_import_request', 'process_export_request']
        },
        'jurisprudence': {
            'module': 'modules.jurisprudence',
            'functions': ['process_jurisprudence_request', 'show_jurisprudence_interface'],
            'expected': ['process_jurisprudence_request', 'show_jurisprudence_interface']
        },
        'mapping': {
            'module': 'modules.mapping',
            'functions': ['process_mapping_request'],
            'expected': 'process_mapping_request'
        },
        'plaidoirie': {
            'module': 'modules.plaidoirie',
            'functions': ['process_plaidoirie_request'],
            'expected': 'process_plaidoirie_request'
        },
        'preparation_client': {
            'module': 'modules.preparation_client',
            'functions': ['process_preparation_client_request'],
            'expected': 'process_preparation_client_request'
        },
        'redaction_unified': {
            'module': 'modules.redaction_unified',
            'functions': ['process_redaction_request'],
            'expected': 'process_redaction_request'
        },
        'selection_piece': {
            'module': 'modules.selection_piece',
            'functions': ['show_page as selection_piece_page'],
            'expected': 'selection_piece_page'
        },
        'synthesis': {
            'module': 'modules.synthesis',
            'functions': ['process_synthesis_request'],
            'expected': 'process_synthesis_request'
        },
        'templates': {
            'module': 'modules.templates',
            'functions': ['process_template_request'],
            'expected': 'process_template_request'
        },
        'timeline': {
            'module': 'modules.timeline',
            'functions': ['process_timeline_request'],
            'expected': 'process_timeline_request'
        }
    }
    
    # Vérifier recherche_simplified
    st.markdown("## 📋 Vérification de recherche_simplified.py")
    
    try:
        import modules.recherche_simplified as rs
        st.success("✅ Module recherche_simplified.py chargé")
        
        # Vérifier MODULE_FUNCTIONS
        if hasattr(rs, 'MODULE_FUNCTIONS'):
            st.info(f"📊 {len(rs.MODULE_FUNCTIONS)} fonctions importées")
            
            # Vérifier chaque fonction attendue
            total_functions = 0
            imported_functions = 0
            
            for module_name, module_info in your_functions.items():
                st.markdown(f"### {module_name}")
                
                expected = module_info['expected']
                if isinstance(expected, str):
                    expected = [expected]
                
                for func_name in expected:
                    total_functions += 1
                    
                    col1, col2, col3 = st.columns([3, 1, 2])
                    with col1:
                        st.write(f"`{func_name}`")
                    
                    with col2:
                        if func_name in rs.MODULE_FUNCTIONS:
                            st.success("✅")
                            imported_functions += 1
                        else:
                            st.error("❌")
                    
                    with col3:
                        # Vérifier dans le routing
                        routing_check = check_routing(rs, func_name)
                        if routing_check:
                            st.success("✅ Routé")
                        else:
                            st.warning("⚠️ Vérifier routing")
            
            # Résumé
            st.markdown("## 📈 Résumé")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total fonctions", total_functions)
            
            with col2:
                st.metric("Importées", imported_functions)
            
            with col3:
                coverage = (imported_functions / total_functions * 100) if total_functions > 0 else 0
                st.metric("Couverture", f"{coverage:.1f}%")
            
            # Recommandations
            if coverage == 100:
                st.success("""
                🎉 **Parfait !** Toutes vos fonctions sont correctement importées.
                
                Vérifiez maintenant que :
                1. Le routing dans `process_query` appelle bien ces fonctions
                2. Les boutons d'actions rapides utilisent `MODULE_FUNCTIONS`
                3. Les interfaces appellent directement vos fonctions
                """)
            else:
                st.warning("""
                ⚠️ **Intégration incomplète**
                
                Certaines fonctions ne sont pas importées. Vérifiez :
                1. Les imports dans recherche_simplified.py
                2. Les noms de fonctions correspondent exactement
                3. Les modules sont bien présents
                """)
        else:
            st.error("❌ MODULE_FUNCTIONS non trouvé dans recherche_simplified")
            
    except Exception as e:
        st.error(f"❌ Erreur chargement recherche_simplified : {e}")
    
    # Test du routing
    st.markdown("## 🧪 Test du routing")
    
    test_commands = {
        "rédiger document": "process_redaction_request",
        "analyser": "analyse_ia_page",
        "créer bordereau": "process_bordereau_request",
        "jurisprudence": "process_jurisprudence_request ou show_jurisprudence_interface",
        "importer": "process_import_request",
        "exporter": "process_export_request",
        "comparer documents": "process_comparison_request",
        "envoyer email": "process_email_request",
        "timeline": "process_timeline_request",
        "cartographie": "process_mapping_request",
        "plaidoirie": "process_plaidoirie_request",
        "préparer client": "process_preparation_client_request",
        "sélection pièces": "selection_piece_page",
        "synthèse": "process_synthesis_request",
        "templates": "process_template_request",
        "explorer": "show_explorer_interface",
        "configuration": "config_page"
    }
    
    st.markdown("### Commandes à tester :")
    for cmd, expected_func in test_commands.items():
        col1, col2 = st.columns([2, 3])
        with col1:
            st.code(cmd)
        with col2:
            st.caption(f"→ {expected_func}")

def check_routing(module, function_name):
    """Vérifie si la fonction est utilisée dans le routing"""
    try:
        import inspect
        source = inspect.getsource(module.process_query)
        return function_name in source
    except:
        return False

if __name__ == "__main__":
    verify_function_integration()