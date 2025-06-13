"""Module de génération de chronologies (timelines) juridiques"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict, OrderedDict
import logging

logger = logging.getLogger(__name__)

# Imports optionnels
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly non disponible - graphiques désactivés")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas non disponible - fonctionnalités limitées")

class TimelineModule:
    """Module de création de timeline juridique avec IA"""
    
    def __init__(self):
        self.name = "Timeline juridique"
        self.description = "Créez une chronologie visuelle et intelligente des événements"
        self.icon = "📅"
        self.available = True
        
        # Initialiser l'état de session
        if 'timeline_history' not in st.session_state:
            st.session_state.timeline_history = []
        if 'saved_timelines' not in st.session_state:
            st.session_state.saved_timelines = {}
            
    def render(self):
        """Interface principale du module"""
        st.markdown(f"### {self.icon} {self.name}")
        st.markdown(f"*{self.description}*")
        
        # Tabs principaux
        tab1, tab2, tab3, tab4 = st.tabs([
            "🆕 Nouvelle timeline",
            "📜 Historique",
            "💾 Timelines sauvegardées",
            "❓ Aide"
        ])
        
        with tab1:
            self._render_new_timeline()
            
        with tab2:
            self._render_history()
            
        with tab3:
            self._render_saved_timelines()
            
        with tab4:
            self._render_help()
    
    def _render_new_timeline(self):
        """Interface de création de nouvelle timeline"""
        
        # Sélection de la source
        source = st.radio(
            "📁 Source des données",
            ["Documents chargés", "Saisie manuelle", "Import fichier", "Templates"],
            horizontal=True
        )
        
        events = []
        
        if source == "Documents chargés":
            events = self._get_events_from_documents()
        elif source == "Saisie manuelle":
            events = self._get_manual_events()
        elif source == "Import fichier":
            events = self._get_events_from_file()
        else:
            events = self._get_template_events()
        
        if events:
            # Configuration
            config = self._get_timeline_config(events)
            
            # Actions
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if st.button("🚀 Générer la timeline", type="primary", use_container_width=True):
                    self._generate_timeline(events, config)
            
            with col2:
                if st.button("💾 Sauvegarder", use_container_width=True):
                    self._save_timeline_config(events, config)
                    
            with col3:
                if st.button("🔄 Réinitialiser", use_container_width=True):
                    st.rerun()
    
    def _get_events_from_documents(self) -> List[Dict[str, Any]]:
        """Extrait les événements depuis les documents"""
        events = []
        
        # Vérifier les documents disponibles
        documents = []
        
        # Documents Azure
        if 'azure_documents' in st.session_state:
            for doc_id, doc in st.session_state.azure_documents.items():
                documents.append({
                    'id': doc_id,
                    'title': getattr(doc, 'title', f'Document {doc_id}'),
                    'content': getattr(doc, 'content', ''),
                    'source': 'Azure'
                })
        
        # Documents sélectionnés
        if 'selected_documents' in st.session_state and st.session_state.selected_documents:
            st.info(f"📄 {len(st.session_state.selected_documents)} documents sélectionnés")
            # Filtrer pour ne garder que les sélectionnés
            selected_names = st.session_state.selected_documents
            documents = [d for d in documents if d['title'] in selected_names]
        
        if not documents:
            st.warning("Aucun document disponible. Chargez des documents ou utilisez une autre source.")
            return []
        
        # Sélection et extraction
        st.markdown("#### 📄 Documents à analyser")
        
        selected_docs = []
        for i, doc in enumerate(documents):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if st.checkbox(doc['title'], key=f"timeline_doc_{i}", value=True):
                    selected_docs.append(doc)
                    
            with col2:
                if st.button("👁️", key=f"preview_timeline_{i}", help="Aperçu"):
                    with st.expander("Aperçu", expanded=True):
                        st.text(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
        
        if selected_docs and st.button("🔍 Extraire les événements", key="extract_timeline_events"):
            with st.spinner("Extraction des événements en cours..."):
                for doc in selected_docs:
                    doc_events = self._extract_events_from_text(doc['content'], doc['title'])
                    events.extend(doc_events)
                
                if events:
                    st.success(f"✅ {len(events)} événements extraits")
                    
                    # Aperçu des événements
                    with st.expander("Aperçu des événements extraits", expanded=True):
                        for i, event in enumerate(events[:5]):
                            st.write(f"**{event['date']}** - {event['description'][:100]}...")
                        
                        if len(events) > 5:
                            st.info(f"... et {len(events) - 5} autres événements")
                else:
                    st.warning("Aucun événement trouvé dans les documents")
        
        return events
    
    def _extract_events_from_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Extrait les événements d'un texte"""
        events = []
        
        # Patterns de dates
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
            r'((?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        # Chercher les dates et leur contexte
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                date_str = match.group(1)
                
                # Extraire le contexte (phrase contenant la date)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                # Nettoyer le contexte
                context = ' '.join(context.split())
                
                # Parser la date
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    # Déterminer l'importance
                    importance = self._calculate_importance(context)
                    
                    # Extraire les acteurs
                    actors = self._extract_actors(context)
                    
                    events.append({
                        'date': parsed_date,
                        'description': context,
                        'source': source,
                        'importance': importance,
                        'actors': actors,
                        'category': self._determine_category(context)
                    })
        
        # Dédupliquer et trier
        unique_events = []
        seen = set()
        
        for event in sorted(events, key=lambda x: x['date']):
            key = (event['date'], event['description'][:50])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date depuis une chaîne"""
        # Remplacer les mois français
        mois_fr = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        date_clean = date_str.lower()
        for mois, num in mois_fr.items():
            date_clean = date_clean.replace(mois, num)
        
        # Essayer différents formats
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
            '%d %m %Y', '%Y-%m-%d', '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(re.sub(r'[^\d/-]', ' ', date_clean).strip(), fmt)
            except:
                continue
        
        return None
    
    def _calculate_importance(self, text: str) -> int:
        """Calcule l'importance d'un événement (1-10)"""
        importance = 5
        
        # Mots-clés augmentant l'importance
        high_words = ['important', 'crucial', 'décisif', 'majeur', 'signature', 'jugement', 'condamnation']
        low_words = ['mineur', 'secondaire', 'simple', 'courrier']
        
        text_lower = text.lower()
        
        for word in high_words:
            if word in text_lower:
                importance += 1
        
        for word in low_words:
            if word in text_lower:
                importance -= 1
        
        return max(1, min(10, importance))
    
    def _extract_actors(self, text: str) -> List[str]:
        """Extrait les acteurs d'un texte"""
        actors = []
        
        # Patterns pour les personnes
        patterns = [
            r'(?:M\.|Mme|Dr|Me|Pr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+\s+[A-Z]+)(?:\s|,|\.|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            actors.extend(matches)
        
        # Dédupliquer
        return list(set(actors))[:5]
    
    def _determine_category(self, text: str) -> str:
        """Détermine la catégorie d'un événement"""
        text_lower = text.lower()
        
        categories = {
            'procédure': ['plainte', 'audition', 'perquisition', 'jugement'],
            'financier': ['virement', 'paiement', 'euros', '€'],
            'contractuel': ['contrat', 'accord', 'signature'],
            'communication': ['lettre', 'courrier', 'email', 'réunion']
        }
        
        for cat, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        
        return 'autre'
    
    def _get_manual_events(self) -> List[Dict[str, Any]]:
        """Interface de saisie manuelle d'événements"""
        st.markdown("#### ✍️ Saisie manuelle des événements")
        
        events = []
        
        # Nombre d'événements
        num_events = st.number_input(
            "Nombre d'événements",
            min_value=1,
            max_value=50,
            value=5,
            key="num_timeline_events"
        )
        
        # Saisie pour chaque événement
        for i in range(num_events):
            with st.expander(f"📅 Événement {i+1}", expanded=i<3):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    date = st.date_input(
                        "Date",
                        value=datetime.now() - timedelta(days=i*30),
                        key=f"event_date_{i}"
                    )
                    
                    importance = st.slider(
                        "Importance",
                        1, 10, 5,
                        key=f"event_importance_{i}"
                    )
                    
                    category = st.selectbox(
                        "Catégorie",
                        ["procédure", "financier", "contractuel", "communication", "autre"],
                        key=f"event_category_{i}"
                    )
                
                with col2:
                    description = st.text_area(
                        "Description",
                        placeholder="Décrivez l'événement...",
                        height=100,
                        key=f"event_description_{i}"
                    )
                    
                    actors = st.text_input(
                        "Acteurs (séparés par des virgules)",
                        placeholder="Jean Dupont, Société XYZ",
                        key=f"event_actors_{i}"
                    )
                
                if description:
                    events.append({
                        'date': datetime.combine(date, datetime.min.time()),
                        'description': description,
                        'importance': importance,
                        'category': category,
                        'actors': [a.strip() for a in actors.split(',') if a.strip()],
                        'source': 'Saisie manuelle'
                    })
        
        return events
    
    def _get_events_from_file(self) -> List[Dict[str, Any]]:
        """Import d'événements depuis un fichier"""
        st.markdown("#### 📁 Import depuis un fichier")
        
        uploaded_file = st.file_uploader(
            "Choisissez un fichier",
            type=['csv', 'xlsx', 'json'],
            help="Format: Date, Description, Importance, Catégorie, Acteurs"
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    # Import CSV
                    if PANDAS_AVAILABLE:
                        df = pd.read_csv(uploaded_file)
                        return self._convert_dataframe_to_events(df)
                    else:
                        st.error("pandas requis pour importer des CSV")
                        
                elif uploaded_file.name.endswith('.xlsx'):
                    # Import Excel
                    if PANDAS_AVAILABLE:
                        df = pd.read_excel(uploaded_file)
                        return self._convert_dataframe_to_events(df)
                    else:
                        st.error("pandas requis pour importer des fichiers Excel")
                        
                elif uploaded_file.name.endswith('.json'):
                    # Import JSON
                    import json
                    data = json.load(uploaded_file)
                    return self._convert_json_to_events(data)
                    
            except Exception as e:
                st.error(f"Erreur lors de l'import : {e}")
        
        return []
    
    def _get_template_events(self) -> List[Dict[str, Any]]:
        """Événements depuis des templates"""
        st.markdown("#### 📋 Templates d'événements")
        
        template = st.selectbox(
            "Choisir un template",
            [
                "Procédure pénale type",
                "Affaire commerciale",
                "Divorce contentieux",
                "Accident de la route",
                "Litige immobilier"
            ]
        )
        
        templates = {
            "Procédure pénale type": [
                {
                    'date': datetime.now() - timedelta(days=180),
                    'description': "Dépôt de plainte initiale au commissariat",
                    'importance': 8,
                    'category': 'procédure',
                    'actors': ['Plaignant', 'Police']
                },
                {
                    'date': datetime.now() - timedelta(days=150),
                    'description': "Première audition du mis en cause",
                    'importance': 7,
                    'category': 'procédure',
                    'actors': ['Mis en cause', 'Enquêteurs']
                },
                {
                    'date': datetime.now() - timedelta(days=120),
                    'description': "Perquisition au domicile",
                    'importance': 9,
                    'category': 'procédure',
                    'actors': ['Police', 'Mis en cause']
                },
                {
                    'date': datetime.now() - timedelta(days=90),
                    'description': "Mise en examen",
                    'importance': 10,
                    'category': 'procédure',
                    'actors': ['Juge d\'instruction', 'Mis en examen']
                },
                {
                    'date': datetime.now() - timedelta(days=30),
                    'description': "Clôture de l'instruction",
                    'importance': 8,
                    'category': 'procédure',
                    'actors': ['Juge d\'instruction']
                }
            ],
            "Affaire commerciale": [
                {
                    'date': datetime.now() - timedelta(days=365),
                    'description': "Signature du contrat commercial",
                    'importance': 9,
                    'category': 'contractuel',
                    'actors': ['Société A', 'Société B']
                },
                {
                    'date': datetime.now() - timedelta(days=200),
                    'description': "Premiers retards de paiement constatés",
                    'importance': 6,
                    'category': 'financier',
                    'actors': ['Société B']
                },
                {
                    'date': datetime.now() - timedelta(days=150),
                    'description': "Mise en demeure envoyée",
                    'importance': 7,
                    'category': 'communication',
                    'actors': ['Société A', 'Avocat']
                },
                {
                    'date': datetime.now() - timedelta(days=90),
                    'description': "Assignation devant le Tribunal de Commerce",
                    'importance': 9,
                    'category': 'procédure',
                    'actors': ['Société A', 'Tribunal']
                }
            ]
        }
        
        # Récupérer le template sélectionné
        selected_template = templates.get(template, [])
        
        # Permettre l'édition
        st.info(f"📋 Template : {template} - {len(selected_template)} événements")
        
        events = []
        for i, event in enumerate(selected_template):
            with st.expander(f"Événement {i+1}: {event['description'][:50]}...", expanded=i==0):
                # Permettre la modification
                col1, col2 = st.columns(2)
                
                with col1:
                    event['date'] = st.date_input(
                        "Date",
                        value=event['date'],
                        key=f"template_date_{i}"
                    )
                    event['importance'] = st.slider(
                        "Importance",
                        1, 10, event['importance'],
                        key=f"template_imp_{i}"
                    )
                
                with col2:
                    event['description'] = st.text_area(
                        "Description",
                        value=event['description'],
                        key=f"template_desc_{i}"
                    )
                
                # Ajouter à la liste
                events.append({
                    'date': datetime.combine(event['date'], datetime.min.time()) if isinstance(event['date'], type(datetime.now().date())) else event['date'],
                    'description': event['description'],
                    'importance': event['importance'],
                    'category': event.get('category', 'autre'),
                    'actors': event.get('actors', []),
                    'source': f'Template: {template}'
                })
        
        return events
    
    def _get_timeline_config(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Configuration de la timeline"""
        st.markdown("#### ⚙️ Configuration de la timeline")
        
        config = {}
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            config['view_type'] = st.selectbox(
                "📊 Type de vue",
                ["Linéaire", "Par catégorie", "Par acteur", "Densité temporelle"],
                help="Comment organiser visuellement les événements"
            )
            
            config['date_format'] = st.selectbox(
                "📅 Format de date",
                ["JJ/MM/AAAA", "MM/AAAA", "Trimestre", "Relatif"],
                help="Comment afficher les dates"
            )
        
        with col2:
            config['show_importance'] = st.checkbox(
                "⭐ Afficher l'importance",
                value=True,
                help="Taille variable selon l'importance"
            )
            
            config['show_connections'] = st.checkbox(
                "🔗 Montrer les liens",
                value=False,
                help="Relier les événements liés"
            )
            
            config['show_actors'] = st.checkbox(
                "👥 Afficher les acteurs",
                value=True
            )
        
        with col3:
            config['color_scheme'] = st.selectbox(
                "🎨 Couleurs",
                ["Par catégorie", "Par importance", "Par acteur", "Uniforme"],
                help="Schéma de couleurs"
            )
            
            config['interactive'] = st.checkbox(
                "🖱️ Interactif",
                value=True,
                help="Timeline cliquable avec détails"
            )
        
        # Filtres
        with st.expander("🔍 Filtres", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Filtre par date
                dates = [e['date'] for e in events if 'date' in e]
                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    
                    config['date_range'] = st.date_input(
                        "Période",
                        value=(min_date, max_date),
                        key="timeline_date_range"
                    )
                
                # Filtre par importance
                config['min_importance'] = st.slider(
                    "Importance minimale",
                    1, 10, 1,
                    key="timeline_min_imp"
                )
            
            with col2:
                # Filtre par catégorie
                categories = list(set(e.get('category', 'autre') for e in events))
                config['categories'] = st.multiselect(
                    "Catégories",
                    categories,
                    default=categories,
                    key="timeline_categories"
                )
                
                # Filtre par acteur
                all_actors = []
                for e in events:
                    all_actors.extend(e.get('actors', []))
                unique_actors = list(set(all_actors))
                
                if unique_actors:
                    config['actors'] = st.multiselect(
                        "Acteurs",
                        unique_actors,
                        default=unique_actors[:5] if len(unique_actors) > 5 else unique_actors,
                        key="timeline_actors"
                    )
        
        # Options d'export
        with st.expander("💾 Options d'export", expanded=False):
            config['export_format'] = st.multiselect(
                "Formats d'export",
                ["Image PNG", "PDF", "PowerPoint", "Excel", "JSON"],
                default=["PDF", "Excel"]
            )
            
            config['include_analysis'] = st.checkbox(
                "Inclure l'analyse",
                value=True,
                help="Ajouter des statistiques et insights"
            )
        
        return config
    
    def _generate_timeline(self, events: List[Dict[str, Any]], config: Dict[str, Any]):
        """Génère et affiche la timeline"""
        
        # Filtrer les événements
        filtered_events = self._filter_events(events, config)
        
        if not filtered_events:
            st.warning("Aucun événement ne correspond aux critères")
            return
        
        # Container de progression
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Génération de la timeline...")
            progress = st.progress(0)
            status = st.empty()
            
            # Étapes
            steps = [
                ("Tri des événements", 0.2),
                ("Analyse des patterns", 0.4),
                ("Création de la visualisation", 0.6),
                ("Génération des insights", 0.8),
                ("Finalisation", 1.0)
            ]
            
            timeline_result = {'events': filtered_events, 'config': config}
            
            for step_name, prog in steps:
                status.text(f"⏳ {step_name}...")
                progress.progress(prog)
                
                if prog == 0.4:
                    # Analyse
                    timeline_result['analysis'] = self._analyze_timeline(filtered_events)
                elif prog == 0.6:
                    # Visualisation
                    timeline_result['visualization'] = self._create_visualization(filtered_events, config)
                elif prog == 0.8:
                    # Insights
                    timeline_result['insights'] = self._generate_insights(filtered_events, timeline_result['analysis'])
        
        # Effacer la progression
        progress_container.empty()
        
        # Sauvegarder dans l'historique
        timeline_result['timestamp'] = datetime.now()
        timeline_result['event_count'] = len(filtered_events)
        st.session_state.timeline_history.append(timeline_result)
        
        # Afficher les résultats
        self._display_timeline_results(timeline_result)
    
    def _filter_events(self, events: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtre les événements selon la configuration"""
        filtered = events
        
        # Filtre par date
        if 'date_range' in config and len(config['date_range']) == 2:
            start, end = config['date_range']
            start_dt = datetime.combine(start, datetime.min.time())
            end_dt = datetime.combine(end, datetime.max.time())
            
            filtered = [
                e for e in filtered 
                if 'date' in e and start_dt <= e['date'] <= end_dt
            ]
        
        # Filtre par importance
        if 'min_importance' in config:
            filtered = [
                e for e in filtered 
                if e.get('importance', 5) >= config['min_importance']
            ]
        
        # Filtre par catégorie
        if 'categories' in config:
            filtered = [
                e for e in filtered 
                if e.get('category', 'autre') in config['categories']
            ]
        
        # Filtre par acteur
        if 'actors' in config:
            filtered = [
                e for e in filtered 
                if any(actor in config['actors'] for actor in e.get('actors', []))
            ]
        
        return filtered
    
    def _analyze_timeline(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse la timeline pour extraire des patterns"""
        analysis = {
            'total_events': len(events),
            'date_range': None,
            'density': {},
            'key_periods': [],
            'actor_involvement': {},
            'category_distribution': {}
        }
        
        if not events:
            return analysis
        
        # Plage de dates
        dates = [e['date'] for e in events if 'date' in e]
        if dates:
            analysis['date_range'] = {
                'start': min(dates),
                'end': max(dates),
                'duration_days': (max(dates) - min(dates)).days
            }
        
        # Densité temporelle
        date_counts = defaultdict(int)
        for event in events:
            if 'date' in event:
                month_key = event['date'].strftime('%Y-%m')
                date_counts[month_key] += 1
        
        analysis['density'] = dict(date_counts)
        
        # Périodes clés (mois avec le plus d'événements)
        if date_counts:
            sorted_periods = sorted(date_counts.items(), key=lambda x: x[1], reverse=True)
            analysis['key_periods'] = sorted_periods[:3]
        
        # Implication des acteurs
        actor_counts = defaultdict(int)
        for event in events:
            for actor in event.get('actors', []):
                actor_counts[actor] += 1
        
        analysis['actor_involvement'] = dict(sorted(
            actor_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        # Distribution par catégorie
        cat_counts = defaultdict(int)
        for event in events:
            cat_counts[event.get('category', 'autre')] += 1
        
        analysis['category_distribution'] = dict(cat_counts)
        
        return analysis
    
    def _create_visualization(self, events: List[Dict[str, Any]], config: Dict[str, Any]) -> Any:
        """Crée la visualisation de la timeline"""
        if not PLOTLY_AVAILABLE:
            return None
        
        # Trier les événements par date
        sorted_events = sorted(events, key=lambda x: x.get('date', datetime.min))
        
        # Créer le graphique selon le type de vue
        if config.get('view_type') == 'Par catégorie':
            return self._create_categorized_timeline(sorted_events, config)
        elif config.get('view_type') == 'Par acteur':
            return self._create_actor_timeline(sorted_events, config)
        elif config.get('view_type') == 'Densité temporelle':
            return self._create_density_timeline(sorted_events, config)
        else:
            return self._create_linear_timeline(sorted_events, config)
    
    def _create_linear_timeline(self, events: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
        """Crée une timeline linéaire"""
        fig = go.Figure()
        
        # Couleurs par catégorie
        colors = {
            'procédure': '#1f77b4',
            'financier': '#2ca02c',
            'contractuel': '#ff7f0e',
            'communication': '#d62728',
            'autre': '#9467bd'
        }
        
        # Préparer les données
        x_dates = []
        y_positions = []
        texts = []
        marker_colors = []
        marker_sizes = []
        
        for i, event in enumerate(events):
            x_dates.append(event['date'])
            y_positions.append(i % 3)  # Alterner sur 3 niveaux
            
            # Texte
            text = f"<b>{event['date'].strftime('%d/%m/%Y')}</b><br>"
            text += f"{event['description'][:100]}...<br>"
            if event.get('actors'):
                text += f"<i>Acteurs: {', '.join(event['actors'][:3])}</i>"
            texts.append(text)
            
            # Couleur
            if config.get('color_scheme') == 'Par catégorie':
                marker_colors.append(colors.get(event.get('category', 'autre'), '#9467bd'))
            elif config.get('color_scheme') == 'Par importance':
                importance = event.get('importance', 5)
                if importance >= 8:
                    marker_colors.append('#ff0000')
                elif importance >= 5:
                    marker_colors.append('#ffa500')
                else:
                    marker_colors.append('#00ff00')
            else:
                marker_colors.append('#1f77b4')
            
            # Taille
            if config.get('show_importance'):
                marker_sizes.append(10 + event.get('importance', 5) * 3)
            else:
                marker_sizes.append(20)
        
        # Ajouter la trace
        fig.add_trace(go.Scatter(
            x=x_dates,
            y=y_positions,
            mode='markers+text' if len(events) < 20 else 'markers',
            text=texts,
            textposition='top center',
            hovertext=texts,
            hoverinfo='text',
            marker=dict(
                size=marker_sizes,
                color=marker_colors,
                line=dict(width=2, color='white')
            ),
            showlegend=False
        ))
        
        # Mise en forme
        fig.update_layout(
            title="Timeline des événements",
            xaxis=dict(
                title="Date",
                type='date',
                rangeslider=dict(visible=True) if config.get('interactive') else None
            ),
            yaxis=dict(
                title="",
                showticklabels=False,
                range=[-0.5, 3.5]
            ),
            height=600,
            hovermode='closest',
            plot_bgcolor='white'
        )
        
        # Ajouter des lignes verticales pour les événements importants
        important_events = [e for e in events if e.get('importance', 0) >= 8]
        for event in important_events:
            fig.add_vline(
                x=event['date'],
                line_dash="dash",
                line_color="red",
                opacity=0.3
            )
        
        return fig
    
    def _create_categorized_timeline(self, events: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
        """Crée une timeline organisée par catégorie"""
        # Grouper par catégorie
        categories = {}
        for event in events:
            cat = event.get('category', 'autre')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(event)
        
        # Créer des subplots
        n_cats = len(categories)
        fig = make_subplots(
            rows=n_cats,
            cols=1,
            shared_xaxes=True,
            subplot_titles=list(categories.keys()),
            vertical_spacing=0.05
        )
        
        # Ajouter les traces par catégorie
        colors = px.colors.qualitative.Set3
        
        for i, (cat, cat_events) in enumerate(categories.items()):
            x_dates = [e['date'] for e in cat_events]
            texts = [e['description'][:50] + '...' for e in cat_events]
            sizes = [10 + e.get('importance', 5) * 2 for e in cat_events]
            
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=[1] * len(cat_events),
                    mode='markers+text',
                    text=texts,
                    textposition='top center',
                    marker=dict(
                        size=sizes,
                        color=colors[i % len(colors)]
                    ),
                    showlegend=False,
                    hovertext=[e['description'] for e in cat_events],
                    hoverinfo='text'
                ),
                row=i+1,
                col=1
            )
            
            # Masquer l'axe Y
            fig.update_yaxes(
                showticklabels=False, 
                showgrid=False, 
                row=i+1, 
                col=1
            )
        
        # Mise en forme
        fig.update_layout(
            title="Timeline par catégorie",
            height=200 * n_cats,
            showlegend=False
        )
        
        fig.update_xaxes(title="Date", row=n_cats, col=1)
        
        return fig
    
    def _generate_insights(self, events: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[str]:
        """Génère des insights sur la timeline"""
        insights = []
        
        # Insight sur la durée
        if analysis['date_range']:
            duration = analysis['date_range']['duration_days']
            insights.append(f"📅 La période analysée couvre {duration} jours")
        
        # Insight sur la densité
        if analysis['density']:
            max_month = max(analysis['density'].items(), key=lambda x: x[1])
            insights.append(f"📊 Le mois le plus actif est {max_month[0]} avec {max_month[1]} événements")
        
        # Insight sur les acteurs
        if analysis['actor_involvement']:
            top_actor = list(analysis['actor_involvement'].items())[0]
            insights.append(f"👤 {top_actor[0]} est impliqué dans {top_actor[1]} événements")
        
        # Insight sur l'accélération
        if len(events) >= 10:
            # Comparer première et dernière moitié
            mid = len(events) // 2
            first_half = events[:mid]
            second_half = events[mid:]
            
            if first_half and second_half:
                first_duration = (first_half[-1]['date'] - first_half[0]['date']).days
                second_duration = (second_half[-1]['date'] - second_half[0]['date']).days
                
                if first_duration > 0 and second_duration > 0:
                    if second_duration < first_duration / 2:
                        insights.append("⚡ Forte accélération des événements dans la période récente")
        
        return insights
    
    def _display_timeline_results(self, result: Dict[str, Any]):
        """Affiche les résultats de la timeline"""
        st.success(f"✅ Timeline générée avec {result['event_count']} événements")
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Événements", result['event_count'])
        
        with col2:
            if result.get('analysis', {}).get('date_range'):
                duration = result['analysis']['date_range']['duration_days']
                st.metric("⏱️ Période", f"{duration} jours")
        
        with col3:
            if result.get('analysis', {}).get('actor_involvement'):
                st.metric("👥 Acteurs", len(result['analysis']['actor_involvement']))
        
        with col4:
            if result.get('analysis', {}).get('category_distribution'):
                st.metric("📁 Catégories", len(result['analysis']['category_distribution']))
        
        # Visualisation
        if result.get('visualization'):
            st.plotly_chart(result['visualization'], use_container_width=True)
        else:
            st.info("Installez plotly pour visualiser la timeline : `pip install plotly`")
        
        # Insights
        if result.get('insights'):
            st.markdown("### 💡 Insights")
            for insight in result['insights']:
                st.info(insight)
        
        # Tabs de détails
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Événements",
            "📊 Analyse",
            "💾 Export",
            "🔧 Actions"
        ])
        
        with tab1:
            self._display_events_tab(result)
        
        with tab2:
            self._display_analysis_tab(result)
        
        with tab3:
            self._display_export_tab(result)
        
        with tab4:
            self._display_actions_tab(result)
    
    def _display_events_tab(self, result: Dict[str, Any]):
        """Affiche la liste des événements"""
        events = result.get('events', [])
        
        # Options de tri et filtre
        col1, col2 = st.columns(2)
        
        with col1:
            sort_by = st.selectbox(
                "Trier par",
                ["Date", "Importance", "Catégorie"],
                key="sort_events"
            )
        
        with col2:
            search = st.text_input(
                "Rechercher",
                placeholder="Filtrer les événements...",
                key="search_events"
            )
        
        # Trier
        if sort_by == "Date":
            sorted_events = sorted(events, key=lambda x: x.get('date', datetime.min))
        elif sort_by == "Importance":
            sorted_events = sorted(events, key=lambda x: x.get('importance', 0), reverse=True)
        else:
            sorted_events = sorted(events, key=lambda x: x.get('category', ''))
        
        # Filtrer
        if search:
            sorted_events = [
                e for e in sorted_events 
                if search.lower() in e.get('description', '').lower()
            ]
        
        # Afficher
        for i, event in enumerate(sorted_events):
            with st.expander(
                f"{event['date'].strftime('%d/%m/%Y')} - {event['description'][:50]}...",
                expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Description:** {event['description']}")
                    if event.get('actors'):
                        st.write(f"**Acteurs:** {', '.join(event['actors'])}")
                    st.write(f"**Source:** {event.get('source', 'N/A')}")
                
                with col2:
                    importance = event.get('importance', 5)
                    color = '🔴' if importance >= 8 else '🟡' if importance >= 5 else '🟢'
                    st.metric("Importance", f"{color} {importance}/10")
                    st.write(f"**Catégorie:** {event.get('category', 'autre')}")
    
    def _display_analysis_tab(self, result: Dict[str, Any]):
        """Affiche l'analyse de la timeline"""
        analysis = result.get('analysis', {})
        
        # Période
        if analysis.get('date_range'):
            st.markdown("#### 📅 Période analysée")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Début:** {analysis['date_range']['start'].strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**Fin:** {analysis['date_range']['end'].strftime('%d/%m/%Y')}")
            with col3:
                st.write(f"**Durée:** {analysis['date_range']['duration_days']} jours")
        
        # Distribution temporelle
        if analysis.get('density') and PLOTLY_AVAILABLE:
            st.markdown("#### 📊 Distribution temporelle")
            
            months = list(analysis['density'].keys())
            counts = list(analysis['density'].values())
            
            fig = go.Figure(data=[
                go.Bar(x=months, y=counts)
            ])
            fig.update_layout(
                title="Nombre d'événements par mois",
                xaxis_title="Mois",
                yaxis_title="Nombre d'événements"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Acteurs clés
        if analysis.get('actor_involvement'):
            st.markdown("#### 👥 Acteurs principaux")
            
            for actor, count in list(analysis['actor_involvement'].items())[:5]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{actor}**")
                with col2:
                    st.write(f"{count} événements")
        
        # Distribution par catégorie
        if analysis.get('category_distribution') and PLOTLY_AVAILABLE:
            st.markdown("#### 📁 Répartition par catégorie")
            
            fig = px.pie(
                values=list(analysis['category_distribution'].values()),
                names=list(analysis['category_distribution'].keys()),
                title="Distribution des événements"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _display_export_tab(self, result: Dict[str, Any]):
        """Options d'export de la timeline"""
        st.markdown("#### 💾 Exporter la timeline")
        
        # Format JSON
        import json
        json_str = json.dumps({
            'events': [
                {
                    'date': e['date'].isoformat() if isinstance(e['date'], datetime) else str(e['date']),
                    'description': e['description'],
                    'importance': e.get('importance', 5),
                    'category': e.get('category', 'autre'),
                    'actors': e.get('actors', [])
                }
                for e in result.get('events', [])
            ],
            'analysis': {
                k: v for k, v in result.get('analysis', {}).items()
                if k != 'date_range'
            }
        }, ensure_ascii=False, indent=2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📥 Télécharger JSON",
                data=json_str,
                file_name=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # Format texte
            text_export = self._export_to_text(result)
            st.download_button(
                "📥 Télécharger TXT",
                data=text_export,
                file_name=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            # Format CSV si pandas disponible
            if PANDAS_AVAILABLE:
                df = pd.DataFrame([
                    {
                        'Date': e['date'].strftime('%d/%m/%Y'),
                        'Description': e['description'],
                        'Importance': e.get('importance', 5),
                        'Catégorie': e.get('category', 'autre'),
                        'Acteurs': ', '.join(e.get('actors', [])),
                        'Source': e.get('source', '')
                    }
                    for e in result.get('events', [])
                ])
                
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Télécharger CSV",
                    data=csv,
                    file_name=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    def _export_to_text(self, result: Dict[str, Any]) -> str:
        """Exporte la timeline en format texte"""
        lines = []
        lines.append("TIMELINE JURIDIQUE")
        lines.append("=" * 50)
        lines.append(f"Générée le : {result['timestamp'].strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"Nombre d'événements : {result['event_count']}")
        lines.append("")
        
        # Analyse
        if result.get('analysis', {}).get('date_range'):
            lines.append(f"Période : {result['analysis']['date_range']['start'].strftime('%d/%m/%Y')} - {result['analysis']['date_range']['end'].strftime('%d/%m/%Y')}")
            lines.append(f"Durée : {result['analysis']['date_range']['duration_days']} jours")
            lines.append("")
        
        # Événements
        lines.append("CHRONOLOGIE DES ÉVÉNEMENTS")
        lines.append("-" * 50)
        
        for event in result.get('events', []):
            lines.append(f"\n{event['date'].strftime('%d/%m/%Y')}")
            lines.append(f"Description : {event['description']}")
            if event.get('actors'):
                lines.append(f"Acteurs : {', '.join(event['actors'])}")
            lines.append(f"Importance : {event.get('importance', 5)}/10")
            lines.append(f"Catégorie : {event.get('category', 'autre')}")
        
        return "\n".join(lines)
    
    def _display_actions_tab(self, result: Dict[str, Any]):
        """Actions disponibles sur la timeline"""
        st.markdown("#### 🔧 Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Régénérer avec d'autres paramètres", use_container_width=True):
                st.session_state.regenerate_timeline = True
                st.rerun()
            
            if st.button("➕ Ajouter des événements", use_container_width=True):
                st.session_state.add_events_to_timeline = True
                st.rerun()
        
        with col2:
            if st.button("🎨 Changer le style", use_container_width=True):
                st.session_state.change_timeline_style = True
                st.rerun()
            
            if st.button("📧 Partager", use_container_width=True):
                st.info("Fonctionnalité de partage à venir")
    
    def _render_history(self):
        """Affiche l'historique des timelines"""
        st.markdown("#### 📜 Historique des timelines")
        
        if not st.session_state.timeline_history:
            st.info("Aucune timeline dans l'historique")
            return
        
        # Afficher les timelines récentes
        for i, timeline in enumerate(reversed(st.session_state.timeline_history[-10:])):
            with st.expander(
                f"Timeline du {timeline['timestamp'].strftime('%d/%m/%Y %H:%M')} - {timeline['event_count']} événements",
                expanded=False
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️ Voir", key=f"view_timeline_{i}"):
                        self._display_timeline_results(timeline)
                
                with col2:
                    if st.button("💾 Sauvegarder", key=f"save_timeline_{i}"):
                        self._save_timeline(timeline)
                
                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_timeline_{i}"):
                        st.session_state.timeline_history.remove(timeline)
                        st.rerun()
    
    def _render_saved_timelines(self):
        """Affiche les timelines sauvegardées"""
        st.markdown("#### 💾 Timelines sauvegardées")
        
        if not st.session_state.saved_timelines:
            st.info("Aucune timeline sauvegardée")
            return
        
        for tid, timeline_data in st.session_state.saved_timelines.items():
            with st.expander(f"{timeline_data['name']} (ID: {tid})"):
                st.write(f"Créée le : {timeline_data['saved_at'].strftime('%d/%m/%Y %H:%M')}")
                st.write(f"Événements : {timeline_data['timeline']['event_count']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📂 Charger", key=f"load_{tid}"):
                        self._display_timeline_results(timeline_data['timeline'])
                
                with col2:
                    if st.button("📤 Exporter", key=f"export_{tid}"):
                        st.session_state.export_timeline = timeline_data['timeline']
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Supprimer", key=f"delete_{tid}"):
                        del st.session_state.saved_timelines[tid]
                        st.rerun()
    
    def _save_timeline(self, timeline: Dict[str, Any]):
        """Sauvegarde une timeline"""
        import hashlib
        
        # Générer un ID unique
        timeline_id = hashlib.md5(
            f"{timeline['timestamp']}{timeline['event_count']}".encode()
        ).hexdigest()[:8]
        
        # Nom par défaut
        name = f"Timeline {timeline['timestamp'].strftime('%d/%m/%Y')}"
        
        # Sauvegarder
        st.session_state.saved_timelines[timeline_id] = {
            'name': name,
            'timeline': timeline,
            'saved_at': datetime.now()
        }
        
        st.success(f"Timeline sauvegardée avec l'ID : {timeline_id}")
    
    def _render_help(self):
        """Affiche l'aide du module"""
        st.markdown("""
        #### ❓ Guide d'utilisation du module Timeline
        
        ##### 🎯 Objectif
        Ce module permet de créer des chronologies visuelles et interactives à partir de vos documents juridiques.
        
        ##### 📋 Sources de données
        1. **Documents chargés** : Extraction automatique des dates et événements
        2. **Saisie manuelle** : Créez vos événements un par un
        3. **Import fichier** : CSV, Excel ou JSON
        4. **Templates** : Modèles prédéfinis pour différents types d'affaires
        
        ##### 🔧 Fonctionnalités principales
        - **Extraction intelligente** : Détection automatique des dates et contextes
        - **Filtrage avancé** : Par date, importance, catégorie, acteurs
        - **Visualisations multiples** : Linéaire, par catégorie, densité temporelle
        - **Analyse automatique** : Patterns, périodes clés, acteurs principaux
        - **Export multi-format** : JSON, CSV, TXT, PDF
        
        ##### 💡 Conseils d'utilisation
        - Commencez par charger tous vos documents pertinents
        - Utilisez l'extraction automatique puis affinez manuellement
        - Définissez l'importance (1-10) pour hiérarchiser les événements
        - Exploitez les filtres pour vous concentrer sur des périodes spécifiques
        - Sauvegardez vos timelines importantes pour y revenir plus tard
        
        ##### 🎨 Options de visualisation
        - **Linéaire** : Vue chronologique classique
        - **Par catégorie** : Événements groupés par type
        - **Par acteur** : Focus sur l'implication des personnes
        - **Densité** : Identification des périodes intenses
        
        ##### ⚡ Raccourcis
        - `Ctrl+F` : Rechercher dans les événements
        - Double-clic sur un événement : Voir les détails
        - Glisser sur le graphique : Zoomer sur une période
        """)
    
    def _save_timeline_config(self, events: List[Dict[str, Any]], config: Dict[str, Any]):
        """Sauvegarde la configuration d'une timeline"""
        if 'saved_configs' not in st.session_state:
            st.session_state.saved_configs = {}
        
        config_id = f"timeline_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.saved_configs[config_id] = {
            'events': events,
            'config': config,
            'created_at': datetime.now()
        }
        
        st.success(f"Configuration sauvegardée : {config_id}")
    
    def _convert_dataframe_to_events(self, df) -> List[Dict[str, Any]]:
        """Convertit un DataFrame en liste d'événements"""
        events = []
        
        for _, row in df.iterrows():
            event = {
                'date': pd.to_datetime(row.get('Date', datetime.now())),
                'description': str(row.get('Description', 'Sans description')),
                'importance': int(row.get('Importance', 5)),
                'category': str(row.get('Catégorie', 'autre')),
                'actors': str(row.get('Acteurs', '')).split(',') if row.get('Acteurs') else [],
                'source': 'Import CSV/Excel'
            }
            events.append(event)
        
        return events
    
    def _convert_json_to_events(self, data: Any) -> List[Dict[str, Any]]:
        """Convertit des données JSON en liste d'événements"""
        if isinstance(data, list):
            events = []
            for item in data:
                if isinstance(item, dict):
                    event = {
                        'date': datetime.fromisoformat(item.get('date', datetime.now().isoformat())),
                        'description': item.get('description', 'Sans description'),
                        'importance': item.get('importance', 5),
                        'category': item.get('category', 'autre'),
                        'actors': item.get('actors', []),
                        'source': 'Import JSON'
                    }
                    events.append(event)
            return events
        return []
    
    def _create_actor_timeline(self, events: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
        """Crée une timeline organisée par acteur"""
        # Grouper par acteur
        actor_events = defaultdict(list)
        for event in events:
            for actor in event.get('actors', ['Sans acteur']):
                actor_events[actor].append(event)
        
        # Créer le graphique
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        y_positions = {}
        
        for i, (actor, events_list) in enumerate(actor_events.items()):
            y_positions[actor] = i
            
            x_dates = [e['date'] for e in events_list]
            texts = [e['description'][:50] + '...' for e in events_list]
            sizes = [10 + e.get('importance', 5) * 2 for e in events_list]
            
            fig.add_trace(go.Scatter(
                x=x_dates,
                y=[i] * len(events_list),
                mode='markers',
                name=actor,
                text=texts,
                marker=dict(
                    size=sizes,
                    color=colors[i % len(colors)]
                ),
                hovertext=[e['description'] for e in events_list],
                hoverinfo='text'
            ))
        
        # Mise en forme
        fig.update_layout(
            title="Timeline par acteur",
            xaxis=dict(title="Date", type='date'),
            yaxis=dict(
                title="Acteurs",
                tickmode='array',
                tickvals=list(range(len(actor_events))),
                ticktext=list(actor_events.keys())
            ),
            height=max(400, 50 * len(actor_events)),
            hovermode='closest'
        )
        
        return fig
    
    def _create_density_timeline(self, events: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
        """Crée une timeline montrant la densité des événements"""
        if not PANDAS_AVAILABLE:
            return self._create_linear_timeline(events, config)
        
        # Créer un DataFrame
        df = pd.DataFrame([
            {
                'date': e['date'],
                'importance': e.get('importance', 5),
                'category': e.get('category', 'autre')
            }
            for e in events
        ])
        
        # Regrouper par semaine
        df['week'] = df['date'].dt.to_period('W')
        weekly_counts = df.groupby('week').size()
        
        # Créer le graphique
        fig = go.Figure()
        
        # Histogramme de densité
        fig.add_trace(go.Bar(
            x=weekly_counts.index.astype(str),
            y=weekly_counts.values,
            name='Événements par semaine',
            marker_color='lightblue'
        ))
        
        # Ajouter une ligne de tendance
        fig.add_trace(go.Scatter(
            x=weekly_counts.index.astype(str),
            y=weekly_counts.rolling(window=4).mean(),
            mode='lines',
            name='Tendance (moyenne mobile)',
            line=dict(color='red', width=2)
        ))
        
        # Mise en forme
        fig.update_layout(
            title="Densité temporelle des événements",
            xaxis=dict(title="Semaine"),
            yaxis=dict(title="Nombre d'événements"),
            hovermode='x unified'
        )
        
        return fig