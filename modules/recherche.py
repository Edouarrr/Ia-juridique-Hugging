# modules/recherche.py
"""Module de recherche unifié utilisant UniversalSearchService"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

# ========================= IMPORTS CENTRALISÉS =========================

# Import du service de recherche depuis les managers
from managers import UniversalSearchService, get_universal_search_service

# Import des dataclasses et configurations
from models.dataclasses import (
    Document, DocumentJuridique, Partie, TypePartie, PhaseProcedure,
    TypeDocument, TypeAnalyse, QueryAnalysis, InfractionAffaires,
    PieceSelectionnee, BordereauPieces, collect_available_documents,
    group_documents_by_category, determine_document_category,
    calculate_piece_relevance, create_bordereau, create_bordereau_document
)

from models.configurations import (
    DEFAULT_STYLE_CONFIGS, BUILTIN_DOCUMENT_TEMPLATES,
    DEFAULT_LETTERHEADS, FORMULES_JURIDIQUES,
    ARGUMENTATION_PATTERNS, ANALYSIS_CONFIGS
)

# Import des fonctionnalités avancées
from modules.advanced_features import (
    generate_advanced_plainte,
    verify_jurisprudences_in_plainte,
    compare_ai_generations,
    show_plainte_statistics,
    show_improvement_suggestions,
    perform_legal_search,
    manage_documents_advanced,
    enhanced_multi_llm_comparison,
    use_dynamic_generators,
    generate_plainte_simple,
    generate_plainte_cpc,
    show_piece_selection_advanced,
    show_bordereau_interface_advanced,
    export_piece_list,
    synthesize_selected_pieces,
    show_document_statistics,
    save_current_work,
    show_work_statistics,
    process_plainte_request,
    MANAGERS
)

# ========================= IMPORTS DES MODULES SPÉCIFIQUES =========================

MODULES_AVAILABLE = {}
MODULE_FUNCTIONS = {}

# Import conditionnel de tous les modules
modules_to_import = [
    ('analyse_ia', ['show_page']),
    ('bordereau', ['process_bordereau_request', 'create_bordereau']),
    ('comparison', ['process_comparison_request']),
    ('configuration', ['show_page']),
    ('email', ['process_email_request']),
    ('explorer', ['show_explorer_interface']),
    ('import_export', ['process_import_request', 'process_export_request']),
    ('jurisprudence', ['process_jurisprudence_request', 'show_jurisprudence_interface']),
    ('mapping', ['process_mapping_request']),
    ('plaidoirie', ['process_plaidoirie_request']),
    ('preparation_client', ['process_preparation_client_request']),
    ('redaction_unified', ['process_redaction_request']),
    ('selection_piece', ['show_page']),
    ('synthesis', ['process_synthesis_request']),
    ('templates', ['process_template_request']),
    ('timeline', ['process_timeline_request'])
]

for module_name, functions in modules_to_import:
    try:
        module = __import__(f'modules.{module_name}', fromlist=functions)
        MODULES_AVAILABLE[module_name] = True
        
        for func_name in functions:
            if hasattr(module, func_name):
                if func_name == 'show_page':
                    MODULE_FUNCTIONS[f'{module_name}_page'] = getattr(module, func_name)
                else:
                    MODULE_FUNCTIONS[func_name] = getattr(module, func_name)
    except ImportError:
        MODULES_AVAILABLE[module_name] = False

# ========================= INTERFACE UTILISATEUR =========================

class SearchInterface:
    """Interface utilisateur pour le module de recherche"""
    
    def __init__(self):
        """Initialisation avec le service de recherche universelle"""
        self.search_service = get_universal_search_service()
        self.current_phase = PhaseProcedure.ENQUETE_PRELIMINAIRE
    
    async def process_universal_query(self, query: str):
        """Traite une requête en utilisant le service de recherche"""
        
        # Sauvegarder la requête
        st.session_state.last_universal_query = query
        
        # Analyser la requête avec le service
        query_analysis = self.search_service.analyze_query_advanced(query)
        
        # Router selon le type de commande détecté
        if query_analysis.command_type == 'redaction':
            return await self._process_redaction_request(query, query_analysis)
        elif query_analysis.command_type == 'plainte':
            return await process_plainte_request(query, query_analysis)
        elif query_analysis.command_type == 'plaidoirie':
            return await self._process_plaidoirie_request(query, query_analysis)
        elif query_analysis.command_type == 'preparation_client':
            return await self._process_preparation_client_request(query, query_analysis)
        elif query_analysis.command_type == 'import':
            return await self._process_import_request(query, query_analysis)
        elif query_analysis.command_type == 'export':
            return await self._process_export_request(query, query_analysis)
        elif query_analysis.command_type == 'email':
            return await self._process_email_request(query, query_analysis)
        elif query_analysis.command_type == 'analysis':
            return await self._process_analysis_request(query, query_analysis)
        elif query_analysis.command_type == 'piece_selection':
            return await self._process_piece_selection_request(query, query_analysis)
        elif query_analysis.command_type == 'bordereau':
            return await self._process_bordereau_request(query, query_analysis)
        elif query_analysis.command_type == 'synthesis':
            return await self._process_synthesis_request(query, query_analysis)
        elif query_analysis.command_type == 'template':
            return await self._process_template_request(query, query_analysis)
        elif query_analysis.command_type == 'jurisprudence':
            return await self._process_jurisprudence_request(query, query_analysis)
        elif query_analysis.command_type == 'timeline':
            return await self._process_timeline_request(query, query_analysis)
        elif query_analysis.command_type == 'mapping':
            return await self._process_mapping_request(query, query_analysis)
        elif query_analysis.command_type == 'comparison':
            return await self._process_comparison_request(query, query_analysis)
        else:
            # Recherche par défaut
            return await self._process_search_request(query, query_analysis)
    
    # ===================== PROCESSEURS DE REQUÊTES =====================
    
    async def _process_redaction_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de rédaction"""
        st.info("📝 Détection d'une demande de rédaction...")
        
        if 'process_redaction_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_redaction_request'](query, query_analysis)
        else:
            st.warning("Module de rédaction non disponible")
    
    async def _process_analysis_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'analyse"""
        if 'analyse_ia_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['analyse_ia_page']()
        else:
            st.warning("Module d'analyse non disponible")
    
    async def _process_plaidoirie_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de plaidoirie"""
        if 'process_plaidoirie_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_plaidoirie_request'](query, query_analysis)
        else:
            st.warning("Module plaidoirie non disponible")
    
    async def _process_preparation_client_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de préparation client"""
        if 'process_preparation_client_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_preparation_client_request'](query, query_analysis)
        else:
            st.warning("Module préparation client non disponible")
    
    async def _process_import_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'import"""
        if 'process_import_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_import_request'](query, query_analysis)
        else:
            st.warning("Module import non disponible")
    
    async def _process_export_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'export"""
        if 'process_export_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_export_request'](query, query_analysis)
        else:
            st.warning("Module export non disponible")
    
    async def _process_email_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'email"""
        if 'process_email_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_email_request'](query, query_analysis)
        else:
            st.warning("Module email non disponible")
    
    async def _process_piece_selection_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de sélection de pièces"""
        if 'selection_piece_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['selection_piece_page']()
        else:
            show_piece_selection_advanced(query_analysis)
    
    async def _process_bordereau_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de bordereau"""
        if 'process_bordereau_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_bordereau_request'](query, query_analysis)
        else:
            docs = collect_available_documents(query_analysis)
            if docs:
                show_bordereau_interface_advanced(docs, query_analysis)
    
    async def _process_synthesis_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de synthèse"""
        if 'process_synthesis_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_synthesis_request'](query, query_analysis)
        elif st.session_state.get('selected_pieces'):
            return await synthesize_selected_pieces(st.session_state.selected_pieces)
        else:
            st.warning("Module synthèse non disponible ou aucune pièce sélectionnée")
    
    async def _process_template_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de template"""
        if 'process_template_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_template_request'](query, query_analysis)
        else:
            st.warning("Module templates non disponible")
    
    async def _process_jurisprudence_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de jurisprudence"""
        if 'process_jurisprudence_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_jurisprudence_request'](query, query_analysis)
        elif 'show_jurisprudence_interface' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['show_jurisprudence_interface']()
        else:
            st.warning("Module jurisprudence non disponible")
    
    async def _process_timeline_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de timeline"""
        if 'process_timeline_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_timeline_request'](query, query_analysis)
        else:
            st.warning("Module timeline non disponible")
    
    async def _process_mapping_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de cartographie"""
        if 'process_mapping_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_mapping_request'](query, query_analysis)
        else:
            st.warning("Module cartographie non disponible")
    
    async def _process_comparison_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de comparaison"""
        if 'process_comparison_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_comparison_request'](query, query_analysis)
        else:
            st.warning("Module comparaison non disponible")
    
    async def _process_search_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de recherche par défaut"""
        st.info("🔍 Recherche en cours...")
        
        # Utiliser le service de recherche
        search_result = await self.search_service.search(query)
        
        # Stocker les résultats
        st.session_state.search_results = search_result.documents
        
        if not search_result.documents:
            st.warning("⚠️ Aucun résultat trouvé")
        else:
            st.success(f"✅ {len(search_result.documents)} résultats trouvés")
            
            # Afficher les facettes si disponibles
            if search_result.facets:
                with st.expander("🔍 Filtres disponibles"):
                    for facet_name, facet_values in search_result.facets.items():
                        st.write(f"**{facet_name}**")
                        for value, count in facet_values.items():
                            st.write(f"- {value}: {count}")
            
            # Afficher les suggestions si disponibles
            if search_result.suggestions:
                st.info("💡 Suggestions de recherche:")
                for suggestion in search_result.suggestions:
                    if st.button(suggestion, key=f"suggestion_{suggestion}"):
                        st.session_state.pending_query = suggestion
                        st.rerun()
        
        return search_result

# ========================= FONCTION PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    # Initialiser l'interface
    if 'search_interface' not in st.session_state:
        st.session_state.search_interface = SearchInterface()
    
    interface = st.session_state.search_interface
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # État des modules
    if st.checkbox("🔧 Voir l'état des modules"):
        show_modules_status()
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        default_value = ""
        if 'pending_query' in st.session_state:
            default_value = st.session_state.pending_query
            del st.session_state.pending_query
        elif 'universal_query' in st.session_state:
            default_value = st.session_state.universal_query
        
        query = st.text_input(
            "Entrez votre commande ou recherche",
            value=default_value,
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
    
    with col2:
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Suggestions de commandes
    with st.expander("💡 Exemples de commandes", expanded=False):
        st.markdown("""
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        
        **Analyse :**
        - `analyser les risques @dossier_pénal`
        - `identifier les infractions @affaire_corruption`
        
        **Rédaction :**
        - `rédiger conclusions défense @affaire_martin abus biens sociaux`
        - `créer plainte avec constitution partie civile escroquerie`
        - `rédiger plainte contre Vinci, SOGEPROM @projet_26_05_2025`
        
        **Synthèse :**
        - `synthétiser les pièces @dossier_fraude`
        - `résumer les auditions @affaire_martin`
        
        **Gestion :**
        - `sélectionner pièces @dossier catégorie procédure`
        - `créer bordereau @pièces_sélectionnées`
        - `importer documents PDF`
        - `exporter analyse format word`
        """)
    
    # Menu d'actions rapides
    show_quick_actions()
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            # Utiliser une nouvelle boucle d'événements
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(interface.process_universal_query(query))
            finally:
                loop.close()
    
    # Afficher les résultats
    show_unified_results()
    
    # Réinitialiser le flag de traitement
    if 'process_query' in st.session_state:
        st.session_state.process_query = False
    
    # Footer avec actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder le travail", key="save_work"):
            save_current_work()
    
    with col2:
        if st.button("📊 Afficher les statistiques", key="show_stats"):
            # Afficher les statistiques du service de recherche
            stats = asyncio.run(interface.search_service.get_search_statistics())
            st.json(stats)
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            st.info("Fonctionnalité de partage à implémenter")

def show_modules_status():
    """Affiche l'état détaillé des modules"""
    with st.expander("🔧 État des modules et fonctions", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Modules disponibles", sum(1 for v in MODULES_AVAILABLE.values() if v))
            st.metric("Fonctions importées", len(MODULE_FUNCTIONS))
        
        with col2:
            st.metric("Managers avancés", sum(1 for v in MANAGERS.values() if v))
            # Vérifier si le service de recherche est disponible
            search_service_available = False
            try:
                from managers import UniversalSearchService
                search_service_available = True
            except:
                pass
            st.metric("Service de recherche", "✅" if search_service_available else "❌")
        
        with col3:
            st.metric("Templates", len(BUILTIN_DOCUMENT_TEMPLATES))
            st.metric("Styles", len(DEFAULT_STYLE_CONFIGS))
        
        # Liste détaillée
        st.markdown("### 📋 Modules actifs")
        for module, available in MODULES_AVAILABLE.items():
            if available:
                st.success(f"✅ {module}")
            else:
                st.error(f"❌ {module}")

def show_quick_actions():
    """Affiche les actions rapides"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Nouvelle rédaction", key="quick_redaction"):
            st.session_state.pending_query = "rédiger "
            st.session_state.process_query = True
            st.rerun()
    
    with col2:
        if st.button("🤖 Analyser dossier", key="quick_analysis"):
            st.session_state.pending_query = "analyser "
            st.session_state.process_query = True
            st.rerun()
    
    with col3:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.pending_query = "importer documents"
            st.session_state.process_query = True
            st.rerun()
    
    with col4:
        if st.button("🔄 Réinitialiser", key="quick_reset"):
            clear_universal_state()

def show_unified_results():
    """Affiche tous les types de résultats de manière unifiée"""
    
    # Vérifier tous les types de résultats possibles
    results_found = False
    
    # Résultats de rédaction
    if st.session_state.get('redaction_result'):
        show_redaction_results()
        results_found = True
    
    # Plainte générée
    elif st.session_state.get('generated_plainte'):
        show_plainte_results()
        results_found = True
    
    # Résultats d'analyse
    elif st.session_state.get('ai_analysis_results'):
        show_analysis_results()
        results_found = True
    
    # Résultats de recherche
    elif st.session_state.get('search_results'):
        show_search_results()
        results_found = True
    
    # Résultats de synthèse
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        results_found = True
    
    # Autres résultats...
    elif st.session_state.get('timeline_result'):
        show_timeline_results()
        results_found = True
    
    elif st.session_state.get('bordereau_result'):
        show_bordereau_results()
        results_found = True
    
    elif st.session_state.get('jurisprudence_results'):
        show_jurisprudence_results()
        results_found = True
    
    if not results_found:
        st.info("💡 Utilisez la barre de recherche universelle pour commencer")

def show_redaction_results():
    """Affiche les résultats de rédaction"""
    result = st.session_state.redaction_result
    
    st.markdown("### 📝 Document juridique généré")
    
    # Contenu éditable
    edited_content = st.text_area(
        "Contenu du document",
        value=result.get('document', result.get('content', '')),
        height=600,
        key="edit_redaction"
    )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📥 Télécharger",
            edited_content.encode('utf-8'),
            f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("📧 Envoyer"):
            st.session_state.pending_email = {'content': edited_content}
    
    with col3:
        if st.button("🔄 Régénérer"):
            st.session_state.process_query = True
            st.rerun()

def show_plainte_results():
    """Affiche les résultats de génération de plainte"""
    content = st.session_state.generated_plainte
    
    st.markdown("### 📋 Plainte générée")
    
    # Options avancées si disponibles
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("✨ Version avancée", key="upgrade_plainte"):
            query = st.session_state.get('last_universal_query', '')
            asyncio.run(generate_advanced_plainte(query))
    
    # Contenu éditable
    edited_content = st.text_area(
        "Contenu de la plainte",
        value=content,
        height=600,
        key="edit_plainte"
    )
    
    # Actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.download_button(
            "📥 Télécharger",
            edited_content.encode('utf-8'),
            f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("📊 Statistiques", key="stats_plainte"):
            show_plainte_statistics(edited_content)
    
    with col3:
        if st.button("✅ Vérifier", key="verify_plainte"):
            verify_jurisprudences_in_plainte(edited_content)
    
    with col4:
        if st.button("🔄 Régénérer", key="regen_plainte"):
            st.session_state.process_query = True
            st.rerun()

def show_analysis_results():
    """Affiche les résultats d'analyse"""
    results = st.session_state.ai_analysis_results
    
    st.markdown("### 🤖 Résultats de l'analyse")
    
    # Contenu
    st.text_area(
        "Analyse",
        value=results.get('content', ''),
        height=400,
        key="analysis_content"
    )
    
    # Métadonnées
    if results.get('document_count'):
        st.info(f"📄 Documents analysés : {results['document_count']}")

def show_search_results():
    """Affiche les résultats de recherche"""
    results = st.session_state.search_results
    
    if isinstance(results, list) and results:
        st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
        
        for i, result in enumerate(results[:10], 1):
            # Si c'est un objet Document
            if hasattr(result, 'highlights'):
                with st.expander(f"{i}. {result.title}"):
                    # Afficher les highlights s'ils existent
                    if result.highlights:
                        st.markdown("**Extraits pertinents:**")
                        for highlight in result.highlights:
                            st.info(f"...{highlight}...")
                    else:
                        st.write(result.content[:500] + '...')
                    
                    # Métadonnées
                    if hasattr(result, 'metadata') and result.metadata:
                        st.caption(f"Score: {result.metadata.get('score', 0):.0f} | Source: {result.source}")
            else:
                # Format dictionnaire
                with st.expander(f"{i}. {result.get('title', 'Sans titre')}"):
                    st.write(result.get('content', '')[:500] + '...')
                    st.caption(f"Score: {result.get('score', 0):.0%}")

def show_synthesis_results():
    """Affiche les résultats de synthèse"""
    result = st.session_state.synthesis_result
    
    st.markdown("### 📝 Synthèse des documents")
    
    st.text_area(
        "Contenu de la synthèse",
        value=result.get('content', ''),
        height=400,
        key="synthesis_content"
    )
    
    if result.get('piece_count'):
        st.info(f"📄 Pièces analysées : {result['piece_count']}")

def show_timeline_results():
    """Affiche les résultats de timeline"""
    st.markdown("### ⏱️ Chronologie des événements")
    st.info("Timeline générée")

def show_bordereau_results():
    """Affiche les résultats de bordereau"""
    st.markdown("### 📊 Bordereau de communication")
    st.info("Bordereau généré")

def show_jurisprudence_results():
    """Affiche les résultats de jurisprudence"""
    st.markdown("### ⚖️ Jurisprudences trouvées")
    st.info("Résultats de jurisprudence")

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'current_analysis',
        'redaction_result', 'ai_analysis_results', 'search_results',
        'synthesis_result', 'selected_pieces', 'import_files',
        'generated_plainte', 'timeline_result', 'bordereau_result',
        'jurisprudence_results'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Effacer aussi le cache du service
    if hasattr(st.session_state, 'search_interface'):
        st.session_state.search_interface.search_service.clear_cache()
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()