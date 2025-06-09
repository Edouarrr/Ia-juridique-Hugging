# modules/recherche_simplified.py
"""Module de recherche universelle simplifié - Sans redondances"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import re

# ========================= CONFIGURATION =========================

# Vérifier quels modules sont disponibles
MODULES_AVAILABLE = {
    'analyse_ia': False,
    'bordereau': False,
    'comparison': False,
    'configuration': False,
    'email': False,
    'explorer': False,
    'import_export': False,
    'jurisprudence': False,
    'mapping': False,
    'plaidoirie': False,
    'preparation_client': False,
    'redaction_unified': False,
    'selection_piece': False,
    'synthesis': False,
    'templates': False,
    'timeline': False,
    'advanced_features': False
}

# Vérifier chaque module
for module_name in MODULES_AVAILABLE.keys():
    try:
        __import__(f'modules.{module_name}')
        MODULES_AVAILABLE[module_name] = True
    except ImportError:
        pass

# ========================= IMPORTS COMPLETS DE VOS MODULES =========================

# Tenter d'importer TOUTES les fonctions spécifiques de vos modules
MODULE_FUNCTIONS = {}

# Analyse IA
try:
    from modules.analyse_ia import show_page as analyse_ia_page
    MODULE_FUNCTIONS['analyse_ia_page'] = analyse_ia_page
except ImportError:
    pass

# Bordereau
try:
    from modules.bordereau import process_bordereau_request, create_bordereau
    MODULE_FUNCTIONS['process_bordereau_request'] = process_bordereau_request
    MODULE_FUNCTIONS['create_bordereau'] = create_bordereau
except ImportError:
    pass

# Comparison
try:
    from modules.comparison import process_comparison_request
    MODULE_FUNCTIONS['process_comparison_request'] = process_comparison_request
except ImportError:
    pass

# Configuration
try:
    from modules.configuration import show_page as config_page
    MODULE_FUNCTIONS['config_page'] = config_page
except ImportError:
    pass

# Email
try:
    from modules.email import process_email_request
    MODULE_FUNCTIONS['process_email_request'] = process_email_request
except ImportError:
    pass

# Explorer
try:
    from modules.explorer import show_explorer_interface
    MODULE_FUNCTIONS['show_explorer_interface'] = show_explorer_interface
except ImportError:
    pass

# Import/Export
try:
    from modules.import_export import process_import_request, process_export_request
    MODULE_FUNCTIONS['process_import_request'] = process_import_request
    MODULE_FUNCTIONS['process_export_request'] = process_export_request
except ImportError:
    pass

# Jurisprudence
try:
    from modules.jurisprudence import process_jurisprudence_request, show_jurisprudence_interface
    MODULE_FUNCTIONS['process_jurisprudence_request'] = process_jurisprudence_request
    MODULE_FUNCTIONS['show_jurisprudence_interface'] = show_jurisprudence_interface
except ImportError:
    pass

# Mapping
try:
    from modules.mapping import process_mapping_request
    MODULE_FUNCTIONS['process_mapping_request'] = process_mapping_request
except ImportError:
    pass

# Plaidoirie
try:
    from modules.plaidoirie import process_plaidoirie_request
    MODULE_FUNCTIONS['process_plaidoirie_request'] = process_plaidoirie_request
except ImportError:
    pass

# Préparation client
try:
    from modules.preparation_client import process_preparation_client_request
    MODULE_FUNCTIONS['process_preparation_client_request'] = process_preparation_client_request
except ImportError:
    pass

# Rédaction unifiée
try:
    from modules.redaction_unified import process_redaction_request
    MODULE_FUNCTIONS['process_redaction_request'] = process_redaction_request
except ImportError:
    pass

# Sélection de pièces
try:
    from modules.selection_piece import show_page as selection_piece_page
    MODULE_FUNCTIONS['selection_piece_page'] = selection_piece_page
except ImportError:
    pass

# Synthèse
try:
    from modules.synthesis import process_synthesis_request
    MODULE_FUNCTIONS['process_synthesis_request'] = process_synthesis_request
except ImportError:
    pass

# Templates
try:
    from modules.templates import process_template_request
    MODULE_FUNCTIONS['process_template_request'] = process_template_request
except ImportError:
    pass

# Timeline
try:
    from modules.timeline import process_timeline_request
    MODULE_FUNCTIONS['process_timeline_request'] = process_timeline_request
except ImportError:
    pass

# ========================= INTERFACE PRINCIPALE =========================

def show_page():
    """Page principale de recherche universelle simplifiée avec TOUS vos modules"""
    
    st.title("🔍 Recherche Universelle")
    st.markdown("---")
    
    # État des modules avec détail des fonctions
    if st.checkbox("🔧 Voir l'état détaillé des modules"):
        show_modules_status()
    
    # Barre de recherche principale
    search_container = st.container()
    with search_container:
        # Gérer la valeur de recherche
        initial_value = ""
        if 'pending_search' in st.session_state:
            initial_value = st.session_state.pending_search
            del st.session_state.pending_search
        
        query = st.text_area(
            "💬 Que souhaitez-vous faire ?",
            value=initial_value,
            placeholder="Ex: 'rédiger une plainte contre VINCI', 'analyser les risques', 'créer un bordereau', etc.",
            height=100,
            key="universal_search_query"
        )
        
        col1, col2, col3 = st.columns([2, 2, 6])
        with col1:
            if st.button("🔍 Rechercher", type="primary", use_container_width=True):
                if query:
                    process_query(query)
        
        with col2:
            if st.button("🗑️ Effacer", use_container_width=True):
                st.session_state.universal_search_query = ""
                st.session_state.search_results = None
                st.rerun()
    
    # Suggestions et actions rapides
    st.markdown("### 💡 Actions rapides")
    show_quick_actions()
    
    # Afficher les résultats
    if st.session_state.get('search_results') or st.session_state.get('generated_plainte') or st.session_state.get('synthesis_result'):
        show_results()
    
    # Footer avec statistiques
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"📊 {len(MODULE_FUNCTIONS)} fonctions disponibles")
    
    with col2:
        modules_count = sum(1 for v in MODULES_AVAILABLE.values() if v)
        st.caption(f"📦 {modules_count} modules actifs")
    
    with col3:
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

def show_modules_status():
    """Affiche l'état des modules disponibles avec leurs fonctions spécifiques"""
    with st.expander("🔧 État des modules et fonctions", expanded=False):
        # Compter les modules et fonctions
        modules_count = sum(1 for v in MODULES_AVAILABLE.values() if v)
        functions_count = len(MODULE_FUNCTIONS)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Modules disponibles", modules_count)
        with col2:
            st.metric("Fonctions importées", functions_count)
        
        st.markdown("### 📋 Détail des fonctions disponibles")
        
        # Grouper les fonctions par module
        function_groups = {
            'Analyse IA': ['analyse_ia_page'],
            'Bordereau': ['process_bordereau_request', 'create_bordereau'],
            'Comparaison': ['process_comparison_request'],
            'Configuration': ['config_page'],
            'Email': ['process_email_request'],
            'Explorer': ['show_explorer_interface'],
            'Import/Export': ['process_import_request', 'process_export_request'],
            'Jurisprudence': ['process_jurisprudence_request', 'show_jurisprudence_interface'],
            'Mapping': ['process_mapping_request'],
            'Plaidoirie': ['process_plaidoirie_request'],
            'Préparation client': ['process_preparation_client_request'],
            'Rédaction': ['process_redaction_request'],
            'Sélection pièces': ['selection_piece_page'],
            'Synthèse': ['process_synthesis_request'],
            'Templates': ['process_template_request'],
            'Timeline': ['process_timeline_request']
        }
        
        # Afficher par groupe
        for group_name, functions in function_groups.items():
            available_funcs = [f for f in functions if f in MODULE_FUNCTIONS]
            if available_funcs:
                st.write(f"**{group_name}** ✅")
                for func in available_funcs:
                    st.caption(f"  • {func}")
            else:
                st.write(f"**{group_name}** ❌")
        
        # Modules avancés
        st.markdown("### 🚀 Modules avancés")
        if MODULES_AVAILABLE['advanced_features']:
            st.success("✅ Module advanced_features disponible")
            st.caption("Inclut : plaintes avancées, gestion documentaire, multi-IA, statistiques...")
        else:
            st.warning("❌ Module advanced_features non disponible")

