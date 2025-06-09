# modules/recherche.py
"""Module de recherche unifié avec toutes les améliorations intégrées"""

import streamlit as st
import asyncio
import re
import html
from datetime import datetime
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher

# ========================= IMPORTS CENTRALISÉS =========================

# Import du service de recherche depuis les managers
try:
    from managers import UniversalSearchService, get_universal_search_service
    SEARCH_SERVICE_AVAILABLE = True
except ImportError:
    SEARCH_SERVICE_AVAILABLE = False

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
        if SEARCH_SERVICE_AVAILABLE:
            self.search_service = get_universal_search_service()
        else:
            self.search_service = None
        self.current_phase = PhaseProcedure.ENQUETE_PRELIMINAIRE
    
    async def process_universal_query(self, query: str):
        """Traite une requête en utilisant le service de recherche"""
        
        # Sauvegarder la requête
        st.session_state.last_universal_query = query
        
        # Analyser la requête avec le service
        if self.search_service:
            query_analysis = self.search_service.analyze_query_advanced(query)
        else:
            # Fallback simple si le service n'est pas disponible
            query_analysis = self._simple_query_analysis(query)
        
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
    
    def _simple_query_analysis(self, query: str) -> QueryAnalysis:
        """Analyse simple de la requête si le service n'est pas disponible"""
        analysis = QueryAnalysis(
            original_query=query,
            query_lower=query.lower(),
            timestamp=datetime.now()
        )
        
        # Détection basique du type de commande
        query_lower = analysis.query_lower
        if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer']):
            analysis.command_type = 'redaction'
        else:
            analysis.command_type = 'search'
        
        # Extraction basique de la référence
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            analysis.reference = ref_match.group(1)
        
        return analysis
    
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
        
        if self.search_service:
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
                    cols = st.columns(min(len(search_result.suggestions), 3))
                    for i, suggestion in enumerate(search_result.suggestions):
                        with cols[i]:
                            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                                st.session_state.pending_query = suggestion
                                st.rerun()
            
            return search_result
        else:
            # Fallback simple
            st.warning("Service de recherche non disponible")
            return []

# ========================= FONCTIONS UTILITAIRES =========================

def get_reference_suggestions(query: str) -> List[str]:
    """Obtient des suggestions de références basées sur la requête"""
    
    suggestions = []
    
    if SEARCH_SERVICE_AVAILABLE:
        service = get_universal_search_service()
        
        # Extraire la partie après le dernier @
        if '@' in query:
            parts = query.split('@')
            partial_ref = parts[-1].strip().split()[0] if parts[-1].strip() else ''
            
            if partial_ref:
                suggestions = service.generate_reference_suggestions(partial_ref)
    
    return suggestions[:5]

