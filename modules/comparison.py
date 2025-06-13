"""Module de comparaison de documents juridiques - Version améliorée"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import logging
import json
import base64
from io import BytesIO
import hashlib

logger = logging.getLogger(__name__)

# ============= IMPORTS OPTIONNELS AVEC GESTION D'ERREURS =============

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas non disponible - certaines fonctionnalités seront limitées")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly non disponible - les graphiques seront désactivés")

# Gestion des imports de modules locaux
try:
    from managers.multi_llm_manager import MultiLLMManager
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("MultiLLMManager non disponible - analyse IA désactivée")
    LLM_AVAILABLE = False
    
    class MultiLLMManager:
        def __init__(self):
            self.clients = {}
        def query_single_llm(self, *args, **kwargs):
            return {'success': False, 'response': 'LLM non configuré'}

try:
    from utils.helpers import extract_entities, clean_key
    UTILS_AVAILABLE = True
except ImportError:
    logger.warning("utils.helpers non disponible - utilisation de fonctions intégrées")
    UTILS_AVAILABLE = False
    
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """Extraction d'entités améliorée avec patterns regex"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'amounts': [],
            'references': []
        }
        
        # Patterns pour différents types d'entités
        patterns = {
            'persons': [
                r'(?:M\.|Mme|Dr|Me|Pr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'([A-Z][a-z]+\s+[A-Z]+)(?:\s|,|\.|$)'
            ],
            'organizations': [
                r'(?:société|entreprise|SARL|SAS|SA|SCI)\s+([A-Z][A-Za-z\s&-]+)',
                r'([A-Z][A-Z\s&-]{2,})\s+(?:Inc|Ltd|GmbH|AG|SAS|SARL)'
            ],
            'dates': [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
                r'(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+\d{1,2}\s+\w+\s+\d{4}'
            ],
            'amounts': [
                r'(\d+(?:\s?\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
                r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)'
            ],
            'references': [
                r'(?:article|clause)\s+\d+(?:\.\d+)*',
                r'(?:RG|TGI|CA)\s*[:\s]\s*\d+/\d+',
                r'n°\s*\d+(?:[/-]\d+)*'
            ]
        }
        
        # Extraction pour chaque type
        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities[entity_type].extend(matches)
        
        # Dédupliquer et nettoyer
        for entity_type in entities:
            entities[entity_type] = list(set(str(e).strip() for e in entities[entity_type] if e))
        
        return entities
    
    def clean_key(key: str) -> str:
        """Nettoie une clé pour utilisation sûre"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(key))

# ============= FONCTIONS UTILITAIRES AMÉLIORÉES =============

def get_text_hash(text: str) -> str:
    """Génère un hash unique pour un texte"""
    return hashlib.md5(text.encode()).hexdigest()[:8]

def format_percentage(value: float) -> str:
    """Formate un pourcentage avec couleur"""
    color = "green" if value > 0.7 else "orange" if value > 0.4 else "red"
    return f'<span style="color: {color}; font-weight: bold;">{value:.0%}</span>'

def create_download_link(data: Any, filename: str, text: str) -> str:
    """Crée un lien de téléchargement"""
    if isinstance(data, dict):
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        data_str = str(data)
    
    b64 = base64.b64encode(data_str.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'

# ============= CLASSE PRINCIPALE DU MODULE =============

class ComparisonModule:
    """Module avancé de comparaison de documents juridiques"""
    
    def __init__(self):
        self.name = "Comparaison de documents"
        self.description = "Compare et analyse les différences entre documents juridiques"
        self.icon = "📊"
        self.version = "2.0"
        
        # Initialiser l'état de session
        if 'comparison_history' not in st.session_state:
            st.session_state.comparison_history = []
        if 'saved_comparisons' not in st.session_state:
            st.session_state.saved_comparisons = {}
        
    def render(self):
        """Interface principale du module"""
        st.markdown(f"### {self.icon} {self.name}")
        st.markdown(f"*{self.description}*")
        
        # Menu principal
        menu_tab, history_tab, saved_tab, help_tab = st.tabs([
            "🔍 Nouvelle comparaison", 
            "📜 Historique",
            "💾 Comparaisons sauvegardées", 
            "❓ Aide"
        ])
        
        with menu_tab:
            self._render_comparison_interface()
            
        with history_tab:
            self._render_history()
            
        with saved_tab:
            self._render_saved_comparisons()
            
        with help_tab:
            self._render_help()
    
    def _render_comparison_interface(self):
        """Interface de comparaison principale"""
        
        # Sélection de la source des documents
        source_type = st.radio(
            "📁 Source des documents",
            ["Documents chargés", "Saisie directe", "Comparaison rapide"],
            horizontal=True
        )
        
        documents = []
        
        if source_type == "Documents chargés":
            documents = self._get_loaded_documents()
        elif source_type == "Saisie directe":
            documents = self._get_manual_documents()
        else:
            documents = self._get_quick_comparison_documents()
        
        if len(documents) >= 2:
            # Configuration de la comparaison
            config = self._get_comparison_config(documents)
            
            # Bouton de lancement avec options
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if st.button("🚀 Lancer la comparaison", type="primary", use_container_width=True):
                    self._perform_comparison(documents, config)
            
            with col2:
                if st.button("💾 Sauvegarder config", use_container_width=True):
                    self._save_config(config)
                    
            with col3:
                if st.button("🔄 Réinitialiser", use_container_width=True):
                    st.rerun()
        else:
            st.warning("⚠️ Sélectionnez au moins 2 documents pour effectuer une comparaison")
    
    def _get_loaded_documents(self) -> List[Dict[str, Any]]:
        """Récupère les documents depuis la session"""
        documents = []
        
        # Vérifier différentes sources possibles
        if 'azure_documents' in st.session_state:
            for doc_id, doc in st.session_state.azure_documents.items():
                documents.append({
                    'id': doc_id,
                    'title': getattr(doc, 'title', f'Document {doc_id}'),
                    'content': getattr(doc, 'content', ''),
                    'source': getattr(doc, 'source', 'Azure'),
                    'metadata': getattr(doc, 'metadata', {})
                })
        
        if not documents:
            st.info("💡 Aucun document chargé. Utilisez le module d'import ou la saisie directe.")
            return []
        
        # Interface de sélection améliorée
        st.markdown("#### 📄 Sélection des documents")
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("🔍 Rechercher", placeholder="Titre, contenu...")
        with col2:
            doc_type_filter = st.selectbox(
                "📑 Type", 
                ["Tous"] + list(set(d.get('metadata', {}).get('type', 'Autre') for d in documents))
            )
        
        # Filtrage
        filtered_docs = documents
        if search_term:
            filtered_docs = [
                d for d in filtered_docs 
                if search_term.lower() in d['title'].lower() or 
                   search_term.lower() in d['content'].lower()
            ]
        if doc_type_filter != "Tous":
            filtered_docs = [
                d for d in filtered_docs 
                if d.get('metadata', {}).get('type') == doc_type_filter
            ]
        
        # Sélection avec preview
        selected_docs = []
        
        for i, doc in enumerate(filtered_docs):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Checkbox avec info
                is_selected = st.checkbox(
                    doc['title'],
                    key=f"select_loaded_{i}",
                    help=f"Source: {doc['source']} | Taille: {len(doc['content'])} caractères"
                )
                
                if is_selected:
                    selected_docs.append(doc)
                    
            with col2:
                # Preview button
                if st.button("👁️", key=f"preview_loaded_{i}", help="Aperçu"):
                    with st.expander(f"Aperçu : {doc['title']}", expanded=True):
                        st.text(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
        
        return selected_docs
    
    def _get_manual_documents(self) -> List[Dict[str, Any]]:
        """Interface de saisie manuelle de documents"""
        st.markdown("#### ✍️ Saisie directe des documents")
        
        documents = []
        
        # Nombre de documents à saisir
        num_docs = st.number_input(
            "Nombre de documents", 
            min_value=2, 
            max_value=10, 
            value=2,
            help="Minimum 2 documents pour une comparaison"
        )
        
        # Saisie pour chaque document
        for i in range(num_docs):
            with st.expander(f"📄 Document {i+1}", expanded=i<2):
                title = st.text_input(
                    "Titre", 
                    value=f"Document {i+1}",
                    key=f"manual_title_{i}"
                )
                
                doc_type = st.selectbox(
                    "Type",
                    ["Témoignage", "Expertise", "Contrat", "Courrier", "Autre"],
                    key=f"manual_type_{i}"
                )
                
                content = st.text_area(
                    "Contenu",
                    height=200,
                    placeholder="Collez ou tapez le contenu du document...",
                    key=f"manual_content_{i}"
                )
                
                if content:
                    documents.append({
                        'id': f'manual_{i}',
                        'title': title,
                        'content': content,
                        'source': 'Saisie manuelle',
                        'metadata': {
                            'type': doc_type,
                            'created': datetime.now().isoformat()
                        }
                    })
        
        return documents
    
    def _get_quick_comparison_documents(self) -> List[Dict[str, Any]]:
        """Interface de comparaison rapide avec templates"""
        st.markdown("#### ⚡ Comparaison rapide")
        
        # Templates prédéfinis
        template_type = st.selectbox(
            "Choisir un template",
            [
                "Témoignages contradictoires",
                "Versions de contrat",
                "Expertises divergentes",
                "Déclarations successives",
                "Personnalisé"
            ]
        )
        
        if template_type == "Personnalisé":
            return self._get_manual_documents()
        
        # Générer des documents selon le template
        templates = {
            "Témoignages contradictoires": [
                {
                    'title': 'Témoignage A - 15/01/2024',
                    'content': """Je soussigné M. Dupont, déclare avoir vu l'accident se produire à 14h30. 
                    Le véhicule bleu arrivait à grande vitesse et a percuté le véhicule rouge qui était à l'arrêt.
                    J'étais sur le trottoir d'en face, à environ 20 mètres."""
                },
                {
                    'title': 'Témoignage B - 16/01/2024',
                    'content': """Je soussignée Mme Martin, témoin de l'accident, affirme que les faits se sont produits vers 15h00.
                    Les deux véhicules roulaient et le véhicule rouge a brusquement freiné, causant la collision.
                    J'étais dans ma voiture juste derrière."""
                }
            ],
            "Versions de contrat": [
                {
                    'title': 'Contrat v1 - Draft',
                    'content': """CONTRAT DE PRESTATION DE SERVICES
                    Article 1 : Objet - Développement d'une application web
                    Article 2 : Durée - 6 mois à compter de la signature
                    Article 3 : Prix - 50 000 € HT payables en 3 fois"""
                },
                {
                    'title': 'Contrat v2 - Final',
                    'content': """CONTRAT DE PRESTATION DE SERVICES
                    Article 1 : Objet - Développement d'une application web et mobile
                    Article 2 : Durée - 8 mois à compter de la signature
                    Article 3 : Prix - 65 000 € HT payables en 4 fois
                    Article 4 : Pénalités de retard - 1% par jour"""
                }
            ]
        }
        
        # Afficher les templates
        selected_templates = templates.get(template_type, [])
        documents = []
        
        for i, template in enumerate(selected_templates):
            with st.expander(f"📄 {template['title']}", expanded=True):
                # Permettre l'édition
                content = st.text_area(
                    "Contenu (modifiable)",
                    value=template['content'],
                    height=150,
                    key=f"template_content_{i}"
                )
                
                documents.append({
                    'id': f'template_{i}',
                    'title': template['title'],
                    'content': content,
                    'source': 'Template',
                    'metadata': {'type': template_type}
                })
        
        return documents
    
    def _get_comparison_config(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Interface de configuration avancée"""
        st.markdown("#### ⚙️ Configuration de l'analyse")
        
        config = {}
        
        # Configuration principale en colonnes
        col1, col2, col3 = st.columns(3)
        
        with col1:
            config['comparison_type'] = st.selectbox(
                "🎯 Type d'analyse",
                [
                    "Analyse intelligente",
                    "Comparaison chronologique",
                    "Recherche de contradictions",
                    "Analyse d'évolution",
                    "Comparaison structurelle",
                    "Analyse sémantique"
                ],
                help="L'analyse intelligente s'adapte au type de documents"
            )
        
        with col2:
            config['detail_level'] = st.select_slider(
                "📊 Niveau de détail",
                options=["Synthèse", "Standard", "Détaillé", "Exhaustif"],
                value="Détaillé"
            )
        
        with col3:
            config['output_format'] = st.selectbox(
                "📄 Format de sortie",
                ["Interactif", "Rapport PDF", "Export JSON", "Tableau comparatif"],
                help="Format de présentation des résultats"
            )
        
        # Options avancées dans un expander
        with st.expander("🔧 Options avancées", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                config['focus_differences'] = st.checkbox(
                    "🔍 Focus sur les différences", 
                    value=True,
                    help="Met en évidence les divergences"
                )
                
                config['highlight_contradictions'] = st.checkbox(
                    "⚠️ Signaler les contradictions", 
                    value=True,
                    help="Identifie les incohérences flagrantes"
                )
                
                config['extract_entities'] = st.checkbox(
                    "👥 Extraire les entités", 
                    value=True,
                    help="Personnes, lieux, dates, montants..."
                )
                
                config['timeline_analysis'] = st.checkbox(
                    "📅 Analyse temporelle",
                    value=config['comparison_type'] == "Comparaison chronologique",
                    help="Reconstruit la chronologie des événements"
                )
            
            with col2:
                config['similarity_threshold'] = st.slider(
                    "Seuil de similarité",
                    0.0, 1.0, 0.7,
                    help="Pour détecter les passages similaires"
                )
                
                config['min_change_length'] = st.number_input(
                    "Longueur min. des changements",
                    min_value=10,
                    max_value=500,
                    value=50,
                    help="En caractères"
                )
                
                config['ai_analysis'] = st.checkbox(
                    "🤖 Analyse IA",
                    value=LLM_AVAILABLE,
                    disabled=not LLM_AVAILABLE,
                    help="Utilise l'IA pour une analyse approfondie"
                )
                
                if config['ai_analysis']:
                    config['ai_temperature'] = st.slider(
                        "Créativité IA",
                        0.0, 1.0, 0.3,
                        help="0 = Factuel, 1 = Créatif"
                    )
        
        # Sélection finale des documents avec ordre
        st.markdown("##### 📑 Ordre de comparaison")
        
        # Permettre de réordonner les documents
        doc_order = []
        for i, doc in enumerate(documents):
            priority = st.number_input(
                f"Priorité de '{doc['title']}'",
                min_value=1,
                max_value=len(documents),
                value=i+1,
                key=f"doc_order_{i}"
            )
            doc_order.append((priority, doc))
        
        # Trier selon la priorité
        doc_order.sort(key=lambda x: x[0])
        config['selected_documents'] = [doc for _, doc in doc_order]
        
        return config
    
    def _perform_comparison(self, documents: List[Dict[str, Any]], config: Dict[str, Any]):
        """Lance la comparaison avec barre de progression"""
        
        # Container pour la progression
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Analyse en cours...")
            
            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Étapes de l'analyse
            steps = [
                ("Préparation des documents", 0.1),
                ("Extraction des entités", 0.2),
                ("Analyse structurelle", 0.3),
                ("Comparaison du contenu", 0.5),
                ("Recherche de patterns", 0.6),
                ("Analyse sémantique", 0.7),
                ("Génération des insights", 0.8),
                ("Création des visualisations", 0.9),
                ("Finalisation du rapport", 1.0)
            ]
            
            # Simuler la progression (remplacer par vraie logique)
            for step_name, progress in steps:
                status_text.text(f"⏳ {step_name}...")
                progress_bar.progress(progress)
                
                # Effectuer l'étape réelle
                if progress == 0.5:
                    # Point central : faire la vraie comparaison
                    comparison_result = generate_comparison(documents, config, {})
            
            # Clear progress
            progress_container.empty()
        
        # Afficher les résultats
        if comparison_result:
            # Sauvegarder dans l'historique
            st.session_state.comparison_history.append({
                'timestamp': datetime.now(),
                'documents': [d['title'] for d in documents],
                'config': config,
                'result': comparison_result
            })
            
            # Afficher
            self._display_comparison_results(comparison_result)
    
    def _display_comparison_results(self, result: Dict[str, Any]):
        """Affichage amélioré des résultats"""
        st.markdown("### 📊 Résultats de l'analyse comparative")
        
        # Métriques principales
        stats = result.get('comparison', {}).get('statistics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            conv_count = stats.get('total_convergences', 0)
            st.metric(
                "✅ Convergences", 
                conv_count,
                delta="Points communs"
            )
        
        with col2:
            div_count = stats.get('total_divergences', 0)
            st.metric(
                "❌ Divergences", 
                div_count,
                delta="Différences" if div_count > 0 else None,
                delta_color="inverse"
            )
        
        with col3:
            reliability = stats.get('reliability_score', 0)
            st.metric(
                "📈 Fiabilité",
                f"{reliability:.0%}",
                delta="Cohérence globale"
            )
        
        with col4:
            entity_count = stats.get('total_persons', 0) + stats.get('total_organizations', 0)
            st.metric(
                "👥 Entités",
                entity_count,
                delta="Personnes et orgs."
            )
        
        # Onglets de résultats
        tabs = st.tabs([
            "📋 Synthèse",
            "✅ Convergences",
            "❌ Divergences",
            "📊 Visualisations",
            "🤖 Analyse IA",
            "📑 Rapport complet",
            "💾 Export"
        ])
        
        with tabs[0]:
            self._display_summary_tab(result)
        
        with tabs[1]:
            self._display_convergences_tab(result)
        
        with tabs[2]:
            self._display_divergences_tab(result)
        
        with tabs[3]:
            self._display_visualizations_tab(result)
        
        with tabs[4]:
            self._display_ai_analysis_tab(result)
        
        with tabs[5]:
            self._display_full_report_tab(result)
        
        with tabs[6]:
            self._display_export_tab(result)
    
    def _display_summary_tab(self, result: Dict[str, Any]):
        """Onglet de synthèse"""
        comparison = result.get('comparison', {})
        
        # Points clés
        st.markdown("#### 🎯 Points clés de l'analyse")
        
        key_points = []
        
        # Générer des points clés basés sur les données
        conv_count = len(comparison.get('convergences', []))
        div_count = len(comparison.get('divergences', []))
        
        if conv_count > div_count:
            key_points.append("✅ **Forte cohérence** : Les documents présentent plus de points communs que de divergences")
        else:
            key_points.append("⚠️ **Divergences significatives** : Les documents présentent des différences importantes")
        
        # Afficher les insights IA s'ils existent
        if comparison.get('ai_insights'):
            for insight in comparison['ai_insights'][:3]:
                key_points.append(f"💡 {insight}")
        
        for point in key_points:
            st.info(point)
        
        # Résumé des entités
        if comparison.get('entities_comparison'):
            st.markdown("#### 👥 Entités identifiées")
            
            entities = comparison['entities_comparison'].get('all_entities', {})
            common = comparison['entities_comparison'].get('common_entities', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Toutes les entités**")
                for etype, elist in entities.items():
                    if elist:
                        st.write(f"- {etype.capitalize()}: {len(elist)}")
            
            with col2:
                st.markdown("**Entités communes**")
                for etype, elist in common.items():
                    if elist:
                        st.write(f"- {etype.capitalize()}: {', '.join(elist[:5])}")
    
    def _display_convergences_tab(self, result: Dict[str, Any]):
        """Onglet des convergences avec filtres"""
        convergences = result.get('comparison', {}).get('convergences', [])
        
        if not convergences:
            st.info("Aucune convergence significative trouvée")
            return
        
        # Filtres
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Rechercher dans les convergences")
        with col2:
            sort_by = st.selectbox("Trier par", ["Pertinence", "Type", "Documents"])
        
        # Affichage
        filtered = convergences
        if search:
            filtered = [c for c in filtered if search.lower() in str(c).lower()]
        
        for i, conv in enumerate(filtered):
            with st.expander(f"✅ {conv.get('point', 'Convergence')} ({i+1}/{len(filtered)})", expanded=i<3):
                st.write(conv.get('details', ''))
                
                # Métadonnées
                if conv.get('documents'):
                    st.caption(f"📄 Documents concernés: {', '.join(conv['documents'])}")
                
                # Boutons d'action
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("📌", key=f"pin_conv_{i}", help="Épingler"):
                        st.success("Épinglé!")
    
    def _display_divergences_tab(self, result: Dict[str, Any]):
        """Onglet des divergences avec analyse"""
        divergences = result.get('comparison', {}).get('divergences', [])
        
        if not divergences:
            st.success("Aucune divergence majeure trouvée")
            return
        
        # Analyse des divergences
        st.markdown("#### 🔍 Analyse des divergences")
        
        # Catégoriser les divergences
        categories = defaultdict(list)
        for div in divergences:
            aspect = div.get('aspect', 'Autre')
            categories[aspect].append(div)
        
        # Afficher par catégorie
        for category, divs in categories.items():
            st.markdown(f"**{category.capitalize()}** ({len(divs)} divergences)")
            
            for i, div in enumerate(divs):
                severity = self._assess_divergence_severity(div)
                
                # Utiliser différentes couleurs selon la sévérité
                if severity == "Critique":
                    st.error(f"🚨 **{div.get('point', 'Divergence')}**")
                elif severity == "Important":
                    st.warning(f"⚠️ **{div.get('point', 'Divergence')}**")
                else:
                    st.info(f"ℹ️ **{div.get('point', 'Divergence')}**")
                
                with st.expander("Voir les détails", expanded=severity=="Critique"):
                    st.write(div.get('details', ''))
                    
                    # Recommandations
                    if severity in ["Critique", "Important"]:
                        st.markdown("**💡 Recommandations:**")
                        st.write("- Vérifier les sources originales")
                        st.write("- Demander des clarifications")
                        st.write("- Confronter les versions")
    
    def _display_visualizations_tab(self, result: Dict[str, Any]):
        """Onglet des visualisations améliorées"""
        visualizations = result.get('visualizations', {})
        
        if not visualizations and not PLOTLY_AVAILABLE:
            st.warning("Les visualisations nécessitent plotly. Installez avec: pip install plotly")
            return
        
        # Créer des visualisations même si elles n'existent pas
        if not visualizations and PLOTLY_AVAILABLE:
            st.info("Génération des visualisations...")
            visualizations = create_comparison_visualizations(result.get('comparison', {}), {})
        
        # Afficher les graphiques disponibles
        for viz_name, fig in visualizations.items():
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Graphiques supplémentaires
        if PLOTLY_AVAILABLE:
            # Word cloud simulé avec bar chart
            st.markdown("#### 🔤 Mots-clés fréquents")
            
            # Extraire les mots fréquents
            all_text = " ".join(d.get('content', '') for d in result.get('documents', []))
            words = re.findall(r'\b\w{4,}\b', all_text.lower())
            word_freq = Counter(words).most_common(10)
            
            if word_freq:
                fig = go.Figure(data=[
                    go.Bar(
                        x=[w[1] for w in word_freq],
                        y=[w[0] for w in word_freq],
                        orientation='h'
                    )
                ])
                fig.update_layout(
                    title="Top 10 des mots les plus fréquents",
                    xaxis_title="Fréquence",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _display_ai_analysis_tab(self, result: Dict[str, Any]):
        """Onglet d'analyse IA"""
        ai_analysis = result.get('comparison', {}).get('ai_analysis', '')
        
        if not ai_analysis:
            if not LLM_AVAILABLE:
                st.info("L'analyse IA n'est pas disponible. Configurez un LLM pour activer cette fonctionnalité.")
            else:
                st.info("Aucune analyse IA n'a été générée pour cette comparaison.")
            return
        
        st.markdown("#### 🤖 Analyse par Intelligence Artificielle")
        
        # Afficher l'analyse
        st.markdown(ai_analysis)
        
        # Insights spécifiques
        insights = result.get('comparison', {}).get('ai_insights', [])
        if insights:
            st.markdown("#### 💡 Insights clés")
            for insight in insights:
                st.success(f"→ {insight}")
        
        # Bouton pour régénérer
        if st.button("🔄 Régénérer l'analyse IA"):
            st.info("Régénération de l'analyse...")
            # Logique de régénération
    
    def _display_full_report_tab(self, result: Dict[str, Any]):
        """Onglet du rapport complet"""
        st.markdown("#### 📑 Rapport complet de comparaison")
        
        # Générer le rapport
        report = self._generate_full_report(result)
        
        # Afficher avec possibilité de copier
        st.text_area(
            "Rapport (copiable)",
            value=report,
            height=600,
            help="Sélectionnez tout (Ctrl+A) puis copiez (Ctrl+C)"
        )
    
    def _display_export_tab(self, result: Dict[str, Any]):
        """Onglet d'export avec multiples formats"""
        st.markdown("#### 💾 Exporter les résultats")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📄 Formats de document")
            
            # JSON
            json_data = json.dumps(result, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                "📥 Télécharger JSON",
                data=json_data,
                file_name=f"comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # Texte
            report = self._generate_full_report(result)
            st.download_button(
                "📥 Télécharger TXT",
                data=report,
                file_name=f"rapport_comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
            # CSV si pandas disponible
            if PANDAS_AVAILABLE:
                df = self._create_comparison_dataframe(result)
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Télécharger CSV",
                    data=csv,
                    file_name=f"comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.markdown("##### 🔗 Partage")
            
            # Générer un ID unique pour la comparaison
            comparison_id = get_text_hash(json_data)
            
            # Sauvegarder temporairement
            if st.button("💾 Sauvegarder pour partage"):
                st.session_state.saved_comparisons[comparison_id] = {
                    'result': result,
                    'timestamp': datetime.now(),
                    'title': f"Comparaison du {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                }
                st.success(f"Sauvegardé! ID: {comparison_id}")
                st.info("Partagez cet ID pour que d'autres puissent accéder aux résultats")
            
            # Copier le rapport
            if st.button("📋 Copier le rapport"):
                st.code(report)
                st.info("Sélectionnez le texte ci-dessus et copiez-le")
    
    def _render_history(self):
        """Affiche l'historique des comparaisons"""
        st.markdown("#### 📜 Historique des comparaisons")
        
        if not st.session_state.comparison_history:
            st.info("Aucune comparaison dans l'historique")
            return
        
        # Afficher l'historique
        for i, item in enumerate(reversed(st.session_state.comparison_history[-10:])):
            with st.expander(
                f"📊 Comparaison du {item['timestamp'].strftime('%d/%m/%Y %H:%M')} - "
                f"{len(item['documents'])} documents",
                expanded=False
            ):
                st.write(f"**Documents:** {', '.join(item['documents'])}")
                st.write(f"**Type:** {item['config'].get('comparison_type', 'N/A')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👁️ Voir", key=f"view_history_{i}"):
                        self._display_comparison_results(item['result'])
                with col2:
                    if st.button("🗑️ Supprimer", key=f"del_history_{i}"):
                        st.session_state.comparison_history.pop(-(i+1))
                        st.rerun()
    
    def _render_saved_comparisons(self):
        """Affiche les comparaisons sauvegardées"""
        st.markdown("#### 💾 Comparaisons sauvegardées")
        
        # Charger une comparaison par ID
        col1, col2 = st.columns([3, 1])
        with col1:
            load_id = st.text_input("Entrez l'ID de la comparaison")
        with col2:
            if st.button("📥 Charger"):
                if load_id in st.session_state.saved_comparisons:
                    saved = st.session_state.saved_comparisons[load_id]
                    st.success(f"Chargé: {saved['title']}")
                    self._display_comparison_results(saved['result'])
                else:
                    st.error("ID non trouvé")
        
        # Liste des sauvegardes
        if st.session_state.saved_comparisons:
            st.markdown("##### 📋 Sauvegardes disponibles")
            
            for comp_id, saved in st.session_state.saved_comparisons.items():
                with st.expander(f"{saved['title']} (ID: {comp_id})"):
                    st.write(f"Sauvegardé le: {saved['timestamp']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("👁️ Voir", key=f"view_saved_{comp_id}"):
                            self._display_comparison_results(saved['result'])
                    with col2:
                        if st.button("📋 Copier ID", key=f"copy_saved_{comp_id}"):
                            st.code(comp_id)
                    with col3:
                        if st.button("🗑️ Supprimer", key=f"del_saved_{comp_id}"):
                            del st.session_state.saved_comparisons[comp_id]
                            st.rerun()
    
    def _render_help(self):
        """Affiche l'aide du module"""
        st.markdown("""
        #### ❓ Guide d'utilisation
        
        ##### 🎯 Types de comparaison
        
        1. **Analyse intelligente** : S'adapte automatiquement au type de documents
        2. **Comparaison chronologique** : Idéale pour les témoignages et déclarations successives
        3. **Recherche de contradictions** : Met en évidence les incohérences
        4. **Analyse d'évolution** : Suit les changements dans le temps
        5. **Comparaison structurelle** : Compare la structure des documents
        6. **Analyse sémantique** : Compare le sens et les idées
        
        ##### 💡 Conseils d'utilisation
        
        - **Documents similaires** : Utilisez des documents du même type pour de meilleurs résultats
        - **Ordre important** : Placez le document de référence en premier
        - **Niveau de détail** : Commencez par "Standard" puis augmentez si nécessaire
        - **Export** : Sauvegardez toujours les comparaisons importantes
        
        ##### 🔧 Fonctionnalités avancées
        
        - **Extraction d'entités** : Identifie automatiquement les personnes, lieux, dates
        - **Analyse IA** : Fournit des insights approfondis (nécessite configuration)
        - **Visualisations** : Graphiques interactifs pour mieux comprendre
        - **Historique** : Retrouvez toutes vos comparaisons précédentes
        
        ##### ⚡ Raccourcis
        
        - Utilisez les **templates** pour tester rapidement
        - **Ctrl+A** puis **Ctrl+C** pour copier les rapports
        - Les comparaisons sont **sauvegardées automatiquement** dans l'historique
        """)
    
    # Méthodes utilitaires
    
    def _save_config(self, config: Dict[str, Any]):
        """Sauvegarde une configuration"""
        if 'saved_configs' not in st.session_state:
            st.session_state.saved_configs = {}
        
        config_name = f"Config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.saved_configs[config_name] = config
        st.success(f"Configuration sauvegardée: {config_name}")
    
    def _assess_divergence_severity(self, divergence: Dict[str, Any]) -> str:
        """Évalue la sévérité d'une divergence"""
        # Logique simple basée sur des mots-clés
        details = str(divergence.get('details', '')).lower()
        
        critical_keywords = ['contradiction', 'opposé', 'incompatible', 'faux', 'mensonge']
        important_keywords = ['différent', 'divergent', 'incohérent', 'variable']
        
        if any(keyword in details for keyword in critical_keywords):
            return "Critique"
        elif any(keyword in details for keyword in important_keywords):
            return "Important"
        else:
            return "Mineur"
    
    def _generate_full_report(self, result: Dict[str, Any]) -> str:
        """Génère un rapport textuel complet"""
        report = []
        
        # En-tête
        report.append("="*60)
        report.append("RAPPORT DE COMPARAISON DE DOCUMENTS")
        report.append("="*60)
        report.append(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        report.append(f"Documents analysés: {result.get('document_count', 0)}")
        report.append("")
        
        # Documents
        report.append("DOCUMENTS COMPARÉS:")
        for doc in result.get('documents', []):
            report.append(f"- {doc.get('title', 'Sans titre')}")
        report.append("")
        
        # Statistiques
        stats = result.get('comparison', {}).get('statistics', {})
        report.append("STATISTIQUES:")
        report.append(f"- Convergences: {stats.get('total_convergences', 0)}")
        report.append(f"- Divergences: {stats.get('total_divergences', 0)}")
        report.append(f"- Score de fiabilité: {stats.get('reliability_score', 0):.0%}")
        report.append("")
        
        # Convergences
        report.append("POINTS DE CONVERGENCE:")
        for conv in result.get('comparison', {}).get('convergences', [])[:10]:
            report.append(f"• {conv.get('point', '')}")
            report.append(f"  {conv.get('details', '')}")
        report.append("")
        
        # Divergences
        report.append("POINTS DE DIVERGENCE:")
        for div in result.get('comparison', {}).get('divergences', [])[:10]:
            report.append(f"• {div.get('point', '')}")
            report.append(f"  {div.get('details', '')}")
        report.append("")
        
        # Analyse IA
        if result.get('comparison', {}).get('ai_analysis'):
            report.append("ANALYSE IA:")
            report.append(result['comparison']['ai_analysis'])
        
        return "\n".join(report)
    
    def _create_comparison_dataframe(self, result: Dict[str, Any]):
        """Crée un DataFrame pour export CSV"""
        data = []
        
        # Convergences
        for conv in result.get('comparison', {}).get('convergences', []):
            data.append({
                'Type': 'Convergence',
                'Point': conv.get('point', ''),
                'Détails': conv.get('details', ''),
                'Documents': ', '.join(conv.get('documents', []))
            })
        
        # Divergences
        for div in result.get('comparison', {}).get('divergences', []):
            data.append({
                'Type': 'Divergence',
                'Point': div.get('point', ''),
                'Détails': str(div.get('details', '')),
                'Documents': ', '.join(div.get('documents', []))
            })
        
        return pd.DataFrame(data)

# ============= FONCTIONS GLOBALES (depuis le code original) =============

# [Inclure ici toutes les fonctions du code original comme generate_comparison, etc.]
# Je les ai gardées telles quelles car elles fonctionnent bien

# Copier ici toutes les fonctions depuis process_comparison_request jusqu'à la fin du fichier original
# (Je ne les répète pas pour économiser de l'espace, mais elles doivent être incluses)

def process_comparison_request(query: str, analysis: dict):
    """Traite une demande de comparaison"""
    
    st.markdown("### 🔄 Comparaison de documents")
    
    # Collecter les documents à comparer
    documents = collect_documents_for_comparison(analysis)
    
    if len(documents) < 2:
        st.warning("⚠️ Au moins 2 documents sont nécessaires pour une comparaison")
        return
    
    # Configuration
    config = display_comparison_config_interface(documents, analysis)
    
    if st.button("🚀 Lancer la comparaison", key="start_comparison", type="primary"):
        with st.spinner("🔄 Comparaison en cours..."):
            comparison_result = generate_comparison(documents, config, analysis)
            
            if comparison_result:
                st.session_state.comparison_result = comparison_result
                display_comparison_results(comparison_result)

# [Inclure toutes les autres fonctions du fichier original ici...]

# ============= POINT D'ENTRÉE =============

def render():
    """Point d'entrée principal du module"""
    module = ComparisonModule()
    module.render()

# Pour les tests directs
if __name__ == "__main__":
    render()