def show_quick_actions():
    """Affiche les boutons d'actions rapides avec VOS fonctions spécifiques"""
    
    # Première ligne d'actions principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Rédiger", use_container_width=True):
            if 'process_redaction_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_redaction_request']("rédiger", SimpleAnalysis(""))
            else:
                generate_simple_document()
    
    with col2:
        if st.button("📊 Analyser", use_container_width=True):
            if 'analyse_ia_page' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['analyse_ia_page']()
            else:
                st.info("Module d'analyse non disponible")
    
    with col3:
        if st.button("📁 Importer", use_container_width=True):
            if 'process_import_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_import_request']("importer", SimpleAnalysis(""))
            else:
                st.info("Module d'import non disponible")
    
    with col4:
        if st.button("📋 Bordereau", use_container_width=True):
            if 'process_bordereau_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_bordereau_request']("bordereau", SimpleAnalysis(""))
            elif MODULES_AVAILABLE['advanced_features']:
                st.session_state.pending_search = "créer bordereau"
                st.rerun()
            else:
                st.info("Module bordereau non disponible")
    
    # Deuxième ligne d'actions juridiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚖️ Jurisprudence", use_container_width=True):
            if 'show_jurisprudence_interface' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['show_jurisprudence_interface']()
            elif 'process_jurisprudence_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_jurisprudence_request']("", SimpleAnalysis(""))
            else:
                st.info("Module jurisprudence non disponible")
    
    with col2:
        if st.button("🗺️ Cartographie", use_container_width=True):
            if 'process_mapping_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_mapping_request']("mapping", SimpleAnalysis(""))
            else:
                st.info("Module cartographie non disponible")
    
    with col3:
        if st.button("📧 Email", use_container_width=True):
            if 'process_email_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_email_request']("email", SimpleAnalysis(""))
            else:
                st.info("Module email non disponible")
    
    with col4:
        if st.button("⏱️ Timeline", use_container_width=True):
            if 'process_timeline_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_timeline_request']("timeline", SimpleAnalysis(""))
            else:
                st.info("Module timeline non disponible")
    
    # Troisième ligne - Modules spécialisés
    st.markdown("### 📚 Modules spécialisés")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎤 Plaidoirie", use_container_width=True, key="plaidoirie_btn"):
            if 'process_plaidoirie_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_plaidoirie_request']("plaidoirie", SimpleAnalysis(""))
            else:
                st.info("Module plaidoirie non disponible")
    
    with col2:
        if st.button("👥 Prép. Client", use_container_width=True, key="prep_client_btn"):
            if 'process_preparation_client_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_preparation_client_request']("préparer client", SimpleAnalysis(""))
            else:
                st.info("Module préparation client non disponible")
    
    with col3:
        if st.button("🔄 Comparaison", use_container_width=True, key="comparison_btn"):
            if 'process_comparison_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_comparison_request']("comparer", SimpleAnalysis(""))
            else:
                st.info("Module comparaison non disponible")
    
    with col4:
        if st.button("📂 Explorer", use_container_width=True, key="explorer_btn"):
            if 'show_explorer_interface' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['show_explorer_interface']()
            else:
                st.info("Module explorer non disponible")
    
    # Quatrième ligne - Gestion avancée
    st.markdown("### 🚀 Fonctionnalités avancées")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 Sélection pièces", use_container_width=True, key="select_pieces_btn"):
            if 'selection_piece_page' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['selection_piece_page']()
            elif MODULES_AVAILABLE['advanced_features']:
                show_piece_selection_advanced(SimpleAnalysis(""))
            else:
                st.info("Module sélection non disponible")
    
    with col2:
        if st.button("📄 Synthèse", use_container_width=True, key="synthesis_btn"):
            if 'process_synthesis_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_synthesis_request']("synthèse", SimpleAnalysis(""))
            elif st.session_state.get('selected_pieces') and MODULES_AVAILABLE['advanced_features']:
                from modules.advanced_features import synthesize_selected_pieces
                asyncio.run(synthesize_selected_pieces(st.session_state.selected_pieces))
            else:
                st.warning("Sélectionnez d'abord des pièces")
    
    with col3:
        if st.button("📑 Templates", use_container_width=True, key="templates_btn"):
            if 'process_template_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_template_request']("templates", SimpleAnalysis(""))
            else:
                st.info("Module templates non disponible")
    
    with col4:
        if st.button("⚙️ Config", use_container_width=True, key="config_btn"):
            if 'config_page' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['config_page']()
            else:
                st.info("Module configuration non disponible")
    
    # Cinquième ligne - Outils IA avancés (si disponibles)
    if MODULES_AVAILABLE['advanced_features']:
        st.markdown("### 🤖 Intelligence Artificielle")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Recherche juridique", use_container_width=True, key="adv_search"):
                from modules.advanced_features import perform_legal_search
                asyncio.run(perform_legal_search(""))
        
        with col2:
            if st.button("🤖 Multi-IA", use_container_width=True, key="adv_multi"):
                from modules.advanced_features import enhanced_multi_llm_comparison
                asyncio.run(enhanced_multi_llm_comparison(""))
        
        with col3:
            if st.button("📄 Gestion docs", use_container_width=True, key="adv_docs"):
                from modules.advanced_features import manage_documents_advanced
                asyncio.run(manage_documents_advanced("import"))
        
        with col4:
            if st.button("✨ Générateurs", use_container_width=True, key="adv_gen"):
                from modules.advanced_features import use_dynamic_generators
                asyncio.run(use_dynamic_generators("plainte", {}))
    
    # Sixième ligne - Utilitaires
    st.markdown("### 🔧 Utilitaires")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Statistiques", use_container_width=True, key="stats_btn"):
            if MODULES_AVAILABLE['advanced_features']:
                from modules.advanced_features import show_work_statistics
                asyncio.run(show_work_statistics())
            else:
                st.info("Statistiques non disponibles")
    
    with col2:
        if st.button("💾 Sauvegarder", use_container_width=True, key="save_btn"):
            if MODULES_AVAILABLE['advanced_features']:
                from modules.advanced_features import save_current_work
                save_current_work()
            else:
                st.info("Sauvegarde non disponible")
    
    with col3:
        if st.button("📤 Exporter", use_container_width=True, key="export_btn"):
            if 'process_export_request' in MODULE_FUNCTIONS:
                MODULE_FUNCTIONS['process_export_request']("exporter", SimpleAnalysis(""))
            else:
                st.info("Module export non disponible")
    
    with col4:
        if st.button("🔄 Réinitialiser", use_container_width=True, key="reset_btn"):
            clear_session_state()
            st.success("✅ Session réinitialisée")
            st.rerun()

