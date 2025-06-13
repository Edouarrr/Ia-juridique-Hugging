"""Module de stratégie juridique avec IA"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StrategyModule:
    """Module de génération de stratégies juridiques"""
    
    def __init__(self):
        self.name = "Stratégie juridique"
        self.description = "Développez des stratégies de défense intelligentes avec l'aide de l'IA"
        self.icon = "⚖️"
        self.available = True
        
        # Templates de stratégies
        self.strategy_templates = {
            'penal': {
                'name': 'Défense pénale',
                'axes': ['Contestation procédure', 'Absence d\'intention', 'Légitime défense', 'Prescription'],
                'focus': 'innocence et respect de la procédure'
            },
            'commercial': {
                'name': 'Litige commercial',
                'axes': ['Inexécution contractuelle', 'Force majeure', 'Vice caché', 'Bonne foi'],
                'focus': 'respect des obligations contractuelles'
            },
            'civil': {
                'name': 'Affaire civile',
                'axes': ['Responsabilité', 'Préjudice', 'Causalité', 'Réparation'],
                'focus': 'établissement du préjudice et de la responsabilité'
            },
            'administratif': {
                'name': 'Contentieux administratif',
                'axes': ['Excès de pouvoir', 'Illégalité', 'Détournement', 'Incompétence'],
                'focus': 'légalité des décisions administratives'
            }
        }
    
    def render(self):
        """Interface principale du module"""
        st.markdown(f"### {self.icon} {self.name}")
        st.markdown(f"*{self.description}*")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Nouvelle stratégie",
            "📚 Bibliothèque",
            "🔄 Comparaison",
            "❓ Aide"
        ])
        
        with tab1:
            self._render_new_strategy()
        
        with tab2:
            self._render_strategy_library()
        
        with tab3:
            self._render_strategy_comparison()
        
        with tab4:
            self._render_help()
    
    def _render_new_strategy(self):
        """Interface de création de stratégie"""
        
        # Type d'affaire
        col1, col2 = st.columns(2)
        
        with col1:
            case_type = st.selectbox(
                "Type d'affaire",
                list(self.strategy_templates.keys()),
                format_func=lambda x: self.strategy_templates[x]['name']
            )
            
            urgency = st.select_slider(
                "Urgence",
                ["Faible", "Modérée", "Élevée", "Critique"],
                value="Modérée"
            )
        
        with col2:
            complexity = st.select_slider(
                "Complexité",
                ["Simple", "Modérée", "Complexe", "Très complexe"],
                value="Modérée"
            )
            
            budget = st.selectbox(
                "Budget",
                ["Limité", "Standard", "Confortable", "Illimité"],
                help="Impact sur la profondeur de la stratégie"
            )
        
        # Contexte de l'affaire
        st.markdown("#### 📋 Contexte de l'affaire")
        
        context = st.text_area(
            "Description du cas",
            placeholder="Décrivez brièvement les faits, les parties impliquées, et les enjeux...",
            height=150
        )
        
        # Points clés
        col1, col2 = st.columns(2)
        
        with col1:
            strengths = st.text_area(
                "💪 Points forts",
                placeholder="- Preuves favorables\n- Témoignages\n- Précédents",
                height=100
            )
        
        with col2:
            weaknesses = st.text_area(
                "⚠️ Points faibles",
                placeholder="- Éléments défavorables\n- Contradictions\n- Risques",
                height=100
            )
        
        # Objectifs
        st.markdown("#### 🎯 Objectifs")
        
        objectives = st.multiselect(
            "Objectifs prioritaires",
            [
                "Acquittement/Relaxe",
                "Réduction des charges",
                "Négociation amiable",
                "Minimisation des dommages",
                "Gain de temps",
                "Précédent juridique",
                "Protection réputation"
            ],
            default=["Acquittement/Relaxe"]
        )
        
        # Configuration avancée
        with st.expander("⚙️ Configuration avancée", expanded=False):
            include_jurisprudence = st.checkbox("Inclure recherche jurisprudence", value=True)
            include_scenarios = st.checkbox("Générer scénarios alternatifs", value=True)
            include_timeline = st.checkbox("Créer planning d'actions", value=True)
            risk_assessment = st.checkbox("Analyse des risques détaillée", value=True)
        
        # Génération
        if st.button("🚀 Générer la stratégie", type="primary", use_container_width=True):
            if context:
                config = {
                    'case_type': case_type,
                    'urgency': urgency,
                    'complexity': complexity,
                    'budget': budget,
                    'context': context,
                    'strengths': strengths,
                    'weaknesses': weaknesses,
                    'objectives': objectives,
                    'include_jurisprudence': include_jurisprudence,
                    'include_scenarios': include_scenarios,
                    'include_timeline': include_timeline,
                    'risk_assessment': risk_assessment
                }
                
                self._generate_strategy(config)
            else:
                st.warning("Veuillez décrire le contexte de l'affaire")
    
    def _generate_strategy(self, config: Dict[str, Any]):
        """Génère une stratégie juridique"""
        
        with st.spinner("Génération de la stratégie en cours..."):
            # Simuler la génération
            strategy = {
                'id': f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.now(),
                'config': config,
                'main_approach': self._generate_main_approach(config),
                'action_plan': self._generate_action_plan(config),
                'arguments': self._generate_arguments(config),
                'risks': self._assess_risks(config) if config['risk_assessment'] else None,
                'scenarios': self._generate_scenarios(config) if config['include_scenarios'] else None,
                'timeline': self._generate_timeline(config) if config['include_timeline'] else None,
                'resources': self._estimate_resources(config)
            }
            
            # Sauvegarder
            if 'strategy_history' not in st.session_state:
                st.session_state.strategy_history = []
            st.session_state.strategy_history.append(strategy)
            
            # Afficher
            self._display_strategy(strategy)
    
    def _generate_main_approach(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Génère l'approche principale"""
        template = self.strategy_templates[config['case_type']]
        
        # Sélectionner les axes pertinents
        selected_axes = []
        if "innocence" in config['context'].lower():
            selected_axes.append(template['axes'][1])  # Absence d'intention
        if "procédure" in config['context'].lower():
            selected_axes.append(template['axes'][0])  # Contestation procédure
        
        # Si aucun axe spécifique, prendre les 2 premiers
        if not selected_axes:
            selected_axes = template['axes'][:2]
        
        return {
            'title': f"Stratégie de {template['name']}",
            'focus': template['focus'],
            'primary_axes': selected_axes,
            'narrative': f"La défense s'articulera autour de {len(selected_axes)} axes principaux, "
                        f"en mettant l'accent sur {template['focus']}. "
                        f"Cette approche vise à {config['objectives'][0].lower()}.",
            'key_message': "Notre client a agi de bonne foi dans le respect de ses obligations."
        }
    
    def _generate_action_plan(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère le plan d'action"""