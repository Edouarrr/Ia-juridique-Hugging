"""Interface de recherche universelle compatible avec UniversalSearchService existant"""

import asyncio
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from utils.prompt_rewriter import rewrite_prompt

# Import des classes du service existant - pas d'import direct pour éviter les erreurs circulaires
# Les classes seront importées depuis universal_search_service lors de l'utilisation

class UniversalSearchInterface:
    """Interface utilisateur pour la recherche universelle"""
    
    def __init__(self):
        """Initialise l'interface de recherche"""
        # Import différé pour éviter les problèmes d'import circulaire
        from .universal_search_service import UniversalSearchService
        
        self.search_service = UniversalSearchService()
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialise les variables de session nécessaires"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        
        if 'last_search_results' not in st.session_state:
            st.session_state.last_search_results = None
        
        if 'selected_filters' not in st.session_state:
            st.session_state.selected_filters = {}
        
        if 'current_query_analysis' not in st.session_state:
            st.session_state.current_query_analysis = None
    
    def render(self):
        """Affiche l'interface de recherche complète"""
        # En-tête de recherche avec le même style que votre app
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='margin: 0; color: #1a237e;'>🔍 Recherche Universelle Intelligente</h2>
            <p style='margin: 5px 0 0 0; color: #666;'>Recherchez dans tous vos documents, dossiers et références avec analyse IA</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Analyser et afficher la requête
        query_analysis = self._show_query_analysis()
        
        # Barre de recherche principale
        search_query = self._render_search_bar()
        
        # Effectuer la recherche si nécessaire
        if search_query:
            self._perform_search(search_query)
        
        # Afficher les résultats précédents s'ils existent
        if st.session_state.last_search_results:
            self._display_results(st.session_state.last_search_results)
    
    def _show_query_analysis(self):
        """Affiche l'analyse de la requête en cours"""
        if st.session_state.current_query_analysis:
            analysis = st.session_state.current_query_analysis
            
            with st.expander("🧠 Analyse IA de votre requête", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**📌 Éléments détectés**")
                    if analysis.reference:
                        st.success(f"Référence: @{analysis.reference}")
                    if analysis.document_type:
                        st.info(f"Type: {analysis.document_type}")
                    if analysis.command_type:
                        st.warning(f"Action: {analysis.command_type}")
                
                with col2:
                    st.markdown("**👥 Parties identifiées**")
                    if analysis.parties['demandeurs']:
                        st.write("Demandeurs:")
                        for d in analysis.parties['demandeurs']:
                            st.caption(f"• {d}")
                    if analysis.parties['defendeurs']:
                        st.write("Défendeurs:")
                        for d in analysis.parties['defendeurs']:
                            st.caption(f"• {d}")
                
                with col3:
                    st.markdown("**⚖️ Éléments juridiques**")
                    if analysis.infractions:
                        st.write("Infractions:")
                        for inf in analysis.infractions:
                            st.caption(f"• {inf}")
                    if analysis.keywords:
                        st.write("Mots-clés:")
                        st.caption(", ".join(analysis.keywords[:5]))
    
    def _render_search_bar(self) -> Optional[str]:
        """Affiche la barre de recherche avec suggestions intelligentes"""
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Zone de recherche avec exemples adaptés à votre système
            search_input = st.text_input(
                "Rechercher",
                placeholder="Ex: @VINCI2024 conclusions, abus de biens sociaux SOGEPROM, plainte contre PERINET...",
                label_visibility="hidden",
                key="universal_search_input"
            )

            if search_input:
                rewritten = rewrite_prompt(search_input)
                st.markdown(f"*Reformulation :* {rewritten}")
            
            # Analyser la requête en temps réel
            if search_input and len(search_input) > 2:
                # Analyse rapide de la requête
                temp_analysis = self.search_service.analyze_query_advanced(search_input)
                st.session_state.current_query_analysis = temp_analysis
                
                # Afficher des suggestions contextuelles
                self._show_contextual_suggestions(search_input, temp_analysis)
        
        with col2:
            search_button = st.button(
                "🔍 Rechercher",
                use_container_width=True,
                type="primary",
                key="universal_search_button"
            )
        
        # Retourner la requête si le bouton est cliqué ou Enter est pressé
        if search_button and search_input:
            return search_input
        
        return None
    
    def _show_contextual_suggestions(self, query: str, analysis):
        """Affiche des suggestions contextuelles basées sur l'analyse"""
        suggestions = []
        
        # Suggestions basées sur le type de commande détecté
        if analysis.command_type == 'redaction':
            suggestions.extend([
                f"{query} modèle professionnel",
                f"{query} avec jurisprudence récente",
                f"{query} format Word"
            ])
        elif analysis.command_type == 'search' and analysis.reference:
            suggestions.extend([
                f"Tous les documents {analysis.reference}",
                f"Dernières pièces {analysis.reference}",
                f"Synthèse {analysis.reference}"
            ])
        
        # Suggestions basées sur les parties détectées
        if analysis.parties['demandeurs'] and not analysis.parties['defendeurs']:
            for defendeur in ['PERINET', 'VP INVEST', 'PERRAUD']:
                suggestions.append(f"{query} contre {defendeur}")
        
        # Suggestions basées sur les infractions
        if analysis.infractions:
            suggestions.append(f"Jurisprudence {analysis.infractions[0]}")
        
        # Afficher les suggestions
        if suggestions:
            st.caption("💡 Suggestions intelligentes :")
            cols = st.columns(min(len(suggestions), 3))
            for idx, suggestion in enumerate(suggestions[:3]):
                with cols[idx]:
                    if st.button(suggestion, key=f"smart_suggestion_{idx}"):
                        st.session_state.universal_search_input = suggestion
                        st.rerun()
    
    def _perform_search(self, query: str):
        """Effectue la recherche et stocke les résultats"""
        with st.spinner(f"🔍 Recherche intelligente en cours pour : **{query}**"):
            # Construire les filtres depuis l'interface
            filters = self._build_filters()
            
            # Créer une nouvelle boucle d'événements pour l'exécution asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Effectuer la recherche avec le service
                results = loop.run_until_complete(
                    self.search_service.search(query, filters)
                )
                
                # Stocker les résultats
                st.session_state.last_search_results = results
                
                # L'historique est déjà géré par le service
                
            finally:
                loop.close()
    
    def _build_filters(self) -> Dict[str, Any]:
        """Construit les filtres actifs depuis la session"""
        filters = {}
        
        # Récupérer les filtres depuis la session
        if st.session_state.selected_filters:
            filters.update(st.session_state.selected_filters)
        
        return filters
    
    def _display_results(self, results):
        """Affiche les résultats de recherche avec le style approprié"""
        # Vérifier le type de results - c'est un objet SearchResult
        if not hasattr(results, 'documents'):
            st.error("Format de résultats invalide")
            return
        
        # Statistiques enrichies
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Documents trouvés", results.total_count)
        with col2:
            st.metric("📊 Résultats affichés", len(results.documents))
        with col3:
            if hasattr(results, 'timestamp'):
                st.metric("⏱️ Temps", f"{results.timestamp.strftime('%H:%M:%S')}")
        with col4:
            # Score moyen des résultats
            if results.documents:
                avg_score = sum(d.metadata.get('score', 0) for d in results.documents) / len(results.documents)
                st.metric("⭐ Score moyen", f"{avg_score:.1f}")
        
        # Facettes pour filtrage dynamique
        if results.facets:
            self._render_facets(results.facets)
        
        # Suggestions de recherches alternatives
        if results.suggestions:
            self._render_suggestions(results.suggestions)
        
        # Onglets pour différentes vues
        tab1, tab2, tab3 = st.tabs(["📄 Résultats", "📊 Analyse", "🔍 Détails"])
        
        with tab1:
            # Résultats principaux
            st.markdown("### 📄 Documents trouvés")
            
            if results.documents:
                for idx, doc in enumerate(results.documents, 1):
                    self._render_document_result(doc, idx)
            else:
                st.warning("Aucun document trouvé pour cette recherche.")
                self._show_search_tips()
        
        with tab2:
            # Analyse des résultats
            self._render_results_analysis(results)
        
        with tab3:
            # Détails techniques
            self._render_technical_details(results)
    
    def _render_facets(self, facets: Dict[str, Dict[str, int]]):
        """Affiche les facettes pour le filtrage"""
        with st.expander("🔧 Affiner les résultats", expanded=False):
            cols = st.columns(4)
            
            # Sources
            with cols[0]:
                st.markdown("**📁 Sources**")
                sources = facets.get('sources', {})
                for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                    if st.checkbox(f"{source} ({count})", key=f"facet_source_{source}"):
                        st.session_state.selected_filters['source'] = source
            
            # Types
            with cols[1]:
                st.markdown("**📋 Types**")
                types = facets.get('types', {})
                for doc_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]:
                    display_type = doc_type.upper() if doc_type != 'unknown' else 'Non classé'
                    if st.checkbox(f"{display_type} ({count})", key=f"facet_type_{doc_type}"):
                        st.session_state.selected_filters['document_type'] = doc_type
            
            # Scores
            with cols[2]:
                st.markdown("**⭐ Pertinence**")
                scores = facets.get('scores', {})
                if scores.get('high', 0) > 0:
                    if st.checkbox(f"🔥 Très pertinent ({scores['high']})", key="facet_score_high"):
                        st.session_state.selected_filters['min_score'] = 20
                if scores.get('medium', 0) > 0:
                    if st.checkbox(f"⭐ Pertinent ({scores['medium']})", key="facet_score_medium"):
                        st.session_state.selected_filters['min_score'] = 10
            
            # Bouton de réinitialisation
            with cols[3]:
                st.markdown("**🔄 Actions**")
                if st.button("Réinitialiser filtres", key="reset_facets"):
                    st.session_state.selected_filters = {}
                    st.rerun()
    
    def _render_suggestions(self, suggestions: List[str]):
        """Affiche les suggestions de recherche"""
        st.markdown("### 💡 Recherches suggérées")
        cols = st.columns(len(suggestions) if len(suggestions) <= 3 else 3)
        
        for idx, suggestion in enumerate(suggestions[:3]):
            with cols[idx]:
                if st.button(f"🔍 {suggestion}", key=f"alt_search_{idx}", use_container_width=True):
                    st.session_state.universal_search_input = suggestion
                    st.rerun()
    
    def _render_document_result(self, doc, index: int):
        """Affiche un résultat de document avec le style approprié"""
        # Utiliser la structure Document de votre service
        with st.container():
            col1, col2 = st.columns([10, 2])
            
            with col1:
                # Titre avec badges selon le score
                score = doc.metadata.get('score', 0)
                score_badge = self._get_score_badge(score)
                doc_type = doc.metadata.get('type', 'document').upper()
                
                st.markdown(f"### {index}. {doc.title} {score_badge}")
                
                # Métadonnées sur une ligne
                metadata_parts = [
                    f"📄 {doc.source}",
                    f"📋 {doc_type}",
                    f"🆔 {doc.id[:8]}...",
                    f"⭐ Score: {score:.0f}"
                ]
                
                if doc.metadata.get('date'):
                    metadata_parts.append(f"📅 {doc.metadata['date']}")
                
                st.caption(" | ".join(metadata_parts))
                
                # Highlights s'ils existent
                if doc.highlights:
                    st.markdown("**📍 Extraits pertinents:**")
                    for highlight in doc.highlights[:3]:
                        # Nettoyer et afficher le highlight
                        clean_highlight = highlight.strip()
                        if clean_highlight:
                            st.info(f"*...{clean_highlight}...*")
                else:
                    # Afficher un extrait du contenu
                    content_preview = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                    with st.expander("📝 Aperçu du contenu", expanded=False):
                        st.text(content_preview)
            
            with col2:
                # Actions groupées
                st.markdown("**Actions**")
                
                if st.button("👁️ Voir", key=f"view_{doc.id}_{index}"):
                    self._show_document_detail(doc)
                
                if st.button("📥 Télécharger", key=f"download_{doc.id}_{index}"):
                    self._download_document(doc)
                
                if st.button("🔗 Similaires", key=f"similar_{doc.id}_{index}"):
                    self._search_similar_documents(doc)
        
        st.markdown("---")
    
    def _get_score_badge(self, score: float) -> str:
        """Retourne un badge selon le score"""
        if score >= 20:
            return "🔥"  # Très pertinent
        elif score >= 10:
            return "⭐"  # Pertinent
        else:
            return "📄"  # Standard
    
    def _show_document_detail(self, doc):
        """Affiche le détail d'un document dans un modal"""
        with st.expander(f"📄 Document complet : {doc.title}", expanded=True):
            # En-tête avec toutes les métadonnées
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🆔 Identifiant**")
                st.code(doc.id)
                
                st.markdown("**📁 Source**")
                st.write(doc.source)
                
                st.markdown("**📋 Type**")
                st.write(doc.metadata.get('type', 'Non spécifié'))
            
            with col2:
                st.markdown("**⭐ Score de pertinence**")
                st.progress(min(doc.metadata.get('score', 0) / 50, 1.0))
                st.caption(f"{doc.metadata.get('score', 0):.1f} / 50")
                
                if doc.metadata.get('date'):
                    st.markdown("**📅 Date**")
                    st.write(doc.metadata['date'])
            
            # Contenu complet avec highlights
            st.markdown("### 📝 Contenu")
            
            if doc.highlights:
                # Afficher le contenu avec les passages surlignés
                content_with_highlights = self._highlight_content(doc.content, doc.highlights)
                st.markdown(content_with_highlights, unsafe_allow_html=True)
            else:
                st.text_area("", doc.content, height=400, disabled=True)
            
            # Actions
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="💾 Télécharger",
                    data=self._prepare_document_download(doc),
                    file_name=f"{doc.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            with col2:
                if st.button("📧 Envoyer par email", key=f"email_detail_{doc.id}"):
                    st.info("Fonctionnalité email à implémenter")
            with col3:
                if st.button("🔗 Rechercher similaires", key=f"similar_detail_{doc.id}"):
                    self._search_similar_documents(doc)
    
    def _highlight_content(self, content: str, highlights: List[str]) -> str:
        """Met en surbrillance les passages dans le contenu"""
        highlighted_content = content
        
        for highlight in highlights:
            # Échapper les caractères spéciaux pour la regex
            escaped_highlight = re.escape(highlight.strip())
            # Remplacer avec surbrillance
            highlighted_content = re.sub(
                escaped_highlight,
                f'<mark style="background-color: #ffd93d; padding: 2px;">{highlight}</mark>',
                highlighted_content,
                flags=re.IGNORECASE
            )
        
        return highlighted_content
    
    def _download_document(self, doc):
        """Prépare et télécharge un document"""
        content = self._prepare_document_download(doc)
        
        st.download_button(
            label="💾 Télécharger le document",
            data=content,
            file_name=f"{doc.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            key=f"download_action_{doc.id}"
        )
    
    def _prepare_document_download(self, doc) -> str:
        """Prépare le contenu d'un document pour le téléchargement"""
        content = f"""# {doc.title}

## Métadonnées
- **ID:** {doc.id}
- **Source:** {doc.source}
- **Type:** {doc.metadata.get('type', 'Non spécifié')}
- **Score:** {doc.metadata.get('score', 0):.1f}
- **Date:** {doc.metadata.get('date', 'Non spécifiée')}

## Contenu

{doc.content}

---
*Document exporté le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*
*Depuis l'Assistant Pénal des Affaires IA*
"""
        return content
    
    def _search_similar_documents(self, doc):
        """Lance une recherche de documents similaires"""
        # Extraire des termes clés du document
        keywords = []
        
        # Extraire depuis le titre
        title_words = doc.title.split()[:3]
        keywords.extend(title_words)
        
        # Extraire depuis les highlights
        if doc.highlights:
            for highlight in doc.highlights[:2]:
                words = highlight.split()[:3]
                keywords.extend(words)
        
        # Construire une nouvelle requête
        similar_query = ' '.join(keywords[:5])
        
        # Lancer la recherche
        st.session_state.universal_search_input = f"documents similaires à : {similar_query}"
        st.rerun()
    
    def _render_results_analysis(self, results):
        """Affiche une analyse des résultats"""
        st.markdown("### 📊 Analyse des résultats")
        
        if not results.documents:
            st.info("Aucun résultat à analyser")
            return
        
        # Analyse par source
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Distribution par source**")
            source_counts = {}
            for doc in results.documents:
                source = doc.source
                source_counts[source] = source_counts.get(source, 0) + 1
            
            for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
                st.progress(count / len(results.documents))
                st.caption(f"{source}: {count} documents")
        
        with col2:
            st.markdown("**Distribution par type**")
            type_counts = {}
            for doc in results.documents:
                doc_type = doc.metadata.get('type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                st.progress(count / len(results.documents))
                st.caption(f"{doc_type}: {count} documents")
        
        # Statistiques des scores
        st.markdown("**Statistiques de pertinence**")
        scores = [doc.metadata.get('score', 0) for doc in results.documents]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score max", f"{max(scores):.1f}")
        with col2:
            st.metric("Score moyen", f"{sum(scores)/len(scores):.1f}")
        with col3:
            st.metric("Score min", f"{min(scores):.1f}")
    
    def _render_technical_details(self, results):
        """Affiche les détails techniques de la recherche"""
        st.markdown("### 🔍 Détails techniques")
        
        # Analyse de la requête
        if st.session_state.current_query_analysis:
            st.markdown("**Analyse de la requête**")
            analysis = st.session_state.current_query_analysis
            
            analysis_data = {
                "Requête originale": analysis.original_query,
                "Type de recherche": analysis.search_type,
                "Type de commande": analysis.command_type,
                "Référence": analysis.reference,
                "Type de document": analysis.document_type,
                "Parties demandeurs": analysis.parties['demandeurs'],
                "Parties défendeurs": analysis.parties['defendeurs'],
                "Infractions": analysis.infractions,
                "Mots-clés": analysis.keywords
            }
            
            st.json(analysis_data)
        
        # Métadonnées de recherche
        st.markdown("**Métadonnées de recherche**")
        metadata = {
            "Total trouvé": results.total_count,
            "Affichés": len(results.documents),
            "Timestamp": results.timestamp.isoformat() if hasattr(results, 'timestamp') else None,
            "Facettes disponibles": list(results.facets.keys()) if results.facets else []
        }
        st.json(metadata)
    
    def _show_search_tips(self):
        """Affiche des conseils de recherche"""
        st.info("💡 **Conseils pour améliorer votre recherche :**")
        
        tips = [
            "Utilisez @ suivi d'une référence pour rechercher dans un dossier spécifique (ex: @VINCI2024)",
            "Précisez le type de document recherché (ex: conclusions, plainte, assignation)",
            "Mentionnez les parties concernées avec 'contre' (ex: VINCI contre PERINET)",
            "Ajoutez des infractions spécifiques (ex: abus de biens sociaux)",
            "Combinez plusieurs critères pour affiner (ex: @VINCI2024 conclusions corruption)"
        ]
        
        for tip in tips:
            st.caption(f"• {tip}")
    
    def render_sidebar_filters(self):
        """Affiche les filtres avancés dans la sidebar"""
        st.sidebar.markdown("### 🔧 Filtres avancés")
        
        # Type de document
        doc_types = ["Tous", "CONCLUSIONS", "PLAINTE", "ASSIGNATION", "COURRIER", "EXPERTISE", "JUGEMENT", "CONTRAT", "FACTURE"]
        selected_type = st.sidebar.selectbox(
            "Type de document",
            doc_types,
            index=0,
            key="filter_doc_type"
        )
        
        if selected_type != "Tous":
            st.session_state.selected_filters['document_type'] = selected_type
        
        # Période
        st.sidebar.markdown("**Période**")
        date_filter = st.sidebar.radio(
            "Sélectionner",
            ["Toutes dates", "Personnalisée", "30 derniers jours", "6 derniers mois", "Année en cours"],
            key="date_filter_type"
        )
        
        if date_filter == "Personnalisée":
            date_range = st.sidebar.date_input(
                "Sélectionner les dates",
                value=[],
                key="filter_date_range"
            )
            
            if len(date_range) == 2:
                st.session_state.selected_filters['date_range'] = date_range
        
        # Score minimum
        min_score = st.sidebar.slider(
            "Score minimum de pertinence",
            min_value=0,
            max_value=50,
            value=0,
            step=5,
            key="filter_min_score"
        )
        
        if min_score > 0:
            st.session_state.selected_filters['min_score'] = min_score
        
        # Source
        st.sidebar.markdown("**Source des documents**")
        sources = ["Toutes", "Azure Search", "Azure Blob", "Documents importés", "Dossier référence"]
        selected_source = st.sidebar.selectbox(
            "Filtrer par source",
            sources,
            key="filter_source"
        )
        
        if selected_source != "Toutes":
            st.session_state.selected_filters['source'] = selected_source
        
        # Actions sur les filtres
        st.sidebar.markdown("---")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Réinitialiser", key="reset_filters"):
                st.session_state.selected_filters = {}
                st.rerun()
        
        with col2:
            if st.button("✅ Appliquer", key="apply_filters"):
                if st.session_state.last_search_results:
                    st.rerun()
    
    def render_search_history(self):
        """Affiche l'historique des recherches dans la sidebar"""
        # Récupérer l'historique depuis le service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            history = loop.run_until_complete(self.search_service.export_search_history())
            
            if history:
                st.sidebar.markdown("### 📜 Historique récent")
                
                for item in reversed(history[-5:]):
                    query = item['query']
                    timestamp = item['timestamp'].strftime('%H:%M')
                    count = item['results_count']
                    
                    # Tronquer la requête si trop longue
                    display_query = query[:25] + "..." if len(query) > 25 else query
                    
                    if st.sidebar.button(
                        f"🕐 {timestamp} - {display_query} ({count})",
                        key=f"history_{timestamp}_{query[:10]}",
                        use_container_width=True
                    ):
                        st.session_state.universal_search_input = query
                        st.rerun()
                
                # Option pour effacer l'historique
                if st.sidebar.button("🗑️ Effacer l'historique", key="clear_history"):
                    self.search_service._search_history.clear()
                    st.sidebar.success("Historique effacé")
                    st.rerun()
        finally:
            loop.close()
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de recherche depuis le service"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.search_service.get_search_statistics())
        finally:
            loop.close()
    
    def render_statistics_dashboard(self):
        """Affiche un tableau de bord des statistiques"""
        stats = self.get_search_statistics()
        
        st.markdown("### 📊 Tableau de bord des recherches")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔍 Recherches totales", stats.get('total_searches', 0))
        
        with col2:
            st.metric("💾 Taille du cache", stats.get('cache_size', 0))
        
        with col3:
            st.metric("📊 Résultats moyens", f"{stats.get('average_results', 0):.0f}")
        
        with col4:
            st.metric("🔑 Mots-clés uniques", len(stats.get('popular_keywords', {})))
        
        # Mots-clés populaires
        if stats.get('popular_keywords'):
            st.markdown("### 🏷️ Mots-clés les plus recherchés")
            
            keywords = stats['popular_keywords']
            # Créer un nuage de mots simple
            for keyword, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(count / max(keywords.values()))
                    st.caption(keyword)
                with col2:
                    st.caption(f"{count} fois")