# Classe utilitaire pour compatibilité
class SimpleAnalysis:
    def __init__(self, query):
        self.query = query
        self.reference = None
        self.parties = {'demandeurs': [], 'defendeurs': []}
        self.infractions = []

def clear_session_state():
    """Nettoie l'état de session"""
    keys_to_keep = ['search_service', 'azure_blob_manager', 'azure_search_manager']
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]

def process_query(query: str):
    """Traite la requête et route vers le bon module avec ses fonctions spécifiques"""
    query_lower = query.lower()
    
    # Initialiser les résultats
    st.session_state.search_results = {
        'query': query,
        'type': 'unknown',
        'results': []
    }
    
    # Créer une analyse de requête simple pour compatibilité
    class SimpleAnalysis:
        def __init__(self, query):
            self.query = query
            self.reference = None
            self.parties = {'demandeurs': [], 'defendeurs': []}
            self.infractions = []
            
            # Extraire la référence @
            ref_match = re.search(r'@(\w+)', query)
            if ref_match:
                self.reference = ref_match.group(1)
    
    analysis = SimpleAnalysis(query)
    
    # ROUTING AVEC VOS FONCTIONS SPÉCIFIQUES
    
    # ==== PLAINTE ====
    if 'plainte' in query_lower:
        if MODULES_AVAILABLE['advanced_features']:
            from modules.advanced_features import process_plainte_request
            asyncio.run(process_plainte_request(query, analysis))
        else:
            generate_simple_plainte(query)
    
    # ==== RÉDACTION ====
    elif 'rédiger' in query_lower or 'créer' in query_lower:
        if 'process_redaction_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_redaction_request'](query, analysis)
        else:
            generate_simple_document()
    
    # ==== ANALYSE ====
    elif 'analys' in query_lower:
        if 'analyse_ia_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['analyse_ia_page']()
        else:
            st.warning("Module d'analyse non disponible")
    
    # ==== JURISPRUDENCE ====
    elif 'jurisprudence' in query_lower:
        if 'process_jurisprudence_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_jurisprudence_request'](query, analysis)
        elif 'show_jurisprudence_interface' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['show_jurisprudence_interface']()
        else:
            st.warning("Module jurisprudence non disponible")
    
    # ==== IMPORT ====
    elif 'import' in query_lower:
        if 'process_import_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_import_request'](query, analysis)
        else:
            st.warning("Module import non disponible")
    
    # ==== EXPORT ====
    elif 'export' in query_lower:
        if 'process_export_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_export_request'](query, analysis)
        else:
            st.warning("Module export non disponible")
    
    # ==== BORDEREAU ====
    elif 'bordereau' in query_lower:
        if 'process_bordereau_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_bordereau_request'](query, analysis)
        elif MODULES_AVAILABLE['advanced_features']:
            from modules.advanced_features import collect_available_documents, create_bordereau
            docs = collect_available_documents(analysis)
            if docs:
                show_bordereau_interface_advanced(docs, analysis)
        else:
            st.warning("Module bordereau non disponible")
    
    # ==== COMPARAISON ====
    elif 'compar' in query_lower and 'document' in query_lower:
        if 'process_comparison_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_comparison_request'](query, analysis)
        else:
            st.warning("Module de comparaison non disponible")
    
    # ==== EMAIL ====
    elif 'email' in query_lower or 'envoyer' in query_lower:
        if 'process_email_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_email_request'](query, analysis)
        else:
            st.warning("Module email non disponible")
    
    # ==== TIMELINE ====
    elif 'timeline' in query_lower or 'chronologie' in query_lower:
        if 'process_timeline_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_timeline_request'](query, analysis)
        else:
            st.warning("Module timeline non disponible")
    
    # ==== CARTOGRAPHIE ====
    elif 'cartographie' in query_lower or 'mapping' in query_lower:
        if 'process_mapping_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_mapping_request'](query, analysis)
        else:
            st.warning("Module de cartographie non disponible")
    
    # ==== PLAIDOIRIE ====
    elif 'plaidoirie' in query_lower or 'plaider' in query_lower:
        if 'process_plaidoirie_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_plaidoirie_request'](query, analysis)
        else:
            st.warning("Module plaidoirie non disponible")
    
    # ==== PRÉPARATION CLIENT ====
    elif 'préparer' in query_lower and 'client' in query_lower:
        if 'process_preparation_client_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_preparation_client_request'](query, analysis)
        else:
            st.warning("Module de préparation client non disponible")
    
    # ==== SÉLECTION DE PIÈCES ====
    elif 'sélection' in query_lower or 'pièces' in query_lower:
        if 'selection_piece_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['selection_piece_page']()
        elif MODULES_AVAILABLE['advanced_features']:
            show_piece_selection_advanced(analysis)
        else:
            st.warning("Module de sélection de pièces non disponible")
    
    # ==== SYNTHÈSE ====
    elif 'synthèse' in query_lower or 'synthétiser' in query_lower:
        if 'process_synthesis_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_synthesis_request'](query, analysis)
        elif MODULES_AVAILABLE['advanced_features'] and st.session_state.get('selected_pieces'):
            from modules.advanced_features import synthesize_selected_pieces
            asyncio.run(synthesize_selected_pieces(st.session_state.selected_pieces))
        else:
            st.warning("Module de synthèse non disponible")
    
    # ==== TEMPLATES ====
    elif 'template' in query_lower or 'modèle' in query_lower:
        if 'process_template_request' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['process_template_request'](query, analysis)
        else:
            st.warning("Module templates non disponible")
    
    # ==== EXPLORER ====
    elif 'explorer' in query_lower or 'parcourir' in query_lower:
        if 'show_explorer_interface' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['show_explorer_interface']()
        else:
            st.warning("Module explorer non disponible")
    
    # ==== CONFIGURATION ====
    elif 'configuration' in query_lower or 'paramètres' in query_lower:
        if 'config_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['config_page']()
        else:
            st.warning("Module configuration non disponible")
    
    # ==== FONCTIONNALITÉS AVANCÉES ====
    elif 'recherche juridique' in query_lower and MODULES_AVAILABLE['advanced_features']:
        from modules.advanced_features import perform_legal_search
        asyncio.run(perform_legal_search(query))
    
    elif 'comparer' in query_lower and 'ia' in query_lower and MODULES_AVAILABLE['advanced_features']:
        from modules.advanced_features import enhanced_multi_llm_comparison
        asyncio.run(enhanced_multi_llm_comparison(query))
    
    elif 'gérer documents' in query_lower and MODULES_AVAILABLE['advanced_features']:
        from modules.advanced_features import manage_documents_advanced
        asyncio.run(manage_documents_advanced('import'))
    
    elif 'statistiques' in query_lower and MODULES_AVAILABLE['advanced_features']:
        from modules.advanced_features import show_work_statistics
        asyncio.run(show_work_statistics())
    
    elif 'sauvegarder' in query_lower and MODULES_AVAILABLE['advanced_features']:
        from modules.advanced_features import save_current_work
        save_current_work()
    
    else:
        # Recherche générale
        st.info(f"🔍 Recherche générale pour : '{query}'")
        show_command_suggestions()

