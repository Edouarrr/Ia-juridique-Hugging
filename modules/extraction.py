"""Module d'extraction d'informations juridiques"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class ExtractionModule:
    """Module d'extraction intelligente d'informations"""
    
    def __init__(self):
        self.name = "Extraction d'informations"
        self.description = "Extrayez automatiquement les informations clés de vos documents"
        self.icon = "📑"
        self.available = True
        
        # Patterns d'extraction prédéfinis
        self.extraction_patterns = {
            'persons': {
                'patterns': [
                    r'(?:M\.|Mme|Dr|Me|Pr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'([A-Z][a-z]+\s+[A-Z]+)(?:\s|,|\.|$)'
                ],
                'icon': '👤',
                'name': 'Personnes'
            },
            'organizations': {
                'patterns': [
                    r'(?:société|entreprise|SARL|SAS|SA|SCI)\s+([A-Z][A-Za-z\s&-]+)',
                    r'([A-Z][A-Z\s&-]{2,})\s+(?:Inc|Ltd|GmbH|AG|SAS|SARL)'
                ],
                'icon': '🏢',
                'name': 'Organisations'
            },
            'dates': {
                'patterns': [
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                    r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}'
                ],
                'icon': '📅',
                'name': 'Dates'
            },
            'amounts': {
                'patterns': [
                    r'(\d+(?:\s?\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
                    r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)'
                ],
                'icon': '💰',
                'name': 'Montants'
            },
            'references': {
                'patterns': [
                    r'(?:article|clause)\s+\d+(?:\.\d+)*',
                    r'(?:RG|TGI|CA)\s*[:\s]\s*\d+/\d+',
                    r'n°\s*\d+(?:[/-]\d+)*'
                ],
                'icon': '📎',
                'name': 'Références'
            }
        }
    
    def render(self):
        """Interface principale du module"""
        st.markdown(f"### {self.icon} {self.name}")
        st.markdown(f"*{self.description}*")
        
        # Tabs principaux
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Extraction",
            "📊 Analyse",
            "💾 Exports",
            "❓ Aide"
        ])
        
        with tab1:
            self._render_extraction_tab()
        
        with tab2:
            self._render_analysis_tab()
        
        with tab3:
            self._render_export_tab()
        
        with tab4:
            self._render_help_tab()
    
    def _render_extraction_tab(self):
        """Onglet d'extraction principale"""
        
        # Type d'extraction
        extraction_type = st.radio(
            "🎯 Type d'extraction",
            ["Automatique complète", "Points favorables", "Éléments à charge", "Personnalisée"],
            horizontal=True
        )
        
        # Source des documents
        source = st.radio(
            "📁 Source",
            ["Documents chargés", "Texte direct", "Recherche"],
            horizontal=True
        )
        
        documents = self._get_documents_for_extraction(source)
        
        if documents:
            # Configuration
            config = self._get_extraction_config(extraction_type)
            
            # Bouton d'extraction
            if st.button("🚀 Lancer l'extraction", type="primary", use_container_width=True):
                self._perform_extraction(documents, config, extraction_type)
    
    def _get_documents_for_extraction(self, source: str) -> List[Dict[str, Any]]:
        """Récupère les documents selon la source"""
        documents = []
        
        if source == "Documents chargés":
            # Documents depuis la session
            if 'selected_documents' in st.session_state and st.session_state.selected_documents:
                st.info(f"📄 {len(st.session_state.selected_documents)} documents sélectionnés")
                
                # Récupérer le contenu des documents
                for doc_name in st.session_state.selected_documents:
                    # Simuler la récupération du contenu
                    documents.append({
                        'title': doc_name,
                        'content': f"Contenu du document {doc_name}...",  # À remplacer par le vrai contenu
                        'source': 'Session'
                    })
            else:
                st.warning("Aucun document sélectionné")
        
        elif source == "Texte direct":
            # Saisie directe
            text = st.text_area(
                "Collez ou tapez votre texte",
                height=300,
                placeholder="Entrez le texte à analyser..."
            )
            
            if text:
                documents.append({
                    'title': 'Texte direct',
                    'content': text,
                    'source': 'Saisie'
                })
        
        else:  # Recherche
            search_query = st.text_input(
                "Requête de recherche",
                placeholder="Ex: contrats 2024"
            )
            
            if search_query and st.button("🔍 Rechercher"):
                st.info("Recherche simulée - À connecter avec Azure Search")
                # Simuler des résultats
                documents = [
                    {
                        'title': f'Document trouvé {i+1}',
                        'content': f'Contenu relatif à {search_query}...',
                        'source': 'Recherche'
                    }
                    for i in range(3)
                ]
        
        return documents
    
    def _get_extraction_config(self, extraction_type: str) -> Dict[str, Any]:
        """Configuration de l'extraction"""
        config = {
            'type': extraction_type,
            'entities_to_extract': []
        }
        
        if extraction_type == "Personnalisée":
            st.markdown("#### ⚙️ Configuration personnalisée")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection des entités
                for entity_type, entity_info in self.extraction_patterns.items():
                    if st.checkbox(
                        f"{entity_info['icon']} {entity_info['name']}",
                        value=True,
                        key=f"extract_{entity_type}"
                    ):
                        config['entities_to_extract'].append(entity_type)
                
                # Patterns personnalisés
                custom_pattern = st.text_input(
                    "Pattern regex personnalisé",
                    placeholder="Ex: \\b[A-Z]{2,}\\b",
                    help="Expression régulière pour extraction personnalisée"
                )
                
                if custom_pattern:
                    config['custom_pattern'] = custom_pattern
            
            with col2:
                # Options avancées
                config['context_window'] = st.slider(
                    "Fenêtre de contexte",
                    10, 200, 50,
                    help="Nombre de caractères de contexte autour des extractions"
                )
                
                config['min_confidence'] = st.slider(
                    "Confiance minimale",
                    0.0, 1.0, 0.7,
                    help="Seuil de confiance pour les extractions"
                )
                
                config['group_similar'] = st.checkbox(
                    "Grouper les similaires",
                    value=True,
                    help="Regroupe les entités similaires"
                )
        else:
            # Configurations prédéfinies
            if extraction_type == "Points favorables":
                config['focus'] = 'favorable'
                config['keywords'] = ['innocent', 'justifié', 'légitime', 'bonne foi', 'sans intention']
            elif extraction_type == "Éléments à charge":
                config['focus'] = 'charge'
                config['keywords'] = ['coupable', 'intention', 'préméditation', 'fraude', 'violation']
            else:
                config['focus'] = 'all'
                config['entities_to_extract'] = list(self.extraction_patterns.keys())
        
        return config
    
    def _perform_extraction(self, documents: List[Dict[str, Any]], config: Dict[str, Any], extraction_type: str):
        """Effectue l'extraction"""
        
        with st.spinner("Extraction en cours..."):
            results = {
                'documents_analyzed': len(documents),
                'extractions': defaultdict(list),
                'statistics': {},
                'insights': []
            }
            
            # Extraction pour chaque document
            for doc in documents:
                doc_extractions = self._extract_from_document(doc, config)
                
                # Agrégation des résultats
                for entity_type, entities in doc_extractions.items():
                    results['extractions'][entity_type].extend(entities)
            
            # Analyse des résultats
            results['statistics'] = self._analyze_extractions(results['extractions'])
            
            # Génération d'insights
            results['insights'] = self._generate_extraction_insights(
                results['extractions'], 
                config, 
                extraction_type
            )
            
            # Sauvegarder les résultats
            if 'extraction_history' not in st.session_state:
                st.session_state.extraction_history = []
            
            st.session_state.extraction_history.append({
                'timestamp': datetime.now(),
                'type': extraction_type,
                'results': results
            })
            
            # Afficher les résultats
            self._display_extraction_results(results, extraction_type)
    
    def _extract_from_document(self, doc: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Extrait les entités d'un document"""
        extractions = defaultdict(list)
        content = doc['content']
        
        # Extraction selon le type
        if config['type'] == "Points favorables":
            extractions['favorable_points'] = self._extract_favorable_points(content, config)
        elif config['type'] == "Éléments à charge":
            extractions['charge_elements'] = self._extract_charge_elements(content, config)
        else:
            # Extraction des entités sélectionnées
            for entity_type in config.get('entities_to_extract', []):
                if entity_type in self.extraction_patterns:
                    entities = self._extract_entities(
                        content, 
                        self.extraction_patterns[entity_type]['patterns'],
                        config.get('context_window', 50)
                    )
                    extractions[entity_type] = entities
            
            # Pattern personnalisé
            if config.get('custom_pattern'):
                custom_entities = self._extract_with_custom_pattern(
                    content,
                    config['custom_pattern'],
                    config.get('context_window', 50)
                )
                extractions['custom'] = custom_entities
        
        return extractions
    
    def _extract_entities(self, text: str, patterns: List[str], context_window: int) -> List[Dict[str, Any]]:
        """Extrait des entités avec leur contexte"""
        entities = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Extraire le contexte
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context = text[start:end]
                
                # Nettoyer le contexte
                context = ' '.join(context.split())
                
                entities.append({
                    'value': match.group(0),
                    'context': context,
                    'position': match.start(),
                    'confidence': 0.8  # Simulé
                })
        
        return entities
    
    def _extract_favorable_points(self, text: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les points favorables"""
        points = []
        
        # Patterns pour les points favorables
        favorable_patterns = [
            r'(?:n\'a pas|jamais|aucun|absence de)\s+[^.]+(?:intention|préméditation|volonté)',
            r'(?:bonne foi|légitime|justifié|innocent|victime)',
            r'(?:coopér|collabor|aid)\w+\s+(?:avec|à|aux)\s+(?:enquête|autorités|police)',
            r'(?:témoignages?\s+favorables?|attestations?\s+positives?)'
        ]
        
        for pattern in favorable_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Extraire la phrase complète
                sentence_start = text.rfind('.', 0, match.start()) + 1
                sentence_end = text.find('.', match.end())
                if sentence_end == -1:
                    sentence_end = len(text)
                
                sentence = text[sentence_start:sentence_end].strip()
                
                points.append({
                    'type': 'favorable',
                    'text': sentence,
                    'keyword': match.group(0),
                    'importance': self._assess_importance(sentence),
                    'confidence': 0.85
                })
        
        return points
    
    def _extract_charge_elements(self, text: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les éléments à charge"""
        elements = []
        
        # Patterns pour les éléments à charge
        charge_patterns = [
            r'(?:preuves?\s+accablantes?|éléments?\s+compromettants?)',
            r'(?:intention|préméditation|volonté)\s+(?:de|d\')',
            r'(?:fraude|escroquerie|détournement|abus)',
            r'(?:signatures?\s+falsifiées?|documents?\s+falsifiés?)'
        ]
        
        for pattern in charge_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Extraire le contexte élargi
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end]
                
                elements.append({
                    'type': 'charge',
                    'text': context.strip(),
                    'keyword': match.group(0),
                    'severity': self._assess_severity(context),
                    'confidence': 0.8
                })
        
        return elements
    
    def _extract_with_custom_pattern(self, text: str, pattern: str, context_window: int) -> List[Dict[str, Any]]:
        """Extraction avec un pattern personnalisé"""
        try:
            return self._extract_entities(text, [pattern], context_window)
        except re.error as e:
            st.error(f"Erreur dans le pattern regex : {e}")
            return []
    
    def _assess_importance(self, text: str) -> int:
        """Évalue l'importance d'un point (1-10)"""
        importance = 5
        
        # Mots augmentant l'importance
        high_importance = ['crucial', 'déterminant', 'preuve', 'établit', 'démontre']
        low_importance = ['suggère', 'pourrait', 'éventuellement', 'peut-être']
        
        text_lower = text.lower()
        
        for word in high_importance:
            if word in text_lower:
                importance += 1
        
        for word in low_importance:
            if word in text_lower:
                importance -= 1
        
        return max(1, min(10, importance))
    
    def _assess_severity(self, text: str) -> str:
        """Évalue la sévérité d'un élément à charge"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['crime', 'délit grave', 'récidive']):
            return 'Critique'
        elif any(word in text_lower for word in ['infraction', 'violation', 'manquement']):
            return 'Important'
        else:
            return 'Modéré'
    
    def _analyze_extractions(self, extractions: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Analyse statistique des extractions"""
        stats = {
            'total_extractions': sum(len(v) for v in extractions.values()),
            'by_type': {}
        }
        
        for entity_type, entities in extractions.items():
            # Dédupliquer
            unique_values = set()
            for entity in entities:
                if isinstance(entity, dict):
                    unique_values.add(entity.get('value', str(entity)))
                else:
                    unique_values.add(str(entity))
            
            stats['by_type'][entity_type] = {
                'total': len(entities),
                'unique': len(unique_values),
                'top_5': Counter([
                    e.get('value', str(e)) if isinstance(e, dict) else str(e) 
                    for e in entities
                ]).most_common(5)
            }
        
        return stats
    
    def _generate_extraction_insights(self, extractions: Dict[str, List[Any]], config: Dict[str, Any], extraction_type: str) -> List[str]:
        """Génère des insights sur les extractions"""
        insights = []
        
        # Insights selon le type
        if extraction_type == "Points favorables":
            favorable = extractions.get('favorable_points', [])
            if favorable:
                insights.append(f"✅ {len(favorable)} points favorables identifiés")
                
                # Points les plus importants
                important_points = [p for p in favorable if p.get('importance', 0) >= 8]
                if important_points:
                    insights.append(f"⭐ {len(important_points)} points de haute importance")
        
        elif extraction_type == "Éléments à charge":
            charges = extractions.get('charge_elements', [])
            if charges:
                insights.append(f"⚠️ {len(charges)} éléments à charge détectés")
                
                # Éléments critiques
                critical = [e for e in charges if e.get('severity') == 'Critique']
                if critical:
                    insights.append(f"🚨 {len(critical)} éléments critiques nécessitant attention immédiate")
        
        else:
            # Insights généraux
            total = sum(len(v) for v in extractions.values())
            insights.append(f"📊 {total} éléments extraits au total")
            
            # Personnes les plus mentionnées
            if 'persons' in extractions and extractions['persons']:
                persons_count = Counter([p['value'] for p in extractions['persons']])
                top_person = persons_count.most_common(1)[0]
                insights.append(f"👤 {top_person[0]} est mentionné {top_person[1]} fois")
            
            # Montants totaux
            if 'amounts' in extractions and extractions['amounts']:
                amounts = []
                for amount_dict in extractions['amounts']:
                    try:
                        # Nettoyer et parser le montant
                        amount_str = amount_dict['value']
                        amount_clean = re.sub(r'[^\d,]', '', amount_str).replace(',', '.')
                        amounts.append(float(amount_clean))
                    except:
                        pass
                
                if amounts:
                    total_amount = sum(amounts)
                    insights.append(f"💰 Montant total identifié : {total_amount:,.2f} €")
        
        return insights
    
    def _display_extraction_results(self, results: Dict[str, Any], extraction_type: str):
        """Affiche les résultats de l'extraction"""
        st.success(f"✅ Extraction terminée - {results['documents_analyzed']} documents analysés")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Documents", results['documents_analyzed'])
        
        with col2:
            st.metric("🔍 Extractions", results['statistics']['total_extractions'])
        
        with col3:
            types_count = len(results['statistics']['by_type'])
            st.metric("📊 Types", types_count)
        
        with col4:
            # Métrique spécifique selon le type
            if extraction_type == "Points favorables":
                favorable_count = len(results['extractions'].get('favorable_points', []))
                st.metric("✅ Favorables", favorable_count)
            elif extraction_type == "Éléments à charge":
                charge_count = len(results['extractions'].get('charge_elements', []))
                st.metric("⚠️ À charge", charge_count)
            else:
                unique_total = sum(
                    stats['unique'] 
                    for stats in results['statistics']['by_type'].values()
                )
                st.metric("🎯 Uniques", unique_total)
        
        # Insights
        if results['insights']:
            st.markdown("### 💡 Insights clés")
            for insight in results['insights']:
                st.info(insight)
        
        # Résultats détaillés par type
        st.markdown("### 📋 Résultats détaillés")
        
        if extraction_type in ["Points favorables", "Éléments à charge"]:
            # Affichage spécifique pour points favorables/charges
            self._display_specific_results(results['extractions'], extraction_type)
        else:
            # Affichage par type d'entité
            for entity_type, entities in results['extractions'].items():
                if entities:
                    entity_info = self.extraction_patterns.get(
                        entity_type, 
                        {'icon': '📌', 'name': entity_type.title()}
                    )
                    
                    with st.expander(
                        f"{entity_info['icon']} {entity_info['name']} ({len(entities)} trouvés)",
                        expanded=entity_type in ['persons', 'amounts']
                    ):
                        self._display_entity_results(entities, entity_type)
    
    def _display_specific_results(self, extractions: Dict[str, List[Any]], extraction_type: str):
        """Affichage spécifique pour points favorables/charges"""
        if extraction_type == "Points favorables":
            points = extractions.get('favorable_points', [])
            
            if points:
                # Trier par importance
                sorted_points = sorted(points, key=lambda x: x.get('importance', 0), reverse=True)
                
                for i, point in enumerate(sorted_points, 1):
                    importance = point.get('importance', 5)
                    color = 'green' if importance >= 8 else 'blue' if importance >= 5 else 'gray'
                    
                    st.markdown(
                        f"""
                        <div style="border-left: 4px solid {color}; padding-left: 1rem; margin: 1rem 0;">
                            <strong>Point {i}</strong> - Importance: {importance}/10<br>
                            <em>"{point['text']}"</em><br>
                            <small>Mot-clé: {point['keyword']}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        elif extraction_type == "Éléments à charge":
            elements = extractions.get('charge_elements', [])
            
            if elements:
                # Grouper par sévérité
                by_severity = defaultdict(list)
                for element in elements:
                    by_severity[element.get('severity', 'Modéré')].append(element)
                
                # Afficher par niveau de sévérité
                for severity in ['Critique', 'Important', 'Modéré']:
                    if severity in by_severity:
                        severity_elements = by_severity[severity]
                        
                        color = {'Critique': 'red', 'Important': 'orange', 'Modéré': 'yellow'}[severity]
                        icon = {'Critique': '🚨', 'Important': '⚠️', 'Modéré': 'ℹ️'}[severity]
                        
                        st.markdown(f"#### {icon} {severity} ({len(severity_elements)} éléments)")
                        
                        for element in severity_elements:
                            st.markdown(
                                f"""
                                <div style="border-left: 4px solid {color}; padding-left: 1rem; margin: 0.5rem 0;">
                                    <strong>Élément identifié:</strong> {element['keyword']}<br>
                                    <em>Contexte: "{element['text'][:200]}..."</em>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
    
    def _display_entity_results(self, entities: List[Any], entity_type: str):
        """Affiche les résultats pour un type d'entité"""
        # Dédupliquer et compter
        entity_counts = Counter()
        entity_contexts = defaultdict(list)
        
        for entity in entities:
            if isinstance(entity, dict):
                value = entity.get('value', str(entity))
                context = entity.get('context', '')
                entity_counts[value] += 1
                if context:
                    entity_contexts[value].append(context)
            else:
                entity_counts[str(entity)] += 1
        
        # Afficher les plus fréquents
        st.markdown("**Top 10 des plus fréquents:**")
        
        for value, count in entity_counts.most_common(10):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"• **{value}**")
                
                # Afficher un contexte exemple
                if value in entity_contexts and entity_contexts[value]:
                    with st.expander("Voir un exemple de contexte"):
                        st.text(entity_contexts[value][0])
            
            with col2:
                st.write(f"{count} fois")
        
        # Option pour voir tous
        if len(entity_counts) > 10:
            if st.checkbox(f"Voir tous ({len(entity_counts)} au total)", key=f"see_all_{entity_type}"):
                remaining = list(entity_counts.items())[10:]
                for value, count in remaining:
                    st.write(f"• {value} ({count} fois)")
    
    def _render_analysis_tab(self):
        """Onglet d'analyse des extractions"""
        st.markdown("#### 📊 Analyse des extractions")
        
        if 'extraction_history' not in st.session_state or not st.session_state.extraction_history:
            st.info("Aucune extraction à analyser. Effectuez d'abord une extraction.")
            return
        
        # Sélection de l'extraction à analyser
        extraction_options = [
            f"{ext['timestamp'].strftime('%d/%m/%Y %H:%M')} - {ext['type']}"
            for ext in st.session_state.extraction_history
        ]
        
        selected_idx = st.selectbox(
            "Choisir une extraction",
            range(len(extraction_options)),
            format_func=lambda x: extraction_options[x],
            index=len(extraction_options)-1
        )
        
        selected_extraction = st.session_state.extraction_history[selected_idx]
        results = selected_extraction['results']
        
        # Visualisations
        self._display_extraction_analytics(results)
    
    def _display_extraction_analytics(self, results: Dict[str, Any]):
        """Affiche les analyses visuelles des extractions"""
        
        # Distribution par type
        st.markdown("##### 📊 Distribution par type")
        
        type_data = []
        for entity_type, stats in results['statistics']['by_type'].items():
            type_data.append({
                'Type': entity_type.replace('_', ' ').title(),
                'Total': stats['total'],
                'Uniques': stats['unique']
            })
        
        if type_data:
            # Créer un graphique simple avec colonnes
            cols = st.columns(len(type_data))
            for i, data in enumerate(type_data):
                with cols[i]:
                    st.metric(
                        data['Type'],
                        data['Total'],
                        delta=f"{data['Uniques']} uniques"
                    )
        
        # Top entités par type
        st.markdown("##### 🏆 Top entités")
        
        for entity_type, stats in results['statistics']['by_type'].items():
            if stats['top_5']:
                st.markdown(f"**{entity_type.replace('_', ' ').title()}:**")
                
                for value, count in stats['top_5']:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {value}")
                    with col2:
                        st.write(f"({count}x)")
        
        # Graphique si plotly disponible
        try:
            import plotly.express as px
            import pandas as pd
            
            # Créer un DataFrame pour visualisation
            viz_data = []
            for entity_type, stats in results['statistics']['by_type'].items():
                for value, count in stats['top_5']:
                    viz_data.append({
                        'Type': entity_type,
                        'Entité': value[:30] + '...' if len(value) > 30 else value,
                        'Occurrences': count
                    })
            
            if viz_data:
                df = pd.DataFrame(viz_data)
                
                fig = px.bar(
                    df,
                    x='Occurrences',
                    y='Entité',
                    color='Type',
                    orientation='h',
                    title="Top entités extraites par type"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass
    
    def _render_export_tab(self):
        """Onglet d'export des extractions"""
        st.markdown("#### 💾 Export des extractions")
        
        if 'extraction_history' not in st.session_state or not st.session_state.extraction_history:
            st.info("Aucune extraction à exporter.")
            return
        
        # Sélection de l'extraction
        extraction_options = [
            f"{ext['timestamp'].strftime('%d/%m/%Y %H:%M')} - {ext['type']}"
            for ext in st.session_state.extraction_history
        ]
        
        selected_idx = st.selectbox(
            "Extraction à exporter",
            range(len(extraction_options)),
            format_func=lambda x: extraction_options[x],
            index=len(extraction_options)-1,
            key="export_extraction_select"
        )
        
        selected_extraction = st.session_state.extraction_history[selected_idx]
        
        # Formats d'export
        col1, col2 = st.columns(2)
        
        with col1:
            # Export JSON
            import json
            json_data = json.dumps(selected_extraction, default=str, ensure_ascii=False, indent=2)
            
            st.download_button(
                "📥 Télécharger JSON",
                data=json_data,
                file_name=f"extraction_{selected_extraction['timestamp'].strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # Export texte
            text_export = self._create_text_export(selected_extraction)
            st.download_button(
                "📥 Télécharger TXT",
                data=text_export,
                file_name=f"extraction_{selected_extraction['timestamp'].strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            # Export CSV si pandas disponible
            try:
                import pandas as pd
                
                # Créer un DataFrame
                csv_data = []
                for entity_type, entities in selected_extraction['results']['extractions'].items():
                    for entity in entities:
                        if isinstance(entity, dict):
                            csv_data.append({
                                'Type': entity_type,
                                'Valeur': entity.get('value', str(entity)),
                                'Contexte': entity.get('context', '')[:100],
                                'Confiance': entity.get('confidence', 0)
                            })
                
                if csv_data:
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        "📥 Télécharger CSV",
                        data=csv,
                        file_name=f"extraction_{selected_extraction['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            except ImportError:
                st.info("pandas requis pour l'export CSV")
    
    def _create_text_export(self, extraction: Dict[str, Any]) -> str:
        """Crée un export texte formaté"""
        lines = []
        lines.append("RAPPORT D'EXTRACTION")
        lines.append("=" * 50)
        lines.append(f"Date : {extraction['timestamp'].strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"Type : {extraction['type']}")
        lines.append(f"Documents analysés : {extraction['results']['documents_analyzed']}")
        lines.append("")
        
        # Statistiques
        lines.append("STATISTIQUES")
        lines.append("-" * 30)
        lines.append(f"Total des extractions : {extraction['results']['statistics']['total_extractions']}")
        lines.append("")
        
        # Résultats par type
        lines.append("RÉSULTATS DÉTAILLÉS")
        lines.append("-" * 30)
        
        for entity_type, entities in extraction['results']['extractions'].items():
            if entities:
                lines.append(f"\n{entity_type.upper()} ({len(entities)} trouvés)")
                
                # Compter les occurrences
                counts = Counter()
                for entity in entities:
                    if isinstance(entity, dict):
                        counts[entity.get('value', str(entity))] += 1
                    else:
                        counts[str(entity)] += 1
                
                # Afficher les plus fréquents
                for value, count in counts.most_common(10):
                    lines.append(f"  • {value} ({count}x)")
        
        # Insights
        if extraction['results']['insights']:
            lines.append("\n\nINSIGHTS")
            lines.append("-" * 30)
            for insight in extraction['results']['insights']:
                lines.append(f"• {insight}")
        
        return "\n".join(lines)
    
    def _render_help_tab(self):
        """Onglet d'aide"""
        st.markdown("""
        #### ❓ Guide d'utilisation du module d'extraction
        
        ##### 🎯 Objectifs
        Ce module permet d'extraire automatiquement des informations clés de vos documents juridiques :
        - Personnes, organisations, dates, montants
        - Points favorables à la défense
        - Éléments à charge
        - Références juridiques
        
        ##### 🔧 Types d'extraction
        
        1. **Extraction automatique complète**
           - Extrait toutes les entités disponibles
           - Idéal pour une vue d'ensemble
        
        2. **Points favorables**
           - Identifie les éléments positifs pour la défense
           - Recherche : absence d'intention, bonne foi, coopération
        
        3. **Éléments à charge**
           - Détecte les points négatifs
           - Classe par niveau de sévérité
        
        4. **Extraction personnalisée**
           - Choisissez les types d'entités
           - Ajoutez vos propres patterns regex
        
        ##### 💡 Conseils d'utilisation
        
        - **Documents longs** : Utilisez d'abord l'extraction automatique
        - **Analyse ciblée** : Préférez les extractions spécifiques
        - **Patterns personnalisés** : Testez sur un petit échantillon d'abord
        - **Export** : Sauvegardez toujours les extractions importantes
        
        ##### 📊 Interprétation des résultats
        
        - **Confiance** : Score de 0 à 1 (1 = très confiant)
        - **Importance** : Échelle de 1 à 10 pour les points favorables
        - **Sévérité** : Critique > Important > Modéré pour les charges
        
        ##### ⚡ Patterns regex utiles
        
        ```regex
        # Numéros de téléphone français
        (?:0|\+33)[1-9](?:[0-9]{8})
        
        # Adresses email
        [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
        
        # Numéros SIRET
        [0-9]{14}
        
        # Plaques d'immatriculation
        [A-Z]{2}-[0-9]{3}-[A-Z]{2}
        ```
        """)


# Point d'entrée pour tests
if __name__ == "__main__":
    module = ExtractionModule()
    module.render()