def collect_all_references() -> List[str]:
    """Collecte toutes les références de dossiers disponibles"""
    
    if SEARCH_SERVICE_AVAILABLE:
        service = get_universal_search_service()
        return service.collect_all_references()
    
    # Fallback
    references = set()
    
    # Parcourir tous les documents
    all_docs = {}
    all_docs.update(st.session_state.get('azure_documents', {}))
    all_docs.update(st.session_state.get('imported_documents', {}))
    
    for doc in all_docs.values():
        title = doc.get('title', '')
        
        # Patterns simples pour extraire les références
        patterns = [
            r'affaire[_\s]+(\w+)',
            r'dossier[_\s]+(\w+)',
            r'projet[_\s]+(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, title, re.IGNORECASE)
            references.update(matches)
    
    return sorted(list(references))

def find_matching_documents(reference: str) -> List[Dict]:
    """Trouve les documents correspondant à une référence partielle"""
    
    matches = []
    ref_lower = reference.lower()
    
    # Parcourir tous les documents
    all_docs = {}
    all_docs.update(st.session_state.get('azure_documents', {}))
    all_docs.update(st.session_state.get('imported_documents', {}))
    
    for doc_id, doc in all_docs.items():
        title = doc.get('title', '')
        content = doc.get('content', '')[:200]  # Aperçu du contenu
        
        # Vérifier la correspondance
        if ref_lower in title.lower() or ref_lower in content.lower():
            # Extraire une référence propre du titre
            clean_ref = extract_clean_reference(title)
            
            matches.append({
                'id': doc_id,
                'title': title,
                'type': doc.get('type', 'Document'),
                'date': doc.get('date', doc.get('metadata', {}).get('date', 'Non daté')),
                'preview': content,
                'clean_ref': clean_ref or reference,
                'score': calculate_match_score(title, content, reference)
            })
    
    # Trier par score de pertinence
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def extract_clean_reference(title: str) -> str:
    """Extrait une référence propre du titre"""
    
    # Patterns pour extraire les références
    patterns = [
        r'affaire[_\s]+(\w+)',
        r'dossier[_\s]+(\w+)',
        r'projet[_\s]+(\w+)',
        r'^(\w+_\d{4})',
        r'^(\w+)[\s_]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Si pas de pattern, prendre le premier mot significatif
    words = title.split()
    for word in words:
        if len(word) > 3 and word.isalnum():
            return word
    
    return None

def calculate_match_score(title: str, content: str, reference: str) -> float:
    """Calcule un score de pertinence pour le tri"""
    
    score = 0
    ref_lower = reference.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Correspondance exacte dans le titre
    if ref_lower == title_lower:
        score += 100
    # Commence par la référence
    elif title_lower.startswith(ref_lower):
        score += 50
    # Contient la référence dans le titre
    elif ref_lower in title_lower:
        score += 30
    # Contient dans le contenu
    elif ref_lower in content_lower:
        score += 10
    
    # Bonus pour les références courtes (plus spécifiques)
    if len(reference) >= 5:
        score += 5
    
    return score

def highlight_match(text: str, match: str) -> str:
    """Surligne les correspondances dans le texte"""
    
    # Échapper les caractères HTML
    text = html.escape(text)
    match = html.escape(match)
    
    # Remplacer avec surbrillance (insensible à la casse)
    pattern = re.compile(re.escape(match), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark style="background-color: #ffeb3b; padding: 2px;">{m.group()}</mark>',
        text
    )
    
    return highlighted

def show_live_preview(reference: str, full_query: str):
    """Affiche une prévisualisation des dossiers correspondants"""
    
    with st.container():
        # Rechercher les correspondances
        matches = find_matching_documents(reference)
        
        if matches:
            st.markdown(f"### 📁 Aperçu des résultats pour **@{reference}**")
            
            # Limiter à 5 résultats
            for i, match in enumerate(matches[:5]):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    # Titre avec surbrillance
                    highlighted_title = highlight_match(match['title'], reference)
                    st.markdown(f"**{i+1}.** {highlighted_title}", unsafe_allow_html=True)
                
                with col2:
                    # Métadonnées
                    doc_type = match.get('type', 'Document')
                    date = match.get('date', 'Non daté')
                    st.caption(f"{doc_type} • {date}")
                
                with col3:
                    # Action rapide
                    if st.button("Utiliser", key=f"use_{match['id']}", use_container_width=True):
                        # Remplacer la référence partielle par la complète
                        new_query = full_query.replace(f"@{reference}", f"@{match['clean_ref']}")
                        st.session_state.pending_query = new_query
                        st.rerun()
            
            # Afficher le nombre total si plus de 5
            if len(matches) > 5:
                st.info(f"📊 {len(matches) - 5} autres résultats disponibles. Affinez votre recherche ou cliquez sur Rechercher.")
        else:
            st.info(f"🔍 Aucun dossier trouvé pour '@{reference}'. Essayez avec d'autres termes.")

def show_available_references():
    """Affiche toutes les références disponibles de manière organisée"""
    
    references = collect_all_references()
    
    if references:
        st.markdown("### 📚 Références disponibles")
        
        # Grouper par première lettre
        grouped = {}
        for ref in references:
            first_letter = ref[0].upper()
            if first_letter not in grouped:
                grouped[first_letter] = []
            grouped[first_letter].append(ref)
        
        # Afficher en colonnes
        cols = st.columns(4)
        col_idx = 0
        
        for letter in sorted(grouped.keys()):
            with cols[col_idx % 4]:
                st.markdown(f"**{letter}**")
                for ref in grouped[letter]:
                    if st.button(f"@{ref}", key=f"ref_{ref}", use_container_width=True):
                        st.session_state.pending_query = f"@{ref} "
                        st.rerun()
            col_idx += 1
    else:
        st.info("Aucune référence trouvée. Importez des documents pour commencer.")

# ========================= FONCTION PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle avec toutes les améliorations"""
    
    # Initialiser l'interface
    if 'search_interface' not in st.session_state:
        st.session_state.search_interface = SearchInterface()
    
    interface = st.session_state.search_interface
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # État des modules
    if st.checkbox("🔧 Voir l'état des modules"):
        show_modules_status()
    
    # Barre de recherche principale avec auto-complétion
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
        
        # Auto-complétion des références
        if query and '@' in query:
            suggestions = get_reference_suggestions(query)
            if suggestions:
                st.markdown("**Suggestions :**")
                cols = st.columns(min(len(suggestions), 5))
                for i, suggestion in enumerate(suggestions[:5]):
                    with cols[i]:
                        if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                            # Remplacer la partie après @ par la suggestion
                            parts = query.split('@')
                            if len(parts) > 1:
                                # Garder ce qui est avant @ et ajouter la suggestion
                                new_query = parts[0] + suggestion
                                st.session_state.pending_query = new_query
                                st.rerun()
    
    with col2:
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Prévisualisation en temps réel
    if query and '@' in query:
        # Extraire la référence
        parts = query.split('@')
        if len(parts) > 1:
            ref_part = parts[-1].split()[0] if parts[-1].strip() else ''
            
            if ref_part and len(ref_part) >= 2:  # Au moins 2 caractères
                show_live_preview(ref_part, query)
    
    # Afficher les références disponibles
    if st.checkbox("📁 Voir toutes les références disponibles"):
        show_available_references()
    
    # Suggestions de commandes
    with st.expander("💡 Exemples de commandes", expanded=False):
        st.markdown("""
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        - `@mart` (trouvera martin, martinez, etc.)
        - `@2024` (tous les dossiers de 2024)
        
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
            if interface.search_service:
                # Afficher les statistiques du service de recherche
                stats = asyncio.run(interface.search_service.get_search_statistics())
                with st.expander("📊 Statistiques de recherche", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Recherches totales", stats['total_searches'])
                        st.metric("Résultats moyens", f"{stats['average_results']:.0f}")
                    with col2:
                        st.metric("Taille du cache", stats['cache_size'])
                    
                    if stats['popular_keywords']:
                        st.markdown("**Mots-clés populaires:**")
                        for keyword, count in list(stats['popular_keywords'].items())[:5]:
                            st.write(f"- {keyword}: {count} fois")
            else:
                asyncio.run(show_work_statistics())
    
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
            st.metric("Service de recherche", "✅" if SEARCH_SERVICE_AVAILABLE else "❌")
        
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
    """Affiche les résultats de recherche avec highlights"""
    results = st.session_state.search_results
    
    if isinstance(results, list) and results:
        st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
        
        # Options de tri
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_option = st.selectbox(
                "Trier par",
                ["Pertinence", "Date", "Type"],
                key="sort_results"
            )
        
        # Afficher les résultats
        for i, result in enumerate(results[:10], 1):
            # Si c'est un objet Document
            if hasattr(result, 'highlights'):
                with st.expander(f"{i}. {result.title}"):
                    # Afficher les highlights s'ils existent
                    if result.highlights:
                        st.markdown("**📌 Extraits pertinents:**")
                        for highlight in result.highlights:
                            st.info(f"...{highlight}...")
                    else:
                        st.write(result.content[:500] + '...')
                    
                    # Métadonnées
                    if hasattr(result, 'metadata') and result.metadata:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"📊 Score: {result.metadata.get('score', 0):.0f}")
                        with col2:
                            st.caption(f"📁 Source: {result.source}")
                        with col3:
                            match_type = result.metadata.get('match_type', 'standard')
                            if match_type == 'exact':
                                st.caption("✅ Correspondance exacte")
                            elif match_type == 'partial':
                                st.caption("📍 Correspondance partielle")
            else:
                # Format dictionnaire
                with st.expander(f"{i}. {result.get('title', 'Sans titre')}"):
                    st.write(result.get('content', '')[:500] + '...')
                    st.caption(f"Score: {result.get('score', 0):.0%}")
        
        # Pagination si plus de 10 résultats
        if len(results) > 10:
            st.info(f"📄 Affichage des 10 premiers résultats sur {len(results)}. Utilisez les filtres pour affiner.")

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
    if hasattr(st.session_state, 'search_interface') and st.session_state.search_interface.search_service:
        st.session_state.search_interface.search_service.clear_cache()
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()