def show_command_suggestions():
    """Affiche les suggestions de commandes"""
    
    with st.expander("💡 Exemples de commandes complètes"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📝 Rédaction & Plaintes**
            - rédiger une plainte contre X
            - plainte avec constitution de partie civile
            - créer des conclusions
            - préparer une assignation
            - générer avec templates
            - mise en demeure
            """)
        
        with col2:
            st.markdown("""
            **📊 Analyse & Recherche**
            - analyser les risques
            - analyser dossier VINCI
            - vérifier jurisprudences
            - recherche juridique avancée
            - comparer avec plusieurs IA
            - analyser infractions
            """)
        
        with col3:
            st.markdown("""
            **🔧 Gestion & Outils**
            - sélectionner pièces
            - créer bordereau
            - synthétiser documents
            - importer documents
            - timeline affaire X
            - gérer documents avancé
            - statistiques
            - sauvegarder travail
            """)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎯 Commandes spécialisées**
            - plaidoirie audience
            - préparer client interrogatoire
            - cartographie sociétés
            - comparer documents
            """)
        
        with col2:
            st.markdown("""
            **📧 Communication**
            - envoyer par email
            - exporter format Word
            - partager dossier
            - créer rapport
            """)
        
        with col3:
            st.markdown("""
            **⚙️ Configuration**
            - afficher templates
            - choisir style rédaction
            - paramètres IA
            - options avancées
            """)
        
        st.markdown("---")
        st.info("""
        💡 **Astuces** :
        - Utilisez @ pour référencer une affaire (ex: @VINCI2024)
        - Ajoutez "contre X" pour identifier les parties
        - Précisez les infractions pour une meilleure analyse
        - Utilisez des phrases naturelles, l'IA comprendra votre intention !
        """)
