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
        actions = []
        
        # Actions selon l'urgence
        if config['urgency'] in ['Élevée', 'Critique']:
            actions.append({
                'phase': 'Immédiat (0-7 jours)',
                'priority': 'Critique',
                'tasks': [
                    'Constituer l\'équipe de défense',
                    'Sécuriser et analyser toutes les preuves',
                    'Identifier et contacter les témoins clés',
                    'Préparer les premières réponses procédurales'
                ]
            })
        
        actions.append({
            'phase': 'Court terme (1-4 semaines)',
            'priority': 'Élevée',
            'tasks': [
                'Analyse approfondie du dossier',
                'Recherche de jurisprudence favorable',
                'Préparation des arguments principaux',
                'Évaluation des options de négociation'
            ]
        })
        
        actions.append({
            'phase': 'Moyen terme (1-3 mois)',
            'priority': 'Normale',
            'tasks': [
                'Développement de la stratégie complète',
                'Préparation des témoins',
                'Constitution du dossier de plaidoirie',
                'Anticipation des contre-arguments'
            ]
        })
        
        if config['complexity'] in ['Complexe', 'Très complexe']:
            actions.append({
                'phase': 'Long terme (3+ mois)',
                'priority': 'Stratégique',
                'tasks': [
                    'Expertise technique si nécessaire',
                    'Stratégie médiatique (si applicable)',
                    'Préparation aux appels éventuels',
                    'Plans de contingence'
                ]
            })
        
        return actions
    
    def _generate_arguments(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Génère les arguments juridiques"""
        arguments = {
            'principaux': [],
            'subsidiaires': [],
            'contra': []
        }
        
        # Arguments selon le type d'affaire
        case_type = config['case_type']
        
        if case_type == 'penal':
            arguments['principaux'] = [
                "Absence d'élément intentionnel caractérisé",
                "Violation des droits de la défense dans la procédure",
                "Insuffisance de preuves matérielles"
            ]
            arguments['subsidiaires'] = [
                "Contrainte morale exercée sur le client",
                "Erreur de fait excusable",
                "Prescription de l'action publique"
            ]
        elif case_type == 'commercial':
            arguments['principaux'] = [
                "Respect intégral des obligations contractuelles",
                "Force majeure empêchant l'exécution",
                "Inexécution imputable à la partie adverse"
            ]
            arguments['subsidiaires'] = [
                "Déséquilibre contractuel manifeste",
                "Vice du consentement",
                "Enrichissement sans cause"
            ]
        
        # Contre-arguments anticipés
        arguments['contra'] = [
            "La partie adverse pourrait invoquer...",
            "Il sera nécessaire de réfuter...",
            "Nous devons anticiper l'argument selon lequel..."
        ]
        
        return arguments
    
    def _assess_risks(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue les risques de la stratégie"""
        risks = {
            'level': 'Modéré',
            'factors': [],
            'mitigation': []
        }
        
        # Facteurs de risque
        if config['weaknesses']:
            risks['factors'].append({
                'type': 'Points faibles identifiés',
                'severity': 'Élevée',
                'description': 'Les faiblesses du dossier pourraient être exploitées'
            })
        
        if config['urgency'] == 'Critique':
            risks['factors'].append({
                'type': 'Contrainte temporelle',
                'severity': 'Élevée',
                'description': 'Le temps limité réduit les options stratégiques'
            })
        
        if config['budget'] == 'Limité':
            risks['factors'].append({
                'type': 'Ressources limitées',
                'severity': 'Modérée',
                'description': 'Budget insuffisant pour toutes les actions souhaitées'
            })
        
        # Stratégies de mitigation
        for factor in risks['factors']:
            if factor['type'] == 'Points faibles identifiés':
                risks['mitigation'].append(
                    "Préparer des contre-arguments solides pour chaque faiblesse"
                )
            elif factor['type'] == 'Contrainte temporelle':
                risks['mitigation'].append(
                    "Prioriser les actions à fort impact et mobiliser l'équipe"
                )
            elif factor['type'] == 'Ressources limitées':
                risks['mitigation'].append(
                    "Optimiser l'allocation des ressources sur les axes prioritaires"
                )
        
        # Calcul du niveau global
        high_risks = sum(1 for f in risks['factors'] if f['severity'] == 'Élevée')
        if high_risks >= 2:
            risks['level'] = 'Élevé'
        elif high_risks == 1:
            risks['level'] = 'Modéré'
        else:
            risks['level'] = 'Faible'
        
        return risks
    
    def _generate_scenarios(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des scénarios alternatifs"""
        scenarios = []
        
        # Scénario optimiste
        scenarios.append({
            'name': 'Scénario favorable',
            'probability': '30%',
            'description': 'Tous les arguments sont acceptés, procédure rapide',
            'outcome': config['objectives'][0],
            'conditions': [
                'Jurisprudence favorable appliquée',
                'Témoins crédibles et cohérents',
                'Faiblesses de la partie adverse exploitées'
            ]
        })
        
        # Scénario réaliste
        scenarios.append({
            'name': 'Scénario probable',
            'probability': '50%',
            'description': 'Succès partiel avec compromis nécessaires',
            'outcome': 'Résolution négociée ou victoire partielle',
            'conditions': [
                'Arguments principaux reconnus',
                'Quelques concessions nécessaires',
                'Délais respectés'
            ]
        })
        
        # Scénario pessimiste
        scenarios.append({
            'name': 'Scénario défavorable',
            'probability': '20%',
            'description': 'Difficultés majeures nécessitant adaptation',
            'outcome': 'Nécessité d\'appel ou négociation défensive',
            'conditions': [
                'Arguments rejetés en première instance',
                'Nouvelles preuves défavorables',
                'Complications procédurales'
            ],
            'contingency': 'Préparer immédiatement la stratégie d\'appel'
        })
        
        return scenarios
    
    def _generate_timeline(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère un planning détaillé"""
        timeline = []
        
        # Calculer les dates selon l'urgence
        start_date = datetime.now()
        
        milestones = [
            ('Analyse initiale complète', 7),
            ('Arguments principaux finalisés', 21),
            ('Dossier de preuves constitué', 30),
            ('Préparation des témoins terminée', 45),
            ('Stratégie de plaidoirie finalisée', 60),
            ('Prêt pour l\'audience', 75)
        ]
        
        # Ajuster selon l'urgence
        if config['urgency'] == 'Critique':
            factor = 0.5
        elif config['urgency'] == 'Élevée':
            factor = 0.75
        else:
            factor = 1.0
        
        for milestone, days in milestones:
            timeline.append({
                'milestone': milestone,
                'target_date': start_date + timedelta(days=int(days * factor)),
                'status': 'À venir',
                'responsible': 'Équipe juridique',
                'deliverables': [
                    'Document de synthèse',
                    'Validation client',
                    'Archivage sécurisé'
                ]
            })
        
        return timeline
    
    def _estimate_resources(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Estime les ressources nécessaires"""
        resources = {
            'team': [],
            'time_estimate': '',
            'budget_estimate': '',
            'external_needs': []
        }
        
        # Équipe selon la complexité
        if config['complexity'] in ['Simple', 'Modérée']:
            resources['team'] = [
                'Avocat principal',
                'Assistant juridique'
            ]
            resources['time_estimate'] = '50-100 heures'
        else:
            resources['team'] = [
                'Avocat principal senior',
                'Avocat collaborateur',
                '2 Assistants juridiques',
                'Stagiaire'
            ]
            resources['time_estimate'] = '200-500 heures'
        
        # Budget
        budget_multiplier = {
            'Limité': 0.5,
            'Standard': 1.0,
            'Confortable': 1.5,
            'Illimité': 2.0
        }[config['budget']]
        
        base_cost = 10000 if config['complexity'] in ['Simple', 'Modérée'] else 25000
        resources['budget_estimate'] = f"{int(base_cost * budget_multiplier):,} - {int(base_cost * budget_multiplier * 1.5):,} €"
        
        # Besoins externes
        if config['include_jurisprudence']:
            resources['external_needs'].append('Accès bases de données juridiques')
        if config['complexity'] in ['Complexe', 'Très complexe']:
            resources['external_needs'].append('Expert technique')
        if 'financier' in config['case_type']:
            resources['external_needs'].append('Expert-comptable')
        
        return resources
    
    def _display_strategy(self, strategy: Dict[str, Any]):
        """Affiche la stratégie générée"""
        st.success("✅ Stratégie générée avec succès")
        
        # En-tête
        st.markdown(f"## 📋 {strategy['main_approach']['title']}")
        st.markdown(f"*Générée le {strategy['created_at'].strftime('%d/%m/%Y à %H:%M')}*")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            urgency_colors = {
                'Faible': '🟢',
                'Modérée': '🟡',
                'Élevée': '🟠',
                'Critique': '🔴'
            }
            st.metric(
                "Urgence",
                strategy['config']['urgency'],
                delta=urgency_colors.get(strategy['config']['urgency'], '⚪')
            )
        
        with col2:
            if strategy.get('risks'):
                risk_colors = {
                    'Faible': '🟢',
                    'Modéré': '🟡',
                    'Élevé': '🔴'
                }
                st.metric(
                    "Niveau de risque",
                    strategy['risks']['level'],
                    delta=risk_colors.get(strategy['risks']['level'], '⚪')
                )
        
        with col3:
            st.metric(
                "Phases d'action",
                len(strategy['action_plan'])
            )
        
        with col4:
            st.metric(
                "Budget estimé",
                strategy['resources']['budget_estimate'].split('-')[0].strip()
            )
        
        # Tabs de contenu
        tabs = st.tabs([
            "🎯 Approche",
            "📋 Plan d'action",
            "💭 Arguments",
            "⚠️ Risques",
            "🔄 Scénarios",
            "📅 Planning",
            "👥 Ressources",
            "💾 Export"
        ])
        
        with tabs[0]:
            self._display_approach_tab(strategy)
        
        with tabs[1]:
            self._display_action_plan_tab(strategy)
        
        with tabs[2]:
            self._display_arguments_tab(strategy)
        
        with tabs[3]:
            self._display_risks_tab(strategy)
        
        with tabs[4]:
            self._display_scenarios_tab(strategy)
        
        with tabs[5]:
            self._display_timeline_tab(strategy)
        
        with tabs[6]:
            self._display_resources_tab(strategy)
        
        with tabs[7]:
            self._display_export_tab(strategy)
    
    def _display_approach_tab(self, strategy: Dict[str, Any]):
        """Affiche l'approche stratégique"""
        approach = strategy['main_approach']
        
        st.markdown("### 🎯 Approche stratégique principale")
        
        st.info(approach['narrative'])
        
        st.markdown("#### 📍 Axes prioritaires")
        for i, axis in enumerate(approach['primary_axes'], 1):
            st.markdown(f"{i}. **{axis}**")
        
        st.markdown("#### 💬 Message clé")
        st.success(f'"{approach["key_message"]}"')
        
        st.markdown("#### 🎯 Objectifs visés")
        objectives = strategy['config']['objectives']
        
        cols = st.columns(min(len(objectives), 3))
        for i, obj in enumerate(objectives):
            with cols[i % len(cols)]:
                st.markdown(f"✓ {obj}")
    
    def _display_action_plan_tab(self, strategy: Dict[str, Any]):
        """Affiche le plan d'action"""
        st.markdown("### 📋 Plan d'action détaillé")
        
        for phase in strategy['action_plan']:
            priority_colors = {
                'Critique': 'red',
                'Élevée': 'orange',
                'Normale': 'blue',
                'Stratégique': 'green'
            }
            
            with st.expander(f"**{phase['phase']}** - Priorité {phase['priority']}", expanded=True):
                for task in phase['tasks']:
                    st.markdown(f"- [ ] {task}")
                
                # Bouton pour copier les tâches
                task_list = '\n'.join([f"- [ ] {task}" for task in phase['tasks']])
                st.code(task_list)
    
    def _display_arguments_tab(self, strategy: Dict[str, Any]):
        """Affiche les arguments juridiques"""
        st.markdown("### 💭 Arguments juridiques")
        
        arguments = strategy['arguments']
        
        # Arguments principaux
        st.markdown("#### ⚖️ Arguments principaux")
        for i, arg in enumerate(arguments['principaux'], 1):
            st.success(f"**{i}.** {arg}")
        
        # Arguments subsidiaires
        if arguments['subsidiaires']:
            st.markdown("#### 🔄 Arguments subsidiaires")
            for i, arg in enumerate(arguments['subsidiaires'], 1):
                st.info(f"**{i}.** {arg}")
        
        # Contre-arguments
        if arguments['contra']:
            st.markdown("#### 🛡️ Anticipation des contre-arguments")
            for arg in arguments['contra']:
                st.warning(f"⚠️ {arg}")
    
    def _display_risks_tab(self, strategy: Dict[str, Any]):
        """Affiche l'analyse des risques"""
        if not strategy.get('risks'):
            st.info("Analyse des risques non demandée")
            return
        
        risks = strategy['risks']
        
        st.markdown("### ⚠️ Analyse des risques")
        
        # Niveau global
        level_colors = {
            'Faible': 'green',
            'Modéré': 'orange',
            'Élevé': 'red'
        }
        
        st.markdown(
            f"<h4 style='color: {level_colors.get(risks['level'], 'gray')}'>Niveau de risque global : {risks['level']}</h4>",
            unsafe_allow_html=True
        )
        
        # Facteurs de risque
        st.markdown("#### 📊 Facteurs de risque identifiés")
        
        for factor in risks['factors']:
            severity_icon = '🔴' if factor['severity'] == 'Élevée' else '🟡'
            
            with st.expander(f"{severity_icon} {factor['type']}", expanded=True):
                st.write(f"**Sévérité :** {factor['severity']}")
                st.write(f"**Description :** {factor['description']}")
        
        # Stratégies de mitigation
        st.markdown("#### 🛡️ Stratégies de mitigation")
        
        for i, mitigation in enumerate(risks['mitigation'], 1):
            st.markdown(f"{i}. {mitigation}")
    
    def _display_scenarios_tab(self, strategy: Dict[str, Any]):
        """Affiche les scénarios"""
        if not strategy.get('scenarios'):
            st.info("Génération de scénarios non demandée")
            return
        
        st.markdown("### 🔄 Scénarios possibles")
        
        for scenario in strategy['scenarios']:
            # Couleur selon la probabilité
            prob_value = int(scenario['probability'].rstrip('%'))
            if prob_value >= 50:
                color = 'green'
            elif prob_value >= 30:
                color = 'orange'
            else:
                color = 'red'
            
            with st.expander(
                f"**{scenario['name']}** - Probabilité : {scenario['probability']}",
                expanded=scenario['name'] == 'Scénario probable'
            ):
                st.write(f"**Description :** {scenario['description']}")
                st.write(f"**Résultat attendu :** {scenario['outcome']}")
                
                st.write("**Conditions :**")
                for condition in scenario['conditions']:
                    st.write(f"- {condition}")
                
                if scenario.get('contingency'):
                    st.warning(f"**Plan B :** {scenario['contingency']}")
    
    def _display_timeline_tab(self, strategy: Dict[str, Any]):
        """Affiche le planning"""
        if not strategy.get('timeline'):
            st.info("Planning non demandé")
            return
        
        st.markdown("### 📅 Planning prévisionnel")
        
        # Timeline sous forme de tableau
        for milestone in strategy['timeline']:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{milestone['milestone']}**")
                
                # Livrables
                with st.expander("Livrables"):
                    for deliverable in milestone['deliverables']:
                        st.write(f"- {deliverable}")
            
            with col2:
                st.write(f"📅 {milestone['target_date'].strftime('%d/%m/%Y')}")
                st.write(f"👤 {milestone['responsible']}")
            
            with col3:
                if milestone['status'] == 'À venir':
                    st.write("⏳ À venir")
                elif milestone['status'] == 'En cours':
                    st.write("🔄 En cours")
                else:
                    st.write("✅ Terminé")
    
    def _display_resources_tab(self, strategy: Dict[str, Any]):
        """Affiche les ressources nécessaires"""
        resources = strategy['resources']
        
        st.markdown("### 👥 Ressources nécessaires")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👨‍⚖️ Équipe juridique")
            for member in resources['team']:
                st.write(f"• {member}")
            
            st.markdown("#### ⏱️ Temps estimé")
            st.info(resources['time_estimate'])
        
        with col2:
            st.markdown("#### 💰 Budget estimé")
            st.success(resources['budget_estimate'])
            
            if resources['external_needs']:
                st.markdown("#### 🔗 Besoins externes")
                for need in resources['external_needs']:
                    st.write(f"• {need}")
    
    def _display_export_tab(self, strategy: Dict[str, Any]):
        """Options d'export de la stratégie"""
        st.markdown("### 💾 Export de la stratégie")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export PDF (simulé)
            if st.button("📄 Générer PDF", use_container_width=True):
                st.info("Génération du PDF en cours...")
                # Ici, intégrer une vraie génération PDF
            
            # Export Word (texte)
            doc_content = self._generate_strategy_document(strategy)
            st.download_button(
                "📝 Télécharger Word",
                data=doc_content,
                file_name=f"strategie_{strategy['id']}.txt",
                mime="text/plain"
            )
        
        with col2:
            # Export JSON
            import json
            json_str = json.dumps(strategy, default=str, ensure_ascii=False, indent=2)
            
            st.download_button(
                "💾 Télécharger JSON",
                data=json_str,
                file_name=f"strategie_{strategy['id']}.json",
                mime="application/json"
            )
            
            # Partage
            if st.button("📧 Envoyer par email", use_container_width=True):
                st.info("Fonctionnalité d'envoi par email à venir")
    
    def _generate_strategy_document(self, strategy: Dict[str, Any]) -> str:
        """Génère un document de stratégie formaté"""
        lines = []
        
        # En-tête
        lines.append("DOCUMENT DE STRATÉGIE JURIDIQUE")
        lines.append("=" * 50)
        lines.append(f"Généré le : {strategy['created_at'].strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"Type d'affaire : {self.strategy_templates[strategy['config']['case_type']]['name']}")
        lines.append(f"Urgence : {strategy['config']['urgency']}")
        lines.append(f"Complexité : {strategy['config']['complexity']}")
        lines.append("")
        
        # Contexte
        lines.append("CONTEXTE DE L'AFFAIRE")
        lines.append("-" * 30)
        lines.append(strategy['config']['context'])
        lines.append("")
        
        # Approche
        lines.append("APPROCHE STRATÉGIQUE")
        lines.append("-" * 30)
        lines.append(strategy['main_approach']['narrative'])
        lines.append(f"\nMessage clé : {strategy['main_approach']['key_message']}")
        lines.append("\nAxes prioritaires :")
        for i, axis in enumerate(strategy['main_approach']['primary_axes'], 1):
            lines.append(f"  {i}. {axis}")
        lines.append("")
        
        # Plan d'action
        lines.append("PLAN D'ACTION")
        lines.append("-" * 30)
        for phase in strategy['action_plan']:
            lines.append(f"\n{phase['phase']} (Priorité : {phase['priority']})")
            for task in phase['tasks']:
                lines.append(f"  - {task}")
        lines.append("")
        
        # Arguments
        lines.append("ARGUMENTS JURIDIQUES")
        lines.append("-" * 30)
        lines.append("\nArguments principaux :")
        for i, arg in enumerate(strategy['arguments']['principaux'], 1):
            lines.append(f"  {i}. {arg}")
        
        if strategy['arguments']['subsidiaires']:
            lines.append("\nArguments subsidiaires :")
            for i, arg in enumerate(strategy['arguments']['subsidiaires'], 1):
                lines.append(f"  {i}. {arg}")
        lines.append("")
        
        # Ressources
        lines.append("RESSOURCES NÉCESSAIRES")
        lines.append("-" * 30)
        lines.append(f"Budget estimé : {strategy['resources']['budget_estimate']}")
        lines.append(f"Temps estimé : {strategy['resources']['time_estimate']}")
        lines.append("\nÉquipe :")
        for member in strategy['resources']['team']:
            lines.append(f"  - {member}")
        
        return "\n".join(lines)
    
    def _render_strategy_library(self):
        """Bibliothèque de stratégies sauvegardées"""
        st.markdown("#### 📚 Bibliothèque de stratégies")
        
        if 'strategy_history' not in st.session_state or not st.session_state.strategy_history:
            st.info("Aucune stratégie sauvegardée. Créez votre première stratégie pour commencer.")
            return
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Type d'affaire",
                ["Tous"] + list(self.strategy_templates.keys()),
                format_func=lambda x: "Tous" if x == "Tous" else self.strategy_templates[x]['name']
            )
        
        with col2:
            filter_urgency = st.selectbox(
                "Urgence",
                ["Tous", "Faible", "Modérée", "Élevée", "Critique"]
            )
        
        with col3:
            search = st.text_input("Rechercher", placeholder="Mots-clés...")
        
        # Filtrer les stratégies
        filtered_strategies = st.session_state.strategy_history
        
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
        
        if search:
            filtered_strategies = [
                s for s in filtered_strategies 
                if search.lower() in s['config']['context'].lower()
            ]
        
        # Afficher les stratégies
        for strategy in filtered_strategies:
            with st.expander(
                f"{self.strategy_templates[strategy['config']['case_type']]['name']} - "
                f"{strategy['created_at'].strftime('%d/%m/%Y')}",
                expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Urgence :** {strategy['config']['urgency']}")
                    st.write(f"**Complexité :** {strategy['config']['complexity']}")
                    st.write(f"**Contexte :** {strategy['config']['context'][:200]}...")
                
                with col2:
                    if st.button("📂 Charger", key=f"load_{strategy['id']}"):
                        self._display_strategy(strategy)
                    
                    if st.button("🗑️ Supprimer", key=f"delete_{strategy['id']}"):
                        st.session_state.strategy_history.remove(strategy)
                        st.rerun()
    
    def _render_strategy_comparison(self):
        """Compare plusieurs stratégies"""
        st.markdown("#### 🔄 Comparaison de stratégies")
        
        if 'strategy_history' not in st.session_state or len(st.session_state.strategy_history) < 2:
            st.info("Au moins 2 stratégies sont nécessaires pour effectuer une comparaison.")
            return
        
        # Sélection des stratégies à comparer
        strategies_options = [
            f"{s['id']} - {s['created_at'].strftime('%d/%m/%Y')}"
            for s in st.session_state.strategy_history
        ]
        
        selected_indices = st.multiselect(
            "Sélectionner 2 à 4 stratégies",
            range(len(strategies_options)),
            format_func=lambda x: strategies_options[x],
            max_selections=4
        )
        
        if len(selected_indices) >= 2:
            if st.button("🔍 Comparer", type="primary"):
                selected_strategies = [
                    st.session_state.strategy_history[i] 
                    for i in selected_indices
                ]
                
                self._display_strategy_comparison(selected_strategies)
    
    def _display_strategy_comparison(self, strategies: List[Dict[str, Any]]):
        """Affiche la comparaison de stratégies"""
        st.markdown("### 📊 Comparaison des stratégies")
        
        # Tableau comparatif
        comparison_data = []
        
        for strategy in strategies:
            comparison_data.append({
                'ID': strategy['id'][-8:],
                'Type': self.strategy_templates[strategy['config']['case_type']]['name'],
                'Urgence': strategy['config']['urgency'],
                'Complexité': strategy['config']['complexity'],
                'Budget': strategy['config']['budget'],
                'Axes': len(strategy['main_approach']['primary_axes']),
                'Actions': sum(len(phase['tasks']) for phase in strategy['action_plan']),
                'Risque': strategy.get('risks', {}).get('level', 'N/A')
            })
        
        # Afficher sous forme de colonnes
        cols = st.columns(len(strategies))
        
        for i, (col, data) in enumerate(zip(cols, comparison_data)):
            with col:
                st.markdown(f"**Stratégie {i+1}**")
                for key, value in data.items():
                    st.write(f"**{key}:** {value}")
        
        # Points de divergence
        st.markdown("#### 🔀 Points de divergence")
        
        # Identifier les différences majeures
        divergences = []
        
        # Comparer les urgences
        urgencies = set(s['config']['urgency'] for s in strategies)
        if len(urgencies) > 1:
            divergences.append(f"**Urgence variable :** {', '.join(urgencies)}")
        
        # Comparer les approches
        approaches = set(tuple(s['main_approach']['primary_axes']) for s in strategies)
        if len(approaches) > 1:
            divergences.append("**Approches stratégiques différentes**")
        
        # Comparer les budgets
        budgets = set(s['config']['budget'] for s in strategies)
        if len(budgets) > 1:
            divergences.append(f"**Budgets différents :** {', '.join(budgets)}")
        
        for divergence in divergences:
            st.warning(divergence)
        
        # Recommandation
        st.markdown("#### 💡 Recommandation")
        
        # Stratégie optimale (simplifiée)
        optimal_idx = 0
        for i, strategy in enumerate(strategies):
            if strategy.get('risks', {}).get('level') == 'Faible':
                optimal_idx = i
                break
        
        st.success(
            f"La stratégie {optimal_idx + 1} semble la plus équilibrée "
            f"compte tenu du rapport risque/bénéfice."
        )
    
    def _render_help(self):
        """Affiche l'aide du module"""
        st.markdown("""
        #### ❓ Guide d'utilisation du module Stratégie
        
        ##### 🎯 Objectif
        Ce module vous aide à développer des stratégies juridiques complètes et adaptées à votre affaire.
        
        ##### 📋 Fonctionnalités principales
        
        1. **Génération de stratégie**
           - Analyse du contexte et des enjeux
           - Identification des axes de défense
           - Plan d'action détaillé
           - Arguments juridiques structurés
        
        2. **Analyse des risques**
           - Identification des points faibles
           - Stratégies de mitigation
           - Scénarios alternatifs
        
        3. **Planning et ressources**
           - Timeline avec jalons clés
           - Estimation budgétaire
           - Constitution de l'équipe
        
        ##### 💡 Conseils d'utilisation
        
        - **Contexte détaillé** : Plus vous fournissez d'informations, plus la stratégie sera pertinente
        - **Points faibles** : N'hésitez pas à mentionner les difficultés, cela améliore l'analyse
        - **Objectifs clairs** : Hiérarchisez vos objectifs pour une stratégie focalisée
        - **Révision régulière** : Adaptez la stratégie selon l'évolution de l'affaire
        
        ##### 🔧 Paramètres avancés
        
        - **Jurisprudence** : Active la recherche de précédents
        - **Scénarios** : Génère des hypothèses optimiste/réaliste/pessimiste
        - **Timeline** : Crée un planning détaillé avec livrables
        - **Analyse des risques** : Évalue et propose des mitigations
        
        ##### 📊 Interprétation des résultats
        
        - **Niveau de risque** : Faible (vert) → Élevé (rouge)
        - **Priorités** : Critique → Stratégique
        - **Probabilités** : Basées sur l'expérience et les précédents
        - **Budget** : Fourchette estimative à affiner
        
        ##### ✨ Astuces
        
        - Utilisez la **comparaison** pour évaluer plusieurs approches
        - Exportez en **PDF** pour partager avec votre équipe
        - La **bibliothèque** conserve toutes vos stratégies
        - Adaptez les **templates** à vos besoins spécifiques
        """)


# Point d'entrée pour tests
if __name__ == "__main__":
    module = StrategyModule()
    module.render()