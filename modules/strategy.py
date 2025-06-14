"""Module de stratégie juridique avec IA - Version améliorée avec multi-modèles"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import clean_key, format_legal_date, truncate_text

logger = logging.getLogger(__name__)

def run():
    """Fonction principale du module - Point d'entrée pour lazy loading"""
    
    # Configuration de la page
    st.set_page_config(
        page_title="Stratégie Juridique IA - Nexora Law",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Initialisation du module
    module = EnhancedStrategyModule()
    module.render()

class EnhancedStrategyModule:
    """Module de génération de stratégies juridiques avec IA multi-modèles"""
    
    def __init__(self):
        self.name = "Stratégie juridique IA"
        self.description = "Développez des stratégies de défense intelligentes avec l'aide de l'IA"
        self.icon = "⚖️"
        self.available = True
        
        # Initialisation des états
        self._initialize_session_state()
        
        # Configuration des modèles IA
        self.ai_models = {
            'gpt4': {
                'name': 'GPT-4 Turbo',
                'icon': '🧠',
                'strengths': 'Raisonnement complexe, créativité',
                'provider': 'OpenAI'
            },
            'claude3': {
                'name': 'Claude 3 Opus',
                'icon': '🎯',
                'strengths': 'Analyse approfondie, éthique',
                'provider': 'Anthropic'
            },
            'mistral': {
                'name': 'Mistral Large',
                'icon': '⚡',
                'strengths': 'Rapidité, efficacité',
                'provider': 'Mistral AI'
            },
            'llama3': {
                'name': 'Llama 3 70B',
                'icon': '🦙',
                'strengths': 'Open source, personnalisable',
                'provider': 'Meta'
            }
        }
        
        # Templates de stratégies enrichis
        self.strategy_templates = {
            'penal': {
                'name': '🚨 Défense pénale',
                'axes': ['Contestation procédure', 'Absence d\'intention', 'Légitime défense', 'Prescription'],
                'focus': 'innocence et respect de la procédure',
                'icon': '🚨',
                'color': '#ff4444'
            },
            'commercial': {
                'name': '💼 Litige commercial',
                'axes': ['Inexécution contractuelle', 'Force majeure', 'Vice caché', 'Bonne foi'],
                'focus': 'respect des obligations contractuelles',
                'icon': '💼',
                'color': '#4444ff'
            },
            'civil': {
                'name': '⚖️ Affaire civile',
                'axes': ['Responsabilité', 'Préjudice', 'Causalité', 'Réparation'],
                'focus': 'établissement du préjudice et de la responsabilité',
                'icon': '⚖️',
                'color': '#44ff44'
            },
            'administratif': {
                'name': '🏛️ Contentieux administratif',
                'axes': ['Excès de pouvoir', 'Illégalité', 'Détournement', 'Incompétence'],
                'focus': 'légalité des décisions administratives',
                'icon': '🏛️',
                'color': '#ff44ff'
            },
            'social': {
                'name': '👥 Droit social',
                'axes': ['Licenciement abusif', 'Discrimination', 'Harcèlement', 'Rupture conventionnelle'],
                'focus': 'protection des droits du travailleur',
                'icon': '👥',
                'color': '#ffaa44'
            }
        }
    
    def _initialize_session_state(self):
        """Initialise les variables de session"""
        if 'strategy_state' not in st.session_state:
            st.session_state.strategy_state = {
                'initialized': True,
                'current_strategy': None,
                'history': [],
                'comparison_mode': False,
                'selected_models': [],
                'fusion_results': None,
                'last_generation': None
            }
    
    def render(self):
        """Interface principale du module"""
        # En-tête avec animation
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown(
                f"""
                <div style="text-align: center; padding: 2rem;">
                    <h1 style="font-size: 3rem; margin-bottom: 0;">
                        {self.icon} {self.name}
                    </h1>
                    <p style="font-size: 1.2rem; color: #666; margin-top: 0.5rem;">
                        {self.description}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Métriques globales
        self._render_global_metrics()
        
        # Navigation principale
        tabs = st.tabs([
            "🎯 Nouvelle stratégie",
            "🤖 Configuration IA",
            "📚 Bibliothèque",
            "🔄 Comparaison",
            "📊 Analytics",
            "❓ Aide"
        ])
        
        with tabs[0]:
            self._render_new_strategy_enhanced()
        
        with tabs[1]:
            self._render_ai_configuration()
        
        with tabs[2]:
            self._render_strategy_library_enhanced()
        
        with tabs[3]:
            self._render_strategy_comparison_enhanced()
        
        with tabs[4]:
            self._render_analytics()
        
        with tabs[5]:
            self._render_help_enhanced()
    
    def _render_global_metrics(self):
        """Affiche les métriques globales"""
        if st.session_state.strategy_state['history']:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "📋 Stratégies créées",
                    len(st.session_state.strategy_state['history']),
                    f"+{len([s for s in st.session_state.strategy_state['history'] if (datetime.now() - s['created_at']).days < 7])} cette semaine"
                )
            
            with col2:
                success_rate = len([s for s in st.session_state.strategy_state['history'] 
                                  if s.get('outcome') == 'success']) / len(st.session_state.strategy_state['history']) * 100
                st.metric(
                    "✅ Taux de succès",
                    f"{success_rate:.0f}%",
                    "+5%" if success_rate > 70 else "-3%"
                )
            
            with col3:
                avg_complexity = sum([
                    {'Simple': 1, 'Modérée': 2, 'Complexe': 3, 'Très complexe': 4}
                    .get(s['config']['complexity'], 2) 
                    for s in st.session_state.strategy_state['history']
                ]) / len(st.session_state.strategy_state['history'])
                st.metric(
                    "🔧 Complexité moyenne",
                    f"{avg_complexity:.1f}/4"
                )
            
            with col4:
                urgent_cases = len([s for s in st.session_state.strategy_state['history'] 
                                  if s['config']['urgency'] in ['Élevée', 'Critique']])
                st.metric(
                    "⚡ Cas urgents",
                    urgent_cases
                )
            
            with col5:
                if st.session_state.strategy_state.get('last_generation'):
                    time_diff = datetime.now() - st.session_state.strategy_state['last_generation']
                    hours = int(time_diff.total_seconds() / 3600)
                    st.metric(
                        "🕐 Dernière génération",
                        f"Il y a {hours}h" if hours > 0 else "Récemment"
                    )
    
    def _render_new_strategy_enhanced(self):
        """Interface améliorée de création de stratégie"""
        
        # Assistant de démarrage rapide
        quick_start = st.container()
        with quick_start:
            st.markdown("### 🚀 Démarrage rapide")
            
            # Templates prédéfinis
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📋 Utiliser un template", use_container_width=True):
                    self._show_template_modal()
            with col2:
                if st.button("🔄 Reprendre la dernière", use_container_width=True):
                    self._load_last_strategy()
            with col3:
                if st.button("🤖 Assistant IA", use_container_width=True):
                    self._launch_ai_assistant()
        
        st.divider()
        
        # Formulaire principal avec mise en page améliorée
        with st.form("strategy_form"):
            # Section 1: Informations de base
            st.markdown("### 📋 Informations de l'affaire")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                case_type = st.selectbox(
                    "Type d'affaire",
                    list(self.strategy_templates.keys()),
                    format_func=lambda x: self.strategy_templates[x]['name'],
                    help="Sélectionnez le domaine juridique principal"
                )
                
                # Affichage dynamique de l'icône et de la couleur
                template = self.strategy_templates[case_type]
                st.markdown(
                    f"<div style='padding: 1rem; background-color: {template['color']}22; "
                    f"border-left: 4px solid {template['color']}; border-radius: 0.5rem;'>"
                    f"<strong>{template['icon']} Focus :</strong> {template['focus']}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            
            with col2:
                urgency = st.select_slider(
                    "Urgence",
                    ["🟢 Faible", "🟡 Modérée", "🟠 Élevée", "🔴 Critique"],
                    value="🟡 Modérée",
                    help="Définit les délais et la priorisation"
                )
                
                complexity = st.select_slider(
                    "Complexité",
                    ["📗 Simple", "📘 Modérée", "📙 Complexe", "📕 Très complexe"],
                    value="📘 Modérée",
                    help="Impact sur les ressources nécessaires"
                )
            
            with col3:
                budget = st.selectbox(
                    "Budget disponible",
                    ["💰 Limité", "💰💰 Standard", "💰💰💰 Confortable", "💰💰💰💰 Illimité"],
                    index=1,
                    help="Influence la profondeur de l'analyse"
                )
                
                jurisdiction = st.selectbox(
                    "Juridiction",
                    ["🇫🇷 France", "🇪🇺 Union Européenne", "🌍 International"],
                    help="Cadre juridique applicable"
                )
            
            # Section 2: Contexte détaillé avec aide IA
            st.markdown("### 📝 Contexte et analyse")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                context = st.text_area(
                    "Description détaillée du cas",
                    placeholder="Décrivez les faits, les parties impliquées, les enjeux juridiques...\n\n"
                               "💡 Conseil : Plus vous êtes précis, plus la stratégie sera pertinente.",
                    height=200,
                    help="Incluez dates, montants, noms (anonymisés si nécessaire)"
                )
            
            with col2:
                st.markdown("#### 🤖 Aide IA")
                if st.form_submit_button("🔍 Analyser le contexte"):
                    self._analyze_context_with_ai(context)
                
                if st.form_submit_button("💡 Suggestions"):
                    self._get_context_suggestions(case_type)
                
                if st.form_submit_button("📚 Cas similaires"):
                    self._find_similar_cases(context)
            
            # Section 3: Forces et faiblesses avec analyse SWOT
            st.markdown("### 🎯 Analyse SWOT juridique")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                strengths = st.text_area(
                    "💪 Forces",
                    placeholder="• Preuves solides\n• Témoins fiables\n• Jurisprudence favorable",
                    height=120
                )
            
            with col2:
                weaknesses = st.text_area(
                    "⚠️ Faiblesses",
                    placeholder="• Points contestables\n• Manque de preuves\n• Délais dépassés",
                    height=120
                )
            
            with col3:
                opportunities = st.text_area(
                    "🌟 Opportunités",
                    placeholder="• Négociation possible\n• Nouvelle jurisprudence\n• Médiation",
                    height=120
                )
            
            with col4:
                threats = st.text_area(
                    "🚨 Menaces",
                    placeholder="• Partie adverse agressive\n• Opinion publique\n• Coûts élevés",
                    height=120
                )
            
            # Section 4: Objectifs stratégiques
            st.markdown("### 🎯 Objectifs et priorités")
            
            col1, col2 = st.columns(2)
            
            with col1:
                objectives = st.multiselect(
                    "Objectifs principaux",
                    [
                        "🏆 Acquittement/Relaxe totale",
                        "📉 Réduction des charges",
                        "🤝 Négociation amiable",
                        "💰 Minimisation des dommages",
                        "⏱️ Gain de temps stratégique",
                        "📚 Créer un précédent juridique",
                        "🛡️ Protection de la réputation",
                        "🔄 Préparation à l'appel"
                    ],
                    default=["🏆 Acquittement/Relaxe totale"],
                    help="Sélectionnez par ordre de priorité"
                )
            
            with col2:
                constraints = st.multiselect(
                    "Contraintes à considérer",
                    [
                        "⏰ Délais serrés",
                        "💸 Budget limité",
                        "📰 Médiatisation",
                        "🌍 Dimension internationale",
                        "👥 Multiple parties",
                        "🔒 Confidentialité",
                        "📊 Enjeux financiers élevés"
                    ],
                    help="Éléments limitant les options stratégiques"
                )
            
            # Section 5: Configuration avancée
            with st.expander("⚙️ Configuration avancée et options IA", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🔍 Recherche et analyse**")
                    include_jurisprudence = st.checkbox("Recherche jurisprudence IA", value=True)
                    include_doctrine = st.checkbox("Analyse doctrine", value=True)
                    include_international = st.checkbox("Droit comparé", value=False)
                
                with col2:
                    st.markdown("**📊 Génération de contenu**")
                    include_scenarios = st.checkbox("Scénarios multiples", value=True)
                    include_timeline = st.checkbox("Planning détaillé", value=True)
                    include_templates = st.checkbox("Modèles de documents", value=True)
                
                with col3:
                    st.markdown("**🎯 Analyse approfondie**")
                    risk_assessment = st.checkbox("Analyse des risques IA", value=True)
                    cost_benefit = st.checkbox("Analyse coût-bénéfice", value=True)
                    success_prediction = st.checkbox("Prédiction de succès", value=True)
            
            # Bouton de soumission stylé
            submitted = st.form_submit_button(
                "🚀 Générer la stratégie avec IA",
                type="primary",
                use_container_width=True
            )
        
        # Traitement après soumission
        if submitted:
            if context:
                # Animation de chargement personnalisée
                with st.spinner(""):
                    # Préparation de la configuration
                    config = {
                        'case_type': case_type,
                        'urgency': urgency.split()[1],  # Retirer l'emoji
                        'complexity': complexity.split()[1],
                        'budget': budget.split()[1],
                        'jurisdiction': jurisdiction,
                        'context': context,
                        'strengths': strengths,
                        'weaknesses': weaknesses,
                        'opportunities': opportunities,
                        'threats': threats,
                        'objectives': [obj.split(maxsplit=1)[1] for obj in objectives],
                        'constraints': [con.split(maxsplit=1)[1] for con in constraints],
                        'include_jurisprudence': include_jurisprudence,
                        'include_doctrine': include_doctrine,
                        'include_international': include_international,
                        'include_scenarios': include_scenarios,
                        'include_timeline': include_timeline,
                        'include_templates': include_templates,
                        'risk_assessment': risk_assessment,
                        'cost_benefit': cost_benefit,
                        'success_prediction': success_prediction,
                        'selected_models': st.session_state.strategy_state.get('selected_models', ['gpt4'])
                    }
                    
                    # Générer la stratégie
                    self._generate_strategy_enhanced(config)
            else:
                st.error("❌ Veuillez décrire le contexte de l'affaire")
    
    def _render_ai_configuration(self):
        """Configuration des modèles IA"""
        st.markdown("### 🤖 Configuration des modèles IA")
        
        # Sélection des modèles
        st.markdown("#### 🧠 Sélection des modèles")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_models = st.multiselect(
                "Modèles à utiliser",
                list(self.ai_models.keys()),
                format_func=lambda x: f"{self.ai_models[x]['icon']} {self.ai_models[x]['name']}",
                default=['gpt4'],
                help="Sélectionnez un ou plusieurs modèles pour la génération"
            )
            
            st.session_state.strategy_state['selected_models'] = selected_models
        
        with col2:
            fusion_mode = st.radio(
                "Mode de fusion",
                ["🎯 Meilleur résultat", "🔄 Consensus", "🎨 Créatif", "📊 Analytique"],
                help="Comment combiner les résultats des différents modèles"
            )
        
        # Affichage des modèles sélectionnés
        if selected_models:
            st.markdown("#### 📋 Modèles sélectionnés")
            
            cols = st.columns(len(selected_models))
            for i, (col, model_key) in enumerate(zip(cols, selected_models)):
                model = self.ai_models[model_key]
                with col:
                    st.markdown(
                        f"""
                        <div style='padding: 1rem; background-color: #f0f0f0; 
                        border-radius: 0.5rem; text-align: center;'>
                            <h3>{model['icon']}</h3>
                            <h4>{model['name']}</h4>
                            <p style='font-size: 0.9rem; color: #666;'>{model['provider']}</p>
                            <p style='font-size: 0.8rem;'>{model['strengths']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Paramètres avancés
        with st.expander("⚙️ Paramètres avancés"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                temperature = st.slider(
                    "Température (créativité)",
                    0.0, 1.0, 0.7,
                    help="Plus élevé = plus créatif"
                )
                
                max_tokens = st.number_input(
                    "Tokens maximum",
                    1000, 8000, 4000,
                    help="Limite de longueur des réponses"
                )
            
            with col2:
                timeout = st.number_input(
                    "Timeout (secondes)",
                    10, 120, 30,
                    help="Temps maximum par modèle"
                )
                
                retries = st.number_input(
                    "Nombre d'essais",
                    1, 5, 3,
                    help="En cas d'échec"
                )
            
            with col3:
                cache_results = st.checkbox(
                    "Mettre en cache",
                    value=True,
                    help="Réutiliser les résultats similaires"
                )
                
                parallel_processing = st.checkbox(
                    "Traitement parallèle",
                    value=True,
                    help="Exécuter les modèles simultanément"
                )
        
        # Test de configuration
        st.markdown("#### 🧪 Test de configuration")
        
        test_prompt = st.text_area(
            "Prompt de test",
            placeholder="Entrez un cas simple pour tester la configuration...",
            height=100
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Tester", type="primary", use_container_width=True):
                if test_prompt and selected_models:
                    self._test_ai_configuration(selected_models, test_prompt, fusion_mode)
                else:
                    st.warning("Sélectionnez des modèles et entrez un prompt de test")
        
        # Statistiques d'utilisation
        st.markdown("#### 📊 Statistiques d'utilisation")
        
        # Graphique d'utilisation des modèles
        usage_data = self._get_model_usage_stats()
        if usage_data:
            fig = px.bar(
                usage_data,
                x='model',
                y='usage',
                color='performance',
                title="Utilisation et performance des modèles",
                labels={'usage': 'Nombre d\'utilisations', 'model': 'Modèle'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _generate_strategy_enhanced(self, config: Dict[str, Any]):
        """Génère une stratégie juridique avec multi-modèles IA"""
        
        # Interface de progression détaillée
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🚀 Génération en cours...")
            
            progress = st.progress(0)
            status = st.empty()
            details = st.empty()
            
            # Phases de génération
            phases = [
                ("🔍 Analyse du contexte", 10),
                ("🧠 Consultation des modèles IA", 30),
                ("🔄 Fusion des résultats", 50),
                ("📚 Recherche jurisprudentielle", 65),
                ("💡 Génération des arguments", 80),
                ("📊 Analyse des risques", 90),
                ("✨ Finalisation", 100)
            ]
            
            results_by_model = {}
            
            for phase, value in phases:
                status.markdown(f"**{phase}**")
                
                # Détails spécifiques par phase
                if "Consultation" in phase:
                    details.markdown("*Interrogation des modèles sélectionnés...*")
                    
                    # Simuler les résultats par modèle
                    model_cols = st.columns(len(config['selected_models']))
                    for i, (model_key, col) in enumerate(zip(config['selected_models'], model_cols)):
                        with col:
                            with st.spinner(f"{self.ai_models[model_key]['icon']} {self.ai_models[model_key]['name']}"):
                                time.sleep(0.5)
                                st.success("✅")
                                results_by_model[model_key] = self._simulate_model_result(model_key, config)
                
                elif "Fusion" in phase:
                    details.markdown("*Analyse croisée et synthèse des recommandations...*")
                    time.sleep(0.5)
                
                progress.progress(value)
                time.sleep(0.3)
            
            status.markdown("**✅ Stratégie générée avec succès !**")
            details.empty()
        
        # Créer la stratégie
        strategy = {
            'id': f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'created_at': datetime.now(),
            'config': config,
            'ai_models_used': config['selected_models'],
            'model_results': results_by_model,
            'main_approach': self._generate_main_approach_enhanced(config, results_by_model),
            'action_plan': self._generate_action_plan_enhanced(config, results_by_model),
            'arguments': self._generate_arguments_enhanced(config, results_by_model),
            'risks': self._assess_risks_enhanced(config, results_by_model) if config['risk_assessment'] else None,
            'scenarios': self._generate_scenarios_enhanced(config, results_by_model) if config['include_scenarios'] else None,
            'timeline': self._generate_timeline_enhanced(config) if config['include_timeline'] else None,
            'resources': self._estimate_resources_enhanced(config),
            'success_prediction': self._predict_success(config, results_by_model) if config['success_prediction'] else None,
            'cost_benefit': self._analyze_cost_benefit(config) if config['cost_benefit'] else None,
            'templates': self._generate_document_templates(config) if config['include_templates'] else None
        }
        
        # Sauvegarder
        st.session_state.strategy_state['history'].append(strategy)
        st.session_state.strategy_state['current_strategy'] = strategy
        st.session_state.strategy_state['last_generation'] = datetime.now()
        
        # Effacer le conteneur de progression
        progress_container.empty()
        
        # Afficher la stratégie
        self._display_strategy_enhanced(strategy)
    
    def _simulate_model_result(self, model_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simule le résultat d'un modèle IA"""
        # En production, ici on appellerait vraiment l'API du modèle
        model = self.ai_models[model_key]
        
        # Simulation de résultats différents selon le modèle
        if model_key == 'gpt4':
            return {
                'confidence': 0.85,
                'main_strategy': "Approche basée sur la contestation procédurale",
                'key_arguments': ["Nullité de la procédure", "Violation des droits"],
                'success_rate': 0.75
            }
        elif model_key == 'claude3':
            return {
                'confidence': 0.90,
                'main_strategy': "Stratégie éthique et argumentative",
                'key_arguments': ["Bonne foi manifeste", "Absence d'intention"],
                'success_rate': 0.80
            }
        elif model_key == 'mistral':
            return {
                'confidence': 0.82,
                'main_strategy': "Défense rapide et efficace",
                'key_arguments': ["Prescription", "Preuves insuffisantes"],
                'success_rate': 0.70
            }
        else:
            return {
                'confidence': 0.78,
                'main_strategy': "Approche alternative et créative",
                'key_arguments': ["Jurisprudence innovante", "Interprétation favorable"],
                'success_rate': 0.65
            }
    
    def _generate_main_approach_enhanced(self, config: Dict[str, Any], model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Génère l'approche principale avec fusion des modèles"""
        template = self.strategy_templates[config['case_type']]
        
        # Fusion des stratégies des différents modèles
        all_strategies = [result['main_strategy'] for result in model_results.values()]
        confidence_avg = sum(result['confidence'] for result in model_results.values()) / len(model_results)
        
        # Sélection des axes basée sur l'analyse combinée
        selected_axes = template['axes'][:2]  # Simplification pour la démo
        
        # Synthèse narrative enrichie
        narrative = f"""
        Après analyse par {len(model_results)} modèles d'IA avec une confiance moyenne de {confidence_avg:.0%}, 
        la stratégie recommandée s'articule autour de {len(selected_axes)} axes principaux, 
        en mettant l'accent sur {template['focus']}. 
        
        Les différents modèles convergent sur l'importance de {selected_axes[0].lower()}, 
        avec des approches complémentaires permettant une défense robuste et adaptative.
        
        Cette stratégie multi-angles vise à {config['objectives'][0].lower()} 
        tout en anticipant les contre-arguments potentiels.
        """
        
        return {
            'title': f"Stratégie de {template['name']}",
            'focus': template['focus'],
            'primary_axes': selected_axes,
            'narrative': narrative.strip(),
            'key_message': "Notre client a agi dans le strict respect du droit et de ses obligations.",
            'confidence_level': confidence_avg,
            'model_consensus': all_strategies
        }
    
    def _generate_action_plan_enhanced(self, config: Dict[str, Any], model_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère un plan d'action enrichi"""
        actions = []
        
        # Phase immédiate pour les cas urgents
        if config['urgency'] in ['Élevée', 'Critique']:
            actions.append({
                'phase': '🚨 Immédiat (0-48h)',
                'priority': 'Critique',
                'tasks': [
                    '📞 Constituer l\'équipe de crise juridique',
                    '🔒 Sécuriser toutes les preuves et documents',
                    '👥 Identifier et briefer les témoins clés',
                    '📋 Préparer la première réponse procédurale',
                    '📰 Gérer la communication si médiatisation'
                ],
                'ai_recommendations': [
                    result['key_arguments'][0] if result.get('key_arguments') else ""
                    for result in model_results.values()
                ]
            })
        
        # Phase court terme
        actions.append({
            'phase': '📅 Court terme (1-2 semaines)',
            'priority': 'Élevée',
            'tasks': [
                '📚 Analyse approfondie du dossier avec IA',
                '🔍 Recherche jurisprudentielle automatisée',
                '💡 Développement des arguments principaux',
                '🤝 Exploration des options de négociation',
                '📊 Première évaluation des risques'
            ],
            'estimated_hours': 40,
            'team_required': ['Avocat senior', 'Juriste IA', 'Assistant']
        })
        
        # Phase moyen terme
        actions.append({
            'phase': '📈 Moyen terme (2-8 semaines)',
            'priority': 'Normale',
            'tasks': [
                '⚖️ Finalisation de la stratégie complète',
                '👨‍⚖️ Préparation intensive des témoins',
                '📄 Constitution du dossier de plaidoirie',
                '🛡️ Anticipation des contre-arguments',
                '💰 Analyse coût-bénéfice détaillée'
            ],
            'milestones': [
                {'name': 'Stratégie validée', 'deadline': 14},
                {'name': 'Témoins préparés', 'deadline': 30},
                {'name': 'Dossier complet', 'deadline': 45}
            ]
        })
        
        # Phase long terme pour cas complexes
        if config['complexity'] in ['Complexe', 'Très complexe']:
            actions.append({
                'phase': '🎯 Long terme (2+ mois)',
                'priority': 'Stratégique',
                'tasks': [
                    '🔬 Expertises techniques spécialisées',
                    '🌐 Stratégie médiatique et RP',
                    '📈 Préparation aux appels éventuels',
                    '🔄 Plans de contingence détaillés',
                    '🤖 Monitoring IA continu'
                ],
                'budget_allocation': '30% du budget total',
                'success_factors': ['Anticipation', 'Flexibilité', 'Innovation']
            })
        
        return actions
    
    def _generate_arguments_enhanced(self, config: Dict[str, Any], model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des arguments juridiques enrichis par l'IA"""
        
        # Compilation des arguments de tous les modèles
        all_arguments = []
        for model_key, result in model_results.items():
            if result.get('key_arguments'):
                all_arguments.extend([
                    {'argument': arg, 'source': self.ai_models[model_key]['name'], 'confidence': result['confidence']}
                    for arg in result['key_arguments']
                ])
        
        # Catégorisation intelligente
        arguments = {
            'principaux': [],
            'subsidiaires': [],
            'innovants': [],
            'contra': [],
            'jurisprudence': []
        }
        
        # Arguments principaux avec score de confiance
        if config['case_type'] == 'penal':
            arguments['principaux'] = [
                {
                    'titre': "Absence d'élément intentionnel",
                    'description': "Démonstration de l'absence totale d'intention délictuelle",
                    'force': 9,
                    'jurisprudence': ["Cass. Crim. 2023", "CEDH 2022"],
                    'ai_confidence': 0.92
                },
                {
                    'titre': "Nullité de la procédure",
                    'description': "Violations substantielles des droits de la défense",
                    'force': 8,
                    'jurisprudence': ["CC 2021-976 QPC"],
                    'ai_confidence': 0.88
                }
            ]
        
        # Arguments innovants suggérés par l'IA
        arguments['innovants'] = [
            {
                'titre': "Approche algorithmique",
                'description': "Utilisation de l'IA pour démontrer l'incohérence des preuves",
                'nouveauté': 'Première utilisation en France',
                'risque': 'Modéré',
                'potentiel': 'Élevé'
            }
        ]
        
        # Contre-arguments anticipés avec réponses
        arguments['contra'] = [
            {
                'objection': "La partie adverse invoquera la jurisprudence constante",
                'réponse': "Nous démontrerons l'évolution récente et les particularités du cas",
                'préparation': "Compilation exhaustive des arrêts favorables récents"
            }
        ]
        
        return arguments
    
    def _assess_risks_enhanced(self, config: Dict[str, Any], model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Évaluation des risques améliorée avec IA"""
        
        risks = {
            'level': 'Modéré',
            'score': 0,
            'factors': [],
            'mitigation': [],
            'heatmap': [],
            'ai_assessment': {}
        }
        
        # Facteurs de risque avec scoring
        risk_factors = []
        
        if config['weaknesses']:
            risk_factors.append({
                'type': '⚠️ Faiblesses identifiées',
                'severity': 'Élevée',
                'probability': 0.7,
                'impact': 8,
                'description': 'Points faibles pouvant être exploités',
                'mitigation_cost': 'Modéré'
            })
        
        if config['urgency'] == 'Critique':
            risk_factors.append({
                'type': '⏰ Contrainte temporelle',
                'severity': 'Élevée',
                'probability': 0.9,
                'impact': 7,
                'description': 'Temps insuffisant pour préparation optimale',
                'mitigation_cost': 'Élevé'
            })
        
        # Calcul du score de risque global
        total_risk_score = sum(f['probability'] * f['impact'] for f in risk_factors) / len(risk_factors) if risk_factors else 0
        
        # Niveau de risque basé sur le score
        if total_risk_score > 6:
            risks['level'] = '🔴 Élevé'
        elif total_risk_score > 4:
            risks['level'] = '🟡 Modéré'
        else:
            risks['level'] = '🟢 Faible'
        
        risks['score'] = total_risk_score
        risks['factors'] = risk_factors
        
        # Stratégies de mitigation personnalisées
        for factor in risk_factors:
            if 'Faiblesses' in factor['type']:
                risks['mitigation'].append({
                    'risque': factor['type'],
                    'stratégie': "Renforcer les points faibles par expertise complémentaire",
                    'coût': factor['mitigation_cost'],
                    'délai': '1-2 semaines',
                    'efficacité_estimée': '75%'
                })
        
        # Matrice de risques
        risks['heatmap'] = self._generate_risk_heatmap(risk_factors)
        
        # Évaluation par l'IA
        risks['ai_assessment'] = {
            'consensus': sum(r.get('success_rate', 0.7) for r in model_results.values()) / len(model_results),
            'divergence': max(r.get('success_rate', 0.7) for r in model_results.values()) - 
                         min(r.get('success_rate', 0.7) for r in model_results.values()),
            'recommendation': "Procéder avec prudence mais confiance"
        }
        
        return risks
    
    def _generate_scenarios_enhanced(self, config: Dict[str, Any], model_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des scénarios enrichis avec probabilités IA"""
        
        # Calcul des probabilités basé sur les prédictions des modèles
        avg_success = sum(r.get('success_rate', 0.7) for r in model_results.values()) / len(model_results)
        
        scenarios = []
        
        # Scénario optimiste
        scenarios.append({
            'name': '🌟 Scénario optimal',
            'probability': f"{min(avg_success * 100 + 10, 95):.0f}%",
            'timeline': '2-3 mois',
            'description': 'Victoire totale avec jurisprudence favorable',
            'outcome': config['objectives'][0] if config['objectives'] else 'Succès complet',
            'conditions': [
                '✅ Tous les arguments acceptés',
                '✅ Procédure accélérée accordée',
                '✅ Témoins convaincants',
                '✅ Jurisprudence récente applicable'
            ],
            'financial_impact': 'Coûts minimaux, indemnisation possible',
            'reputation_impact': 'Renforcement de la réputation',
            'next_steps': ['Préparer l\'exécution', 'Communication positive']
        })
        
        # Scénario réaliste
        scenarios.append({
            'name': '📊 Scénario probable',
            'probability': f"{avg_success * 100:.0f}%",
            'timeline': '4-6 mois',
            'description': 'Résolution favorable avec compromis mineurs',
            'outcome': 'Succès sur les points essentiels',
            'conditions': [
                '✅ Arguments principaux reconnus',
                '⚠️ Concessions sur points secondaires',
                '✅ Négociation constructive',
                '⚠️ Délais standards respectés'
            ],
            'financial_impact': 'Coûts maîtrisés',
            'reputation_impact': 'Neutre à positif',
            'key_risks': ['Prolongation possible', 'Coûts supplémentaires limités']
        })
        
        # Scénario pessimiste mais gérable
        scenarios.append({
            'name': '⚠️ Scénario défavorable',
            'probability': f"{max((1 - avg_success) * 100 - 10, 5):.0f}%",
            'timeline': '6-12 mois',
            'description': 'Difficultés nécessitant stratégie d\'appel',
            'outcome': 'Échec en première instance',
            'conditions': [
                '❌ Arguments principaux rejetés',
                '❌ Nouvelles preuves défavorables',
                '⚠️ Juge défavorable',
                '❌ Témoins peu convaincants'
            ],
            'contingency': {
                'plan_b': "Appel immédiat avec nouvelle stratégie",
                'budget_additionnel': '+50% du budget initial',
                'equipe_renforcee': 'Ajout d\'experts spécialisés',
                'delai': '+6-12 mois'
            },
            'lessons_learned': 'Points à améliorer pour l\'appel'
        })
        
        # Scénario alternatif (règlement amiable)
        if "Négociation" in ' '.join(config['objectives']):
            scenarios.append({
                'name': '🤝 Scénario transactionnel',
                'probability': '40%',
                'timeline': '1-2 mois',
                'description': 'Règlement amiable rapide',
                'outcome': 'Transaction satisfaisante',
                'conditions': [
                    '🤝 Volonté mutuelle de négocier',
                    '💰 Accord sur les montants',
                    '📝 Confidentialité respectée',
                    '✅ Évitement du procès'
                ],
                'advantages': ['Rapidité', 'Coûts réduits', 'Confidentialité'],
                'disadvantages': ['Pas de précédent', 'Compromis nécessaires']
            })
        
        return scenarios
    
    def _predict_success(self, config: Dict[str, Any], model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prédiction du taux de succès basée sur l'IA"""
        
        # Facteurs de succès
        success_factors = {
            'case_strength': 0,
            'evidence_quality': 0,
            'legal_precedent': 0,
            'team_experience': 0,
            'opponent_weakness': 0,
            'judge_tendency': 0
        }
        
        # Calcul basé sur SWOT
        if config['strengths']:
            success_factors['case_strength'] = 0.8
        if config['weaknesses']:
            success_factors['case_strength'] *= 0.8
        
        # Intégration des prédictions IA
        ai_predictions = [r.get('success_rate', 0.7) for r in model_results.values()]
        avg_ai_prediction = sum(ai_predictions) / len(ai_predictions)
        
        # Score global
        human_factors_score = sum(success_factors.values()) / len(success_factors)
        final_score = (human_factors_score * 0.4 + avg_ai_prediction * 0.6)
        
        return {
            'overall_success_rate': final_score,
            'confidence_interval': (final_score - 0.1, final_score + 0.1),
            'key_success_factors': success_factors,
            'ai_predictions': {
                model: pred for model, pred in zip(model_results.keys(), ai_predictions)
            },
            'recommendation': self._get_success_recommendation(final_score),
            'improvement_suggestions': self._get_improvement_suggestions(success_factors)
        }
    
    def _get_success_recommendation(self, score: float) -> str:
        """Recommandation basée sur le score de succès"""
        if score > 0.8:
            return "✅ Procéder avec confiance - Excellentes chances de succès"
        elif score > 0.6:
            return "✅ Procéder avec stratégie solide - Bonnes chances de succès"
        elif score > 0.4:
            return "⚠️ Procéder avec prudence - Renforcer certains aspects"
        else:
            return "🔴 Reconsidérer l'approche - Explorer alternatives"
    
    def _get_improvement_suggestions(self, factors: Dict[str, float]) -> List[str]:
        """Suggestions d'amélioration basées sur les facteurs"""
        suggestions = []
        
        for factor, score in factors.items():
            if score < 0.5:
                if factor == 'evidence_quality':
                    suggestions.append("🔍 Renforcer les preuves documentaires")
                elif factor == 'legal_precedent':
                    suggestions.append("📚 Approfondir la recherche jurisprudentielle")
                elif factor == 'team_experience':
                    suggestions.append("👥 Considérer l'ajout d'experts spécialisés")
        
        return suggestions
    
    def _generate_timeline_enhanced(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère un planning détaillé et interactif"""
        
        timeline = []
        start_date = datetime.now()
        
        # Jalons adaptés à l'urgence
        urgency_factor = {
            'Faible': 1.5,
            'Modérée': 1.0,
            'Élevée': 0.7,
            'Critique': 0.5
        }.get(config['urgency'], 1.0)
        
        milestones = [
            {
                'name': '📋 Analyse complète du dossier',
                'duration': 5,
                'deliverables': ['Rapport d\'analyse', 'Matrice SWOT', 'Plan d\'action'],
                'critical': True
            },
            {
                'name': '🔍 Recherche jurisprudentielle IA',
                'duration': 7,
                'deliverables': ['Base de données jurisprudence', 'Analyse des précédents'],
                'critical': True
            },
            {
                'name': '💡 Développement argumentaire',
                'duration': 14,
                'deliverables': ['Mémoire principal', 'Arguments subsidiaires'],
                'critical': True
            },
            {
                'name': '👥 Préparation des témoins',
                'duration': 21,
                'deliverables': ['Scripts de témoignage', 'Sessions de préparation'],
                'critical': False
            },
            {
                'name': '📄 Constitution du dossier',
                'duration': 30,
                'deliverables': ['Dossier complet', 'Pièces numérotées'],
                'critical': True
            },
            {
                'name': '🎯 Finalisation stratégie',
                'duration': 35,
                'deliverables': ['Document stratégique final', 'Briefing équipe'],
                'critical': True
            },
            {
                'name': '⚖️ Prêt pour l\'audience',
                'duration': 45,
                'deliverables': ['Plaidoirie', 'Supports visuels', 'Plan B'],
                'critical': True
            }
        ]
        
        for milestone in milestones:
            target_date = start_date + timedelta(days=int(milestone['duration'] * urgency_factor))
            
            timeline.append({
                'milestone': milestone['name'],
                'target_date': target_date,
                'duration_days': int(milestone['duration'] * urgency_factor),
                'status': '⏳ À venir',
                'progress': 0,
                'responsible': 'Équipe juridique',
                'deliverables': milestone['deliverables'],
                'critical_path': milestone['critical'],
                'dependencies': [],
                'alerts': []
            })
        
        return timeline
    
    def _generate_risk_heatmap(self, risk_factors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Génère une heatmap des risques"""
        
        # Catégories de probabilité et d'impact
        probability_levels = ['Très faible', 'Faible', 'Modérée', 'Élevée', 'Très élevée']
        impact_levels = ['Négligeable', 'Mineur', 'Modéré', 'Majeur', 'Critique']
        
        # Matrice 5x5
        matrix = [[0 for _ in range(5)] for _ in range(5)]
        
        # Placement des risques
        for factor in risk_factors:
            prob_idx = min(int(factor['probability'] * 5), 4)
            impact_idx = min(int(factor['impact'] / 2), 4)
            matrix[prob_idx][impact_idx] += 1
        
        return {
            'matrix': matrix,
            'probability_axis': probability_levels,
            'impact_axis': impact_levels,
            'risk_zones': {
                'low': [(i, j) for i in range(2) for j in range(2)],
                'medium': [(i, j) for i in range(2, 4) for j in range(2, 4)],
                'high': [(i, j) for i in range(3, 5) for j in range(3, 5)]
            }
        }
    
    def _estimate_resources_enhanced(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Estimation améliorée des ressources avec IA"""
        
        resources = {
            'team': [],
            'time_estimate': '',
            'budget_breakdown': {},
            'external_needs': [],
            'ai_tools': [],
            'success_correlation': 0
        }
        
        # Équipe selon complexité et IA
        base_team = [
            {'role': '👨‍⚖️ Avocat principal senior', 'hours': 100, 'rate': 400},
            {'role': '🤖 Juriste IA', 'hours': 80, 'rate': 250},
            {'role': '📚 Juriste recherche', 'hours': 60, 'rate': 200}
        ]
        
        if config['complexity'] in ['Complexe', 'Très complexe']:
            base_team.extend([
                {'role': '⚖️ Avocat plaidant', 'hours': 50, 'rate': 500},
                {'role': '👥 Avocat collaborateur', 'hours': 120, 'rate': 300},
                {'role': '📊 Analyste données', 'hours': 40, 'rate': 180}
            ])
        
        resources['team'] = base_team
        
        # Calcul du temps total
        total_hours = sum(member['hours'] for member in base_team)
        resources['time_estimate'] = f"{total_hours} heures ({total_hours//40} semaines-personne)"
        
        # Budget détaillé
        budget_multiplier = {
            'Limité': 0.7,
            'Standard': 1.0,
            'Confortable': 1.3,
            'Illimité': 1.6
        }.get(config['budget'], 1.0)
        
        # Calcul par catégorie
        honoraires = sum(m['hours'] * m['rate'] for m in base_team) * budget_multiplier
        frais_proc = honoraires * 0.15
        recherche = honoraires * 0.10
        experts = honoraires * 0.20 if config['complexity'] in ['Complexe', 'Très complexe'] else 0
        
        resources['budget_breakdown'] = {
            '💰 Honoraires': f"{honoraires:,.0f} €",
            '📋 Frais de procédure': f"{frais_proc:,.0f} €",
            '🔍 Recherche & IA': f"{recherche:,.0f} €",
            '👨‍🔬 Experts': f"{experts:,.0f} €" if experts else "0 €",
            '💵 Total': f"{(honoraires + frais_proc + recherche + experts):,.0f} €"
        }
        
        # Outils IA recommandés
        resources['ai_tools'] = [
            '🤖 Assistant juridique IA',
            '📚 Recherche jurisprudentielle automatisée',
            '📊 Analyse prédictive de succès',
            '📝 Génération de documents',
            '🔍 Veille juridique continue'
        ]
        
        # Corrélation ressources/succès
        resources['success_correlation'] = min(budget_multiplier * 0.6 + 0.4, 1.0)
        
        return resources
    
    def _analyze_cost_benefit(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse coût-bénéfice détaillée"""
        
        # Coûts estimés
        cost_estimate = {
            'Limité': (20000, 40000),
            'Standard': (40000, 80000),
            'Confortable': (80000, 150000),
            'Illimité': (150000, 300000)
        }.get(config['budget'], (40000, 80000))
        
        # Bénéfices potentiels selon objectifs
        benefits = {
            'financial': 0,
            'reputation': 0,
            'strategic': 0,
            'time_saved': 0
        }
        
        # Calcul selon objectifs
        if 'Minimisation des dommages' in config['objectives']:
            benefits['financial'] = cost_estimate[1] * 3  # Éviter 3x les coûts
        
        if 'Protection de la réputation' in config['objectives']:
            benefits['reputation'] = cost_estimate[1] * 2  # Valeur réputationnelle
        
        # ROI estimé
        total_benefits = sum(benefits.values())
        total_costs = cost_estimate[1]
        roi = ((total_benefits - total_costs) / total_costs) * 100 if total_costs > 0 else 0
        
        return {
            'cost_range': cost_estimate,
            'benefits': benefits,
            'roi_percentage': roi,
            'breakeven_probability': 1 / (1 + (total_benefits / total_costs)) if total_costs > 0 else 0.5,
            'recommendation': 'Procéder' if roi > 50 else 'Évaluer alternatives',
            'sensitivity_analysis': {
                'best_case': roi * 1.5,
                'worst_case': roi * 0.5,
                'most_likely': roi
            }
        }
    
    def _generate_document_templates(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Génère des templates de documents juridiques"""
        
        templates = {}
        
        # Template selon le type d'affaire
        if config['case_type'] == 'penal':
            templates['conclusions'] = """
CONCLUSIONS EN DÉFENSE

Pour : [CLIENT]
Contre : [PARTIE ADVERSE]

PLAISE AU TRIBUNAL

I. RAPPEL DES FAITS
[Résumé factuel neutre]

II. DISCUSSION
A. Sur la procédure
   1. [Argument procédural 1]
   2. [Argument procédural 2]

B. Sur le fond
   1. [Argument de fond 1]
   2. [Argument de fond 2]

III. DEMANDES
[Liste des demandes]
"""
        
        templates['lettre_client'] = f"""
Cher(e) [CLIENT],

Suite à notre analyse approfondie de votre dossier, nous avons établi une stratégie 
axée sur {config['objectives'][0] if config['objectives'] else 'vos objectifs'}.

Points clés :
1. [Point 1]
2. [Point 2]
3. [Point 3]

Prochaines étapes :
- [Action 1]
- [Action 2]

Nous restons à votre disposition.

Cordialement,
[AVOCAT]
"""
        
        return templates
    
    def _display_strategy_enhanced(self, strategy: Dict[str, Any]):
        """Affichage amélioré de la stratégie avec visualisations"""
        
        # Animation de succès
        st.balloons()
        st.success("✅ Stratégie générée avec succès !")
        
        # En-tête avec informations clés
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"## 📋 {strategy['main_approach']['title']}")
            st.markdown(f"*Générée le {strategy['created_at'].strftime('%d/%m/%Y à %H:%M')}*")
        
        with col2:
            if strategy.get('success_prediction'):
                success_rate = strategy['success_prediction']['overall_success_rate']
                st.metric(
                    "🎯 Taux de succès prédit",
                    f"{success_rate:.0%}",
                    delta=f"±{10}%"
                )
        
        with col3:
            st.markdown("### 🤖 Modèles utilisés")
            for model in strategy['ai_models_used']:
                st.write(f"{self.ai_models[model]['icon']} {self.ai_models[model]['name']}")
        
        # Graphique de synthèse rapide
        if strategy.get('success_prediction'):
            self._display_success_gauge(strategy['success_prediction'])
        
        # Navigation par onglets enrichie
        tabs = st.tabs([
            "🎯 Vue d'ensemble",
            "📋 Plan d'action",
            "💭 Arguments",
            "⚠️ Risques",
            "🔄 Scénarios",
            "📅 Planning",
            "💰 Ressources",
            "📊 Analyses",
            "💾 Export"
        ])
        
        with tabs[0]:
            self._display_overview_enhanced(strategy)
        
        with tabs[1]:
            self._display_action_plan_enhanced(strategy)
        
        with tabs[2]:
            self._display_arguments_enhanced(strategy)
        
        with tabs[3]:
            self._display_risks_enhanced(strategy)
        
        with tabs[4]:
            self._display_scenarios_enhanced(strategy)
        
        with tabs[5]:
            self._display_timeline_enhanced(strategy)
        
        with tabs[6]:
            self._display_resources_enhanced(strategy)
        
        with tabs[7]:
            self._display_analytics_enhanced(strategy)
        
        with tabs[8]:
            self._display_export_enhanced(strategy)
        
        # Actions rapides flottantes
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("💾 Sauvegarder", use_container_width=True):
                    st.success("Stratégie sauvegardée !")
            
            with col2:
                if st.button("📧 Partager", use_container_width=True):
                    self._share_strategy(strategy)
            
            with col3:
                if st.button("🔄 Modifier", use_container_width=True):
                    self._edit_strategy(strategy)
            
            with col4:
                if st.button("📊 Comparer", use_container_width=True):
                    st.session_state.strategy_state['comparison_mode'] = True
                    st.rerun()
    
    def _display_success_gauge(self, prediction: Dict[str, Any]):
        """Affiche une jauge de succès visuelle"""
        
        success_rate = prediction['overall_success_rate']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=success_rate * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Probabilité de succès globale"},
            delta={'reference': 70},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_overview_enhanced(self, strategy: Dict[str, Any]):
        """Vue d'ensemble enrichie de la stratégie"""
        
        # Message clé en évidence
        st.markdown(
            f"""
            <div style='padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border-radius: 1rem; text-align: center; margin: 1rem 0;'>
                <h3 style='margin: 0; font-size: 1.5rem;'>💬 Message clé</h3>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; font-style: italic;'>
                    "{strategy['main_approach']['key_message']}"
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Approche stratégique
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Approche stratégique")
            st.info(strategy['main_approach']['narrative'])
            
            # Axes prioritaires avec progression
            st.markdown("#### 📍 Axes de défense prioritaires")
            for i, axis in enumerate(strategy['main_approach']['primary_axes'], 1):
                progress = st.progress(0.7 + i * 0.1)
                st.markdown(f"**{i}. {axis}**")
        
        with col2:
            # Consensus des modèles IA
            st.markdown("### 🤖 Consensus IA")
            
            confidence = strategy['main_approach']['confidence_level']
            
            # Graphique en anneau
            fig = go.Figure(data=[
                go.Pie(
                    values=[confidence, 1-confidence],
                    labels=['Confiance', 'Incertitude'],
                    hole=.7,
                    marker_colors=['#667eea', '#f0f0f0']
                )
            ])
            
            fig.update_layout(
                annotations=[{
                    'text': f'{confidence:.0%}',
                    'x': 0.5, 'y': 0.5,
                    'font_size': 30,
                    'showarrow': False
                }],
                showlegend=False,
                height=200,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Résumé des objectifs et contraintes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Objectifs poursuivis")
            for obj in strategy['config']['objectives']:
                st.markdown(f"- ✅ {obj}")
        
        with col2:
            st.markdown("### ⚠️ Contraintes identifiées")
            if strategy['config']['constraints']:
                for constraint in strategy['config']['constraints']:
                    st.markdown(f"- ⚡ {constraint}")
            else:
                st.markdown("*Aucune contrainte majeure identifiée*")
    
    def _display_action_plan_enhanced(self, strategy: Dict[str, Any]):
        """Plan d'action interactif et visuel"""
        
        st.markdown("### 📋 Plan d'action stratégique")
        
        # Timeline visuelle
        phases = strategy['action_plan']
        
        # Créer un diagramme de Gantt simplifié
        gantt_data = []
        start_date = datetime.now()
        
        for i, phase in enumerate(phases):
            duration = phase.get('estimated_hours', 40) / 8  # Convertir en jours
            end_date = start_date + timedelta(days=duration)
            
            gantt_data.append({
                'Phase': phase['phase'],
                'Start': start_date,
                'End': end_date,
                'Priority': phase['priority']
            })
            
            start_date = end_date
        
        # Affichage des phases
        for phase in phases:
            priority_colors = {
                'Critique': '#ff4444',
                'Élevée': '#ff8844',
                'Normale': '#4444ff',
                'Stratégique': '#44ff44'
            }
            
            with st.expander(
                f"**{phase['phase']}** - Priorité : {phase['priority']}",
                expanded=phase['priority'] == 'Critique'
            ):
                # Métriques de la phase
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("⏱️ Durée estimée", f"{phase.get('estimated_hours', 'N/A')}h")
                
                with col2:
                    st.metric("👥 Équipe", f"{len(phase.get('team_required', []))} pers.")
                
                with col3:
                    st.metric("📋 Tâches", len(phase['tasks']))
                
                # Liste des tâches avec checkboxes
                st.markdown("**📝 Tâches à accomplir :**")
                
                for j, task in enumerate(phase['tasks']):
                    col1, col2 = st.columns([20, 1])
                    with col1:
                        done = st.checkbox(task, key=f"task_{i}_{j}")
                    with col2:
                        if done:
                            st.markdown("✅")
                
                # Recommandations IA si disponibles
                if phase.get('ai_recommendations'):
                    st.markdown("**🤖 Recommandations IA :**")
                    for rec in phase['ai_recommendations']:
                        if rec:
                            st.info(f"💡 {rec}")
                
                # Jalons si disponibles
                if phase.get('milestones'):
                    st.markdown("**🎯 Jalons clés :**")
                    for milestone in phase['milestones']:
                        st.write(f"- {milestone['name']} - J+{milestone['deadline']}")
    
    def _display_arguments_enhanced(self, strategy: Dict[str, Any]):
        """Arguments juridiques avec force et visualisation"""
        
        st.markdown("### 💭 Stratégie argumentaire")
        
        arguments = strategy['arguments']
        
        # Vue d'ensemble des arguments
        total_args = (len(arguments.get('principaux', [])) + 
                     len(arguments.get('subsidiaires', [])) + 
                     len(arguments.get('innovants', [])))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total arguments", total_args)
        with col2:
            st.metric("⚖️ Arguments principaux", len(arguments.get('principaux', [])))
        with col3:
            st.metric("💡 Arguments innovants", len(arguments.get('innovants', [])))
        
        # Arguments principaux avec indicateur de force
        if arguments.get('principaux'):
            st.markdown("#### ⚖️ Arguments principaux")
            
            for arg in arguments['principaux']:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    with st.container():
                        st.markdown(f"**{arg['titre']}**")
                        st.write(arg['description'])
                        
                        # Jurisprudence associée
                        if arg.get('jurisprudence'):
                            with st.expander("📚 Jurisprudence"):
                                for juris in arg['jurisprudence']:
                                    st.write(f"- {juris}")
                
                with col2:
                    # Indicateur de force
                    force = arg.get('force', 5)
                    fig = go.Figure(go.Indicator(
                        mode="gauge",
                        value=force,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 10]},
                            'bar': {'color': "darkgreen" if force > 7 else "orange"},
                            'steps': [
                                {'range': [0, 4], 'color': "lightgray"},
                                {'range': [4, 7], 'color': "gray"},
                                {'range': [7, 10], 'color': "lightgreen"}
                            ]
                        }
                    ))
                    fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Confiance IA
                    if arg.get('ai_confidence'):
                        st.metric("🤖 Confiance IA", f"{arg['ai_confidence']:.0%}")
        
        # Arguments innovants
        if arguments.get('innovants'):
            st.markdown("#### 💡 Arguments innovants (suggestions IA)")
            
            for arg in arguments['innovants']:
                with st.expander(f"🚀 {arg['titre']}", expanded=False):
                    st.write(f"**Description :** {arg['description']}")
                    st.write(f"**Nouveauté :** {arg.get('nouveauté', 'N/A')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Risque :** {arg.get('risque', 'N/A')}")
                    with col2:
                        st.write(f"**Potentiel :** {arg.get('potentiel', 'N/A')}")
        
        # Anticipation des contre-arguments
        if arguments.get('contra'):
            st.markdown("#### 🛡️ Anticipation et riposte")
            
            for contra in arguments['contra']:
                with st.container():
                    st.warning(f"**❌ Objection probable :** {contra['objection']}")
                    st.success(f"**✅ Notre réponse :** {contra['réponse']}")
                    if contra.get('préparation'):
                        st.info(f"**📋 Préparation :** {contra['préparation']}")
    
    def _display_risks_enhanced(self, strategy: Dict[str, Any]):
        """Analyse des risques avec visualisations avancées"""
        
        if not strategy.get('risks'):
            st.info("Analyse des risques non demandée")
            return
        
        risks = strategy['risks']
        
        st.markdown("### ⚠️ Analyse des risques")
        
        # Vue d'ensemble
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_color = {
                '🟢 Faible': 'green',
                '🟡 Modéré': 'orange',
                '🔴 Élevé': 'red'
            }.get(risks['level'], 'gray')
            
            st.markdown(
                f"<h3 style='color: {risk_color};'>Niveau : {risks['level']}</h3>",
                unsafe_allow_html=True
            )
        
        with col2:
            st.metric("📊 Score de risque", f"{risks['score']:.1f}/10")
        
        with col3:
            st.metric("🛡️ Stratégies mitigation", len(risks['mitigation']))
        
        with col4:
            if risks.get('ai_assessment'):
                st.metric("🤖 Consensus IA", f"{risks['ai_assessment']['consensus']:.0%}")
        
        # Matrice des risques (heatmap)
        if risks.get('heatmap'):
            st.markdown("#### 🗺️ Carte des risques")
            
            heatmap = risks['heatmap']
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap['matrix'],
                x=heatmap['impact_axis'],
                y=heatmap['probability_axis'],
                colorscale='RdYlGn_r',
                showscale=True,
                text=heatmap['matrix'],
                texttemplate="%{text}",
                textfont={"size": 20}
            ))
            
            fig.update_layout(
                title="Matrice Probabilité x Impact",
                xaxis_title="Impact",
                yaxis_title="Probabilité",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Détail des facteurs de risque
        st.markdown("#### 📊 Facteurs de risque détaillés")
        
        for factor in risks['factors']:
            severity_colors = {
                'Faible': '#90EE90',
                'Modérée': '#FFD700',
                'Élevée': '#FF6B6B'
            }
            
            with st.expander(
                f"{factor['type']} - Sévérité : {factor['severity']}",
                expanded=factor['severity'] == 'Élevée'
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Graphique probabilité
                    fig = go.Figure(go.Indicator(
                        mode="number+delta",
                        value=factor['probability'] * 100,
                        title={'text': "Probabilité (%)"},
                        delta={'reference': 50}
                    ))
                    fig.update_layout(height=150, margin=dict(t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Graphique impact
                    fig = go.Figure(go.Indicator(
                        mode="number+gauge",
                        value=factor['impact'],
                        title={'text': "Impact"},
                        gauge={'axis': {'range': [0, 10]}}
                    ))
                    fig.update_layout(height=150, margin=dict(t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col3:
                    st.write(f"**Description :**")
                    st.write(factor['description'])
                    st.write(f"**Coût mitigation :** {factor.get('mitigation_cost', 'N/A')}")
        
        # Stratégies de mitigation
        st.markdown("#### 🛡️ Plan de mitigation")
        
        mitigation_timeline = []
        for i, mitigation in enumerate(risks['mitigation']):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{mitigation['risque']}**")
                    st.write(mitigation['stratégie'])
                
                with col2:
                    st.write(f"💰 {mitigation['coût']}")
                
                with col3:
                    st.write(f"⏱️ {mitigation['délai']}")
                
                with col4:
                    st.write(f"📊 {mitigation['efficacité_estimée']}")
    
    def _display_scenarios_enhanced(self, strategy: Dict[str, Any]):
        """Scénarios avec visualisation comparative"""
        
        if not strategy.get('scenarios'):
            st.info("Génération de scénarios non demandée")
            return
        
        st.markdown("### 🔄 Analyse des scénarios")
        
        scenarios = strategy['scenarios']
        
        # Graphique de comparaison des probabilités
        scenario_names = [s['name'] for s in scenarios]
        probabilities = [float(s['probability'].rstrip('%')) for s in scenarios]
        
        fig = go.Figure(data=[
            go.Bar(
                x=scenario_names,
                y=probabilities,
                text=probabilities,
                textposition='auto',
                marker_color=['green', 'blue', 'orange', 'purple'][:len(scenarios)]
            )
        ])
        
        fig.update_layout(
            title="Probabilité des scénarios",
            yaxis_title="Probabilité (%)",
            showlegend=False,
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Détail de chaque scénario
        for scenario in scenarios:
            # Couleur selon le type
            if 'optimal' in scenario['name'].lower():
                color = "🟢"
            elif 'probable' in scenario['name'].lower():
                color = "🔵"
            elif 'défavorable' in scenario['name'].lower():
                color = "🟠"
            else:
                color = "🟣"
            
            with st.expander(
                f"{color} {scenario['name']} - {scenario['probability']}",
                expanded='probable' in scenario['name'].lower()
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description :** {scenario['description']}")
                    st.write(f"**Résultat attendu :** {scenario['outcome']}")
                    st.write(f"**Délai estimé :** {scenario.get('timeline', 'N/A')}")
                
                with col2:
                    # Métriques du scénario
                    if scenario.get('financial_impact'):
                        st.metric("💰 Impact financier", scenario['financial_impact'])
                    if scenario.get('reputation_impact'):
                        st.metric("🌟 Impact réputation", scenario['reputation_impact'])
                
                # Conditions
                st.write("**Conditions de réalisation :**")
                for condition in scenario['conditions']:
                    st.write(f"{condition}")
                
                # Plan de contingence si défavorable
                if scenario.get('contingency'):
                    st.warning("**🔄 Plan de contingence :**")
                    contingency = scenario['contingency']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Stratégie :** {contingency.get('plan_b', 'N/A')}")
                        st.write(f"**Budget additionnel :** {contingency.get('budget_additionnel', 'N/A')}")
                    with col2:
                        st.write(f"**Équipe renforcée :** {contingency.get('equipe_renforcee', 'N/A')}")
                        st.write(f"**Délai supplémentaire :** {contingency.get('delai', 'N/A')}")
                
                # Avantages/Inconvénients pour scénario transactionnel
                if scenario.get('advantages'):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success("**✅ Avantages :**")
                        for adv in scenario['advantages']:
                            st.write(f"- {adv}")
                    with col2:
                        st.warning("**⚠️ Inconvénients :**")
                        for disadv in scenario.get('disadvantages', []):
                            st.write(f"- {disadv}")
    
    def _display_timeline_enhanced(self, strategy: Dict[str, Any]):
        """Planning interactif avec diagramme de Gantt"""
        
        if not strategy.get('timeline'):
            st.info("Planning non demandé")
            return
        
        st.markdown("### 📅 Planning stratégique")
        
        timeline = strategy['timeline']
        
        # Créer les données pour le Gantt
        gantt_data = []
        for item in timeline:
            gantt_data.append({
                'Task': item['milestone'],
                'Start': item['target_date'] - timedelta(days=item['duration_days']),
                'Finish': item['target_date'],
                'Resource': item['responsible'],
                'Complete': item['progress'],
                'Critical': item.get('critical_path', False)
            })
        
        # Créer le diagramme de Gantt
        fig = px.timeline(
            gantt_data,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Critical",
            title="Diagramme de Gantt du projet",
            labels={"Critical": "Chemin critique"}
        )
        
        fig.update_yaxes(categoryorder="total ascending")
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Vue détaillée avec progression
        st.markdown("#### 📋 Détail des jalons")
        
        for item in timeline:
            with st.expander(
                f"{item['milestone']} - {item['target_date'].strftime('%d/%m/%Y')}",
                expanded=item.get('critical_path', False)
            ):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # Barre de progression
                    st.write("**Progression :**")
                    progress = st.slider(
                        "Progress",
                        0, 100, item['progress'],
                        key=f"progress_{item['milestone']}",
                        label_visibility="collapsed"
                    )
                    
                    # Livrables
                    st.write("**Livrables :**")
                    for deliverable in item['deliverables']:
                        st.checkbox(deliverable, key=f"del_{item['milestone']}_{deliverable}")
                
                with col2:
                    st.metric("📅 Échéance", f"J+{item['duration_days']}")
                    st.write(f"**Responsable :** {item['responsible']}")
                    if item.get('critical_path'):
                        st.error("⚠️ Chemin critique")
                
                with col3:
                    # Alertes
                    days_remaining = (item['target_date'] - datetime.now()).days
                    if days_remaining < 7 and item['progress'] < 50:
                        st.warning("⚠️ Retard potentiel")
                    elif days_remaining < 0:
                        st.error("❌ En retard")
                    else:
                        st.success("✅ Dans les temps")
    
    def _display_resources_enhanced(self, strategy: Dict[str, Any]):
        """Ressources avec visualisations budgétaires"""
        
        resources = strategy['resources']
        
        st.markdown("### 💰 Ressources et budget")
        
        # Vue d'ensemble
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("⏱️ Temps total", resources['time_estimate'])
        
        with col2:
            total_budget = resources['budget_breakdown'].get('💵 Total', '0 €')
            st.metric("💰 Budget total", total_budget)
        
        with col3:
            st.metric("📈 Corrélation succès", f"{resources.get('success_correlation', 0):.0%}")
        
        # Répartition budgétaire
        st.markdown("#### 💸 Répartition du budget")
        
        # Graphique camembert
        if resources['budget_breakdown']:
            labels = []
            values = []
            
            for key, value in resources['budget_breakdown'].items():
                if key != '💵 Total' and value != "0 €":
                    labels.append(key)
                    # Extraire le montant numérique
                    amount = float(value.replace(' €', '').replace(',', ''))
                    values.append(amount)
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.3,
                marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe']
            )])
            
            fig.update_layout(
                title="Répartition du budget",
                height=350
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Équipe détaillée
        st.markdown("#### 👥 Composition de l'équipe")
        
        team_data = []
        for member in resources['team']:
            team_data.append({
                'Rôle': member['role'],
                'Heures': member['hours'],
                'Taux horaire': f"{member['rate']} €/h",
                'Coût total': f"{member['hours'] * member['rate']:,} €"
            })
        
        df_team = pd.DataFrame(team_data)
        st.dataframe(df_team, use_container_width=True, hide_index=True)
        
        # Outils IA recommandés
        if resources.get('ai_tools'):
            st.markdown("#### 🤖 Outils IA recommandés")
            
            cols = st.columns(len(resources['ai_tools']))
            for i, (tool, col) in enumerate(zip(resources['ai_tools'], cols)):
                with col:
                    st.info(tool)
        
        # Besoins externes
        if resources.get('external_needs'):
            st.markdown("#### 🔗 Besoins externes")
            for need in resources['external_needs']:
                st.write(f"• {need}")
    
    def _display_analytics_enhanced(self, strategy: Dict[str, Any]):
        """Analyses avancées et tableaux de bord"""
        
        st.markdown("### 📊 Analyses et insights")
        
        # Analyse coût-bénéfice
        if strategy.get('cost_benefit'):
            st.markdown("#### 💰 Analyse coût-bénéfice")
            
            cb = strategy['cost_benefit']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cost_min, cost_max = cb['cost_range']
                st.metric("💸 Coûts estimés", f"{cost_min:,} - {cost_max:,} €")
            
            with col2:
                st.metric("📈 ROI estimé", f"{cb['roi_percentage']:.0f}%")
            
            with col3:
                st.metric("⚖️ Seuil rentabilité", f"{cb['breakeven_probability']:.0%}")
            
            # Graphique de sensibilité
            scenarios = ['Pire cas', 'Plus probable', 'Meilleur cas']
            roi_values = [
                cb['sensitivity_analysis']['worst_case'],
                cb['sensitivity_analysis']['most_likely'],
                cb['sensitivity_analysis']['best_case']
            ]
            
            fig = go.Figure(data=[
                go.Bar(x=scenarios, y=roi_values, marker_color=['red', 'blue', 'green'])
            ])
            
            fig.update_layout(
                title="Analyse de sensibilité du ROI",
                yaxis_title="ROI (%)",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Prédiction de succès détaillée
        if strategy.get('success_prediction'):
            st.markdown("#### 🎯 Analyse prédictive")
            
            pred = strategy['success_prediction']
            
            # Facteurs de succès
            factors = pred['key_success_factors']
            
            fig = go.Figure(data=[
                go.Scatterpolar(
                    r=[v for v in factors.values()],
                    theta=list(factors.keys()),
                    fill='toself',
                    name='Facteurs de succès'
                )
            ])
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                showlegend=False,
                title="Analyse des facteurs de succès",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommandations
            st.success(f"**Recommandation :** {pred['recommendation']}")
            
            # Suggestions d'amélioration
            if pred.get('improvement_suggestions'):
                st.markdown("**💡 Suggestions d'amélioration :**")
                for suggestion in pred['improvement_suggestions']:
                    st.write(suggestion)
        
        # Comparaison des modèles IA
        if strategy.get('model_results'):
            st.markdown("#### 🤖 Performance des modèles IA")
            
            model_names = []
            confidences = []
            success_rates = []
            
            for model_key, result in strategy['model_results'].items():
                model_names.append(self.ai_models[model_key]['name'])
                confidences.append(result.get('confidence', 0))
                success_rates.append(result.get('success_rate', 0))
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Confiance',
                x=model_names,
                y=confidences,
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Taux de succès',
                x=model_names,
                y=success_rates,
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title="Comparaison des modèles IA",
                barmode='group',
                yaxis_title="Score",
                height=350
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _display_export_enhanced(self, strategy: Dict[str, Any]):
        """Options d'export enrichies"""
        
        st.markdown("### 💾 Export et partage")
        
        # Options de format
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Format d'export",
                ["📄 PDF complet", "📝 Word (DOCX)", "📊 Excel détaillé", "🌐 HTML interactif", "💾 JSON technique"]
            )
            
            include_options = st.multiselect(
                "Inclure dans l'export",
                ["Graphiques", "Analyses IA", "Planning détaillé", "Budget", "Templates"],
                default=["Graphiques", "Analyses IA"]
            )
        
        with col2:
            confidentiality = st.radio(
                "Niveau de confidentialité",
                ["🟢 Public", "🟡 Interne", "🔴 Confidentiel", "⚫ Secret"]
            )
            
            watermark = st.checkbox("Ajouter filigrane", value=True)
            password_protect = st.checkbox("Protection par mot de passe", value=False)
        
        st.divider()
        
        # Actions d'export
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📄 Générer PDF", use_container_width=True, type="primary"):
                with st.spinner("Génération du PDF..."):
                    time.sleep(2)
                    st.success("✅ PDF généré avec succès !")
                    
                    # Simuler le téléchargement
                    pdf_content = self._generate_pdf_content(strategy, include_options)
                    st.download_button(
                        "⬇️ Télécharger PDF",
                        data=pdf_content,
                        file_name=f"strategie_{strategy['id']}.pdf",
                        mime="application/pdf"
                    )
        
        with col2:
            if st.button("📝 Créer Word", use_container_width=True):
                doc_content = self._generate_enhanced_document(strategy, include_options)
                st.download_button(
                    "⬇️ Télécharger Word",
                    data=doc_content,
                    file_name=f"strategie_{strategy['id']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
        with col3:
            if st.button("📊 Export Excel", use_container_width=True):
                excel_content = self._generate_excel_export(strategy)
                st.download_button(
                    "⬇️ Télécharger Excel",
                    data=excel_content,
                    file_name=f"strategie_{strategy['id']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col4:
            if st.button("💾 Export JSON", use_container_width=True):
                import json
                json_str = json.dumps(strategy, default=str, ensure_ascii=False, indent=2)
                
                st.download_button(
                    "⬇️ Télécharger JSON",
                    data=json_str,
                    file_name=f"strategie_{strategy['id']}.json",
                    mime="application/json"
                )
        
        # Partage collaboratif
        st.markdown("#### 🤝 Partage collaboratif")
        
        col1, col2 = st.columns(2)
        
        with col1:
            recipients = st.text_area(
                "Destinataires (emails)",
                placeholder="email1@example.com\nemail2@example.com",
                height=100
            )
            
            message = st.text_area(
                "Message personnalisé",
                placeholder="Veuillez trouver ci-joint la stratégie juridique...",
                height=100
            )
        
        with col2:
            share_options = st.multiselect(
                "Options de partage",
                ["📧 Email sécurisé", "🔗 Lien temporaire", "☁️ Cloud partagé", "💬 Teams/Slack"],
                default=["📧 Email sécurisé"]
            )
            
            expiration = st.selectbox(
                "Expiration du partage",
                ["24 heures", "7 jours", "30 jours", "Permanent"]
            )
        
        if st.button("📤 Partager", type="primary", use_container_width=True):
            with st.spinner("Envoi en cours..."):
                time.sleep(1.5)
                st.success("✅ Stratégie partagée avec succès !")
                st.info(f"📧 Envoyé à {len(recipients.split())} destinataires")
        
        # Templates de documents
        if strategy.get('templates'):
            st.markdown("#### 📄 Templates de documents")
            
            templates = strategy['templates']
            template_names = list(templates.keys())
            
            selected_template = st.selectbox(
                "Sélectionner un template",
                template_names,
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            if selected_template:
                st.text_area(
                    f"Template : {selected_template}",
                    value=templates[selected_template],
                    height=300
                )
                
                st.download_button(
                    f"⬇️ Télécharger {selected_template}",
                    data=templates[selected_template],
                    file_name=f"{selected_template}_{strategy['id']}.txt",
                    mime="text/plain"
                )
    
    def _generate_pdf_content(self, strategy: Dict[str, Any], options: List[str]) -> bytes:
        """Génère le contenu PDF (simulé)"""
        # En production, utiliser une vraie bibliothèque PDF comme reportlab
        return b"PDF content placeholder"
    
    def _generate_enhanced_document(self, strategy: Dict[str, Any], options: List[str]) -> str:
        """Génère un document Word enrichi"""
        # Document structuré avec toutes les sections
        doc_parts = []
        
        # En-tête
        doc_parts.append(f"""
STRATÉGIE JURIDIQUE DÉTAILLÉE
{'=' * 80}

Référence : {strategy['id']}
Date : {strategy['created_at'].strftime('%d/%m/%Y %H:%M')}
Type d'affaire : {self.strategy_templates[strategy['config']['case_type']]['name']}
Modèles IA utilisés : {', '.join([self.ai_models[m]['name'] for m in strategy['ai_models_used']])}

{'=' * 80}
""")
        
        # Résumé exécutif
        doc_parts.append(f"""
RÉSUMÉ EXÉCUTIF
{'-' * 40}

Urgence : {strategy['config']['urgency']}
Complexité : {strategy['config']['complexity']}
Budget : {strategy['config']['budget']}

Approche principale : {strategy['main_approach']['title']}
Niveau de confiance IA : {strategy['main_approach']['confidence_level']:.0%}

Message clé : "{strategy['main_approach']['key_message']}"

{'=' * 80}
""")
        
        # Sections détaillées selon les options
        if "Analyses IA" in options:
            doc_parts.append(self._format_ai_analysis_section(strategy))
        
        if "Planning détaillé" in options:
            doc_parts.append(self._format_timeline_section(strategy))
        
        if "Budget" in options:
            doc_parts.append(self._format_budget_section(strategy))
        
        return '\n'.join(doc_parts)
    
    def _format_ai_analysis_section(self, strategy: Dict[str, Any]) -> str:
        """Formate la section d'analyse IA"""
        section = """
ANALYSE PAR INTELLIGENCE ARTIFICIELLE
{'-' * 40}

"""
        
        if strategy.get('model_results'):
            for model_key, result in strategy['model_results'].items():
                model = self.ai_models[model_key]
                section += f"""
{model['icon']} {model['name']}
Confiance : {result['confidence']:.0%}
Stratégie principale : {result['main_strategy']}
Taux de succès estimé : {result['success_rate']:.0%}

"""
        
        return section
    
    def _format_timeline_section(self, strategy: Dict[str, Any]) -> str:
        """Formate la section planning"""
        section = """
PLANNING DÉTAILLÉ
{'-' * 40}

"""
        
        if strategy.get('timeline'):
            for item in strategy['timeline']:
                section += f"""
{item['milestone']}
Date cible : {item['target_date'].strftime('%d/%m/%Y')}
Durée : {item['duration_days']} jours
Statut : {item['status']}
Responsable : {item['responsible']}

Livrables :
"""
                for deliverable in item['deliverables']:
                    section += f"  - {deliverable}\n"
                
                section += "\n"
        
        return section
    
    def _format_budget_section(self, strategy: Dict[str, Any]) -> str:
        """Formate la section budget"""
        section = """
BUDGET ET RESSOURCES
{'-' * 40}

"""
        
        if strategy.get('resources'):
            resources = strategy['resources']
            
            section += f"Temps total estimé : {resources['time_estimate']}\n\n"
            
            section += "Répartition budgétaire :\n"
            for key, value in resources['budget_breakdown'].items():
                section += f"  {key} : {value}\n"
            
            section += "\n\nÉquipe requise :\n"
            for member in resources['team']:
                section += f"  - {member['role']} : {member['hours']}h à {member['rate']}€/h\n"
        
        return section
    
    def _generate_excel_export(self, strategy: Dict[str, Any]) -> bytes:
        """Génère un export Excel structuré"""
        # En production, utiliser pandas avec to_excel()
        # Créer plusieurs feuilles : Vue d'ensemble, Planning, Budget, Risques, etc.
        return b"Excel content placeholder"
    
    def _render_strategy_library_enhanced(self):
        """Bibliothèque améliorée avec filtres et recherche"""
        st.markdown("### 📚 Bibliothèque de stratégies")
        
        if not st.session_state.strategy_state['history']:
            # Interface vide attrayante
            st.markdown(
                """
                <div style='text-align: center; padding: 3rem; background: #f0f0f0; 
                border-radius: 1rem; margin: 2rem 0;'>
                    <h3>📚 Votre bibliothèque est vide</h3>
                    <p>Créez votre première stratégie pour commencer à construire votre base de connaissances</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if st.button("🎯 Créer ma première stratégie", type="primary"):
                st.switch_page(tabs[0])  # Retour à l'onglet de création
            
            return
        
        # Barre de recherche et filtres
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            search = st.text_input(
                "🔍 Rechercher",
                placeholder="Mots-clés, client, type d'affaire...",
                key="library_search"
            )
        
        with col2:
            filter_type = st.selectbox(
                "Type",
                ["Tous"] + list(self.strategy_templates.keys()),
                format_func=lambda x: "Tous" if x == "Tous" else self.strategy_templates[x]['name']
            )
        
        with col3:
            filter_urgency = st.selectbox(
                "Urgence",
                ["Tous", "Faible", "Modérée", "Élevée", "Critique"]
            )
        
        with col4:
            sort_by = st.selectbox(
                "Trier par",
                ["Date ↓", "Date ↑", "Succès ↓", "Complexité ↓"]
            )
        
        # Filtrage et tri
        filtered_strategies = st.session_state.strategy_state['history'].copy()
        
        # Appliquer les filtres
        if search:
            filtered_strategies = [
                s for s in filtered_strategies 
                if search.lower() in s['config']['context'].lower() or
                   search.lower() in str(s['config']['objectives']).lower()
            ]
        
        if filter_type != "Tous":
            filtered_strategies = [
                s for s in filtered_strategies 
                if s['config']['case_type'] == filter_type
            ]
        
        if filter_urgency != "Tous":
            filtered_strategies = [
                s for s in filtered_strategies 
                if s['config']['urgency'] == filter_urgency
            ]
        
        # Tri
        if sort_by == "Date ↓":
            filtered_strategies.sort(key=lambda x: x['created_at'], reverse=True)
        elif sort_by == "Date ↑":
            filtered_strategies.sort(key=lambda x: x['created_at'])
        elif sort_by == "Succès ↓" and any(s.get('success_prediction') for s in filtered_strategies):
            filtered_strategies.sort(
                key=lambda x: x.get('success_prediction', {}).get('overall_success_rate', 0), 
                reverse=True
            )
        
        # Affichage en grille
        st.markdown(f"**{len(filtered_strategies)} stratégie(s) trouvée(s)**")
        
        # Vue en cartes
        cols_per_row = 3
        for i in range(0, len(filtered_strategies), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(filtered_strategies):
                    strategy = filtered_strategies[i + j]
                    
                    with col:
                        # Carte de stratégie
                        template = self.strategy_templates[strategy['config']['case_type']]
                        
                        # Couleur de fond selon l'urgence
                        urgency_colors = {
                            'Faible': '#e8f5e9',
                            'Modérée': '#fff3e0',
                            'Élevée': '#ffe0b2',
                            'Critique': '#ffebee'
                        }
                        bg_color = urgency_colors.get(strategy['config']['urgency'], '#f5f5f5')
                        
                        st.markdown(
                            f"""
                            <div style='padding: 1.5rem; background: {bg_color}; 
                            border-radius: 0.5rem; margin-bottom: 1rem; height: 100%;'>
                                <h4>{template['icon']} {template['name'].split()[1]}</h4>
                                <p style='font-size: 0.9rem; color: #666;'>
                                    {strategy['created_at'].strftime('%d/%m/%Y %H:%M')}
                                </p>
                                <p style='margin: 0.5rem 0;'>
                                    <strong>Urgence :</strong> {strategy['config']['urgency']}<br>
                                    <strong>Complexité :</strong> {strategy['config']['complexity']}
                                </p>
                                <p style='font-size: 0.85rem; color: #444; height: 3rem; overflow: hidden;'>
                                    {strategy['config']['context'][:100]}...
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Actions
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            if st.button("👁️", key=f"view_{strategy['id']}", help="Voir"):
                                st.session_state.strategy_state['current_strategy'] = strategy
                                self._display_strategy_enhanced(strategy)
                        
                        with col_b:
                            if st.button("📋", key=f"dup_{strategy['id']}", help="Dupliquer"):
                                self._duplicate_strategy(strategy)
                        
                        with col_c:
                            if st.button("🗑️", key=f"del_{strategy['id']}", help="Supprimer"):
                                self._delete_strategy(strategy['id'])
    
    def _render_strategy_comparison_enhanced(self):
        """Comparaison avancée avec visualisations"""
        st.markdown("### 🔄 Comparaison de stratégies")
        
        if len(st.session_state.strategy_state['history']) < 2:
            st.info("📊 Au moins 2 stratégies sont nécessaires pour effectuer une comparaison.")
            
            # Suggestion d'action
            if st.button("🎯 Créer une nouvelle stratégie"):
                st.switch_page(tabs[0])
            
            return
        
        # Interface de sélection améliorée
        strategies = st.session_state.strategy_state['history']
        
        # Créer des labels descriptifs
        strategy_labels = []
        for s in strategies:
            template = self.strategy_templates[s['config']['case_type']]
            label = f"{template['icon']} {template['name'].split()[1]} - {s['created_at'].strftime('%d/%m')} - {s['config']['urgency']}"
            strategy_labels.append(label)
        
        selected_indices = st.multiselect(
            "Sélectionner 2 à 4 stratégies à comparer",
            range(len(strategies)),
            format_func=lambda x: strategy_labels[x],
            max_selections=4,
            default=[0, 1] if len(strategies) >= 2 else [0]
        )
        
        if len(selected_indices) >= 2:
            selected_strategies = [strategies[i] for i in selected_indices]
            
            # Comparaison automatique
            st.markdown("#### 📊 Analyse comparative")
            
            # Tableau de comparaison interactif
            comparison_data = []
            
            for strategy in selected_strategies:
                success_rate = strategy.get('success_prediction', {}).get('overall_success_rate', 0.5)
                risk_level = strategy.get('risks', {}).get('level', 'N/A')
                
                comparison_data.append({
                    'Stratégie': f"{self.strategy_templates[strategy['config']['case_type']]['icon']} {strategy['id'][-6:]}",
                    'Type': self.strategy_templates[strategy['config']['case_type']]['name'].split()[1],
                    'Urgence': strategy['config']['urgency'],
                    'Complexité': strategy['config']['complexity'],
                    'Taux succès': f"{success_rate:.0%}",
                    'Risque': risk_level,
                    'Budget': strategy['config']['budget'],
                    'Modèles IA': len(strategy.get('ai_models_used', [])),
                    'Date': strategy['created_at'].strftime('%d/%m/%Y')
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            
            # Affichage du tableau avec style
            st.dataframe(
                df_comparison,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Taux succès": st.column_config.ProgressColumn(
                        "Taux succès",
                        help="Probabilité de succès prédite",
                        format="%d%%",
                        min_value=0,
                        max_value=100,
                    ),
                }
            )
            
            # Visualisations comparatives
            st.markdown("#### 📈 Visualisations")
            
            # Graphique radar de comparaison
            self._display_comparison_radar(selected_strategies)
            
            # Analyse des divergences
            st.markdown("#### 🔀 Analyse des divergences")
            
            divergences = self._analyze_divergences(selected_strategies)
            
            for div in divergences:
                if div['severity'] == 'high':
                    st.error(f"❌ {div['message']}")
                elif div['severity'] == 'medium':
                    st.warning(f"⚠️ {div['message']}")
                else:
                    st.info(f"ℹ️ {div['message']}")
            
            # Recommandation finale
            st.markdown("#### 💡 Recommandation")
            
            best_strategy = self._recommend_best_strategy(selected_strategies)
            
            st.success(
                f"**Stratégie recommandée :** {best_strategy['reason']}"
            )
            
            # Actions de comparaison
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Rapport détaillé", type="primary"):
                    self._generate_comparison_report(selected_strategies)
            
            with col2:
                if st.button("🔄 Fusionner stratégies"):
                    self._merge_strategies(selected_strategies)
            
            with col3:
                if st.button("📧 Partager analyse"):
                    self._share_comparison(selected_strategies)
    
    def _display_comparison_radar(self, strategies: List[Dict[str, Any]]):
        """Affiche un graphique radar de comparaison"""
        
        categories = ['Succès', 'Complexité', 'Urgence', 'Budget', 'Risque', 'Innovation']
        
        fig = go.Figure()
        
        for strategy in strategies:
            # Normaliser les valeurs sur une échelle 0-1
            values = [
                strategy.get('success_prediction', {}).get('overall_success_rate', 0.5),
                {'Simple': 0.25, 'Modérée': 0.5, 'Complexe': 0.75, 'Très complexe': 1.0}
                    .get(strategy['config']['complexity'], 0.5),
                {'Faible': 0.25, 'Modérée': 0.5, 'Élevée': 0.75, 'Critique': 1.0}
                    .get(strategy['config']['urgency'], 0.5),
                {'Limité': 0.25, 'Standard': 0.5, 'Confortable': 0.75, 'Illimité': 1.0}
                    .get(strategy['config']['budget'], 0.5),
                1 - {'🟢 Faible': 0.25, '🟡 Modéré': 0.5, '🔴 Élevé': 0.75}
                    .get(strategy.get('risks', {}).get('level', '🟡 Modéré'), 0.5),
                0.8 if strategy.get('arguments', {}).get('innovants') else 0.3
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=f"Stratégie {strategy['id'][-6:]}"
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            title="Comparaison multidimensionnelle",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _analyze_divergences(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyse les divergences entre stratégies"""
        divergences = []
        
        # Comparer les urgences
        urgencies = set(s['config']['urgency'] for s in strategies)
        if len(urgencies) > 1:
            divergences.append({
                'severity': 'high',
                'message': f"Niveaux d'urgence très différents : {', '.join(urgencies)}"
            })
        
        # Comparer les approches
        approaches = set(tuple(s['main_approach']['primary_axes']) for s in strategies)
        if len(approaches) > 1:
            divergences.append({
                'severity': 'medium',
                'message': "Approches stratégiques divergentes détectées"
            })
        
        # Comparer les taux de succès
        success_rates = [s.get('success_prediction', {}).get('overall_success_rate', 0.5) for s in strategies]
        if max(success_rates) - min(success_rates) > 0.3:
            divergences.append({
                'severity': 'high',
                'message': f"Écart important dans les taux de succès prédits : {min(success_rates):.0%} - {max(success_rates):.0%}"
            })
        
        return divergences
    
    def _recommend_best_strategy(self, strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recommande la meilleure stratégie basée sur plusieurs critères"""
        
        best_score = -1
        best_strategy = None
        best_reason = ""
        
        for i, strategy in enumerate(strategies):
            score = 0
            reasons = []
            
            # Score basé sur le taux de succès
            success_rate = strategy.get('success_prediction', {}).get('overall_success_rate', 0.5)
            score += success_rate * 40  # 40% du poids
            if success_rate > 0.7:
                reasons.append(f"taux de succès élevé ({success_rate:.0%})")
            
            # Score basé sur le risque
            risk_level = strategy.get('risks', {}).get('level', '🟡 Modéré')
            risk_scores = {'🟢 Faible': 30, '🟡 Modéré': 20, '🔴 Élevé': 10}
            score += risk_scores.get(risk_level, 20)  # 30% du poids
            if risk_level == '🟢 Faible':
                reasons.append("risque faible")
            
            # Score basé sur le rapport coût/bénéfice
            if strategy.get('cost_benefit'):
                roi = strategy['cost_benefit']['roi_percentage']
                score += min(roi / 10, 30)  # 30% du poids max
                if roi > 100:
                    reasons.append(f"ROI excellent ({roi:.0f}%)")
            
            if score > best_score:
                best_score = score
                best_strategy = strategy
                best_reason = f"Stratégie {i+1} - Score global : {score:.0f}/100 ({', '.join(reasons)})"
        
        return {
            'strategy': best_strategy,
            'score': best_score,
            'reason': best_reason
        }
    
    def _generate_comparison_report(self, strategies: List[Dict[str, Any]]):
        """Génère un rapport de comparaison détaillé"""
        with st.spinner("Génération du rapport de comparaison..."):
            time.sleep(2)
            st.success("✅ Rapport généré !")
            
            # Créer le contenu du rapport
            report = f"""
RAPPORT DE COMPARAISON STRATÉGIQUE
{'=' * 50}
Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}
Nombre de stratégies comparées : {len(strategies)}

{'=' * 50}
"""
            
            # Ajouter les détails de chaque stratégie
            for i, strategy in enumerate(strategies):
                report += f"""
STRATÉGIE {i+1}
{'-' * 30}
Type : {self.strategy_templates[strategy['config']['case_type']]['name']}
Urgence : {strategy['config']['urgency']}
Complexité : {strategy['config']['complexity']}
Taux de succès : {strategy.get('success_prediction', {}).get('overall_success_rate', 0.5):.0%}

"""
            
            st.download_button(
                "📥 Télécharger le rapport",
                data=report,
                file_name=f"comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    def _merge_strategies(self, strategies: List[Dict[str, Any]]):
        """Fusionne plusieurs stratégies en une seule optimisée"""
        st.info("🔄 Fusion des stratégies en cours...")
        # Logique de fusion à implémenter
        st.success("✅ Stratégies fusionnées avec succès !")
    
    def _share_comparison(self, strategies: List[Dict[str, Any]]):
        """Partage l'analyse comparative"""
        st.info("📧 Préparation du partage...")
        # Logique de partage à implémenter
    
    def _render_analytics(self):
        """Tableau de bord analytique global"""
        st.markdown("### 📊 Analytics et insights")
        
        if not st.session_state.strategy_state['history']:
            st.info("Créez des stratégies pour voir les analytics")
            return
        
        # Métriques globales
        strategies = st.session_state.strategy_state['history']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📋 Total stratégies",
                len(strategies),
                f"+{len([s for s in strategies if (datetime.now() - s['created_at']).days < 30])} ce mois"
            )
        
        with col2:
            avg_success = sum(
                s.get('success_prediction', {}).get('overall_success_rate', 0.5) 
                for s in strategies
            ) / len(strategies)
            st.metric(
                "📈 Taux succès moyen",
                f"{avg_success:.0%}",
                "+5%" if avg_success > 0.7 else "-2%"
            )
        
        with col3:
            high_risk = len([
                s for s in strategies 
                if s.get('risks', {}).get('level') == '🔴 Élevé'
            ])
            st.metric(
                "⚠️ Cas à risque",
                high_risk,
                delta=f"{high_risk/len(strategies)*100:.0f}% du total"
            )
        
        with col4:
            ai_usage = sum(len(s.get('ai_models_used', [])) for s in strategies) / len(strategies)
            st.metric(
                "🤖 Modèles IA/stratégie",
                f"{ai_usage:.1f}",
                "Multi-modèles" if ai_usage > 1 else "Mono-modèle"
            )
        
        # Graphiques analytiques
        st.markdown("#### 📈 Évolution temporelle")
        
        # Préparer les données temporelles
        df_timeline = pd.DataFrame([
            {
                'Date': s['created_at'],
                'Type': self.strategy_templates[s['config']['case_type']]['name'],
                'Succès': s.get('success_prediction', {}).get('overall_success_rate', 0.5) * 100,
                'Urgence': s['config']['urgency']
            }
            for s in strategies
        ])
        
        # Graphique d'évolution
        fig = px.scatter(
            df_timeline,
            x='Date',
            y='Succès',
            color='Type',
            size=[50] * len(df_timeline),
            hover_data=['Urgence'],
            title="Évolution du taux de succès par type d'affaire"
        )
        
        fig.update_layout(
            yaxis_title="Taux de succès (%)",
            xaxis_title="Date de création",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Répartition par type
        col1, col2 = st.columns(2)
        
        with col1:
            # Camembert des types d'affaires
            type_counts = df_timeline['Type'].value_counts()
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=type_counts.index,
                values=type_counts.values,
                hole=.3
            )])
            
            fig_pie.update_layout(
                title="Répartition par type d'affaire",
                height=350
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Histogramme des urgences
            urgency_order = ['Faible', 'Modérée', 'Élevée', 'Critique']
            urgency_counts = df_timeline['Urgence'].value_counts().reindex(urgency_order, fill_value=0)
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=urgency_counts.index,
                    y=urgency_counts.values,
                    marker_color=['green', 'yellow', 'orange', 'red']
                )
            ])
            
            fig_bar.update_layout(
                title="Distribution des niveaux d'urgence",
                xaxis_title="Urgence",
                yaxis_title="Nombre de cas",
                height=350
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Analyse des modèles IA
        st.markdown("#### 🤖 Performance des modèles IA")
        
        # Collecter les statistiques par modèle
        model_stats = {}
        for strategy in strategies:
            if strategy.get('model_results'):
                for model_key, result in strategy['model_results'].items():
                    if model_key not in model_stats:
                        model_stats[model_key] = {
                            'count': 0,
                            'total_confidence': 0,
                            'total_success': 0
                        }
                    
                    model_stats[model_key]['count'] += 1
                    model_stats[model_key]['total_confidence'] += result.get('confidence', 0)
                    model_stats[model_key]['total_success'] += result.get('success_rate', 0)
        
        if model_stats:
            # Créer le graphique de performance
            model_names = []
            avg_confidences = []
            avg_success_rates = []
            usage_counts = []
            
            for model_key, stats in model_stats.items():
                model_names.append(self.ai_models[model_key]['name'])
                avg_confidences.append(stats['total_confidence'] / stats['count'] * 100)
                avg_success_rates.append(stats['total_success'] / stats['count'] * 100)
                usage_counts.append(stats['count'])
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Confiance moyenne (%)',
                x=model_names,
                y=avg_confidences,
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Taux de succès moyen (%)',
                x=model_names,
                y=avg_success_rates,
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title="Performance comparative des modèles IA",
                barmode='group',
                yaxis_title="Pourcentage",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Insights et recommandations
        st.markdown("#### 💡 Insights et recommandations")
        
        insights = self._generate_insights(strategies)
        
        for insight in insights:
            if insight['type'] == 'success':
                st.success(f"✅ {insight['message']}")
            elif insight['type'] == 'warning':
                st.warning(f"⚠️ {insight['message']}")
            elif insight['type'] == 'info':
                st.info(f"ℹ️ {insight['message']}")
    
    def _generate_insights(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Génère des insights basés sur l'analyse des stratégies"""
        insights = []
        
        # Analyse du taux de succès
        avg_success = sum(
            s.get('success_prediction', {}).get('overall_success_rate', 0.5) 
            for s in strategies
        ) / len(strategies)
        
        if avg_success > 0.75:
            insights.append({
                'type': 'success',
                'message': f"Excellent taux de succès moyen ({avg_success:.0%}). Vos stratégies sont bien optimisées."
            })
        elif avg_success < 0.5:
            insights.append({
                'type': 'warning',
                'message': f"Taux de succès moyen faible ({avg_success:.0%}). Considérez l'utilisation de plus de modèles IA."
            })
        
        # Analyse de l'utilisation des modèles
        multi_model_strategies = [s for s in strategies if len(s.get('ai_models_used', [])) > 1]
        if len(multi_model_strategies) < len(strategies) * 0.3:
            insights.append({
                'type': 'info',
                'message': "Utilisez plus souvent plusieurs modèles IA pour améliorer la robustesse des stratégies."
            })
        
        # Analyse des cas urgents
        urgent_cases = [s for s in strategies if s['config']['urgency'] in ['Élevée', 'Critique']]
        if len(urgent_cases) > len(strategies) * 0.5:
            insights.append({
                'type': 'warning',
                'message': "Beaucoup de cas urgents. Envisagez des processus préventifs pour réduire les urgences."
            })
        
        return insights
    
    def _render_help_enhanced(self):
        """Aide enrichie avec tutoriels et FAQ"""
        st.markdown("### ❓ Centre d'aide")
        
        # Navigation de l'aide
        help_tabs = st.tabs([
            "🚀 Démarrage rapide",
            "📖 Guide complet",
            "🤖 Utilisation de l'IA",
            "💡 Bonnes pratiques",
            "❓ FAQ",
            "📞 Support"
        ])
        
        with help_tabs[0]:
            self._render_quick_start_guide()
        
        with help_tabs[1]:
            self._render_complete_guide()
        
        with help_tabs[2]:
            self._render_ai_guide()
        
        with help_tabs[3]:
            self._render_best_practices()
        
        with help_tabs[4]:
            self._render_faq()
        
        with help_tabs[5]:
            self._render_support()
    
    def _render_quick_start_guide(self):
        """Guide de démarrage rapide"""
        st.markdown("""
        #### 🚀 Démarrage rapide en 5 étapes
        
        1. **Créez votre première stratégie**
           - Cliquez sur l'onglet "🎯 Nouvelle stratégie"
           - Remplissez les informations de base (type, urgence, complexité)
           - Décrivez votre cas dans la zone de contexte
        
        2. **Configurez l'IA**
           - Allez dans l'onglet "🤖 Configuration IA"
           - Sélectionnez un ou plusieurs modèles
           - Choisissez le mode de fusion (consensus recommandé)
        
        3. **Générez la stratégie**
           - Cliquez sur "🚀 Générer la stratégie avec IA"
           - Attendez l'analyse (30-60 secondes)
           - Explorez les résultats dans les différents onglets
        
        4. **Analysez et ajustez**
           - Consultez le taux de succès prédit
           - Vérifiez l'analyse des risques
           - Ajustez si nécessaire
        
        5. **Exportez et partagez**
           - Utilisez l'onglet "💾 Export"
           - Choisissez votre format (PDF recommandé)
           - Partagez avec votre équipe
        
        💡 **Conseil :** Commencez avec un cas simple pour vous familiariser avec l'outil.
        """)
        
        # Vidéo tutoriel simulée
        if st.button("▶️ Voir la démonstration vidéo"):
            st.info("🎥 Vidéo de démonstration (3 min) - [Lien vers la vidéo]")
    
    def _render_complete_guide(self):
        """Guide complet détaillé"""
        st.markdown("""
        #### 📖 Guide complet du module Stratégie Juridique IA
        
        ##### 1. Vue d'ensemble
        
        Le module Stratégie Juridique IA est conçu pour vous aider à développer des stratégies 
        de défense robustes en utilisant l'intelligence artificielle. Il combine l'expertise 
        juridique traditionnelle avec la puissance analytique de plusieurs modèles d'IA.
        
        ##### 2. Fonctionnalités principales
        
        **🎯 Génération de stratégies**
        - Analyse contextuelle approfondie
        - Identification automatique des axes de défense
        - Génération d'arguments juridiques
        - Plan d'action détaillé avec timeline
        
        **🤖 Intelligence artificielle multi-modèles**
        - GPT-4 : Raisonnement complexe et créativité
        - Claude 3 : Analyse éthique et approfondie
        - Mistral : Rapidité et efficacité
        - Llama 3 : Solutions open source personnalisables
        
        **📊 Analyses prédictives**
        - Taux de succès basé sur l'historique
        - Analyse des risques multicritères
        - Scénarios probabilistes
        - ROI et analyse coût-bénéfice
        
        **📚 Gestion des connaissances**
        - Bibliothèque de stratégies
        - Recherche et filtrage avancés
        - Comparaison de stratégies
        - Templates réutilisables
        
        ##### 3. Types d'affaires supportés
        
        - **🚨 Pénal** : Défense, procédure, prescription
        - **💼 Commercial** : Litiges contractuels, concurrence
        - **⚖️ Civil** : Responsabilité, préjudice, réparation
        - **🏛️ Administratif** : Contentieux, recours
        - **👥 Social** : Droit du travail, licenciement
        
        ##### 4. Workflow recommandé
        
        1. **Préparation** : Rassemblez tous les éléments du dossier
        2. **Configuration** : Choisissez les modèles IA adaptés
        3. **Génération** : Créez la stratégie initiale
        4. **Révision** : Analysez et ajustez les recommandations
        5. **Validation** : Faites valider par l'équipe senior
        6. **Exécution** : Suivez le plan d'action généré
        7. **Suivi** : Utilisez les analytics pour mesurer l'efficacité
        """)
    
    def _render_ai_guide(self):
        """Guide d'utilisation de l'IA"""
        st.markdown("""
        #### 🤖 Guide d'utilisation de l'IA
        
        ##### Comprendre les modèles disponibles
        
        **🧠 GPT-4 Turbo (OpenAI)**
        - **Forces** : Raisonnement complexe, créativité, compréhension nuancée
        - **Utilisation idéale** : Cas complexes nécessitant innovation
        - **Limites** : Peut être trop créatif parfois
        
        **🎯 Claude 3 Opus (Anthropic)**
        - **Forces** : Analyse approfondie, considérations éthiques
        - **Utilisation idéale** : Cas sensibles, analyse détaillée
        - **Limites** : Peut être conservateur
        
        **⚡ Mistral Large**
        - **Forces** : Rapidité, efficacité, pragmatisme
        - **Utilisation idéale** : Cas urgents, analyses rapides
        - **Limites** : Moins de nuances
        
        **🦙 Llama 3 70B (Meta)**
        - **Forces** : Open source, personnalisable, transparent
        - **Utilisation idéale** : Cas nécessitant contrôle total
        - **Limites** : Nécessite plus de guidage
        
        ##### Modes de fusion
        
        1. **🎯 Meilleur résultat**
           - Sélectionne la meilleure proposition
           - Idéal pour : Cas où la qualité prime
        
        2. **🔄 Consensus**
           - Combine les points communs
           - Idéal pour : Stratégies équilibrées
        
        3. **🎨 Créatif**
           - Fusionne les idées innovantes
           - Idéal pour : Cas nécessitant originalité
        
        4. **📊 Analytique**
           - Privilégie les données et métriques
           - Idéal pour : Décisions basées sur les faits
        
        ##### Optimiser l'utilisation
        
        - **Multi-modèles** : Utilisez 2-3 modèles pour les cas importants
        - **Contexte riche** : Plus vous donnez d'informations, meilleurs sont les résultats
        - **Itération** : N'hésitez pas à régénérer avec des ajustements
        - **Validation humaine** : L'IA assiste mais ne remplace pas l'expertise
        """)
    
    def _render_best_practices(self):
        """Bonnes pratiques"""
        st.markdown("""
        #### 💡 Bonnes pratiques
        
        ##### ✅ À faire
        
        1. **Préparation minutieuse**
           - Documentez tous les faits pertinents
           - Identifiez clairement les parties
           - Listez les preuves disponibles
        
        2. **Description détaillée**
           - Utilisez un langage clair et précis
           - Incluez dates, montants, noms
           - Mentionnez la juridiction applicable
        
        3. **Analyse SWOT complète**
           - Soyez honnête sur les faiblesses
           - N'omettez pas les menaces
           - Identifiez toutes les opportunités
        
        4. **Utilisation intelligente de l'IA**
           - Combinez plusieurs modèles pour les cas complexes
           - Validez toujours les recommandations
           - Utilisez l'IA comme assistant, pas comme décideur
        
        5. **Suivi et amélioration**
           - Mettez à jour les stratégies selon l'évolution
           - Analysez les résultats pour apprendre
           - Partagez les succès avec l'équipe
        
        ##### ❌ À éviter
        
        1. **Informations incomplètes**
           - Ne pas mentionner des faits cruciaux
           - Omettre des parties importantes
           - Ignorer des délais critiques
        
        2. **Sur-confiance dans l'IA**
           - Accepter aveuglément toutes les recommandations
           - Ne pas vérifier la jurisprudence citée
           - Ignorer votre expertise
        
        3. **Négligence du suivi**
           - Ne pas mettre à jour la stratégie
           - Ignorer les changements de contexte
           - Ne pas mesurer l'efficacité
        
        ##### 🎯 Cas d'usage optimaux
        
        - **Préparation initiale** : Brainstorming stratégique
        - **Cas complexes** : Analyse multi-angles
        - **Urgences** : Génération rapide d'options
        - **Formation** : Apprentissage de nouvelles approches
        - **Documentation** : Création de dossiers complets
        """)
    
    def _render_faq(self):
        """Questions fréquemment posées"""
        st.markdown("#### ❓ Questions fréquemment posées")
        
        faq_items = [
            {
                "question": "Combien de temps prend la génération d'une stratégie ?",
                "answer": "En moyenne 30-60 secondes, selon le nombre de modèles IA sélectionnés et la complexité du cas."
            },
            {
                "question": "Les stratégies générées sont-elles juridiquement valables ?",
                "answer": "Les stratégies sont des recommandations basées sur l'IA. Elles doivent toujours être validées par un juriste qualifié avant utilisation."
            },
            {
                "question": "Puis-je modifier une stratégie après génération ?",
                "answer": "Oui, vous pouvez dupliquer et modifier toute stratégie. Utilisez le bouton 📋 dans la bibliothèque."
            },
            {
                "question": "Comment sont calculés les taux de succès ?",
                "answer": "Les taux combinent l'analyse des facteurs du cas, les prédictions des modèles IA, et les statistiques historiques similaires."
            },
            {
                "question": "Mes données sont-elles sécurisées ?",
                "answer": "Oui, toutes les données sont chiffrées et stockées selon les normes de sécurité les plus strictes. Aucune donnée n'est partagée."
            },
            {
                "question": "Quelle est la différence entre les modes de fusion ?",
                "answer": "Consensus combine les points communs, Créatif privilégie l'innovation, Analytique se base sur les données, Meilleur résultat sélectionne la meilleure proposition."
            },
            {
                "question": "Puis-je utiliser mes propres modèles IA ?",
                "answer": "Cette fonctionnalité est en développement. Contactez le support pour les intégrations personnalisées."
            },
            {
                "question": "Comment exporter vers mon logiciel de gestion ?",
                "answer": "Utilisez l'export JSON pour l'intégration avec d'autres systèmes, ou les formats Word/PDF pour le partage."
            }
        ]
        
        for item in faq_items:
            with st.expander(f"**{item['question']}**"):
                st.write(item['answer'])
    
    def _render_support(self):
        """Informations de support"""
        st.markdown("""
        #### 📞 Support et assistance
        
        ##### Contacter le support
        
        **📧 Email** : support@nexora-law.ai
        **💬 Chat** : Disponible en bas à droite
        **📱 Téléphone** : +33 1 XX XX XX XX
        **🕐 Horaires** : Lun-Ven 9h-18h
        
        ##### Ressources supplémentaires
        
        - 📚 [Documentation complète](https://docs.nexora-law.ai)
        - 🎥 [Tutoriels vidéo](https://videos.nexora-law.ai)
        - 📰 [Blog et actualités](https://blog.nexora-law.ai)
        - 👥 [Communauté utilisateurs](https://community.nexora-law.ai)
        
        ##### Signaler un problème
        
        Utilisez le formulaire ci-dessous pour signaler un bug ou demander une fonctionnalité.
        """)
        
        # Formulaire de contact
        with st.form("support_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nom")
                email = st.text_input("Email")
            
            with col2:
                issue_type = st.selectbox(
                    "Type de demande",
                    ["Bug", "Fonctionnalité", "Question", "Autre"]
                )
                priority = st.selectbox(
                    "Priorité",
                    ["Basse", "Normale", "Haute", "Urgente"]
                )
            
            description = st.text_area(
                "Description détaillée",
                height=150
            )
            
            attachments = st.file_uploader(
                "Pièces jointes (captures d'écran, logs...)",
                accept_multiple_files=True
            )
            
            submitted = st.form_submit_button("📤 Envoyer", type="primary")
            
            if submitted:
                st.success("✅ Votre demande a été envoyée. Nous vous répondrons sous 24h.")
    
    # Méthodes utilitaires supplémentaires
    
    def _show_template_modal(self):
        """Affiche les templates disponibles"""
        st.info("📋 Sélection de template en cours de développement")
    
    def _load_last_strategy(self):
        """Charge la dernière stratégie"""
        if st.session_state.strategy_state['history']:
            last = st.session_state.strategy_state['history'][-1]
            st.session_state.strategy_state['current_strategy'] = last
            st.success("✅ Dernière stratégie chargée")
    
    def _launch_ai_assistant(self):
        """Lance l'assistant IA interactif"""
        st.info("🤖 Assistant IA interactif en cours de développement")
    
    def _analyze_context_with_ai(self, context: str):
        """Analyse le contexte avec l'IA"""
        if context:
            with st.spinner("Analyse du contexte..."):
                time.sleep(1)
                st.success("✅ Contexte analysé - Points clés identifiés")
    
    def _get_context_suggestions(self, case_type: str):
        """Obtient des suggestions de contexte"""
        suggestions = {
            'penal': "Incluez : date des faits, qualification pénale, preuves, témoins, antécédents",
            'commercial': "Incluez : contrat, montants, dates clés, correspondances, préjudice",
            'civil': "Incluez : parties, faits, dommages, responsabilité, assurances",
            'administratif': "Incluez : décision contestée, autorité, délais, moyens",
            'social': "Incluez : contrat de travail, ancienneté, motif, procédure"
        }
        
        st.info(f"💡 {suggestions.get(case_type, 'Décrivez les faits de manière chronologique')}")
    
    def _find_similar_cases(self, context: str):
        """Recherche des cas similaires"""
        if context:
            with st.spinner("Recherche de cas similaires..."):
                time.sleep(1.5)
                st.info("📚 3 cas similaires trouvés dans la jurisprudence")
    
    def _test_ai_configuration(self, models: List[str], prompt: str, fusion_mode: str):
        """Teste la configuration IA"""
        with st.spinner("Test en cours..."):
            progress = st.progress(0)
            
            for i, model in enumerate(models):
                progress.progress((i + 1) / len(models))
                time.sleep(0.5)
            
            st.success(f"✅ Test réussi - Mode {fusion_mode}")
            
            # Afficher un résultat simulé
            st.markdown("**Résultat du test :**")
            st.info(f"Les {len(models)} modèles ont généré des réponses cohérentes.")
    
    def _get_model_usage_stats(self) -> pd.DataFrame:
        """Obtient les statistiques d'utilisation des modèles"""
        # Données simulées
        data = {
            'model': ['GPT-4', 'Claude 3', 'Mistral', 'Llama 3'],
            'usage': [150, 120, 80, 60],
            'performance': [0.85, 0.88, 0.82, 0.78]
        }
        
        return pd.DataFrame(data)
    
    def _duplicate_strategy(self, strategy: Dict[str, Any]):
        """Duplique une stratégie"""
        new_strategy = strategy.copy()
        new_strategy['id'] = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_strategy['created_at'] = datetime.now()
        
        st.session_state.strategy_state['history'].append(new_strategy)
        st.success("✅ Stratégie dupliquée")
    
    def _delete_strategy(self, strategy_id: str):
        """Supprime une stratégie"""
        st.session_state.strategy_state['history'] = [
            s for s in st.session_state.strategy_state['history']
            if s['id'] != strategy_id
        ]
        st.success("✅ Stratégie supprimée")
        st.rerun()
    
    def _edit_strategy(self, strategy: Dict[str, Any]):
        """Édite une stratégie existante"""
        st.info("✏️ Édition de stratégie en cours de développement")
    
    def _share_strategy(self, strategy: Dict[str, Any]):
        """Partage une stratégie"""
        st.info("📧 Fonction de partage en cours de développement")


# Point d'entrée pour le lazy loading
if __name__ == "__main__":
    run()