# ========================= INTERFACES SPÉCIFIQUES =========================

# ========================= INTERFACES SPÉCIFIQUES =========================

def show_redaction_interface():
    """Interface de rédaction - appelle le module si disponible"""
    if 'process_redaction_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_redaction_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'redaction',
            'action': 'show_interface'
        }

def show_analysis_interface():
    """Interface d'analyse - appelle le module si disponible"""
    if 'analyse_ia_page' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['analyse_ia_page']()
    else:
        st.session_state.search_results = {
            'type': 'analysis',
            'action': 'show_interface'
        }

def show_import_interface():
    """Interface d'import - appelle le module si disponible"""
    if 'process_import_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_import_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'import',
            'action': 'show_interface'
        }

def show_export_interface():
    """Interface d'export - appelle le module si disponible"""
    if 'process_export_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_export_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'export',
            'action': 'show_interface'
        }

def show_bordereau_interface():
    """Interface de bordereau - appelle le module si disponible"""
    if 'process_bordereau_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_bordereau_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'bordereau',
            'action': 'show_interface'
        }

def show_jurisprudence_interface():
    """Interface de jurisprudence - appelle le module si disponible"""
    if 'show_jurisprudence_interface' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['show_jurisprudence_interface']()
    elif 'process_jurisprudence_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_jurisprudence_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'jurisprudence',
            'action': 'show_interface'
        }

def show_comparison_interface():
    """Interface de comparaison - appelle le module si disponible"""
    if 'process_comparison_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_comparison_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'comparison',
            'action': 'show_interface'
        }

def show_email_interface():
    """Interface email - appelle le module si disponible"""
    if 'process_email_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_email_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'email',
            'action': 'show_interface'
        }

def show_timeline_interface():
    """Interface timeline - appelle le module si disponible"""
    if 'process_timeline_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_timeline_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'timeline',
            'action': 'show_interface'
        }

def show_mapping_interface():
    """Interface de cartographie - appelle le module si disponible"""
    if 'process_mapping_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_mapping_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'mapping',
            'action': 'show_interface'
        }

def show_synthesis_interface():
    """Interface de synthèse - appelle le module si disponible"""
    if 'process_synthesis_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_synthesis_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'synthesis',
            'action': 'show_interface'
        }

def show_plaidoirie_interface():
    """Interface de plaidoirie - appelle le module si disponible"""
    if 'process_plaidoirie_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_plaidoirie_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'plaidoirie',
            'action': 'show_interface'
        }

def show_client_prep_interface():
    """Interface de préparation client - appelle le module si disponible"""
    if 'process_preparation_client_request' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['process_preparation_client_request']("", SimpleAnalysis(""))
    else:
        st.session_state.search_results = {
            'type': 'client_prep',
            'action': 'show_interface'
        }

def show_piece_selection_interface():
    """Interface de sélection de pièces - appelle le module si disponible"""
    if 'selection_piece_page' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['selection_piece_page']()
    else:
        st.session_state.search_results = {
            'type': 'piece_selection',
            'action': 'show_interface'
        }

def show_explorer_interface():
    """Interface d'exploration - appelle le module si disponible"""
    if 'show_explorer_interface' in MODULE_FUNCTIONS:
        MODULE_FUNCTIONS['show_explorer_interface']()
    else:
        st.session_state.search_results = {
            'type': 'explorer',
            'action': 'show_interface'
        }

# ========================= HANDLERS SIMPLIFIÉS =========================

# ========================= HANDLERS SIMPLIFIÉS =========================

def handle_analysis_request(query: str):
    """Gère une demande d'analyse"""
    if 'analyse_ia_page' in MODULE_FUNCTIONS:
        # Appeler directement la page d'analyse
        MODULE_FUNCTIONS['analyse_ia_page']()
    else:
        st.warning("Module d'analyse non disponible")
        st.info("Essayez d'activer le module analyse_ia")

def generate_simple_plainte(query: str):
    """Génère une plainte simple si le module avancé n'est pas disponible"""
    st.info("Génération d'une plainte simple...")
    
    # Extraire les parties de la requête
    parties = re.findall(r'contre\s+(\w+)', query, re.IGNORECASE)
    
    content = f"""
PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE

Je soussigné(e) [NOM PRÉNOM]
Demeurant [ADRESSE]

Ai l'honneur de porter plainte avec constitution de partie civile contre :
{', '.join(parties) if parties else '[PARTIES]'}

Pour les faits suivants :
[EXPOSÉ DES FAITS]

Ces faits sont susceptibles de recevoir la qualification de :
- Abus de biens sociaux (articles L. 241-3 et L. 242-6 du Code de commerce)
- Escroquerie (article 313-1 du Code pénal)

Je me constitue partie civile et sollicite la désignation d'un juge d'instruction.

Fait à [VILLE], le {datetime.now().strftime('%d/%m/%Y')}

Signature
"""
    
    st.session_state.generated_plainte = content
    st.session_state.search_results = {
        'type': 'plainte',
        'content': content
    }

def generate_simple_document():
    """Génère un document simple"""
    st.info("Interface de génération de document")
    
    doc_type = st.selectbox(
        "Type de document",
        ["Plainte", "Conclusions", "Assignation", "Courrier"]
    )
    
    if st.button("Générer"):
        st.success(f"Document {doc_type} généré !")
        # Ici on pourrait appeler un module de génération plus avancé

# ========================= AFFICHAGE DES RÉSULTATS =========================

def show_results():
    """Affiche les résultats selon leur type"""
    results = st.session_state.get('search_results', {})
    result_type = results.get('type', 'unknown')
    
    st.markdown("### 📊 Résultats")
    
    if result_type == 'plainte' and results.get('content'):
        st.markdown("#### 📋 Plainte générée")
        
        # Options avancées si le module est disponible
        if MODULES_AVAILABLE['advanced_features']:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("✨ Version avancée"):
                    from modules.advanced_features import generate_advanced_plainte
                    asyncio.run(generate_advanced_plainte(results.get('query', '')))
        
        content = st.text_area(
            "Contenu",
            value=results['content'],
            height=400,
            key="plainte_content"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "📥 Télécharger",
                content,
                file_name=f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        with col2:
            if st.button("📧 Envoyer"):
                if MODULES_AVAILABLE['email']:
                    show_email_interface()
        with col3:
            if st.button("🔄 Régénérer"):
                process_query(results.get('query', ''))
    
    elif result_type == 'analysis' and results.get('results'):
        st.markdown("#### 📊 Résultats d'analyse")
        st.write(results['results'])
    
    elif result_type == 'jurisprudence':
        st.markdown("#### ⚖️ Jurisprudences trouvées")
        st.info("Affichage des jurisprudences...")
    
    elif result_type in ['redaction', 'import', 'export', 'bordereau', 'timeline', 
                         'mapping', 'synthesis', 'comparison', 'email', 'plaidoirie',
                         'client_prep', 'piece_selection', 'explorer']:
        # Rediriger vers le module approprié
        st.info(f"Ouverture du module {result_type}...")
        
        # Ici, on pourrait appeler directement le module
        module_map = {
            'redaction': 'redaction_unified',
            'import': 'import_export',
            'export': 'import_export',
            'bordereau': 'bordereau',
            'timeline': 'timeline',
            'mapping': 'mapping',
            'synthesis': 'synthesis',
            'comparison': 'comparison',
            'email': 'email',
            'plaidoirie': 'plaidoirie',
            'client_prep': 'preparation_client',
            'piece_selection': 'selection_piece',
            'explorer': 'explorer'
        }
        
        module_name = module_map.get(result_type)
        if module_name and MODULES_AVAILABLE.get(module_name):
            st.success(f"✅ Module {module_name} disponible")
            st.info("Utilisez les boutons d'action rapide pour accéder directement aux fonctionnalités")
        else:
            st.error(f"❌ Module {module_name} non disponible")
    
    else:
        st.info("Aucun résultat spécifique. Essayez une commande plus précise.")
        show_command_suggestions()

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()